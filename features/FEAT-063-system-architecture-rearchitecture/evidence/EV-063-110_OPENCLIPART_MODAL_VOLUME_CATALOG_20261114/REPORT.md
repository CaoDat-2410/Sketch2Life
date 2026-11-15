# EV-063-110 — Openclipart catalog on Modal Volume

**Date:** 2026-11-15 (Asia/Ho_Chi_Minh)<br>
**Plan:** [Rev87.15](../../plan/PLAN_REV87_15_MODAL_OPENCLIPART_CATALOG_QWEN_STROKES_20261114.md)<br>
**Runtime status:** Full Modal catalog import and `/health` passed. One real Qwen inference reached output validation and failed path coverage. No retry was sent.

## What was run

1. Deployed `sketch2life-srs23-language-audio-dev` in Modal `dev`, including `generate-topic-svg-stroke-guide-draft` and CPU-only `health-api`.
2. Resumed the CPU-only importer for `kawwaaa/openclipart` into Modal Volume v2 `sketch2life-openclipart-catalog-dev`. The importer resolved the immutable revision `df38e5ef633be067d397df7da19a9f009e69b3bd`, processed all 18 source shards, verified each stored shard hash, then returned `READY`.
3. Called `/health`. Qwen3.5-9B checkpoint and the SVG catalog both reported `ready`; health used no GPU and executed no inference.
4. Dispatched exactly one synthetic topic request (`con mèo`, `beginner`) to the deployed Qwen worker. No child image/profile/voice, Parent account, DB/consent, video, or fixture was used.

The dataset corpus and derived index remain only on the dedicated Modal Volume. No corpus was copied into Docker, the local repository, or the mobile app.

## Import result

| Metric | Result |
|---|---:|
| Dataset revision | `df38e5ef633be067d397df7da19a9f009e69b3bd` |
| Source shards | 18 / 18, verified |
| Source rows | 178,561 |
| CC0 records counted by importer | 178,135 |
| Unique SQLite source rows | 178,134 |
| Guide-eligible SVGs | 1,923 |
| Not guide-eligible / rejected | 176,638 |
| Original compressed shard bytes | 22,340,611,707 (~20.8 GiB) |
| Extracted SVG bytes | 87,741,484,027 (~81.7 GiB) |
| SQLite catalog | 202,518,528 bytes |
| Total durable Volume data | 110,284,614,262 bytes (~102.7 GiB) |
| Volume | `sketch2life-openclipart-catalog-dev`, v2, environment `dev` |

The importer counted one repeated `source_id`; SQLite's primary key/`INSERT OR REPLACE` leaves one unique source row, explaining the 178,135 versus 178,134 count. The importer returned `READY` after complete shard/hash verification. Its final result is preserved in [modal-import-result.json](modal-import-result.json), with shard logs in [modal-import-logs.txt](modal-import-logs.txt).

### Storage cost note

Modal's current [pricing page](https://modal.com/pricing) lists Volume storage at $0.09/GiB-month with 1 TiB/month included. This catalog is approximately 102.7 GiB, so it is within that allowance by itself; total workspace storage and any other billable usage were not measured. Modal documents daily storage snapshots and up to four days of residual storage billing after deleting data in its [Volume guide](https://modal.com/docs/guide/volumes).

## Health result

`/health` returned `status=ok`, Qwen checkpoint `ready` at pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, and SVG catalog `ready` on Volume v2. `gpu_allocated=false` and `inference_executed=false` for this health call. See [modal-health.json](modal-health.json).

## Real Qwen inference result

- Modal call: `fc-01M7DQQQNP9VDA8NHJ3EPHD9HN`
- Workload: `svg.topic-stroke-guide.generate`
- Model: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- Elapsed from dispatch to terminal worker failure: about 109.1 seconds
- Model load: 25.968 s
- Catalog query expansion: 39.494 s
- Catalog candidate search: 3.690 s
- Source render: 0.311 s
- Prompt encoding: 0.018 s
- Qwen inference: 25.547 s
- Failure phase: `output_parse_and_source_identity_validation`
- Terminal error: `SVG_CATALOG_STROKE_PLAN_PATH_COVERAGE_INVALID`

The request was **not a timeout**. Model generation completed, but the worker rejected its stage plan because the selected source paths were not covered exactly once. The worker does not log raw model output, so these logs cannot distinguish a missing path from a repeated path. No final SVG guide was returned or previewed. No retry/additional inference was performed. Full bounded worker log is in [modal-worker-logs.txt](modal-worker-logs.txt); the machine-readable summary is [modal-worker-summary.json](modal-worker-summary.json).

## Scope and limitations

- This tested the real Modal catalog → Qwen worker path, not the authenticated Parent HTTP API, Parent UI, Android emulator, or Teacher presentation.
- `workloads.json` remains disabled by default; the direct worker call did not enable the product workload.
- Video generation was not requested or tested.
- No child data, Firebase account/consent, DB/profile seed, secret, or Docker dataset change was made.
- The worker function has `min_containers=0` and `scaledown_window=120`; no GPU is configured to remain warm. The deployment object remains available in `dev`.
- No commit or push was made. This evidence and the runtime runner are uncommitted in the active worktree.

## Acceptance status

- **Pass:** the full corpus and derived catalog are on the dedicated Modal Volume; all 18 original shards passed integrity verification; no local/Docker copy.
- **Pass:** Qwen app deployed and CPU `/health` confirmed the pinned model and catalog ready.
- **Fail:** real Qwen output did not satisfy exact source-path coverage; no stroke guide was produced.
- **Not run:** Parent API/UI/Android integration and Teacher presentation runtime.
