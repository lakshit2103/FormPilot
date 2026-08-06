from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import (
    hash_password, verify_password, generate_secure_token, hash_token,
    create_access_token, create_refresh_token,
)
from app.core.email import send_verification_email, send_password_reset_email
from app.core.config import settings
from app.models.user import User
from app.models.auth_tokens import EmailVerificationToken, PasswordResetToken, UserSession
from app.models.profile_meta import ProfileCompletion


ONBOARDING_SECTIONS = [
    "personal", "contact", "addresses", "education", "experience",
    "skills", "projects", "certifications", "preferences", "professional_links", "documents"
]


class AuthService:

    # ─── Register ──────────────────────────────────────────────────────────────

    async def register(self, db: AsyncSession, full_name: str, email: str, password: str) -> User:
        # Check uniqueness
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
        )
        db.add(user)
        await db.flush()  # get the user.id

        # Create profile_completion rows for each onboarding section
        for section in ONBOARDING_SECTIONS:
            db.add(ProfileCompletion(user_id=user.id, section_name=section))

        # Create and store email verification token
        plain_token = generate_secure_token()
        db.add(EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(plain_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))

        await db.commit()
        await db.refresh(user)

        # Send verification email (non-blocking best-effort)
        await send_verification_email(to=user.email, full_name=user.full_name, token=plain_token)

        return user

    # ─── Verify Email ──────────────────────────────────────────────────────────

    async def verify_email(self, db: AsyncSession, token: str) -> User:
        token_hash = hash_token(token)
        result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.expires_at > datetime.now(timezone.utc),
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link.")

        # Mark token used
        token_record.used_at = datetime.now(timezone.utc)

        # Mark user verified
        user_result = await db.execute(select(User).where(User.id == token_record.user_id))
        user = user_result.scalar_one()
        user.is_email_verified = True

        await db.commit()
        await db.refresh(user)
        return user

    # ─── Resend Verification ───────────────────────────────────────────────────

    async def resend_verification(self, db: AsyncSession, email: str) -> None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or user.is_email_verified:
            return  # Silently ignore to prevent email enumeration

        plain_token = generate_secure_token()
        db.add(EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(plain_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))
        await db.commit()
        await send_verification_email(to=user.email, full_name=user.full_name, token=plain_token)

    # ─── Login ─────────────────────────────────────────────────────────────────

    async def login(self, db: AsyncSession, email: str, password: str) -> dict:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")
        
        # Auto-verify email in development mode or if already verified
        if not user.is_email_verified:
            if settings.APP_ENV == "development":
                user.is_email_verified = True
                await db.commit()
                await db.refresh(user)
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified. Please check your inbox.")

        access_token = create_access_token(str(user.id))
        plain_refresh = generate_secure_token()

        db.add(UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(plain_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ))
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": plain_refresh,
            "token_type": "bearer",
            "user": user,
        }

    # ─── Refresh Token ─────────────────────────────────────────────────────────

    async def refresh(self, db: AsyncSession, refresh_token: str) -> dict:
        token_hash = hash_token(refresh_token)
        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

        # Rotate: revoke old, issue new
        session.revoked_at = datetime.now(timezone.utc)

        user_result = await db.execute(select(User).where(User.id == session.user_id))
        user = user_result.scalar_one()

        access_token = create_access_token(str(user.id))
        new_plain_refresh = generate_secure_token()
        db.add(UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(new_plain_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ))
        await db.commit()

        return {"access_token": access_token, "refresh_token": new_plain_refresh, "token_type": "bearer"}

    # ─── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, db: AsyncSession, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
        session = result.scalar_one_or_none()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    # ─── Forgot Password ───────────────────────────────────────────────────────

    async def forgot_password(self, db: AsyncSession, email: str) -> None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return  # Silently ignore

        plain_token = generate_secure_token()
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(plain_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        await db.commit()
        await send_password_reset_email(to=user.email, full_name=user.full_name, token=plain_token)

    # ─── Reset Password ────────────────────────────────────────────────────────

    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> None:
        token_hash = hash_token(token)
        result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link.")

        token_record.used_at = datetime.now(timezone.utc)

        user_result = await db.execute(select(User).where(User.id == token_record.user_id))
        user = user_result.scalar_one()
        user.password_hash = hash_password(new_password)

        # Revoke all existing sessions
        sessions_result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None),
            )
        )
        for s in sessions_result.scalars():
            s.revoked_at = datetime.now(timezone.utc)

        await db.commit()


auth_service = AuthService()
