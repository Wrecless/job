from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobAlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    score_total: float
    explanation: str
    status: str
    draft_data: dict
    created_at: datetime
    read_at: datetime | None
    job_company: str
    job_title: str
    job_location: str | None
    job_application_url: str


class JobAlertListResponse(BaseModel):
    alerts: list[JobAlertResponse]
    unread_total: int
    ready_total: int


class JobAlertStatusUpdate(BaseModel):
    status: str
