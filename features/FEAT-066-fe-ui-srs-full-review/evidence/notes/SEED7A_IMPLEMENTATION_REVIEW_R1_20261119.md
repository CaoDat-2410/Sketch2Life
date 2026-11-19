# B3 SEED-7a implementation review, round 1

- **Reviewer:** Sonnet 5.5 (`claude-sonnet-5-5`), high effort (as launched by the coordinating session; the effort level cannot be read back from inside the session).
- **Date:** 2026-11-19. **Mode:** read-only. I edited, staged, committed and pushed nothing, and ran no database, Docker, network or git-write command. `D:\s2l-gate-secrets` was not read. This report is the only file I wrote (plus a mypy cache under `tmp/phase-bc/reviews/`, which I created by running mypy).
- **Target:** worktree `.worktrees/be-integration`, branch `feature/feat066-be-integration`, HEAD `5e20faf7`, uncommitted working-tree diff.
- **Approved package:** `plan/PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT3_20261119.md` (read fully) and its review `B3_SEED7A_PKG_DRAFT3_REVIEW_R3.md` (READY WITH NOTES, six P3 notes).
- **Files read in full:** `tools/seed/{data.py (diff), guard.py, s1_core.py, s7a_runs.py}`, `tests/unit/{test_seed_data.py (diff), test_seed_guard.py (diff and helpers), test_seed_s7a.py}`, `tests/integration/{test_seed_s7a_postgres.py, test_seed_s1_postgres.py}`, both runbooks. Product code read for comparison: `application/services/parent_story_runs.py`, `ports/parent_story_runs.py`, `infrastructure/persistence/parent_story_repository.py` (`create_run`, `confirm_context`, `get_run`, `get_active_run`, helpers), `interfaces/http/routers/parent_story_runs.py:75-84`, `infrastructure/config/settings.py`.

## 1. Verdict

**ACCEPTABLE WITH NOTES. P1 = 0, P2 = 0, P3 = 7** (plus four informational items in section 8).

The implementation matches the approved package on every behaviour I could check without a database. None of the findings changes behaviour or blocks the task commit. The P3 items are test-coverage gaps, one decision-table ordering deviation and runbook wording. The database evidence (coordinator run) I could not re-run, so I treat it as reported and have checked that the code and the tests are consistent with it.

## 2. What I ran (all read-only)

| Check | Result |
|---|---|
| `pytest tests/unit/test_seed_data.py tests/unit/test_seed_guard.py tests/unit/test_seed_s7a.py -q -rs` (PYTHONPATH = integration `backend/src`, root venv interpreter) | **139 tests, all passed, 0 skipped.** `-rs` shows no skip, so the Modal config test ran (Modal 1.6.4 is installed in this venv) |
| `ruff check` (tools/seed + the 6 test files) and `ruff format --check` (9 files) | clean |
| `mypy --explicit-package-bases tools/seed` | no issues in 5 files. I could **not** reproduce the 3 pre-existing `no-untyped-def` errors in `parent_story_repository.py` that the coordinator reported; this is harmless (probably a cache or invocation difference) but the evidence note should quote its own command and output |
| `mypy` on the three test files | 1 error, `tests/unit/test_seed_data.py:230` (`derive_visibility` argument type). That line is **not** in the diff (the diff starts at line 285), so it is pre-existing |
| `python tools/validate_repository_security.py` / `validate_architecture.py` / `validate_harness.py` | `REPOSITORY_SECURITY_VALID` (7,880 files; the validator uses `git ls-files --others`, so the untracked new files were scanned), `ARCHITECTURE_VALID`, `HARNESS_VALID` |
| `git diff --check` | exit 0 |
| Import-graph probe (`python -B -c "import tools.seed.s7a_runs"`) | settings cache `currsize=0` for both `get_settings` and `get_core_database_settings`, and `modal` not in `sys.modules`. So importing the writer reads no settings and imports no Modal client. This settles package §4 and §7 item 2 |
| Byte scan of all 10 changed or new code and runbook files | 0 CR bytes, no BOM, each ends with a newline |

## 3. Q1: behaviour equals the package

