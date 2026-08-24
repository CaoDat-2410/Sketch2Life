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

## Open decisions

See `features/FEAT-001-stack-and-team-plan/TEAM_ALLOCATION.md` and ADR-0006 for the revised Sprint 1 allocation, FEAT-008 for the generic skeleton, FEAT-009 for Android foundation, and FEAT-010 for auth/release/AI-provider strategy. Remaining integration questions are listed in `docs/setup/SYSTEM_QUESTIONS.md`.
