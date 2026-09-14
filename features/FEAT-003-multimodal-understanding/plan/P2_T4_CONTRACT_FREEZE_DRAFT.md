# P2-T4 contract-freeze draft

- Status: **DRAFT - READY FOR OWNER FREEZE DECISION**
- Revision: 8
- Draft date: 2026-09-14
- Owner: Person 2
- Feature: FEAT-003 Multimodal understanding
- Final task status: **DRAFT - READY FOR OWNER FREEZE DECISION**

This is a documentation-only, reviewable proposal. It is not a contract freeze, an
implementation approval, a runtime authorization, a migration decision, a registry
decision, or an Integration Sprint allocation. No schema, service, test, fixture, or
runtime file is created or changed by this document.

## 1. Authority, source precedence, and non-adoption

The current remediation task and its exact seven-file direction are authoritative for
this reissue. Within this proposal, precedence is:

1. the current task's explicit requirements and owner-selected semantics;
2. ADR-0006 and the repository `AGENTS.md` boundary;
3. the validated P2-T2/P2-T3 source schemas in `asr.py` and `vision.py`;
4. the dated P2-T4 owner decisions and this synchronized remediation record;
5. the committed B0 reconciliation report, source register, and review records;
6. older draft wording, which is historical wherever it conflicts with this reissue.

The active proposed output identity is exactly
`P2T4.P2T4FusedResultV1@1.0`, serialized as
`P2T4FusedResultV1 / 1.0`. The former P2-T4 `RawUnderstandingResultV1` wording is
historical baseline language only. It is not the active P2-T4 output identity and does
not adopt the FEAT-018 `RawUnderstandingResultV1` contract.

The B0 mapping family `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` remains
`PROPOSED_NOT_ADOPTED`. This draft does not adopt it, implement it, add a mapping
module, add a preservation envelope, or define an edge-3 consumer contract.

### 1.1 Post-sync FEAT-018 implementation fact and incompatibility boundary

The review base for this reissue is `d706d88a70c6a9136e397bea10d29f96bafd190b`. The merged
tree contains the current FEAT-018 P2-T2 implementation, including the FEAT-018-owned,
frozen/implemented live-development handoff `RawUnderstandingResultV1 / 1.0` and its schema,
port, mapper, and focused contract/unit tests. FEAT-018's bounded offline closure was approved
at `11468d3a5a327697a491f09251a3210987337da0`. That is current implementation state, not the
historical Raw proposal described by the immutable B0 snapshot.

The boundary is intentionally not an alias or replacement:

| Concern | Proposed P2-T4 direction | Current FEAT-018 implementation |
|---|---|---|
| Vision input | Consumes P2 `VisionUnderstandingResultV1@1.0` from `vision.py` | The Raw mapper consumes FEAT-003 `VisionUnderstandingResultV2@2.0` from `vision_v2.py`; optional ASR is P2 `AsrResultV1` |
| Output identity/status | `P2T4FusedResultV1@1.0`, with `FUSED | UPSTREAM_FAILURE` and a separate safe rejection type | `RawUnderstandingResultV1@1.0`, with discriminated `SUCCEEDED | FAILED` Raw branches |
| Envelope/provenance | Correlation, P2 ASR/Vision source-result refs/digests, and fusion-policy hash; future Gate A proposal | Required `session_id`, `source_image_ref`, `gate_a_required=true`, and `RawProvenanceV1` identifying V2/profile/catalog/model provenance |
| Ambiguity and fused claims | Ambiguous regions omitted from fused observations; no `fused_claims` array | Ambiguous observations are preserved; `fused_claims` carries source refs and confidence |
| Conflicts and confidence | `P2T4ConflictV1` uses reason code, Vision observation ref, narration claim ref, and reviewer attention; P2-T4 certainty rows use `MEASURED`, `NOT_MEASURED`, or `NOT_APPLICABLE_CONFLICTING` | `RawConflictV1` uses conflict ID, claim refs, and `RawConflictCode`; Raw candidates require Vision confidence while ASR claims may be nullable and uncertainty has its own status/value invariant |
| Failure shape | Top-level `UPSTREAM_FAILURE` with typed ASR/Vision/BOTH failure references, or a separate input rejection | Typed `RawFailureV1` with `RawFailureCode` in the `FAILED` branch; provenance is optional on failure and status semantics differ |

These differences are semantic and structural. Direct aliasing, replacement, or silent field
projection is rejected. The immutable B0 report, manifest, and review records predate the
implemented FEAT-018 Raw module and remain an old snapshot; they are not edited or silently
upgraded here. Their mapping remains `PROPOSED_NOT_ADOPTED`, and a separately approved
integration reconciliation is required before adoption, registry change, consumer update, or
edge-3 handoff.

Two independent post-sync final audits passed, so the status is exactly
`DRAFT - READY FOR OWNER FREEZE DECISION`. This restores owner review only; it is not a
contract freeze or implementation approval. The future T4 freeze/implementation source commit is
`UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`; it is distinct from `review_base_commit` and the
existing FEAT-018 closure commit, and no future or self-referential digest is asserted.

The inherited owner decisions are B0 Option 3, B5 removal of `NOT_FUSIBLE`, B1
support-only narration, B4 vision-only themes, B6's exact cue/window rule, B2
primary-only weighting, B3a's one-time `0.10` cap, B3b `AGREEMENT_WEIGHTED_V1`, and
B3c `NOT_MEASURED` null confidence. The current remediation additionally records the
owner-selected output identity, per-segment matching boundary, canonical coordinate
and reference rules, decimal-string policy representation, ambiguous-region handling,
and mixed-positive/refuting handling below.

## 2. Proposed contract identities

The word "accepted" below means accepted as the proposed input boundary for owner
review. It does not mean frozen or approved.

| Role | Exact review identity | Serialized identity | Accepted validated branch |
|---|---|---|---|
| ASR input | `P2.AsrResultV1@1.0` | `contract_name="AsrResultV1"`, `contract_version="1.0"` | `AsrSuccessV1` or `AsrFailureV1` from `contracts/schemas/asr.py` |
| Vision input | `P2.VisionUnderstandingResultV1@1.0` | `contract_name="VisionUnderstandingResultV1"`, `contract_version="1.0"` | `VisionUnderstandingSuccessV1` or `VisionUnderstandingFailureV1` from `contracts/schemas/vision.py` |
| Fusion output | `P2T4.P2T4FusedResultV1@1.0` | `contract_name="P2T4FusedResultV1"`, `contract_version="1.0"` | `P2T4FusedResultV1`, with only `FUSED` or `UPSTREAM_FAILURE` |
| Safe input rejection | `P2T4.P2T4FusionInputRejectionV1@1.0` | `contract_name="P2T4FusionInputRejectionV1"`, `contract_version="1.0"` | `P2T4FusionInputRejectionV1`, outside the fused-result union |

The pure fusion service accepts only the two exact, already validated P2 result unions
above. It rejects the FEAT-018 flat result family, whose exact live identities are
`FEAT018.LiveAsrResultV1@1.0` and `FEAT018.LiveVisionUnderstandingResultV1@1.0`;
the P2 V2 Vision family `P2.VisionUnderstandingResultV2@2.0`; requests, catalogs,
provider payloads, arbitrary mappings, dataclasses, and untyped objects. A same-name
serialized field is not sufficient evidence of family identity.

