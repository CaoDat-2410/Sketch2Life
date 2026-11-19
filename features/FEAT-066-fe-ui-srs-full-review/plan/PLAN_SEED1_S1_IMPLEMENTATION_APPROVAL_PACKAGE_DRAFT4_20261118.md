# FEAT-066 SEED-1 — S1 core-data seed: implementation approval package (Draft 4)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package proposes a bounded implementation slice. It authorizes no script, database, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Supersedes:** Draft 3 (20,100 B, `FE732B49…`). Draft 4 changes only the seven P3 notes of round 3. Review rounds so far:
  - Round 1, on Draft 1: NOT READY with 0 P1, 4 P2 and 6 P3. Record: `evidence/notes/SEED_1_COLD_REVIEW_DRAFT1_20261118.md`.
  - Round 2, on Draft 2: NOT READY with 0 P1, 2 P2 and 6 P3. Record: `evidence/notes/SEED_1_COLD_REVIEW_DRAFT2_R2_20261118.md`. The repeat-class condition was met, and the owner chose "Draft 3 + round 3, keep SQL" (2026-11-18).
  - Round 3, on Draft 3: **READY WITH NOTES** with 0 P1, 0 P2 and 7 P3. Record: `evidence/notes/SEED_1_COLD_REVIEW_DRAFT3_R3_20261118.md`.
  - §9 maps the round-1 findings to their fixes, §10 round 2, and §11 round 3.
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

- **S1 is core data, written by direct SQL.** It needs only the current schema, after `upgrade heads`. The repository has several Alembic heads; the S1 tables come from the revisions `20261110_ar_0001`, `20261028_ll_0001`, `20261109_m2_parent_profiles` and `20261112_parent_story_context`, among others.
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
- **Principal reference columns** hold the adult's **subject**, not the account UUID. That covers `access_grants.audience_ref` for PRINCIPAL, `parent_principal_ref`, `created_by`, `granted_by` and `invited_by`, as the product writes them (`service.py:1394`, `:1551`, `:1683`, `:1781`). The only column that holds the Parent's `be1_adult_identities.account_id` is `story.runs.active_owner_parent_account_id`.
- **Class profiles** (`be1_managed_profiles`):
  - `data_origin = 'SYNTHETIC_DEV'`, with `consent_id` and `consent_purpose_ref` NULL (the ORM default is `REAL`, so it is always set explicitly);
  - `age_source = SYNTHETIC_FIXTURE`;
  - ages between 36 and 120 months.
- **Parent profiles:** `revision_hash` from the domain snapshot function (`domain/parent_profiles.py:54`). `child_profiles` and `profile_revisions` are written in the same transaction, because of a deferred circular FK.
- **Lessons** (Core `Table` objects in `infrastructure/lesson_library/tables.py`):
  - `structured_content_hash` from `canonical_content_hash` (`domain/lesson_library/model.py:16`);
  - content that validates against **both** `validate_content` (`model.py:21–47`) and the wider `LessonContentInputV1` (`contracts/schemas/lesson_library.py:29–43`). That means it includes `drawing_steps_text`, `subject_learning_notes`, an `activity_kind` of `outdoor`, `indoor` or `mixed`, and `target_age_band_version` of at least 1;
  - stored the way the product writer stores it:
    - `content_json` holds the content **without** the `activities` key (`service.py:350`);
    - `structured_content_hash` is computed over the **full** content, including activities (`:351`);
    - the activities go to `lesson.version_activities` with `activity_order` starting at 1;
  - `target_age_band_ref` is a fixed placeholder band ref in `data.py`, because the bands are still open (D-171 item 6, Q-05);
  - `internal_visibility` is `PRIVATE` or `SCHOOL`;
  - a PUBLIC grant sets the bound version's `review_state` to `PENDING_REVIEW`.
- **Lesson visibility:**
  - `data.py` holds a **pure** re-derivation of the product rule in `_recalculate_visibility` (`service.py:1280–1309`):
    1. A grant counts only if its `state` is `ACTIVE` **and** its `expires_at` is NULL or later than now.
    2. If any counted grant is `PUBLIC`, the value is `PUBLIC`.
    3. Otherwise, if any is `PRINCIPAL` or `PARENT_GROUP`, the value is `SELECTED_AUDIENCE`.
    4. Otherwise, if any is `ORGANIZATION`, the value is `SCHOOL`.
    5. Otherwise the value is the lesson's own `internal_visibility`.
  - Seeded grants have `expires_at` NULL, so the result does not depend on time.
  - Expected values: **L1 `SCHOOL`** (GR1 is ACTIVE ORGANIZATION), **L2 `PRIVATE`** (its only grant, GR3, is REVOKED; `internal_visibility` PRIVATE), **L3 `SCHOOL`** (GR4 is PENDING_REVIEW; `internal_visibility` SCHOOL).
  - The writer inserts these values. It does **not** call the product method.
  - Owner-run test 7 builds `LessonLibraryService` with the guarded session and stub storage, parser and scanner ports (the constructor only stores them, `service.py:96–107`). It calls `_recalculate_visibility` for L1–L3, asserts each value is unchanged, and then **rolls back**, because the method also rewrites `updated_at`.
