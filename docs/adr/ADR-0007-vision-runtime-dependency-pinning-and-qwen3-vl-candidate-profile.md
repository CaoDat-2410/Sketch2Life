# ADR-0007: Vision runtime dependency pins and Qwen3-VL candidate profile

- Status: Recorded for P2-T3 Phase B B1; no profile freeze and no runtime default
- Date: 2026-09-01
- Scope: Local contract/configuration/adapter skeleton and no-GPU validation only
- Approval: `features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`, P2-T3 Phase B

## Context

The approved B1 slice needs an additive real-model contract without changing the frozen
Phase A V1 models, catalog, hash functions, fake adapter, or behavior. It also needs enough
model and dependency provenance to make a later runtime study reproducible, while keeping
weights, provider credentials, prompts, model output, and machine-local paths out of Git.

This record is a B1 provenance and boundary decision. It is not a model-selection freeze,
production-provider decision, deployment decision, or authorization for B2-B5 execution.

## Decision

### V1 remains frozen

Phase A remains in `backend/src/sketch2life/contracts/schemas/vision.py`. The real-model
candidate uses disjoint V2 profile ID, request, profile, catalog, and result types in
`vision_v2.py`. V2 has separately named `vision_profile_config_hash_v2()` and
`vision_profile_catalog_hash_v2()` functions. The only canonical V2 catalog contains one
candidate; it is not a per-request dynamic catalog and it never contains a V1 profile.

### Candidate provenance captured at B1

| Field | Recorded value |
|---|---|
| V2 profile ID | `QWEN3_VL_8B_INSTRUCT_BF16_V1` |
| Model identifier | `Qwen/Qwen3-VL-8B-Instruct` |
| Immutable revision | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |
| License | `apache-2.0` |
| Weight source | `https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct` |
| Repository-level weight SHA-256 | Absent: the official source did not publish a single digest that was verified for this record; no weights were downloaded |
| Absence reason | `SOURCE_DOES_NOT_PUBLISH_A_DIGEST` |
| Compute profile | `GPU_BF16` |
| Adapter kind/version | `QWEN_VL_LOCAL` / `qwen3-vl-local-adapter-v2-b1` |
| Timeout budget | `120.0` seconds per adapter inference attempt |
| Decode identity | greedy (`sampling_enabled=false`, `temperature/top_p/top_k=null`, `beam_count=1`, `max_new_tokens=512`, `repetition_penalty=1.0`, `seed=0`) |
| Image preprocessing identity | `qwen3-vl-processor-config-b1` |

The revision and license are recorded from the official Hugging Face model page and its
immutable commit page. The official Qwen repository and Transformers documentation support
the Qwen3-VL Transformers loading/processor path. The exact runtime behavior, local device
feasibility, and the model's compatibility with these exact pins remain B2 verification items.

### Exact optional dependency pins

The optional `vision-qwen` extra records these exact pins, in canonical package order:

```text
accelerate==1.10.1
qwen-vl-utils==0.0.14
torch==2.8.0
transformers==4.57.6
```

These versions were selected from the official Qwen guidance (`transformers>=4.57.0` and
`qwen-vl-utils==0.0.14` in its deployment guidance) and the corresponding PyPI release
records. The extra was not installed in B1. No wheel, weight, cache, or model artifact was
downloaded.

The contract's decoding names are configuration identity fields, not a claim that every
parameter has already been verified against the exact pinned model runtime. The injectable
test seam exercises only generic Transformers-style generation fields already shown by the
official documentation. B2 must verify the exact pinned Qwen processor/model calls and any
provider-specific mapping before a live run. No timeout/deadline/cancellation parameter is
invented or passed to the model API.

### Runtime configuration and timeout design

`QwenVisionRuntimeConfig` is constructor-injected and lives under `infrastructure/ai`; it is
not added to shared application `Settings`. It reads only these local keys when an explicitly
selected env file is used:

```text
SKETCH2LIFE_VISION_MODEL_DIR
SKETCH2LIFE_VISION_MODEL_CACHE_DIR
SKETCH2LIFE_VISION_DEVICE
SKETCH2LIFE_VISION_DEVICE_INDEX
SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD
```

There is no default model or cache path. The committed `.vision.env.example` contains
placeholders only; the local `backend/.vision.env` path is ignored. The B1 default runner
loads and generates inside a spawned, killable subprocess. The parent enforces the profile's
deadline, terminates and joins the worker on expiry, and has a second kill fallback. Thus a
timeout does not abandon a synchronous model call in a thread or leave residual generation
running after the typed result is returned. A timeout on either inference attempt is terminal;
there is no third attempt.

The subprocess mechanism is a B1 design boundary, not runtime evidence. B2 must verify actual
model/device cleanup, subprocess behavior with the pinned CUDA stack, and any provider API
deadline/cancel capability before relying on a live measurement. B1 makes no claim about local
8 GB feasibility.

### Repository hygiene and non-goals

Only the approved local runtime/cache/image paths are ignored: `backend/.vision.env`, the
future B4 image payload directory, `**/qwen-vl-cache/`, and `models/`. No real env file,
credential, endpoint, weight, prompt, model output, or child data is committed. B1 does not
add a benchmark runner, download flow, GPU/cloud/provider execution, API/UI/mobile/database/
queue integration, result promotion, or profile/runtime default.

## Official sources

- [Qwen3-VL-8B-Instruct model page](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) — model identifier and license.
- [Immutable Hugging Face model revision](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/commit/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b) — revision recorded above.
- [Qwen3-VL official repository README](https://github.com/QwenLM/Qwen3-VL/blob/main/README.md) — official Transformers path and dependency guidance.
- [Official Transformers Qwen3-VL documentation](https://huggingface.co/docs/transformers/en/model_doc/qwen3_vl) — model/processor API reference.
- [accelerate 1.10.1](https://pypi.org/project/accelerate/1.10.1/), [qwen-vl-utils 0.0.14](https://pypi.org/project/qwen-vl-utils/0.0.14/), [torch 2.8.0](https://pypi.org/project/torch/2.8.0/), and [transformers 4.57.6](https://pypi.org/project/transformers/4.57.6/) — selected exact release records.

## Unresolved for B2

- Verify the exact pinned runtime/model/processor loading and generation parameter mapping.
- Verify local GPU, VRAM, CUDA, and BF16 feasibility using synthetic fixtures only.
- Verify worker termination/device-memory cleanup and any supported provider-level cancellation
  capability; do not add a deadline parameter until verified.
- If the official weight source later publishes a usable repository-level SHA-256, replace the
  explicit absence statement only through a reviewed provenance update; otherwise retain the
  absence reason.
