# FEAT-018 P2-T2 image-only media-validator implementation-approval package

STATUS: HISTORICAL (SUPERSEDED DRAFT)
NOT AN IMPLEMENTATION APPROVAL
NOT A RUNTIME AUTHORIZATION
PROPOSED_NOT_ADOPTED

This proposal is retained for provenance only and is superseded by the
owner-bound D6 governance checkpoint `d87bfcd259a1cf3c63d7ce81867462c584b8afe6`
(`docs(feat018): bind D6 image-only validator`). The current D6 authority is
the exact committed image-only validator binding recorded in that checkpoint;
the `PENDING` and `PROPOSED_NOT_ADOPTED` values below are historical draft
state and must not be read as current approval or current implementation scope.

Date: 2026-09-19 scope reconciliation
Evidence ID: `EV-018-P2-T2-IMAGE-ONLY-MEDIA-VALIDATION-APPROVAL-PACKAGE-DRAFT-01`
Related scope: FEAT-018 P2-T2 live Lightning boundary, D6 media-validation source only

Expected result:

```text
SCOPE_CORRECTION = PASS
JPEG_VALIDATION_DESIGN = RECONCILED
PACKAGE_STATUS = READY_FOR_OWNER_IMPLEMENTATION_APPROVAL
OWNER_APPROVAL = PENDING
IMPLEMENTATION = NOT AUTHORIZED
D6.MEDIA_VALIDATION_SOURCE = PENDING
D6.MEDIA_VALIDATION_SOURCE_DETAIL = SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D6 fixture identity = RESOLVED_WITH_PROPOSED_VALUE
D6 overall = NOT FINALLY RESOLVED
D1 = BLOCKED
D11 = BLOCKED
Stage 4 = NOT READY
live smoke/model load/inference = NOT AUTHORIZED
LIGHTNING/MODEL/GPU/PROVIDER/NETWORK EXECUTION = NOT AUTHORIZED
```

This is a documentation-only implementation-approval package. It defines the
bounded scope and acceptance criteria for a future image-only validator. It
does not implement or test the validator, modify the live runner, resolve D6,
bind D11, open Stage 4, or authorize a model, GPU, provider, network,
subprocess, or Lightning session.

## 1. Authority and current task boundary

The package was reconciled against the repository operating rules, source
register, FEAT-018 context/decisions/plan/approval record, the D2 image
admission specification, the committed validator package, the read-only
validator dependencies, and the prior image-only package review reports.

The current task permits tracked edits only to these two feature evidence
notes:

- this implementation-approval package;
- `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_IMAGE_ONLY_MEDIA_VALIDATOR_OWNER_APPROVAL_DRAFT_20260919.md`.

The task permits one ignored report at:

`tmp/feat018-p2t2-image-only-validator-scope-reconciliation-20260919/REPORT.md`

No source, test, fixture, plan, context, decision, approval record, evidence
data, runtime file, or other worktree is in the current edit scope.

The canonical approval record remains unchanged. Owner implementation approval
must be recorded there separately before implementation begins. Until then,
`IMPLEMENTATION = NOT AUTHORIZED` remains in force.

## 2. Exact future implementation scope

The only writable implementation paths that may be approved for this
image-only validator are:

1. `backend/src/sketch2life/contracts/schemas/media_validation.py`
2. `backend/src/sketch2life/application/services/media_validation.py`
3. `backend/src/sketch2life/domain/understanding/media_quality.py`
4. `backend/tests/unit/test_media_validation.py`

This is a four-file ceiling, not a claim that every file must change. The
future change is additive and must preserve the existing audio-required
contract and validator behavior.

| Writable path | Permitted future boundary | Required preservation |
|---|---|---|
| `backend/src/sketch2life/contracts/schemas/media_validation.py` | Add one versioned, frozen, extra-forbidden image-only result and deterministic serialization support. | Preserve `MediaValidationResultV1`, `MediaFixtureManifestV1`, audio fields, and existing audio serialization/helpers. |
| `backend/src/sketch2life/application/services/media_validation.py` | Add one image-only Phase-0 application entry point and typed failure/result handling. | Do not route through `DeterministicMediaValidator`, its audio request, or an audio inspector. |
| `backend/src/sketch2life/domain/understanding/media_quality.py` | Add only additive image-only structural policy/evaluation support if required by the four-file design. | Do not alter existing audio policy, `assess_audio`, `assess_media`, or subjective/semantic image-quality behavior. |
| `backend/tests/unit/test_media_validation.py` | Add focused in-memory JPEG/PNG contract, service, serialization, failure, privacy, and output-boundary tests. | Preserve existing audio-required tests and their deterministic serialization baseline. |

