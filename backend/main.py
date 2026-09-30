"""
Main FastAPI application — Smart Guided Troubleshooting Engine v5.0

Architecture (v5.0 — Question-First Diagnostic Engine):

  User Query
       │
       ▼
  FAST LOCAL GATE (< 1ms, no LLM, no Laya)
       │
  ┌────┼────────────┐
  │    │             │
 CLEAR PARTIAL    VAGUE
  │    │             │
  ▼    ▼             ▼
FAST  FOLLOW-UP   LLM FALLBACK
 KB   QUESTION      │
  │    │             ▼
  │    ▼         DIAGNOSTIC
  │  DIAG STATE     STATE
  │    │             │
  │    ▼             ▼
  │  LAYA          LAYA
  │  (only when   (only when
  │   needed)      needed)
  │    │             │
  └────┼─────────────┘
       ▼
  VERIFICATION
       │
       ▼
  VERIFIED RESULT

Core principles:
  - Fast path by default (CLEAR queries skip LLM and Laya entirely)
  - Ask questions when information is missing (question-first UX)
  - Use Laya for decision-making (not classification)
  - Use LLM only when local understanding fails (fallback)
  - Never generate unverified troubleshooting advice
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager

from schemas import (
    TroubleshootRequest, TroubleshootResponse,
    ActionLink, IssueResult, FollowUpQuestion, FollowUpOption,
)
from fast_gate import fast_gate, preprocess_signal, PreprocessedSignal, GateVerdict, Specificity
from classifier import classify_complaint
from knowledge_base import (
    search_knowledge, get_supported_issues,
    get_issue_criteria, has_exact_kb_record,
)
from serp_fallback import search_official_support
from diagnostic_flow import (
    detect_ambiguous_pattern, get_question, apply_option,
    get_entry_tree_for_domain,
)
from decision_engine import (
    decide_diagnostic_step,
    decide_domain, decide_issue, decide_sufficient_evidence,
    decide_next_action,
)
from sufficiency_gate import (
    evaluate_sufficiency, process_slot_answer, validate_decision,
    DiagnosticDecision, NextAction, SufficiencyStatus,
)
from session import create_session, get_session, delete_session, has_rounds_left
from config import CONFIDENCE_THRESHOLD, FAST_PATH_CONFIDENCE
from logger import log_request
from perf import RequestMetrics, aggregate_stats

app = FastAPI(title="Smart Guided Troubleshooting Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FINAL_CONFIDENCE_THRESHOLD = 0.4
MAX_DIAGNOSTIC_STEPS = 5


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "troubleshoot-engine", "version": "5.0.0"}


@app.get("/v1/perf")
@app.get("/api/v1/perf")
def perf_stats():
    """Lightweight performance stats endpoint for benchmarking."""
    return aggregate_stats.summary()


@app.get("/3d")
@app.get("/api/3d")
@app.get("/architecture")
def get_3d_architecture():
    """Serve the interactive 3D WebGL topology visualizer."""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "project-3d-architecture.html"))
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    raise HTTPException(status_code=404, detail="3D Architecture file not found")


@app.get("/2d")
@app.get("/api/2d")
def get_2d_architecture():
    """Serve the Archify 2D blueprint diagram."""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samsung-prism-architecture.html"))
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    raise HTTPException(status_code=404, detail="2D Architecture file not found")


# ============================================================
# No-op context manager for when metrics is None
# ============================================================

@contextmanager
def _noop_ctx():
    yield


# ============================================================
# Helper: Build a follow-up question response
# ============================================================

def _build_followup_response(
    session, tree_name: str, node_name: str,
    category: str = None, category_confidence: float = None,
) -> TroubleshootResponse:
    """Build a follow-up question response from a diagnostic tree node."""
    question_data = get_question(tree_name, node_name)
    if not question_data:
        delete_session(session.session_id)
        return TroubleshootResponse(
            status="no_match",
            message="We couldn't determine the right follow-up question. Please describe your issue differently.",
        )

    options = [
        FollowUpOption(label=opt["label"], index=idx)
        for idx, opt in enumerate(question_data["options"])
    ]

    # Track the question in session state
    session.questions_asked.append(question_data["text"])

    cat = category or session.current_domain or (tree_name if tree_name != "general" else None)
    cat_conf = category_confidence or (0.85 if cat else None)

    return TroubleshootResponse(
        status="follow_up",
        session_id=session.session_id,
        follow_up=FollowUpQuestion(
            text=question_data["text"],
            options=options,
            round_number=session.round_count + 1,
            max_rounds=MAX_DIAGNOSTIC_STEPS,
            category=cat.capitalize() if cat else None,
            category_confidence=round(cat_conf, 2) if cat_conf else None,
        ),
    )


# ============================================================
# Helper: Build a slot-based follow-up question response
# ============================================================

def _build_slot_followup_response(
    session, decision: DiagnosticDecision,
) -> TroubleshootResponse:
    """Build a follow-up question response from a sufficiency gate decision.

    Uses the same FollowUpQuestion format as tree-based questions for
    frontend compatibility with FollowUpCard.jsx.
    """
    if not decision.question or not decision.question_options:
        # Fallback: no slot question available, try tree-based
        tree_name = get_entry_tree_for_domain(decision.category)
        if tree_name:
            session.current_tree = tree_name
            session.question_source = "tree"
            return _build_followup_response(
                session, tree_name, "entry_question",
                category=decision.category,
                category_confidence=decision.category_confidence,
            )
        return TroubleshootResponse(
            status="no_match",
            message="We couldn't determine the right follow-up question. Please describe your issue differently.",
        )

    options = [
        FollowUpOption(label=opt["label"], index=idx)
        for idx, opt in enumerate(decision.question_options)
    ]

    # Track in session
    session.questions_asked.append(decision.question)
    session.pending_slot_question = decision.missing_slots[0] if decision.missing_slots else None
    session.slot_question_options = decision.question_options
    session.question_source = "slot"

    cat = decision.category
    cat_conf = decision.category_confidence

    return TroubleshootResponse(
        status="follow_up",
        session_id=session.session_id,
        follow_up=FollowUpQuestion(
            text=decision.question,
            options=options,
            round_number=session.round_count + 1,
            max_rounds=MAX_DIAGNOSTIC_STEPS,
            category=cat.capitalize() if cat else None,
            category_confidence=round(cat_conf, 2) if cat_conf else None,
        ),
    )


# ============================================================
# Helper: Resolve an issue through the KB
# ============================================================

def _resolve_issue(
    domain: str, issue: str, query: str,
    context: str = None, confidence: float = 0.85,
    metrics: RequestMetrics = None,
) -> TroubleshootResponse:
    """Look up a resolved issue in the KB and return the response."""
    if metrics:
        metrics.increment("kb_searches")

    with (metrics.measure("kb_lookup") if metrics else _noop_ctx()):
        kb_result = search_knowledge(
            domain=domain, issue=issue, query=query, context=context,
        )

    if kb_result:
        record, match_confidence = kb_result
        final_confidence = confidence * match_confidence

        if final_confidence >= FINAL_CONFIDENCE_THRESHOLD:
            action = None
            if (record.get("action_label")
                    and record.get("deep_link")
                    and record.get("action_verified", False)):
                action = ActionLink(
                    label=record["action_label"],
                    deep_link=record["deep_link"],
                )

            result = IssueResult(
                domain=domain,
                issue=issue,
                confidence=round(confidence, 2),
                match_confidence=round(match_confidence, 2),
                final_confidence=round(final_confidence, 2),
                title=record.get("title"),
                steps=record.get("steps"),
                action=action,
                source=record.get("source"),
                source_type=record.get("source_type"),
            )

            return TroubleshootResponse(
                status="success",
                results=[result],
                domain=domain, issue=issue,
                confidence=round(final_confidence, 2),
                title=record.get("title"),
                steps=record.get("steps"),
                action=action,
                source=record.get("source"),
                source_type=record.get("source_type"),
            )

    return TroubleshootResponse(
        status="no_match",
        message="We couldn't find a verified troubleshooting procedure for this specific issue.",
    )


# ============================================================
# Helper: Resolve multiple issues concurrently
# ============================================================

def _resolve_multi_issues(
    issues: list, query: str, metrics: RequestMetrics = None,
) -> TroubleshootResponse:
    """Resolve multiple clear issues from the fast gate."""
    results = []
    for item in issues:
        domain = item["domain"]
        issue = item["issue"]
        context = item.get("context")

        if metrics:
            metrics.increment("kb_searches")

        with (metrics.measure("kb_lookup") if metrics else _noop_ctx()):
            kb_result = search_knowledge(
                domain=domain, issue=issue, query=query, context=context,
            )

        if kb_result:
            record, match_confidence = kb_result
            final_confidence = 0.85 * match_confidence

            if final_confidence >= FINAL_CONFIDENCE_THRESHOLD:
                action = None
                if (record.get("action_label")
                        and record.get("deep_link")
                        and record.get("action_verified", False)):
                    action = ActionLink(
                        label=record["action_label"],
                        deep_link=record["deep_link"],
                    )

                results.append(IssueResult(
                    domain=domain,
                    issue=issue,
                    confidence=0.85,
                    match_confidence=round(match_confidence, 2),
                    final_confidence=round(final_confidence, 2),
                    title=record.get("title"),
                    steps=record.get("steps"),
                    action=action,
                    source=record.get("source"),
                    source_type=record.get("source_type"),
                ))

    if results:
        first = results[0]
        return TroubleshootResponse(
            status="success",
            results=results,
            domain=first.domain, issue=first.issue,
            confidence=first.final_confidence,
            title=first.title, steps=first.steps,
            action=first.action,
            source=first.source, source_type=first.source_type,
        )

    return TroubleshootResponse(
        status="no_match",
        message="We couldn't find verified troubleshooting procedures for these issues.",
    )


# ============================================================
# Helper: Run the Laya-powered diagnostic loop (LLM fallback)
# ============================================================

def _run_laya_diagnosis(query: str, classification, metrics: RequestMetrics = None) -> TroubleshootResponse:
    """
    Use Laya to make structured decisions about classification.

    This is now the FALLBACK path — only called when the fast gate
    cannot resolve the query locally.
    """
    # Extract symptoms from LLM classification
    valid_issues = [
        issue for issue in classification.issues
        if issue.confidence >= CONFIDENCE_THRESHOLD and issue.domain != "unknown"
    ]

    symptoms = []
    contexts = []
    for vi in valid_issues:
        symptoms.append(f"{vi.domain}/{vi.issue}")
        if vi.context:
            contexts.append(vi.context)

    # --- Decision A: Domain ---
    if metrics:
        metrics.increment("laya_calls")
    with (metrics.measure("laya_domain") if metrics else _noop_ctx()):
        domain_decision = decide_domain(symptoms, query)
    domain = domain_decision["domain"]

    if domain == "unknown" or domain_decision["confidence"] < 0.3:
        return None  # Caller will handle

    # --- Decision B: Issue ---
    issue_criteria = get_issue_criteria(domain)
    if not issue_criteria:
        return None

    if metrics:
        metrics.increment("laya_calls")
    with (metrics.measure("laya_issue") if metrics else _noop_ctx()):
        issue_decision = decide_issue(domain, symptoms, query, issue_criteria)
    issue = issue_decision["issue"]
    if issue == "unknown" or issue_decision.get("confidence", 0.0) < 0.3:
        return None

    # --- Decision C: Sufficient evidence? ---
    candidate_issues = [f"{domain}/{issue}"] if issue != "unknown" else []

    if issue == "unknown" or not candidate_issues:
        if metrics:
            metrics.increment("laya_calls")
        with (metrics.measure("laya_evidence") if metrics else _noop_ctx()):
            decide_sufficient_evidence(
                symptoms, contexts, candidate_issues, query,
            )

    # --- Decision D: Next action ---
    # CHANGED (v5.1): Evaluate sufficiency BEFORE KB lookup.
    # Old code fetched KB here unconditionally (Root Cause 4).
    with metrics.measure("sufficiency_check") if metrics else _noop_ctx():
        suff_decision = evaluate_sufficiency(
            domain=domain,
            issue=issue,
            context=contexts[0] if contexts else None,
            query=query,
            gate_confidence=max(
                domain_decision["confidence"],
                issue_decision["confidence"],
            ),
        )

    # Use has_exact_kb_record (O(1) index check) instead of
    # search_knowledge (which actually retrieves data).
    has_kb_match = has_exact_kb_record(
        suff_decision.category, suff_decision.issue,
    )

    if metrics:
        metrics.increment("laya_calls")
    with (metrics.measure("laya_action") if metrics else _noop_ctx()):
        action_decision = decide_next_action(
            symptoms=symptoms,
            contexts=contexts,
            candidate_issues=candidate_issues,
            confirmed_issues=[],
            questions_asked=0,
            has_kb_match=has_kb_match,
            query=query,
        )

    action = action_decision["action"]

    # --- Execute decision ---
    # INVARIANT: KB retrieval requires sufficiency gate approval
    if action in ("RESOLVE", "LOOKUP_KNOWLEDGE") and suff_decision.kb_retrieval_allowed:
        return _resolve_issue(
            domain=suff_decision.category,
            issue=suff_decision.issue,
            query=query,
            confidence=max(domain_decision["confidence"], issue_decision["confidence"]),
            metrics=metrics,
        )

    if action in ("RESOLVE", "LOOKUP_KNOWLEDGE") and not suff_decision.kb_retrieval_allowed:
        # Laya wants to resolve but sufficiency says no — ask question
        tree_name = get_entry_tree_for_domain(domain)
        if tree_name:
            session = create_session(
                original_query=query,
                domain=domain,
                tree=tree_name,
                symptoms=symptoms,
            )
            session.current_domain = domain
            session.current_issue = issue if issue != "unknown" else None
            session.contexts = contexts
            session.filled_slots = suff_decision.filled_slots
            session.actions_taken.append(
                f"Laya→{action}→sufficiency_blocked"
            )
            return _build_slot_followup_response(session, suff_decision)

    if action == "ASK_USER":
        tree_name = get_entry_tree_for_domain(domain)
        if tree_name:
            session = create_session(
                original_query=query,
                domain=domain,
                tree=tree_name,
                symptoms=symptoms,
            )
            session.current_domain = domain
            session.current_issue = issue if issue != "unknown" else None
            session.contexts = contexts
            session.actions_taken.append(f"Laya→ASK_USER (domain={domain})")
            return _build_followup_response(session, tree_name, "entry_question")

    if action == "NO_MATCH":
        return None

    # Default: try KB lookup only if sufficiency allows
    if suff_decision.kb_retrieval_allowed and has_kb_match:
        return _resolve_issue(
            domain=suff_decision.category,
            issue=suff_decision.issue,
            query=query, metrics=metrics,
        )

    return None


# ============================================================
# Main endpoint
# ============================================================

@app.post("/v1/troubleshoot", response_model=TroubleshootResponse)
@app.post("/api/v1/troubleshoot", response_model=TroubleshootResponse)
def troubleshoot(request: TroubleshootRequest):
    """
    Main troubleshooting endpoint — v5.0 Question-First Diagnostic Engine.

    Flow:
    1. Session continuation (if session_id provided)
    2. Fast Local Gate (deterministic, < 1ms)
       - CLEAR → fast KB lookup → verified result
       - PARTIAL → predefined follow-up question
       - VAGUE → LLM fallback → diagnostic engine
    3. Verification layer
    4. Response
    """
    metrics = RequestMetrics()
    query = request.query.strip() if request.query else ""

    # ========================================================
    # CASE 1: Continuing an existing diagnostic session
    # ========================================================
    if request.session_id and request.selected_option is not None:
        metrics.set_path("session_continuation")
        session = get_session(request.session_id)
        if not session:
            aggregate_stats.record(metrics)
            return TroubleshootResponse(
                status="no_match",
                message="Your session has expired. Please describe your issue again.",
            )

        session.round_count += 1
        session.answers.append(str(request.selected_option))

        # ── CASE 1a: Slot-based follow-up answer ──
        if session.question_source == "slot" and session.pending_slot_question:
            slot_name = session.pending_slot_question
            with metrics.measure("slot_processing"):
                slot_result = process_slot_answer(
                    slot_name=slot_name,
                    option_index=request.selected_option,
                    current_domain=session.current_domain or "",
                    current_issue=session.current_issue or "",
                )

            if slot_result.get("error"):
                delete_session(session.session_id)
                aggregate_stats.record(metrics)
                return TroubleshootResponse(
                    status="no_match",
                    message="Something went wrong. Please describe your issue again.",
                )

            # Fill the slot
            session.fill_slot(slot_name, slot_result["slot_value"])
            session.pending_slot_question = None
            session.slot_question_options = None
            session.actions_taken.append(
                f"slot_fill→{slot_name}={slot_result['slot_value']}"
            )

            # Apply redirection if the answer changes the issue
            if slot_result.get("redirected_issue"):
                session.current_issue = slot_result["redirected_issue"]
                if slot_result.get("redirected_domain"):
                    session.current_domain = slot_result["redirected_domain"]
                session.actions_taken.append(
                    f"redirect→{session.current_domain}/{session.current_issue}"
                )

            # Re-evaluate sufficiency with updated slots
            with metrics.measure("sufficiency_check"):
                decision = evaluate_sufficiency(
                    domain=session.current_domain,
                    issue=session.current_issue,
                    context=None,
                    query=session.original_query,
                    filled_slots=session.filled_slots,
                    gate_confidence=0.85,
                    questions_asked=session.round_count,
                )

            if decision.kb_retrieval_allowed:
                # Sufficient — retrieve from KB
                delete_session(session.session_id)
                resp = _resolve_issue(
                    domain=decision.category,
                    issue=decision.issue,
                    query=session.original_query,
                    context=decision.context,
                    confidence=decision.category_confidence,
                    metrics=metrics,
                )
                aggregate_stats.record(metrics)
                return resp
            else:
                # Still insufficient — ask the next slot question
                if has_rounds_left(session):
                    resp = _build_slot_followup_response(session, decision)
                    aggregate_stats.record(metrics)
                    return resp
                else:
                    # Budget exhausted — try KB with what we have
                    delete_session(session.session_id)
                    resp = _resolve_issue(
                        domain=session.current_domain,
                        issue=session.current_issue,
                        query=session.original_query,
                        confidence=0.70,
                        metrics=metrics,
                    )
                    aggregate_stats.record(metrics)
                    return resp

        # ── CASE 1b: Tree-based follow-up answer (existing logic) ──
        result = apply_option(
            session.current_tree,
            session.current_node,
            request.selected_option,
        )

        if result.get("error"):
            delete_session(session.session_id)
            aggregate_stats.record(metrics)
            return TroubleshootResponse(
                status="no_match",
                message="Something went wrong. Please describe your issue again.",
            )

        # Option switches to a different tree
        if "sets_tree" in result and result.get("next_tree"):
            session.current_tree = result.get("next_tree", result.get("sets_tree"))
            session.current_node = result.get("next_node", "entry_question")
            if result.get("domain"):
                session.current_domain = result["domain"]
            session.actions_taken.append(f"tree_switch→{session.current_tree}")
            session.question_source = "tree"
            resp = _build_followup_response(session, session.current_tree, session.current_node)
            aggregate_stats.record(metrics)
            return resp

        # Update session state
        if result.get("domain"):
            session.current_domain = result["domain"]
        if result.get("issue"):
            session.current_issue = result["issue"]
            session.add_candidate(result["domain"] or session.current_domain, result["issue"])
        if result.get("context"):
            session.add_context(result["context"])

        # Check if resolved by the tree
        if result.get("resolved"):
            # ── SUFFICIENCY GUARD: evaluate before KB retrieval ──
            with metrics.measure("sufficiency_check"):
                decision = evaluate_sufficiency(
                    domain=session.current_domain,
                    issue=session.current_issue,
                    context=result.get("context"),
                    query=session.original_query,
                    filled_slots=session.filled_slots,
                    gate_confidence=0.90,
                    questions_asked=session.round_count,
                )

            if decision.kb_retrieval_allowed:
                delete_session(session.session_id)
                resp = _resolve_issue(
                    domain=decision.category,
                    issue=decision.issue,
                    query=session.original_query,
                    context=result.get("context"),
                    confidence=decision.category_confidence,
                    metrics=metrics,
                )
                aggregate_stats.record(metrics)
                return resp
            else:
                # Tree says resolved, but sufficiency gate wants more info
                if has_rounds_left(session):
                    session.actions_taken.append("tree_resolved→sufficiency_insufficient")
                    resp = _build_slot_followup_response(session, decision)
                    aggregate_stats.record(metrics)
                    return resp
                # Budget exhausted — proceed anyway
                delete_session(session.session_id)
                resp = _resolve_issue(
                    domain=session.current_domain,
                    issue=session.current_issue,
                    query=session.original_query,
                    context=result.get("context"),
                    confidence=0.80,
                    metrics=metrics,
                )
                aggregate_stats.record(metrics)
                return resp

        # Not resolved yet — ask the next follow-up question
        if result.get("next_node") and has_rounds_left(session):
            session.current_tree = result.get("next_tree", session.current_tree)
            session.current_node = result["next_node"]
            session.question_source = "tree"
            resp = _build_followup_response(session, session.current_tree, session.current_node)
            aggregate_stats.record(metrics)
            return resp

        # Out of rounds or no next question
        delete_session(session.session_id)
        if session.current_domain and session.current_issue:
            resp = _resolve_issue(
                domain=session.current_domain,
                issue=session.current_issue,
                query=session.original_query,
                confidence=0.80,
                metrics=metrics,
            )
            aggregate_stats.record(metrics)
            return resp
        aggregate_stats.record(metrics)
        return TroubleshootResponse(
            status="no_match",
            message="We couldn't narrow down the issue. Please try describing your problem differently.",
        )

    # ========================================================
    # CASE 2: New query — FAST LOCAL GATE FIRST
    # ========================================================
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(query) > 500:
        raise HTTPException(status_code=400, detail="Query is too long (max 500 characters).")

    try:
        # ─── STEP 1: Fast Local Gate Preprocessing (< 0.5ms, no LLM) ───
        with metrics.measure("fast_gate"):
            signal = preprocess_signal(query)
            gate_result = signal.raw_gate_result

        # ─── STEP 2: Route based on verdict ───

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PATH A: CLEAR — Sufficiency check → fast resolve
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if gate_result.verdict == GateVerdict.CLEAR:

            # Multi-issue: evaluate sufficiency for each issue
            if gate_result.multi_issues:
                all_sufficient = True
                for mi in gate_result.multi_issues:
                    with metrics.measure("sufficiency_check"):
                        mi_decision = evaluate_sufficiency(
                            domain=mi["domain"],
                            issue=mi["issue"],
                            context=mi.get("context"),
                            query=query,
                            gate_confidence=0.85,
                        )
                    if not mi_decision.kb_retrieval_allowed:
                        all_sufficient = False
                        break

                if all_sufficient:
                    metrics.set_path("fast_path_multi")
                    resp = _resolve_multi_issues(gate_result.multi_issues, query, metrics)
                    log_request(
                        query=query, classification=None,
                        final_status=resp.status,
                    )
                    aggregate_stats.record(metrics)
                    return resp
                # else: fall through to single-issue sufficiency below

            # ── DETERMINISTIC SUFFICIENCY CHECK (ZERO LLM, ZERO LAYA) ──
            # For CLEAR queries, Fast Gate has already determined domain and issue.
            # We evaluate sufficiency deterministically without neural models (< 1ms).
            with metrics.measure("sufficiency_check"):
                decision = evaluate_sufficiency(
                    domain=gate_result.domain,
                    issue=gate_result.issue,
                    context=gate_result.context,
                    query=query,
                    filled_slots=signal.apparent_slots or {},
                    gate_confidence=gate_result.confidence or 0.85,
                )
                decision = validate_decision(decision)

            if decision.kb_retrieval_allowed:
                # Sufficient — fast path KB retrieval (< 1ms, 0 LLM, 0 Laya)
                metrics.set_path("fast_path")
                resp = _resolve_issue(
                    domain=decision.category,
                    issue=decision.issue,
                    query=query,
                    context=decision.context,
                    confidence=decision.category_confidence,
                    metrics=metrics,
                )

                if resp.status == "success":
                    log_request(
                        query=query, classification=None,
                        final_status="success",
                    )
                    aggregate_stats.record(metrics)
                    return resp

                # KB had no match — fall through to PARTIAL path
                metrics.set_path("fast_path_fallback")
            else:
                # Insufficient — ask a slot question
                metrics.set_path("sufficiency_question")
                session = create_session(
                    original_query=query,
                    domain=decision.category,
                    tree=decision.category,
                )
                session.current_domain = decision.category
                session.current_issue = decision.issue
                session.filled_slots = decision.filled_slots
                session.actions_taken.append(
                    f"fast_gate→insufficient (missing={decision.missing_slots})"
                )

                log_request(
                    query=query, classification=None,
                    final_status="follow_up",
                    no_match_reason=f"Sufficiency check failed: missing {decision.missing_slots}",
                )
                resp = _build_slot_followup_response(session, decision)
                aggregate_stats.record(metrics)
                return resp

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PATH B: PARTIAL — Ask a follow-up question
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if gate_result.verdict == GateVerdict.PARTIAL:
            metrics.set_path("follow_up_question")
            tree_name = gate_result.tree
            if tree_name:
                session = create_session(
                    original_query=query,
                    domain=gate_result.domain,
                    tree=tree_name,
                )
                if gate_result.domain:
                    session.current_domain = gate_result.domain
                if gate_result.issue:
                    session.current_issue = gate_result.issue
                session.question_source = "tree"
                session.actions_taken.append(
                    f"fast_gate→PARTIAL (tree={tree_name}, "
                    f"specificity={gate_result.specificity.value})"
                )

                log_request(
                    query=query, classification=None,
                    final_status="follow_up",
                    no_match_reason=f"Fast gate PARTIAL → tree={tree_name}",
                )
                resp = _build_followup_response(
                    session, tree_name, "entry_question",
                    category=gate_result.domain,
                    category_confidence=gate_result.confidence,
                )
                aggregate_stats.record(metrics)
                return resp

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PATH C: VAGUE / AMBIGUOUS — LAYA PRIMARY DECISION ENGINE FIRST
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 3a: Laya evaluates the preprocessed signal first (<12ms)
        metrics.increment("laya_calls")
        with metrics.measure("laya_decision"):
            laya_decision = decide_diagnostic_step(signal)

        with metrics.measure("sufficiency_check"):
            laya_decision = validate_decision(laya_decision)

        # Case C1: Laya resolves domain and specific issue
        if laya_decision.category and laya_decision.issue:
            if laya_decision.kb_retrieval_allowed:
                metrics.set_path("laya_resolved")
                resp = _resolve_issue(
                    domain=laya_decision.category,
                    issue=laya_decision.issue,
                    query=query,
                    context=laya_decision.context,
                    confidence=laya_decision.category_confidence,
                    metrics=metrics,
                )
                if resp.status == "success":
                    log_request(
                        query=query, classification=None,
                        final_status="success",
                    )
                    aggregate_stats.record(metrics)
                    return resp
            elif laya_decision.missing_slots:
                metrics.set_path("laya_sufficiency_question")
                session = create_session(
                    original_query=query,
                    domain=laya_decision.category,
                    tree=laya_decision.category,
                )
                session.current_domain = laya_decision.category
                session.current_issue = laya_decision.issue
                session.filled_slots = laya_decision.filled_slots
                session.actions_taken.append(
                    f"laya→insufficient (missing={laya_decision.missing_slots})"
                )
                log_request(
                    query=query, classification=None,
                    final_status="follow_up",
                    no_match_reason=f"Laya sufficiency check: missing {laya_decision.missing_slots}",
                )
                resp = _build_slot_followup_response(session, laya_decision)
                aggregate_stats.record(metrics)
                return resp

        # Case C2: Laya identifies domain, but issue needs diagnostic tree narrowing
        elif laya_decision.category and not laya_decision.issue:
            tree_name = get_entry_tree_for_domain(laya_decision.category) or laya_decision.category
            metrics.set_path("laya_diagnostic_tree")
            session = create_session(query, domain=laya_decision.category, tree=tree_name)
            session.current_domain = laya_decision.category
            session.actions_taken.append(f"laya→domain_tree={tree_name}")
            log_request(
                query=query, classification=None,
                final_status="follow_up",
                no_match_reason=f"Laya domain identified ({laya_decision.category}), issue ambiguous",
            )
            resp = _build_followup_response(session, tree_name, "entry_question")
            aggregate_stats.record(metrics)
            return resp

        # Step 3b: Exceptional Fallback — Laya cannot categorize; invoke Gemini LLM
        metrics.set_path("llm_fallback")
        metrics.increment("llm_calls")
        with metrics.measure("llm_classify"):
            classification = classify_complaint(query)

        # Step 3c: Filter valid issues from LLM
        valid_issues = [
            issue for issue in classification.issues
            if issue.confidence >= CONFIDENCE_THRESHOLD and issue.domain != "unknown"
        ]

        # Step 3d: Try LLM classification → sufficiency check → KB lookup
        if valid_issues:
            results = []
            kb_candidates = []
            no_match_reasons = []
            first_insufficient_decision = None

            for issue_cls in valid_issues:
                # ── SUFFICIENCY GUARD ──
                with metrics.measure("sufficiency_check"):
                    issue_decision = evaluate_sufficiency(
                        domain=issue_cls.domain,
                        issue=issue_cls.issue,
                        context=issue_cls.context,
                        query=query,
                        gate_confidence=issue_cls.confidence,
                    )

                if not issue_decision.kb_retrieval_allowed:
                    no_match_reasons.append(
                        f"{issue_cls.domain}/{issue_cls.issue}: "
                        f"insufficient (missing={issue_decision.missing_slots})"
                    )
                    if first_insufficient_decision is None:
                        first_insufficient_decision = issue_decision
                    continue

                # Sufficiency passed — KB retrieval permitted
                metrics.increment("kb_searches")
                with metrics.measure("kb_lookup"):
                    kb_result = search_knowledge(
                        domain=issue_decision.category,
                        issue=issue_decision.issue,
                        query=query, context=issue_cls.context,
                    )
                if kb_result:
                    record, match_confidence = kb_result
                    kb_candidates.append(record)
                    final_confidence = issue_cls.confidence * match_confidence

                    if final_confidence < FINAL_CONFIDENCE_THRESHOLD:
                        no_match_reasons.append(
                            f"{issue_cls.domain}/{issue_cls.issue}: "
                            f"final_conf={final_confidence:.2f} below threshold"
                        )
                        continue

                    action = None
                    if (record.get("action_label")
                            and record.get("deep_link")
                            and record.get("action_verified", False)):
                        action = ActionLink(
                            label=record["action_label"],
                            deep_link=record["deep_link"],
                        )

                    results.append(IssueResult(
                        domain=issue_cls.domain,
                        issue=issue_decision.issue,
                        confidence=round(issue_cls.confidence, 2),
                        match_confidence=round(match_confidence, 2),
                        final_confidence=round(final_confidence, 2),
                        title=record.get("title"),
                        steps=record.get("steps"),
                        action=action,
                        source=record.get("source"),
                        source_type=record.get("source_type"),
                    ))
                else:
                    no_match_reasons.append(
                        f"{issue_cls.domain}/{issue_cls.issue}: no KB record found"
                    )

            # Direct hit from LLM classification
            if results:
                first = results[0]
                log_request(
                    query=query, classification=classification,
                    kb_candidates=kb_candidates,
                    selected_results=[r.model_dump() for r in results],
                    final_status="success",
                )
                resp = TroubleshootResponse(
                    status="success",
                    results=results,
                    domain=first.domain, issue=first.issue,
                    confidence=first.final_confidence,
                    title=first.title, steps=first.steps,
                    action=first.action,
                    source=first.source, source_type=first.source_type,
                )
                aggregate_stats.record(metrics)
                return resp

            # If insufficiency blocked retrieval, ask a slot question
            if first_insufficient_decision:
                domain = first_insufficient_decision.category
                session = create_session(query, domain=domain, tree=domain)
                session.current_domain = domain
                session.current_issue = first_insufficient_decision.issue
                session.filled_slots = first_insufficient_decision.filled_slots
                session.actions_taken.append("llm→sufficiency_insufficient")
                log_request(
                    query=query, classification=classification,
                    final_status="follow_up",
                    no_match_reason="; ".join(no_match_reasons),
                )
                resp = _build_slot_followup_response(session, first_insufficient_decision)
                aggregate_stats.record(metrics)
                return resp

            # LLM classified domain, but KB didn't match → offer domain diagnostic flow
            domain = valid_issues[0].domain
            tree_name = get_entry_tree_for_domain(domain)
            if tree_name:
                metrics.set_path("fallback_diagnostic_tree")
                session = create_session(query, domain=domain, tree=tree_name)
                session.current_domain = domain
                session.actions_taken.append("fallback→diagnostic_tree")
                log_request(
                    query=query, classification=classification,
                    final_status="follow_up",
                    no_match_reason="; ".join(no_match_reasons),
                )
                resp = _build_followup_response(session, tree_name, "entry_question")
                aggregate_stats.record(metrics)
                return resp

        # Step 3e: Nothing worked → check if fast gate had a tree suggestion
        if gate_result.tree and gate_result.tree != "general":
            metrics.set_path("vague_fallback_tree")
            session = create_session(query, domain=gate_result.domain, tree=gate_result.tree)
            if gate_result.domain:
                session.current_domain = gate_result.domain
            session.actions_taken.append(f"vague_fallback→tree={gate_result.tree}")
            log_request(
                query=query, classification=classification,
                final_status="follow_up",
                no_match_reason="LLM + Laya failed, using gate tree suggestion",
            )
            resp = _build_followup_response(session, gate_result.tree, "entry_question")
            aggregate_stats.record(metrics)
            return resp

        # Step 3f: Complete no-match
        metrics.set_path("no_match")
        fallback = search_official_support(query, "general")
        fallback_msg = "We couldn't identify a specific device issue. Try describing your problem more specifically."
        if fallback:
            fallback_msg += f"\n\nYou may find help here: {fallback['link']}"

        log_request(
            query=query, classification=classification,
            final_status="no_match",
            no_match_reason="All classification and Laya attempts failed",
        )

        resp = TroubleshootResponse(
            status="no_match",
            message=fallback_msg,
        )
        aggregate_stats.record(metrics)
        return resp

    except Exception as e:
        print(f"Error during troubleshooting: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error occurred.")


# ============================================================
# Mount Frontend Static Assets (Production / Docker build)
# ============================================================
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


