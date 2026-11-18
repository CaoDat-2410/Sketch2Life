# FEAT-063 M2-S3 Draft 9 — cold review R2 — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Opus 5.5, effort set to high by the caller, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) under the owner's instruction to proceed through the S3 steps. Review round 2 of the S3 plan (round 1: Draft 8).
- **Pin reviewed:** `plan/M2_S3_TASK_APPROVAL_DRAFT9_20261118.md`, 37,494 bytes, SHA-256 `8B8C2DF16D5E1552B0B62E61DA3D63954C7D555E2F6B5506305C18BADD2F97E2`, at HEAD `4cfd1412a4812cc862e3de00397c29c9c5b8c945` with `DECISIONS.md` carrying the uncommitted D-210 and D-211 rows. The reviewer states pin, HEAD and working tree matched, that `DECISIONS.md` is append-only against HEAD, and that it made no writes, ran no test, validator or application code, and connected to nothing.
- **Verdict:** NOT READY — **P1=0, P2=1, P3=12**. The P1 and P2 count fell from 7 to 1. The single P2 would stop S3 at the inventory step. Otherwise the reviewer finds the draft close: pins, precondition, decision table and departures are largely accurate.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 finding

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| M1 | The 30 catalogued Lesson Library operations (`/api/lesson-library/v1/*`) fit no classification value. "Frozen compatibility surface" covers BE1, classroom and demo operations (D-171 item 7); the Lesson Library router is mounted outside both the classroom and the demo groups (`router_composition.py:35-77`) and the SRS names it as a separate group. "Mounted, no current authority — OPEN-OWNER" requires "outside the catalog", and these 30 are inside it. The draft makes an operation that fits no value a stop condition, so S3 would stop. Related: `GET /health` fits "classroom" only through a source comment; SRS section 9.6 arguably gives route-group authority to `/v1/me` and to the Parent drawing-guide and sketch-deck groups, which D-211 item 5 places under OPEN-OWNER. | An owner rule naming the value for the Lesson Library operations and `/health`: compatibility surface with a stated basis, or OPEN-OWNER extended to catalogued operations with no authority. |

## P3 findings (summary)

M2 `GET /v1/story-runs/active/current` is listed as an M2 target but its runtime summary begins "[PROPOSAL]": it carries two values and its contract card should say so. M3 the freeze names two flags; the export also recorded the StoryRun-lite demo flag as off, on which the seven Parent StoryRun operations depend, and the pilot and example flags take effect only in the local (or test) environment. M4 departure 4's line list is inaccurate (lines 397 and 408 do not concern client integration; lines 76, 264 and 409 are omitted); the narrowing of the "before D9 / N-1" block rests on D-210 item 1 and is not attributed; whether line 409 ("OpenAPI request/response/error parity được freeze trước client integration") still applies to the Parent operations is addressed by neither departure 3 nor 4. M5 the rule that the runtime spelling `{run_id}` is the frozen one settles D-151 condition C3 and is not marked "decided by approving this draft"; section 4 then calls C3 open. M6 M2 would also close with M2-AT-01 parts NOT RUN, M2-AT-04A and 04B PARTIAL and a PARTIAL part of M2-AT-10, which departure 1 does not list; the basis is D-210 item 3's narrowings, not "C4 applies"; "weakest part" has no defined order. M7 Draft 6 rules dropped silently: the ledger's exit-status column; "a 202/PENDING response is not proof of completed purge"; "membership alone does not establish target-contract status"; exact read paths with hashes (the draft allows two source folders and "a further input"); no pre-edit pin for `.gitattributes`. M8 commands are not runnable from one working directory as written (the interpreter is under the main checkout's `tmp`, the validators and feature paths in the worktree); `-I` missing on two commands; the extractor's input not named; no rule against rerunning to obtain a pass. M9 `git diff --check` skips untracked files; piping `git show` to a hash in Windows PowerShell 5.1 corrupts bytes; the post-commit hash check can run only after acceptance, an ordering not stated; `validate_skeleton` was dropped although the harness asks for it when structure is added. M10 "every input is pinned at a named commit" cannot be met while `DECISIONS.md`, Draft 8, its review and Draft 9 are uncommitted and outside the allowlist. M11 the approved S1a-P2 specification can be pinned now: `plan/M2_S1A_P2_TASK_APPROVAL_DRAFT7_20261112.md`, 40,474 bytes, SHA-256 `49B5352CA552DEC9C53C4B155C196C64FD0CE9115E844FC0CBFB8BF3613B66A1` (approval record lines 2530-2552 and 2563). M12 missing from the limitation list: S1a-P2 specifics (real-PostgreSQL PATCH, DELETE and list NOT VERIFIED; post-rework validators NOT RUN; production adapter NOT COVERED) and the baseline's "no list route in M2". M13 D-211's preamble says each item quoted the governing text; item 5 quotes none.

## Status of the previous round's findings (L1 to L16)

RESOLVED: L1 (the precondition check, computed now by the reviewer, gives exactly the expected result), L2 (every acceptance row gets a status from the named sources; none hits NOT ESTABLISHED), L4, L7, L8, L9, L10, L12, L13, L14, L15, L16. PARTIAL: L3 (M1), L5 (M4), L6 (M7), L11 (M12).

## Reviewer's classification tally of the 151 operations

M2 target 9 (one also "proposal" by its summary text); proposal 3; pilot-only 5 (all also BE1 compatibility); local example 3; OPEN-OWNER 11 (auth 2, platform-admin 3, Parent AI v1 3, Teacher AI v1 3); BE1 compatibility, non-pilot, 54; demo-group compatibility 35; `/health` 1; **no value: Lesson Library 30**. Total 151.

M2 target operations, all present in the runtime schema: `POST`, `GET` `/v1/parent/profiles`; `GET`, `PATCH`, `DELETE` `/v1/parent/profiles/{profile_id}`; `POST /v1/story-runs`; `GET /v1/story-runs/active/current`; `GET /v1/story-runs/{run_id}`; `POST /v1/story-runs/{run_id}/cancel`.

## Reviewer's precondition computation

`pinnedInputStates` (14 entries): all 11 non-test entries equal; one test module equal; two test modules differ. `changedPaths` under `backend/src` (7 entries): 6 equal; one differs, `infrastructure/persistence/parent_story_repository.py`. This equals the draft's expected result; S3 would not stop there.

## Pins

All 27 pins of the draft's section 8, the header hashes, the two schema files and the six hash-only citations match.

## Repeats (project rule D-171 item 11)

M1 is a narrower residual of L3, a P2 in the previous round, in the same class (operations without a classification value cause a stop); the previous review did not name the Lesson Library operations. M4, M7 and M12 are P3 residuals of L5, L6 and L11. The P1 and P2 count fell from 7 to 1.

## Not read or not verified (reviewer)

Most of the SRS beyond sections 9.6 to 9.9 and 21.1 to 21.4; most of foundation plan Draft 11; S2 Draft 18 beyond searches; the comparison report's contents; several S1a reports beyond searches; D-172 to D-187 and D-189 to D-195; the owner's chat selections behind D-210 and D-211; the meaning of "D9".

## Disposition by the coordinating session

Not yet addressed. Draft 9 is not revised. Because M1 is a residual of a P2 from the previous round, the work returns to the owner under D-171 item 11 for a decision on the classification of the Lesson Library operations and `/health`, and on whether line 409 of the baseline still applies to the Parent operations (M4). The other findings are drafting corrections.
