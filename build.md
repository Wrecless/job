# JobCodex Build Plan

This document is the step-by-step plan to build the MVP v1 of JobCodex in **Mode A: copilot mode**.

The MVP should help a user:

- find relevant jobs
- understand why each job matches
- tailor resume and cover letter drafts
- track applications and follow-ups
- prepare everything for manual submission or source-approved submission later

It should **not** start with auto-apply. That is a later phase, if ever, because the first version should maximize usefulness while minimizing platform and compliance risk.

## 0. MVP Definition

### In scope

- User profile
- Resume upload and parsing
- Job ingestion from a small set of allowed sources
- Job matching and ranking
- Tailored resume bullet suggestions
- Tailored cover letter draft generation
- Application queue and status tracking
- Follow-up reminders
- Manual export or copy-ready submission packets

### Out of scope

- Blind auto-apply
- Scraping sites that prohibit automation
- Browser bots that submit without review
- Complex referral automation
- Interview prep bots
- Salary negotiation automation

### Success criteria

The MVP is useful if a user can:

1. add a resume and preferences
2. see a ranked list of jobs
3. get a clear explanation for each match
4. generate a tailored application packet in minutes
5. track the application through follow-up

## 1. Choose the First Product Shape

Build a **job copilot** rather than a submission bot.

The core workflow is:

1. ingest job data
2. score it against the user profile
3. generate tailored application material
4. let the user review and submit manually
5. track outcomes and reminders

This is the right first version because:

- it is immediately useful
- it avoids the hardest compliance issues
- it gives you the same data model you will need later if you add assisted submission
- it is much easier to debug than browser automation

## 2. Pick Safe Initial Data Sources

Start with sources that already expose structured job data or published career endpoints.

### Recommended initial source strategy

- company career pages powered by ATS systems
- public job board endpoints from ATS vendors
- user-saved job URLs
- job alert emails

### Source types to prioritize first

1. **Greenhouse job boards**
   - Greenhouse exposes a public Job Board API for published jobs.
   - Their docs say public GET endpoints do not require authentication.
   - This is a strong first integration target for ingestion.

2. **Lever postings**
   - Lever provides a public postings API and hosted job sites.
   - This is another strong structured source for job ingestion.

3. **Ashby job postings**
   - Ashby exposes a public job postings API for published roles.
   - It can include compensation when available.

### Why this matters

Starting with ATS-backed sources gives you:

- structured fields
- predictable job metadata
- less parsing work
- fewer compliance surprises
- a better foundation for matching

### Source research notes

- Greenhouse Job Board API: public job data and application submission endpoints are documented by Greenhouse.
- Lever Postings API: public postings data and a job site model are documented by Lever.
- Ashby Job Postings API: public job posting data is documented by Ashby.

## 3. Define the Core User Flow

The first release should follow one simple path:

1. user creates account
2. user uploads resume
3. user fills in target roles and constraints
4. system ingests jobs
5. system ranks jobs
6. user reviews matches
7. system generates tailored drafts
8. user exports or submits manually
9. system tracks status and reminders

Do not add extra product loops until this one is solid.

## 4. Build the Data Model First

Before integrating job sources or AI, create the canonical internal schema.

### Core entities

- `User`
- `Profile`
- `Resume`
- `Job`
- `JobSource`
- `MatchScore`
- `Application`
- `ApplicationArtifact`
- `Task`
- `AuditLog`

### Fields to model early

- job title
- company
- location
- remote status
- salary range
- description
- application URL
- source type
- source URL
- posted date
- match score
- score breakdown
- tailoring artifacts
- application status
- follow-up dates

### Why this comes first

If the schema is stable, every later piece becomes easier:

- ingestion can normalize into one shape
- matching can score one shape
- AI can tailor from one shape
- tracking can sit on one shape

## 5. Build Profile and Resume Intake

This is the first user-facing feature after auth.

### Step 5.1: Upload resume

- Accept PDF and DOCX
- Store the original file
- Generate a parsed text version
- Generate a structured resume JSON

### Step 5.2: Parse into structured sections

- contact details
- summary
- work history
- education
- skills
- certifications
- projects
- links

### Step 5.3: Add manual correction UI

Parsing will never be perfect.

Let the user fix:

- job titles
- dates
- employer names
- bullet points
- skills
- education fields

### Step 5.4: Create preference form

Capture:

