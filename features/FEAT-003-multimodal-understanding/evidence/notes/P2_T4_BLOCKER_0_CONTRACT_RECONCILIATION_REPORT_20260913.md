# P2-T4 Blocker-0 contract reconciliation report

- Evidence ID: EV-003-T4-RECON-02
- Date: 2026-09-13
- Worktree baseline: branch plan/person-2-multimodal-fusion-conflict-detection, baseline HEAD 93e503f3807805d7ce343fc7b5ed6f67e6b110ef
- Status: PROPOSED RECONCILIATION OUTCOME — REVIEW COMPLETE; OWNER CONFIRMATION AND ADOPTION APPROVAL PENDING
- Governing approval: features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md, current P2-T4 Blocker-0 approval
- Companion fixture: features/FEAT-003-multimodal-understanding/fixtures/p2-t4-contract-reconciliation-v1/manifest-v1.json
- Companion follow-up record: P2_T4_CONTRACT_RECONCILIATION_FOLLOW_UP_IMPACT_20260913.md

This is a documentation and synthetic-compatibility evidence record. It is not a
schema, runtime adapter, registry cutover, migration execution, fusion
implementation, or approval for adoption. The same serialized contract name is
therefore shown with an explicit reconciliation namespace below. The namespace is
a review identity marker only; it does not alter any existing serialized payload.

## 1. Outcome

The current repository contains three material identity collisions:

1. P2-T2 owns a provider-neutral, discriminated AsrResultV1 in
   backend/src/sketch2life/contracts/schemas/asr.py. The live/provider-shaped
   AsrResultV1 in backend/src/sketch2life/contracts/schemas/understanding.py
   has the same serialized name and version but a different envelope, required
   fields, and failure model.
2. P2-T3 owns a provider-neutral, discriminated
   VisionUnderstandingResultV1 in
   backend/src/sketch2life/contracts/schemas/vision.py. The live/provider-shaped
   VisionUnderstandingResultV1 in understanding.py has the same serialized
   name and version but different source, observation, uncertainty, policy, and
   provenance semantics.
3. FEAT-018's registry/fixture handoff uses
   RawUnderstandingResultV1 for a claims-shaped Gate A proposal, while the
   P2-T4 research baseline uses that name for a fused observation result with
   FUSED | UPSTREAM_FAILURE statuses, source-result references, conflicts,
   uncertainty, and typed upstream-failure references.

The same name is not sufficient evidence of compatibility. A payload must match
the family identity, exact version, discriminator branch, requiredness,
provenance, source-reference rules, privacy policy, and downstream acceptance
rules.

### Reconciliation recommendation

Recommend Option B: one explicit, versioned mapping family
P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0 with three named directional
edges:

| Edge | Source identity | Target identity | Boundary |
|---|---|---|---|
| ASR input reconciliation | FEAT018.LiveAsrResultV1@1.0 | P2.AsrResultV1@1.0 | Live/provider-shaped result into the P2-T4 provider-neutral input |
| Vision input reconciliation | FEAT018.LiveVisionUnderstandingResultV1@1.0 | P2.VisionUnderstandingResultV1@1.0 | Live/provider-shaped result into the P2-T4 provider-neutral input |
| Gate A handoff reconciliation | P2T4.ProposedFusedRawUnderstandingResultV1@1.0 | FEAT018.RawUnderstandingResultV1@1.0 | P2-T4 design output toward the existing FEAT-018 Gate A/P1 handoff |

The mapping family is explicitly fail-closed. It admits a case only when exact
source/target identity and version are known and every required source field is
preserved either in the target or in an explicitly approved mapping envelope.
It rejects missing provenance, missing source hashes, missing discriminators,
unknown versions, wrong-family inputs, prohibited content, and fields without a
declared loss/rejection rule. It never fabricates a default, changes a
discriminator by string matching, or silently flattens a typed observation.

This is a proposed reconciliation outcome, not a final canonical contract or
adoption decision. The P2-T4 fused identity remains a design baseline only. The
existing FEAT-018 family, P2-T2/P2-T3 contracts, and FEAT-015 fixture remain
unchanged in this worktree. The positive fixture case is therefore
MAPPING_ADMISSIBLE_FOR_OWNER_REVIEW with adoption deliberately not applied.

### What the evidence establishes

- A single shared serialized V1 identity cannot be adopted without dropping or
  inventing fields.
- A conditional, explicit mapping is safer than a silent alias or a
  replacement of either family.
- The current FEAT-015 compact expected payloads are negative compatibility
  inputs for the P2 envelopes; their names do not make them P2-schema-valid.
- The P2-T3 V2 family is a separate identity and is not the P2-T3 V1 input or
  the P2-T4 V1 input.
- The current worktree has no runtime mapping, registry cutover, or source
  mutation to roll back.

## 2. Authority, source precedence, and baseline

Source precedence for this review was:

1. The direct task brief and repository AGENTS.md.
2. The current approved P2-T4 Blocker-0 section of
   features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md.
3. The accepted Sprint 1 allocation rules in
   docs/adr/ADR-0006-parallel-sprint-allocation.md and the governance
   workflow/policy.
4. FEAT-003 CONTEXT.md, DECISIONS.md, the P2-T2/P2-T3 schemas and plans,
   and the P2-T4 research/reconciliation plans.
5. The FEAT-018 contract freeze and P1/Gate A plans.
6. The existing FEAT-015 manifest, expected artifacts, loader, flow, and tests.
7. FEAT-017 live-path documentation and the inspected route/transport boundary.

The pre-edit baseline was verified on the target branch: the worktree was clean,
HEAD and upstream both pointed to 93e503f, and no P2-T3 source, fixture,
evidence, or approval file was changed before this package was created. The
fixture below records immutable source hashes captured from that baseline.

