# P2-T4 Blocker-0 contract reconciliation plan

- Status: **AWAITING APPROVAL - NOT APPROVED**
- Date: 2026-09-13
- Lead: Person 2, with FEAT-018/shared-integration and P1/Gate A review
- Feature: FEAT-003 multimodal understanding
- Related plan: `P2_T4_FUSION_RESEARCH_PLAN.md`
- Approval request: `../evidence/notes/P2_T4_CONTRACT_RECONCILIATION_APPROVAL_REQUEST.md`

This is a bounded documentation and contract-reconciliation workstream. It is
not a contract implementation plan, a migration execution, or an approval to
change a producer or consumer. The workstream may begin only after its separate
approval is granted; P2-T4 fusion implementation requires a further approval.

## 1. Problem statement and conflicting contract identities

The repository currently uses the same serialized names for incompatible
contracts:

- `backend/src/sketch2life/contracts/schemas/understanding.py` defines a live
  provider-shaped `AsrResultV1` and `VisionUnderstandingResultV1` family. They
  are flat Pydantic models with shared optional fields, `source_audio`/
  `source_image`, `ModelProvenanceV1`, and `AdapterFailureV1`.
- `backend/src/sketch2life/contracts/schemas/asr.py` defines the P2-T2
  provider-neutral `AsrResultV1` as a discriminated
  `AsrSuccessV1 | AsrFailureV1` family with `source_audio_ref`, typed failure
  detail, attempt/repair semantics, and ASR diagnostics.
- `backend/src/sketch2life/contracts/schemas/vision.py` defines the P2-T3
  provider-neutral `VisionUnderstandingResultV1` as a discriminated
  `VisionUnderstandingSuccessV1 | VisionUnderstandingFailureV1` family with
  nested source references, `ObservedTextV1`, globally checked observation
  references, policy provenance, and typed failure detail.
- FEAT-018's `plan/CONTRACT_FREEZE.md` defines `RawUnderstandingResultV1` as a
  claims-shaped Gate A/P1 handoff with `claims[]`, `conflicts`, and
  `gate_a_required`. The FEAT-015 integration fixture instantiates that shape.
- P2-T4's design baseline uses the same `RawUnderstandingResultV1` name for a
  fused entity/action/relation/theme result with source result references,
  conflicts, uncertainty, and typed upstream-failure provenance. Its active v1
  statuses are only `FUSED | UPSTREAM_FAILURE`, but its shape is not canonical
  until this reconciliation is complete.

The conflict is therefore not a Python import alias. It affects serialized
contract identity, field names, requiredness, discriminators, provenance,
failure behavior, and downstream acceptance. A consumer can currently receive a
payload that claims to be `AsrResultV1`, `VisionUnderstandingResultV1`, or
`RawUnderstandingResultV1` while meaning a different shape.

## 2. Authority and ownership boundaries

The following sources and boundaries govern the reconciliation:

| Source or boundary | Role in this workstream |
|---|---|
| `AGENTS.md`, `docs/governance/WORKFLOW.md`, and `docs/governance/APPROVAL_POLICY.md` | Require a reviewable plan, explicit approval, and scope-matched implementation. |
| `docs/context/SOURCE_REGISTER.md` | Defines external references as contextual input only; it does not authorize implementation. |
| `docs/adr/ADR-0006-parallel-sprint-allocation.md` | Keeps Sprint 1 workstreams independent and requires separate integration allocation/approval. |
| FEAT-003 `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`, and P2-T4 plan | Define P2 ownership, the nine recorded design decisions, active v1 boundaries, and the non-approval state. |
| P2-T2 `P2_T2_ASR_RESEARCH_PLAN.md` and `contracts/schemas/asr.py` | Authority for the P2 ASR research contract and its producer boundary. |
| P2-T3 `P2_T3_VISION_RESEARCH_PLAN.md` and `contracts/schemas/vision.py` | Authority for the P2 V1 vision research contract and its producer boundary. |
| P2-T3 `contracts/schemas/vision_v2.py` and its approved study plan | An adjacent, separately named study family; it is not silently substituted for the T4 V1 input. |
| FEAT-018 `plan/CONTRACT_FREEZE.md` and feature decisions | Authority for the live integration registry and its current claims-shaped handoff. |
| `approvals/TASK_APPROVAL.md` in FEAT-003 and FEAT-018 | Approval authority. The FEAT-003 record remains unchanged until the owner separately approves the applicable scope. |
| Project owner | Approves the reconciliation scope and the final canonical identity/mapping. |

