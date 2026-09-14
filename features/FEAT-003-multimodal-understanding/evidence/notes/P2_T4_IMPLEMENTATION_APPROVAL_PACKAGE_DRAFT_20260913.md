# FEAT-003 P2-T4 contract-freeze and conditional implementation-approval package (draft)

DRAFT

NOT AN IMPLEMENTATION APPROVAL

NOT A RUNTIME AUTHORIZATION

BLOCKED_PENDING_CONTRACT_FREEZE

- Package ID: EV-003-T4-IMPL-APPROVAL-DRAFT-01
- Revision: 3 (see §9 revision history)
- Date: 2026-09-13
- Prepared by: Person 2 workstream, in the existing P2-T4 worktree
- Feature-local evidence location: FEAT-003 multimodal understanding
- Governing plan: features/FEAT-003-multimodal-understanding/plan/P2_T4_FUSION_RESEARCH_PLAN.md
- Governing reconciliation plan: features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md
- Mapping status: PROPOSED_NOT_ADOPTED (unchanged; B0 manifest
  `fixtures/p2-t4-contract-reconciliation-v1/manifest-v1.json` lines 100-106,
  registry_cutover_applied=false, runtime_mapping_applied=false)

This package is a review input for later owner decisions. It is split into two
explicit stages:

- **Stage A — contract-freeze/design stage.** It proposes a T4-owned result
  contract, a namespaced input preservation envelope, a failure/retry rule set,
  and edge dispositions. Every Stage A item is `PROPOSED_REQUIRES_OWNER_APPROVAL`
  and every Stage A decision in §3.8 is OPEN.
- **Stage B — conditional offline implementation stage.** It lists an exact
  9-file additive offline scope that cannot be approved, started, or partially
  started until every Stage A decision is recorded by the owner through the
  required approval process and a versioned contract-freeze record exists.

The package status is `BLOCKED_PENDING_CONTRACT_FREEZE`. Describing a type in
prose below does not freeze it, make it canonical, place it in
`backend/src/sketch2life/contracts/schemas/`, or make Stage B implementation-ready.
No implementation, schema, fixture, registry, approval, or runtime action is taken
by this document.

## 0. Stage model and status

| Stage | Content | Status | Exit condition |
|---|---|---|---|
| A. Contract freeze/design | §3: proposed `P2T4FusedResultV1` family, proposed `P2T4LiveInputPreservationEnvelopeV1`, failure/retry rules, session deferral, edge dispositions, decision register D-A0 to D-A10 | OPEN; `BLOCKED_PENDING_CONTRACT_FREEZE` | Owner records every D-A decision in the authoritative approval process; a versioned freeze record exists; this package is re-issued against that record |
| B. Conditional offline implementation | §4: exact 9 additive files, conditional per file on named Stage A decisions and on ADR-0006 allocation for the mapping module | NOT APPROVABLE | Stage A exit plus a separately recorded implementation approval naming exactly these files |

This package does not edit `approvals/TASK_APPROVAL.md`. That record currently
approves only the bounded P2-T4 Blocker-0 reconciliation scope (lines 120-138)
and excludes P2-T4 implementation.

## 1. Authority, precedence, and ownership

### 1.1 Source precedence

1. The task brief and repository `AGENTS.md`.
2. FEAT-003 `approvals/TASK_APPROVAL.md` (Blocker-0 scope only).
3. FEAT-003 `CONTEXT.md`, `DECISIONS.md`, the P2-T4 fusion plan, and the P2-T4
   reconciliation plan.
4. The committed Blocker-0 package: reconciliation report
   (`EV-003-T4-RECON-02`), follow-up impact record, technical review, governance
   review, and the synthetic reconciliation manifest.
5. FEAT-018 `plan/CONTRACT_FREEZE.md`, `CONTEXT.md`, and `DECISIONS.md`.
6. FEAT-017 `approvals/TASK_APPROVAL.md`, `plan/PLAN.md`, `CONTEXT.md`, and
   `LIVE_AI_GUIDE.md`.
7. The committed contract modules `asr.py`, `vision.py`, `vision_v2.py`, and
   `understanding.py`, and the existing FEAT-015 fixture baseline.
8. `docs/context/SOURCE_REGISTER.md` for provenance/context only.

Local-only working records (including the 2026-09-13 independent review whose
finding IDs B1-B3 and M1-M4 this revision answers) are not authority and are not
linked, consistent with FEAT-003 `CONTEXT.md` lines 5-8.

### 1.2 Ownership from committed records

| Surface | Owner | Committed evidence |
|---|---|---|
| P2-T2 ASR contract (`asr.py`), P2-T3 Vision V1 (`vision.py`) and the P2-T3 V2 study family (`vision_v2.py`) | FEAT-003 / Person 2 | FEAT-003 `approvals/TASK_APPROVAL.md` line 3; `DECISIONS.md` line 108 |
| P2-T4 fusion semantics and the proposed T4 contract family in §3.2 | FEAT-003 / Person 2 | FEAT-003 `DECISIONS.md` lines 3-36; P2-T4 plan lines 14-58 |
| Backend-only Lightning live producer (`infrastructure/ai/lightning_client.py`) and local live route (`interfaces/http/routers/live_understanding.py`) | FEAT-017, implemented by its allocated integration owner | FEAT-017 `approvals/TASK_APPROVAL.md` lines 7 and 10 ("integration owner implements backend adapter/route"); FEAT-017 `CONTEXT.md` line 24; FEAT-017 `plan/PLAN.md` lines 19 and 23 |
| Shared contract-freeze registry and the Gate A/P1 handoff target `RawUnderstandingResultV1` | FEAT-018 | FEAT-018 `plan/CONTRACT_FREEZE.md` lines 5-13, 25, and 48 |
| Adult confirmation, context, eligibility, catalog/objective identity | P1/Gate A | `CONTRACT_FREEZE.md` lines 26-28 |
| Integration-fixture v1 baseline | FEAT-015 | Existing FEAT-015 manifest and expected payloads (immutable) |
| Any cross-feature adapter or integration work | Requires a separately approved allocation | `AGENTS.md` lines 23-24; `docs/adr/ADR-0006-parallel-sprint-allocation.md` line 25 |

The `CONTRACT_FREEZE.md` registry "Owner" column records the role `P2` for
`AsrResultV1`, `VisionUnderstandingResultV1`, and `RawUnderstandingResultV1`
(lines 23-25). This package records that column as found and does not
reinterpret it.

**Unresolved: ownership of the flat `understanding.py` contract identity.**
Committed records disagree. `CONTRACT_FREEZE.md` lines 23-24 list owner `P2`; the
module docstring (`understanding.py` line 1) names the "Person 2 understanding
boundary"; the B0 report contract inventory (row at line 140) records
"FEAT-018/shared integration"; FEAT-017's approval allocates its adapter/route to
an integration owner. This package assigns no owner to that identity. It is open
owner decision D-A7.

### 1.3 Source-identity conclusion for the live input edges

For `feat018-live-asr-to-p2-asr` and `feat018-live-vision-v1-to-p2-vision-v1`,
each source is **one contract identity and version with multiple producers**:

- Identity: the single `AsrResultV1` class (`understanding.py` lines 75-105) and
  the single `VisionUnderstandingResultV1` class (lines 148-172), both at
  `contract_version` 1.0 (review identities `FEAT018.LiveAsrResultV1@1.0` and
  `FEAT018.LiveVisionUnderstandingResultV1@1.0`). The `FEAT018` prefix is a B0
  review namespace marker only (B0 report lines 13-15); it does not assert
  ownership.
- Producers: FEAT-017's `lightning_client.py` through `live_understanding.py`;
  `infrastructure/understanding/fixture_adapters.py`; and
  `infrastructure/understanding/qwen3_vl_adapter.py` / `whisper_adapter.py`,
  which no module in `backend/src` imports.
- FEAT-017 is a producer of this identity. It does not define a separate
  contract identity, so no edge split is required. Equivalence rests on the
  single class, not on shape similarity.
- The source identity is distinct from the P2-owned `P2.AsrResultV1@1.0`
  (`asr.py`) and `P2.VisionUnderstandingResultV1@1.0` (`vision.py`). They share
  only the serialized name and version string, the collision recorded by B0.

## 2. Mapping family and edge dispositions

### 2.1 Family identity

| Field | Value |
|---|---|
| Mapping family | P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1 |
| Mapping version | 1.0 |
| Selection | Option B: explicit versioned mapping |
| Status | PROPOSED_NOT_ADOPTED |
| Registry cutover / runtime mapping | Not applied / not applied |
| Existing-source policy | Source contracts, the B0 manifest, and fixture baselines remain immutable |

### 2.2 Edge dispositions in this package