| Evidence/source | Role | SHA-256 |
|---|---|---|
| features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md | Current Blocker-0 approval authority | 460134d3a7ad06feb91797382f7c521f1d23541559ed085acc174084aa8a69c1 |
| features/FEAT-003-multimodal-understanding/plan/P2_T2_ASR_RESEARCH_PLAN.md | P2 ASR contract/ownership boundary | d688e227d72b262324b2d895aeaa51b67a032b492b0deb512c905dd174b9710f |
| features/FEAT-003-multimodal-understanding/plan/P2_T3_VISION_RESEARCH_PLAN.md | P2 vision contract/ownership boundary | 88158620cbb3fcc3a140f7d41744b36f901031a321eccaa0b1fff829fc5864d1 |
| features/FEAT-003-multimodal-understanding/plan/P2_T4_FUSION_RESEARCH_PLAN.md | T4 design baseline and nine decisions | f8e138ac23810efac96893f98c1f5e275746f544cff74d25fcbfbffb20f2e8e8 |
| features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md | Approved-scope reconciliation plan, status updated after review | f44b38f01c3f00890c73264c2be8d9be5264519b7ccb64734208355862598539 |
| features/FEAT-018-live-image-canvas-flow/plan/CONTRACT_FREEZE.md | FEAT-018 registry and Gate A/P1 handoff | 156061b5132342e9742839685e187fdc7eb247d85778c4d64e0824c03fa7c063 |
| backend/src/sketch2life/contracts/schemas/asr.py | P2 ASR schema source | 1dcf8db144ebfd080266f05b8e75ae404ec230edc7983937a0e598e48c0b9b22 |
| backend/src/sketch2life/contracts/schemas/vision.py | P2 vision V1 schema source | c3f2719c593d443404b90e22013dcaec4cd8befed9dc6a985c0214766c3a90f4 |
| backend/src/sketch2life/contracts/schemas/vision_v2.py | P2 vision V2 schema source | ee7d35c7dbdc2d8661aa6da1b4b43ae82f21d4092519b36614193d55e905470e |
| backend/src/sketch2life/contracts/schemas/understanding.py | FEAT-018/live provider-shaped schema source | c386e313b7cfd313d7f064c9ec66707b287d4a803d4092d7255a4cb0493bd2bd |
| features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/manifest.json | Existing fixture registry | 1dd3318713a35c93e29cb66adb552444e28e3447a4be7cd4bb1f0d75331aa8be |
| features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/expected/asr-result.json | Existing ASR fixture baseline | fdd6b0a4d42b1159c39f9dad16a9024c3ba8bea0b33d7fd928cbd58b387e0af5 |
| features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/expected/vision-result.json | Existing V2-labelled vision fixture baseline | c517cf97df0483845af755d7e16dc450ea1ad2637da6daee6f4ee23ef8289443 |
| features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/expected/raw-understanding.json | Existing claims-shaped raw baseline | e3c469d44c9b48fc838d33c731c09831eaa9fa1d96981685dc9407d3802998be |
| features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/provenance/source-register.json | Existing synthetic/provenance declaration | 51fdad19ac8cb5bf938eb8b44651e7905a6c9dac3bacd46764f98e106ec725fb |

The current reconciliation worktree contains the FEAT-018 live/provider-shaped
schema and the FEAT-018 registry documents. It does not contain a separate
raw_understanding.py implementation module. The FEAT-018
RawUnderstandingResultV1 identity is consequently recorded here from the
contract-freeze registry and the existing FEAT-015 expected artifact, not
inferred from an absent source file.

## 3. Contract-family inventory

The namespace prefixes in this section are review-only identity markers.
Serialized names and versions are the values currently present in their source
artifacts.

| Review identity | Serialized name/version | Authoritative source | Required shape/status | Producer and consumer boundary | Owner/state |
|---|---|---|---|---|---|
| P2.AsrResultV1@1.0 | AsrResultV1 / 1.0 | backend/src/sketch2life/contracts/schemas/asr.py | Discriminated AsrSuccessV1 / AsrFailureV1; source audio hash/ref, resolved profile, attempt/repair, diagnostics or typed error | P2 ASR port/fake/adapter and benchmark; proposed P2-T4 input | Person 2; approved P2-T2 contract |
| P2.VisionUnderstandingResultV1@1.0 | VisionUnderstandingResultV1 / 1.0 | backend/src/sketch2life/contracts/schemas/vision.py | Discriminated success/failure; nested image ref, observation IDs/references, policy provenance, five collections, typed failure | P2 vision port/fake/policy and proposed P2-T4 input | Person 2; approved P2-T3 V1 contract |
| P2.VisionUnderstandingResultV2@2.0 | VisionUnderstandingResultV2 / 2.0 | backend/src/sketch2life/contracts/schemas/vision_v2.py | Separate V2 profile/catalog/model-provenance family; discriminated success/failure | P2-T3 V2 study, Qwen boundary, V2 evidence | Person 2; adjacent study family, not T4 V1 input |
| FEAT018.LiveAsrResultV1@1.0 | AsrResultV1 / 1.0 | backend/src/sketch2life/contracts/schemas/understanding.py | Flat status model; nested source_audio, optional transcript/segments/quality, required ModelProvenanceV1, optional typed AdapterFailureV1 | application/ports/understanding.py, live provider-shaped adapters, live route | FEAT-018/shared integration; implemented live-dev boundary |
| FEAT018.LiveVisionUnderstandingResultV1@1.0 | VisionUnderstandingResultV1 / 1.0 | backend/src/sketch2life/contracts/schemas/understanding.py | Flat status model; nested source_image, defaulted plain collections, scalar uncertainty, required ModelProvenanceV1 | Same live port/adapter/route family | FEAT-018/shared integration; implemented live-dev boundary |
| FEAT018.RawUnderstandingResultV1@1.0 | RawUnderstandingResultV1 / 1.0 | features/FEAT-018-live-image-canvas-flow/plan/CONTRACT_FREEZE.md and FEAT-015 expected artifact | Claims-shaped proposal with source modality, confidence, conflicts, and gate_a_required; existing fixture status is PROPOSAL | Gate A/P1 and FEAT-015 offline flow | FEAT-018 registry handoff; current baseline |
| P2T4.ProposedFusedRawUnderstandingResultV1@1.0 | RawUnderstandingResultV1 / 1.0 | features/FEAT-003-multimodal-understanding/plan/P2_T4_FUSION_RESEARCH_PLAN.md | Design-only fused result with source result refs, fusion-policy hash, five fused collections, conflicts, uncertainty summary, typed upstream-failure refs, statuses FUSED / UPSTREAM_FAILURE | Future P2-T4 fusion output toward Gate A/P1 | Person 2; not frozen or implemented |

