import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.db.models import User
from backend.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)


@pytest.fixture
def test_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
    )


class TestPasswordHashing:
    def test_password_hash_creates_different_hash(self):
        password = "mypassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert hash1 != password

    def test_verify_password_correct(self):
        password = "correctpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "correctpassword"
        hashed = get_password_hash(password)
        
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    def test_create_and_verify_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        
        assert token is not None
        assert len(token) > 0
        
        verified_id = verify_access_token(token)
        assert verified_id == user_id

    def test_create_and_verify_refresh_token(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        
        assert token is not None
        assert len(token) > 0
        
        verified_id = verify_refresh_token(token)
        assert verified_id == user_id

    def test_access_token_fails_on_refresh_token(self):
        user_id = uuid.uuid4()
        refresh_token = create_refresh_token(user_id)
        
        result = verify_access_token(refresh_token)
        assert result is None

    def test_refresh_token_fails_on_access_token(self):
        user_id = uuid.uuid4()
        access_token = create_access_token(user_id)
        
        result = verify_refresh_token(access_token)
        assert result is None

    def test_invalid_token_returns_none(self):
        result = verify_access_token("invalid.token.here")
        assert result is None

    def test_tampered_token_returns_none(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        tampered = token[:-5] + "XXXXX"
        
        result = verify_access_token(tampered)
        assert result is None


class TestAuthRoutes:
    @pytest.mark.asyncio
    async def test_register_success(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={"email": "new@example.com", "password": "securepassword123"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        user = User(
            id=uuid.uuid4(),
            email="existing@example.com",
            password_hash=get_password_hash("password"),
        )
        async_session.add(user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={"email": "existing@example.com", "password": "password123"},
            )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_success(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        user = User(
            id=uuid.uuid4(),
            email="login@example.com",
            password_hash=get_password_hash("loginpassword"),
        )
        async_session.add(user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={"email": "login@example.com", "password": "loginpassword"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        user = User(
            id=uuid.uuid4(),
            email="wrongpass@example.com",
            password_hash=get_password_hash("correctpassword"),
        )
        async_session.add(user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={"email": "wrongpass@example.com", "password": "wrongpassword"},
            )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={"email": "nonexistent@example.com", "password": "anypassword"},
            )
        
        assert response.status_code == 401
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        user = User(
            id=uuid.uuid4(),
            email="refresh@example.com",
            password_hash=get_password_hash("password"),
        )
        async_session.add(user)
        await async_session.commit()
        
        refresh_token = create_refresh_token(user.id)
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/auth/refresh",
                json={"refresh_token": "invalid.token.here"},
            )
        
        assert response.status_code == 401
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_protected_route_without_token(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/auth/me")
        
        assert response.status_code == 401
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_protected_route_with_valid_token(self, async_session):
        from httpx import AsyncClient, ASGITransport
        from backend.db.base import get_session
        
        user = User(
            id=uuid.uuid4(),
            email="protected@example.com",
            password_hash=get_password_hash("password"),
        )
        async_session.add(user)
        await async_session.commit()
        
        access_token = create_access_token(user.id)
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
        
        app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_check(self):
        with TestClient(app) as client:
            response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
