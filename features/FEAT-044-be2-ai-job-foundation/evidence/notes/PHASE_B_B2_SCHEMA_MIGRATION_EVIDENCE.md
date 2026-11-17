# BE2-01 Phase B — B2 schema and migration evidence

> Historical Claude pre-review delivery. Current correction/package state and operator commands
> are in PHASE_B_B2_CODEX_FIX_EVIDENCE_20261015.md; old eb9d package/run instructions below are
> superseded. Current local corrections PASS, PostgreSQL NOT_RUN; no B3.

- Date: 2026-10-15, Asia/Saigon. Executor: Claude, under the actual Phase B approval in
  `approvals/PHASE_B_TASK_APPROVAL.md` (plan rev3 B1–B6, first code turn **B2 only**) and
  `plan/CLAUDE_PHASE_B_IMPLEMENTATION_PROMPT.md`. No B3–B6 code. No commit, push or deploy.
- State: **B2_CODE_COMPLETE — PostgreSQL checks NOT_RUN (REQUIRES_STUDIO_RUN)**. The B2 exit
  (migration matrix and constraint introspection on real PostgreSQL) is not yet evidenced, so
  this is not yet `B2_READY_FOR_REVIEW`. The Studio run below is the only remaining B2 step.

## Files (source snapshot)

Base commit `993a26cae78c0a4fe983033f03881838c886b176` (= Studio checkout) plus patch
`b2_source.patch` sha256 `eb9d75bdca165ffb8ffbdb98db3fa79310930cf619d3c278640ec5a2fefa5bab`
(59,067 bytes; manifest sha256 `bdd4d1f8f9a74c582be74cf139f564c910071cdc7ed911a48971570efb1f49bd`).
Verified: the patch reverse-applies to this worktree and applies cleanly onto pristine `993a26c`.

