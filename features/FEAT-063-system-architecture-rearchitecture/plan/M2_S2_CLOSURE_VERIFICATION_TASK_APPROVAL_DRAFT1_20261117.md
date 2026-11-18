# FEAT-063 M2-S2 Closure Verification — Task Approval Draft 1 (revision 3)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. No command in this draft has run.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2.
- **Revision history:** revision 1 was 9,419 bytes, SHA-256 `ABB2AC7B0045BEB3692B75E0F96D5F86C927C2294E88CB72C0EE023BB420F1D9`, with driver SHA-256 `E067B6F63EABFD9039538756AA6593EB224A1A5357431F119AA0399A0DAAB624`. Cold review R1 (Sonnet 5.5, effort high) returned NOT READY, 1 P1 / 5 P2 / 9 P3: `evidence/M2_S2_CLOSURE_VERIFICATION_DRAFT1_COLD_REVIEW_R1_20261117.md`. Revision 2 (14,847 bytes, SHA-256 `A08FB8BCE66D1DCAA875C72886C829BAE07220841D792688E75FDE67812293F6`, driver SHA-256 `2128FF58A6FB4EAAB180ACF49F408D5E70B7DCDED19EF21D92A6FA5E057B66BE`) addressed those findings. Delta review R2 (Sonnet 5.5, effort high) confirmed twelve of the fourteen as fixed and two as partly fixed, and returned NOT READY, 1 P1 / 3 P2 / 12 P3 new: `evidence/M2_S2_CLOSURE_VERIFICATION_DRAFT1_DELTA_REVIEW_R2_20261117.md`. This revision 3 and driver revision 3 address every R1 and R2 finding (section 7). Revision 3 has not been re-reviewed.
- **Purpose:** produce the test, typecheck and lint evidence that `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` still lists as missing, so the owner can decide whether to close M2-S2. This draft changes no source and no test.
- **Not in scope:** fixing any diagnostic or test; M2-S3; FR-C-08; commit, push, merge or deployment; any Modal or provider call (`OWNER_MODAL_CALL_APPROVED=NO`).

## 1. Basis

- Worktree `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`, nothing staged.
- S2 implementation report: `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md`. Twelve of its source and test pins (the five S2 source paths other than `app.py` and seven test paths) and the recorded post-overlay hash of `be1_artifacts.py` were re-hashed on 2026-11-17 and still match. `app.py` and `test_openapi_contract_catalog.py` changed under the mapper task; `test_app_composition.py` matches its pin. The two context files and the route baseline JSON of that report were not re-hashed.
- Mapper task: accepted with recorded deviations on 2026-11-17 (`evidence/M2_S2_SHARED_OPENAPI_MAPPER_IMPLEMENTATION_EVIDENCE_20261117.md`, SHA-256 `CCB014AFB23D7A156FC4E229C7B4A717B758982D425023E075AAED632F5C60C6`).
- Uncommitted changes under `backend/src` are exactly seven files: the six S2 source paths (one of them, `app.py`, also carries the mapper change) and `interfaces/http/routers/be1_artifacts.py` (the FEAT-047 description overlay). A comparison of the worktree with HEAD therefore measures S2, the mapper task and that overlay together, and nothing else.

## 2. What is still missing for S2