No new committed fixture is approved. JPEG and PNG payloads must be generated
in memory by the approved test file. No raw image binary, child/personal
media, manifest, fixture module, or additional test file may be added.

Any required writable path outside these four files is
`BLOCKED_PENDING_SCOPE_DECISION`. Implementation must stop; it must not invent
a new path or workaround.

## 3. Read-only dependencies and regression targets

The following paths are explicitly read-only for this scope:

### Runtime and policy dependencies

- `backend/src/sketch2life/application/ports/image_decoder.py`
- `backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py`
- `backend/src/sketch2life/domain/understanding/image_admission.py`
- `backend/pyproject.toml`

### Regression targets

- `backend/src/sketch2life/application/services/image_admission.py`
- `backend/tests/unit/test_image_admission.py`

The future implementation may inject or reuse the existing
`ImageDecoderPort`, `AvImageDecoder`, and pure D2 admission policy facts. It
must not modify the D2 source, API, behavior, or regression tests, and it must
not depend on `Feat018ImageAdmission` as an application service. The D2
service remains an independent eligibility path.

The read-only decoder interface already provides metadata, bounded frame
probing, and one-frame scalar dimensions/pixel format. The read-only D2 policy
provides the supported container, codec, pixel-format, frame-count, byte,
pixel, and longest-edge limits. `backend/pyproject.toml` records the existing
optional `av==18.1.0` image-admission dependency. None of these facts authorizes
a decoder or dependency change.

If Design A cannot obtain the required facts from these committed interfaces
and policy without modifying a read-only path, the implementation result is:

```text
DESIGN_A_INSUFFICIENT
STOP
BLOCKED_PENDING_SCOPE_DECISION
```

No third decoder path, inspector path, fixture path, or runtime service may be
invented in response.

## 4. Selected JPEG/PNG design

```text
DESIGN_A = SELECTED
```

Design A is the only selected design for this approval draft:

- JPEG and PNG validation uses the existing read-only D2 decoder facts.
- The validator proves structural validity only. It does not claim subjective
  visual quality, semantic quality, drawing quality, or model suitability.
- Supported container, codec, pixel format, frame count, dimensions, pixel
  budget, and longest-edge limits come from the read-only D2 policy.
- The path is image-only. It has no audio input, audio inspector, fabricated
  audio, placeholder audio, narration field, or audio provenance.
- There is no MIME/extension requirement. The path does not compare MIME with
  a filename extension and does not use a filename or extension as acceptance
  evidence.
- D2 source, API, behavior, tests, and fixtures are not modified.

The existing multimodal `MediaQualityPolicy` and `assess_image` behavior are
not evidence of subjective quality acceptance for this path. If
`media_quality.py` is changed within the four-file ceiling, its additive
image-only support must represent the selected structural policy only and
must not inherit audio or subjective/semantic thresholds implicitly.

## 5. Phase boundary and digest semantics

Phase 0 validator behavior is exactly:

```text
source exists
-> bounded complete source read
-> computed source SHA-256 equals expected source SHA-256
-> D2 decoder structural validation
-> image-only policy PASS
-> deterministic typed result and canonical serialization
```

The source digest is the lowercase SHA-256 of the complete bytes actually
read. A byte-budget rejection receives no prefix digest. A digest mismatch is
typed failure and cannot be repaired by a filename, MIME value, extension,
manifest, constant, or stale value.

D8 / Phase 1 owns staging, staged SHA-256 recomputation, and equality with the
approved source digest after the session is provisioned and ready. The Phase 0
validator does not claim or prove staged-digest correctness. Staged-digest
fields, staged-digest equality, and staged-digest mismatch are absent from
the validator contract, PASS criteria, provenance claim, and focused tests.

