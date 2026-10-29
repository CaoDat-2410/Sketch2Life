# FEAT-060 — Classroom FE/BE integration and SR-01–SR-10 remediation

- Status: APPROVED
- Plan revision: 2
- Implementation status: NOT_STARTED
- Baseline: local `dev@0a7ce768c153f2104cff930569c3eda6e484532c` plus the pre-existing uncommitted FEAT-059 working tree.

## Goal

Connect the current Child, Teacher, and Admin interfaces to supported backend capabilities, prove the four registered classroom workflows with synthetic data, and close or explicitly gate every attached review finding SR-01–SR-10. Report implementation evidence separately from target design and unavailable deployment checks.

## Scope

- Read-only contract and source audit across all three UI apps, BE1 HTTP/schema code, FEAT-057 gates, migration heads, ADRs, active local branch and Modal configuration.
- A staged FE/BE integration starting with WF-01 and WF-02 against the existing BE1 v1 API. Use backend-owned identity, durable records, typed failures, and versioned request/response contracts. Keep provider credentials out of every client.
- Classroom/demo composition separation as an additive runtime profile, preserving the compatibility `create_app()` entrypoint until its callers and route behavior are verified.
- Admin calls only to existing, role-authorized BE1 contracts. Unsupported Admin modules must fail visibly or remain labeled prototype-only; no fictitious list or successful mutation response.
- Evidence-driven remediation for migration/bootstrap order, persisted state mapping, consent/retention/deletion controls, and the four end-to-end workflows. Changes requiring undecided policy or a different owning feature remain gated and are recorded as open, not silently invented.
- Modal preflight and a bounded synthetic live call only when an already-deployed endpoint and complete local secret/profile configuration exist. No deploy, paid GPU provisioning, or production-data request.
- A finding-by-finding register and evidence under this feature; no edits to external handbook/form originals.

## Out of scope

- Merging any remote branch or changing the P2-T5 baseline.
- Production deployment, public endpoint creation, live child data, school pilot, provider-side retention changes, paid GPU provisioning, or performance/capacity claims without an approved profile.
- Breaking or rewriting the BE1 v1 contract, adding broad BE2 functionality outside its exact FEAT-057 card approvals, or claiming complete BE2 graph adoption.
- Choosing a new identity/database/queue/storage framework. Do not change nine migration heads or persisted state semantics until their owner-approved order and contract are recorded.
- Filling the official class/project field with `FA26SE225` based only on a filename.

## Work plan

### 0. Pin source and map contracts

1. Record initial Git status and hashes for relevant FE services, backend routers/schemas, migration heads, FEAT-057 gates, and the FEAT-059 implementation manifest. Preserve unrelated dirty files.
2. Create the SR-01–SR-10 traceability matrix: current source/evidence, supported contract, change needed, owner, verification, and open decision.
3. Map the four approved workflows and each UI service method to an existing route or an explicit contract gap. Inspect current remote refs read-only; do not merge branches.

### 1. Separate the classroom runtime profile (SR-02)

1. Add an explicit classroom-only app factory/entrypoint mounting health and durable BE1 routes; keep local/legacy demo composition in a separate factory/entrypoint.
2. Keep `create_app()` compatibility and test route/middleware/error/lifespan behavior before proposing any default-entrypoint switch.
3. Record the intended deploy entrypoint and rollback path. Do not deploy this change.

### 2. Integrate WF-01 and WF-02 (SR-01, SR-06, SR-10)

1. Implement shared typed API transport for Child, Teacher, and Admin with explicit base URL, bounded timeout, request ID, structured BE1 error parsing, no implicit success fallback, and dependency-injected auth.
2. Connect adult sign-in/token retrieval through the already selected Firebase Authentication path using local environment configuration; never commit project secrets or service-account credentials. A missing config must yield a clear unavailable state.
3. Connect Teacher session setup/lobby/admission controls to existing BE1 session contracts. Surface the returned session identifier and high-entropy join material through an adult-only path.
4. Connect Child admission through both (a) QR/deep link carrying the existing high-entropy BE1 join payload and (b) a six-digit classroom code. The six-digit path uses a new explicit versioned BE1 command that creates only a pending device join request, never reveals child/session data before Teacher admission, and applies code uniqueness/expiry and persisted attempt throttling against enumeration. If the throttling cannot be enforced by the current backend/persistence boundary, keep six-digit entry disabled and surface QR/deep link as the working path until that contract is approved.
5. Keep the device key in platform secure storage, use the Teacher admission step, and bind the returned device grant to the selected managed profile. The display names currently shown in the prototype are not profile identities.
6. Connect drawing operations, checkpoint/reconnect, and artifact upload/read to BE1 contracts. Keep tentative offline strokes labeled local/pending until the backend returns a durable receipt; reject stale revisions and unauthorized device state visibly.
7. Verify WF-01 and WF-02 with synthetic fixtures and a disposable isolated database path when available. Run UI client tests against a deterministic backend/test transport; do not present mocks as a live deployment.

