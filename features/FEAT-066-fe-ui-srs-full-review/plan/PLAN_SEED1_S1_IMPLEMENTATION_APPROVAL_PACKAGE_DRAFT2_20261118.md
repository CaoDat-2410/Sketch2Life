# FEAT-066 SEED-1 — S1 core-data seed: implementation approval package (Draft 2)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package proposes a bounded implementation slice. It authorizes no script, database, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Supersedes:** Draft 1 (7,909 B, `3B74E04F…`). Its round-1 cold review was NOT READY with 0 P1, 4 P2 and 6 P3 (`evidence/notes/SEED_1_COLD_REVIEW_DRAFT1_20261118.md`). §9 maps each finding to its fix.
- **Place in the plan:**
  - Phase B, BE queue slot 3, after CONV-1 and FR-C-08.
  - Billing is frozen by the owner (2026-11-18), so only S1 applies.
  - This document may be written and reviewed now. The code waits for its slot.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Seed design | `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT6_20261118.md`, 28,192 B, `CABC4BCA…` (Draft 5 round 4: READY WITH NOTES 0/0/4; Draft 6 fixes those four P3s, not re-reviewed by owner instruction) |
| Working SRS (D-209) | 701,157 B, `B9B1F42D…`: §24.1 (synthetic data only), §9.7 consent row, §23.1 |
| Owner decisions | D-066-65 (O-SEED: all four roles). SD-1 to SD-5 (§8) |
| Source base | Fixed at the implementation base (SD-4). Statements below were checked statically at `08439b22` |

## 2. Scope: S1 only (SD-1)

- **S1 is core data, written by direct SQL.** It needs only the current schema. All S1 tables exist under the current Alembic heads (`20261110_ar_0001`, `20261028_ll_0001`, `20261109_m2_parent_profiles`, `20261112_parent_story_context`).
- **S2 to S4 need Billing**, which is frozen. They become SEED-2 to SEED-4, later.
- **What S1 gives:** synthetic data present for every role:
  - Platform Admin;
  - School Managers for organizations A–H;
  - Teachers, including the unassigned candidate and the no-organization case;
  - classes and class profiles;
  - Parents P1–P3 with profiles K1–K3;
  - Parent groups;
  - lessons L1–L3 with grants GR1–GR4;
  - StoryRuns.
- **Flows become testable** through FE or Bruno only once an adult principal can be authenticated. That is SD-5, deferred. The design's acceptance "each role can open its main FE screen with data" is therefore **deferred with SD-5**, not met by SEED-1.

## 3. Proposed behaviour

### 3.1 Guard (design §2 rule 3, plus the SD-3 delta)

**The seed reads one variable only, `S2L_SEED_DATABASE_URL`.** The following checks run before any settings are read, and all must pass:
- (a) The database name contains `seed`, and contains neither `be1_acceptance` nor `m2_s1a`.
- (b) The URL has an explicit loopback host (`127.0.0.1`, `::1` or `localhost`) and an **explicit port**, and **the port is neither 5432 nor 5433** (the SD-3 delta to the design). It has no query string. None of `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGSERVICE`, `PGSERVICEFILE` or `PGOPTIONS` is set.
- (c) `S1A_P_ALEMBIC_DATABASE_URL` and `STORYRUN_LITE_DATABASE_URL` are unset, or equal to the guarded URL.

**Then:**
- It sets `SKETCH2LIFE_DATABASE_URL` for its own process to the guarded URL and clears the `lru_cache` of `get_settings()` and `get_core_database_settings()`.
- It requires the resolved `settings.env` to be `local` or `test`.
- It creates every engine with the explicit URL.
- **Before any write**, it compares the engine's database name, host and port with the guarded values. It then runs its **own** live check on the server: `current_database()`, `inet_server_port()`, a loopback `inet_server_addr()`, and `current_user` as the database owner. It cannot reuse `verify_goal_database_owner`, which requires a `storyrun_lite_` name.
- **No URL is ever printed.** Every refusal raises a fixed message with `from None`, so URL-parsing and driver errors cannot echo the URL.
- It never imports `main.py`, `classroom_main.py`, `demo_main.py` or `story_run_lite_app.py`.
- It never creates, drops or migrates a database.

### 3.2 Markers and column rules (design §2 rule 4, made exact)

- **IDs:**
  - text IDs are `seed-…`, at most 36 characters;
  - names get a `[SEED]` prefix;
  - UUID columns use UUIDv5 from one fixed namespace, including `be1_adult_identities.account_id`.
- **Adults:** `account_role` (`platform_admin`, `school_manager`, `teacher` or `parent`) with `role_revision = 1`.
- **Class profiles** (`be1_managed_profiles`):
  - `data_origin = 'SYNTHETIC_DEV'`, with `consent_id` and `consent_purpose_ref` NULL (the ORM default is `REAL`, so it is always set explicitly);
  - `age_source = SYNTHETIC_FIXTURE`;
  - ages between 36 and 120 months.
