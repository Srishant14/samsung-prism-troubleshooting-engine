"""
Fast Local Gate — the first decision layer in the diagnostic engine.

This module answers ONE question:
    "Can this query be safely handled without LLM or Laya?"

It uses ONLY:
    - Deterministic keyword/phrase matching
    - Canonical issue aliases (version-controlled)
    - Query specificity scoring
    - In-memory KB index checks

It does NOT:
    - Call any LLM
    - Call Laya
    - Query Supabase
    - Generate troubleshooting advice

Outputs one of three verdicts:
    CLEAR   — domain + issue fully resolved, can go to fast KB path
    PARTIAL — domain known but issue needs narrowing (follow-up question)
    VAGUE   — not enough info, ask for domain or fall back to LLM

Performance target: < 1 ms for any query.
"""
import re
from typing import Dict, List, Optional, Tuple, NamedTuple, Any
from enum import Enum

from knowledge_base import has_exact_kb_record


# ============================================================
# Verdict types
# ============================================================

class GateVerdict(str, Enum):
    CLEAR = "CLEAR"       # Fully resolved — fast path
    PARTIAL = "PARTIAL"   # Domain known, issue needs narrowing
    VAGUE = "VAGUE"       # Not enough info — ask domain or LLM fallback


class Specificity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class GateResult(NamedTuple):
    verdict: GateVerdict
    domain: Optional[str]
    issue: Optional[str]
    context: Optional[str]
    specificity: Specificity
    confidence: float
    tree: Optional[str]          # diagnostic tree to use for PARTIAL
    multi_issues: Optional[List[dict]]  # for multi-issue queries


# ============================================================
# Preprocessed Signal Contract (for Laya-First Architecture)
# ============================================================

from pydantic import BaseModel, Field

class PreprocessedSignal(BaseModel):
    """
    Lightweight, deterministic preprocessed signal for the Laya Decision Engine.
    
    CRITICAL ARCHITECTURAL INVARIANT:
        This signal NEVER authorizes knowledge retrieval.
        It extracts normalized query text, symptoms, device models, slot values,
        and candidate domain/issue hints for Laya to arbitrate.
    """
    normalized_query: str
    symptoms: List[str] = Field(default_factory=list)
    device_model: Optional[str] = None
    candidate_domain: Optional[str] = None
    candidate_issue: Optional[str] = None
    candidate_confidence: float = 0.0
    context: Optional[str] = None
    apparent_slots: Dict[str, str] = Field(default_factory=dict)
    tree_hint: Optional[str] = None
    multi_issues: Optional[List[dict]] = None
    raw_gate_result: Optional[Any] = None


# ============================================================
# Canonical Issue Aliases
# ============================================================