### 3. Integrate supported Admin/Teacher capabilities and close unsupported seams (SR-01, SR-10)

1. Replace Admin mock-token authentication with the same Firebase Auth token source and a backend-verified role/assignment response.
2. Wire only Admin/Teacher service functions that map to existing BE1 organization, class, profile, gallery, observation, and data-request contracts.
3. For dashboard metrics, generic users, AI policy, settings, audit-log export, templates, or other unsupported routes, remove fake successful mutations from runtime mode and record a contract gap. Add a contract proposal only in the owning feature after review.

### 4. Resolve data model, state, privacy, and migration findings (SR-03–SR-05)

1. Inventory all Alembic roots/heads, ORM/table mappings, logical SRS entities, and current migration test coverage. Produce a clean-database bootstrap, upgrade, rollback, and ownership proposal.
2. Obtain Khoa/owner review of the migration sequence before adding merge revisions or altering schema. Verify any approved path on a disposable PostgreSQL database with synthetic data.
3. Publish a versioned state mapping from the target classroom states to BE1 persisted states; cover every allowed and rejected transition. Keep `finished` versus `EndedEarly` unresolved until the responsible owner chooses a semantic mapping.
4. Trace purpose references, consent evidence, effective-consent checks, 90-day retention baseline, export/delete requests, inaccessible-archive transition, purge, and audit evidence. Verify fail-closed paths and deletion behavior with synthetic records.
5. Do not claim consent verification or provider-copy purge unless the mechanism is implemented and its evidence is reproducible. Do not load real child data.

### 5. Expand workflow verification (SR-06)

1. WF-01: Teacher prepares and admits a classroom session; child membership is durable.
2. WF-02: Two synthetic clients draw, change turn, disconnect, reconnect, and recover accepted canvas state; invalid/stale operations are rejected.
3. WF-03: Request and review a sketch suggestion; only the exact Teacher-approved version can be shown, and unsafe/stale/failure cases stay unavailable. Use a deterministic provider adapter unless a separately authorized provider profile exists.
4. WF-04: Review learning media, run an off-screen activity/reflection, and persist outcome before session completion; failure/skip remains truthful.
5. Keep WF-03/WF-04 implementation behind the exact FEAT-057 BE2 cross-lane and per-card gates. A passing unit batch alone does not satisfy these workflow criteria.
6. Capacity of one class/up to 40 children is a target only. Run a bounded synthetic load check only after the test profile, rate limits, and target NFR values are approved.

### 6. Modal and measurable NFR gate (SR-07, SR-08)

1. Record the Modal app/environment, endpoint/auth mechanism, model/license, GPU, region, warm/cold scaling, timeout/retry behavior, secret management, budget cap, retention, and rollback profile.
2. If an existing configured endpoint is available, send one bounded synthetic request, capture request/response IDs and timing without logging credentials or child content, and verify typed result/failure behavior. Otherwise preserve the gap as `NOT_TESTED_CONFIGURATION_UNAVAILABLE`.
3. Propose measurable NFRs for API p95, AI cold/warm latency, availability/error rate, job success, recovery, data deletion, and 40-client capacity. Mark all thresholds proposed until owner/supervisor approval; record measured values separately from targets.

### 7. Review metadata and close the evidence package (SR-09)

1. Preserve the official class/project field as TBD until confirmed from an official source. Do not infer a class or project code from `FA26SE225` in a filename.
2. Update the SR traceability matrix, feature context, decisions, source register, and Review 2 package only after verification. Do not alter external source originals.
3. Run the focused UI/backend checks requested by the owner, applicable architecture/harness checks, `git diff --check`, and `python tools/validate_repository_security.py` before any future commit/push. No commit/push is in this plan.