The FEAT-015 manifest additionally registers VisionUnderstandingResultV2
and RawUnderstandingResultV1 for its existing package. The V2-labelled
expected file is a compact fixture shape and does not contain the full P2 V2
envelope. The raw expected file is the claims-shaped baseline. Neither file may
be reclassified by name alone.

## 4. Producer, consumer, route, and registry matrix

Every row below was inspected or referenced only. Existing code, route,
adapter, port, schema, loader, flow, consumer, and fixture artifacts remain
inspection-only under the approved scope.

| Producer/boundary | Current family | Consumer/handoff | Reconciliation finding and later owner |
|---|---|---|---|
| backend/src/sketch2life/application/ports/asr.py | P2 AsrRequestV1 -> P2.AsrResultV1 | P2-T4 design and ASR benchmark/fake boundary | Preserve P2 discriminator, source hash, profile, attempt/repair, diagnostics, and typed failure. Person 2 owns semantics. |
| backend/src/sketch2life/infrastructure/ai/fake_asr.py | P2 deterministic ASR fixture | P2-T2 contract tests and future T4 fixtures | Keep fake outputs in P2 family; no hidden FEAT-018 conversion. Person 2 follow-up only. |
| backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py and backend/src/sketch2life/benchmark/asr_round1_runner.py | P2 provider-neutral ASR adapter/benchmark | P2 evidence and future T4 input | Preserve profile/config/provenance and retry/repair semantics. Any live-family bridge needs the mapping edge and separate approval. |
| backend/src/sketch2life/application/ports/vision_understanding.py | P2 V1 request/result | P2-T4 design and P2-T3 fixtures | Preserve nested image refs, observation IDs, policy state, nullable confidence semantics, and typed error matrix. |
| backend/src/sketch2life/infrastructure/ai/fake_vision.py and vision_lexical_policy.py | P2 V1 fake/policy | P2-T3 contract/evidence tests and future T4 input | Do not import or emit the FEAT-018 flat family. |
| backend/src/sketch2life/application/ports/vision_understanding_v2.py, qwen_vision.py, and V2 benchmark modules | P2 V2 study family | P2-T3 V2 evidence | V2 is explicit and must be rejected at the P2-T4 V1 boundary. No V1/V2 name coercion. |
| backend/src/sketch2life/application/ports/understanding.py | FEAT-018 flat ASR/Vision family | FEAT-018 provider-shaped adapters and live route | Same Python port names do not establish P2 identity. A separately approved adapter must implement the two family-mapping edges. |
| backend/src/sketch2life/infrastructure/understanding/fixture_adapters.py | FEAT-018 flat fixture family | FEAT-018 live route/tests | Existing fixture behavior remains unchanged. A later versioned fixture/migration is required if this boundary moves. |
| backend/src/sketch2life/infrastructure/understanding/whisper_adapter.py and qwen3_vl_adapter.py | FEAT-018 provider-shaped adapters | application/ports/understanding.py and live route | Their output must not be accepted as P2 results under the same serialized name without explicit mapping metadata. |
| backend/src/sketch2life/infrastructure/ai/lightning_client.py | FEAT-018 live transport and flat-contract adapters | interfaces/http/routers/live_understanding.py | Provider credentials/endpoints stay in infrastructure. A later route/adapter change must use the mapping record and sanitized typed failures. |
| backend/src/sketch2life/interfaces/http/routers/live_understanding.py | FEAT-018 live request plus outer LiveUnderstandingResultV1 proposal envelope | FEAT-017 live backend path and mobile proposal flow | Outer PROPOSAL/FAILED status is not a P2 FUSED/UPSTREAM_FAILURE discriminator. Route migration is separate follow-up. |
| features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/manifest.json | Existing registry names AsrResultV1, VisionUnderstandingResultV2, RawUnderstandingResultV1 | FEAT-015 loader, flow, tests, integration review | Preserve manifest and hash. Add a new fixture/version only under a later migration approval. |
| FEAT-015 expected/asr-result.json | Compact/provider-shaped ASR baseline | FEAT-015 loader/flow and live assumptions | It lacks P2 envelope metadata; negative compatibility case. Do not edit or relabel it here. |
| FEAT-015 expected/vision-result.json | Compact V2-labelled vision baseline | FEAT-015 loader/flow and P1/Gate A test path | V2 identity is explicit, but the compact payload is not full P2 V2. Negative compatibility case. |
| FEAT-015 expected/raw-understanding.json | Claims-shaped FEAT-018 raw proposal | FEAT-015 Gate A/P1 scenario harness | Does not satisfy the T4 fused-result baseline. Preserve claims and Gate A behavior; migration is follow-up. |
| features/FEAT-015-integration-readiness-review/src/integration_fixture/loader.py, flow.py, and tests | Offline fixture oracle and scenario transitions | FEAT-015 readiness review | Existing loader/flow/test behavior remains unchanged. Owner must add a new versioned path if adoption is approved. |
| features/FEAT-018-live-image-canvas-flow/plan/CONTRACT_FREEZE.md | Shared registry and FEAT-018 handoff table | Gate A/P1, mobile/session, all four person plans | Registry note may be updated only after owner confirms the mapping; no cutover is performed here. |
| features/FEAT-018-live-image-canvas-flow/plan/PERSON_2_AI.md | P2 AI handoff expectations | P1 and mobile consumers | Same-name references require the explicit mapping identity and source preservation. Documentation follow-up owner: FEAT-018/shared integration with Person 2. |
| features/FEAT-018-live-image-canvas-flow/plan/PERSON_1_DOMAIN.md and backend/src/sketch2life/contracts/schemas/p1_experience.py | Gate A/P1 candidate and exact activity/objective identity | P1 mapping and Gate B | Preserve adult confirmation, source claims, context, and exact catalog versions. No P1 behavior change. |
| features/FEAT-018-live-image-canvas-flow/plan/ENGINE_REFINEMENT_PLAN.md | Proposed SemanticAnchorSetV1 and later handoffs | P1/P3/P4/shared engine slices | T4 output remains a proposal; anchor/spec mapping is a separate approved workstream. |
| features/FEAT-017-live-ai-dev-integration/LIVE_AI_GUIDE.md and live evidence | FEAT-018/017 provider-shaped live path | Mobile live mode and Gate A | Keep provider details backend-only and Gate A mandatory. Live route/consumer reconciliation is follow-up. |

