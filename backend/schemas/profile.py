from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    headline: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    seniority: str | None = None
    salary_floor: int | None = None
    locations: list[str] = Field(default_factory=list)
    remote_preference: str | None = None
    industries_to_avoid: list[str] = Field(default_factory=list)
    sponsorship_needed: bool = False
    company_size_preference: str | None = None
    keywords_include: list[str] = Field(default_factory=list)
    keywords_exclude: list[str] = Field(default_factory=list)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    headline: str | None = None
    target_roles: list[str] | None = None
    seniority: str | None = None
    salary_floor: int | None = None
    locations: list[str] | None = None
    remote_preference: str | None = None
    industries_to_avoid: list[str] | None = None
    sponsorship_needed: bool | None = None
    company_size_preference: str | None = None
    keywords_include: list[str] | None = None
    keywords_exclude: list[str] | None = None


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    headline: str | None
    target_roles: list[str]
    seniority: str | None
    salary_floor: int | None
    locations: list[str]
    remote_preference: str | None
    industries_to_avoid: list[str]
    sponsorship_needed: bool
    company_size_preference: str | None
    keywords_include: list[str]
    keywords_exclude: list[str]
    timezone: str
    locale: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
