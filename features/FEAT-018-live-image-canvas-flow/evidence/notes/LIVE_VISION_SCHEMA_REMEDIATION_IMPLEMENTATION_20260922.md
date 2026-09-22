# Live VLM schema-output remediation implementation

- Feature: `FEAT-018-live-image-canvas-flow`
- Date: 2026-09-22
- Branch: `codex/feat-018-contract-plan`
- Scope: Lightning `/v2/vision` live demo route only
- Approval: `approvals/TASK_APPROVAL.md`, owner approval dated 2026-09-22

## Implemented behavior

- Reused the existing FEAT-027 bounded Qwen payload normalizer; no second normalization system was
  introduced.
- Enabled bounded repair only in the live Lightning route. The strict adapter/offline path remains
  non-retrying when bounded repair is disabled.
- On the first typed mapping/schema failure, the adapter may perform exactly one repair generation.
  The second result is mapped and validated normally; a second failure is returned as a typed
  `VISION_SCHEMA_INVALID` result and cannot trigger a third generation.
- The repair prompt uses only canonical instructions and closed diagnostic enum values. No raw
  model output, image bytes, narration, credentials, child data or raw exception text is included.
- The route logs only typed outcome, attempt/repair state and closed diagnostic tokens.
- The route now treats a blank `SKETCH2LIFE_VISION_MODEL_DIR` as unset and normalizes the local
  operator alias `MODEL_DIR` before applying the legacy `SKETCH2LIFE_VLM_ROOT` fallback. An
  explicitly configured model directory remains authoritative; a placeholder path is still
  invalid and must be replaced by the owner.

## Local verification

Passed:

- `backend/tests/unit/test_qwen_vision_adapter.py` — 50 passed
- Combined Qwen/schema-path/Phase-B contract sweep — 5 existing skips, remaining tests passed
- Live route repair-prompt privacy tests
- Ruff on touched Python files
- Python compile check
- `python tools/validate_architecture.py`
- `python tools/validate_repository_security.py`
- `git diff --check`

Mypy was attempted for the touched source files but was blocked by the local Windows Application
Control policy while loading a Python DLL. No live Lightning request was made by Codex.

## Remaining owner check

The owner must pull this worktree/commit into Lightning, start the server with the approved Qwen
model snapshot, and manually run the synthetic/non-child smoke matrix within the existing
approximately 25-credit ceiling. Expected logs expose only `status`, typed `error_code`/detail,
`attempt`, `repair_attempted`, and closed `mapping_diagnostics` tokens.
