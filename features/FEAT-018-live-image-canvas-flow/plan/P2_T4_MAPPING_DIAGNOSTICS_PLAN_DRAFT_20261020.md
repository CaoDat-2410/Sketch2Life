# FEAT-018 P2-T4 — Pilot Mapping Diagnostics Plan

**Status:** `DRAFT — NOT APPROVED FOR IMPLEMENTATION`
**Owner:** Person 2
**Branch:** `feature/feat018-p2t4-mapping-diagnostics`
**Parent baseline:** P2-T3 status/evidence commit `fd474b12bb50a603e67fce5c25f889a95e968734`

The separate [input-fixture review brief](P2_T4_MAPPING_INPUT_REVIEW_DRAFT_20261020.md) proposes
synthetic case inputs and lists the contract questions that must be resolved before the fixture
manifest is finalized.

This draft scopes FEAT-018 Person 2's pilot mapping diagnostics task. It is distinct from the
FEAT-003 P2-T4 multimodal-fusion task and its `P2T4*` schemas/tests. It authorizes no code, contract,
provider, mobile, FEAT-003, or live-runtime change. FEAT-018's O4 remains unapproved in
`P2_OFFLINE_FIRST_PLAN.md`; implementation requires a separate explicit owner approval recorded in
`approvals/TASK_APPROVAL.md`.

## Goal

Produce deterministic, offline diagnostics showing how the approved FEAT-018 observation-to-
candidate mapping behaves across the 20 version-2 golden pilot activities. The result is an
auditable proposal/blocked diagnostic, never an activity eligibility decision or Gate B approval.

## Source and authority basis

- `docs/context/SOURCE_REGISTER.md` defines source-register materials as references, not authority
  to implement unapproved work.
- `plan/PERSON_2_AI.md`, P2-T4, requires exact-observation, ambiguous, no-match,
  image/narration-conflict, low-confidence, and adult Gate A correction cases for every pilot; its
  output must remain a proposal/candidate envelope.
- `plan/P2_OFFLINE_FIRST_PLAN.md`, O3/O4, supplies the proposed candidate/handoff and offline
  acceptance boundaries, while explicitly marking O1/O2–O5 unapproved.
- `plan/CONTRACT_FREEZE.md` is the contract authority. Preserve `RawUnderstandingResultV1`, source
  references/provenance, separate ASR and Vision claims, and `gate_a_required=true`; do not modify
  FEAT-003's `VisionUnderstandingResultV2` schema or runtime.
- `plan/ACTIVITY_PILOT_MATRIX.md` defines the selected 20 golden activity/version pairs. Its 100-MVP
  catalog expansion and device/cache/renderer cases are outside this P2-T4 slice.
- `approvals/TASK_APPROVAL.md` has no explicit implementation approval for this FEAT-018 O4/P2-T4
  slice as of this draft.

## Read-only gap inspection so far

The current codebase already contains activity semantic catalogs and focused tests, so this task
must extend verified FEAT-018 behavior rather than duplicate the FEAT-003 fusion contract. The
read-only inspection found:

- `ACTIVITY_PILOT_MATRIX.md` is the canonical FEAT-018 set of 20 golden activity/version-2 rows.
- `backend/src/sketch2life/infrastructure/catalog/activity_semantics_v2.py` and
  `backend/tests/unit/test_semantic_personalization_v2.py` provide catalog and selected semantic
  matching coverage; `backend/tests/unit/test_activity_semantics.py` covers selected exact,
  ambiguous, fallback and no-match behaviors. The current inspected tests do not demonstrate the
  required six-case matrix for every FEAT-018 golden row.
- `fixtures/pilot_20_activity_template.json` is a P4 template with 20 `NOT_ASSIGNED` rows, not a
  P2-T4 mapping-diagnostics manifest. `fixtures/smoke_subset_3_activity.json` also belongs to the
  P4 cache/fallback/handoff smoke slice and is not the P2-T4 golden set.
- `backend/src/sketch2life/application/services/p2_t4_fusion.py`,
  `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`, and
  `backend/tests/contract/test_p2_t4_contract.py` are FEAT-003 P2-T4 fusion artifacts. Their name
  overlap does not make them the FEAT-018 Person 2 mapping-diagnostics task; leave them untouched.
- `plan/LIVE_VISION_SCHEMA_REMEDIATION_PLAN.md` uses “mapping diagnostics” for closed diagnostics
  about mapping/validating provider payload shapes at the FEAT-003/FEAT-027 vision boundary. That
  work is distinct from these FEAT-018 observation-to-activity pilot cases and does not satisfy
  their coverage requirement.
- The approved 2026-09-22 `TOPIC_AND_T2_ACTIVITY_MATCHING_FIX_PLAN.md` implementation already wires
  the reviewed semantic catalog into P1/T2 and preserves Gate A/provenance. Its recorded tests cover
  selected exact, ambiguous/fallback, and no-match examples, not the required six-case matrix for
  all 20 P2 golden activities.