| Edge ID | Direction | Source identity | Target identity | Disposition in this package |
|---|---|---|---|---|
| feat018-live-asr-to-p2-asr | FEAT018_TO_P2 | FEAT018.LiveAsrResultV1@1.0 (`understanding.py`) | P2.AsrResultV1@1.0 (`asr.py`) | Stage B conditional. Rejection-first. A positive admission case exists only if D-A2 and D-A3 approve the envelope and its supplier (§3.3). |
| feat018-live-vision-v1-to-p2-vision-v1 | FEAT018_TO_P2 | FEAT018.LiveVisionUnderstandingResultV1@1.0 (`understanding.py`) | P2.VisionUnderstandingResultV1@1.0 (`vision.py`) | Stage B conditional. Proposed rejection-only in v1 (D-A5): no authoritative source can supply the V1 target's profile, policy, and observation identity for a live result (§3.4). |
| p2t4-fused-design-to-feat018-raw | P2T4_TO_FEAT018 | P2-T4 fused output (now proposed as `P2T4.P2T4FusedResultV1@1.0`) | FEAT018.RawUnderstandingResultV1@1.0 (prose/registry only) | **Deferred to a separate package** (§3.7, D-A6). No field rule is proposed as admissible here, and no implementation, test, or fixture case exists in Stage B. |

The committed B0 manifest continues to list all three edges unchanged. Deferring
edge 3 from this package neither deletes nor adopts it.

### 2.3 V2 identity (deferred)

The separate real-model study family is the **P2-T3 V2 study family**
(`P2.VisionUnderstandingResultV2@2.0` and the disjoint V2 types in
`backend/src/sketch2life/contracts/schemas/vision_v2.py`), per
`plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md` lines 71, 90, and 120, the B0 report
lines 77 and 138, and FEAT-003 `DECISIONS.md` line 108. It is a P2-T3 Phase B
artifact; P2-T2 is the ASR workstream and owns no V2 vision family.

The P2-T3 V2 study family is **deferred**. It is not part of the V1 mapping
family, not an input to any edge or to the fusion service in this package, and
never name-coerced into a V1 identity. A P2-T3 V2 object at a V1 boundary is
`REJECTED_WRONG_FAMILY`.

The FEAT-015 integration fixture's compact `VisionUnderstandingResultV2` label
(`integration-fixture-v1/manifest.json` line 24) is a different, compact
fixture shape. It is neither the P2-T3 V2 study family nor a V1 input
(B0 report lines 144-148), and it is rejected by name-only matching like any
other wrong-family object.

### 2.4 Boundary rules (all stages)

- Match namespace, exact identity, exact version, edge ID, discriminator branch,
  and target version before validating or projecting fields.
- A serialized name is never evidence of compatibility.
- Every adapter is a pure, explicit operation over validated values. It reads
  or writes no registry, database, queue, session store, provider endpoint,
  network resource, or mobile state.
- A value that the declared source or an approved envelope does not supply is
  never fabricated, defaulted, inferred from a model string, derived from list
  position, or taken from mapper time. The mapping is rejected instead.
- An admissible mapping record identifies the source result digest, mapping
  family and version, edge ID, and target identity and version.
- On rejection no partial target object is emitted.

## 3. Stage A — contract-freeze/design (PROPOSED_REQUIRES_OWNER_APPROVAL)

Everything in §3 is a proposal for owner decision. Nothing in §3 is frozen,
canonical, registered, or present in source.

### 3.1 Classification vocabulary

| Classification | Rule |
|---|---|
| PRESERVE | Carry the same semantic and value exactly. |
| TRANSFORM | A deterministic, documented transformation whose input, output, and rule identity are retained. |
| RENAME | Allowed only when semantics, requiredness, units, normalization, and null behavior are identical. Same serialized names across namespaces are not a rename. |
| DEFAULT | Not allowed. A missing required value is rejected. |
| REJECT | Return a typed mapping outcome from §3.5 and emit no partial target. |
| NO_AUTHORITATIVE_SOURCE | The target requires a value that neither the declared source nor any approved envelope can truthfully supply. The field is removed from the envelope and the mapping is rejected. |
| INTENTIONALLY DROPPED | Only prohibited or ephemeral data: raw media bytes, prompts, provider SDK payloads, credentials, endpoints, personal metadata, free-form provider failure messages, and the in-memory match view. The source result digest remains traceable. |

### 3.2 Proposed T4 contract family: `P2T4FusedResultV1`

Status: `PROPOSED_REQUIRES_OWNER_APPROVAL` (decision D-A1).

**Identity.**

| Field | Proposed value |
|---|---|
| Review identity | `P2T4.P2T4FusedResultV1@1.0` |
| `contract_name` | `Literal["P2T4FusedResultV1"]` |
| `contract_version` | `Literal["1.0"]` |
| Owner | FEAT-003 / Person 2 |
| Discriminator | `status: Literal["FUSED", "UPSTREAM_FAILURE"]` |
| Planned location after freeze only | `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py` (Stage B file 1) |

This identity replaces the design-baseline name `RawUnderstandingResultV1`
used by the P2-T4 plan (lines 237-242) for the T4 output. It never reuses,
aliases, subclasses, or imports FEAT-018 `RawUnderstandingResultV1`, and it
modifies no existing schema. A read-only `git grep` at this revision found no
class, contract, or document outside this package using any `P2T4`-prefixed
type name proposed here, and no existing class named `FusionPolicyConfigV1`,
`UpstreamFailureRefV1`, `UncertaintySummaryV1`, or `ConflictV1` in `backend/src`. The
freeze record must also update the plan's baseline name through the plan's own
change process; this package does not edit the plan.

All proposed models are immutable (`frozen=True`) and reject extra fields
(`extra="forbid"`), matching the P2-T2/P2-T3 contracts. Every nested type carries
the `P2T4` prefix so that no name collides with an existing or FEAT-018 contract.

**`P2T4FusedResultV1` fields (single strict model, per owner decision B5).**

| Field | Type | Required | Source of value | Rule |
|---|---|---|---|---|
| `contract_name` | `Literal["P2T4FusedResultV1"]` | yes | constant | exact |
| `contract_version` | `Literal["1.0"]` | yes | constant | exact |
| `status` | `Literal["FUSED", "UPSTREAM_FAILURE"]` | yes | fusion service | `FUSED` iff both validated upstream results have `status="SUCCEEDED"`; otherwise `UPSTREAM_FAILURE` |
| `correlation_id` | `str` (min length 1) | yes | both validated upstream P2 results | PRESERVE. Both upstream `correlation_id` values must be equal; inequality is input rejection `REJECTED_CORRELATION_MISMATCH` and produces no T4 result (sub-decision D-A1.a) |
| `executed_at` | timezone-aware `datetime` | yes | fusion service execution time, injected as a clock dependency | T4 is the authoritative producer of its own execution time; tests inject a fixed clock |
| `source_asr_result_ref` | `P2T4SourceResultRefV1` | yes | validated upstream `P2.AsrResultV1` | digest reference, never a display label or request ID |
| `source_vision_result_ref` | `P2T4SourceResultRefV1` | yes | validated upstream `P2.VisionUnderstandingResultV1` | digest reference |
| `fusion_policy_config_hash` | `str`, pattern `^[a-f0-9]{64}$` | yes | `P2T4FusionPolicyConfigV1` | canonical hash, see below |
| `entities` | `tuple[P2T4FusedEntityV1, ...]` | yes | source vision entities | empty when `UPSTREAM_FAILURE` |
| `actions` | `tuple[P2T4FusedActionV1, ...]` | yes | source vision actions | empty when `UPSTREAM_FAILURE` |
| `relations` | `tuple[P2T4FusedRelationV1, ...]` | yes | source vision relations | empty when `UPSTREAM_FAILURE` |
| `themes` | `tuple[P2T4FusedThemeV1, ...]` | yes | source vision themes (vision-only, B4) | empty when `UPSTREAM_FAILURE` |
| `conflicts` | `tuple[P2T4ConflictV1, ...]` | yes | bounded negation and floor rules (B6) | empty when `UPSTREAM_FAILURE` |
| `uncertainty` | `P2T4UncertaintySummaryV1` | yes | certainty rules (B3a-B3c) | `per_entity` empty when `UPSTREAM_FAILURE` |
| `upstream_failure` | `P2T4UpstreamFailureRefV1 \| None` | yes (nullable) | validated upstream failure results | non-null exactly for `UPSTREAM_FAILURE`, null for `FUSED` |

Source ambiguous regions are not fused in v1 (the plan baseline defines no fused
ambiguous-region type). They remain available through the source Vision result
digest; this is recorded as sub-decision D-A1.b rather than a silent drop.

**`P2T4SourceResultRefV1`** (sub-decision D-A1.c; the plan baseline typed these
references as `str`).

| Field | Type | Rule |
|---|---|---|
| `identity` | `Literal["P2.AsrResultV1@1.0", "P2.VisionUnderstandingResultV1@1.0"]` | must match the field it occupies |
| `status` | `Literal["SUCCEEDED", "FAILED"]` | copied from the upstream result |
| `result_sha256` | `str`, pattern `^[a-f0-9]{64}$` | SHA-256 of `dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))` encoded UTF-8, the same convention as `vision_profile_config_hash` (`vision.py` lines 176-178) |

