import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import Application, AuditLog, Job, Resume, User
from backend.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationWithJob, ApplicationListResponse, ApplicationPipeline

router = APIRouter(prefix="/applications", tags=["applications"])


async def _get_or_create_system_resume(session: AsyncSession, user_id: uuid.UUID) -> Resume:
    result = await session.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.is_primary.desc(), Resume.created_at.desc())
    )
    resume = result.scalars().first()
    if resume:
        return resume

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        version_name="System Resume",
        source_file="system://placeholder",
        file_type="system",
        parsed_json={},
        rendered_text="",
        is_primary=True,
    )
    session.add(resume)
    await session.flush()
    return resume


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApplicationListResponse:
    total_result = await session.execute(
        select(func.count()).select_from(Application).where(Application.user_id == current_user.id)
    )
    total = total_result.scalar() or 0

    query = (
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
    )

    result = await session.execute(query)
    rows = result.all()

    pipeline_query = (
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    )
    pipeline_result = await session.execute(pipeline_query)
    pipeline_data = dict(pipeline_result.all())

    pipeline = ApplicationPipeline(
        found=pipeline_data.get("found", 0),
        saved=pipeline_data.get("saved", 0),
        tailoring=pipeline_data.get("tailoring", 0),
        ready=pipeline_data.get("ready", 0),
        submitted=pipeline_data.get("submitted", 0),
        interviewing=pipeline_data.get("interviewing", 0),
        rejected=pipeline_data.get("rejected", 0),
        offer=pipeline_data.get("offer", 0),
        closed=pipeline_data.get("closed", 0),
    )

    applications = [
        ApplicationWithJob(
            id=app.id,
            user_id=app.user_id,
            job_id=app.job_id,
            resume_id=app.resume_id,
            status=app.status,
            submission_method=app.submission_method,
            submitted_at=app.submitted_at,
            notes=app.notes,
            created_at=app.created_at,
            job_company=job.company,
            job_title=job.title,
            job_location=job.location,
            job_application_url=job.application_url,
        )
        for app, job in rows
    ]

    return ApplicationListResponse(applications=applications, pipeline=pipeline, total=total)


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    request: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationResponse:
    job_result = await session.execute(select(Job).where(Job.id == request.job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = await session.execute(
        select(Application).where(
            Application.user_id == current_user.id,
            Application.job_id == request.job_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application already exists for this job")

    resume = await _get_or_create_system_resume(session, current_user.id)

    application = Application(
        id=uuid.uuid4(),
        user_id=current_user.id,
        job_id=request.job_id,
        resume_id=resume.id,
        status="found",
        notes=request.notes,
    )
    session.add(application)

    audit = AuditLog(
        id=uuid.uuid4(),
        actor="system",
        actor_id=current_user.id,
        action="application.created",
        target_type="application",
        target_id=application.id,
        before=None,
        after={"status": "found", "job_id": str(request.job_id)},
    )
    session.add(audit)

    await session.commit()
    await session.refresh(application)

    return ApplicationResponse.model_validate(application)


@router.delete("/{application_id}")
async def delete_application(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    await session.delete(application)
    await session.commit()

    return {"message": "Application deleted"}
