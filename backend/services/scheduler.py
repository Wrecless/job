import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import get_settings

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


async def run_job_bot_cycle():
    from backend.db.base import async_session
    from backend.services.bot import run_job_bot
    
    try:
        async with async_session() as session:
            result = await run_job_bot(session)
            logger.info(
                "Bot run complete: %s sources checked, %s failed, %s created, %s updated, %s scored",
                result["sources_checked"],
                result["sources_failed"],
                result["jobs_created"],
                result["jobs_updated"],
                result["jobs_scored"],
            )
    except Exception as e:
        logger.error(f"Bot run error: {e}")


async def scan_job_alerts():
    from backend.db.base import async_session
    from backend.services.scan import scan_and_queue_matches

    try:
        async with async_session() as session:
            created = await scan_and_queue_matches(session)
            logger.info(f"Queued {created} job alerts")
    except Exception as e:
        logger.error(f"Job scan error: {e}")


def start_scheduler():
    global scheduler
    if scheduler is not None:
        return scheduler
    
    settings = get_settings()
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        run_job_bot_cycle,
        IntervalTrigger(hours=settings.job_fetch_interval_hours),
        id="job_fetch",
        replace_existing=True,
    )
    scheduler.add_job(
        scan_job_alerts,
        IntervalTrigger(hours=settings.job_scan_interval_hours),
        id="job_scan",
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