- target roles
- target seniority
- location preferences
- remote/hybrid/on-site preference
- salary floor
- sponsorship requirement
- industries to avoid
- company size preference
- keywords to include or exclude

### Output of this phase

The system should be able to answer:

- who the user is
- what they want
- what experience they have

## 6. Build Job Ingestion

Ingestion should be source-specific, normalized, and retryable.

### Step 6.1: Create a source registry

For each source, record:

- source name
- access method
- refresh frequency
- rate limits
- allowed fields
- parsing strategy
- terms/compliance notes
- failure handling

### Step 6.2: Implement the first connectors

Recommended order:

1. Greenhouse public job boards
2. Lever postings
3. Ashby job postings
4. user-pasted job URLs

### Step 6.3: Normalize all jobs

Convert source-specific payloads into one internal job object.

### Step 6.4: Deduplicate jobs

Use a combination of:

- source job ID
- canonical URL
- company
- title
- location
- description hash

### Step 6.5: Store raw and normalized data

Keep both:

- raw source payload for debugging
- normalized record for the product

### Step 6.6: Add source health checks

Track:

- last successful fetch
- number of jobs fetched
- parsing failures
- response latency
- duplicate rate

## 7. Build Matching and Ranking

The matching system is the heart of the copilot.

### Step 7.1: Define scoring factors

Start with transparent heuristics:

- title similarity
- skill overlap
- seniority fit
- remote/location fit
- salary fit
- sponsorship fit
- recency
- company preference fit
- application friction

### Step 7.2: Produce a score breakdown

Every job should have:

- total score
- factor scores
- one plain-English explanation

### Step 7.3: Add filters

Allow the user to hide jobs that fail:

- salary floor
- location rules
- sponsorship requirement
- industry exclusions
- seniority mismatch

### Step 7.4: Add learning later

After the MVP works, use behavior signals:

- saved jobs
- skipped jobs
- applied jobs
- response outcomes

For v1, keep it simple and explainable.

## 8. Build the Tailoring Engine

This is where the copilot becomes valuable.

### Step 8.1: Create a source-grounded generation flow

The AI should only tailor from:

- the user profile
- the parsed resume
- the job description
- explicit user edits

### Step 8.2: Generate specific artifacts

Start with:

- resume bullet suggestions
- summary rewrite
- cover letter draft
- short answer draft

### Step 8.3: Add factual guardrails

Never allow the model to:

- invent employment
- invent metrics
- invent degrees or certifications
- invent technologies the user did not list
- overstate seniority or scope

### Step 8.4: Show diffs and rationale

For every generated artifact, show:

- what changed
- why it changed
- which resume/job facts it came from

### Step 8.5: Let the user approve edits

The user should be able to:

- accept
- edit
- reject
- regenerate

This feedback loop matters more than fancy prompt engineering.

## 9. Build the Application Workspace

This is the screen where the user actually gets value.

### Core views

- ranked jobs feed
- job detail view
- tailoring workspace
- application tracker
- follow-up queue

### Job detail view should show

- match score
- fit explanation
- missing requirements
- tailored resume preview
- cover letter draft
- application checklist

### Application tracker should show

- saved
- drafting
- ready to submit
- submitted
- followed up
- interviewing
- closed

### Follow-up queue should show

- jobs that need a follow-up
- due dates
- draft follow-up message
- last activity

## 10. Build Manual Submission Support

For MVP v1, the submission step should be manual or user-driven.

### What to support

- copy-ready application packets
- downloaded PDF resume variants
- copyable cover letters
- filled form data the user can paste
- a checklist of questions to answer

### What not to do yet

- blind browser submission
- hidden click automation on sites with unclear terms
- token storage for automated access unless explicitly necessary and approved

### Why manual submission is enough

The product’s value is in:

- discovering
- filtering
- tailoring
- organizing

Submission automation can be added later if a source allows it and the product is stable.

## 11. Build Notifications and Reminders

This feature keeps the pipeline alive.

### Notifications to implement

- new high-match jobs
- pending review items
- follow-up reminders
- application status changes
- source ingestion failures

### Channels

- in-app notifications first
- email second
- push notifications later

### Reminder logic

- no reminder spam
- respect user timezone
- configurable reminder windows
- snooze support

## 12. Add Auditability and Safety Controls

This is non-optional.

### Every meaningful action should be logged

- profile edits
- resume uploads
- job ingestions
- scoring runs
- document generation
- manual approval
- exports
- application submissions

