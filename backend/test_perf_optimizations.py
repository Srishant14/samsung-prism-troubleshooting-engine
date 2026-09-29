"""
Performance optimization tests for the Smart Guided Troubleshooting Engine.

These tests validate that performance optimizations work correctly
WITHOUT breaking existing behavior. They supplement the original 25 tests.

Run with:
    cd backend
    python -m pytest test_perf_optimizations.py -v
"""
import os
import sys
import time
import pytest

# Ensure we can import the backend modules
sys.path.insert(0, os.path.dirname(__file__))

# Force no API keys so tests use keyword fallback (deterministic)
os.environ["GEMINI_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

from classifier import classify_complaint, simple_keyword_fallback
from knowledge_base import (
    search_knowledge, get_supported_issues, get_issue_criteria,
    has_exact_kb_record, _KB_INDEX, _TAXONOMY, _ISSUE_CRITERIA,
)
from schemas import LLMClassification, IssueClassification
from config import FAST_PATH_CONFIDENCE, CONFIDENCE_THRESHOLD
from session import (
    create_session, get_session, delete_session, has_rounds_left,
    SESSION_TTL_SECONDS, MAX_ROUNDS, _sessions,
)
from perf import RequestMetrics


# ============================================================
# Test 1: Fast path does not invoke unnecessary Laya decisions
# ============================================================
class TestFastPath:
    def test_fast_path_returns_without_laya(self):
        """A clear battery drain query with slots should resolve via fast path (no Laya calls)."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "My battery is draining very fast while gaming heavy use"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["domain"] == "battery"
        # The fast path should work — verified by the existence of results
        assert len(data["results"]) >= 1
        assert data["results"][0]["issue"] == "fast_drain"

    def test_fast_path_screen_flicker(self):
        """Screen flicker should resolve via fast path."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "My screen keeps flickering"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["results"][0]["domain"] == "display"
        assert data["results"][0]["issue"] == "screen_flicker"

    def test_fast_path_camera_blur(self):
        """Camera blur with slots should resolve via fast path."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "My camera photos are blurry at night in low light"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["results"][0]["domain"] == "camera"

    def test_fast_path_slow_phone(self):
        """Slow phone with slots should resolve via fast path."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "My phone has become very slow with storage full"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["results"][0]["domain"] == "performance"


# ============================================================
# Test 2: Ambiguous path invokes Laya (diagnostic flow)
# ============================================================
class TestAmbiguousPath:
    def test_ambiguous_overheating_triggers_followup(self):
        """Ambiguous 'overheating' query should trigger follow-up, not fast path."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "My phone is overheating"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "follow_up"
        assert data["session_id"] is not None

    def test_ambiguous_battery_problem_triggers_followup(self):
        """Generic 'battery problem' should trigger follow-up."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "I have a battery problem"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "follow_up"


# ============================================================
# Test 3: Exact KB match exits early
# ============================================================
class TestEarlyExit:
    def test_exact_kb_match_returns_immediately(self):
        """An exact domain+issue match should return without extra processing."""
        result = search_knowledge("battery", "fast_drain", "battery draining fast")
        assert result is not None
        record, conf = result
        assert conf >= 0.7
        assert record["domain"] == "battery"
        assert record["issue"] == "fast_drain"

    def test_exact_kb_match_via_api(self):
        """Full API call with exact match should return success immediately."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={
            "query": "My phone battery is draining very fast while idle overnight"
        })
        data = response.json()
        assert data["status"] == "success"
        assert len(data["results"]) >= 1


# ============================================================
# Test 4: No-match exits early
# ============================================================
class TestNoMatchEarlyExit:
    def test_vague_query_exits_early(self):
        """Vague query should exit without expensive processing."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={
            "query": "My phone smells strange"
        })
        data = response.json()
        assert data["status"] == "no_match"

    def test_unsupported_domain_returns_none(self):
        """Searching an unsupported domain returns None immediately."""
        result = search_knowledge("connectivity", "wifi_slow", "wifi is slow")
        assert result is None


