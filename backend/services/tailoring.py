import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User, Profile, Resume, Job, ApplicationArtifact


def extract_keywords(text: str) -> set[str]:
    keywords = set()
    important_words = {
        "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
        "react", "angular", "vue", "node", "django", "flask", "fastapi",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "git", "ci/cd", "devops", "agile", "scrum",
        "machine learning", "ml", "ai", "data science", "tensorflow", "pytorch",
        "api", "rest", "graphql", "microservices", "distributed",
        "lead", "managed", "developed", "implemented", "designed", "built",
        "team", "architecture", "scalable", "performance", "optimization",
    }
    text_lower = text.lower()
    for word in important_words:
        if word in text_lower:
            keywords.add(word)
    return keywords


def find_matching_skills(
    resume_skills: list[str],
    job_description: str,
    job_skills: list[str],
) -> tuple[list[str], list[str]]:
    resume_skills_lower = {s.lower() for s in resume_skills}
    job_keywords = extract_keywords(job_description)
    job_skills_lower = {s.lower() for s in job_skills}
    
    all_job_requirements = job_keywords | job_skills_lower
    
    matched = list(resume_skills_lower & all_job_requirements)
    unmatched = list(resume_skills_lower - all_job_requirements)
    
    return matched, unmatched


def find_relevant_experience(
    resume_experience: list[dict],
    job_keywords: set[str],
) -> list[dict]:
    relevant = []
    
    for exp in resume_experience:
        description = exp.get("description", "").lower()
        bullets = exp.get("bullets", [])
        
        exp_keywords = set()
        for bullet in bullets:
            exp_keywords |= extract_keywords(bullet)
        
        overlap = exp_keywords & job_keywords
        if overlap:
            relevant.append({
                "title": exp.get("title", ""),
                "organization": exp.get("organization", ""),
                "bullets": bullets,
                "matched_keywords": list(overlap),
                "overlap_score": len(overlap),
            })
    
    relevant.sort(key=lambda x: x["overlap_score"], reverse=True)
    return relevant


def tailor_bullet(
    bullet: str,
    matched_skills: list[str],
    job_title: str,
) -> str:
    tailored = bullet
    
    skill_mentions = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "react": "React",
        "api": "REST APIs",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "sql": "SQL",
        "machine learning": "machine learning",
        "ml": "ML",
    }
    
    for skill, display in skill_mentions.items():
        if skill in bullet.lower() and skill in [s.lower() for s in matched_skills]:
            if display.lower() not in bullet.lower():
                pass
    
    return tailored


def generate_tailored_resume_bullets(
    resume: dict,
    job: dict,
) -> tuple[list[dict], list[str], float]:
    from backend.schemas.tailoring import TailoredBullet
    
    job_keywords = extract_keywords(job.description)
    job_keywords |= extract_keywords(job.title)
    
    if job.skills_required:
        job_keywords |= {s.lower() for s in job.skills_required}
    
    resume_experience = resume.get("experience", [])
    relevant_exp = find_relevant_experience(resume_experience, job_keywords)
    
    matched_skills, unmatched_skills = find_matching_skills(
        resume.get("skills", []),
        job.description,
        job.skills_required or [],
    )
    
    tailored_bullets = []
    
    for exp in relevant_exp[:3]:
        exp_bullets = exp.get('bullets', [])
        for bullet in exp_bullets[:2]:
            tailored = tailor_bullet(bullet, matched_skills, job.title)
            tailored_bullets.append(TailoredBullet(
                original=bullet,
                tailored=tailored,
                source_section=f"{exp.get('title', 'Experience')} at {exp.get('organization', '')}",
                skills_matched=exp.get('matched_keywords', []),
                confidence=0.85,
            ))
    
    missing = []
    for skill in list(job_keywords)[:5]:
        if skill not in matched_skills and skill not in unmatched_skills:
            if len(skill) > 2:
                missing.append(skill)
    
    confidence = len(matched_skills) / max(len(job_keywords), 1)
    
    return tailored_bullets, missing, min(confidence + 0.3, 0.95)


def generate_summary_suggestion(
    resume_summary: str | None,
    job_title: str,
    company: str,
    matched_skills: list[str],
) -> str:
    if resume_summary:
        return f"Experienced professional seeking to leverage {', '.join(matched_skills[:3])} expertise as {job_title} at {company}."
    
    return f"Looking to apply strong {', '.join(matched_skills[:3])} skills as {job_title}."


def generate_cover_letter_intro(
    job: dict,
    profile: dict,
) -> tuple[str, str]:
    prompt = f"Write a professional cover letter opening for a {job.title} position at {job.company}."
    
    intro = f"I am excited to apply for the {job.title} position at {job.company}."
    
    if profile.get("headline"):
        intro += f" With my background as a {profile['headline']},"
    
    intro += " I bring a strong combination of technical skills and proven experience that aligns well with this role."
    
    return intro, prompt


def generate_cover_letter_body(
    job: dict,
    resume: dict,
    matched_skills: list[str],
) -> list[dict]:
    body_sections = []
    
    prompt1 = f"Write a paragraph highlighting relevant experience with {', '.join(matched_skills[:3])} for a {job.title} role."
    
    if resume.get("experience"):
        first_exp = resume["experience"][0]
        org = first_exp.get("organization", "my previous position")
        body_sections.append({
            "content": f"In my role at {org}, I developed hands-on expertise in {', '.join(matched_skills[:2])}, skills directly applicable to this position.",
            "prompt_used": prompt1,
        })
    
    prompt2 = f"Write a paragraph about achievements with {matched_skills[0] if matched_skills else 'technical skills'}."
    
    if resume.get("experience"):
        for exp in resume["experience"][:2]:
            bullets = exp.get("bullets", [])
            if bullets:
                body_sections.append({
                    "content": f"Key achievement: {bullets[0][:150]}...",
                    "prompt_used": prompt2,
                })
                break
    
    return body_sections


