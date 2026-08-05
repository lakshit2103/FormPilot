"""
Onboarding service — handles all 11 wizard steps with per-step completion tracking.
Each save is idempotent: safe to call multiple times.
"""
import uuid
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    UserProfile, Address, Education, Experience, Skill,
    Project, Certification, JobPreference, ProfessionalLink,
    UserEmail, UserPhoneNumber, ProfileCompletion, User
)
from app.schemas.onboarding import (
    PersonalInfoIn, ContactInfoIn, AddressesIn, EducationListIn,
    ExperienceListIn, SkillsListIn, ProjectsListIn, CertificationsListIn,
    PreferencesIn, ProfessionalLinksIn, OnboardingStatusOut, OnboardingStepStatus
)

STEPS = [
    ("personal",           "Personal Info",       ["first_name", "last_name", "date_of_birth"]),
    ("contact",            "Contact Info",        ["primary_phone"]),
    ("addresses",          "Address",             ["address_line_1", "city", "country"]),
    ("education",          "Education",           ["institution_name", "degree"]),
    ("experience",         "Experience",          ["company_name", "job_title"]),
    ("skills",             "Skills",              ["skill_name"]),
    ("projects",           "Projects",            ["title"]),
    ("certifications",     "Certifications",      ["name"]),
    ("preferences",        "Job Preferences",     ["preferred_roles", "preferred_locations"]),
    ("professional_links", "Professional Links",  ["url"]),
    ("documents",          "Documents",           []),
]


async def get_or_create_profile_completion(db: AsyncSession, user_id: uuid.UUID) -> list[ProfileCompletion]:
    result = await db.execute(select(ProfileCompletion).where(ProfileCompletion.user_id == user_id))
    existing = {r.section_name: r for r in result.scalars().all()}
    
    created = []
    for section_name, _, _ in STEPS:
        if section_name not in existing:
            pc = ProfileCompletion(
                user_id=user_id,
                section_name=section_name,
                completion_percentage=0.0,
                is_complete=False,
            )
            db.add(pc)
            created.append(pc)
    if created:
        await db.flush()
    
    result2 = await db.execute(select(ProfileCompletion).where(ProfileCompletion.user_id == user_id))
    return result2.scalars().all()


async def get_onboarding_status(db: AsyncSession, user: User) -> OnboardingStatusOut:
    completions = await get_or_create_profile_completion(db, user.id)
    comp_map = {c.section_name: c for c in completions}
    
    steps_out = []
    for section_name, label, _ in STEPS:
        pc = comp_map.get(section_name)
        pct = pc.completion_percentage if pc else 0.0
        complete = pc.is_complete if pc else False
        steps_out.append(OnboardingStepStatus(
            section_name=section_name,
            label=label,
            completion_percentage=pct,
            is_complete=complete,
        ))
    
    overall = sum(s.completion_percentage for s in steps_out) / len(steps_out)
    next_step = next((s.section_name for s in steps_out if not s.is_complete), None)
    
    return OnboardingStatusOut(
        setup_complete=user.setup_complete,
        overall_percentage=overall,
        steps=steps_out,
        next_incomplete_step=next_step,
    )


async def _set_completion(db: AsyncSession, user_id: uuid.UUID, section: str, pct: float, complete: bool):
    result = await db.execute(
        select(ProfileCompletion).where(
            ProfileCompletion.user_id == user_id,
            ProfileCompletion.section_name == section
        )
    )
    pc = result.scalar_one_or_none()
    if pc:
        pc.completion_percentage = pct
        pc.is_complete = complete
        pc.updated_at = datetime.utcnow()
    else:
        pc = ProfileCompletion(user_id=user_id, section_name=section, completion_percentage=pct, is_complete=complete)
        db.add(pc)


async def save_personal(db: AsyncSession, user: User, data: PersonalInfoIn):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    
    profile.date_of_birth = data.date_of_birth
    profile.gender = data.gender
    profile.nationality = data.nationality if hasattr(profile, 'nationality') else None
    
    # Update user full_name components stored on user
    if data.first_name and data.last_name:
        parts = [data.first_name]
        if data.middle_name:
            parts.append(data.middle_name)
        parts.append(data.last_name)
        user.full_name = " ".join(parts)
    
    await db.flush()
    filled = sum([
        bool(data.first_name), bool(data.last_name), bool(data.date_of_birth),
        bool(data.gender), bool(data.nationality)
    ])
    pct = (filled / 5) * 100
    await _set_completion(db, user.id, "personal", pct, pct >= 60)


async def save_contact(db: AsyncSession, user: User, data: ContactInfoIn):
    # Alternate email
    if data.alternate_email:
        result = await db.execute(
            select(UserEmail).where(UserEmail.user_id == user.id, UserEmail.is_primary == False)
        )
        alt = result.scalar_one_or_none()
        if not alt:
            alt = UserEmail(user_id=user.id, email=data.alternate_email, email_type="alternate", is_primary=False)
            db.add(alt)
        else:
            alt.email = data.alternate_email

    # Phones
    for phone_data in [data.primary_phone, data.alternate_phone]:
        if not phone_data:
            continue
        result = await db.execute(
            select(UserPhoneNumber).where(
                UserPhoneNumber.user_id == user.id,
                UserPhoneNumber.is_primary == phone_data.is_primary
            )
        )
        phone = result.scalar_one_or_none()
        if not phone:
            phone = UserPhoneNumber(
                user_id=user.id,
                country_code=phone_data.country_code,
                phone_number=phone_data.phone_number,
                phone_type=phone_data.phone_type,
                is_primary=phone_data.is_primary,
            )
            db.add(phone)
        else:
            phone.phone_number = phone_data.phone_number
            phone.country_code = phone_data.country_code
    
    await db.flush()
    pct = 100.0 if data.primary_phone else 50.0
    await _set_completion(db, user.id, "contact", pct, pct >= 100)


