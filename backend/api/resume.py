import os
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User, Resume
from backend.schemas.resume import (
    ResumeCreate,
    ResumeResponse,
    ResumeListResponse,
    ParsedResume,
)
from backend.services.parser import (
    allowed_file,
    get_file_type,
    extract_text,
    parse_resume_text,
    generate_file_hash,
    MAX_FILE_SIZE,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])
UPLOAD_DIR = "backend/uploads"


@router.post("/", response_model=ResumeResponse)
async def upload_resume(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    file: Annotated[UploadFile, File(description="Resume file (PDF or DOCX)")],
    version_name: str = "",
    is_primary: bool = False,
) -> ResumeResponse:
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(['.pdf', '.docx'])}",
        )
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )
    
    if is_primary:
        result = await session.execute(
            select(Resume).where(Resume.user_id == current_user.id)
        )
        existing_resumes = result.scalars().all()
        for existing in existing_resumes:
            existing.is_primary = False
        await session.commit()
    
    file_type = get_file_type(file.filename)
    file_hash = generate_file_hash(content)
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    safe_filename = f"{current_user.id}_{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    text_content = extract_text(file.filename, content)
    parsed_data = parse_resume_text(text_content)
    
    resume = Resume(
        id=uuid.uuid4(),
        user_id=current_user.id,
        version_name=version_name,
        source_file=file_path,
        file_type=file_type,
        parsed_json=parsed_data.model_dump(),
        rendered_text=text_content,
        is_primary=is_primary,
    )
    
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    
    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        version_name=resume.version_name,
        file_type=resume.file_type,
        is_primary=resume.is_primary,
        parsed_json=ParsedResume(**resume.parsed_json),
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


@router.get("/", response_model=list[ResumeListResponse])
async def list_resumes(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ResumeListResponse]:
    result = await session.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    
    return [
        ResumeListResponse(
            id=r.id,
            version_name=r.version_name,
            file_type=r.file_type,
            is_primary=r.is_primary,
            created_at=r.created_at,
        )
        for r in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResumeResponse:
    result = await session.execute(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    
    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        version_name=resume.version_name,
        file_type=resume.file_type,
        is_primary=resume.is_primary,
        parsed_json=ParsedResume(**resume.parsed_json),
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    result = await session.execute(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    
    if os.path.exists(resume.source_file):
        os.remove(resume.source_file)
    
    await session.delete(resume)
    await session.commit()
    
    return {"message": "Resume deleted"}


@router.post("/{resume_id}/set-primary")
async def set_primary_resume(
    resume_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    result = await session.execute(
        select(Resume).where(Resume.user_id == current_user.id)
    )
    all_resumes = result.scalars().all()
    
    target_resume = None
    for r in all_resumes:
        if r.id == resume_id:
            target_resume = r
            r.is_primary = True
        else:
            r.is_primary = False
    
    if target_resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    
    await session.commit()
    
    return {"message": "Primary resume updated"}
