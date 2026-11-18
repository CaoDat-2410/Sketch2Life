# FEAT-063 M2-S2 closure verification — evidence — 2026-11-17

- **Status:** EVIDENCE REPORT / NOT OWNER-ACCEPTED. All six closure-verification actions have run. M2-S2 is NOT CLOSED: closing it is the owner's decision and has not been given. M2-S2 remains PARTIAL / NOT COMPLETE.
- **Author:** coordinating Claude session (Fable 5.2); owner Person 2. This report, revision 3 of the approved draft and of the driver, and the Mypy triage in section 4 were not independently reviewed.
- **Authority:** `plan/M2_S2_CLOSURE_VERIFICATION_TASK_APPROVAL_DRAFT1_20261117.md`, revision 3, 20,007 bytes, SHA-256 `0FA1C880907C8864BF2DF1C0A2A76CE8220DE4A381471986949E6543C1343549`. Approved in two steps recorded in `approvals/TASK_APPROVAL.md`: C1 to C5 with decisions D1 to D3, then C6 with the decision on the added Mypy diagnostics. After the C6 result entry that record was 475,283 bytes, SHA-256 `69D6E22929F0F0300874C21D78B4B7AF8B36BE5A5BCADAC8BF753B84454F0F4A`.
- **Reviews of the plan:** cold review R1 (NOT READY, 1 P1 / 5 P2 / 9 P3) and delta review R2 (NOT READY, 1 P1 / 3 P2 / 12 P3), both Sonnet 5.5, effort high: `evidence/M2_S2_CLOSURE_VERIFICATION_DRAFT1_COLD_REVIEW_R1_20261117.md`, `evidence/M2_S2_CLOSURE_VERIFICATION_DRAFT1_DELTA_REVIEW_R2_20261117.md`. Revision 3 addressed their findings and was approved without a third review.
- **Where:** worktree `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`; nothing staged or committed. Driver and all run outputs are under the git-ignored repo-root `tmp/m2-s2-closure/` (local only; identified here by hash). Driver `s2_closure_driver.py`, 28,728 bytes, SHA-256 `DFE6A9188D8296EC1D7E4D0E3C38CAE0C12FC8385711F7AC784AF687CA2ECFBD`. Interpreter SHA-256 `0B471133E110CFB53A061CAD528CE8E517D7B9AC41A0A396C39AD795A487FC14`, 108 installed distributions, pytest 8.4.2, Mypy 1.20.2, Ruff 0.17.2.

## 1. Results

Each action ran once. Every result records the worktree fingerprint as identical before and after the action.

| Action | Result | `result.json` SHA-256 (manifest for C1) |
|---|---|---|
| C1 `snapshot` | HEAD `backend/src` and `backend/pyproject.toml` extracted, 627 files | `0CE4BC3A3CEE1F1B088E323CDF030431E6D0A865604A1CDA4389F0F2D9977C8B` |
| C2 `ruff-worktree` | 17 diagnostics on the six S2 source paths; complete capture; file list equals the six paths | `1C1AE2783C6F3D8E74D03114F9CC57D43641D7264D2A47E70B998C2EAFA8D70E` |
| C2 `ruff-head` | 17 diagnostics; complete capture; file list equals the six paths | `4538F49FCE50065667BCAAC66D5B845C7B68E98A7A20BEF9D3E7C6EAFC61D58A` |
| C3 `mypy-head` | 336 signatures; complete capture | `34964F0C316C1DFD1AC0E86F2E6FB76371F41BA39363E4224DD4D464FF98E65D` |
| C4 `delta` | Valid. Ruff: 0 added, 0 removed. Mypy: worktree 353, HEAD 336, 19 added, 2 removed | `62A0531694B29BD85F8CB97115F5B621B09014AE401D92C5C2ADEF187C00BA62` |
| C5 `pytest-collect` | Exit code 0; 84 tests collected; no collection error; egress block required and in effect | `7D602A87B4E78F66BA8B2EFA72000ADB728A2F03DB9BCBA47594B2994A36D5FD` |
| C6 `pytest` | Exit code 0; 84 tests, 0 failures, 0 errors, 0 skipped; not timed out; 17.85 s; egress block required and in effect | `D2C9A1AF492E4EA41E46DDD0CCA628AAE4F537207A10CD88E332C3F1AE88588A` |

C6 run root: `tmp/m2-s2-closure/runs/pytest-cea74c55352445e986b0a11b3ea80b01`; `junit.xml` SHA-256 `35036081CCC87083BD3145E647C455915E7F120DC8C539A743BEB546339851AF`; `console.txt` SHA-256 `F9AACDC50AF1D6C4503F04D1499B527E54F8039329F69A9BAD598E86DE46D63B`.

The Mypy worktree side of C4 is the mapper task's post-check manifest (`run-manifest.json` SHA-256 `56D6B692596DE1239E4B70FF3F1A880B05254A0A104ACDE7EF612C522C730256`), reused because the seven uncommitted source files still have the hashes it was measured on; the driver enforced those hashes before every action.

Egress: C5 and C6 were started with the egress block required, and both probe connections were refused (Windows error 10013). C1 to C4 ran without requiring the block, as approved (decision D1); each of their results records what the probe saw at the time (the network was reachable when C1 ran; the owner re-created the firewall rules while C3 and C4 were in progress). The results do not prove network, database or provider isolation.

## 2. What was tested