- **Parent profiles:** `revision_hash` from the domain snapshot function (`domain/parent_profiles.py:54`). `child_profiles` and `profile_revisions` are written in the same transaction, because of a deferred circular FK.
- **Lessons** (Core `Table` objects in `infrastructure/lesson_library/tables.py`):
  - `structured_content_hash` from `canonical_content_hash` (`domain/lesson_library/model.py:16`);
  - content shaped and checked with `validate_content` (`model.py:21`);
  - `target_age_band_ref` is a fixed placeholder band ref in `data.py`, because the bands are still open (D-171 item 6, Q-05);
  - `internal_visibility` is `PRIVATE` or `SCHOOL`;
  - a PUBLIC grant sets the bound version's `review_state` to `PENDING_REVIEW`.
- **Lesson visibility:**
  - `data.py` holds a **pure** re-derivation of the product rule: ORGANIZATION → SCHOOL, PRINCIPAL or PARENT_GROUP → SELECTED_AUDIENCE, PUBLIC → PUBLIC, otherwise PRIVATE, from ACTIVE grants only. The writer inserts that value.
  - The product method `_recalculate_visibility` is an instance method of `LessonLibraryService` that queries the database. It is **not** called by the writer. Owner-run test 7 builds the service with the guarded session and stub ports, calls the method for the seeded lessons, and asserts it leaves each value unchanged (parity).
- **Not seeded:**
  - `lesson.library_source_documents` and `lesson.library_document_revisions` (many NOT NULL columns, and a unique `upload_session_id`);
  - consent records;
  - sessions;
  - eligibility proofs.
- **StoryRuns** (Core tables in `infrastructure/story_run_lite/tables.py`):
  - `run_id` is a **UUIDv5** string, because the Parent routes take `run_id: UUID`. This is an exception to the `seed-` text-ID rule.
  - `actor_scope_ref` is the SHA-256 of the canonical JSON of the Parent's issuer and subject, the same derivation as `_principal_scope_ref` (`parent_story_repository.py:1654–1656`). It is re-implemented in `data.py` and compared with the private function in a unit test.
  - `active_owner_parent_account_id` is set **only** on the single active run of each Parent account. It is NULL on COMPLETED, FAILED and DELETE_PENDING runs (the unique index `uq_story_run_active_parent`).
  - `run_inputs` rows satisfy the CHECKs that tie the context snapshot, its hash and `source_profile_revision_ref` together (`tables.py:351–364`). `profile_ref` is the `parent.child_profiles` ID, and `child_age_months` is between 36 and 120.
  - The implementer confirms first whether any further asset or metadata row is required. If it is, the task stops.

### 3.3 Idempotency and atomicity

- Rows are insert-if-absent on stable IDs, never `ON CONFLICT DO UPDATE`.
- **S1 runs as one transaction: all or nothing.** A second run reports zero new rows.

### 3.4 Data set

Design §4.1, S1 rows, as listed in §2 above, with the §3.2 exclusions.

### 3.5 Counts

- One count query per seeded table. The output is a table of counts with no row contents.
- The expected counts live in `data.py` as `EXPECTED_COUNTS`, and test 7 compares against them.

## 4. Proposed allowlist (SD-2: `backend/tools/seed/`)

