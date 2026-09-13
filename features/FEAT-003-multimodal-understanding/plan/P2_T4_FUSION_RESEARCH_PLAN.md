# P2-T4 multimodal fusion and conflict detection research plan

- Status: **DRAFT - OWNER DECISIONS RECORDED - B0 RECONCILIATION PACKAGE COMPLETE - OWNER CONFIRMATION/ADOPTION PENDING - T4 IMPLEMENTATION NOT APPROVED**
- Decision date: 2026-09-13
- Owner: Person 2
- Parent plan: `PLAN.md`, revision 4, task P2-T4
- Input dependency: validated P2-T2 `AsrResultV1` and P2-T3
  `VisionUnderstandingResultV1` results. The contract identities are subject to the
  separately scoped Blocker-0 reconciliation described below.
- Output boundary: a versioned raw-understanding proposal for Gate A/P1. It is never
  canonical meaning, a Gate A decision, or session/job state.
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
follow-up implementation approval remain pending. Contract freeze, migration,
schema replacement, registry cutover, runtime wiring, FEAT-018 changes, and P2-T4
fusion implementation remain separately gated.

`approvals/TASK_APPROVAL.md` remains unchanged. It authorizes the bounded P2-T4
Blocker-0 documentation/reconciliation scope but still excludes P2-T4 fusion
implementation and P2-T5. No P2-T4 schema, fusion code, migration execution,
registry cutover, runtime wiring, provider call, GPU/model work, or FEAT-018 change
exists or is authorized from this plan; the additive metadata-only reconciliation
fixture is the sole B0 fixture output.

The active v1 design choices are:

- `RawUnderstandingResultV1.status` contains only `FUSED` and
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
- The entire workstream remains `NOT APPROVED` for implementation.

## Research question

Can a pure, deterministic, model-free fusion layer combine already-typed ASR and
vision results while preserving every disagreement and never fabricating a claim
that neither modality produced? T4 consumes validated provider-neutral result
objects. It does not call a model, provider, network, GPU, or live service.

The research output is a contract-and-policy design plus a fixture/test plan. The
contract identity and cross-feature mapping cannot be frozen until the separately
approved B0 reconciliation resolves the existing same-name contract families.

## Scope and explicit non-goals

### In scope after the required approvals

- A versioned deterministic fusion policy configuration.
- A versioned raw-understanding result with source references, fused observations,
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

1. FEAT-018's provider-shaped `AsrResultV1`, `VisionUnderstandingResultV1`, and
   claims-shaped `RawUnderstandingResultV1`, used by the live route, adapters,
   tests, contract freeze, and FEAT-015 integration fixture.
2. P2-T2/P2-T3's provider-neutral discriminated `AsrResultV1` and
   `VisionUnderstandingResultV1`, plus this plan's proposed fusion result, which
   use different fields, discriminators, provenance, and failure semantics.

The owner selected **B0 Option 3**. The approved documentation-only reconciliation
package records the proposed explicit mapping and its compatibility/migration
fixture, while owner confirmation/adoption remains pending. This plan therefore
treats every T4 result sketch below as a reconciliation input, not a frozen public
contract or an adopted runtime shape.

The full bounded workstream is in
`plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md`. It inventories both families,
their producers and consumers, the Gate A/P1 and integration registry impacts,
the migration/rollback requirements, and the validation gates. Its approved
documentation-only package is complete; owner confirmation/adoption and separate
T4 implementation approval are still required before any contract freeze or
implementation starts.

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
conflicts. Weighting never runs as a way to suppress a conflict. Any tie behavior
must be deterministic and explicitly testable; no new ranking signal is added.
An implementation may use stable source order solely to make an existing tie
reproducible, not to introduce another score.

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
FusionPolicyConfigV1:
  contract_name: Literal["FusionPolicyConfigV1"]
  contract_version: Literal["1.0"]
  config_version: str
  entity_match_mode: Literal["WHOLE_TOKEN_SEQUENCE"]
  narration_weight_mode: Literal["SUPPORT_ONLY"]
  confidence_floor: float                 # 0.0..1.0
  uncertainty_formula_id: Literal["AGREEMENT_WEIGHTED_V1"]