**`P2T4FusionPolicyConfigV1`** (plan lines 217-235, prefixed).

| Field | Type |
|---|---|
| `contract_name` | `Literal["P2T4FusionPolicyConfigV1"]` |
| `contract_version` | `Literal["1.0"]` |
| `config_version` | `str` (min length 1) |
| `entity_match_mode` | `Literal["WHOLE_TOKEN_SEQUENCE"]` |
| `narration_weight_mode` | `Literal["SUPPORT_ONLY"]` |
| `confidence_floor` | `float`, 0.0 to 1.0 |
| `uncertainty_formula_id` | `Literal["AGREEMENT_WEIGHTED_V1"]` |
| `negation_cues` | `tuple[str, ...]`, exactly `("not", "no", "never", "isn't", "doesn't", "didn't")` in that order (sub-decision D-A1.d) |
| `negation_window_tokens` | `Literal[3]` (sub-decision D-A1.d) |
| `corroboration_increment` | `Literal[0.10]` (sub-decision D-A1.d) |

The plan (lines 231-235) requires the cue list and window to be traceable and
hash-comparable but deliberately left the field names open. The three
sub-decision D-A1.d field names above are proposals for that gap.
`fusion_policy_config_hash` uses the canonical serialization above.

**`P2T4UpstreamFailureRefV1`** (plan lines 269-301, prefixed; sub-decision D-A1.e
adds `retryable` and `repair_attempted` so that existing source failure semantics
are preserved rather than dropped).

| Type / field | Type | Source and rule |
|---|---|---|
| `P2T4UpstreamFailureRefV1.contract_name` / `contract_version` | `Literal["P2T4UpstreamFailureRefV1"]` / `Literal["1.0"]` | constant |
| `failed_modality` | `Literal["ASR", "VISION", "BOTH"]` | `ASR`: ASR ref set, Vision ref null. `VISION`: the reverse. `BOTH`: both set |
| `asr_failure_ref` | `P2T4AsrFailureReferenceV1 \| None` | structural per `failed_modality` |
| `vision_failure_ref` | `P2T4VisionFailureReferenceV1 \| None` | structural per `failed_modality` |
| `P2T4AsrFailureReferenceV1` | `source_asr_result_ref: P2T4SourceResultRefV1`; `error_code: AsrErrorCode`; `error_detail: AsrErrorDetail`; `attempt_number: int` (0-2); `retryable: bool`; `repair_attempted: bool` | every value PRESERVED from a validated `P2.AsrFailureV1` (`asr.py` lines 330-347, 382-386) |
| `P2T4VisionFailureReferenceV1` | `source_vision_result_ref: P2T4SourceResultRefV1`; `error_code: VisionErrorCode`; `error_detail: VisionFailureDetail`; `attempt_number: int` (0-2); `retryable: bool`; `repair_attempted: bool`; `policy_execution_state: Literal["NOT_EXECUTED", "BLOCKED"]` | every value PRESERVED from a validated `P2.VisionUnderstandingFailureV1` (`vision.py` lines 317-338, 464-503) |

No free-form message, provider payload, prompt, or endpoint is carried.

**Fused candidates** (plan lines 303-348, prefixed). Each wraps exactly one source
vision observation; distinct source observations are never merged.

| Type | Fields |
|---|---|
| `P2T4FusedEntityV1` | `fused_observation_id: str`; `source_observation_ref: str`; `label: ObservedTextV1`; `narration_support_applied: bool`; `narration_support_ref: str \| None`; `primary_interpretation: bool` |
| `P2T4FusedActionV1` | same as entity plus `actor_ref: str \| None`; `object_ref: str \| None` |
| `P2T4FusedRelationV1` | `fused_observation_id`; `source_observation_ref`; `predicate: ObservedTextV1`; `subject_ref: str`; `object_ref: str`; `narration_support_applied`; `narration_support_ref`; `primary_interpretation` |
| `P2T4FusedThemeV1` | `fused_observation_id`; `source_observation_ref`; `label: ObservedTextV1`; `evidence_refs: tuple[str, ...]` (min length 1) |

`ObservedTextV1` is imported unchanged from `vision.py` (lines 105-117). Proposed
identity rules (sub-decision D-A1.f):

- `fused_observation_id` equals the source `observation_id`, so no new identity
  is generated. `source_observation_ref` equals the same value.
- `actor_ref`, `object_ref`, `subject_ref`, and `evidence_refs` are copied
  unchanged and must resolve to a fused observation in the same result.
- `narration_support_ref` has the form `asr-segment:<index>`, where `<index>` is
  the P2 `AsrSegmentV1.index` (`asr.py` line 304) of the lowest-index matching
  segment. It is null when `narration_support_applied=false`.
- Labels and predicates are copied from the validated source; T4 never
  re-normalizes stored text.

**`P2T4ConflictV1`** (plan lines 350-379, prefixed): `conflict_id: str`;
`reason_code: P2T4ConflictReasonCode` (exactly `ENTITY_ATTRIBUTE_CONTRADICTION`,
`ACTION_CONTRADICTION`, `RELATION_CONTRADICTION`, `LOW_CONFIDENCE_EVIDENCE`);
`vision_claim_ref: str | None` (a fused observation ID);
`narration_claim_excerpt_ref: str | None` (the `asr-segment:<index>` form);
`recommended_reviewer_attention: Literal[True]`. The derivation of
`conflict_id` is sub-decision D-A1.g. The proposal is
`<reason_code>:<fused_observation_id>`, which is deterministic and unique per
reason and observation.

**`P2T4UncertaintySummaryV1`** (plan lines 428-461, prefixed):
`formula_id: Literal["AGREEMENT_WEIGHTED_V1"]`;
`per_entity: tuple[P2T4EntityUncertaintyV1, ...]`, with exactly one row per fused
entity, action, and relation and none for themes. Each row is
`observation_id: str` (the fused observation ID) plus
`certainty_status: Literal["MEASURED", "NOT_MEASURED", "NOT_APPLICABLE_CONFLICTING"]`
and `certainty: float | None`, under the approved B3a-B3c rules.

**Provenance and privacy.** The T4 result carries no model or provider provenance
of its own. Upstream provenance is reachable through the two source-result
digests. No field at any depth may carry personality, diagnosis, mental-state,
trauma, developmental, or eligibility claims, raw transcript text, raw media,
provider payloads, prompts, credentials, or endpoints.

**Status, empty, null, and unknown rules** (carried forward unchanged from
revision 2 and the approved B1-B6 decisions):

- `FUSED` requires both validated upstream results to succeed, including an
  empty but schema-valid collection set.
- `UPSTREAM_FAILURE` requires one or both validated typed upstream failures and a
  populated `upstream_failure`. Its entities, actions, relations, themes,
  conflicts, and `per_entity` rows are empty.
- The FEAT-017/FEAT-018 live outer statuses `PROPOSAL` and `FAILED` are distinct
  from `FUSED` and `UPSTREAM_FAILURE` and are never translated by name.
- A schema-valid successful ASR result with an empty transcript is a valid
  no-speech case. It produces no narration support and no conflict, and vision
  observations remain. Missing input is not an empty success.
- A missing narration counterpart is not a contradiction. Narration-only text
  never creates an entity, action, relation, or theme in v1.
- Null Vision confidence remains `certainty=null` with
  `certainty_status=NOT_MEASURED`, and support references are retained when a
  match exists. Null is never below the confidence floor.
- Unknown identity, version, discriminator, enum, failure detail, observation
  reference, or edge is rejected. There is no fallback family, guessed version,
  default confidence, default timestamp, default policy pass, or default session
  identity.

**T4 input rejection (not a T4 status).** The pure fusion service accepts only
validated `P2.AsrResultV1@1.0` and `P2.VisionUnderstandingResultV1@1.0` objects
plus a valid `P2T4FusionPolicyConfigV1`. Anything else returns one of the §3.5
input outcomes (`REJECTED_WRONG_FAMILY`, `REJECTED_UNSUPPORTED_VERSION`,
`REJECTED_MALFORMED`, `REJECTED_CORRELATION_MISMATCH`) and no
`P2T4FusedResultV1`. There is no third T4 status.

**Separate freeze approval required.** Freezing this family requires all of:

1. Owner approval of D-A1 including sub-decisions D-A1.a to D-A1.g.
2. A versioned freeze record in FEAT-003 through the required approval process.
   This package does not create it.
3. D-A10: owner confirmation of whether a FEAT-018 registry row is needed. For
   FEAT-003-internal offline use none is proposed; any cross-feature consumption
   requires a separately approved registry update.
4. Updating the plan's design-baseline name through the plan's own change
   process.

