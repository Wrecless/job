import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.db.models import Job, JobSource


class BaseConnector(ABC):
    source_name: str
    source_type: str
    
    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
    
    @abstractmethod
    async def fetch_raw(self) -> list[dict]:
        pass
    
    def normalize(self, raw: dict) -> dict:
        job_id = raw.get("id") or raw.get("id") or str(raw.get("absolute_id", ""))
        company = raw.get("company") or raw.get("departments", [{}])[0].get("name", "Unknown")
        title = raw.get("title", "Unknown")
        location = self._extract_location(raw)
        description = self._extract_description(raw)
        
        canonical = f"{self.source_name}:{job_id}"
        if isinstance(canonical, str):
            canonical = canonical.encode('utf-8')
        canonical_hash = hashlib.sha256(canonical).hexdigest()
        
        return {
            "source_job_id": str(job_id),
            "company": company,
            "title": title,
            "location": location,
            "remote_type": self._extract_remote_type(raw),
            "salary_min": self._extract_salary(raw, "min"),
            "salary_max": self._extract_salary(raw, "max"),
            "employment_type": self._extract_employment_type(raw),
            "seniority": self._extract_seniority(raw),
            "description": description,
            "skills_required": self._extract_skills(raw),
            "benefits": self._extract_benefits(raw),
            "application_url": self._extract_application_url(raw),
            "source_url": self._extract_source_url(raw),
            "posted_at": self._extract_posted_at(raw),
            "expires_at": self._extract_expires_at(raw),
            "raw_payload": raw,
            "canonical_hash": canonical_hash,
        }
    
    def _extract_location(self, raw: dict) -> str | None:
        location = raw.get("location", "")
        if location:
            return location
        offices = raw.get("offices", [])
        if offices:
            loc_parts = []
            if offices[0].get("name"):
                loc_parts.append(offices[0]["name"])
            if offices[0].get("location"):
                loc_parts.append(offices[0]["location"])
            return ", ".join(loc_parts) if loc_parts else None
        return None
    
    def _extract_description(self, raw: dict) -> str:
        desc = raw.get("description") or raw.get("content") or raw.get("text") or ""
        return desc.strip() if desc else ""
    
    def _extract_remote_type(self, raw: dict) -> str | None:
        remote = raw.get("remote", raw.get("remote_type", raw.get("work_from_home")))
        if remote is True or str(remote).lower() in ("true", "yes", "remote", "hybrid"):
            if str(remote).lower() == "hybrid":
                return "hybrid"
            return "remote"
        return None
    
    def _extract_salary(self, raw: dict, min_or_max: str) -> int | None:
        compensation = raw.get("compensation", {}) or {}
        if min_or_max == "min":
            return compensation.get("min_cents") // 100 if compensation.get("min_cents") else None
        return compensation.get("max_cents") // 100 if compensation.get("max_cents") else None
    
    def _extract_employment_type(self, raw: dict) -> str | None:
        emp_type = raw.get("employment_type", raw.get("type", ""))
        if emp_type:
            return emp_type.lower()
        return None
    
    def _extract_seniority(self, raw: dict) -> str | None:
        seniority = raw.get("seniority", raw.get("level", ""))
        if seniority:
            return seniority.lower()
        return None
    
    def _extract_skills(self, raw: dict) -> list[str]:
        skills = raw.get("skills", raw.get("requirements", raw.get("technologies_required", [])))
        if isinstance(skills, list):
            return [s if isinstance(s, str) else s.get("name", "") for s in skills if s]
        return []
    
    def _extract_benefits(self, raw: dict) -> list[str]:
        benefits = raw.get("benefits", raw.get("perks", raw.get("extra", [])))
        if isinstance(benefits, list):
            return [b if isinstance(b, str) else b.get("name", "") for b in benefits if b]
        return []
    
    def _extract_application_url(self, raw: dict) -> str:
        return raw.get("absolute_url", raw.get("application_url", raw.get("apply_url", "")))
    
    def _extract_source_url(self, raw: dict) -> str:
        return raw.get("absolute_url", raw.get("source_url", self.base_url))
    
    def _extract_posted_at(self, raw: dict) -> datetime | None:
        posted = raw.get("created_at", raw.get("published_at", raw.get("posted_at")))
        if posted:
            return self._parse_datetime(posted)
        return None
    
    def _extract_expires_at(self, raw: dict) -> datetime | None:
        expires = raw.get("expires_at", raw.get("closed_at", raw.get("expiration_date")))
        if expires:
            return self._parse_datetime(expires)
        return None
    
    def _parse_datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
