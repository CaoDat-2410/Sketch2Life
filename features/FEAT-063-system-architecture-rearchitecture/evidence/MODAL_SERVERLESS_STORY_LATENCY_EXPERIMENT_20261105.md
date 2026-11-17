# Modal serverless Parent story latency experiment

**Status:** COMPLETE — scheduling/model startup improved; story output rejected  
**Date:** 2026-11-05, Asia/Saigon  
**Feature:** FEAT-063  
**Plan:** [`MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`](../plan/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md)  
**Approved plan SHA-256:** `E18267CD3B9D5AC5F75F3A5F80DAD6958AEFF9EDCFF3A36C2C00BF579F2C8711`

## Result

The one synthetic Parent `story.generate` worker call was dispatched once as `fc-01M6M14QE9V6R129AAEXWVQRW2`. Modal allocated an **NVIDIA A10** from the ordered `L4 → L40S → A10` options. The worker started, loaded the pinned Qwen2.5 checkpoint, and generated tokens; this request did not remain queued for 30 minutes.

The worker then rejected the generated text with `MODAL_MODEL_OUTPUT_INVALID`. The call produced no valid StoryRevision result. This is a separate generation/contract issue after scheduling and inference, not a GPU queue timeout. The single-call plan prohibited retry, so no second story call was sent.

## Timings

| Stage | Observed |
|---|---:|
| Client elapsed from dispatch to terminal response | 46.803 s |
| Modal log: worker start | 02:39:01 +07:00 |
| Torch import | 2.224 s |
| Actual GPU | NVIDIA A10 |
| Tokenizer + model loader (`_load_text_model`) | 12.634 s |
| Prompt encoding | 0.015 s |
| Token generation | 27.407 s; 722 tokens |
| Final parser result | `MODAL_MODEL_OUTPUT_INVALID` |

The worker logs show four checkpoint shards loaded with the Transformers parallel-loading environment enabled. The 2026-11-04 readiness probe measured tokenizer load 0.538 s, model load 15.989 s, and an 8-token smoke inference in 1.297 s. Its model-load metric and this experiment's combined tokenizer/model-loader metric are not identical; the combined prior time is about 16.527 s. The new 12.634 s reading is directionally faster, but GPU type, host/storage conditions, and measurement boundaries differ. One sample cannot attribute the difference solely to parallel loading or establish a latency distribution.

Absolute timestamps from the local caller and Modal worker logs differ by roughly 14 seconds near completion, so this report uses the caller's monotonic elapsed result for end-to-end timing and does not claim a precise queue-wait duration. The observed change is that a worker was allocated quickly on A10, whereas earlier L4-only attempts remained pending for 30 minutes without a container.

## Failure interpretation

The existing parser accepts only a JSON story with an exact top-level field set, 5–15 sequential scenes, bounded scene fields, and a timeline matching the declared duration. It emits the same `MODAL_MODEL_OUTPUT_INVALID` code for JSON decoding, schema, and timeline failures. Generated text is not persisted or logged, so the exact offending field cannot be identified from this call without another inference. Modal logs also report ignored generation flags (`temperature`, `top_p`, `top_k`) and a missing attention mask because the pad token equals EOS; these should be addressed in a separately approved story-output reliability task.

No prompt, generated story text, child profile, or personal data was included in instrumentation logs. The fixture used a previously generated synthetic butterfly drawing and a synthetic adult-confirmed idea.

## Deployment and cleanup

- The successful dev deployment was Modal app `ap-yyRNizBtBC0u7HiF2LGcT6`. An initial deployment attempt hit a Windows console encoding error after creating a stopped app record; the deployment was rerun with UTF-8 output enabled. No inference was sent to that first record.
- After the single request, the language/audio app was explicitly stopped at `02:41:22 +07:00`. Modal reported `state=stopped`, `tasks=0`; both task-created app records are stopped. Shared model and scratch Volumes were retained. The task's scratch prefix was removed after the terminal result.
- The 120-second scaledown setting is a dev experiment and may incur idle GPU cost. The app was stopped after evidence capture; exact Modal spend was not queried.
- Video calls: zero. Other AI calls: zero. Product workload remains disabled. No commit, push, or merge.

## Verification

- `py -3.12 -m py_compile` for the Modal worker and one-shot runner: passed.
- Ruff on the Modal worker and one-shot runner: passed.
- Modal deploy: succeeded after retrying only the CLI command that failed on Windows output encoding; this was before any worker call.
- One Modal worker call: reached A10 and generation, then failed the existing output parser as described above.
- Post-run Modal app list: task-owned app `stopped`, zero active tasks.

## Source references

- [Modal GPU fallbacks](https://modal.com/docs/guide/gpu) — ordered GPU alternatives are supported; actual allocation depends on capacity.
- [Modal cold-start performance](https://modal.com/docs/guide/cold-start) — separates queue time from container initialization and notes that warm-container settings trade latency for resource use.
- [Modal Memory Snapshots](https://modal.com/docs/guide/memory-snapshots) — GPU snapshots are Alpha and generally do not speed up model-weight loading from storage.
- [Transformers v4.53.0 `modeling_utils.py`](https://github.com/huggingface/transformers/blob/v4.53.0/src/transformers/modeling_utils.py) — the pinned version supports `HF_ENABLE_PARALLEL_LOADING` and `HF_PARALLEL_LOADING_WORKERS` for loading checkpoint shards with a thread pool.

## Evidence files

- Dispatch intent and terminal worker result: `assets/modal_serverless_story_latency_20261105/story_dispatch_intent.json`, `story_result.json`.
- Worker logs and timing events: `assets/modal_serverless_story_latency_20261105/modal_function_logs.txt`.
- Post-stop app/task state: `assets/modal_serverless_story_latency_20261105/modal_app_state_after_stop.json`.
- Runner: `scripts/run_modal_serverless_story_latency_20261105.py`.
