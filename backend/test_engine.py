"""
Automated test suite for the Smart Guided Troubleshooting Engine.

Tests the classification → KB retrieval → validation pipeline.
Uses the keyword fallback classifier (no LLM API needed to run tests).

Run with:
    cd backend
    python -m pytest test_engine.py -v
"""
import os
import sys
import pytest

# Ensure we can import the backend modules
sys.path.insert(0, os.path.dirname(__file__))

# Force no API keys so tests use keyword fallback (deterministic)
os.environ["GEMINI_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

from classifier import classify_complaint, simple_keyword_fallback
from knowledge_base import search_knowledge
from schemas import LLMClassification, IssueClassification


# ============================================================
# Helper
# ============================================================

def classify_and_search(query: str):
    """Run the full pipeline: classify → search KB for each issue."""
    classification = simple_keyword_fallback(query)
    results = []
    for issue in classification.issues:
        if issue.domain == "unknown":
            continue
        kb = search_knowledge(
            domain=issue.domain,
            issue=issue.issue,
            query=query,
            context=issue.context,
        )
        if kb:
            record, match_conf = kb
            final_conf = issue.confidence * match_conf
            results.append({
                "domain": issue.domain,
                "issue": issue.issue,
                "context": issue.context,
                "classification_confidence": issue.confidence,
                "match_confidence": match_conf,
                "final_confidence": final_conf,
                "title": record.get("title"),
            })
    return classification, results


# ============================================================
# Test 1: Clear battery drain
# ============================================================
class TestBatteryDrain:
    def test_explicit_battery_drain(self):
        """'My phone battery is draining very fast' → battery/fast_drain"""
        cls, results = classify_and_search("My phone battery is draining very fast")
        assert len(results) >= 1
        assert results[0]["domain"] == "battery"
        assert results[0]["issue"] == "fast_drain"

    def test_paraphrase_barely_lasts(self):
        """'My phone barely lasts half a day' → battery/fast_drain"""
        cls, results = classify_and_search("My phone barely lasts half a day")
        assert len(results) >= 1
        assert results[0]["domain"] == "battery"
        assert results[0]["issue"] == "fast_drain"

    def test_paraphrase_lose_charge(self):
        """'Why does my phone lose charge so quickly?' → battery/fast_drain"""
        cls, results = classify_and_search("Why does my phone lose charge so quickly?")
        assert len(results) >= 1
        assert results[0]["domain"] == "battery"
        assert results[0]["issue"] == "fast_drain"

    def test_slang_battery(self):
        """'bro my battery is literally dying in like 3 hours 😭' → battery/fast_drain"""
        cls, results = classify_and_search("bro my battery is literally dying in like 3 hours 😭")
        assert len(results) >= 1
        assert results[0]["domain"] == "battery"
        assert results[0]["issue"] == "fast_drain"

    def test_battery_after_update(self):
        """'My battery started draining quickly after the latest update' → battery/fast_drain"""
        cls, results = classify_and_search("My battery started draining quickly after the latest update")
        assert len(results) >= 1
        assert results[0]["domain"] == "battery"
        assert results[0]["issue"] == "fast_drain"


# ============================================================
# Test 2: Performance
# ============================================================
class TestPerformance:
    def test_phone_slow(self):
        """'My phone has become very slow' → performance"""
        cls, results = classify_and_search("My phone has become very slow")
        assert len(results) >= 1
        assert results[0]["domain"] == "performance"

    def test_apps_taking_forever(self):
        """'Apps are taking forever to open' → performance/slow_apps"""
        cls, results = classify_and_search("Apps are taking forever to open")
        assert len(results) >= 1
        assert results[0]["domain"] == "performance"
        assert results[0]["issue"] == "slow_apps"

    def test_slow_after_app_install(self):
        """'My phone became extremely slow after installing a new app' → performance"""
        cls, results = classify_and_search("My phone became extremely slow after installing a new app")
        assert len(results) >= 1
        assert results[0]["domain"] == "performance"


# ============================================================
# Test 3: Camera
# ============================================================
class TestCamera:
    def test_blurry_photos(self):
        """'My camera photos are blurry' → camera/camera_blur"""
        cls, results = classify_and_search("My camera photos are blurry")
        assert len(results) >= 1
        assert results[0]["domain"] == "camera"
        assert results[0]["issue"] == "camera_blur"

    def test_close_up_blur_no_match(self):
        """'My camera is blurry only when I take close-up photos' → no verified match
        The system should NOT return generic camera_blur steps for a close-up specific issue."""
        cls, results = classify_and_search("My camera is blurry only when I take close-up photos")
        # Should either have no results, or the final confidence should be low
        if results:
            # If something matched, the final confidence should be below typical thresholds
            for r in results:
                assert r["final_confidence"] < 0.4, \
                    f"Should not confidently match close-up camera issue: {r}"


# ============================================================
# Test 4: Display
# ============================================================
class TestDisplay:
    def test_screen_flickering(self):
        """'My screen keeps flickering' → display/screen_flicker"""
        cls, results = classify_and_search("My screen keeps flickering")
        assert len(results) >= 1
        assert results[0]["domain"] == "display"
        assert results[0]["issue"] == "screen_flicker"

    def test_flicker_brightness(self):
        """'My screen flickers whenever I change the brightness' → display/screen_flicker"""
        cls, results = classify_and_search("My screen flickers whenever I change the brightness")
        assert len(results) >= 1
        assert results[0]["domain"] == "display"
        assert results[0]["issue"] == "screen_flicker"


# ============================================================
# Test 5: No-match (vague/unsupported)
# ============================================================
class TestNoMatch:
    def test_vague_not_working(self):
        """'My phone is not working properly' → no match"""
        cls, results = classify_and_search("My phone is not working properly")
        assert len(results) == 0

    def test_vague_getting_worse(self):
        """'It's getting worse' → no match"""
        cls, results = classify_and_search("It's getting worse")
        assert len(results) == 0

    def test_unsupported_smell(self):
        """'My phone smells strange' → no match"""
        cls, results = classify_and_search("My phone smells strange")
        assert len(results) == 0

    def test_vague_fix_request(self):
        """'Can you fix my phone?' → no match"""
        cls, results = classify_and_search("Can you fix my phone?")
        assert len(results) == 0


# ============================================================
# Test 6: Multi-issue detection
# ============================================================
class TestMultiIssue:
    def test_flicker_and_battery(self):
        """'My screen is flickering and my battery is draining very fast' → TWO issues"""
        cls, results = classify_and_search(
            "My screen is flickering and my battery is draining very fast"
        )
        domains = {r["domain"] for r in results}
        assert "display" in domains, f"Expected display in results, got {domains}"
        assert "battery" in domains, f"Expected battery in results, got {domains}"
        assert len(results) >= 2

    def test_slow_and_battery(self):
        """'My phone is slow and the battery is also draining quickly' → TWO issues"""
        cls, results = classify_and_search(
            "My phone is slow and the battery is also draining quickly"
        )
        domains = {r["domain"] for r in results}
        assert "performance" in domains, f"Expected performance in results, got {domains}"
        assert "battery" in domains, f"Expected battery in results, got {domains}"
        assert len(results) >= 2


# ============================================================
# Test 7: Confidence validation
# ============================================================
class TestConfidence:
    def test_high_confidence_returns_result(self):
        """A clear query should produce a result with reasonable final confidence."""
        cls, results = classify_and_search("My phone battery is draining very fast")
        assert len(results) >= 1
        assert results[0]["final_confidence"] >= 0.4

    def test_classification_returns_issues_array(self):
        """Classification should return issues array format."""
        cls = simple_keyword_fallback("My battery is dying fast")
        assert hasattr(cls, "issues")
        assert len(cls.issues) >= 1
        assert cls.issues[0].domain == "battery"


# ============================================================
# Test 8: KB retrieval validation
# ============================================================
class TestRetrievalValidation:
    def test_exact_match_high_confidence(self):
        """An exact domain+issue match should have high retrieval confidence."""
        result = search_knowledge("battery", "fast_drain", "battery draining fast")
        assert result is not None
        record, conf = result
        assert conf >= 0.7

    def test_wrong_domain_no_match(self):
        """Searching wrong domain should return None."""
        result = search_knowledge("connectivity", "wifi_slow", "wifi is slow")
        assert result is None

    def test_context_mismatch_penalized(self):
        """A specific context not covered by KB should reduce confidence."""
        result = search_knowledge("camera", "camera_blur", "camera blurry for close-up", context="close_up")
        # Should either be None or have very low confidence
        if result is not None:
            record, conf = result
            assert conf < 0.5, f"Context mismatch should be penalized, got conf={conf}"


# ============================================================
# Test 9: Diagnostic Decision Engine & Conversational Flow
# ============================================================
class TestDiagnosticFlow:
    def test_ambiguous_overheating_triggers_followup(self):
        """Ambiguous query 'My phone is overheating' should return status='follow_up' with session_id."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post("/v1/troubleshoot", json={"query": "My phone is overheating"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "follow_up"
        assert data["session_id"] is not None
        assert data["follow_up"] is not None
        assert "text" in data["follow_up"]
        assert len(data["follow_up"]["options"]) >= 2

    def test_followup_option_selection_resolves_issue(self):
        """Selecting an option in a follow-up session should narrow down and resolve the issue."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        # Step 1: Trigger follow-up
        res1 = client.post("/v1/troubleshoot", json={"query": "My phone is overheating"})
        data1 = res1.json()
        assert data1["status"] == "follow_up"
        session_id = data1["session_id"]

        # Step 2: Select option 0 ("While charging") -> narrows to overheating_while_charging
        res2 = client.post("/v1/troubleshoot", json={
            "query": "My phone is overheating",
            "session_id": session_id,
            "selected_option": 0
        })
        data2 = res2.json()
        assert data2["status"] == "success"
        assert len(data2["results"]) >= 1
        assert data2["results"][0]["domain"] == "battery"
        assert data2["results"][0]["issue"] == "overheating_while_charging"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

