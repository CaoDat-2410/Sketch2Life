# Feature decisions

## D-01 — Use PostgreSQL only for this durable core adapter

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for FEAT-046 under ADR-0016.
- Decision: PostgreSQL 17 is authoritative for relational core metadata and transactions; SQLAlchemy 2.x and Alembic provide the adapter and migration boundary. This does not freeze the complete product stack.

## D-02 — Keep external delivery and object bytes behind ports

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for FEAT-046.
- Decision: persist outbox events and asset metadata/source lineage in PostgreSQL. Do not use Redis/RQ as durable truth or select/call an S3-compatible provider in this feature; media bytes remain behind opaque references.

## D-03 — Record the continuation instruction as bounded task approval

- Date: 2026-10-14 (Asia/Saigon).
- Status: recorded.
- Basis: user said “implement tiếp đi” immediately after BE1-02 was identified as the next task and its separate plan/approval requirement was explained.
- Decision: apply that approval only to the exact BE1-02 scope and plan hash in `approvals/TASK_APPROVAL.md`.
