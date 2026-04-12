import uuid
import pytest
from datetime import datetime

from backend.services.matching import (
    calculate_title_similarity,
    calculate_skill_match,
    calculate_seniority_fit,
    calculate_location_fit,
    calculate_salary_fit,
    calculate_remote_fit,
    score_job,
    MatchingService,
)


@pytest.fixture
async def async_session():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from backend.db.base import Base
    
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()


class TestTitleSimilarity:
    def test_exact_match(self):
        result = calculate_title_similarity(["Software Engineer"], "Software Engineer")
        assert result == 100.0

    def test_partial_match(self):
        result = calculate_title_similarity(["Software Engineer"], "Senior Software Engineer")
        assert result > 50.0

    def test_no_match(self):
        result = calculate_title_similarity(["Designer"], "Software Engineer")
        assert result < 50.0

    def test_empty_profile_roles(self):
        result = calculate_title_similarity([], "Software Engineer")
        assert result == 0.0

    def test_empty_job_title(self):
        result = calculate_title_similarity(["Engineer"], "")
        assert result == 0.0


class TestSkillMatch:
    def test_full_match(self):
        result = calculate_skill_match(["Python", "SQL", "Docker"], ["Python", "SQL", "Docker"])
        assert result == 100.0

    def test_partial_match(self):
        result = calculate_skill_match(["Python"], ["Python", "SQL", "Docker"])
        assert result == pytest.approx(33.33, rel=0.1)

    def test_no_overlap(self):
        result = calculate_skill_match(["Python"], ["Java", "C++"])
        assert result == 0.0

    def test_empty_job_skills(self):
        result = calculate_skill_match(["Python"], [])
        assert result == 50.0

    def test_empty_user_skills(self):
        result = calculate_skill_match([], ["Python"])
        assert result == 25.0


class TestSeniorityFit:
    def test_exact_match(self):
        result = calculate_seniority_fit("senior", "senior")
        assert result == 100.0

    def test_one_level_diff(self):
        result = calculate_seniority_fit("senior", "mid")
        assert result == 75.0

    def test_two_levels_diff(self):
        result = calculate_seniority_fit("junior", "senior")
        assert result == 50.0

    def test_ignore_case(self):
        result = calculate_seniority_fit("SENIOR", "Senior")
        assert result == 100.0


class TestLocationFit:
    def test_remote_in_profile(self):
        result = calculate_location_fit(["Remote"], "San Francisco, CA")
        assert result == 100.0

    def test_exact_location_match(self):
        result = calculate_location_fit(["San Francisco"], "San Francisco, CA")
        assert result == 100.0

    def test_partial_location_match(self):
        result = calculate_location_fit(["California"], "San Francisco, CA")
        assert result == 100.0

    def test_no_match(self):
        result = calculate_location_fit(["New York"], "San Francisco, CA")
        assert result == 25.0

    def test_empty_profile_locations(self):
        result = calculate_location_fit([], "San Francisco, CA")
        assert result == 50.0


class TestSalaryFit:
    def test_at_floor(self):
        result = calculate_salary_fit(100000, 100000, 150000)
        assert result == 100.0

    def test_above_max(self):
        result = calculate_salary_fit(200000, 50000, 100000)
        assert result == 20.0

    def test_between_range(self):
        result = calculate_salary_fit(125000, 100000, 150000)
        assert result > 50.0

    def test_no_job_salary(self):
        result = calculate_salary_fit(100000, None, None)
        assert result == 50.0

    def test_no_profile_floor(self):
        result = calculate_salary_fit(None, 100000, 150000)
        assert result == 50.0


class TestRemoteFit:
    def test_both_remote(self):
        result = calculate_remote_fit("remote", "remote")
        assert result == 100.0

    def test_profile_remote_job_onsite(self):
        result = calculate_remote_fit("remote", "onsite")
        assert result == 75.0

    def test_both_onsite(self):
        result = calculate_remote_fit("onsite", "onsite")
        assert result == 100.0

    def test_hybrid_match(self):
        result = calculate_remote_fit("hybrid", "hybrid")
        assert result == 100.0


