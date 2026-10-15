# BE1-02 durable core adapters context

- Status: APPROVED for implementation under plan revision 1.
- Created: 2026-10-14 (Asia/Saigon).
- Goal: deliver the next P2/BE1 task after FEAT-045: durable core repositories, migrations, atomic canvas mutation receipts/audit/outbox, and restart-safe recovery.
- Owner request: “implement tiếp đi”, following the explicit note that BE1-02 requires its own feature plan and approval.
- Current authorities: BE1-02 card in FEAT-040 task breakdown; ADR-0015; ADR-0003/0005; ADR-0014; canonical Master SRS v3.1; FEAT-045 BE1-01 contract/domain boundary.
- Scope: PostgreSQL-backed core metadata and transaction adapter using the repository's SQLAlchemy/Alembic dependencies; migration and feature-local adapter documentation.
- Constraints: no Firebase data products; no credentials, seed accounts, real child records, provider calls, app deployment, production rollout, Redis-as-truth, or S3 object-byte integration. Asset media bytes remain behind an opaque reference.
- Dependencies: approved FEAT-045 BE1-01 domain/ports/contracts. The user's continuation instruction is recorded in `approvals/TASK_APPROVAL.md` for this exact bounded plan.
- Implementation snapshot (2026-10-14): SQLAlchemy models/repositories, organization-scoped read ports for revisions, idempotency receipts, operations, audit/checkpoints/assets/outbox state, atomic canvas CAS transaction, audit/outbox, local consumer receipts, Alembic initial migration, and a non-auto-applied synthetic seed fixture are present. Ruff lint/format and targeted mypy pass. Live PostgreSQL 17.11 migration, transaction rollback, tenant isolation, engine recreation/restart persistence, and outbox lease/duplicate handling passed with synthetic identifiers in an ephemeral Docker database. API/worker wiring and deployment remain outside the approved feature scope; see `evidence/README.md` and `evidence/raw/postgres_acceptance_smoke_20261014.txt`.