- FEAT-018 `P2_OFFLINE_FIRST_PLAN.md` marks O4 and the remainder of the plan unapproved, and the
  feature's `approvals/TASK_APPROVAL.md` contains no specific O4/P2-T4 implementation approval.
  `plan/ENGINE_REFINEMENT_PLAN.md` also states P2-T4/T5 require their own approval when work goes
  beyond already approved P2 scope.
- `ACTIVITY_PILOT_MATRIX.md` also lists P4 cache-hit, cache-miss and renderer-fallback cases. Those
  are not part of the six P2-T4 mapping cases below; keep P4 execution out of this task.

This is a targeted read-only gap review, not a complete file-level implementation plan. Before
implementation, bind the exact paths to change and confirm the fixture/output contract. Do not
broaden scope because a nearby file appears convenient.

## In-scope proposal

- Use only synthetic, contract-valid fixtures for the offline mapping diagnostics.
- Cover exactly these version-2 golden activity IDs from `ACTIVITY_PILOT_MATRIX.md`:
  `ACT-0004`, `ACT-0016`, `ACT-0019`, `ACT-0020`, `ACT-0023`, `ACT-0026`, `ACT-0030`,
  `ACT-0033`, `ACT-0039`, `ACT-0046`, `ACT-0055`, `ACT-0058`, `ACT-0061`, `ACT-0067`,
  `ACT-0074`, `ACT-0085`, `ACT-0087`, `ACT-0091`, `ACT-0097`, and `ACT-0099`.
- For each activity, include six independently identified diagnostic cases:

| Case | Required behavior to verify |
|---|---|
| Exact observation | Supported evidence may produce a traceable candidate proposal with its source claim references. |
| Ambiguous observation | Preserve ambiguity; do not promote it to an exact activity match. |
| No matching candidate | Return a typed no-match/blocked diagnostic; do not invent a label or force a match. |
| Image/narration conflict | Preserve both modality claims and their references; expose conflict for review; do not silently choose a modality. |
| Low or unknown confidence | Preserve the measured value or `NOT_MEASURED`; block unsupported certainty and do not default confidence. |
| Adult Gate A correction | Preserve the original observation and record the adult correction separately with provenance; correction is not eligibility approval. |

- Produce a feature-local coverage manifest and compatibility report with per-case `PASS`, expected
  `BLOCKED`, or `UNRESOLVED` disposition, fixture identity, contract/version, and test reference.
- Use injected fixtures only: no model, network, Lightning, GPU, real child data, or real media.

## Invariants and non-goals

- AI observations and mapping diagnostics do not infer age, readiness, materials, supervision,
  psychological traits, safety, or eligibility.
- P2 emits evidence/candidates only. P1 owns activity/objective eligibility, and Gate A remains
  required before any compatible handoff.
- Unknown vocabulary, ambiguous evidence, stale/wrong-source input, missing provenance, duplicate
  or dangling claim references, and unsupported confidence must remain typed and fail closed.
- No automatic semantic-contradiction detector, new model prompt, provider retry behavior, FEAT-003
  contract/runtime modification, P1 policy change, mobile/UI change, catalog expansion beyond the
  20 golden rows, or live evaluation is included.
- Do not alter or reinterpret the separate FEAT-003 P2-T4 fusion implementation or tests.

## Acceptance criteria for the proposed offline slice

1. The coverage manifest contains exactly the 20 listed activity/version pairs and all 120
   activity/case combinations; no duplicate, missing, or silently extra case is accepted.
2. Every case's expected result is reviewed and tied to the fixture's source claim IDs and
   contract/version. Image and narration provenance remain distinct in conflict cases.
3. Exact cases produce only proposal/candidate diagnostics; the other five cases preserve their
   ambiguity, no-match, conflict, uncertainty, or correction state without inventing evidence.
4. No output adds P1 eligibility, Gate B approval, inferred profile facts, or a direct activity
   selection authority.
5. Fixture execution is deterministic and offline. Rejected or blocked fixtures make zero provider
   calls; no raw media, transcript, prompt, model output, token, or personal data is added to evidence.
6. Relevant contract/unit tests, schema compatibility checks, repository validators, and independent
   review pass before this offline slice is marked complete. Any out-of-scope schema or FEAT-003
   change stops for separate owner review.

## Proposed work order

1. Complete the read-only gap review against current FEAT-018 code/tests and bind exact paths,
   contracts, and existing coverage; distinguish current behavior from missing coverage.
2. Resolve any contract/vocabulary ambiguity using the existing freeze or submit a narrowly scoped
   contract amendment for owner review. Do not introduce a parallel schema.
3. Obtain explicit Person 2 implementation approval for this plan revision and exact file scope in
   `approvals/TASK_APPROVAL.md`.
4. Only after approval, implement the smallest additive fixture/test/report slice; stop on any
   required FEAT-003, P1, mobile, or provider change.
5. Run the approved offline checks, record limitations honestly, update feature context/evidence,
   and obtain independent review before declaring this slice complete.

## Current gate

`NOT APPROVED FOR IMPLEMENTATION`. The next allowed work is the read-only gap review and plan
refinement. No implementation or provider execution is authorized by this draft.
