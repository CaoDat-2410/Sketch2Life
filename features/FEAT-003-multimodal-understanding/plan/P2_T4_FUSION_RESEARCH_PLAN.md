# P2-T4 multimodal fusion and conflict detection research plan

- Status: **DRAFT - READY FOR OWNER FREEZE DECISION**
- Decision date: 2026-09-13
- Owner: Person 2
- Parent plan: `PLAN.md`, revision 5, task P2-T4
- Input dependency: validated `P2.AsrResultV1@1.0` and
  `P2.VisionUnderstandingResultV1@1.0` results from P2-T2/P2-T3.
- Output boundary: the proposed `P2T4.P2T4FusedResultV1@1.0`, serialized as
  `P2T4FusedResultV1 / 1.0`, for a future Gate A/P1 handoff. It is never canonical
  meaning, a Gate A decision, or session/job state. Former P2-T4
  `RawUnderstandingResultV1` wording is historical baseline only.
- Reconciliation request: `P2_T4_CONTRACT_RECONCILIATION_APPROVAL_REQUEST.md`

## Current state and approval boundary

All nine P2-T4 owner decisions are resolved as design choices: B0, B1, B2, B3a,
B3b, B3c, B4, B5, and B6. Recording those choices does not freeze a contract or
authorize implementation.

B0 selects **Option 3**, a separately approved reconciliation between the live
FEAT-018 contract family and the P2-T2/P2-T3/P2-T4 family. The approved
documentation-only reconciliation package is complete: its report, synthetic
compatibility fixture, follow-up impact record, and independent technical and
governance reviews are recorded in the feature-local package. It records one
explicit versioned mapping as a proposal only; the mapping is not adopted as a
runtime contract. Owner confirmation of source preservation and any adoption or
follow-up implementation approval remain pending. Contract freeze, migration, schema
replacement, registry cutover, runtime wiring, FEAT-018 changes, and P2-T4 fusion
  implementation remain separately gated. The 2026-09-14 reissue has a seven-file
  offline core direction and a companion freeze draft under post-sync upstream
  reconciliation; implementation and runtime integration are not approved.

`approvals/TASK_APPROVAL.md` now records a separate 2026-09-14 docs-only remediation/reissue
scope, but still excludes P2-T4 fusion implementation and P2-T5. No P2-T4 schema, fusion
code, migration execution, registry cutover, runtime wiring, provider call, GPU/model work,
  or FEAT-018 change is authorized from this plan. The existing FEAT-018 implementation is
  inspected only; the additive metadata-only B0 reconciliation fixture remains a B0 artifact
  and is not a T4 implementation fixture.

The active proposed v1 design choices are:

The earlier full-document technical and governance/security reviews of the reissued package
and freeze draft remain historical readiness evidence. Two independent post-sync final audits
(technical/contract and governance/security/scope) passed; the owner-freeze-ready status is
restored. The owner freeze decision and separate implementation approval remain pending.

- `P2T4FusedResultV1.status` contains only `FUSED` and
  `UPSTREAM_FAILURE`.
- `upstream_failure` is non-null exactly for `UPSTREAM_FAILURE` and null for
  `FUSED`.
- Narration is support/refute-only; it does not independently create entity,
  action, relation, or theme claims.
- Themes pass through from vision only; narration does not create or re-score
  themes.
- Contradiction detection uses exactly the six approved cues and exactly three
  match-view tokens immediately before an already-matched claim span.
- Weighting can affect only `primary_interpretation` among non-conflicting
  candidates; source observations and conflicts are never erased or weakened.
- Corroboration adds `0.10` at most once per supported, non-conflicting candidate
  and caps the result at `1.0`.
- The formula identity remains `AGREEMENT_WEIGHTED_V1`.
- A null source vision confidence remains `certainty=null` with
  `certainty_status=NOT_MEASURED`, even when narration support exists; support
  provenance is retained and no numeric base is fabricated.
- `LOW_CONFIDENCE_EVIDENCE` applies to every entity, action, relation, or theme with
  finite numeric Vision confidence below the floor; a theme may emit that conflict but
  remains Vision-only, has no uncertainty row, and never enters primary ranking.
- Matching runs independently against each validated `AsrSegmentV1.text`; normalized
  token coordinates are `(segment_index, claim_start, claim_end)` and both token
  coordinates and the three-token negation window reset for every segment.
- `transcript_raw` is not authoritative and is never copied into T4. The policy/hash
  representation of `corroboration_increment` is the exact string `"0.10"`, converted
  to `Decimal` only for arithmetic.
- Ambiguous Vision regions do not become fused observations; provenance is retained
  only through the canonical source-result reference/digest. Mixed positive/refuting
  spans retain support plus canonical positive/refuting refs while suppressing
  adjustment and primary eligibility.
- Finite confidence values rank before null values, and stable source observation ID is
  the final tie-break for every primary-selection tie.
- The current upstream `AsrSuccessV1` contract permits duplicate
  `AsrSegmentV1.index` values. T4 therefore requires the admissibility invariant exactly:
  `For AsrSuccessV1, all AsrSegmentV1.index values MUST be unique.` The upstream
  `VisionUnderstandingSuccessV1` validator already enforces global uniqueness across
  entities, actions, relations, themes, and ambiguous regions through
  `_validate_observation_references`; T4 adds no redundant Vision uniqueness rule or
  owner decision.
