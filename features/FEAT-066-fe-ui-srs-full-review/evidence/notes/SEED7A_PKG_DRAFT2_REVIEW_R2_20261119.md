# SEED-7a package Draft 2 — cold review, round 2

- **Reviewer:** Sonnet 5.5 (`claude-sonnet-5-5`), effort `high` as set by the session that launched this review. The model ID is known to me; the effort level cannot be read back from inside the session, so it is recorded as launched.
- **Date:** 2026-11-19. **Mode:** read-only. I edited, staged, committed and pushed nothing. I ran no database, Docker, storage, network, git-write or test command. `D:\s2l-gate-secrets` was not read. This report is the only file I wrote.
- **Reviewed file:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT2_20261119.md`, worktree `.worktrees/be-integration`, branch `feature/feat066-be-integration`, HEAD `5e20faf7` (the package was written at `ed9ab3a6`).
- **Pin check (done first):** 21,950 B, SHA-256 `4F9782B3956C762D026F3DBC2FA154F888129DDFCF4A241367A46B172633C840`. It matches. The copy committed in `be-integration` hashes the same.
- **Other pins re-checked:**
  - Draft 11: 73,863 B, `6E4EFDE0…727CE8`. Match.
  - `DECISIONS.md` in `be-integration`: 73,010 B, `A1C58957…740C7A`. Match. D-066-80 is at line 627.
  - R1 review: 25,117 B, `9625A3C2…`. Match.
  - Draft 1: 15,936 B, `B21C251E…`. Match.
  - SRS: 701,157 B, `B9B1F42D…`. Match.
- **Commits named by the package:** `4e2f6d96`, `732111ee` and `ed9ab3a6` all exist. `git diff 4e2f6d96 HEAD` over `backend/tools/seed` and the three seed test files is empty, so the "identical to `4e2f6d96`" claim holds.

## 1. Verdict

**NOT READY.** Counts: **P1 = 0, P2 = 2, P3 = 10.**

Draft 2 is a real improvement. The four R1 P2 findings are fixed in substance, and the code claims I re-checked against the `be-integration` tree are accurate. Two new problems stop approval:

- N-01: the owner-run commands would import product code from the wrong checkout.
- N-02: the git plan can no longer be executed as written, because the docs commit it describes already exists.

Both fixes are one or two sentences. No redesign is needed, so a focused re-check of Draft 3 is enough.

## 2. Q1 — Are R1's 4 P2 and 8 P3 fixed, and did the fixes add problems?

| R1 | Result | Evidence and remaining gap |
|---|---|---|
| F-01 P2: whole-table S1 counts | **Fixed** | §3.2 "Counting scope" and allowlist rows 3 and 8. `s1_core.py:101–107` (`count_rows`, whole-table `select count(*)`) and `s1_core.py:167` (exit 1 unless totals equal `EXPECTED_COUNTS`) are cited correctly. The S1-scoped design works: `SEED_STEPS` already holds each table, and its row builders yield the primary keys. See P3-8 for the test-9 first-run assertion. |
| F-02 P2: commit model | **Fixed** | §3.3 step 8. I confirmed the repository commits inside each command: `parent_story_repository.py:125, 204` (`create_run`) and `:683, :737` (`confirm_context`). `get_db` (`be1_runtime.py:152–163`) does not commit, and the router has no commit. `create_core_session_factory` is at `persistence/database.py:42` and is used as the package says. |
| F-03 P2: S1 runbook and upgrade rule | **Fixed, one wording gap** | Allowlist row 10 and the re-seed rule (§3.2 "Upgrade rule") now match Draft 11 §11.4. The existing runbook sentence "Running S1 again on a seeded database is safe: it adds nothing" (`SEED_RUNBOOK_S1…md` §4) would become false for a pre-7a database. See P3-7. |
| F-04 P2: guard order | **Fixed** | §3.1: `check_s7a_environment()`, then `guarded_engine()`, then `check_no_provider()`. `guard.py:167–178` is cited correctly: `check_target`, then `prepare_runtime` (the first settings read), then the engine, then the live check. |
| F-05 P3 | **Mostly fixed** | The `STORYRUN_LITE_*` names and values match `composition.py:122–126, 162` and Draft 11 rule 10. `MODAL_CONFIG_PATH` is computed at run time. The wording "installed Modal is 1.6.3" and the "test 5" reference are wrong (P3-1, P3-2). |
| F-06 P3 | **Fixed** | `story.command_receipts.resource_ref` is `ForeignKey("story.runs.run_id", ondelete="RESTRICT")` (`story_run_lite/tables.py:425`). Rows are 2 / 2 / 4. `confirm_context` stores a receipt on a first confirm (`:724`), and `create_run` stores one at `:191`. |
| F-07 P3 | **Fixed, gaps remain** | `account_id` is passed, the recovery row exists, `roles=frozenset()`, and the router is not imported. Gaps: P3-3 and P3-4. |
| F-08 P3 | **Not resolved as written** | N-02 below. |
| F-09 P3 | **Fixed** | K4 (72 months) and K5 (96 months) are inside 36–120. One revision each gives 25, 5 and 7. The tuple shape matches `PARENT_PROFILE_SPECS` (`data.py:267`). |
| F-10 P3 | **Fixed** | The four validators are named. `validate_skeleton.py` is listed too. The harness asks for it only when structure changes, so running it is harmless. |
| F-11 P3 | **Fixed** | The clock line is in §3.3. `create_run` and `confirm_context` use `datetime.now(UTC)` (`:138`, `:702`). |
| F-12 P3 | **Fixed** | §2.3 records the stage-class exception. §2.1 names `SqlContentStore`. |

**New problems introduced or left by the fixes:** N-01, N-02, and P3-1 (a renumbering slip).

## 3. Q2 — Is the package implementable and testable as written?

- **S5 as `NOT_BUILT`: confirmed.** All of these hold at HEAD.
  - The files named in §2.1 exist.
  - `SqlContentStore` is at `infrastructure/learning_content/sql.py:188`. The `ai_policy` SQL stores are in `infrastructure/ai_policy/*.py`.
  - The boundaries have only test implementers: `tests/learning_content_fixtures.py:67`, `tests/unit/test_learning_content_eligibility.py:82` and `tests/ai_policy_fixtures.py`.
  - `routers/learning_content.py:138` is tagged `governance-candidate`. `app.py` and `router_composition.py` have no match for `learning_content` or `ai_policy`.
  - `AiPolicyCommands` appears only in its definition file and `ai_policy_governance.py`.
  - Supporting detail the package does not state: the Parent activity catalog that the product reads today is the Lesson Library read model (`infrastructure/lesson_library/parent_activity_catalog.py`, `LessonLibraryParentActivityCatalogAdapter`), which S1 already seeds. `learning_content` is not read by any Parent flow.
- **S7a behaviour (P4/K4, P5/K5; `create_run` then `confirm_context`): sound.** Re-checked at the post-FR-C-08 HEAD:
  - `ParentStoryRunService.create_run` and `confirm_context` have the signatures the package uses (`services/parent_story_runs.py:41–52`, `:137–145`). `get_active_run` takes `principal` and `account_id` (`:108–111`).
  - `create_run` writes only `story.runs`, `story.run_inputs` and `story.command_receipts` (`repository:154–203`). It writes no outbox row, audit row or aggregate row. The FR-C-08 outbox and audit tables are touched only by the lifecycle commands.
  - `confirm_context` updates `run_inputs` and `story_runs` and inserts one receipt (`:706–736`). A second confirm with a new key on a confirmed run only adds a receipt, so the "check `context_confirmed` first" rule is required, and the decision table has it.
  - I found no `CREATE TRIGGER` on the story tables. The trigger migrations are the `ap_*` and `lc_*` ones.
  - The profile gate (`ACTIVE`, `SYNTHETIC_DEV`, 36–120 months; `services/parent_story_runs.py:218–232`) accepts K4 and K5.
  - The route's `_require_parent` checks `state == "active"`, `account_role == "parent"` and `issuer == principal.issuer` (`routers/parent_story_runs.py:75–84`). See P3-4.
  - `get_run` returns `ParentStoryRunRecord`, or `ParentStoryLifecycleRecord` only for purge states (`:270–272`). See P3-3.
  - Importing the repository pulls no settings: `core_models`, `story_run_lite.tables`, `ports/*` and the profile lookup contain no `get_settings` or `os.environ`. `modal` is imported lazily and only in `infrastructure/ai/modal_function_client.py`. §4's "trace once and record" instruction is safe to keep, and I found nothing that would trigger a stop.
- **Idempotency: sound.** A replayed run takes decision row 3 and calls no command. A foreign active run stops the task. A cancelled or completed seed run makes `create_run` replay the old non-active run through the same key (`repository:123–126`). See P3-3.
- **Provider guards: complete against Draft 11 rule 10.** All the `Settings` fields exist (`settings.py:35, 47–56, 77–78`). The `STORYRUN_LITE_*` switches match `composition.py:122–126, 162`. I checked the installed Modal config module: `user_config_path` is evaluated at import from `MODAL_CONFIG_PATH` (`modal/config.py:123`), so the plan to set the variable before any import is the right mechanism. See P3-2 and P3-5.
- **Test boundary: correct.** The fresh database name contains `seed`, the port is neither 5432 nor 5433, and `sketch2life_m2_s1a` and `be1_acceptance` are refused (`guard.py:20–21, 77–81, 88–89`; package §5). The tests skip without `S2L_SEED_DATABASE_URL`.
- **Git boundary:** N-02.
- **Interpreter and source tree for the owner-run commands:** N-01.

## 4. Findings

### P1

None.

### P2

**N-01 — The owner-run `python -m tools.seed.…` commands would use product code from the root checkout, not `be-integration`.**
- Location: package §5 owner-run steps 1–3 and row 10 (the S1 runbook), §7 third bullet. The existing `SEED_RUNBOOK_S1_20261119.md` §3 has the same gap.
- Evidence:
  - `be-integration/backend` has no `.venv`.
  - The only venv that carries the dependencies is `D:\GitHub\Sketch2Life\backend\.venv`. Its editable install (`_editable_impl_sketch2life_backend.pth`) points at the **root** `backend/src`.
  - The root checkout is on `feature/feat063-m2-parent-teacher-foundation`. Its `application/services/parent_story_runs.py` has no `cancel_run` (grep count 0), and it has no seed tools. So it is a pre-FR-C-08, pre-SEED tree.
  - `pytest` is safe, because `pyproject.toml:92` sets `pythonpath = ["src"]`. `python -m tools.seed.s1_core` and `python -m tools.seed.s7a_runs` are not safe: `sys.path[0]` is `backend/`, which has no `sketch2life` package. `sketch2life` therefore resolves through the `.pth` to the root tree.
  - Neither the package nor the runbook mentions `PYTHONPATH`. The package pins `MYPYPATH=src` for mypy only (§5 row 2).
- Why it matters: the whole of §3.3 and §7 rests on the post-FR-C-08 behaviour of `create_run`, `confirm_context` and `get_active_run`. If the writer runs against the root tree, the guard code, the services and the evidence all come from a different branch than the one that was reviewed. The evidence note could record a pass for the wrong code.
- Fix: in the S7a runbook and the S1 runbook update, require `$env:PYTHONPATH = 'src'` (or an equivalent explicit pin) in the owner's terminal. Add a pre-run step that prints `sketch2life.__file__` and `tools.seed.guard.__file__` and stops unless both are under the `be-integration` worktree. Record that line in the evidence. Say which interpreter the owner uses, because `be-integration` has none of its own.

**N-02 — The git plan and the "nothing written before approval" statement are stale or unexecutable.**
- Location: §1 pins table (the `DECISIONS.md` row says "uncommitted" in `.worktrees/seed1`), §5 commit plan (lines 217–219), §8 SP-2 (line 244), and the §1 base row (line 16).
- Evidence:
  - `be-integration` HEAD is `5e20faf7` "docs(FEAT-066): carry seed design Drafts 7-11, D-066-80 and SEED-7a package Drafts 1-2". It already holds Drafts 7–11, D-066-80 and both package drafts (8 files, 3,216 insertions). `DECISIONS.md` there is committed, not uncommitted.
  - So SP-2's sentence "Nothing is written into `.worktrees/be-integration` before this package is approved" is no longer true.
  - §5 item 1 says the docs commit will also carry "the Task Approval entry once approved". That entry cannot go into a commit that already exists. §5 item 2 puts the `STATUS.md` and `CONTEXT.md` entries in the task commit.
  - Workflow rule: one finished task is one commit. The plan allows exactly two commits. After the docs commit, the Task Approval entry fits neither.
- Why it matters: the package asks the owner to approve a git boundary ("one docs commit, one task commit, never push") that no longer matches the branch. An implementer who follows it literally either makes a third commit or folds approval records into the task commit without an approved rule.
- Fix: restate the base as `5e20faf7` (or "HEAD at implementation") and say the docs commit is done. State where the Task Approval entry goes: in the task commit, or as one small approval-record commit. Remove the stale "uncommitted" and "not written before approval" text. If Draft 3 is edited after the commit, say which commit carries it.

### P3

**P3-1 — Test numbering is broken, and the acceptance cannot be checked as written.**
- Location: §3.1 item 4 ("Test 5"), §5 owner-run step 3 ("tests 8 and 9"), §6 ("Tests 1 to 9 pass"), §7 fourth bullet ("test 5"), §9 F-05 ("test 5 uses placeholder values"), the §4 imports bullet ("test 9 only").
- Evidence: the package never defines a numbered test list. If the number means the allowlist row, "test 5" is `test_seed_data.py`, but the Modal subprocess check and the placeholder-value rule belong to `test_seed_guard.py` (row 6). Rows 1–4 are not tests. This looks like a renumbering slip: row 3 (`s1_core.py`) was inserted and the Draft 1 numbers were shifted for rows 8 and 9 but not for "test 5".
- Fix: number the tests explicitly, or use file names, in §5 and §6.

**P3-2 — "The installed Modal SDK is version 1.6.3" is a pin claim, not an installed-version claim.**
- Location: §3.1 item 4 (line 65), §7 fourth bullet.
- Evidence: `backend/pyproject.toml:30, 85` and `uv.lock:1222` say 1.6.3. The only venv that exists (`D:\GitHub\Sketch2Life\backend\.venv`) has `modal-1.6.4.dist-info`. The test in the package re-checks against whatever is installed, so the plan still works.
- Fix: say "pinned 1.6.3; the owner's venv may differ; the test checks the installed version".

**P3-3 — The decision table does not say how the writer handles the `ParentStoryRunView` union or a replayed non-active run.**
- Location: §3.3 step 4 and step 7.
- Evidence: `get_active_run` and `create_run` return `ParentStoryRunRecord | ParentStoryLifecycleRecord` (`ports/parent_story_runs.py:90`). The lifecycle record has no context fields. If a seed run was later cancelled or deleted, `create_run` with the old key returns that run (`repository:123–126`), and the package then calls `confirm_context` before the end check.
- Fix: state an `isinstance` check on the returned record, and check the run state between `create_run` and `confirm_context`. Map any other state to a fixed refusal, as the package already does for errors.

**P3-4 — Step 1 omits the issuer check.**
- Location: §3.3 step 1 (line 104).
- Evidence: the route checks three conditions (`identity.state != "active" or identity.account_role != "parent" or identity.issuer != principal.issuer`, `routers/parent_story_runs.py:75–84`). The package lists only two.
- Fix: list all three, or say "the same three conditions as `_require_parent`".

**P3-5 — The `MODAL_CONFIG_PATH` plan has gaps.**
- Location: §3.1 item 1 (line 59), allowlist rows 6 and 9.
- Evidence:
  - "The run's own scratch folder" is undefined. The writer has no such folder. Say where the path comes from, for example a `tempfile` directory.
  - Draft 11 rule 10 requires the path to be set before any `modal` import. The writer cannot verify that in a process where `modal` was imported earlier (for example inside a pytest session). Test 9 calls the guards inside pytest, so its check can pass vacuously.
  - `check_s7a_environment()` writes `os.environ`. The tests need `monkeypatch`, or the value leaks into later tests.
- Fix: say how the path is chosen. Add "assert `modal` is not in `sys.modules` when the check runs" or run that part in a subprocess. Require `monkeypatch` for every environment write in the tests.

**P3-6 — The allowlist is not fully exact, and the command count is off.**
- Location: §4 rows 11 and 12 (`SEED_RUNBOOK_S7A_<date>.md`, `SEED_7A_IMPLEMENTATION_EVIDENCE_<date>.md`), §5 row 6 ("the six new paths").
- Evidence: two paths carry a `<date>` placeholder. The table has five new (`N`) rows: 4, 7, 9, 11, 12. The evidence note (row 12) is written after the owner run, so at the time of `git add -N` and `git diff --check` only four new files exist.
- Fix: give the dates or the exact names. Fix the count and say which new paths exist at each step.

**P3-7 — S1 runbook sentences that become false.**
- Location: allowlist row 10; `SEED_RUNBOOK_S1_20261119.md` §4 ("Running S1 again on a seeded database is safe: it adds nothing.") and §5 ("command receipts … are not seeded").
- Evidence: after SEED-7a, an old seed database run through the new S1 adds P4 and P5. S7a adds command receipts. The runbook also calls the S1 integration test "Test 7", while the package's row 8 is that same file.
- Fix: update those sentences in row 10, not only the counts.

**P3-8 — Test 9's first-run assertion is unspecified.**
- Location: allowlist row 9, §5 owner-run steps 2–3.
- Evidence: the owner runs S7a twice (step 2) before test 9, which runs S7a again. On that database the test's first S7a run creates zero rows. The existing S1 test already handles the same case with `value in {0, EXPECTED_COUNTS[name]}` (`test_seed_s1_postgres.py:75–76`).
- Fix: assert that totals equal `EXPECTED_S7A_COUNTS` and that the second run adds zero, and allow `{0, expected}` for the first.

**P3-9 — Seed content and key naming are not pinned.**
- Location: §3.3 step 5 ("a fixed `[SEED]` topic and `adult_confirmed_idea` from `data.py`"), §3.3 step 5 key `seed:s7a:p4:create-1`.
- Evidence: the topic and idea values are not given, so the owner approves content that is not on the page. S1's topics carry no `[SEED]` marker (`data.py:535–540`). Draft 11 §11 intro says keys follow `seed:s<n>:<scope>:<case>`; `s7a` is not `s<n>`. This is harmless but may confuse a later 2b task.
- Fix: list the two topic and idea strings and their length (topic at most 120, idea at most 500 characters, `services/parent_story_runs.py:97–102`), and note the key rule.

**P3-10 — SRS wording is slightly stronger than the SRS.**
- Location: §2.1 "Scope mismatch" bullet.
- Evidence: SRS §11.2 (`SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1048`) says GLOBAL is only for "catalog/policy nền tảng" and never owns a profile, run, quota or asset. It does not name the Parent activity catalog. The claim comes from Draft 11 §11.2. The conclusion (the module owner decides the scope) is still right.
- Fix: cite Draft 11 §11.2 together with SRS §11.2, or say "platform catalog".

## 5. Q3 — Do the cited code references match the tree?

Yes. No broken reference found.

| Reference in the package | Result |
|---|---|
| `guard.py:167–178` (`guarded_engine`, calls `prepare_runtime`) | Correct (`:167–178`) |
| `s1_core.py:101–107` (whole-table counts) | Correct (`:101–107`) |
| `backend/pyproject.toml`, Modal 1.6.3 | Correct (`:30`, `:85`; `uv.lock:1222`) |
| `ParentStoryRunService`, `SqlParentStoryRunRepository`, `SqlParentStoryProfileLookup`, `create_core_session_factory` | All exist; the route builds the service the same way (`routers/parent_story_runs.py:70–75`) |
| `VerifiedPrincipal`, `AdultIdentityModel`, `ParentStoryRunRecord`, `ParentStoryRunError`, `ParentStoryRunServiceError`, `ParentStoryRunResponseV1` | All exist at the imported paths |
| §2.1 file and class names (`ContentCommands`, `AiPolicyCommands`, `ResourceAccountingService`, the boundaries and fixtures) | All exist |
| `PARENT_PROFILE_SPECS`, `PARENT_SUBJECTS`, `EXPECTED_COUNTS` (`data.py:267, 92, 629`) | Correct; shapes match the proposed additions |
| Seed test files in the allowlist | All three exist; the S7a test files are new |

Not verified by me: the line numbers inside `ParentStoryRunResponseV1` use. The package does not cite line numbers for the router, repository or `get_db`; I checked the behaviour instead.

## 6. Q4 — SRS conflict or invented product intent

- **SRS conflicts: none.**
  - §11.1 item 3 (one unclosed run per Parent account; `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1019`). The package holds the lock with `INPUT_PROCESSING`.
  - §11.2 (`:1048`) is used only as stated in P3-10.
  - §24.1 (`:1915`, demo data is synthetic only). K4 and K5 are `SYNTHETIC_DEV`, with no consent.
- **Invented intent: none beyond what Draft 11 already decided.** The K4/K5 display names and interests ("Thích vẽ chim", "Thích vẽ nhà") are synthetic placeholders in the same style as K1 to K3. The end state `INPUT_PROCESSING` with a confirmed context comes from Draft 11 §11.4 item 2a, which the owner accepted in D-066-80. The package does not seed S5, assets, understanding, story or video, as Draft 11 §3 requires for missing commands.
- **D-066-80 consistency:** the "R5 notes move to the first object-writing stage" statement matches the decision text. The package asks for no launch, which matches "each stage needs its own Task Approval and owner launch".

## 7. What I did not verify

- I did not run any test, linter, type checker or validator. The unit and contract comparison against the base (§5 row 4) is untested.
- I did not read the migration files in full. I searched for `CREATE TRIGGER`, and the matches are the `ap_*` and `lc_*` migrations, not story ones. A trigger on `story.*` written another way would not have been found.
- I did not check how `tools/validate_repository_security.py` treats the new names.
- I did not run the S1-scoped counting design. I only confirmed it is feasible from the code.
- I did not confirm which interpreter and venv the owner will use.
- I did not re-read Draft 11 outside rules 3, 5, 6, 9, 10, 12, §3 and §11.1–§11.10.

## 8. Summary

- **Verdict: NOT READY.** P1 = 0, P2 = 2 (N-01, N-02), P3 = 10.
- **R1 status:** all four R1 P2 findings are fixed; R1's eight P3 findings are fixed except F-08 (N-02) and parts of F-05 and F-07.
- **Next step:** a short Draft 3 that adds the `PYTHONPATH` pin and source-path check, restates the base and commit plan at `5e20faf7`, and fixes the numbering, wording and content notes. A focused re-check is enough.
