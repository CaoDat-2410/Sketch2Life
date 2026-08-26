# FEAT-001 Stack and team plan

- Status: AWAITING_APPROVAL
- Plan revision: 3
- Implementation status: NOT_STARTED
- Scope: stack proposal, four-person allocation, MVP milestones, and pre-implementation validation gates

## Steps

1. Approve or revise the mobile/backend/AI stack proposal.
2. Run a thin React Native + PixiJS/GSAP bridge spike using a fixture drawing.
3. Freeze versioned contracts and fixture manifests.
4. Create four independently runnable Sprint 1 component plans with fixture contracts.
5. Review the detailed, balanced Sprint 1 task allocation in `SPRINT_1_TASK_ALLOCATION.md`, then freeze shared contract/fixture conventions.
6. Review Sprint 1 outputs and freeze integration contracts.
7. Create a separately estimated and allocated Integration Sprint before implementing the vertical slice/E2E flow.

## Acceptance criteria

- [ ] Mobile-only client target is recorded.
- [ ] Backend/data plane and Lightning AI plane boundaries are explicit.
- [ ] Real-model testing is limited to fixture/synthetic data.
- [ ] Four Sprint 1 workstreams can progress in parallel without live-service dependencies.
- [ ] Each Person 1-4 workstream has bounded task cards, versioned fixture/schema outputs, acceptance evidence, and explicit exclusions.
- [ ] Integration is retained in a visible later backlog and receives a new allocation rather than a default owner.
- [ ] React Native + PixiJS/GSAP bridge risk has a spike plan and pass/fail evidence.
- [ ] Final stack decision is recorded in ADR-0003 after project-owner approval.
- [ ] No product implementation begins before this plan and the child feature plans are approved.

## Risks and mitigations

- Bridge performance risk: validate a minimal WebView renderer before committing to full art implementation.
- GPU capacity risk: benchmark real models on Lightning AI with capped profiles and fallback behavior.
- Scope risk: sequence the full flow as vertical slices; defer non-MVP infrastructure until evidence justifies it.
- Integration risk: keep integration visible as a separately planned backlog; do not attach backend/infra/E2E ownership to Person 4 by default.

## Verification plan

- Architecture review against `docs/architecture/DEPENDENCY_RULES.md`.
- Fixture-only data audit.
- Bridge spike benchmark and device smoke test.
- Contract, state-machine, and fallback tests before E2E.
