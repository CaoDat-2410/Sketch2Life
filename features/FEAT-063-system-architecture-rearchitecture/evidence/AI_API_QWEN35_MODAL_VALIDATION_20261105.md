# FEAT-063 AI API and Qwen3.5 Modal validation — 2026-11-05

## Scope and role decision

This Rev44 pass uses synthetic fixtures only and the immutable dev checkpoint `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`. The SRS source checkout baseline was SHA-256 `7D88057653104A5F3BFD791135DDD22144DEE033FF82928AA6F86775E6FC1AF4`; after the additive Q159/Qwen3.5 amendment, the current synchronized SRS copy is SHA-256 `6BADEBAAD6C28239CA9B759CF17C57A0405D7242B45F3411F40B7E8FEBDC8381`. It does not enable production workloads. Platform Admin and Teacher may start new lesson/activity/plan suggestions. Parent may edit an existing authorized draft or personal copy, but may not start suggestion generation. AI lesson output remains a private draft pending authorized human review.

Video was deferred per the owner's earlier instruction. No LTX, Wan, scene validation, final video safety, composition or playback test was performed. No real child artwork, profile, audio, lesson, token or credential was used.

## Modal readiness and runtime diagnosis

- Qwen3.5 checkpoint marker and indexed weight shards were present in the existing Modal Volume. No model Volume was deleted or recreated.
- GPU readiness for the language worker passed on an L40S: `AutoProcessor`, `AutoModelForMultimodalLM`, Transformers 5.22.1, GPU available with 47,695,921,152 bytes reported. The pinned checkpoint/runtime was ready; this did not establish output quality.
- Story and lesson generation both failed before generation with `MODAL_CONSTRAINED_DECODER_UNAVAILABLE`. Modal logs showed that LM Format Enforcer's Transformers adapter imported `PreTrainedTokenizerBase` from the Transformers 4 path `transformers.tokenization_utils`; that import fails under Transformers 5.22.1 and LMFE masks the import error as “transformers is not installed.”
- The worker now pins `lm-format-enforcer==0.11.3` and builds the LMFE tokenizer data/`TokenEnforcer` callback directly. It no longer imports the incompatible LMFE Transformers adapter. The schema remains the generation-time constraint, followed by the existing strict worker and backend parsers.
- Local constrained-token tests passed. A CPU-only Modal readiness call then reported `ready` for Transformers 5.22.1, LMFE 0.11.3, `JsonSchemaParser`, `TokenEnforcer`, `AutoModelForMultimodalLM` and `AutoProcessor`. This checked imports only: it did not load Qwen weights or perform another inference. No second story or lesson inference was dispatched under the Rev44 one-attempt-per-workload limit.
- The Qwen drawing source was corrected after its failed call to use the documented Qwen3.5 image message form (`{"type":"image","image":...}`) and to reject empty output explicitly. Local message-shape/parser tests pass. This correction has not been inference-tested.

## Actual inference results

| Workload | Modal call | Time | Result |
|---|---|---:|---|
| `drawing.analyze` | `fc-01M6NBS5J15QCCTBEBSS9PMV1P` | about 27s | Failed terminal with unusable/empty decoded text. No subject candidate was accepted. |
| `story.generate` + `storyboard.generate` | `fc-01M6NBT067B8Q397JCPWXWQKPM` | 26.280s | Failed before text generation with `MODAL_CONSTRAINED_DECODER_UNAVAILABLE`; cause and unverified fix are above. |
| `teacher.sketch-deck.generate` | `fc-01M6NBTT00BYWZ26Z6NC39GMNW` | 40.042s | Passed worker contract: Vietnamese DRAFT, 16:9, five slides, four drawing steps, and exactly two approved activity references. No authenticated Teacher API or durable job was exercised. |
| `lesson.plan.suggest` | `fc-01M6NBW4AQ6GZZ43R8GN4EGSVB` | 23.106s | Failed before generation with `MODAL_CONSTRAINED_DECODER_UNAVAILABLE`; no lesson draft was generated. |
| `tts.narration.generate` | `fc-01M6NBWQJB2TP9V7CM3E9PB0KA` | 23.501s | Passed worker execution; produced a Vietnamese WAV, 184,364 bytes. |
| `asr.transcribe` | `fc-01M6NBXHY3BR862BXDWCQX66XJ` | 31.564s | Completed in Vietnamese, but the requested “Con bướm bay qua khu vườn đầy nắng.” was transcribed as “Con đứng bay qua khu vườn đầy nắng.” Exact fixture transcription failed; adult transcript confirmation remains necessary. |