## 3. Pre-validation boundary and terminal precedence

An outer boundary may receive `object` values only to classify them into the safe typed
rejection below. It may inspect only the closed identity, version, and discriminator
values needed for classification and must never copy the unknown object into a result.
A validation failure is reduced to a closed `code` and `field_code`; no Pydantic
`ValidationError`, exception text, field path, or input value escapes.

The pure fusion boundary is narrower:

```text
fuse(
    asr: AsrSuccessV1 | AsrFailureV1,
    vision: VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1,
    policy: P2T4FusionPolicyConfigV1,
    executed_at: timezone-aware datetime,
) -> P2T4FusedResultV1
```

It has no `object` or provider-shaped overload. Policy construction and both upstream
models must already be strict, validated, immutable Pydantic values before this
function is entered.

Terminal precedence is exactly:

```text
identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion
```

For each arrow, the ASR slot is inspected before the Vision slot. The first rejection
is terminal. An earlier rejection cannot be masked by a valid second input, a later
status, or a successful fusion path. A wrong-family ASR plus a failed Vision returns
the ASR identity rejection; a malformed Vision plus a failed ASR returns the Vision
strict-validation rejection after the valid ASR check; and a correlation mismatch is
reported before either failure status is converted to `UPSTREAM_FAILURE`.

1. **Identity/version:** require the exact family, name, and version in section 2.
2. **Strict upstream-contract validation:** require the exact P2 model, exact `SUCCEEDED`/`FAILED`
   discriminator branch, `extra="forbid"`, frozen nested models, finite bounded
   numeric values, complete discriminated fields, cross-field invariants, and
   timezone-aware datetimes.
3. **P2-T4 admissibility invariants:** after strict upstream validation, require every
   T4-only invariant. The exact ASR invariant is `For AsrSuccessV1, all
   AsrSegmentV1.index values MUST be unique.` Vision observation-ID uniqueness is already
   enforced by the upstream V1
   schema and is not redundantly reimplemented by T4.
4. **Correlation equality:** require `asr.correlation_id == vision.correlation_id`.
5. **Typed upstream status:** both successes use the fusion path; one or both typed failures
   use the typed upstream-failure path.
6. **Fusion:** only success/success performs matching, conflict detection, primary
   selection, uncertainty calculation, and deterministic serialization metadata.

The first failing stage is terminal. Where slot ordering applies, ASR is checked before
Vision. Strict upstream-contract validation is distinct from the T4 admissibility stage:
the current upstream `AsrSuccessV1` schema permits duplicate segment indexes, so a
strictly valid duplicate-index result is rejected only at the T4 admissibility stage.

## 4. Safe typed input rejection

`P2T4FusionInputRejectionV1` is a separate terminal result and is never represented as
an additional `P2T4FusedResultV1.status`. It is strict, frozen, has no arbitrary map,
and contains exactly these fields:

| Field | Type and requiredness | Allowlist/invariant |
|---|---|---|
| `contract_name` | required string | literal `P2T4FusionInputRejectionV1` |
| `contract_version` | required string | literal string `1.0` |
| `status` | required string | literal `REJECTED` |
| `input_slot` | required string | `ASR`, `VISION`, or `BOTH`; `BOTH` only for correlation equality |
| `phase` | required string | `IDENTITY_VERSION`, `STRICT_VALIDATION`, `ADMISSIBILITY`, or `CORRELATION` |
| `code` | required string | `UNKNOWN_INPUT`, `WRONG_FAMILY`, `UNSUPPORTED_VERSION`, `INVALID_DISCRIMINATOR`, `INVALID_STRUCTURE`, or `CORRELATION_MISMATCH` |
| `expected_identity` | required string | `NONE`, `P2.AsrResultV1@1.0`, or `P2.VisionUnderstandingResultV1@1.0`; `NONE` only for an unknown slot or correlation mismatch |
| `observed_identity` | required string | `UNKNOWN`, `P2.AsrResultV1@1.0`, `P2.VisionUnderstandingResultV1@1.0`, `FEAT018.LiveAsrResultV1@1.0`, `FEAT018.LiveVisionUnderstandingResultV1@1.0`, or `P2.VisionUnderstandingResultV2@2.0` |
| `observed_status` | required nullable string | `SUCCEEDED`, `FAILED`, `UNKNOWN`, or `null`; never an arbitrary status |
| `field_code` | required string | `NONE`, `CONTRACT_NAME`, `CONTRACT_VERSION`, `STATUS`, `CORRELATION_ID`, `SOURCE_REFERENCE`, `FAILURE_BRANCH`, `UPSTREAM_TYPE`, or `DUPLICATE_SEGMENT_INDEX` |

`observed_identity=UNKNOWN` is used for every unallowlisted identity or object;
arbitrary identity text is not echoed. All fields are required except that
`observed_status` may be null. `input_slot=BOTH` requires
`phase=CORRELATION`, `code=CORRELATION_MISMATCH`, `expected_identity=NONE`, and
`field_code=CORRELATION_ID`.

The duplicate-segment-index admissibility rejection is exactly:

```text
contract_name=P2T4FusionInputRejectionV1
contract_version=1.0
status=REJECTED
input_slot=ASR
phase=ADMISSIBILITY
code=INVALID_STRUCTURE
expected_identity=P2.AsrResultV1@1.0
observed_identity=P2.AsrResultV1@1.0
observed_status=SUCCEEDED
field_code=DUPLICATE_SEGMENT_INDEX
```

It is emitted only after strict validation has produced an `AsrSuccessV1` and before
correlation equality or typed upstream-status handling. The duplicate numeric index,
transcript, input object, exception, validation path, and any other raw detail are never
exposed. No later-stage rejection or fused result may mask this first failure.

The following are forbidden at every rejection depth: raw input objects or their JSON,
`ValidationError` instances, exception messages, stack traces, field paths, transcript
text, candidate labels or predicates, media or artifact paths, provider payloads,
prompts, credentials, endpoints, arbitrary metadata, and unbounded strings.

`UNKNOWN_INPUT`, `WRONG_FAMILY`, and `UNSUPPORTED_VERSION` are identity/version-phase
codes. `INVALID_DISCRIMINATOR` is a strict-validation-phase code. `INVALID_STRUCTURE`
is used for strict-validation failures and the T4 admissibility failure above;
`DUPLICATE_SEGMENT_INDEX` identifies the latter through `phase=ADMISSIBILITY` and
`input_slot=ASR`. `CORRELATION_MISMATCH` is the only correlation-phase code. No code
is emitted for a later phase after an earlier phase has rejected an input.

## 5. Exact validated P2 input surface

The proposal consumes existing P2 V1 result models; it does not widen or redefine
them. This inventory records every upstream field relevant to the boundary, including
requiredness, nullability, and cross-field behavior.

### 5.1 ASR envelope and segments

Both ASR branches require these non-null fields:

| Field | Type/constraint | Cross-field rule |
|---|---|---|
| `contract_name` | literal `AsrResultV1` | exact P2 ASR identity |
| `contract_version` | literal string `1.0` | exact version |
| `correlation_id` | non-empty string | equals Vision input |
| `executed_at` | timezone-aware datetime | naive value rejects |
| `source_audio_ref` | `AsrAudioReferenceV1` | `artifact_ref` non-empty; `sha256` lowercase 64-hex |
| `profile_id` | closed `AsrProfileId` | no provider-specific value |
| `attempt_number` | integer `0..2` | copied only into typed failure provenance when failed |
| `repair_attempted` | boolean | copied only into typed failure provenance when failed |
| `status` | literal `SUCCEEDED` or `FAILED` | selects the exact Pydantic branch |

