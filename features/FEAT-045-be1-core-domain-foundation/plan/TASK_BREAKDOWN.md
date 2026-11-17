# BE1-01 implementation tasks

This decomposition stays within the approved scope and acceptance criteria in `PLAN.md` revision 1. No dates or duration estimates are assigned.

| ID | Task | Output | Depends on | Acceptance/evidence |
|---|---|---|---|---|
| BE1-01-T1 | Define closed, versioned core command, state, result, and manifest schemas | Backend boundary models and feature fixture manifest schema | None | AC-01, AC-06 |
| BE1-01-T2 | Implement framework-independent authorization, scope, profile-age, consent, admission, turn/canvas, gallery, and data-request rules | Pure domain value objects and typed rule failures | T1 | AC-02–05 |
| BE1-01-T3 | Define inward-facing application ports for verified identity, consent, membership, aggregate CAS, idempotency receipts, and audit | Protocol interfaces over domain types | T2 | AC-08 |
| BE1-01-T4 | Add synthetic request/state/result fixtures for each BE1-01 handoff | Versioned fixture pack, including negative cases | T1–T3 | AC-03–06 |
| BE1-01-T5 | Build the standalone fixture runner and in-memory test adapters | Feature-local runner and reproducible command/output | T1–T4 | AC-05–07 |
| BE1-01-T6 | Review layer direction, proposal labels, provenance, and known source gaps | Feature-local architecture/source-gap note and final status | T1–T5 | AC-08 |

## Scope guard

BE1-01-T5 is the specifically required fixture runner, not a production adapter. It must not call HTTP, a provider, a database, a queue, or an external account. BE1-02 and cross-workstream integration remain separate tasks.
