# Owner requirements closure — architecture, FR/NFR and test operations

- Date: 2026-09-23
- Feature: FEAT-029-master-srs
- Decision source: direct owner answers in the current project conversation
- Scope: requirements and architecture baseline only; no runtime implementation, provider call,
  cloud provisioning or production release was authorized by this record.

## Confirmed architecture

- Backend: FastAPI/Python modular monolith.
- Local test services: PostgreSQL, Redis/RQ and MinIO.
- Mobile: Android-only React Native.
- Guide Console: React/TypeScript web, desktop-browser first.
- Parent Web: React/TypeScript responsive web, must support mobile and desktop browsers.
- API: REST/OpenAPI; bounded HTTP polling for asynchronous progress.
- UI language: Vietnamese first; other locales may be added later.
- Current stage: test/demo only. Lightning connectivity, AI/provider stress testing and production
  deployment are explicitly outside this stage.

## Authentication and role decisions

- Use the owner-controlled real Firebase Authentication project for test integration.
- Adult authentication uses Google Sign-In and email/password according to the repository boundary.
- Backend verifies Firebase ID tokens and owns authorization.
- Roles are mutually exclusive per account: `PARENT`, `GUIDE` or `ADMIN`.
- There is no `CHILD` role and no child credential. A child is a supervised participant in an
  adult-owned session.
- No Firebase Storage, Firestore or Realtime Database is allowed.
- Firebase tokens, service-account JSON, refresh tokens and other credentials must remain runtime
  secrets and must not enter the repository, mobile bundle or logs.

## Functional requirements confirmed

- Full test flow is in scope: login, ChildProfile, Guide assignment, session, fixture capture and
  understanding, Gate A, recommendation, Gate B, Pixi flow, whiteboard fixture/placeholder,
  off-screen handoff and feedback.
- Guide Console is required and supports assigned children, session, Gate A/B, recommendation,
  observation, feedback and approved curriculum/mapping operations.
- Parent Web is required in the overall operational SRS; it is not deferred to a Phase 2 scope.
- Parent Web supports ChildProfile management, Guide assignment/revoke, monitoring, history,
  retention/deletion, feedback and notifications.
- Parent live monitoring is a minimal projection: phase, status, progress and update time only;
  technical errors and internal processing details are not exposed.
- Parent revoke immediately stops an active Guide session, blocks subsequent Guide commands and
  records notification/business/audit events.
- Rate limiting, retry budget, idempotency and one-active-session-per-Guide are mandatory in test.

## Non-functional requirements confirmed

- Vietnamese-first UI.
- Guide Console desktop-browser first.
- Parent Web responsive on mobile browser and desktop browser.
- Backend monitoring is required for health, errors, latency, queue/jobs, database/storage,
  session state, assignments/notifications, security and data lifecycle.
- Business events and security audit records remain authoritative; telemetry is redacted and never
  contains raw drawing, raw audio, full transcript, tokens, secrets or provider URLs.
- Test-stage rate-limit baseline: one active session per Guide, five session starts per minute per
  user, three processing retries per session/stage, image limit 10 MB, audio limit 20 MB, and
  user/IP API throttling with typed `RATE_LIMITED` errors.
- AI quality/latency stress tests, production capacity, cloud availability and provider benchmarks
  are not acceptance gates for this stage.

## Explicitly still open

- Firebase account invitation, recovery, MFA/reauthentication and Admin provisioning UX.
- Exact notification channels and retry/dead-letter policy.
- Guide field-level access to raw media, transcript and history.
- Parent Web session-creation command UX.
- Break-glass dual approval, notice and exact time window.
- Production SLO/RPO/RTO, deployment topology and capacity.
- Legal guardian verification and consent/assent handling for children aged 7+.
- Backup/provider-copy deletion and legal archive exceptions.

