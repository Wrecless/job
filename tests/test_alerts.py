import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.db.base import get_session
from backend.db.models import JobSource, Job, JobAlert
from backend.main import app as fastapi_app
from backend.services.scan import scan_and_queue_matches


@pytest.mark.asyncio
async def test_daily_scan_creates_in_app_alert(async_session):
    source = JobSource(
        id=uuid.uuid4(),
        name="RemoteSource",
        source_type="greenhouse",
        base_url="https://example.com",
    )
    async_session.add(source)
    await async_session.flush()

    remote_job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="REMOTE-1",
        company="Remote Co",
        title="Backend Engineer",
        location="Remote",
        remote_type="remote",
        salary_min=40000,
        salary_max=50000,
        description="Remote role",
        application_url="https://example.com/apply",
        source_url="https://example.com/job",
        raw_payload={},
        canonical_hash="remote-1",
    )
    onsite_job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="ONSITE-1",
        company="Office Co",
        title="Backend Engineer",
        location="London",
        remote_type="onsite",
        salary_min=40000,
        salary_max=50000,
        description="Onsite role",
        application_url="https://example.com/apply2",
        source_url="https://example.com/job2",
        raw_payload={},
        canonical_hash="onsite-1",
    )
    rss_source = JobSource(
        id=uuid.uuid4(),
        name="RSSSource",
        source_type="rss",
        base_url="https://example.com/rss",
    )
    async_session.add_all([remote_job, onsite_job, rss_source])
    await async_session.flush()

    rss_job = Job(
        id=uuid.uuid4(),
        source_id=rss_source.id,
        source_job_id="RSS-1",
        company="RSS Co",
        title="Software Engineer",
        location="Remote",
        remote_type="remote",
        salary_min=60000,
        salary_max=70000,
        description="Remote role from RSS source",
        application_url="https://example.com/apply3",
        source_url="https://example.com/job3",
        raw_payload={},
        canonical_hash="rss-1",
    )
    async_session.add(rss_job)
    await async_session.commit()

    created = await scan_and_queue_matches(async_session)

    assert created == 1
    result = await async_session.execute(select(JobAlert))
    alerts = result.scalars().all()
    assert len(alerts) == 1
    assert alerts[0].status == "unread"
    assert alerts[0].draft_data["ready_to_review"] is True
    assert "application_draft" in alerts[0].draft_data
    assert "fully remote" in alerts[0].draft_data["application_draft"].lower()


@pytest.mark.asyncio
async def test_alerts_api_lists_and_marks_read(async_session):
    async def override_get_session():
        yield async_session

    fastapi_app.dependency_overrides[get_session] = override_get_session

    try:
        source = JobSource(
            id=uuid.uuid4(),
            name="RemoteSource2",
            source_type="greenhouse",
            base_url="https://example.com",
        )
        async_session.add(source)
        await async_session.flush()

        job = Job(
            id=uuid.uuid4(),
            source_id=source.id,
            source_job_id="REMOTE-2",
            company="Remote Co 2",
            title="Product Engineer",
            location="Remote",
            remote_type="remote",
            salary_min=50000,
            salary_max=60000,
            description="Remote role",
            application_url="https://example.com/apply",
            source_url="https://example.com/job",
            raw_payload={},
            canonical_hash="remote-2",
        )
        async_session.add(job)
        await async_session.commit()

        await scan_and_queue_matches(async_session)

        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/alerts/")
            assert response.status_code == 200
            data = response.json()
            assert data["unread_total"] == 1
            assert data["ready_total"] == 0
            assert len(data["alerts"]) == 1
            assert data["alerts"][0]["draft_data"]["application_draft"].startswith("Hi")

            alert_id = data["alerts"][0]["id"]
            ready = await client.patch(f"/alerts/{alert_id}/status", json={"status": "ready"})
            assert ready.status_code == 200
            assert ready.json()["status"] == "ready"

            refreshed = await client.get("/alerts/")
            assert refreshed.json()["ready_total"] == 1

            mark_read = await client.patch(f"/alerts/{alert_id}/read")
            assert mark_read.status_code == 200
            assert mark_read.json()["status"] == "read"
    finally:
        fastapi_app.dependency_overrides.clear()
