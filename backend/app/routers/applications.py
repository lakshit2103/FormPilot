"""
Applications router — full REST API for the job search + form-filling workflow.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_verified_user
from app.models import User, ApplicationSession, JobSearchResult, FieldMapping, MissingQuestion, ValidationError
from app.schemas.applications import (
    StartApplicationIn, ApplicationSessionOut, SelectJobIn, ManualURLIn,
    JobResultOut, BrowserStatusOut, AnswersIn, ReviewSummaryOut, FieldMappingOut,
    EditFieldIn,
)
import app.services.application_service as svc

router = APIRouter(prefix="/api/applications", tags=["applications"])

# In-memory event queues per session (for WebSocket streaming)
_event_queues: dict[str, asyncio.Queue] = {}


def _get_or_create_queue(session_id: str) -> asyncio.Queue:
    if session_id not in _event_queues:
        _event_queues[session_id] = asyncio.Queue()
    return _event_queues[session_id]


# ── Session CRUD ─────────────────────────────────────────────────────────────

@router.post("/start", response_model=ApplicationSessionOut, status_code=status.HTTP_201_CREATED)
async def start_application(
    data: StartApplicationIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Create a new application session and trigger the search phase."""
    session = await svc.create_session(db, user, data)
    return ApplicationSessionOut(
        id=session.id,
        user_query=session.user_query,
        intent=session.intent,
        company=session.company,
        role=session.role,
        location=session.location,
        status=session.status,
        current_node=session.current_node,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("", response_model=list[ApplicationSessionOut])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    sessions = await svc.get_user_sessions(db, user)
    return [
        ApplicationSessionOut(
            id=s.id, user_query=s.user_query, intent=s.intent,
            company=s.company, role=s.role, location=s.location,
            status=s.status, current_node=s.current_node,
            created_at=s.created_at, updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=ApplicationSessionOut)
async def get_application(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ApplicationSessionOut(
        id=session.id, user_query=session.user_query, intent=session.intent,
        company=session.company, role=session.role, location=session.location,
        status=session.status, current_node=session.current_node,
        created_at=session.created_at, updated_at=session.updated_at,
    )


# ── Search Phase ─────────────────────────────────────────────────────────────

@router.post("/{session_id}/search")
async def trigger_search(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Trigger the DuckDuckGo search phase for a session."""
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = _get_or_create_queue(str(session_id))
    session.status = "searching"
    await db.commit()

    background_tasks.add_task(svc.run_search_phase, db, session, user, queue)
    return {"message": "Search started", "session_id": str(session_id)}


@router.get("/{session_id}/jobs", response_model=list[JobResultOut])
async def get_job_results(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Get ranked job search results for a session."""
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(JobSearchResult)
        .where(JobSearchResult.session_id == session_id)
        .order_by(JobSearchResult.relevance_score.desc())
    )
    jobs = result.scalars().all()
    return [
        JobResultOut(
            id=j.id, title=j.title, company=j.company, location=j.location,
            url=j.url, domain=j.domain, snippet=j.snippet,
            source_type=j.source_type, relevance_score=j.relevance_score,
            is_official=j.is_official, job_status=j.job_status,
        )
        for j in jobs
    ]


@router.post("/{session_id}/select-job")
async def select_job(
    session_id: uuid.UUID,
    data: SelectJobIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """User selects a job from results — triggers the navigation + fill pipeline."""
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(JobSearchResult).where(
            JobSearchResult.id == data.job_id,
            JobSearchResult.session_id == session_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job result not found")

    session.selected_job_id = job.id
    session.current_url = job.url
    session.status = "navigating"
    await db.commit()

    queue = _get_or_create_queue(str(session_id))
    background_tasks.add_task(svc.run_full_pipeline, db, session, user, job.url, queue)
    return {"message": "Job selected — opening application page", "url": job.url}


@router.post("/{session_id}/job-url")
async def provide_manual_url(
    session_id: uuid.UUID,
    data: ManualURLIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """User provides a manual job URL — triggers navigation + fill pipeline."""
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.current_url = data.url
    session.status = "navigating"
    await db.commit()

    queue = _get_or_create_queue(str(session_id))
    background_tasks.add_task(svc.run_full_pipeline, db, session, user, data.url, queue)
    return {"message": "Opening job URL", "url": data.url}


# ── Browser Control ───────────────────────────────────────────────────────────

@router.post("/{session_id}/continue")
async def continue_session(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Resume after user completes manual action (login / CAPTCHA)."""
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "running"
    await db.commit()

    queue = _get_or_create_queue(str(session_id))
    # Resume from extract_form since login is now complete
    if session.current_url:
        background_tasks.add_task(svc.run_full_pipeline, db, session, user, session.current_url, queue)
    return {"message": "Resuming application"}


@router.post("/{session_id}/stop")
async def stop_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    """Pause / stop the current session."""
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "paused"
    await db.commit()

    # Close browser context
    from app.browser.manager import BrowserManager
    await BrowserManager.close_context(str(session_id))
    return {"message": "Session paused"}


@router.get("/{session_id}/browser-status", response_model=BrowserStatusOut)
async def get_browser_status(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.browser.manager import BrowserManager
    browser_active = session_id in BrowserManager._contexts

    return BrowserStatusOut(
        session_id=session_id,
        current_url=session.current_url,
        current_node=session.current_node,
        status=session.status,
        browser_active=browser_active,
    )


# ── Missing Questions ────────────────────────────────────────────────────────

@router.get("/{session_id}/questions")
async def get_questions(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(MissingQuestion).where(
            MissingQuestion.session_id == session_id,
            MissingQuestion.status == "pending",
        )
    )
    questions = result.scalars().all()
    return [
        {
            "id": str(q.id),
            "question": q.question,
            "field_requirements": q.field_requirements,
            "status": q.status,
        }
        for q in questions
    ]


@router.post("/{session_id}/answers")
async def submit_answers(
    session_id: uuid.UUID,
    data: AnswersIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.models import UserAnswer
    for answer in data.answers:
        ua = UserAnswer(
            session_id=session_id,
            answer_value=answer.answer_value,
            save_to_profile=answer.save_to_profile,
        )
        db.add(ua)

    session.status = "running"
    await db.commit()

    queue = _get_or_create_queue(str(session_id))
    if session.current_url:
        background_tasks.add_task(svc.run_full_pipeline, db, session, user, session.current_url, queue)
    return {"message": "Answers received — continuing form fill"}


# ── Review ────────────────────────────────────────────────────────────────────

@router.get("/{session_id}/review")
async def get_review(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mappings_r = await db.execute(
        select(FieldMapping).where(FieldMapping.session_id == session_id)
    )
    mappings = mappings_r.scalars().all()

    errors_r = await db.execute(
        select(ValidationError).where(ValidationError.session_id == session_id)
    )
    errors = errors_r.scalars().all()

    auto_filled = sum(1 for m in mappings if m.mapping_status == "ready" and m.confidence >= 0.90)
    user_provided = sum(1 for m in mappings if m.mapping_status == "ready" and m.confidence >= 1.0)
    missing = sum(1 for m in mappings if m.mapping_status == "missing")
    low_conf = sum(1 for m in mappings if 0.40 <= (m.confidence or 0) < 0.90)

    return {
        "session_id": str(session_id),
        "total_fields": len(mappings),
        "auto_filled": auto_filled,
        "user_provided": user_provided,
        "missing": missing,
        "low_confidence": low_conf,
        "errors": len(errors),
        "mappings": [
            {
                "id": str(m.id),
                "profile_key": m.profile_key,
                "proposed_value": m.proposed_value,
                "confidence": m.confidence,
                "mapping_status": m.mapping_status,
                "reason": m.reason,
                "user_approved": m.user_approved,
            }
            for m in mappings
        ],
        "validation_errors": [
            {"id": str(e.id), "error_type": e.error_type, "error_message": e.error_message}
            for e in errors
        ],
    }


@router.patch("/{session_id}/fields/{field_id}")
async def edit_field(
    session_id: uuid.UUID,
    field_id: uuid.UUID,
    data: EditFieldIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    result = await db.execute(
        select(FieldMapping).where(
            FieldMapping.id == field_id,
            FieldMapping.session_id == session_id,
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="Field mapping not found")

    mapping.proposed_value = data.proposed_value
    mapping.user_approved = data.user_approved
    await db.commit()
    return {"message": "Field updated"}


@router.post("/{session_id}/validate")
async def rerun_validation(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_verified_user),
):
    session = await svc.get_session(db, session_id, user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = _get_or_create_queue(str(session_id))
    return {"message": "Validation re-run started"}