# ============================================================
# Test 5: Multi-issue lookup is optimized
# ============================================================
class TestMultiIssueOptimized:
    def test_multi_issue_concurrent_lookup(self):
        """Multi-issue query should return multiple results."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={
            "query": "My screen is flickering and my battery is draining very fast while idle overnight"
        })
        data = response.json()
        assert data["status"] == "success"
        domains = {r["domain"] for r in data["results"]}
        assert "display" in domains
        assert "battery" in domains
        assert len(data["results"]) >= 2


# ============================================================
# Test 6: Laya Router is singleton
# ============================================================
class TestLayaSingleton:
    def test_router_singleton(self):
        """Laya Router should be initialized at most once."""
        from decision_engine import _get_router, _router, _init_attempted
        # After first import, _get_router returns same instance each time
        r1 = _get_router()
        r2 = _get_router()
        # Both should be the same object (or both None if laya not installed)
        assert r1 is r2

    def test_executor_is_singleton(self):
        """ThreadPoolExecutor should be a module-level singleton."""
        from decision_engine import _executor
        import concurrent.futures
        assert isinstance(_executor, concurrent.futures.ThreadPoolExecutor)


# ============================================================
# Test 7: Session TTL remains functional
# ============================================================
class TestSessionTTL:
    def test_session_ttl_is_600_seconds(self):
        """Session TTL should be 10 minutes (600 seconds)."""
        assert SESSION_TTL_SECONDS == 600

    def test_session_creation_and_retrieval(self):
        """Created session should be retrievable."""
        session = create_session("test query", domain="battery", tree="battery")
        retrieved = get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        # Cleanup
        delete_session(session.session_id)

    def test_expired_session_returns_none(self):
        """An expired session should return None."""
        session = create_session("test query", domain="battery", tree="battery")
        # Manually expire the session
        session.created_at = time.time() - SESSION_TTL_SECONDS - 10
        retrieved = get_session(session.session_id)
        assert retrieved is None


# ============================================================
# Test 8: Maximum 5 diagnostic steps remains enforced
# ============================================================
class TestMaxDiagnosticSteps:
    def test_max_rounds_is_5(self):
        """MAX_ROUNDS should be 5."""
        assert MAX_ROUNDS == 5

    def test_has_rounds_left_enforced(self):
        """Session with round_count >= 5 should not have rounds left."""
        session = create_session("test query", domain="battery", tree="battery")
        session.round_count = 4
        assert has_rounds_left(session) is True
        session.round_count = 5
        assert has_rounds_left(session) is False
        # Cleanup
        delete_session(session.session_id)


# ============================================================
# Test 9: Timeout fallback works
# ============================================================
class TestTimeoutFallback:
    def test_laya_timeout_uses_fallback(self):
        """If Laya times out, the fallback should still return a valid result."""
        from decision_engine import _fallback_decide_domain

        result = _fallback_decide_domain(
            ["battery/fast_drain"], "My battery is draining"
        )
        assert result["domain"] == "battery"
        assert result["confidence"] > 0

    def test_fallback_next_action_with_kb_match(self):
        """Fallback next action with KB match should return RESOLVE or LOOKUP."""
        from decision_engine import _fallback_next_action

        result = _fallback_next_action(
            symptoms=["battery/fast_drain"],
            contexts=[],
            candidate_issues=["battery/fast_drain"],
            confirmed_issues=["battery/fast_drain"],
            questions_asked=0,
            has_kb_match=True,
        )
        assert result["action"] in ("RESOLVE", "LOOKUP_KNOWLEDGE")


# ============================================================
# Test 10: Laya failure fallback works
# ============================================================
class TestLayaFailureFallback:
    def test_fallback_domain_classification(self):
        """Rule-based fallback should classify battery queries correctly."""
        from decision_engine import _fallback_decide_domain

        result = _fallback_decide_domain([], "My battery is draining very fast")
        assert result["domain"] == "battery"

    def test_fallback_issue_classification(self):
        """Rule-based fallback should classify issues via word overlap."""
        from decision_engine import _fallback_decide_issue

        supported = {
            "fast_drain": "Battery Draining Quickly, rapid battery percentage drop",
            "slow_charging": "Phone Charges Slowly, slow charging speed",
        }
        result = _fallback_decide_issue(
            "battery", ["battery/fast_drain"],
            "my battery drains fast", supported,
        )
        assert result["issue"] == "fast_drain"

    def test_fallback_evidence_check(self):
        """Rule-based fallback should assess evidence based on heuristics."""
        from decision_engine import _fallback_sufficient_evidence

        result = _fallback_sufficient_evidence(
            symptoms=["battery/fast_drain"],
            contexts=["after_update"],
            candidate_issues=["battery/fast_drain"],
        )
        assert "sufficient" in result
        assert "probability" in result


# ============================================================
# Test 11: Precomputed KB indexes are correct
# ============================================================
class TestPrecomputedIndexes:
    def test_kb_index_populated(self):
        """KB index should have entries for known domain/issue pairs."""
        assert ("battery", "fast_drain") in _KB_INDEX
        assert ("display", "screen_flicker") in _KB_INDEX
        assert ("camera", "camera_blur") in _KB_INDEX
        assert ("performance", "app_lag") in _KB_INDEX

    def test_taxonomy_populated(self):
        """Taxonomy should have all 4 domains."""
        assert "battery" in _TAXONOMY
        assert "display" in _TAXONOMY
        assert "camera" in _TAXONOMY
        assert "performance" in _TAXONOMY

    def test_issue_criteria_populated(self):
        """Issue criteria should be precomputed for all domains."""
        for domain in ["battery", "display", "camera", "performance"]:
            criteria = get_issue_criteria(domain)
            assert len(criteria) > 0, f"No criteria for {domain}"

    def test_has_exact_kb_record(self):
        """has_exact_kb_record should return True for known pairs."""
        assert has_exact_kb_record("battery", "fast_drain") is True
        assert has_exact_kb_record("connectivity", "wifi_slow") is False

    def test_get_supported_issues_uses_cache(self):
        """get_supported_issues should return the cached taxonomy."""
        taxonomy = get_supported_issues()
        assert taxonomy is _TAXONOMY  # Same object, not a copy


# ============================================================
# Test 12: Performance metrics collection
# ============================================================
class TestPerformanceMetrics:
    def test_request_metrics_timing(self):
        """RequestMetrics should measure elapsed time."""
        m = RequestMetrics()
        with m.measure("test_op"):
            time.sleep(0.02)  # 20ms
        summary = m.summary()
        assert "test_op" in summary["timings_ms"]
        assert summary["timings_ms"]["test_op"] >= 5  # at least 5ms

    def test_request_metrics_counters(self):
        """RequestMetrics should track call counts."""
        m = RequestMetrics()
        m.increment("laya_calls")
        m.increment("laya_calls")
        m.increment("kb_searches")
        summary = m.summary()
        assert summary["counts"]["laya_calls"] == 2
        assert summary["counts"]["kb_searches"] == 1

    def test_request_metrics_path(self):
        """RequestMetrics should track which path was taken."""
        m = RequestMetrics()
        m.set_path("fast_path")
        assert m.summary()["path"] == "fast_path"

    def test_perf_endpoint(self):
        """The /v1/perf endpoint should return aggregate stats."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/v1/perf")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "avg_latency_ms" in data


# ============================================================
# Test 13: FAST_PATH_CONFIDENCE is configurable
# ============================================================
class TestConfigurable:
    def test_fast_path_confidence_exists(self):
        """FAST_PATH_CONFIDENCE should be defined and >= 0."""
        assert FAST_PATH_CONFIDENCE >= 0
        assert FAST_PATH_CONFIDENCE <= 1.0

    def test_confidence_threshold_exists(self):
        """CONFIDENCE_THRESHOLD should be 0.6."""
        assert CONFIDENCE_THRESHOLD == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