### 3.3 Proposed preservation envelope: `P2T4LiveInputPreservationEnvelopeV1` (B1)

Status: `PROPOSED_REQUIRES_OWNER_APPROVAL` (decisions D-A2 and D-A3). It is not
canonical, not a runtime contract, and not placed in source until approved.

**Identity and ownership.**

| Field | Proposed value |
|---|---|
| Review identity | `P2T4.LiveInputPreservationEnvelopeV1@1.0` |
| `contract_name` / `contract_version` | `Literal["P2T4LiveInputPreservationEnvelopeV1"]` / `Literal["1.0"]` |
| Applies to | edge `feat018-live-asr-to-p2-asr` only |
| Field-definition owner | FEAT-003 / Person 2 (the fields mirror P2 target requirements) |
| Value supplier | **NONE_CURRENTLY.** No committed producer emits these values. A supplier requires D-A3: FEAT-017 owner acceptance of a producer change under its own approval, plus ADR-0006 allocation |
| Placement after approval only | Stage B file 1, alongside the T4 family |

**Envelope fields.** Every field is required. "Supplier today" is the committed
producer that could truthfully provide the value at this revision.

| Field | Type | P2 target requirement it serves | Supplier today | If missing or inconsistent |
|---|---|---|---|---|
| `contract_name`, `contract_version` | literals | envelope identity | envelope writer | `REJECTED_UNSUPPORTED_VERSION` / `REJECTED_WRONG_FAMILY` |
| `edge_id` | `Literal["feat018-live-asr-to-p2-asr"]` | edge binding | envelope writer | `REJECTED_WRONG_FAMILY` |
| `source_result_sha256` | `^[a-f0-9]{64}$` | binds the envelope to exactly one flat source instance (canonical digest as in §3.2) | derivable from the source object; the mapper recomputes it | `REJECTED_ENVELOPE_SOURCE_MISMATCH` |
| `correlation_id` | `str` (min 1) | `AsrResultEnvelopeV1.correlation_id` (`asr.py` line 335) | NONE_CURRENTLY. The route's `request_id` is not a correlation ID (B0 report line 198) | `REJECTED_MISSING_REQUIRED_METADATA` |
| `executed_at` | timezone-aware `datetime` | `asr.py` line 336 | NONE_CURRENTLY | `REJECTED_MISSING_REQUIRED_METADATA` |
| `profile_id` | `AsrProfileId` | `asr.py` line 338 | NONE_CURRENTLY. Valid only if the producer executed that exact catalog profile (`asr.py` lines 14-19); never inferred from `ModelProvenanceV1.model` | `REJECTED_MISSING_REQUIRED_METADATA` |
| `attempt_number`, `repair_attempted` | `int` (0-2), `bool` | `asr.py` lines 339-340; P2-T2 retry/repair matrix | NONE_CURRENTLY. Live adapter retries are not P2 attempts (B0 report line 201) | `REJECTED_MISSING_REQUIRED_METADATA` |
| `model_identifier`, `model_revision`, `adapter_version`, `runtime_version`, `config_hash` | `str`; `config_hash` `^[a-f0-9]{64}$` | `AsrSuccessV1` (`asr.py` lines 362-366) | NONE_CURRENTLY. `ModelProvenanceV1.config_version` is not a config hash | `REJECTED_MISSING_REQUIRED_METADATA` |
| `media_validation_artifact_ref`, `media_validation_artifact_sha256` | `str`, `^[a-f0-9]{64}$` | `AsrQualityMetadataV1` (`asr.py` lines 320-327) | NONE_CURRENTLY. The live request carries only the literal `PASS` (`understanding.py` line 66) | `REJECTED_MISSING_REQUIRED_METADATA` |
| `speech_diagnostic`, `input_duration_seconds`, `vad_enabled`, `duration_after_vad_seconds` | P2 types | `AsrSuccessV1` (`asr.py` lines 353, 359-361) | NONE_CURRENTLY | `REJECTED_MISSING_REQUIRED_METADATA` |
| `segment_indexes` | `tuple[int, ...]`, one per flat segment, strictly increasing | `AsrSegmentV1.index` (`asr.py` line 304) | NONE_CURRENTLY. A list position is not adopted as a provider segment index | `REJECTED_MISSING_REQUIRED_METADATA` |
| `failure_detail` (failure branch only) | `AsrErrorDetail` | `AsrFailureV1.error_detail` (`asr.py` line 386) | NONE_CURRENTLY | `REJECTED_MISSING_REQUIRED_METADATA` |
| `failure_retryable` (failure branch only) | `bool` | `AsrFailureV1.retryable` with P2-T2 matrix semantics (P2-T2 plan lines 166-179) | NONE_CURRENTLY | `REJECTED_MISSING_REQUIRED_METADATA`; matrix disagreement is `REJECTED_FAILURE_METADATA_CONFLICT` (§3.5) |

**Fields removed from the envelope (NO_AUTHORITATIVE_SOURCE).**

- *All Vision V1 target identity and policy fields.* This covers `profile_id`,
  `profile_catalog_hash`, `config_hash`, `content_policy_version`,
  `policy_match_view_version`, and `policy_execution_state` (`vision.py` lines
  317-332, 341-356). `VisionProfileId` contains only `FAKE_DETERMINISTIC_V1`
  (`vision.py` lines 120-124), and the V1 contract is frozen (`DECISIONS.md`
  line 108), so no live result can truthfully carry a V1 profile. No P2 content
  policy executes in the live path, so `PASSED` would be fabricated. This is why
  edge 2 is proposed rejection-only (§3.4).
- *Vision observation IDs, reference graphs, and `ObservedTextV1` language
  declarations* (`vision.py` lines 105-117, 218-268). The flat live candidates
  (`understanding.py` lines 108-129) have none, and generating them from text or
  list position is prohibited.
- *Prohibited-claim category.* The flat failure (`understanding.py` lines 12-25)
  has no category field and no P2 policy executed.
- *Session ID, expected session version, request ID, and idempotency key.* These
  are transport-boundary fields (§3.6). No P2 target or T4 contract carries them.

**Envelope failure behavior.** A missing envelope, any missing required field, a
wrong envelope identity, version, or edge, a digest that does not match the
supplied source, any prohibited content, or any value inconsistent with the
source (for example `segment_indexes` count differing from the flat segment
count) rejects the whole mapping with the §3.5 outcome and emits no partial
target. The mapper never fills an envelope field.

**Supplier caveat.** Even with an approved envelope, a positive edge-1 case in
Stage B represents only a *hypothetical approved supplier*. It proves the
boundary rule offline; it does not claim the live producer supplies these
values. Until D-A2 and D-A3 are both approved, edge 1 is rejection-only.

### 3.4 Field and failure rules for the live input edges (M3)

**Edge `feat018-live-asr-to-p2-asr`** (source `understanding.py` lines 75-105;
target `asr.py` lines 330-386).

| Source field or condition | Rule | Outcome |
|---|---|---|
| Identity, version, and `status` branch | Validate exact source identity and version, then select `AsrSuccessV1` or `AsrFailureV1` by the same branch value | wrong family or version: `REJECTED_WRONG_FAMILY` / `REJECTED_UNSUPPORTED_VERSION`; invalid branch: `REJECTED_MALFORMED` |
| Envelope | Required for every branch (§3.3) | absent: `REJECTED_MISSING_REQUIRED_METADATA` |
| `source_audio.artifact_ref`, `sha256`, `source_status` | RENAME to `source_audio_ref` only when `AVAILABLE` with a lowercase 64-character hash; absolute or local machine paths are rejected | otherwise `REJECTED_MISSING_REQUIRED_METADATA` or `REJECTED_MALFORMED` |
| `transcript` | RENAME to `transcript_raw` on success | null on success: `REJECTED_MALFORMED` |
| `language`, `language_confidence` | RENAME to `detected_language` / `language_probability` only as measured detection; the flat contract does not distinguish a hint echo, so equivalence requires D-A2 approval of this row | null `language` on success: `REJECTED_MISSING_REQUIRED_METADATA`; row not approved: `REJECTED_LOSSY_REQUIRED_FIELD` |
| `segments[].start_seconds`, `end_seconds`, `text` | PRESERVE with envelope `segment_indexes` | empty text (P2 min length 1): `REJECTED_MALFORMED` |
| `segments[].confidence` | No P2 target slot; never reinterpreted as `average_log_probability` | non-null value present: `REJECTED_LOSSY_REQUIRED_FIELD` |
| `quality.no_speech_probability`, `average_log_probability`, `segment_count` | Not semantically equal to P2 `mean_no_speech_probability` / `mean_segment_log_probability`; `segment_count` is a consistency check only | non-null probabilities: `REJECTED_LOSSY_REQUIRED_FIELD`; count mismatch: `REJECTED_MALFORMED` |
| `provenance` (`ModelProvenanceV1`) | Retained only through `source_result_sha256`; P2 provenance comes from the envelope. `provider` values `fixture` or `unknown` never satisfy P2 provenance | envelope provenance absent: `REJECTED_MISSING_REQUIRED_METADATA` |
| `failure.message` | INTENTIONALLY DROPPED; never placed in `error_detail` | none |
| `failure.retryable` | **Not used.** Its semantics are not proven equal to the P2-T2 matrix `retryable` ("whether a retry was attempted", P2-T2 plan line 154), so it is neither copied nor used as a check. P2 `retryable` comes only from envelope `failure_retryable` | none |
| `failure.code` with envelope `failure_detail`, `failure_retryable`, `attempt_number`, `repair_attempted` | Admissible only through the closed table below (D-A4). The tuple must equal a P2-T2 matrix row (P2-T2 plan lines 172-177) | no row: `REJECTED_UNMAPPABLE_FAILURE`; row found but values disagree: `REJECTED_FAILURE_METADATA_CONFLICT` |

