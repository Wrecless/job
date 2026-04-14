from backend.api.jobs import router as jobs_router
from backend.api.applications import router as applications_router
from backend.api.alerts import router as alerts_router

__all__ = ["jobs_router", "applications_router", "alerts_router"]
