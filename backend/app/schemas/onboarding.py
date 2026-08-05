"""
Onboarding schemas — Pydantic v2 models for all 11 wizard steps.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl


# ── Step 1: Personal ────────────────────────────────────────────────────────

class PersonalInfoIn(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    preferred_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None


# ── Step 2: Contact ─────────────────────────────────────────────────────────

class AlternateEmailIn(BaseModel):
    email: str
    email_type: str = "alternate"


class PhoneIn(BaseModel):
    country_code: str = "+91"
    phone_number: str
    phone_type: str = "primary"
    is_primary: bool = True


class ContactInfoIn(BaseModel):
    alternate_email: Optional[str] = None
    primary_phone: Optional[PhoneIn] = None
    alternate_phone: Optional[PhoneIn] = None


# ── Step 3: Addresses ───────────────────────────────────────────────────────

class AddressIn(BaseModel):
    address_type: str = "current"
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None


class AddressesIn(BaseModel):
    addresses: list[AddressIn]


# ── Step 4: Education ───────────────────────────────────────────────────────

class EducationIn(BaseModel):
    institution_name: str
    degree: str
    specialisation: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cgpa: Optional[float] = None
    percentage: Optional[float] = None
    is_current: bool = False


class EducationListIn(BaseModel):
    education: list[EducationIn]


# ── Step 5: Experience ──────────────────────────────────────────────────────

class ExperienceIn(BaseModel):
    company_name: str
    job_title: str
    employment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None


class ExperienceListIn(BaseModel):
    experience: list[ExperienceIn]
    is_fresher: bool = False


# ── Step 6: Skills ──────────────────────────────────────────────────────────

class SkillIn(BaseModel):
    skill_name: str
    proficiency_level: Optional[str] = None  # beginner | intermediate | advanced | expert
    years_of_experience: Optional[int] = None


class SkillsListIn(BaseModel):
    skills: list[SkillIn]


# ── Step 7: Projects ────────────────────────────────────────────────────────

class ProjectIn(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: Optional[str] = None
    project_url: Optional[str] = None
    repository_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectsListIn(BaseModel):
    projects: list[ProjectIn]


# ── Step 8: Certifications ──────────────────────────────────────────────────

class CertificationIn(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = None


class CertificationsListIn(BaseModel):
    certifications: list[CertificationIn]


# ── Step 9: Preferences ─────────────────────────────────────────────────────

class PreferencesIn(BaseModel):
    preferred_roles: Optional[list[str]] = None
    preferred_locations: Optional[list[str]] = None
    preferred_work_modes: Optional[list[str]] = None
    preferred_employment_types: Optional[list[str]] = None
    minimum_salary: Optional[int] = None
    notice_period: Optional[str] = None
    willing_to_relocate: Optional[bool] = None


# ── Step 10: Professional Links ─────────────────────────────────────────────

class ProfessionalLinkIn(BaseModel):
    platform: str  # linkedin | github | portfolio | kaggle | other
    url: str
    is_default: bool = False


class ProfessionalLinksIn(BaseModel):
    links: list[ProfessionalLinkIn]


# ── Onboarding Status ───────────────────────────────────────────────────────

class OnboardingStepStatus(BaseModel):
    section_name: str
    label: str
    completion_percentage: float
    is_complete: bool


class OnboardingStatusOut(BaseModel):
    setup_complete: bool
    overall_percentage: float
    steps: list[OnboardingStepStatus]
    next_incomplete_step: Optional[str] = None
