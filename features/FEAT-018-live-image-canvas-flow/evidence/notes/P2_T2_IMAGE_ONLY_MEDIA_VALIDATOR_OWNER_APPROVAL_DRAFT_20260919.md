# FEAT-018 P2-T2 image-only media-validator owner implementation-approval draft

STATUS: HISTORICAL (SUPERSEDED DRAFT)
DRAFT
NOT AN IMPLEMENTATION APPROVAL
NOT A RUNTIME AUTHORIZATION
PROPOSED_NOT_ADOPTED

This proposal is retained for provenance only and is superseded by the
owner-bound D6 governance checkpoint `d87bfcd259a1cf3c63d7ce81867462c584b8afe6`
(`docs(feat018): bind D6 image-only validator`). The current D6 authority is
the exact committed image-only validator binding recorded in that checkpoint;
the `PENDING` and `PROPOSED_NOT_ADOPTED` values below are historical draft
state and must not be read as current approval or current implementation scope.

Date: 2026-09-19
Evidence ID: `EV-018-P2-T2-IMAGE-ONLY-MEDIA-VALIDATOR-OWNER-APPROVAL-DRAFT-20260919`
Related scope: FEAT-018 P2-T2 live Lightning boundary, D6 media-validation source only

Expected result:

```text
OWNER_APPROVAL_DRAFT = READY_FOR_OWNER_IMPLEMENTATION_APPROVAL
SCOPE_CORRECTION = PASS
JPEG_VALIDATION_DESIGN = RECONCILED
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

This is a proposed owner decision prepared for signing. It authorizes no
implementation until the owner records an approval in the canonical
`features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md` record.
It does not implement or test code, resolve D6, bind D11, open Stage 4, or
authorize staging, model loading, inference, GPU, provider, network,
subprocess, Lightning, or live-smoke activity.

## 1. Proposed decision

Approve only the future additive image-only Phase-0 validator described here,
within the exact four-file ceiling in Section 2, subject to the acceptance
criteria in Section 8. Preserve all existing audio-required behavior and all
read-only D2 behavior. Any required path outside that ceiling is
`BLOCKED_PENDING_SCOPE_DECISION`.

The owner approval binds a bounded implementation scope and behavior. It does
not pre-bind a future class, function, contract name/version, policy identity,
fixture identity, provenance carrier, owner, or Git hash. Those identities are
recorded only after implementation, focused tests, independent review, and a
post-review identity/provenance binding record.

## 2. Exact implementation scope

The only writable future implementation paths are:

1. `backend/src/sketch2life/contracts/schemas/media_validation.py`
2. `backend/src/sketch2life/application/services/media_validation.py`
3. `backend/src/sketch2life/domain/understanding/media_quality.py`
4. `backend/tests/unit/test_media_validation.py`

| Path | Approval boundary |
|---|---|
| `backend/src/sketch2life/contracts/schemas/media_validation.py` | Add one frozen, extra-forbidden, versioned image-only result and deterministic serialization support; preserve the existing audio-required contract and fixture contract. |
| `backend/src/sketch2life/application/services/media_validation.py` | Add one image-only Phase-0 entry point and typed failure handling; do not route through `DeterministicMediaValidator` or an audio inspector. |
| `backend/src/sketch2life/domain/understanding/media_quality.py` | Add only structural image-only policy/evaluation support if needed; preserve existing audio and subjective/semantic policy behavior. |
| `backend/tests/unit/test_media_validation.py` | Add the focused in-memory JPEG/PNG matrix, contract/serialization/privacy checks, and result-output checks; preserve existing audio tests. |

No new committed fixture, raw image binary, manifest, fixture module, or test
file is approved. JPEG/PNG bytes are generated in memory in the one approved
test file. The four paths are a ceiling; no other file may be modified under
this approval.

## 3. Read-only dependencies and regression protection

These runtime/policy paths are read-only:

- `backend/src/sketch2life/application/ports/image_decoder.py`
- `backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py`
- `backend/src/sketch2life/domain/understanding/image_admission.py`
- `backend/pyproject.toml`

These regression paths are read-only:

- `backend/src/sketch2life/application/services/image_admission.py`
- `backend/tests/unit/test_image_admission.py`

The future code may inject or reuse the existing decoder port, its PyAV
implementation, and the pure D2 policy facts. It may not modify D2 source,
API, behavior, or tests, and it may not depend on `Feat018ImageAdmission` as an
application service. If a required fact cannot be supplied by these committed
interfaces without changing a read-only path, implementation must stop with:

```text
DESIGN_A_INSUFFICIENT
BLOCKED_PENDING_SCOPE_DECISION
```

No replacement decoder, inspector, fixture, or runtime path may be invented.

## 4. Selected JPEG/PNG design

```text
DESIGN_A = SELECTED
```

The signed scope selects Design A:

- Use existing read-only D2 decoder facts for JPEG and PNG.
- Prove structural validity only. Do not claim subjective visual quality,
  semantic quality, drawing quality, or model suitability.
- Take supported container, codec, pixel format, frame count, dimensions,
  pixel budget, and longest-edge limits from the read-only D2 policy.
- Require no audio. Do not fabricate audio, accept placeholder audio, call an
  audio inspector, or serialize audio provenance.
- Enforce no MIME/extension agreement. Do not derive acceptance from a MIME
  value, filename, or extension, and do not add a MIME/extension enforcer.
- Do not modify D2 source, API, behavior, tests, fixtures, or dependency
  metadata.

The existing multimodal image-quality thresholds are not the Phase-0 PASS
criterion. Any additive `media_quality.py` support must be structural and
image-only; audio and subjective/semantic values may not be inherited
implicitly.

## 5. Phase 0 and digest ownership

The validator must implement this sequence:

```text
source exists
-> bounded complete source read
-> computed source SHA-256 equals expected source SHA-256
-> D2 decoder structural validation
-> image-only policy PASS
-> deterministic typed result and canonical serialization
```

The source digest is computed over the complete bytes actually read. A source
digest mismatch fails closed. Missing, unreadable, and oversized sources do
not receive fabricated or prefix digests. A source digest is never inferred
from a path, MIME value, extension, manifest, constant, or stale carrier.

D8 / Phase 1 owns staging, staged SHA-256 recomputation, and equality with the
approved source digest after the session is provisioned and ready. The Phase 0
validator must not claim or prove staged-digest correctness. The validator
contract, PASS criteria, provenance claim, and focused tests contain no staged
digest field or staged-digest mismatch case.

## 6. Result, provenance, and canonical serialization

Future concrete symbols and exact identities remain
`UNKNOWN_UNTIL_IMPLEMENTED_REVIEWED_COMMITTED` until implementation, focused
tests, independent review, and binding. The additive result must be frozen,
extra-forbidden, versioned, and deterministic.

Required result concepts:

- closed `status`: `PASS` or `FAIL`;
- one typed `failure_code` for `FAIL`, and `null` for `PASS`;
- bounded opaque source reference, source status, digest status, and complete
  source SHA-256 when available;
- structural image profile: container, codec, pixel format, dimensions,
  complete byte count, and bounded frame facts;
- fixed ordered checks for source read, source digest, D2 metadata, frame
  count, dimensions, pixel budget, longest edge, decode integrity, and
  structural policy;
- bounded validator identity and `IMAGE_ONLY` structural-policy identity,
  bound only after review; and
- no audio fields, raw bytes, raw path, URL, exception, traceback, secret,
  token, credential, prompt, provider payload, or model output.

Minimum typed failures:

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

Canonical serialization is Pydantic v2 `model_dump_json()` using declared
field order, no indentation, no aliases, and `exclude_none=False`; the exact
UTF-8 bytes are hashed with lowercase SHA-256. The serialization hash is not
self-referential. A changed result, serialization, or recomputed hash fails
closed before a future consumer hand-off.

## 7. Failure/output invariant

```text
NO_PARTIAL_RESULT_OR_SERIALIZATION_OUTPUT
```

Every failure must produce:

- no `PASS` result;
- no partially populated result;
- no canonical serialized success payload;
- no success artifact hash; and
- no leaked path, exception, secret, token, credential, audio, provider, or
  model data.

Filesystem/evidence publication and atomic commit belong to the future
D11/finalizer scope. They are not claimed, implemented, or tested by this
Phase-0 validator approval.

## 8. Focused test matrix

All tests are offline and use deterministic in-memory JPEG/PNG generators in
`backend/tests/unit/test_media_validation.py`.

| Case | Acceptance requirement |
|---|---|
| Valid JPEG PASS | Structurally valid JPEG passes under Design A without audio or subjective-quality claims. |
| Valid PNG PASS | Structurally valid PNG passes under Design A without audio or subjective-quality claims. |
| Repeated byte-identical result/serialization/hash | Repeating identical JPEG and PNG bytes yields byte-identical typed results, canonical JSON, and serialization SHA-256 values. |
| Source digest mismatch | The expected and complete computed source digests differ; failure is typed and emits no success output. |
| Missing/unreadable source | Failure is typed, sanitized, digest-free where unavailable, and output-free. |
| Unsupported container/codec/pixel format | Each unsupported D2 fact fails closed before `PASS`. |
| Corrupt/truncated/oversized input | Corrupt and truncated input fails structurally; oversized input stops at the bound without a prefix digest or decode. |
| Multiple frames | More than the D2 frame limit fails closed. |
| Pixel and longest-edge limit failures | Each D2 dimension guard is tested independently. |
| Decoder source/processing exception | Source exception maps to a structural corrupt/truncated failure; processing exception maps to sanitized `VALIDATOR_EXCEPTION`. |
| Malformed typed result | Extra, missing, wrong-type, non-finite, and contradictory fields fail as `MALFORMED_RESULT`. |
| Canonical serialization/hash mismatch | Recomputed bytes/hash disagreement fails as `SERIALIZATION_HASH_MISMATCH` and emits no success output. |
| No-audio-required | No audio argument, path, reference, inspector call, or serialized audio field exists. |
| `NO_PARTIAL_RESULT_OR_SERIALIZATION_OUTPUT` | Every failure has no partial result, serialized success payload, or success artifact hash. |
| Privacy sanitization | No path, URL, exception detail, traceback, secret, token, credential, raw image, or provider/model payload leaks. |

Staged-digest mismatch is deliberately removed from the focused matrix. Stale
and duplicate provenance cases are deferred because no exact Phase-0 fields or
deterministic ownership for those future D11 concerns are approved here; they
would require a separate D11 contract decision.

## 9. Acceptance criteria and exclusions

Owner implementation approval is signable only if it accepts all of the
following:

1. The future implementation changes only the four files in Section 2.
2. Design A is used, or implementation stops with `DESIGN_A_INSUFFICIENT`.
3. JPEG and PNG PASS means structural D2 validity only; no subjective or
   semantic visual-quality claim is introduced.
4. The existing D2 decoder port/implementation and policy remain read-only,
   and `Feat018ImageAdmission` is not an application-service dependency.
5. The Phase-0 source digest is complete-source SHA-256 equality only; D8 /
   Phase 1 owns staging and staged-digest recomputation after provision/ready.
6. The result is typed, extra-forbidden, deterministic, sanitized, image-only,
   and has no staged digest field or audio fields.
7. `NO_PARTIAL_RESULT_OR_SERIALIZATION_OUTPUT` is enforced in every failure
   path; future filesystem/evidence publication and atomic commit remain D11 /
   finalizer work.
8. The full Section 8 matrix is implemented and reviewed without adding a
   committed fixture.
9. MIME/extension enforcement, Qwen, mapper, runner, D11, Stage 4, live
   smoke, model, GPU, provider, network, and Lightning behavior remain out of
   scope.

Any failure to satisfy these criteria leaves the implementation blocked and
does not change D6, D11, or Stage 4.

## 10. Historical owner sign-off block — superseded and intentionally blank

This draft is not signed and does not alter `TASK_APPROVAL.md`.

```text
OWNER DECISION: [ ] APPROVE THE EXACT FOUR-FILE IMPLEMENTATION SCOPE
                [ ] NEEDS REVISION / DO NOT APPROVE
APPROVER:       ______________________________________
DATE:           ______________________________________
SIGNATURE:      ______________________________________
TASK_APPROVAL ADDENDUM RECORDED: [ ] YES  [ ] NO
```

Until the owner completes the decision in the canonical approval record:

```text
OWNER_APPROVAL = PENDING
IMPLEMENTATION = NOT AUTHORIZED
```

## 11. Historical preserved gate state (superseded)

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

The only next action authorized by this draft is owner review and, if the
owner agrees, a separately recorded implementation approval. No implementation
or runtime action is authorized by the draft itself.
