from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JobPreference(Base):
    __tablename__ = "job_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_locations: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_industries: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_work_modes: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # remote | hybrid | onsite
    preferred_employment_types: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # full_time | part_time | contract | internship
    minimum_salary: Mapped[int | None] = mapped_column(Integer)
    notice_period: Mapped[str | None] = mapped_column(String(100))  # e.g. "Immediate" | "1 month" | "2 months"
    joining_date: Mapped[str | None] = mapped_column(String(100))
    willing_to_relocate: Mapped[bool | None] = mapped_column(Boolean)
    willing_to_travel: Mapped[bool | None] = mapped_column(Boolean)
    shift_preference: Mapped[str | None] = mapped_column(String(100))
    expected_salary: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")
