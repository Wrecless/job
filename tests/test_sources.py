import uuid

import pytest
from sqlalchemy import select
from httpx import AsyncClient, ASGITransport

from backend.db.base import get_session
from backend.db.models import JobSource, Job, User, MatchScore, JobAlert
from backend.main import app as fastapi_app
from backend.services.source_seed import STARTER_SOURCES, seed_starter_sources


@pytest.mark.asyncio
async def test_source_crud(async_session):
    async def override_get_session():
        yield async_session

    fastapi_app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/sources/",
                json={
                    "name": "Greenhouse Co",
                    "source_type": "greenhouse",
                    "base_url": "https://boards.greenhouse.io/company",
                    "is_active": True,
                },
            )
            assert created.status_code == 200
            source_id = created.json()["id"]

            listed = await client.get("/sources/")
            assert listed.status_code == 200
            assert len(listed.json()["sources"]) == 1

            updated = await client.patch(f"/sources/{source_id}", json={"is_active": False})
            assert updated.status_code == 200
            assert updated.json()["is_active"] is False

            deleted = await client.delete(f"/sources/{source_id}")
            assert deleted.status_code == 200
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_seed_starter_sources_replaces_placeholders(async_session):
    async_session.add(
        JobSource(
            id=uuid.uuid4(),
            name="ManualSource",
            source_type="manual",
            base_url="https://example.com",
        )
    )
    await async_session.commit()

    created = await seed_starter_sources(async_session)

    assert created == len(STARTER_SOURCES)
    result = await async_session.execute(select(JobSource))
    names = {row.name for row in result.scalars().all()}
    assert "GitLab" in names
    assert "ManualSource" not in names


@pytest.mark.asyncio
async def test_seed_starter_sources_purges_demo_jobs(async_session):
    source = JobSource(
        id=uuid.uuid4(),
        name="ManualSource",
        source_type="manual",
        base_url="https://example.com",
    )
    user = User(id=uuid.uuid4(), email="seed-test@example.com", password_hash="hash")
    job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="demo-1",
        company="Demo Co",
        title="Demo Role",
        description="Demo",
        application_url="https://example.com/apply",
        source_url="https://example.com/job",
        raw_payload={},
        canonical_hash="demo",
    )
    async_session.add_all([
        source,
        user,
        job,
        MatchScore(
            id=uuid.uuid4(),
            job_id=job.id,
            user_id=user.id,
            score_total=10.0,
            score_breakdown={},
            explanation="demo",
        ),
        JobAlert(
            id=uuid.uuid4(),
            user_id=user.id,
            job_id=job.id,
            score_total=10.0,
            explanation="demo",
            status="unread",
            draft_data={},
        ),
    ])
    await async_session.commit()

    created = await seed_starter_sources(async_session)

    assert created == len(STARTER_SOURCES)
    job_count = (await async_session.execute(select(Job))).scalars().all()
    alert_count = (await async_session.execute(select(JobAlert))).scalars().all()
    assert len(job_count) == 0
    assert len(alert_count) == 0
