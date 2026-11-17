# FEAT-038 Lightning vision server startup fix

Status: APPROVED — implementation in progress
Revision: 1
Date: 2026-10-09

## Goal

Allow the Lightning Vision V2 service to import and start in its Python 3.12 Linux environment using a clear, secret-safe Bash launcher.

## Scope

- Add `tools/start_lightning_vision_v2.sh` to configure the provided project/model paths, validate the required auth secret is already present in the runtime environment, configure Python imports, and launch the existing Uvicorn app.
- Remove the unsupported `PipeConnection` import and use `Connection` for the corresponding type annotation in `backend/src/sketch2life/infrastructure/ai/qwen_vision.py`.
- Add feature-local evidence and update feature context/status after implementation.

## Out of scope

- Changing API contracts, model profiles, inference behavior, security/auth semantics, or provider integrations.
- Embedding or rotating credentials in code. The exposed credential must be rotated by the owner in Lightning managed secrets.
- Downloading/installing model weights, dependencies, or running live Qwen, SAM2, ASR, or provider inference.
- Changing `tools/start_local_backend.ps1` or unrelated dirty workspace files.

## Acceptance criteria

1. The Python module no longer imports `PipeConnection`; the runtime endpoint annotation uses the supported `Connection` type.
2. The new launcher uses Bash syntax, configures the supplied Qwen/SAM2/ASR paths and CUDA settings, and runs `tools.lightning_vision_v2_server:app` on port 8000 by default.
3. Missing `LIGHTNING_DEV_AUTH` stops launch with a message that does not reveal any secret value; the repository launcher contains no credential value.
4. Startup remains lazy: no model/provider request is made by the launcher.
5. The feature records implementation evidence and its final status without changing unrelated workspace files.

## Implementation steps

1. Add this plan and record the owner's direct approval.
2. Implement the isolated Python import and Bash launcher changes.
3. Record exact changed files, static inspection, and any runtime limitations in `evidence/` and update status/context.

## Verification plan

- Inspect the Python import and annotation change.
- Parse the launcher with Bash syntax checking when Bash is available; do not start the remote service or make model/provider calls from this workstation.
- Confirm the launcher uses an externally supplied secret and does not print it.

## Risks

- The remote Studio's model directory layout or managed-secret configuration may differ from the supplied paths; the script allows the root/model directory variables to be overridden.
- This workstation cannot establish that remote model weights, CUDA runtime, or Lightning networking are ready. Those require a Studio-side launch after this patch.
