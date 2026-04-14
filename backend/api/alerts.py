from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_session
from backend.db.models import JobAlert, Job, User
from backend.dependencies import get_current_user
from backend.schemas.alert import JobAlertListResponse, JobAlertResponse, JobAlertStatusUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=JobAlertListResponse)
async def list_alerts(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JobAlertListResponse:
    unread_result = await session.execute(
        select(func.count()).select_from(JobAlert).where(
            JobAlert.user_id == current_user.id,
            JobAlert.status == "unread",
        )
    )
    unread_total = unread_result.scalar() or 0

    ready_result = await session.execute(
        select(func.count()).select_from(JobAlert).where(
            JobAlert.user_id == current_user.id,
            JobAlert.status == "ready",
        )
    )
    ready_total = ready_result.scalar() or 0

    result = await session.execute(
        select(JobAlert, Job)
        .join(Job, JobAlert.job_id == Job.id)
        .where(JobAlert.user_id == current_user.id)
        .order_by(JobAlert.created_at.desc())
    )

    alerts = [
        JobAlertResponse(
            id=alert.id,
            user_id=alert.user_id,
            job_id=alert.job_id,
            score_total=float(alert.score_total),
            explanation=alert.explanation,
            status=alert.status,
            draft_data=alert.draft_data or {},
            created_at=alert.created_at,
            read_at=alert.read_at,
            job_company=job.company,
            job_title=job.title,
            job_location=job.location,
            job_application_url=job.application_url,
        )
        for alert, job in result.all()
    ]

    return JobAlertListResponse(alerts=alerts, unread_total=unread_total, ready_total=ready_total)


@router.patch("/{alert_id}/read", response_model=JobAlertResponse)
async def mark_alert_read(
    alert_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JobAlertResponse:
    result = await session.execute(
        select(JobAlert, Job)
        .join(Job, JobAlert.job_id == Job.id)
        .where(JobAlert.id == alert_id, JobAlert.user_id == current_user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert, job = row
    if alert.status != "read":
        alert.status = "read"
        alert.read_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(alert)

    return JobAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        job_id=alert.job_id,
        score_total=float(alert.score_total),
        explanation=alert.explanation,
        status=alert.status,
        draft_data=alert.draft_data or {},
        created_at=alert.created_at,
        read_at=alert.read_at,
        job_company=job.company,
        job_title=job.title,
        job_location=job.location,
        job_application_url=job.application_url,
    )


@router.patch("/{alert_id}/status", response_model=JobAlertResponse)
async def update_alert_status(
    alert_id: UUID,
    payload: JobAlertStatusUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JobAlertResponse:
    result = await session.execute(
        select(JobAlert, Job)
        .join(Job, JobAlert.job_id == Job.id)
        .where(JobAlert.id == alert_id, JobAlert.user_id == current_user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert, job = row
    alert.status = payload.status
    if payload.status != "unread" and alert.read_at is None:
        alert.read_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(alert)

    return JobAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        job_id=alert.job_id,
        score_total=float(alert.score_total),
        explanation=alert.explanation,
        status=alert.status,
        draft_data=alert.draft_data or {},
        created_at=alert.created_at,
        read_at=alert.read_at,
        job_company=job.company,
        job_title=job.title,
        job_location=job.location,
        job_application_url=job.application_url,
    )
