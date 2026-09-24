# Task approval

- Status: APPROVED
- Approver: Project owner; direct request and explicit scope answers in the current conversation
- Approved scope: create one Vietnamese master Markdown SRS based on the current Sketch2Life repository and the supplied workflow/product-flow references, including actor and scope model, business rules, entities/ERD, state machine, functional/non-functional requirements, detailed versioned contract inventory, traceability, and TBD decisions.
- User-confirmed target requirements: use the supplied product workflow; Parent and Guide are adult guardians participating with the child; include Admin; narration is editable and can be recorded again when unclear; digital flow target is about 10 minutes maximum excluding physical activity; parent/guardian selects 30/60/90-day retention.
- Contract treatment: include discovered contract families and preserve unresolved same-name shape conflicts as unadopted/open; do not migrate or adopt contracts.
- Plan revision: 1
- Approved at: 2026-09-18
- Notes: Documentation-only approval. Product/runtime changes, provider execution, contract migration, cloud changes, frontend asset generation/application, release, commit/push, and modification of pre-existing user changes are excluded.

## Addendum — expanded registration-aligned SRS scope

- Status: APPROVED for source review, requirements gap analysis, and preparation of owner clarification questions.
- Owner instruction (2026-09-18): expand the master SRS to match the full scope of Phieu_FA26SE225.docx, include authentication, ask across all requirement sections, check carefully, and do not invent missing decisions.
- Approved next scope after owner answers: revise the same master Markdown SRS, preserving source traceability and distinguishing confirmed requirements, accepted repository constraints, proposed scope, and OPEN_TBD decisions.
- Approval does not authorize application implementation, provider calls, real-child data collection, deployment, publication/release of a dataset, or changes to pre-existing user work.

## Addendum — owner clarification responses

- 2026-09-18: Owner selected the supplied workflow image and confirmed the experience includes a narrated story; set target age range to 0–12; confirmed the repository authentication approach; set Admin as the highest system role; and limited Parent/Guide access to their own children.
- 2026-09-18: Retention data scope and research protocol remain undecided. Expand the SRS using confirmed form facts and repository auth constraints, and label these unresolved details OPEN_TBD.
- Clarification still required: how Guide's own-child boundary interacts with the registration's Guide classroom functions; whether Admin may inspect child content; which listed features are MVP versus extended; detailed auth account lifecycle; and research/retention values.

## Addendum — complete SRS structure, relationships and logical schemas

- 2026-09-19: Owner requested one detailed Markdown system SRS with relationships, schemas and the sections normally expected in a complete SRS.
- Approved documentation scope: add introduction/overall-description sections, external interfaces, relationship/cardinality model, logical data dictionary, proposed request/response schemas, API/error/idempotency contract surface, use cases, verification/acceptance matrix, operational/security constraints, traceability and glossary.
- Schema/API additions are logical SRS proposals and must be labelled PROPOSED_UNADOPTED unless they already match an approved repository contract. No runtime contract migration or implementation is authorized.

## Addendum — owner-approved scope closure and observability

- 2026-09-19: Owner approved the proposed scope strategy: MVP includes animation, narrated story and micro-video; Parent Web is Phase 2 but must be described and share the same backend authorization model.
- 2026-09-19: Owner approved one Owner Caregiver per ChildProfile, many ChildProfiles per owner, many Guide assignments per ChildProfile, immediate assignment, 3/7/15/30-day share, immediate Parent revoke, one active session per Guide, and overlapping Guide assignments.
- 2026-09-19: Owner approved immediate revoke behavior during a running Guide session: stop the session, show an on-screen message, and emit notifications.
- 2026-09-19: Owner approved Parent live visibility of all necessary session information with data minimization; Parent Web is management/monitoring/information surface and is not implicitly a session runner.
- 2026-09-19: Owner approved combined notification channels, Grafana-based observability, durable business/audit logs, and separate audit retention.
- 2026-09-19: Owner approved full child/session data retention classes under the 30/60/90-day policy, archive-to-restricted-storage before purge, and Admin raw-content access only through break-glass.
- 2026-09-19: Documentation scope authorizes updating the master Markdown SRS and feature records. It does not authorize application implementation, provider calls, cloud provisioning, contract migration, or deployment.

## Addendum — owner requirements closure for v1.5

- 2026-09-23: Owner approved updating the SRS and feature records with the architecture and
  requirements answers recorded in `evidence/notes/OWNER_REQUIREMENTS_CLOSURE_20260923.md`.
- Approved target: FastAPI/Python modular monolith, PostgreSQL, Redis/RQ, MinIO local, Android
  React Native, desktop-first Guide Console, responsive Parent Web, REST/OpenAPI and bounded polling.
- Approved test authentication: real owner-controlled Firebase Authentication project with backend
  token verification. Secrets remain runtime-only and no Firebase data products may be introduced.
- Approved role model: mutually exclusive adult `PARENT`, `GUIDE`, `ADMIN`; no child role or child
  credential.
- Approved scope: Parent Web and Guide Console are required operational surfaces; Parent Web is not
  deferred to a Phase 2 scope. Vietnamese is the first UI language.
- Approved Parent projection: phase, status, progress and update time only, with minimum aliases;
  technical errors and internal processing metadata are excluded.
- Approved test requirements: rate limits, retry budgets, idempotency, concurrency guards and
  redacted backend operational monitoring. Lightning connectivity, AI stress testing, cloud
  provisioning and production release remain outside this documentation update.
- This addendum authorizes SRS/context/ADR/evidence/status updates only. It does not authorize
  runtime implementation or Firebase/provider calls in this turn.

## Addendum — implementation-grade SRS detail expansion v1.6

- 2026-09-23: The owner requested a more detailed SRS for the complete target and test operation.
- Approved documentation expansion: local test topology, bounded contexts, role/resource matrix,
  state transitions, API behavior, screen requirements, monitoring signals, rate-limit/idempotency
  behavior, synthetic personas/fixtures, verification layers and implementation sequencing.
- No new product decision is inferred by this expansion. Numeric production SLO/capacity, provider
  execution, cloud deployment, production release and unresolved B28 questions remain unchanged.
- This addendum authorizes documentation/evidence/status updates only; it does not authorize runtime
  code, Firebase calls, Lightning calls or deployment.
