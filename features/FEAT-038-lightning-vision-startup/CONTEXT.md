# FEAT-038 Lightning vision server startup context

## Goal

Make the existing Lightning Vision V2 server start under the project's Python 3.12 runtime using an explicit Bash launcher, while keeping runtime credentials outside repository files.

## Constraints and assumptions

- The target runtime is a Linux Lightning Studio with the project at `/teamspace/studios/this_studio/Sketch2Life` unless overridden by environment variables.
- Model weights and the SAM2 checkout remain local to the Studio and are not copied into the repository.
- `LIGHTNING_DEV_AUTH` is supplied by the Lightning managed secret/runtime environment; the launcher must never contain or print its value.
- Startup must not submit an inference request or load model weights. Model initialization remains request-driven in the server.
- The existing `tools/start_local_backend.ps1` is a separate Windows/local API launcher and remains unchanged.

## Current status

The approved launcher and Python 3.12 import fix are implemented. Bash syntax and source inspection pass locally. Starting the service against the Lightning Studio's model mounts remains to be confirmed there; no remote service launch or inference request has been made from this workstation.

## Modal portability review — 2026-10-28

The owner requested a source-based assessment of moving the existing Lightning configuration to a Modal endpoint. The review finds the Vision/ASR/SAM FastAPI service portable in principle through a custom Modal App HTTP endpoint, with explicit image/dependency packaging, model mounts, runtime secrets, memory checks and latency verification. The dashboard's managed Endpoints product uses different API contracts and is not a direct replacement. Video is a separate service with additional local-artifact and long-job constraints. No migration was implemented or deployed; the revision-1 approval is unchanged. See `evidence/MODAL_PORTABILITY_REVIEW_20261028.md` for sources, limits and a proposed follow-up plan.
