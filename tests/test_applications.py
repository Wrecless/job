import uuid
import pytest

from backend.db.models import Application, Job, JobSource, Resume, User
from backend.services.auth import get_password_hash


@pytest.fixture
async def test_data(async_session):
    user = User(
        id=uuid.uuid4(),
        email="app-test@example.com",
        password_hash=get_password_hash("password"),
    )
    async_session.add(user)

    source = JobSource(
        id=uuid.uuid4(),
        name="TestSource",
        source_type="greenhouse",
        base_url="https://test.com",
    )
    async_session.add(source)
    await async_session.flush()

    job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="JOB-001",
        company="Test Corp",
        title="Software Engineer",
        description="Great role",
        application_url="https://test.com/apply",
        source_url="https://test.com/job",
        raw_payload={},
        canonical_hash="abc123",
    )
    async_session.add(job)
    await async_session.commit()

    return {"user": user, "job": job}


class TestApplicationWorkflow:
    @pytest.mark.asyncio
    async def test_create_application_without_resume(self, async_session, test_data):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app as fastapi_app
        from backend.db.base import get_session
        from backend.services.auth import create_access_token

        async def override_get_session():
            yield async_session

        fastapi_app.dependency_overrides[get_session] = override_get_session

        token = create_access_token(test_data["user"].id)

        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/applications/",
                json={"job_id": str(test_data["job"].id)},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "found"
        assert data["job_id"] == str(test_data["job"].id)

        fastapi_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_applications(self, async_session, test_data):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app as fastapi_app
        from backend.db.base import get_session
        from backend.services.auth import create_access_token

        resume = Resume(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            version_name="System Resume",
            source_file="system://placeholder",
            file_type="system",
            parsed_json={},
            rendered_text="",
            is_primary=True,
        )
        async_session.add(resume)

        application = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=resume.id,
            status="found",
        )
        async_session.add(application)
        await async_session.commit()

        async def override_get_session():
            yield async_session

        fastapi_app.dependency_overrides[get_session] = override_get_session

        token = create_access_token(test_data["user"].id)

        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/applications/",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["applications"]) == 1
        assert data["pipeline"]["found"] == 1

        fastapi_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_application(self, async_session, test_data):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app as fastapi_app
        from backend.db.base import get_session
        from backend.services.auth import create_access_token

        resume = Resume(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            version_name="System Resume",
            source_file="system://placeholder",
            file_type="system",
            parsed_json={},
            rendered_text="",
            is_primary=True,
        )
        async_session.add(resume)

        application = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=resume.id,
            status="found",
        )
        async_session.add(application)
        await async_session.commit()

        async def override_get_session():
            yield async_session

        fastapi_app.dependency_overrides[get_session] = override_get_session

        token = create_access_token(test_data["user"].id)

        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/applications/{application.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

        fastapi_app.dependency_overrides.clear()
