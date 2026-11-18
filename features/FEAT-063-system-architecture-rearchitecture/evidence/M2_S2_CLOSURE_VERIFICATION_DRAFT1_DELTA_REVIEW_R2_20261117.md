# FEAT-063 M2-S2 Closure Verification Draft 1 revision 2 — delta review R2 — 2026-11-17

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) at the owner's instruction ("Review delta").
- **Pins reviewed:** `plan/M2_S2_CLOSURE_VERIFICATION_TASK_APPROVAL_DRAFT1_20261117.md` revision 2, 14,847 bytes, SHA-256 `A08FB8BCE66D1DCAA875C72886C829BAE07220841D792688E75FDE67812293F6`; driver revision 2 (outside the worktree), 22,559 bytes, SHA-256 `2128FF58A6FB4EAAB180ACF49F408D5E70B7DCDED19EF21D92A6FA5E057B66BE`; R1 record SHA-256 `A37049D2B9BC9A43283D4E8BE1841F217E1396C7D5A8E2515B8967818B268A54`. The reviewer states all matched.
- **Reviewer's own disclosure:** no file written and no project code run; two read-only commands outside the listed examples were run: a trivial `python -I -c "print(1)"` on the system interpreter, and a plain `git status --porcelain` without `--no-optional-locks`, which can refresh the worktree's Git index file. The coordinating session's later checks found the worktree at the same row count with nothing staged.
- **Verdict:** NOT READY — P1=1, P2=3, P3=12.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Status of the R1 findings in revision 2

Fixed: 1 (with the caveats P2-2 and P2-3 below), 2, 3, 4, 6, 7, 9, 10, 11 (fails closed), 12, 13, 14. Partly: 5 and 8, because the `snapshot` action wrote no result record with a worktree fingerprint and one output file was not hashed.

## New findings

| ID | Sev | Finding | Reviewer's smallest fix |
|---|---|---|---|
| P1-1 | P1 | `pytest-collect` passed `-q` on top of the `-q` in `pyproject.toml`; at that verbosity this pytest version prints per-file counts and no "N tests collected" line, so a good collection would be recorded as not passed with no count. From reading the installed pytest source, not from a run. | Drop the extra `-q`, or sum the per-file lines. |
| P2-1 | P2 | A non-delta action accepted extra arguments; a mistyped egress flag would be ignored and the action would run without the block. | Require exactly the expected argument count. |
| P2-2 | P2 | On timeout only the top process is terminated; the venv launcher, the real interpreter and tools they start may survive and keep files open. Launcher behaviour not verified. | Terminate the process tree. |
| P2-3 | P2 | A hung pytest run would show only dots and no JUnit, so the hung test could not be named. | `faulthandler_timeout` below the driver timeout, or verbose node ids. |
| P3-1 | P3 | `snapshot` writes no fingerprint or `worktreeUnchanged`. | Record them or state the exception. |
| P3-2 | P3 | C1 is not repeatable; an interruption between the folder rename and the manifest write would block every later run until a manual delete. | Make the manifest name the valid folder. |
| P3-3 | P3 | Mypy completeness does not cross-check exit code against diagnostics. | Require consistency. |
| P3-4 | P3 | `delta` does not compare tool versions or record the snapshot manifest hash. | Compare and record. |
| P3-5 | P3 | The `--show-files` output file is in a subfolder and not hashed. | Hash it. |
| P3-6 | P3 | Ruff path handling assumes absolute paths; a relative path would be resolved against the wrong directory (fails closed), and an unusual prefix could raise after both runs. | Join with the backend directory first; catch the error. |
| P3-7 | P3 | A Git failure while finishing would print "nothing launched" after a tool ran, and leave no result file. | Handle it and still write the result. |
| P3-8 | P3 | Children inherit standard input. | Use the null device. |
| P3-9 | P3 | The driver's own `-X utf8` is not enforced. | Check the flag. |
| P3-10 | P3 | The fingerprint cannot see git-ignored paths or empty directories; the whiteboard artifact root default is a relative path that is not redirected (believed unused in this environment). | Probe ignored locations. |
| P3-11 | P3 | A D2 "revert" would also require re-pinning and re-reviewing the driver. | Say so. |
| P3-12 | P3 | The "exactly seven uncommitted source files" precondition is not enforced; the snapshot is verified before a run but not after; sibling directories absent from the snapshot have no effect today (no import found). | Enforce; verify after. |

## Reviewer's "checked and found correct" (summary)

Argument handling for `delta`; the 26 child environment names; import resolution under isolated mode; JUnit structure against a real file; Mypy parsing identical to the approved child bootstrap; archive extraction with the data filter, no symlinks, path lengths; snapshot manifest keys; no tool writes into the snapshot; `delta` key names and no path by which an incomplete or wrong input yields a valid result; the draft's statements on order, timeouts, expected 627 files, pass logic and skipped names; all seven source pins against the S2 report, the mapper evidence and the actual files.

## Reviewer's "not checked"

Nothing was executed. Ruff's `--show-files` output format, the venv launcher's process behaviour, antivirus effects on new folders, the cause of the 2026-11-14 hang, and the expected test count (about 84) are unverified.

## Disposition by the coordinating session

All findings are addressed in driver revision 3 and draft revision 3; the new pins are stated in the revised draft. Revision 3 has not been re-reviewed. After the change the coordinating session ran three static checks on the driver file only: a syntax parse, Ruff rules F, E9 and B with `--isolated` (clean), and two invocations with invalid arguments, which stopped in argument checking before the preflight and launched nothing.
