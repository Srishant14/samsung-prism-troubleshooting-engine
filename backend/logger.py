import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Configure logger
logger = logging.getLogger("troubleshoot_engine")
logger.setLevel(logging.DEBUG)

# Console handler with simple format
_handler = logging.StreamHandler()
_handler.setLevel(logging.DEBUG)
_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s"))
logger.addHandler(_handler)


def _safe_serialize(obj: Any) -> Any:
    """Make objects JSON-serializable."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def log_request(
    query: str,
    classification: Any,
    kb_candidates: Optional[List[Dict]] = None,
    selected_results: Optional[List[Dict]] = None,
    final_status: str = "",
    no_match_reason: Optional[str] = None,
):
    """Log a complete troubleshooting request for debugging."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "classification": _safe_serialize(classification),
        "kb_candidates_count": len(kb_candidates) if kb_candidates else 0,
        "selected_results_count": len(selected_results) if selected_results else 0,
        "final_status": final_status,
    }
    if no_match_reason:
        entry["no_match_reason"] = no_match_reason
    if selected_results:
        entry["selected_results"] = [
            {
                "domain": r.get("domain", ""),
                "issue": r.get("issue", ""),
                "title": r.get("title", ""),
                "match_confidence": r.get("match_confidence", 0),
                "final_confidence": r.get("final_confidence", 0),
            }
            for r in selected_results
        ]

    logger.info(json.dumps(entry, indent=2, default=str))


def log_classification(query: str, classification: Any):
    """Log just the classification step."""
    logger.debug(
        f"CLASSIFY | query={query!r} | result={json.dumps(_safe_serialize(classification), default=str)}"
    )


def log_kb_search(domain: str, issue: str, context: Optional[str], found: bool, match_conf: float):
    """Log a KB search attempt."""
    logger.debug(
        f"KB_SEARCH | domain={domain} | issue={issue} | context={context} | found={found} | match_conf={match_conf:.2f}"
    )
