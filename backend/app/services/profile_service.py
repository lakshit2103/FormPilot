from __future__ import annotations

import uuid
from typing import Any, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.profile import UserProfile, UserEmail, UserPhoneNumber
from app.models.address import Address
from app.models.education import Education
from app.models.experience import Experience
from app.models.skills import Skill
from app.models.projects import Project
from app.models.certifications import Certification
from app.models.preferences import JobPreference
from app.models.professional_links import ProfessionalLink
from app.models.profile_meta import ProfileCompletion

T = TypeVar("T")


async def _get_or_404(db: AsyncSession, model: Type[T], item_id: uuid.UUID, user_id: uuid.UUID) -> T:
    result = await db.execute(select(model).where(model.id == item_id, model.user_id == user_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found.")
    return obj


class ProfileService:

    # ─── Personal Profile ──────────────────────────────────────────────────────

    async def get_or_create_profile(self, db: AsyncSession, user: User) -> UserProfile:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    async def update_profile(self, db: AsyncSession, user: User, data: dict) -> UserProfile:
        profile = await self.get_or_create_profile(db, user)
        for k, v in data.items():
            if v is not None:
                setattr(profile, k, v)
        # Also update full_name on user record
        if "first_name" in data or "last_name" in data:
            first = data.get("first_name") or profile.first_name or ""
            last = data.get("last_name") or profile.last_name or ""
            user.full_name = f"{first} {last}".strip() or user.full_name
        await db.commit()
        await db.refresh(profile)
        await self._recalculate_completion(db, user.id, "personal")
        return profile

    # ─── Generic list/create/update/delete helpers ────────────────────────────

    async def list_items(self, db: AsyncSession, model: Type[T], user_id: uuid.UUID) -> list[T]:
        result = await db.execute(select(model).where(model.user_id == user_id))
        return list(result.scalars().all())

    async def create_item(self, db: AsyncSession, model: Type[T], user_id: uuid.UUID, data: dict) -> T:
        obj = model(user_id=user_id, **data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update_item(self, db: AsyncSession, model: Type[T], item_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> T:
        obj = await _get_or_404(db, model, item_id, user_id)
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete_item(self, db: AsyncSession, model: Type[T], item_id: uuid.UUID, user_id: uuid.UUID) -> None:
        obj = await _get_or_404(db, model, item_id, user_id)
        await db.delete(obj)
        await db.commit()

    # ─── Preferences (singleton per user) ─────────────────────────────────────

    async def get_or_create_preferences(self, db: AsyncSession, user_id: uuid.UUID) -> JobPreference:
        result = await db.execute(select(JobPreference).where(JobPreference.user_id == user_id))
        prefs = result.scalar_one_or_none()
        if not prefs:
            prefs = JobPreference(user_id=user_id)
            db.add(prefs)
            await db.commit()
            await db.refresh(prefs)
        return prefs

    async def update_preferences(self, db: AsyncSession, user_id: uuid.UUID, data: dict) -> JobPreference:
        prefs = await self.get_or_create_preferences(db, user_id)
        for k, v in data.items():
            if v is not None:
                setattr(prefs, k, v)
        await db.commit()
        await db.refresh(prefs)
        await self._recalculate_completion(db, user_id, "preferences")
        return prefs

    # ─── Profile Completion ────────────────────────────────────────────────────

    async def get_completion(self, db: AsyncSession, user_id: uuid.UUID) -> list[ProfileCompletion]:
        result = await db.execute(
            select(ProfileCompletion).where(ProfileCompletion.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _recalculate_completion(self, db: AsyncSession, user_id: uuid.UUID, section: str) -> None:
        """Simple heuristic completion calculation per section."""
        result = await db.execute(
            select(ProfileCompletion).where(
                ProfileCompletion.user_id == user_id,
                ProfileCompletion.section_name == section,
            )
        )
        pc = result.scalar_one_or_none()
        if not pc:
            return
        # Check if any items exist for list sections
        list_sections = {
            "education": Education,
            "experience": Experience,
            "skills": Skill,
            "projects": Project,
            "certifications": Certification,
            "addresses": Address,
            "professional_links": ProfessionalLink,
        }
        if section in list_sections:
            model = list_sections[section]
            count_result = await db.execute(select(model).where(model.user_id == user_id))
            count = len(count_result.scalars().all())
            pct = 100.0 if count > 0 else 0.0
        else:
            pct = 50.0  # updated but may not be fully filled
        pc.completion_percentage = pct
        pc.is_complete = pct >= 100.0
        await db.commit()


profile_service = ProfileService()