- The entire workstream remains `NOT APPROVED` for implementation.

## Post-sync FEAT-018 handoff reconciliation (2026-09-14)

The review base is `d706d88a70c6a9136e397bea10d29f96bafd190b`. The merged tree contains the
current FEAT-018 P2-T2 implementation: FEAT-018's frozen/implemented live-development handoff
is `RawUnderstandingResultV1 / 1.0`, owned by FEAT-018 and closed for its bounded offline slice
at `11468d3a5a327697a491f09251a3210987337da0`. The schema, raw-mapper port, mapper, and focused
contract/unit tests are current implementation sources, not a historical proposal.

The FEAT-018 mapper consumes FEAT-003 `VisionUnderstandingResultV2` and optional P2 `AsrResultV1`.
The FEAT-020 backend workflow in
`backend/src/sketch2life/application/services/backend_ai_workflow.py` also requests
`VisionUnderstandingRequestV2` and consumes `VisionUnderstandingResultV2`. P2-T4 remains a separate offline proposal consuming P2
`VisionUnderstandingResultV1` and emitting the proposed `P2T4FusedResultV1`; it is neither an
alias of nor a replacement for FEAT-018 `RawUnderstandingResultV1`.

The incompatibilities are contract-level, not naming-only: the input Vision versions differ;
P2-T4 proposes `P2T4FusedResultV1` with `FUSED | UPSTREAM_FAILURE`, while FEAT-018 owns
`RawUnderstandingResultV1` with `SUCCEEDED | FAILED` branches; FEAT-018 requires `session_id`,
`source_image_ref`, `gate_a_required=true`, and V2 profile/catalog/model provenance; and the
families differ in ambiguous-observation preservation, `fused_claims`, conflict IDs/claim refs
and reason codes, confidence/uncertainty requiredness, and typed failure shapes. No alias,
replacement, or silent projection is valid.

The immutable B0 report, manifest, and review records predate the implemented FEAT-018 Raw module.
They remain an old reconciliation snapshot, with the mapping
`P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` still `PROPOSED_NOT_ADOPTED`. Separately approved
integration reconciliation is required before adoption, registry change, consumer update, or
edge-3 handoff. Two independent post-sync final audits (technical/contract and
governance/security/scope) passed, so the current remediation status is
`DRAFT - READY FOR OWNER FREEZE DECISION`.
The future T4 freeze/implementation source commit is
`UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`.

## Confirmed admissibility and rejection boundary

The normative processing pipeline is exactly:

```text
identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants -> correlation equality -> typed upstream status -> fusion
```