`AsrSuccessV1` additionally requires `transcript_raw` (empty string is valid),
`speech_diagnostic`, `detected_language`, `segments`, `input_duration_seconds > 0`,
`vad_enabled`, `model_identifier`, `model_revision`, `adapter_version`,
`runtime_version`, `config_hash`, and `quality_metadata`. `language_hint_applied` is
also a serialized non-null boolean field with construction default `false`. Nullable success fields
are `language_probability`, `language_hint_echo`, and `duration_after_vad_seconds`.
When `vad_enabled` is true, `duration_after_vad_seconds` is required; when false it is
null. `DETECTED` speech requires at least one segment and the last segment cannot end
after the input duration.

Each `AsrSegmentV1` has required `index >= 0`, `start_seconds >= 0`,
`end_seconds >= start_seconds`, and non-empty `text`. Its
`average_log_probability`, `compression_ratio`, `no_speech_probability`, and `words`
fields are nullable; when present, words have nonnegative ordered timestamps,
non-empty text, and nullable probability bounded to `[0,1]`. Segment and word numeric
values must be finite. The upstream `AsrSuccessV1` schema does not enforce global
uniqueness of `AsrSegmentV1.index`; T4 therefore adds the exact admissibility invariant
`For AsrSuccessV1, all AsrSegmentV1.index values MUST be unique.` A duplicate produces the exact ASR rejection in
section 4, not a new error vocabulary. `transcript_raw` is never used as the matching
source and is never copied into a T4 result, reference, conflict, or fixture.

`AsrQualityMetadataV1` contains required `contract_version` literal string `1.0`,
`media_validation_artifact_ref`, and lowercase `media_validation_artifact_sha256`;
`mean_segment_log_probability` and `mean_no_speech_probability` are nullable, with
the latter bounded to `[0,1]`. `AsrFailureV1`
requires only its closed `error_code`, `retryable`, and `error_detail` failure fields
in addition to the shared envelope. T4 copies only closed failure tokens and safe
envelope metadata into `P2T4AsrFailureReferenceV1`.

### 5.2 Vision envelope and observations

Both Vision branches require these non-null fields:

| Field | Type/constraint | Cross-field rule |
|---|---|---|
| `contract_name` | literal `VisionUnderstandingResultV1` | exact P2 Vision identity |
| `contract_version` | literal string `1.0` | exact version |
| `correlation_id` | non-empty string | equals ASR input |
| `executed_at` | timezone-aware datetime | naive value rejects |
| `source_image_ref` | `VisionImageReferenceV1` | non-empty non-absolute artifact ref; lowercase 64-hex `sha256` |
| `profile_id` | closed `VisionProfileId` | exact P2 V1 enum |
| `profile_catalog_hash` | lowercase 64-hex string | retained through the source digest only |
| `attempt_number` | integer `0..2` | copied only into typed failure provenance when failed |
| `repair_attempted` | boolean | copied only into typed failure provenance when failed |
| `content_policy_version` | non-empty string | retained through the source digest only |
| `policy_match_view_version` | non-empty string | successful fusion requires the declared v2 match view |
| `policy_execution_state` | `NOT_EXECUTED`, `PASSED`, or `BLOCKED` | success requires `PASSED` |
| `status` | literal `SUCCEEDED` or `FAILED` | selects the exact Pydantic branch |

`VisionUnderstandingSuccessV1` requires non-null tuples `entities`, `actions`,
`relations`, `themes`, and `ambiguous_regions`, and requires `adapter_version` and
`config_hash`. Its `_requires_consistent_observation_references` validator calls the
upstream `_validate_observation_references` helper, which registers entity, action,
relation, theme, and ambiguous-region IDs in one global map; duplicate IDs therefore
already fail the upstream V1 contract across all five arrays. T4 relies on that validated
invariant and adds no redundant Vision uniqueness rule or new owner decision. Every source
observation ID is lowercase `[a-z0-9-]+` and globally unique across all five arrays.
`EntityCandidateV1` has required `observation_id`,
`label`, and nullable finite `confidence` in `[0,1]`. `ActionCandidateV1` contains
required `observation_id`, required `label`, nullable `actor_ref`, nullable
`object_ref`, and nullable finite `confidence` in `[0,1]`; each non-null reference
resolves to an entity.
`RelationCandidateV1` has required `observation_id`, `predicate`, `subject_ref`,
`object_ref`, and nullable finite `confidence` in `[0,1]`, resolving to entity or
action observations with distinct subject and object.
`ThemeCandidateV1` has required `observation_id`, `label`, and non-empty
`evidence_refs`, plus nullable finite `confidence` in `[0,1]`; evidence references
resolve to entity, action, or relation observations.
`AmbiguousRegionCandidateV1` has required `note` and no confidence or evidence-ref
field. `ObservedTextV1` values and their language declarations are copied unchanged
when a candidate is emitted; the match view is a derived internal view only.

For completeness, the embedded source text models are not redefined by T4 and have
these exact source fields: `ObservedTextV1` contains required non-empty normalized
`value` and required `language: TextLanguageDeclarationV1`; the latter contains
required `status` (`DECLARED`, `MIXED`, or `NOT_DETERMINED`), tuple `tags` defaulting
to empty, each tag length `2..32` and lowercased/sorted with no duplicates, and literal
`is_ground_truth=false`. `DECLARED` requires exactly one tag, `MIXED` at least two,
and `NOT_DETERMINED` none. `ObservedTextV1.value` uses the source
`vision-label-normalizer-v1` (NFC, trim, whitespace collapse), rejects an empty
normalized value, and does not casefold or translate. These source models are frozen,
`extra="forbid"`, and copied unchanged into fused observations; T4 adds no hidden
text, language, confidence, or metadata field. Their authoritative declaration is
`backend/src/sketch2life/contracts/schemas/vision.py:L79-L117`.

`VisionUnderstandingFailureV1` instead requires its closed `error_code`,
`error_detail`, and `retryable` fields and has no success-only candidate arrays. A
prohibited-claim failure requires a prohibited-claim category,
`policy_execution_state=BLOCKED`, and `retryable=false`. A failure reference carries
only closed enums, attempt/repair booleans, and `NOT_EXECUTED` or `BLOCKED` policy
state.

The source enum allowlists carried by the above fields are closed and are copied from
the authoritative P2 schemas (no free-form substitutes):

