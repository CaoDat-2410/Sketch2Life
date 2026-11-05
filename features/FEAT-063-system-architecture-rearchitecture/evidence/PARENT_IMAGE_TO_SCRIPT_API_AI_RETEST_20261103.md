# Parent image-to-script API and AI retest - 2026-11-03

**Status:** Test execution complete with AI capacity blockers. No product code, API route, or database schema was changed for this retest.

## Scope and environment

- Followed the latest SRS in FEAT-063 and the approved plan `plan/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md` (latest SHA-256 `8491CBA56D6A44F60B2980D7A5D92ADD88A20F9CB8E85D40495D33016B7561B7`).
- Used the generated synthetic butterfly drawing `evidence/assets/drawing_vlm_synthetic_butterfly.png` (3,919 bytes; SHA-256 `4b18777ae70eb429273c1e0ba7189ff005171b9dda88491510d91965aafa07fc`). No real child image, profile, voice, or school data was used.
- Ran the standalone synthetic Parent StoryRun-lite app from the feature checkout on `127.0.0.1:8002`, with a new owned test database `storyrun_lite_parent_retest_20261103` on `127.0.0.1:5433`. `alembic upgrade heads` completed successfully against this database. The API used the existing ClamAV service on `127.0.0.1:3310`.
- This is evidence for the isolated StoryRun-lite app; it does not establish that the pre-existing Docker API on port 8000 exposes or dispatches these routes.

## API results

| Operation | Result | Notes |
|---|---:|---|
| `GET /health` | 404 | No health route is registered in this standalone app. |
| `GET /openapi.json` | 404 | OpenAPI/docs are explicitly disabled in this app. |
| `GET /` | 404 | No root route. |
| `POST /v1/story-runs` | 201 | Synthetic Parent run created. |
| `POST /v1/upload-sessions` | 201 | Upload session created for the run. |
| `PUT /v1/upload-sessions/{upload_ref}/parts/1` | 200 | One image part accepted with size and SHA-256 checks. |
| `POST /v1/upload-sessions/{upload_ref}/complete` | 202 | Accepted; upload processing completed. |
| `GET /v1/upload-sessions/{upload_ref}` | 200 | Upload reached `READY`; ClamAV and image normalization gates passed. |
| `GET /v1/story-runs/{run_ref}` before attach | 200 | Run was `INPUT_PROCESSING`, revision 1. |
| `POST /v1/story-runs/{run_ref}/assets` | 202 | Request took 904.056 seconds. It did not yield a vision result before the Modal call timeout. |
| `GET /v1/story-runs/{run_ref}` after attach | 200 | `INPUT_PROCESSING` / `AWAITING_RECONCILIATION`, `VISION_OUTCOME_UNKNOWN`, `OPERATOR_REVIEW`; correlation ID `1736564d-6f75-4ccd-9f56-bc39bdc78ba1`. No retry was sent. |

The upload and basic run APIs passed. The attachment API returned its documented asynchronous acceptance status, but its downstream AI outcome is unresolved because Modal did not schedule an L4 worker. This is an AI dispatch/capacity failure, not an upload validation failure.

`POST /v1/story-runs/{run_ref}/subject-confirmation` was not called because no image-understanding result was available to confirm. The current StoryRun-lite router has no Parent script-generation endpoint; `story.generate` is exposed only as a private Modal function in this checkout. Consequently, there is no end-to-end Parent API script-generation result to report.

## AI results

- **Drawing analysis:** The API-triggered `analyze-drawing` request was staged in the scratch Volume. Modal logs reported it waiting to be scheduled on `GPU_L4` at 22:51:25 and 22:52:13 local time. No worker container or terminal model result was observed. The API recorded `VISION_OUTCOME_UNKNOWN`; the run was preserved and not retried.
- **Sample story:** One detached `story.generate` request was staged with the visually verified synthetic topic `bướm`, language `vi`, and five scenes. It was not connected to the unresolved Parent run and did not pass through the Parent subject-confirmation API. During a 436-second bounded wait, no language/audio container or worker log appeared; the local client was stopped per the owner instruction. The result is `UNKNOWN_NO_RETRY`; no story output file was produced.
- **Video:** Zero video requests. No LTX/Wan, composition, or video-safety worker was invoked. FLUX, ASR, TTS, and SAM2 were also not invoked during this retest.

## Cleanup

- Stopped and verified all Modal `dev` apps as `stopped`: drawing VLM (`ap-7kNcbOesrIpJpPSZcX6aDb`), language/audio (`ap-w5VBjY4t0m47RcHktpg7kb`), FLUX (`ap-yBGfmdN4KEITZPy3IpsgVM`), and video candidate (`ap-dsvERz4dAJoKtom5If4krY`). All reported zero tasks. App records remain; shared Volumes and model files were not deleted.
- Removed only the two task-specific staged input prefixes from the scratch Volume after the apps stopped.
- Stopped the task-owned API on port 8002 and PostgreSQL cluster on port 5433. Existing project Docker services were left untouched.

## Evidence files

- `evidence/assets/parent_image_to_script_retest_20261103/api_prepare.json`
- `evidence/assets/parent_image_to_script_retest_20261103/api_vision.json`
- `evidence/assets/parent_image_to_script_retest_20261103/checkpoint.json`
- `evidence/assets/parent_image_to_script_retest_20261103/story_worker_dispatch_intent.json`
- `evidence/assets/parent_image_to_script_retest_20261103/story_worker_summary.json`
- `evidence/scripts/run_parent_story_worker_retest_20261103.py`

The test proves the local upload path and the safety gates around one synthetic image. It does not prove successful Modal vision, subject confirmation, or script generation; available L4 capacity and a script API route are the remaining blockers.
