"""
Diagnostic state model for tracking multi-round troubleshooting sessions.

This is a lightweight Pydantic model — not a complicated state-management framework.

Extended in v5.1 to support:
- Diagnostic slot tracking (filled_slots)
- Slot-question tracking (pending_slot_question)
- Question source tracking (question_source: 'tree' | 'slot')
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class DiagnosticState(BaseModel):
    """Tracks the full state of a diagnostic conversation."""
    session_id: str
    original_query: str
    device: Optional[str] = None

    # Extracted from user query + follow-up answers
    symptoms: List[str] = Field(default_factory=list)
    contexts: List[str] = Field(default_factory=list)

    # Diagnostic progress
    candidate_issues: List[str] = Field(default_factory=list)  # e.g. ["battery/fast_drain"]
    confirmed_issues: List[str] = Field(default_factory=list)
    current_domain: Optional[str] = None
    current_issue: Optional[str] = None

    # Conversation history
    questions_asked: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    actions_taken: List[str] = Field(default_factory=list)

    # Decision engine state
    current_tree: Optional[str] = None
    current_node: str = "entry_question"

    # v5.1: Diagnostic slot tracking
    filled_slots: Dict[str, str] = Field(default_factory=dict)
    pending_slot_question: Optional[str] = None  # slot name being asked
    slot_question_options: Optional[List[dict]] = None  # options for current slot question
    question_source: str = "tree"  # "tree" or "slot" — which system generated the current question
    unanswered_slots: List[str] = Field(default_factory=list)  # slots user said "don't know" for

    # Status
    status: str = "diagnosing"  # "diagnosing", "resolved", "no_match"
    round_count: int = 0
    created_at: float = Field(default_factory=lambda: __import__("time").time())

    def add_symptom(self, symptom: str):
        if symptom and symptom not in self.symptoms:
            self.symptoms.append(symptom)

    def add_context(self, context: str):
        if context and context not in self.contexts:
            self.contexts.append(context)

    def add_candidate(self, domain: str, issue: str):
        key = f"{domain}/{issue}"
        if key not in self.candidate_issues:
            self.candidate_issues.append(key)

    def confirm_issue(self, domain: str, issue: str):
        key = f"{domain}/{issue}"
        if key not in self.confirmed_issues:
            self.confirmed_issues.append(key)

    def fill_slot(self, slot_name: str, slot_value: str):
        """Record a filled diagnostic slot."""
        self.filled_slots[slot_name] = slot_value
        # Remove from unanswered if it was previously marked
        if slot_name in self.unanswered_slots:
            self.unanswered_slots.remove(slot_name)

    def mark_slot_unanswered(self, slot_name: str):
        """Mark a slot as unanswered (user said 'not sure')."""
        if slot_name not in self.unanswered_slots:
            self.unanswered_slots.append(slot_name)
