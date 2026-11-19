# SEED-7a package Draft 3 — focused re-check, round 3

- **Reviewer:** Sonnet 5.5 (`claude-sonnet-5-5`), effort `high` as set by the session that launched this review. The model ID is known to me; the effort level cannot be read back from inside the session, so it is recorded as launched.
- **Date:** 2026-11-19. **Mode:** read-only. I edited, staged, committed and pushed nothing. I ran no database, Docker, storage, network, git-write or test command. `D:\s2l-gate-secrets` was not read. This report is the only file I wrote.
- **Reviewed file:** `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT3_20261119.md`, worktree `.worktrees/be-integration`, branch `feature/feat066-be-integration`, HEAD `5e20faf7`.
- **Pin check (done first):** 26,991 B, SHA-256 `193312626922A2383047B8002481CF2D229D51537BD0B4B9F0780F7BF68C7403`. It matches the `19331262…` the launching session gave. HEAD is `5e20faf7`, as Draft 3 says. Draft 2 (`4F9782B3…`) and the R2 report are the ones I reviewed last round.
- **Scope:** a focused re-check of the R2 findings and the new text. I did not re-open parts of Draft 2 that Draft 3 did not change, beyond spot checks.

## 1. Verdict

**READY WITH NOTES.** Counts: **P1 = 0, P2 = 0, P3 = 6.**

Both R2 P2 findings and all ten R2 P3 findings are fixed. The new text introduced no P1 or P2. The six P3 notes are small clarifications. None blocks approval. The package is implementable and testable as written.

## 2. Q1 — Are N-01, N-02 and P3-1 to P3-10 fixed?

| R2 | Result | Evidence |
|---|---|---|
| N-01 (P2) interpreter and source tree | **Fixed** | §5 step 0 (line 203) pins `PYTHONPATH` to the integration worktree's `backend/src`, runs `python -c "import sketch2life, tools.seed.guard as g; print(…__file__)"`, stops unless both paths are under the worktree, and records only "both under be-integration: yes". It notes that `pytest` is safe because of `pyproject.toml:92`. I confirmed the mechanism: `PYTHONPATH` entries come before the site-packages `.pth` that points at the root `backend/src`. `sketch2life/__init__.py` and `tools/seed/__init__.py` exist, so both `__file__` values are real paths (`tools` itself is a namespace package, which does not matter here). Row 10 carries the pin into the S1 runbook. `alembic` needs no pin: `alembic.ini` has `prepend_sys_path = %(here)s/src`, although `alembic/env.py` imports `sketch2life.*`. |
| N-02 (P2) commit plan and stale base | **Fixed** | Line 13 (`DECISIONS.md` committed in `5e20faf7`), line 16 (base ends at `5e20faf7`), §5 commit plan (lines 222–224: docs commit done, one task commit) and SP-2 (line 249). I re-checked `5e20faf7`: it holds seed Drafts 7–11, D-066-80 and package Drafts 1–2, and `DECISIONS.md` there is 73,010 B with the pinned hash. The program approval entry exists at `approvals/TASK_APPROVAL.md:550` (goal v2 program, B3 is the SEED-7a task), so "the program approval entry is the Task Approval" is accurate. See P3-1 for one wording gap. |
| P3-1 test numbering | **Fixed** | §5 line 194 names T1–T5 by file. Allowlist rows 5–9 carry T1–T5. The text now uses T2 (Modal check), T4/T5 (database tests) and "T1 to T5 pass". |
| P3-2 Modal "installed" claim | **Fixed** | §3.1 item 4 (line 65): pinned 1.6.3, the venv may differ, T2 re-checks the installed version in a subprocess. |
| P3-3 union and state check | **Fixed, one inconsistency** | §3.3 step 4 (line 116): `isinstance` check and state check before `confirm_context`, fixed `S7A_UNEXPECTED_RUN_STATE`; T3 covers it. See P3-3 below. |
| P3-4 issuer check | **Fixed** | Step 1 (line 104) lists `state == "active"`, `account_role == "parent"` and issuer equal; it matches `routers/parent_story_runs.py:75–84`. |
| P3-5 `MODAL_CONFIG_PATH` | **Fixed, two notes** | `tempfile.mkdtemp`, file absent, `modal` not in `sys.modules`, `monkeypatch` for test environment writes (line 59); T5 asserts or uses a subprocess (row 9). See P3-4 and P3-5. |
| P3-6 allowlist exactness | **Fixed** | Rows 11 and 12 carry the date. §5 row 6 (line 192) lists the new paths that exist at that step: rows 4, 7, 9 and 11. That is correct: the evidence note (row 12) is written after the run. |
| P3-7 runbook sentences | **Fixed** | Row 10 names both sentences and the `PYTHONPATH` pin. |
| P3-8 T5 first-run assertion | **Fixed** | Row 9: first run `0` or expected, totals equal, second run adds zero, citing `test_seed_s1_postgres.py:75–76` (those lines do hold the `value in {0, EXPECTED_COUNTS[name]}` assertion). |
| P3-9 content pinned | **Fixed** | Step 5 (line 123) gives both topics and ideas and the length limits. I checked them: topics are well under 120 and ideas well under 500 characters (`services/parent_story_runs.py:97–102`; `ParentRunContextSnapshotV1` has the same limits), and the topic has a non-space character. The `s7a` key scope is explained. |
| P3-10 SRS wording | **Fixed** | §2.1 line 30 cites SRS §11.2 at line 1048 (matches the SRS) and names the Lesson Library read model. |