### Not dispatched / previously blocked

| Workload | Status | Reason |
|---|---|---|
| `parent.sketch-guide.generate` | Blocked, no call | Pinned FLUX.3 weights returned HTTP 401 and the Modal dev workspace has no Hugging Face Secret. The current worker contains legacy FLUX.2 code and fails closed. |
| `lesson.visual.generate` | Blocked, no call | Same FLUX.3 access blocker; the PUP pipeline and compatible FLUX.3 worker are not ready. |
| `drawing.segment` (SAM 2.1) | `UNKNOWN_NO_RETRY` | Earlier synthetic attempt waited 1,800 seconds for `GPU_L4` scheduling and produced no mask. No retry in Rev44. |
| `video.scene.generate` (LTX-2.5), `video.scene.validate`, `video.compose`, `video.final-safety.validate` | Deferred/not run | Video deferred; final safety policy/model is unselected. No video or playable output is claimed. |

## API coverage and contract gaps

- Main backend OpenAPI `OPENAPI_FEAT063_REV45_20261101.json`: 24 operations across 17 path templates; none directly dispatches an AI worker. Existing Lesson Library routes implement lesson CRUD, upload sessions and source-document reads, not AI extraction/suggestion.
- Isolated StoryRun-lite OpenAPI: 13 operations across 12 paths. `POST /v1/story-runs/{run_ref}/assets` dispatches drawing VLM, and `POST /v1/story-runs/{run_ref}/story-revisions` dispatches story generation. These are synthetic fixture routes with in-process FastAPI `BackgroundTasks`; they are not durable `ai_jobs`/outbox execution and do not supply production Firebase role, tenant or consent enforcement.
- Missing from the mounted product API: SRS Parent idea/ASR route, exact context confirmation, bounded rewrite route, exact script confirmation, video admission, shared authorized `GET /v1/jobs/{job_id}`, playback token, Parent Sketch Guide session route, Teacher occurrence/deck API, Admin/Teacher lesson suggestion API, and lesson visual/slide asset API. The catalog enumerates the exact target operations and current state.
- Worker-only does not mean product API is complete. Lesson suggestion has an allowlisted input validator and `LessonContentInputV1` draft adapter, but no authenticated durable API/job persistence. The Parent role cannot start a new suggestion. Do not expose a generic `POST /ai/{workload}` route.
- Every row in `deployment/modal/srs_v23/workloads.json` remains disabled. No public Modal URL or provider credential is given to a client.

## Verification

- Modal worker/parser suite: **59 passed**.
- Backend API/contract set (`test_story_run_lite_api.py`, `test_story_run_lite_main_composition.py`, `test_openapi_contract_catalog.py`, Lesson Library API integration contract, AI story contracts, Modal client and image-worker tests): **79 passed, 6 skipped**.
- Touched-file Ruff, Python `compileall`, OpenAPI catalog parity tests, and `git diff --check` passed. Repository security validation passed after removing machine-specific paths and a false-positive secret-like cache variable name; scan result: 6,388 publishable files, no absolute machine paths or credentials. A broad Ruff scan of the entire Modal directory found seven pre-existing findings in untouched legacy modules (`drawing_segment_app.py`, `l4_app.py`, `video_app.py`, and `wan_video_candidate_app.py`); no automatic changes were applied to those files.
- Evidence files contain hashes/references and synthetic worker results; raw child media, prompts, model output and credentials are not included in this report.

## Shutdown

Both task-owned apps were stopped and verified via `modal app list --env dev --json` at 2026-11-05 15:31:46 Asia/Saigon:

| App | App ID | State | Tasks | Stopped at |
|---|---|---|---:|---|
| `sketch2life-srs23-drawing-vlm-dev` | `ap-hkLJ6XzSSB1ohM4vTIXpsf` | stopped | 0 | 2026-11-05 15:31:31 +07:00 |
| `sketch2life-srs23-language-audio-dev` | `ap-TIESD5wt8qWc7McHycT09D` | stopped | 0 | 2026-11-05 15:31:36 +07:00 |

Shared model and scratch Volumes were retained. The exact post-test readiness and shutdown metadata is stored in `assets/ai_api_qwen35_modal_validation_20261105/summary.json` and `assets/ai_api_qwen35_modal_validation_20261105/modal_app_shutdown.json`.
