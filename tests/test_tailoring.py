import uuid
import pytest

from backend.services.tailoring import (
    extract_keywords,
    find_matching_skills,
    find_relevant_experience,
    tailor_bullet,
    generate_tailored_resume_bullets,
    generate_summary_suggestion,
    generate_cover_letter_intro,
    generate_cover_letter_body,
    generate_cover_letter_closing,
    generate_cover_letter,
    TailoringService,
)


class TestExtractKeywords:
    def test_extract_python(self):
        result = extract_keywords("Experience with Python and Django")
        assert "python" in result

    def test_extract_multiple(self):
        result = extract_keywords("Built with React, Node.js, and AWS")
        assert "react" in result
        assert "node" in result
        assert "aws" in result

    def test_empty_text(self):
        result = extract_keywords("")
        assert len(result) == 0


class TestFindMatchingSkills:
    def test_full_match(self):
        resume_skills = ["Python", "SQL", "Docker"]
        job_skills = ["Python", "SQL", "Docker"]
        matched, unmatched = find_matching_skills(resume_skills, "", job_skills)
        assert len(matched) == 3
        assert len(unmatched) == 0

    def test_partial_match(self):
        resume_skills = ["Python", "SQL"]
        job_skills = ["Python", "Docker", "Kubernetes"]
        matched, unmatched = find_matching_skills(resume_skills, "", job_skills)
        assert "python" in matched
        assert "python" not in unmatched

    def test_case_insensitive(self):
        resume_skills = ["PYTHON", "JAVASCRIPT"]
        job_skills = ["Python", "React"]
        matched, unmatched = find_matching_skills(resume_skills, "", job_skills)
        assert "python" in matched


class TestFindRelevantExperience:
    def test_finds_matching_experience(self):
        experience = [
            {
                "title": "Software Engineer",
                "organization": "Tech Corp",
                "bullets": ["Built API with Python and Docker"],
            }
        ]
        keywords = {"python", "docker", "api"}
        result = find_relevant_experience(experience, keywords)
        assert len(result) == 1
        assert result[0]["overlap_score"] >= 2

    def test_ignores_non_matching(self):
        experience = [
            {
                "title": "Designer",
                "organization": "Art Studio",
                "bullets": ["Created logos and graphics"],
            }
        ]
        keywords = {"python", "docker", "kubernetes"}
        result = find_relevant_experience(experience, keywords)
        assert len(result) == 0

    def test_sorts_by_relevance(self):
        experience = [
            {
                "title": "Junior Dev",
                "organization": "Small Co",
                "bullets": ["Used Python once"],
            },
            {
                "title": "Senior Engineer",
                "organization": "Big Tech",
                "bullets": ["Led team using Python, Docker, Kubernetes, and AWS"],
            },
        ]
        keywords = {"python", "docker", "kubernetes", "aws"}
        result = find_relevant_experience(experience, keywords)
        assert result[0]["organization"] == "Big Tech"


class TestTailorBullet:
    def test_basic_tailoring(self):
        bullet = "Built scalable systems with Python and Docker"
        result = tailor_bullet(bullet, ["python", "docker"], "Software Engineer")
        assert "Python" in result or "Docker" in result

    def test_preserves_original(self):
        bullet = "Developed REST APIs using Node.js"
        result = tailor_bullet(bullet, ["node", "api"], "Backend Engineer")
        assert "REST APIs" in result or "Node" in result


class TestGenerateTailoredResumeBullets:
    def test_generates_bullets(self):
        resume = {
            "experience": [
                {
                    "description": "Built API with Python at Tech Corp",
                    "bullets": ["Built API with Python", "Deployed with Docker"],
                }
            ],
            "skills": ["Python", "Docker"],
        }
        job = type('Job', (), {
            "title": "Backend Engineer",
            "description": "Looking for Python and Docker experts",
            "skills_required": ["Python", "Docker"],
        })()
        
        bullets, missing, confidence = generate_tailored_resume_bullets(resume, job)
        
        assert len(bullets) > 0
        assert confidence > 0

    def test_identifies_missing(self):
        resume = {
            "experience": [
                {
                    "description": "Did some stuff at Co",
                    "bullets": ["Did some stuff"],
                }
            ],
            "skills": ["Python"],
        }
        job = type('Job', (), {
            "title": "ML Engineer",
            "description": "Need TensorFlow, PyTorch, and Kubernetes experience",
            "skills_required": ["TensorFlow", "PyTorch", "Kubernetes"],
        })()
        
        bullets, missing, confidence = generate_tailored_resume_bullets(resume, job)
        
        assert confidence < 0.7


class TestGenerateSummarySuggestion:
    def test_with_existing_summary(self):
        result = generate_summary_suggestion(
            "Experienced developer",
            "Software Engineer",
            "Tech Corp",
            ["Python", "Docker"],
        )
        assert "Software Engineer" in result
        assert "Tech Corp" in result

    def test_without_summary(self):
        result = generate_summary_suggestion(
            None,
            "Engineer",
            "Company",
            ["Python"],
        )
        assert "Engineer" in result


class TestCoverLetterGeneration:
    def test_intro_generation(self):
        job = type('Job', (), {"title": "Engineer", "company": "Tech Corp"})()
        profile = {"headline": "Senior Developer"}
        intro, prompt = generate_cover_letter_intro(job, profile)
        assert "Engineer" in intro
        assert "Tech Corp" in intro

    def test_body_generation(self):
        resume = {
            "experience": [
                {
                    "title": "Developer",
                    "organization": "Old Co",
                    "bullets": ["Built systems with Python"],
                }
            ],
            "skills": ["Python"],
        }
        job = type('Job', (), {"title": "Engineer", "company": "Co"})()
        body = generate_cover_letter_body(job, resume, ["python"])
        assert len(body) > 0
        assert "Old Co" in body[0]["content"]

    def test_closing_generation(self):
        job = type('Job', (), {"title": "Engineer", "company": "Tech Corp"})()
        closing, prompt = generate_cover_letter_closing(job, "Tech Corp")
        assert "Tech Corp" in closing
        assert "Engineer" in closing

    def test_full_letter_generation(self):
        resume = {
            "experience": [
                {
                    "title": "Developer",
                    "organization": "Co",
                    "bullets": ["Built things"],
                }
            ],
            "skills": ["Python"],
            "summary": None,
        }
        job = type('Job', (), {
            "title": "Engineer",
            "company": "Tech Corp",
            "description": "Need Python experts",
            "skills_required": ["Python"],
        })()
        profile = {}
        
        result, missing, confidence = generate_cover_letter(resume, job, profile)
        
        assert "intro" in result
        assert "closing" in result
        assert "Tech Corp" in result["full_text"]
        assert confidence > 0


class TestTailoringService:
    @pytest.mark.asyncio
    async def test_service_requires_job_and_resume(self, async_session):
        service = TailoringService(async_session)
        fake_job_id = uuid.uuid4()
        
        result = await service.tailor_resume(
            user_id=uuid.uuid4(),
            job_id=fake_job_id,
        )
        
        assert result is None