The first failing stage is terminal. ASR is checked before Vision where slot ordering
applies. Strict upstream validation and T4 admissibility are distinct: duplicate ASR
segment indexes can pass `AsrSuccessV1` validation and are then rejected by T4 with
`status=REJECTED`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`,
`input_slot=ASR`, and `field_code=DUPLICATE_SEGMENT_INDEX`. The complete rejection
identity is `P2T4FusionInputRejectionV1@1.0`; `expected_identity` and
`observed_identity` are `P2.AsrResultV1@1.0`, and `observed_status=SUCCEEDED`.
The duplicate index, transcript, input object, exception, validation path, and other
raw details are never emitted. `ADMISSIBILITY` and `DUPLICATE_SEGMENT_INDEX` extend
the existing closed phase/field-code tables; `INVALID_STRUCTURE` is reused rather
than a synonymous new code.

Canonical narration reference ordering is exactly
`(segment_index ASC, claim_start ASC, claim_end ASC)`. Identical coordinate tuples
are deduplicated before independently selecting the earliest positive and earliest
refuting reference, and selection is independent of source tuple traversal order.
This is a normative admissibility/serialization rule, not a new owner decision.

The future fixture/test artifacts are exactly:

```text
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json
```

## Research question

Can a pure, deterministic, model-free fusion layer combine already-typed ASR and
vision results while preserving every disagreement and never fabricating a claim
that neither modality produced? T4 consumes validated provider-neutral result
objects. It does not call a model, provider, network, GPU, or live service.

The research output is a contract-and-policy design plus a fixture/test plan. The
companion freeze draft proposes the exact P2 V1 input identities and a namespaced P2-T4
output; earlier technical and governance/security reviews are historical, and the current
post-sync reconciliation must complete before the owner-freeze-ready status is restored. It
does not freeze either family, adopt the cross-feature mapping, or authorize implementation.

## Scope and explicit non-goals

### In scope after the required approvals

- A versioned deterministic fusion policy configuration.
- The proposed versioned `P2T4FusedResultV1` with source references, fused observations,
  conflicts, uncertainty, and typed upstream-failure provenance.
- Support/refute matching from transcript text to vision-produced candidates.
- Bounded deterministic negation conflict detection.
- Explicit preservation of source observations, references, and provenance.
- Synthetic fixture coverage and JSON-Schema/Pydantic round-trip and determinism
  tests, all without a model or network.

### Explicit non-goals

- No live provider, model, GPU, Lightning, Runpod, dependency download, or
  provider credential.
- No P2-T4 implementation code, schema migration, runtime wiring, or API route.
- No FEAT-018 migration, shared integration code, session/job/database/queue/UI,
  or mobile work.
- No Gate A UI, Gate A decision, P1 eligibility decision, or user-facing meaning.
- No independent narration NLU/entity extractor or narration-side theme extractor.
- No P2-T5 CLI or end-to-end evaluation report.
- No real child data, raw media, raw transcript duplication, prompt, provider
  payload, secret, endpoint, or personal metadata in evidence or logs.
- No change to P2-T1, P2-T2, or P2-T3 contracts, fixtures, policy, evidence, or
  historical results.
- No selection of a canonical FEAT-018/P2 contract shape inside this plan. That
  choice belongs to the separately approved B0 reconciliation.

## Blocker-0 contract identity gate

The repository contains two live/documented families using the same serialized
names:

1. FEAT-018's provider-shaped `AsrResultV1`/flat live Vision family and its current
   FEAT-018-owned `RawUnderstandingResultV1` handoff. The Raw schema, mapper port, mapper,
   and tests are implemented in the post-sync tree; the mapper consumes FEAT-003
   `VisionUnderstandingResultV2` plus optional P2 ASR and carries session/image/Gate-A/V2
   provenance.
2. P2-T2/P2-T3's provider-neutral discriminated `AsrResultV1` and
   `VisionUnderstandingResultV1`, plus this plan's proposed fusion result, which
   use different fields, discriminators, provenance, and failure semantics.

The owner selected **B0 Option 3**. The approved documentation-only reconciliation
package records the proposed explicit mapping and its compatibility/migration fixture,
while owner confirmation/adoption remains pending. The companion freeze draft narrows
the future offline T4 direction to the exact P2 V1 inputs and seven implementation paths,
but the result remains a review proposal rather than a frozen public contract or adopted
runtime shape. The existing B0 mapping fixture is not part of the T4 implementation case
set.

The immutable B0 report, manifest, and reviews are an older snapshot that predates the
implemented FEAT-018 Raw module. They are not edited or upgraded by this reissue. The mapping
remains `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` / `PROPOSED_NOT_ADOPTED`, and a
separately approved integration reconciliation is required before adoption, registry change,
consumer update, or edge-3 handoff. The current review base is
`d706d88a70c6a9136e397bea10d29f96bafd190b`; the future T4 freeze/implementation source commit
is `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`.

The full bounded workstream is in
`plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md`. It inventories both families,
their producers and consumers, the Gate A/P1 and integration registry impacts,
the migration/rollback requirements, and the validation gates. Its approved
documentation-only package is complete. Mapping adoption remains a separate deferred
decision; the P2-T4 owner freeze decision and separate T4 implementation approval are
still required before any contract or implementation becomes active.

## Resolved owner decisions

The following register is the active design record. It is consistent with the
canonical dated entry in `DECISIONS.md`; none of these rows is an unresolved
owner-choice placeholder.

### B0 - Option 3 selected, reconciliation package complete; adoption pending

P2-T4 uses the approved documentation-only reconciliation package between the
live FEAT-018 contract family and the P2-T2/P2-T3/P2-T4 family. The package
records a proposed explicit versioned mapping; owner confirmation/adoption remains
pending, and it does not select a final runtime canonical shape or authorize
migration or implementation.

### B5 - remove the former status from v1

Remove `NOT_FUSIBLE` from the proposed v1 contract. A future status may be
proposed only when a concrete reachable precondition, payload, fixtures, and
approval exist. The v1 result statuses become `FUSED | UPSTREAM_FAILURE`.

No active v1 field, invariant, fixture, status table, or implementation slice
uses the removed status. A structural incompatibility discovered during B0 is
handled by the reconciled contract/mapping and its typed validation behavior;
this plan does not invent a third result status or payload.

### B1 - support-only narration

Narration may support or refute vision candidates. It does not independently
create entities, actions, relations, or themes in v1. A transcript-only mention
has no T4 candidate unless a vision candidate is already present; it cannot create
a narration-only fused observation.

### B4 - vision-only themes

Themes pass through from vision. Narration does not create or re-score themes in
v1. A theme's source observation and evidence references remain traceable to the
vision result.

### B6 - bounded deterministic negation

The closed v1 cue list is exactly:

```text
not
no
never
isn't
doesn't
didn't
```

The window is exactly the three match-view tokens immediately preceding an
already-matched claim span. A cue outside that window, associated with another
span, or lacking a vision counterpart produces no conflict. This is deliberately
bounded and does not broaden into sarcasm, semantic contradiction, synonym/
antonym matching, coreference, or general NLU.

### B2 - primary-only weighting

Narration support may affect only `primary_interpretation` among non-conflicting
candidates. It never removes, rewrites, lowers, or suppresses source evidence or
conflicts. Weighting never runs as a way to suppress a conflict. Ranking is
deterministic and explicitly testable: positive support, finite confidence descending
with null after finite values, and stable source observation ID ascending as the final
tie-break. Input/source order is never a tie-break or a hidden score.

### B3a - increment 0.10

Apply the corroboration increment at most once per supported, non-conflicting
candidate, cap the result at `1.0`, and never stack the increment because the same
candidate matched multiple transcript segments.

### B3b - retain `AGREEMENT_WEIGHTED_V1`

`AGREEMENT_WEIGHTED_V1` remains the closed v1 formula identity. It is carried in
the uncertainty summary and participates in the policy/configuration provenance
after the B0 reconciliation places the final versioned field shape.

### B3c - retain `NOT_MEASURED`

If source vision confidence is null, certainty remains null and
`certainty_status=NOT_MEASURED`, even when narration support exists. The support
boolean/reference is preserved. T4 does not fabricate a numeric base value.

## Candidate contract baseline for reconciliation

The following is the design baseline to be reconciled, not a unilateral contract
freeze. All models are intended to be immutable and `extra="forbid"`, matching
the strictness of the P2-T2/P2-T3 contracts.

### Fusion policy configuration

```text
P2T4FusionPolicyConfigV1:
  contract_name: Literal["P2T4FusionPolicyConfigV1"]
  contract_version: Literal["1.0"]
  config_version: str
  entity_match_mode: Literal["WHOLE_TOKEN_SEQUENCE"]
  narration_weight_mode: Literal["SUPPORT_ONLY"]
  confidence_floor: float                 # 0.0..1.0
  uncertainty_formula_id: Literal["AGREEMENT_WEIGHTED_V1"]
  match_view_version: Literal["vision_policy_match_view-v2"]
  negation_cues: tuple[tuple[str, ...], ...]  # exact six token sequences
  negation_window_tokens: Literal[3]
  corroboration_increment: str             # exact canonical token "0.10"
