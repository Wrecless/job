import uuid
import pytest
from datetime import datetime, timedelta, timezone

from backend.db.models import Application, Task, Job, Resume, User, JobSource
from backend.services.auth import get_password_hash


@pytest.fixture
async def test_data(async_session):
    user = User(
        id=uuid.uuid4(),
        email="app-test@example.com",
        password_hash=get_password_hash("password"),
    )
    async_session.add(user)
    
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user.id,
        version_name="Primary",
        source_file="/path/to/resume.pdf",
        file_type="pdf",
        parsed_json={"skills": ["Python"]},
        rendered_text="Resume content",
        is_primary=True,
    )
    async_session.add(resume)
    
    source = JobSource(
        id=uuid.uuid4(),
        name='TestSource',
        source_type='greenhouse',
        base_url='https://test.com',
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
    
    return {"user": user, "resume": resume, "job": job}


class TestApplicationModel:
    @pytest.mark.asyncio
    async def test_create_application(self, async_session, test_data):
        app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="found",
        )
        async_session.add(app)
        await async_session.commit()
        
        result = await async_session.get(Application, app.id)
        assert result is not None
        assert result.status == "found"

    @pytest.mark.asyncio
    async def test_update_status_to_submitted(self, async_session, test_data):
        app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="found",
        )
        async_session.add(app)
        await async_session.commit()
        
        app.status = "submitted"
        app.submitted_at = datetime.now(timezone.utc)
        await async_session.commit()
        
        result = await async_session.get(Application, app.id)
        assert result.status == "submitted"
        assert result.submitted_at is not None

    @pytest.mark.asyncio
    async def test_unique_user_job_constraint(self, async_session, test_data):
        app1 = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="found",
        )
        async_session.add(app1)
        await async_session.commit()
        
        app2 = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="saved",
        )
        async_session.add(app2)
        
        with pytest.raises(Exception):
            await async_session.commit()


class TestTaskModel:
    @pytest.mark.asyncio
    async def test_create_task(self, async_session, test_data):
        app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="found",
        )
        async_session.add(app)
        await async_session.flush()
        
        task = Task(
            id=uuid.uuid4(),
            application_id=app.id,
            task_type="follow_up",
            status="pending",
            due_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        async_session.add(task)
        await async_session.commit()
        
        result = await async_session.get(Task, task.id)
        assert result is not None
        assert result.task_type == "follow_up"
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_complete_task(self, async_session, test_data):
        app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="submitted",
        )
        async_session.add(app)
        await async_session.flush()
        
        task = Task(
            id=uuid.uuid4(),
            application_id=app.id,
            task_type="interview_prep",
            status="pending",
        )
        async_session.add(task)
        await async_session.commit()
        
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        await async_session.commit()
        
        result = await async_session.get(Task, task.id)
        assert result.status == "completed"
        assert result.completed_at is not None


class TestApplicationRoutes:
    @pytest.mark.asyncio
    async def test_create_application_endpoint(self, async_session, test_data):
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
        
        test_app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="found",
        )
        async_session.add(test_app)
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
    async def test_update_application_status(self, async_session, test_data):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app as fastapi_app
        from backend.db.base import get_session
        from backend.services.auth import create_access_token
        
        test_app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="found",
        )
        async_session.add(test_app)
        await async_session.commit()
        app_id = str(test_app.id)
        
        async def override_get_session():
            yield async_session
        
        fastapi_app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_data["user"].id)
        
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/applications/{app_id}",
                json={"status": "submitted", "submission_method": "manual"},
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert data["submission_method"] == "manual"
        
        fastapi_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_task_endpoint(self, async_session, test_data):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app as fastapi_app
        from backend.db.base import get_session
        from backend.services.auth import create_access_token
        
        test_app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="submitted",
        )
        async_session.add(test_app)
        await async_session.commit()
        app_id = str(test_app.id)
        
        async def override_get_session():
            yield async_session
        
        fastapi_app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_data["user"].id)
        
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/applications/{app_id}/tasks",
                json={
                    "task_type": "follow_up",
                    "due_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_type"] == "follow_up"
        assert data["status"] == "pending"
        
        fastapi_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_pending_tasks(self, async_session, test_data):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app as fastapi_app
        from backend.db.base import get_session
        from backend.services.auth import create_access_token
        
        test_app = Application(
            id=uuid.uuid4(),
            user_id=test_data["user"].id,
            job_id=test_data["job"].id,
            resume_id=test_data["resume"].id,
            status="submitted",
        )
        async_session.add(test_app)
        await async_session.flush()
        
        task = Task(
            id=uuid.uuid4(),
            application_id=test_app.id,
            task_type="follow_up",
            status="pending",
            due_at=datetime.now(timezone.utc) + timedelta(days=3),
        )
        async_session.add(task)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        fastapi_app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_data["user"].id)
        
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/applications/tasks/pending",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["task_type"] == "follow_up"
        
        fastapi_app.dependency_overrides.clear()
