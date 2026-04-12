# JobCodex

JobCodex is a personal "job copilot" for job discovery, prioritization, tailoring, tracking, and assisted application submission.

The goal is not to build a blind spam bot. The right product shape is a workflow engine that helps a user move faster while keeping quality, compliance, and control.

## 1. Product Goal

Build a system that:

- Finds relevant jobs from multiple sources
- Scores how well each role matches the user
- Tailors resume and cover letter drafts to the role
- Autofills applications where allowed
- Tracks application status, follow-ups, and outcomes
- Learns from results to improve future recommendations

The user should always know:

- What was found
- Why it was recommended
- What changed in a tailored document
- What was submitted
- What still needs approval

## 2. Product Boundaries

### What JobCodex should do

- Aggregate jobs from public sources and approved integrations
- Normalize job data into one internal schema
- Rank jobs by fit, urgency, salary, location, and user goals
- Generate application artifacts:
  - Resume variants
  - Cover letters
  - Short answers
  - Recruiter outreach drafts
- Track application lifecycle:
  - Found
  - Saved
  - Tailored
  - Ready to apply
  - Submitted
  - Interviewing
  - Rejected
  - Offer
- Remind the user to follow up
- Maintain an audit trail of all actions

### What JobCodex should not do

- Scrape sites in a way that violates site terms
- Use hidden automation against services that prohibit bots
- Submit applications without user permission unless the target source explicitly permits it and the user has opted in
- Store credentials insecurely
- Make unreviewed claims in resumes or answers

## 3. Core User Experience

### Primary flow

1. User creates a profile.
2. User uploads or builds a master resume.
3. User defines preferences:
   - Roles
   - Seniority
   - Locations
   - Remote/hybrid/on-site
   - Salary floor
   - Industries to avoid
   - Sponsorship requirements
   - Company size preferences
4. JobCodex searches for jobs.
5. JobCodex scores and filters opportunities.
6. User reviews candidates in a queue.
7. User approves tailoring.
8. JobCodex creates a submission packet.
9. User either:
   - clicks to submit manually, or
   - allows an approved integration to submit
10. JobCodex tracks status and follow-up timing.

### Daily flow

- New matching jobs appear
- Best jobs are ranked first
- The user gets a short digest
- Expiring or urgent opportunities are surfaced
- Applications waiting for approval are highlighted

## 4. Product Modes

### Mode A: Copilot

Best default mode.

- Finds jobs
- Scores them
- Tailors documents
- Prepares application steps
- User approves before submission

This is the safest and most defensible mode.

### Mode B: Assisted Auto-Apply

- Uses approved integrations or user-authorized browser flows
- Applies only to sources where this is allowed
- Limits daily submissions
- Requires strict filters
- Keeps a pre-submit review step for risky applications

### Mode C: Full Autopilot

High risk.

- Applies automatically within tightly defined limits
- Requires explicit opt-in
- Needs source-specific rules and compliance checks
- Needs strong logging and kill switches

If you build this, keep it separate from the core copilot so it can be disabled without breaking the rest of the product.

## 5. Functional Requirements

### 5.1 Authentication and identity

- Email/password or OAuth login
- MFA support
- Session management
- Device/session revocation
- Profile linking for resume variants and application history

### 5.2 Profile ingestion

- Upload resume PDF/DOCX
- Parse resume into structured data
- Manual editing of:
  - Work history
  - Education
  - Skills
  - Projects
  - Certifications
  - Achievements
  - Links
- Store multiple resume versions
- Store user preferences and constraints

### 5.3 Job ingestion

Potential sources:

- Public ATS pages
- Company career pages
- Job boards with permitted access
- Email alerts
- RSS feeds where available
- User-saved job URLs

Each source should define:

- Access method
- Refresh frequency
- Rate limits
- Allowed fields
- Terms/compliance notes
- Failure handling

### 5.4 Job normalization

Normalize every job into a common object:

- Title
- Company
- Location
- Remote status
- Salary range
- Employment type
- Seniority
- Description
- Skills
- Benefits
- Application URL
- Source
- Posted date
- Expiry date if known
- Screening questions if available

### 5.5 Matching and ranking

Score jobs using weighted criteria:

- Title fit
- Skill overlap
- Seniority fit
- Location fit
- Compensation fit
- Remote preference fit
- Visa/sponsorship fit
- Industry fit
- Company preference fit
- Recency
- Application friction

Show the score with a plain explanation:

- Why it matched
- What was missing
- Why it was ranked above or below similar roles

### 5.6 Tailoring engine

The system should be able to generate:

- Resume variants
- Summary bullets
- Cover letters
- Short answer responses
- Thank-you messages
- Follow-up notes
- Referral outreach drafts

Rules:

- Never invent experience
- Never invent employers, degrees, metrics, or responsibilities
- Prefer conservative phrasing
- Preserve truthfulness even when tailoring aggressively
- Highlight the same real experience in different ways, not fabricated experience

### 5.7 Application workflow

Application steps may include:

- Login
- Fill personal information
- Upload resume
- Answer screening questions
- Provide salary expectations
- Confirm work authorization
- Provide references
- Submit

