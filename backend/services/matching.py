import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import User, Profile, Resume, Job, MatchScore
from backend.schemas.matching import ScoreBreakdown


WEIGHTS = {
    "title_similarity": 0.25,
    "skill_match": 0.30,
    "seniority_fit": 0.15,
    "location_fit": 0.10,
    "salary_fit": 0.10,
    "remote_fit": 0.10,
}


def normalize_title(title: str) -> list[str]:
    words = title.lower().replace("-", " ").replace("/", " ").split()
    stop_words = {"and", "or", "the", "a", "an", "of", "for", "to", "in", "on", "at", "by"}
    return [w for w in words if w not in stop_words and len(w) > 2]


def calculate_title_similarity(profile_roles: list[str], job_title: str) -> float:
    if not profile_roles or not job_title:
        return 0.0
    
    job_words = set(normalize_title(job_title))
    max_overlap = 0.0
    
    for role in profile_roles:
        role_words = set(normalize_title(role))
        if not role_words:
            continue
        overlap = len(job_words & role_words)
        max_overlap = max(max_overlap, overlap / len(job_words))
    
    return min(max_overlap * 100, 100.0)


def calculate_skill_match(user_skills: list[str], job_skills: list[str]) -> float:
    if not job_skills:
        return 50.0
    
    user_skills_lower = {s.lower() for s in user_skills}
    job_skills_lower = {s.lower() for s in job_skills}
    
    if not user_skills_lower:
        return 25.0
    
    overlap = len(user_skills_lower & job_skills_lower)
    return min((overlap / len(job_skills_lower)) * 100, 100.0)


def calculate_seniority_fit(profile_seniority: str | None, job_seniority: str | None) -> float:
    if not profile_seniority or not job_seniority:
        return 50.0
    
    seniority_levels = {
        "intern": 1,
        "junior": 2,
        "mid": 3,
        "senior": 4,
        "staff": 5,
        "principal": 6,
        "lead": 5,
        "manager": 5,
        "director": 7,
        "vp": 8,
        "executive": 9,
    }
    
    profile_level = seniority_levels.get(profile_seniority.lower(), 3)
    job_level = seniority_levels.get(job_seniority.lower(), 3)
    
    diff = abs(profile_level - job_level)
    
    if diff == 0:
        return 100.0
    elif diff == 1:
        return 75.0
    elif diff == 2:
        return 50.0
    else:
        return 25.0


def calculate_location_fit(
    profile_locations: list[str],
    job_location: str | None,
) -> float:
    if not profile_locations or not job_location:
        return 50.0
    
    job_loc_lower = job_location.lower()
    
    for loc in profile_locations:
        loc_lower = loc.lower()
        if loc_lower == "remote":
            return 100.0
        if loc_lower in job_loc_lower or job_loc_lower in loc_lower:
            return 100.0
    
    return 25.0


def calculate_salary_fit(
    profile_floor: int | None,
    job_salary_min: int | None,
    job_salary_max: int | None,
) -> float:
    if not profile_floor:
        return 50.0
    
    if not job_salary_min and not job_salary_max:
        return 50.0
    
    if job_salary_max and profile_floor > job_salary_max:
        return 20.0
    
    if job_salary_min and profile_floor <= job_salary_min:
        return 100.0
    
    if job_salary_min and job_salary_max:
        midpoint = (job_salary_min + job_salary_max) / 2
        if profile_floor <= midpoint:
            return 100.0
        ratio = job_salary_max / profile_floor
        return min(ratio * 50, 100.0)
    
    return 50.0


def calculate_remote_fit(
    profile_remote: str | None,
    job_remote: str | None,
) -> float:
    if not profile_remote:
        return 50.0
    
    profile_remote = profile_remote.lower()
    job_remote = (job_remote or "").lower()
    
    if profile_remote == "remote":
        if job_remote in ("remote", "") or not job_remote:
            return 100.0
        return 75.0
    
    if profile_remote == "hybrid":
        if job_remote == "hybrid":
            return 100.0
        if job_remote == "remote":
            return 75.0
        if job_remote == "onsite":
            return 50.0
        return 75.0
    
    if profile_remote == "onsite":
        if job_remote in ("onsite", "") or not job_remote:
            return 100.0
        if job_remote == "hybrid":
            return 75.0
        return 50.0
    
    return 50.0


