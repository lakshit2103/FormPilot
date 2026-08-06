"""
Applications service — manages ApplicationSession lifecycle and coordinates the agent graph.
"""
import uuid
import asyncio
import json
from datetime import datetime
from typing import Optional, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ApplicationSession, JobSearchResult, DetectedFormField,
    FieldMapping, MissingQuestion, UserAnswer, ValidationError,
    AuditLog, User, Document
)
from app.schemas.applications import StartApplicationIn, SelectJobIn, ManualURLIn, AnswersIn
from app.agents.state import AgentState


def _empty_state(session_id: str, user_id: str, user_query: str) -> AgentState:
    return AgentState(
        session_id=session_id,
        user_id=user_id,
        user_query=user_query,
        intent=None,
        search_queries=[],
        raw_results=[],
        ranked_results=[],
        selected_job=None,
        current_url=None,
        current_node="start",
        browser_session_id=None,
        detected_fields=[],
        field_mappings=[],
        missing_questions=[],
        user_answers=[],
        validation_errors=[],
        review_ready=False,
        error_message=None,
        manual_action_required=False,
        manual_action_reason=None,
        messages=[],
    )


async def create_session(db: AsyncSession, user: User, data: StartApplicationIn) -> ApplicationSession:
    session = ApplicationSession(
        user_id=user.id,
        user_query=data.user_query,
        status="created",
        current_node="start",
    )
    db.add(session)
    await db.flush()
    await db.commit()
    await db.refresh(session)
    return session


