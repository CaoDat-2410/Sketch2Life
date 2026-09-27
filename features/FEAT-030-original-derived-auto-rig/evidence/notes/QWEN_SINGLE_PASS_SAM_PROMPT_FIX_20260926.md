# Qwen single-pass and SAM prompt handoff fix

Date: 2026-09-26; updated 2026-09-27
Scope: Lightning `/v2/vision` and backend SAM 2.1 prompt preparation

## Findings

- The Lightning vision route enabled bounded repair for every request.
- The default Qwen runner owns model loading inside a fresh killable subprocess per attempt.
- A repair therefore produced a second checkpoint-shard load before the single HTTP access log.
- The SAM worker correctly rejected a request without a box or point prompt with
  `PROMPT_REQUIRED`; the backend auto-proposal could return `None` when Pillow was unavailable
  or when downsampling split a drawing into small disconnected strokes.

## Changes

- Live Lightning vision now uses one Qwen inference by default.
- Bounded repair remains available only with the explicit benchmark flag
  `SKETCH2LIFE_LIGHTNING_VISION_BOUNDED_REPAIR=true`.
- Structural normalization is enabled independently for the live route, allowing safe in-memory
  conversion of common Qwen JSON shape drift without a second inference.
- The backend declares Pillow as a runtime dependency for image prompt preparation.
- Colored/ink pixels are clustered before choosing a component box, with a bounded aggregate
  fallback for sparse drawings. Blank images remain fail-closed and no full-frame prompt is sent.
- Structured vision logs include whether bounded repair was enabled.

## Verification

Command:

```text
$env:PYTHONPATH='backend/src'; backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_lightning_sam21.py backend/tests/unit/test_qwen_vision_adapter.py --basetemp "$env:TEMP\sketch2life-qwen-sam-fix"
```

Result: `57 passed` after adding the one-inference structural-normalization regression test.

Additional checks:

- A synthetic colored drawing produced a normalized prompt region:
  `x=0.21375, y=0.16333, width=0.37458, height=0.72333`.
- A blank drawing returned no prompt.
- The server flag resolves to `False` by default and `True` only for the explicit `true` value.
- `compileall` passed for the touched server, backend AI module, and SAM tests.

## Remaining deployment action

Restart the local backend and pull/restart the Lightning worker after this change. The remote
worker should show one Qwen shard-load sequence for `/v2/vision`, followed by a `/v2/rig/segment`
request containing a non-null `prompt_region` for a non-blank drawing.