| Source type | Exact values |
|---|---|
| `AsrProfileId` | `FAKE_DETERMINISTIC_V1`, `FAKE_IDEMPOTENT_TIMEOUT_V1`, `WHISPER_TURBO_INT8_AUTO_V1`, `WHISPER_TURBO_FP16_AUTO_V1`, `WHISPER_LARGE_V3_INT8_AUTO_V1` |
| `AsrSpeechDiagnostic` | `DETECTED`, `NO_SPEECH_SUSPECTED`, `INDETERMINATE` |
| `VisionProfileId` | `FAKE_DETERMINISTIC_V1` |
| `AsrErrorCode` | `INPUT_NOT_VALIDATED`, `ASR_TIMEOUT`, `ASR_MODEL_UNAVAILABLE`, `ASR_PROVIDER_FAILURE`, `ASR_SCHEMA_INVALID` |
| `AsrErrorDetail` | `MEDIA_VALIDATION_NOT_PASSED`, `MEDIA_VALIDATION_PROVENANCE_MISSING`, `SOURCE_AUDIO_UNREADABLE`, `SOURCE_AUDIO_HASH_MISMATCH`, `TIMEOUT_BUDGET_EXCEEDED`, `MODEL_LOAD_FAILED`, `DEVICE_UNAVAILABLE`, `TRANSIENT_RUNTIME_FAILURE`, `PERMANENT_RUNTIME_FAILURE`, `OUTPUT_MAPPING_FAILED` |
| `VisionErrorCode` | `INPUT_NOT_VALIDATED`, `VISION_MODEL_UNAVAILABLE`, `VISION_TIMEOUT`, `VISION_PROVIDER_FAILURE`, `VISION_SCHEMA_INVALID`, `PROHIBITED_CLAIM_DETECTED` |
| `VisionNonPolicyErrorDetail` | `MEDIA_VALIDATION_NOT_PASSED`, `MEDIA_VALIDATION_PROVENANCE_MISSING`, `SOURCE_IMAGE_UNREADABLE`, `SOURCE_IMAGE_HASH_MISMATCH`, `MODEL_LOAD_FAILED`, `DEVICE_UNAVAILABLE`, `TIMEOUT_BUDGET_EXCEEDED`, `TRANSIENT_RUNTIME_FAILURE`, `PERMANENT_RUNTIME_FAILURE`, `OUTPUT_MAPPING_FAILED`, `DUPLICATE_OBSERVATION_ID`, `REFERENCE_INTEGRITY_VIOLATION` |
| `VisionProhibitedClaimCategory` | `PSYCHOLOGICAL_INFERENCE_CLAIM`, `PERSONALITY_CLAIM`, `DIAGNOSTIC_CLAIM`, `MENTAL_STATE_CLAIM`, `TRAUMA_CLAIM`, `DEVELOPMENTAL_CLAIM` |

`VisionFailureDetail` is exactly the union of `VisionNonPolicyErrorDetail` and
`VisionProhibitedClaimCategory`; the source failure-matrix invariants remain active.
The enum declarations are in `backend/src/sketch2life/contracts/schemas/asr.py:L15-L46`
and `backend/src/sketch2life/contracts/schemas/vision.py:L120-L126,L365-L403`.

FEAT-018 flat fields, P2 V2 profile/provenance/decoding fields, and provider-specific
fields are not admissible substitutes for these inputs.

## 6. Proposed P2-T4 output schema

All proposed P2-T4 models are strict `frozen=True` models with `extra="forbid"`.
Nested arrays are tuples, nested models are immutable, and no output model contains a
mutable arbitrary map or metadata field.

### 6.1 `P2T4FusedResultV1`

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `contract_name` | literal `P2T4FusedResultV1` | required, non-null | exact serialized name |
| `contract_version` | literal string `1.0` | required, non-null | exact serialized version |
| `status` | `FUSED` or `UPSTREAM_FAILURE` | required, non-null | no third fused-result status |
| `correlation_id` | non-empty string | required, non-null | copied after equality validation |
| `executed_at` | timezone-aware datetime | required, non-null | injected T4 execution time |
| `source_asr_result_ref` | `P2T4SourceResultRefV1` | required, non-null | exact ASR identity, status, and digest |
| `source_vision_result_ref` | `P2T4SourceResultRefV1` | required, non-null | exact Vision identity, status, and digest |
| `fusion_policy_config_hash` | lowercase 64-hex string | required, non-null | hash of the validated policy |
| `entities` | tuple of `P2T4FusedEntityV1` | required, non-null | Vision source order; empty on upstream failure |
| `actions` | tuple of `P2T4FusedActionV1` | required, non-null | Vision source order; empty on upstream failure |
| `relations` | tuple of `P2T4FusedRelationV1` | required, non-null | Vision source order; empty on upstream failure |
| `themes` | tuple of `P2T4FusedThemeV1` | required, non-null | Vision source order; empty on upstream failure |
| `conflicts` | tuple of `P2T4ConflictV1` | required, non-null | canonical conflict order; empty on upstream failure |
| `uncertainty` | `P2T4UncertaintySummaryV1` | required, non-null | empty per-observation rows on upstream failure |
| `upstream_failure` | `P2T4UpstreamFailureRefV1` or null | required, nullable | non-null exactly for `UPSTREAM_FAILURE` |

Ambiguous regions are not emitted as T4 observations. Their source result remains
traceable only through `source_vision_result_ref.result_sha256`; there is no ambiguous
text field, preservation envelope, or ambiguous-output collection. No output field
contains raw transcript text, raw media, provider payloads, prompts, credentials,
endpoints, or psychological, diagnostic, personality, trauma, developmental, or
mental-state claims.

### 6.2 Exact source references, claim references, and policy fields

`P2T4SourceResultRefV1` contains exactly these required, non-null fields:

| Field | Type | Rule |
|---|---|---|
| `identity` | `P2.AsrResultV1@1.0` or `P2.VisionUnderstandingResultV1@1.0` | matches its result slot |
| `status` | `SUCCEEDED` or `FAILED` | copied from the validated source branch |
| `result_sha256` | lowercase 64-hex string | SHA-256 of the canonical validated source-result JSON |

`P2T4NarrationClaimRefV1` contains exactly these required, non-null fields:

| Field | Type | Rule |
|---|---|---|
| `segment_index` | integer `>= 0` | exact `AsrSegmentV1.index`; unique within the validated source |
| `claim_start` | integer `>= 0` | token offset in that normalized segment only |
| `claim_end` | integer `> claim_start` | exclusive token offset in that same segment |

This tuple is the canonical internal coordinate `(segment_index, claim_start,
claim_end)`. It contains no transcript text and cannot refer to another segment.

`P2T4FusionPolicyConfigV1` contains exactly these required, non-null fields:

| Field | Type | Exact value/invariant |
|---|---|---|
| `contract_name` | literal string | `P2T4FusionPolicyConfigV1` |
| `contract_version` | literal string | `1.0` |
| `config_version` | non-empty string | versioned policy identifier |
| `entity_match_mode` | literal string | `WHOLE_TOKEN_SEQUENCE` |
| `narration_weight_mode` | literal string | `SUPPORT_ONLY` |
| `confidence_floor` | finite float in `[0,1]` | original base comparison only |
| `uncertainty_formula_id` | literal string | `AGREEMENT_WEIGHTED_V1` |
| `match_view_version` | literal string | `vision_policy_match_view-v2` |
| `negation_cues` | tuple of token tuples | exactly `(("not",), ("no",), ("never",), ("isn", "t"), ("doesn", "t"), ("didn", "t"))` |
| `negation_window_tokens` | literal integer | `3` |
| `corroboration_increment` | canonical decimal string | exactly `"0.10"`; hash and contract retain this string |

The value `"0.10"` is converted to `Decimal("0.10")` for approved arithmetic only.
It is never first converted through a binary float, and the canonical policy/hash
projection retains the exact string.

`P2T4UpstreamFailureRefV1` contains exactly:

