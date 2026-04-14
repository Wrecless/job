from urllib.parse import urlparse

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Application, ApplicationArtifact, Job, JobAlert, JobSource, MatchScore, Task


PLACEHOLDER_HOSTS = {"example.com", "localhost", "127.0.0.1"}
DEMO_SOURCE_NAMES = {
    "ManualSource",
    "OrmSource",
    "LiveSampleSource",
    "ManualLiveSource",
    "ExcludedRSS",
}

STARTER_SOURCES = [
    {"name": "GitLab", "source_type": "greenhouse", "base_url": "https://boards.greenhouse.io/gitlab"},
    {"name": "Canonical", "source_type": "greenhouse", "base_url": "https://boards.greenhouse.io/canonical"},
    {"name": "LaunchDarkly", "source_type": "greenhouse", "base_url": "https://boards.greenhouse.io/launchdarkly"},
    {"name": "CircleCI", "source_type": "greenhouse", "base_url": "https://boards.greenhouse.io/circleci"},
]


def _is_placeholder_source(source: JobSource) -> bool:
    host = urlparse(source.base_url).hostname or ""
    return source.name in DEMO_SOURCE_NAMES or host in PLACEHOLDER_HOSTS


async def seed_starter_sources(session: AsyncSession) -> int:
    result = await session.execute(select(JobSource))
    sources = list(result.scalars().all())

    if sources and any(not _is_placeholder_source(source) for source in sources):
        return 0

    if sources:
        await session.execute(delete(JobAlert))
        await session.execute(delete(MatchScore))
        await session.execute(delete(Task))
        await session.execute(delete(ApplicationArtifact))
        await session.execute(delete(Application))
        await session.execute(delete(Job))

    if sources:
        await session.execute(delete(JobSource))

    for starter in STARTER_SOURCES:
        session.add(
            JobSource(
                id=uuid.uuid4(),
                name=starter["name"],
                source_type=starter["source_type"],
                base_url=starter["base_url"],
                is_active=True,
            )
        )

    await session.commit()
    return len(STARTER_SOURCES)