```

The policy hash is SHA-256 over the complete `P2T4-CANONICAL-JSON-V1` configuration
projection. `corroboration_increment` remains the exact string `"0.10"` in the
contract and hash and is converted to `Decimal("0.10")` only for arithmetic. The
exact negation lexicon and three-token window are traceable and hash-comparable.

### Active proposed P2-T4 result baseline

```text
P2T4FusedResultV1:
  contract_name: Literal["P2T4FusedResultV1"]
  contract_version: Literal["1.0"]
  correlation_id: str
  executed_at: datetime
  source_asr_result_ref: P2T4SourceResultRefV1
  source_vision_result_ref: P2T4SourceResultRefV1
  fusion_policy_config_hash: str
  status: Literal["FUSED", "UPSTREAM_FAILURE"]
  entities: tuple[P2T4FusedEntityV1, ...]
  actions: tuple[P2T4FusedActionV1, ...]
  relations: tuple[P2T4FusedRelationV1, ...]
  themes: tuple[P2T4FusedThemeV1, ...]
  conflicts: tuple[P2T4ConflictV1, ...]
  uncertainty: P2T4UncertaintySummaryV1
  upstream_failure: P2T4UpstreamFailureRefV1 | None
```

The active proposed status set has exactly two members. `UPSTREAM_FAILURE` is used when
one or both validated upstream result objects is a typed failure; fusion does not
run on absent/failed input. `FUSED` is used when both upstream results succeed,
including an empty but schema-valid collection set. `upstream_failure` is
non-null exactly for `UPSTREAM_FAILURE` and null for `FUSED`.

An `UPSTREAM_FAILURE` result has empty `entities`, `actions`, `relations`,
`themes`, `conflicts`, and uncertainty rows. It carries only the typed failure references needed to
identify the failed modality; it never copies provider output or a free-form
failure message.

`P2T4SourceResultRefV1` contains exactly `identity`, `status`, and
`result_sha256`; identity is the exact P2 ASR or P2 Vision identity, status is
`SUCCEEDED` or `FAILED`, and the digest is lowercase SHA-256 of the canonical
validated source-result JSON. The source result reference/digest is the only T4
provenance for an omitted ambiguous Vision region.

### Typed upstream-failure references

```text
P2T4UpstreamFailureRefV1:
  contract_name: Literal["P2T4UpstreamFailureRefV1"]
  contract_version: Literal["1.0"]
  failed_modality: Literal["ASR", "VISION", "BOTH"]
  asr_failure_ref: P2T4AsrFailureReferenceV1 | None
  vision_failure_ref: P2T4VisionFailureReferenceV1 | None

P2T4AsrFailureReferenceV1:
  source_asr_result_ref: P2T4SourceResultRefV1
  error_code: AsrErrorCode
  error_detail: AsrErrorDetail
  attempt_number: int
  retryable: bool
  repair_attempted: bool

P2T4VisionFailureReferenceV1:
  source_vision_result_ref: P2T4SourceResultRefV1
  error_code: VisionErrorCode
  error_detail: VisionErrorDetail
  attempt_number: int
  retryable: bool
  repair_attempted: bool
  policy_execution_state: Literal["NOT_EXECUTED", "BLOCKED"]
