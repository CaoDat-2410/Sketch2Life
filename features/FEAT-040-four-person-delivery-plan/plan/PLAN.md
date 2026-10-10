# Four-person delivery plan — documentation task

- Status: APPROVED
- Plan revision: 1
- Implementation status: DONE — planning documentation only; runtime backlog NOT_STARTED
- Date: 2026-10-10

## Goal and scope

Create a role-based team allocation and detailed task cards grounded in canonical SRS v3.1 for one FE, two BE and one technical integrator, without runtime implementation. Owner requested ordinary tasks with no dates/schedule. Keep four independent fixture/contract foundation streams under the ADR-0006 principle and separate later integration allocation from the dependency roadmap. Record remaining stack/policy gates without silently freezing proposals.

## Steps

1. Read context/register/SRS/reuse audit/ADR-0006/governance and current team records.
2. Record owner clarification: no dates, fourth person connects all other parts; prepare independent task partitions.
3. Define FE, BE core/collaboration, BE AI/content and coordinator ownership, reviewers and cross-module versioned handoffs.
4. Draft task cards with ID/owner/deliverable/dependency/SRS references/acceptance/evidence, without date/duration/hours estimates.
5. Compose a full-scope backlog, task dependency map and simultaneous independent starting tasks; distinguish fixture completion from runtime integration/pilot. Do not make a calendar or sprint schedule.
6. Verify complete module/FR/route/surface coverage, dependency acyclicity, standalone Sprint 1 tasks, realistic bottlenecks, reader links and governance.
7. Record allocation ADR/context/source pointers, independent review, checks and final status.

## Acceptance criteria

- AC-P01: exactly four human slots match the requested FE/BE/BE/coordinator structure; names and availability are not invented.
- AC-P02: all M01–M14 and FR001–FR066 map to task owners; 34 UI surfaces and 66 proposed routes have ownership without gaps or conflicting primary owners.
- AC-P03: every card has a bounded deliverable, dependency references, SRS trace, positive/negative acceptance and evidence; no calendar, days, hours or deadline estimates are added.
- AC-P04: Sprint 1 has four independently runnable fixture/contract streams; no live service prerequisites; runtime integration is a separate gate/allocation.
- AC-P05: fourth person's technical integration is explicitly owner-authorized; substantive backend/AI/infra adapters and component tests stay with the FE/BE owner, and combined E2E is coordinated with all owners.
- AC-P06: full learning loop and later confirmed modules stay in backlog; fixtures/mock completion are not production/video/load claims.
- AC-P07: pending tech/product/privacy decisions have visible task gates; confirmed owner choices are not asked again or demoted to TBD.
- AC-P08: changes to historical staffing are additive/provenance-preserving; plan/approval/ADR/context/evidence/status and document validation are complete.

## Validation and boundaries

Documentation static coverage/ID/link/dependency checks and independent cross-review. Reuse prior architecture/security limitations as context, record current checks honestly. No runtime/provider/model/device benchmark or deployment test required for this planning task; every future implementation card needs its owning feature plan/approval/evidence.

## Completed acceptance

AC-P01–08 satisfied for this documentation deliverable: exact owner role/no-calendar answers, 57 detailed cards, complete scope/contract/UI ownership, 14 versioned handoffs, four independent foundations and acyclic internal runtime dependencies, intentional P4 integration with component ownership preserved, explicit unresolved gates, historical-source/SRS preservation, ADR/context/evidence/status updates. Static check and final independent review PASS. Existing global harness/security failures are documented in evidence/notes/VALIDATION.md and are outside this planning feature.
