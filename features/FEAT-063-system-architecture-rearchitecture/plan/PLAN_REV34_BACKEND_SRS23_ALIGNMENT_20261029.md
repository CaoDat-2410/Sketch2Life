# Plan revision 34 - backend slice 1 aligned to SRS 2.3

- Feature: FEAT-063 - whole-repository architecture redesign.
- Plan status at authoring: AWAITING_APPROVAL. Nothing in this plan is actionable until the owner records approval against this exact plan hash in `approvals/TASK_APPROVAL.md`. This revision does not edit that file.
- Authority: owner instruction on 2026-10-29 to revise the plan against the FEAT-063 SRS 2.3. This is a documentation revision, not implementation approval.
- Supersession: this revision replaces Rev33 for future approval and planning. Rev33 is retained unchanged for provenance. The S1 inventory is a subordinate draft; its candidate operations require individual disposition and this revision governs any conflict.
- Baseline: SRS `v2.3-draft` (`artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`) and `artifacts/DATA_TABLE_REGISTER.md` v2.3, plus the approved Rev31 route inventory and Rev32 purpose catalog. The `V2.2_PRESERVED` snapshot is historical and is not the build baseline. Both SRS and register remain unsigned drafts; ADR-0021 is PROPOSED.
- Plan type: implementation plan for three backend slices. Implementation is blocked until approval and until the blocking open decisions below are answered or explicitly defaulted by the owner.

## Goal

Start moving the backend from the collaborative-classroom and process-local demo model to the one-child Parent/Teacher model, using only additive, reversible changes. This slice prepares the ground for StoryRun, the Modal pipeline, billing and Teacher sketch work (later plans) without implementing any of them.

## Verified baseline (static review, no execution)

| Area | Current state | Source |
|---|---|---|
| Route composition | Three profiles: `combined`, `classroom`, `demo`; mounted by `mount_all_routers` / `mount_classroom_routers` / `mount_demo_routers` | `backend/src/sketch2life/interfaces/http/router_composition.py`, `interfaces/http/app.py` |
| Legacy surface | 56 BE1/classroom and 35 demo/local-flow declarations (canvas, lobby, room code, groups, learning stage, Gate A/B, P1, Pixi renderer, whiteboard video) | Rev32 catalog |
| Teacher profile constraints | `be1_managed_profiles`: `age_months BETWEEN 36 AND 155`; `consent_id` and `consent_purpose_ref` NOT NULL | `infrastructure/persistence/be1_models.py` |
| Enrollment | `be1_enrollments` unique on (organization, class, child) only; `state IN ('active','withdrawn')`; no "one active class per child" guarantee | same |
| Consent | `be1_consent_records.state IN ('pending','revoked')` | same |
| Identity | `be1_adult_identities` has issuer/subject/state; no Parent/Teacher account scope | same; register rows for `be1_adult_identities` |
| AI jobs table | `ai_jobs.job.organization_id` NOT NULL; `subject_refs` JSONB array; `history` and `result_refs` JSONB; states `queued, running, succeeded, failed_retryable, failed_exhausted, blocked_unsafe, cancelled`; no target kind, no deadline, no owner scope | `infrastructure/ai_jobs/sql/tables.py`, `domain/ai_jobs/model.py` |
| Settings flags | Feature flags exist as `Settings` booleans (for example `storage_example_enabled`, `whiteboard_video_enabled`) | `infrastructure/config/settings.py` |
| Migration head | `20261028_ll_0001_lesson_library` | `backend/alembic/versions/` |

Not yet reviewed in depth (confirm at implementation start): the full `be1_adult_identities` constraints, the Lesson Library service internals, and every consumer of `JobScope.organization_id` in `application/services/ai_jobs.py`.

## Scope

### Slice S1 - legacy fence (feature flags, no deletion)

