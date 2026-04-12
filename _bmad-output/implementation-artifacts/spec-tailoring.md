---
title: Tailoring Engine
type: feature
created: 2026-04-12
status: done
context: []
baseline_commit: 4b8afc5
---

## Intent

**Problem:** Users need to customize resume bullets and cover letters for each job application, but doing this manually is time-consuming.

**Approach:** Build a tailoring service that generates tailored resume bullets and cover letters from user profile, resume, and job description using templates + AI hints.

## Boundaries & Constraints

**Always:**
- Tailor from source facts only (resume, profile, job)
- Never fabricate experience or qualifications
- User must review and approve all generated content
- Show diffs and source attribution

**Never:**
- No AI hallucination of metrics or achievements
- No submission without user approval

## Code Map

- `backend/services/tailoring.py` -- Tailoring logic
- `backend/api/tailoring.py` -- Tailoring endpoints
- `backend/schemas/tailoring.py` -- Request/response models

## Tasks & Acceptance

**Execution:**
- [x] `backend/schemas/tailoring.py` -- Tailor request/response models
- [x] `backend/services/tailoring.py` -- Tailoring service
- [x] `backend/api/tailoring.py` -- Tailor endpoints
- [x] `tests/test_tailoring.py` -- Tailoring tests

**Acceptance Criteria:**
- Given job and resume, when tailoring, then resume bullets tailored to job
- Given job and profile, when tailoring, then cover letter draft generated
- Given no relevant experience, when tailoring, then no fabricated content
- Given generated content, when reviewing, then source attribution shown

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**Tailoring Rules:**
- Extract relevant experience from resume
- Map skills to job requirements
- Rewrite bullets to emphasize matching skills
- Generate cover letter with intro, body, closing structure
- Flag missing qualifications instead of fabricating

## Verification

**Commands:**
- `pytest tests/test_tailoring.py -v` -- expected: all tests pass

## Suggested Review Order

**Schemas**

- Tailoring request/response models
  [`schemas/tailoring.py:1`](backend/schemas/tailoring.py#L1)

**Service**

- Tailoring algorithms and content generation
  [`services/tailoring.py:1`](backend/services/tailoring.py#L1)

**API Routes**

- Tailoring endpoints
  [`api/tailoring.py:1`](backend/api/tailoring.py#L1)

**Tests**

- Tailoring unit tests
  [`test_tailoring.py:1`](tests/test_tailoring.py#L1)