## 3. Q2 — Did the fixes add problems?

I checked every new item the launching session listed against the code and the program.

- **`tempfile` and `modal` not in `sys.modules`:** workable. `modal` is imported lazily and only in `infrastructure/ai/modal_function_client.py`, so a plain `python -m tools.seed.s7a_runs` has not imported it before the check. See P3-4 and P3-5 for refinements.
- **`isinstance` and state check with `S7A_UNEXPECTED_RUN_STATE`:** consistent with the code. `get_active_run` and `create_run` return `ParentStoryRunRecord | ParentStoryLifecycleRecord` (`ports/parent_story_runs.py:90`). A replayed key for a cancelled run goes through `repository:123–126`, so the state check before `confirm_context` is needed and correct.
- **Topics and ideas:** valid against the schema and the service limits. They carry `[SEED]` on the topic only, which is a reasonable marker for run text.
- **Step 0:** correct, see N-01 row above.
- **T1–T5 naming:** consistent across §3.1, §4, §5 and §6. Section 9 (the Draft 2 table) still uses old numbers ("test 8", "test 5"). It is headed as the earlier round, so I treat it as history (nit, no finding).
- **Commit plan and program entry:** consistent with the program (`GOAL_V2_PHASE_BC_PROGRAM_20261119.md` §1 rules 3, 5, 8, 9; B3 row). The fresh database name pattern `frc08_seed7a_<stamp>` the program allows contains `seed`, and the container port is 55458, neither 5432 nor 5433. The guard accepts it.

## 4. Q3 — Is the package implementable now?

Yes.

- **Exact allowlist:** rows 1–12 with exact paths. The read-only imports are listed. A product-module change stops the task.
- **Behaviour (P4/K4, P5/K5; one run each; provider guards; S5 parked):** consistent with the code I re-checked last round. `create_run` and `confirm_context` write only the three tables, with no outbox or audit rows. The `Settings` fields and `STORYRUN_LITE_*` switches exist.
- **Idempotency:** a second run takes decision row 3 and writes nothing. T5 asserts it. See P3-3 for one wording conflict.
- **Test boundary:** fresh database named with `seed` on the loopback `frc08` container; ports 5432 and 5433, `sketch2life_m2_s1a` and `be1_acceptance` are refused in `guard.py:20–21, 77–89`.
- **Git boundary:** one task commit, no push. The docs commit exists. See P3-1 and P3-2.
- **Cited references:** unchanged from R2 and correct (`guard.py:167–178`, `s1_core.py:101–107`, `routers/parent_story_runs.py:75–84`, `pyproject.toml:92`, `test_seed_s1_postgres.py:75–76`, SRS line 1048).
- **SRS and intent:** no conflict and no invented intent. K4/K5, the two topics and the `INPUT_PROCESSING` end state all come from Draft 11 §11.4 item 2a or are synthetic placeholders allowed by SRS §24.1.

## 5. Findings

### P1

None.

### P2

None.

### P3

**P3-1 — Who triggers the commit and the governance records is stated as "the owner's word", but the program approval already authorizes them.**
- Location: §5 commit plan heading (line 222: "on the owner's word only"), §4 "Governance records" (line 174: "The coordinator writes them … on the owner's word"), and the status line 3 ("authorizes no … commit").
- Evidence: the program approval (`approvals/TASK_APPROVAL.md:550–565`; program §1 rules 2, 6 and 8) lets the goal commit once per finished task after the implementation review is ACCEPTABLE (WITH NOTES) and the checks are green, and record decisions as "the goal's", never as the owner's. It forbids pushes. The package also does not say that `validate_repository_security.py` runs again immediately before the commit (the harness and program rule 9 require it; row 5 lists it only as a coordinator check).
- Fix: say that the task commit is made by the goal under the program approval after review and checks, and the owner's push stays out of scope. Say that records are written as the goal's. Add the security-validator rerun to the commit step.

