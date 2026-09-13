# P2-T4 contract reconciliation follow-up impact record

- Evidence ID: EV-003-T4-RECON-03
- Date: 2026-09-13
- Status: FOLLOW-UP ONLY — NO IMPLEMENTATION OR ADOPTION ACTION AUTHORIZED
- Parent report: P2_T4_BLOCKER_0_CONTRACT_RECONCILIATION_REPORT_20260913.md
- Mapping proposal: P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0
- Approval boundary: FEAT-003 approvals/TASK_APPROVAL.md, P2-T4 Blocker-0 reconciliation only

This record is the handoff register for work that may be required after owner
confirmation of the proposed mapping and a separate approval for adoption,
runtime changes, migrations, or P2-T4 fusion implementation. It is intentionally
not an execution checklist for the current worktree. Every item below is
separately gated, and every existing artifact named below remains unchanged.

## 1. Impact principles

- P2 provider-neutral contracts remain the source of P2 semantics.
- FEAT-018 provider-shaped contracts and the FEAT-015 fixture remain the current
  live/integration baseline until a new versioned boundary is approved.
- No same-name import, type alias, registry lookup, or fixture label is a
  mapping.
- A later adapter must check exact family identity, exact version, discriminator
  branch, source hash/reference, provenance, status, and privacy before
  projecting fields.
- Missing or non-equivalent fields are rejected. No default, identity coercion,
  silent field drop, or free-text failure conversion is permitted.
- Any target projection that cannot carry source-result references, uncertainty,
  policy/config identity, conflict references, or typed failure provenance must
  retain them in an explicitly approved envelope or reject the projection.
- Gate A remains mandatory, P1 remains the owner of catalog/objective identity,
  and P2-T4 remains a proposal until its own implementation approval.

## 2. Required follow-up change register

