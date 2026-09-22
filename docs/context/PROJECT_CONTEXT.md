# Project context ledger

## Purpose

Sketch2Life is a capstone product concept that turns a child's drawing and narration into a short, personalized learning experience, then hands the child off to a physical Montessori activity and captures adult/guide feedback.

## Current phase

`FOUNDATION_PUBLISHED`

The workspace harness and approved architecture skeleton are established and securely published to the project repository. Product feature code must not be started until that feature's plan and relevant task approval are recorded.

## Confirmed from the user's request

- Context must be retained in detail.
- Each feature is isolated in its own folder.
- Evidence belongs inside each feature folder.
- The codebase must have a deliberate clean-architecture layout.
- Frontend visuals must be generated first, reviewed/approved, and only then applied.
- Work must have a plan and explicit approval before implementation.
- The next decision is to ask focused questions and finalize the technology stack.

## Confirmed project decisions from the project owner

- Client target: mobile-only.
- Team: four people; all can contribute across disciplines.
- AI hosting: Lightning AI is required for real-model testing.
- Backend hosting: provider-agnostic initially; AWS-compatible deployment is acceptable later.
- Test data: fixtures/synthetic data only; no real child data in the MVP development loop.
- MVP ambition: cover the full experience, divided into four owned workstreams.
- Delivery model: Sprint 1 uses four independently runnable, fixture/contract-driven workstreams; integration runtime work is deferred to a separately planned Integration Sprint.
- Planning distinction: the project roadmap is dependency-driven, while team sprint assignment is parallel-workstream-driven; one must not be used as the other.
- Mobile delivery: Android-only, bare React Native, one app with role-based child/parent/guide modes.
- Android identity and support: `com.sketch2life.mobile`; minSdk 29, targetSdk 36, compileSdk 37.
- AI connectivity: every provider is backend-only through an authenticated adapter; the current Lightning account is not treated as private networking.
- AI provider lifecycle: Lightning AI is fixture/dev only on the current normal account; Runpod Serverless is the production target behind the same backend port.
- Async progress default: bounded HTTP polling for MVP, revisited only with measured evidence.
- Authentication: Firebase Authentication only, verified by the backend; no Firebase Storage/Firestore/Realtime Database.
- Account model: parent/guide users authenticate with Google Sign-In or email/password; child mode has no independent child account.
- Ownership model: each ChildProfile has exactly one Owner Caregiver (parent or legal guardian); one Owner Caregiver can create many ChildProfiles; ChildProfile has no login credential.
- Guide model: a ChildProfile can have multiple Guide assignments, including overlapping assignments. Parent-created assignments are effective immediately and notify the Guide; exceptional Admin-created assignments notify both Owner and Guide. Share durations are 3/7/15/30 days, and the Owner can revoke immediately.
- Session model: each Guide can run one session at a time. A Guide session notifies the Owner, exposes a live redacted projection to the Owner, and stops immediately when the Owner revokes the Guide assignment.
- Product surfaces: mobile and Guide Console are MVP surfaces. Parent Web is a Phase 2 management/monitoring surface using the same backend authorization; it is not implicitly a session runner.
- MVP media scope: personalized animation, narrated story, and learning micro-video are included in the owner-approved MVP target. Research dataset release remains separately gated.
- Observability: durable domain/session events and audit records are authoritative. Grafana is an operations/dashboard layer over redacted logs, metrics, and traces; raw child media and credentials never enter telemetry.
- Child data lifecycle: Owner selects 30/60/90 days for child/session data classes. Expired data becomes inaccessible archive data before purge. Audit retention follows a separate policy. Admin raw-content access is break-glass, reason-required, temporary in scope, and audited.
- Ownership: the project owner controls Firebase/Google Play accounts and Android release/upload key custody.
- Artifact storage: S3-compatible storage owned by backend ports; no direct mobile bucket access.
- Android delivery: installable APKs for internal testing first, then signed AAB through Google Play test tracks to public release.

## Reference baseline, not yet a final decision

The attached handbook proposes a modular monolith plus workers, a FastAPI/Pydantic backend, PostgreSQL, S3-compatible object storage, Redis/RQ, PixiJS + GSAP for deterministic original-art animation, and a separate AI plane. Based on the owner's answers, the current proposal is React Native + TypeScript for the mobile app, with a PixiJS + GSAP renderer embedded behind a controlled mobile bridge, and the handbook's Python AI/backend baseline. Exact model profiles and cloud services remain benchmark/approval decisions.

## Product invariants carried into the harness

- Original child media is immutable and every derivative has provenance.
- Human Gate A confirms/corrects multimodal understanding.
- Human Gate B approves both activity identity/version and learning-objective identity/version.
- Deterministic safety, age/readiness, prerequisite, and material rules run before any model selector.
- Personalized art animation operates on the child's original artwork; generated learning media is a separate artifact.
- Reviewed learning assets are resolved before cache-miss generation.
- Media failure falls back to simpler safe content and does not remove the off-screen activity.
- A session reaching a ready state must end in an off-screen activity handoff and feedback path.
- Sensitive child data has consent, least-privilege access, retention, and deletion semantics.
- OwnerCaregiverOwnership is the only ownership relationship for a ChildProfile; GuideAssignment grants time-bounded delegated access and never transfers ownership.
- Guide revoke invalidates new access immediately and stops an active Guide session with an in-product message and audit/notification events.
- Parent live monitoring exposes the necessary session projection while applying data minimization to technical metadata.
- Business event history and security audit history are separate from Grafana technical telemetry.

## Open decisions

See `features/FEAT-001-stack-and-team-plan/TEAM_ALLOCATION.md` and ADR-0006 for the revised Sprint 1 allocation, FEAT-008 for the generic skeleton, FEAT-009 for Android foundation, and FEAT-010 for auth/release/AI-provider strategy. Remaining integration questions are listed in `docs/setup/SYSTEM_QUESTIONS.md`.

The following remain open and must not be invented by implementation: exact notification channel/retry matrix; Guide field-level access to raw media/history; Parent Web session creation; break-glass dual approval, notice and time window; physical database/object-storage/queue/Grafana deployment; legal-guardian verification and child assent for age 7+; backup/provider-copy deletion; production SLO/RPO/RTO; account lifecycle and Admin provisioning.

## Master SRS scope closure — 2026-09-19

The owner-approved target baseline is recorded in `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` v1.3 and the feature evidence note `features/FEAT-029-master-srs/evidence/notes/OWNER_SCOPE_CLOSURE_20260919.md`. It covers the B4–B12 workflow plus complete SRS sections for actors, relationships, schemas, contracts, state, security, observability, retention, Parent Web and verification. This is a requirements baseline; it does not authorize runtime implementation, provider calls, cloud provisioning, contract migration or deployment.

## Cross-workstream review snapshot — 2026-09-05

Remote workstreams P1 b3f397c, P2 f3014e5, P3 68aceeb and P4 f0dd622 have independent implementations. They are not an integrated runtime and are not merged into the foundation main baseline. FEAT-015 records pinned branch readiness, reproduced test evidence and proposed integration/test gates. ADR-0006 remains unchanged; integration allocation/implementation still requires separate approval. P4 branch context/plan status is stale relative to its approval/code and is explicitly flagged in the review rather than silently corrected here.
