# Deterministic hard-rule semantics

Rules execute for every candidate before any future scoring/model selector. All applicable block reasons are retained; evaluation does not stop at the first failure.

Evaluation order is stable for reporting only:

1. catalog status;
2. age range and band;
3. required readiness tags;
4. prerequisite activities;
5. supervision and policy constraints;
6. required material groups.

The order cannot change the allowed/blocked outcome. Reason codes are sorted by rule priority and code.

## Invariants

- `ACTIVE_FIXTURE` permits deterministic fixture evaluation; it does not imply pedagogical approval.
- Age is represented in completed months. Both min and max bounds are inclusive.
- Every required readiness tag must be present.
- Every prerequisite activity ID must be in the completed set.
- Supervision levels order as `NONE < NEARBY < DIRECT`.
- Each required material group passes when at least one listed material is available.
- Age band `0-3` always requires `CAREGIVER_PRESENT` policy and direct supervision.
- A blocked candidate cannot enter future ranking.
- If no candidate is allowed, result status is `NO_VALID_ACTIVITY`.

The canonical rule data is `data/activity-catalog/mvp/hard-rules.v1.json`.
