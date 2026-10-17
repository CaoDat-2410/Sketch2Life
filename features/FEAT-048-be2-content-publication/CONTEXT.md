# FEAT-048 — BE2-12 content authoring, publication and recall

- Status: IN_PROGRESS
- Owner: second BE2 executor, BE2-12 only.
- Goal: versioned learning-library content with exact safety/pedagogical review,
  explicit publication, recall/archive and immutable provenance.
- Scope: DATA-33 content envelope; consume shared DATA-24; sole CMD-48 dispatcher;
  domain/application/ports, persistence/migration, HTTP, tests and handoff.
- Non-goals: BE2-08–11/13–14 logic, frontend/player/model inference, production
  policy selection, provider provisioning, deployment or direct BE1/job DB writes.
- Base: 6dcc57ee0b3d053f071c8c92e72aaaee2e98d899 on foundation branch.
- Work branch: feature/be2-12-content-publication, created 2026-10-17.
- Implementation status: IN_PROGRESS. Owner approved revision 1/P1–P4 on 2026-10-17.

## Approval continuation — 2026-10-17

Actual owner reply approves plan revision 1 including P1–P4 and continued
implementation. The reviewed plan hash is preserved. Begin C1 domain/contracts
on this branch; no service/cloud/package activation, push/merge/deploy or
cross-owner sign-off is inferred. Approval record is authoritative over older
planning-state wording below.

## Authority and source context

The active owner goal authorizes preparation, a separate branch, autonomous local
checks and scoped commits; it explicitly requires presenting a concrete plan
before code when implementation approval is missing. This is that checkpoint,
not inferred approval. See plan/PLAN.md revision 1 and approvals/TASK_APPROVAL.md.

Canonical SRS v3.1 FR056/FR062, UC-035, DATA-33/shared DATA-24/35 and CMD-48 govern
the feature. FEAT-040 card BE2-12 and FEAT-044 handoff define component ownership.
Source-register IDs: collaborative-srs-v3-20261010, four-person-task-backlog-v1,
owner-four-person-allocation-20261010 and
owner-be2-checkpoint-publication-and-split-20261016.

Foundation remains BE2-01 IN_PROGRESS: A17 cloud receipts reviewed, Studio
A17-fix01 NOT_RUN, CR01 pending runtime closure, B-12 HANDOFF. OwnerFence fixtures
are ASSUMED_CONTRACT, not a real BE1 adapter. Candidate shared review schema does
not mean BE2-05 service is implemented or adopted for production.

## Dependencies and risks

- Shared ExactContentReviewCommandV1/RecordV1 0.1-candidate owned by BE2-05.
- BE1 authorization/current consent/artifact/audit ports and P4 composition:
  actual conformance/adoption is an integration gate, never mocked as complete.
- Publication/reviewer separation/recall policy needs approval (plan P1–P4).
- PostgreSQL/SQLAlchemy is a proposed scoped reuse for this card, not authority
  inherited from BE2-01/BE1 ADRs.
- No source/runtime changes outside feature documentation in planning checkpoint.