| # | Item | Last recorded state | Gap |
|---|---|---|---|
| 1 | Targeted pytest selection, nine files | Never passed as a whole: 81 of 82 on 2026-11-14, then 1 failure and 1 `tmp_path` error in the combined run. One earlier attempt hung without output and was interrupted; cause unknown | One complete run. The mapper task ran one of the nine files fully (`test_openapi_contract_catalog.py`) and one node of a second (`test_app_composition.py`); seven files have not run since `app.py` changed |
| 2 | Mypy on `src/sketch2life` | 353 signatures (327 errors, 26 notes, 65 files) in the mapper task's post check; 32 signatures lie in the seven uncommitted source files | Not known how many of them the uncommitted work added. Needs a HEAD comparison |
| 3 | Ruff on the six S2 source paths | 17 diagnostics on 2026-11-14 (Python 3.13 environment, Ruff 0.17.5) | Not classified as existing or added; not measured in the task environment (Ruff 0.17.2) |
| 4 | FEAT-047 description overlay on `be1_artifacts.py` | Applied as a temporary integration overlay | Keep or revert (owner decision D2, to be taken before the first action) |
| 5 | `evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md` | Open | Closing note: the mapper task addressed the finding |
| 6 | Stale-version P3 on broader routes (Allowlist R2) | Outside the S2 allowlist | Record as a separate follow-up, not a closure blocker |
| 7 | `CONTEXT.md`, owner closure entry, one commit | Not done | After the evidence |

## 3. Proposed commands

All actions use one driver, outside the worktree: `D:\GitHub\Sketch2Life\tmp\m2-s2-closure\s2_closure_driver.py`, 28,728 bytes, SHA-256 `DFE6A9188D8296EC1D7E4D0E3C38CAE0C12FC8385711F7AC784AF687CA2ECFBD`. No action of it has been executed. Static checks only: a syntax parse, Ruff rules F, E9 and B on the driver file (clean), and two invocations with invalid arguments that stopped in argument checking before the preflight. It is run as `python.exe -I -X utf8 s2_closure_driver.py <action>` with the mapper task's interpreter (`D:\GitHub\Sketch2Life\tmp\m2-s2-mapper-env\.venv\Scripts\python.exe`, SHA-256 `0B471133E110CFB53A061CAD528CE8E517D7B9AC41A0A396C39AD795A487FC14`; that environment was shown equal to the lock resolution, 108 distributions, during the mapper task, and the driver records the current distribution count and the pytest, Mypy and Ruff versions but does not re-prove lock equality).