class TestScoreJob:
    def test_perfect_match(self):
        profile = {
            "target_roles": ["Software Engineer"],
            "seniority": "senior",
            "salary_floor": 100000,
            "locations": ["Remote"],
            "remote_preference": "remote",
        }
        job = {
            "title": "Software Engineer",
            "skills_required": ["Python", "SQL"],
            "seniority": "senior",
            "location": "Remote",
            "salary_min": 100000,
            "salary_max": 150000,
            "remote_type": "remote",
        }
        
        score, breakdown, explanation = score_job(profile, job, ["Python", "SQL"])
        
        assert score >= 80.0
        assert breakdown.title_similarity == 100.0
        assert breakdown.skill_match == 100.0
        assert breakdown.seniority_fit == 100.0
        assert "strong title match" in explanation

    def test_poor_match(self):
        profile = {
            "target_roles": ["Designer"],
            "seniority": "junior",
            "salary_floor": 50000,
            "locations": ["NYC"],
            "remote_preference": "onsite",
        }
        job = {
            "title": "Senior Backend Engineer",
            "skills_required": ["Kubernetes", "Go"],
            "seniority": "senior",
            "location": "London",
            "salary_min": 200000,
            "salary_max": 300000,
            "remote_type": "onsite",
        }
        
        score, breakdown, explanation = score_job(profile, job, ["Figma", "Sketch"])
        
        assert score < 50.0


class TestMatchingService:
    @pytest.mark.asyncio
    async def test_score_job_creates_match_score(self, async_session):
        from backend.db.models import User, Profile, Job, MatchScore
        from backend.services.auth import get_password_hash
        from sqlalchemy import select
        
        user = User(
            id=uuid.uuid4(),
            email="match-test@example.com",
            password_hash=get_password_hash("password"),
        )
        async_session.add(user)
        
        profile = Profile(
            id=uuid.uuid4(),
            user_id=user.id,
            target_roles=["Software Engineer"],
            seniority="senior",
            locations=["Remote"],
            remote_preference="remote",
        )
        async_session.add(profile)
        
        source = type('Source', (), {
            'id': uuid.uuid4(),
            'name': 'TestSource',
            'source_type': 'greenhouse',
            'base_url': 'https://test.com',
        })()
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
        
        service = MatchingService(async_session)
        match_score = await service.score_job_for_user(user.id, job.id)
        
        assert match_score is not None
        assert match_score.score_total > 0
        assert "title" in match_score.explanation.lower()

    @pytest.mark.asyncio
    async def test_get_jobs_with_scores(self, async_session):
        from backend.db.models import User, Job, MatchScore
        from backend.services.auth import get_password_hash
        
        user = User(
            id=uuid.uuid4(),
            email="list-test@example.com",
            password_hash=get_password_hash("password"),
        )
        async_session.add(user)
        
        source = type('Source', (), {
            'id': uuid.uuid4(),
            'name': 'TestSource2',
            'source_type': 'greenhouse',
            'base_url': 'https://test.com',
        })()
        async_session.add(source)
        await async_session.flush()
        
        job1 = Job(
            id=uuid.uuid4(),
            source_id=source.id,
            source_job_id="JOB-001",
            company="Corp A",
            title="Engineer",
            description="Role 1",
            application_url="https://test.com/1",
            source_url="https://test.com/1",
            raw_payload={},
            canonical_hash="abc123",
        )
        job2 = Job(
            id=uuid.uuid4(),
            source_id=source.id,
            source_job_id="JOB-002",
            company="Corp B",
            title="Designer",
            description="Role 2",
            application_url="https://test.com/2",
            source_url="https://test.com/2",
            raw_payload={},
            canonical_hash="def456",
        )
        async_session.add_all([job1, job2])
        
        score1 = MatchScore(
            id=uuid.uuid4(),
            job_id=job1.id,
            user_id=user.id,
            score_total=85.0,
            score_breakdown={},
            explanation="Good match",
        )
        score2 = MatchScore(
            id=uuid.uuid4(),
            job_id=job2.id,
            user_id=user.id,
            score_total=45.0,
            score_breakdown={},
            explanation="Poor match",
        )
        async_session.add_all([score1, score2])
        
        await async_session.commit()
        
        service = MatchingService(async_session)
        jobs, total = await service.get_jobs_with_scores(user.id)
        
        assert total == 2
        assert len(jobs) == 2
        assert jobs[0]["score_total"] == 85.0
        assert jobs[1]["score_total"] == 45.0