| Package item | Verdict | Evidence |
|---|---|---|
| Guard order: `check_s7a_environment`, `guarded_engine`, `check_no_provider` | **Matches** | `s7a_runs.py:260-289`. The environment check and the S1 guard share one `try` that returns 2; `check_no_provider` runs after the engine exists and returns 2 with `engine.dispose()` in the outer `finally`. Importing the writer reads no settings (probe above), so "before any settings are read" holds |
| Fixed messages, no value ever printed | **Matches** | `guard.py:203-247, 250-275`: every refusal is a fixed string raised through `_refuse` with `from None` where a try block precedes it. The only formatted message is `S7A_COMMAND_FAILED_{exc.code}` (`s7a_runs.py:150`), and the codes are fixed repository or service constants. `main()` prints `exc.code` or a fixed string. No URL, ID or content is printed; the output table holds counts and `p4=INPUT_PROCESSING/created` only |
| Environment rules | **Matches** | The four must-be-unset variables, vision mode `loopback` or unset, story mode `disabled` or unset, loopback-only vision URL, no `MODAL_*` except `MODAL_CONFIG_PATH`, `modal` not in `sys.modules`. `STORYRUN_LITE_*` is read straight from `os.environ` in `story_run_lite/composition.py:122-162`, not from `.env`, so an env-only check is sufficient |
| `MODAL_CONFIG_PATH` handling | **Matches, and better than the package** | `guard.py:237-247`: the Modal-imported refusal is evaluated before the scratch directory is made, so a refusal leaves no environment change (the test asserts `MODAL_CONFIG_PATH not in env`). `mkdtemp(dir=<worktree>/tmp/seed7a)` applies package note P3-4 (`tmp/` is git-ignored: `.gitignore:99`). The path is never printed. Modal's `config.py` evaluates `user_config_path = os.environ.get("MODAL_CONFIG_PATH") or ...` at import, so the override is effective, and the subprocess test confirms it against the installed 1.6.4 |
| Decision table rows 1-4 plus state check | **Matches, one ordering deviation** | `s7a_runs.py:119-151`. Row 1 create then confirm, row 2 confirm only, row 3 nothing, row 4 `S7A_FOREIGN_ACTIVE_RUN`. The `isinstance` and `INPUT_PROCESSING` check is `_expect_record` (`:89-94`) and runs on both the created and the active record and again after confirm. See P3-2 for the ordering deviation |
| Three `_require_parent` conditions | **Matches** | `s7a_runs.py:154-164` is line-for-line the route's check (`routers/parent_story_runs.py:75-84`): `state == "active"`, `account_role == "parent"`, issuer equal; same `session.get(AdultIdentityModel, principal.subject)` |
| Principal, service, session | **Matches** | `roles=frozenset()`, `account_id` passed, service built exactly as the route builds it, session from `create_core_session_factory(engine)`; no writer commit (the repository commits) |
| Error mapping | **Matches** | `ParentStoryRunError` and `ParentStoryRunServiceError` both carry `.code`; both are mapped to `S7A_COMMAND_FAILED_<code>` with `from None`. `ParentStoryProfileLookupUnavailable` never escapes, because the service converts it (`parent_story_runs.py:~215`). SQLAlchemy errors map to `S7A_DATABASE_ERROR` |
| S1 key counting, `tuple_ IN` | **Correct** | See section 3.1 |
| `EXPECTED_COUNTS` and `EXPECTED_S7A_COUNTS` | **Match** | 25 / 5 / 7 and 2 / 2 / 4. `adult_rows()` builds parents from `PARENT_SUBJECTS`, so P4 and P5 add exactly two identities; `test_counts_include_p4_and_p5` and the existing `test_counts_match_expected` tie the numbers to the row builders. The parity test `test_scope_ref_parity` is parametrised over `sorted(PARENT_SUBJECTS)`, so it covers P4 and P5 without edits |
| Idempotency | **Matches** | Run 2 takes row 3 for both Parents. The hash check recomputes the canonical SHA-256 of the stored snapshot and compares it with the stored hash; `data.sha256_json` is the same encoding as `_sha256_json` (`ensure_ascii=False`, sorted keys, compact separators). Replay after a partial first run is row 2 |
| Seed S7a rows | **Correct** | `create_run` writes `story.runs`, `story.run_inputs` and one `CREATE_RUN` receipt; `confirm_context` writes one `CONFIRM_CONTEXT` receipt (`resource_ref` = run id, `String(36)` FK). Nothing else is written |

