import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from backend.db.models import (
    User, Profile, Resume, JobSource, Job, MatchScore,
    Application, ApplicationArtifact, Task, AuditLog
)

Base = declarative_base()


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_create(session):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
    )
    session.add(user)
    await session.commit()
    
    result = await session.get(User, user.id)
    assert result.email == "test@example.com"
    assert result.deleted_at is None


@pytest.mark.asyncio
async def test_user_soft_delete(session):
    user = User(
        id=uuid.uuid4(),
        email="delete@example.com",
        password_hash="hashed_password",
    )
    session.add(user)
    await session.commit()
    
    user.deleted_at = datetime.utcnow()
    await session.commit()
    
    from sqlalchemy import select
    stmt = select(User).where(User.deleted_at.is_(None))
    result = await session.execute(stmt)
    users = result.scalars().all()
    assert len(users) == 0


@pytest.mark.asyncio
async def test_profile_with_arrays(session):
    user = User(id=uuid.uuid4(), email="profile@example.com", password_hash="hash")
    session.add(user)
    await session.flush()
    
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user.id,
        target_roles=["Engineer", "Developer"],
        locations=["Remote", "New York"],
        keywords_include=["Python", "TypeScript"],
        keywords_exclude=["Java"],
    )
    session.add(profile)
    await session.commit()
    
    result = await session.get(Profile, profile.id)
    assert "Engineer" in result.target_roles
    assert "Java" in result.keywords_exclude


@pytest.mark.asyncio
async def test_job_source_unique_name(session):
    source1 = JobSource(
        id=uuid.uuid4(),
        name="Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io",
    )
    session.add(source1)
    await session.commit()
    
    source2 = JobSource(
        id=uuid.uuid4(),
        name="Greenhouse",
        source_type="greenhouse",
        base_url="https://other.greenhouse.io",
    )
    session.add(source2)
    
    with pytest.raises(Exception):
        await session.commit()


@pytest.mark.asyncio
async def test_job_with_indexes(session):
    source = JobSource(
        id=uuid.uuid4(),
        name="TestSource",
        source_type="manual",
        base_url="https://example.com",
    )
    session.add(source)
    await session.flush()
    
    job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="JOB-001",
        company="Acme Corp",
        title="Software Engineer",
        description="Build things",
        application_url="https://example.com/apply",
        source_url="https://example.com/job/1",
        raw_payload={"original": "data"},
        canonical_hash="abc123",
    )
    session.add(job)
    await session.commit()
    
    result = await session.get(Job, job.id)
    assert result.company == "Acme Corp"
    assert result.skills_required == []
    assert result.benefits == []


@pytest.mark.asyncio
async def test_match_score_unique_constraint(session):
    user = User(id=uuid.uuid4(), email="match@example.com", password_hash="hash")
    session.add(user)
    
    source = JobSource(
        id=uuid.uuid4(),
        name="MatchSource",
        source_type="manual",
        base_url="https://example.com",
    )
    session.add(source)
    await session.flush()
    
    job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="JOB-MATCH-001",
        company="Match Corp",
        title="Engineer",
        description="Test",
        application_url="https://example.com/apply",
        source_url="https://example.com/job/1",
        raw_payload={},
        canonical_hash="match123",
    )
    session.add(job)
    await session.flush()
    
    score1 = MatchScore(
        id=uuid.uuid4(),
        job_id=job.id,
        user_id=user.id,
        score_total=85.5,
        score_breakdown={"skills": 40, "title": 30, "location": 15.5},
        explanation="Good match for Python developer",
    )
    session.add(score1)
    await session.commit()
    
    score2 = MatchScore(
        id=uuid.uuid4(),
        job_id=job.id,
        user_id=user.id,
        score_total=90.0,
        score_breakdown={"skills": 50, "title": 30, "location": 10},
        explanation="Updated score",
    )
    session.add(score2)
    
    with pytest.raises(Exception):
        await session.commit()


@pytest.mark.asyncio
async def test_application_workflow(session):
    user = User(id=uuid.uuid4(), email="app@example.com", password_hash="hash")
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user.id,
        version_name="Primary",
        source_file="/path/to/resume.pdf",
        file_type="pdf",
        parsed_json={},
        rendered_text="Resume content",
        is_primary=True,
    )
    source = JobSource(
        id=uuid.uuid4(),
        name="AppSource",
        source_type="manual",
        base_url="https://example.com",
    )
    session.add_all([user, resume, source])
    await session.flush()
    
    job = Job(
        id=uuid.uuid4(),
        source_id=source.id,
        source_job_id="APP-JOB-001",
        company="Hiring Corp",
        title="Developer",
        description="Great opportunity",
        application_url="https://example.com/apply",
        source_url="https://example.com/job/2",
        raw_payload={},
        canonical_hash="app123",
    )
    session.add(job)
    await session.flush()
    
    app = Application(
        id=uuid.uuid4(),
        user_id=user.id,
        job_id=job.id,
        resume_id=resume.id,
        status="found",
    )
    session.add(app)
    await session.commit()
    
    assert app.status == "found"
    
    app.status = "submitted"
    app.submitted_at = datetime.utcnow()
    app.submission_method = "manual"
    await session.commit()
    
    result = await session.get(Application, app.id)
    assert result.status == "submitted"
    assert result.submitted_at is not None


@pytest.mark.asyncio
async def test_audit_log_captures_changes(session):
    user = User(id=uuid.uuid4(), email="audit@example.com", password_hash="hash")
    session.add(user)
    await session.flush()
    
    audit = AuditLog(
        id=uuid.uuid4(),
        actor="system",
        actor_id=user.id,
        action="user.created",
        target_type="user",
        target_id=user.id,
        before=None,
        after={"email": "audit@example.com"},
        ip_address="127.0.0.1",
    )
    session.add(audit)
    await session.commit()
    
    result = await session.get(AuditLog, audit.id)
    assert result.action == "user.created"
    assert result.after["email"] == "audit@example.com"
