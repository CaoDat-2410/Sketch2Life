# SAM2.1 runtime availability diagnostic — 2026-09-27

## Observed Lightning evidence

The live worker now reports one successful Qwen request followed by a typed SAM2 failure:

```text
vision_request_completed status=SUCCEEDED entities=4 actions=0 themes=0 attempt=1 repair_attempted=True
POST /v2/vision HTTP/1.1 200 OK
sam21_segmentation_completed status=FAILED code=MODEL_UNAVAILABLE retryable=True
POST /v2/rig/segment HTTP/1.1 200 OK
```

This proves Qwen is no longer being invoked twice. `MODEL_UNAVAILABLE` is emitted only for a
missing SAM2 checkpoint, unavailable SAM2/PyTorch imports, or unavailable CUDA; it is not a mask
quality rejection and does not indicate a mobile/UI contract failure.

## Repository change

- The Lightning runtime now accepts `SAM2_MODEL_DIR` (or
  `SKETCH2LIFE_SAM21_MODEL_DIR`) as a directory fallback and resolves the standard Hiera Small
  checkpoint names when the explicit checkpoint path is absent or renamed.
- Relative SAM2 config paths are resolved against the process directory, the model directory,
  and the installed `sam2` package. Hydra-owned config names remain unchanged when the package
  owns the config search path.
- The provider response remains the safe typed `MODEL_UNAVAILABLE` result. The private worker
  log additionally emits a closed diagnostic reason such as `CHECKPOINT_NOT_FOUND`,
  `RUNTIME_DEPENDENCIES_UNAVAILABLE`, or `CUDA_UNAVAILABLE`.

## Verification

- `backend/tests/unit/test_sam21_runtime_config.py`: 2 passed.
- Ruff passed for the changed Python files.
- Python compile check passed for the changed Python files.
- Full SAM2 integration remains pending in the private Lightning environment because model
  weights and the optional SAM2 runtime are intentionally not committed to the repository.
