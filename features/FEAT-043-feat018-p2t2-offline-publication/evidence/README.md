# Evidence index

FEAT-043 records the authority and verification for publishing the FEAT-018 P2-T2 offline WIP
checkpoint (owner: Person 2). Local logs, helper scripts and the PUB-P1 draft plan/inventory are
not published; they are cited by identity only.

| Evidence ID | Record | Type | Status |
|---|---|---|---|
| `EV-043-PUBLICATION-VERIFICATION-20261011` | [publication verification](notes/PUBLICATION_VERIFICATION_20261011.md) | test/review/decision | Fresh checks on every commit tree. Architecture, Ruff and mypy recorded as FAIL under owner decisions B1/C1. |
| `EV-043-SCANNER-FRESH-REVIEW-20261011` | [scanner fresh review](notes/SCANNER_FRESH_REVIEW_20261011.md) | review | Non-independent. No blocking defect in scope. Not a security PASS. |
| `EV-043-SCANNER-EXCLUSIONS-20261011` | [exclusion list](metrics/SCANNER_EXCLUSIONS_T1_T4.tsv) | metrics | 231 baseline rows, SHA-256 `a40f8fed3f693462481d82ce69bccdc8814e5d28681ce6db38582fc4c2468c02`, accepted under decision A. |
| — | [owner approval and decisions](../approvals/TASK_APPROVAL.md) | decision | APPROVED (A + B1 + C1), 2026-10-11. |

Derived public summary for the owning feature:
[FEAT-018 P2-T2 offline checkpoint status](../../FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_PUBLICATION_OFFLINE_STATUS_20261011.md).