### 3.1 S1-scoped counting (`s1_core.py:101-113`)

- `sa.tuple_(*key_columns).in_(keys)` is correct for composite keys, and for single-column keys it renders `(col) IN ((v1), (v2), ...)`, which PostgreSQL accepts. The coordinator's run (16 of 16 `ok`, run 2 adds 0) is consistent with this.
- **Scale:** the largest S1 table has 52 rows, so the statement carries at most 52 key tuples; the PostgreSQL and psycopg parameter limits are not close.
- **NULL:** primary-key columns cannot be NULL, so tuple comparison cannot hit three-valued logic. An empty key list cannot occur (every step has rows).
- **Precondition:** `row[column.name]` needs every step's row dictionaries to carry each primary-key column under its column name. This holds today (the same dictionaries feed `_insert_if_absent`) but nothing tests it. See P3-6.
- **Consequence to know:** S1 totals no longer detect extra non-S1 rows in an S1 table. This is the design choice the package approved (F-01) and `test_counts_in_the_database` (T5) proves the property that matters: with the S7a rows present, `count_rows == EXPECTED_COUNTS`, which would fail (`story.runs` 8, not 6) under whole-table counting.

## 4. Q2: tests

| Test | Does it assert what the package says, and can it fail? |
|---|---|
| T1 `test_seed_data.py` (4 new tests) | Yes. Markers, ages inside 36-120, one revision each, no S1 run for P4 or P5, the three new counts, the S7a spec and key shapes. Synthetic origin and no-consent are already covered for every profile by the existing tests at `test_seed_data.py:118-119, 164`. Gap: the package also lists "the S1 key sets used for counting"; nothing checks them (P3-6) |
| T2 `test_seed_guard.py` | Non-vacuous. Each refusal test passes a value fragment and `_assert_refused` (`:37-52`) checks the message, `__cause__`, `__suppress_context__` and captured output for it. For `STORYRUN_LITE_VISION_MODE="modal"` the fragment `modal` is absent from the fixed message, so the check can fail. The accept test checks that the file does not exist and that its parent's parent is the scratch root. The `SimpleNamespace` settings in the provider tests use attribute names I confirmed against the real `Settings` (`settings.py:35-78`). Gaps: P3-1 and P3-3 |
| T3 `test_seed_s7a.py` | Rows 1-4, the tampered hash, the lifecycle and other-state cases (both after create and in the table), an unconfirmed result after confirm, and both error types on create and confirm. Call-order assertions (`service.calls == [...]`) make them real. The fake accepts only the exact seed idempotency keys, topics and ideas. It is faithful to the service signature (keyword-only, same names). The record carries a hand-made three-key snapshot, which is fine because the writer only reads `topic`, `adult_confirmed_idea` and the hash. Gaps: P3-2, P3-4 |
| T4 `test_seed_s1_postgres.py` | **Not edited** although allowlist row 8 reserves it. No edit was needed: it already calls `count_rows`, which is now scoped. The S1-scoped property is exercised by T5, not by T4 (see P3-6 and section 8) |
| T5 `test_seed_s7a_postgres.py` | Matches package row 9. S1 and S7a run as **subprocesses** (`python -m tools.seed.…`), which isolates the Modal-import and environment checks from pytest and applies package note P3-5; skips when `S2L_SEED_DATABASE_URL` is unset. First run asserts `new in {0, expected}` and total equal expected, second run asserts new 0 and total equal expected (`:100-110`), as `test_seed_s1_postgres.py:75-76` does for S1. It then reads P4 and P5 through the product repository, requires a `ParentStoryRunRecord` in `INPUT_PROCESSING` with `context_confirmed is True`, validates through `ParentStoryRunResponseV1`, and checks the topic and idea. It also re-reads the S1 runs by state. I could not run it (no database). The output regex matches the writer's table format (`format_s7a`), and the `runs` fixture restores `SKETCH2LIFE_DATABASE_URL` and clears both settings caches, as T4 does |

