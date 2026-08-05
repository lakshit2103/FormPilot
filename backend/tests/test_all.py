"""
Backend test suite — tests for auth, onboarding, profile, applications, and agents.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import get_db

# ── Test database setup ───────────────────────────────────────────────────────

TEST_DB_URL = "postgresql+asyncpg://formpilot:formpilot@localhost:5432/formpilot_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register, verify (skip), and login to get auth headers."""
    email = "test_user@formpilot.ai"
    password = "TestPassword123!"
    
    # Register
    resp = await client.post("/api/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "password": password,
    })
    
    # Force-verify (in test mode, skip email verification)
    # We'll use the console email to get the token
    # For now, login directly (works if email verification is disabled in test mode)
    
    login_resp = await client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        return {"Authorization": f"Bearer {data['access_token']}"}
    return {}


# ── Health Check ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Authentication ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/auth/register", json={
        "full_name": "New User",
        "email": "newuser_test@example.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code in (201, 200)


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    email = "dup@example.com"
    await client.post("/api/auth/register", json={
        "full_name": "First",
        "email": email,
        "password": "Pass123!",
    })
    resp = await client.post("/api/auth/register", json={
        "full_name": "Second",
        "email": email,
        "password": "Pass123!",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "full_name": "Wrongpass User",
        "email": "wrongpass@example.com",
        "password": "Correct123!",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


# ── Profile ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client):
    resp = await client.get("/api/profile")
    assert resp.status_code == 401


# ── Onboarding ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_onboarding_status_requires_auth(client):
    resp = await client.get("/api/onboarding/status")
    assert resp.status_code == 401


# ── Applications ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_application_requires_auth(client):
    resp = await client.post("/api/applications/start", json={"user_query": "Find me a job"})
    assert resp.status_code == 401


# ── Intent Agent ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intent_agent_fallback():
    from app.agents.intent_agent import _fallback_intent
    
    result = _fallback_intent("Find a Python developer job at Google in Bengaluru")
    assert result["intent"] in ("search_and_apply", "search_only", "fill_only", "open_and_apply")

    result2 = _fallback_intent("https://careers.google.com/jobs/123")
    assert result2["intent"] == "open_and_apply"

    result3 = _fallback_intent("Continue my previous application")
    assert result3["intent"] == "continue_application"


# ── Search Agent ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_query_generation():
    from app.agents.search_agent import _generate_queries
    
    intent = {
        "company": "TCS",
        "role": "Agentic AI Engineer",
        "location": "India",
        "skills": ["Python", "LangGraph"],
        "employment_type": "Full-time",
    }
    
    queries = _generate_queries(intent)
    assert len(queries) >= 3
    assert any("TCS" in q for q in queries)
    assert any("Agentic AI Engineer" in q for q in queries)


@pytest.mark.asyncio
async def test_url_classification():
    from app.agents.search_agent import _classify_result
    
    # Official domain
    result = _classify_result("https://careers.tcs.com/jobs/123", "Apply for TCS", "TCS")
    assert result["is_official"] or result["source_type"] in ("official", "trusted_third_party")
    
    # Suspicious content
    result = _classify_result("https://example.com", "earn per day scam work from home unlimited", None)
    assert result["job_status"] == "suspicious" or result["relevance_score"] < 10


# ── Rule-based Mapping ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rule_based_mapping():
    from app.agents.mapping_agent import _rule_based_mapping
    
    fields = [
        {"field_id": "#name", "label": "Candidate Full Name", "input_type": "text",
         "is_required": True, "is_visible": True, "is_enabled": True,
         "available_options": [], "current_value": "", "page_number": 1,
         "section_name": "", "validation_constraints": {}},
        {"field_id": "#email", "label": "Email Address", "input_type": "email",
         "is_required": True, "is_visible": True, "is_enabled": True,
         "available_options": [], "current_value": "", "page_number": 1,
         "section_name": "", "validation_constraints": {}},
    ]
    
    profile = {
        "personal": {"full_name": "Test User", "first_name": "Test", "last_name": "User"},
        "contact": {"email": "test@example.com", "phone": "+91 99999 99999"},
        "addresses": [],
        "preferences": {},
        "professional_links": [],
    }
    
    mappings = _rule_based_mapping(fields, profile)
    assert len(mappings) == 2
    email_mapping = next((m for m in mappings if "email" in m.get("profile_key", "")), None)
    assert email_mapping is not None
    assert email_mapping["value"] == "test@example.com"


# ── Answer Validation ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_answer_validation():
    from app.agents.clarification_agent import validate_answer
    
    # Valid email
    assert validate_answer("user@example.com", {"type": "email", "required": True}) is None
    
    # Invalid email
    assert validate_answer("not-an-email", {"type": "email", "required": True}) is not None
    
    # Required but empty
    assert validate_answer("", {"type": "text", "required": True}) is not None
    
    # Optional and empty — should pass
    assert validate_answer("", {"type": "text", "required": False}) is None
    
    # Number out of range
    assert validate_answer("200", {"type": "number", "constraints": {"min": "0", "max": "100"}}) is not None