## 5. Field-by-field compatibility matrix

The mapping decisions use four classifications:

- PRESERVE: exact semantic preservation, with a documented field rename allowed
  only when the source and target meaning are identical.
- PROJECT: a derived target view may be produced only when the source remains
  available through the approved mapping envelope and every loss is explicit.
- REJECT: the input is not admissible at that boundary.
- PROHIBITED SYNTHESIS: no default, inferred value, identity coercion, or
  fabricated provenance is allowed.

### 5.1 Identity, envelope, source, and provenance

| Field/concern | P2-T2/P2-T3/T4 side | FEAT-018/live side | Mapping decision | Owner and migration impact |
|---|---|---|---|---|
| contract_name, contract_version | Literal names/versions; P2 ASR and V1 vision are both 1.0; T4 design also sketches RawUnderstandingResultV1@1.0 | Live ASR/Vision use the same serialized V1 names; FEAT-018 raw also uses RawUnderstandingResultV1@1.0 | REJECT name-only matching. Use P2, FEAT018, and P2T4 review identities and an exact mapping edge. | Shared registry owner plus Person 2; any adopted alias/version requires a separately approved registry update. |
| status and discriminator | ASR/Vision are discriminated SUCCEEDED / FAILED; T4 raw is exactly FUSED / UPSTREAM_FAILURE | Flat live ASR/Vision also use SUCCEEDED / FAILED; live outer route/fixture uses PROPOSAL / FAILED; FEAT-018 raw fixture uses PROPOSAL | REJECT string substitution. A status branch must be mapped by an explicit table and validated against the branch payload. | Person 2 owns P2/T4 status semantics; FEAT-018/shared owns target status and Gate A behavior. |
| correlation_id | Required on P2 ASR/Vision results and T4 design; echoed from request | Absent from flat understanding.py result models; route has request/session/request identifiers outside the result | PRESERVE only through an explicit transport/mapping envelope. PROHIBITED SYNTHESIS if absent. | Shared integration follow-up; route and consumer changes require separate approval. |
| session_id, expected_session_version, request_id, idempotency | P2 plans require transport/session metadata around requests; not a substitute for result identity | Live route request carries session/version/request fields; returned outer proposal echoes request metadata | PRESERVE at transport boundary; do not silently move these into a result or use them as contract identity. | Shared integration/FEAT-016 owner; no session/runtime change here. |
| executed_at | Required timezone-aware P2 ASR/Vision result envelope; T4 design requires it | Absent from live flat result models; route has no typed equivalent in the result model | REJECT when missing; no timestamp default. | Person 2 and shared integration follow-up. |
| attempt_number, repair_attempted | Required P2 ASR/Vision envelopes, bounded and tied to typed failure matrices | Absent from live flat results; live adapter retry exists in infrastructure but does not publish P2 attempt fields | PRESERVE only if captured at the P2 boundary; never infer from a generic retry count or default to 1. | Adapter owner follow-up; tests/evidence must cover both branches. |
| source_audio_ref / source_image_ref | P2 nested refs carry artifact identity and lowercase SHA-256; P2 vision rejects absolute machine paths; T4 retains source result refs | Live uses source_audio/source_image nested SourceMediaReferenceV1; old FEAT-015 expected payloads use compact artifact IDs | RENAME-ONLY if artifact ref, status, and hash are all present and unchanged. Existing compact IDs alone are REJECTED. | P2 owns source semantics; FEAT-015 migration must add a new version/fixture rather than edit v1. |
| source_asr_result_ref, source_vision_result_ref | Required by T4 design to identify exact upstream result artifacts | Not present in FEAT-018 raw claims baseline | PRESERVE in mapping envelope or REJECT; never replace with a display label or request ID. | Person 2 plus shared integration; required for audit and rollback. |
| Processing/derivation references | P2 requests allow optional working-copy refs only with a complete hash chain to the original | Live result family has no equivalent output fields | PRESERVE or REJECT when supplied; never discard a derivation chain. | P2 adapter follow-up. |
| Media-validation provenance | P2 request contracts accept typed validation provenance and require a passing source at the correct boundary | Live request uses a literal PASS plus source model, while the result does not retain P2 validation metadata | PRESERVE only in an approved envelope; do not turn a literal PASS into a P2 validation artifact or default its hash. | P2/shared integration; later migration fixture required. |
| Profile/catalog identity | P2 ASR resolves requested_profile_id against AsrProfileCatalogV1; P2 vision V1 has profile/catalog hash; V2 has a disjoint V2 catalog | Live ModelProvenanceV1 carries provider/model/adapter/config strings but no P2 catalog identity | REJECT unresolved profiles. A model string is not a profile/catalog identity, and V2 profile IDs never validate as V1. | Person 2 owns profile identity; no profile freeze/default is implied. |
| Model/config provenance | P2 ASR success carries model/revision/adapter/runtime/config hash; P2 V1 vision carries adapter/config; V2 carries structured model/weight/dependency provenance | Live requires provider/model/adapter/config version but has different semantics and no P2 branch rules | PROJECT only under a reviewed field table with semantic equality. Do not coerce a config hash to a version or invent model provenance on an input-failure branch. | Person 2 owns source provenance; FEAT-018/shared owns target serialization. |
| Privacy/prohibited fields | P2 V1/V2 policy rejects six prohibited psychological/diagnostic categories and forbids raw provider details | Live schemas have no equivalent P2 policy envelope, but route/adapter redaction rules forbid raw payloads, prompts, credentials, and endpoints | REJECT privacy-invalid inputs before projection. No raw content is included in this package. | Person 2 and FEAT-018/shared; redaction acceptance remains mandatory. |
| Unknown/ambiguous identity | P2 and FEAT-018 each have closed names/version expectations | Same serialized name can resolve to multiple families | REJECT before field validation; never pick the nearest version or import path. | Registry owner; mapping registry entry must remain explicit. |