async def save_addresses(db: AsyncSession, user: User, data: AddressesIn):
    # Delete old addresses and replace
    await db.execute(delete(Address).where(Address.user_id == user.id))
    for addr in data.addresses:
        a = Address(
            user_id=user.id,
            address_type=addr.address_type,
            address_line_1=addr.address_line_1,
            address_line_2=addr.address_line_2,
            city=addr.city,
            state=addr.state,
            country=addr.country,
            postal_code=addr.postal_code,
        )
        db.add(a)
    await db.flush()
    pct = 100.0 if data.addresses else 0.0
    await _set_completion(db, user.id, "addresses", pct, pct >= 100)


async def save_education(db: AsyncSession, user: User, data: EducationListIn):
    await db.execute(delete(Education).where(Education.user_id == user.id))
    for edu in data.education:
        e = Education(
            user_id=user.id,
            institution_name=edu.institution_name,
            degree=edu.degree,
            specialisation=edu.specialisation,
            start_date=edu.start_date,
            end_date=edu.end_date,
            cgpa=edu.cgpa,
            percentage=edu.percentage,
            is_current=edu.is_current,
        )
        db.add(e)
    await db.flush()
    pct = 100.0 if data.education else 0.0
    await _set_completion(db, user.id, "education", pct, pct >= 100)


async def save_experience(db: AsyncSession, user: User, data: ExperienceListIn):
    await db.execute(delete(Experience).where(Experience.user_id == user.id))
    for exp in data.experience:
        e = Experience(
            user_id=user.id,
            company_name=exp.company_name,
            job_title=exp.job_title,
            employment_type=exp.employment_type,
            location=exp.location,
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=exp.is_current,
            description=exp.description,
        )
        db.add(e)
    await db.flush()
    pct = 100.0 if (data.experience or data.is_fresher) else 0.0
    await _set_completion(db, user.id, "experience", pct, pct >= 100)


async def save_skills(db: AsyncSession, user: User, data: SkillsListIn):
    await db.execute(delete(Skill).where(Skill.user_id == user.id))
    for sk in data.skills:
        s = Skill(
            user_id=user.id,
            skill_name=sk.skill_name,
            proficiency_level=sk.proficiency_level,
            years_of_experience=sk.years_of_experience,
        )
        db.add(s)
    await db.flush()
    pct = min(100.0, len(data.skills) * 20)
    await _set_completion(db, user.id, "skills", pct, len(data.skills) >= 3)


async def save_projects(db: AsyncSession, user: User, data: ProjectsListIn):
    await db.execute(delete(Project).where(Project.user_id == user.id))
    for proj in data.projects:
        p = Project(
            user_id=user.id,
            title=proj.title,
            description=proj.description,
            technologies=proj.technologies,
            project_url=proj.project_url,
            repository_url=proj.repository_url,
            start_date=proj.start_date,
            end_date=proj.end_date,
        )
        db.add(p)
    await db.flush()
    pct = 100.0 if data.projects else 0.0
    await _set_completion(db, user.id, "projects", pct, pct >= 100)


async def save_certifications(db: AsyncSession, user: User, data: CertificationsListIn):
    await db.execute(delete(Certification).where(Certification.user_id == user.id))
    for cert in data.certifications:
        c = Certification(
            user_id=user.id,
            name=cert.name,
            issuing_organization=cert.issuing_organization,
            issue_date=cert.issue_date,
            expiry_date=cert.expiry_date,
            credential_url=cert.credential_url,
        )
        db.add(c)
    await db.flush()
    pct = 100.0 if data.certifications else 0.0
    await _set_completion(db, user.id, "certifications", pct, pct >= 100)


async def save_preferences(db: AsyncSession, user: User, data: PreferencesIn):
    result = await db.execute(select(JobPreference).where(JobPreference.user_id == user.id))
    pref = result.scalar_one_or_none()
    if not pref:
        pref = JobPreference(user_id=user.id)
        db.add(pref)
    
    if data.preferred_roles is not None:
        pref.preferred_roles = data.preferred_roles
    if data.preferred_locations is not None:
        pref.preferred_locations = data.preferred_locations
    if data.preferred_work_modes is not None:
        pref.preferred_work_modes = data.preferred_work_modes
    if data.preferred_employment_types is not None:
        pref.preferred_employment_types = data.preferred_employment_types
    if data.minimum_salary is not None:
        pref.minimum_salary = data.minimum_salary
    if data.notice_period is not None:
        pref.notice_period = data.notice_period
    if data.willing_to_relocate is not None:
        pref.willing_to_relocate = data.willing_to_relocate
    
    await db.flush()
    filled = sum([
        bool(data.preferred_roles), bool(data.preferred_locations),
        bool(data.preferred_work_modes), bool(data.notice_period)
    ])
    pct = (filled / 4) * 100
    await _set_completion(db, user.id, "preferences", pct, pct >= 75)


async def save_professional_links(db: AsyncSession, user: User, data: ProfessionalLinksIn):
    await db.execute(delete(ProfessionalLink).where(ProfessionalLink.user_id == user.id))
    for link in data.links:
        pl = ProfessionalLink(
            user_id=user.id,
            platform=link.platform,
            url=link.url,
            is_default=link.is_default,
        )
        db.add(pl)
    await db.flush()
    pct = 100.0 if data.links else 0.0
    await _set_completion(db, user.id, "professional_links", pct, pct >= 100)


async def mark_complete(db: AsyncSession, user: User):
    user.setup_complete = True
    await db.flush()