1. Add settings flags `classroom_writes_enabled` and `demo_flow_enabled`. Defaults preserve today's behavior (both true) so the change is a no-op until an environment turns a flag off.
2. When `classroom_writes_enabled` is false, only the individually approved method/path operations in the versioned S1 disposition return the error chosen in OD-2, with no command side effect. Do not infer the disposition from HTTP method or a broad prefix: semantic reads such as POST join-status and privacy data requests are not classroom write fences. Registry operations are outside this fence. Preserved routes remain subject to existing authentication, authorization, validation and dependencies; a preserved route is not guaranteed HTTP 200. Before implementation, disposition finish, completion, grant revoke, membership leave and room-code rotation individually; do not silently authorize legacy writes at final cutover.
3. When `demo_flow_enabled` is false, `mount_demo_routers` contributions are not mounted in the `combined` profile; the standalone `demo` profile is unchanged.
4. No source route is deleted, renamed or re-versioned; the disabled demo flag changes mounting in the combined profile as described above. No table is dropped, truncated or copied. Existing session IDs keep their historical meaning and are never converted into story runs. The flag is preparation only: any real cutover follows SRS 2.3 section 12.3 baseline/backup, expand, mapping, reconciliation and read-only gates, frontend coordination, monitoring and rollback. A local flag test is not cutover approval.

### Slice S2 - Parent identity and profile foundation

1. Alembic expand migration (new revision after the current head), additive only:
   - `be1_adult_identities`: add nullable `account_scope` (`PARENT` or `TEACHER`) with a CHECK; existing rows stay NULL (treated as legacy/unclassified, never inferred as Parent).
   - `be1_managed_profiles`: add `data_origin` (`SYNTHETIC_TEST`, `REAL`, `LEGACY_UNCLASSIFIED`), backfilled `LEGACY_UNCLASSIFIED`; make consent references nullable with a CHECK that synthetic profiles have neither consent reference, REAL profiles have both, and legacy rows retain their existing references without granting eligibility. Check existing rows and migration compatibility before execution. No fake consent rows and no synthetic organization are created. A reference does not prove current consent: `LEGACY_UNCLASSIFIED` fails closed, and REAL processing remains blocked pending an approved real-data policy and current authorization decision. Synthetic eligibility requires separately approved, server-managed evidence; deny missing, revoked or expired evidence.
   - New `parent` schema with `child_profiles`, `profile_revisions` (immutable, unique `(parent_profile_id, revision_no)`, age CHECK per OD-1), `profile_context_entries`, `data_authorizations`, as specified in the register. `profile_support_needs` (encrypted notes) and `profile_share_grants` (v2.3 sharing) are excluded from this slice.
2. Separate gated step, not part of the automatic upgrade: a read-only reconciliation query/report for duplicate active enrollments, then a partial unique index on active enrollment per `(organization_id, child_id)`. The index step aborts with a clear message if duplicates exist; it never auto-withdraws or rewrites enrollments.
3. Domain and application code, dependency direction inward: `domain/parent_profiles` (profile head + immutable revision rules), contracts `OwnerScopeRefV1` and `ProfileRefV1` under `contracts/`, repository port and SQL adapter, use cases for create/revise/list/delete with idempotency keys.
4. HTTP: `GET /v1/me` (verified identity, role and scope) and `/v1/parent/profiles` (list, create, create revision, delete). Authorization is derived server-side from the verified Firebase identity through the existing identity port; the client never supplies scope. A principal already scoped as the other account type receives `ACCOUNT_SETUP_UNAVAILABLE` (409). Foreign or missing resources return the single `RESOURCE_NOT_FOUND` shape.
5. Parent data never uses a fake organization ID.

### Slice S3 - AI job target model (additive)

