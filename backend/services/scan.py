import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_personal_user
from backend.db.models import Job, JobSource, JobAlert
from backend.services.matching import MatchingService

MATCH_THRESHOLD = 70.0


def build_application_draft(job: Job, explanation: str, profile: dict) -> str:
    salary_floor = profile.get("salary_floor")
    salary_line = (
        f"The posted salary appears to meet my minimum floor of £{salary_floor:,}."
        if salary_floor
        else "The role appears to fit my salary expectations."
    )

    return (
        f"Hi {job.company} team,\n\n"
        f"I’m interested in the {job.title} role because it is fully remote and fits my preference for travel-friendly work.\n"
        f"{salary_line}\n"
        f"Match summary: {explanation}\n\n"
        f"Best,\nBruno"
    )


def build_draft_data(job: Job, score_total: float, explanation: str, profile: dict) -> dict:
    return {
        "ready_to_review": True,
        "score_total": score_total,
        "reason": explanation,
        "application_draft": build_application_draft(job, explanation, profile),
        "job_summary": {
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "application_url": job.application_url,
        },
        "next_steps": [
            "Review the job description",
            "Confirm it is fully remote",
            "Check salary meets UK minimum wage",
            "Prepare application draft",
        ],
    }


async def scan_and_queue_matches(session: AsyncSession) -> int:
    user = await get_personal_user(session)
    matcher = MatchingService(session)
    profile = await matcher.get_user_profile(user.id) or {}

    await matcher.score_all_jobs_for_user(user.id)
    jobs, _ = await matcher.get_jobs_with_scores(user.id, page_size=500)

    created = 0
    for job_data in jobs:
        score_breakdown = job_data.get("score_breakdown")
        if score_breakdown and getattr(score_breakdown, "salary_fit", 0) <= 0:
            continue

        score_total = job_data.get("score_total")
        if score_total is None or float(score_total) < MATCH_THRESHOLD:
            continue

        job_result = await session.execute(select(Job).where(Job.id == job_data["job_id"]))
        job = job_result.scalar_one_or_none()
        if not job or (job.remote_type or "").lower() != "remote":
            continue

        source_result = await session.execute(select(JobSource).where(JobSource.id == job.source_id))
        source = source_result.scalar_one_or_none()
        if not source:
            continue

        include_types = {s.lower() for s in profile.get("source_types_include", []) if s}
        exclude_types = {s.lower() for s in profile.get("source_types_exclude", []) if s}
        include_names = {s.lower() for s in profile.get("source_names_include", []) if s}
        exclude_names = {s.lower() for s in profile.get("source_names_exclude", []) if s}

        source_type = (source.source_type or "").lower()
        source_name = (source.name or "").lower()

        if include_types and source_type not in include_types:
            continue
        if source_type in exclude_types:
            continue
        if include_names and source_name not in include_names:
            continue
        if source_name in exclude_names:
            continue

        existing = await session.execute(
            select(JobAlert).where(JobAlert.user_id == user.id, JobAlert.job_id == job.id)
        )
        if existing.scalar_one_or_none():
            continue

        explanation = job_data.get("explanation") or "Match found"
        alert = JobAlert(
            id=uuid.uuid4(),
            user_id=user.id,
            job_id=job.id,
            score_total=float(score_total),
            explanation=explanation,
            status="unread",
            draft_data=build_draft_data(job, float(score_total), explanation, profile),
            read_at=None,
        )
        session.add(alert)
        created += 1

    await session.commit()
    return created
