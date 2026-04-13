from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.db.base import engine, Base
from backend.api import auth, resume_router, profile_router
from backend.api.sources import router as sources_router
from backend.api.jobs import router as jobs_router
from backend.api.tailoring import router as tailoring_router
from backend.api.applications import router as applications_router
from backend.api.automation import router as automation_router
from backend.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    start_scheduler()
    
    yield
    stop_scheduler()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(auth.router)
    app.include_router(resume_router)
    app.include_router(profile_router)
    app.include_router(sources_router)
    app.include_router(jobs_router)
    app.include_router(tailoring_router)
    app.include_router(applications_router)
    app.include_router(automation_router)
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    return app


app = create_app()