The workflow engine should:

- Detect required fields
- Fill from the profile
- Flag unknown or risky questions
- Stop for user review when needed
- Record every field filled and every manual override

### 5.8 Tracking

Track:

- Job discovered date
- First seen date
- Application started date
- Submitted date
- Follow-up dates
- Interview dates
- Outcome
- Notes

Also track funnel metrics:

- Jobs seen
- Jobs matched
- Jobs saved
- Applications drafted
- Applications submitted
- Responses received
- Interviews booked
- Offers received

### 5.9 Alerts and reminders

- New high-score matches
- Application approvals pending
- Follow-up reminders
- Interview prep reminders
- Duplicate application warnings
- Deadline alerts

## 6. Data Model

### Core entities

#### User

- id
- email
- auth state
- preferences
- locale
- timezone
- created_at

#### Profile

- user_id
- headline
- target_roles
- seniority
- salary_floor
- locations
- remote_preference
- industries_to_avoid
- sponsorship_needed

#### Resume

- id
- user_id
- version_name
- source_file
- parsed_json
- rendered_text
- created_at

#### Job

- id
- source_id
- company
- title
- location
- description
- salary_min
- salary_max
- remote_type
- posted_at
- expires_at
- url
- raw_payload

#### MatchScore

- job_id
- user_id
- score_total
- score_breakdown
- explanation

#### Application

- id
- user_id
- job_id
- status
- submission_method
- submitted_at
- last_updated_at
- notes

#### Task

- id
- application_id
- task_type
- status
- due_at
- payload

#### AuditLog

- id
- actor
- action
- target_type
- target_id
- before
- after
- timestamp

## 7. System Architecture

### Frontend

- Dashboard
- Job feed
- Match detail view
- Resume editor
- Application workspace
- Tracking board
- Settings and compliance controls

### Backend services

- Auth service
- Profile service
- Job ingestion service
- Matching service
- Document generation service
- Workflow orchestration service
- Notification service
- Audit/logging service

### Storage

- Relational database for core entities
- Object storage for uploads and generated documents
- Search index for jobs and resumes
- Queue system for ingestion and workflow jobs

### Background jobs

- Job ingestion refresh
- Re-scoring when profile changes
- Document regeneration
- Follow-up reminders
- Source health checks
- De-duplication

## 8. AI/ML Components

### Recommended AI tasks

- Resume parsing cleanup
- Job-to-profile matching explanation
- Tailored summary generation
- Draft cover letters
- Screen question draft answers
- Follow-up email drafting

### Avoid overusing AI for

- Hard validation of user identity fields
- Final submission without checks
- Extraction from poorly structured sources without verification

### Guardrails

- Use templates plus AI, not pure freeform generation
- Add factual grounding from the user profile
- Require a "no hallucination" policy in generation prompts
- Store source evidence for every tailored claim

## 9. Compliance and Legal Considerations

This is a major design area, not a footnote.

### Platform terms

- Many job platforms restrict automation, scraping, or bot activity
- Each source needs its own policy review
- Build per-source allow/deny rules
- Prefer officially supported APIs or user-authorized workflows

### Privacy

- You will store sensitive personal data
- Data may include:
  - Resume history
  - Employment history
  - Contact details
  - Salary expectations
  - Work authorization
  - Demographic data if user chooses to provide it

Design for:

- Data minimization
- Encryption at rest and in transit
- Separate secrets from application data
- Deletion/export capabilities

### Employment risk

- A bad application can hurt a candidate
- An inaccurate answer can disqualify them
- A false statement can create legal and reputational problems

### Truthfulness policy

- The system should never fabricate a qualification
- If unsure, it should ask the user
- If a field is missing, it should leave it blank or mark it for review

## 10. Security Requirements

- Encrypt sensitive data in transit and at rest
- Use short-lived access tokens
- Rotate secrets
- Log privileged actions
- Protect uploaded files from malware
- Sandbox file parsing
- Rate limit public endpoints
- Add abuse detection
- Support account deletion

If you store browser credentials or session tokens for assisted submission, treat that as highly sensitive and isolate it.

## 11. Source Strategy

### Safer sources

- Company career pages with clear terms
- ATS systems with permitted access
- Job alert emails
- User-provided job links
- APIs that allow this use case

### Riskier sources

- Sites with aggressive anti-bot controls
- Sources that ban third-party automation
- Sources that require brittle browser automation

### Practical approach

Build a source registry with:

- Source name
- Access pattern
- Allowed actions
- Pagination strategy
- Retry policy
- Rate limits
- Terms notes
- Fallback behavior

## 12. Application Quality Controls

Every application should pass through checks:

- Is the job relevant enough?
- Does the resume match the role?
- Are salary and location preferences satisfied?
- Are any answers ambiguous?
- Does the user need to confirm sensitive fields?
- Did the system alter anything factual?

Recommended controls:

- Minimum match score
- Company blacklists
- Duplicate job detection
- Daily application cap
- Manual review for seniority jumps
- Manual review for sponsorship/work authorization fields
- Manual review for compensation answers

## 13. UX Considerations

### Dashboard should answer

