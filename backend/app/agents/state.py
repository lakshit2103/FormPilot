"""
LangGraph Agent State — shared state TypedDict for the FormPilot workflow.
"""
import uuid
from typing import TypedDict, Optional, Any
from datetime import datetime

from app.schemas.applications import IntentResult, JobResultOut


class DetectedField(TypedDict):
    field_id: str
    html_tag: str
    input_type: str
    label: str
    placeholder: str
    is_required: bool
    is_visible: bool
    is_enabled: bool
    available_options: list[str]
    current_value: str
    page_number: int
    section_name: str
    validation_constraints: dict


class FieldMapping(TypedDict):
    field_id: str
    field_label: str
    profile_key: Optional[str]
    value: Optional[str]
    confidence: float
    status: str  # ready | missing | ambiguous | unsupported | sensitive | requires_user_action | not_applicable
    reason: str


class MissingQuestion(TypedDict):
    question_id: str
    field_id: str
    question: str
    field_requirements: dict
    answer: Optional[str]
    save_to_profile: str


class AgentState(TypedDict, total=False):
    session_id: str
    user_id: str
    user_query: str
    intent: Optional[IntentResult]
    search_queries: list[str]
    raw_results: list[dict]
    ranked_results: list[dict]
    selected_job: Optional[dict]
    current_url: Optional[str]
    current_node: str
    browser_session_id: Optional[str]
    detected_fields: list[DetectedField]
    field_mappings: list[FieldMapping]
    missing_questions: list[MissingQuestion]
    user_answers: list[dict]
    validation_errors: list[dict]
    review_ready: bool
    error_message: Optional[str]
    manual_action_required: bool
    manual_action_reason: Optional[str]
    messages: list[dict]  # agent messages for the UI feed
    # Private keys used internally by agents
    _profile_data: Optional[dict]          # filtered profile (profile_retrieval_agent)
    _full_profile_data: Optional[dict]     # full raw profile (injected by service)
    _review_summary: Optional[dict]        # structured review (review_agent)
