"""
Application session schemas — Pydantic v2 models for the job search + form-filling workflow.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Application Session ──────────────────────────────────────────────────────

class StartApplicationIn(BaseModel):
    user_query: str


class ApplicationSessionOut(BaseModel):
    id: uuid.UUID
    user_query: str
    intent: Optional[dict] = None
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    status: str
    current_node: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Intent ───────────────────────────────────────────────────────────────────

class IntentResult(BaseModel):
    intent: str  # search_and_apply | search_only | open_and_apply | fill_only | continue_application
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    skills: list[str] = []
    job_url: Optional[str] = None


# ── Job Search ────────────────────────────────────────────────────────────────

class JobSearchIn(BaseModel):
    pass  # uses intent already stored on session


class SelectJobIn(BaseModel):
    job_id: uuid.UUID


class ManualURLIn(BaseModel):
    url: str


class JobResultOut(BaseModel):
    id: uuid.UUID
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: str
    domain: Optional[str] = None
    snippet: Optional[str] = None
    source_type: str
    relevance_score: float
    is_official: bool
    job_status: str

    class Config:
        from_attributes = True


# ── Browser / Mapping ─────────────────────────────────────────────────────────

class BrowserStatusOut(BaseModel):
    session_id: uuid.UUID
    current_url: Optional[str] = None
    current_node: Optional[str] = None
    status: str
    browser_active: bool


# ── Missing Questions ─────────────────────────────────────────────────────────

class MissingQuestionOut(BaseModel):
    id: uuid.UUID
    question: str
    field_requirements: Optional[dict] = None
    original_field_label: Optional[str] = None

    class Config:
        from_attributes = True


class AnswerIn(BaseModel):
    question_id: uuid.UUID
    answer_value: str
    save_to_profile: str = "use_once"  # use_once | save_to_profile | replace_default


class AnswersIn(BaseModel):
    answers: list[AnswerIn]


# ── Review ────────────────────────────────────────────────────────────────────

class FieldMappingOut(BaseModel):
    id: uuid.UUID
    detected_field_id: Optional[uuid.UUID] = None
    field_label: Optional[str] = None
    profile_key: Optional[str] = None
    proposed_value: Optional[str] = None
    confidence: Optional[float] = None
    mapping_status: str
    reason: Optional[str] = None
    user_approved: bool

    class Config:
        from_attributes = True


class EditFieldIn(BaseModel):
    proposed_value: str
    user_approved: bool = True


class ReviewSummaryOut(BaseModel):
    session_id: uuid.UUID
    total_fields: int
    auto_filled: int
    user_provided: int
    missing: int
    low_confidence: int
    errors: int
    mappings: list[FieldMappingOut]
    validation_errors: list[dict]
