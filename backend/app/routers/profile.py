from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.deps import DBSession, VerifiedUser
from app.models.address import Address
from app.models.education import Education
from app.models.experience import Experience
from app.models.skills import Skill
from app.models.projects import Project
from app.models.certifications import Certification
from app.models.professional_links import ProfessionalLink
from app.schemas.profile import (
    ProfileUpdate, ProfileResponse,
    EducationCreate, EducationResponse,
    ExperienceCreate, ExperienceResponse,
    SkillCreate, SkillResponse,
    ProjectCreate, ProjectResponse,
    CertificationCreate, CertificationResponse,
    AddressCreate, AddressResponse,
    PreferencesUpdate, PreferencesResponse,
    ProfessionalLinkCreate, ProfessionalLinkResponse,
    ProfileCompletionResponse, SectionCompletion,
)
from app.services.profile_service import profile_service
from typing import List

router = APIRouter(prefix="/api/profile", tags=["profile"])


# ─── Personal Profile ──────────────────────────────────────────────────────────

@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: VerifiedUser, db: DBSession):
    return await profile_service.get_or_create_profile(db, current_user)


@router.put("", response_model=ProfileResponse)
async def update_profile(body: ProfileUpdate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_profile(db, current_user, body.model_dump(exclude_unset=True))


# ─── Completion ───────────────────────────────────────────────────────────────

@router.get("/completion", response_model=ProfileCompletionResponse)
async def get_completion(current_user: VerifiedUser, db: DBSession):
    sections = await profile_service.get_completion(db, current_user.id)
    total = sum(s.completion_percentage for s in sections) / max(len(sections), 1)
    return ProfileCompletionResponse(
        overall_percentage=round(total, 1),
        sections=[SectionCompletion.model_validate(s) for s in sections],
    )


# ─── Education ────────────────────────────────────────────────────────────────

@router.get("/education", response_model=List[EducationResponse])
async def list_education(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, Education, current_user.id)


@router.post("/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def create_education(body: EducationCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, Education, current_user.id, body.model_dump())


@router.patch("/education/{edu_id}", response_model=EducationResponse)
async def update_education(edu_id: uuid.UUID, body: EducationCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, Education, edu_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/education/{edu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(edu_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, Education, edu_id, current_user.id)


# ─── Experience ───────────────────────────────────────────────────────────────

@router.get("/experience", response_model=List[ExperienceResponse])
async def list_experience(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, Experience, current_user.id)


@router.post("/experience", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(body: ExperienceCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, Experience, current_user.id, body.model_dump())


@router.patch("/experience/{exp_id}", response_model=ExperienceResponse)
async def update_experience(exp_id: uuid.UUID, body: ExperienceCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, Experience, exp_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/experience/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(exp_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, Experience, exp_id, current_user.id)


# ─── Skills ───────────────────────────────────────────────────────────────────

@router.get("/skills", response_model=List[SkillResponse])
async def list_skills(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, Skill, current_user.id)


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(body: SkillCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, Skill, current_user.id, body.model_dump())


@router.patch("/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(skill_id: uuid.UUID, body: SkillCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, Skill, skill_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(skill_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, Skill, skill_id, current_user.id)


# ─── Projects ─────────────────────────────────────────────────────────────────

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, Project, current_user.id)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, Project, current_user.id, body.model_dump())


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: uuid.UUID, body: ProjectCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, Project, project_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, Project, project_id, current_user.id)


# ─── Certifications ───────────────────────────────────────────────────────────

@router.get("/certifications", response_model=List[CertificationResponse])
async def list_certs(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, Certification, current_user.id)


@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def create_cert(body: CertificationCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, Certification, current_user.id, body.model_dump())


@router.patch("/certifications/{cert_id}", response_model=CertificationResponse)
async def update_cert(cert_id: uuid.UUID, body: CertificationCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, Certification, cert_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/certifications/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cert(cert_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, Certification, cert_id, current_user.id)


# ─── Addresses ────────────────────────────────────────────────────────────────

@router.get("/addresses", response_model=List[AddressResponse])
async def list_addresses(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, Address, current_user.id)


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(body: AddressCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, Address, current_user.id, body.model_dump())


@router.patch("/addresses/{addr_id}", response_model=AddressResponse)
async def update_address(addr_id: uuid.UUID, body: AddressCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, Address, addr_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/addresses/{addr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(addr_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, Address, addr_id, current_user.id)


# ─── Preferences ──────────────────────────────────────────────────────────────

@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(current_user: VerifiedUser, db: DBSession):
    return await profile_service.get_or_create_preferences(db, current_user.id)


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(body: PreferencesUpdate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_preferences(db, current_user.id, body.model_dump(exclude_unset=True))


# ─── Professional Links ───────────────────────────────────────────────────────

@router.get("/professional-links", response_model=List[ProfessionalLinkResponse])
async def list_links(current_user: VerifiedUser, db: DBSession):
    return await profile_service.list_items(db, ProfessionalLink, current_user.id)


@router.post("/professional-links", response_model=ProfessionalLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(body: ProfessionalLinkCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.create_item(db, ProfessionalLink, current_user.id, body.model_dump())


@router.patch("/professional-links/{link_id}", response_model=ProfessionalLinkResponse)
async def update_link(link_id: uuid.UUID, body: ProfessionalLinkCreate, current_user: VerifiedUser, db: DBSession):
    return await profile_service.update_item(db, ProfessionalLink, link_id, current_user.id, body.model_dump(exclude_unset=True))


@router.delete("/professional-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(link_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await profile_service.delete_item(db, ProfessionalLink, link_id, current_user.id)
