# FEAT-066 SEED-1 — S1 seed runbook (2026-11-19)

Authority: the SEED-1 implementation approval package, Draft 4
(`PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md`), and D-066-77.
This runbook covers S1 only. S2–S4 are out of scope. SEED-7a (package Draft 3) added the Parents P4 and P5 to S1; the command-made runs of S7 item 2a have their own runbook, `SEED_RUNBOOK_S7A_20261119.md`.

## 1. What S1 writes

Synthetic rows only, all in one transaction, insert-if-absent on stable primary keys:

| Table | Rows |
|---|---|
| `be1_organizations` | 8 |
| `be1_adult_identities` | 25 |
| `be1_organization_assignments` | 19 |
| `be1_classrooms` | 41 |
| `be1_managed_profiles` | 52 |
| `be1_enrollments` | 52 |
| `be1_parent_groups` | 2 |
| `be1_parent_group_members` | 3 |
| `parent.child_profiles` | 5 |
| `parent.profile_revisions` | 7 |
| `lesson.library_items` | 3 |
| `lesson.library_versions` | 4 |
| `lesson.version_activities` | 8 |
| `lesson.access_grants` | 4 |
| `story.runs` | 6 |
| `story.run_inputs` | 6 |

`backend/tools/seed/data.py` holds these values as `EXPECTED_COUNTS`. S1 counts only the rows it owns (by primary key), so the rows that S7a adds to `story.runs` and `story.run_inputs` do not change the S1 counts. Text IDs start with
`seed-`; display names start with `[SEED]`; UUID columns are UUIDv5 from one fixed namespace.

## 2. Target database rules (enforced by `tools/seed/guard.py`)

- The only input is `S2L_SEED_DATABASE_URL`. No refusal prints any part of it.
- Scheme `postgresql` or `postgresql+psycopg`; one database name that contains `seed` and does
  not contain `be1_acceptance` or `m2_s1a`.
- Explicit loopback host (`127.0.0.1`, `::1` or `localhost`) and an explicit port that is
  neither 5432 nor 5433. No query string.
- None of `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGSERVICE`, `PGSERVICEFILE` or
  `PGOPTIONS` is set. `S1A_P_ALEMBIC_DATABASE_URL` and `STORYRUN_LITE_DATABASE_URL` are unset or
  equal to the seed URL.
- `settings.env` resolves to `local` or `test`.
- Live check before any write: the server database name equals the guarded name, and the
  connected user owns that database. The host and port are enforced on the client side only
  (D-066-78), because Docker port mapping makes the server report its in-container port and
  interface address.

Never point any step of this runbook at `sketch2life_m2_s1a`, `be1_acceptance`, or ports 5432
and 5433.

## 3. Steps (PowerShell, from `backend/` of the worktree)

**Step 0, interpreter and source tree.** The integration worktree has no virtual environment of its own. The only environment is the root checkout's `backend/.venv`, and its editable install points at the root checkout's `backend/src`, which is a different, older tree. So before every `python -m tools.seed.…` command, set `PYTHONPATH` to this worktree's `backend/src` (for example `$env:PYTHONPATH = (Resolve-Path src).Path`) and run the check `python -c "import sketch2life, tools.seed.guard as g; print(sketch2life.__file__); print(g.__file__)"`. Stop unless both paths are under this worktree. `pytest` does not need this, because `pyproject.toml` sets `pythonpath = ["src"]`.

Set the variables for the session. Type the URL at the prompt; it is not echoed.

```powershell
$secure = Read-Host 'Seed database URL' -AsSecureString
$env:S2L_SEED_DATABASE_URL = [Net.NetworkCredential]::new('', $secure).Password
$env:S1A_P_ALEMBIC_DATABASE_URL = $env:S2L_SEED_DATABASE_URL
$env:SKETCH2LIFE_ENV = 'local'
```

1. Guard only (no write): `python -c "from tools.seed.guard import guarded_engine; e, _ = guarded_engine(); e.dispose()"`.
   Stop if it refuses.
2. Migrations on the **fresh** seed database: `python -m alembic upgrade heads`.
   `S1A_P_ALEMBIC_DATABASE_URL` must be set explicitly, because `alembic/env.py` otherwise
   falls back to other settings.
3. S1 run 1: `python -m tools.seed.s1_core`. The output is a counts table; every row must say
   `ok yes`, and the exit code is 0.
4. S1 run 2: the same command. Every `new` value must be 0.
5. Test 7: `python -m pytest tests/integration/test_seed_s1_postgres.py -q -rA`. Run this file on
   its own, not inside the whole `tests/integration` tree. After FR-C-08 the case `test_runs_read_back_through_the_product[r3]` fails (the S1 `DELETE_PENDING` run is returned as a lifecycle record); design §11.8 owns that case.
6. For S7 item 2a, continue with `SEED_RUNBOOK_S7A_20261119.md`.
7. Clear the variables: `Remove-Item env:S2L_SEED_DATABASE_URL, env:S1A_P_ALEMBIC_DATABASE_URL`.

Exit codes of `tools.seed.s1_core`: 0 counts match; 1 counts differ; 2 guard refused;
3 write or count failed (the message names the table and the constraint, never the URL).

## 4. Re-seeding

- **Never run `alembic upgrade` on a database that is already seeded.** Migration
  `20261112_parent_story_context` raises when `story.runs` is not empty.
- To re-seed, drop and recreate the seed database, then start again at step 1.
- Running S1 again on a database that S1 already seeded at the current data version adds nothing. On a database seeded **before** SEED-7a, the new S1 adds only the P4 and P5 rows (insert-if-absent). That is a convenience, not a tested path: re-seed instead.

## 5. Known limits

- Seeded runs are static and display-only. They can be read through `get_run` in every state,
  but they cannot advance (for example, the `PREPARATION_REVIEW` run has no understanding row).
- Lesson source documents, consent records, sessions and eligibility proofs are not seeded by S1
  (package §3.2). S1 writes no command receipts; S7a adds four (package Draft 3 §3.4).
- The lesson age band ref is a fixed placeholder until the age bands are decided.
- Signing in as a seeded adult needs SD-5 (adult sign-in), which is deferred.