| Field | Type | Required/nullability |
|---|---|---|
| `contract_name` | literal `P2T4UpstreamFailureRefV1` | required, non-null |
| `contract_version` | literal string `1.0` | required, non-null |
| `failed_modality` | `ASR`, `VISION`, or `BOTH` | required, non-null |
| `asr_failure_ref` | `P2T4AsrFailureReferenceV1` or null | required; non-null for `ASR`/`BOTH` |
| `vision_failure_ref` | `P2T4VisionFailureReferenceV1` or null | required; non-null for `VISION`/`BOTH` |

`P2T4AsrFailureReferenceV1` contains exactly `source_asr_result_ref`,
`error_code`, `error_detail`, `attempt_number`, `retryable`, and
`repair_attempted`; all are required and non-null, with closed source enums,
`attempt_number` in `0..2`, and no free-form error detail. `source_asr_result_ref`
is the exact `P2T4SourceResultRefV1` for the failed ASR result.

`P2T4VisionFailureReferenceV1` contains exactly `source_vision_result_ref`,
`error_code`, `error_detail`, `attempt_number`, `retryable`,
`repair_attempted`, and `policy_execution_state`; all are required and non-null,
with closed source enums, `attempt_number` in `0..2`, and policy state limited to
`NOT_EXECUTED` or `BLOCKED`. It has no free-form error detail.

### 6.3 Exact fused observation fields

Every fused observation wraps exactly one Vision source observation. Distinct source
observation IDs are never merged, even if their normalized labels are equal.
`fused_observation_id` and `source_observation_ref` are required strings matching
`[a-z0-9-]+` and are equal. The exact fields are:

`P2T4FusedEntityV1`:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `fused_observation_id` | lowercase observation ID | required, non-null | equals source observation ID |
| `source_observation_ref` | lowercase observation ID | required, non-null | resolves to one source entity |
| `label` | `ObservedTextV1` | required, non-null | copied unchanged from Vision |
| `narration_support_applied` | boolean | required, non-null | true iff a positive exact span exists |
| `narration_support_ref` | `P2T4NarrationClaimRefV1` or null | required, nullable | canonical earliest positive span |
| `primary_interpretation` | boolean | required, non-null | false when conflicting |

`P2T4FusedActionV1` has exactly these fields:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `fused_observation_id` | lowercase observation ID | required, non-null | equals source observation ID |
| `source_observation_ref` | lowercase observation ID | required, non-null | resolves to one source action |
| `label` | `ObservedTextV1` | required, non-null | copied unchanged from Vision |
| `actor_ref` | lowercase observation ID or null | required, nullable | resolves to a fused entity when non-null |
| `object_ref` | lowercase observation ID or null | required, nullable | resolves to a fused entity when non-null |
| `narration_support_applied` | boolean | required, non-null | true iff a positive exact span exists |
| `narration_support_ref` | `P2T4NarrationClaimRefV1` or null | required, nullable | canonical earliest positive span |
| `primary_interpretation` | boolean | required, non-null | false when conflicting |

`P2T4FusedRelationV1` has exactly these fields:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `fused_observation_id` | lowercase observation ID | required, non-null | equals source observation ID |
| `source_observation_ref` | lowercase observation ID | required, non-null | resolves to one source relation |
| `predicate` | `ObservedTextV1` | required, non-null | copied unchanged from Vision |
| `subject_ref` | lowercase observation ID | required, non-null | resolves to a fused entity or action |
| `object_ref` | lowercase observation ID | required, non-null | resolves to a fused entity or action and differs from subject |
| `narration_support_applied` | boolean | required, non-null | true iff a positive exact span exists |
| `narration_support_ref` | `P2T4NarrationClaimRefV1` or null | required, nullable | canonical earliest positive span |
| `primary_interpretation` | boolean | required, non-null | false when conflicting |

`P2T4FusedThemeV1` has exactly these fields:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `fused_observation_id` | lowercase observation ID | required, non-null | equals source observation ID |
| `source_observation_ref` | lowercase observation ID | required, non-null | resolves to one source theme |
| `label` | `ObservedTextV1` | required, non-null | copied unchanged from Vision |
| `evidence_refs` | non-empty tuple of lowercase observation IDs | required, non-null | exact source cardinality/order; resolves to entity/action/relation |

Themes are Vision-only and never receive narration support, a primary flag, a
certainty row, or a negation conflict. Actor/object/subject references are copied from
the validated source and are never retargeted.

### 6.4 Exact conflicts and uncertainty fields

`P2T4ConflictV1` contains exactly these required fields:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `conflict_id` | `P2T4-CONFLICT-` plus 64 lowercase hex | required, non-null | exact algorithm in section 9 |
| `reason_code` | closed enum | required, non-null | `ENTITY_ATTRIBUTE_CONTRADICTION`, `ACTION_CONTRADICTION`, `RELATION_CONTRADICTION`, or `LOW_CONFIDENCE_EVIDENCE` |
| `vision_claim_ref` | lowercase observation ID | required, non-null | conflicting fused observation |
| `narration_claim_ref` | `P2T4NarrationClaimRefV1` or null | required, nullable | required for contradiction; null for low-confidence without positive/refuting span |
| `recommended_reviewer_attention` | literal boolean | required, non-null | always `true` for an emitted conflict |

The entity/action/relation contradiction reason requires a canonical refuting claim
reference. A `LOW_CONFIDENCE_EVIDENCE` conflict uses the canonical positive reference
when one exists and null otherwise. No conflict carries text, labels, or excerpts.

`P2T4UncertaintySummaryV1` contains exactly:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `formula_id` | literal string | required, non-null | `AGREEMENT_WEIGHTED_V1` |
| `per_observation` | tuple of `P2T4ObservationUncertaintyV1` | required, non-null | one row per entity/action/relation, none for themes |

`P2T4ObservationUncertaintyV1` contains exactly:

| Field | Type | Required/nullability | Rule |
|---|---|---|---|
| `observation_id` | lowercase observation ID | required, non-null | resolves to one fused entity/action/relation |
| `candidate_kind` | `ENTITY`, `ACTION`, or `RELATION` | required, non-null | matches resolved candidate |
| `certainty_status` | closed enum | required, non-null | `MEASURED`, `NOT_MEASURED`, or `NOT_APPLICABLE_CONFLICTING` |
| `certainty` | finite float in `[0,1]` or null | required, nullable | non-null only for `MEASURED` |

`MEASURED` means finite numeric source confidence, with or without an eligible
positive match. `NOT_MEASURED` means source confidence is null and certainty is null,
even when support exists. `NOT_APPLICABLE_CONFLICTING` means any conflict participant
and certainty is null. An upstream-failure result has an empty `per_observation` tuple.

### 6.5 Result invariants

- `FUSED` means both validated upstream models have `status=SUCCEEDED`, including an
  empty but schema-valid transcript and empty Vision collections. It has
  `upstream_failure=null`.
- `UPSTREAM_FAILURE` means one or both validated upstream models have `status=FAILED`.
  It has the structurally matching non-null failure reference and empty entities,
  actions, relations, themes, conflicts, and uncertainty rows.
- Identity mismatch, strict-validation error, or correlation mismatch returns the
  rejection type and never produces a fused-result status.
- Source result references are required in both statuses and retain only identity,
  source branch status, and canonical digest. The digest does not embed source text.