- C6 is the nine-file selection of `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md`: `tests/contract/test_parent_story_run_request_contract.py`, `tests/contract/test_parent_story_run_cancel_route.py`, `tests/contract/test_parent_ai_late_result_guards.py`, `tests/contract/test_app_composition.py`, `tests/contract/test_assistance_request_contracts.py`, `tests/contract/test_assistance_requests_api.py`, `tests/contract/test_openapi_contract_catalog.py`, `tests/unit/test_parent_story_run_create_service.py`, `tests/unit/test_parent_story_run_cancel_repository.py`. The count is 84: the 82 of 2026-11-14 plus the two tests the mapper task added.
- The hashes of the nine test files, the seven source files, `pyproject.toml` and `uv.lock` at the time of each run are in the result files.
- The seven uncommitted source files (the six S2 source paths and `interfaces/http/routers/be1_artifacts.py`) are the whole of the uncommitted change under `backend/src`; the driver enforced that before every action. The comparison with HEAD therefore covers S2, the mapper task and the FEAT-047 overlay together.

## 3. Closure conditions of the approved draft

| # | Condition | State |
|---|---|---|
| 1 | C6 passes with the worktree unchanged | MET |
| 2 | C4 valid, zero diagnostics added by the uncommitted work | Ruff: MET. Mypy: NOT MET (19 added). Waived by the owner for those 19 only, as recorded typing debt |
| 3 | Added diagnostics need their own allowlist approval to fix | Not exercised: the owner chose to record, not to fix |
| 4 | Failure handling for C6 | Not exercised: C6 passed |
| 5 | Items 4 to 6 of the draft dispositioned in writing | Section 5 of this report |
| 6 | Validators and `git diff --check` after the final documentation edits | Run after this report was written; result stated in `status/STATUS.md` |

## 4. The 19 added Mypy diagnostics

All 19 are `arg-type` errors. Nine are in `src/sketch2life/interfaces/http/routers/parent_ai.py` and ten in `src/sketch2life/interfaces/http/routers/parent_story_runs.py`. The two removed diagnostics are `no-untyped-def`, one in each file.

| Argument | Callee | Passed type | Expected type | Files |
|---|---|---|---|---|
| `run_id` | `ParentStoryRunResponseV1` | `str` | `UUID` | both |
| `run_state` | `ParentStoryRunResponseV1` | `str` | a literal set of run states | both |
| `context_snapshot` | `ParentStoryRunResponseV1` | `dict[str, Any]` | `ParentRunContextSnapshotV1` | both |
| `lesson_pin_snapshot` | `ParentStoryRunResponseV1` | `dict[str, Any] \| None` | `ParentLessonPinSnapshotV1 \| None` | both |
| `candidate` | `ParentStoryRunResponseV1` | `dict[str, Any] \| None` | `ParentDrawingCandidateV1 \| None` | both |
| `story_revision_id` | `ParentStoryRunResponseV1` | `str \| None` | `UUID \| None` | both |
| `story_status` | `ParentStoryRunResponseV1` | `str \| None` | a literal set of story states | both |
| `story` | `ParentStoryRunResponseV1` | `dict[str, Any] \| None` | `ParentStoryDisplayV1 \| None` | both |
| `job_state` | `ParentStoryRunResponseV1` | `str \| None` | a literal set of job states | both |
| `request_id` | `ParentStoryRunCancelEnvelopeV1` | `str` | `UUID` | `parent_story_runs.py` only (line 280) |

Triage by the coordinating session, read from the diff against HEAD and the raw Mypy output:

- S2 added a type annotation to the `record` parameter of `_story_response` (`parent_ai.py`) and `_response` (`parent_story_runs.py`). At HEAD Mypy reported the missing annotation and did not check the bodies of those two functions; with the annotation it checks them. Eighteen of the diagnostics are in those two bodies and concern arguments those functions already passed at HEAD.
- The nineteenth, `request_id`, is in the cancel route that S2 itself added.
- Whether these mismatches have any runtime effect was not tested. The 84 tests, which include the contract tests of the Parent story-run and cancel routes, passed; which of them reach these two response builders was not traced, so this is an observation, not a proof.

The owner decided to accept the 19 as recorded typing debt and not to require a fix before closing M2-S2.

## 5. Dispositions

- **FEAT-047 description overlay on `be1_artifacts.py`:** KEPT by owner decision D2. The file stays at SHA-256 `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF`. Its approval and evidence are in the FEAT-047 feature folder.
- **Out-of-scope OpenAPI finding (`evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md`):** addressed by the shared OpenAPI mapper task. The catalog test that exposed it, `test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`, is part of `tests/contract/test_openapi_contract_catalog.py` and passed in C6 and in the mapper task's second pytest run. The earlier record is left unchanged; this paragraph is its closing note.
- **Stale-version P3 on broader routes (Allowlist R2):** outside the S2 allowlist; not worked on; carried as a follow-up. Not a closure blocker.

## 6. Debt carried out of S2 (follow-ups, none started)

1. Mypy on `src/sketch2life`: 336 signatures exist at HEAD; the worktree has 353 (the 19 above added, 2 removed).
2. Ruff: 17 diagnostics on the six S2 source paths, all present at HEAD; and one `I001` on `tests/contract/test_openapi_contract_catalog.py` recorded by the mapper task.
3. The stale-version P3 of section 5.
4. From the mapper task: the request-ID inventory remains OPEN beyond the scope decided in its Amendment 1.

## 7. Limits

- Only the nine-file selection ran. The full backend test suite was not run for S2 or for the mapper task.
- The exports and the comparison of the mapper task predate the two small test-file changes made under its Amendments 2 and 3; C6 ran on the current files.
- The comparison in C4 ignores line numbers: a diagnostic that only moved is not counted, and identical diagnostics that were fixed and re-introduced cancel out.
- The timeout path of the driver was not exercised.
- The 2026-11-14 hang of this selection did not recur and remains unexplained.
- Nothing was committed or pushed. No Modal or provider call was made; `OWNER_MODAL_CALL_APPROVED=NO`.
