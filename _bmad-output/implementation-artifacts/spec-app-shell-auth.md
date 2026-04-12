---
title: App Shell and Auth
type: feature
created: 2026-04-12
status: done
context: []
baseline_commit: 340ebd6
---

## Intent

**Problem:** JobCodex has no application structure or authentication system.

**Approach:** Create FastAPI application shell with JWT auth, session management, and basic user registration/login flows.

## Boundaries & Constraints

**Always:**
- FastAPI framework
- JWT access + refresh tokens
- Password hashing with bcrypt
- Async database operations
- Environment-based config

**Never:**
- No session cookies for auth (use JWT only)
- No plaintext password storage
- No business logic in routes

## Code Map

- `backend/main.py` -- FastAPI app factory
- `backend/config.py` -- Environment config
- `backend/api/` -- API routes
- `backend/api/auth.py` -- Auth endpoints
- `backend/services/` -- Business logic
- `backend/services/auth.py` -- JWT and password service

## Tasks & Acceptance

**Execution:**
- [x] `backend/config.py` -- Pydantic settings from env vars -- Config management
- [x] `backend/main.py` -- FastAPI app with CORS, routes -- App bootstrap
- [x] `backend/services/auth.py` -- JWT tokens, password hashing -- Auth service
- [x] `backend/api/auth.py` -- /register, /login, /refresh -- Auth routes
- [x] `backend/dependencies.py` -- get_current_user dependency -- Auth middleware
- [x] `tests/test_auth.py` -- Auth endpoint tests -- Validate flows

**Acceptance Criteria:**
- Given valid credentials, when registering, then user is created and tokens returned
- Given valid credentials, when logging in, then JWT access + refresh tokens returned
- Given expired access token, when using refresh token, then new tokens returned
- Given invalid credentials, when logging in, then 401 returned
- Given missing auth header, when accessing protected route, then 401 returned

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**JWT Structure:**
- Access token: 15 min expiry, user_id claim
- Refresh token: 7 day expiry, user_id claim
- Both signed with HS256

**Password:** bcrypt with 12 rounds

**Config:** Use Pydantic Settings with .env support

## Verification

**Commands:**
- `pytest tests/test_auth.py -v` -- expected: all tests pass
- `python -c "from backend.main import app; print('App loads OK')"` -- expected: silent success

## Suggested Review Order

**Core App**

- FastAPI app factory with lifespan, CORS, routes
  [`main.py:1`](backend/main.py#L1)

**Config**

- Pydantic settings from environment
  [`config.py:1`](backend/config.py#L1)

**Auth Service**

- JWT token creation and verification
  [`services/auth.py:1`](backend/services/auth.py#L1)

**Auth Routes**

- Register, login, refresh, and me endpoints
  [`api/auth.py:1`](backend/api/auth.py#L1)

**Middleware**

- Current user dependency injection
  [`dependencies.py:1`](backend/dependencies.py#L1)

**Tests**

- Auth flow tests
  [`test_auth.py:1`](tests/test_auth.py#L1)