| ID | Existing surface | Later change required if adoption proceeds | Owner | Acceptance evidence | Approval gate |
|---|---|---|---|---|---|
| FU-01 | backend/src/sketch2life/contracts/schemas/asr.py | Keep P2.AsrResultV1 as the provider-neutral source. Add no alias. If a public version or mapping envelope is needed, add it as a separately reviewed versioned artifact with the existing status/attempt/provenance invariants. | Person 2 | Schema export, positive/negative branch fixtures, source-hash and attempt/repair checks | P2-T4 implementation/adoption approval |
| FU-02 | backend/src/sketch2life/contracts/schemas/vision.py | Keep P2.VisionUnderstandingResultV1 as the provider-neutral V1 source. Preserve policy state, observation/reference integrity, nullable confidence, and typed failure matrix. | Person 2 | Schema export, V1 success/failure fixtures, prohibited-field and reference-integrity checks | P2-T4 implementation/adoption approval |
| FU-03 | backend/src/sketch2life/contracts/schemas/vision_v2.py | Keep P2.VisionUnderstandingResultV2 and its V2 profile/catalog/model provenance disjoint from V1 and T4. No V2-to-V1 coercion. | Person 2 | V2 identity/version rejection fixture and unchanged V2 evidence hashes | P2-T3/P2-T4 boundary approval if consumed |
| FU-04 | backend/src/sketch2life/contracts/schemas/understanding.py | Decide whether the live flat family remains isolated or receives an explicit adapter into P2 contracts. Do not rename or widen it silently. | FEAT-018/shared integration with Person 2 | Exact mapping edge tests, complete source/provenance preservation, flat-family regression | FEAT-018 integration/adoption approval |
| FU-05 | backend/src/sketch2life/application/ports/asr.py | Keep the P2 AsrPort return type bound to P2.AsrResultV1. If a bridge is added, put the conversion at an explicit adapter boundary rather than changing the port to a union of same-name families. | Person 2 | Port contract test and wrong-family rejection | P2-T4 implementation approval |
| FU-06 | backend/src/sketch2life/application/ports/vision_understanding.py | Keep the P2 V1 vision port bound to P2.VisionUnderstandingResultV1. Add no live-family import or implicit conversion. | Person 2 | Port contract test, V1/V2 identity separation | P2-T4 implementation approval |
| FU-07 | backend/src/sketch2life/application/ports/vision_understanding_v2.py | Preserve the separate V2 port and profile identity. Any future shared handoff must state V2 explicitly. | Person 2 | V2 fixture and port-level wrong-family rejection | Separate V2/T4 integration approval |
| FU-08 | backend/src/sketch2life/application/ports/understanding.py | Keep the FEAT-018 flat port separate from the P2 ports, or introduce a named mapping port with a versioned mapping result. Do not resolve the collision by import order. | FEAT-018/shared integration | Both port families load independently; mapping edge and discriminator tests | FEAT-018 integration approval |
| FU-09 | backend/src/sketch2life/infrastructure/ai/fake_asr.py | Preserve deterministic P2 fake semantics. Add only separately approved mapping fixtures or an injected mapping adapter; do not make the fake emit the live family. | Person 2 | Existing P2 fake regression plus mapping fixture | P2-T4 implementation approval |
| FU-10 | backend/src/sketch2life/infrastructure/ai/fake_vision.py and vision_lexical_policy.py | Preserve P2 V1 policy and typed output. A later T4 adapter must receive a validated P2 result, not raw/live provider output. | Person 2 | Policy/prohibited-field/reference fixtures | P2-T4 implementation approval |
| FU-11 | backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py and benchmark/asr_round1_runner.py | If live-family output is bridged, retain P2 profile, source, diagnostics, retry/repair, and typed-failure semantics. Keep benchmark evidence separate from integration evidence. | Person 2 | Adapter/benchmark regression and provenance mapping report | P2-T4 plus integration approval |
| FU-12 | backend/src/sketch2life/infrastructure/ai/qwen_vision.py and V2 benchmark modules | If V2 is used by a later integration slice, keep its exact V2 identity/profile/model provenance and map it through an explicit V2 edge. Do not treat V2 as T4 V1. | Person 2 | V2 success/failure, profile, and wrong-family fixtures | Separate V2 integration approval |
| FU-13 | backend/src/sketch2life/infrastructure/understanding/fixture_adapters.py | Decide whether the existing FEAT-018 fixture adapter remains a legacy provider-shaped path or gets an explicit mapping adapter. Existing fixture behavior must remain available during any compatibility window. | FEAT-018/shared integration | Old and new fixture runs, unchanged-source proof, rollback run | FEAT-018 migration approval |
| FU-14 | backend/src/sketch2life/infrastructure/understanding/whisper_adapter.py and qwen3_vl_adapter.py | Preserve live-family output at its current boundary or add named mapping adapters that supply all missing P2 metadata without fabrication. | FEAT-018/shared integration with Person 2 | Complete mapping matrix, failure/redaction tests, no provider payload leakage | FEAT-018 integration approval |
| FU-15 | backend/src/sketch2life/infrastructure/ai/lightning_client.py | Keep token, endpoint, artifact bytes, and provider-specific behavior inside infrastructure. If the route changes, map sanitized typed results only and preserve exact source hashes. | FEAT-018/shared integration | Transport redaction, source-hash, retry, and typed-failure tests | FEAT-018 live-path approval |
| FU-16 | backend/src/sketch2life/interfaces/http/routers/live_understanding.py | Add an explicit route-level family/mapping identity only if approved. Do not reinterpret outer LiveUnderstandingResultV1 PROPOSAL/FAILED status as P2-T4 FUSED/UPSTREAM_FAILURE. | FEAT-018/shared integration | Route contract, stale-session, wrong-family, and redaction tests | Route/adoption approval |
| FU-17 | features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/manifest.json | Retain the v1 manifest as an immutable baseline. If the mapping is adopted, add a new manifest/version and record old/new identity, version, source hashes, and migration provenance. | FEAT-015/integration owner | Old manifest hash unchanged; new manifest registry validation | FEAT-015 migration approval |
| FU-18 | FEAT-015 existing expected/asr-result.json, expected/vision-result.json, expected/raw-understanding.json, and provenance/source-register.json | Do not edit or relabel the existing payloads. Add new versioned expected artifacts only after the target shape and mapping envelope are approved. | FEAT-015/integration owner with Person 2 | Byte/hash comparison, positive/negative compatibility fixtures, provenance review | FEAT-015 migration approval |
| FU-19 | features/FEAT-015-integration-readiness-review/src/integration_fixture/loader.py | Teach a later loader version to select the exact fixture/mapping identity and reject unsupported versions. Keep the current v1 loader behavior unchanged during the compatibility window. | FEAT-015/integration owner | Loader positive/negative/stale/escape checks | FEAT-015 migration approval |
| FU-20 | features/FEAT-015-integration-readiness-review/src/integration_fixture/flow.py and tests | Add a later scenario path for the approved mapping while retaining Gate A, adult confirmation, conflict visibility, and current v1 scenarios. Do not use the existing flow as proof of T4 fusion compatibility. | FEAT-015/integration owner, Gate A/P1 reviewer | Full old/new scenario suite and Gate A blocking checks | Integration allocation and migration approval |
| FU-21 | features/FEAT-018-live-image-canvas-flow/plan/CONTRACT_FREEZE.md | Add a narrow mapping registry/handoff entry only after owner confirms the mapping and target preservation mechanism. If a breaking target is chosen, add a new version and migration fixture. | FEAT-018/shared integration and project owner | Registry diff review, schema compatibility report, link/path checks | Owner confirmation plus registry/adoption approval |
| FU-22 | features/FEAT-018-live-image-canvas-flow/plan/PERSON_2_AI.md | Clarify exact P2/FEAT-018 namespaced identities, producer ownership, and the approved mapping edge without changing model/provider ownership. | FEAT-018/shared integration with Person 2 | Plan-to-registry parity and handoff review | FEAT-018 contract review |
| FU-23 | features/FEAT-018-live-image-canvas-flow/plan/PERSON_1_DOMAIN.md | Confirm that P1 consumes only the approved post-Gate-A proposal and retains exact activity/objective identity/version rules. No raw-contract projection may create eligibility. | P1 owner | Gate A/P1 acceptance fixtures, stale/mismatched identity checks | P1/integration approval |
| FU-24 | features/FEAT-018-live-image-canvas-flow/plan/ENGINE_REFINEMENT_PLAN.md | If the mapping feeds SemanticAnchorSetV1, record the exact source claim/pointer preservation and versioned adapter. Keep the proposed engine contracts separate until approved. | P1/shared integration with Person 2 | Anchor provenance, adult correction, and spec identity fixtures | FEAT-018 engine approval |
| FU-25 | backend/src/sketch2life/contracts/schemas/p1_experience.py and Gate A/P1 application surfaces | Validate that mapped observations cannot bypass Gate A, infer adult context, select a catalog identity, or change Gate B versions. | P1/Gate A owner | Missing Gate A, stale session, missing context, and identity mismatch fixtures | P1/Gate A implementation approval |
| FU-26 | features/FEAT-017-live-ai-dev-integration/LIVE_AI_GUIDE.md, plan/PLAN.md, and live evidence | Document the explicit mapping or continued isolation of the live provider path. Keep provider endpoint/token/raw payload exclusions and Gate A requirement unchanged. | FEAT-017/shared integration | Sanitized live-path evidence and mobile bundle scan | FEAT-017/live-path approval |
| FU-27 | P2-T4 fusion schema, policy, implementation, fixtures, and tests (not currently present/authorized) | After B0 adoption is approved, freeze the exact T4 identity and implement the nine existing decisions: FUSED/UPSTREAM_FAILURE, support-only narration, vision-only themes, bounded negation, primary-only weighting, 0.10 cap, formula identity, and NOT_MEASURED. | Person 2 | Full deterministic fusion suite, round-trip, source-reference, failure, redaction, and fixture evidence | Separate complete P2-T4 implementation approval |
| FU-28 | Contract registry, generated schemas, and downstream mirrors | Publish one approved mapping/target version and update all producers, consumers, mirrors, and migration fixtures atomically. No partial registry cutover. | Shared integration / project owner | Registry parity, generated-schema diff, old/new compatibility window | Explicit registry-cutover approval |
| FU-29 | Mobile/session/API/job/database/queue integration | If adoption reaches the integration sprint, carry mapping identity, session/version, idempotency, Gate A, and typed failure state through the chosen transport. This is not assigned by this record. | Separately allocated shared integration | Contract/E2E/stale/idempotency/security tests | ADR-0006-compliant allocation and approval |
| FU-30 | P3/P4/media/renderer downstream consumers | Confirm that approved ExperienceSpec/activity/objective/source-art identity is unchanged by any raw-understanding projection. Media fallback cannot replace the source or alter the approved concept. | P3/P4/shared owners | Continuity, source-hash, fallback, and Gate B identity fixtures | Downstream integration approval |

