import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.main import app
from backend.db.base import Base
from backend.db.models import User, JobSource, Job
from backend.services.auth import get_password_hash, create_access_token
from backend.services.ingestion import (
    BaseConnector,
    GreenhouseConnector,
    LeverConnector,
    AshbyConnector,
    SourceRegistry,
)


class TestConnectors:
    def test_greenhouse_connector_initialization(self):
        connector = GreenhouseConnector("https://boards.greenhouse.io/test")
        assert connector.source_name == "greenhouse"
        assert connector.base_url == "https://boards.greenhouse.io/test"

    def test_lever_connector_initialization(self):
        connector = LeverConnector("https://jobs.lever.co/test")
        assert connector.source_name == "lever"
        assert connector.base_url == "https://jobs.lever.co/test"

    def test_ashby_connector_initialization(self):
        connector = AshbyConnector("https://api.ashbyhq.com/test")
        assert connector.source_name == "ashby"
        assert connector.base_url == "https://api.ashbyhq.com/test"

    def test_base_connector_normalize_greenhouse(self):
        connector = GreenhouseConnector("https://boards.greenhouse.io/test")
        raw = {
            "id": 12345,
            "title": "Software Engineer",
            "content": "<p>Job description</p>",
            "location": "San Francisco, CA",
            "departments": [{"name": "Engineering"}],
            "offices": [{"name": "SF", "location": "CA"}],
            "employment_type": "Full-time",
        }
        normalized = connector.normalize(raw)
        
        assert normalized["source_job_id"] == "12345"
        assert normalized["title"] == "Software Engineer"
        assert normalized["company"] == "Engineering"
        assert normalized["location"] == "San Francisco, CA"
        assert normalized["employment_type"] == "full-time"
        assert "Job description" in normalized["description"]
        assert normalized["canonical_hash"] is not None

    def test_base_connector_normalize_lever(self):
        connector = LeverConnector("https://jobs.lever.co/test")
        raw = {
            "id": "abc123",
            "text": "Lever job description",
            "lists": {
                "Location": ["New York"],
                "Team": ["Backend"],
            },
        }
        normalized = connector.normalize(raw)
        
        assert normalized["source_job_id"] == "abc123"
        assert "Lever job description" in normalized["description"]

    def test_base_connector_normalize_with_compensation(self):
        connector = AshbyConnector("https://api.ashbyhq.com/test")
        raw = {
            "id": "job123",
            "title": "Senior Engineer",
            "description": "Great role",
            "compensation": {
                "min_cents": 15000000,
                "max_cents": 20000000,
            },
        }
        normalized = connector.normalize(raw)
        
        assert normalized["salary_min"] == 150000
        assert normalized["salary_max"] == 200000


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def test_user():
    return User(
        id=uuid.uuid4(),
        email="source-test@example.com",
        password_hash=get_password_hash("password"),
    )


class TestSourceRegistry:
    @pytest.mark.asyncio
    async def test_create_source(self, async_session):
        registry = SourceRegistry(async_session)
        source = await registry.create_source(
            name="TestSource",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/test",
        )
        
        assert source.name == "TestSource"
        assert source.source_type == "greenhouse"
        assert source.is_active is True

    @pytest.mark.asyncio
    async def test_get_source(self, async_session):
        registry = SourceRegistry(async_session)
        created = await registry.create_source(
            name="GetTest",
            source_type="lever",
            base_url="https://jobs.lever.co/test",
        )
        
        found = await registry.get_source("GetTest")
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_source_not_found(self, async_session):
        registry = SourceRegistry(async_session)
        found = await registry.get_source("NonExistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_or_create_source_creates(self, async_session):
        registry = SourceRegistry(async_session)
        source, created = await registry.get_or_create_source(
            name="NewSource",
            source_type="ashby",
            base_url="https://api.ashbyhq.com/test",
        )
        
        assert created is True
        assert source.name == "NewSource"

    @pytest.mark.asyncio
    async def test_get_or_create_source_returns_existing(self, async_session):
        registry = SourceRegistry(async_session)
        first, created1 = await registry.get_or_create_source(
            name="ExistingSource",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/test",
        )
        
        second, created2 = await registry.get_or_create_source(
            name="ExistingSource",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/test",
        )
        
        assert created1 is True
        assert created2 is False
        assert first.id == second.id

    @pytest.mark.asyncio
    async def test_list_sources(self, async_session):
        registry = SourceRegistry(async_session)
        await registry.create_source("Source1", "greenhouse", "https://1.com")
        await registry.create_source("Source2", "lever", "https://2.com")
        
        sources = await registry.list_sources()
        assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_list_sources_active_only(self, async_session):
        registry = SourceRegistry(async_session)
        source1 = await registry.create_source("ActiveSource", "greenhouse", "https://1.com")
        source2 = await registry.create_source("InactiveSource", "lever", "https://2.com")
        
        source2.is_active = False
        await async_session.commit()
        
        active = await registry.list_sources(active_only=True)
        assert len(active) == 1
        assert active[0].name == "ActiveSource"


class TestSourceRoutes:
    @pytest.mark.asyncio
    async def test_create_source_requires_auth(self, async_session):
        from backend.db.base import async_session as db_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        with TestClient(app) as client:
            response = client.post(
                "/sources/",
                json={"name": "Test", "source_type": "greenhouse", "base_url": "https://test.com"},
            )
        
        assert response.status_code == 401
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sources(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            response = client.get(
                "/sources/",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_source(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            response = client.post(
                "/sources/",
                json={
                    "name": "MyGreenhouse",
                    "source_type": "greenhouse",
                    "base_url": "https://boards.greenhouse.io/mycompany",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MyGreenhouse"
        assert data["source_type"] == "greenhouse"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_source(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            client.post(
                "/sources/",
                json={"name": "GetTest", "source_type": "lever", "base_url": "https://test.com"},
                headers={"Authorization": f"Bearer {token}"},
            )
            
            response = client.get(
                "/sources/GetTest",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        assert response.json()["name"] == "GetTest"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_source_not_found(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            response = client.get(
                "/sources/NonExistent",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 404
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_toggle_source(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            client.post(
                "/sources/",
                json={"name": "ToggleTest", "source_type": "greenhouse", "base_url": "https://test.com"},
                headers={"Authorization": f"Bearer {token}"},
            )
            
            response = client.patch(
                "/sources/ToggleTest/toggle?is_active=false",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_source(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            client.post(
                "/sources/",
                json={"name": "DeleteTest", "source_type": "lever", "base_url": "https://test.com"},
                headers={"Authorization": f"Bearer {token}"},
            )
            
            response = client.delete(
                "/sources/DeleteTest",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]
        app.dependency_overrides.clear()