```

`failed_modality` determines the populated sub-reference structurally: `ASR` has an
ASR reference and null Vision reference; `VISION` has null ASR reference and a Vision
reference; `BOTH` has both references. The references carry closed identifiers and
pointers only. They carry no raw provider output, prompt, endpoint, or free-form
message.

### Exact fused candidate baseline

Each fused candidate wraps exactly one source Vision observation. T4 does not merge
distinct Vision observations, even when their normalized labels match. The exact
fields are:

```text
P2T4FusedEntityV1:
  fused_observation_id: str
  source_observation_ref: str
  label: ObservedTextV1
  narration_support_applied: bool
  narration_support_ref: P2T4NarrationClaimRefV1 | None
  primary_interpretation: bool

P2T4FusedActionV1:
  fused_observation_id: str
  source_observation_ref: str
  label: ObservedTextV1
  actor_ref: str | None
  object_ref: str | None
  narration_support_applied: bool
  narration_support_ref: P2T4NarrationClaimRefV1 | None
  primary_interpretation: bool

P2T4FusedRelationV1:
  fused_observation_id: str
  source_observation_ref: str
  predicate: ObservedTextV1
  subject_ref: str
  object_ref: str
  narration_support_applied: bool
  narration_support_ref: P2T4NarrationClaimRefV1 | None
  primary_interpretation: bool

P2T4FusedThemeV1:
  fused_observation_id: str
  source_observation_ref: str
  label: ObservedTextV1
  evidence_refs: tuple[str, ...]

P2T4NarrationClaimRefV1:
  segment_index: int
  claim_start: int
  claim_end: int
```

`fused_observation_id` equals `source_observation_ref` and both use the closed
lowercase observation-ID alphabet. Labels and predicates are copied unchanged from
the source Vision observation. Support references contain only the canonical
`(segment_index, claim_start, claim_end)` coordinates and never transcript text.
Ambiguous regions are not represented in this collection.

### Conflict baseline

The closed v1 reason-code set is exactly:

```text
ENTITY_ATTRIBUTE_CONTRADICTION
ACTION_CONTRADICTION
RELATION_CONTRADICTION
LOW_CONFIDENCE_EVIDENCE
```

`ENTITY_ATTRIBUTE_CONTRADICTION` is reachable in v1 only through the bounded
negation-cue path, not through positive attribute antonyms. Presence mismatch and
upstream typed failure are not conflict records: silence is not a contradiction,
and an upstream failure is represented by the top-level status and typed
`upstream_failure` references.

```text
P2T4ConflictV1:
  conflict_id: str
  reason_code: ConflictReasonCode
  vision_claim_ref: str
  narration_claim_ref: P2T4NarrationClaimRefV1 | None
  recommended_reviewer_attention: bool
```

`recommended_reviewer_attention` is deterministic: every emitted conflict is
marked for reviewer attention, and no record is emitted for a non-conflict case.
Both claims remain available through their source pointers. A conflict is never
removed or downgraded by weighting.

## Matching and contradiction policy

### Per-segment support-only matching

The transcript and its segments are a support/refute signal against Vision entities,
actions, and relation predicates. Narration never creates an independent
entity/action/relation/theme collection. Matching runs independently against each
validated `AsrSegmentV1.text`; `transcript_raw` is not authoritative and is ignored.

The derived in-memory match view is rebuilt from zero for every segment and follows
the P2-T3 recipe: Unicode NFC, whitespace collapse and trim, casefold, a second NFC
normalization, mapping of Unicode punctuation and separator categories to ASCII spaces,
and a final whitespace collapse and trim. Stored `ObservedTextV1.value` and segment
text are never changed.

Each Vision label or relation predicate is matched as an exact contiguous
`WHOLE_TOKEN_SEQUENCE` in that segment's match-view tokens. The source segment
`index` is the canonical `segment_index`; T4 rejects duplicate indexes. A hit records
the exact internal coordinate `(segment_index, claim_start, claim_end)`, with an
inclusive start and exclusive end relative to that segment's normalized tokens.
Coordinates reset to zero for every segment, and no span crosses a segment boundary.
The source tuple order is not part of the coordinate; canonical evidence selection
uses numeric coordinate order. A short segment prefix has only the available preceding
tokens, so no negative token positions are invented.

A miss is not a conflict: a drawing may contain a Vision observation that narration
does not mention. A narration-only phrase has no counterpart to conflict with.
Ambiguous Vision regions are not candidates and are omitted from T4 observations;
their source-result reference/digest is retained at the result level only.

### Exact negation behavior

After an entity, action, or relation claim span has already matched, inspect exactly
the three match-view tokens immediately preceding `claim_start` in that same segment.
A cue must fit entirely inside that prefix. The exact six cue sequences after match-view
normalization are `("not",)`, `("no",)`, `("never",)`, `("isn", "t")`,
`("doesn", "t")`, and `("didn", "t")`. ASCII and curly apostrophes are punctuation
and therefore produce the split forms.

There is no sentence tokenizer and no sentence-boundary rule: punctuation becomes a
space and cannot stop or extend a window. A cue outside the exact three-token window,
a partial cue sequence, a cue associated with another claim span, a cue in another
segment, or a cue with no Vision counterpart produces no conflict. Sarcasm, indirect
negation, distant scope, coreference, synonym/antonym contradiction, and general
semantic contradiction are out of scope.

### Multi-span rule

Every valid occurrence is classified independently as positive or refuting. Exact
duplicate coordinate tuples are deduplicated once; distinct overlapping spans remain
distinct. For one candidate, select the lowest unique coordinate tuple independently
from the positive set and the refuting set. Multiple segments or spans produce at most
one corroboration increment.

When positive and refuting spans both exist, support remains true with the canonical
positive reference, one contradiction is emitted with the canonical refuting
reference, and adjustment plus primary eligibility are suppressed. Support and
contradiction references contain coordinates only, never transcript text.

## Weighting and uncertainty

### Primary interpretation

Support can select `primary_interpretation` only among already-agreeing,
non-conflicting candidates. It cannot remove a source candidate, mutate its
label, change a source confidence, suppress a conflict, or create a narration
candidate. Grouping uses candidate kind, normalized match-view claim, and structural
references. Within each group, rank eligible candidates by positive support first,
original finite source confidence descending with null after all finite values, and
stable source observation ID ascending as the final tie-break for every remaining tie.
Source input order is never a tie-break. Conflicting candidates and themes cannot be
primary; if no candidate is eligible, the group has zero primaries.

### Certainty states

```text
P2T4UncertaintySummaryV1:
  formula_id: Literal["AGREEMENT_WEIGHTED_V1"]
  per_observation: tuple[ObservationUncertaintyV1, ...]