## 3. Required later migration package

If owner confirmation leads to adoption, the follow-up change set must include
all of the following before a registry cutover:

1. A final owner-approved mapping record or new target contract identity with
   exact versions and producer/consumer ownership.
2. A source-to-target field ledger covering every required, optional, default,
   discriminator, source reference, hash, provenance, confidence,
   uncertainty, policy, privacy, failure, and status field.
3. A lossless round-trip test for fields classified PRESERVE, and an explicit
   projection test for fields classified PROJECT. Any required field without a
   representation is a rejection test, not a default.
4. Positive success/adoption evidence, wrong-family rejection, unsupported
   version rejection, malformed/provenance rejection, privacy rejection,
   source-hash rejection, stale-session rejection, and rollback/non-adoption
   evidence.
5. A new additive FEAT-015/FEAT-018 fixture version with source hashes and
   deterministic expected output. The current v1 package must remain byte-stable.
6. Gate A/P1 review confirming adult confirmation, source claim provenance,
   explicit context, and exact activity/objective version behavior.
7. Security, architecture, harness, skeleton, link/path, contract, and
   repository-security validation at the exact adoption commit.

## 4. Current non-actions and approval gates

The following were not performed by this reconciliation package:

- no schema, contract, port, adapter, route, loader, flow, consumer, or runtime
  change;
