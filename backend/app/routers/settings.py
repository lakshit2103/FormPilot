"""
Settings & Privacy Router — account management, sessions, data export and consent.
PRD §22 (Settings and Privacy page).
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_verified_user
from app.models.user import User
import app.services.settings_service as svc

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── Request / Response Schemas ────────────────────────────────────────────────

class UpdateNameIn(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class RevokeSessionIn(BaseModel):
    session_id: uuid.UUID


class DeleteAccountIn(BaseModel):
    password: str = Field(..., min_length=1)
    confirmation: str = Field(..., description="Must be 'DELETE' to confirm")


# ── Account Endpoints ─────────────────────────────────────────────────────────

@router.get("/account")
async def get_account(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Return account details for the settings page."""
    return await svc.get_account_info(db, user)


@router.patch("/account/name")
async def update_name(
    data: UpdateNameIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Update the user's display name."""
    updated = await svc.update_display_name(db, user, data.full_name)
    return {"message": "Name updated", "full_name": updated.full_name}


@router.post("/account/change-password")
async def change_password(
    data: ChangePasswordIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Change the account password after verifying the current one."""
    success, message = await svc.change_password(
        db, user, data.current_password, data.new_password
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": message}


# ── Session Management ────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """List all active refresh sessions for the current user."""
    return await svc.list_active_sessions(db, user)


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Revoke a specific session by ID."""
    success = await svc.revoke_session(db, user, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session revoked"}


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Revoke all active sessions (sign out everywhere)."""
    count = await svc.revoke_all_sessions(db, user)
    return {"message": f"Revoked {count} session(s)"}


# ── Data Export ───────────────────────────────────────────────────────────────

@router.get("/data-export")
async def export_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """
    Export all user data as JSON (GDPR-style data portability).
    Excludes password hashes, tokens and raw file contents.
    """
    data = await svc.export_user_data(db, user)
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": 'attachment; filename="formpilot-export.json"',
        },
    )


# ── Account Deletion ──────────────────────────────────────────────────────────

@router.delete("/account")
async def delete_account(
    data: DeleteAccountIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """
    Permanently delete the user account and all associated data.
    Requires password confirmation and the literal string 'DELETE'.
    """
    if data.confirmation != "DELETE":
        raise HTTPException(
            status_code=400,
            detail="Confirmation must be the string 'DELETE'",
        )

    success, message = await svc.delete_account(db, user, data.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message}