ObservationUncertaintyV1:
  observation_id: str
  candidate_kind: Literal["ENTITY", "ACTION", "RELATION"]
  certainty_status: Literal[
    "MEASURED",
    "NOT_MEASURED",
    "NOT_APPLICABLE_CONFLICTING"
  ]
  certainty: float | None
```

`per_observation` contains exactly one row for every fused entity, action, and
relation, regardless of state. Themes have no certainty row because they are
vision-only pass-through observations.

The source vision confidence is the only numeric base. T4 never invents a base
value or rewrites source confidence:

- Numeric confidence with no support: `MEASURED`, certainty equals the source
  confidence.
- Numeric confidence with support and no conflict: `MEASURED`, certainty equals
  source confidence plus `Decimal("0.10")`, capped at `1.0`, applied once per candidate;
  the policy contract/hash stores the exact string `"0.10"`.
- Null source confidence: `NOT_MEASURED`, certainty null, whether or not support
  exists. Support fields remain true/populated when a match occurred.
- Conflict participant: `NOT_APPLICABLE_CONFLICTING`, certainty null.

`LOW_CONFIDENCE_EVIDENCE` is emitted only when a measured numeric confidence is
strictly below `confidence_floor`. A measured candidate is any entity, action,
relation, or theme with a finite numeric Vision confidence. A low-confidence theme
may emit this evidence conflict with a null narration reference; it remains
Vision-only, has no certainty row, and never enters primary ranking. Null is not
below the floor and never becomes numeric low confidence merely because it is null.

## Provenance, privacy, and source preservation

Every fused result retains pointers to the exact ASR and vision result artifacts,
the correlation ID, execution time, and the complete fusion-policy hash. Source
vision observation IDs and source text remain traceable. Original media and raw
transcript content are not copied into derived evidence when a pointer is
sufficient.

No field at any nesting level may express personality, diagnosis, mental state,
trauma, developmental inference, or another psychological claim. No free-form
provider payload, prompt, credential, endpoint, raw child media, or personal data
may cross the approved boundary.

## Fixture and contract-test plan

The following cases are the minimum future fixture set for the seven-file offline
core, after the owner freeze decision and separate T4 implementation approval.
They are synthetic and run without a model, GPU, network, mobile app, API, database,
queue, or live provider. They are fusion/core input cases, not B0 mapping cases.

1. Agreement: a Vision entity/action/relation is matched by narration, canonical
   segment/claim refs are populated, primary selection is deterministic, and the
   one-time string `"0.10"` increment uses approved Decimal arithmetic and the `1.0` cap.
2. Audio-only assertion: narration mentions a concept absent from Vision; no
   narration-only candidate and no conflict are produced.
3. Image-only assertion: Vision produces a candidate absent from narration; the
   candidate is retained without support and without a conflict.
4. Entity, action, and relation negation using each exact cue and three-token window.
5. Cue outside the exact window, partial cue, short segment prefix, and no-sentence-
   boundary cases produce no out-of-scope conflict.
6. Separate segments reset token coordinates and windows; a claim cannot cross a
   segment boundary; changing `transcript_raw` does not change matching, coordinates,
   support, conflicts, or uncertainty (the source-artifact digest may change because it
   binds the validated source artifact).
7. Duplicate normalized labels preserve distinct source IDs; duplicate coordinate
   spans deduplicate; distinct overlapping spans remain distinct.
8. Mixed positive and refuting spans retain support and canonical positive/refuting
   refs while suppressing adjustment and primary eligibility.
9. Negation with no Vision counterpart produces no conflict.
10. Measured confidence below, at, and above the configured floor; null confidence
    without and with support remains `NOT_MEASURED` with null certainty.
11. Stable primary ranking proves finite confidence before null and source observation
    ID as the final tie-break for equal support/confidence, including null ties.
12. Ambiguous Vision regions are omitted from fused observations and only the canonical
    source-result reference/digest remains.
13. ASR typed failure: `UPSTREAM_FAILURE`, ASR reference populated, Vision reference
    null, and all fused collections plus uncertainty rows empty.
14. Vision typed failure: `UPSTREAM_FAILURE`, Vision reference populated, ASR reference
    null, and all fused collections plus uncertainty rows empty.
15. Both typed failures: `UPSTREAM_FAILURE`, both references populated, and all fused
    collections plus uncertainty rows empty.
16. Empty successful inputs produce `FUSED` with empty collections and no failure ref.
  17. Unknown input, wrong family (including `FEAT018.LiveAsrResultV1@1.0` and
     `FEAT018.LiveVisionUnderstandingResultV1@1.0`), unsupported version, invalid
     discriminator, malformed structure, correlation mismatch, non-finite confidence,
     naive datetime, duplicate `AsrSegmentV1.index` after strict upstream validation,
     exact `ADMISSIBILITY`/`INVALID_STRUCTURE`/`ASR`/`DUPLICATE_SEGMENT_INDEX` rejection,
     ASR-before-Vision slot precedence, and terminal-precedence rejection cases.
18. Canonical round-trip/determinism, exact datetime/enum/tuple/null/float encoding,
    array sort keys, exact conflict-ID NUL bytes and lowercase SHA-256, source/reference
    integrity, independent hand-authored schema parity, and privacy sentinels.

No fixture may construct or assert a third fused-result status. Structural identity,
version, strict-validation, admissibility, correlation, and privacy rejection cases belong
to the T4 input-rejection family in the future core fixture set. The duplicate-index case
must prove that a strictly valid `AsrSuccessV1` reaches the T4 admissibility stage, while a
strict-validation failure in the ASR slot terminates before admissibility and before Vision.
The canonical narration-reference cases must deduplicate identical coordinate tuples before
independently selecting earliest positive/refuting references, and must produce the same result
regardless of source tuple traversal order. The existing B0
reconciliation mapping fixture remains immutable and is not copied into or expanded
by the T4 implementation proposal.

## Implementation slices after approval

1. Record the owner freeze decision for `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md`; the
   completed independent technical and governance reviews remain evidence, and the B0
   mapping remains `PROPOSED_NOT_ADOPTED` and is not a prerequisite implementation module
   or test case in this core direction.
2. Obtain a separate approval naming exactly the seven future offline implementation
   paths and no broader runtime or integration scope.
3. Implement the pure deterministic per-segment support/refute matcher, canonical
   coordinate/reference handling, primary-only weighting, and uncertainty calculation
   only after that approval.
  4. Implement the exact bounded negation conflicts, mixed-span truth table, ASR
     admissibility rejection, and the minimum fusion/core input fixture set above. Preserve
     all source observations and conflict references without adding a mapping adapter or
     preservation envelope.
  5. Add round-trip, deterministic canonical serialization, exact conflict-ID bytes,
     provenance, reference-integrity, conditional-failure, duplicate-index admissibility,
     coordinate-deduplication/source-order-independence, privacy-sentinel, and independently
     hand-authored schema-parity tests. Run them with no model or network.
6. Bind the source commit, freeze/package digest, dependency/lock hash, fixture
   manifest/cases/expected SHA-256 values, and final evidence SHA-256 value before the
   separate implementation gate is closed.
7. Publish any Integration Sprint compatibility note only under a separately approved
   integration allocation. P2-T5 remains a separate downstream task.

No implementation item in this section is currently authorized. The completed B0
package and this remediation are documentation-only; mapping adoption, migration,
registry cutover, runtime wiring, and fusion implementation remain separately gated.

## Dependency graph and gates

```text
P2-T2 validated ASR + P2-T3 validated vision
                 |
                 v
  B0 reconciliation plan and producer/consumer inventory
                 |
                 v
  docs-only seven-file reissue and freeze draft
                 |
                 v
  owner freeze decision and separate T4 implementation approval
                 |
                 v
  deterministic seven-file T4 implementation and fixture/test evidence
                 |
                 v
  P2-T5 CLI/evaluation (separate approval)
