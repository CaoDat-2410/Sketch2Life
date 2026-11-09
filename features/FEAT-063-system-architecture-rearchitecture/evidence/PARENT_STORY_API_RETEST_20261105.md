# Parent StoryRun-lite API and AI retest

**Status:** Complete; API contract matrix passed, live AI flow incomplete with two AI failures.  
**Execution:** 2026-11-05 09:36:17–09:42:27 Asia/Saigon (370.06 seconds).  
**Approved scope:** Plan revision 43, approval baseline SHA-256 `0088A5AEA37D0B44D1A1DA291AF0CEE4CE469D0FEFED0692E8497F74C7B01B27`.  
**Code changes:** No product/API/SRS/OpenAPI changes. The test harness was corrected for the synthetic profile contract and now propagates failed HTTP/AI results to its process exit code.

## Result summary

| Check | Result |
|---|---|
| Focused backend StoryRun-lite tests | 154 passed, 0 failed, 12.52 s |
| Modal story-output/parser contract tests | 45 passed, 1 skipped, 0 failed, 0.67 s |
| Alembic | `upgrade head` reported 12 independent heads; `upgrade heads` applied all heads in 2.05 s on the isolated DB |
| No-AI HTTP matrix | 22 requests across all 13 distinct mounted operations; all expected statuses; 2.624 s |
| Live drawing VLM | One Qwen2.5-VL call; unknown at 303.762 s. API returned 202 after 304.333 s; run stayed in reconciliation state |
| Live story generation | One Qwen2.5 story call; API returned 502 `STORY_OUTPUT_INVALID` after 59.266 s. Worker reason: `EDUCATIONAL_FACT_INVALID` |
| Video | Not called |
| Cleanup | Both task-owned Modal apps stopped with 0 tasks; disposable PostgreSQL container exited; shared Docker services remained running |

The real VLM did not reach adult subject review. To exercise the independent story API without retrying the VLM, the harness used a separate synthetic run and a deterministic butterfly vision fixture. This is **not** a successful end-to-end Parent AI flow. The story route received adult subject confirmation before its one Modal call; no story draft was returned, so adult script confirmation and later video/activity steps were not reached.

## Per-operation API results

The times below are representative no-AI matrix calls. The full 22-request trace, including expected negative cases and duplicate route calls, is in [`api_request_trace_safe.json`](assets/parent_story_api_retest_20261105/attempt_02/api_request_trace_safe.json).

| Operation | Purpose | Result and time |
|---|---|---|
| `POST /v1/story-runs` | Create a Parent run | 201 in 41.45 ms; missing age 422 in 2.67 ms; duplicate active run 409 in 11.58 ms |
| `GET /v1/story-runs/{run_ref}` | Read run state/revision | 200 in 5.18 ms |
| `POST /v1/story-runs/{run_ref}/assets` | Attach admitted artwork and start drawing analysis | Unknown asset 404 in 9.78 ms; live AI request returned 202 in 304,333 ms but ended `VISION_OUTCOME_UNKNOWN` |
| `POST /v1/story-runs/{run_ref}/subject-confirmation` | Adult confirms the VLM candidate | Premature confirmation 409 in 12.98 ms; separate fixture-backed adult confirmation 202 in 21.74 ms |
| `POST /v1/story-runs/{run_ref}/story-revisions` | Generate a story draft after subject confirmation | Activity preselection 422 in 1.63 ms; before subject confirmation 409 in 16.44 ms; live AI call returned 502 in 59,265.75 ms |
| `GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}` | Read a generated story revision | Missing revision 404 in 6.53 ms; no live positive read because generation failed |
| `POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation` | Adult confirms the exact story revision/hash | Missing revision 404 in 9.59 ms; no positive confirmation because no draft was returned |
| `POST /v1/story-runs/{run_ref}/cancel` | Cancel an active run | 202 in 16.26 ms |
| `POST /v1/upload-sessions` | Start an artwork upload | 201 in 22.71 ms |
| `PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}` | Upload a checksummed binary part | 200 in 22.25 ms |
| `POST /v1/upload-sessions/{upload_ref}/complete` | Finalize upload and run admission/scanning | 202 in 562.56 ms; subsequent poll reached `READY` in 12.52 ms |
| `GET /v1/upload-sessions/{upload_ref}` | Read upload/admission state | 200 in 10.86 ms |
| `DELETE /v1/upload-sessions/{upload_ref}` | Abort a pending upload | 202 in 21.11 ms |

All negative responses above matched the intended validation/business guards. The full Parent flow also completed image upload/admission, subject confirmation with the test fixture, and the story-generation HTTP request. It could not exercise a successful story-revision GET/confirmation because the worker returned no draft.

## AI call details

### Drawing understanding — `drawing.analyze`