**Env and module leakage:** every environment test in T2 passes its own `env` dictionary and `modules={}`, so nothing touches `os.environ` or `sys.modules`; T5 never imports the guards in-process. The single leak is `pytest.importorskip("modal")` (P3-3).

## 5. Q3: allowlist

`git status` shows exactly these code and doc paths changed or new: `data.py`, `guard.py`, `s1_core.py`, `s7a_runs.py`, `test_seed_data.py`, `test_seed_guard.py`, `test_seed_s7a.py`, `test_seed_s7a_postgres.py`, `SEED_RUNBOOK_S1_20261119.md` (edited), `SEED_RUNBOOK_S7A_20261119.md` (new). That is rows 1-7, 9, 10 and 11. Row 8 (`test_seed_s1_postgres.py`) is unchanged, which is within the allowlist (an allowed edit that was not needed). Row 12 (the evidence note) does not exist yet and is the coordinator's. No product module, no `pyproject.toml`, no migration and no other seed file changed. The remaining untracked paths are the deferred BRU-0a files (ignored as instructed) and the package Draft 3 file itself (its location is a commit-plan matter, review R3 P3-2).

## 6. Q4: secrets, URLs, paths, bytes, names

- **Secrets and URLs:** no refusal or error path prints a value. Test placeholders are the literals `placeholder-*` and `https://placeholder.invalid`. No real host, credential or token appears in the diff.
- **Absolute machine paths:** none in the changed files. (My first scan flagged `://` patterns in connection-string f-strings in `test_seed_guard.py`; those are placeholders, not machine paths.) The runbooks use relative paths only (`tmp/seed7a/`).
- **CR and BOM:** none (section 2).
- **UPPER-case names:** no assignment target contains TOKEN, SECRET, PASSWORD, API_KEY or PRIVATE_KEY. The variable names `STORYRUN_LITE_MODAL_TOKEN` and similar appear as string literals: in `guard.py:189-194` inside the tuple `_S7A_MUST_BE_UNSET`, and in the tests as dictionary keys. The package §4 said they "appear only as string literals in a lower-case tuple"; the tuple name here is upper-case (`_S7A_MUST_BE_UNSET`). The repository validator's pattern (`validate_repository_security.py:28`) only matches an assignment whose **name** contains those words, and the validator passes on these files, so this is not a defect. It is a small wording deviation from the package.

## 7. Q5: runbooks against the code

`SEED_RUNBOOK_S7A_20261119.md` is accurate on: the three tables and counts; the guard order; the exit codes 0/1/2/3 (`main()` returns exactly these); the output line (`runs: p4=INPUT_PROCESSING/created, …` then `kept`); the scratch path under `tmp/seed7a/` (git-ignored); the re-seed and never-upgrade rule; the FR-C-08 command ban; the non-atomic-per-Parent and wall-clock notes; the known `r3` failure (`test_runs_read_back_through_the_product[r3]`, caused by FR-C-08, as the coordinator reported). Package note P3-6 (who creates the database, outside the seed tools, name contains `seed`) is applied at step 1.

`SEED_RUNBOOK_S1_20261119.md` is accurate on the new counts (25 / 5 / 7), the scoped-counting sentence, the step 0 interpreter pin, the reworded insert-if-absent sentence and the receipts sentence. Wording gaps are in P3-5.

## 8. Findings

### P1

None.

### P2

None.

### P3