# Maps (domain, issue) -> list of phrases that unambiguously mean this issue.
# These are version-controlled and deterministic.
CANONICAL_ALIASES: Dict[Tuple[str, str], List[str]] = {
    # --- Battery ---
    ("battery", "fast_drain"): [
        "battery draining fast", "battery drains quickly", "battery dying fast",
        "battery dies quickly", "battery doesn't last", "barely lasts half a day",
        "battery backup is terrible", "losing charge quickly",
        "phone dies within a few hours", "battery percentage drops rapidly",
        "battery draining very fast", "battery is dying very fast",
        "battery drains so fast", "battery life has become very bad",
        "phone doesn't last half a day", "phone dies too quickly",
        "battery backup has become terrible", "phone barely lasts half a day",
        "phone doesn't last all day", "battery goes from 100 to 0",
        "phone barely survives half a day", "battery is terrible",
        "battery dying in like 3 hours", "battery is literally dying",
        "my phone lose charge so quickly", "loses charge", "lose charge",
        "draining quickly after", "battery draining quickly after",
        "phone battery draining very fast", "battery dying",
        "battery draining", "phone dying fast", "battery life bad",
        "battery runs out fast", "dies within hours",
        "battery dies in", "phone battery is draining",
        # Variations with auxiliary verbs
        "battery is draining very fast", "battery is draining fast",
        "battery is draining quickly", "battery is dying fast",
        "battery is dying quickly", "battery is draining so fast",
        "phone is draining", "phone battery is draining very fast",
        "battery keeps draining", "battery keeps dying",
    ],
    ("battery", "slow_charging"): [
        "phone charges slowly", "slow charging", "takes forever to charge",
        "charging slow", "charges slowly", "slow to charge",
    ],
    ("battery", "overheating_while_charging"): [
        "hot while charging", "overheating while charging",
        "heats up while charging", "gets warm while charging",
        "phone hot when charging",
    ],
    ("battery", "battery_percentage_stuck"): [
        "battery percentage stuck", "battery percentage not updating",
        "percentage seems wrong", "battery percent wrong",
    ],
    ("battery", "drain_overnight"): [
        "battery drains overnight", "battery dies overnight",
        "drains on standby", "drains while sleeping",
        "battery drains during sleep", "loses charge overnight",
    ],
    ("battery", "battery_swelling"): [
        "battery swelling", "battery bulging", "battery swollen",
        "battery expanding", "battery popping out",
    ],

    # --- Display ---
    ("display", "screen_flicker"): [
        "screen flickers", "display flashes", "screen keeps blinking",
        "display is flickering", "screen flashes randomly",
        "screen flickering", "screen glitches", "display flickering",
        "screen blinking", "display flashing", "screen keeps flickering",
        # Auxiliary verb variations
        "screen is flickering", "screen is blinking", "screen is flashing",
        "screen is glitching", "display is flashing", "display is blinking",
    ],
    ("display", "auto_brightness_issue"): [
        "auto brightness not working", "adaptive brightness broken",
        "brightness adjusts wrong", "auto brightness issue",
    ],
    ("display", "touch_unresponsive"): [
        "touchscreen not responding", "touch not working",
        "screen won't respond to touch", "unresponsive screen",
        "tap not registering",
    ],
    ("display", "screen_burn_in"): [
        "ghost images on screen", "burn-in on screen",
        "screen burn in", "faint image stuck on screen",
    ],
    ("display", "always_on_display_fail"): [
        "always on display not working", "aod not showing",
        "always on display broken",
    ],
    ("display", "screen_too_dim"): [
        "screen too dim", "screen too dark", "display too dark",
        "can't see screen", "screen very dim",
    ],

    # --- Camera ---
    ("camera", "camera_blur"): [
        "photos are blurry", "pictures look fuzzy", "camera photos are unclear",
        "camera photos blurry", "blurry photos", "camera blurry",
        "pictures are blurry", "photos blurry", "camera is blurry",
        "photos are unclear", "blurry camera",
    ],
    ("camera", "camera_app_crash"): [
        "camera app crashing", "camera keeps crashing",
        "camera app not opening", "camera crashes",
        "camera force closes", "camera app crashes",
    ],
    ("camera", "blurry_night_photos"): [
        "blurry photos at night", "night photos blurry",
        "photos blurry in low light", "dark photos blurry",
    ],
    ("camera", "camera_lag_shutter"): [
        "camera shutter delay", "camera lag", "shutter takes long",
        "delay when taking photos",
    ],
    ("camera", "front_camera_issue"): [
        "selfie camera bad", "front camera quality bad",
        "selfie camera blurry", "front camera issue",
    ],
    ("camera", "camera_black_screen"): [
        "camera black screen", "camera shows black",
        "viewfinder black", "camera screen black",
    ],

    # --- Performance ---
    ("performance", "app_lag"): [
        "phone feels slow", "phone is laggy", "everything feels laggy",
        "phone stutters", "phone is slow", "phone laggy",
        "phone has become very slow", "phone became very slow",
        "phone has become slow", "phone extremely slow",
        "phone became extremely slow", "phone slow",
    ],
    ("performance", "slow_apps"): [
        "apps take forever to open", "apps are very slow",
        "apps load slowly", "applications are taking forever",
        "apps lag when opening", "apps taking forever",
        "apps are taking forever to open", "apps slow to open",
    ],
    ("performance", "phone_freezing"): [
        "phone keeps freezing", "phone frozen", "phone hangs",
        "phone locking up", "phone freezes",
    ],
    ("performance", "storage_full_slowdown"): [
        "phone slow due to storage", "storage full and slow",
        "no storage space and slow", "memory full and slow",
    ],
    ("performance", "overheating_gaming"): [
        "phone overheats while gaming", "hot during gaming",
        "overheating during games", "phone gets hot when gaming",
    ],
    ("performance", "apps_crashing"): [
        "apps keep crashing", "apps force closing",
        "apps keep force closing", "apps crash randomly",
    ],
    ("performance", "slow_boot"): [
        "phone takes long to start", "slow to boot",
        "slow startup", "phone takes forever to turn on",
    ],
}