### 5.2 ASR content, quality, and failure fields

| Field/concern | P2 AsrResultV1 | FEAT-018/live AsrResultV1 | Mapping decision | Owner and impact |
|---|---|---|---|---|
| Success payload branch | AsrSuccessV1 requires transcript_raw, speech diagnostic, detected language/probability, segments, duration/VAD, model/revision/adapter/runtime/config hash, and quality metadata | Flat success requires a non-null transcript, available source, quality, and no failure; its provenance is the live ModelProvenanceV1 | RENAME-ONLY for the minimal transcript/language subset; complete success metadata must remain in the mapping envelope or the case is REJECTED. | Person 2 owns P2 result; live adapter owner must not broaden the flat model implicitly. |
| Transcript | P2 transcript_raw is an ASR proposal and may be empty on a successful quiet result | Live transcript is optional in the model but required by its success validator | PRESERVE value only; transcript_raw -> transcript is allowed only when the status branch is valid. Do not turn a missing value into an empty string. | Person 2; T4 support-only narration remains unchanged. |
| Language | P2 has detected_language, language_probability, hint echo/applied semantics | Live has language, language_confidence | RENAME-ONLY for measured values with the same meaning. A forced-hint sentinel or missing probability cannot be relabelled as detection confidence. | Person 2; later adapter evidence must keep auto-detect and hint behavior distinct. |
| Segments | P2 segments require index, ordered timestamps, text, optional word timestamps and diagnostics | Live segments have start/end/text/nullable confidence and no index/word/diagnostic fields | PROJECT only if the P2 source remains preserved and loss is explicitly accepted; otherwise REJECT. No silent drop of index, words, log probabilities, or no-speech probabilities. | Person 2/shared integration; mapping fixture must retain the loss ledger. |
| Quality | P2 quality metadata points to media-validation artifact/hash and measured probabilities | Live quality has no validation artifact/hash and uses segment count plus provider-style probabilities | PROJECT only with explicit source-preservation metadata; no quality default or field reinterpretation. | P2/shared integration. |
| Quiet success vs failure | P2 distinguishes successful empty transcript diagnostics from provider/schema failure | Live success requires a non-null transcript, while typed failure is a separate optional object | Preserve the P2 branch meaning. Never turn quiet success into failure or failure into empty success. | Person 2; T4 consumes diagnostics without making a recapture decision. |
| Typed failure | P2 AsrFailureV1 carries closed error_code, error_detail, retryable, plus envelope attempt/profile/source fields | Live AdapterFailureV1 carries a code, bounded message, and retryable flag; result is otherwise flat | REJECT unless a versioned code/detail mapping and required envelope are present. Never convert free text to a P2 enum by substring. | Person 2 owns P2 code semantics; live adapter/shared integration owns target mapping. |
| Failure provenance | P2 input-validation failures can have attempt 0; model/provider outcomes have matrix-specific attempts | Live result always requires ModelProvenanceV1, including failure | PRESERVE branch rules; never fabricate live model provenance for a P2 input failure and never default P2 attempt values. | Adapter owner; separate failure fixtures required. |

### 5.3 Vision content, uncertainty, policy, and failure fields