**P3-1. Guard order and refusal exit codes of the S7a command have no test, and three guard branches are untested.**
- Location: `s7a_runs.py:260-289` (`main`); `guard.py:216-225` (unparsable loopback URL), `guard.py:240-244` (scratch directory failure), `guard.py:254-258` (settings cannot be resolved).
- Evidence: package §6 first acceptance line is "Every refusal of §3.1 happens in the stated order". The S1 command has `test_s1_main_exits_2_on_refused_target`; S7a has nothing equivalent. The code order is correct (I read it), but only reading protects it. T5 runs only the success path. The three listed branches have no test, and `_require_parent` (the identity checks) has no test with a fake session.
- Fix: add a small T3 or T2 test that monkeypatches the three guard functions in `s7a_runs` with recorders and asserts the call order, the exit code 2 on each refusal, and that `guarded_engine` is not called when `check_s7a_environment` refuses. Optionally add the three branch tests and a `_require_parent` test with a `SimpleNamespace` session. Alternatively, have the evidence note record one deliberate refusal run (for example with a vision-mode variable set), which needs no database for the environment refusal.

**P3-2. A foreign active run that is not in `INPUT_PROCESSING` stops with `S7A_UNEXPECTED_RUN_STATE`, not `S7A_FOREIGN_ACTIVE_RUN`; and the "seed's run" hash check is weaker than the package wording.**
- Location: `s7a_runs.py:133-136` (state check at `:134` before the seed-identity check at `:135`), `s7a_runs.py:97-104`.
- Evidence: package §3.3 row 4 is "any other run → `S7A_FOREIGN_ACTIVE_RUN`", and the state error is meant for the seed's own run. Today a foreign run in, for example, `PREPARATION_REVIEW` returns the state error, which is not wrong in outcome (the task stops) but names the wrong cause, and T3 only tests foreign runs that are already in `INPUT_PROCESSING`. `_is_seed_run` recomputes the hash from the **stored snapshot** and compares it with the stored hash; it does not recompute the expected snapshot from the seed data (profile revision, age, interests), so it checks integrity and topic and idea, not full identity.
- Fix: run `_is_seed_run` first (for a `ParentStoryRunRecord`), then the state check, and add a T3 case for a foreign run in another state. If the weaker identity check is intended, say so in the evidence note.

**P3-3. `pytest.importorskip("modal")` imports Modal into the pytest process.**
- Location: `tests/unit/test_seed_guard.py:366`.
- Evidence: the test's own subprocess is the right isolation, but `importorskip` first imports `modal` in the test process. Modal's `config.py` loads the developer's `~/.modal.toml` when it is imported with no `MODAL_CONFIG_PATH`, and `modal` then stays in `sys.modules` for later tests in that process. Other repository tests already import Modal, so this is not new, but it contradicts the spirit of package §3.1 item 4 (re-check "in a subprocess").
- Fix: skip with `importlib.util.find_spec("modal") is None` (no import of the top-level package) and keep the subprocess as the only importer.

**P3-4. The `from None` assertion in the error-mapping test is weak.**
- Location: `tests/unit/test_seed_s7a.py:207`.
- Evidence: `info.value.__cause__ is None` is also true when the code uses a bare `raise` inside the `except`; only `__suppress_context__` proves `from None`. `_assert_refused` in `test_seed_guard.py:46-47` does check `__suppress_context__`.
- Fix: assert `info.value.__suppress_context__ is True`.

**P3-5. Runbook wording: replay promise, variable setup, and step order.**
- Location: `SEED_RUNBOOK_S7A_20261119.md:20-21, 36-50`; `SEED_RUNBOOK_S1_20261119.md` step 3 and step 5.
- Evidence: (a) The S7a runbook says a second run "adds nothing" without the condition package R3 P3-3 asked for. Replay is guaranteed only while P4 and P5 are still in `INPUT_PROCESSING` with exactly the four S7a receipts: after a later stage advances them, the writer stops with `S7A_UNEXPECTED_RUN_STATE`, and the receipt and input counts would also differ. (b) The S7a runbook does not list the session variables (`S2L_SEED_DATABASE_URL`, `S1A_P_ALEMBIC_DATABASE_URL`, `SKETCH2LIFE_ENV = 'local'`) or repeat that `STORYRUN_LITE_DATABASE_URL` and all `MODAL_*` must be unset; step 0 points only at the interpreter pin. (c) In the S1 runbook the new sentence "Then, for S7 item 2a, continue with the S7a runbook" sits inside step 3, before S1 run 2, test 7 and the variable clean-up (steps 4-6), and the S7a runbook repeats S1 as its own step 3. (d) The S1 runbook's step 5 (test 7) does not warn that `[r3]` fails after FR-C-08 (only the S7a runbook does).
- Fix: state the replay condition; add the variable block or a pointer to S1 runbook §3 for it; move the continuation note to the end of the S1 steps; add the known `[r3]` failure to the S1 runbook step 5.

