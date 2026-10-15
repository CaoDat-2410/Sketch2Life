# FEAT-047 — Real BE1 runtime backend

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_STARTED
- Created: 2026-10-14 (Asia/Saigon)
- Owner request: implement a real backend for BE1 SRS capabilities, not a fixture-only backend.

## Goal

Turn the BE1 domain and durable-adapter foundation into a runnable FastAPI backend that handles real requests through authenticated application services and PostgreSQL-backed state. Runtime success must come from persisted application behavior; fixture runners and in-memory stores are not valid request-path implementations.

## Authorities

- `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, BE1-01 through BE1-16 and dependency map.
- `features/FEAT-045-be1-core-domain-foundation/` and `features/FEAT-046-be1-durable-core-adapters/` as existing foundation and adapter inputs.
- Canonical `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, especially owner-confirmed decisions and B19–B26 source-status labels.
- `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, ADR-0006, ADR-0014, ADR-0015, ADR-0016, and this feature's ADR-0017.
- Owner instruction in this conversation: make the backend real, do not implement it as fixtures; owner answers that consent must remain pending until approved verification and local development media uses persistent filesystem storage.

## Scope

1. Wire the BE1 application path into the existing FastAPI composition root. Persistent BE1 capabilities must require PostgreSQL and must never silently fall back to in-memory/fixture state.
2. Implement BE1-03 through BE1-15 as real, organization-scoped application services, HTTP endpoints, PostgreSQL repositories/migrations, and a durable worker entrypoint, delivered as sequential vertical slices:
   - verified adult identity, role assignments, device-grant lifecycle, classes, managed profiles, enrollment, and consent records;
   - session configuration/lobby/start, join requests/admission, manual groups, progress/help/leave, active-child turns, and canvas operations;
   - operation sync, checkpoints/restore/reconnect, Teacher controls and durable finish;
   - scoped read models, artifact authorization/delivery, gallery snapshots/presentation/annotations, observations/reflections/assessment/portfolio;
   - retention scheduling and export/delete/copy-purge request lifecycle.
3. Use Firebase Authentication only for adult identity verification. Role, school/class assignments, device grants, and authorization are resolved by the backend. No seeded users/accounts or committed credentials.
4. Use PostgreSQL 17 as this feature's durable system of record, reusing FEAT-046 and extending its migrations. Outbox/worker state remains database-authoritative; do not make Redis/RQ authoritative.
5. Use a persistent filesystem artifact adapter only for local development, with a configurable data root and opaque references. Production object storage remains unselected; Firebase Storage is forbidden.
6. Expose a versioned implementation API and document its mapping to the current SRS. B22 routes/DTOs remain proposed and are not silently adopted as a product-wide contract.
7. Enforce only owner-confirmed or separately approved behavior. Consent remains pending and child-data workflows remain blocked until an approved verification path exists. Unresolved retention classes, media-provider purge, group semantics, and other `PROPOSED`/`TBD` details remain gated rather than receiving invented defaults.

## Explicit boundaries

- BE1-16 automatic grouping is Phase 2 and excluded pending a separate allocation/approval.
- No BE2 AI/provider job implementation, mobile client implementation, production deployment, legal conclusion, or full product tech-stack freeze.
- No Firebase Storage/Firestore/Realtime Database; no provider tokens, real child data, seed accounts, or media bytes committed to the repository.
- The user's request removes fixture-only implementation as the backend deliverable. Synthetic data may be used only for feature-local verification against the real runtime and real PostgreSQL/filesystem adapters.
- Do not claim live Firebase authentication or external provider purge without runtime credentials and successful evidence.

## Acceptance criteria

- AC-01: A running FastAPI process exposes the BE1 versioned API and composes real application services; DB-backed actions fail closed when PostgreSQL is unavailable or unconfigured.
- AC-02: Adult identity is verified server-side through Firebase Authentication; role/assignment checks and every resource read/write enforce organization and narrower scopes. No caller-provided role or child ID grants access.
- AC-03: Organization, class, managed profile, enrollment, and purpose-scoped consent records persist durably. Age uses the confirmed 36–155 completed-month bounds. Pending/unverified consent cannot authorize child-data capture or processing.
- AC-04: Session configuration, lobby/start, join request, Teacher admission, manual groups, progress/help/move/leave, and child turn selection are real state transitions with authorization, CAS/idempotency where required, audit, and durable outbox effects.
- AC-05: Canvas writes persist immutable attributed operations with durable acknowledgement; checkpoint, restore/reconnect, and Teacher controls preserve accepted history and reject stale/unauthorized operations.
- AC-06: Scoped reads, artifact authorization, gallery snapshots, presentation/annotations, observation/reflection/assessment, and portfolio access persist and return only authorized projections with source/provenance links.
- AC-07: Session/artwork default retention is 90 days after session end. Export/delete requests have durable status and completion is not reported while unresolved copies or unverified external purge remain.
- AC-08: Local artifact bytes use the configured persistent filesystem adapter and opaque references; unavailable storage fails safely. No fixture/in-memory artifact backend serves real API requests.
- AC-09: Audit/outbox effects are durable and atomic where required; logs and responses exclude credentials, raw media, child names, and unbounded operation payloads.
- AC-10: Docker PostgreSQL 17 runtime acceptance verifies migrations, API-backed persistence, authorization boundaries, stale/idempotent commands, restart/reconnect, artifact persistence, and worker recovery with synthetic identifiers.
- AC-11: Feature-local evidence maps implementation and runtime results to BE1 cards and SRS rows, records open decision gates, and distinguishes local verification from production readiness.

## Steps

1. Record task-scoped runtime, authentication, database, consent, and artifact-storage decisions in ADR-0017; map BE1 cards to modules/contracts.
2. Build the non-fixture runtime composition and request-scoped database/authentication dependencies.
3. Add organization/class/profile/enrollment/consent persistence and authorized management commands.
4. Add session/admission/group/turn/canvas/control commands and synchronization/read endpoints.
5. Add mediated artifacts, gallery, observations/portfolio, and retention/data-request lifecycle.
6. Add durable worker/outbox and local filesystem artifact storage; preserve provider ports and honest pending states.
7. Run Docker-backed acceptance checks and repository static/security checks as required; update feature-local evidence and project context.

## Risks and mitigations

- Consent verification authority and purpose taxonomy are unresolved in SRS OD04. Keep consent pending and deny child-data paths until a separately approved verifier policy is implemented.
- Storage for production, external-copy guarantees, and non-session retention classes remain unresolved. Do not report a purge as complete without verifiable receipts.
- SRS B19/B21/B22 contain proposed fields, transitions, and API details. Preserve source-status labels; implement no proposed semantics without task-scoped decisions.
- Existing prototype routes use in-memory services. Keep them separate until each is replaced by an explicitly wired durable use case; do not relabel prototype state as persistent.
- Firebase project configuration is runtime-only and may be unavailable in local verification. Keep auth verification fail-closed and record any live identity gate.

## Verification and evidence plan

- Use the backend virtualenv and Docker PostgreSQL 17; use only synthetic identifiers and no seeded users or child records.
- Exercise real HTTP routes and repositories against the database; verify restart durability and rollback. Verify local filesystem round trips in a temporary feature-local runtime root and clean test artifacts afterward.
- Run static checks and the repository security validator before any commit/push. Do not treat fixture-runner output as acceptance evidence for the real backend.
- Store commands, sanitized outputs, environment details, and remaining gates under this feature's `evidence/` directory.

Implementation is allowed only for revision 1 and the bounded scope above, as recorded in `approvals/TASK_APPROVAL.md`.
