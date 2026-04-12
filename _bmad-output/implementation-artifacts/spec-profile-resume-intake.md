---
title: Profile and Resume Intake
type: feature
created: 2026-04-12
status: done
context: []
baseline_commit: 1ae14b3
---

## Intent

**Problem:** Users need to upload resumes and define preferences so JobCodex can match and tailor applications.

**Approach:** Build resume upload/parsing, structured profile editor, and preferences form with AI-assisted parsing.

## Boundaries & Constraints

**Always:**
- Accept PDF and DOCX for resume uploads
- Store original file and parsed JSON
- Async file handling
- User owns and controls their data

**Never:**
- No AI fabrication of resume content
- No storage of raw credentials
- No automatic submission

## Code Map

- `backend/api/resume.py` -- Resume upload and CRUD
- `backend/api/profile.py` -- Profile endpoints
- `backend/services/parser.py` -- Resume parsing logic
- `backend/schemas/` -- Pydantic request/response models

## Tasks & Acceptance

**Execution:**
- [x] `backend/schemas/resume.py` -- Resume Pydantic models
- [x] `backend/schemas/profile.py` -- Profile Pydantic models
- [x] `backend/api/resume.py` -- Upload, list, get, delete resume
- [x] `backend/api/profile.py` -- Get/update profile
- [x] `backend/services/parser.py` -- Parse PDF/DOCX to structured JSON
- [x] `tests/test_resume.py` -- Resume API tests
- [x] `tests/test_profile.py` -- Profile API tests

**Acceptance Criteria:**
- Given PDF file, when uploading, then file stored and parsed JSON returned
- Given DOCX file, when uploading, then file stored and parsed JSON returned
- Given invalid file type, when uploading, then 400 error returned
- Given profile data, when updating, then profile saved and returned
- Given existing profile, when getting, then full profile with defaults returned

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**Parser Strategy:** Use python-docx for DOCX, PyPDF2 for PDF text extraction. Store raw text for AI to parse into structured format.

**Profile Defaults:**
- target_roles: []
- locations: []
- remote_preference: null
- seniority: null
- salary_floor: null
- industries_to_avoid: []
- sponsorship_needed: false
- keywords_include: []
- keywords_exclude: []

## Verification

**Commands:**
- `pytest tests/test_resume.py tests/test_profile.py -v` -- expected: all tests pass

## Suggested Review Order

**Schemas**

- Resume request/response models
  [`schemas/resume.py:1`](backend/schemas/resume.py#L1)

- Profile request/response models
  [`schemas/profile.py:1`](backend/schemas/profile.py#L1)

**API Routes**

- Resume upload with file parsing
  [`api/resume.py:1`](backend/api/resume.py#L1)

- Profile CRUD operations
  [`api/profile.py:1`](backend/api/profile.py#L1)

**Services**

- Resume parsing logic
  [`services/parser.py:1`](backend/services/parser.py#L1)

**Tests**

- Resume API tests
  [`test_resume.py:1`](tests/test_resume.py#L1)

- Profile API tests
  [`test_profile.py:1`](tests/test_profile.py#L1)
