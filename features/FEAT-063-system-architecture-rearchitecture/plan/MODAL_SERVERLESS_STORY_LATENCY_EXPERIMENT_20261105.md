# Modal serverless Parent story latency experiment

**Plan revision:** 1  
**Status:** APPROVED / IN PROGRESS  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063  
**Worktree:** `codex/feat063-modal-backend-completion-20261103`

## Goal

Reduce the wait for one cold, synthetic Parent story-generation request on the existing Modal serverless path, and distinguish GPU scheduling time from container/model initialization and generation time. The current implementation already caches Qwen in each worker process; this experiment must preserve that behavior and the pinned model/runtime.

## Approved scope

1. Change only the `generate-story-and-storyboard` Modal function in `deployment/modal/srs_v23/language_audio_app.py`:
   - request GPU choices in order `L4`, `L40S`, then `A10`; retain L4 as first preference;
   - keep `min_containers=0`, `max_containers=1`, `timeout=600`, and `retries=0`;
   - set the story worker `scaledown_window=120` seconds;
   - create a story-only image layer with `HF_ENABLE_PARALLEL_LOADING=true` and `HF_PARALLEL_LOADING_WORKERS=4`; leave the Teacher Deck image unchanged;
   - add privacy-safe stage timing logs for worker start/GPU type, model load, prompt encoding, and token generation. Do not log prompts, child/profile data, or generated text.
2. Keep Qwen/Qwen2.5-7B-Instruct, its pinned revision, Python/PyTorch/Transformers/Accelerate versions, request schema, story business rules, and disabled workload status unchanged.
3. Deploy only the FEAT-063 `dev` language/audio Modal app and make exactly one fresh synthetic Parent story request after recording its dispatch intent. Record the Modal call ID immediately after `spawn` and before polling.
4. Cap the client-side queue/result wait at 300 seconds. If the call has not completed by then, request cancellation, verify the call/app state, and do not retry or dispatch a second call. A pre-dispatch deployment/setup failure is recorded without dispatching a replacement request.
5. Save exact timing, worker GPU, model-load and output-contract results, call/app identifiers, and cleanup evidence under `evidence/` and `evidence/assets/modal_serverless_story_latency_20261105/`.
6. Stop the task-owned language/audio Modal `dev` app after the experiment and verify that it has no active task/container. Retain shared Volumes and checkpoints.

## Explicit exclusions

- No video inference, FLUX, drawing VLM, SAM2, Teacher Deck inference, or other workload calls.
- No real child/profile data; use a newly generated synthetic Parent fixture only.
- No changes to the canonical SRS, model selection/revision, worker schema, business rules, API, backend, quotas, production configuration, or workload enablement.
- No persistent `min_containers`, parallel GPU concurrency, memory snapshots, duplicate/unknown-call retry, Volume/checkpoint deletion, commit, push, or merge.
- The fallback list and 120-second scaledown are a bounded dev experiment, not a production default or an availability/cost guarantee.

## Acceptance criteria

- The deployed story function reports the configured fallback order and remains scale-to-zero (`min_containers=0`, maximum one container).
- The one request either returns a valid story output matching the existing worker contract, or is classified with evidence as pre-dispatch failure, GPU queue timeout/cancelled, worker/model error, or output validation failure.
- When a worker starts, evidence separates queue time, model-load time, prompt-encoding time, and generation time, and identifies the actual GPU type without capturing personal or prompt content.
- No second story call and no video call are dispatched.
- The task-owned Modal app is stopped after the run; no task-owned active container remains; shared Volumes are retained.
- The final report compares the observation with the 2026-11-04 baseline and states the experiment's limitations, including that one sample cannot establish a latency distribution.

## Verification plan

1. Static-check the exact Transformers v4.53.0 source for the two parallel-loading variables and run compile/lint checks on the changed Modal source and experiment runner.
2. Review the diff against this file allowlist: `deployment/modal/srs_v23/language_audio_app.py`; this plan; the matching approval and feature context/decision/source/status/evidence index; one experiment runner and task-local evidence files.
3. Check existing Modal dev app/container state before deployment; deploy only the language/audio app.
4. Use a new synthetic fixture, unique job/generation/attempt IDs, the pinned Qwen checkpoint and existing contract validation. Record dispatch intent before the single `spawn` call and flush the returned call ID to disk before waiting.
5. Stop/cancel at the 300-second client cap if still pending; never rerun an ambiguous call.
6. Stop the task-owned app, verify final status and zero active task/container, and inspect saved output/log records for accidental prompt or personal data.

## Risks and interpretation

- Modal GPU fallback support is documented, but actual allocation is capacity-dependent. The ordered choices may still queue beyond five minutes.
- L40S can have a different runtime price/performance profile than L4/A10. The experiment reports the assigned GPU; no production cost policy is inferred.
- A 120-second scaledown window may bill idle resources during that interval. The app will be explicitly stopped after the test; persistent warm containers are excluded.
- Parallel shard loading is supported in the pinned Transformers v4.53.0 source. Its effect depends on shard count and storage/CPU behavior; it cannot remove GPU scheduling delay.
- GPU Memory Snapshots are not included: Modal currently marks GPU snapshots Alpha and documents that they generally do not accelerate model-weight loading from storage.
- The 2026-11-04 readiness probe loaded the exact Qwen checkpoint in 15.989 seconds and completed a smoke generation in 1.297 seconds after GPU allocation. That was not the full story workload and is only an approximate baseline for model initialization, not a direct end-to-end comparison.

## Files in scope

- `deployment/modal/srs_v23/language_audio_app.py`
- `features/FEAT-063-system-architecture-rearchitecture/plan/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_modal_serverless_story_latency_20261105.py`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/modal_serverless_story_latency_20261105/`