**P3-6. The S1-scoped counting precondition is covered only by the database runs.**
- Location: `s1_core.py:101-109`; `tests/unit/test_seed_data.py` (new tests).
- Evidence: package row 5 lists "the S1 key sets used for counting" under T1. No unit test checks that every `SEED_STEPS` row dictionary carries each primary-key column (the precondition for `row[column.name]`), or that the statement compiles for a single-column and a composite key. The behaviour is correct today (coordinator's 16 of 16), but a future data change that renames a key column would surface only on a database.
- Fix: add one pure test that, for every step, asserts `{c.name for c in step.table.primary_key.columns} <= set(rows[0])` and that the primary keys in `step.rows()` are unique.

**P3-7. Allowlist row 8 and the package's "S1-scoped counts" assertion.**
- Location: allowlist row 8, `tests/integration/test_seed_s1_postgres.py` (unchanged).
- Evidence: package row 8 says T4 asserts "S1-scoped counts; still passes when S7a rows exist". T4 is unchanged and cannot fail if the scoping broke while no S7a rows exist. The property is proven only by `test_counts_in_the_database` in T5 (S7a rows present). That is sufficient for the acceptance line in §6, but the evidence note should say that T5, not T4, carries the property, and the runbook's step order (S1, then S7a, then T4) means T4 also runs with S7a rows present.
- Fix: say so in the evidence note; no code change needed.

### Informational (no action required)

- **I-1.** `check_s7a_environment` leaves one empty scratch directory under `tmp/seed7a/` per call, including calls where `guarded_engine` then refuses. Harmless (git-ignored).
- **I-2.** T5 discards the child's stderr, so a failed exit code shows only the number. Printing `result.stderr` (a fixed code, never a URL) in the assertion message would shorten diagnosis.
- **I-3.** The T3 fake builds a `ParentStoryRunRecord` in `DELETE_PENDING` and `COMPLETED`; the real repository returns a lifecycle record for purge states. The test covers both shapes, so this is fine.
- **I-4.** I could not verify the coordinator's database evidence (alembic head, S1 and S7a counts, the `[r3]` failure analysis). I checked that the code and tests are consistent with it, and that the `[r3]` failure is unrelated to this diff: `test_runs_read_back_through_the_product` is unchanged and calls `ParentStoryRunResponseV1` on a record that FR-C-08 now returns as a lifecycle projection for `DELETE_PENDING`.

## 9. What I did not verify

- Any database behaviour: the alembic run, S1 and S7a runs, T4 and T5. The statement that `story.command_receipts.resource_ref` counts exactly four rows rests on reading the repository code, not on a query.
- The full unit and contract suite against the base (package §5 row 4). I ran only the three seed unit files.
- That the repository's own `uv.lock` pins Modal 1.6.3 as the package says; the venv has 1.6.4 and the Modal config test passed against it.

## 10. Summary

1. **Verdict: ACCEPTABLE WITH NOTES. P1 = 0, P2 = 0, P3 = 7**, plus 4 informational items.
2. Behaviour equals package Draft 3: guard order, fixed messages, `MODAL_CONFIG_PATH`, decision table, `_require_parent`, error mapping, counts and idempotency all match; importing the writer reads no settings and no Modal client.
3. S1-scoped counting by primary key with `tuple_ IN` is correct for single and composite keys and has no scale or NULL issue; the property is proven by T5 only (P3-6, P3-7).
4. 139 seed unit tests pass, ruff, format, three validators and `git diff --check` are clean; the allowlist is respected (rows 1-7, 9-11; row 8 untouched); no secret, URL, machine path, CR or BOM.
5. Main notes: no test for the S7a guard order and exit codes (P3-1), foreign-run state ordering (P3-2), `importorskip("modal")` import (P3-3), weak `from None` assertion (P3-4) and runbook wording (P3-5).
