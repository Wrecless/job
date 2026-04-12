---
title: Job Matching and Ranking
type: feature
created: 2026-04-12
status: done
context: []
baseline_commit: c0e0d84
---

## Intent

**Problem:** Users have profiles and jobs exist, but there's no way to score how well jobs match their preferences and resume.

**Approach:** Build a matching service that scores jobs against user profiles using weighted criteria and returns explainable rankings.

## Boundaries & Constraints

**Always:**
- Transparent scoring with factor breakdown
- Plain-English explanations
- Scores stored for caching

**Never:**
- No hidden black-box scoring
- No fabricating match reasons

## Code Map

- `backend/services/matching.py` -- Matching logic
- `backend/api/jobs.py` -- Job listing with matching
- `backend/schemas/matching.py` -- Match response models

## Tasks & Acceptance

**Execution:**
- [x] `backend/schemas/matching.py` -- MatchScore Pydantic models
- [x] `backend/services/matching.py` -- Scoring algorithm
- [x] `backend/api/jobs.py` -- Job listing with scores
- [x] `tests/test_matching.py` -- Matching tests

**Acceptance Criteria:**
- Given user profile and job, when scoring, then score with breakdown returned
- Given multiple jobs, when listing, then jobs sorted by score DESC
- Given new resume, when rescoring, then all scores updated
- Given filter params, when listing, then jobs filtered and sorted

## Spec Change Log

<!-- Empty until first bad_spec loopback. -->

## Design Notes

**Scoring Factors (weighted):**
- title_similarity: 25%
- skill_match: 30%
- seniority_fit: 15%
- location_fit: 10%
- salary_fit: 10%
- remote_fit: 10%

**Score Range:** 0-100

## Verification

**Commands:**
- `pytest tests/test_matching.py -v` -- expected: all tests pass

## Suggested Review Order

**Schemas**

- Match score response models
  [`schemas/matching.py:1`](backend/schemas/matching.py#L1)

**Matching Service**

- Scoring algorithms and factor calculations
  [`services/matching.py:1`](backend/services/matching.py#L1)

**API Routes**

- Job listing with scores and filters
  [`api/jobs.py:1`](backend/api/jobs.py#L1)

**Tests**

- Matching algorithm unit tests
  [`test_matching.py:1`](tests/test_matching.py#L1)
