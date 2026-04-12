---
title: Job Ingestion
type: feature
created: 2026-04-12
status: done
context: []
baseline_commit: 1bcef92
---

## Intent

**Problem:** JobCodex needs to discover and store job listings from external sources to match against user profiles.

**Approach:** Build a source registry, implement connectors for Greenhouse/Lever/Ashby APIs, normalize job data, and handle deduplication.

## Boundaries & Constraints

**Always:**
- Use public APIs only (no scraping)
- Respect rate limits per source
- Store raw payload for debugging
- Normalize all jobs to internal schema

**Never:**
- No scraping of sites with anti-bot protection
- No storage of credentials in code
- No auto-submission

## Code Map

- `backend/services/ingestion/` -- Source connectors
- `backend/services/ingestion/base.py` -- Base connector class
- `backend/services/ingestion/greenhouse.py` -- Greenhouse connector
- `backend/services/ingestion/lever.py` -- Lever connector
- `backend/services/ingestion/ashby.py` -- Ashby connector
- `backend/services/ingestion/registry.py` -- Source registry
- `backend/api/sources.py` -- Source management endpoints

## Tasks & Acceptance

**Execution:**
- [x] `backend/services/ingestion/base.py` -- Base connector with fetch/normalize
- [x] `backend/services/ingestion/greenhouse.py` -- Greenhouse public API
- [x] `backend/services/ingestion/lever.py` -- Lever public API
- [x] `backend/services/ingestion/ashby.py` -- Ashby public API
- [x] `backend/services/ingestion/registry.py` -- Source registry with health tracking
- [x] `backend/api/sources.py` -- Source CRUD and trigger endpoints
- [x] `tests/test_ingestion.py` -- Connector tests

**Acceptance Criteria:**
- Given Greenhouse board token, when fetching jobs, then normalized jobs stored
- Given duplicate job, when ingesting, then existing job updated not duplicated
- Given inactive source, when fetching, then error returned
- Given rate limit hit, when fetching, then retry after backoff

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**Source Pattern:**
```python
class BaseConnector:
    async def fetch(self) -> list[dict]: ...
    def normalize(self, raw: dict) -> Job: ...
    def get_source_name(self) -> str: ...
```

**Normalization:** All sources map to internal Job schema with:
- company, title, location, remote_type
- salary_min/max, employment_type, seniority
- description, skills_required, benefits
- application_url, source_url, posted_at

## Verification

**Commands:**
- `pytest tests/test_ingestion.py -v` -- expected: all tests pass

## Suggested Review Order

**Base Connector**

- Abstract base with normalization logic
  [`services/ingestion/base.py:1`](backend/services/ingestion/base.py#L1)

**Source Connectors**

- Greenhouse job board API
  [`services/ingestion/greenhouse.py:1`](backend/services/ingestion/greenhouse.py#L1)

- Lever postings API
  [`services/ingestion/lever.py:1`](backend/services/ingestion/lever.py#L1)

- Ashby job API with GraphQL
  [`services/ingestion/ashby.py:1`](backend/services/ingestion/ashby.py#L1)

**Registry**

- Source management and ingestion orchestration
  [`services/ingestion/registry.py:1`](backend/services/ingestion/registry.py#L1)

**API Routes**

- Source CRUD and ingest trigger
  [`api/sources.py:1`](backend/api/sources.py#L1)

**Tests**

- Connector and API tests
  [`test_ingestion.py:1`](tests/test_ingestion.py#L1)