- Model/config: Qwen2.5-VL-7B-Instruct, pinned revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`, Modal L4 app.
- Exactly one dispatch was made from `POST /v1/story-runs/{run_ref}/assets`; no retry.
- Modal client wait: 303.762 s, ending `ModalFunctionOutcomeUnknown`. The API call returned 202 after 304.333 s. Modal had no worker-stage log for this call, and the run row ended at `INPUT_PROCESSING`, job `AWAITING_RECONCILIATION`, error `VISION_OUTCOME_UNKNOWN`.
- No usable subject candidate was committed. The provider/cold-start cause is not proven by this run; available logs do not distinguish GPU scheduling from worker startup failure. The important observable issue is that the HTTP request waited about five minutes before returning its 202 response.

### Story/storyboard — `story.generate`

- Model/config: Qwen2.5-7B-Instruct, pinned revision `a09a35458c702b33eeacc393d103063234e8bc28`, Modal language/audio app. The worker ran on L40S.
- Exactly one dispatch was made through `POST /v1/story-runs/{run_ref}/story-revisions`; it used a separate fixture-backed run after the VLM outcome was unknown. No retry.
- Worker timings: model load 11.898 s; token generation 25.922 s; 545 output tokens. Total API wait was 59.266 s.
- The structured JSON parser reached semantic validation; the worker rejected the generated butterfly lifecycle with safe reason `EDUCATIONAL_FACT_INVALID`. The backend exposed HTTP 502 `STORY_OUTPUT_INVALID`; persisted run/job state was `PREPARATION_REVIEW` / `FAILED` with the same safe API error code.
- The local parser contract tests passed. The live failure was a factual/lifecycle validation failure, **not evidence of a JSON parser/schema mismatch**. Do not weaken the fact guard based on this evidence; a later prompt/quality change needs a new bounded plan and inference.

## Contract and business-rule findings

1. **The StoryRun-lite route contract is internally consistent for the exercised slice.** The local OpenAPI contains 13 operations. The create, upload, state-guard, subject-confirmation, cancellation, and upload-lifecycle responses matched the expected HTTP contract. `502` is declared for story generation; `STORY_OUTPUT_INVALID` is an allowed error code.
2. **The current create-run DTO is synthetic-only.** `CreateRunRequest.profile_ref` accepts only the literal `synthetic-parent-demo`. The initial harness payloads using invented synthetic profile refs correctly received 422; the harness was corrected and those first-attempt results were preserved under `attempt_01_invalid_synthetic_run_request/`. This restriction makes the mounted slice unsuitable for real Parent profile IDs, although it is consistent with its synthetic-only purpose.
3. **The drawing endpoint blocks on provider work before returning 202.** The service calls the vision adapter inside `attach_asset`; the measured request took 304.333 s to return. This differs from the expected quick asynchronous acceptance/polling experience. The API then left the run in `AWAITING_RECONCILIATION` after an unknown provider outcome. The no-retry/fail-closed behavior is correct; request latency and reconciliation visibility need follow-up.
4. **The story route failed closed on factual validation.** It did not create a revision and therefore correctly did not allow adult script confirmation or video admission. The API response is contract-shaped, but the generated story did not satisfy the required butterfly facts.
5. **This OpenAPI is a StoryRun-lite slice, not the complete SRS platform API.** SRS v2.3-draft §21.2 and §31.5 describe more product surfaces. Not present in this slice include profile/lesson catalog and post-video activity delivery; the target SRS also describes context confirmation, idea/audio input, story rewrites, script confirmation, video generations, unsuitable-video handling, completion, playback token, and job-status operations. These were not counted as failures of the 13 mounted operations; they remain unimplemented/unverified against the broader SRS.
6. **Only two Parent HTTP routes currently dispatch Modal AI.** Parent line-sketch guide, lesson visuals, ASR/TTS, SAM2, and Teacher Sketch Deck have no mounted HTTP dispatch route in this StoryRun-lite API slice. They were not called directly. Video remained excluded.
7. **Model pins match the current FEAT-063 v2.3-draft candidates.** The SRS names Qwen2.5-VL-7B and Qwen2.5-7B as candidates and records Qwen3-VL as NO_GO evidence. This run used the pinned Qwen2.5 revisions; it did not test model quality successfully for either full Parent AI stage.

## Verification, privacy, and cleanup

- The temporary database was `storyrun_lite_feat063_ai_20261104` on the task-owned `127.0.0.1:5433` container, connected as its database owner. No shared database was used.
- The test image was the existing generated synthetic butterfly PNG. No real child/profile data was used.
- No prompt or raw story text was written to evidence. Evidence contains request names/routes, status, timings, safe error codes, field names, counts, and hashes only.
- The command initially exited `0` despite the story HTTP 502 because the harness did not propagate a recorded `passed=false` response. The harness was corrected after the run. The evidence status is **FAIL/PARTIAL**, regardless of that initial process exit code; no inference was repeated.
- Both deployed Modal apps were stopped; final Modal app listing showed 0 active tasks. The task-owned PostgreSQL container was stopped and verified `exited`. Shared API, Redis, ClamAV, and PostgreSQL containers remained running. Modal model Volumes were retained.

## Evidence files

- [`retest_results_safe.json`](assets/parent_story_api_retest_20261105/attempt_02/retest_results_safe.json): test, migration, route, AI dispatch, and timing summary.
- [`api_request_trace_safe.json`](assets/parent_story_api_retest_20261105/attempt_02/api_request_trace_safe.json): safe per-request trace.
- [`drawing_analyze_modal_result_safe.json`](assets/parent_story_api_retest_20261105/attempt_02/drawing_analyze_modal_result_safe.json) and [`story_generate_modal_result_safe.json`](assets/parent_story_api_retest_20261105/attempt_02/story_generate_modal_result_safe.json): safe AI outcomes.
- `attempt_01_invalid_synthetic_run_request/`: preserved initial harness attempt; it made no AI dispatch.

**Sources:** Canonical FEAT-063 SRS v2.3-draft `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC`; StoryRun-lite OpenAPI `artifacts/storyrun-lite/openapi.json`, SHA-256 `1257158CE5AFB0B92F9D7CC03E12B4DEFC4A4B009DB93A64242AC4646D3EAA8B`.
