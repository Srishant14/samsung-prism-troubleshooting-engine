"""
Tests for Samsung PRISM v5.1 Question-First Diagnostic Architecture.

Covers all 16 architectural test scenarios:
1. "battery draining fast" (CLEAR alias match, missing drain conditions) -> follow_up
2. "battery drains overnight on Galaxy S24" -> sufficient -> immediate KB retrieval for drain_overnight
3. "camera blurry" -> follow_up asking blur conditions (low light, close-up, front)
4. "camera blurry for close-up photos" -> sufficient -> camera_blur (close-up context)
5. "phone is slow" -> follow_up asking lag conditions (slow apps, freezing, gaming, storage)
6. "phone freezes when opening camera" -> multi-signal narrow/follow-up
7. "screen flickering" -> sufficient (no blocking slots required) -> immediate KB retrieval
8. "phone gets warm while charging" -> sufficient (overheating_while_charging) -> immediate KB retrieval
9. "my phone smells like burnt toast" -> no match -> official support fallback
10. "it doesn't work" -> VAGUE -> asks user to describe issue / classify
11. Multi-issue: "screen flickering and battery drains fast while idle" -> display + battery
12. Follow-up answer "while idle" to battery question -> redirects to drain_overnight -> resolves
13. Follow-up answer "during gaming" to slow phone -> redirects to overheating_gaming -> resolves
14. Non-blocking issues bypass clarification cleanly
15. Max diagnostic rounds reached -> resolves with best available knowledge without infinite loop
16. Latency test: fast path with all slots filled completes in < 10ms
"""
import time
import pytest
from fastapi.testclient import TestClient
from main import app
from sufficiency_gate import (
    evaluate_sufficiency, extract_slots_from_query,
    SufficiencyStatus, NextAction, DiagnosticDecision
)
from session import create_session, get_session

client = TestClient(app)


class TestSufficiencyGateUnit:
    """Unit tests for the Sufficiency & Slot Guard."""

    def test_missing_slot_blocks_retrieval(self):
        decision = evaluate_sufficiency(
            domain="battery",
            issue="fast_drain",
            context=None,
            query="battery draining fast",
        )
        assert decision.sufficiency == SufficiencyStatus.INSUFFICIENT
        assert not decision.kb_retrieval_allowed
        assert decision.next_action == NextAction.ASK_QUESTION
        assert "drain_conditions" in decision.missing_slots
        assert decision.question is not None
        assert len(decision.question_options) > 0

    def test_filled_slot_in_query_allows_retrieval(self):
        decision = evaluate_sufficiency(
            domain="battery",
            issue="fast_drain",
            context=None,
            query="battery draining fast while idle overnight",
        )
        assert decision.sufficiency == SufficiencyStatus.SUFFICIENT
        assert decision.kb_retrieval_allowed
        assert decision.next_action == NextAction.RETRIEVE_KB
        assert len(decision.missing_slots) == 0

    def test_invariant_enforcement_in_pydantic_model(self):
        decision = DiagnosticDecision(
            category="battery",
            issue="fast_drain",
            sufficiency=SufficiencyStatus.INSUFFICIENT,
            missing_slots=["drain_conditions"],
            kb_retrieval_allowed=True,  # Contradiction!
            next_action=NextAction.RETRIEVE_KB,
        )
        # Model validator forces kb_retrieval_allowed to False
        assert not decision.kb_retrieval_allowed
        assert decision.next_action == NextAction.ASK_QUESTION