Person 2 owns the P2 ASR/vision/fusion research boundaries. FEAT-018/shared
integration owns the live integration contract and its downstream allocation.
P1 owns canonical activity/objective identity and is a consumer/reviewer of the
raw handoff, not an owner of the P2 provider contracts. No owner boundary is
transferred by this plan.

## 3. Contract-family inventory

### 3.1 P2-T2/P2-T3/P2-T4 research family

| Contract | Current source | Shape and invariant | Current state |
|---|---|---|---|
| P2 `AsrResultV1` | `backend/src/sketch2life/contracts/schemas/asr.py` | Discriminated success/failure union; original audio reference/hash, profile identity, attempt/repair semantics, transcript/segments/diagnostics or closed typed failure. | P2-T2 approved and implemented; input to T4 by plan. |
| P2 `VisionUnderstandingResultV1` | `backend/src/sketch2life/contracts/schemas/vision.py` | Discriminated success/failure union; nested image reference, observation IDs/references, `ObservedTextV1`, nullable-but-required candidate confidence, policy provenance, or closed typed failure. | P2-T3 Phase A approved/implemented; input to T4 by plan. |
| P2 `VisionUnderstandingResultV2` | `backend/src/sketch2life/contracts/schemas/vision_v2.py` | Separate V2 profile/catalog/request/result family for the approved Qwen study. | Approved T3 study family; not the T4 V1 input. |
| T4 fusion result baseline | `features/FEAT-003-multimodal-understanding/plan/P2_T4_FUSION_RESEARCH_PLAN.md` | Proposed source-preserving fused observations, typed upstream failure, conflicts, uncertainty, and active statuses `FUSED | UPSTREAM_FAILURE`. | Design baseline only; not frozen or implemented. |

### 3.2 FEAT-018 live/provider-shaped family

| Contract | Current source | Shape and consumers | Current state |
|---|---|---|---|
| Live `AsrResultV1` | `backend/src/sketch2life/contracts/schemas/understanding.py` | Flat model with `status`, `source_audio`, optional `transcript`/language/segments/quality, required `ModelProvenanceV1`, and optional `AdapterFailureV1`; consumed by the live route and provider-shaped adapters. | Implemented live development path. |
| Live `VisionUnderstandingResultV1` | `backend/src/sketch2life/contracts/schemas/understanding.py` | Flat model with `source_image`, defaulted collections, result-level uncertainty, plain label/confidence candidates, and `ModelProvenanceV1`; consumed by the live route and provider-shaped adapters. | Implemented live development path. |
| Live `RawUnderstandingResultV1` | FEAT-018 `plan/CONTRACT_FREEZE.md` and FEAT-015 expected fixture | Claims-shaped Gate A/P1 proposal with `claims[]`, `conflicts`, and `gate_a_required`; not the P2-T4 fused-candidate baseline. | Registry and fixture-backed integration identity. |

The reconciliation must also account for FEAT-018's use of P2-T3 V1/V2
references in its plans and fixture manifest. No document may silently call one
family the other.

## 4. Producer and consumer matrix

The following matrix is the inventory to reconcile. It intentionally records
current paths without changing them.