Proposed closed ASR failure table (D-A4; every other combination is rejected).

| Flat `failure.code` | Envelope `failure_detail` | P2 `error_code` | Required envelope `failure_retryable` / `attempt_number` / `repair_attempted` |
|---|---|---|---|
| `VALIDATION_REJECTED` | `MEDIA_VALIDATION_NOT_PASSED` or `MEDIA_VALIDATION_PROVENANCE_MISSING` | `INPUT_NOT_VALIDATED` | false / 0 / false |
| `SOURCE_MISMATCH` | `SOURCE_AUDIO_UNREADABLE` or `SOURCE_AUDIO_HASH_MISMATCH` | `INPUT_NOT_VALIDATED` | false / 0 / false |
| `TIMEOUT` | `TIMEOUT_BUDGET_EXCEEDED` | `ASR_TIMEOUT` | false / 1 / false. The idempotent-timeout variant (true / 2, P2-T2 plan line 174) is `REJECTED_FAILURE_METADATA_CONFLICT` in v1 unless D-A4 approves an explicit rule tying it to a declared profile in the static P2-T2 catalog |
| `PROVIDER_ERROR` | `TRANSIENT_RUNTIME_FAILURE` | `ASR_PROVIDER_FAILURE` | true / 2 / false |
| `PROVIDER_ERROR` | `PERMANENT_RUNTIME_FAILURE` | `ASR_PROVIDER_FAILURE` | false / 1 / false |
| `MALFORMED_OUTPUT` | `OUTPUT_MAPPING_FAILED` | `ASR_SCHEMA_INVALID` | false / 1 / true or false |
| `RATE_LIMITED`, `PROHIBITED_FIELD` | any | none | always `REJECTED_UNMAPPABLE_FAILURE` |

`ASR_MODEL_UNAVAILABLE` (`MODEL_LOAD_FAILED`, `DEVICE_UNAVAILABLE`) has no flat
source code that distinguishes it, so it is not admissible from this edge.
Because `asr.py` does not pin detail-to-code pairs in the schema (the P2-T2 matrix
is adapter-enforced, P2-T2 plan line 179), the closed table above is the only
admissible pairing and requires owner approval.

**Edge `feat018-live-vision-v1-to-p2-vision-v1`** (source `understanding.py`
lines 108-172; target `vision.py` lines 317-503). Proposed rejection-only in v1
(D-A5).

| Source condition | Rule | Outcome |
|---|---|---|
| Wrong identity, version, or namespace (including a P2-T3 V2 object or a FEAT-015 compact V2-labelled payload) | Checked first | `REJECTED_WRONG_FAMILY` / `REJECTED_UNSUPPORTED_VERSION` |
| Prohibited provider payload, prompt, endpoint, credential, raw media, or personal metadata present | Checked second | `REJECTED_PRIVACY_INVALID` |
| Invalid branch, interval, enum, or structurally malformed input | Checked third | `REJECTED_MALFORMED` |
| Any schema-valid `SUCCEEDED` result | V1 success requires a truthful V1 profile/catalog/config identity, `policy_execution_state="PASSED"`, observation IDs, and `ObservedTextV1` language declarations; none has an authoritative source (§3.3) | `REJECTED_NO_AUTHORITATIVE_SOURCE` |
| Any schema-valid `FAILED` result with code `VALIDATION_REJECTED`, `SOURCE_MISMATCH`, `TIMEOUT`, `PROVIDER_ERROR`, or `MALFORMED_OUTPUT` | V1 failure still requires profile/catalog identity and a policy state, and no source detail or attempt exists | `REJECTED_NO_AUTHORITATIVE_SOURCE` |
| `FAILED` with `PROHIBITED_FIELD` or `RATE_LIMITED` | No prohibited category exists in the source and no P2 policy executed; the result is not claimed as a preserved policy block | `REJECTED_UNMAPPABLE_FAILURE`; terminal, blocks progression, never success |
| Any envelope or extra metadata asserting a V1 profile or policy `PASSED` for a live result | Fabrication guard | `REJECTED_NO_AUTHORITATIVE_SOURCE` |

Outcome precedence for both edges is deterministic: identity/version, then
privacy, then malformed, then no authoritative source, then missing required
metadata, then failure-metadata conflict or unmappable failure, then lossy
required field. Each case has exactly one oracle label.

A positive Vision path requires work outside this package: either a separately
approved P2-T3 V1 catalog/policy amendment (V1 is frozen), or a separate package
defining a new edge to the deferred P2-T3 V2 study family. Neither is proposed
here.

### 3.5 Closed outcome vocabulary

These are deterministic test-oracle labels for Stage B. They are not public
statuses and are not added to any registry.

| Label | Meaning |
|---|---|
| `MAPPING_ADMISSIBLE_FOR_OFFLINE_REVIEW` | Edge 1 only, and only after D-A2 and D-A3; always `adoption_applied=false` |
| `REJECTED_WRONG_FAMILY` | Identity, namespace, or edge mismatch, including same-name contracts |
| `REJECTED_UNSUPPORTED_VERSION` | Unknown contract, envelope, mapping, or edge version |
| `REJECTED_MALFORMED` | Invalid branch, enum, interval, count, or structure |
| `REJECTED_PRIVACY_INVALID` | Prohibited content present |
| `REJECTED_NO_AUTHORITATIVE_SOURCE` | Target value cannot be truthfully supplied under current contracts |
| `REJECTED_MISSING_REQUIRED_METADATA` | A required source or envelope value is absent |
| `REJECTED_ENVELOPE_SOURCE_MISMATCH` | Envelope digest does not match the supplied source |
| `REJECTED_FAILURE_METADATA_CONFLICT` | Envelope failure tuple disagrees with its approved matrix row |
| `REJECTED_UNMAPPABLE_FAILURE` | No approved failure row exists for the source code |
| `REJECTED_LOSSY_REQUIRED_FIELD` | A non-null source semantic has no approved target representation |
| `REJECTED_CORRELATION_MISMATCH` | T4 service input: upstream correlation IDs differ |
| `UNCHANGED_BASELINE` | Baseline hash check passed |

Removed from this package: `REJECTED_STALE_SESSION` (§3.6),
`REJECTED_CLEANUP_FAILURE` (runtime-only, no offline producer), `REJECTED_POLICY`
(no source category exists), and every edge-3 label (§3.7).

Publication invariants:

- Two validated successful P2 inputs produce `FUSED`, even with empty
  collections.
- One or two validated P2 failure inputs produce `UPSTREAM_FAILURE` with empty
  collections and the correct references.
- A mapping rejection or T4 input rejection is never converted into
  `UPSTREAM_FAILURE` or success.
- T4 never re-invokes ASR, Vision, Lightning, Runpod, a model, or a fixture
  provider.

### 3.6 Session, request, and idempotency validation: deferred (M4)

Stage B contains **no** stale-session, request-ID, or idempotency validation and
no test that assumes one. The reasons, from committed sources:

- No in-scope contract carries these fields: the P2 result envelopes
  (`asr.py` lines 330-347, `vision.py` lines 317-338), the flat live results
  (`understanding.py` lines 75-172), the proposed T4 family (§3.2), and the
  proposed envelope (§3.3).
- They exist only on the FEAT-017 route request (`live_understanding.py` lines
  28-35, with the version check at lines 47-48) and in the FEAT-018 transport
  rule (`CONTRACT_FREEZE.md` line 13). The route is FEAT-017-owned (§1.2).
- Detecting an idempotency-key mismatch or replay requires memory of previously
  seen keys, which is a store and is prohibited in Stage B.

These checks are deferred to a separate transport/integration package with its
own ADR-0006 allocation. If that package brings them into scope, staleness must
be exact version equality between explicit payload fields and an injected
expected version, with no store, database, registry, network, or runtime lookup.
Time-based staleness requires a separately approved time rule, because no
committed source defines one. No mapper or fusion service invents, defaults,
or drops session identity; since none of their inputs carries it, there is
nothing to preserve at this boundary.

