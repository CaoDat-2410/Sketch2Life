# FEAT-038 status

Status: REVIEW
Updated: 2026-10-28

The revision-1 plan hash is recorded in `approvals/TASK_APPROVAL.md`.

- Implemented the dedicated Lightning Bash launcher and removed the unavailable `PipeConnection` import/type reference.
- `bash -n tools/start_lightning_vision_v2.sh` passed using Git Bash on the workstation.
- Source inspection confirms the launcher reads the auth variable from its environment and does not contain its value; it does not submit inference at startup.
- Pending: launch in Lightning Studio to confirm the remote Python 3.12 import, model mounts, CUDA libraries, and port exposure. No live model/provider call has been made.
- 2026-10-28 review: source and official documentation support a custom Modal App endpoint as a feasible migration path for Vision/ASR/SAM after packaging/configuration work. Managed Endpoints differ from the current custom contracts. Combined memory, latency, cost and runtime readiness on Modal are NOT_MEASURED; implementation/deployment and the separate video migration remain unapproved.