| Producer/boundary | Current contract family | Consumer or handoff | Compatibility question |
|---|---|---|---|
| `backend/src/sketch2life/application/ports/asr.py` | P2-T2 `AsrRequestV1` -> P2 `AsrResultV1` | P2-T4 fusion design; ASR benchmark runners | Can the P2 discriminator, source refs, and typed failures be consumed by the selected canonical handoff? |
| `backend/src/sketch2life/infrastructure/ai/fake_asr.py` | P2-T2 fixture fake | P2-T2 contract tests and future T4 fixtures | Preserve fake outputs and provenance; no live-family conversion may be hidden in the fake. |
| `backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py` and `backend/src/sketch2life/benchmark/asr_round1_runner.py` | P2-T2 real-adapter/benchmark family | P2-T2 evidence; future T4 input boundary | Keep provider-neutral result semantics and typed failure/attempt fields. |
| `backend/src/sketch2life/application/ports/vision_understanding.py` | P2-T3 V1 request -> P2 V1 vision result | P2-T4 fusion design and P2-T3 fixtures | Preserve nested image refs, observation references, policy state, and typed errors. |
| `backend/src/sketch2life/infrastructure/ai/fake_vision.py` and `vision_lexical_policy.py` | P2-T3 V1 fake/policy family | P2-T3 contract/evidence tests; future T4 fixtures | Do not import or emit the FEAT-018 flat family. |
| `backend/src/sketch2life/application/ports/vision_understanding_v2.py`, `qwen_vision.py`, and V2 benchmark modules | P2-T3 V2 study family | P2-T3 Phase B evidence only | Decide how V2 is identified at any integration boundary; do not silently map it as V1. |
| `backend/src/sketch2life/application/ports/understanding.py` | FEAT-018 live `AsrResultV1`/`VisionUnderstandingResultV1` | FEAT-018 live adapters and route | Decide whether this port remains isolated, is renamed/versioned, or receives an explicit adapter. |
| `backend/src/sketch2life/infrastructure/understanding/fixture_adapters.py` | FEAT-018 flat fixture family | FEAT-018 live route/tests | Preserve its existing fixture behavior until a reviewed migration is adopted. |
| `backend/src/sketch2life/infrastructure/understanding/whisper_adapter.py` and `qwen3_vl_adapter.py` | FEAT-018 provider-shaped adapters | `application/ports/understanding.py`; live route/tests | Map or isolate without accepting a P2 result under the same name by accident. |
| `backend/src/sketch2life/infrastructure/ai/lightning_client.py` | FEAT-018 live transport adapters | `interfaces/http/routers/live_understanding.py` | Keep provider credentials/endpoints in infrastructure; define the selected contract at the route boundary. |
| `backend/src/sketch2life/interfaces/http/routers/live_understanding.py` | FEAT-018 live request/result envelope | FEAT-017 live backend path and mobile proposal flow | Route must emit the selected versioned identity or an explicit mapping; no silent field translation. |
| FEAT-015 `fixtures/integration-fixture-v1/manifest.json` | Registry names `AsrResultV1`, `VisionUnderstandingResultV2`, and `RawUnderstandingResultV1` | FEAT-015 loader, flow, tests, and integration review | Reconcile the manifest registry and expected payloads with the selected identity/mapping. |
| FEAT-015 `fixtures/integration-fixture-v1/expected/asr-result.json` | Simplified live/provider-shaped ASR fixture | FEAT-015 loader/flow and live integration assumptions | Decide whether it remains an isolated fixture or receives a versioned migration fixture. |
| FEAT-015 `fixtures/integration-fixture-v1/expected/vision-result.json` | V2-shaped provider fixture | FEAT-015 loader/flow and P1/Gate A test path | Keep V2 explicit and prevent it from validating as P2 V1. |
| FEAT-015 `fixtures/integration-fixture-v1/expected/raw-understanding.json` | FEAT-018 claims-shaped raw proposal | FEAT-015 Gate A/P1 scenario harness | Preserve claims and `gate_a_required` or map them explicitly to the selected handoff. |
| FEAT-015 `src/integration_fixture/loader.py`, `flow.py`, and tests | Offline integration adapters and scenario oracle | FEAT-015 readiness review | Update only through an approved mapping/fixture change; this plan does not edit them. |
| FEAT-018 `plan/CONTRACT_FREEZE.md` | Shared registry and handoff table | Gate A/P1, mobile/session, all four person plans | The registry must name one identity/version or an explicit mapping and migration status. |
| FEAT-018 `plan/PERSON_2_AI.md` | P2 AI handoff expectations | P1 and mobile consumers | Replace ambiguous same-name references only after shared review. |
| FEAT-018 `plan/PERSON_1_DOMAIN.md`, `ENGINE_REFINEMENT_PLAN.md`, and `backend/src/sketch2life/contracts/schemas/p1_experience.py` | Gate A/P1 consumption of raw claims/anchors | P1 mapping and Gate B identity | Preserve Gate A, source claim provenance, and P1 ownership; P1 must not infer a new contract. |
| FEAT-017 `plan/PLAN.md`, `LIVE_AI_GUIDE.md`, and live evidence | Live provider-shaped route/proposal path | Mobile live mode, Gate A | Keep live provider path separate or explicitly mapped; no direct P2-T4 implementation is implied. |

The matrix is a review artifact. It does not authorize changing a producer,
consumer, registry, fixture, route, or downstream document.

## 5. Reconciliation deliverable

The approved workstream must produce one of the following explicit outcomes:

1. **One canonical versioned contract:** name the canonical serialized identity,
   schema/version, owner, producers, consumers, required fields, provenance,
   failure semantics, and deprecation/non-use status for the other family; or
2. **An explicit versioned mapping:** retain separately named source and target
   contracts, define the mapping boundary and direction, document every field
   preserved/dropped/rejected, identify the mapping owner and consumers, and
   specify when the mapping is applied and how it is versioned.

The deliverable must include a field-by-field comparison of both families, a
contract registry update proposal, an adoption decision, and a compatibility
report. It must not silently declare the current P2-T4 sketch canonical merely
because B0 selected reconciliation.

## 6. Compatibility and migration-fixture requirements

- The compatibility report must validate positive and negative payloads for every
  selected contract identity and version.
- It must cover success, typed upstream/provider failure, missing optional
  narration, source-reference/hash preservation, provenance, Gate A requirement,
  and prohibited-field rejection where those concepts exist in the selected
  shape.
- It must prove that a payload from the non-selected family cannot validate as
  the selected family without the explicitly named mapping.
- A breaking serialized change must use a new major/versioned identity, update
  every listed producer and consumer, and add a migration fixture, following
  FEAT-018 `CONTRACT_FREEZE.md`.
- A compatible optional change may use a reviewed minor contract version only
  when the selected authority and all consumers accept it; no optional field is
  chosen by this plan.
- The migration fixture must contain synthetic metadata only, use relative
  references, include old/new contract identity and hashes, and demonstrate the
  mapping or conversion deterministically. It must not contain raw child media,
  provider payloads, secrets, or absolute local paths.
- The fixture must include a rejected/rollback case and an unchanged-source
  assertion. Existing FEAT-015 and FEAT-018 fixtures remain preserved until an
  approved migration replaces or supersedes them.

## 7. Source, provenance, and prohibited-field constraints

- Preserve immutable original media references and their source hashes. A
  derived/working reference never silently replaces the original.
- Preserve the exact upstream result references and any selected mapping
  provenance. Do not fabricate model, adapter, configuration, actor, or source
  provenance.
- Do not copy raw transcript, image bytes, prompt text, raw provider output,
  credentials, endpoint URLs, signed URLs, or personal metadata into the
  mapping, fixture, logs, or evidence.
- Do not introduce personality, diagnosis, mental-state, trauma, developmental,
  or other psychological-inference fields.
- Preserve the active P2-T4 v1 design boundary: the result status set is exactly
  `FUSED | UPSTREAM_FAILURE`; `upstream_failure` is non-null exactly for
  `UPSTREAM_FAILURE` and null for `FUSED`.
- Preserve the nine owner decisions in FEAT-003 `DECISIONS.md`; the
  reconciliation may resolve identity/mapping questions but may not broaden
  narration, weighting, themes, negation scope, certainty, or failure semantics
  beyond those recorded decisions without a new owner decision.

## 8. Deterministic failure and validation behavior

The selected canonical contract or mapping must define deterministic, fail-closed
behavior for:

- unknown contract name or version;
- source payload from the wrong contract family;
- missing required field, extra field, malformed discriminator, or invalid enum;
- missing or inconsistent provenance/source reference/hash;
- unsupported mapping direction or unmappable field;
- stale session/version or incompatible registry entry, when those fields are
  present at the boundary; and
- migration-fixture or consumer compatibility failure.

Each failure must be a typed, redacted, versioned outcome at the agreed boundary,
or a documented boundary rejection where the selected contract explicitly
requires that behavior. No path may silently drop a field, coerce a contract
identity, fabricate a default, partially publish a result, or fall through to an
uncaught provider exception. The exact final error field names belong to the
selected contract/mapping review; this plan does not invent them.

## 9. Sequencing, rollback, and non-adoption

1. Capture the current registry, source, fixture, and approval baselines without
   editing or deleting any pre-existing artifact.
2. Review the inventory and producer/consumer matrix with P2, FEAT-018/shared
   integration, and P1/Gate A owners.
3. Compare field identity, requiredness, discriminator behavior, provenance,
   failure semantics, and downstream acceptance.
4. Select the canonical contract or explicit mapping and write the compatibility
   report and synthetic migration fixture.
5. Run the positive/negative, round-trip, provenance, redaction, and stale-version
   checks against the selected outcome.
6. Obtain separate approval for the reconciliation deliverable. Only then may
   the approved implementation owner update contracts, adapters, routes,
   fixtures, registries, or downstream consumers.
7. Obtain the separate P2-T4 implementation approval before writing fusion code,
   T4 fixtures, or T4 runtime wiring.

If the owner rejects the canonical shape/mapping, or if compatibility evidence
fails, do not adopt a partial result. Leave the current FEAT-018 live family and
P2 research family unchanged, mark the reconciliation non-adopted, preserve the
fixture and evidence baselines, and return to review with a new bounded proposal.
Rollback means disabling the new mapping/cutover and restoring the previously
approved family at its existing boundary; it never means rewriting source
media, deleting evidence, or force-updating a consumer.