### Safety controls

- minimum score threshold before showing a job as recommended
- manual review for any sensitive answer
- duplicate application detection
- daily processing limits
- kill switch for broken ingestion

### Privacy controls

- delete account
- delete resumes
- export profile data
- clear generated documents
- clear application history

## 13. Choose the Minimal Tech Stack

Keep the first implementation boring.

### Suggested stack

- Frontend: Next.js or React
- Backend: Node.js or Python
- Database: Postgres
- Queue: Redis-based queue or managed queue
- Storage: S3-compatible object storage
- Search: Postgres full-text search initially
- Auth: email/password plus optional OAuth
- AI: hosted LLM API with strict prompts and templates

### Why this stack

- fast to build
- easy to maintain
- good for structured data
- enough for the MVP scale

## 14. Suggested Implementation Sequence

This is the actual step-by-step order I would follow.

### Phase 1: Foundation

1. create the repo and base app shell
2. add auth
3. create the database schema
4. add logging and error handling
5. add a simple dashboard layout

### Phase 2: Profile and resume

6. add resume upload
7. parse resume text
8. build structured resume editor
9. add user preferences form

### Phase 3: Jobs

10. build the job model
11. create source registry
12. implement Greenhouse ingestion
13. implement Lever ingestion
14. implement Ashby ingestion
15. add deduplication and source health metrics

### Phase 4: Matching

16. implement scoring heuristics
17. show score breakdowns
18. add filters and exclusions
19. create ranked feed and job detail pages

### Phase 5: Tailoring

20. implement prompt/template pipeline
21. generate resume bullet suggestions
22. generate cover letter drafts
23. generate short-answer drafts
24. add diff and approval UI

### Phase 6: Tracking

25. add application records
26. add workflow states
27. add follow-up queue
28. add reminder engine

### Phase 7: Polish and hardening

29. add audit trails
30. add privacy/export/delete controls
31. add tests
32. fix edge cases
33. run a closed pilot on your own applications

## 15. Testing Plan

### Unit tests

- resume parsing
- job normalization
- deduplication
- scoring
- prompt rendering
- state transitions

### Integration tests

- source fetch and normalize
- profile to match score
- job to tailored draft
- reminder scheduling

### Manual QA

- resume quality
- job ranking quality
- factual accuracy of generated text
- copy/export workflows
- mobile usability

### Failure tests

- source timeout
- malformed job payload
- duplicate job entries
- partial parsing
- generation failure
- email delivery failure

## 16. Key Research Findings That Shape the Build

These current source capabilities are why the MVP should start with copilot mode:

- Greenhouse provides a public Job Board API and documented application submission endpoints for published jobs.
- Lever provides a postings API and publicly viewable job sites.
- Ashby provides a public job postings API and can include compensation data.
- Indeed’s guidelines say not to use third-party bots or automated tools to apply and say web forms on its platform are not allowed for automated use.
- LinkedIn explicitly prohibits third-party software, crawlers, bots, browser plug-ins, and browser extensions that automate activity on its site.

The practical conclusion is:

- use structured job sources first
- keep submission manual in v1
- design the product around review, not hidden automation

## 17. Risks and How to Avoid Them

### Risk: bad matching

Mitigation:

- keep scoring explainable
- allow user filters
- let users dismiss irrelevant jobs

### Risk: hallucinated tailoring

Mitigation:

- constrain generation to source facts
- require review
- show diffs

### Risk: brittle ingestion

Mitigation:

- prefer public ATS sources
- store raw payloads
- add source health monitoring

### Risk: compliance problems

Mitigation:

- keep auto-apply out of MVP
- document source rules
- add per-source allow/deny logic

### Risk: too much scope

Mitigation:

- ship one end-to-end flow first
- do not build interview prep, networking automation, or salary negotiation until the core loop works

## 18. What “Done” Looks Like

The MVP is done when you can reliably do this:

1. upload one resume
2. define one job target profile
3. ingest jobs from a few allowed sources
4. rank them clearly
5. generate a tailored application packet
6. track the application lifecycle
7. remind the user to follow up

If you can do that, you have a useful product.

## 19. Next Build Decision

If you want the fastest path to a working prototype, build in this order:

1. schema
2. auth
3. resume intake
4. one job source
5. matching
6. tailoring
7. tracker
8. reminders

Everything else is secondary until this loop works.
