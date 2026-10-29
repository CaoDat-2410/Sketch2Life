# C2 — own policy lifecycle storage, before implementation

Approved P5 PostgreSQL17/SQLAlchemy, new ai_policy module branch. This checkpoint
stores lifecycle versions/reviews/command receipts/events/outbox only. Effective
scope pointer/kill epoch and reservation accounting belong to C3 with their own
forward migration when used; no unused guessed budget/TTL/provider columns now.

Six owned tables: record (scoped head/global revision), version (immutable body/
hash/author/time plus mutable lifecycle), review (append-only exact proof),
receipt (org/principal/request scoped), event (append-only safe metadata), outbox
(same scoped event FK and metadata, pending delivery). No foreign owner FK/write.

Accept: SQL UoW commits or rolls back all six together. Parent UPDATE lock for
writes and SHARE lock for readers; exact version resolution never falls back.
Global record CAS changes exactly +1, new version head+1 starts fresh draft.
Old published version may be retired without changing head. Immutable payload,
author/time and historical proofs cannot be rewritten/deleted by ordinary SQL.
Reviews reconstruct latest dimension per current submission context; all contexts
retained in bounded exact-version history. Schema checks/uniqueness supplement
application rules, but are not substitutes for runtime policy/review authority.

New frozen forward migration imports no mutable runtime metadata; additive
Alembic metadata/schema allowlist preserves other modules. Compare frozen table
DDL against compiled metadata offline. Prepare actual PG17 upgrade/downgrade,
restart, rollback, CAS/unique, immutability/history/scoping tests with explicit
opt-in disposable DB only. Missing environment is NOT_RUN, never synthetic SQL PASS.
No server start/download authority inferred from BE2-12 test approval.
