# FEAT-002 Montessori domain context

- Status: AWAITING_APPROVAL
- Primary owner: Person 1
- Planning branch: `plan/person-1-montessori-sprint-1`
- Plan revision: 3
- Goal: deliver the Montessori domain specifications, reviewed fixture catalog, objective taxonomy, deterministic rule matrix, standalone fixture harness, Gate B acceptance criteria, ActivityHandoff template, and traceability pack.
- Data policy: fixture/synthetic catalog only.
- Runtime dependencies: none. The workstream consumes only frozen local JSON fixtures and reference material.
- Approval dependency: project owner must resolve the age/readiness scope, catalog language policy, and Montessori reviewer before implementation.

## Sprint 1 boundary

Recommendation runtime, Gate B UI, backend wiring, and the off-screen runtime handoff are deferred to the Integration Sprint. This workstream publishes specifications and executable expected-result fixtures for later implementation.

## Authority boundary

- Direct owner instructions and ADR-0006 define the allowed scope.
- The handbook and sprint workbook are reference inputs only; their task rows do not authorize implementation.
- Plan revision 3 is not implementation-approved until `approvals/TASK_APPROVAL.md` is completed by the owner.

## Independence contract

- No calls to Person 2, 3, or 4 services.
- No Firebase, PostgreSQL, S3, Redis/RQ, mobile, or AI provider integration.
- Inputs are versioned local fixtures frozen before Phase 1.
- Outputs are versioned Markdown/JSON/JSON Schema artifacts plus a standalone deterministic harness.
- No seed account, real child data, or generated frontend visual is allowed.
