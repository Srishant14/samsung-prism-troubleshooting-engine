"""
Knowledge base with precomputed indexes for fast lookup.

Optimizations vs. original:
1. Precomputed (domain, issue) → record index at startup  (O(1) lookup)
2. Cached taxonomy and issue_criteria (computed once, not per request)
3. search_knowledge uses index instead of scanning all 25 records
4. search_knowledge_batch for concurrent multi-issue lookup
"""
import json
import os
from typing import Dict, List, Optional, Tuple

try:
    from supabase import create_client, Client
except ImportError:
    pass

from config import SUPABASE_URL, SUPABASE_KEY
from logger import log_kb_search

# ── Load seed data once at startup ─────────────────────────────
SEED_DATA_PATH = os.path.join(os.path.dirname(__file__), "seed_data.json")
with open(SEED_DATA_PATH, "r") as f:
    SEED_DATA = json.load(f)

# ── Initialize Supabase if config is available ─────────────────
supabase: Optional["Client"] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")


# ================================================================
# PRECOMPUTED CACHES — built once at import time
# ================================================================

# (domain, issue) → list of active records for that pair
_KB_INDEX: Dict[tuple, List[Dict]] = {}

# domain → list of issue identifiers
_TAXONOMY: Dict[str, List[str]] = {}

# domain → {issue_id: description_string}  (for Laya decide_issue)
_ISSUE_CRITERIA: Dict[str, Dict[str, str]] = {}

# (domain, issue, context|None, query_hash) → (record, confidence) cache
# Bounded LRU of recent lookups — avoids recomputation within the same request
# when _resolve_issue and _run_laya_diagnosis both call search_knowledge
_LOOKUP_CACHE: Dict[tuple, Optional[Tuple[Dict, float]]] = {}
_LOOKUP_CACHE_MAX = 128


def _build_indexes():
    """Build all precomputed indexes from SEED_DATA. Called once at startup."""
    _KB_INDEX.clear()
    _TAXONOMY.clear()
    _ISSUE_CRITERIA.clear()
    _LOOKUP_CACHE.clear()

    for record in SEED_DATA:
        if not record.get("active", True):
            continue

        domain = record["domain"]
        issue = record["issue"]
        key = (domain, issue)

        # KB index
        if key not in _KB_INDEX:
            _KB_INDEX[key] = []
        _KB_INDEX[key].append(record)

        # Taxonomy
        if domain not in _TAXONOMY:
            _TAXONOMY[domain] = []
        if issue not in _TAXONOMY[domain]:
            _TAXONOMY[domain].append(issue)

        # Issue criteria (description for Laya)
        if domain not in _ISSUE_CRITERIA:
            _ISSUE_CRITERIA[domain] = {}
        if issue not in _ISSUE_CRITERIA[domain]:
            desc_parts = []
            if record.get("title"):
                desc_parts.append(record["title"])
            if record.get("symptoms"):
                desc_parts.extend(record["symptoms"][:2])
            _ISSUE_CRITERIA[domain][issue] = ", ".join(desc_parts) or issue


_build_indexes()


# ================================================================
# Public API
# ================================================================

def get_all_domains() -> List[str]:
    """Returns a list of unique domains available in the knowledge base."""
    return list(_TAXONOMY.keys())


def get_supported_issues() -> Dict[str, List[str]]:
    """Returns a map of domain → list of supported issue identifiers.
    Uses precomputed cache — no iteration over SEED_DATA."""
    return _TAXONOMY


def get_issue_criteria(domain: str) -> Dict[str, str]:
    """Returns {issue_id: description} for all issues in a domain.
    Precomputed at startup — no SEED_DATA iteration needed."""
    return _ISSUE_CRITERIA.get(domain, {})


# ================================================================
# Retrieval confidence computation (unchanged logic)
# ================================================================

