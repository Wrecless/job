from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ResumeBase(BaseModel):
    version_name: str = Field(..., min_length=1, max_length=100)
    is_primary: bool = False


class ResumeCreate(ResumeBase):
    pass


class ResumeSection(BaseModel):
    title: str | None = None
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    bullets: list[str] = []


class ParsedResume(BaseModel):
    contact: dict | None = None
    summary: str | None = None
    experience: list[ResumeSection] = []
    education: list[ResumeSection] = []
    skills: list[str] = []
    certifications: list[ResumeSection] = []
    projects: list[ResumeSection] = []
    links: list[str] = []


class ResumeResponse(BaseModel):
    id: UUID
    user_id: UUID
    version_name: str
    file_type: str
    is_primary: bool
    parsed_json: ParsedResume
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    id: UUID
    version_name: str
    file_type: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True