## Acceptance criteria

- AC01 / SR-01: Child and Teacher execute the approved WF-01/WF-02 paths over typed BE1 APIs through both QR/deep-link and six-digit join paths (six-digit path only when uniqueness/expiry/throttle controls pass); successful responses correspond to durable backend receipts, while failures/stale state remain visible.
- AC02 / SR-02: Classroom and demo composition have explicit entrypoints; legacy `create_app()` behavior is preserved and route snapshots are compared.
- AC03 / SR-03: Logical entities map to persisted tables; clean bootstrap/upgrade/rollback is reproducible on an isolated synthetic database, or the exact owner-approved blocker is recorded before declaring this criterion open.
- AC04 / SR-04: State mapping and transition tests cover target-to-persisted mapping, expected revision, terminal states, and invalid transitions; unresolved `EndedEarly` behavior is not guessed.
- AC05 / SR-05: Consent, purpose, retention, export/delete, archive, purge, and audit checks have synthetic-data evidence; no real child data is used or needed.
- AC06 / SR-06: WF-01 through WF-04 have end-to-end acceptance evidence. If a BE2 approval or infrastructure gate blocks a workflow, it stays OPEN with the exact dependency and is not called passing.
- AC07 / SR-07: A live Modal claim is made only with a captured successful synthetic request to a configured endpoint; otherwise evidence records why no live test was possible and no GPU/performance claim is made.
- AC08 / SR-08: Each NFR separates proposed target, approved threshold, test method, measured result, and status; no qualitative phrase is treated as a pass.
- AC09 / SR-09: No official report silently fills blank class/project fields from an inferred filename value; owner confirmation or an official source is cited before update.
- AC10 / SR-10: Firebase-verified adult identity is used for real runtime paths; mock token and fixture services are confined to explicit demo/test mode and cannot return false success in configured runtime mode.
- AC11: All tests/builds/lint/validators claimed in the report were executed on the recorded source snapshot; evidence is feature-local and contains no secrets or real child data.
- AC12: No unrelated dirty source is discarded; no commit, push, tag, public deployment, or paid Modal provisioning occurs under this feature.

## Risks and mitigations

- **BE1 requires Firebase and PostgreSQL.** Current local preflight found neither process-level config; add placeholder env documentation only and keep integration tests deterministic until a real local profile is supplied.
- **The current Child PIN does not match BE1 admission.** Use a reviewed session payload/deep link or QR contract; do not weaken the backend join secret to fit the prototype screen.
- **Many Admin screens have no corresponding backend contract.** Integrate supported operations only and label the remainder as gaps; never fake a success.
- **BE2 graph is not fully adopted.** Respect FEAT-057 per-card and cross-lane gates; use deterministic provider fixtures for local acceptance.
- **Migration heads and lifecycle meanings are unresolved.** Inventory first; require owner/BE1 review before migration or persisted-state changes.
- **Modal test can incur cost or expose data.** Use synthetic content, one bounded request, pre-set spend cap, and an existing endpoint only. No deploy or paid provisioning.
- **Working tree is already dirty.** Make narrow patches, record touched files and compare against the initial status; never use reset/stash/format-all.

## Verification plan

- Before implementation: contract-to-service matrix; route/schema and migration-head snapshot; current test/build command inventory; local configuration-presence check without reading secret values.
- After each slice: service/client tests with typed success, validation, authentication failure, timeout and stale-version cases; backend contract tests for the exact BE1 route; UI tests that assert loading/error/accepted-state behavior.
- Workflow acceptance: synthetic WF-01–WF-04 integration tests against a disposable database and deterministic AI port where gates allow; live Firebase or Modal is a separate receipt, never inferred from a mock.
- Final: UI build/typecheck/lint and tests for changed apps, focused backend tests, architecture/harness/security validators, route compatibility diff, `git diff --check`, and feature-local manifests/logs.

## Evidence plan

Store the baseline source/contract map, finding register, API request/response fixtures, each workflow receipt, migration map, state transition table, privacy/purge results, Modal preflight/live-call result, NFR proposal and measurement report, final changed-file manifest, and validator logs in this feature’s `evidence/` tree. Redact secrets at capture time; never copy `.env` contents or real child data.
