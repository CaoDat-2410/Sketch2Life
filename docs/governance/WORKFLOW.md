# Delivery workflow

Every change follows this lifecycle:

```text
DRAFT -> PLANNED -> AWAITING_APPROVAL -> APPROVED -> IN_PROGRESS -> REVIEW -> DONE
                                  \-> REJECTED / NEEDS_REVISION
```

## Required records

Each feature folder contains:

- `CONTEXT.md`: goals, constraints, assumptions, dependencies, and current status.
- `plan/PLAN.md`: scope, steps, acceptance criteria, risks, and verification plan.
- `approvals/TASK_APPROVAL.md`: explicit approval, approver, date, scope, and plan revision/hash.
- `evidence/`: test output, screenshots, benchmarks, review notes, and source links.
- `assets/`: generated, approved, and applied frontend assets when relevant.
- `DECISIONS.md`: feature-local decisions or links to global ADRs.

## Implementation gate

Implementation is allowed only when:

1. The plan is complete enough to review.
2. The task approval record says `APPROVED`.
3. The implementation scope matches the approved plan.
4. Evidence is added during implementation, not reconstructed afterward.

## Completion gate

A feature is done only when acceptance criteria, architecture review, tests, evidence, and context updates are complete. A plan that is merely written is not an implementation.
