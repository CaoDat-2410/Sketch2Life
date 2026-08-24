# FEAT-001 Stack and team plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Scope: stack proposal, four-person allocation, MVP milestones, and pre-implementation validation gates

## Steps

1. Approve or revise the mobile/backend/AI stack proposal.
2. Run a thin React Native + PixiJS/GSAP bridge spike using a fixture drawing.
3. Freeze versioned contracts and fixture manifests.
4. Create four approved feature plans, one per workstream.
5. Implement the vertical slice only after each feature has an approved task record.
6. Integrate the complete E2E flow and collect evidence per feature.

## Acceptance criteria

- [ ] Mobile-only client target is recorded.
- [ ] Backend/data plane and Lightning AI plane boundaries are explicit.
- [ ] Real-model testing is limited to fixture/synthetic data.
- [ ] Four-person ownership covers every MVP area, including integration.
- [ ] React Native + PixiJS/GSAP bridge risk has a spike plan and pass/fail evidence.
- [ ] Final stack decision is recorded in ADR-0003 after project-owner approval.
- [ ] No product implementation begins before this plan and the child feature plans are approved.

## Risks and mitigations

- Bridge performance risk: validate a minimal WebView renderer before committing to full art implementation.
- GPU capacity risk: benchmark real models on Lightning AI with capped profiles and fallback behavior.
- Scope risk: sequence the full flow as vertical slices; defer non-MVP infrastructure until evidence justifies it.
- Integration risk: Person 4 owns the end-to-end join, while every workstream publishes versioned contracts.

## Verification plan

- Architecture review against `docs/architecture/DEPENDENCY_RULES.md`.
- Fixture-only data audit.
- Bridge spike benchmark and device smoke test.
- Contract, state-machine, and fallback tests before E2E.
