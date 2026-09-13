# Real-AI `AI_FAILED` patch evidence

Date: 2026-09-13

## Observed Lightning result

The real runtime preflight passed on an NVIDIA L4 after Qwen3-VL 8B and faster-whisper Turbo were downloaded. The backend still returned `AI_FAILED` for every age band before selection, with only the generic reason `real ASR/VLM returned a typed failure`.

## Patch scope

- Qwen3-VL chat-template generation follows the official processor call shape and does not pass the unsupported `enable_thinking` keyword. The reviewed Vietnamese prompt now explicitly distinguishes `observation_id` from `id` and requires `label`, `predicate`, and `note` to be nested text objects.
- The workflow failure stage now exposes sanitized typed provider diagnostics: provider status, enum error code/detail, retryability, attempt number, repair flag, and vision policy state. Prompts, raw model output, credentials, and runtime paths are never copied into the manifest.
- The existing Transformers runner unit test asserts the non-thinking flag so the integration fix is protected from regression.

## Validation status

- Ruff format: passed.
- Ruff check: passed.
- Mypy on patched modules: passed.
- Qwen adapter/environment/runtime-config tests plus the Lightning E2E selector: passed; the real-AI E2E remains skipped when the local machine has no model runtime.
- The command must be rerun on the configured Lightning L4 to verify the real provider path and capture the now-specific failure code or complete workflow result.