```

The hash is SHA-256 over the complete canonical configuration serialization,
using sorted keys and compact separators. The finalized reconciled configuration
must also make the exact negation lexicon identity and exact three-token window
traceable and hash-comparable. This plan does not invent a new field name or
choose where a compatibility mapping carries those values; that is part of the
B0 field-by-field review.

### Raw result baseline

```text
RawUnderstandingResultV1:
  contract_name: Literal["RawUnderstandingResultV1"]
  contract_version: Literal["1.0"]
  correlation_id: str
  executed_at: datetime
  source_asr_result_ref: str
  source_vision_result_ref: str
  fusion_policy_config_hash: str
  status: Literal["FUSED", "UPSTREAM_FAILURE"]
  entities: tuple[FusedEntityV1, ...]
  actions: tuple[FusedActionV1, ...]
  relations: tuple[FusedRelationV1, ...]
  themes: tuple[FusedThemeV1, ...]
  conflicts: tuple[ConflictV1, ...]
  uncertainty: UncertaintySummaryV1
  upstream_failure: UpstreamFailureRefV1 | None
```

The active status set has exactly two members. `UPSTREAM_FAILURE` is used when
one or both validated upstream result objects is a typed failure; fusion does not
run on absent/failed input. `FUSED` is used when both upstream results succeed,
including an empty but schema-valid collection set. `upstream_failure` is
non-null exactly for `UPSTREAM_FAILURE` and null for `FUSED`.

An `UPSTREAM_FAILURE` result has empty `entities`, `actions`, `relations`,
`themes`, and `conflicts`. It carries only the typed failure references needed to
identify the failed modality; it never copies provider output or a free-form
failure message.

### Typed upstream-failure references

```text
UpstreamFailureRefV1:
  contract_name: Literal["UpstreamFailureRefV1"]
  contract_version: Literal["1.0"]
  failed_modality: Literal["ASR", "VISION", "BOTH"]
  asr_failure_ref: AsrFailureReferenceV1 | None
  vision_failure_ref: VisionFailureReferenceV1 | None

AsrFailureReferenceV1:
  source_asr_result_ref: str
  error_code: AsrErrorCode
  error_detail: AsrErrorDetail
  attempt_number: int

VisionFailureReferenceV1:
  source_vision_result_ref: str
  error_code: VisionErrorCode
  error_detail: VisionFailureDetail
  attempt_number: int
```

`failed_modality` determines the populated sub-reference structurally:

- `ASR`: ASR failed and vision succeeded; ASR reference populated, vision
  reference null.
- `VISION`: vision failed and ASR succeeded; vision reference populated, ASR
  reference null.
- `BOTH`: both upstream results failed; both references populated.

The references carry closed identifiers and pointers only. They carry no raw
provider output, prompt, endpoint, or free-form message.

### Fused candidate baseline

Each fused candidate wraps exactly one source vision observation. T4 does not
merge distinct vision observations, even when their normalized labels match.

```text
FusedEntityV1:
  fused_observation_id: str
  source_observation_ref: str
  label: ObservedTextV1
  narration_support_applied: bool
  narration_support_ref: str | None
  primary_interpretation: bool

FusedActionV1:
  fused_observation_id: str
  source_observation_ref: str
  label: ObservedTextV1
  actor_ref: str | None
  object_ref: str | None
  narration_support_applied: bool
  narration_support_ref: str | None
  primary_interpretation: bool

FusedRelationV1:
  fused_observation_id: str
  source_observation_ref: str
  predicate: ObservedTextV1
  subject_ref: str
  object_ref: str
  narration_support_applied: bool
  narration_support_ref: str | None
  primary_interpretation: bool

FusedThemeV1:
  fused_observation_id: str
  source_observation_ref: str
  label: ObservedTextV1
  evidence_refs: tuple[str, ...]
```

Every reference resolves to a fused observation in the same raw result. Labels
and predicates are copied byte-for-byte from the source vision observation;
T4 does not translate, re-normalize, or edit vision-produced text. Support
references point to transcript segment/index data without copying raw transcript
text into the fused object.

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
ConflictV1:
  conflict_id: str
  reason_code: ConflictReasonCode
  vision_claim_ref: str | None
  narration_claim_excerpt_ref: str | None
  recommended_reviewer_attention: bool
```

`recommended_reviewer_attention` is deterministic: every emitted conflict is
marked for reviewer attention, and no record is emitted for a non-conflict case.
Both claims remain available through their source pointers. A conflict is never
removed or downgraded by weighting.

## Matching and contradiction policy

### Support-only matching

The transcript and its segments are a support/refute signal against vision
entities, actions, and relation predicates. Narration never creates an
independent entity/action/relation/theme collection.