def score_job(
    profile: dict,
    job: dict,
    user_skills: list[str],
) -> tuple[float, ScoreBreakdown, str]:
    title_similarity = calculate_title_similarity(
        profile.get("target_roles", []),
        job.get("title", ""),
    )
    
    skill_match = calculate_skill_match(
        user_skills,
        job.get("skills_required", []),
    )
    
    seniority_fit = calculate_seniority_fit(
        profile.get("seniority"),
        job.get("seniority"),
    )
    
    location_fit = calculate_location_fit(
        profile.get("locations", []),
        job.get("location"),
    )
    
    salary_fit = calculate_salary_fit(
        profile.get("salary_floor"),
        job.get("salary_min"),
        job.get("salary_max"),
    )
    
    remote_fit = calculate_remote_fit(
        profile.get("remote_preference"),
        job.get("remote_type"),
    )
    
    breakdown = ScoreBreakdown(
        title_similarity=round(title_similarity, 1),
        skill_match=round(skill_match, 1),
        seniority_fit=round(seniority_fit, 1),
        location_fit=round(location_fit, 1),
        salary_fit=round(salary_fit, 1),
        remote_fit=round(remote_fit, 1),
    )
    
    score_total = (
        title_similarity * WEIGHTS["title_similarity"] +
        skill_match * WEIGHTS["skill_match"] +
        seniority_fit * WEIGHTS["seniority_fit"] +
        location_fit * WEIGHTS["location_fit"] +
        salary_fit * WEIGHTS["salary_fit"] +
        remote_fit * WEIGHTS["remote_fit"]
    )
    
    explanation_parts = []
    if title_similarity >= 75:
        explanation_parts.append("strong title match")
    elif title_similarity >= 50:
        explanation_parts.append("moderate title match")
    
    if skill_match >= 75:
        explanation_parts.append("high skill overlap")
    elif skill_match >= 50:
        explanation_parts.append("some skill overlap")
    
    if seniority_fit >= 75:
        explanation_parts.append("good seniority fit")
    
    if location_fit >= 75:
        explanation_parts.append("location matches")
    
    if remote_fit >= 75:
        explanation_parts.append("remote preference aligned")
    
    if not explanation_parts:
        explanation = "Limited match based on available information"
    else:
        explanation = "Match factors: " + ", ".join(explanation_parts) + "."
    
    return round(score_total, 2), breakdown, explanation


