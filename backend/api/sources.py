from typing import Annotated
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_session
from backend.db.models import JobSource, User
from backend.dependencies import get_current_user
from backend.schemas.source import SourceCreate, SourceListResponse, SourceResponse, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


def _serialize_source(source: JobSource) -> SourceResponse:
    return SourceResponse.model_validate(source, from_attributes=True)


@router.get("/", response_model=SourceListResponse)
async def list_sources(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SourceListResponse:
    _ = current_user
    result = await session.execute(select(JobSource).order_by(JobSource.created_at.desc()))
    return SourceListResponse(sources=[_serialize_source(source) for source in result.scalars().all()])


@router.post("/", response_model=SourceResponse)
async def create_source(
    payload: SourceCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SourceResponse:
    _ = current_user
    source = JobSource(
        id=uuid.uuid4(),
        name=payload.name,
        source_type=payload.source_type,
        base_url=payload.base_url,
        is_active=payload.is_active,
    )
    session.add(source)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Source name already exists") from exc

    await session.refresh(source)
    return _serialize_source(source)


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    payload: SourceUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SourceResponse:
    _ = current_user
    result = await session.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Source name already exists") from exc

    await session.refresh(source)
    return _serialize_source(source)


@router.delete("/{source_id}")
async def delete_source(
    source_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    _ = current_user
    result = await session.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await session.delete(source)
    await session.commit()
    return {"message": "Source deleted"}
