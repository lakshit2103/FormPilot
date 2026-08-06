"""
Settings & Privacy Service — account management, sessions, data export and consent.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.auth_tokens import UserSession
from app.core.security import hash_password, verify_password


async def get_account_info(db: AsyncSession, user: User) -> dict:
    """Return safe account details for the settings page."""
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "email_verified": user.is_email_verified,
        "setup_complete": user.setup_complete,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


async def update_display_name(
    db: AsyncSession, user: User, new_name: str
) -> User:
    """Update the user's display name."""
    user.full_name = new_name.strip()
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> tuple[bool, str]:
    """
    Verify current password and update to new password.
    Returns (success, message).
    """
    if not verify_password(current_password, user.password_hash):
        return False, "Current password is incorrect."

    if len(new_password) < 8:
        return False, "New password must be at least 8 characters."

    user.password_hash = hash_password(new_password)
    await db.commit()
    return True, "Password updated successfully."


async def list_active_sessions(db: AsyncSession, user: User) -> list[dict]:
    """Return all active refresh sessions for the user."""
    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at == None,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .order_by(UserSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "session_id": str(s.id),
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "is_current": False,
        }
        for s in sessions
    ]


async def revoke_session(
    db: AsyncSession, user: User, session_id: uuid.UUID
) -> bool:
    """Revoke a specific refresh session. Returns True if found and revoked."""
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return False
    session.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return True


async def revoke_all_sessions(db: AsyncSession, user: User) -> int:
    """Revoke all active refresh sessions for the user. Returns count revoked."""
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at == None,
        )
    )
    sessions = result.scalars().all()
    now = datetime.now(timezone.utc)
    for s in sessions:
        s.revoked_at = now
    await db.commit()
    return len(sessions)


async def export_user_data(db: AsyncSession, user: User) -> dict:
    """
    Build a portable JSON export of all user data.
    Excludes password_hash, tokens and internal IDs for security.
    """
    from app.models.profile import UserProfile
    from app.models.education import Education
    from app.models.experience import Experience
    from app.models.skills import Skill
    from app.models.projects import Project
    from app.models.certifications import Certification
    from app.models.preferences import JobPreference
    from app.models.professional_links import ProfessionalLink
    from app.models.address import Address
    from app.models.documents import Document
    from app.models.application import ApplicationSession

    async def fetch_all(model, **where):
        r = await db.execute(select(model).filter_by(**where))
        return r.scalars().all()

    profile = await db.execute(select(UserProfile).filter_by(user_id=user.id))
    profile = profile.scalar_one_or_none()

    education = await fetch_all(Education, user_id=user.id)
    experience = await fetch_all(Experience, user_id=user.id)
    skills = await fetch_all(Skill, user_id=user.id)
    projects = await fetch_all(Project, user_id=user.id)
    certs = await fetch_all(Certification, user_id=user.id)
    addresses = await fetch_all(Address, user_id=user.id)
    links = await fetch_all(ProfessionalLink, user_id=user.id)
    documents = await fetch_all(Document, user_id=user.id)
    sessions = await fetch_all(ApplicationSession, user_id=user.id)

    return {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "account": {
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "profile": {
            "date_of_birth": str(profile.date_of_birth) if profile and profile.date_of_birth else None,
            "gender": profile.gender if profile else None,
            "nationality": profile.nationality if profile else None,
        } if profile else {},
        "education": [
            {
                "institution": e.institution_name,
                "degree": e.degree,
                "specialisation": e.specialisation,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "cgpa": str(e.cgpa) if e.cgpa else None,
            }
            for e in education
        ],
        "experience": [
            {
                "company": e.company_name,
                "title": e.job_title,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "is_current": e.is_current,
            }
            for e in experience
        ],
        "skills": [s.skill_name for s in skills],
        "projects": [p.title for p in projects],
        "certifications": [c.name for c in certs],
        "addresses": [
            {"type": a.address_type, "city": a.city, "state": a.state, "country": a.country}
            for a in addresses
        ],
        "professional_links": [{"platform": l.platform, "url": l.url} for l in links],
        "documents": [
            {"type": d.document_type, "filename": d.original_filename, "is_default": d.is_default}
            for d in documents
        ],
        "application_sessions": [
            {
                "query": s.user_query,
                "company": s.company,
                "role": s.role,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    }


async def delete_account(db: AsyncSession, user: User, password: str) -> tuple[bool, str]:
    """
    Permanently delete the user account after password confirmation.
    Returns (success, message).
    """
    if not verify_password(password, user.password_hash):
        return False, "Password is incorrect. Account not deleted."

    # Cascade deletes handle all related records via FK constraints
    await db.delete(user)
    await db.commit()
    return True, "Account and all associated data permanently deleted."