- A successful ASR empty transcript is not an error, creates no narration-only
  candidate, and remains eligible for `FUSED` when Vision also succeeds.

## 7. Matching, negation, coordinates, and multi-span semantics

### 7.1 Per-segment match source and token coordinates

For a successful ASR result, matching runs independently for each validated
`AsrSegmentV1.text`. The segment's source `index` is the canonical `segment_index`.
The normalized token list is rebuilt from zero for every segment. A segment's tokens
are never concatenated with another segment's tokens, and a claim cannot cross a
segment boundary. `transcript_raw` is not authoritative and is ignored for matching,
coordinates, derived references, and fixture semantics. The source-result digest may
still change when the validated source artifact changes; it binds provenance and does
not copy transcript text into the T4 output.

The admissibility stage must first establish unique nonnegative segment indexes. Match
coordinates are exactly `(segment_index, claim_start, claim_end)`, where `claim_start`
is inclusive and `claim_end` is exclusive, both relative to that segment's normalized
token list. Canonical narration reference ordering is exactly
`(segment_index ASC, claim_start ASC, claim_end ASC)`. The source tuple order is never
used to make coordinates or select evidence: identical coordinate tuples are deduplicated
before independently selecting the canonical earliest positive and earliest refuting
reference. A short segment prefix yields a short
preceding window; no negative indexes are manufactured and a cue sequence must fit
entirely within the available prefix.

### 7.2 One match view and no sentence boundaries

T4 uses the existing `vision_policy_match_view-v2` recipe exactly once per segment or
candidate text:

1. Unicode NFC normalization;
2. whitespace collapse and trim;
3. Unicode casefold;
4. a second Unicode NFC normalization;
5. map every Unicode punctuation or separator category `P*` or `Z*` to an ASCII space;
6. final whitespace collapse and trim;
7. tokenize by single-space separators.

Stored `ObservedTextV1.value` and `AsrSegmentV1.text` are never rewritten. There is
no sentence tokenizer and no sentence-boundary behavior: punctuation becomes a space
under the match view and cannot stop or extend a window. ASCII apostrophe and curly
apostrophe are both punctuation and become spaces, so `isn't` and its curly form
produce `("isn", "t")`; the corresponding forms of `doesn't` and `didn't` produce
`("doesn", "t")` and `("didn", "t")`. No second apostrophe tokenizer exists.

Vision labels and relation predicates match only exact contiguous
`WHOLE_TOKEN_SEQUENCE` sequences in each segment's match-view tokens. Every occurrence
at every valid start is a span candidate. Exact duplicate coordinate tuples are
deduplicated once; distinct overlapping spans remain distinct. Matching is performed
independently for each Vision observation, so equal normalized labels do not merge
source observation IDs.

### 7.3 Exact negation window and cues

After a claim span matches, inspect exactly the three match-view tokens immediately
preceding `claim_start` in that same segment. A cue matches only if its entire sequence
fits inside that three-token prefix. The frozen cue sequences are exactly:

```text
("not",)
("no",)
("never",)
("isn", "t")
("doesn", "t")
("didn", "t")
```

A cue outside the window, a partial cue sequence, a cue in another segment, or a cue
with no Vision counterpart produces no contradiction. Sarcasm, indirect negation,
distant scope, coreference, synonym/antonym reasoning, semantic contradiction, and
sentence parsing are out of scope.

### 7.4 Multi-span truth table and canonical references

Each exact match span is classified independently as positive or refuting. Positive
means no complete cue sequence occurs in the exact preceding window. Refuting means a
complete cue sequence is present.

| Vision counterpart | Positive spans | Refuting spans | Support fields | Conflict | Adjustment/primary eligibility |
|---|---:|---:|---|---|---|
| absent | any | any | no T4 candidate | none | not applicable |
| present | 0 | 0 | false, null ref | none | no adjustment; eligible if otherwise measured |
| present | >=1 | 0 | true, earliest positive ref | none | one adjustment at most; eligible |
| present | 0 | >=1 | false, null ref | one contradiction with earliest refuting ref | no adjustment; not eligible |
| present | >=1 | >=1 | true, earliest positive ref | one contradiction with earliest refuting ref | no adjustment; not eligible |

For mixed positive/refuting spans, support remains true and retains the canonical
positive reference; the contradiction retains the canonical refuting reference;
adjustment and primary eligibility are suppressed. For any set of duplicate or
multiple qualifying spans, first deduplicate identical coordinate tuples, then sort
the remaining tuples exactly by `(segment_index ASC, claim_start ASC, claim_end ASC)`
and independently select the earliest positive and earliest refuting tuple. Selection
is independent of source tuple traversal order. One candidate receives at most one
positive adjustment, regardless of segment or span count. A support reference and a
contradiction reference are distinct fields and cannot contain raw text.

## 8. Confidence, primary selection, and evidence cardinality

### 8.1 Confidence and low-confidence ordering

Every numeric source confidence and configured floor is finite and in `[0,1]`.
`NaN`, positive infinity, and negative infinity are strict-validation rejections. The
low-confidence test uses the original source confidence before support adjustment and
is strictly `base < configured_floor`; null is never below the floor.

For a finite base with positive support and no conflict, compute exactly:

```text
adjusted = min(Decimal("1.0"), Decimal(str(base)) + Decimal("0.10"))
```

Do not quantize or round. Convert the final Decimal to a Python/JSON float exactly
once and reject it if non-finite. The candidate receives at most one adjustment. A
null source confidence remains `NOT_MEASURED`/null even with support. A conflict
participant receives no adjustment and `NOT_APPLICABLE_CONFLICTING`/null.

`LOW_CONFIDENCE_EVIDENCE` is emitted for each measured candidate whose original base
is strictly below the floor. Here, a measured candidate means an entity, action,
relation, or theme with a finite numeric Vision confidence. A low-confidence theme
may therefore emit this evidence conflict with a null narration reference; it remains
Vision-only, has no uncertainty row, and never enters primary ranking. This is a typed
evidence conflict, not an upstream failure. Any candidate with only this conflict
remains in the fused collection but is not primary.

### 8.2 Primary grouping and complete ranking

Grouping is by candidate kind, normalized match-view claim, and structural references:

- entity: `(ENTITY, normalized(label), ())`;
- action: `(ACTION, normalized(label), actor_ref, object_ref)`;
- relation: `(RELATION, normalized(predicate), subject_ref, object_ref)`.

The stored label or predicate is copied unchanged; the normalized claim is only an
internal grouping key. Same-label candidates with distinct source observation IDs
remain distinct fused records; grouping never merges source IDs.

An eligible candidate is validated, non-conflicting, and of kind entity, action, or
relation. Themes never enter primary selection. Within each group, rank in this exact
order:

1. positive narration support: `true` before `false`;
2. original finite source confidence, descending; null confidence is after every finite
   numeric value;
3. stable source observation ID, ascending lexicographic order, as the final tie-break
   for every remaining tie, including equal support and null confidence.

Source input order is never a tie-break. If no candidate in a group is eligible, every
candidate in that group has `primary_interpretation=false` and the group has zero
primaries. Primary selection never removes, rewrites, lowers, or suppresses source
candidates or conflicts.

### 8.3 Evidence cardinality and order

- Every fused entity, action, relation, and theme has exactly one source observation
  reference. No merged multi-source candidate exists.
