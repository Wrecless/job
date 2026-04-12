---
title: Application Tracking
type: feature
created: 2026-04-12
status: done
context: []
baseline_commit: 0dc8c93
---

## Intent

**Problem:** Users need to track the status of job applications from submission through outcome, including follow-up reminders.

**Approach:** Build an application tracking system with status workflow, follow-up task scheduling, and status history.

## Boundaries & Constraints

**Always:**
- Track all status transitions with timestamps
- Support follow-up reminders
- User controls all status changes
- Audit log all application actions

**Never:**
- No automatic status changes based on external data
- No submission without user approval

## Code Map

- `backend/api/applications.py` -- Application endpoints
- `backend/schemas/application.py` -- Application models

## Tasks & Acceptance

**Execution:**
- [x] `backend/schemas/application.py` -- Application models
- [x] `backend/api/applications.py` -- Application CRUD
- [x] `tests/test_applications.py` -- Application tests

**Acceptance Criteria:**
- Given job and resume, when creating application, then application with found status created
- Given application, when updating status, then status history recorded
- Given application, when adding follow-up, then task created with due date
- Given application pipeline, when listing, then jobs grouped by status

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**Status Flow:**
- found → saved → tailoring → ready → submitted → interviewing → offer/rejected → closed

**Task Types:**
- follow_up: reminder to check on application
- interview_prep: prepare for interview

## Verification

**Commands:**
- `pytest tests/test_applications.py -v` -- expected: all tests pass

## Suggested Review Order

**Schemas**

- Application and task models
  [`schemas/application.py:1`](backend/schemas/application.py#L1)

**API Routes**

- Application CRUD and pipeline
  [`api/applications.py:1`](backend/api/applications.py#L1)

**Tests**

- Application tracking tests
  [`test_applications.py:1`](tests/test_applications.py#L1)
