import io
import uuid
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.db.models import User, Resume
from backend.services.auth import get_password_hash, create_access_token
from backend.services.parser import (
    allowed_file,
    get_file_type,
    extract_text,
    parse_resume_text,
    generate_file_hash,
)


class TestParserUtils:
    def test_allowed_file_pdf(self):
        assert allowed_file("resume.pdf") is True

    def test_allowed_file_docx(self):
        assert allowed_file("resume.docx") is True

    def test_allowed_file_txt(self):
        assert allowed_file("resume.txt") is False

    def test_allowed_file_uppercase(self):
        assert allowed_file("RESUME.PDF") is True

    def test_get_file_type_pdf(self):
        assert get_file_type("resume.pdf") == "pdf"

    def test_get_file_type_docx(self):
        assert get_file_type("resume.docx") == "docx"

    def test_generate_file_hash(self):
        content = b"test content"
        hash1 = generate_file_hash(content)
        hash2 = generate_file_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_generate_file_hash_different_content(self):
        hash1 = generate_file_hash(b"content1")
        hash2 = generate_file_hash(b"content2")
        assert hash1 != hash2


class TestParseResumeText:
    def test_parse_empty_text(self):
        result = parse_resume_text("")
        assert result.contact is None
        assert result.experience == []
        assert result.education == []
        assert result.skills == []

    def test_parse_with_sections(self):
        text = """
John Doe
john@example.com
(555) 123-4567

Profile
Software engineer with 5 years of experience.

Experience
Senior Software Engineer at Tech Corp
2020 - Present
- Led team of 5 engineers
- Built scalable systems

Education
BS Computer Science
University of Technology
2015 - 2019

Skills
Python, JavaScript, SQL, Docker
"""
        result = parse_resume_text(text)
        assert result.summary is not None
        assert len(result.experience) > 0
        assert len(result.education) > 0
        assert len(result.skills) > 0

    def test_extract_contact(self):
        text = """
John Doe
john@example.com
(555) 123-4567
"""
        result = parse_resume_text(text)
        assert result.contact is not None
        assert "email" in result.contact


@pytest.fixture
def test_user():
    return User(
        id=uuid.uuid4(),
        email="resume-test@example.com",
        password_hash=get_password_hash("password"),
    )


class TestResumeRoutes:
    @pytest.mark.asyncio
    async def test_upload_resume_requires_auth(self, async_session):
        from backend.db.base import get_session
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/resumes/",
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
                data={"version_name": "Test Resume"},
            )
        
        assert response.status_code == 401
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, async_session, test_user):
        from backend.db.base import get_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/resumes/",
                files={"file": ("test.txt", b"text content", "text/plain")},
                data={"version_name": "Test Resume"},
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_resumes_empty(self, async_session, test_user):
        from backend.db.base import get_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_user.id)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/resumes/",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        assert response.json() == []
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_resume_not_found(self, async_session, test_user):
        from backend.db.base import get_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_user.id)
        fake_id = uuid.uuid4()
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/resumes/{fake_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 404
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_resume_not_found(self, async_session, test_user):
        from backend.db.base import get_session
        
        async_session.add(test_user)
        await async_session.commit()
        
        async def override_get_session():
            yield async_session
        
        app.dependency_overrides[get_session] = override_get_session
        
        token = create_access_token(test_user.id)
        fake_id = uuid.uuid4()
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/resumes/{fake_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 404
        app.dependency_overrides.clear()
