# FEAT-066 SEED-1 — S1 core-data seed: implementation approval package (Draft 1)

- **Status:** DRAFT / NOT REVIEWED / NOT APPROVED / NOT LAUNCHED. This package proposes a bounded implementation slice. It authorizes no script, database, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Place in the plan:**
  - Phase B, BE queue slot 3. The queue is CONV-1 → FR-C-08 → SEED-1 → Billing B-1.
  - This document may be written and reviewed now. The code waits for its queue slot.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Seed design | `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT6_20261118.md`, 28,192 B, `CABC4BCA…` (Draft 5 round 4: READY WITH NOTES 0/0/4; Draft 6 fixes those four P3s, not re-reviewed by owner instruction) |
| Working SRS (D-209) | 701,157 B, `B9B1F42D…`: §24.1 (synthetic data only), §9.7 consent row, §23.1 |
| Owner decisions | D-066-65 (O-SEED: all four roles); D-171 items used by the design |
| Source base | To be fixed at the implementation base (see SD-4). The design was written against `dev` `1c9148e8` plus M2 |

## 2. Why only S1 now

The design has four stages.
- **S1** is core data, written by direct SQL. It needs only the current schema.
- **S2 to S4** need Billing B-1 to B-5, O-SEED-PAY and O-SEED-CLOCK, and none of those exist yet.

SEED-1 is therefore **S1 only**, together with the guard, the data module, the count queries and the runbook (owner decision SD-1). S2, S3 and S4 become SEED-2, SEED-3 and SEED-4, after their Billing slices.

What S1 alone gives:
- every role's read flows, with synthetic data: Platform Admin, School Manager for organizations A–H, Teachers (including the unassigned candidate and the no-organization case), classes, class profiles, Parents P1–P3 with profiles K1–K3, Parent groups, lessons L1–L3 with grants GR1–GR4, and StoryRuns;
- all organizations, still without Billing state.

## 3. Proposed scope (from the design, S1 rows only)

1. **Guard** (design §2 rule 3), complete:
   - checks run before settings are read;
   - database-name and loopback rules;
   - any query string, `PG*` variable or alternate URL variable is refused;
   - process `SKETCH2LIFE_DATABASE_URL` is set and the settings caches are cleared;
   - the resolved env must be local or test;
   - every engine is created with the explicit URL;
   - live server-side checks (`current_database()`, `inet_server_port()`, a loopback `inet_server_addr()`, `current_user` as database owner);
   - the URL is never printed;
   - entry modules are never imported.

   The seed never creates, drops or migrates a database.
2. **Markers** (rule 4): `seed-` IDs within 36 characters, a `[SEED]` name prefix, UUIDv5 from one namespace, and the column rules taken from source. The column rules cover:
   - lesson `review_state`, with derived `visibility` computed through `_recalculate_visibility`;
   - `internal_visibility`;
   - `account_role` with `role_revision = 1`;
   - `revision_hash` computed through the domain snapshot function;
   - `age_source = SYNTHETIC_FIXTURE`.

   Eligibility proofs are not seeded.
3. **Idempotency** (rule 5): insert-if-absent on stable IDs, never `ON CONFLICT DO UPDATE`. A second run reports zero new rows.
4. **S1 data set** (design §4.1), with no Billing rows, consent records or sessions.
5. **Count queries:** one per seeded table, printed as a table of counts, with no row contents.
6. **Runbook**, under the feature's `evidence/` or `plan/` (SD-2):
   - create the seed database and run `upgrade heads` with `S1A_P_ALEMBIC_DATABASE_URL` unset;
   - run S1, and run it again to prove idempotency;
   - run the counts;
   - re-seed.

**Out of scope:**
- S2 to S4, and Billing anything;
- consent records and classroom or device sessions;
- a Bruno environment (that needs O-TOKEN);
- FE sign-in for seeded adults (open point, §6);
- any product source change;
- any migration.