| Field/concern | P2 V1/V2 family | FEAT-018/live family | Mapping decision | Owner and impact |
|---|---|---|---|---|
| Collection shape | P2 V1 and V2 require entities, actions, relations, themes, and ambiguous regions as typed collections, including observation IDs and reference checks | Live collections default to empty and use plain label/confidence, subject/predicate/object, or label/description/confidence values | PROJECT only with a complete, reviewed projection. A defaulted empty collection is not proof of source absence; no source collection may be silently dropped. | Person 2/shared integration; T4 preserves vision observations. |
| Entity/action labels | P2 uses ObservedTextV1 and IDs; action actor/object refs are typed | Live uses plain strings and no observation identity/ref graph | REJECT or PROJECT with source pointers. Plain labels cannot replace P2 reference integrity. | Person 2; P1 receives only validated proposals. |
| Relation fields | P2 predicate and subject/object refs resolve to entity/action IDs; self-reference is rejected | Live relation subject/predicate/object are plain strings | PROJECT only if references can be preserved and the target projection is explicitly lossy; otherwise REJECT. No ID synthesis from display text. | Person 2/shared integration. |
| Themes | P2 themes carry observation IDs and at least one evidence reference; T4 themes pass through vision only | Live themes are plain candidates with no P2 evidence graph | PROJECT only with retained evidence refs; narration may not create or re-score themes. | Person 2; T4 B4 decision remains unchanged. |
| Ambiguous regions | P2 V1/V2 ambiguity has observation ID and note; no geometry/confidence is supplied by V1 Phase A | Live region requires label, description, and numeric confidence | REJECT when target-required description/confidence is absent. Do not fabricate confidence or geometry. | Person 2; later target version/mapping review. |
| Confidence | P2 candidate confidence is nullable-but-typed in V1/V2; T4 null remains NOT_MEASURED and support provenance remains | Live candidates require numeric confidence; live scalar uncertainty is also required | PROHIBITED SYNTHESIS for null values. A numeric default is not allowed. A projection that requires numeric confidence is REJECTED unless a source-measured value exists. | Person 2; B3c is preserved. |
| Result-level uncertainty | P2 V1/V2 result envelopes do not provide the live scalar uncertainty field; T4 uses an uncertainty summary with per-observation states | Live Vision requires scalar uncertainty | REJECT or preserve in mapping envelope; never synthesize a scalar from collection count, null confidence, or status. | Person 2/shared integration; T4 formula remains AGREEMENT_WEIGHTED_V1. |
| Policy provenance/state | P2 V1/V2 carry content-policy version, match-view version, and NOT_EXECUTED / PASSED / BLOCKED; success requires PASSED | Live flat result has no equivalent policy execution state in its schema | PRESERVE or REJECT. Do not treat a structurally valid live result as policy-passed P2 output. | Person 2; policy gate remains before Gate A. |
| V1/V2 profile/model provenance | P2 V1 has V1 profile/catalog and adapter/config; V2 has V2 profile/catalog and detailed model provenance | Live has provider/model/adapter/config strings | REJECT identity/version mismatch; no V2-to-V1 coercion or model-string substitution. | Person 2 owns study family; registry owner handles later adoption. |
| Typed failure | P2 failure has closed error/detail matrix, attempt/repair, policy state, and branch-specific provenance; V2 adds profile-resolvability and branch rules | Live failure has generic adapter code/message/retryable | REJECT unless exact mapping table and branch invariants are approved. Do not expose raw provider messages. | Person 2/shared integration; negative fixture required for every unsupported branch. |

### 5.4 Raw handoff and fusion fields

| Field/concern | FEAT-018 raw baseline | P2-T4 design baseline | Mapping decision | Owner and impact |
|---|---|---|---|---|
| Raw identity/version | FEAT018.RawUnderstandingResultV1@1.0, claims-shaped registry/fixture identity | P2T4.ProposedFusedRawUnderstandingResultV1@1.0, same serialized name/version | Use the explicit mapping namespace; never use the name as a validator. | Shared registry and Person 2; no registry cutover here. |
| Status | Existing fixture uses PROPOSAL; FEAT-018 live outer envelope uses PROPOSAL/FAILED | Active T4 design has exactly FUSED/UPSTREAM_FAILURE | REJECT status string coercion. A target status requires an explicit branch mapping and target acceptance. | Person 2 and Gate A/shared integration. |
| Claims vs fused collections | Claims carry claim ID, source modality, label/text, confidence, and conflicts | T4 carries fused entities/actions/relations/themes with source observation refs and support/refute provenance | PROJECT only as an explicitly lossy target view with source retained in the mapping envelope; otherwise REJECT. Never flatten by field-name similarity. | Person 2 owns T4 semantics; FEAT-018/shared/P1 review target. |
| Source result refs | Not present in the existing claims-shaped fixture | T4 requires exact ASR and vision result references and a fusion-policy hash | PRESERVE in the mapping envelope or REJECT. A claim ID or request ID is not a source-result ref. | Person 2/shared integration. |
| Source observations | FEAT-018 claims do not preserve the full T4 observation graph | T4 retains source observation IDs, labels, refs, and source provenance | Preserve pointers and original source observations; no normalized-label replacement or silent merge. | Person 2; P1 consumes proposals after Gate A. |
| Conflicts | FEAT-018 raw has a claims conflict list | T4 has closed contradiction/low-confidence conflict codes, reviewer attention, and preserved source refs | Map only through an explicit reason-code table. Do not suppress, downgrade, or turn all conflicts into a boolean. | Person 2; Gate A must retain adult review. |
| Uncertainty | FEAT-018 registry says uncertainty is retained but existing compact fixture has no T4 uncertainty summary | T4 has formula identity, per-observation states, nullable certainty, and NOT_MEASURED | Preserve T4 summary by pointer or REJECT; never collapse to a scalar/default. | Person 2; B3b/B3c unchanged. |
| Upstream failures | Existing raw baseline has no T4 typed upstream-failure reference structure | T4 has ASR, VISION, or BOTH references with empty fused collections and no raw provider message | PROJECT only through an approved typed failure mapping; otherwise REJECT. Do not turn UPSTREAM_FAILURE into PROPOSAL or a generic text failure. | Person 2/shared integration. |
| Gate A | FEAT-018 raw is a proposal and requires Gate A; P1 must not treat claims as eligibility | T4 output boundary is also proposal-only and explicitly not a Gate A decision | Preserve gate_a_required=true, adult confirmation/correction, source claim provenance, and session/version checks. | Gate A/P1 owners; no behavior change here. |
| Narration semantics | Existing claims fixture contains ASR and Vision claims | T4 B1 is support/refute-only; narration cannot create candidates or themes | Preserve separate ASR evidence and apply no narration-only candidate synthesis. | Person 2; T4 implementation follow-up. |

