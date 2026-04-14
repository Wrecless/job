from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User
from backend.schemas.matching import JobListResponse, JobWithMatch
from backend.services.matching import MatchingService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_score: float | None = Query(None, ge=0, le=100),
    company: str | None = None,
    location: str | None = None,
    remote_type: str | None = None,
) -> JobListResponse:
    service = MatchingService(session)
    await service.score_all_jobs_for_user(current_user.id)
    jobs, total = await service.get_jobs_with_scores(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        min_score=min_score,
        company=company,
        location=location,
        remote_type=remote_type,
    )

    return JobListResponse(
        jobs=[JobWithMatch(**j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )
