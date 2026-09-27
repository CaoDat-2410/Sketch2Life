# FEAT-018 P2-T2 D6 media-validation binding package draft and owner-bound state

Date: 2026-09-20
Task mode: plan/evidence package correction only. The historical pre-owner
preparation state is retained and the current owner-bound state is recorded
below. This correction does not modify implementation, D2 files, approvals,
plans, governance state, worktrees, or stashes. It does not authorize Stage 4
or any runtime execution.

```text
D6_BINDING_PACKAGE = OWNER_APPROVED
D6_BINDING_PACKAGE_STATUS_BEFORE_OWNER_DECISION = RESOLVED_PENDING_OWNER_BINDING
D6_BINDING_PACKAGE_STATUS = OWNER_BOUND_AND_RESOLVED
D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION
D4_RUNTIME_REVALIDATION = STAGE_4_LOCAL_ONLY
D11 = BLOCKED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
```

## 1. Package purpose and gate meaning

This package binds the owner-approved `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE`
value to the exact committed offline image-only validator identity. It assembles
the implementation, contract, provenance, review, and lifecycle facts needed
for the independent D6 binding-review rerun.

The package was initially prepared before the owner decision. That preparation
state is retained only as explicitly labeled historical provenance:

```text
HISTORICAL_PRE_OWNER_DECISION
HISTORICAL_D6_BINDING_PACKAGE_STATUS = RESOLVED_PENDING_OWNER_BINDING
HISTORICAL_D6.MEDIA_VALIDATION_SOURCE = SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW
HISTORICAL_D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
HISTORICAL_D6 = NOT FINALLY RESOLVED
```

After the owner addendum, the current package and governance state is:

```text
D6_BINDING_PACKAGE_STATUS = OWNER_BOUND_AND_RESOLVED
D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR
P2T2-LIVE-D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
```

The independent D6 binding review and owner addendum have already occurred.
This correction mirrors that existing owner decision and prepares the package
for an independent review rerun; it does not create a new approval or modify
the current `TASK_APPROVAL.md` state.

## 2. Exact committed identity

The owner-bound D6 implementation is bound to the local commit below, not to the
current working-tree documentation state or to an uncommitted candidate:

| Identity | Value |
| --- | --- |
| Commit | `16c52da26c444947ab4388712d9b7310480360b4` |
| Commit subject | `feat(feat018): add offline image-only validator` |
| Commit tree | `581687bea88ecbc172c25160e1e11012e51d83fa` |
| Validator identity | `feat018-image-only-structural-validator-v1` |
| Result contract | `ImageOnlyValidationResultV1@1.0` |
| Policy identity | `feat018-image-only-structural-policy-v1` |

The exact committed writable paths and blobs are:

| Path | Role | Commit blob |
| --- | --- | --- |
| `backend/src/sketch2life/contracts/schemas/media_validation.py` | result, verification, provenance, and serialization contract | `e5681c2f260329513788d117d0425c043fe215a2` |
| `backend/src/sketch2life/application/services/media_validation.py` | offline image-only validator service | `6b0e8de7b34500cc4bbfd7c01ed9235388c021b9` |
| `backend/src/sketch2life/domain/understanding/media_quality.py` | image-only structural policy bridge | `b8d89efebc6ae8a82b3821e3d833627ef4fd2439` |
| `backend/tests/unit/test_media_validation.py` | deterministic contract and validator tests | `cd4a170105b59ba40c1416135e13f4adaa97b886` |

The separately committed Route A hygiene correction is part of the reviewed
checkpoint support, not part of the four-file validator identity:

| Path | Role | Commit blob |
| --- | --- | --- |
| `tools/validate_repository_security.py` | exact-path, exact-category, exact-marker synthetic-fixture exemption | `56f54fd67c58f3c08518a730bd3b7cf5ba275029` |

The commit contains exactly these five paths. No D2 source, admission service,
Qwen, runner, mapper, coordinator, workflow, plan, approval, context, decision,
draft, or unrelated path is part of this identity.

## 3. Read-only D2 dependency identity

The validator reuses D2 structural facts through read-only boundaries. These
paths were not changed by the checkpoint:

| Path | Read-only role | Observed blob |
| --- | --- | --- |
| `backend/src/sketch2life/application/ports/image_decoder.py` | decoder port consumed by `ImageOnlyStructuralMediaValidator` | `48dd8e4da64f5f95c0f35c89dc9dd985447adcae` |
| `backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py` | PyAV decoder adapter | `a070b44ca4323605e2bbbe206812c1ab8b102928` |
| `backend/src/sketch2life/domain/understanding/image_admission.py` | pure D2 admission limits/reasons and structural facts | `cfe3253655faea33a7cff02249f163d0b8b332ab` |

The D6 validator does not depend on `Feat018ImageAdmission` as an application
service and does not alter D2 behavior, APIs, tests, or dependency metadata.

## 4. Contract and provenance binding

`ImageOnlyValidationResultV1@1.0` is frozen and extra-forbidden. It carries the
source artifact reference, source availability, digest status, source SHA-256
when available, bounded byte count, structural profile on success, the complete
canonical check sequence, validator identity, and policy identity. It has no
audio field and no staged digest field.

Canonical result bytes are exactly:

```text
result.model_dump_json(by_alias=False, exclude_none=False, indent=None)
  -> UTF-8 bytes
  -> lowercase SHA-256
```

The serialization hash is outside the serialized result. Verification first
checks the supplied payload hash, reparses the payload, and requires the
canonical reserialization to be byte-identical to the submitted payload.
Malformed payloads and non-canonical payloads fail with typed verification
outcomes; caller-controlled parser diagnostics are sanitized.

The closed image-only failure vocabulary is:

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

The service entry point is:

```text
ImageOnlyValidationRequest(image_path, image_artifact_ref, expected_source_sha256)
ImageOnlyStructuralMediaValidator(decoder, policy).validate(request)
```

The validator reads one bounded complete source snapshot, hashes those bytes,
rejects a source-digest mismatch before decoding, delegates structural decode
facts through `ImageDecoderPort`, applies the image-only D2 structural policy,
and emits a typed result. It does not invent an audio input or a runtime field.

## 5. Fixture-reference semantics

The committed positive allowlist is the following ASCII pattern:

```text
fixture-b[0-9]{2}
fixture:drawing:v[0-9]+
fixture:small-dark-drawing:v[0-9]+
fixture:corrupt-drawing:v[0-9]+
fixture:rejected-reference:v1
```

Therefore `fixture-b00` through `fixture-b99` match. The implementation is not
limited to B01 through B08. The owner-reviewed Cohort B candidate set is B01 to
B08, but that is a separate source-review set and must not be silently
described as the validator's entire allowlist.

```text
ALLOWLIST_SCOPE = COMMITTED_PATTERN_ABOVE
OWNER_DECISION_IF_B01_B08_ONLY_IS_REQUIRED = UNRESOLVED
```

If the live D6 decision requires B01-B08 only, that is a separate owner
decision requiring an explicit contract/implementation change and new review;
this package does not narrow or rewrite the committed validator.

The fixed `fixture:rejected-reference:v1` value is a sanitized failure sentinel,
not a source that is accepted as a valid image. Sensitive-looking references,
malformed references, parser mappings, and direct mappings remain negative
privacy-test inputs with their assertions intact.

## 6. Route A hygiene binding

The Route A correction is exactly the committed change identified above. Its
security exemption is fail-closed and machine-checkable:

```text
SECURITY_VALIDATOR_SYNTHETIC_FIXTURES: BEGIN
SECURITY_VALIDATOR_SYNTHETIC_FIXTURES: END
```

The exemption applies only when all three conditions hold:

1. relative path is exactly `backend/tests/unit/test_media_validation.py`;
2. the detected category is exactly `private key material` or exactly
   `non-placeholder secret assignment`; and
3. the finding is fully contained in exactly one explicitly marked synthetic
   fixture block.

Wrong path, wrong category, an unmarked finding, duplicate blocks, path-wide
suppression, broad regex suppression, repository-wide suppression, runtime or
configuration exemption, and `.env` or credential exemptions remain rejected.
The synthetic fixtures were not concatenated, encoded, obfuscated, renamed to
hide their meaning, or weakened merely to bypass scanning. The negative privacy
coverage remains intentional test data. No real credential, token, password,
private key, endpoint, provider secret, or child data is present.

The typed `ConfigDict` correction preserves `hide_input_in_errors=True` without
an untyped configuration mutation or blanket type-ignore. It changes typing
representation only; it does not change the result contract or privacy rules.

## 7. CI evidence scope correction

The owner-supplied CI evidence is recorded with its exact identity:

| Field | Value |
| --- | --- |
| Run ID | `35500484772` |
| Workflow | `feat018-posix` |
| Head SHA | `16c52da26c444947ab4388712d9b7310480360b4` |
| Conclusion | `success` |

The only supported CI claim is:

> CI run 35500484772 proves the FEAT-018 POSIX process-group cleanup workflow
> passed for commit 16c52da.

That run does not prove the complete image-only validator suite, strict mypy,
the repository security validator, the full backend suite, or all repository
validation. Those claims are bound separately to the Route A correction report,
Route A independent review, post-commit independent review, and owner
checkpoint report listed in Section 11.

## 8. D4 lifecycle correction

The pre-Stage-4 D4 state is the approved snapshot selection/readiness/identity,
not a session-local runtime fact:

```text
D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION
```

The package does not require session-local runtime revalidation before Stage 4
approval. That check depends on the approved execution checkout and the
provisioned session, so requiring it earlier would be circular.

The lifecycle boundary is:

```text
Stage-4 approval
  -> verify approval checkout
  -> provision session
  -> SESSION_READY
  -> D4 runtime/session-local revalidation
  -> D8 staging and staged-digest verification
  -> exactly one smoke
  -> cleanup
  -> evidence finalization
```

This package records D4 as ready for that later runtime revalidation only. It
does not authorize model loading, GPU use, provider access, network access,
Lightning, or Stage 4.

## 9. D6 responsibility boundary

### Phase 0 image-only validator owns

- source existence and bounded source read;
- source SHA-256 computation and expected-source digest comparison;
- decoder structural validation through the D2 port;
- D2 metadata, frame-count, pixel-budget, longest-edge, decode-integrity, and
  structural-policy checks;
- stable typed failure mapping;
- the typed `ImageOnlyValidationResultV1` serialization and its canonical hash
  verification helpers.

### D8/session controller owns

- staging the selected source after `SESSION_READY`;
- recomputing the staged file SHA-256;
- comparing source and staged digests at the staging boundary; and
- recording the runtime/session-local staging facts.

The validator does not claim `staged_sha256`, does not enforce MIME/extension
agreement, and does not publish evidence. `D6.MIME_EXTENSION_RULE` is already
`RESOLVED: REMOVE_REQUIREMENT`; MIME and extension remain owner-reviewed
metadata only.

The validator also does not select or use `DeterministicMediaValidator`, which
is the existing audio-bearing validator. It does not implement audio, D11,
the approved host caller, Stage 4, evidence finalization, or live execution.

## 10. Governance state preserved

This package records the current governance state already established by the
owner addendum; it does not create a new approval or claim that D6 overall,
D11, or Stage 4 is fully resolved:

| Item | Current state |
| --- | --- |
| D1 | `BLOCKED` |
| D4 | owner-approved readiness identity; runtime/session-local revalidation remains Stage-4-local |
| D6 package status | `OWNER_BOUND_AND_RESOLVED` |
| D6 fixture identity | `RESOLVED_WITH_PROPOSED_VALUE` |
| D6 media source | `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR` |
| D6 MIME rule | `RESOLVED: REMOVE_REQUIREMENT` |
| D11 | `BLOCKED` |
| Stage 4 | `NOT READY` |
| Lightning/model/GPU/provider/network | `NOT AUTHORIZED` |

The original implementation approval marker and Route A addendum counts in
`features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md` are:

| Marker or record | Count |
| --- | ---: |
| `APPROVED_FOR_EXACT_FOUR_FILE_OFFLINE_IMAGE_ONLY_VALIDATOR_IMPLEMENTATION_ONLY` | 1 |
| `HYGIENE_ROUTE = A_NARROW_SECURITY_VALIDATOR_EXEMPTION` | 1 |
| `Separate security-fixture hygiene addendum - 2026-09-20` | 1 |
| `Route A is approved separately.` | 1 |

No approval marker is added by this package correction.

## 11. Validation and review evidence

The following are recorded offline results from the committed checkpoint and
Route A correction chain. They are evidence references, not new workload runs
for this package:

