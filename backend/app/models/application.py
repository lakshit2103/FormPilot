from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApplicationSession(Base):
    __tablename__ = "application_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_query: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    selected_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_search_results.id", use_alter=True, name="fk_app_session_job"), nullable=True)
    current_url: Mapped[str | None] = mapped_column(String(2000))
    current_node: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="created")
    browser_session_id: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="application_sessions")
    selected_job = relationship("JobSearchResult", foreign_keys=[selected_job_id])
    job_results = relationship("JobSearchResult", back_populates="session", foreign_keys="JobSearchResult.session_id", cascade="all, delete-orphan")
    form_fields = relationship("DetectedFormField", back_populates="session", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="session", cascade="all, delete-orphan")
    missing_questions = relationship("MissingQuestion", back_populates="session", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="session", cascade="all, delete-orphan")
    validation_errors = relationship("ValidationError", back_populates="session", cascade="all, delete-orphan")


class JobSearchResult(Base):
    __tablename__ = "job_search_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    company: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(200))
    snippet: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(String(50))
    relevance_score: Mapped[float | None] = mapped_column(Float)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    job_status: Mapped[str | None] = mapped_column(String(50))
    search_query: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ApplicationSession", back_populates="job_results", foreign_keys=[session_id])


class DetectedFormField(Base):
    __tablename__ = "detected_form_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    field_identifier: Mapped[str | None] = mapped_column(String(500))
    field_type: Mapped[str | None] = mapped_column(String(50))
    label: Mapped[str | None] = mapped_column(String(500))
    placeholder: Mapped[str | None] = mapped_column(String(500))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    available_options: Mapped[dict | None] = mapped_column(JSONB)
    current_value: Mapped[str | None] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_name: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ApplicationSession", back_populates="form_fields")
    mapping = relationship("FieldMapping", back_populates="detected_field", uselist=False, cascade="all, delete-orphan")
    missing_question = relationship("MissingQuestion", back_populates="detected_field", uselist=False, cascade="all, delete-orphan")
    validation_errors = relationship("ValidationError", back_populates="detected_field", cascade="all, delete-orphan")


class FieldMapping(Base):
    __tablename__ = "field_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("detected_form_fields.id", ondelete="CASCADE"), unique=True, nullable=False)
    profile_source: Mapped[str | None] = mapped_column(String(100))
    profile_key: Mapped[str | None] = mapped_column(String(200))
    proposed_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    mapping_status: Mapped[str] = mapped_column(String(50), default="missing")
    reason: Mapped[str | None] = mapped_column(Text)
    user_approved: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session = relationship("ApplicationSession", back_populates="field_mappings")
    detected_field = relationship("DetectedFormField", back_populates="mapping")


class MissingQuestion(Base):
    __tablename__ = "missing_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_field_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("detected_form_fields.id", ondelete="SET NULL"), nullable=True, unique=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    field_requirements: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | answered | skipped
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session = relationship("ApplicationSession", back_populates="missing_questions")
    detected_field = relationship("DetectedFormField", back_populates="missing_question")
    answer = relationship("UserAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("missing_questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    answer_value: Mapped[str] = mapped_column(Text, nullable=False)
    save_to_profile: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ApplicationSession", back_populates="user_answers")
    question = relationship("MissingQuestion", back_populates="answer")


class ValidationError(Base):
    __tablename__ = "validation_errors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_field_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("detected_form_fields.id", ondelete="SET NULL"), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session = relationship("ApplicationSession", back_populates="validation_errors")
    detected_field = relationship("DetectedFormField", back_populates="validation_errors")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("application_sessions.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    target: Mapped[str | None] = mapped_column(String(500))
    result: Mapped[str | None] = mapped_column(String(50))
    log_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
