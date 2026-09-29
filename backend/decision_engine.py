"""
Laya Decision Engine integration.

Laya is a System-1 decision engine that makes structured decisions
using typed primitives (choice, score, noul) instead of generating text.

It is used here as the DECISION ENGINE — not a chatbot.
It decides:
- Which domain does a symptom belong to?
- Which specific issue matches?
- Is there enough evidence?
- What should happen next? (ASK_USER, LOOKUP_KNOWLEDGE, RESOLVE, NO_MATCH)

Laya does NOT generate troubleshooting steps.
The knowledge base remains the source of truth for procedures.

Optimizations vs. original:
1. ThreadPoolExecutor is created ONCE (singleton), not per-call
2. DOMAIN_CRITERIA is unchanged (already static)
3. Issue criteria now come from knowledge_base._ISSUE_CRITERIA (precomputed)
4. decide_domain_and_issue() combines two sequential calls when both are needed
"""
import time
import concurrent.futures
from typing import Dict, Any, Optional, List

# Maximum time allowed for Laya inference before falling back to rules (seconds)
LAYA_TIMEOUT = 2.0

# ============================================================
# Laya initialization — singleton, loaded once at startup
# ============================================================

_router = None
_init_attempted = False

# Singleton thread pool — avoids creating/destroying a pool per call
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def _get_router():
    """Get or create the Laya Router singleton."""
    global _router, _init_attempted
    if _router is not None:
        return _router
    if _init_attempted:
        return None  # Don't retry continuously if failed

    _init_attempted = True
    try:
        from laya import Router
        print("[Laya] Initializing Router in background...")
        start = time.time()
        _router = Router()
        elapsed = time.time() - start
        print(f"[Laya] Router ready in {elapsed:.1f}s")
        return _router
    except Exception as e:
        print(f"[Laya] Failed to initialize: {e}")
        print("[Laya] Falling back to rule-based decision engine")
        return None


def _run_with_timeout(func, *args, **kwargs):
    """Run a function with a timeout using the singleton thread pool.
    Falls back if it takes too long."""
    future = _executor.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=LAYA_TIMEOUT)
    except concurrent.futures.TimeoutError:
        print(f"[Laya] Decision timed out (>{LAYA_TIMEOUT}s), using rule-based fallback")
        return None
    except Exception as e:
        print(f"[Laya] Decision error: {e}")
        return None


# ============================================================
# Decision functions
# ============================================================

DOMAIN_CRITERIA = {
    "battery": "battery drain, charging issues, battery life, power problems, battery swelling",
    "display": "screen flickering, brightness issues, touchscreen problems, burn-in, AOD",
    "camera": "blurry photos, camera crashes, focus issues, selfie quality, black screen",
    "performance": "slow phone, app lag, freezing, overheating during gaming, app crashes, slow boot",
}


def _raw_predict_domain(router, symptoms: List[str], query: str) -> Dict[str, Any]:
    state = {
        "body": query,
        "symptoms": ", ".join(symptoms) if symptoms else query,
    }
    questions = {
        "domain": {
            "type": "choice",
            "instructions": "Select the troubleshooting domain that best matches the symptoms.",
            "criteria": DOMAIN_CRITERIA,
        }
    }
    result = router.predict(state, questions)
    domain_result = result.get("domain", {})
    chosen = domain_result.get("choice", "unknown")
    probs = domain_result.get("probabilities", {})
    confidence = probs.get(chosen, 0.0) if probs else 0.5
    return {
        "domain": chosen,
        "probabilities": probs,
        "confidence": float(confidence),
    }


def decide_domain(symptoms: List[str], query: str) -> Dict[str, Any]:
    """Decision A — Which troubleshooting domain best matches the symptoms?"""
    router = _get_router()
    if router:
        res = _run_with_timeout(_raw_predict_domain, router, symptoms, query)
        if res and res.get("domain") != "unknown" and res.get("confidence", 0.0) >= 0.35:
            return res
    return _fallback_decide_domain(symptoms, query)


