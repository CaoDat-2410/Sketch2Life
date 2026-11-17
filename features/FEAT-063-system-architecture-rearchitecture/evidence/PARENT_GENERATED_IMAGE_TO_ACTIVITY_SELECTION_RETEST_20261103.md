# Parent generated-image, story, and activity retest

**Execution:** 2026-11-03 23:34 to 2026-11-04 00:05 Asia/Saigon
**Scope:** synthetic drawing only; no video generation.
**Plan and approvals:** `plan/PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md`; `approvals/TASK_APPROVAL.md`.

## Result

- **Image upload/admission:** passed on the isolated StoryRun-lite API. The generated PNG passed the configured ClamAV and image-normalization gates and reached `READY`.
- **Drawing understanding:** passed on Modal. Qwen2.5-VL returned `bướm`; adult confirmation was accepted, and a read-only follow-up confirmed `PREPARATION_REVIEW` / `SUCCEEDED`.
- **Story generation:** passed on Modal. Qwen2.5-7B-Instruct returned a Vietnamese story with five storyboard scenes.
- **Selectable activity:** the legacy activity endpoint returned one catalog choice; selecting it returned HTTP 200 / `SUCCEEDED`.
- **Video:** zero calls.

This is not an end-to-end match for the current SRS Parent flow. StoryRun-lite has no script-generation HTTP route; the story worker was called directly after adult confirmation. The activity endpoint belongs to a separate legacy session, uses a deterministic VLM fixture and returns suggestions before video. It is not integrated with this StoryRun and does not verify the SRS post-video outdoor-activity step.

## Synthetic image

- Asset: `assets/parent_generated_image_activity_retest_20261103/synthetic_childlike_butterfly.png`
- Provenance: `assets/parent_generated_image_activity_retest_20261103/synthetic_childlike_butterfly_provenance.json`
- SHA-256: `c16930354d637199b97d744de16c62bfc4f0ee97c34a23751e27912d968c6949`
- Size: 1,775,882 bytes.
- The image is a generated childlike colored-pencil butterfly illustration. It contains no real child image or personal data.

## API results and timings

Times below are local HTTP-call wall times; polling requests are listed separately. Modal enqueue/start/runtime values come from `modal function calls` for the exact call IDs.

### Initial setup attempt

The first synthetic run used a runtime-pinned Modal run ID that differed from its generated `run_ref`. The API's safety guard returned `VISION_ATTEMPT_HOLD` before a durable invocation-ledger row or Modal Function Call existed. This run was preserved and not mutated or retried. A replacement run was created, and the task API was restarted with its exact `run_ref` pinned.

| Operation | HTTP | Time | Result |
|---|---:|---:|---|
| `GET /health` probe | 404 | 4.919 ms | Health route is not registered |
| `GET /openapi.json` probe | 404 | 1.735 ms | Standalone StoryRun-lite app does not expose OpenAPI |
| `POST /v1/story-runs` | 201 | 50.992 ms | Initial synthetic run created |
| `POST /v1/upload-sessions` | 201 | 20.433 ms | Upload session created |
| `PUT /v1/upload-sessions/{upload_ref}/parts/1` | 200 | 23.484 ms | Image part accepted |
| `POST /v1/upload-sessions/{upload_ref}/complete` | 202 | 1,809.156 ms | Admission queued |
| `GET /v1/upload-sessions/{upload_ref}` | 200 | 5.430 ms | Image reached `READY` |
| `POST /v1/story-runs/{run_ref}/assets` | 202 | 30.211 ms | Enqueued, then safety guard held the mismatched run ID |
| `GET /v1/story-runs/{run_ref}` | 200 | 3.601 ms | `FAILED`, `VISION_ATTEMPT_HOLD`; no provider call |

### Aligned replacement Parent run

| Operation | HTTP | Time | Result |
|---|---:|---:|---|
| `POST /v1/story-runs` (replacement) | 201 | 12.299 ms | `aa84ff1a-410d-4953-96f4-cda22abc1e80` |
| `GET /v1/story-runs/{run_ref}` | 200 | 29.938 ms | `INPUT_PROCESSING` |
| `POST /v1/upload-sessions` | 201 | 21.107 ms | Upload session created |
| `PUT /v1/upload-sessions/{upload_ref}/parts/1` | 200 | 22.705 ms | Image part accepted |
| `POST /v1/upload-sessions/{upload_ref}/complete` | 202 | 1,314.964 ms | ClamAV/normalization admission queued |
| `GET /v1/upload-sessions/{upload_ref}` | 200 | 5.223 ms | `READY`, with source and derived asset references |
| `GET /v1/story-runs/{run_ref}` before attach | 200 | 3.515 ms | `INPUT_PROCESSING` |
| `POST /v1/story-runs/{run_ref}/assets` | 202 | 634,121.112 ms | Modal drawing call completed; request returned after roughly 10m34s |
| `GET /v1/story-runs/{run_ref}` after vision | 200 | 3.357 ms | `SUBJECT_REVIEW`; label `bướm` |
| `POST /v1/story-runs/{run_ref}/subject-confirmation` | 202 | 11.950 ms | Accepted; run advanced to `PREPARATION_REVIEW` |
| `GET /v1/story-runs/{run_ref}` after confirmation | 200 | 5.668 ms | Confirmed `PREPARATION_REVIEW`, job `SUCCEEDED` |