| File | Change | sha256 |
|---|---|---|
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/__init__.py` | new | `389d10a2…6e6dec09f501b` |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | new — SQLAlchemy Core metadata, schema `ai_jobs` | `af90b030…4a444aec366707bef8f` |
| `backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py` | new — frozen DDL, branch `ai_jobs` | `d4420b8b…6e6da2c81c0a1d5fe7c35c` |
| `backend/alembic/env.py` | ai_jobs metadata + schema filter (default + `ai_jobs` only) | `7beb279c…af391b44c3eba6dff9f` |
| `backend/alembic/README.md`, `backend/README.md` | module-branch upgrade commands | `a2dfeab8…`, `85a3d3bc…` |
| `backend/tests/integration/ai_jobs/conftest.py` | new — per-test disposable PostgreSQL DB | `c44c3abd…72f04ef1c2804ff61637ccee9b4172a4` |
| `backend/tests/integration/ai_jobs/test_migrations.py` | new — 14 checks | `23b2bffb…c49adf5d1c3c69fc2` |

## Behaviour (plan §6; ADR-0018 D1/D2; Q1/Q7)

- Schema `ai_jobs`, seven tables exactly as §6: `job` (CAS `job_revision`, DATA-25 state check,
  scope/request/progress/failure/policy snapshot/`accepted_fences` JSONB), `attempt` (UNIQUE
  `job_id, attempt_number`; Δ7 `dispatched_at`, `dispatch_count`), `command_receipt` (five-column
  NOT NULL PK), `semantic_request` (PK = canonical `semantic_key_sha256` only; raw columns, nullable
  `session_id` in no unique index), `completion_receipt` (PK `job_id, attempt_id`), `cancellation_notice`
  (`status` only `COMPLETE`), `outbox` (Δ6 lease owner/generation/until; partial UNIQUE `event_id`
  where `kind <> 'dispatch'`; pending index on `available_at`; token-free payload guard).
- No FK into BE1; FKs stay inside `ai_jobs`. No seed rows, users or credentials.
- Alembic: one existing environment, BE1 history unchanged (`20261014_0001…0004`, branch
  `be1_core`); new independent root revision `20261015_ai_0001`, branch `ai_jobs`. Commands:
  `upgrade ai_jobs@head`, `upgrade be1_core@head`, `upgrade heads`. Downgrade `ai_jobs@base` drops
  only this schema (`DROP SCHEMA ai_jobs RESTRICT`), disposable databases only.
- Mapping choices to confirm in B3 (no semantic change): `policy_snapshot_id` + `policy_snapshot`
  JSONB hold the job's retry policy; `history` JSONB holds the domain history; sweep indexes for
  Δ10/Δ11 queries are partial indexes.

## Checks actually run (local Windows, worktree source, PYTHONPATH/MYPYPATH pinned)

Receipts: ignored `evidence/local/b2-local-checks-20261015/run1_*`. Python 3.12.10, SQLAlchemy
2.0.52, Alembic 1.19.1, psycopg 3.3.4 (local venv; Studio has 2.1.4/1.20.0/3.3.6).

| Check | Result |
|---|---|
| B2 tests `backend/tests/integration/ai_jobs` | 6 passed (offline: script graph keeps BE1 chain + independent `ai_jobs` head; plain `head` refused; metadata scoped to `ai_jobs`; semantic key only; command/completion keys; offline upgrade/downgrade SQL touches only `ai_jobs`), **8 skipped = NOT_RUN** (PostgreSQL) |
| Phase A suites (6 files) | 223 passed, 1 skipped (known Pillow live-route skip on this Windows venv) |
| ruff check / format on B2 files; mypy on B2 files | exit 0 / 5 files formatted / no issues |
| ruff on `backend/alembic/env.py` | exit 1: one I001 import-order finding that already exists at `993a26c` (BE1 file; not reordered) |
| `alembic heads` (offline) | `20261014_0004 (be1_core)` and `20261015_ai_0001 (ai_jobs)` |
| harness `--feature`, architecture, security, skeleton, `git diff --check` | all exit 0 |
| Phase A 24-path snapshot | unchanged; only the recorded EOF-disposition hash differs |

## PostgreSQL checks — NOT_RUN, exact Studio procedure

No remote execution access exists from this session. On `sketch2life-backend-test`: upload
`b2_source.patch` and `b2_source.sha256` (feature `evidence/local/b2-studio-package-20261015/`)
to `$HOME/be2-b2-package/`, then run `run_b2_on_studio.sh` from the same folder. It verifies branch,
HEAD `993a26c`, a clean tracked tree and both hashes, applies the patch, re-checks file hashes and
runs, in the existing `sketch2life-be2-venv312` runner on `sketch2life-be2-net`:
`pytest backend/tests/integration/ai_jobs -rs -v` (each test creates and drops its own
`be2_b2_<random>` database; `be2_synthetic` and service volumes are untouched) and the six Phase A
suites. Outputs go to the Studio's ignored `evidence/local/b2-postgres-20261015/`; the password is
read from the read-only private-file mount and never printed.

PostgreSQL checks waiting for that run (B-01 schema level, B-07, B-11 / B2 exit): fresh `upgrade
heads`; existing `be1_core` database then `ai_jobs@head` with BE1 schema snapshot unchanged; rerun
no-op; `downgrade ai_jobs@base` removes only `ai_jobs` then re-upgrade; migration ↔ `tables.py`
parity (`compare_metadata` + CHECK names); introspected PK/UNIQUE/partial index/FK targets and
NULL `session_id` semantics; constraint rejections (state, revision, attempt number, semantic key,
command key, completion key, notice status, outbox event id/identity/lease/token guard);
committed rows read back through a new engine.

## Risks and open items (no B3 work started)

- **Plain `alembic upgrade head` now fails** ("Multiple head revisions") because the module branches
  are independent. It fails before changing the database. BE1 docs in `backend/README.md` and
  `backend/alembic/README.md` now use `be1_core@head` (same effect as before for BE1). BE1 (P2) and
  P4 procedures that say `upgrade head` (FEAT-046/047 evidence) need the same change; flagged, not
  edited.
- B-01 here is schema-level only (rows survive new connections); restart/crash recovery is B6.
- Real P2 adapters/integration stay B-12; no durability, recovery or conformance claim.
