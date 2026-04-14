from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    source_type: str = Field(min_length=1, max_length=50)
    base_url: str = Field(min_length=1, max_length=500)
    is_active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    source_type: str | None = Field(default=None, min_length=1, max_length=50)
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    is_active: bool | None = None


class SourceResponse(SourceBase):
    id: UUID
    last_fetch_at: datetime | None
    last_success_at: datetime | None
    error_count: int
    created_at: datetime


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
