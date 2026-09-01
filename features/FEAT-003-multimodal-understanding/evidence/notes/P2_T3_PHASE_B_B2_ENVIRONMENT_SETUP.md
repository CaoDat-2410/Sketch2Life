# P2-T3 Phase B B2 environment setup readiness

- Evidence ID: `EV-003-T3-03`
- Date: 2026-09-01
- Owner: Person 2
- Scope: internal Lightning L4 environment readiness before real B2 model load/inference
- Approval authority: `approvals/TASK_APPROVAL.md`, bounded P2-T3 Phase B B1–B5 scope

## Result

The B2 environment setup now has a deterministic, sanitized readiness path in
`backend/src/sketch2life/infrastructure/ai/qwen_vision_environment_readiness.py`.
It explicitly reads the ignored `.vision.env` file, resolves the explicitly named V2 profile,
and checks the approved environment without importing Transformers or loading model weights.

The checker verifies:

- the profile's exact dependency pins, including accepting the CUDA local-version suffix on
  `torch==2.8.0+cu128` only when its pinned base version remains `2.8.0`;
- `device=cuda`, the configured device index, CUDA availability, BF16 support, and normalized
  `NVIDIA_L4` device class;
- an explicitly configured local model directory with downloads disabled, required processor and
  tokenizer/chat-template assets, every safetensors shard named by the weight index, and the
  pinned Qwen load-critical manifest present;
- Hugging Face local-directory metadata for every pinned load-critical file and indexed shard
  against the approved immutable model revision;
- the V2 profile/config/catalog hashes from the canonical approved catalog.

The output deliberately contains no environment path, package install path, provider endpoint,
credential, raw model output, prompt, or hardware free-form string. It reports only closed issue
tokens, safe version values, booleans, normalized device class, and contract hashes. Both
`model_load_performed` and `inference_performed` are structurally `false` in this setup record.

## Lightning command

Run from `backend/` after creating the ignored `.vision.env` and installing the exact B1 pins:

```bash
python -c "from pathlib import Path; from sketch2life.contracts.schemas.vision_v2 import VisionProfileIdV2; from sketch2life.infrastructure.ai.qwen_vision_environment_readiness import inspect_qwen_vision_environment_from_env_file; result=inspect_qwen_vision_environment_from_env_file(Path('.vision.env'), VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1); print(result.model_dump_json(indent=2))"
```

`READY` means only that environment configuration, exact pins, CUDA/L4/BF16, and local revision
metadata are ready. It is not the B2 typed GPU preflight required by the approved plan because it
does not load the model or execute the synthetic inference. `NOT_READY` must be preserved and
reported; no issue may be bypassed by enabling downloads or editing evidence manually.

## Test evidence

Focused tests cover a fully ready injected environment; missing and mismatched dependencies;
Torch's CUDA local-version suffix; CUDA unavailable; device-index unavailable; BF16 unsupported;
wrong device class; missing/mismatched revision metadata; explicit env-file loading; cache-only or
download-enabled configuration; non-CUDA configuration; and absence of local paths in serialized
output. They also reject a constructed profile object, missing tokenizer/chat-template assets,
incomplete per-file revision metadata, and corrupt metadata without exposing a traceback. All tests
use injected probes and temporary synthetic metadata. They do not import Qwen, load a model, invoke
a GPU/provider, or download any artifact.

Validation completed locally: the focused readiness suite passed **16 tests**; the full backend
suite passed **396 tests with 5 deliberate skips**; Ruff passed; strict mypy passed over 50 source
files; the harness, repository-security, architecture, and skeleton validators all returned their
`*_VALID` result; and `git diff --check` was clean. These are code/readiness validations only, not
Lightning runtime measurements.

## Remaining B2 gate

After a real Lightning run returns `READY`, B2 still requires one real model load and one synthetic
inference through `QwenVisionAdapter`, with typed result mapping, latency/VRAM measurements, and
worker/device cleanup evidence. Those measurements remain `NOT_MEASURED` in this setup slice.
No B3 mapping study, B4 benchmark, B5 recommendation, profile freeze, or runtime-default selection
is claimed here.