**P3-2 — The task commit lists files that are not in the allowlist.**
- Location: §5 commit plan item 2 (line 224): "package Draft 3, the review records kept in the repository".
- Evidence: the allowlist (§4) names 12 paths. Package Draft 3 and "review records kept in the repository" have no path. `tmp/` is ignored by git, so the repository copies need a stated location (for example `evidence/notes/`).
- Fix: name the paths for package Draft 3 and for each review record that will be committed, or say they stay in `tmp/` and only the package is committed.

**P3-3 — Decision row 3 ("nothing") and step 7 (end state must be `INPUT_PROCESSING`) can disagree.**
- Location: §3.3 step 4 table row 3 (line 113) and step 7 (line 126).
- Evidence: row 3 says a confirmed seed run needs no action, whatever its state. Step 7 says any state other than `INPUT_PROCESSING` stops the task. If a later stage (2b) has moved the run on, a replay of S7a would take row 3 and then stop at step 7 with an error rather than doing nothing. Draft 11 §3 treats later S7 stages as one-shot, so this is a corner case, but the replay claim in §3.4 reads as unconditional.
- Fix: put the state check inside the table (row 3 applies only to a confirmed run in `INPUT_PROCESSING`; other states give `S7A_UNEXPECTED_RUN_STATE`), or say that S7a replay is guaranteed only before a later stage has advanced the runs.

**P3-4 — `tempfile.mkdtemp` writes into the system temp folder, which the project harness asks to avoid.**
- Location: §3.1 item 1 (line 59).
- Evidence: `.claude/sketch2life-harness.md` says scratch folders that Claude creates for this project go under `D:\GitHub\Sketch2Life\tmp\`, not `%TEMP%`. When the goal session runs the writer, an empty directory appears in `%TEMP%` on every run. It holds nothing, so the harm is small, but it leaves one directory per run.
- Fix: pass `dir=` pointing at the repository's `tmp/seed7a/` (git-ignored), or say that the directory is empty and acceptable. The check that the file does not exist stays the same.

**P3-5 — The `modal`-not-in-`sys.modules` assertion needs a stated failure mode and run isolation.**
- Location: §3.1 item 1 (line 59) and allowlist row 9 (line 160).
- Evidence: the check lives in `check_s7a_environment()`. Inside the T5 pytest process, an earlier test could have imported `modal` (T2's subprocess does not count, but other tests might). The package does not say whether the check then raises a guard refusal or only warns, and T5 "asserts it is absent, or runs it in a subprocess". A refusal would make T5 fail for a reason unrelated to the seed.
- Fix: say the check raises a fixed refusal, and that step 3 runs T4 and T5 in their own pytest invocation (or that T5 uses the subprocess form).

**P3-6 — The steps do not say who creates the fresh database.**
- Location: §5 steps 0–3 (lines 202–206) and the "Database run" paragraph (line 196).
- Evidence: the program (§1 rule 5) lets the goal create a database named with the task tag, such as `frc08_seed7a_<stamp>`. The seed never creates one (Draft 11 rule 3). The step list starts at `alembic upgrade heads`, which needs the database to exist.
- Fix: add a step 0b: create the fresh database (name contains `seed`, on the `frc08` container), outside the seed tools, and record its name (not the URL) in the evidence.

## 6. What I did not verify

- I did not run any test, linter, type checker or validator, or the S1-scoped counting design.
- I did not read the migration files in full. As in R2, I only searched for triggers, and none were on story tables.
- I did not check how `validate_repository_security.py` treats the two Vietnamese topic and idea strings or the new names.
- I did not confirm which interpreter the goal session will use. Step 0 handles any interpreter.
- I did not re-read Draft 11 beyond rules 3, 6, 10 and §11.4, which R2 covered.

## 7. Summary

- **Verdict: READY WITH NOTES.** P1 = 0, P2 = 0, P3 = 6.
- **R2 findings:** N-01 and N-02 (P2) and P3-1 to P3-10 are all fixed. No new P1 or P2 came from the fixes.
- **Notes to apply during implementation or in Draft 4 if one is cut:** commit authority and security rerun wording (P3-1), allowlist paths for the committed docs (P3-2), the row 3 / step 7 state rule (P3-3), the temp directory location (P3-4), the `modal` check failure mode (P3-5) and the database creation step (P3-6).