# Build inverted index: phrase → (domain, issue)
_PHRASE_INDEX: Dict[str, Tuple[str, str]] = {}
for (domain, issue), phrases in CANONICAL_ALIASES.items():
    for phrase in phrases:
        _PHRASE_INDEX[phrase.lower()] = (domain, issue)


# ============================================================
# Domain-level keyword signals (for partial/domain detection)
# ============================================================

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "battery": ["battery", "charge", "charging", "drain", "power", "backup"],
    "display": ["screen", "display", "brightness", "touch", "aod"],
    "camera":  ["camera", "photo", "photos", "picture", "pictures", "lens", "selfie"],
    "performance": ["slow", "lag", "laggy", "freeze", "freezing", "hang", "hangs", "performance", "perf", "speed", "sluggish", "stutter"],
}

# These vague patterns mean "domain is somewhat known but issue is ambiguous"
AMBIGUOUS_DOMAIN_PATTERNS: Dict[str, List[str]] = {
    "battery": [
        "battery problem", "battery issue", "battery trouble",
        "something wrong with battery", "issue with battery",
        "battery sucks", "my battery sucks", "battery is bad",
        "battery is terrible", "battery bad", "my battery is terrible",
        "battery trouble", "having battery issues",
    ],
    "display": [
        "screen problem", "display issue", "screen not working",
        "display trouble", "something wrong with screen",
        "something wrong with display",
    ],
    "camera": [
        "camera problem", "camera issue", "camera not working",
        "camera trouble", "something wrong with camera",
    ],
    "performance": [
        "phone problem", "performance issue", "performance problem",
        "phone not right", "phone trouble", "speed issue", "slow issue",
    ],
}

# Cross-domain ambiguous patterns (e.g., overheating can be battery or performance)
CROSS_DOMAIN_PATTERNS: Dict[str, Dict] = {
    "overheating": {
        "keywords": ["overheat", "overheating", "overheats", "hot", "warm",
                      "heating", "heats"],
        "tree": "overheating",
    },
}

# Specificity boosters: phrases that indicate the user provided enough detail
SPECIFICITY_BOOSTERS = [
    r"\d+\s*%",           # percentage mentioned
    r"\d+\s*hour",        # time duration
    r"after\s+update",    # context: after update
    r"after\s+install",   # context: after install
    r"while\s+charging",  # context
    r"while\s+gaming",    # context
    r"at\s+night",        # context
    r"in\s+low\s+light",  # context
    r"when\s+idle",       # context
    r"on\s+standby",      # context
    r"when\s+i\s+take",   # specific action
    r"close-up|closeup|macro",  # specific condition
    r"front\s+camera|selfie",   # specific component
]


# ============================================================
# Context extraction
# ============================================================

