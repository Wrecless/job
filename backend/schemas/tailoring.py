from uuid import UUID
from pydantic import BaseModel
from typing import Literal


class TailorRequest(BaseModel):
    job_id: UUID
    resume_id: UUID | None = None


class TailoredBullet(BaseModel):
    original: str
    tailored: str
    source_section: str
    skills_matched: list[str]
    confidence: float


class ResumeTailoringResponse(BaseModel):
    job_id: UUID
    resume_id: UUID
    tailored_bullets: list[TailoredBullet]
    summary_suggestion: str | None
    missing_qualifications: list[str]
    confidence: float


class CoverLetterSection(BaseModel):
    content: str
    prompt_used: str


class CoverLetterResponse(BaseModel):
    job_id: UUID
    intro: CoverLetterSection
    body: list[CoverLetterSection]
    closing: CoverLetterSection
    full_text: str
    missing_qualifications: list[str]
    confidence: float


class TailorResponse(BaseModel):
    resume: ResumeTailoringResponse
    cover_letter: CoverLetterResponse