| # | File | Note |
|---|---|---|
| 1 | `backend/tools/seed/__init__.py` | New, empty |
| 2 | `backend/tools/seed/guard.py` | New: §3.1 |
| 3 | `backend/tools/seed/data.py` | New: keys, IDs, UUIDv5 namespace, S1 rows, the pure visibility rule, the scope-ref derivation, `EXPECTED_COUNTS` |
| 4 | `backend/tools/seed/s1_core.py` | New: the one-transaction insert-if-absent writer and the counts. Invoked as `python -m tools.seed.s1_core` from `backend/` |
| 5 | `backend/tests/unit/test_seed_guard.py` | New: every refusal case of §3.1, including ports 5432 and 5433. Each case asserts that the output holds no URL fragment. Settings are monkeypatched, so the worktree `.env` is never read |
| 6 | `backend/tests/unit/test_seed_data.py` | New, pure and without a database: ID length within 36; markers; UUIDv5 determinism; ages 36–120; `SYNTHETIC_DEV` with no consent; **one active run per Parent account**; the visibility re-derivation for GR1–GR4; scope-ref parity with `_principal_scope_ref`; the content hash through `canonical_content_hash` |
| 7 | `backend/tests/integration/test_seed_s1_postgres.py` | New, owner-run: it calls the guard first and **skips when `S2L_SEED_DATABASE_URL` is unset**; runs S1 twice; checks zero new rows and `EXPECTED_COUNTS`; checks `_recalculate_visibility` parity |
| 8 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S1_<date>.md` | New: runbook |
| 9 | `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/SEED_1_IMPLEMENTATION_EVIDENCE_<date>.md` | New: evidence note, written by the coordinator |

- **Imports, read-only:**
  - the `be1` and `parent` ORM models;
  - the lesson and story Core tables;
  - `canonical_content_hash` and `validate_content`;
  - the Parent snapshot hash;
  - in tests 6 and 7 only, `_principal_scope_ref` and `LessonLibraryService`.

  A change to any product module stops the task for an owner scope amendment.
- **Naming cautions:** the security validator rejects a path containing `seed` together with `account`, `credential` or `user`. It also rejects UPPER-case names containing TOKEN, SECRET, PASSWORD, API_KEY or PRIVATE_KEY. Test URLs use placeholder credentials.

## 5. Verification and command ceiling

**Coordinator or Codex, without a database:**
1. `ruff check backend/tools/seed backend/tests/unit/test_seed_guard.py backend/tests/unit/test_seed_data.py backend/tests/integration/test_seed_s1_postgres.py`
2. `mypy --explicit-package-bases backend/tools/seed`, run from `backend/` with `MYPYPATH=src`, because `tools` is a namespace package.
3. `pytest backend/tests/unit/test_seed_guard.py backend/tests/unit/test_seed_data.py`, with `PYTHONPATH=src`.
4. `python tools/validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py` and `validate_skeleton.py` (a new directory).
5. `git diff --check`.

**Owner-run in their own terminal, against the seed database only.** The database name contains `seed`, the port is neither 5432 nor 5433, and the name is never `be1_acceptance` or `sketch2life_m2_s1a`.
1. `alembic upgrade heads` on the **fresh** seed database, with `S1A_P_ALEMBIC_DATABASE_URL` unset or equal to the seed URL (Alembic reads it first).
2. S1 run 1, then S1 run 2, then the counts.
3. Test 7.

**Runbook notes:**
- use `PYTHONPATH=src`;
- **never `upgrade` an already seeded database**, because migration `20261112_parent_story_context` raises when `story.runs` is not empty. Re-seed instead: drop and recreate.

**Evidence:** counts before and after run 2, exit codes and log hashes, with no URL. Then an independent evidence review on Sonnet 5.5 at high effort. Then one task commit on the local branch, on the owner's word, with no push.

## 6. Acceptance

- The guard refuses each case in §3.1, without printing any part of the URL.
- Run 1 creates exactly `EXPECTED_COUNTS`. Run 2 creates zero rows.
- Test 6 passes, and test 7 passes against the seed database, including `_recalculate_visibility` parity.
- The diff contains no secret (security validator plus a manual search).
- **Deferred:** "each role can open its main FE screen with data" waits for SD-5 (adult sign-in).

## 7. Not verified

- Whether a database trigger or later migration adds CHECKs on `story.runs` beyond those read.
- Whether `LessonLibraryService` can be built with stub storage, parser and scanner ports in test 7.
- Runtime behaviour of any command; nothing was run.

## 8. Owner decisions (answered 2026-11-18: "SD-1 đến SD-5 theo đề xuất")

| ID | Answer |
|---|---|
| SD-1 | S1 only; S2–S4 later (Billing frozen) |
| SD-2 | `backend/tools/seed/` |
| SD-3 | A separate database whose name contains `seed`, on a loopback port other than 5432 or 5433, prepared by the owner. **Enforced by the guard** (§3.1 b) |
| SD-4 | A local branch `feature/feat066-seed1`, cut from the tip of the queue when the slot opens. The base is re-pinned then |
| SD-5 | Adult sign-in deferred until before the FE slices. The FE-screen acceptance is deferred with it |

They are recorded as a decision row when the package is approved.

## 9. Round-1 findings and their fixes

| Finding | Fixed in |
|---|---|
| S1R-01 (P2) | §3.2 lesson visibility (pure re-derivation; product method only in test 7); §4 imports; tests 6 and 7 |
| S1R-02 (P2) | §3.2 StoryRuns; test 6 grain is "one active run per Parent account" |
| S1R-03 (P2) | §3.1 (the single variable named; ports 5432 and 5433 refused); test 7 skips when the variable is unset |
| S1R-04 (P2) | §2 reworded; the FE-screen acceptance deferred with SD-5 (§6, §8) |
| S1R-05 | §3.1: explicit port; alternate variables; engine comparison before writes; fixed messages with `from None`; its own owner SQL |
| S1R-06 | §3.2 class profiles; test 6 |
| S1R-07 | §3.3 one transaction |
| S1R-08 | §3.2 lessons (placeholder band) and "not seeded" |
| S1R-09 | §5 explicit commands and runbook notes |
| S1R-10 | §4 rows 8 and 9; `EXPECTED_COUNTS`; naming cautions; base re-pinned at SD-4 |
