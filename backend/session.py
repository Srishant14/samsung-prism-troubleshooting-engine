"""
Simple in-memory session management for diagnostic conversations.
Sessions expire after 10 minutes. No external dependencies needed.
"""
import time
from typing import Dict, Optional

from diagnostic_state import DiagnosticState

# Sessions expire after 10 minutes
SESSION_TTL_SECONDS = 600
MAX_ROUNDS = 5  # max diagnostic steps as per spec


# In-memory session store
_sessions: Dict[str, DiagnosticState] = {}


def create_session(
    original_query: str,
    domain: Optional[str] = None,
    tree: Optional[str] = None,
    symptoms: list = None,
) -> DiagnosticState:
    """Create a new diagnostic session."""
    import uuid
    _cleanup_expired()

    session_id = uuid.uuid4().hex[:12]
    session = DiagnosticState(
        session_id=session_id,
        original_query=original_query,
        current_domain=domain,
        current_tree=tree or domain,
        symptoms=symptoms or [],
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[DiagnosticState]:
    """Retrieve a session by ID. Returns None if expired or not found."""
    _cleanup_expired()
    session = _sessions.get(session_id)
    if session and not _is_expired(session):
        return session
    # Remove expired
    if session_id in _sessions:
        del _sessions[session_id]
    return None


def delete_session(session_id: str):
    """Remove a session."""
    _sessions.pop(session_id, None)


def has_rounds_left(session: DiagnosticState) -> bool:
    """Check if the session can ask more questions."""
    return session.round_count < MAX_ROUNDS


def _is_expired(session: DiagnosticState) -> bool:
    """Check if a session has expired."""
    return (time.time() - session.created_at) > SESSION_TTL_SECONDS


def _cleanup_expired():
    """Remove all expired sessions."""
    expired = [sid for sid, s in _sessions.items() if _is_expired(s)]
    for sid in expired:
        del _sessions[sid]
