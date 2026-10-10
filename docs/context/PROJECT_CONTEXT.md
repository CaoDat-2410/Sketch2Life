# Project context ledger

## Current product-scope authority — 2026-10-10

Owner explicitly replaced the prior product scope with Product Scope v1.0 for Montessori-inspired collaborative creative learning. Canonical requirements are now Master SRS v3.0 at `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, governed by FEAT-039 and ADR-0014. The target is ages 3–12, Child/Teacher/Super Admin, Android child clients, classroom/group sessions, personal/collaborative canvas, adaptive sketch, gallery, teacher-approved knowledge video, off-screen, reflection/portfolio and administration/privacy/recovery. Owner confirmed keeping FastAPI and React Native.

The older sections below are retained as dated/history records and implementation context. Conflicting product assumptions (under-9, adult-only roles, Parent portal/payment/credit, one-child session, fixed video duration/model and numeric retention) do not override v3.0. Existing source still follows several old policies and is not migrated by this documentation change. Owner additionally chose per-Sketch review for pilot, active-child selection by turn on shared tablets, and explicit Teacher retry/skip/end after exhausted video failure; generation still waits and never automatically skips. Exact age endpoint, child credentials, consent/retention, tenancy/capacity, retry parameters and other technology selections remain open in SRS B17. Security, provenance, inward dependencies and ADR-0006 planning separation continue. See `features/FEAT-039-collaborative-learning-scope/artifacts/REUSE_AND_ARCHITECTURE.md` for source maturity and proposed architecture. Exact old working-copy SRS v2.0 is preserved under FEAT-039 with its hash.

## Detailed SRS foundation amendment — 2026-10-10

The owner requested a more detailed SRS as the foundation for the entire system. Canonical Master SRS is now v3.1 under FEAT-029, governed by FEAT-039 documentation plan/approval revision 3. B19–B26 add state/policy/concurrency/recovery, 38 detailed use cases with acceptance, logical fields/API contracts, 34 screens, privacy workflows, measurement profiles and per-FR verification. Exact v2.0 and v3.0 are preserved with hashes. Current canonical v3.1 supersedes the v3.0 pointer in the earlier same-day amendment; historical records remain evidence.

Owner additionally chose a one-school pilot with expansion preparation; teacher-managed child profiles and QR/session code, without separate child login accounts; school collection of legal-representative consent with authorized Teacher/Admin recording evidence and purposes. Owner then confirmed inclusive 36–155 completed months, one simultaneous class with at most 40 children as pilot target, and default session/artwork retention 90 days after session end. Organization schema, admission/grant/turn mechanics, verification process, age calculations and device/model/performance parameters remain proposed or open as labelled in SRS B17/B19. Enrollment and role are not consent; capacity is not proven. Portfolio/profile/audit/copy policies remain separate, without silently extending raw-source retention.

Only documentation changed in this task. Existing source is not migrated; Android/FastAPI/React Native remain the confirmed technologies. Other runtime/editor/sync/DB/queue/storage/model/web/deployment choices need the applicable ADR and feature approval. ADR-0006 independent Sprint 1 workstreams and separate integration allocation continue.

## Current four-person task allocation amendment — 2026-10-10

For the replacement SRS v3.1, the owner now requests one FE, two BE and one person who connects all other parts, with ordinary task lists and no calendar/duration estimates. FEAT-040 and ADR-0015 record this explicit staffing amendment. Current planning artifact: `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, 57 proposed runtime cards with module/FR/API/data/UI ownership and versioned handoffs.

P1 owns Android and Teacher/Admin UI, P2 core/classroom/collaboration/data, P3 AI/content/media, P4 technical composition/connectors and combined validation coordination. Component owners retain their logic/adapters/tests/fixes. Four independent fixture runners continue under ADR-0006's principle; historical BA/AI/animation/media role labels do not override this newer owner split. Integration allocation is now intentionally recorded, but every runtime feature still needs its own approval. No runtime or SRS bytes are changed by this planning task; task counts are not effort estimates or proof of implementation.

## FEAT-018 legacy branch integration amendment — 2026-10-10

