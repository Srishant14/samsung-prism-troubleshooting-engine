"""
Sufficiency Gate — centralized diagnostic sufficiency evaluation.

This module enforces the critical architectural invariant:
    No KB retrieval may proceed without passing the sufficiency check.

It evaluates:
1. What diagnostic slots are required for the identified issue?
2. Which slots are already filled from the query/session context?
3. Is the diagnostic context sufficient for KB retrieval?
4. If not, what is the highest-value question to ask next?

Design principles:
- Purely deterministic (no LLM calls) for fast-path decisions
- Category-specific required/optional slot definitions
- Reuses existing diagnostic tree questions where appropriate
- Returns typed DiagnosticDecision objects
- Validates invariants (e.g., missing required slots → retrieval blocked)
"""
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field, model_validator


# ============================================================
# Enums
# ============================================================

class SufficiencyStatus(str, Enum):
    SUFFICIENT = "sufficient"       # All required slots filled
    INSUFFICIENT = "insufficient"   # Missing required diagnostic slots
    UNKNOWN = "unknown"             # Cannot evaluate (no category)


class NextAction(str, Enum):
    ASK_QUESTION = "ask_question"
    CLASSIFY = "classify"
    RETRIEVE_KB = "retrieve_kb"
    REFINE_QUERY = "refine_query"
    OFFICIAL_SEARCH = "official_search"
    ANSWER = "answer"


# ============================================================
# Diagnostic Decision Contract
# ============================================================

class DiagnosticDecision(BaseModel):
    """
    Typed decision contract for the diagnostic pipeline.

    This is the single source of truth for what happens next.
    The orchestrator MUST respect kb_retrieval_allowed.
    """
    category: Optional[str] = None          # domain, e.g. "battery"
    issue: Optional[str] = None             # e.g. "fast_drain"
    category_confidence: float = 0.0
    sufficiency: SufficiencyStatus = SufficiencyStatus.UNKNOWN
    filled_slots: Dict[str, str] = Field(default_factory=dict)
    missing_slots: List[str] = Field(default_factory=list)
    next_action: NextAction = NextAction.ASK_QUESTION
    question: Optional[str] = None
    question_options: Optional[List[dict]] = None
    kb_retrieval_allowed: bool = False
    context: Optional[str] = None
    redirected_issue: Optional[str] = None
    reason: Optional[str] = None

    @property
    def known_fields(self) -> Dict[str, str]:
        return self.filled_slots

    @property
    def missing_required_fields(self) -> List[str]:
        return self.missing_slots

    @property
    def is_sufficient(self) -> bool:
        return self.sufficiency == SufficiencyStatus.SUFFICIENT

    @model_validator(mode='after')
    def enforce_invariants(self):
        """Enforce critical invariants after construction."""
        # INVARIANT: missing required slots → retrieval MUST be blocked
        if self.missing_slots and self.kb_retrieval_allowed:
            self.kb_retrieval_allowed = False
            if self.next_action == NextAction.RETRIEVE_KB:
                self.next_action = NextAction.ASK_QUESTION
        # INVARIANT: confidence must be [0, 1]
        self.category_confidence = max(0.0, min(1.0, self.category_confidence))
        # INVARIANT: RETRIEVE_KB requires kb_retrieval_allowed
        if self.next_action == NextAction.RETRIEVE_KB and not self.kb_retrieval_allowed:
            self.next_action = NextAction.ASK_QUESTION
        return self


# ============================================================
# Category-Specific Diagnostic Slot Requirements
# ============================================================
#
# Required slots MUST be filled before KB retrieval is permitted.
# These are chosen because they genuinely change the diagnostic
# routing or the KB result:
#   - battery/fast_drain: drain_conditions distinguishes from
#     drain_overnight, overheating_while_charging
#   - camera/camera_blur: blur_conditions distinguishes from
#     blurry_night_photos, close_up issues
#   - performance/app_lag: lag_conditions distinguishes from
#     phone_freezing, overheating_gaming, storage_full_slowdown
#
# Issues NOT listed here use DEFAULT_SLOT_REQUIREMENTS (no
# required slots) because the issue is already specific enough.

ISSUE_SLOT_REQUIREMENTS: Dict[Tuple[str, str], Dict[str, List[str]]] = {
    ("battery", "fast_drain"): {
        "required": ["drain_conditions"],
        "optional": ["device_model", "trigger_event"],
    },
    ("camera", "camera_blur"): {
        "required": ["blur_conditions"],
        "optional": ["device_model"],
    },
    ("performance", "app_lag"): {
        "required": ["lag_conditions"],
        "optional": ["device_model", "trigger_event"],
    },
}

