# P1 runtime verification — 2026-09-10

The verification exercised the actual FastAPI/Uvicorn process and the real
Lightning adapter serialization path. A temporary local HTTP stub returned
contract-shaped ASR and vision JSON; no external Lightning, Runpod, production
API or credential was used.

Observed results:

- `/health` returned `200`.
- `/v1/live-understanding` returned `200`, `PROPOSAL`, `gate_a_required=true`,
  `AsrResultV1`, and `VisionUnderstandingResultV1` with the `butterfly` label.
- The smoke script exited `0` and verified source hashes for both fixture media.
- A request with `expected_session_version=2` returned `409`, `STALE_SESSION_VERSION`.
- The P1 compiler loaded the committed golden catalog and compiled `ACT-0004 v2`
  to `OBJ_OBJECT_PERMANENCE v1`, producing a spec hash and an approved Gate B.
- Workspace typecheck/tests, the 23-case offline integration fixture suite, the
  backend suite, P1 unit tests, and all repository/P1 validators passed.

This proves local process, HTTP, adapter, contract, fixture hash, catalog and
Gate B behavior. It does not claim that the external live provider, Android
device flow, P3 renderer, P4 media, or shared gallery integration is complete;
those remain outside the approved P1 slice.