```

The B0 documentation-only reconciliation package is complete, but its proposed
mapping is not adopted. The seven-file direction and freeze draft are also only
documentation/proposal artifacts. Every downstream arrow after B0 remains gated until
the owner freeze decision and the required separate implementation approval exist.
P2-T2 and P2-T3 remain independently owned and
independently validated; T4 does not create a live dependency on either provider.

## Exit criteria

- [x] All nine owner decisions are recorded as design choices in `DECISIONS.md`
      and this plan.
- [x] B0 direction is Option 3; the approved documentation-only reconciliation
      package is complete and records a proposed mapping without adoption.
- [x] Active proposed `P2T4FusedResultV1` statuses are exactly `FUSED | UPSTREAM_FAILURE`.
- [x] The active v1 plan contains no third status, no dead structural-failure
      payload, and no fixture or implementation slice for one.
- [x] `upstream_failure` is non-null exactly for `UPSTREAM_FAILURE` and null for
      `FUSED`; upstream-failure fixtures preserve empty fused collections.
- [x] The exact six-token lexicon and exact three-match-view-token window are
      recorded; broader contradiction mechanisms are excluded.
- [x] The corroboration increment is exactly `0.10`, once per supported
      non-conflicting candidate, capped at `1.0`.
- [x] Null source confidence remains `NOT_MEASURED` with null certainty even
      when narration support exists; support provenance remains present.
- [x] `AGREEMENT_WEIGHTED_V1`, support-only narration, vision-only themes, and
      primary-only weighting are recorded with their boundaries.
- [x] The proposed B0 mapping remains explicitly `PROPOSED_NOT_ADOPTED`; mapping,
      compatibility, migration, rollback, and downstream acceptance remain deferred
      and are not prerequisites for this T4 owner-freeze decision.
- [x] The active output identity is `P2T4.P2T4FusedResultV1@1.0`; former Raw wording
      is historical only and the exact FEAT-018 live rejection identities are recorded.
- [x] Per-segment matching, canonical coordinates, duplicate/multi-span behavior,
      mixed-span suppression, null ranking, canonical bytes/IDs, evidence binding,
      and independent schema parity are recorded in the freeze draft.
- [x] The current `AsrSuccessV1` duplicate-index allowance is separated from the T4
      admissibility invariant: all `AsrSegmentV1.index` values MUST be unique, with the
      closed-field terminal rejection and ASR-before-Vision precedence recorded.
- [x] Vision V1 global `observation_id` uniqueness is attributed to
      `_validate_observation_references`; no redundant T4 Vision rule or owner decision is
      introduced.
- [x] Canonical narration references use exact `(segment_index ASC, claim_start ASC,
      claim_end ASC)` ordering, deduplicate identical tuples before independent positive/
      refuting selection, and are source-traversal-order independent.
- [ ] The proposed T4 contract receives the separate owner freeze decision.
- [ ] The seven-file T4 implementation scope receives separate approval in the
      authoritative approval record.
- [x] The 2026-09-14 docs-only remediation reissues the future scope as exactly seven
      offline paths and explicitly removes mapping/preservation-envelope implementation
      from that scope.
- [x] `P2_T4_CONTRACT_FREEZE_DRAFT.md` completed the post-sync upstream reconciliation and
      confirmed-blocker remediation review; it is owner-freeze-ready, remains a draft, and is
      not itself the approval.
- [ ] Pure fusion implementation, fixture tests, and feature-local evidence are
      completed under that separate approval.
- [ ] P2-T5 cites the compatible T4 output only after the T4 gate is complete.

## Current gate status - 2026-09-14

The owner decisions and the explicit remediation selections are recorded, and the
approved B0 documentation-only reconciliation package is complete. Its mapping remains
`PROPOSED_NOT_ADOPTED`; mapping adoption is deferred and is not required for the T4 core
freeze decision. `approvals/TASK_APPROVAL.md` records the bounded docs-only reissue, while
contract freeze, migration, registry cutover, runtime wiring, P2-T4 fusion
implementation, and integration remain **NOT APPROVED**.

The exact current next action is the separate owner freeze decision for the synchronized P2-T4
draft. A separate seven-file implementation approval is still required afterward. No T4
contract or code is treated as canonical by this package.

The post-remediation technical/contract and governance/security/scope audits both passed. They
verified the exact repo-root-qualified fixture paths, ASR admissibility and closed rejection
semantics, terminal precedence and canonical reference determinism, upstream Vision uniqueness
ownership, the seven-document edit boundary, future-path absence, and preservation of B0 and
deferred implementation/integration gates.

- The feature-local implementation-approval package draft is
  evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md. It is
  `DRAFT - READY FOR OWNER FREEZE DECISION`, NOT AN IMPLEMENTATION APPROVAL, and NOT A
  RUNTIME AUTHORIZATION; it records the reissued seven-file direction without changing
  the mapping status, contract freeze, registry, runtime, or implementation approval
  boundary.
- The companion `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` has the same owner-freeze-ready status
  and is a proposed normative review artifact, not an approved contract or runtime
  authorization. The exact future fixture paths are the three repo-root-qualified paths
  recorded in the freeze draft and package; no artifact exists yet.

## Historical audit record - not active v1 semantics

This appendix preserves the material history of the earlier draft without making
it part of the current contract:

- On 2026-09-12 the draft identified the cross-feature identity collision, missing
  candidate/reference definitions, uncertainty-state ambiguity, and incomplete
  upstream-failure detail. Those findings motivated the separate B0 workstream.
- The earlier draft used a three-value result-status sketch and described a
  possible structural-failure outcome. That text is historical only. The
  2026-09-13 B5 decision removes `NOT_FUSIBLE` from active v1; the current
  statuses are only `FUSED | UPSTREAM_FAILURE`.
- The earlier draft left the corroboration amount, negation-window size, and
  cue content as owner decisions. The 2026-09-13 decisions fixed them at
  `0.10`, exactly three match-view tokens, and the exact six-cue list recorded
  above.
- Earlier review passes clarified that upstream failure is a top-level typed
  outcome, that null confidence is not numeric low confidence, and that support
  does not erase source evidence. Those clarifications are now active rules.
- The 2026-09-10 proposal note and 2026-09-11 pipeline recap remain ignored local
  context. They are not approval records or canonical evidence.

No historical text authorizes implementation, migration, integration, or a
change to `TASK_APPROVAL.md`.