The aligned API sequence took about **11m19.725s** from its recorded start to confirmation follow-up. The confirmation route returns HTTP 202; the runner initially expected 200 and stopped, then this read-only GET verified the accepted state. The confirmation POST was not repeated.

### Modal inference timings

| Workload | Modal Function Call | Queue wait | Function execution | Client-side total |
|---|---|---:|---:|---:|
| Drawing understanding, `analyze-drawing` | `fc-01M6H51D7MD2P4XS68S2DQEN53` | 595.263 s | 29.295 s | 632.494 s Modal client elapsed; 634.121 s HTTP attach elapsed |
| Vietnamese story and storyboard, `generate-story-and-storyboard` | `fc-01M6H5P6TFKW6Q7ZKRX28JCTDD` | 202.845 s | 90.741 s | 296.688 s, including staging/setup |

The drawing call used the deployed Qwen2.5-VL-7B worker. Its API confidence value is the conservative `0.0` sentinel because the worker does not provide calibrated confidence; it should not be read as a model confidence score. The story worker used Qwen2.5-7B-Instruct revision `a09a35458c702b33eeacc393d103063234e8bc28`.

## Activity list and selection

The harness uploaded the same generated PNG to the current HTTP router but used its explicit deterministic test VLM fixture (`bướm`); the curated catalog produced one available option, with no AI ranking call:

| ID | Activity | Time | Age band | Materials / supervision | Selection |
|---|---|---:|---|---|---|
| `ACT-0102` | Ghép con vật với nơi sống | 12 min | 3–6 tuổi | Vật mẫu thiên nhiên an toàn, thẻ hình; người lớn ở gần | `PUT /v1/sessions/{session_id}/p1-context` returned 200 / `SUCCEEDED` |

The fixture session used a synthetic 60-month age. This activity is a card-matching catalog item, not evidence of the SRS outdoor-activity-after-video step. The complete API response and timings are in `assets/parent_generated_image_activity_retest_20261103/activity_api_result.json`.

## Story output review

The generated title was **“Bướm Đẹp”** and the worker returned five scenes. The model described an egg, a young butterfly emerging, a butterfly eating leaves, an adult on a flower, and a butterfly seeking a nest. The output has factual errors: a caterpillar hatches from a butterfly egg, and butterflies do not build nests. Treat the generated script as a draft that needs educator review; it was not passed through an educational fact-checking gate.

The worker input contained only the confirmed topic `bướm`, Vietnamese language, and fixed scene count `5`; it did not receive the drawing pixels. The full structured output is in `assets/parent_generated_image_activity_retest_20261103/story_worker_result.json`.

## Evidence files

- `assets/parent_generated_image_activity_retest_20261103/storyrun_api_result.json`: first guarded run.
- `assets/parent_generated_image_activity_retest_20261103/storyrun_recovery_seed.json`: replacement run creation.
- `assets/parent_generated_image_activity_retest_20261103/storyrun_aligned_api_result.json`: successful upload, VLM result, subject confirmation, and timings.
- `assets/parent_generated_image_activity_retest_20261103/storyrun_aligned_drawing_dispatch_intent.json`: one drawing call intent.
- `assets/parent_generated_image_activity_retest_20261103/activity_api_result.json`: full activity-list response and selected item.
- `assets/parent_generated_image_activity_retest_20261103/story_worker_result.json`: direct worker result and timings.
- `scripts/run_parent_storyrun_lite_generated_image_retest_20261103.py`, `scripts/run_parent_storyrun_aligned_image_retest_20261103.py`, `scripts/record_parent_accepted_confirmation_20261103.py`, `scripts/run_parent_confirmed_story_worker_20261103.py`: task-scoped runners. No product code, API contract, or database schema was changed.

## Shutdown

After outputs were saved, all currently deployed Modal `dev` apps were stopped at 2026-11-04 00:09:03–00:09:06 Asia/Saigon, and the task-owned StoryRun-lite API and PostgreSQL server were stopped. Port checks confirmed 8002 and 5433 closed while the pre-existing API on port 8000 remained available. Shared model Volumes and weights were retained. Final states are recorded in `status/STATUS.md`.