Owner directly requested merging the existing codex/feat-018-contract-plan into dev after the SRS/task publication. FEAT-042 records pinned history, direct approval, conflict/regression reconciliation and offline verification. The incoming branch includes FEAT-030 whiteboard/story-video and UI scaffolds; these remain legacy/experimental and do not override canonical SRSv3.1 or complete its runtime migration. Existing dev guards, Pixi flow and immutable artifacts are preserved. Thirty-four incoming target images/crops remain dormant without verified visual approval. Missing media dependencies and model/GPU/device/visual acceptance remain explicit gates; no live provider or deployment is performed.

FEAT-042 integration completed with merge429e9c6 published to dev and verified retaining both sourcef959426 and prior dev396b4f6. Available offline checks passed: backend2001, mobile22, renderer67 and exact-index web export. Protected SRS/task bytes and original pending runtime work remain unchanged. Actual receipts and environment limits are in FEAT-042 evidence/notes/PUBLICATION.md and VALIDATION.md.

## Purpose

Sketch2Life is now a Montessori-inspired collaborative creative learning platform: children draw, cooperate, receive teacher-controlled AI assistance, explore knowledge/video, perform off-screen activities and reflect; teachers coordinate classroom/group sessions and observe each child's progress.

## Current phase

`FOUNDATION_PUBLISHED`

## Environment policy (owner override, 2026-10-10)

- Windows is the code-development, repository-management and lightweight-static-test environment.
- Do not install new PyTorch, CUDA/cuDNN, Diffusers, Transformers, Accelerate,
  xFormers, model weights, large datasets, Docker images or GPU-specific packages on Windows.
- If a required local dependency is missing, record `REQUIRES_LIGHTNINGAI_TEST`;
  do not call the test passed.
- LightningAI is the dependency-installation, GPU/inference and integration-test
  environment. Use a separate Sketch2Life virtualenv and do not modify the existing
  Wan2.2 environment.
- The canonical workflow is `scripts/lightningai/setup.sh`, then read-only
  `verify.sh`, then `run_tests.sh`. Setup requires explicit
  `SKETCH2LIFE_ALLOW_INSTALL=1`; no script uploads child media or downloads model
  weights implicitly.
- `LOCAL_CODE_READY`, `LIGHTNINGAI_ENVIRONMENT_READY`, `LIGHTNINGAI_TEST_PASS` and
  `VISUAL_QA_PASS` are separate gates and must not be conflated.

The workspace harness and approved architecture skeleton are established and securely published to the project repository. Product feature code must not be started until that feature's plan and relevant task approval are recorded.

## Owner product-scope amendment — 2026-10-06

- Supported child population is younger than 9 years: 0–107 completed months inclusive, across product bands 0–3, 3–6 and 6–9.
- At 108 completed months, a child is outside the supported product target; age-sensitive session and GenAI requests are rejected before provider execution.
- Keep existing 9–12 Montessori catalog rows as source data for future scope; do not return them for current product sessions.
- Age comes from an adult-confirmed profile/session context. The system must not infer age from drawings, narration, or model output.
- Owner-approved capstone-trial package assumptions: Free 10 credits/month; Gia đình 99,000 VND/month with 30 pooled credits for up to 3 child profiles; Lớp học 499,000 VND/class/month with 120 pooled credits for one Guide and up to 25 assigned profiles. One-time top-ups: 10/49,000 VND, 30/129,000 VND, 60/239,000 VND.
- One credit covers a completed adult-approved drawing/story experience through the off-screen handoff; reserve at session start, debit after successful handoff, release on failure/cancellation, and make same-session retries idempotent. Paid monthly plans are manually renewed; backend verifies payment before entitlement/credit grant. No provider or live billing integration is selected; see FEAT-037.

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
- Mobile delivery: Android-only, bare React Native, one app with adult Parent/Guide modes and supervised child participation; child has no role or credential.
- Android identity and support: `com.sketch2life.mobile`; minSdk 29, targetSdk 36, compileSdk 37.
- AI connectivity: every provider is backend-only through an authenticated adapter; the current Lightning account is not treated as private networking.
- AI provider lifecycle: Lightning AI is fixture/dev only on the current normal account; Runpod Serverless is the production target behind the same backend port.
- Async progress default: bounded HTTP polling for MVP, revisited only with measured evidence.
- Authentication: Firebase Authentication only, verified by the backend; test uses the owner-controlled real Firebase project; no Firebase Storage/Firestore/Realtime Database.
- Account model: parent/guide users authenticate with Google Sign-In or email/password; child mode has no independent child account.
- Ownership model: each ChildProfile has exactly one Owner Caregiver (parent or legal guardian); one Owner Caregiver can create many ChildProfiles; ChildProfile has no login credential.
- Guide model: a ChildProfile can have multiple Guide assignments, including overlapping assignments. Parent-created assignments are effective immediately and notify the Guide; exceptional Admin-created assignments notify both Owner and Guide. Share durations are 3/7/15/30 days, and the Owner can revoke immediately.
- Session model: each Guide can run one session at a time. A Guide session notifies the Owner, exposes a live redacted projection to the Owner, and stops immediately when the Owner revokes the Guide assignment.
- Product surfaces: mobile, desktop Guide Console and responsive Parent Web are all target operational surfaces using the same backend authorization. Parent Web is not implicitly a session runner unless a separate command contract is approved.
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

