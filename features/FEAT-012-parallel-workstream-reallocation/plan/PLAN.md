# FEAT-012 plan

- Status: DONE
- Plan revision: 1
- Implementation status: DONE

## Goal

Replace the imbalanced ownership model with four parallel Sprint 1 workstreams and explicitly separate the dependency-driven project roadmap from sprint staffing.

## Scope

- Rewrite system baseline Section 21.
- Rewrite the authoritative four-person allocation document.
- Label Section 26 as a project roadmap, not a team assignment sequence.
- Record the cross-project rule in context and an ADR.
- Preserve the current clean architecture and technology decisions.

## Steps

1. Record the owner's correction and approval.
2. Define independent Sprint 1 inputs, outputs, and exclusions for all four people.
3. Define Integration Sprint scope without assigning it to one default owner.
4. Separate roadmap dependencies from sprint workstream assignment.
5. Validate documentation, harness, architecture, and repository security.

## Acceptance criteria

- [x] Sprint 1 lists the four owner-approved workstreams and excludes integration runtime ownership.
- [x] Person 1 does not implement recommendation runtime in Sprint 1.
- [x] Person 3 does not own the full Android app in Sprint 1.
- [x] Person 4 does not own backend orchestration, infrastructure, deployment, or E2E in Sprint 1.
- [x] Every Sprint 1 workstream can execute against versioned fixtures/contracts without another person's live service.
- [x] Integration Sprint is documented as a separately planned and reallocated phase.
- [x] Project roadmap and team sprint assignment are explicitly distinguished.
- [x] Harness, architecture, and security validators pass.

## Risks and mitigations

- Contract drift: freeze versioned fixture contracts and require compatibility tests.
- Hidden integration work: maintain a visible Integration Sprint backlog instead of attaching it to Person 4.
- Unequal work despite new labels: plan by acceptance criteria/evidence and rebalance before task approval.
- Premature runtime coupling: require standalone runners/harnesses for each Sprint 1 workstream.

## Verification plan

- Review Section 21 and the allocation document against the owner's exact split.
- Search for stale statements assigning end-to-end integration to Person 4 or all Android work to Person 3.
- Run harness, skeleton, architecture, and repository-security validators.

## Evidence plan

Store the documentation review and validator results under this feature's `evidence/notes/` directory.

Implementation is authorized by `approvals/TASK_APPROVAL.md` for revision 1 only.
