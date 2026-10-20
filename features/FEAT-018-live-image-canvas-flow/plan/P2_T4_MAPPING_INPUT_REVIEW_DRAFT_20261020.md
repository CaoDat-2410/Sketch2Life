# FEAT-018 P2-T4 — Input Fixture Review Brief

**Status:** `DRAFT — REVIEW INPUT DESIGN ONLY`
**Branch:** `feature/feat018-p2t4-mapping-diagnostics`
**Related plan:** `P2_T4_MAPPING_DIAGNOSTICS_PLAN_DRAFT_20261020.md`

## Review request

Review whether the proposed synthetic inputs and expected outcomes below correctly exercise
FEAT-018 P2-T4 mapping diagnostics across the 20 golden pilots. Identify contract mismatches,
ambiguous scope, or missing provenance before any fixture manifest or implementation is approved.
This brief grants no implementation, schema-change, test-execution, provider, Lightning, or live
authority.

## Proposed source cases

The exact-observation seed for each activity comes from the canonical `plan/ACTIVITY_PILOT_MATRIX.md`
row. Fixtures should use synthetic claims and stable fake source/claim IDs; they must not contain
real images, child data, provider output, prompts, or secrets.

| Activity | Canonical pilot observation seed |
|---|---|
| ACT-0004 v2 | partly covered familiar object / cloth |
| ACT-0016 v2 | large objects and two bowls |
| ACT-0019 v2 | handwashing materials / sink |
| ACT-0020 v2 | small water spill and cloth |
| ACT-0023 v2 | small plant and watering can |
| ACT-0026 v2 | dry grains and pouring vessels |
| ACT-0030 v2 | button frame |
| ACT-0033 v2 | table setting objects |
| ACT-0039 v2 | graded color boards |
| ACT-0046 v2 | metal insets / tracing frame |
| ACT-0055 v2 | plant parts |
| ACT-0058 v2 | water cycle model |
| ACT-0061 v2 | stamp game / multiplication material |
| ACT-0067 v2 | word-class symbols and text |
| ACT-0074 v2 | weekly planning materials |
| ACT-0085 v2 | data table or chart |
| ACT-0087 v2 | classification key materials |
| ACT-0091 v2 | moon phase model |
| ACT-0097 v2 | source packet and argument organizer |
| ACT-0099 v2 | project planner and source log |

## Proposed six input families

These are input recipes for review, not finalized fixtures. Apply each family to every pilot seed
only if the reviewer confirms that the resulting input has a meaningful, contract-valid expected
outcome for that activity.

| Case | Proposed synthetic input | Intended diagnostic boundary |
|---|---|---|
| Exact observation | One grounded VLM entity/action claim derived from that row's pilot observation, with unique claim IDs and source provenance. | A traceable candidate/proposal may be emitted; it grants no eligibility. |
| Ambiguous observation | A valid ambiguous-region observation or two competing supported interpretations, retaining both references. | Preserve ambiguity; do not promote either interpretation to an exact mapping. |
| No matching candidate | A contract-valid synthetic observation outside the reviewed labels/concepts for the pilot set. | Return a typed no-match/blocked diagnostic at the P2 proposal boundary; do not treat a P1 age fallback as an exact match. |
| Image/narration conflict | A VLM claim grounded in the pilot seed and a distinct ASR/text-typed claim naming an incompatible synthetic observation, linked by a `SOURCE_DISAGREEMENT` conflict. | Retain both modality claims and references; expose conflict without silently selecting a source. |
| Low or unknown confidence | Low numeric claim confidence for one case; separately, a case with uncertainty not supplied by the upstream result. | Preserve the supplied number or the explicit not-provided state; block unsupported certainty. No numeric low-confidence threshold is assumed here. |
| Adult Gate A correction | Preserve the original synthetic observation and add a distinct adult assertion/correction with its own identifier and provenance. | Keep original and correction distinguishable; correction is not activity eligibility or Gate B approval. |

## Contract and policy questions for review

1. **Case boundary:** Should the fixture harness test `RawUnderstandingResultV1` before Gate A, the
   confirmed-scene/anchor mapping after Gate A, or both? P2-T4 describes mapping diagnostics while
   the adult-correction case necessarily crosses the Gate A boundary.
2. **No-match:** Which existing P2-owned operation is the intended proposal boundary? The existing
   semantic activity resolver may produce an age-baseline fallback; confirm how a true P2 no-match
   is represented without testing P1 eligibility or relabeling a fallback as exact.
3. **Low confidence:** No approved threshold was identified in the reviewed contract sources.
   Confirm whether the case should assert only preservation/typed uncertainty, or whether an owner-
   approved threshold already exists. Do not invent one in the fixture.
4. **Adult correction:** `SemanticAnchorSetV1` has `adult_correction_label`, and anchor provenance can
   carry `source_adult_assertion_id`; confirm this is enough to retain both the original observation
   and correction. If not, stop for a separately reviewed/approved contract change rather than
   silently widening a contract in P2-T4.
5. **Per-pilot applicability:** Confirm that all six families are meaningful for every pilot ID and
   that expected blocked outcomes count as successful diagnostics. Do not force a candidate for
   every case.
6. **Conflicting-modality input:** Confirm that the fixture uses distinct VLM and ASR/text-typed
   claims and a closed conflict reference, without putting raw transcript-like content into evidence.

## Relevant existing contracts

- `contracts/schemas/raw_understanding.py`: `RawUnderstandingSuccessV1`, typed narration status,
  source-specific claim records, uncertainty status, and `RawConflictV1` claim references.
- `contracts/schemas/semantic_personalization_v2.py`: `SceneConceptV2` confidence and evidence IDs;
  `ConfirmedSceneUnderstandingV2` modality/conflict state.
- `contracts/schemas/p1_experience.py`: `SemanticAnchorSetV1`, Gate-A confirmation, adult correction
  label, and `AnchorProvenanceV1.source_adult_assertion_id`.
- `plan/CONTRACT_FREEZE.md`: frozen cross-feature contracts and Gate-A/Gate-B ownership boundaries.

## Reviewer boundary

This is a static review request. Do not run tests or application code, edit files, alter contracts,
or infer implementation approval. Return findings and exact proposed changes to the input recipes;
leave unresolved policy decisions explicit for Person 2.
