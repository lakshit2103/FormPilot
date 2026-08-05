from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl


# ─── Profile ──────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    primary_phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    nationality: Optional[str]
    primary_phone: Optional[str]
    alternate_phone: Optional[str]
    current_city: Optional[str]
    current_state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    model_config = {"from_attributes": True}


# ─── Education ────────────────────────────────────────────────────────────────

class EducationCreate(BaseModel):
    education_level: Optional[str] = None
    institution_name: Optional[str] = None
    board_or_university: Optional[str] = None
    degree: Optional[str] = None
    specialisation: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cgpa: Optional[float] = None
    percentage: Optional[float] = None
    is_current: bool = False


class EducationResponse(EducationCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Experience ───────────────────────────────────────────────────────────────

class ExperienceCreate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    is_not_applicable: bool = False
    description: Optional[str] = None
    technologies: Optional[str] = None


class ExperienceResponse(ExperienceCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Skill ────────────────────────────────────────────────────────────────────

class SkillCreate(BaseModel):
    skill_name: str
    category: Optional[str] = None
    proficiency_level: Optional[str] = None
    years_of_experience: Optional[float] = None


class SkillResponse(SkillCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Project ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    contribution: Optional[str] = None
    technologies: Optional[str] = None
    project_url: Optional[str] = None
    repository_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(ProjectCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Certification ────────────────────────────────────────────────────────────

class CertificationCreate(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class CertificationResponse(CertificationCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Address ──────────────────────────────────────────────────────────────────

class AddressCreate(BaseModel):
    address_type: str = "current"
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None


class AddressResponse(AddressCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Preferences ──────────────────────────────────────────────────────────────

class PreferencesUpdate(BaseModel):
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_industries: Optional[List[str]] = None
    preferred_work_modes: Optional[List[str]] = None
    preferred_employment_types: Optional[List[str]] = None
    minimum_salary: Optional[int] = None
    notice_period: Optional[str] = None
    joining_date: Optional[str] = None
    willing_to_relocate: Optional[bool] = None
    willing_to_travel: Optional[bool] = None
    shift_preference: Optional[str] = None
    expected_salary: Optional[int] = None


class PreferencesResponse(PreferencesUpdate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Professional Link ────────────────────────────────────────────────────────

class ProfessionalLinkCreate(BaseModel):
    platform: str
    url: str
    is_default: bool = False


class ProfessionalLinkResponse(ProfessionalLinkCreate):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}


# ─── Profile Completion ───────────────────────────────────────────────────────

class SectionCompletion(BaseModel):
    section_name: str
    completion_percentage: float
    is_complete: bool
    model_config = {"from_attributes": True}


class ProfileCompletionResponse(BaseModel):
    overall_percentage: float
    sections: List[SectionCompletion]
