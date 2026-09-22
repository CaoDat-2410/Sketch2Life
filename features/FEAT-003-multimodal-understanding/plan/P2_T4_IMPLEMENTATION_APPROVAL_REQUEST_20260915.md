# P2-T4 G2 implementation-approval request

- Status: **REQUESTED — NOT GRANTED**
- Request date: 2026-09-15
- Owner: Person 2
- Feature: FEAT-003 multimodal understanding
- Contract prerequisite: G1-approved `P2T4.P2T4FusedResultV1@1.0`
- Immutable freeze commit: `18d0c33d35431ca96a76692a68c6b992098699e7`
- Freeze SHA-256: `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2`
- Package SHA-256: `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`

## Requested scope

G2 requests authorization to create and modify exactly these seven offline implementation and
test/fixture paths, and no other implementation path:

1. `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`
2. `backend/src/sketch2life/application/services/p2_t4_fusion.py`
3. `backend/tests/contract/test_p2_t4_contract.py`
4. `backend/tests/unit/test_p2_t4_fusion.py`
5. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`
6. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`
7. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`

The seven paths are the complete proposed implementation boundary. They must not be expanded by
inference, convenience, generated output, or an unlisted helper. No path is authorized until the
owner grants G2 explicitly.

## Required implementation boundary after approval

- Implement only the immutable G1 contract identity and semantics. Preserve the exact P2 ASR and
  Vision input identities, rejection precedence, admissibility invariant, canonical references,
  conflict behavior, uncertainty precedence, primary-before-adjustment rule, Decimal arithmetic,
  and privacy restrictions recorded by G1.
- Keep the service deterministic, model-free, provider-free, network-free, GPU-free, and free of
  Lightning/runtime integration.
- Keep the outer validation boundary separate from the pure `fuse()` boundary. Unknown objects,
  mapping-shaped inputs, provider payloads, raw exceptions, raw paths, and raw model output must
  not cross the typed contract boundary.
- Preserve source observations and provenance. Do not adopt the B0 mapping, replace FEAT-018
  contracts, change P2-T2/P2-T3 contracts, or modify FEAT-018/FEAT-020 code, routes, ports,
  registries, sessions, idempotency, Gate A, migration, API, queue, storage, or UI behavior.
- Do not add `NOT_FUSIBLE`; v1 statuses remain `FUSED | UPSTREAM_FAILURE`.
- Use CPython 3.13.x for canonicalization/determinism evidence. The architecture validator must
  be reported truthfully as `ARCHITECTURE_INVALID` with only the approved baseline fingerprint:
  `application imports an outer layer` at
  `backend/src/sketch2life/application/services/backend_ai_workflow.py`, expected count `1`,
  validator SHA-256
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`. Any additional or changed
  finding blocks the implementation checkpoint.

## Explicit non-authorizations

This request does not authorize Lightning, CUDA, model/provider execution, network/downloads,
production use, runtime or integration adoption, mapping migration/cutover, P2-T5, or changes to
any path outside the seven-file list. Evidence files, manifests outside the listed fixture paths,
validator-output records, and generated artifacts require separate authorization or must remain
operator-local until explicitly named.

## Required gates if G2 is granted

1. Record the exact owner approval and the seven paths in `approvals/TASK_APPROVAL.md`.
2. Implement only the seven paths; capture no raw model/provider output or sensitive data.
3. Run focused contract/unit tests, repository harness/security/skeleton checks, and the
   architecture validator under Policy B.
4. Perform an independent diff/governance review before any implementation commit.
5. Commit the exact candidate checkpoint, then bind any separately authorized evidence to that
   commit and the immutable G1 digests.

## Owner decision requested

Approve or reject G2 for the exact seven paths above. Approval must state that it is separate from
G1, does not authorize runtime/integration/live execution, and does not authorize any unlisted
file or evidence artifact.
