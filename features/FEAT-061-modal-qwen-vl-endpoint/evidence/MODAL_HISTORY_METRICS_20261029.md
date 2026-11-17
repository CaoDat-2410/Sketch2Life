# Modal historical metrics — final Qwen synthetic session

## Scope and source

- Owner explicitly requested that the assistant check historical Modal information using PowerShell. The assistant used the locally installed Modal CLI 1.6.3 only for read-only App information, function calls, logs, stats and metrics. No App/function/container was started, no GPU or inference request was launched, no secret value was displayed, and no installation or account modification was performed.
- Workspace/environment: owner-configured workspace, `main`; App `ap-CKwqnmWYEtmSXOMADCzC1g`, function `fu-iz7bO28VsOUluPn3St9qFQ`. Time window 2026-10-29 01:45–02:10 Asia/Saigon, with 60-second metric buckets. Modal CLI reports bucket timestamps at their starts; missing samples remain missing and are not treated as measured zeros.
- `modal app info ... --env main --no-color` reported state `stopped`, created 01:46, stopped 02:03 Asia/Saigon. Owner's previous screenshots separately reported `Finished`, zero live containers and App-level usage.
- One initial read-only `modal app logs` invocation with `--no-color` failed because this subcommand does not support that option. It was corrected by removing the option; no account or local files were modified by that failure.

## Function calls and container identity

The CLI `function calls` response for 01:59–02:04 Asia/Saigon showed the two final successful requests with the same container ID `ta-01M61Y7EWQVVTN0S3JVPA24W8R`:

| Request enqueued (Asia/Saigon) | Container | Queue (s) | Function execution (s) | State |
| --- | --- | ---: | ---: | --- |
| 02:01:42 | `ta-01M61Y7EWQVVTN0S3JVPA24W8R` | 3.30 | 15.07 | Succeeded |
| 02:02:01 | `ta-01M61Y7EWQVVTN0S3JVPA24W8R` | 0.01 | 1.66 | Succeeded |

Read-only App log search for `vision_request_completed`, with timestamps and container IDs, returned two `status=SUCCEEDED`, `entities=1`, `actions=0`, `themes=0`, `attempt=1`, `repair_attempted=True` completion lines at 02:02:00 and 02:02:02, both for that same container. Independent owner probe reports client wall times of 19.190 s / 2.408 s in the existing JSONL; these differ from Modal execution times because they measure different boundaries.

Same-container reuse is now directly observed. The source has a persistent Qwen worker/cache, making model reuse plausible; container identity alone does not independently prove the worker/model remained loaded between these calls. The second call is a warm-container observation, not a controlled load benchmark or a direct proof of model cache reuse.

## One-minute GPU metrics

`modal function metrics ... --group gpu --bucket-size 1m --json` returned `gpu_memory_avg`, unit GiB, described by Modal as average total GPU memory consumed across matching GPUs. Non-null points:

| Bucket start Asia/Saigon | `gpu_memory_avg` GiB | `gpu_count_l40s_avg` |
| --- | ---: | ---: |
| 01:50 | 0.0058186400613825144 | 0.7333276828130086 |
| 01:51 | 0.0048661773034837106 | 0.6132880687713623 |
| 01:54 | 8.385364208381118 | 0.6333277026812235 |
| 01:55 | 7.974479750768418 | 0.5019196589787801 |
| 02:01 | 2.683123595276023 | 0.266665252049764 |
| 02:02 | **17.09301842028508** | 0.9999857664108276 |
| 02:03 | 2.8492501766787126 | 0.1956330100695292 |

The largest returned one-minute **average** was 17.093 GiB at 02:02. It is not a maximum instantaneous VRAM measurement, a per-process PyTorch peak, or a guaranteed upper bound. Exact transient peak GPU memory remains `NOT_MEASURED`. The day-wide screenshot is much coarser; its approximate 1 GiB graph height must not be interpreted as the model's peak or directly compared to a one-minute average.

`gpu_count_l40s_avg` is defined as the average number of allocated L40S GPUs in each bucket. Multiplying the seven non-null values by 60 seconds gives approximately **236.65 GPU-seconds** for the listed observed buckets in this 25-minute query window. This is an estimate derived from bucket averages, not a provider billing-duration record; unreported/missing samples are not asserted to be zero and it must not be treated as a final billed figure. The owner's Dashboard screenshot shows App-level Oct 1–31 usage $0.17, with $0.13 L40S, $0.02 CPU, $0.02 memory as displayed. Those rounded amounts are not the marginal cost of the two final calls.

## Interpretation and open gates

- The source metrics are sampled/aggregated, not a latency or VRAM guarantee; there is one synthetic image and two consecutive requests. No model-quality or production readiness conclusion is supported.
- GPU peak, actual billed resource duration and total workspace spend remain unmeasured. The original probe JSONL retains its contemporaneous `NOT_MEASURED` / `NOT_VERIFIED` fields unchanged; later observations are recorded here instead of rewriting historical evidence.
- Backend integration, comparison to Lightning L4 on approved synthetic cases and production provider decisions remain outside this dev smoke. Production selection remains Runpod.
- References: [Modal function CLI metrics](https://modal.com/docs/cli/latest/function), [Modal GPU metrics](https://modal.com/docs/guide/gpu-metrics). CLI reports minimum one-minute buckets and may round time boundaries; this query uses exact minute-aligned bounds.
