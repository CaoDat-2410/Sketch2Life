# P2-T4 Blocker-0 contract reconciliation plan

- Status: **APPROVED FOR RECONCILIATION ONLY — PACKAGE COMPLETE; OWNER CONFIRMATION/ADOPTION PENDING**
- Date: 2026-09-13
- Lead: Person 2, with FEAT-018/shared-integration and P1/Gate A review
- Feature: FEAT-003 multimodal understanding
- Related plan: `P2_T4_FUSION_RESEARCH_PLAN.md`
- Approval request: `../evidence/notes/P2_T4_CONTRACT_RECONCILIATION_APPROVAL_REQUEST.md`

This is a bounded documentation and contract-reconciliation workstream. It is
not a contract implementation plan, a migration execution, or an approval to
change a producer or consumer. Its separate scope approval is recorded in
approvals/TASK_APPROVAL.md. The permitted outputs and edits remain limited to
the scope in Section 4.1; P2-T4 fusion implementation and adoption require
further approval.

## Current reconciliation status (2026-09-13)

The approved documentation-only package is complete. The report, synthetic
compatibility fixture, follow-up impact record, and independent technical and
governance reviews recommend one explicit versioned mapping family and record
the mapping as PROPOSED_NOT_ADOPTED. Owner confirmation of source preservation
and separate approval for registry cutover, migration, runtime mapping,
consumer updates, or P2-T4 implementation remain open.

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
current paths without changing them. FEAT-015/FEAT-018 code, existing fixture
baselines, loaders, flows, routes, adapters, ports, schemas, runtime wiring, and
downstream consumers named below are inspection-only under this approval. They
may be inspected and listed in the impact matrix, but they may not be edited.

| Producer/boundary | Current contract family | Consumer or handoff | Compatibility question |
|---|---|---|---|
| `backend/src/sketch2life/application/ports/asr.py` | P2-T2 `AsrRequestV1` -> P2 `AsrResultV1` | P2-T4 fusion design; ASR benchmark runners | Can the P2 discriminator, source refs, and typed failures be consumed by the selected canonical handoff? |
| `backend/src/sketch2life/infrastructure/ai/fake_asr.py` | P2-T2 fixture fake | P2-T2 contract tests and future T4 fixtures | Preserve fake outputs and provenance; no live-family conversion may be hidden in the fake. |
| `backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py` and `backend/src/sketch2life/benchmark/asr_round1_runner.py` | P2-T2 real-adapter/benchmark family | P2-T2 evidence; future T4 input boundary | Keep provider-neutral result semantics and typed failure/attempt fields. |
| `backend/src/sketch2life/application/ports/vision_understanding.py` | P2-T3 V1 request -> P2 V1 vision result | P2-T4 fusion design and P2-T3 fixtures | Preserve nested image refs, observation references, policy state, and typed errors. |
| `backend/src/sketch2life/infrastructure/ai/fake_vision.py` and `vision_lexical_policy.py` | P2-T3 V1 fake/policy family | P2-T3 contract/evidence tests; future T4 fixtures | Do not import or emit the FEAT-018 flat family. |
| `backend/src/sketch2life/application/ports/vision_understanding_v2.py`, `qwen_vision.py`, and V2 benchmark modules | P2-T3 V2 study family | P2-T3 Phase B evidence only | Record how V2 must be identified at any integration boundary; do not silently map it as V1 or change the V2 study artifacts. |
| `backend/src/sketch2life/application/ports/understanding.py` | FEAT-018 live `AsrResultV1`/`VisionUnderstandingResultV1` | FEAT-018 live adapters and route | Analyze whether this port remains isolated, is renamed/versioned, or receives an explicit adapter; record any change as follow-up. |
| `backend/src/sketch2life/infrastructure/understanding/fixture_adapters.py` | FEAT-018 flat fixture family | FEAT-018 live route/tests | Record the existing fixture behavior and any later, separately approved migration requirement; do not edit this adapter or baseline under this scope. |
| `backend/src/sketch2life/infrastructure/understanding/whisper_adapter.py` and `qwen3_vl_adapter.py` | FEAT-018 provider-shaped adapters | `application/ports/understanding.py`; live route/tests | Analyze the mapping/isolation boundary without changing the adapters or accepting a P2 result under the same name by accident. |
| `backend/src/sketch2life/infrastructure/ai/lightning_client.py` | FEAT-018 live transport adapters | `interfaces/http/routers/live_understanding.py` | Analyze the transport boundary needed to keep provider credentials/endpoints in infrastructure; record any route-contract change as follow-up. |
| `backend/src/sketch2life/interfaces/http/routers/live_understanding.py` | FEAT-018 live request/result envelope | FEAT-017 live backend path and mobile proposal flow | Analyze the required versioned identity or explicit mapping at the route boundary; do not change the route or silently translate fields. |
| FEAT-015 `fixtures/integration-fixture-v1/manifest.json` | Registry names `AsrResultV1`, `VisionUnderstandingResultV2`, and `RawUnderstandingResultV1` | FEAT-015 loader, flow, tests, and integration review | Analyze the manifest registry and expected-payload relationship to the selected identity/mapping; do not edit the manifest under this scope. |
| FEAT-015 `fixtures/integration-fixture-v1/expected/asr-result.json` | Simplified live/provider-shaped ASR fixture | FEAT-015 loader/flow and live integration assumptions | Record whether it remains isolated or needs a separately approved migration; do not modify this existing fixture baseline. |
| FEAT-015 `fixtures/integration-fixture-v1/expected/vision-result.json` | V2-shaped provider fixture | FEAT-015 loader/flow and P1/Gate A test path | Verify in the impact analysis that V2 remains explicit and cannot validate as P2 V1; do not edit the fixture or test path. |
| FEAT-015 `fixtures/integration-fixture-v1/expected/raw-understanding.json` | FEAT-018 claims-shaped raw proposal | FEAT-015 Gate A/P1 scenario harness | Record compatibility and follow-up ownership for claims and `gate_a_required`; do not edit the existing fixture. |
| FEAT-015 `src/integration_fixture/loader.py`, `flow.py`, and tests | Offline integration adapters and scenario oracle | FEAT-015 readiness review | Inspect and list required mapping/fixture changes as follow-up; do not edit the loader, flow, or tests under this scope. |
| FEAT-018 `plan/CONTRACT_FREEZE.md` | Shared registry and handoff table | Gate A/P1, mobile/session, all four person plans | Analyze the registry and handoff requirement; only a narrow identity/mapping documentation record may be proposed, not a registry cutover. |
| FEAT-018 `plan/PERSON_2_AI.md` | P2 AI handoff expectations | P1 and mobile consumers | Record ambiguous same-name references and follow-up ownership; do not change the handoff or consumers under this scope. |
| FEAT-018 `plan/PERSON_1_DOMAIN.md`, `ENGINE_REFINEMENT_PLAN.md`, and `backend/src/sketch2life/contracts/schemas/p1_experience.py` | Gate A/P1 consumption of raw claims/anchors | P1 mapping and Gate B identity | Record downstream acceptance checks while preserving Gate A, source claim provenance, and P1 ownership; do not change behavior or code. |
| FEAT-017 `plan/PLAN.md`, `LIVE_AI_GUIDE.md`, and live evidence | Live provider-shaped route/proposal path | Mobile live mode, Gate A | Record the live-path isolation/mapping follow-up; do not change the route, consumer, or live behavior under this scope. |