class MatchingService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_profile(self, user_id: uuid.UUID) -> dict | None:
        from sqlalchemy import select
        from backend.db.models import Profile
        
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            return {
                "headline": profile.headline,
                "target_roles": profile.target_roles or [],
                "seniority": profile.seniority,
                "salary_floor": profile.salary_floor,
                "locations": profile.locations or [],
                "remote_preference": profile.remote_preference,
                "industries_to_avoid": profile.industries_to_avoid or [],
                "keywords_include": profile.keywords_include or [],
                "keywords_exclude": profile.keywords_exclude or [],
            }
        return None
    
    async def get_user_skills(self, user_id: uuid.UUID) -> list[str]:
        from sqlalchemy import select
        from backend.db.models import Resume
        
        result = await self.session.execute(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.is_primary == True,
            ).order_by(Resume.created_at.desc())
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            result = await self.session.execute(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
            )
            resume = result.scalar_one_or_none()
        
        if resume and resume.parsed_json:
            return resume.parsed_json.get("skills", [])
        
        return []
    
    async def score_job_for_user(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> MatchScore | None:
        profile = await self.get_user_profile(user_id)
        if not profile:
            return None
        
        from sqlalchemy import select
        from backend.db.models import Job
        
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        user_skills = await self.get_user_skills(user_id)
        
        job_dict = {
            "title": job.title,
            "skills_required": job.skills_required or [],
            "seniority": job.seniority,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "remote_type": job.remote_type,
        }
        
        score_total, breakdown, explanation = score_job(profile, job_dict, user_skills)
        
        existing = await self.session.execute(
            select(MatchScore).where(
                MatchScore.user_id == user_id,
                MatchScore.job_id == job_id,
            )
        )
        existing_score = existing.scalar_one_or_none()
        
        if existing_score:
            existing_score.score_total = score_total
            existing_score.score_breakdown = breakdown.model_dump()
            existing_score.explanation = explanation
            match_score = existing_score
        else:
            match_score = MatchScore(
                id=uuid.uuid4(),
                job_id=job_id,
                user_id=user_id,
                score_total=score_total,
                score_breakdown=breakdown.model_dump(),
                explanation=explanation,
            )
            self.session.add(match_score)
        
        await self.session.commit()
        await self.session.refresh(match_score)
        
        return match_score
    
    async def score_all_jobs_for_user(self, user_id: uuid.UUID) -> int:
        from sqlalchemy import select
        from backend.db.models import Job
        
        profile = await self.get_user_profile(user_id)
        if not profile:
            return 0
        
        user_skills = await self.get_user_skills(user_id)
        
        result = await self.session.execute(select(Job))
        jobs = result.scalars().all()
        
        count = 0
        for job in jobs:
            job_dict = {
                "title": job.title,
                "skills_required": job.skills_required or [],
                "seniority": job.seniority,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "remote_type": job.remote_type,
            }
            
            score_total, breakdown, explanation = score_job(profile, job_dict, user_skills)
            
            existing = await self.session.execute(
                select(MatchScore).where(
                    MatchScore.user_id == user_id,
                    MatchScore.job_id == job.id,
                )
            )
            existing_score = existing.scalar_one_or_none()
            
            if existing_score:
                existing_score.score_total = score_total
                existing_score.score_breakdown = breakdown.model_dump()
                existing_score.explanation = explanation
            else:
                match_score = MatchScore(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    user_id=user_id,
                    score_total=score_total,
                    score_breakdown=breakdown.model_dump(),
                    explanation=explanation,
                )
                self.session.add(match_score)
            
            count += 1
        
        await self.session.commit()
        return count
    
    async def get_jobs_with_scores(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        min_score: float | None = None,
        company: str | None = None,
        location: str | None = None,
        remote_type: str | None = None,
    ) -> tuple[list[dict], int]:
        from sqlalchemy import select, func
        from backend.db.models import Job, MatchScore
        
        query = (
            select(Job, MatchScore)
            .join(MatchScore, Job.id == MatchScore.job_id, isouter=True)
            .where(MatchScore.user_id == user_id)
        )
        
        if min_score is not None:
            query = query.where(MatchScore.score_total >= min_score)
        
        if company:
            query = query.where(Job.company.ilike(f"%{company}%"))
        
        if location:
            query = query.where(Job.location.ilike(f"%{location}%"))
        
        if remote_type:
            query = query.where(Job.remote_type == remote_type)
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.order_by(MatchScore.score_total.desc().nullslast())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        jobs_with_scores = []
        for job, match_score in rows:
            job_dict = {
                "job_id": job.id,
                "source_job_id": job.source_job_id,
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "remote_type": job.remote_type,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "description": job.description,
                "application_url": job.application_url,
                "posted_at": job.posted_at,
                "score_total": match_score.score_total if match_score else None,
                "score_breakdown": ScoreBreakdown(**match_score.score_breakdown) if match_score and match_score.score_breakdown else None,
                "explanation": match_score.explanation if match_score else None,
                "matched_at": match_score.created_at if match_score else None,
            }
            jobs_with_scores.append(job_dict)
        
        return jobs_with_scores, total