CONTEXT_PATTERNS: Dict[str, List[str]] = {
    "after_update": ["after update", "after the update", "since update", "after updating"],
    "after_app_install": ["after install", "after installing", "new app", "after app install"],
    "charging": ["while charging", "when charging", "during charging"],
    "gaming": ["while gaming", "during gaming", "when gaming", "playing games"],
    "low_light": ["at night", "in low light", "in dark", "low light"],
    "close_up": ["close-up", "close up", "closeup", "macro"],
    "overnight": ["overnight", "during sleep", "standby", "when idle", "on standby"],
}


def _extract_context(query_lower: str) -> Optional[str]:
    """Extract the most specific context from the query."""
    for context, patterns in CONTEXT_PATTERNS.items():
        for p in patterns:
            if p in query_lower:
                return context
    return None


# ============================================================
# Specificity scoring
# ============================================================

def compute_specificity(query: str, domain: Optional[str], issue: Optional[str]) -> Specificity:
    """
    Compute a deterministic specificity score.
    
    HIGH: Clear issue + domain, possibly with context detail
    MEDIUM: Domain is identifiable, issue partially identifiable
    LOW: Vague or unclear
    """
    query_lower = query.lower()
    score = 0

    # Domain identified?
    if domain:
        score += 2

    # Issue identified?
    if issue:
        score += 3

    # Specificity boosters (details in the query)
    for pattern in SPECIFICITY_BOOSTERS:
        if re.search(pattern, query_lower):
            score += 1
            break  # one booster is enough

    # Query length — very short queries are more likely to be vague
    word_count = len(query_lower.split())
    if word_count >= 4:
        score += 1
    elif word_count <= 2:
        score -= 1

    # Final score mapping
    if score >= 5:
        return Specificity.HIGH
    elif score >= 2:
        return Specificity.MEDIUM
    else:
        return Specificity.LOW


# ============================================================
# Multi-issue detection
# ============================================================

def _detect_multi_issues(query_lower: str) -> List[dict]:
    """
    Detect if the query contains multiple independent issues.
    Returns a list of {domain, issue, context} dicts.
    """
    # Split on conjunctions
    parts = re.split(r'\band\b|\balso\b|\bplus\b|,\s*', query_lower)
    if len(parts) < 2:
        return []

    issues = []
    seen = set()
    for part in parts:
        part = part.strip()
        if not part:
            continue
        match = _match_aliases(part)
        if match:
            domain, issue = match
            key = (domain, issue)
            if key not in seen:
                seen.add(key)
                issues.append({
                    "domain": domain,
                    "issue": issue,
                    "context": _extract_context(part),
                })

    return issues if len(issues) >= 2 else []


# ============================================================
# Core alias matching
# ============================================================

def _match_aliases(query_lower: str) -> Optional[Tuple[str, str]]:
    """
    Match query against canonical aliases.
    Returns (domain, issue) or None.
    
    Strategy:
    1. Try exact phrase match (longest match first)
    2. Try substring containment for known phrases
    """
    # Sort phrases by length descending (prefer longest/most specific match)
    # This is a one-time sort per call, but the list is small (~200 entries)
    best_match = None
    best_len = 0

    for phrase, (domain, issue) in _PHRASE_INDEX.items():
        if phrase in query_lower and len(phrase) > best_len:
            best_match = (domain, issue)
            best_len = len(phrase)

    return best_match


def _detect_domain(query_lower: str) -> Optional[str]:
    """Detect the most likely domain from keywords."""
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', query_lower))
        if score > 0:
            scores[domain] = score

    if not scores:
        return None

    return max(scores, key=scores.get)


def _is_ambiguous_domain(query_lower: str) -> Optional[str]:
    """Check if query is an ambiguous domain-level complaint."""
    for domain, patterns in AMBIGUOUS_DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in query_lower:
                return domain
    return None