DEFAULT_SLOT_REQUIREMENTS: Dict[str, List[str]] = {
    "required": [],
    "optional": ["device_model"],
}


# ============================================================
# Slot Questions with Selectable Options
# ============================================================
#
# Each question targets a specific required slot.
# Options may redirect to a different issue when selected.

SLOT_QUESTIONS: Dict[str, Dict] = {
    "drain_conditions": {
        "text": "When does the battery drain fastest?",
        "options": [
            {
                "label": "While idle or on standby",
                "slot_value": "idle",
                "redirects_to_issue": "drain_overnight",
            },
            {
                "label": "During heavy use (gaming, video, etc.)",
                "slot_value": "heavy_use",
            },
            {
                "label": "Both while idle and during use",
                "slot_value": "both",
            },
            {
                "label": "Mainly while charging",
                "slot_value": "charging",
                "redirects_to_issue": "overheating_while_charging",
            },
        ],
    },
    "blur_conditions": {
        "text": "When are your photos blurry?",
        "options": [
            {
                "label": "All the time / in general",
                "slot_value": "general",
            },
            {
                "label": "In low light or at night",
                "slot_value": "low_light",
                "redirects_to_issue": "blurry_night_photos",
            },
            {
                "label": "Only for close-up or macro shots",
                "slot_value": "close_up",
            },
            {
                "label": "Only with the front/selfie camera",
                "slot_value": "front",
                "redirects_to_issue": "front_camera_issue",
            },
        ],
    },
    "lag_conditions": {
        "text": "What kind of slowness are you experiencing?",
        "options": [
            {
                "label": "Phone feels slow or laggy overall",
                "slot_value": "general",
            },
            {
                "label": "Apps take too long to open",
                "slot_value": "slow_apps",
                "redirects_to_issue": "slow_apps",
            },
            {
                "label": "Phone keeps freezing or hanging",
                "slot_value": "freezing",
                "redirects_to_issue": "phone_freezing",
            },
            {
                "label": "Phone overheats during gaming",
                "slot_value": "gaming",
                "redirects_to_issue": "overheating_gaming",
            },
            {
                "label": "Storage is almost full",
                "slot_value": "storage",
                "redirects_to_issue": "storage_full_slowdown",
            },
        ],
    },
}


# ============================================================
# Samsung Device Model Extraction
# ============================================================

_SAMSUNG_DEVICE_PATTERNS = [
    r"galaxy\s*s\d{1,2}\s*(?:ultra|plus|\+|fe)?",
    r"galaxy\s*a\d{1,2}(?:s)?",
    r"galaxy\s*z\s*(?:fold|flip)\s*\d?",
    r"galaxy\s*note\s*\d{1,2}\s*(?:ultra|plus|\+)?",
    r"galaxy\s*m\d{1,2}",
    r"galaxy\s*f\d{1,2}",
    r"(?:s|a)\d{1,2}\s*(?:ultra|plus|\+|fe)",
    r"note\s*\d{1,2}",
    r"fold\s*\d",
    r"flip\s*\d",
]


def extract_device_model(query: str) -> Optional[str]:
    """Extract Samsung device model from query text."""
    q = query.lower()
    for pattern in _SAMSUNG_DEVICE_PATTERNS:
        match = re.search(pattern, q)
        if match:
            return match.group(0).strip()
    return None


# ============================================================
# Context → Slot Mapping
# ============================================================
#
# Maps fast_gate context strings to (slot_name, slot_value)

_CONTEXT_TO_SLOT: Dict[str, Tuple[str, str]] = {
    "overnight":         ("drain_conditions", "idle"),
    "charging":          ("drain_conditions", "charging"),
    "gaming":            ("drain_conditions", "heavy_use"),
    "after_update":      ("trigger_event", "after_update"),
    "after_app_install":  ("trigger_event", "after_app_install"),
    "low_light":         ("blur_conditions", "low_light"),
    "close_up":          ("blur_conditions", "close_up"),
}


# ============================================================
# Slot Extraction Functions
# ============================================================

