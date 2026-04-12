import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User, Application, Task, Job, Resume, AuditLog, APPLICATION_STATUSES
from backend.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    TaskCreate,
    TaskUpdate,
    ApplicationResponse,
    ApplicationWithJob,
    TaskResponse,
    ApplicationPipeline,
    ApplicationListResponse,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApplicationListResponse:
    count_query = select(func.count()).select_from(Application).where(
        Application.user_id == current_user.id
    )
    if status_filter:
        count_query = count_query.where(Application.status == status_filter)
    
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    query = (
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.user_id == current_user.id)
    )
    
    if status_filter:
        query = query.where(Application.status == status_filter)
    
    query = query.order_by(Application.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
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
    
    applications = []
    for app, job in rows:
        applications.append(ApplicationWithJob(
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
        ))
    
    return ApplicationListResponse(
        applications=applications,
        pipeline=pipeline,
        total=total,
    )


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    request: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationResponse:
    job_result = await session.execute(
        select(Job).where(Job.id == request.job_id)
    )
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
    
    resume_id = request.resume_id
    if not resume_id:
        resume_result = await session.execute(
            select(Resume).where(
                Resume.user_id == current_user.id,
                Resume.is_primary == True,
            ).order_by(Resume.created_at.desc())
        )
        resume = resume_result.scalar_one_or_none()
        if not resume:
            resume_result = await session.execute(
                select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
            )
            resume = resume_result.scalar_one_or_none()
        if resume:
            resume_id = resume.id
    
    if not resume_id:
        raise HTTPException(status_code=400, detail="No resume found. Please upload a resume first.")
    
    application = Application(
        id=uuid.uuid4(),
        user_id=current_user.id,
        job_id=request.job_id,
        resume_id=resume_id,
        status="found",
        notes=request.notes,
    )
    session.add(application)
    
    audit = AuditLog(
        id=uuid.uuid4(),
        actor="user",
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


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationResponse:
    result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return ApplicationResponse.model_validate(application)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: uuid.UUID,
    request: ApplicationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationResponse:
    result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    before_state = {
        "status": application.status,
        "notes": application.notes,
        "submission_method": application.submission_method,
    }
    
    if request.status:
        if request.status not in APPLICATION_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {APPLICATION_STATUSES}")
        application.status = request.status
        if request.status == "submitted" and not application.submitted_at:
            application.submitted_at = datetime.now(timezone.utc)
    
    if request.notes is not None:
        application.notes = request.notes
    
    if request.submission_method:
        application.submission_method = request.submission_method
    
    audit = AuditLog(
        id=uuid.uuid4(),
        actor="user",
        actor_id=current_user.id,
        action="application.updated",
        target_type="application",
        target_id=application.id,
        before=before_state,
        after={
            "status": application.status,
            "notes": application.notes,
            "submission_method": application.submission_method,
        },
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


@router.post("/{application_id}/tasks", response_model=TaskResponse)
async def create_task(
    application_id: uuid.UUID,
    request: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskResponse:
    app_result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if request.task_type not in ["follow_up", "interview_prep", "review", "tailor", "submit"]:
        raise HTTPException(status_code=400, detail="Invalid task type")
    
    due_at = request.due_at
    if not due_at:
        if request.task_type == "follow_up":
            due_at = datetime.now(timezone.utc) + timedelta(days=7)
        elif request.task_type == "interview_prep":
            due_at = datetime.now(timezone.utc) + timedelta(days=1)
    
    task = Task(
        id=uuid.uuid4(),
        application_id=application_id,
        task_type=request.task_type,
        status="pending",
        due_at=due_at,
        payload=request.payload or {},
    )
    session.add(task)
    
    await session.commit()
    await session.refresh(task)
    
    return TaskResponse.model_validate(task)


@router.get("/{application_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    application_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TaskResponse]:
    app_result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = await session.execute(
        select(Task)
        .where(Task.application_id == application_id)
        .order_by(Task.due_at.asc().nullslast())
    )
    tasks = result.scalars().all()
    
    return [TaskResponse.model_validate(t) for t in tasks]


@router.patch("/{application_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    application_id: uuid.UUID,
    task_id: uuid.UUID,
    request: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskResponse:
    app_result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.application_id == application_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if request.status:
        if request.status not in ["pending", "in_progress", "completed", "skipped"]:
            raise HTTPException(status_code=400, detail="Invalid task status")
        task.status = request.status
        if request.status == "completed":
            task.completed_at = datetime.now(timezone.utc)
    
    if request.due_at:
        task.due_at = request.due_at
    
    await session.commit()
    await session.refresh(task)
    
    return TaskResponse.model_validate(task)


@router.delete("/{application_id}/tasks/{task_id}")
async def delete_task(
    application_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    app_result = await session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.application_id == application_id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await session.delete(task)
    await session.commit()
    
    return {"message": "Task deleted"}


@router.get("/tasks/pending", response_model=list[TaskResponse])
async def list_pending_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TaskResponse]:
    result = await session.execute(
        select(Task, Application)
        .join(Application, Task.application_id == Application.id)
        .where(
            Application.user_id == current_user.id,
            Task.status.in_(["pending", "in_progress"]),
        )
        .order_by(Task.due_at.asc().nullslast())
    )
    rows = result.all()
    
    return [TaskResponse.model_validate(task) for task, _ in rows]