The derived in-memory match view follows the P2-T3 recipe: Unicode NFC,
whitespace collapse and trim, casefold, a second NFC normalization, mapping of
Unicode punctuation and separator categories to ASCII spaces, and a final
whitespace collapse and trim. The stored `ObservedTextV1.value` is never changed.

Each vision label or relation predicate is matched as an exact contiguous
`WHOLE_TOKEN_SEQUENCE` in the transcript match-view. A hit records
`narration_support_applied=true` and a segment/index reference. A miss is not a
conflict: a drawing may contain a vision observation that narration does not
mention. A narration-only phrase has no counterpart to conflict with.

### Exact negation behavior

After an entity, action, or relation claim span has already matched in the
transcript match-view, inspect exactly the three match-view tokens immediately
preceding the start of that span. Consult only the exact six-token cue list:
`not`, `no`, `never`, `isn't`, `doesn't`, `didn't`.

If a cue is present in that exact window, reclassify the support match as a
conflict using the corresponding reason code. A cue outside the window, a cue
associated with another span, or a cue with no vision counterpart produces no
conflict. The policy does not attempt sarcasm, indirect negation, distant scope,
coreference, synonym/antonym contradiction, or general semantic contradiction.

Multiple transcript segments matching one candidate still produce one
corroboration increment and deterministic support provenance; they do not stack
the increment. The fixture/test plan must assert the deterministic handling of
multiple spans without widening the cue scope.

## Weighting and uncertainty

### Primary interpretation

Support can select `primary_interpretation` only among already-agreeing,
non-conflicting candidates. It cannot remove a source candidate, mutate its
label, change a source confidence, suppress a conflict, or create a narration
candidate. Equal cases use a deterministic, explicitly tested stable rule and
introduce no extra ranking signal.

### Certainty states

```text
UncertaintySummaryV1:
  formula_id: Literal["AGREEMENT_WEIGHTED_V1"]
  per_entity: tuple[EntityUncertaintyV1, ...]

EntityUncertaintyV1:
  observation_id: str
  certainty_status: Literal[
    "MEASURED",
    "NOT_MEASURED",
    "NOT_APPLICABLE_CONFLICTING"
  ]
  certainty: float | None
```

`per_entity` contains exactly one row for every fused entity, action, and
relation, regardless of state. Themes have no certainty row because they are
vision-only pass-through observations.

The source vision confidence is the only numeric base. T4 never invents a base
value or rewrites source confidence:

- Numeric confidence with no support: `MEASURED`, certainty equals the source
  confidence.
- Numeric confidence with support and no conflict: `MEASURED`, certainty equals
  source confidence plus `0.10`, capped at `1.0`, applied once per candidate.
- Null source confidence: `NOT_MEASURED`, certainty null, whether or not support
  exists. Support fields remain true/populated when a match occurred.
- Conflict participant: `NOT_APPLICABLE_CONFLICTING`, certainty null.

`LOW_CONFIDENCE_EVIDENCE` is emitted only when a measured numeric confidence is
strictly below `confidence_floor`. Null is not below the floor and never becomes
numeric low confidence merely because it is null.

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

The following cases are the minimum fixture set after the reconciliation and T4
implementation approvals. They are synthetic and run without a model, GPU,
network, mobile app, API, database, queue, or live provider.

1. Agreement: a vision entity/action/relation is matched by narration, support
   refs are populated, primary selection is deterministic, and certainty applies
   the one-time `0.10` increment with the `1.0` cap.
2. Audio-only assertion: narration mentions a concept absent from vision; no
   narration-only candidate and no conflict are produced.
3. Image-only assertion: vision produces a candidate absent from narration; the
   candidate is retained without support and without a conflict.
4. Entity negation contradiction using each exact cue/window rule as applicable;
   only an already-matched entity span can produce the entity reason code.
5. Action negation contradiction using the exact same bounded rule.
6. Relation negation contradiction using the exact same bounded rule.
7. Cue outside the exact three-token window: no conflict.
8. Negation with no vision counterpart: no conflict.
9. Low-confidence measured value below, at, and above the configured floor.
10. Duplicate normalization: two distinct source observation IDs remain two
    fused candidates; no merge is performed.
11. Null vision confidence without support: `NOT_MEASURED`, null certainty.
12. Null vision confidence with support: still `NOT_MEASURED`, null certainty,
    with support boolean/reference preserved.
13. Multiple transcript matches for one candidate: one increment only and stable
    support reference behavior.