### 3.7 Edge 3 `p2t4-fused-design-to-feat018-raw`: deferred (B3)

Edge 3 is deferred to a separate package. Reasons:

- The FEAT-018 target `RawUnderstandingResultV1` exists only as a registry row
  and prose (`CONTRACT_FREEZE.md` lines 25 and 48) and as the FEAT-015 expected
  JSON (`integration-fixture-v1/expected/raw-understanding.json`). A read-only
  search found no schema class for it in `backend/src` or FEAT-015 `src`.
- FEAT-018 owns that target and handoff (§1.2). FEAT-003 must not define it.
- Testing an admissible projection against a prose-only target would require
  schema invention.

Entry conditions for the separate package:

1. FEAT-018 publishes a frozen, machine-checkable target contract, or a new
   target version, under its own approval.
2. `P2T4FusedResultV1` is frozen (D-A1).
3. FEAT-018 and P1/Gate A approve how T4 source references, conflicts,
   uncertainty, typed upstream failures, and `gate_a_required` are preserved.
4. An ADR-0006 allocation names the implementer.

Carry-forward constraints from B0 that the future package must keep:

- `FUSED`/`UPSTREAM_FAILURE` are never coerced to `PROPOSAL`/`FAILED` by string
  matching.
- T4 observations are never flattened into claims with field loss.
- `gate_a_required=true` is never omitted or set false.
- Source text is never re-normalized.
- Prohibited content never enters a projection.
- A projection that cannot preserve required semantics is rejected.

Under this package, no T4 output reaches Gate A or P1.

### 3.8 Stage A decision register (all OPEN)

| ID | Decision required from the owner | Blocks |
|---|---|---|
| D-A0 | Confirm that the proposed mapping family remains the planning basis for edges 1-2 while staying `PROPOSED_NOT_ADOPTED`; implementing offline validators is not adoption | Stage B files 3, 5, mapping fixture cases |
| D-A1 | Freeze `P2T4FusedResultV1` and its nested `P2T4` types as in §3.2, including sub-decisions D-A1.a (correlation equality), D-A1.b (no fused ambiguous regions in v1), D-A1.c (digest source references), D-A1.d (policy cue/window/increment fields), D-A1.e (retryable and repair preserved in failure references), D-A1.f (identity and support-reference rules), and D-A1.g (conflict ID derivation) | All Stage B files |
| D-A2 | Approve, amend, or reject `P2T4LiveInputPreservationEnvelopeV1` (§3.3), including the language RENAME row in §3.4 | Edge-1 positive case; envelope model in file 1 |
| D-A3 | Name an authoritative supplier for envelope values, with FEAT-017 owner acceptance of any producer change and ADR-0006 allocation; otherwise edge 1 stays rejection-only | Edge-1 positive case |
| D-A4 | Approve the closed ASR failure table (§3.4) and confirm that flat `failure.retryable` is not used | Edge-1 failure cases |
| D-A5 | Accept edge 2 as rejection-only in v1 | Edge-2 cases |
| D-A6 | Accept deferral of edge 3 to a separate package (§3.7) | Package scope |
| D-A7 | Resolve ownership of the flat `understanding.py` contract identity (§1.2) | Files 3, 5 |
| D-A8 | Approve an ADR-0006 allocation stating who implements `p2_t4_mapping.py` and under which approval record, or direct re-issue of this package without it | Files 3, 5, mapping fixture cases |
| D-A9 | Accept deferral of session, request, and idempotency validation to a transport/integration package (§3.6) | Package scope |
| D-A10 | Confirm whether `P2T4FusedResultV1` needs a FEAT-018 registry row before any cross-feature consumption (none proposed for FEAT-003-internal offline use) | File 1 |

Stage A exit: every row above is recorded by the owner through the required
approval process, a versioned freeze record exists, and this package is re-issued
against that record. Until then the package remains
`BLOCKED_PENDING_CONTRACT_FREEZE`.

## 4. Stage B — conditional offline implementation (NOT APPROVABLE UNTIL STAGE A EXIT)

### 4.1 Exact conditional scope

**Exact scope statement.** The conditional implementation scope is exactly 9
additive files: 3 source modules, 3 test modules, and 3 synthetic fixture files.
None exists, and none is created by this package.

The following are governance artifacts outside the 9 files and must never be
added to the list: this package, any approval addendum or freeze record, the
FEAT-003 `CONTEXT.md`/`DECISIONS.md`/plan metadata that references this package,
and ignored `tmp/` reports.

| # | Repository-relative path | Responsibility | Stage A conditions |
|---|---|---|---|
| 1 | backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py | The frozen `P2T4` contract family (§3.2); the envelope model only if D-A2 approves it | D-A1, D-A10; D-A2 for the envelope |
| 2 | backend/src/sketch2life/application/services/p2_t4_fusion.py | Pure fusion over validated P2 inputs and the frozen policy: support-only narration, bounded negation, primary-only weighting, conflicts, uncertainty, and `FUSED`/`UPSTREAM_FAILURE` | D-A1 |
| 3 | backend/src/sketch2life/infrastructure/understanding/p2_t4_mapping.py | Unregistered, fail-closed validators for edges 1 and 2 only (§3.4). No edge 3. | **Conditional on the separate ADR-0006 cross-feature allocation (D-A8)**, plus D-A0, D-A2, D-A3 (positive case only), D-A4, D-A5, D-A6, D-A7 |
| 4 | backend/tests/unit/test_p2_t4_fusion.py | The 17 pure fusion cases, T4 input rejections, determinism, and status invariants | D-A1 |
| 5 | backend/tests/unit/test_p2_t4_mapping.py | Edge 1 and 2 rejection oracles, the conditional edge-1 positive case, and no-partial-publication | Same as file 3 |
| 6 | backend/tests/contract/test_p2_t4_contract.py | JSON Schema/Pydantic parity, exact identity/version, discriminator and structural invariants, strict extras, and round-trip serialization for the frozen `P2T4` family (and the envelope if approved) | D-A1; D-A2 for the envelope |
| 7 | features/FEAT-003-multimodal-understanding/fixtures/p2-t4-mapping-family-v1/manifest-v1.json | Synthetic manifest: fixture identity, contract and mapping identity, case coverage by condition, source hashes, `adoption_applied=false` | D-A1; mapping entries also D-A0 and D-A2 to D-A8 |
| 8 | features/FEAT-003-multimodal-understanding/fixtures/p2-t4-mapping-family-v1/cases-v1.json | Synthetic fusion and mapping cases without raw payloads, secrets, or personal data | as file 7 |
| 9 | features/FEAT-003-multimodal-understanding/fixtures/p2-t4-mapping-family-v1/expected-v1.json | Deterministic expected outcomes and serialization/hash assertions | as file 7 |

Allocation boundary. FEAT-003 approval alone does not authorize implementing
FEAT-017, FEAT-018, or shared-integration behavior. Files 3 and 5 and the mapping
fixture cases may be implemented only by the implementer and under the approval
record that D-A8 names.

The 9-file list is approvable only as a whole. If D-A8 is refused or any mapping
decision is rejected, this package must be re-issued with a revised scope. A
reduced file list is not pre-authorized here.

The later implementation must not change:

- `backend/src/sketch2life/contracts/schemas/asr.py`, `vision.py`,
  `vision_v2.py`, `understanding.py`, or any other existing schema
- `backend/src/sketch2life/application/ports/asr.py`,
  `vision_understanding.py`, `vision_understanding_v2.py`, or `understanding.py`
- `backend/src/sketch2life/interfaces/http/routers/live_understanding.py` or any
  route
- any contract registry or generated mirror, including `CONTRACT_FREEZE.md`
- any FEAT-015 fixture, loader, or flow, or the B0 reconciliation fixture
- any FEAT-017 source, guide, route, provider configuration, evidence, or mobile
  path
- any FEAT-018 route, runtime, mobile, session, Gate A, P1, or downstream path
- `approvals/TASK_APPROVAL.md`

Explicit exclusions: schema replacement, registry/port/route changes, migration,
registry cutover, production use, provider/model/GPU/network execution, FEAT-017
changes, FEAT-018 runtime changes, mobile, Gate A UI, P1 behavior, session/store
work, edge 3, and changes to existing fixtures. Any exception requires a new
bounded plan and separate approval.

### 4.2 Dependency direction

- File 1 depends only on standard validation/types and existing P2 value types
  (`ObservedTextV1`, `AsrErrorCode`, `AsrErrorDetail`, `VisionErrorCode`,
  `VisionFailureDetail`) imported without modification.
- File 2 depends inward on file 1 and the validated P2 contracts. It imports no
  router, provider, storage, queue, `understanding.py`, FEAT-018 type, mobile
  type, or clock implementation (the clock is injected).
- File 3 is the only proposed cross-family boundary. It imports `understanding.py`
  source types and P2 target types and holds no implicit state.
- No application port is added or widened. Any transport port, route, session,
  or registry entry is a separate integration scope.