- What should I do today?
- Which jobs matter most?
- What is waiting on me?
- What was submitted already?
- What is the status of my active applications?

### Useful views

- Ranked job queue
- Application pipeline
- Follow-up calendar
- Resume versions
- Source health
- Submission history

### Important UX principle

Do not hide automation behind magic. Show the system's confidence, assumptions, and edits.

## 14. Operational Considerations

### Monitoring

- Ingestion success rate
- Source-specific error rates
- Job duplication rate
- Submission success rate
- Match acceptance rate
- User approval latency
- Notification delivery rate

### Reliability

- Retry transient failures
- Dead-letter queue for failed jobs
- Idempotent application actions
- Checkpoints in multi-step flows
- Safe resume after interruption

### Cost control

AI and browser automation can get expensive fast.

Watch:

- LLM token cost
- Document generation cost
- Browser session cost
- Proxies or infrastructure cost
- Storage and search indexing cost
- Notification costs

## 15. MVP Scope

If you want a real first version, keep it tight.

### MVP v1

- User profile
- Resume upload and parsing
- Job ingestion from a few sources
- Matching and ranking
- Tailored resume bullets
- Cover letter draft
- Application tracker
- Manual submission workflow

### MVP v2

- Assisted autofill
- Screening question helper
- Follow-up reminders
- Email integration
- Better source coverage

### MVP v3

- Controlled auto-apply for approved sources
- Multi-resume optimization
- Outcome learning
- Referral suggestions
- Interview prep support

## 16. Build Order

Suggested implementation sequence:

1. Define internal schemas for user, job, resume, and application.
2. Build resume parser and profile editor.
3. Build one or two job ingestion connectors.
4. Build matching and ranking.
5. Build the application tracker.
6. Add document tailoring.
7. Add manual application workspace.
8. Add notifications and follow-ups.
9. Add assisted autofill for approved sources.
10. Add automation only where policy and reliability support it.

## 17. Testing Strategy

### Unit tests

- Parsing
- Scoring
- Deduplication
- Template rendering
- Validation rules

### Integration tests

- Source ingestion
- Application workflow steps
- Document generation
- Notification delivery

### Human QA

- Resume correctness
- Cover letter quality
- Factual consistency
- Edge-case jobs
- Sensitive question handling

### Failure tests

- Source timeout
- Duplicate job records
- Resume parse failure
- Invalid login session
- Partial submission
- Network interruption mid-flow

## 18. Metrics That Matter

- Match-to-save rate
- Save-to-apply rate
- Apply-to-response rate
- Response-to-interview rate
- Interview-to-offer rate
- Time saved per application
- User approval rate on suggested jobs
- Document edit rate after AI generation
- Error rate per source

If the tool submits more applications but gets fewer responses, the product is getting worse, not better.

## 19. Risks

### Product risks

- Too much automation, too little quality
- Bad job recommendations
- Generic tailoring
- Poor source reliability

### Business risks

- Users may churn if outcomes are weak
- Infrastructure can become expensive
- Auto-apply can create support burden

### Legal and platform risks

- Terms violations
- Account restrictions
- Data privacy issues
- Unintended misrepresentation

### Model risks

- Hallucinated qualifications
- Overconfident answer generation
- Biased ranking or filtering

## 20. Recommended Personal Build Strategy

If you are building this for yourself, the smartest sequence is:

1. Start as a tracker and matcher.
2. Add resume tailoring.
3. Add assisted autofill.
4. Only then consider limited auto-apply on carefully chosen sources.

This gives you real value early without building a fragile bot first.

## 21. Suggested Tech Stack

This is one reasonable stack, not the only one.

- Frontend: React or Next.js
- Backend: Node.js or Python
- Database: Postgres
- Object storage: S3-compatible storage
- Queue: Redis queue or managed queue
- Search: Postgres full-text or dedicated search engine
- Auth: OAuth plus email login
- AI layer: hosted LLM API plus templates
- Browser automation: only for approved workflows
- Observability: logs, metrics, and tracing

## 22. File and Folder Ideas

If this becomes a codebase, a clean structure might be:

- `apps/web`
- `apps/api`
- `apps/worker`
- `packages/shared`
- `packages/schemas`
- `packages/integrations`
- `docs/compliance`
- `docs/sources`
- `docs/prompts`

## 23. Decision Checklist

Before building, answer these questions:

- Which sources are allowed?
- Is auto-apply in scope or not?
- What is the minimum match score?
- What fields can be auto-filled?
- What must always be user-reviewed?
- What data will be stored?
- How will deletion work?
- What happens when a source breaks?
- What is the fallback if automation fails?
- What is the kill switch for bad behavior?

## 24. Non-Negotiables

- Do not fabricate profile data
- Do not silently submit risky answers
- Do not ignore source terms
- Do not store secrets casually
- Do not make automation invisible to the user
- Do not optimize for volume at the expense of fit

## 25. Bottom Line

JobCodex should be designed as a controlled job copilot, not a spam engine.

The winning design is:

- strong job matching
- truthful tailoring
- visible automation
- safe submission controls
- tracking and follow-up discipline

If built that way, it can genuinely save time without turning into a brittle, risky bot.