## 10. Explicit non-goals

- No live provider work, model download, GPU/Lightning/Runpod execution, or
  dependency installation.
- No P2-T4 fusion implementation, conflict detector, schema implementation,
  migration code, or runtime wiring in this workstream.
- No FEAT-018 implementation, mobile/session/UI/database/queue/API integration,
  or production deployment.
- No change to P2-T2/P2-T3 source schemas, adapters, fixtures, evidence, or
  approvals while preparing the reconciliation plan.
- No P1 catalog/objective selection, Gate A/B implementation, renderer/media
  integration, or downstream behavioral change.
- No real child data, raw media, credentials, provider payloads, or absolute
  local paths.
- No final canonical shape or new schema field is selected by this plan merely
  to make the inventory complete.
- No approval is granted by this plan or its approval request.

## 11. Acceptance criteria for the reconciliation workstream

- [ ] The identity collision and both contract families are documented with
      exact source paths, versions, shapes, owners, and consumers.
- [ ] The producer/consumer matrix covers P2 ports/adapters, live routes,
      FEAT-015 fixtures/registry, FEAT-018 contract freeze, Gate A/P1, and
      FEAT-017 live-path references.
- [ ] The owner-approved outcome is exactly one canonical versioned contract or
      one explicit versioned mapping; no same-name ambiguity remains at the
      selected integration boundary.
- [ ] A field-by-field compatibility report proves requiredness, discriminator,
      provenance, failure, redaction, and source-preservation behavior.
- [ ] A synthetic migration fixture covers successful adoption, wrong-family or
      incompatible input rejection, rollback/non-adoption, and deterministic
      output without raw media or secrets.
- [ ] Every affected producer/consumer and registry entry has a reviewed update
      list, with no unapproved implementation performed.
- [ ] Downstream Gate A/P1 acceptance checks preserve adult confirmation,
      source claim provenance, and P1 canonical identity/version rules.
- [ ] Repository validators, relevant contract tests, link/path checks, security
      checks, and `git diff --check` pass after the approved workstream changes.
- [ ] The separate approval record names the exact reconciliation plan revision,
      scope, acceptance criteria, reviewer, and timestamp before implementation.

## 12. Repository validation requirements

Run from the worktree root after each meaningful approved reconciliation change
and before any commit/push:

```text
git diff --check
python tools/validate_harness.py
python tools/validate_architecture.py
python tools/validate_repository_security.py
python tools/validate_skeleton.py
```

Also run the focused contract/fixture tests and any available documentation/link
check. Review `git diff`, every staged path, staged diff, ignored-note status,
and the immutable P2-T3 baseline before commit. Run repository security
validation immediately before each commit and again immediately before push.

## 13. Approval gate

This plan requests approval for the bounded Blocker-0 contract-reconciliation
workstream only. It does not grant approval. No reconciliation implementation,
contract edit, migration, route/adapter change, fixture migration, or downstream
consumer change begins until the owner separately approves this exact scope.

Even after reconciliation approval, full P2-T4 fusion implementation remains
outside this request and requires its own plan/approval boundary. The FEAT-003
`TASK_APPROVAL.md` record must remain unchanged until an explicitly approved
scope is recorded through the repository governance process.

## 14. Unresolved shape questions for the implementation review

The following questions are intentionally listed for the separately approved
review; this plan does not choose new fields or a final shape:

1. Which serialized contract identity/version is canonical at the shared
   boundary, or what exact source/target identities does the mapping use?
2. Is the claims-shaped FEAT-018 handoff retained, replaced by the T4 fused
   observation baseline, or connected through an explicit versioned mapping?
3. Which producer owns the canonical result and which adapter owns conversion?
4. How are P2 `source_*_ref` values and the live family's nested/flat source
   references preserved without loss or ambiguity?
5. How are discriminated success/failure unions mapped to the live flat result,
   and how are live `PROPOSAL`/failure outcomes mapped to the active P2 status
   set?
6. How is optional/missing narration represented at the selected handoff while
   preserving the support-only narration decision?
7. Where do correlation/session/idempotency fields belong at the integration
   boundary, and which version/staleness checks are mandatory?
8. Which contract/version registry entries and FEAT-015/FEAT-018 fixtures are
   retained, superseded, or migrated?
9. What compatibility window and rollback/non-adoption rule applies to old
   consumers?
10. How does the separately named P2-T3 V2 study family remain explicit without
    being silently accepted as the P2-T3 V1 input?

No item above is resolved by implication. The implementation review must answer
each item in the approved decision/mapping record before any implementation
begins.