def _raw_predict_issue(router, domain: str, symptoms: List[str], query: str, supported_issues: Dict[str, str]) -> Dict[str, Any]:
    state = {
        "body": query,
        "symptoms": ", ".join(symptoms) if symptoms else query,
        "domain": domain,
    }
    questions = {
        "issue": {
            "type": "choice",
            "instructions": "Select the specific issue within the domain that best describes the symptoms.",
            "criteria": supported_issues,
        }
    }
    result = router.predict(state, questions)
    issue_result = result.get("issue", {})
    chosen = issue_result.get("choice", "unknown")
    probs = issue_result.get("probabilities", {})
    confidence = probs.get(chosen, 0.0) if probs else 0.5
    return {
        "issue": chosen,
        "probabilities": probs,
        "confidence": float(confidence),
    }


def decide_issue(
    domain: str,
    symptoms: List[str],
    query: str,
    supported_issues: Dict[str, str],
) -> Dict[str, Any]:
    """Decision B — Which canonical issue within the domain is most likely?"""
    router = _get_router()
    if router and supported_issues:
        res = _run_with_timeout(_raw_predict_issue, router, domain, symptoms, query, supported_issues)
        if res and res.get("issue") != "unknown" and res.get("confidence", 0.0) >= 0.35:
            return res
    return _fallback_decide_issue(domain, symptoms, query, supported_issues)


def _raw_predict_evidence(router, symptoms, contexts, candidate_issues, query) -> Dict[str, Any]:
    evidence_summary = (
        f"Symptoms: {', '.join(symptoms) if symptoms else 'unclear'}. "
        f"Contexts: {', '.join(contexts) if contexts else 'none'}. "
        f"Candidate issues: {', '.join(candidate_issues) if candidate_issues else 'none'}."
    )
    state = {
        "body": f"User complaint: {query}",
        "evidence": evidence_summary,
    }
    questions = {
        "sufficient": {
            "type": "noul",
            "instructions": "Is there enough diagnostic evidence to select a specific supported troubleshooting path?",
            "criteria": "Is there enough diagnostic evidence to select a specific supported troubleshooting path?",
        }
    }
    result = router.predict(state, questions)
    noul_result = result.get("sufficient", {})
    probability = noul_result.get("probability", 0.5)
    return {
        "sufficient": probability >= 0.6,
        "probability": float(probability),
    }


def decide_sufficient_evidence(
    symptoms: List[str],
    contexts: List[str],
    candidate_issues: List[str],
    query: str,
) -> Dict[str, Any]:
    """Decision C — Do we have enough evidence to proceed?"""
    router = _get_router()
    if router:
        res = _run_with_timeout(_raw_predict_evidence, router, symptoms, contexts, candidate_issues, query)
        if res:
            return res
    return _fallback_sufficient_evidence(symptoms, contexts, candidate_issues)


def _raw_predict_action(router, symptoms, contexts, candidate_issues, confirmed_issues, questions_asked, has_kb_match, query) -> Dict[str, Any]:
    state_summary = (
        f"User complaint: {query}. "
        f"Symptoms identified: {', '.join(symptoms) if symptoms else 'unclear'}. "
        f"Contexts: {', '.join(contexts) if contexts else 'none'}. "
        f"Candidate issues: {', '.join(candidate_issues) if candidate_issues else 'none'}. "
        f"Confirmed issues: {', '.join(confirmed_issues) if confirmed_issues else 'none'}. "
        f"Questions asked so far: {questions_asked}. "
        f"Knowledge base has matching record: {'yes' if has_kb_match else 'no'}."
    )
    state = {"body": state_summary}
    questions = {
        "action": {
            "type": "choice",
            "instructions": "Determine the next action to take for this user request.",
            "criteria": {
                "ASK_USER": "Need more information from the user to narrow down the issue, ask a diagnostic question",
                "LOOKUP_KNOWLEDGE": "Have enough evidence, look up verified troubleshooting steps in the knowledge base",
                "RESOLVE": "Issue is confirmed and verified steps are available, present the solution to the user",
                "NO_MATCH": "Cannot identify a supported issue or no verified procedure exists for this problem",
            },
        }
    }
    result = router.predict(state, questions)
    action_result = result.get("action", {})
    chosen = action_result.get("choice", "NO_MATCH")
    probs = action_result.get("probabilities", {})
    confidence = probs.get(chosen, 0.0) if probs else 0.5
    return {
        "action": chosen,
        "probabilities": probs,
        "confidence": float(confidence),
    }


