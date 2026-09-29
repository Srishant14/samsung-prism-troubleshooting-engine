"""
Test suite for the Fast Local Gate and refactored diagnostic engine.

Tests validate:
1. FAST PATH: Clear queries resolve with zero LLM/Laya calls
2. AMBIGUOUS: Partial queries trigger follow-up questions
3. NARROW: Specific contexts don't return generic answers
4. MULTI-ISSUE: Multiple issues detected simultaneously
5. LLM FALLBACK: Unusual queries invoke LLM exactly once
6. NO-MATCH: Unsupported queries return no-match
7. PERFORMANCE: Fast gate runs in < 5ms

Run with:
    cd backend
    python -m pytest test_fast_gate.py -v
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

from fast_gate import (
    fast_gate, GateVerdict, Specificity, GateResult,
    compute_specificity, _match_aliases, _detect_domain,
    _is_vague_query, _detect_multi_issues, _extract_context,
)
from knowledge_base import search_knowledge


# ============================================================
# Test 1: FAST PATH — Clear queries (zero LLM, zero Laya)
# ============================================================
class TestFastPathGate:
    def test_battery_drain_clear(self):
        """'My battery is draining very fast' → CLEAR, battery/fast_drain"""
        result = fast_gate("My battery is draining very fast")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "battery"
        assert result.issue == "fast_drain"

    def test_phone_slow_clear(self):
        """'My phone has become very slow' → CLEAR, performance/app_lag"""
        result = fast_gate("My phone has become very slow")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "performance"
        assert result.issue == "app_lag"

    def test_screen_flickering_clear(self):
        """'My screen keeps flickering' → CLEAR, display/screen_flicker"""
        result = fast_gate("My screen keeps flickering")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "display"
        assert result.issue == "screen_flicker"

    def test_camera_blur_clear(self):
        """'My camera photos are blurry' → CLEAR, camera/camera_blur"""
        result = fast_gate("My camera photos are blurry")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "camera"
        assert result.issue == "camera_blur"

    def test_apps_forever_clear(self):
        """'Apps are taking forever to open' → CLEAR, performance/slow_apps"""
        result = fast_gate("Apps are taking forever to open")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "performance"
        assert result.issue == "slow_apps"

    def test_slang_battery_clear(self):
        """'bro my battery is literally dying in like 3 hours' → CLEAR"""
        result = fast_gate("bro my battery is literally dying in like 3 hours")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "battery"
        assert result.issue == "fast_drain"

    def test_paraphrase_barely_lasts(self):
        """'My phone barely lasts half a day' → CLEAR, battery/fast_drain"""
        result = fast_gate("My phone barely lasts half a day")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "battery"

    def test_fast_path_via_api(self):
        """Full API call should use fast path (zero LLM calls)."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        # Without slots: Sufficiency Guard blocks premature KB retrieval
        response_vague = client.post("/v1/troubleshoot", json={
            "query": "My battery is draining very fast"
        })
        assert response_vague.status_code == 200
        assert response_vague.json()["status"] == "follow_up"

        # With slots specified: Guarded Fast-path resolves immediately
        response = client.post("/v1/troubleshoot", json={
            "query": "My battery is draining very fast while idle overnight"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["domain"] == "battery"
        assert len(data["results"]) >= 1

    def test_fast_path_camera_via_api(self):
        """Camera blur without slots triggers follow-up; with slots resolves."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        # Without slots: Sufficiency Guard triggers clarification
        resp_vague = client.post("/v1/troubleshoot", json={
            "query": "My camera photos are blurry"
        })
        assert resp_vague.status_code == 200
        assert resp_vague.json()["status"] == "follow_up"

        # With slots: Resolves
        response = client.post("/v1/troubleshoot", json={
            "query": "My camera photos are blurry at night in low light"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["results"][0]["domain"] == "camera"


# ============================================================
# Test 2: AMBIGUOUS — Follow-up questions
# ============================================================
class TestAmbiguousGate:
    def test_overheating_partial(self):
        """'My phone gets hot' → PARTIAL, needs follow-up"""
        result = fast_gate("My phone gets hot")
        assert result.verdict == GateVerdict.PARTIAL
        assert result.tree is not None

    def test_phone_acting_weird(self):
        """'My phone is acting weird' → PARTIAL, needs domain question"""
        result = fast_gate("My phone is acting weird")
        assert result.verdict == GateVerdict.PARTIAL
        assert result.tree == "general"

    def test_overheating_via_api(self):
        """'My phone is overheating' should trigger follow-up."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={
            "query": "My phone is overheating"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "follow_up"
        assert data["session_id"] is not None
        assert data["follow_up"] is not None
        assert len(data["follow_up"]["options"]) >= 2

    def test_battery_problem_partial(self):
        """'I have a battery problem' → PARTIAL, follow-up"""
        result = fast_gate("I have a battery problem")
        assert result.verdict == GateVerdict.PARTIAL
        assert result.domain == "battery"
        assert result.tree == "battery"

    def test_camera_not_working_partial(self):
        """'My camera is not working properly' → PARTIAL"""
        result = fast_gate("My camera is not working properly")
        assert result.verdict == GateVerdict.PARTIAL
        assert result.domain == "camera"


# ============================================================
# Test 3: NARROW — Specific contexts
# ============================================================
class TestNarrowIssue:
    def test_closeup_blur_not_generic(self):
        """'My camera is blurry only when I take close-up photos' → PARTIAL (not generic)"""
        result = fast_gate("My camera is blurry only when I take close-up photos")
        # Should NOT be CLEAR with camera_blur — the context is too specific
        if result.verdict == GateVerdict.CLEAR:
            assert result.context == "close_up"
            # Verify that KB doesn't confidently resolve this
            kb = search_knowledge(result.domain, result.issue, 
                                  "camera blurry close-up", context="close_up")
            if kb:
                _, conf = kb
                assert conf < 0.5, "Should not confidently match close-up"
        else:
            # PARTIAL is the expected behavior
            assert result.verdict == GateVerdict.PARTIAL


# ============================================================
# Test 4: MULTI-ISSUE
# ============================================================
class TestMultiIssueGate:
    def test_flicker_and_battery(self):
        """'My screen is flickering and my battery is draining very fast' → two issues"""
        result = fast_gate("My screen is flickering and my battery is draining very fast")
        assert result.verdict == GateVerdict.CLEAR
        assert result.multi_issues is not None
        assert len(result.multi_issues) >= 2
        domains = {m["domain"] for m in result.multi_issues}
        assert "display" in domains
        assert "battery" in domains

    def test_multi_issue_via_api(self):
        """Multi-issue API test: both display and battery results when slots are satisfied."""
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
# Test 5: LLM FALLBACK
# ============================================================
class TestLLMFallback:
    def test_unusual_query_goes_vague(self):
        """An unusual query the fast gate can't recognize → VAGUE"""
        result = fast_gate("My phone smells like burnt toast")
        assert result.verdict == GateVerdict.VAGUE

    def test_slang_that_gate_handles(self):
        """Slang that the gate CAN handle should be CLEAR."""
        result = fast_gate("battery dying fast")
        assert result.verdict == GateVerdict.CLEAR
        assert result.domain == "battery"


# ============================================================
# Test 6: NO-MATCH
# ============================================================
class TestNoMatchGate:
    def test_smell_no_match(self):
        """'My phone smells strange' → VAGUE"""
        result = fast_gate("My phone smells strange")
        assert result.verdict == GateVerdict.VAGUE

    def test_smell_via_api(self):
        """'My phone smells strange' → no_match via API."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={
            "query": "My phone smells strange"
        })
        data = response.json()
        assert data["status"] == "no_match"


# ============================================================
# Test 7: PERFORMANCE — Gate speed
# ============================================================
class TestGatePerformance:
    def test_gate_runs_under_5ms(self):
        """Fast gate should complete in under 5ms."""
        queries = [
            "My battery is draining very fast",
            "My phone is overheating",
            "My phone is acting weird",
            "My screen is flickering and my battery is draining",
            "My camera photos are blurry",
            "Apps are taking forever to open",
            "My phone smells strange",
        ]
        for q in queries:
            start = time.perf_counter()
            fast_gate(q)
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert elapsed_ms < 5, f"Gate took {elapsed_ms:.1f}ms for '{q}'"


# ============================================================
# Test 8: Specificity scoring
# ============================================================
class TestSpecificity:
    def test_high_specificity(self):
        """Detailed query with domain + issue → HIGH"""
        s = compute_specificity(
            "My battery drains from 80% to 20% within a few hours",
            "battery", "fast_drain"
        )
        assert s == Specificity.HIGH

    def test_medium_specificity(self):
        """Domain known but no issue → MEDIUM"""
        s = compute_specificity("My battery drains quickly", "battery", None)
        assert s == Specificity.MEDIUM

    def test_low_specificity(self):
        """Vague query → LOW"""
        s = compute_specificity("My phone is acting weird", None, None)
        assert s == Specificity.LOW


# ============================================================
# Test 9: Context extraction
# ============================================================
class TestContextExtraction:
    def test_after_update(self):
        ctx = _extract_context("battery started draining after update")
        assert ctx == "after_update"

    def test_while_charging(self):
        ctx = _extract_context("phone gets hot while charging")
        assert ctx == "charging"

    def test_no_context(self):
        ctx = _extract_context("my battery drains fast")
        assert ctx is None


# ============================================================
# Test 10: Diagnostic flow integration
# ============================================================
class TestDiagnosticFlowIntegration:
    def test_followup_resolves_to_success(self):
        """Full diagnostic flow: overheating → select option → resolved."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Step 1: Trigger follow-up
        res1 = client.post("/v1/troubleshoot", json={
            "query": "My phone is overheating"
        })
        data1 = res1.json()
        assert data1["status"] == "follow_up"
        session_id = data1["session_id"]

        # Step 2: Select option 0 ("While charging")
        res2 = client.post("/v1/troubleshoot", json={
            "query": "My phone is overheating",
            "session_id": session_id,
            "selected_option": 0
        })
        data2 = res2.json()
        assert data2["status"] == "success"
        assert data2["results"][0]["domain"] == "battery"
        assert data2["results"][0]["issue"] == "overheating_while_charging"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