## 6. Option analysis and recommended mapping

### Option A: one canonical shared contract

Option A is not safe on the present evidence:

- Choosing the FEAT-018 flat ASR/Vision family would discard P2 correlation,
  attempt/repair, profile/catalog, policy, typed diagnostics, observation
  references, and branch-specific failure invariants.
- Choosing the P2 ASR/Vision family would require every live route, provider
  adapter, port, fixture, and consumer to migrate; that is outside this
  Blocker-0 execution scope and cannot be a silent alias.
- Choosing the existing FEAT-018 claims-shaped raw result would discard the
  T4 fused observation graph, source-result refs, uncertainty state, policy
  hash, and typed upstream-failure references.
- Choosing the T4 fused baseline as the one raw contract would break the
  current FEAT-018 raw registry/handoff and still would not resolve the live
  ASR/Vision family collision. The T4 baseline is not frozen.

Option A would require a new owner-approved version, complete migration
fixtures, producer/consumer updates, registry changes, and downstream Gate A/P1
review. None of those changes is executed here.

### Option B: explicit versioned mapping family

Option B is the safer proposed reconciliation:

- Mapping identity: P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1
- Mapping version: 1.0
- Mapping status: PROPOSED_NOT_ADOPTED
- Source family: P2 provider-neutral contracts plus the P2-T4 fused design
  baseline
- Target family: FEAT-018 live/provider-shaped contracts plus the existing
  Gate A/P1 handoff
- Default: reject unless exact identity/version and complete preservation
  metadata are present
- Owner split: Person 2 owns P2/T4 source semantics; FEAT-018/shared
  integration owns route/target boundary; P1/Gate A owns downstream acceptance
- Adoption: not applied; registry cutover: not performed; runtime mapping: not
  implemented

The three edge identities and all required preservation/rejection rules are in
the companion fixture. The mapping family is one versioned reconciliation
record; its directional edges are explicit so the upstream input bridge and
downstream Gate A projection cannot be mistaken for the same transformation.

The mapping is not yet lossless against the current FEAT-018 target contracts.
That is an intentional fail-closed result, not a missing decision. The positive
case proves that a complete, metadata-bearing mapping record can be admitted
for owner review; actual target projection/adoption requires a separate owner
decision on a preservation envelope, a new target version, or an equivalent
approved contract boundary.

## 7. Deterministic acceptance, rejection, and redaction behavior

The companion fixture is metadata-only and uses expected outcome labels for
evidence. Those labels are not new public runtime error codes.

1. Resolve exact mapping identity and version before inspecting fields.
2. Resolve the exact source and target edge before accepting a serialized name.
3. Verify source artifact refs, hashes, status, correlation/session metadata,
   profile/catalog identity, policy/provenance markers, and discriminator branch
   wherever the selected edge requires them.
4. Accept a positive case only when every transformed field is listed as
   lossless or an explicit projection and no required source field is
   unmappable.
5. Reject an unknown identity/version, a P2-T3 V2 object at the P2-T4 V1
   boundary, a compact FEAT-015 payload missing the required P2 envelope, a
   missing source hash/provenance marker, or a privacy-invalid field.
6. Reject a status branch whose required/forbidden fields do not match that
   branch. Do not map PROPOSAL to FUSED, FAILED to UPSTREAM_FAILURE, or
   any other status by text similarity.
7. Preserve source observations, source result pointers, conflict references,
   uncertainty state, policy/config identity, and typed failure references.
8. Never fabricate a confidence, timestamp, attempt count, profile, source
   hash, failure message, policy pass, or missing narration result.
9. Never copy raw media, transcript content, provider payloads, prompts,
   credentials, endpoint details, signed URLs, or personal metadata into the
   mapping or evidence.
10. On rejection, publish no partial target result and do not mutate any source
    fixture, result, registry entry, or session state.

The positive fixture case is deliberately an adoption simulation with
adoption_applied=false. Negative cases cover wrong family, incomplete
provider-neutral envelope, unsupported version, privacy-invalid input,
rollback/non-adoption, and unchanged-source hashes.

## 8. Downstream acceptance and follow-up gates

The mapping recommendation is acceptable for owner review only if each
downstream boundary retains its current invariant:

