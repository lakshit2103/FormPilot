from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.deps import DBSession, CurrentUser
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, LogoutRequest,
    ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest,
    ResendVerificationRequest, UserResponse,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DBSession):
    user = await auth_service.register(db, body.full_name, body.email, body.password)
    return user


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(body: VerifyEmailRequest, db: DBSession):
    user = await auth_service.verify_email(db, body.token)
    return user


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(body: ResendVerificationRequest, db: DBSession):
    await auth_service.resend_verification(db, body.email)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DBSession):
    result = await auth_service.login(db, body.email, body.password)
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        setup_complete=result["user"].setup_complete,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DBSession):
    result = await auth_service.refresh(db, body.refresh_token)
    return TokenResponse(**result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, db: DBSession):
    await auth_service.logout(db, body.refresh_token)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(body: ForgotPasswordRequest, db: DBSession):
    await auth_service.forgot_password(db, body.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(body: ResetPasswordRequest, db: DBSession):
    await auth_service.reset_password(db, body.token, body.new_password)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return current_user
