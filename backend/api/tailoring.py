from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User
from backend.schemas.tailoring import (
    TailorRequest,
    TailorResponse,
    ResumeTailoringResponse,
    CoverLetterResponse,
)
from backend.services.tailoring import TailoringService

router = APIRouter(prefix="/tailor", tags=["tailoring"])


@router.post("/", response_model=TailorResponse)
async def tailor_application(
    request: TailorRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TailorResponse:
    service = TailoringService(session)
    
    result = await service.tailor_and_generate_cover_letter(
        user_id=current_user.id,
        job_id=request.job_id,
        resume_id=request.resume_id,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job or resume not found",
        )
    
    return TailorResponse(
        resume=ResumeTailoringResponse(**result["resume"]),
        cover_letter=CoverLetterResponse(**result["cover_letter"]),
    )


@router.post("/resume", response_model=ResumeTailoringResponse)
async def tailor_resume(
    request: TailorRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResumeTailoringResponse:
    service = TailoringService(session)
    
    result = await service.tailor_resume(
        user_id=current_user.id,
        job_id=request.job_id,
        resume_id=request.resume_id,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job or resume not found",
        )
    
    return ResumeTailoringResponse(**result)


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: TailorRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CoverLetterResponse:
    service = TailoringService(session)
    
    result = await service.generate_cover_letter_for_job(
        user_id=current_user.id,
        job_id=request.job_id,
        resume_id=request.resume_id,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job or resume not found",
        )
    
    return CoverLetterResponse(**result)