| Boundary | Required acceptance check | Current result |
|---|---|---|
| P2-T2 ASR input | Exact P2 AsrResultV1 union, original audio ref/hash, profile identity, attempt/repair, typed error, and no live flat alias | Documented; no P2 source changed |
| P2-T3 V1 input | Exact P2 V1 vision union, five typed collections, observation/reference integrity, policy state, and typed error | Documented; no P2 source changed |
| P2-T3 V2 study | V2 name/profile/catalog/model provenance remains explicit and is never treated as V1/T4 input | Documented negative case |
| P2-T4 design | Statuses remain only FUSED / UPSTREAM_FAILURE; support-only narration, vision-only themes, bounded negation, primary-only weighting, and NOT_MEASURED remain intact | Design baseline preserved; implementation still separately gated |
| FEAT-018 registry | Namespaced mapping entry is reviewed before any registry/handoff change; breaking target change gets a new version and migration fixture | Proposed only; no cutover |
| FEAT-015 fixture | Existing manifest, expected payloads, loader, flow, tests, and hashes remain stable; any replacement is a new version | Existing baseline preserved |
| Gate A | gate_a_required=true; adult confirmation/correction and source claim provenance are retained; no AI proposal becomes meaning automatically | No behavior changed |
| P1/Gate B | Adult context remains explicit; exact activity/objective IDs and versions remain P1-owned; no raw claim becomes eligibility | No behavior changed |
| FEAT-017 live route | Provider details remain backend-only; outer proposal/failure envelope is not confused with P2/T4 status; route change requires separate approval | No route change |
| FEAT-018 engine handoff | Proposed SemanticAnchorSetV1 and later ExperienceSpecV1 work remain separately approved; source artwork and provenance remain immutable | No engine change |

The separate follow-up impact record enumerates the affected code, route,
adapter, port, loader, flow, registry, fixture, P1/Gate A, FEAT-017, and T4
surfaces with owner, change class, acceptance check, and approval requirement.

## 9. Owner questions remaining before adoption

The reconciliation answers the identity/mapping choice for this package but
does not answer the following adoption decisions by implication:

1. Does the owner accept the explicit mapping family and its three directional
   edges as the integration boundary?
2. Which approved preservation mechanism carries T4 source-result refs,
   uncertainty, policy/config identity, and typed failures when the current
   FEAT-018 raw target cannot carry them: an envelope/sidecar, a new target
   version, or a different reviewed boundary?
3. Which adapter/port owns each edge, and which producer is authoritative for
   each retained field?
4. What exact code/detail table maps P2 typed failures to the live typed
   failure family without free-text coercion?
5. What exact success/empty/missing-narration behavior is accepted at the
   chosen target, while preserving support-only narration?
6. Where are correlation, session version, request ID, and idempotency
   validated at the selected boundary?
7. Which registry entries and FEAT-015/FEAT-018 fixtures are retained and which
   receive a new version; what is the compatibility window?
8. How is the P2-T3 V2 study family kept explicit in all future fixture and
   route registries?
9. Has the P1/Gate A owner accepted the source-preservation and adult-confirmation
   checks before any target projection is consumed?

These are adoption/follow-up questions, not reasons to mutate the current
families or to invent a provisional schema field in this workstream.

## 10. Rollback and non-adoption

Before a separately approved adoption, rollback is a no-op because this package
does not enable a runtime mapping or change a registry. If the owner rejects
the proposal or compatibility evidence fails:

- keep the FEAT-018 live/provider-shaped family unchanged;
- keep the P2-T2/P2-T3 contracts and P2-T4 design baseline unchanged;
- preserve every existing FEAT-015/FEAT-018 source fixture and recorded hash;
- leave the mapping status PROPOSED_NOT_ADOPTED;
- do not publish a partial target result or alter downstream session/Gate A/P1
  state; and
- return to review with a new bounded proposal.

For a later, separately approved adoption, rollback means disabling the new
mapping/cutover and restoring the previously approved family at its existing
boundary. It does not mean deleting evidence, rewriting source media, or
forcing a consumer update. No such action is performed here.

## 11. Reconciliation-package acceptance record

- [x] Approved scope is limited to documentation, registry analysis, a new
      synthetic compatibility fixture, follow-up ownership/checks, and narrow
      mapping documentation.
- [x] Both same-name contract families and the P2-T4 design identity are
      enumerated with source paths, versions, shapes, owners, and consumers.
- [x] P2 ports/adapters, FEAT-018 live route/transport, FEAT-015 fixture
      registry/loader/flow, FEAT-018 registry, Gate A/P1, and FEAT-017 live
      references are listed.
- [x] A single explicit versioned mapping family is proposed with exact
      directional source/target identities and fail-closed rules.
- [x] Field-by-field requiredness, discriminator, source/reference,
      provenance, failure, uncertainty, privacy, loss, rejection, and owner
      treatment is recorded.
- [x] The new fixture contains positive review admission, wrong-family and
      incompatible rejection, unsupported-version rejection, privacy rejection,
      rollback/non-adoption, and unchanged-source cases.
- [x] No default, identity coercion, partial publication, or silent field drop
      is permitted.
- [x] Gate A/P1 adult confirmation, provenance, and exact identity/version
      acceptance remain downstream requirements.
- [x] No code, schema, route, adapter, port, loader, flow, runtime, existing
      fixture, P2-T2/T3 evidence, or P1/Gate A behavior was changed.
- [ ] Owner confirms the proposed mapping and preservation mechanism.
- [ ] Separate approval authorizes any registry cutover, migration, runtime
      adapter, consumer update, or P2-T4 implementation/adoption.

## 12. Review status

The two independent review passes required by the approved workstream are
complete:

- [x] Technical review: P2_T4_CONTRACT_RECONCILIATION_TECHNICAL_REVIEW_20260913.md
      — PASS WITH OWNER ACTIONS.
- [x] Governance review: P2_T4_CONTRACT_RECONCILIATION_GOVERNANCE_REVIEW_20260913.md
      — PASS WITH OWNER ACTIONS.
- [x] Post-review validation: harness, architecture, repository security,
      skeleton, whitespace, and deterministic fixture checks all passed.

A passing review confirms package quality; it does not grant owner
confirmation, contract freeze, migration approval, or adoption approval.