def _compute_retrieval_confidence(
    record: Dict,
    domain: str,
    issue: str,
    context: Optional[str],
    query: str
) -> float:
    """
    Compute how well a KB record matches the classified issue.
    Returns a confidence score between 0.0 and 1.0.

    Scoring:
    - domain match: required (0.0 if no match)
    - exact issue match: 0.6 base
    - context compatibility: +0.2
    - query variation match: +0.2
    """
    # Domain must match
    if record["domain"] != domain:
        return 0.0

    score = 0.0

    # Issue match
    if record["issue"] == issue:
        score += 0.6
    else:
        # Issue doesn't match at all — this record is for a different problem
        return 0.0

    # Context compatibility
    record_contexts = record.get("contexts", ["general"])
    if context is None or context in record_contexts or "general" in record_contexts:
        score += 0.2
    else:
        # User has a specific context that this record doesn't cover
        # Penalize but don't zero out — the domain+issue still match
        score += 0.05

    # Query variation / keyword match (bonus)
    query_lower = query.lower()
    variation_match = False

    # Check keywords
    for keyword in record.get("keywords", []):
        if keyword.lower() in query_lower:
            variation_match = True
            break

    # Check query variations
    if not variation_match:
        for variation in record.get("query_variations", []):
            var_words = set(variation.lower().split())
            q_words = set(query_lower.split())
            overlap = len(var_words.intersection(q_words))
            if overlap >= max(2, len(var_words) // 2):
                variation_match = True
                break

    if variation_match:
        score += 0.2
    else:
        # No keyword/variation match, but domain+issue matched — still okay
        score += 0.1

    return min(score, 1.0)


def _validate_context_match(record: Dict, context: Optional[str]) -> bool:
    """
    Check if the user's specific context is actually covered by this KB record.
    If the user specifies a narrow context (like 'close_up' for camera blur)
    and the record only covers 'general', this is a weak match.
    """
    if context is None:
        return True  # No specific context — general records are fine

    record_contexts = record.get("contexts", ["general"])

    # These specific contexts require explicit KB support
    specific_contexts = {"close_up", "macro", "underwater", "wide_angle", "zoom"}
    if context in specific_contexts:
        # Only pass if the record explicitly lists this context
        return context in record_contexts

    # For other contexts (after_update, brightness_change, etc.),
    # "general" records are acceptable
    return context in record_contexts or "general" in record_contexts


def search_knowledge(
    domain: str,
    issue: str,
    query: str,
    context: Optional[str] = None
) -> Optional[Tuple[Dict, float]]:
    """
    Search for troubleshooting steps based on domain, issue, and query.
    Returns (record, match_confidence) or None.

    Uses precomputed index for O(1) domain+issue lookup instead of
    scanning all records.
    """
    # Check in-process cache first
    cache_key = (domain, issue, context, query)
    if cache_key in _LOOKUP_CACHE:
        cached = _LOOKUP_CACHE[cache_key]
        # Re-log even on cache hit for observability
        if cached is not None:
            log_kb_search(domain, issue, context, True, cached[1])
        else:
            log_kb_search(domain, issue, context, False, 0.0)
        return cached

    # Use precomputed index — only scan records for this (domain, issue) pair
    candidates = _KB_INDEX.get((domain, issue), [])

    best_record = None
    best_confidence = 0.0

    for record in candidates:
        # Compute retrieval confidence
        match_conf = _compute_retrieval_confidence(record, domain, issue, context, query)

        # Validate context — reject specific contexts that aren't covered
        if not _validate_context_match(record, context):
            match_conf *= 0.3  # Heavy penalty for context mismatch

        if match_conf > best_confidence:
            best_confidence = match_conf
            best_record = record

    # Log the search
    log_kb_search(domain, issue, context, best_record is not None, best_confidence)

    # Threshold: only return if match confidence is good enough
    result = None
    if best_record and best_confidence >= 0.5:
        result = (best_record, best_confidence)

    # Cache the result (bounded)
    if len(_LOOKUP_CACHE) >= _LOOKUP_CACHE_MAX:
        # Evict oldest entry (simple FIFO — good enough for bounded cache)
        oldest_key = next(iter(_LOOKUP_CACHE))
        del _LOOKUP_CACHE[oldest_key]
    _LOOKUP_CACHE[cache_key] = result

    return result


def search_knowledge_batch(
    lookups: List[Tuple[str, str, str, Optional[str]]]
) -> List[Optional[Tuple[Dict, float]]]:
    """
    Batch lookup for multiple (domain, issue, query, context) tuples.
    Avoids repeated index lookups for multi-issue queries.
    """
    return [search_knowledge(d, i, q, c) for d, i, q, c in lookups]


def has_exact_kb_record(domain: str, issue: str) -> bool:
    """Fast check: does the KB contain at least one active record for
    this domain+issue? Uses the precomputed index — no iteration."""
    return (domain, issue) in _KB_INDEX
