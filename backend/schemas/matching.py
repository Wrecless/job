from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    title_similarity: float
    skill_match: float
    seniority_fit: float
    location_fit: float
    salary_fit: float
    remote_fit: float


class MatchScoreResponse(BaseModel):
    job_id: UUID
    user_id: UUID
    score_total: float
    score_breakdown: ScoreBreakdown
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobWithMatch(BaseModel):
    job_id: UUID
    source_job_id: str
    company: str
    title: str
    location: str | None
    remote_type: str | None
    salary_min: int | None
    salary_max: int | None
    description: str
    application_url: str
    posted_at: datetime | None
    score_total: float | None
    score_breakdown: ScoreBreakdown | None
    explanation: str | None
    matched_at: datetime | None


class JobListResponse(BaseModel):
    jobs: list[JobWithMatch]
    total: int
    page: int
    page_size: int
