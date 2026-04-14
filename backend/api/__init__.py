from backend.api.jobs import router as jobs_router
from backend.api.applications import router as applications_router
from backend.api.alerts import router as alerts_router
from backend.api.bot import router as bot_router
from backend.api.sources import router as sources_router

__all__ = ["jobs_router", "applications_router", "alerts_router", "bot_router", "sources_router"]