def extract_slots_from_query(query: str) -> Dict[str, str]:
    """Extract diagnostic slot values directly from query text."""
    slots: Dict[str, str] = {}
    q = query.lower()

    # Device model
    device = extract_device_model(query)
    if device:
        slots["device_model"] = device

    # Drain conditions
    if any(p in q for p in [
        "while idle", "on standby", "when not using",
        "overnight", "during sleep", "when sleeping",
        "while sleeping", "drains overnight",
    ]):
        slots["drain_conditions"] = "idle"
    elif any(p in q for p in [
        "while gaming", "during gaming", "when gaming",
        "playing games", "heavy use",
    ]):
        slots["drain_conditions"] = "heavy_use"
    elif any(p in q for p in [
        "while charging", "when charging", "during charging",
    ]):
        slots["drain_conditions"] = "charging"
    elif any(p in q for p in [
        "all the time", "always", "constantly",
        "both idle and", "whether idle",
    ]):
        slots["drain_conditions"] = "both"

    # Blur conditions
    if any(p in q for p in [
        "at night", "in low light", "in dark", "in the dark",
        "low light", "night photos",
    ]):
        slots["blur_conditions"] = "low_light"
    elif any(p in q for p in [
        "close-up", "close up", "closeup", "macro",
    ]):
        slots["blur_conditions"] = "close_up"
    elif any(p in q for p in [
        "selfie", "front camera",
    ]):
        slots["blur_conditions"] = "front"

    # Lag conditions
    if any(p in q for p in [
        "storage full", "no storage", "no space",
        "storage almost full", "memory full",
    ]):
        slots["lag_conditions"] = "storage"
    elif any(p in q for p in [
        "freezing", "frozen", "hangs", "hanging",
        "locks up", "locking up",
    ]):
        slots["lag_conditions"] = "freezing"
    elif any(p in q for p in [
        "apps slow", "apps take", "apps load slowly",
        "apps open slowly", "apps are slow",
        "apps are taking forever",
    ]):
        slots["lag_conditions"] = "slow_apps"
    elif any(p in q for p in [
        "overheats during gaming", "hot during gaming",
        "overheating during games", "hot when gaming",
    ]):
        slots["lag_conditions"] = "gaming"

    # Trigger events
    if any(p in q for p in [
        "after update", "after the update", "since update",
        "after updating", "since the update",
    ]):
        slots["trigger_event"] = "after_update"
    elif any(p in q for p in [
        "after install", "after installing", "new app",
        "after app install",
    ]):
        slots["trigger_event"] = "after_app_install"

    return slots


def extract_slots_from_context(context: Optional[str]) -> Dict[str, str]:
    """Extract slot values from the fast gate's context signal."""
    if not context:
        return {}
    mapping = _CONTEXT_TO_SLOT.get(context)
    if mapping:
        return {mapping[0]: mapping[1]}
    return {}


# ============================================================
# Slot Answer Processing
# ============================================================

def process_slot_answer(
    slot_name: str,
    option_index: int,
    current_domain: str,
    current_issue: str,
) -> Dict:
    """
    Process a user's answer to a slot question.

    Returns a dict with:
    - slot_value: the value to store
    - redirected_issue: new issue if the answer redirects, or None
    - redirected_domain: new domain if changed, or None
    """
    question = SLOT_QUESTIONS.get(slot_name)
    if not question or option_index >= len(question["options"]):
        return {"error": "Invalid slot question or option index"}

    option = question["options"][option_index]
    result = {
        "slot_value": option["slot_value"],
        "redirected_issue": option.get("redirects_to_issue"),
        "redirected_domain": None,
    }

    # Some redirects cross domains (e.g., overheating_while_charging is battery)
    if result["redirected_issue"]:
        # Infer domain from the redirected issue
        from knowledge_base import has_exact_kb_record
        for candidate_domain in [current_domain, "battery", "display", "camera", "performance"]:
            if has_exact_kb_record(candidate_domain, result["redirected_issue"]):
                result["redirected_domain"] = candidate_domain
                break
        if not result["redirected_domain"]:
            result["redirected_domain"] = current_domain

    return result


# ============================================================
# Main Sufficiency Evaluation
# ============================================================