The following remain open and must not be invented by implementation: exact notification channel/retry matrix; Guide field-level access to raw media/history; Parent Web session-creation command UX; break-glass dual approval, notice and time window; physical deployment details; legal-guardian verification and child assent for age 7+; backup/provider-copy deletion; production SLO/RPO/RTO; account lifecycle and Admin provisioning. Test-stage rate limits, redacted backend monitoring and adult-only role enforcement are requirements, not optional scope.

## Local Android development connectivity baseline — 2026-09-28

`apps/ui-mobile` uses Expo SDK 52 with a native development client. The supported local launch
paths are LAN mode for physical devices and explicit ADB reverse mode for localhost/emulator use.
The repository records this recovery in FEAT-032; a host Metro probe alone does not prove that an
Android device can reach the server, and device reload evidence requires a connected ADB device.

## Master SRS scope closure — 2026-09-19

The owner-approved target baseline is recorded in `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` v1.8 and the feature evidence notes `OWNER_SCOPE_CLOSURE_20260919.md`, `OWNER_REQUIREMENTS_CLOSURE_20260923.md` and `SRS_DETAIL_EXPANSION_20260923.md`. It covers the B4–B12 workflow plus complete SRS sections for actors, relationships, schemas, contracts, state, security, observability, retention, Parent Web, verification and implementation-grade test detail. On 2026-10-06 the owner superseded the earlier 0–12 product age target with `<9` / 0–107 completed months; FEAT-029 v1.9 records that amendment. This is a requirements baseline; it does not authorize unrelated provider calls, cloud provisioning, contract migration or deployment.

## Cross-workstream review snapshot — 2026-09-05

Remote workstreams P1 b3f397c, P2 f3014e5, P3 68aceeb and P4 f0dd622 have independent implementations. They are not an integrated runtime and are not merged into the foundation main baseline. FEAT-015 records pinned branch readiness, reproduced test evidence and proposed integration/test gates. ADR-0006 remains unchanged; integration allocation/implementation still requires separate approval. P4 branch context/plan status is stale relative to its approval/code and is explicitly flagged in the review rather than silently corrected here.

## Session-only Montessori profile and mask-quality increment — 2026-09-29

The owner-approved integrated FEAT-018/020/030 increment adds request-scoped explicit child learning
context to deterministic activity ranking, plus offline SAM2.1 candidate checks and pigment-safe
mask-bounded cutout reconstruction. ADR-0010 fixes the current boundary: profile edits remain
volatile/session-only, with no new durable backend record or storage-provider decision. Backend,
mobile, renderer and security evidence is indexed under the owning FEAT-018/020/030 records. Real
SAM/L4 performance, held-out mask quality and Android emulator visual acceptance remain open; a
synthetic selector score is not a real-model quality claim.