- A positive or refuting selection emits at most one `P2T4NarrationClaimRefV1`.
  Duplicate coordinate tuples are one reference, not multiple evidence records.
- `narration_support_ref` is non-null exactly when at least one positive span exists.
  A contradiction's `narration_claim_ref` is non-null and is the canonical refuting
  span. It is nullable for low-confidence-only evidence with no positive span.
- Theme `evidence_refs` is non-empty and preserves exact source tuple cardinality and
  order. It is not silently deduplicated or sorted.
- Conflicts are one record per reason/candidate pair. The ID algorithm prevents
  duplicate records for the same reason and fused observation.

## 9. Canonical projection, serialization, and conflict IDs

The canonicalization identity is `P2T4-CANONICAL-JSON-V1`. The Python reference
algorithm is pinned to CPython 3.13 and is the v1 interoperability oracle; a future
cross-language implementation must byte-match it or use a new canonicalization
identity.

### 9.1 Projection and included/excluded values

For a validated P2-T4 model, the projection starts with
`model_dump(mode="python", by_alias=False, exclude_none=False, exclude_unset=False)`.
It includes every declared contract field, including required null fields, policy
strings, source-result digests, claim coordinates, empty tuples, and failure refs when
structurally required. It excludes model-private fields, caches, temporary token
lists, source raw transcript text, raw media, provider payloads, prompts, credentials,
endpoints, absolute paths, unknown extras, and any value not declared by the contract.
The separate `result_sha256` source-artifact digest uses the complete validated source
model projection, including fields not copied into T4; its raw values are hashed but
never embedded in the T4 output.

The recursive normalization rules are exact:

| Value | Canonical representation |
|---|---|
| Pydantic model | declared fields projected recursively; no aliases |
| Enum or literal | its string/value token |
| tuple | JSON array preserving semantic order |
| list | JSON array preserving semantic order |
| dict | object with string keys; `sort_keys=True` orders keys lexically |
| `None` | JSON `null`; never omitted |
| aware datetime | normalize to UTC and format `YYYY-MM-DDTHH:mm:ss.ffffffZ` |
| finite float | Python 3.13 shortest round-trip JSON float representation |
| `Decimal` | forbidden except the policy token, which is already the exact string `"0.10"` |
| bytes or arbitrary object | reject; never stringify |

`json.dumps` is then called exactly as follows:

```python
json.dumps(
    normalized_projection,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
)
```

The UTF-8 encoding of that returned string is the canonical byte sequence. CPython's
standard shortest-round-trip float algorithm is therefore normative for v1; fixed
decimal formatting, locale formatting, binary-Decimal conversion, and alternate JSON
escaping are not allowed. Arrays are never reordered by object-key sorting.

### 9.2 Array order and sort keys

The top-level `entities`, `actions`, `relations`, and `themes` arrays preserve validated
Vision source order. Each theme `evidence_refs` array preserves source order. The
`per_observation` uncertainty array is sorted by
`(candidate_kind_rank, observation_id)`, where `ENTITY=0`, `ACTION=1`, and
`RELATION=2`. The `conflicts` array is sorted by
`(reason_rank, vision_claim_ref, narration_claim_ref_or_null, conflict_id)`, where
`ENTITY_ATTRIBUTE_CONTRADICTION=0`, `ACTION_CONTRADICTION=1`,
`RELATION_CONTRADICTION=2`, and `LOW_CONFIDENCE_EVIDENCE=3`; null claim references
sort before non-null references using the canonical tuple
`(segment_index, claim_start, claim_end)`. Claim-reference fields themselves are
objects and therefore have lexically sorted keys in JSON.

### 9.3 Exact SHA-256 and conflict-ID bytes

For any canonical JSON projection, hash exactly its UTF-8 bytes with SHA-256 and emit
lowercase hexadecimal (`hashlib.sha256(canonical_bytes).hexdigest()`).

For each conflict, let `reason_code` be its closed ASCII token and let
`fused_observation_id` be its closed lowercase observation ID. The exact conflict ID
payload is:

```python
payload = (
    reason_code.encode("utf-8")
    + b"\x00"
    + fused_observation_id.encode("utf-8")
)
conflict_id = "P2T4-CONFLICT-" + hashlib.sha256(payload).hexdigest()
```

The delimiter is one literal NUL byte. There is no escaping, trimming, case folding,
Unicode normalization, URL encoding, or separator substitution before hashing. The
closed reason-code alphabet and `[a-z0-9-]+` observation-ID alphabet cannot contain a
NUL; any future value outside those alphabets is rejected rather than escaped. The
digest suffix is always 64 lowercase hexadecimal characters.

## 10. Evidence binding, fixtures, and independent parity

### 10.1 Evidence binding record

Every future freeze or implementation evidence bundle must contain a hand-authored
binding record with these exact fields:

| Field | Required value/format | Current docs-only value |
|---|---|---|
| `review_base_commit` | full 40-character lowercase Git commit for the post-sync reviewed source tree | `d706d88a70c6a9136e397bea10d29f96bafd190b` |
| `future_source_commit` | explicit non-hash marker until the future freeze/implementation source is reviewed, approved, and committed | `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED` |
| `freeze_draft_sha256` | lowercase SHA-256 of normalized UTF-8 document bytes after removing this binding table and the revision-history section | `a2bc165f270ad003a38874975e5499e4b021a1d193060ac3fd6f75022085535e` |
| `implementation_package_sha256` | lowercase SHA-256 of normalized UTF-8 package bytes after removing its binding table and revision-history section | `af2442cb46f373d28439c4722491dea54e0aaf94ad416e1327a44865e50c6a5f` |
| `dependency_lock_sha256` | lowercase SHA-256 for every declared dependency/lock input | `pnpm-lock.yaml=b406b4c36c1e5304cf0c43b175c426d50aa3b43dc9a2bb81be357ea2b80b1665`; `backend/pyproject.toml=9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6` |
| `manifest_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json` bytes | required when the future artifact exists |
| `cases_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json` bytes | required when the future artifact exists |
| `expected_sha256` | SHA-256 of `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json` bytes | required when the future artifact exists |
| `final_evidence_sha256` | SHA-256 of the final evidence manifest, including the above values and validator outputs | required when the future evidence bundle exists |

The freeze/package digest scopes are explicit so a digest cannot silently hash its
own changing digest line. The current docs-only task does not claim fixture, expected,
or final-evidence hashes because those seven artifacts do not exist. Their required
fields and exact byte algorithm are nevertheless part of the proposed contract and
the future implementation gate, not an unresolved contract semantic.

For reproducibility, normalize `CRLF` and lone `CR` line endings to `LF`; remove the
complete table beginning with the exact binding-table header above through the blank
line immediately after its final row; remove the complete section beginning at the
exact heading `## 13. Revision history` through end of file; then UTF-8 encode the
remaining text and hash those bytes. The package digest uses the same steps with its
exact binding-table header and `## 12. Revision history` heading.

### 10.2 Future fixture and schema-parity requirements

The future offline implementation allowlist is exactly these seven paths, all
future-only in this draft:

