from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.db.base import engine, Base, async_session
from backend.api.jobs import router as jobs_router
from backend.api.applications import router as applications_router
from backend.api.alerts import router as alerts_router
from backend.api.bot import router as bot_router
from backend.api.sources import router as sources_router
from backend.services.scheduler import start_scheduler, stop_scheduler
from backend.services.source_seed import seed_starter_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await seed_starter_sources(session)
    
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
    
    app.include_router(jobs_router)
    app.include_router(applications_router)
    app.include_router(alerts_router)
    app.include_router(bot_router)
    app.include_router(sources_router)
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    return app


app = create_app()
