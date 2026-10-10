# ADR-0015: Four-person role and integration allocation

- Date: 2026-10-10, Asia/Saigon.
- Status: OWNER_ROLE_ALLOCATION_ACCEPTED; DETAILED_RUNTIME_BACKLOG_PROPOSED.
- Owner: Sketch2Life project owner.
- Approval: FEAT-040 documentation task approval revision 1.

## Context and direct authority

The owner asked for tasks for four people: one FE, two BE and one person who synthesizes the work. The owner then answered “chia theo tasks thường thôi, ko cần ngày” and clarified the fourth person “sẽ chịu trách nhiệm nối lại tất cả các thứ khác”. The replacement product baseline is canonical Master SRS v3.1 under FEAT-029/039 and ADR-0014.

ADR-0006 and FEAT-001/012 describe historical discipline-based assignments. Their fixture independence, versioned contracts and separation of dependency roadmap from team assignment remain useful; their old BA/AI/animation/media staffing labels are superseded for this replacement scope by the latest direct owner instruction.

## Accepted staffing decisions

1. P1 is FE, P2 is BE1 core/classroom/collaboration/data, P3 is BE2 AI/content/media, and P4 is the technical integrator. Names are unspecified. The BE domain partition and detailed cards are proposed implementation organization, subject to feature plans and review.
2. Deliver ordinary task cards with outputs, dependencies, SRS trace, acceptance and evidence. No calendar, dates for delivery, hours, duration estimates or sprint schedule.
3. P4 intentionally owns composition, cross-boundary connectors, FE–BE/worker wiring, shared run environment, integration tests coordination and technical handover. This responsibility is explicitly authorized by the owner clarification; it is not a default assignment of all backend/infra/E2E to P4.
4. P1/P2/P3 retain component logic, adapters, component tests, benchmarks and fixes. P4 exposes contract mismatches and routes defects to their owner. Domain/application dependencies point inward; no integration by direct cross-module DB writes.
5. Four independent starting outputs are FE-01, BE1-01, BE2-01 and INTG-01. Their synthetic fixture/contract runners need no other live service, provider or completed task. Later cross-review adopts compatible candidate contracts; runtime integration is a separate approved feature activity. “Sprint 1” remains a historical technical principle, not a calendar added to the new task list.

## Concrete proposed allocation

The authoritative current planning artifact is `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`: 15 FE, 16 BE1, 14 BE2 and 12 integration cards, total 57. It includes 14 handoffs, internal runtime dependencies, all 14 modules/66 FR and one primary maintainer per 66 CMD/35 DATA/34 UI responsibilities. Task count does not imply equal effort or measured delivery duration.

CMD-48 has one P3 dispatcher for content/preset/AI/core-policy typed branches; core non-AI policy logic belongs to P2 through a versioned port. CMD-59/60 remain P2 read/delivery gateways delegating to P3 source projections and exact review eligibility. P3 owns durable AI job adapters and provider-copy lifecycle, not P4. Gallery/video works without live Sketch assistance; shared exact-review schema is available from foundation fixtures.

## Constraints and consequences

- This decision does not implement the 57 cards, adopt all logical SRS contracts, freeze the full stack, call providers or authorize deployment/commit/push.
- Android/FastAPI/React Native are confirmed. Other runtime/editor/sync/DB/queue/storage/web/model/provider choices and numeric policies retain their decision gates.
- Firebase remains Authentication-only; original/provenance, consent/resource scope, privacy and repository security rules remain.
- One FE covering Android and Teacher/Admin is an explicit workload bottleneck. Integrate bounded flows as outputs become ready; do not require all 57 cards before any integration, or declare the full scope finished using fixture success.
- Existing FEAT-001 documents and ADR-0006 remain historical evidence with an additive current-allocation pointer. The SRS bytes and previous evidence are preserved.

## Evidence

- features/FEAT-040-four-person-delivery-plan/approvals/TASK_APPROVAL.md.
- features/FEAT-040-four-person-delivery-plan/evidence/notes/SOURCE_AND_ALLOCATION_REVIEW.md.
- features/FEAT-040-four-person-delivery-plan/evidence/notes/INDEPENDENT_REVIEW.md.
- features/FEAT-040-four-person-delivery-plan/evidence/notes/VALIDATION.md.