def generate_cover_letter_closing(
    job: dict,
    company: str,
) -> tuple[str, str]:
    prompt = f"Write a closing paragraph expressing enthusiasm for {job.title} at {company} and requesting an interview."
    
    closing = f"I am enthusiastic about the opportunity to contribute to {company} as {job.title} and would welcome the chance to discuss how my background aligns with your team's needs. Thank you for considering my application."
    
    return closing, prompt


def generate_cover_letter(
    resume: dict,
    job: dict,
    profile: dict,
) -> tuple[dict, list[str], float]:
    from backend.schemas.tailoring import CoverLetterSection
    
    matched_skills, _ = find_matching_skills(
        resume.get("skills", []),
        job.description,
        job.skills_required or [],
    )
    
    intro_content, intro_prompt = generate_cover_letter_intro(job, profile)
    intro = CoverLetterSection(content=intro_content, prompt_used=intro_prompt)
    
    body_sections_data = generate_cover_letter_body(job, resume, matched_skills)
    body = [
        CoverLetterSection(content=s["content"], prompt_used=s["prompt_used"])
        for s in body_sections_data
    ]
    
    closing_content, closing_prompt = generate_cover_letter_closing(job, job.company)
    closing = CoverLetterSection(content=closing_content, prompt_used=closing_prompt)
    
    full_parts = [intro.content]
    for section in body:
        full_parts.append(section.content)
    full_parts.append(closing.content)
    full_text = "\n\n".join(full_parts)
    
    missing = []
    job_keywords = extract_keywords(job.description)
    if len(matched_skills) < len(job_keywords) * 0.3:
        missing.append("Limited direct experience with some listed requirements")
    
    confidence = min(len(matched_skills) / max(len(job_keywords), 1) + 0.4, 0.95)
    
    return {
        "intro": intro,
        "body": body,
        "closing": closing,
        "full_text": full_text,
        "missing_qualifications": missing,
        "confidence": confidence,
    }, missing, confidence


class TailoringService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_data(self, user_id: uuid.UUID) -> tuple[dict, dict, dict | None]:
        profile = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = profile.scalar_one_or_none()
        
        if profile:
            profile_data = {
                "headline": profile.headline,
                "target_roles": profile.target_roles or [],
                "seniority": profile.seniority,
            }
        else:
            profile_data = {}
        
        return {}, profile_data, None
    
    async def get_job(self, job_id: uuid.UUID) -> dict | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "skills_required": job.skills_required or [],
            "location": job.location,
            "remote_type": job.remote_type,
        }
    
    async def get_resume(self, resume_id: uuid.UUID) -> dict | None:
        result = await self.session.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            return None
        
        return resume.parsed_json
    
    async def get_primary_resume(self, user_id: uuid.UUID) -> dict | None:
        result = await self.session.execute(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.is_primary == True,
            ).order_by(Resume.created_at.desc())
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            result = await self.session.execute(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
            )
            resume = result.scalar_one_or_none()
        
        if not resume:
            return None
        
        return resume.parsed_json
    
    async def tailor_resume(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        resume_id: uuid.UUID | None = None,
    ) -> dict | None:
        job_data = await self.get_job(job_id)
        if not job_data:
            return None
        
        if resume_id:
            resume_data = await self.get_resume(resume_id)
        else:
            resume_data = await self.get_primary_resume(user_id)
        
        if not resume_data:
            return None
        
        _, profile_data, _ = await self.get_user_data(user_id)
        
        job_obj = type('Job', (), job_data)()
        
        tailored_bullets, missing, confidence = generate_tailored_resume_bullets(
            resume_data, job_obj
        )
        
        matched_skills, _ = find_matching_skills(
            resume_data.get("skills", []),
            job_data["description"],
            job_data["skills_required"],
        )
        
        summary = generate_summary_suggestion(
            resume_data.get("summary"),
            job_data["title"],
            job_data["company"],
            matched_skills,
        )
        
        return {
            "job_id": job_id,
            "resume_id": resume_id,
            "tailored_bullets": tailored_bullets,
            "summary_suggestion": summary,
            "missing_qualifications": missing,
            "confidence": confidence,
        }
    
    async def generate_cover_letter_for_job(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        resume_id: uuid.UUID | None = None,
    ) -> dict | None:
        job_data = await self.get_job(job_id)
        if not job_data:
            return None
        
        if resume_id:
            resume_data = await self.get_resume(resume_id)
        else:
            resume_data = await self.get_primary_resume(user_id)
        
        if not resume_data:
            return None
        
        _, profile_data, _ = await self.get_user_data(user_id)
        
        job_obj = type('Job', (), job_data)()
        
        result, missing, confidence = generate_cover_letter(
            resume_data, job_obj, profile_data
        )
        result["job_id"] = job_id
        
        return result
    
    async def tailor_and_generate_cover_letter(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        resume_id: uuid.UUID | None = None,
    ) -> dict | None:
        resume_tailoring = await self.tailor_resume(user_id, job_id, resume_id)
        if not resume_tailoring:
            return None
        
        cover_letter = await self.generate_cover_letter_for_job(user_id, job_id, resume_id)
        
        return {
            "resume": resume_tailoring,
            "cover_letter": cover_letter,
        }
