from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User
from backend.services.scheduler import get_scheduler, fetch_all_jobs

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/fetch-jobs")
async def trigger_job_fetch(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    import asyncio
    asyncio.create_task(fetch_all_jobs())
    return {"status": "triggered", "message": "Job fetch started in background"}


@router.get("/scheduler-status")
async def scheduler_status(
    current_user: User = Depends(get_current_user),
):
    scheduler = get_scheduler()
    jobs = scheduler.get_jobs() if scheduler else []
    
    return {
        "running": scheduler is not None and scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "pending": job.pending,
            }
            for job in jobs
        ],
    }


@router.post("/scheduler/stop")
async def stop_scheduler_endpoint(
    current_user: User = Depends(get_current_user),
):
    from backend.services.scheduler import stop_scheduler
    stop_scheduler()
    return {"status": "stopped"}


@router.post("/scheduler/start")
async def start_scheduler_endpoint(
    current_user: User = Depends(get_current_user),
):
    from backend.services.scheduler import start_scheduler
    start_scheduler()
    return {"status": "started"}
