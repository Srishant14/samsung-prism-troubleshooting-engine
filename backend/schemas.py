from pydantic import BaseModel
from typing import Optional, List


class TroubleshootRequest(BaseModel):
    query: Optional[str] = ""
    session_id: Optional[str] = None       # for follow-up rounds
    selected_option: Optional[int] = None  # which option user picked (0-indexed)


class IssueClassification(BaseModel):
    """A single classified issue from the LLM."""
    domain: str
    issue: str
    context: Optional[str] = None
    confidence: float


class LLMClassification(BaseModel):
    """Full classification result — may contain multiple issues."""
    issues: List[IssueClassification]


class ActionLink(BaseModel):
    label: str
    deep_link: str


class FollowUpOption(BaseModel):
    """A single option in a follow-up question."""
    label: str
    index: int


class FollowUpQuestion(BaseModel):
    """A diagnostic follow-up question with clickable options."""
    text: str
    options: List[FollowUpOption]
    round_number: int  # 1-based, max 5
    max_rounds: int = 5
    category: Optional[str] = None
    category_confidence: Optional[float] = None


class IssueResult(BaseModel):
    """Result for a single detected issue."""
    domain: str
    issue: str
    confidence: float           # LLM classification confidence
    match_confidence: float     # KB retrieval match quality
    final_confidence: float     # Combined confidence
    title: Optional[str] = None
    steps: Optional[List[str]] = None
    action: Optional[ActionLink] = None
    source: Optional[str] = None
    source_type: Optional[str] = None


class TroubleshootResponse(BaseModel):
    status: str  # "success", "no_match", "follow_up"
    results: List[IssueResult] = []
    message: Optional[str] = None
    # Diagnostic flow fields
    session_id: Optional[str] = None
    follow_up: Optional[FollowUpQuestion] = None
    # Legacy single-issue fields kept for backward compat
    domain: Optional[str] = None
    issue: Optional[str] = None
    confidence: Optional[float] = None
    title: Optional[str] = None
    steps: Optional[List[str]] = None
    action: Optional[ActionLink] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
