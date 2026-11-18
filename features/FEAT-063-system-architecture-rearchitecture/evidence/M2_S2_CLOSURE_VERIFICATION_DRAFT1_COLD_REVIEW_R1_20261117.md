# FEAT-063 M2-S2 Closure Verification Draft 1 — cold review R1 — 2026-11-17

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) at the owner's instruction ("Review Sonnet").
- **Pins reviewed:** `plan/M2_S2_CLOSURE_VERIFICATION_TASK_APPROVAL_DRAFT1_20261117.md`, 9,419 bytes, SHA-256 `ABB2AC7B0045BEB3692B75E0F96D5F86C927C2294E88CB72C0EE023BB420F1D9`; driver `s2_closure_driver.py` (outside the worktree), 13,491 bytes, SHA-256 `E067B6F63EABFD9039538756AA6593EB224A1A5357431F119AA0399A0DAAB624`. The reviewer states both matched and that it made no writes and ran no project code.
- **Verdict:** NOT READY — P1=1, P2=5, P3=9. No defect that stops the driver from starting; the findings concern what a one-shot pytest run would record or lose, unverified inputs of the comparison, and statements in the draft.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Findings

| ID | Sev | Finding | Reviewer's smallest fix |
|---|---|---|---|
| 1 | P1 | Children run with `capture_output` and no timeout; output is written only after exit. The 2026-11-14 report records this selection once hanging without output. A hang would consume the pytest ceiling and leave no evidence. | Add timeouts, record a timeout in `result.json`, stream child output to files, add `-ra`. |
| 2 | P2 | `PYTHONUTF8=1` has no effect under `-I`; the approved runner passed `-X utf8`. A failure diff with non-ASCII text could break console capture. | Pass `-X utf8` to every child; make the driver's own console writes tolerant. |
| 3 | P2 | "dotenv disabled" is not what the driver does: the settings class reads a `.env` at the worktree root through pydantic-settings. No such file exists today, but nothing guards against one. | Stop in preflight if a `.env` exists in the worktree; reword the draft. |
| 4 | P2 | `delta` accepts any four JSON files: no manifest hash check, no completeness check, no check that the seven source files still have the hashes the reused Mypy manifest was measured on, no preflight. | Verify all of these and record the seven hashes. |
| 5 | P2 | No record of what was tested: no hashes of test and source inputs, tool versions, driver hash; the snapshot writes no result file and is not integrity-checked later; the "writes nothing into the worktree" claim cannot be checked from the output. | Record them; write and verify a snapshot manifest; fingerprint the worktree before and after each action. |
| 6 | P2 | Run order not specified; nothing exercises the shared driver code before the non-repeatable pytest run; "ceiling consumed" not defined; decision D2 (keep or revert the overlay) must precede the first action because it changes the code under test. | State the order with pytest last; define consumption as "the pytest child started"; optionally approve a `--collect-only` call first; decide D2 first. |
| 7 | P3 | Draft says the mapper task ran two of the nine files; it ran one of them fully and one node of a second (its third selection is not among the nine). Seven files have not run since `app.py` changed. Expected count about 84. | Correct the text. |
| 8 | P3 | "before every action" and "result.json with file hashes" do not hold for `delta` and `snapshot`. | Fix driver or text. |
| 9 | P3 | Some Mypy and Ruff messages embed line numbers; a shifted one would appear as one added and one removed. | Add to the limits. |
| 10 | P3 | A rejected archive member leaves the snapshot directory behind and blocks a re-run; `extractall` without a filter warns on Python 3.12; git's stderr is discarded. | Extract to a partial directory and rename; pass `filter="data"`; keep git's stderr. |
| 11 | P3 | Question, not verified: the snapshot lies under a git-ignored `tmp/`; if Ruff skipped it, the HEAD side would report zero and everything would look added. | Guard: treat HEAD zero against worktree non-zero as suspect, or record the files Ruff will check. |
| 12 | P3 | Skipped test names are not listed, only counted. | List them. |
| 13 | P3 | The probe labels a timeout as "refused". | Cosmetic. |
| 14 | P3 | "108 distributions equal to the lock resolution" is historical; the driver verifies only the interpreter hash. | Record the count; reword. |

The reviewer also noted that the draft's "32 errors" in the seven changed files includes notes (32 signatures).

## Reviewer's "checked and found correct" (summary)

Driver imports and argument handling under isolated mode; all nine test files and six Ruff paths exist and their pins match the 2026-11-14 report or the mapper evidence; interpreter, Git executable, HEAD and empty index; `git status` shows exactly seven modified files under `backend/src`; the JUnit attribute order against a real file of this pytest version; pytest configuration and `pythonpath` handling under isolated mode; the nine files set the flags they need themselves and need no live database or network; the cleared environment has the same 26 names as the approved runner's; `git archive` is read-only, the member check is adequate for the current tree, the snapshot layout is what the driver looks for, 626 source files on both sides, no configuration outside `pyproject.toml`; Mypy and Ruff signature parsing identical to the approved child bootstrap; multiset arithmetic correct; draft counts (353, 327, 32).

## Reviewer's "not checked"

Nothing was run. Behaviour of pytest under a non-UTF-8 console, of Ruff on git-ignored explicit paths, and of isolated mode on `PYTHONUTF8` is from tool knowledge. Cause of the 2026-11-14 hang. Whether the firewall rules cover the base interpreter the venv launcher starts. Whether every code path reached by the nine tests avoids relative writes into the worktree. The 65-file and 17-diagnostic counts. Antivirus interference with new run folders.

## Disposition by the coordinating session

All findings are addressed in a revised driver and a revised draft; the new pins are stated in the revised draft. The revision has not been re-reviewed.