async def get_user_sessions(db: AsyncSession, user: User) -> list[ApplicationSession]:
    result = await db.execute(
        select(ApplicationSession)
        .where(ApplicationSession.user_id == user.id)
        .order_by(ApplicationSession.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


async def get_session(db: AsyncSession, session_id: uuid.UUID, user: User) -> Optional[ApplicationSession]:
    result = await db.execute(
        select(ApplicationSession)
        .where(ApplicationSession.id == session_id, ApplicationSession.user_id == user.id)
    )
    return result.scalar_one_or_none()


async def _persist_state(db: AsyncSession, session: ApplicationSession, state: AgentState):
    """Persist the agent state back to the database after each node."""
    session.intent = state.get("intent")
    session.company = state.get("intent", {}).get("company") if isinstance(state.get("intent"), dict) else None
    session.role = state.get("intent", {}).get("role") if isinstance(state.get("intent"), dict) else None
    session.location = state.get("intent", {}).get("location") if isinstance(state.get("intent"), dict) else None
    session.current_url = state.get("current_url")
    session.current_node = state.get("current_node", "")
    session.updated_at = datetime.utcnow()

    if state.get("manual_action_required"):
        session.status = "paused"
    elif state.get("review_ready"):
        session.status = "reviewing"
    elif state.get("error_message"):
        session.status = "failed"
    else:
        session.status = "running"

    await db.commit()


async def _save_job_results(db: AsyncSession, session: ApplicationSession, results: list[dict]):
    """Persist job search results to DB."""
    for r in results:
        jr = JobSearchResult(
            session_id=session.id,
            title=r.get("title", ""),
            company=r.get("company"),
            location=r.get("location"),
            url=r.get("url", ""),
            domain=r.get("domain"),
            snippet=r.get("snippet"),
            source_type=r.get("source_type", "unverified"),
            relevance_score=r.get("relevance_score", 0.0),
            is_official=r.get("is_official", False),
            job_status=r.get("job_status", "available"),
            search_query=r.get("search_query", ""),
        )
        db.add(jr)
    await db.flush()


async def _load_profile_data(db: AsyncSession, user: User) -> dict:
    """Load the user's full profile in the canonical JSON format for the mapping agent."""
    from sqlalchemy import select as sel
    from app.models import (
        UserProfile, Address, Education, Experience, Skill,
        Project, Certification, JobPreference, ProfessionalLink,
        UserEmail, UserPhoneNumber
    )

    async def one(model, **where):
        r = await db.execute(sel(model).filter_by(**where))
        return r.scalar_one_or_none()

    async def many(model, **where):
        r = await db.execute(sel(model).filter_by(**where))
        return r.scalars().all()

    profile = await one(UserProfile, user_id=user.id)
    addresses = await many(Address, user_id=user.id)
    education = await many(Education, user_id=user.id)
    experience = await many(Experience, user_id=user.id)
    skills = await many(Skill, user_id=user.id)
    projects = await many(Project, user_id=user.id)
    certs = await many(Certification, user_id=user.id)
    prefs_r = await one(JobPreference, user_id=user.id)
    links = await many(ProfessionalLink, user_id=user.id)
    phones = await many(UserPhoneNumber, user_id=user.id)

    primary_phone = next((p for p in phones if p.is_primary), None)

    # Default resume
    docs_r = await db.execute(
        sel(Document).where(
            Document.user_id == user.id,
            Document.document_type == "resume",
            Document.is_default == True,
        )
    )
    default_resume = docs_r.scalar_one_or_none()

    name_parts = user.full_name.split(" ", 1)
    first = name_parts[0]
    last = name_parts[1] if len(name_parts) > 1 else ""

    return {
        "personal": {
            "full_name": user.full_name,
            "first_name": first,
            "last_name": last,
            "date_of_birth": str(profile.date_of_birth) if profile and profile.date_of_birth else None,
            "gender": profile.gender if profile else None,
        },
        "contact": {
            "email": user.email,
            "phone": f"{primary_phone.country_code}{primary_phone.phone_number}" if primary_phone else None,
        },
        "addresses": [
            {
                "address_type": a.address_type,
                "address_line_1": a.address_line_1,
                "address_line_2": a.address_line_2,
                "city": a.city,
                "state": a.state,
                "country": a.country,
                "postal_code": a.postal_code,
            }
            for a in addresses
        ],
        "education": [
            {
                "institution": e.institution_name,
                "degree": e.degree,
                "specialisation": e.specialisation,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "cgpa": str(e.cgpa) if e.cgpa else None,
                "percentage": str(e.percentage) if e.percentage else None,
            }
            for e in education
        ],
        "experience": [
            {
                "company": e.company_name,
                "title": e.job_title,
                "employment_type": e.employment_type,
                "location": e.location,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "is_current": e.is_current,
                "description": e.description,
            }
            for e in experience
        ],
        "skills": [
            {"skill_name": s.skill_name, "proficiency_level": s.proficiency_level}
            for s in skills
        ],
        "projects": [
            {
                "title": p.title,
                "description": p.description,
                "technologies": p.technologies,
                "project_url": p.project_url,
                "repository_url": p.repository_url,
            }
            for p in projects
        ],
        "certifications": [
            {
                "name": c.name,
                "issuing_organization": c.issuing_organization,
                "issue_date": str(c.issue_date) if c.issue_date else None,
            }
            for c in certs
        ],
        "preferences": {
            "preferred_roles": prefs_r.preferred_roles if prefs_r else [],
            "preferred_locations": prefs_r.preferred_locations if prefs_r else [],
            "notice_period": prefs_r.notice_period if prefs_r else None,
            "minimum_salary": prefs_r.minimum_salary if prefs_r else None,
            "willing_to_relocate": prefs_r.willing_to_relocate if prefs_r else None,
        },
        "professional_links": [
            {"platform": l.platform, "url": l.url}
            for l in links
        ],
        "documents": {
            "default_resume": default_resume.storage_path if default_resume else None,
        },
    }


async def run_search_phase(
    db: AsyncSession,
    session: ApplicationSession,
    user: User,
    event_queue: asyncio.Queue,
) -> AgentState:
    """Run parse_request → search_jobs → rank_results, emit events to queue."""
    # Pre-load full profile so it's available when the pipeline continues
    profile_data = await _load_profile_data(db, user)

    state = _empty_state(str(session.id), str(user.id), session.user_query)
    state["_event_queue"] = event_queue
    state["_full_profile_data"] = profile_data

    from app.agents.graph import get_graph
    graph = get_graph()

    # Run up to show_results / request_job_url
    final_state = await graph.ainvoke(state, config={"recursion_limit": 10})

    # Persist
    await _save_job_results(db, session, final_state.get("ranked_results", []))
    await _persist_state(db, session, final_state)

    # Emit events
    for msg in final_state.get("messages", []):
        await event_queue.put(msg)

    return final_state


async def run_full_pipeline(
    db: AsyncSession,
    session: ApplicationSession,
    user: User,
    job_url: str,
    event_queue: asyncio.Queue,
) -> AgentState:
    """Run the complete pipeline from navigation through review."""
    profile_data = await _load_profile_data(db, user)

    state = _empty_state(str(session.id), str(user.id), session.user_query)
    state["selected_job"] = {"url": job_url, "title": "Direct URL"}
    state["_profile_data"] = profile_data
    state["_full_profile_data"] = profile_data  # for profile_retrieval_agent
    state["_event_queue"] = event_queue

    # Restore intent from session
    if session.intent:
        state["intent"] = session.intent

    # Build a mini-graph for the filling phase
    from app.agents.navigation_agent import run_navigation_agent
    from app.agents.extraction_agent import run_extraction_agent
    from app.agents.mapping_agent import run_mapping_agent
    from app.agents.clarification_agent import run_clarification_agent
    from app.agents.filling_agent import run_filling_agent
    from app.agents.validation_agent import run_validation_agent

    state = await run_navigation_agent(state)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    if state.get("manual_action_required"):
        await _persist_state(db, session, state)
        return state

    state = await run_extraction_agent(state)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    state = await run_mapping_agent(state, profile_data)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    state = await run_clarification_agent(state)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    if state.get("missing_questions"):
        session.current_node = "ask_user"
        session.status = "paused"
        # Save field mappings and questions to DB
        await _save_session_data(db, session, state)
        await db.commit()
        return state

    state = await run_filling_agent(state)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    state = await run_validation_agent(state)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    # Build review summary
    from app.agents.review_agent import run_review_agent
    state = await run_review_agent(state)
    for msg in state.get("messages", []):
        await event_queue.put(msg)
    state["messages"] = []

    await _save_session_data(db, session, state)
    await _persist_state(db, session, state)
    return state


async def _save_session_data(db: AsyncSession, session: ApplicationSession, state: AgentState):
    """Persist field mappings, questions, answers, and validation errors to DB."""
    # Field mappings
    for m in state.get("field_mappings", []):
        fm = FieldMapping(
            session_id=session.id,
            profile_key=m.get("profile_key"),
            proposed_value=m.get("value"),
            confidence=m.get("confidence", 0.0),
            mapping_status=m.get("status", "missing"),
            reason=m.get("reason", ""),
            user_approved=m.get("status") == "ready",
        )
        db.add(fm)

    # Missing questions
    for q in state.get("missing_questions", []):
        mq = MissingQuestion(
            session_id=session.id,
            question=q.get("question", ""),
            field_requirements=q.get("field_requirements", {}),
            status="pending",
        )
        db.add(mq)

    # Validation errors
    for e in state.get("validation_errors", []):
        ve = ValidationError(
            session_id=session.id,
            error_type=e.get("error_type", "validation"),
            error_message=e.get("error_message", ""),
            is_resolved=False,
        )
        db.add(ve)

    await db.flush()