### 4.3 Fixture identity and provenance

The fixture files must be synthetic-only and feature-local. Each case carries:

- fixture ID and version
- contract identity and version
- mapping family, version, and edge ID for mapping cases
- the Stage A decisions the case depends on
- relative artifact references and lowercase SHA-256 markers
- provenance pointers
- the single expected oracle label
- `adoption_applied=false`

Cases carry no session, request, or idempotency metadata (§3.6). Synthetic
envelopes are labelled as hypothetical approved-supplier inputs (§3.3). The
manifest states that no raw media, raw provider payload, prompt, credential,
endpoint, token, personal metadata, or absolute machine path is present.

The B0 manifest `fixtures/p2-t4-contract-reconciliation-v1/manifest-v1.json` and
the FEAT-015 v1 manifest and expected payloads are read-only baselines. They are
never replaced, relabelled, or expanded.

### 4.4 Conditional offline case set and oracle

The pure fusion suite (file 4, with contract checks in file 6) retains the
existing 17-case baseline, all conditional on D-A1 and all using validated
synthetic P2 inputs only:

1. Agreement support, deterministic primary selection, one 0.10 increment, and
   the 1.0 cap.
2. Audio-only narration with no narration-created candidate or conflict.
3. Image-only candidate retained without support or conflict.
4. Entity negation for each of not, no, never, isn't, doesn't, and didn't,
   subject to the exact preceding three match-view-token window.
5. Action negation under the same bounded rule.
6. Relation negation under the same bounded rule.
7. A cue outside the three-token window produces no conflict.
8. Negation with no Vision counterpart produces no conflict.
9. Measured confidence below, at, and above the configured floor.
10. Distinct source observation IDs with normalized-equal labels do not merge.
11. Null Vision confidence without support produces `NOT_MEASURED` and null.
12. Null Vision confidence with support remains `NOT_MEASURED` and null while
    retaining support provenance.
13. Multiple transcript matches produce one increment and a deterministic support
    reference.
14. A typed ASR failure produces `UPSTREAM_FAILURE` with only the ASR reference.
15. A typed Vision failure produces `UPSTREAM_FAILURE` with only the Vision
    reference.
16. Both typed failures populate both references and keep collections empty.
17. JSON Schema/Pydantic round-trip, deterministic serialization,
    source/reference integrity, uncertainty-row completeness, conditional failure
    validation, and prohibited-field rejection.

No case asserts a third T4 status.

| Case | Area | Condition | Expected oracle |
|---|---|---|---|
| Fusion cases 1-13 | fusion | D-A1 | `FUSED` per the plan rules |
| Fusion cases 14-16 | fusion | D-A1 | `UPSTREAM_FAILURE`, correct references, empty collections |
| Fusion case 17 | contract | D-A1 | parity, serialization, and integrity assertions pass; prohibited fields rejected |
| Upstream correlation IDs differ | fusion input | D-A1 | `REJECTED_CORRELATION_MISMATCH`, no T4 result |
| Flat `understanding.py` object or P2-T3 V2 object given to the fusion service | fusion input | D-A1 | `REJECTED_WRONG_FAMILY` |
| Live ASR with no envelope (success and failure branches) | edge 1 | D-A0, D-A7, D-A8 | `REJECTED_MISSING_REQUIRED_METADATA` |
| Live ASR with envelope digest not matching the source | edge 1 | + D-A2 | `REJECTED_ENVELOPE_SOURCE_MISMATCH` |
| Live ASR failure with envelope tuple disagreeing with the matrix row | edge 1 | + D-A2, D-A4 | `REJECTED_FAILURE_METADATA_CONFLICT` |
| Live ASR `RATE_LIMITED` or `PROHIBITED_FIELD` | edge 1 | + D-A4 | `REJECTED_UNMAPPABLE_FAILURE` |
| Live ASR with non-null `segments[].confidence` or quality probabilities | edge 1 | + D-A2 | `REJECTED_LOSSY_REQUIRED_FIELD` |
| Live ASR malformed branch, empty segment text, or count mismatch | edge 1 | D-A0 | `REJECTED_MALFORMED` |
| Complete live ASR with an approved envelope from a hypothetical approved supplier | edge 1 | D-A2 **and** D-A3 | `MAPPING_ADMISSIBLE_FOR_OFFLINE_REVIEW`, `adoption_applied=false` |
| Direct synthetic live Vision `SUCCEEDED` result | edge 2 | D-A5, D-A7, D-A8 | `REJECTED_NO_AUTHORITATIVE_SOURCE` |
| Direct synthetic live Vision `FAILED` with each of `VALIDATION_REJECTED`, `SOURCE_MISMATCH`, `TIMEOUT`, `PROVIDER_ERROR`, `MALFORMED_OUTPUT` | edge 2 | D-A5 | `REJECTED_NO_AUTHORITATIVE_SOURCE` |
| Direct synthetic live Vision `PROHIBITED_FIELD` or `RATE_LIMITED` | edge 2 | D-A5 | `REJECTED_UNMAPPABLE_FAILURE`, never success |
| Live Vision with metadata asserting a V1 profile or policy `PASSED` | edge 2 | D-A5 | `REJECTED_NO_AUTHORITATIVE_SOURCE` |
| P2-T3 V2 object or FEAT-015 compact V2-labelled payload at a V1 edge | edges 1-2 | D-A0 | `REJECTED_WRONG_FAMILY` |
| Same serialized name from the wrong namespace | edges 1-2 | D-A0 | `REJECTED_WRONG_FAMILY` |
| Unknown mapping family, edge, or version | edges 1-2 | D-A0 | `REJECTED_UNSUPPORTED_VERSION` |
| Prohibited payload, prompt, endpoint, credential, raw media, or personal metadata | all | D-A0 or D-A1 | `REJECTED_PRIVACY_INVALID` |
| Existing FEAT-015 v1, B0 manifest, and P2 contract module hashes | baseline | none | `UNCHANGED_BASELINE` |

Not in Stage B:

- stale-session, request, and idempotency cases (§3.6)
- every edge-3 case (§3.7)
- cleanup-failure cases (runtime-only)
- any actual Lightning, Qwen, Whisper, model, GPU, network, or provider
  execution

### 4.5 Contract parity, round-trip, and determinism

**Strict definition of "round-trip".** Round-trip means only serialization and
deserialization within one declared contract:

1. Serialize a validated instance of a single named and versioned contract (for
   example `P2T4.P2T4FusedResultV1@1.0`) to canonical JSON.
2. Deserialize it back.
3. Require equal values and byte-identical repeated serialization.

Round-trip never means or authorizes mapping a target identity back to a source
identity or any transformation other than the directional edges in §2.2. It does
not create or authorize a fourth edge or a reverse edge. A round-trip assertion
covers exactly one contract at a time.

- Exported JSON Schema and Pydantic models agree on names, versions,
  discriminators, requiredness, enum values, nullability, and extra-field
  rejection.
- For an admissible mapping case, every PRESERVE value must be carried across the
  edge without value change. Every TRANSFORM value must have a deterministic
  expected value and rule identity. This is edge preservation, not round-trip.
- Repeated execution of the same synthetic case is byte-identical. The injected
  clock is fixed, and digests use the §3.2 canonical serialization.
- A target is never accepted because Pydantic can parse a same-name model. The
  explicit identity and edge are part of the oracle.
- Negative cases prove no partial target or T4 object is emitted.
- Existing FEAT-015, B0, and P2-T2/P2-T3 baseline hashes remain unchanged.

### 4.6 Offline versus later runtime tests

| Test group | Stage B offline | Later, separately approved |
|---|---|---|
| Contract parsing, schema export, discriminators, enum/null/extra-field validation for the frozen `P2T4` family | Yes | No |
| Edge 1-2 rejection oracles and the conditional edge-1 positive case with synthetic objects | Yes, subject to §4.1 conditions | No |
| T4 support/refute, negation, conflicts, weighting, uncertainty, status oracle | Yes | No |
| Deterministic serialization, round-trip, digests, unchanged baselines | Yes | No |
| Actual FEAT-017 Lightning response or model-produced live input | No | Yes |
| Stale-session, request, idempotency, transport, route, session, job | No | Yes, transport/integration package |
| Edge 3 projection to FEAT-018 target | No | Yes, separate edge-3 package |
| Provider retry, timeout cancellation, cleanup, GPU/model/network execution | No | Yes |
| Registry, FEAT-015 flow migration, FEAT-018 runtime, mobile, Gate A UI, P1, E2E | No | Yes, separate owners and approvals |

## 5. Compatibility, rollout, and rollback

### 5.1 Compatibility window

No runtime compatibility window is active. Proposed future staging:

1. **W0, current:** Stage A review only. After Stage A exit and a separate
   implementation approval, offline Stage B tests only. No producer or consumer
   is dual-written.