The validator therefore proves only source-read/source-digest and structural
image validation. Filesystem/evidence publication and atomic commit belong to
the future D11/finalizer scope, not this Phase 0 validator.

## 6. Image-only result and serialization contract

The future concrete class, contract name/version, validator identity, policy
identity, and Git blob remain:

`UNKNOWN_UNTIL_IMPLEMENTED_REVIEWED_COMMITTED`

The owner approval binds the four-file scope and the behavior below; it does
not invent a future symbol or hash. The additive result must be frozen,
extra-forbidden, versioned, and deterministic with these fixed concepts:

| Result concept | Required rule |
|---|---|
| `status` | Closed `PASS` or `FAIL`; no `RECAPTURE` alias. |
| `failure_code` | `null` only for `PASS`; one closed typed value for `FAIL`; no raw exception or OS text. |
| `source` | Bounded opaque artifact reference, source status, digest status, and the complete validated source SHA-256 when available; never a path, URL, token, secret, or raw bytes. |
| `image_profile` | Structural container, codec, pixel format, width, height, complete byte count, and bounded frame facts only. |
| `checks` | Fixed deterministic check order for source read, source digest, D2 metadata, frame count, dimensions, pixel budget, longest edge, decode integrity, and structural policy. |
| `validator_identity` | Bounded identity recorded only after implementation/review/binding. |
| `policy_identity` | Bounded `IMAGE_ONLY` structural-policy identity recorded only after implementation/review/binding. |
| audio fields | Forbidden. Extra keys must be rejected. |

The minimum typed failures are:

```text
MISSING_SOURCE
UNREADABLE_IMAGE
UNSUPPORTED_CONTAINER
UNSUPPORTED_CODEC
UNSUPPORTED_PIXEL_FORMAT
CORRUPT_OR_TRUNCATED
INPUT_TOO_LARGE
SOURCE_DIGEST_MISMATCH
VALIDATOR_EXCEPTION
MALFORMED_RESULT
SERIALIZATION_HASH_MISMATCH
```

Canonical serialization is fixed as follows:

1. Validate the complete typed result with the exact versioned schema.
2. Serialize with Pydantic v2 `model_dump_json()`, declared field order, no
   indentation, no aliases, and `exclude_none=False`.
3. Hash the exact UTF-8 serialization bytes with lowercase SHA-256.
4. Re-validate and recompute before a success result is handed to a future
   consumer. The serialization hash is not self-referential.

No staged digest is part of this contract or its serialization. The
serialization hash is a Phase-0 deterministic result check, not proof of
filesystem/evidence publication.

## 7. Failure/output boundary

```text
NO_PARTIAL_RESULT_OR_SERIALIZATION_OUTPUT
```

On every failure:

- no `PASS` result is returned;
- no partially populated result is returned;
- no canonical serialized success payload is returned;
- no success artifact hash is returned;
- no raw path, exception, secret, token, credential, audio, or provider data
  is emitted; and
- no filesystem/evidence publication or atomic commit is attempted.

The future D11/finalizer owns filesystem/evidence publication and atomic commit.
This validator package does not claim those guarantees and does not add a
publisher, writer, route, runner branch, or carrier.

## 8. Focused offline acceptance matrix

The only focused test file is
`backend/tests/unit/test_media_validation.py`. All JPEG/PNG bytes are
deterministically generated in memory; no committed fixture is used.