The driver accepts exactly one action (plus the three result paths for `delta`) and the optional `--require-egress-block`; any other argument stops it. Before every action it checks: that it runs in isolated UTF-8 mode; interpreter and Git executable pins; HEAD; an empty index; that the uncommitted changes under `backend/src` are exactly the seven pinned files and that they have their pinned hashes; that no `.env` file exists at the worktree root or in `backend/`; and it probes egress. A stop in this preflight launches no tool and consumes no ceiling. Each tool runs in a child process started with `-I -X utf8 -B` and a cleared environment with the same variable names as the mapper task runner's. The settings class reads a `.env` file at the worktree root if one exists; the driver does not patch that class and relies on the preflight check instead. Child output goes straight to files in the run folder and every child has a timeout (pytest 900 s, collection 600 s, Mypy 1,800 s, Ruff 300 s); a timeout is recorded as `timedOut` and is a driver bound, not a tool verdict. On a timeout the driver terminates the child's whole process tree with the system `taskkill`; that path has not been exercised. Children get the null device as standard input. Every result, and the snapshot manifest, records the driver hash, tool versions, the hashes of the seven source files, the nine test files, `pyproject.toml` and `uv.lock`, and a fingerprint before and after the action with a `worktreeUnchanged` flag. The fingerprint is the `git status` output plus probes of git-ignored places: the entries under `backend/.runtime`, the presence of pytest, Mypy and Ruff cache folders, and the number of `__pycache__` folders under `backend/src` and `backend/tests`. Outputs go to `D:\GitHub\Sketch2Life\tmp\m2-s2-closure\runs\<action>-<guid>\`. The driver is designed to write nothing into the worktree (cache providers off, bytecode writing off, base temp, home, temp and the BE1 artifact root under the run folder); the before/after fingerprint is the check of that, limited to what Git and those probes can see.

**Order (the non-repeatable action is last):**

| Step | Action | What it does | Ceiling |
|---|---|---|---|
| C1 | `snapshot` | Extracts `backend/src` and `backend/pyproject.toml` of HEAD with `git archive` into a uniquely named folder `tmp/m2-s2-closure/head-5de30674bc82-<guid>/` after a member check, then writes the manifest `head-5de30674bc82.json` last (archive hash, every file hash, the folder name, worktree fingerprint). Reads the repository only; creates no Git worktree, branch or ref. Later actions use the folder the manifest names, re-hash it before the run and again after it. A folder left by an interrupted run has no manifest and does not block a new run; an existing manifest does. Expected 627 files | 1 |
| C2 | `ruff-worktree`, `ruff-head` | Ruff 0.17.2 (`--no-cache`, JSON output) on the six S2 source paths in the worktree and in the snapshot; each also records the file list Ruff reports for those paths (`--show-files`) and requires it to equal the six paths, requires every diagnostic path to be one of the six, and requires the exit code to agree with the diagnostics; otherwise the capture is marked incomplete | 1 each |
| C3 | `mypy-head` | Mypy on `src/sketch2life` of the HEAD snapshot, same options as the mapper task's check; the capture is complete only if nothing is unparsed, Mypy was not blocked, and the exit code agrees with the error count | 1 |
| C4 | `delta` | No tool run. Compares diagnostic multisets (path, severity, code, message; no line numbers). Mypy worktree side: the mapper task's post manifest, which the driver requires to hash to `56D6B692596DE1239E4B70FF3F1A880B05254A0A104ACDE7EF612C522C730256` and to be a complete Mypy post capture; the seven source hashes it was measured on are enforced by the preflight. The other three inputs must be complete captures of the right action and tree, made by this driver at this HEAD with the worktree unchanged, with the same tool versions on both sides, and, for the two HEAD captures, on the current snapshot found intact after the run; any violation is listed and the result is marked not valid. A HEAD side with zero diagnostics against a non-empty worktree side is flagged as suspect | 1 |
| C5 | `pytest-collect` | `pytest --collect-only` on the nine files (the `-q` of `pyproject.toml` applies; no second `-q`). Imports the test modules and the application; runs no test. Passes only with exit code 0, a non-zero collected count and no collection error line. The count is read from the summary line, or failing that from the node ids or per-file counts, and the source used is recorded | 1 |
| C6 | `pytest` | One invocation of the nine-file selection of the 2026-11-14 report with `-ra`, `-p no:cacheprovider`, a fresh `--basetemp` under the run folder, a JUnit file, and `faulthandler_timeout=600`, which makes pytest write every thread's stack to the console if a test runs longer than 600 s, before the 900 s driver timeout. Expected about 84 tests (82 on 2026-11-14 plus the two the mapper task added); the number C5 reports is the reference | 1, no retry |

C2 to C5 can be repeated as they are under a new owner instruction if the driver misbehaves; C1 can be repeated only after the owner removes its manifest. C1 to C5 exercise all shared driver code before C6, except the timeout path. The C6 ceiling is consumed when the pytest child process has been started, and only then.

The nine pytest files: `tests/contract/test_parent_story_run_request_contract.py`, `tests/contract/test_parent_story_run_cancel_route.py`, `tests/contract/test_parent_ai_late_result_guards.py`, `tests/contract/test_app_composition.py`, `tests/contract/test_assistance_request_contracts.py`, `tests/contract/test_assistance_requests_api.py`, `tests/contract/test_openapi_contract_catalog.py`, `tests/unit/test_parent_story_run_create_service.py`, `tests/unit/test_parent_story_run_cancel_repository.py`.

The six Ruff paths: `src/sketch2life/application/ports/parent_story_runs.py`, `src/sketch2life/contracts/schemas/parent_story_runs.py`, `src/sketch2life/infrastructure/persistence/parent_story_repository.py`, `src/sketch2life/interfaces/http/routers/parent_story_runs.py`, `src/sketch2life/interfaces/http/routers/parent_ai.py`, `src/sketch2life/interfaces/http/app.py`.

C2, C3 and C4 are measurements, not gates: whatever they report is recorded.

## 4. Proposed closure conditions (for the owner to accept or change)

1. C6: exit code 0, not timed out, zero failures, zero errors, a non-zero test count, `worktreeUnchanged` true. Skipped tests, if any, are listed by name in the result.
2. C4: the result is marked valid, and it shows zero Mypy diagnostics and zero Ruff diagnostics added by the uncommitted work. Diagnostics that also exist at HEAD are existing debt: recorded with counts, tracked as a separate follow-up, and not a blocker for closing S2.
3. If C4 shows added diagnostics, S2 is not closed on this evidence; fixing them needs its own allowlist approval, and the fix would change the code C6 ran on.
4. If C6 fails or times out: C1 to C5 stay recorded, S2 is not closed, and a further pytest invocation needs an owner-approved amendment.
5. Items 4 to 6 of section 2 dispositioned in writing.
6. The three repository validators and `git diff --check` exit 0 after the final documentation edits.

Closing S2 remains a separate owner decision after the evidence is reported.

## 5. Owner decisions requested with the approval

- **D1 — egress block.** (a) Require the operating-system egress block for C5 and C6, which import and execute application code (the driver's `--require-egress-block` stops before launch otherwise); C1 to C4 run without it; or (b) run everything without it, as the S2 checks of 2026-11-14 did, and record that. Recommendation: (a).
- **D2 — FEAT-047 overlay, decided before the first action.** Keep the description on the `be1_artifacts.py` route decorator, or revert it. Recommendation: keep. Its hash is a pinned input of the accepted mapper evidence and of this driver, the text equals the catalog purpose, and the FEAT-047 record carries its approval. A revert after any action would invalidate C3, C4 and C6. A revert at any time also means the driver stops in preflight (it pins that file), the reused Mypy manifest no longer applies, and the driver would have to be changed, re-pinned and reviewed again before anything runs.
- **D3 — existing debt.** Accept that Mypy and Ruff diagnostics present at HEAD are outside S2 (closure condition 2).
- **D4 — review.** Whether this revision and the revised driver get a delta review by Sonnet 5.5 high before approval.

## 6. Risks and limits

- C6 has never run in this environment as a whole. Seven of the nine files last ran on 2026-11-14 in a different environment and with the developer's own environment variables. The reviewer read the nine files and found that they set the flags they need themselves and need no live database or network; that is a reading, not a run. C5 reduces the import and collection risk only.
- The hang of 2026-11-14 is unexplained. The timeout bounds it and the streamed console keeps partial output, but a timeout still consumes the C6 ceiling.
- The `tmp_path` permission error of 2026-11-14 is addressed by the fresh `--basetemp`; in the mapper task the affected node passed with the same measure.
- No action of the driver has been executed. C1 to C5 will be its first runs. The timeout path, including the process-tree termination, is exercised by none of them.
- The Ruff `--show-files` output format was not verified; if it is not what the driver expects, C2 is marked incomplete (fail closed) and has to be repeated after a driver fix.
- The whiteboard artifact root defaults to a relative `.runtime/whiteboard` path that the driver does not redirect. The reviewer believes it is used only when a pipeline is configured that this environment does not configure. The `backend/.runtime` probe in the fingerprint would show a write there.
- The HEAD snapshot contains only `backend/src` and `backend/pyproject.toml`. The reviewer found no other configuration file and no import from sibling directories; that the tools behave identically there is not verified by a run. The snapshot lies under a git-ignored folder; the recorded Ruff file list is the guard against Ruff skipping it.
- The comparison ignores line numbers, so a diagnostic that moved is not counted as added, and one that was fixed while an identical one was introduced in the same file cancels out. Conversely, some Mypy and Ruff messages embed a line number in their text; if such a diagnostic shifts in a changed file it appears as one added and one removed entry and has to be read by hand.
- The egress probe reports "not connected" for a refusal and for a timeout alike. The firewall rules of the mapper task may have been removed; under D1 (a) they have to be re-created and the third-party firewall product paused.
- M2-S2 remains PARTIAL / NOT COMPLETE.

## 7. Disposition of review R1

| Finding | Disposition in this revision |
|---|---|
| 1 (P1) no timeout, buffered output | Timeouts per child; output streamed to files; `timedOut` recorded; `-ra` added |
| 2 (P2) UTF-8 mode | Children and the driver itself run with `-X utf8`; driver console writes use replacement on encoding errors |
| 3 (P2) `.env` | Preflight stops if a `.env` exists at the worktree root or in `backend/`; text corrected |
| 4 (P2) unchecked `delta` inputs | Manifest hash, completeness, action and tree, HEAD, driver hash and worktree-unchanged checks; seven source hashes enforced in preflight and recorded; preflight now runs for `delta` too |
| 5 (P2) no record of inputs | Input hashes, tool versions, driver hash, distribution count and before/after worktree fingerprint in every result; snapshot manifest written and verified |
| 6 (P2) order, consumption, D2 timing | Order fixed with pytest last; consumption defined; D2 before the first action; `pytest-collect` added as C5 |
| 7 (P3) mapper coverage wording | Corrected: one file fully, one node of a second, seven files not run; expected count stated |
| 8 (P3) statements not matching the driver | Driver changed so the statements hold |
| 9 (P3) messages embedding line numbers | Added to section 6 |
| 10 (P3) leftover snapshot folder, extraction filter, git stderr | Partial folder and rename; `filter="data"`; git stderr included in the stop message |
| 11 (P3) Ruff on a git-ignored path | File list recorded and required to match; zero-against-non-zero flagged |
| 12 (P3) skipped test names | Listed in the result |
| 13 (P3) probe label | Relabelled "not-connected" |
| 14 (P3) distribution count wording | Reworded; count recorded |

### Disposition of delta review R2

| Finding | Disposition in revision 3 |
|---|---|
| P1-1 collection count lost under double `-q` | Extra `-q` removed; count read from the summary line, else node ids, else per-file counts; source recorded; collection error lines counted |
| P2-1 extra arguments ignored | Exact argument count required; anything else stops before preflight |
| P2-2 timeout kills only the top process | Process tree terminated with `taskkill /F /T`, then the child is killed and awaited |
| P2-3 hung test cannot be named | `faulthandler_timeout=600` on C6 |
| P3-1 snapshot without record | Snapshot manifest carries fingerprints and `worktreeUnchanged` |
| P3-2 C1 not repeatable after an interruption | Unique folder per run, manifest written last and naming the folder |
| P3-3 Mypy exit code not cross-checked | Completeness requires agreement of exit code and error count |
| P3-4 versions and snapshot hash not compared | `delta` compares tool versions and requires the HEAD captures to carry the current snapshot manifest hash and an intact-after-run flag |
| P3-5 file list output not hashed | Written at the top level of the run folder and hashed |
| P3-6 Ruff path handling | Paths joined with the backend directory first; an inexpressible path is treated as a mismatch |
| P3-7 misleading stop while finishing | A Git failure while finishing is recorded as an unavailable fingerprint and the result is still written |
| P3-8 inherited standard input | Null device |
| P3-9 driver UTF-8 mode not enforced | Preflight requires isolated UTF-8 mode |
| P3-10 fingerprint blind to ignored paths | Probes of `backend/.runtime`, cache folders and `__pycache__` counts added; whiteboard root disclosed in section 6 |
| P3-11 D2 revert needs a driver re-pin | Stated in D2 |
| P3-12 preconditions not enforced | Preflight requires exactly the seven modified source files; snapshot re-hashed after each HEAD run |