- **Seeded lesson tables:** `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities` (the activities each version's content declares, as the product writer creates them) and `lesson.access_grants`.
- **Not seeded:**
  - `lesson.library_source_documents` and `lesson.library_document_revisions` (many NOT NULL columns, and a unique `upload_session_id`). **This departs from the design §4.1 lesson row**, which names them. The departure is recorded in the decision row at approval;
  - `parent.command_receipts` and `story.command_receipts`: they record HTTP command replays, and S1 writes no commands. **This also departs from the design** (§4.1 Parent and StoryRun rows name "related receipts"). It is recorded in the decision row with the source-document departure;
  - consent records;
  - sessions;
  - eligibility proofs.
- **StoryRuns** (Core tables `story_runs` and `run_inputs` in `infrastructure/story_run_lite/tables.py`). Each run is written as the product create path writes it (`parent_story_repository.py:90–148`). Later states are then set on the same row.

  **`story.runs`:**

  | Column | Value |
  |---|---|
  | `run_id` | UUIDv5 string; the Parent routes take `run_id: UUID`. This is an exception to the `seed-` text-ID rule |
  | `actor_scope_kind` | `PARENT_ACCOUNT` |
  | `actor_scope_ref` | SHA-256 of the canonical JSON of the Parent's issuer and subject, the same as `_principal_scope_ref` (`:1654–1656`) |
  | `profile_ref` | The `parent.child_profiles` ID, as a UUID string (`get_run` parses it as a UUID) |
  | `child_age_months` | The profile's age, 36–120. This column is on `story.runs` |
  | `run_state` | As in the data set: `COMPLETED`, `FAILED`, `DELETE_PENDING`, `INPUT_PROCESSING` or `PREPARATION_REVIEW` |
  | `revision`, `version` | 1, 1 (`ck_story_run_versions` requires values above 0) |
  | `retryable` | false |
  | `active_owner_parent_account_id` | The Parent's `be1_adult_identities.account_id`, **only** on the single active run of that account (`INPUT_PROCESSING` or `PREPARATION_REVIEW`). NULL on `COMPLETED`, `FAILED` and `DELETE_PENDING` (`uq_story_run_active_parent`; repository lines 407 and 1237) |
  | `current_input_revision` | **1** on every run. When it is NULL, `get_run` raises 409 `PARENT_STORY_CONTEXT_UNAVAILABLE` (`:1555–1557`) |
  | Every other nullable column | NULL. `job_state`, `asset_ref`, understanding and provider fields stay empty, so no asset or understanding rows are needed |

  **`story.run_inputs`**, one row per run, with `input_revision = 1` and a UUIDv5 `run_input_id`:

  | Column | Value |
  |---|---|
  | `source_profile_revision_ref` | The profile's current `parent.profile_revisions.profile_revision_id` (a UUID string) |
  | `context_revision` | 1 |
  | `context_snapshot` | The product shape: `schema_version` = `sketch2life.parent-context.v1`, `profile_revision_ref`, `age_months`, `interests_summary`, `topic`, `adult_confirmed_idea` (`:91–99`) |
  | `context_snapshot_sha256` | The SHA-256 of the same canonical JSON that `_sha256_json` uses (`:1643–1644`). It is re-implemented in `data.py`, and a unit test compares it with the private function |
  | `typed_idea`, `idea_source` | Both NULL, or a synthetic idea with `TEXT`. When set, `typed_idea` equals the snapshot's non-empty `adult_confirmed_idea` |
  | Asset columns | All NULL, which satisfies `ck_story_run_input_versions`, `_hashes` and `_sizes` |
  | `lesson_pin_snapshot`, `lesson_pin_snapshot_sha256` | **SQL NULL**, never an explicit JSON null. A JSON null violates the CHECK (comment at `:135–136`) |
  | `context_confirmed_by`, `context_confirmed_at` | Both NULL |

  **Seeded runs are static and display-only.** They are readable through `get_run` in every state, but they cannot advance.
  - A seeded `PREPARATION_REVIEW` run has no understanding row or SUBJECT review decision, which the product writes on the way to that state. `reserve_story_revision` would refuse it.
  - The `FAILED` run carries `job_state = FAILED` and a synthetic `error_code` (for example `SEED_SYNTHETIC_FAILURE`), as the product sets both on failure.
  - Flows that need a live run create their own through the product.

  **Stop rule:** if the implementer finds any further required row or column, the task stops for a scope amendment.

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
| 5 | `backend/tests/unit/test_seed_guard.py` | New: every refusal case of §3.1, including ports 5432 and 5433. Each case asserts that the output holds no URL fragment. Environment changes use `monkeypatch.setenv`, and the `get_settings()` and `get_core_database_settings()` caches are cleared on teardown, so nothing leaks into other tests and the worktree `.env` is never read |
| 6 | `backend/tests/unit/test_seed_data.py` | New, pure and without a database: ID length within 36; markers; UUIDv5 determinism; ages 36–120; `SYNTHETIC_DEV` with no consent; **one active run per Parent account**; every run has a `run_inputs` row at its `current_input_revision`; the expected visibility L1 `SCHOOL`, L2 `PRIVATE`, L3 `SCHOOL`; scope-ref parity with `_principal_scope_ref`; context-hash parity with `_sha256_json`; the content hash through `canonical_content_hash` |
| 7 | `backend/tests/integration/test_seed_s1_postgres.py` | New, owner-run. Steps:<ol><li>call the guard first, and **skip when `S2L_SEED_DATABASE_URL` is unset**;</li><li>run S1 twice;</li><li>check zero new rows and `EXPECTED_COUNTS`;</li><li>check `_recalculate_visibility` parity, then roll back;</li><li>**read every seeded run back through `SqlParentStoryRunRepository.get_run`**, as its Parent principal, and validate each record through `ParentStoryRunResponseV1`.</li></ol> |
| 8 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S1_<date>.md` | New: runbook |
| 9 | `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/SEED_1_IMPLEMENTATION_EVIDENCE_<date>.md` | New: evidence note, written by the coordinator |

**Governance records**, outside the code allowlist: the decision row in `DECISIONS.md`, the Task Approval entry, and the `STATUS.md` and `CONTEXT.md` entries. The coordinator writes them, append-only, on the owner's word. They go into the same task commit as the code.

- **Imports, read-only:**
  - the `be1` and `parent` ORM models;
  - the lesson and story Core tables;
  - `canonical_content_hash` and `validate_content`;
  - the Parent snapshot hash;
  - in the guard: `get_settings` and `get_core_database_settings`;
  - in tests 6 and 7 only: `_principal_scope_ref`, `_sha256_json`, `LessonLibraryService`, `SqlParentStoryRunRepository`, `VerifiedPrincipal` (`application/ports/identity.py`), the storage, parser and scanner port types used for stubs, and `ParentStoryRunResponseV1`.

  A change to any product module stops the task for an owner scope amendment.
- **Naming cautions:** the security validator rejects a path containing `seed` together with `account`, `credential` or `user`. It also rejects UPPER-case names containing TOKEN, SECRET, PASSWORD, API_KEY or PRIVATE_KEY. Test URLs use placeholder credentials.

## 5. Verification and command ceiling

**Coordinator or Codex, without a database.** The shell is PowerShell; each command names its working directory.

| # | Working directory | Command |
|---|---|---|
| 1 | `backend/` | `ruff check tools/seed tests/unit/test_seed_guard.py tests/unit/test_seed_data.py tests/integration/test_seed_s1_postgres.py` |
| 2 | `backend/` | Set the environment variable `MYPYPATH` to `src` for the session (PowerShell env-drive syntax), then run `mypy --explicit-package-bases tools/seed` |
| 3 | `backend/` | `pytest tests/unit/test_seed_guard.py tests/unit/test_seed_data.py`. `pyproject.toml` already sets `pythonpath = ["src"]` |
| 4 | repository root | `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py` and `python tools/validate_skeleton.py` (a new directory) |
| 5 | repository root | `git add -N` on the **nine task paths of §4 only**, named explicitly, then `git diff --check`. The intent-to-add entries make the new files visible to the check. They stay in the index as intent-to-add until the task commit, and no other untracked file is added |

**mypy pass criterion:** no errors reported in `tools/seed`. Errors in product modules that already existed at the base are the baseline, and are recorded, not fixed.

**Owner-run in their own terminal, against the seed database only.** The database name contains `seed`, the port is neither 5432 nor 5433, and the name is never `be1_acceptance` or `sketch2life_m2_s1a`.
1. Set `S1A_P_ALEMBIC_DATABASE_URL` **explicitly** to the seed URL, because `env.py:98–103` otherwise falls back to other settings. Then run `alembic upgrade heads` on the **fresh** seed database.
2. S1 run 1, then S1 run 2, then the counts.
3. Test 7.

**Runbook notes:**
- **never `upgrade` an already seeded database**, because migration `20261112_parent_story_context` raises when `story.runs` is not empty. Re-seed instead: drop and recreate;
- the runbook gives the PowerShell form of every environment variable.

**Evidence:** counts before and after run 2, exit codes and log hashes, with no URL. Then an independent evidence review on Sonnet 5.5 at high effort. Then one task commit on the local branch, on the owner's word, with no push.

## 6. Acceptance

- The guard refuses each case in §3.1, without printing any part of the URL.
- Run 1 creates exactly `EXPECTED_COUNTS`. Run 2 creates zero rows.
- Test 6 passes, and test 7 passes against the seed database, including `_recalculate_visibility` parity.
- The diff contains no secret (security validator plus a manual search).
- **Deferred:** "each role can open its main FE screen with data" waits for SD-5 (adult sign-in).

## 7. Not verified

- Whether a database trigger or later migration adds CHECKs on `story.runs` beyond those read.
- Runtime behaviour of any command; nothing was run.

## 8. Owner decisions (answered 2026-11-18; the owner's words are quoted below)

| ID | Answer |
|---|---|
| SD-1 | S1 only; S2–S4 later (Billing frozen) |
| SD-2 | `backend/tools/seed/` |
| SD-3 | A separate database whose name contains `seed`, on a loopback port other than 5432 or 5433, prepared by the owner. **Enforced by the guard** (§3.1 b) |
| SD-4 | A local branch `feature/feat066-seed1`, cut from the tip of the queue when the slot opens. The base is re-pinned then |
| SD-5 | Adult sign-in deferred until before the FE slices. The FE-screen acceptance is deferred with it. **Coupling:** the seeded adults' issuer is fixed in `data.py`, and the seeded `actor_scope_ref` and the Parent guard (`identity.issuer == principal.issuer`) depend on it. Whatever sign-in SD-5 chooses must present that same issuer |

The owner's words (chat, 2026-11-18) were "SD-1 đến SD-5 theo đề xuất". They are recorded as a decision row when the package is approved.

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

## 10. Round-2 findings and their fixes

| Finding | Fixed in |
|---|---|
| S2R-01 (P2) | §3.2 lesson visibility: the exact product rule (ACTIVE and not expired; PUBLIC, then PRINCIPAL or PARENT_GROUP, then ORGANIZATION; otherwise `internal_visibility`); seeded `expires_at` NULL; expected values L1 `SCHOOL`, L2 `PRIVATE`, L3 `SCHOOL`; test 7 parity with rollback |
| S2R-02 (P2) | §3.2 StoryRuns: full column tables for `story.runs` and `run_inputs`, as the product create path writes them; test 6 checks the input row at `current_input_revision`; test 7 reads every run back through `get_run` |
| S2R-03 | §3.2 principal reference columns hold the subject |
| S2R-04 | §5 command table with working directory and PowerShell form; mypy pass criterion; `git add -N` before `git diff --check` |
| S2R-05 | §2 Alembic wording; §5 step 1 sets `S1A_P_ALEMBIC_DATABASE_URL` explicitly |
| S2R-06 | Test 5 isolation with `monkeypatch` and cache clearing; test 7 rollback; the §7 item resolved and removed |
| S2R-07 | §3.2 seeded and not-seeded tables (`version_activities` seeded; command receipts not seeded; the source-document exclusion marked as a design departure); §4 governance records |
| S2R-08 | §8 heading in English; the owner's quote kept verbatim in the body |

## 11. Round-3 findings and their fixes (P3 only)

| Finding | Fixed in |
|---|---|
| S3R-01 | §3.2 StoryRuns: line cites corrected (`_sha256_json` at `:1643–1644`, the JSON-null comment at `:135–136`) |
| S3R-02 | §3.2 lessons: content validates against `validate_content` and `LessonContentInputV1`; storage rules for `content_json`, the hash and `activity_order` |
| S3R-03 | §3.2 not seeded: the command-receipt exclusions are marked as design departures |
| S3R-04 | §4 imports completed |
| S3R-05 | §5 row 5: `git add -N` on the nine explicit task paths only |
| S3R-06 | §3.2 StoryRuns: static, display-only runs; `FAILED` carries `job_state` and `error_code`; `typed_idea` equality; test 7 validates through `ParentStoryRunResponseV1` |
| S3R-07 | §8 SD-5: the issuer coupling |