- no FEAT-015/FEAT-018 existing fixture or manifest change;
- no P2-T2/P2-T3 contract, adapter, fixture, evidence, or approval change;
- no P2-T4 fusion implementation, schema freeze, or T4 fixture;
- no registry cutover, migration, rollout, or rollback action;
- no provider, GPU, Lightning, Runpod, model, dependency, or network action;
- no P1/Gate A behavior or mobile/session/API behavior change;
- no edit to the authoritative TASK_APPROVAL.md.

Required gates before any item above is executed:

1. Owner confirms the proposed mapping and the preservation mechanism for
   source-result references, uncertainty, policy/config identity, conflicts,
   and typed failures.
2. A separately approved adoption/migration scope identifies exact paths,
   owners, compatibility window, rollback, and registry changes.
3. A separately approved P2-T4 implementation scope authorizes fusion schema,
   logic, fixtures, tests, and runtime wiring.
4. Any cross-feature integration receives the allocation required by ADR-0006.

## 5. Follow-up acceptance checklist

- [x] Every inspected code, route, adapter, port, loader, flow, registry,
      fixture, P1/Gate A, FEAT-017, downstream, and T4 surface is listed.
- [x] Each item has a later owner, acceptance evidence, and approval gate.
- [x] Existing source/fixture baselines are explicitly marked unchanged.
- [x] Runtime mapping, migration, registry cutover, and fusion implementation
      are all separated from the approved Blocker-0 package.
- [ ] Owner confirms the mapping/preservation mechanism.
- [ ] Adoption/migration is separately approved.
- [ ] P2-T4 implementation is separately approved.
