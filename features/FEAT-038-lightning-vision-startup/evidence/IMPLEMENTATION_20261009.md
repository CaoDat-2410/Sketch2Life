# FEAT-038 implementation evidence — 2026-10-09

## Changes

- Added `tools/start_lightning_vision_v2.sh`, a Bash launcher for the Linux Lightning Studio layout. It configures Qwen, SAM2.1, ASR, `PYTHONPATH`, and Uvicorn on port 8000 by default.
- The launcher requires `LIGHTNING_DEV_AUTH` to be supplied by the runtime environment; it contains no credential value and does not print the secret.
- Changed `backend/src/sketch2life/infrastructure/ai/qwen_vision.py` to import `Connection` only and annotate the subprocess pipe as `Connection | None`.
- Left the local Windows `tools/start_local_backend.ps1` unchanged.

## Verification

- Command: `C:\Program Files\Git\bin\bash.exe -n tools/start_lightning_vision_v2.sh`
- Result: exit code 0; Bash syntax accepted.
- Source inspection: `PipeConnection` no longer appears in `qwen_vision.py`; launcher references only the name of the required secret variable and never a credential value.
- No unit or integration test suite was run. No remote server launch, model load, or provider inference was performed from this workstation.

## Remaining remote check

Run `bash tools/start_lightning_vision_v2.sh` in the Lightning Studio after rotating the exposed development token and storing the replacement as a managed secret. Confirm Uvicorn imports successfully and the model/checkpoint paths are mounted. This evidence does not claim remote runtime readiness.