```text
backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py
backend/src/sketch2life/application/services/p2_t4_fusion.py
backend/tests/contract/test_p2_t4_contract.py
backend/tests/unit/test_p2_t4_fusion.py
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

The manifest, cases, and expected files are separate artifacts. Expected outputs are
hand-authored from this draft and independently reviewed; they are not generated by
the implementation under test. The contract test must include an independent,
hand-authored schema-parity oracle that lists every field, requiredness/nullability,
enum, literal, cross-field invariant, and rejection precedence rule. It must not load
a schema snapshot, serialize the implementation model, introspect implementation
fields, or generate expected schemas from `p2_t4_fusion.py`.

The fixture set must cover agreement; ASR-only narration; Vision-only observations;
entity/action/relation exact negation; cue outside the three-token window; short
segment prefixes; punctuation/apostrophe normalization; no Vision counterpart;
duplicate and overlapping spans; cross-segment non-matching and coordinate reset;
duplicate `AsrSegmentV1.index` rejection at the admissibility stage; strict-validation
versus admissibility precedence with ASR checked before Vision; coordinate-tuple
deduplication and ordering independence;
below/at/above floor; null confidence with and without support; mixed positive and
refuting spans; multiple segments matching once; stable null-confidence ranking;
ambiguous-region omission; ASR failure; Vision failure; both failures; empty success;
canonical round-trip/determinism; exact conflict-ID bytes; rejection precedence;
privacy sentinels; and source/reference integrity. No mapping/adoption case is allowed.

Privacy sentinels must assert that no rejection, fused result, conflict, uncertainty
row, evidence reference, manifest record, case record, expected record, or final
evidence record contains raw input JSON, a `ValidationError`, exception text,
transcript text, candidate labels in a rejection, absolute/local paths, provider
payloads, prompts, credentials, endpoints, arbitrary metadata, or real child data.

No fixture file is created by this task. Existing B0 compatibility fixtures are not
copied, extended, or relabeled as T4 implementation fixtures.

## 11. Governance and deferred boundaries

- The seven paths are an implementation allowlist, not a license to create code or
  artifacts during this documentation task.
- No file in the seven-path list may be created, edited, stubbed, or pre-populated
  while this draft is under review or awaiting owner freeze.
- No schema, code, test, fixture, runtime, provider, GPU, model, download, network,
  commit, push, or pull-request work is authorized by this draft.
- The B0 mapping remains `PROPOSED_NOT_ADOPTED`; no mapping/adoption,
  preservation-envelope implementation, session/request/idempotency, registry, edge
  3, Gate A, migration, runtime wiring, or integration work is included.
- FEAT-017, FEAT-018, P2-T2, P2-T3, their existing evidence and fixtures, and all
  previously approved immutable artifacts remain outside this task.
- A separate contract-freeze decision and a separate seven-file implementation
  approval remain required. This draft cannot make the proposed identity canonical.

## 12. Independent review checklist and final handoff

### Pass 1 - technical completeness

- [x] Active output identity, historical Raw wording, and exact FEAT-018 rejection identities are synchronized.
- [x] Per-segment source text, coordinate reset, short prefixes, duplicate spans, and no cross-segment matching are explicit.
- [x] Exact match-view recipe, apostrophe tokens, cue sequences, three-token window, and sentence-boundary behavior are explicit.
- [x] Mixed positive/refuting spans retain support and both canonical references while suppressing adjustment and primary eligibility.
- [x] Complete field tables, requiredness/nullability, invariants, ranking, null ordering, and final source-ID tie-break are explicit.
- [x] Canonical projection, enum/tuple/null/datetime/float rules, array sort keys, Python 3.13 algorithm, conflict bytes, delimiter, escaping, and lowercase SHA-256 are explicit.
- [x] Evidence binding, independent hand-authored schema parity, fixture coverage, and privacy sentinels are explicit.
- [x] The upstream Vision V1 global observation-ID uniqueness validator is cited without adding a redundant T4 rule.
- [x] Duplicate ASR segment indexes have an admissibility-stage rejection with the exact closed fields and no raw echo.
- [x] Canonical narration references deduplicate coordinate tuples and sort exactly by `(segment_index ASC, claim_start ASC, claim_end ASC)` independently of source order.

The post-sync implementation fact and V1/V2 incompatibility table in section 1.1 must be
included in this pass; the old B0 snapshot is not evidence that the current FEAT-018 Raw
handoff is absent or merely proposed.

### Pass 2 - governance and security

- [x] Status is documentation-only and exactly **READY FOR OWNER FREEZE DECISION** after the
      two post-remediation final audits; the contract is still not frozen.
- [x] The seven-file implementation list is exact and no implementation path was created or edited.
- [x] `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` remains `PROPOSED_NOT_ADOPTED`.
- [x] FEAT-018 adoption, mapping, preservation envelope, session/request/idempotency, registry, edge 3, Gate A, migration, runtime/provider/GPU/network work remain deferred.
- [x] No credentials, raw transcript, media, provider payloads, absolute paths, or real child data are introduced.
- [x] Contract freeze and implementation approval remain separate gates.

The two post-remediation audits also verify that the B0 artifacts remain byte-untouched,
`PROPOSED_NOT_ADOPTED` remains unchanged, and the future source commit is not fabricated.

### Post-remediation final audit record

- Technical/contract audit: **COMPLETE**. The exact fixture paths, ASR admissibility invariant,
  terminal pipeline, closed rejection semantics, Vision upstream uniqueness attribution, and
  canonical narration-reference ordering/deduplication/source-order independence all pass.
- Governance/security/scope audit: **COMPLETE**. The authorized seven-document boundary, absence
  of the seven future implementation artifacts, preservation of B0/FEAT-018/FEAT-020 artifacts,
  deferred approval gates, and docs-only/no-implementation scope all pass.

### Final task status

**DRAFT - READY FOR OWNER FREEZE DECISION**

## 13. Revision history

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-14 | Initial seven-file hold-for-independent-review draft. |
| 2 | 2026-09-14 | Synchronized owner-selected identity and semantics; completed fields, segment matching, canonical bytes/IDs, evidence binding, parity-oracle, fixture, and governance requirements; no implementation added. |
| 3 | 2026-09-14 | Clarified finite-confidence low-confidence evidence for Vision themes, completed source field/enumeration detail and reproducible digest boundaries, and repeated independent reviews; no implementation added. |
| 4 | 2026-09-14 | Reconciled the post-sync implemented FEAT-018 Raw handoff against the proposed P2-T4 direction, recorded incompatibilities and the d706 review base, and held status at `DRAFT - UPSTREAM RECONCILIATION REVIEW REQUIRED` for two final audits; no implementation added. |
| 5 | 2026-09-14 | Recorded the two passing post-sync final audits and restored owner-freeze-ready status; no contract or implementation approval was granted. |
| 6 | 2026-09-14 | Preserved the exact intermediate reconciliation-review status in the history; no contract or implementation approval was granted. |
| 7 | 2026-09-14 | Reopened as `CONTRACT FREEZE BLOCKED` for exact future fixture paths, ASR duplicate-index admissibility, precedence, and canonical reference-order remediation; no implementation added. |
| 8 | 2026-09-14 | Resolved the exact fixture-path, ASR admissibility/precedence, Vision upstream-uniqueness attribution, and canonical-reference ordering blockers; no implementation added. |
| 9 | 2026-09-14 | Recorded the post-remediation technical/contract and governance/security/scope audits, verified digest bindings, and restored owner-freeze-ready status; no contract or implementation approval was granted. |