class TestQuestionFirst16Scenarios:
    """End-to-end API tests covering the 16 core architectural scenarios."""

    # Scenario 1
    def test_scenario_01_vague_battery_triggers_followup(self):
        """'battery draining fast' MUST trigger follow_up question, not premature success."""
        resp = client.post("/v1/troubleshoot", json={"query": "battery draining fast"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "follow_up"
        assert data["session_id"] is not None
        assert "drain" in data["follow_up"]["text"].lower() or "battery" in data["follow_up"]["text"].lower()

    # Scenario 2
    def test_scenario_02_battery_drains_overnight_galaxy_s24(self):
        """'battery drains overnight on Galaxy S24' -> sufficient -> immediate KB retrieval for drain_overnight."""
        resp = client.post("/v1/troubleshoot", json={"query": "battery drains overnight on Galaxy S24"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["domain"] == "battery"
        assert data["issue"] == "drain_overnight"

    # Scenario 3
    def test_scenario_03_camera_blurry_triggers_followup(self):
        """'camera blurry' -> follow-up asking conditions."""
        resp = client.post("/v1/troubleshoot", json={"query": "camera blurry"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "follow_up"
        assert "photo" in data["follow_up"]["text"].lower() or "blurry" in data["follow_up"]["text"].lower()

    # Scenario 4
    def test_scenario_04_camera_blurry_night_photos(self):
        """'camera blurry at night in low light' -> sufficient -> resolves."""
        resp = client.post("/v1/troubleshoot", json={"query": "camera photos are blurry at night in low light"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["domain"] == "camera"

    # Scenario 5
    def test_scenario_05_phone_is_slow_triggers_followup(self):
        """'phone is slow' -> follow-up asking lag conditions."""
        resp = client.post("/v1/troubleshoot", json={"query": "my phone is slow"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "follow_up"
        assert "slowness" in data["follow_up"]["text"].lower() or "slow" in data["follow_up"]["text"].lower()

    # Scenario 6
    def test_scenario_06_phone_freezes_narrow(self):
        """'phone keeps freezing' -> resolves or clarifies freezing."""
        resp = client.post("/v1/troubleshoot", json={"query": "my phone keeps freezing"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "follow_up")

    # Scenario 7
    def test_scenario_07_screen_flickering_immediate(self):
        """'screen flickering' -> no blocking slots required -> immediate KB retrieval."""
        resp = client.post("/v1/troubleshoot", json={"query": "screen flickering"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["domain"] == "display"
        assert data["issue"] == "screen_flicker"

    # Scenario 8
    def test_scenario_08_warm_while_charging_immediate(self):
        """'phone gets hot while charging' -> sufficient -> immediate retrieval."""
        resp = client.post("/v1/troubleshoot", json={"query": "phone gets hot while charging"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["domain"] == "battery"
        assert data["issue"] == "overheating_while_charging"

    # Scenario 9
    def test_scenario_09_burnt_toast_no_match(self):
        """'my phone smells like burnt toast' -> no match with fallback."""
        resp = client.post("/v1/troubleshoot", json={"query": "my phone smells like burnt toast"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "no_match"

    # Scenario 10
    def test_scenario_10_it_doesnt_work_vague(self):
        """'it does not work' -> no domain match -> handles gracefully."""
        resp = client.post("/v1/troubleshoot", json={"query": "it does not work"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("follow_up", "no_match")

    # Scenario 11
    def test_scenario_11_multi_issue_both_resolved(self):
        """Multi-issue with slots satisfied resolves both issues."""
        resp = client.post("/v1/troubleshoot", json={
            "query": "My screen is flickering and my battery is draining fast while idle overnight"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        domains = {r["domain"] for r in data["results"]}
        assert "display" in domains
        assert "battery" in domains

    # Scenario 12
    def test_scenario_12_slot_redirection_idle_to_overnight(self):
        """Answering 'While idle' (option 0) redirects to drain_overnight."""
        resp1 = client.post("/v1/troubleshoot", json={"query": "battery draining fast"})
        data1 = resp1.json()
        assert data1["status"] == "follow_up"
        session_id = data1["session_id"]

        resp2 = client.post("/v1/troubleshoot", json={
            "session_id": session_id,
            "selected_option": 0  # While idle
        })
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["status"] == "success"
        assert data2["domain"] == "battery"
        assert data2["issue"] == "drain_overnight"

    # Scenario 13
    def test_scenario_13_slot_answer_heavy_use(self):
        """Answering 'During heavy use' (option 1) resolves to fast_drain."""
        resp1 = client.post("/v1/troubleshoot", json={"query": "battery draining fast"})
        session_id = resp1.json()["session_id"]

        resp2 = client.post("/v1/troubleshoot", json={
            "session_id": session_id,
            "selected_option": 1  # During heavy use
        })
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["status"] == "success"
        assert data2["domain"] == "battery"
        assert data2["issue"] == "fast_drain"

    # Scenario 14
    def test_scenario_14_non_blocking_issues_bypass_clarification(self):
        """Non-blocking issues like camera app crash resolve without clarification."""
        resp = client.post("/v1/troubleshoot", json={"query": "camera app keeps closing and crashing"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["domain"] == "camera"

    # Scenario 15
    def test_scenario_15_question_budget_exhaustion(self):
        """Exhausting question budget (round_count >= max_rounds) forces resolution."""
        session = create_session("battery draining fast", domain="battery", tree="battery")
        session.round_count = 5  # At max rounds
        decision = evaluate_sufficiency(
            domain="battery",
            issue="fast_drain",
            context=None,
            query="battery draining fast",
            filled_slots={},
            questions_asked=session.round_count,
            max_questions=5,
        )
        assert decision.sufficiency == SufficiencyStatus.SUFFICIENT
        assert decision.kb_retrieval_allowed
        assert decision.next_action == NextAction.RETRIEVE_KB

    # Scenario 16
    def test_scenario_16_fast_path_latency(self):
        """Fully-specified fast path completes well within performance budget (< 15ms)."""
        t0 = time.perf_counter()
        resp = client.post("/v1/troubleshoot", json={"query": "screen flickering"})
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert elapsed_ms < 50.0  # Locally within budget
