---
title: Database Schema
type: chore
created: 2026-04-12
status: done
context: []
baseline_commit: main
---

## Intent

**Problem:** JobCodex has no persistent data layer. The product cannot track users, jobs, matches, or applications without a schema.

**Approach:** Create SQLAlchemy models with Alembic migrations for all core entities. Use SQLite for development, PostgreSQL-ready structure.

## Boundaries & Constraints

**Always:**
- Use SQLAlchemy 2.0 async patterns
- All tables have UUID primary keys
- All tables have created_at/updated_at timestamps
- Soft deletes where appropriate (User)
- Unique constraints prevent duplicate data

**Ask First:**
- Array field implementation (TEXT[] vs JSONB vs separate tables)

**Never:**
- No auto-increment integer PKs
- No business logic in models (pure data only)
- No Flask-specific patterns (stay framework-agnostic)

## Code Map

- `backend/db/models/` -- SQLAlchemy model classes
- `backend/db/migrations/` -- Alembic migration scripts
- `backend/db/base.py` -- SQLAlchemy Base and engine setup
- `backend/alembic.ini` -- Alembic configuration
- `pyproject.toml` -- Project dependencies

## Tasks & Acceptance

**Execution:**
- [x] `backend/db/base.py` -- Create Base class and async engine setup -- Foundation for all models
- [x] `backend/db/models/user.py` -- User model with soft delete -- Core auth entity
- [x] `backend/db/models/profile.py` -- Profile model with JSONB arrays -- User preferences
- [x] `backend/db/models/resume.py` -- Resume model with parsed JSONB -- Document storage
- [x] `backend/db/models/job_source.py` -- JobSource model -- Source registry
- [x] `backend/db/models/job.py` -- Job model with indexes -- Job postings
- [x] `backend/db/models/match.py` -- MatchScore model -- User-job scoring
- [x] `backend/db/models/application.py` -- Application model -- Application lifecycle
- [x] `backend/db/models/artifact.py` -- ApplicationArtifact model -- Tailored documents
- [x] `backend/db/models/task.py` -- Task model -- Follow-up tracking
- [x] `backend/db/models/audit.py` -- AuditLog model -- Audit trail
- [x] `backend/db/models/__init__.py` -- Export all models -- Clean imports
- [x] `alembic.ini` -- Configure Alembic -- Migration tool
- [x] `backend/db/migrations/env.py` -- Alembic env setup -- Migration runner
- [x] `backend/db/migrations/001_initial_schema.py` -- Initial migration -- All tables
- [x] `tests/test_models.py` -- Basic model tests -- Validate relationships
- [x] `pyproject.toml` -- Add dependencies -- sqlalchemy[asyncio], alembic, aiosqlite, pytest-asyncio

**Acceptance Criteria:**
- Given no existing database, when running `alembic upgrade head`, then all tables are created
- Given two jobs with same source_job_id, when inserting the second, then unique constraint error
- Given a deleted user, when querying users, then soft-deleted row is excluded by default
- Given job search, when filtering by score DESC, then index is used efficiently

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**UUID Strategy:** Use `uuid.uuid4()` for all PKs. This avoids enumeration attacks and works well with distributed systems.

**Array Fields:** Use `JSONB` (PostgreSQL) with JSON array storage. For SQLite, serialize to JSON string. Alembic will handle platform-specific migration.

**Async Pattern:**
```python
# base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = create_async_engine("sqlite+aiosqlite:///./jobcodex.db")
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**Migration Structure:**
```bash
backend/
  db/
    models/
      __init__.py
      user.py
      profile.py
      ...
    migrations/
      versions/
        001_initial_schema.py
      env.py
      script.py.mako
  alembic.ini
```

## Verification

**Commands:**
- `alembic upgrade head` -- expected: creates all tables, no errors
- `alembic current` -- expected: shows current revision
- `pytest tests/test_models.py -v` -- expected: all tests pass
- `python -c "from backend.db.models import *; print('Models import OK')"` -- expected: silent success

## Suggested Review Order

**Models**

- User model with soft delete pattern
  [`user.py:1`](backend/db/models/user.py#L1)

- Profile with JSON array fields for preferences
  [`profile.py:1`](backend/db/models/profile.py#L1)

- Job model with all indexes and constraints
  [`job.py:1`](backend/db/models/job.py#L1)

- MatchScore with score breakdown JSONB
  [`match.py:1`](backend/db/models/match.py#L1)

- Application with status workflow
  [`application.py:1`](backend/db/models/application.py#L1)

**Migration**

- Full schema migration with all tables and indexes
  [`001_initial_schema.py:1`](backend/db/migrations/versions/001_initial_schema.py#L1)

**Tests**

- Model tests covering relationships and constraints
  [`test_models.py:1`](tests/test_models.py#L1)

**Config**

- SQLAlchemy async engine setup
  [`base.py:1`](backend/db/base.py#L1)

- Project dependencies
  [`pyproject.toml:1`](pyproject.toml#L1)
