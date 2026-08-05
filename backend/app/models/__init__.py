# Import all models here so Alembic can discover them via metadata
from app.models.user import User  # noqa: F401
from app.models.auth_tokens import EmailVerificationToken, PasswordResetToken, UserSession  # noqa: F401
from app.models.profile import UserProfile, UserEmail, UserPhoneNumber  # noqa: F401
from app.models.address import Address  # noqa: F401
from app.models.education import Education  # noqa: F401
from app.models.experience import Experience  # noqa: F401
from app.models.skills import Skill  # noqa: F401
from app.models.projects import Project  # noqa: F401
from app.models.certifications import Certification  # noqa: F401
from app.models.preferences import JobPreference  # noqa: F401
from app.models.professional_links import ProfessionalLink  # noqa: F401
from app.models.documents import Document  # noqa: F401
from app.models.profile_meta import ProfileFieldSource, UserConsent, ProfileCompletion  # noqa: F401
from app.models.application import (  # noqa: F401
    ApplicationSession,
    JobSearchResult,
    DetectedFormField,
    FieldMapping,
    MissingQuestion,
    UserAnswer,
    ValidationError,
    AuditLog,
)