1. Alembic expand migration on `ai_jobs.job`: add `owner_scope_kind` (`ORGANIZATION`, `PARENT_ACCOUNT`, `GLOBAL`) and `owner_scope_ref`, backfilled `ORGANIZATION` / `organization_id`; relax `organization_id` only under scope-specific invariants. Organization jobs require a matching organization scope/ref; Parent jobs require a real Parent scope/ref with no fabricated organization; GLOBAL representation and allowed references require an explicit versioned contract decision before implementation. Reject invalid or incomplete combinations and test cross-scope isolation. Add `target_kind`, `target_ref`, `target_revision`, `expected_input_hash` and `deadline_at` (nullable for legacy rows). Legacy target fields are all null; new jobs require the complete target/ref/revision/hash tuple, enforced at contract and storage boundaries.
2. Target contract covers the eight SRS/register kinds: `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_SKETCH_DECK_REVISION`, `PARENT_SKETCH_GUIDE`, `LESSON_LIBRARY_VERSION`, `LESSON_VERSION_VISUAL_ASSET`; a new job must carry exactly one target kind/ref/revision and expected input hash, legacy rows remain valid with NULL. New jobs use `session_id=NULL` and empty legacy arrays/history. Fake-only S3 uses an event/receipt port or fixture; durable event/attempt implementation and parity with the register remain a separately gated later slice. Resolve Story/video child scope from the canonical target through a port; sketch and guide targets carry no child/profile subject, and Parent guide input is limited to generic topic/difficulty.
3. Domain: extend `JobScope` / job creation with the owner scope and target, keeping current constructors working. Add the 6-hour acceptance deadline as a named policy value, not a literal in transition code. State-set extension (stale, retry wait, awaiting reconciliation) follows OD-5.
4. Update owner-notice matching and eligibility to be scope-generic while preserving current organization behavior; existing `test_ai_job_*` suites must pass unchanged.
5. No Modal adapter, no provider call, no new job types executing real work in this slice. Job types for the eight target kinds are accepted by the contract and dispatched only to fake adapters, subject to contract and eligibility gates.

### SRS flow alignment and unresolved source conflict

- Parent: BR-08/09/15 and FR-P-05 place the activity list after video; the owner previously selected this ordering in the Rev25 approval. Teacher sample pins one approved activity before its video. Preserve this distinction in future flow contracts.
- SRS UC-02, the StoryRun state description, pipeline, P1, API and `story.runs` register still contain pre-video or mandatory activity language. They have not been reconciled. Do not silently claim the SRS is consistent or assume a blanket precedence across those passages. A separate SRS/register crosswalk and owner decision must resolve the precise data contract and remaining conflicting passages before implementing dependent StoryRun/Parent activity flow; S1 alone does not resolve it.
- The current Teacher source permits 36–155 months; the SRS 2.3 target is 36–120 for both roles. The S2 Parent target is 36–120. Retaining the Teacher source limit temporarily is a migration gap, not SRS conformance. Inventory affected legacy rows and define a separately approved, non-destructive validator/migration before claiming Teacher target compliance.
- The existing Qwen3-VL Modal synthetic smoke establishes technical execution only. SRS records a Qwen3-VL quality NO_GO and Qwen2.5-VL as an unbenchmarked candidate; no new model selection or production readiness is implied.

## Explicitly out of scope (later plans)

Modal provider port and Volume transfer; StoryRun aggregate and state machine; upload/Whisper/VLM review flows; storyboard and script confirmation; admission saga; LTX scene generation, consistency, FFmpeg, TTS, safety; billing, quota, MoMo/VNPAY; notifications; Teacher occurrence/Sketch Deck; Parent sketch guide; profile sharing; support-needs encryption; Python 3.13 move; frontend changes; production hosting.

## Blocking open decisions (owner)

| ID | Decision | Default if the owner says "use your recommendation" |
|---|---|---|
| OD-1 | SRS target is 36–120 months for both roles; source Teacher permits 36–155 | Parent uses 36–120; Teacher temporarily retains source range until separately approved reconciliation/migration, explicitly non-conformant to target |
| OD-2 | Response when classroom writes are disabled (status and code) | HTTP 410 with a stable code `FEATURE_RETIRED`, added to the error contract |
| OD-3 | Frontend coordination: `apps/teacher-ui` still has `SessionLobbyRuntime` and lobby routes | Flags stay on in shared environments until the frontend owner confirms removal |
| OD-4 | `account_scope` for existing identities | Leave NULL; classify only through an explicit, audited step |
| OD-5 | AI job states: extend the DATA-25 set additively with `stale`, `retry_wait`, `awaiting_reconciliation`, or map onto existing states | Extend additively; do not rename existing values |
| OD-6 | New target kinds and the `history` / `result_refs` JSON columns (register says no new JSON history for new work) | New target kinds do not write those columns; a separate event/attempt design is planned in the pipeline plan |
| OD-7 | Whether a disposable local PostgreSQL/Docker run to rehearse upgrade and downgrade is authorized for this slice | Not authorized unless the owner approves it explicitly; otherwise migrations are reviewed statically only |