The matrix is a review artifact. It does not authorize changing a producer,
consumer, registry, fixture, route, or downstream document.

### 4.1 In-scope repository surfaces after separate approval

After separate approval, the Blocker-0 reconciliation workstream may produce or
edit only the following:

- documentation and contract-registry analysis;
- the field-by-field compatibility matrix and compatibility report;
- a clearly named, synthetic-only migration/compatibility fixture created as a
  new artifact, plus its feature-local evidence; this artifact is additive and
  may not replace or modify an existing fixture baseline;
- explicit follow-up ownership and acceptance checks for any required
  downstream change; and
- narrowly scoped documentation updates required to record the selected
  canonical identity or explicit mapping, including a registry or handoff note
  only where that record is necessary. Such documentation updates do not
  change behavior or authorize a registry cutover.

FEAT-015/FEAT-018 code and existing fixture baselines, including manifests,
expected payloads, loaders, flows, routes, adapters, ports, schemas, runtime
wiring, and downstream consumers, may be inspected and listed in the impact
matrix and follow-up record only. They are not editable under this scope.
P2-T2/P2-T3 contracts, adapters, fixtures, evidence, and approvals, and P1/Gate
A behavior, are likewise inspection/reference material only. The workstream may
record a required follow-up and its acceptance checks; it does not perform that
follow-up.

The following are not allowed under this approval:

- modifying any existing FEAT-015 or FEAT-018 fixture baseline;
- changing loaders, flows, routes, adapters, ports, schemas, runtime wiring, or
  downstream consumers;
- executing a migration or cutover;
- changing P2-T2/P2-T3 contracts, adapters, fixtures, evidence, or approvals;
- changing P1/Gate A behavior; or
- implementing the P2-T4 fusion contract or fusion logic.

Any required code change, existing-fixture migration, route/adapter/consumer
update, registry cutover, or runtime behavior change must be listed as a
follow-up scope and receive separate explicit approval before execution.

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
contract-registry analysis and, if needed, a narrowly scoped documentation
update proposal for the selected identity/mapping, an adoption decision, and a
compatibility report. It must not silently declare the current P2-T4 sketch
canonical merely because B0 selected reconciliation.