14. ASR typed failure: `UPSTREAM_FAILURE`, ASR reference populated, vision
    reference null, all fused collections and conflicts empty.
15. Vision typed failure: `UPSTREAM_FAILURE`, vision reference populated, ASR
    reference null, all fused collections and conflicts empty.
16. Both typed failures: `UPSTREAM_FAILURE`, both references populated, all
    fused collections and conflicts empty.
17. JSON-Schema/Pydantic round-trip, byte-identical repeated serialization,
    source-reference/provenance integrity, candidate-reference integrity,
    uncertainty-row completeness, conditional upstream-reference validation,
    and prohibited-field rejection.

No fixture may construct or assert a third raw-result status. A structural
contract mismatch is tested through the separately approved reconciliation
mapping/validation fixture, not by adding another P2-T4 v1 status here.

## Implementation slices after approval

1. Obtain owner confirmation/adoption for the completed B0 reconciliation. Confirm
   the proposed explicit versioned mapping, preservation mechanism, ownership, and
   consumer behavior; the existing synthetic compatibility fixture remains
   additive and unchanged. This plan's candidate fields are inputs to that review,
   not a preselected shape.
2. Freeze the reconciled T4 contract/config identities and acceptance rules in a
   versioned record. Confirm that the exact cue list, exact three-token window,
   policy provenance, and hash representation are compatible with the selected
   mapping.
3. Implement the pure deterministic support/refute matcher, candidate reference
   mapping, primary-only weighting, and uncertainty calculation.
4. Implement the exact bounded negation conflicts and the minimum fixture set
   above. Preserve all source observations and conflict references.
5. Add round-trip, deterministic serialization, provenance, reference-integrity,
   conditional-failure, and prohibited-field tests. Run them with no model or
   network.
6. Publish a compatibility note for the Integration Sprint only after the
   reconciled contract and fixtures have passed review. P2-T5 remains a separate
   downstream task.

No implementation item in this section is currently authorized. The completed B0
package is documentation-only; contract adoption, migration, registry cutover,
runtime wiring, and fusion implementation remain separately gated.

## Dependency graph and gates

```text
P2-T2 validated ASR + P2-T3 validated vision
                 |
                 v
  B0 reconciliation plan and producer/consumer inventory
                 |
                 v
  separate reconciliation approval and migration fixture
                 |
                 v
  reconciled T4 contract/config review and separate T4 approval
                 |
                 v
  deterministic T4 implementation and fixture/test evidence
                 |
                 v
  P2-T5 CLI/evaluation (separate approval)
```

The B0 documentation-only reconciliation package is complete, but its proposed
mapping is not adopted. Every downstream arrow after B0 remains gated until owner
confirmation/adoption and the required separate approval exist. P2-T2 and P2-T3
remain independently owned and independently validated; T4 does not create a
live dependency on either provider.

## Exit criteria

- [x] All nine owner decisions are recorded as design choices in `DECISIONS.md`
      and this plan.
- [x] B0 direction is Option 3; the approved documentation-only reconciliation
      package is complete and records a proposed mapping without adoption.
- [x] Active v1 raw-result statuses are exactly `FUSED | UPSTREAM_FAILURE`.
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
- [ ] The proposed B0 mapping is confirmed and approved for adoption, or a
      canonical identity/shape is separately selected and approved.
- [ ] Compatibility, migration, rollback/non-adoption, and downstream acceptance
      fixtures are reviewed and pass.
- [ ] The reconciled T4 contract and implementation scope receive separate
      approval in the authoritative approval record.
- [ ] Pure fusion implementation, fixture tests, and feature-local evidence are
      completed under that separate approval.
- [ ] P2-T5 cites the compatible T4 output only after the T4 gate is complete.

## Current blocking status - 2026-09-13

The owner decisions are complete as design choices, and the approved B0
documentation-only reconciliation package is complete. Its mapping remains
PROPOSED_NOT_ADOPTED; owner confirmation of source preservation and any adoption
or follow-up implementation approval remain pending. `approvals/TASK_APPROVAL.md`
remains unchanged: it approves only the bounded B0 documentation/reconciliation
scope, while contract freeze, migration, registry cutover, runtime wiring,
P2-T4 fusion implementation, and integration remain **NOT APPROVED**.

The exact current next action is owner confirmation/adoption of the proposed
mapping and preservation mechanism, followed by separate approval for any T4
contract freeze or implementation. No T4 contract or code is treated as
canonical by this package.

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
