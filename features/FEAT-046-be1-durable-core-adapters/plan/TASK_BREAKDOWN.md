# BE1-02 implementation tasks

This decomposition stays within FEAT-046 plan revision 1 and the BE1-02 card.

| ID | Task | Output | Acceptance/evidence |
|---|---|---|---|
| BE1-02-T1 | Record scoped PostgreSQL/SQLAlchemy/Alembic decision and record map | ADR-0016 plus table/port map | AC-01, AC-08 |
| BE1-02-T2 | Implement core SQLAlchemy models and repositories | Core persistence mappings and runtime session factory | AC-01, AC-07, AC-08 |
| BE1-02-T3 | Implement atomic mutation unit-of-work | CAS, operation, receipt, audit, outbox commit | AC-03, AC-04 |
| BE1-02-T4 | Persist checkpoint/asset metadata and lineage | Opaque refs and versioned metadata rows | AC-02, AC-05 |
| BE1-02-T5 | Implement restartable outbox dispatch and idempotent consumer receipt | At-least-once dispatcher and consumer boundary | AC-05, AC-06 |
| BE1-02-T6 | Add initial/restore migrations and review evidence | Alembic environment, migration note, synthetic seed fixture with no credentials, evidence | AC-02, AC-07–AC-09 |

## Guard

The PostgreSQL transaction is authoritative for durable core state. Redis, RQ, and S3-compatible object storage remain unselected/unwired by this feature. Outbox handlers must not log child data or provider secrets.
