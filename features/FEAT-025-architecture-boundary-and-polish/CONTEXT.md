# FEAT-025 — Architecture boundary and backend workflow polish

## Status

`IMPLEMENTED_WITH_EXTERNAL_GATES_PENDING`

This feature is a follow-up to FEAT-024. Implementation is now in progress. The
current repository audit found a real dependency-direction violation in the
backend workflow service and no existing 3D runtime implementation.

## Problem statement

`backend/src/sketch2life/application/services/backend_ai_workflow.py` imports
and constructs infrastructure objects directly. The service currently knows
about catalog loaders, Pixi asset catalog, and the file media inspector. This
violates the repository rule that application depends inward and is reported
by `tools/validate_architecture.py` as `ARCHITECTURE_INVALID`.

The workflow also contains composition and catalog lookup responsibilities in
the same orchestration class. That makes future provider/catalog changes more
expensive and makes unit tests depend on filesystem-backed infrastructure.

The user additionally requested polish described as “hiếu 3d”. The source
audit found no `three.js`, GLTF/GLB, mesh, voxel, or 3D model runtime in the
current backend/mobile/catalog source. The plan therefore keeps 3D work
explicitly gated until the requested meaning and target are confirmed.

## Goal

Restore dependency direction and polish the backend-only workflow without
changing the public workflow contracts, weakening fail-closed behavior, or
silently introducing a UI/3D runtime.

## Non-negotiable constraints

- backend only; no UI integration;
- real ASR/VLM path remains the only demo path;
- no fixture recommendation or provider-output bypass;
- catalog assets and provenance remain immutable and traceable;
- V1/V2 contracts remain backward compatible unless an additive contract
  change is explicitly approved;
- no actual 3D implementation is included until the user clarifies the
  “hiếu 3d” request;
- one coherent implementation commit after verification, unless the user
  explicitly requests another strategy.

## Implementation result

The application/infrastructure dependency-direction violation is fixed. The
workflow now receives an immutable application-owned dependency bundle and the
CLI composition root owns all concrete catalog/media/asset construction. The
focused regression suite, compile, lint, architecture, and repository security
checks pass. A repository-wide rerun is blocked by the separate untracked
FEAT-026 feature: it is missing two required evidence directories and contains
an external-document artifact rejected by the security policy. Real Lightning
smoke also remains external.

## Current audit evidence

- `python tools/validate_architecture.py` currently reports one application
  layer violation in `backend_ai_workflow.py`.
- No 3D runtime/source references were found under backend, mobile, workflow
  feature source, architecture docs, or README.
- FEAT-024 targeted tests and harness/security checks remain green; its real
  Lightning smoke gate is still pending.