## 6. Compatibility and migration-fixture requirements

- The compatibility report must validate positive and negative payloads for every
  selected contract identity and version.
- It must cover success, typed upstream/provider failure, missing optional
  narration, source-reference/hash preservation, provenance, Gate A requirement,
  and prohibited-field rejection where those concepts exist in the selected
  shape.
- It must prove that a payload from the non-selected family cannot validate as
  the selected family without the explicitly named mapping.
- A breaking serialized change identified for later adoption must use a new
  major/versioned identity, identify every producer and consumer that a
  separately approved follow-up would update, and add a migration fixture,
  following FEAT-018 `CONTRACT_FREEZE.md`; those producer/consumer updates are
  not performed under this scope.
- A compatible optional change may use a reviewed minor contract version only
  when the selected authority and all consumers accept it; no optional field is
  chosen by this plan.
- The migration fixture must contain synthetic metadata only, use relative
  references, include old/new contract identity and hashes, and demonstrate the
  mapping or conversion deterministically. It must not contain raw child media,
  provider payloads, secrets, or absolute local paths.
- The fixture must include a rejected/rollback case and an unchanged-source
  assertion. The new fixture is additive. Existing FEAT-015 and FEAT-018
  fixtures remain preserved and unmodified throughout this workstream; any
  migration that replaces or supersedes them is follow-up scope requiring
  separate explicit approval.

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
6. Obtain separate approval for the reconciliation deliverable. After that
   approval, this Blocker-0 workstream may complete only the allowed analysis,
   matrix/report, new synthetic fixture, follow-up ownership/checks, and narrow
   identity/mapping documentation listed in Section 4.1. It may not update any
   existing code, fixture, loader, flow, route, adapter, port, schema, runtime
   wiring, downstream consumer, or execute a registry cutover; these actions are not allowed under this workstream. Any such required change is follow-up scope and requires separate explicit approval.
7. Obtain the separate P2-T4 implementation approval before writing fusion code,
   T4 fixtures, or T4 runtime wiring.

If the owner rejects the canonical shape/mapping, or if compatibility evidence
fails, do not adopt a partial result. Leave the current FEAT-018 live family and
P2 research family unchanged, mark the reconciliation non-adopted, preserve the
fixture and evidence baselines, and return to review with a new bounded proposal.
This workstream only documents rollback/non-adoption criteria. For a later,
separately approved adoption, rollback means disabling the new mapping/cutover
and restoring the previously approved family at its existing boundary; this
workstream does not execute that action, rewrite source media, delete evidence, or force-update a consumer.

## 10. Explicit non-goals

- No live provider work, model download, GPU/Lightning/Runpod execution, or
  dependency installation.
- No P2-T4 fusion implementation, conflict detector, schema implementation,
  migration code, or runtime wiring in this workstream.
- No FEAT-018 implementation, mobile/session/UI/database/queue/API integration,
  or production deployment.
- No modification to FEAT-015/FEAT-018 existing fixture baselines, loaders,
  flows, routes, adapters, ports, schemas, runtime wiring, or downstream
  consumers; those surfaces are inspection-only.
- No change to P2-T2/P2-T3 contracts, adapters, fixtures, evidence, or
  approvals under this workstream.
- No P1 catalog/objective selection, Gate A/B implementation, renderer/media
  integration, or downstream behavioral change.
- No real child data, raw media, credentials, provider payloads, or absolute
  local paths.
- No final canonical shape or new schema field is selected by this plan merely
  to make the inventory complete.
- No approval is granted by this plan or its approval request.

## 11. Acceptance criteria for the reconciliation workstream

- [ ] The permitted output classes are limited to documentation and
      contract-registry analysis, the compatibility matrix/report, a new
      synthetic-only compatibility/migration fixture, explicit follow-up
      ownership and acceptance checks, and narrowly scoped identity/mapping
      documentation; no implementation or runtime change is performed.
- [ ] FEAT-015/FEAT-018 code and existing fixtures, including loaders, flows,
      routes, adapters, ports, schemas, runtime wiring, and downstream
      consumers, are inspection-only and are listed in the impact/follow-up
      record without being edited.
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
- [ ] Every inspected producer/consumer and registry entry has a reviewed
      impact/follow-up list; only a narrowly scoped documentation record of the
      selected identity/mapping may be updated here, and any code,
      existing-fixture, runtime/consumer, or registry-cutover update has
      separate explicit approval.
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
workstream only. It does not grant approval. No code/schema/runtime change,
existing-fixture migration, registry cutover, route/adapter/port/loader/flow
change, or downstream consumer change begins until the owner separately approves
the applicable follow-up scope. The allowed Blocker-0 outputs remain limited to
Section 4.1.

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