| Check | Result | Evidence |
| --- | --- | --- |
| Final artifact review | `PASS` | `tmp/feat018-p2t2-image-only-validator-final-independent-review-20260919/REVIEW.md` |
| Post-apply Ruff correction | Ruff/focused/D2 gates recorded `PASS`; findings were explicitly classified | `tmp/feat018-p2t2-image-only-validator-post-apply-ruff-correction-20260920/REPORT.md` |
| Post-apply independent review | `PASS_WITH_FINDINGS`; no new scope/privacy/runtime regression | `tmp/feat018-p2t2-image-only-validator-post-apply-independent-review-20260920/REVIEW.md` |
| Route A correction | security, strict mypy, Ruff, focused, D2, harness, skeleton `PASS` | `tmp/feat018-p2t2-route-a-hygiene-correction-20260920/REPORT.md` |
| Route A independent review | `VERDICT = PASS`, `ROUTE_A_HYGIENE_REVIEW = PASS` | `tmp/feat018-p2t2-route-a-hygiene-independent-review-20260920/REVIEW.md` |
| Owner checkpoint commit | exact five-path commit, required gates `PASS` | `tmp/feat018-p2t2-offline-validator-owner-checkpoint-20260920/REPORT.md` |
| Post-commit independent review | `POST_COMMIT_REVIEW = PASS` for `16c52da` | `tmp/feat018-p2t2-offline-validator-post-commit-independent-review-20260920/REVIEW.md` |

Recorded validation results:

- strict mypy on the three changed validator source modules: `PASS`;
- strict mypy on `tools/validate_repository_security.py`: `PASS`;
- Ruff on all five committed Python files: `PASS`;
- `python -B tools/validate_repository_security.py`: `PASS`,
  `REPOSITORY_SECURITY_VALID`, `publishable_files_scanned=1026`;
- focused `tests/unit/test_media_validation.py`: `PASS`, 497 tests recorded;
- D2 `tests/unit/test_image_admission.py` and
  `tests/unit/test_image_admission_evaluation.py`: `PASS`, 155 tests recorded;
- `python -B tools/validate_harness.py`: `PASS`, `HARNESS_VALID`;
- `python -B tools/validate_skeleton.py`: `PASS`, `SKELETON_VALID`;
- `git diff --check` and committed-diff checks: `PASS`.

The architecture result is not a new pass claim. It is classified separately as
the only unchanged pre-existing finding:

```text
backend/src/sketch2life/application/services/backend_ai_workflow.py
```

The three known semantic-catalog failures are also separate baselines. They
are caused by the missing file
`backend/data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json` and
are exactly:

```text
test_v2_catalog_preserves_100_unique_curated_activity_profiles
test_concept_matching_restores_nature_and_sun_routes
test_unrelated_activity_uses_explicit_age_baseline_fallback
```

No new failure is hidden behind either baseline.

## 12. Next independent review questions

The separate D6 binding reviewer should verify, against commit
`16c52da26c444947ab4388712d9b7310480360b4` and the five blobs above:

1. the result contract, canonical serialization, hash rule, and closed failure
   vocabulary are exactly as recorded;
2. the owner-bound validator identity is the committed four-file image-only
   implementation and not the audio-bearing deterministic validator;
3. the Route A correction remains exact-path, exact-category, exact-marker,
   fail-closed, and privacy-preserving;
4. the allowlist is understood as the committed pattern, not silently reduced
   to B01-B08;
5. the Phase 0 versus D8 responsibility boundary is preserved;
6. the D4 pre-Stage-4 and session-local lifecycle wording is non-circular;
7. the CI run is used only for the POSIX process-group cleanup claim; and
8. current owner-bound D6, D11, Stage 4, and live non-authorization states remain
   unchanged.

```text
HISTORICAL_PRE_OWNER_DECISION:
HISTORICAL_INDEPENDENT_D6_BINDING_REVIEW = PENDING
HISTORICAL_OWNER_BINDING = PENDING
HISTORICAL_D6_FINAL_RESOLUTION = NOT CLAIMED

CURRENT_AFTER_OWNER_ADDENDUM:
D6_BINDING_PACKAGE_STATUS = OWNER_BOUND_AND_RESOLVED
D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
OWNER_BINDING = RECORDED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
```

No implementation, approval, runtime, model, GPU, provider, network, or
Lightning action occurred while preparing this package.
