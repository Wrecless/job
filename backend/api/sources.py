import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User, JobSource
from backend.services.ingestion import SourceRegistry

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    name: str
    source_type: str
    base_url: str
    api_key: str | None = None


class SourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    base_url: str
    is_active: bool
    last_fetch_at: datetime | None
    last_success_at: datetime | None
    error_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SourceIngestResponse(BaseModel):
    source_name: str
    jobs_created: int
    jobs_updated: int
    total_jobs: int


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    active_only: bool = True,
) -> list[SourceResponse]:
    registry = SourceRegistry(session)
    sources = await registry.list_sources(active_only=active_only)
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/", response_model=SourceResponse)
async def create_source(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    source_data: SourceCreate,
) -> SourceResponse:
    registry = SourceRegistry(session)
    source, created = await registry.get_or_create_source(
        name=source_data.name,
        source_type=source_data.source_type,
        base_url=source_data.base_url,
    )
    
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source with this name already exists",
        )
    
    return SourceResponse.model_validate(source)


@router.get("/{source_name}", response_model=SourceResponse)
async def get_source(
    source_name: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SourceResponse:
    registry = SourceRegistry(session)
    source = await registry.get_source(source_name)
    
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    
    return SourceResponse.model_validate(source)


@router.post("/{source_name}/ingest", response_model=SourceIngestResponse)
async def ingest_source(
    source_name: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    api_key: str | None = None,
) -> SourceIngestResponse:
    registry = SourceRegistry(session)
    source = await registry.get_source(source_name)
    
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    
    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source is inactive",
        )
    
    try:
        jobs_created, jobs_updated = await registry.ingest_from_source(source, api_key)
        return SourceIngestResponse(
            source_name=source_name,
            jobs_created=jobs_created,
            jobs_updated=jobs_updated,
            total_jobs=jobs_created + jobs_updated,
        )
    except Exception as e:
        await registry.update_source_health(source, success=False, error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.patch("/{source_name}/toggle")
async def toggle_source(
    source_name: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    is_active: bool,
) -> dict:
    registry = SourceRegistry(session)
    source = await registry.get_source(source_name)
    
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    
    source.is_active = is_active
    await session.commit()
    
    return {"message": f"Source {'activated' if is_active else 'deactivated'}"}


@router.delete("/{source_name}")
async def delete_source(
    source_name: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    registry = SourceRegistry(session)
    source = await registry.get_source(source_name)
    
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    
    await session.delete(source)
    await session.commit()
    
    return {"message": "Source deleted"}