## Acceptance criteria

- AC1 (S1): with both flags at their defaults, the route set and behavior of the combined app are unchanged (135 declarations, 121 unconditional operations per Rev31/32).
- AC2 (S1): with `classroom_writes_enabled=false`, every explicitly approved method/path in the versioned disposition returns the OD-2 error, request ID and no command side effects. Preserved semantic reads, privacy/registry operations, health, unknown paths and Lesson Library are not caught by the fence and retain their existing auth/validation/availability behavior; no blanket HTTP 200 claim. Test active session/grant transition cases; classify cleanup/security operations before enabling a fence. Final cutover gates and frontend coordination are separate.
- AC3 (S1): with `demo_flow_enabled=false`, the combined app does not expose the demo-flow routes; the `demo` profile still does.
- AC4 (S2): migration is additive; every pre-existing row still satisfies all new constraints; no row is deleted or rewritten except the declared `data_origin` backfill.
- AC5 (S2): a Parent can create a profile and revisions only for themself; revision rows are immutable; another principal receives `RESOURCE_NOT_FOUND`; a Teacher-scoped principal cannot register as Parent and vice versa.
- AC6 (S2): the partial unique enrollment step is separate, gated by a duplicate report, and reports (not resolves) conflicts.
- AC7 (S3): legacy jobs behave exactly as before; each of the eight kinds is contract-tested with correct scope, hash and subject restrictions using fake adapters; a non-organization job can be created, claimed and completed; missing or multiple target identity is rejected for new jobs and legacy arrays/session are not repurposed.
- AC8 (S3): organization-scoped owner notices still cancel only matching organization jobs.
- AC9 (all): no secrets, absolute local paths, real child data or provider calls are added; Firebase use stays Authentication-only; dependency direction follows `AGENTS.md`.
- AC10 (S2): synthetic profiles cannot carry consent references; unclassified and unauthorized/expired/revoked cases fail closed; REAL references alone do not authorize real processing. Test negative cases using fixtures only.

## Verification plan

- New unit tests for the S2 domain and use cases, contract tests for `OwnerScopeRefV1` / `ProfileRefV1` and the error envelope, and route tests for `/v1/me` and `/v1/parent/profiles`.
- Regression: the existing `test_ai_job_*`, BE1 registry/session, and Lesson Library suites for the modified areas.
- Backend linter and type checker for modified modules, using the repository's configured tools.
- Migration review: static review of upgrade/downgrade SQL; upgrade/downgrade rehearsal only if OD-7 is approved.
- Repository gates before any commit proposal: `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `git diff --check`; `python tools/validate_skeleton.py` if repository structure changes. Report actual output and blockers.
- Worktree note: run tests with `PYTHONPATH` pinned to this worktree's `backend/src`, because the editable install may point at another checkout.

## Sequencing

1. S1 first (no schema change, smallest risk, unblocks frontend planning).
2. S2 and S3 each add one Alembic revision; keep a single linear migration chain with S2 before S3. They touch different modules and may be implemented in parallel only if the migration order is fixed in advance.
3. Each slice ends with evidence under `evidence/`, a CONTEXT/status update, and no commit unless the owner asks.

## Rollback

- S1: set the flags back to true; no data is touched.
- S2/S3: migrations only add nullable columns, constraints that existing rows satisfy, and new empty tables. Downgrade removes the added objects only when they hold no data; otherwise it stops with a message. The legacy tables and columns are never dropped.

## Risks

- Changing `ai_jobs.job.organization_id` to nullable touches code that assumes an organization on every job (eligibility, owner notices, cancellation). The scope-generic change must be covered by the existing suites before merge.
- Disabling classroom writes before the Teacher frontend is updated would break the current Teacher UI; OD-3 keeps the default safe.
- Age range and data-origin rules affect privacy review; real child data stays out until the separate real-data gate.
- The SRS is unsigned; if the owner changes v2.3 decisions before approval, this plan needs a new revision and hash.

## Approval request

Record, in `approvals/TASK_APPROVAL.md`, the SHA-256 of this file together with the approved slices (S1, S2, S3 or a subset), the answers or defaults for OD-1 to OD-7, and any explicit exclusions. Until then this plan is documentation only.
