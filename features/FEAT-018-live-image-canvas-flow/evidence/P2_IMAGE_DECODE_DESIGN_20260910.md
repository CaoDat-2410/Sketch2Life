# FEAT-018 P2 — Isolated image admission and decoding design

- Evidence ID: EV-018-P2-DECODE-DESIGN-01
- Date: 2026-09-10; revision: 1
- Type: completed design review / owner-selected public record
- Owner decision: accept the isolated design and publish this note, conditional on preserving the existing FEAT-003 image-research path.
- Implementation: NOT_STARTED. This design record does not amend `approvals/TASK_APPROVAL.md` or claim runtime acceptance.
- Scope: FEAT018-P2-T1 preparation, with D1 specification followed by separately scoped offline implementation and evaluation.

## Meaning of decoding

SHA-256 computes a content fingerprint; it is not reversible image decoding. Base64 decoding converts transport text back into file bytes. JPG/PNG decoding converts compressed file bytes into pixels for inspection. A small compressed file can require substantially more memory when decoded.

## Existing evidence and boundaries

Inspected repository sources:

- `backend/src/sketch2life/infrastructure/media_validation/file_inspector.py`: existing PNG inspector, 25 MiB byte ceiling, 25,000,000 pixel ceiling and per-pixel Python luminance data.
- `backend/src/sketch2life/application/services/media_validation.py`: existing P2-T1 service. The local T0 maintenance patch changes full-file hashing to 1 MiB reads; T0 is not included in this design publication.
- `backend/src/sketch2life/contracts/schemas/media_validation.py`: AVAILABLE sources require full SHA-256, current result version is 1.0, and failure reasons are a closed enum.
- `backend/src/sketch2life/domain/understanding/media_quality.py`: existing image/audio assessment and quality policy.
- `backend/src/sketch2life/infrastructure/ai/lightning_client.py` and `tools/lightning_provider_server.py`: current artifact limit is 5,000,000 bytes, checked after loading or Base64 decoding respectively; this is not a pre-parse HTTP memory limit.
- `plan/PERSON_2_AI.md`, `plan/CONTRACT_FREEZE.md`, `DECISIONS.md` and ADR-0006: feature requirements, shared-contract authority and integration ownership.

Static inspection supports the design. No decoder measurement, GPU/provider execution or model-quality result was produced by this record. Earlier reviewer-reported resource measurements are not adopted as independently verified benchmarks here.

## Preservation requirement

FEAT-018 uses an explicitly injected inspector/profile. Existing FEAT-003 defaults, call sites, validation policy, source/result schemas, PNG inspector, prompt/model/profile configuration, frozen fixtures, scoring, benchmark runners and historical evidence remain unchanged by this slice.

Reusing existing types or ports is allowed in the design; duplicating a public source-reference schema is not. Any discovered need to alter a shared contract, old default, FEAT-003 behavior or research producer connection must be presented to the owner before implementation. Existing T0 authorization remains separate.

Preservation is a design constraint to prove through diff inspection and offline regression/provenance checks; it is not an untested guarantee about future code.

## Trial configuration selected for evaluation

| Setting | Candidate value | Interpretation |
|---|---|---|
| File bytes | At most 5,000,000 | Aligns with the existing Lightning artifact ceiling; not 5 MiB |
| Original pixel count | At most 4,000,000 | Trial budget; may reject ordinary 12 MP camera files |
| Longest edge | At most 4096 pixels | Enforced together with the total-pixel limit |
| Frames | Exactly one | Static images only |
| Concurrency | One decode per trial worker | Establish baseline before scaling |
| Evaluation targets | At most 5 seconds and 256 MiB incremental process memory per image | Unmeasured targets, not hard enforcement or camera-quality evidence |

The pixel/edge/performance values are starting settings accepted for specification and evaluation, not production limits. A failure to meet them requires reporting and design revision, not changing test inputs to hide failure.

Candidate coverage: baseline/progressive JPEG RGB/grayscale and standard PNG grayscale/RGB/RGBA/palette/transparency/interlace combinations supported by the selected decoder. D1 must enumerate exact supported combinations. Initially reject 16-bit PNG, CMYK JPEG and animated images as unsupported unless explicitly added with tests and reviewed policy. Library/version selection is a D1 deliverable, not a dependency decision made by this note.

## D1 — Next task: implementation-ready specification

Specify the admission outcomes, decoder port usage, exact supported formats, limits, immutable byte snapshot and tests without changing public schemas. Compare existing decoder availability and compatibility before recommending dependencies; installation or dependency changes require their own scope.

Use existing source/provenance contracts for accepted, completely hashed bytes. Propose a typed internal admission failure for an input rejected before acceptance/hash completion. Do not fabricate a full-source hash from a prefix, use a path hash, or mark a readable oversized file UNREADABLE merely to satisfy V1. An internal rejection must never masquerade as a public MediaValidationResultV1 success. Public serialization/migration is deferred for explicit review.

| Condition | Intended result |
|---|---|
| Byte budget exceeded | Admission rejection; choose/export a smaller file |
| Pixel/edge limit exceeded | Reject before full pixel decoding; export smaller dimensions |
| Unsupported encoding/profile | Explicit unsupported result; supported-format guidance |
| Corrupt/truncated file | Invalid source result; choose/export a valid file |
| Worker timeout/internal failure | Processing failure, not a claim that the photograph is bad |

An admission success only permits further validation; it does not grant media-quality PASS or permit an AI call.

## D2–D3 — Future bounded offline implementation and evaluation

1. Check byte limits before complete loading/hashing; enforce actual bytes read, not only stat metadata. Inspect headers with bounds, then validate pixel/edge/frame counts before full decoding.
2. Use a single controlled byte snapshot/binding for metadata inspection, decoding and full hash. Do not validate one pathname content and inspect different bytes later.
3. Preserve original bytes. No automatic resize or EXIF-derived file writing in this slice. Resizing after full decode cannot protect the earlier decode allocation.
4. Test accepted/rejected profiles, exact limits and limit+1, tiny compressed inputs with excessive dimensions, truncation, invalid metadata, changing sources and typed failures. Prove rejected inputs cannot invoke the provider using injected spies.
5. Record decoder/runtime identity, sample counts, time and process memory. Python allocation tracing alone does not account for native decoder memory. Hard time/memory isolation requires an enforceable worker mechanism and cleanup tests; measured targets alone do not establish that protection.
6. Confirm old FEAT-003 results and serialized provenance stay unchanged on relevant deterministic fixtures. New fixtures belong in a FEAT-018 manifest instance, not the existing research benchmark manifests.

## Deferred work

Optional-audio composition, framing calibration, changes to shared reason/version enums, EXIF-derived output, model connection, mobile intake, Gate A, persistent session/idempotency and transport changes remain separate scopes. Confidence/taxonomy/RawUnderstanding decisions do not block D1 specification.

Later Base64 transport work must bound encoded payload and HTTP body before decoding/parsing, then verify decoded byte limits. Neither the client nor provider server is changed in this offline slice. Snapshot binding here does not claim to close the existing inference subprocess mutation window.

## Publication and next decision

This is the selected completed design record. Working research, red-team notes and execution goals remain local-only. The next deliverable is a self-contained D1 specification with tests and an exact change-impact table, for scoped implementation approval. No model-quality, profile promotion or full FEAT-018 completion follows from this publication.
