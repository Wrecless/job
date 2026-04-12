import uuid
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.main import app
from backend.db.base import Base
from backend.db.models import User, Profile
from backend.services.auth import get_password_hash, create_access_token


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
        email="profile-test@example.com",
        password_hash=get_password_hash("password"),
    )


class TestProfileRoutes:
    @pytest.mark.asyncio
    async def test_get_profile_requires_auth(self, async_session):
        from backend.db.base import async_session as db_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        with TestClient(app) as client:
            response = client.get("/profile/")
        
        assert response.status_code == 401
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_profile_creates_default(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            response = client.get(
                "/profile/",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert data["target_roles"] == []
        assert data["locations"] == []
        assert data["sponsorship_needed"] is False
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_profile(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            response = client.post(
                "/profile/",
                json={
                    "headline": "Senior Software Engineer",
                    "target_roles": ["Software Engineer", "Tech Lead"],
                    "locations": ["Remote", "San Francisco"],
                    "seniority": "senior",
                    "sponsorship_needed": False,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["headline"] == "Senior Software Engineer"
        assert "Software Engineer" in data["target_roles"]
        assert "San Francisco" in data["locations"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_profile(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            client.post(
                "/profile/",
                json={"headline": "Initial"},
                headers={"Authorization": f"Bearer {token}"},
            )
            
            response = client.put(
                "/profile/",
                json={"headline": "Updated Engineer"},
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["headline"] == "Updated Engineer"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_patch_profile_partial(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            client.put(
                "/profile/",
                json={
                    "headline": "Full Profile",
                    "target_roles": ["Engineer"],
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            
            response = client.patch(
                "/profile/",
                json={"headline": "Patched Headline"},
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["headline"] == "Patched Headline"
        assert data["target_roles"] == ["Engineer"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_profile_already_exists(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            client.post(
                "/profile/",
                json={"headline": "First"},
                headers={"Authorization": f"Bearer {token}"},
            )
            
            response = client.post(
                "/profile/",
                json={"headline": "Second"},
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_profile_with_array_fields(self, async_session, test_user):
        from backend.db.base import async_session as db_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[db_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        with TestClient(app) as client:
            response = client.post(
                "/profile/",
                json={
                    "target_roles": ["SWE", "SRE", "DevOps"],
                    "locations": ["NYC", "LA", "Remote"],
                    "industries_to_avoid": ["Finance", "Gaming"],
                    "keywords_include": ["Python", "Kubernetes", "AWS"],
                    "keywords_exclude": ["C#", "Unity"],
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["target_roles"]) == 3
        assert len(data["locations"]) == 3
        assert "Finance" in data["industries_to_avoid"]
        assert "Python" in data["keywords_include"]
        assert "C#" in data["keywords_exclude"]
        app.dependency_overrides.clear()
