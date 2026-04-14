from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: UUID
    resume_id: UUID | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID
    status: str
    submission_method: str | None
    submitted_at: datetime | None
    last_updated_at: datetime
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationWithJob(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID
    status: str
    submission_method: str | None
    submitted_at: datetime | None
    notes: str | None
    created_at: datetime
    job_company: str
    job_title: str
    job_location: str | None
    job_application_url: str


class ApplicationPipeline(BaseModel):
    found: int = 0
    saved: int = 0
    tailoring: int = 0
    ready: int = 0
    submitted: int = 0
    interviewing: int = 0
    rejected: int = 0
    offer: int = 0
    closed: int = 0


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationWithJob]
    pipeline: ApplicationPipeline
    total: int
