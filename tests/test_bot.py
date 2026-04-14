from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport

from backend.db.base import get_session
from backend.main import app as fastapi_app


@pytest.mark.asyncio
async def test_bot_run_fetches_and_scores_jobs(async_session, monkeypatch):
    from backend.services import bot as bot_service

    async def override_get_session():
        yield async_session

    async def fake_list_sources(self, active_only=True):
        return [
            SimpleNamespace(name="GoodSource", source_type="greenhouse"),
            SimpleNamespace(name="BrokenSource", source_type="lever"),
            SimpleNamespace(name="ManualSource", source_type="manual"),
        ]

    async def fake_ingest_from_source(self, source):
        if source.name == "BrokenSource":
            raise RuntimeError("boom")
        return 3, 4

    async def fake_score_all_jobs_for_user(self, user_id):
        return 5

    monkeypatch.setattr(bot_service.SourceRegistry, "list_sources", fake_list_sources)
    monkeypatch.setattr(bot_service.SourceRegistry, "ingest_from_source", fake_ingest_from_source)
    monkeypatch.setattr(bot_service.MatchingService, "score_all_jobs_for_user", fake_score_all_jobs_for_user)

    fastapi_app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/bot/run")

        assert response.status_code == 200
        assert response.json() == {
            "sources_checked": 3,
            "sources_skipped": 1,
            "sources_failed": 1,
            "jobs_created": 3,
            "jobs_updated": 4,
            "jobs_scored": 5,
        }
    finally:
        fastapi_app.dependency_overrides.clear()
