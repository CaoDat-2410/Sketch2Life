# FEAT-002 Montessori domain plan

- Status: AWAITING_APPROVAL
- Plan revision: 2
- Implementation status: NOT_STARTED
- Owner: Person 1

## Scope

Montessori domain analysis, versioned Activity Catalog, Learning Objective taxonomy, prerequisite/safety/material rule specifications, deterministic expected-result fixture harness, and acceptance criteria. Recommendation runtime and Gate B implementation are excluded.

## Acceptance criteria

- [ ] Versioned activity/objective schemas exist.
- [ ] Positive and negative fixtures cover age, prerequisite, safety, material, and no-result cases.
- [ ] Fixture expectations identify which candidates are valid/invalid and why, without requiring a recommendation service.
- [ ] Acceptance criteria specify the future recommendation and Gate B contract boundaries without implementing them.
- [ ] A standalone harness validates catalog/rule fixtures without AI, mobile, database, or backend runtime dependencies.

## Sprint 1 output contract

- Versioned catalog and taxonomy fixtures.
- Versioned deterministic rule cases and expected decisions.
- Integration compatibility note for future recommendation runtime and Gate B.

Implementation is blocked until this plan is approved.
