"""
Onboarding router — 11-step wizard API with per-step save and completion tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_verified_user
from app.models import User
from app.schemas.onboarding import (
    PersonalInfoIn, ContactInfoIn, AddressesIn, EducationListIn,
    ExperienceListIn, SkillsListIn, ProjectsListIn, CertificationsListIn,
    PreferencesIn, ProfessionalLinksIn, OnboardingStatusOut
)
import app.services.onboarding_service as svc

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/status", response_model=OnboardingStatusOut)
async def get_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    return await svc.get_onboarding_status(db, user)


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_onboarding(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.get_or_create_profile_completion(db, user.id)
    await db.commit()
    return {"message": "Onboarding started"}


@router.patch("/personal")
async def save_personal(
    data: PersonalInfoIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_personal(db, user, data)
    await db.commit()
    return {"message": "Personal info saved"}


@router.patch("/contact")
async def save_contact(
    data: ContactInfoIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_contact(db, user, data)
    await db.commit()
    return {"message": "Contact info saved"}


@router.patch("/addresses")
async def save_addresses(
    data: AddressesIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_addresses(db, user, data)
    await db.commit()
    return {"message": "Addresses saved"}


@router.patch("/education")
async def save_education(
    data: EducationListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_education(db, user, data)
    await db.commit()
    return {"message": "Education saved"}


@router.patch("/experience")
async def save_experience(
    data: ExperienceListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_experience(db, user, data)
    await db.commit()
    return {"message": "Experience saved"}


@router.patch("/skills")
async def save_skills(
    data: SkillsListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_skills(db, user, data)
    await db.commit()
    return {"message": "Skills saved"}


@router.patch("/projects")
async def save_projects(
    data: ProjectsListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_projects(db, user, data)
    await db.commit()
    return {"message": "Projects saved"}


@router.patch("/certifications")
async def save_certifications(
    data: CertificationsListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_certifications(db, user, data)
    await db.commit()
    return {"message": "Certifications saved"}


@router.patch("/preferences")
async def save_preferences(
    data: PreferencesIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_preferences(db, user, data)
    await db.commit()
    return {"message": "Preferences saved"}


@router.patch("/professional-links")
async def save_professional_links(
    data: ProfessionalLinksIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.save_professional_links(db, user, data)
    await db.commit()
    return {"message": "Professional links saved"}


@router.post("/complete")
async def complete_onboarding(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    await svc.mark_complete(db, user)
    await db.commit()
    return {"message": "Account setup complete", "setup_complete": True}