def decide_next_action(
    symptoms: List[str],
    contexts: List[str],
    candidate_issues: List[str],
    confirmed_issues: List[str],
    questions_asked: int,
    has_kb_match: bool,
    query: str,
) -> Dict[str, Any]:
    """Decision D — What should happen next?"""
    router = _get_router()
    if router:
        res = _run_with_timeout(
            _raw_predict_action, router, symptoms, contexts,
            candidate_issues, confirmed_issues, questions_asked, has_kb_match, query,
        )
        if res:
            return res
    return _fallback_next_action(
        symptoms, contexts, candidate_issues,
        confirmed_issues, questions_asked, has_kb_match,
    )


# ============================================================
# Fallback rule-based decisions (when Laya takes >1.5s or unavailable)
# ============================================================

def _fallback_decide_domain(symptoms: List[str], query: str) -> Dict[str, Any]:
    q = query.lower()
    combined = q + " " + " ".join(s.lower() for s in symptoms)

    scores = {
        "battery": sum(1 for w in ["battery", "charge", "drain", "power", "dying", "lasts", "dies"] if w in combined),
        "display": sum(1 for w in ["screen", "display", "flicker", "touch", "dim", "brightness", "burn-in"] if w in combined),
        "camera": sum(1 for w in ["camera", "photo", "blur", "lens", "selfie", "picture", "focus"] if w in combined),
        "performance": sum(1 for w in ["slow", "lag", "freeze", "crash", "heat", "hot", "hang", "boot"] if w in combined),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {"domain": "unknown", "probabilities": scores, "confidence": 0.1}

    total = sum(scores.values()) or 1
    return {
        "domain": best,
        "probabilities": {k: v / total for k, v in scores.items()},
        "confidence": scores[best] / total,
    }


def _fallback_decide_issue(
    domain: str, symptoms: List[str], query: str, supported_issues: Dict[str, str],
) -> Dict[str, Any]:
    q = (query + " " + " ".join(symptoms)).lower()

    best_issue = None
    best_score = 0
    for issue_id, description in supported_issues.items():
        desc_words = set(description.lower().split())
        q_words = set(q.split())
        overlap = len(desc_words.intersection(q_words))
        if overlap > best_score:
            best_score = overlap
            best_issue = issue_id

    if best_issue and best_score > 0:
        return {"issue": best_issue, "probabilities": {}, "confidence": min(0.4 + best_score * 0.1, 0.8)}
    return {"issue": "unknown", "probabilities": {}, "confidence": 0.0}


def _fallback_sufficient_evidence(
    symptoms: List[str], contexts: List[str], candidate_issues: List[str],
) -> Dict[str, Any]:
    score = 0
    if symptoms:
        score += len(symptoms) * 0.3
    if contexts:
        score += len(contexts) * 0.2
    if candidate_issues:
        score += len(candidate_issues) * 0.2
    probability = min(score, 1.0)
    return {"sufficient": probability >= 0.6, "probability": probability}


def _fallback_next_action(
    symptoms, contexts, candidate_issues, confirmed_issues,
    questions_asked, has_kb_match,
) -> Dict[str, Any]:
    if confirmed_issues and has_kb_match:
        return {"action": "RESOLVE", "probabilities": {}, "confidence": 0.9}
    if has_kb_match and candidate_issues:
        return {"action": "LOOKUP_KNOWLEDGE", "probabilities": {}, "confidence": 0.8}
    if not symptoms and questions_asked == 0:
        return {"action": "ASK_USER", "probabilities": {}, "confidence": 0.8}
    if questions_asked >= 3:
        return {"action": "NO_MATCH", "probabilities": {}, "confidence": 0.7}
    if not candidate_issues:
        return {"action": "ASK_USER", "probabilities": {}, "confidence": 0.7}
    return {"action": "LOOKUP_KNOWLEDGE", "probabilities": {}, "confidence": 0.6}


# ============================================================
# Primary Decision Maker (Laya-First Architecture)
# ============================================================

def decide_diagnostic_step(
    signal: Any,  # PreprocessedSignal
    session_slots: Optional[Dict[str, str]] = None,
    questions_asked: int = 0,
    max_questions: int = 5,
) -> Any:  # DiagnosticDecision
    """
    Primary Diagnostic Decision Maker.
    
    Laya is the primary decision-maker on the normal request path.
    Evaluates:
    - Most likely category and issue using Laya primitives
    - Known diagnostic slots vs. required slots
    - Whether context is sufficient for reliable KB retrieval
    - Next action: ASK_QUESTION, CLASSIFY, RETRIEVE_KB, REFINE_QUERY, OFFICIAL_SEARCH
    
    Invariants enforced:
    - Never authorizes KB retrieval when required fields are missing.
    - Times out gracefully to rule-based fallback if Laya is slow.
    """
    from sufficiency_gate import (
        evaluate_sufficiency, DiagnosticDecision, NextAction, SufficiencyStatus
    )
    from knowledge_base import get_issue_criteria, has_exact_kb_record

    query = getattr(signal, "normalized_query", "") or ""
    domain = getattr(signal, "candidate_domain", None)
    issue = getattr(signal, "candidate_issue", None)
    confidence = getattr(signal, "candidate_confidence", 0.0)
    context = getattr(signal, "context", None)
    tree_hint = getattr(signal, "tree_hint", None)

    # Combined slot evidence
    all_slots = dict(session_slots or {})
    apparent_slots = getattr(signal, "apparent_slots", {}) or {}
    all_slots.update(apparent_slots)

    # Multi-issue signal check
    multi_issues = getattr(signal, "multi_issues", None)

    # If domain is not resolved by signal preprocessor, use Laya to predict domain
    if not domain or domain == "unknown":
        domain_res = decide_domain(getattr(signal, "symptoms", []), query)
        if domain_res and domain_res.get("domain") != "unknown" and domain_res.get("confidence", 0.0) >= 0.35:
            domain = domain_res["domain"]
            confidence = domain_res["confidence"]

    # If domain is known but issue is not, use Laya to predict issue
    if domain and (not issue or issue == "unknown"):
        issue_crit = get_issue_criteria(domain)
        if issue_crit:
            issue_res = decide_issue(domain, getattr(signal, "symptoms", []), query, issue_crit)
            if issue_res and issue_res.get("issue") != "unknown" and issue_res.get("confidence", 0.0) >= 0.35:
                issue = issue_res["issue"]
                confidence = max(confidence, issue_res["confidence"])

    # If category or issue is still completely unknown, action is CLASSIFY (late-stage fallback)
    if not domain:
        return DiagnosticDecision(
            category=None,
            issue=None,
            category_confidence=confidence,
            sufficiency=SufficiencyStatus.UNKNOWN,
            filled_slots=all_slots,
            missing_slots=["category", "issue_type"],
            next_action=NextAction.CLASSIFY,
            kb_retrieval_allowed=False,
            reason="Category unresolved by preprocessor and Laya; invoke fallback classifier",
        )

    # Use sufficiency evaluation to check required slots & redirections
    decision = evaluate_sufficiency(
        domain=domain,
        issue=issue,
        context=context,
        query=query,
        filled_slots=all_slots,
        gate_confidence=confidence or 0.85,
        questions_asked=questions_asked,
        max_questions=max_questions,
    )

    # Verify KB existence if retrieval is tentatively allowed
    if decision.kb_retrieval_allowed and decision.issue:
        if not has_exact_kb_record(decision.category, decision.issue):
            # Known issue but no exact KB record
            decision.kb_retrieval_allowed = False
            decision.next_action = NextAction.ASK_QUESTION
            decision.reason = f"No exact KB procedure for {decision.category}/{decision.issue}"
        else:
            decision.reason = "Diagnostic slots verified and exact KB procedure available"
    elif decision.missing_slots:
        decision.reason = f"Missing required diagnostic slots: {decision.missing_slots}"

    return decision
