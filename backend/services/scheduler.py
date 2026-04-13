import asyncio
import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import get_settings

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


async def fetch_all_jobs():
    from backend.db.base import async_session
    from backend.services.ingestion import SourceRegistry
    from sqlalchemy import select
    from backend.db.models import JobSource
    
    try:
        async with async_session() as session:
            registry = SourceRegistry(session)
            sources = await registry.list_sources(active_only=True)
            
            for source in sources:
                try:
                    connector = registry.get_connector(source.source_type)
                    if connector:
                        await connector.fetch_jobs(source, session)
                        logger.info(f"Fetched jobs from {source.name}")
                except Exception as e:
                    logger.error(f"Failed to fetch from {source.name}: {e}")
    except Exception as e:
        logger.error(f"Job fetch error: {e}")


def start_scheduler():
    global scheduler
    if scheduler is not None:
        return scheduler
    
    settings = get_settings()
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        fetch_all_jobs,
        IntervalTrigger(hours=settings.job_fetch_interval_hours),
        id="job_fetch",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler


def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")


def get_scheduler():
    return scheduler
