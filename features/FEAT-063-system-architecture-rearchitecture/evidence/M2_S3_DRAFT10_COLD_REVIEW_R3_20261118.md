# FEAT-063 M2-S3 Draft 10 — cold review R3 — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller (the reviewer notes it cannot see or set its own effort level), read-only by instruction (no sandbox enforcement). Started by the coordinating session (Fable 5.2) on the owner's instruction "Chạy R3 Sonnet". Review round 3 of the S3 plan (round 1: Draft 8; round 2: Draft 9). A first attempt at round 3 was stopped by the previous coordinating session before it reported; it produced no result and no record, and this run started from scratch.
- **Reviewer model rule:** the owner's rule of 2026-11-18 allows only Sonnet 5.5 at high effort for independent and cold reviews (`.claude/sketch2life-harness.md`). Rounds 1 and 2 ran on Opus 5.5 at high effort under the earlier rule (Sonnet 5.5 high or Opus 5.5 high).
- **Pin reviewed:** `plan/M2_S3_TASK_APPROVAL_DRAFT10_20261118.md`, 45,918 bytes, SHA-256 `34ACE27AAED0C699BA1C1C2ADC3D8FE036C202614AE04E56277131DE9139901B`, at HEAD `4cfd1412a4812cc862e3de00397c29c9c5b8c945` with `DECISIONS.md` carrying the uncommitted D-210, D-211 and D-212 rows (229,409 bytes, SHA-256 `55C22A4C09C5F92F3BC844A4131DDC3B1C2C8BB3E6182131BDFBD29BC38E9A8D`). The reviewer reports preflight matched (HEAD, five commits ahead, 0 staged, the expected six uncommitted paths and their hashes) and that `DECISIONS.md` is append-only against HEAD, with prefix hashes equal to the before-append pins of D-210, D-211 and D-212.
- **What the reviewer did not do (its statement):** no write outside its scratch folder `tmp/m2-s3/review-r3/` (read-only parse scripts and their outputs); no test, validator run, application code, export, Alembic, database, port or network use; the gate secret directory not read. One mistyped shell command hung and was stopped; nothing was left running.
- **Verdict:** NOT READY — **P1=0, P2=2, P3=9** (the reviewer's table lists N1 to N10; N4 to N10 are P3 except as stated). The P1 and P2 count rose from 1 (round 2) to 2, so under criterion 8 of the draft and D-171 item 11 the work returns to the owner. Otherwise the reviewer finds the tally, pins, flags, precondition check, quotations and departures verified.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| N1 | Step 0 commits the approval entry for this draft (an append to `approvals/TASK_APPROVAL.md`) and possibly a `DECISIONS.md` row, while section 8 pins those files (and `STATUS.md`, `CONTEXT.md`) at their current state. Step 1 stops on any pin difference, and criterion 1 requires every input to be present in the base commit of step 0. S3 would therefore stop at step 1. A side effect of the M10 fix. | Pin each appended file as a prefix (first N bytes hash to H; the rest is only the step-0 entry), or state that step 1 re-pins from the step-0 commit and verifies the delta is exactly that entry, or keep the approval entry in a separate unpinned file. |
| N2 | Criterion 8 still allows "Sonnet 5.5 high or Opus 5.5 high"; the harness now allows Sonnet 5.5 high only and says a review on another model does not count. The draft does not say whether rounds 1 and 2 (Opus, under the earlier rule) count toward the five-round cap. The reviewer notes a strict owner could treat this as P3. | Criterion 8: Sonnet 5.5 at high effort only, Opus and Fable not allowed, model and effort recorded; one sentence on whether rounds 1 and 2 count as rounds. |

## P3 findings (summary)

N3 (residual of M9) the two-commit plan does not say the step-0 commit is a separate finished task (precedent `a83bf4f0`, `67ef7d7c`); the post-commit hash check "recorded in an appended entry" leaves an uncommitted change or needs a third commit; step 0 has no security validator or `git diff --check` before its commit. Fix: name step 0 as the S3 approval-records task; check the staged blob with `git show :<path>` before the S3 commit; add the checks to step 0. N4 the section 3.5 spelling rule (`{run_id}` against the SRS `{id}`, DIFFERENT and OPEN) combined with D-212 item 2 makes `GET /v1/story-runs/{run_id}` and the cancel operation "not until closed" for a placeholder name alone; the draft does not say so (SRS lines 805 and 1164). Fix: state the consequence or ask the owner whether a placeholder-name-only difference counts. N5 classification ambiguities: `mount_classroom_routers` also mounts the five Parent profile operations, `/health` and five auth and platform-admin operations, so those eleven literally fit "frozen compatibility surface" too (`router_composition.py:35-42`); "proposal 3" omits the active-run read's second value. Fix: a precedence rule (target, outside-scope and OPEN-OWNER over compatibility); tally "proposal 3 (+1 second value)". N6 (residual of M4) departure 4's quotation "trước D9 hoặc frontend/client integration" is verbatim only on baseline lines 317 and 396; lines 76, 264 and 407 read "D9/client integration"; the same sentences require this before exiting S2, which S2 did not meet, and the draft does not name that. N7 baseline section 7 items 1 (per-requirement table, line 404) and 5 (owner approval of target migration, schema inventory, data disposition, rollback limits, line 408) are neither mapped nor listed as departures. N8 (residual of M8) command gaps: no command for the syntax check (`py_compile` would write bytecode; ruff already catches syntax errors); no tool named for the drive-letter search; the precondition comparison has no permitted script (only one scratch script, which reads no other file); step 1 does not recompute the section 3.1 hashes or the six hash-only citations; the extractor input path is feature-relative while commands run from the worktree root; run-count ceilings but no time ceiling. N9 step 3 reads "D-196 to D-211" while section 1 lists D-110 and D-196 to D-212; section 8 "not read" omits D-212 and D-199 to D-206. N10 section 8 mixes repository-root and feature-relative paths without saying so.

## Status of the previous rounds' findings

- **R2 (M1 to M13):** RESOLVED M1, M2, M3, M5, M6, M7, M11, M12, M13; RESOLVED with a P3 residual M4 (N6), M8 (N8), M9 (N3); PARTIAL M10 (N1).
- **R1 (L1 to L16):** all RESOLVED; residual notes on L6 and L9 (N8), L8 (N3), L12 (N2).

## Reviewer's classification tally of the 151 operations

M2 target 9 (one also proposal); proposal 3 (+1 second value); pilot-only 5 (also compatibility); local example 3; OPEN-OWNER 11; BE1 compatibility, non-pilot, 54; demo-group compatibility 35; outside the M2 scope 31 (30 Lesson Library, `/health`). Total 151; every operation fits a value, so no stop condition fires. Path-prefix cross-check: `/api/be1` 59, demo 35, Lesson Library 30, Parent 12, OPEN-OWNER 11, storage example 3, `/health` 1. Runtime 151 operations on 134 paths; projection 34 on 24, all inside the runtime set; catalog `MOUNTED_OPERATION_COUNT` 134.

- M2 target operations: `POST` and `GET /v1/parent/profiles`; `GET`, `PATCH`, `DELETE /v1/parent/profiles/{profile_id}`; `POST /v1/story-runs`; `GET /v1/story-runs/active/current`; `GET /v1/story-runs/{run_id}`; `POST /v1/story-runs/{run_id}/cancel`.
- OPEN-OWNER operations: `POST /api/auth/v1/registrations`; `GET /api/auth/v1/me`; `GET` and `POST /api/platform-admin/v1/accounts`; `PATCH /api/platform-admin/v1/accounts/{account_id}`; `POST /api/parent/v1/ai/sketch-guides`; `POST /api/parent/v1/ai/drawing-understandings`; `POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions`; `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions`, `.../ai/sketch-decks`, `.../ai/lesson-visuals`.
- Proposals: the `context-confirmation`, `subject-confirmation` and `script-confirmation` operations under `/v1/story-runs/{run_id}`.
- Cancel: uncatalogued (12th entry of the test constant), summary only, absent from the projection; responses 202, 400, 401, 403, 404, 409, 422, 500, 503.

## Pins and checks re-verified by the reviewer

- All 29 rows of section 8, including the `.gitattributes` pre-edit pin (11,853 bytes, equal to the HEAD blob); the header hashes (Drafts 6 to 9, the Draft 7 review, R1, R2); both schema files and the six hash-only citations.
- Both schema files are CRLF on every line; `git check-attr` currently reports text auto and eol lf, so the proposed `-text whitespace=cr-at-eol` line is required and matches the repository's existing form.
- The security validator's patterns, applied by hand to both JSON files and to Draft 10: no hits, no drive-letter paths.
- Precondition check recomputed: `pinnedInputStates` 14 entries — 11 non-test equal, `test_app_composition.py` equal, `test_openapi_contract_catalog.py` and `test_openapi_schema_catalog_mapping.py` differ; `changedPaths` under `backend/src` 7 entries — 6 equal, only `parent_story_repository.py` differs; `git diff 7cc5cf74 HEAD -- backend/src` touches only that file. Exactly the expected result.
- Flags and environment of section 3.2 match `environment.json` (local environment, storage-example and pilot flags enabled, StoryRun-lite demo flag disabled; isolation and absence proofs all false).
- The S3 row quotation and the five departure quotations word for word (except N6); line numbers 76, 264, 317, 392, 396, 398, 407, 409 correct; decision table rows 1 to 13 match D-210 to D-212; section 5 S2 debt figures match the closure evidence.

## Repeats (D-171 item 11)

No finding repeats a P2 of round 1 or 2. N1 is a new defect in the class of M9 and M10 (pin against commit ordering), caused by the M10 fix. N3, N6 and N8 are P3 residuals of M9, M4 and M8. The P1 and P2 count did not fall (1 to 2): the work returns to the owner on that rule.

## Not read or not verified (reviewer)

The full SRS beyond searches around section 21.2; the full baseline; D-199 to D-206 and the rest of D-110, D-188 and D-198 beyond the quotations in D-210 to D-212; the S1a specifications, closure records and implementation reports beyond searches; foundation plan Draft 11 rows; the comparison report's contents; `AGENTS.md` in full; whether the validators of section 6 pass (not run); the gate G1 deviations DV-1 to DV-19 beyond spot checks; the owner's acceptance of the mapper egress deviation; the meaning of "D9".

## Disposition by the coordinating session

Not yet addressed. Draft 10 is not revised. The work returns to the owner under D-171 item 11 because the P1 and P2 count did not fall.