## 4. Proposed allowlist (location per SD-2; option A shown)

| # | File | Note |
|---|---|---|
| 1 | `backend/tools/seed/__init__.py` | New, empty |
| 2 | `backend/tools/seed/guard.py` | New: rule 3 |
| 3 | `backend/tools/seed/data.py` | New: the keys, the IDs, the UUIDv5 namespace and the S1 rows as data |
| 4 | `backend/tools/seed/s1_core.py` | New: insert-if-absent writer and counts. Invoked as `python -m tools.seed.s1_core` from `backend/` |
| 5 | `backend/tests/unit/test_seed_guard.py` | New: every refusal case of rule 3, without a database |
| 6 | `backend/tests/unit/test_seed_data.py` | New: ID length within 36, marker rules, UUIDv5 determinism, age range 36–120, one active run per Parent profile, grant and visibility consistency (with `_recalculate_visibility`) |
| 7 | `backend/tests/integration/test_seed_s1_postgres.py` | New: run twice against the seed database, then zero new rows and counts as documented. Owner-run |
| 8 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S1_<date>.md` | New: the runbook |

The seed imports product modules read-only: ORM models, `_recalculate_visibility` and the snapshot hash function. If any product module must change, the task stops for an owner scope amendment.

## 5. Verification and command ceiling

- **Coordinator or Codex, without a database:**
  - `ruff` and `mypy` on files 1–4;
  - unit tests 5 and 6;
  - the repository validators;
  - `git diff --check`.
- **Owner-run in their own terminal, against the seed database only:**
  1. `upgrade heads`.
  2. S1 run 1, S1 run 2 and the counts.
  3. Test 7.

  The database name must contain `seed`. It must not be `be1_acceptance` or `sketch2life_m2_s1a`, and it must not use ports 5432 or 5433 (SD-3).
- **Evidence:** counts before and after run 2, exit codes and log hashes, with no URL. Then an independent evidence review on Sonnet 5.5 at high effort. Then one task commit on the owner's word.

## 6. Owner decisions needed

| ID | Question | Recommendation |
|---|---|---|
| SD-1 | Is SEED-1 S1 only, with S2–S4 as later slices after Billing? | Yes |
| SD-2 | Where does the code live? A: `backend/tools/seed/`, next to `be1_api_smoke.py`. B: a feature folder script, like FEAT-048 `bootstrap_local_pg.py` | A: it imports backend modules and is tested with the backend tests |
| SD-3 | Seed database: a new disposable container or database with a name containing `seed` (for example `s2l_seed`), on a free loopback port that is not 5432 or 5433 (for example 5435) | Yes; the owner prepares it before the owner-run step |
| SD-4 | Implementation base branch. CONV-1 is on the local-only `feature/feat066-conv1`, and FR-C-08 follows it | A local branch `feature/feat066-seed1`, cut from the tip of the queue when the slot opens |
| SD-5 | FE sign-in for seeded adults (the design's open point): a synthetic verifier, or the local Firebase emulator | Defer. S1 is useful to Bruno and the API through the existing synthetic-pilot path. Decide before the FE slices |

**Owner answers (chat, 2026-11-18):** "SD-1 đến SD-5 theo đề xuất". All five follow the recommendation:
- **SD-1:** S1 only.
- **SD-2:** `backend/tools/seed/`.
- **SD-3:** a separate database whose name contains `seed`, on a loopback port other than 5432 or 5433, prepared by the owner.
- **SD-4:** a local branch `feature/feat066-seed1` from the tip of the queue.
- **SD-5:** deferred until before the FE slices.

These are recorded as a decision row when the package is approved.

## 7. Not verified

- Whether direct Story inserts need asset or metadata rows (design §8). The implementer checks this first and stops if the rows are not plain inserts.
- Whether `_recalculate_visibility` and the snapshot hash function can be called without an application session.
- The exact table list under the current Alembic heads.

No test, script, database or validator was run for this draft.
