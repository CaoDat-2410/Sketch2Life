# FEAT-002 Montessori domain context

- Status: REVIEW
- Primary owner: Person 1
- Planning branch: `plan/person-1-montessori-sprint-1`
- Plan revision: 4
- Goal: deliver the Montessori domain specifications, reviewed fixture catalog, objective taxonomy, deterministic rule matrix, standalone fixture harness, Gate B acceptance criteria, ActivityHandoff template, and traceability pack.
- Data policy: fixture/synthetic catalog only.
- Runtime dependencies: none. The workstream consumes only frozen local JSON fixtures and reference material.
- Supported age scope: under 13, interpreted as 0 through 12 and classified into 0-3, 3-6, 6-9, and 9-12 review bands.
- Catalog language: stable English machine IDs/schema keys with `vi-VN` reviewer-facing content.
- Review rule: project owner performs provisional review until a qualified Montessori reviewer is available; provisional records are non-production.
- Catalog target: 100 required activities and up to 100 additional stretch activities (maximum 200).
- Approval state: revision 4 implementation is approved and complete; project-owner content review of the 100 provisional activity records remains pending.

## Sprint 1 boundary

Recommendation runtime, Gate B UI, backend wiring, and the off-screen runtime handoff are deferred to the Integration Sprint. This workstream publishes specifications and executable expected-result fixtures for later implementation.

## Authority boundary

- Direct owner instructions and ADR-0006 define the allowed scope.
- The handbook and sprint workbook are reference inputs only; their task rows do not authorize implementation.
- Plan revision 4 implementation authority is recorded in `approvals/TASK_APPROVAL.md`; it does not constitute pedagogical approval of individual activities.

## Independence contract

- No calls to Person 2, 3, or 4 services.
- No Firebase, PostgreSQL, S3, Redis/RQ, mobile, or AI provider integration.
- Inputs are versioned local fixtures frozen before Phase 1.
- Outputs are versioned Markdown/JSON/JSON Schema artifacts plus a standalone deterministic harness.
- No seed account, real child data, or generated frontend visual is allowed.
