import uuid
from datetime import datetime, timezone
from typing import Type

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Job, JobSource
from backend.services.ingestion.base import BaseConnector
from backend.services.ingestion.greenhouse import GreenhouseConnector
from backend.services.ingestion.lever import LeverConnector
from backend.services.ingestion.ashby import AshbyConnector


CONNECTOR_MAP: dict[str, Type[BaseConnector]] = {
    "greenhouse": GreenhouseConnector,
    "lever": LeverConnector,
    "ashby": AshbyConnector,
}


class SourceRegistry:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_source(self, source_name: str) -> JobSource | None:
        result = await self.session.execute(
            select(JobSource).where(JobSource.name == source_name)
        )
        return result.scalar_one_or_none()
    
    async def create_source(
        self,
        name: str,
        source_type: str,
        base_url: str,
        api_key: str | None = None,
    ) -> JobSource:
        source = JobSource(
            id=uuid.uuid4(),
            name=name,
            source_type=source_type,
            base_url=base_url,
        )
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source
    
    async def get_or_create_source(
        self,
        name: str,
        source_type: str,
        base_url: str,
    ) -> tuple[JobSource, bool]:
        existing = await self.get_source(name)
        if existing:
            return existing, False
        
        source = await self.create_source(name, source_type, base_url)
        return source, True
    
    async def ingest_from_source(
        self,
        source: JobSource,
        api_key: str | None = None,
    ) -> tuple[int, int]:
        connector_class = CONNECTOR_MAP.get(source.source_type)
        if not connector_class:
            raise ValueError(f"Unknown source type: {source.source_type}")
        
        connector = connector_class(source.base_url, api_key)
        
        raw_jobs = await connector.fetch_raw()
        
        jobs_created = 0
        jobs_updated = 0
        
        for raw_job in raw_jobs:
            normalized = connector.normalize(raw_job)
            
            existing = await self.session.execute(
                select(Job).where(
                    Job.source_id == source.id,
                    Job.source_job_id == normalized["source_job_id"],
                )
            )
            existing_job = existing.scalar_one_or_none()
            
            if existing_job:
                for key, value in normalized.items():
                    if key not in ("id", "source_id", "canonical_hash"):
                        setattr(existing_job, key, value)
                existing_job.updated_at = datetime.now(timezone.utc)
                jobs_updated += 1
            else:
                job = Job(
                    id=uuid.uuid4(),
                    source_id=source.id,
                    **normalized,
                )
                self.session.add(job)
                jobs_created += 1
        
        source.last_fetch_at = datetime.now(timezone.utc)
        source.last_success_at = datetime.now(timezone.utc)
        source.error_count = 0
        
        await self.session.commit()
        
        return jobs_created, jobs_updated
    
    async def update_source_health(
        self,
        source: JobSource,
        success: bool,
        error_message: str | None = None,
    ):
        if success:
            source.last_success_at = datetime.now(timezone.utc)
            source.error_count = 0
        else:
            source.error_count += 1
        
        source.last_fetch_at = datetime.now(timezone.utc)
        
        await self.session.commit()
    
    async def list_sources(self, active_only: bool = True) -> list[JobSource]:
        query = select(JobSource)
        if active_only:
            query = query.where(JobSource.is_active == True)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
