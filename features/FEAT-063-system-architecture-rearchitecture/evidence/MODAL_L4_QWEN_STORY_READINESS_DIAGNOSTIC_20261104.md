# Modal L4 Qwen story readiness diagnostic

**Status:** Complete. The model readiness probe passed; the story worker never received a GPU container.  
**Date:** 2026-11-04, Asia/Saigon  
**Approved plan:** [MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md](../plan/MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md)

## Finding

The current failure is at Modal GPU scheduling, before the story worker starts. The Qwen2.5 checkpoint is present and loadable on an L4. Modal's final function log explicitly reported that generate-story-and-storyboard was waiting for a GPU_L4 worker while Modal acquired capacity. Both story calls had status=pending, started_at=null, and container_id=null until the app was stopped. No story inference ran.

This is not evidence of a Qwen checkpoint, tokenizer, model-load, or story-parser failure. The worker timeout is 600 seconds after execution starts; it was never reached. The approved client wait cap was 1,800 seconds. The first call remained enqueued for 31m03 before shutdown, 63 seconds beyond that cap; the second local waiter returned a `RemoteError` record after 1,555 seconds. Neither call acquired a container or ran inference.

## Readiness probe

The AI worker is a private Modal function, not an HTTP server, and it does not expose /health. I used a temporary internal L4 function with the same Python 3.11 image pins, GPU, CPU/memory, read-only model Volume, and Qwen loader settings.

| Check | Result |
|---|---|
| GPU | NVIDIA L4; CUDA available |
| Model marker | Qwen/Qwen2.5-7B-Instruct, revision a09a35458c702b33eeacc393d103063234e8bc28 |
| Checkpoint | Required files present; four safetensors shards found |
| Tokenizer load | 0.538 seconds |
| Model load | 15.989 seconds |
| Smoke token generation | 1.297 seconds; 8 tokens |
| Total probe | 26.194 seconds |
| Probe container | ta-01M6KKN9K9ZDNXHF4F2TVQ7JBR; stopped with zero tasks |

The short smoke prompt did not use the worker's chat template and only checked token generation. It is not a semantic quality result. Modal emitted READY in the container log. The first local collector then failed to deserialize the returned object because local Python 3.14 did not have torch; this affected result collection only. The actual story runner used Python 3.12.

## Story worker dispatch

The deployed app was ap-b54DkVWHGM0HaQRNA6bCXB; the function was fu-a62mw2fRxW1Hu3ixHxwUIs. Autoscaler settings were minimum unset, maximum 1 container, and a 60-second scaledown window.

Two synthetic calls were visible in Modal's function-call listing. The first runner had been interrupted before its call ID was written locally; I initially mistook the absence of a local result file and tasks=0 for a pre-dispatch failure. I then submitted an instrumented call. Once Modal's function-call listing exposed both IDs, I sent cancellation requests and did not send any further calls. Both remained pending until I stopped the dev app.

| Call | Enqueued (Asia/Saigon) | State before stop | Queue wait before stop |
|---|---:|---|---:|
| fc-01M6KM0JNZSDCGR8DC2SHVFDH4 | 22:49:30 | pending; no start/container | 31m03s (63s beyond the approved 30-minute cap) |
| fc-01M6KMA2KYQTF3RA3CRPZW73K0 | 22:54:42 | pending; no start/container | 25m52s |

At 23:20:32, Modal logged that the function was waiting to be scheduled on a GPU_L4 worker and that it was acquiring more capacity. I stopped the deployed language app at 23:20:34. Before shutdown, both calls had no start time or container. The second call's local waiter wrote a `FAILED_TERMINAL` / `RemoteError` record at 23:20:19, but no worker had started; treat this as a queued-call/client observation, not a model or worker failure. After shutdown, `FunctionCall.get()` for both IDs returned `RemoteError`. The app is stopped, and the Modal container list is empty.

**Execution deviations:** (1) The approved plan allowed at most one fresh story request. The first runner had enqueued a call but was interrupted before it surfaced the call ID locally. I mistakenly interpreted the missing local result and zero active tasks as pre-dispatch, then submitted a second instrumented call. Modal later exposed both IDs. I requested cancellation for both and stopped the app; neither reached inference. (2) The first call remained queued for 63 seconds beyond the approved 30-minute cap while its runner was interrupted and the app remained deployed. These exceeded the approved bounds and are recorded here rather than treated as authorized scope. The instrumented temporary runner also raised a local `TypeError` after saving its result because its logging wrapper received `stage` twice; this did not dispatch another request or change the remote call state.

## Model/SRS alignment

The deployed story worker uses the pinned Qwen/Qwen2.5-7B-Instruct revision recorded above. The current FEAT-063 SRS v2.3 draft lists Qwen2.5-7B as a candidate for story generation. Qwen3-VL is explicitly marked NO_GO; Qwen3.5/3.6 appear in the later reassessment as candidates pending benchmark and approval, not as a promoted runtime requirement. The current Qwen2.5 worker therefore matches the approved POC profile; this test does not promote a production model.

## Implications

Increasing the client timeout does not make a queued call run. A warm container could reduce cold-start delay after capacity is assigned, but it would not resolve an L4 capacity shortage. Do not increase persistent container limits blindly; Modal's log identifies capacity acquisition as the current blocker. The next operational fix is to secure available L4 capacity for this workspace or approve a different execution profile, then rerun one synthetic story request.

The product/API path was not retested in this slice. No source, SRS, API, environment, or persistent scaling configuration was changed. No video inference or real child data was used.

## Evidence

- [qwen_l4_health_result.json](assets/modal_l4_qwen_story_readiness_20261104/qwen_l4_health_result.json)
- assets/modal_l4_qwen_story_readiness_20261104/story_call_queue_evidence.json
- assets/modal_l4_qwen_story_readiness_20261104/story_generate_dispatch_intent.json
- assets/modal_l4_qwen_story_readiness_20261104/story_attempt_2/story_result.json