def _is_cross_domain_ambiguous(query_lower: str) -> Optional[str]:
    """Check if query matches a cross-domain ambiguous pattern."""
    for name, pattern_info in CROSS_DOMAIN_PATTERNS.items():
        for kw in pattern_info["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', query_lower):
                return pattern_info["tree"]
    return None


def _is_vague_query(query_lower: str) -> bool:
    """Check if the query is too vague to classify."""
    vague_patterns = [
        "not working properly", "not working right", "acting weird",
        "getting worse", "having problems", "fix my phone",
        "can you fix", "help me", "something is wrong",
        "not working", "it's broken", "doesn't work",
    ]
    for p in vague_patterns:
        if p in query_lower:
            return True

    # Very short, generic queries
    words = query_lower.split()
    if len(words) <= 2 and not any(
        kw in query_lower for kws in DOMAIN_KEYWORDS.values() for kw in kws
    ):
        return True

    return False


# ============================================================
# Main Gate Function
# ============================================================

def fast_gate(query: str) -> GateResult:
    """
    The fast local gate — first decision layer.
    
    Returns a GateResult with:
    - verdict: CLEAR, PARTIAL, or VAGUE
    - domain, issue, context: resolved classification (if available)
    - specificity: HIGH, MEDIUM, or LOW
    - confidence: 0.0 to 1.0
    - tree: diagnostic tree name for PARTIAL verdict
    - multi_issues: list of issues for multi-issue queries
    
    This function is designed to run in < 1ms.
    """
    query_lower = query.lower().strip()

    # === Check for completely vague queries first ===
    if _is_vague_query(query_lower):
        # Check if at least a domain is detectable
        domain = _detect_domain(query_lower)
        if domain:
            return GateResult(
                verdict=GateVerdict.PARTIAL,
                domain=domain,
                issue=None,
                context=None,
                specificity=Specificity.LOW,
                confidence=0.3,
                tree=domain,  # go to domain-level tree
                multi_issues=None,
            )
        return GateResult(
            verdict=GateVerdict.PARTIAL,
            domain=None,
            issue=None,
            context=None,
            specificity=Specificity.LOW,
            confidence=0.3,
            tree="general",
            multi_issues=None,
        )

    # === Check cross-domain ambiguous patterns (e.g., overheating) ===
    cross_tree = _is_cross_domain_ambiguous(query_lower)
    if cross_tree:
        # Overheating without clear context → needs follow-up
        context = _extract_context(query_lower)
        if not context:
            return GateResult(
                verdict=GateVerdict.PARTIAL,
                domain=None,
                issue=None,
                context=None,
                specificity=Specificity.MEDIUM,
                confidence=0.5,
                tree=cross_tree,
                multi_issues=None,
            )
        # Has context — try to resolve via aliases with full query
        # (e.g., "phone overheats while charging" → overheating_while_charging)

    # === Check for multi-issue queries ===
    multi = _detect_multi_issues(query_lower)
    if multi:
        # All issues must be KB-supported
        all_supported = all(
            has_exact_kb_record(m["domain"], m["issue"]) for m in multi
        )
        if all_supported:
            return GateResult(
                verdict=GateVerdict.CLEAR,
                domain=multi[0]["domain"],
                issue=multi[0]["issue"],
                context=multi[0].get("context"),
                specificity=Specificity.HIGH,
                confidence=0.85,
                tree=None,
                multi_issues=multi,
            )

    # === Try canonical alias matching (most specific match) ===
    match = _match_aliases(query_lower)
    if match:
        domain, issue = match
        context = _extract_context(query_lower)

        # Check KB support
        if has_exact_kb_record(domain, issue):
            specificity = compute_specificity(query, domain, issue)

            # For close-up camera issues, we know the KB doesn't have
            # a specific procedure, so don't confidently resolve
            if context == "close_up" and issue == "camera_blur":
                return GateResult(
                    verdict=GateVerdict.PARTIAL,
                    domain=domain,
                    issue=issue,
                    context=context,
                    specificity=Specificity.MEDIUM,
                    confidence=0.5,
                    tree=domain,
                    multi_issues=None,
                )

            return GateResult(
                verdict=GateVerdict.CLEAR,
                domain=domain,
                issue=issue,
                context=context,
                specificity=specificity,
                confidence=0.85,
                tree=None,
                multi_issues=None,
            )
        else:
            # Issue recognized but not in KB
            return GateResult(
                verdict=GateVerdict.PARTIAL,
                domain=domain,
                issue=issue,
                context=context,
                specificity=Specificity.MEDIUM,
                confidence=0.6,
                tree=domain,
                multi_issues=None,
            )

    # === Check ambiguous domain patterns ===
    amb_domain = _is_ambiguous_domain(query_lower)
    if amb_domain:
        return GateResult(
            verdict=GateVerdict.PARTIAL,
            domain=amb_domain,
            issue=None,
            context=None,
            specificity=Specificity.LOW,
            confidence=0.4,
            tree=amb_domain,
            multi_issues=None,
        )

    # === Try domain-level detection (weaker signal) ===
    domain = _detect_domain(query_lower)
    if domain:
        context = _extract_context(query_lower)
        specificity = compute_specificity(query, domain, None)

        if specificity == Specificity.LOW:
            return GateResult(
                verdict=GateVerdict.PARTIAL,
                domain=domain,
                issue=None,
                context=context,
                specificity=specificity,
                confidence=0.4,
                tree=domain,
                multi_issues=None,
            )
        else:
            # Domain detected with some specificity but no alias match
            # This could be unusual phrasing → LLM fallback candidate
            return GateResult(
                verdict=GateVerdict.VAGUE,
                domain=domain,
                issue=None,
                context=context,
                specificity=specificity,
                confidence=0.3,
                tree=domain,
                multi_issues=None,
            )

    # === Nothing matched → VAGUE ===
    return GateResult(
        verdict=GateVerdict.VAGUE,
        domain=None,
        issue=None,
        context=None,
        specificity=Specificity.LOW,
        confidence=0.1,
        tree=None,
        multi_issues=None,
    )


def preprocess_signal(query: str, session_context: Optional[dict] = None) -> PreprocessedSignal:
    """
    Fast, deterministic signal preprocessing (< 0.5ms).
    
    Extracts:
    - Normalized query text
    - Detected symptoms and keyword hints
    - Device model hints (e.g. Galaxy S24, Note 20)
    - Readily apparent diagnostic slot values
    - Candidate domain/issue hints with preliminary confidence
    
    CRITICAL ARCHITECTURAL INVARIANT:
        This preprocessor strictly does NOT authorize knowledge retrieval.
        It feeds structured signals directly into the Laya Decision Engine.
    """
    raw_res = fast_gate(query)
    q_lower = query.lower().strip()
    
    # Extract device model & slots
    from sufficiency_gate import extract_device_model, extract_slots_from_query, extract_slots_from_context
    device = extract_device_model(query)
    
    # Extract apparent slots directly from query and context
    slots = extract_slots_from_query(query)
    if raw_res.context:
        slots.update(extract_slots_from_context(raw_res.context))
    if session_context and "filled_slots" in session_context:
        slots.update(session_context["filled_slots"])
        
    symptoms = []
    if raw_res.domain:
        symptoms.append(raw_res.domain)
    if raw_res.issue:
        symptoms.append(f"{raw_res.domain}/{raw_res.issue}")
        
    return PreprocessedSignal(
        normalized_query=q_lower,
        symptoms=symptoms,
        device_model=device,
        candidate_domain=raw_res.domain,
        candidate_issue=raw_res.issue,
        candidate_confidence=raw_res.confidence,
        context=raw_res.context,
        apparent_slots=slots,
        tree_hint=raw_res.tree,
        multi_issues=raw_res.multi_issues,
        raw_gate_result=raw_res,
    )