def evaluate_sufficiency(
    domain: Optional[str],
    issue: Optional[str],
    context: Optional[str],
    query: str,
    filled_slots: Optional[Dict[str, str]] = None,
    gate_confidence: float = 0.0,
    questions_asked: int = 0,
    max_questions: int = 5,
) -> DiagnosticDecision:
    """
    Evaluate whether diagnostic context is sufficient for KB retrieval.

    This is the centralized sufficiency guard. EVERY path to KB
    retrieval must call this function first.

    Returns a DiagnosticDecision with:
    - kb_retrieval_allowed: whether the orchestrator may call the KB
    - next_action: what to do next
    - question/question_options: if a follow-up is needed
    - filled_slots/missing_slots: current slot state
    """
    # ── Merge all available slot evidence ──
    all_slots: Dict[str, str] = dict(filled_slots or {})
    all_slots.update(extract_slots_from_query(query))
    all_slots.update(extract_slots_from_context(context))

    # ── No category → classify or ask domain question ──
    if not domain or not issue:
        if domain:
            return DiagnosticDecision(
                category=domain,
                issue=None,
                category_confidence=gate_confidence,
                sufficiency=SufficiencyStatus.INSUFFICIENT,
                filled_slots=all_slots,
                missing_slots=["issue_type"],
                next_action=NextAction.ASK_QUESTION,
                kb_retrieval_allowed=False,
            )
        return DiagnosticDecision(
            category=None,
            issue=None,
            category_confidence=gate_confidence,
            sufficiency=SufficiencyStatus.UNKNOWN,
            filled_slots=all_slots,
            missing_slots=["category", "issue_type"],
            next_action=NextAction.CLASSIFY,
            kb_retrieval_allowed=False,
        )

    # ── Get slot requirements for this (domain, issue) ──
    slot_req = ISSUE_SLOT_REQUIREMENTS.get(
        (domain, issue), DEFAULT_SLOT_REQUIREMENTS,
    )
    required = slot_req["required"]
    missing = [s for s in required if s not in all_slots]

    # ── Question budget exhausted → allow retrieval with what we have ──
    if questions_asked >= max_questions and missing:
        return DiagnosticDecision(
            category=domain,
            issue=issue,
            category_confidence=gate_confidence,
            sufficiency=SufficiencyStatus.SUFFICIENT,
            filled_slots=all_slots,
            missing_slots=[],
            next_action=NextAction.RETRIEVE_KB,
            kb_retrieval_allowed=True,
            context=context,
        )

    # ── Missing required slots → ask a question ──
    if missing:
        target_slot = missing[0]
        slot_q = SLOT_QUESTIONS.get(target_slot)
        if slot_q:
            return DiagnosticDecision(
                category=domain,
                issue=issue,
                category_confidence=gate_confidence,
                sufficiency=SufficiencyStatus.INSUFFICIENT,
                filled_slots=all_slots,
                missing_slots=missing,
                next_action=NextAction.ASK_QUESTION,
                question=slot_q["text"],
                question_options=slot_q["options"],
                kb_retrieval_allowed=False,
                context=context,
            )
        # No predefined question for this slot → treat as non-blocking

    # ── Check for issue redirection based on filled slots ──
    redirected_issue = _check_redirections(domain, issue, all_slots)
    final_issue = redirected_issue or issue

    # ── All required slots filled → retrieval permitted ──
    return DiagnosticDecision(
        category=domain,
        issue=final_issue,
        category_confidence=gate_confidence,
        sufficiency=SufficiencyStatus.SUFFICIENT,
        filled_slots=all_slots,
        missing_slots=[],
        next_action=NextAction.RETRIEVE_KB,
        kb_retrieval_allowed=True,
        context=context,
        redirected_issue=redirected_issue,
    )


def _check_redirections(
    domain: str, issue: str, filled_slots: Dict[str, str],
) -> Optional[str]:
    """Check if any filled slot value triggers an issue redirection."""
    slot_req = ISSUE_SLOT_REQUIREMENTS.get((domain, issue))
    if not slot_req:
        return None

    for slot_name in slot_req.get("required", []):
        slot_value = filled_slots.get(slot_name)
        if not slot_value:
            continue
        question = SLOT_QUESTIONS.get(slot_name)
        if not question:
            continue
        for opt in question["options"]:
            if opt["slot_value"] == slot_value and opt.get("redirects_to_issue"):
                return opt["redirects_to_issue"]
    return None


# ============================================================
# Decision Validation (for external callers)
# ============================================================

def validate_decision(decision: DiagnosticDecision) -> DiagnosticDecision:
    """
    Validate and sanitize a DiagnosticDecision.

    Enforces the critical invariant:
        missing required slots → kb_retrieval_allowed = False

    This is a safety net; the model_validator on DiagnosticDecision
    already enforces this, but callers can invoke this explicitly.
    """
    if decision.missing_slots and decision.kb_retrieval_allowed:
        decision.kb_retrieval_allowed = False
        decision.next_action = NextAction.ASK_QUESTION
    if decision.next_action == NextAction.RETRIEVE_KB and not decision.kb_retrieval_allowed:
        decision.next_action = NextAction.ASK_QUESTION
    return decision