| Required case | Required evidence |
|---|---|
| Valid JPEG PASS | A deterministic structurally valid JPEG passes the selected D2 structural policy without audio or subjective-quality claims. |
| Valid PNG PASS | A deterministic structurally valid PNG passes the selected D2 structural policy without audio or subjective-quality claims. |
| Repeated deterministic result | Repeated identical JPEG and PNG bytes produce byte-identical typed results, canonical serializations, and serialization hashes. |
| Source digest mismatch | Expected and computed complete source SHA-256 differ; result fails closed and returns no success output. |
| Missing/unreadable source | Typed failure, no fabricated digest, no raw OS detail, and no success output. |
| Unsupported container/codec/pixel format | Each D2 profile rejection is typed and cannot become `PASS`. |
| Corrupt/truncated/oversized input | Corrupt and truncated input fails structurally; oversized input stops at the bound without a prefix digest or decode. |
| Multiple frames | D2 bounded frame probe rejects more than the approved frame count. |
| Pixel and longest-edge limit failures | Each independent D2 dimension guard fails before structural `PASS`. |
| Decoder source/processing exception | Source exception maps to a typed corrupt/truncated outcome; processing exception maps to sanitized `VALIDATOR_EXCEPTION`. |
| Malformed typed result | Missing, extra, wrong-type, non-finite, or contradictory fields are rejected as `MALFORMED_RESULT`. |
| Canonical serialization/hash mismatch | Changed canonical bytes or recomputed hash fails as `SERIALIZATION_HASH_MISMATCH` and emits no success output. |
| No-audio-required | The request, result, serialized output, and decoder interaction contain no audio path, audio reference, audio inspector call, or audio field. |
| `NO_PARTIAL_RESULT_OR_SERIALIZATION_OUTPUT` | Every failure leaves no partially populated result, canonical serialized success payload, or success artifact hash. |
| Privacy sanitization | Output contains no absolute path, URL, secret, token, credential, raw exception, traceback, raw image, or model/provider payload. |

The staged-digest mismatch case is intentionally removed from this matrix.
Stale/duplicate provenance test names are also not part of this Phase-0
matrix because no exact fields and deterministic ownership for those future
D11 concerns are approved here. They require a separate D11 contract decision
if later needed.

## 9. Approval lifecycle and exclusions

The lifecycle is:

```text
this draft
-> owner implementation approval recorded in TASK_APPROVAL.md
-> implementation within the four-file ceiling
-> focused offline tests
-> independent review
-> exact identity/provenance binding
-> D6.MEDIA_VALIDATION_SOURCE may be reconsidered
```

The owner approval does not authorize D11, Stage 4, staging, model loading,
inference, or any live smoke. D6 remains pending until implementation,
focused tests, independent review, and exact binding are complete.

Explicit exclusions are:

- `DeterministicMediaValidator` and every audio-required path;
- `Feat018ImageAdmission` as an application-service dependency;
- modification of `image_decoder.py`, `av_image_decoder.py`,
  `image_admission.py`, `pyproject.toml`, `image_admission.py` tests, or any
  other read-only dependency/regression target;
- `image_admission_evaluation.py` and Cohort B tooling;
- Qwen, raw-understanding mapper, runner/coordinator, D11 carrier, route,
  registry, queue, database, or provider changes;
- FEAT-003, FEAT-017, P2-T4, P2-T5, mobile, Gate A, P1, P3, P4, and shared
  integration;
- MIME/extension enforcement;
- model, GPU, provider, network, subprocess, Lightning, live smoke, Stage 4,
  deployment, commit, push, or production use.

If any acceptance criterion requires a file or behavior outside this boundary,
the result is `BLOCKED_PENDING_SCOPE_DECISION`. If the read-only D2 facts are
insufficient, the result is `DESIGN_A_INSUFFICIENT`; no replacement path is
authorized.

## 10. Historical gate snapshot (superseded)

```text
HISTORICAL_DRAFT
NOT AN IMPLEMENTATION APPROVAL
NOT A RUNTIME AUTHORIZATION
PROPOSED_NOT_ADOPTED
D6.MEDIA_VALIDATION_SOURCE = PENDING
D6.MEDIA_VALIDATION_SOURCE_DETAIL = SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D6 fixture identity = RESOLVED_WITH_PROPOSED_VALUE
D6 overall = NOT FINALLY RESOLVED
D1 = BLOCKED
D11 = BLOCKED
D11.LIVE_SEAM_BINDING = BLOCKED
Stage 4 = NOT READY
live smoke/model load/inference = NOT AUTHORIZED
LIGHTNING/MODEL/GPU/PROVIDER/NETWORK EXECUTION = NOT AUTHORIZED
IMPLEMENTATION = NOT AUTHORIZED
```

This package is ready for owner implementation-approval review only. It is
not itself an approval and must not be treated as a runtime or implementation
authorization.
