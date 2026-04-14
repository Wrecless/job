import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_personal_user
from backend.services.ingestion.registry import CONNECTOR_MAP, SourceRegistry
from backend.services.matching import MatchingService

logger = logging.getLogger(__name__)


async def run_job_bot(session: AsyncSession) -> dict:
    user = await get_personal_user(session)
    registry = SourceRegistry(session)
    sources = await registry.list_sources(active_only=True)

    jobs_created = 0
    jobs_updated = 0
    sources_failed = 0
    sources_skipped = 0

    for source in sources:
        if source.source_type not in CONNECTOR_MAP:
            sources_skipped += 1
            logger.info("Skipped unsupported source type %s for %s", source.source_type, source.name)
            continue

        try:
            created, updated = await registry.ingest_from_source(source)
            jobs_created += created
            jobs_updated += updated
        except Exception as exc:
            sources_failed += 1
            logger.error("Bot failed to fetch %s: %s", source.name, exc)

    matcher = MatchingService(session)
    jobs_scored = await matcher.score_all_jobs_for_user(user.id)

    return {
        "sources_checked": len(sources),
        "sources_skipped": sources_skipped,
        "sources_failed": sources_failed,
        "jobs_created": jobs_created,
        "jobs_updated": jobs_updated,
        "jobs_scored": jobs_scored,
    }