2. **W1, future shadow:** only after separate runtime/integration approvals,
   including the transport/integration package, the existing FEAT-017/FEAT-018
   path remains the baseline while a new edge is allowlisted for shadow or
   read-only comparison. The owner must set an exact expiry before W1; this
   package does not invent one.
3. **W2, future cutover:** only after an approved target version, registry
   update, migration proof, rollback rehearsal, and FEAT-018/P1/Gate A
   acceptance. The old path remains recoverable.

Until W1 and W2 criteria are set, the compatibility guarantee is NONE beyond the
unchanged existing baselines.

### 5.2 Reader, writer, and version negotiation (future runtime)

- A reader accepts only an exact allowlist row: family, edge, source identity and
  version, target identity and version, and branch. Unknown rows are rejected
  before field validation.
- Same-name contracts are never accepted by name. P2-T3 V2 objects are rejected
  at V1 readers.
- Readers keep the FEAT-015 v1 fixture and the existing FEAT-017/FEAT-018 live
  behavior available during any approved window.
- Writers emit no target when a required preservation value is absent.
- Session, request, and idempotency negotiation belongs to the deferred
  transport/integration package (§3.6).

### 5.3 Migration and cutover prerequisites

Before any migration, registry update, or cutover can be approved:

- Stage A exit and completed, reviewed Stage B evidence
- owner adoption of the mapping family and each edge in use
- an approved supplier for any envelope values (D-A3)
- the separate edge-3 package (§3.7) if a Gate A handoff is involved
- the transport/integration package covering session, request, and idempotency
  (§3.6)
- an immutable old/new fixture strategy (FEAT-015 v1 byte-stable, new fixtures
  additive and versioned)
- reader/writer allowlists, exact window expiry, rollback rehearsal, and
  non-adoption evidence
- review by FEAT-017, FEAT-018, FEAT-015, P1/Gate A, and downstream owners, with
  ADR-0006 allocations for all cross-feature work
- passing architecture, harness, skeleton, repository-security, contract, and
  focused offline tests at the authorized commit

Production use, production cutover, Runpod deployment, cloud provisioning, and
production API authorization are NOT APPROVED by this package.

### 5.4 Rollback and abort

- **Stage A review:** reject or return the package; keep `PROPOSED_NOT_ADOPTED`;
  change no contract, registry, plan, or approval.
- **Stage A decisions:** if any D-A decision is refused, re-issue this package
  with the affected proposal removed or revised. Do not start any Stage B file.
- **Stage B implementation:** stop and remove only uncommitted additive work if
  implementation requires an existing schema, port, route, or registry edit, raw
  data, a provider call, an unapproved field, a session store, or edge-3 behavior.
  Existing baselines stay untouched.
- **Focused testing and review:** abort on nondeterminism, field loss,
  hash/reference mismatch, privacy violation, wrong-family acceptance, or any
  rejection converted into success. Preserve the failing fixture and oracle; do
  not weaken the rule.
- **Future shadow run:** disable the edge allowlist and continue the unchanged
  old path, without deleting new evidence or overwriting old hashes.
- **Future cutover:** use the approved reverse registry/reader/writer procedure
  and retain both fixture versions, confirming that Gate A/P1 identity is
  unchanged.

## 6. P1 and Gate A boundaries

Under this package no T4 output reaches Gate A or P1, because edge 3 is deferred.
The following acceptance criteria apply to the future edge-3 and integration
packages. They are not performed or asserted here:

1. A mapped result carries exact approved source and target identities,
   versions, source digests, typed status/failure data, and mapping edge
   identity. Transport metadata is carried per the transport/integration package.
2. A successful live proposal has `gate_a_required=true`, which cannot be omitted
   or set false.
3. T4 observations, support references, conflicts, certainty states, policy hash,
   and upstream-failure references remain traceable. A target that cannot carry
   them is rejected.
4. Gate A remains a separate adult action recording meaning version, confirmed
   claim IDs, actor, expected session version, and optional adult correction. No
   T4 output is confirmed meaning.
5. P1 receives only an approved post-Gate-A handoff and an explicit adult-owned
   `P1ContextV1`. T4 infers no age, readiness, completed activities, materials,
   supervision, policy flags, eligibility, catalog identity, or objective
   identity.
6. An upstream failure, mapping rejection, unmappable failure, or missing
   provenance blocks progression and is never shown as success or replaced by
   fixture data.
7. Gate B remains responsible for exact activity/objective IDs and versions,
   stale-session checks, and catalog/objective compatibility.
8. No AI field contains personality, diagnosis, mental-state, trauma,
   developmental, or eligibility claims.
9. FEAT-018/P1 reviewers explicitly accept empty-result and missing-narration
   behavior.

Outside P2-T4: Gate A UI, adult confirmation workflow, session/job/API
orchestration, P1 filtering, catalog/objective selection, Gate B, mobile state,
FEAT-017 live transport, FEAT-018 runtime wiring, FEAT-015 flow migration, and
production integration.

## 7. Approval gates and sequence

| Gate | Stage | Entry condition | Authorized output | Abort / rollback |
|---|---|---|---|---|
| A1 Design review | A | This package, B0 records, source contracts, and target freeze reviewed together | Owner questions and decisions may be recorded; no code, schema, or fixture | Return to draft if any identity, owner, supplier, or edge is assumed rather than decided |
| A2 Owner decisions | A | D-A0 to D-A10 presented | Owner records each decision through the required approval process (not by this package) | Any refusal: re-issue the package without that proposal |
| A3 Contract freeze | A | A2 complete | Versioned freeze record for the `P2T4` family (and the envelope if approved); package re-issued; `BLOCKED_PENDING_CONTRACT_FREEZE` lifted only by owner action | No Stage B work until the freeze exists |
| B1 Implementation approval | B | A3 complete; D-A8 allocation recorded | A separately recorded approval naming exactly the 9 files in §4.1 | Do not implement if approval is absent, broad, or implies runtime, registry, route, session, mobile, or edge-3 work |
| B2 Offline implementation | B | B1 | Only the 9 additive files, within their §4.1 conditions | Stop on any need to edit existing schemas, ports, routes, or registries, use raw data, call a provider, or add an unapproved field |
| B3 Focused tests and validators | B | B2 complete | Focused no-provider tests, contract parity/round-trip checks, `git diff --check`, and the repository validators required by the approved task | Abort on nondeterminism, field loss, privacy violation, wrong-family acceptance, or rejection-to-success conversion |
| B4 Independent review | B | B3 evidence and exact diff | Review of dependency direction, oracles, fixture hashes, security, and absence of runtime wiring | Return for correction if the diff touches excluded paths |
| Later: transport/integration package | later | Stage B reviewed; FEAT-017/FEAT-018/FEAT-016 owners and ADR-0006 allocation | Separate plan for session, request, and idempotency validation | No action under this package |
| Later: edge-3 package | later | §3.7 entry conditions | Separate plan for the Gate A handoff projection | No action under this package |
| Later: runtime, migration, cutover | later | §5.3 prerequisites | Separately approved shadow/runtime/migration/cutover plans | Non-adoption leaves all baselines and hashes untouched |

## 8. Current package validation and non-actions

- This package exists only in the P2-T4 worktree, under feature-local FEAT-003
  `evidence/notes/`.
- No source schema, port, route, registry, migration, fixture, code module,
  approval record, plan, FEAT-017 file, FEAT-018 file, or mobile file was changed
  to produce any revision.
- No provider, model, GPU, network, live Vision, Lightning, Runpod, production,
  dependency, or runtime action was performed.
- Validation for each revision was limited to read-only source/status/worktree
  inspection, static package checks, and `git diff --check`. Tests and repository
  validators were not run because this is documentation-only work.
- The main FEAT-018 worktree was not touched.

## 9. Revision history

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-13 | Initial draft: mapping-family field rules, failure/compatibility/rollback, fixtures, and a proposed 9-file scope |
| 2 | 2026-09-13 | Correction pass: V2 naming, source-identity statement, round-trip and stale-session definitions, explicit 9-file scope statement |
| 3 | 2026-09-13 | Blocker correction after independent review. The package is split into Stage A (contract freeze) and Stage B (conditional implementation), with status `BLOCKED_PENDING_CONTRACT_FREEZE`. Answers to the review findings: B1, a proposed namespaced envelope listing NO_AUTHORITATIVE_SOURCE fields; B2, the proposed `P2T4FusedResultV1` family replacing reuse of the colliding name; B3, edge 3 deferred. M1 ownership was corrected from committed records and `understanding.py` ownership recorded as open. M2 made the mapping module conditional on ADR-0006 allocation; M3 rewrote failure rules on source/envelope fields only; M4 deferred session/idempotency validation. The outcome vocabulary was closed, the round-trip wording clarified, and the untracked local citation removed. |

This package remains:

DRAFT

NOT AN IMPLEMENTATION APPROVAL

NOT A RUNTIME AUTHORIZATION

BLOCKED_PENDING_CONTRACT_FREEZE
