# Bird subject recall and topic ordering fix

- Feature owner: FEAT-018 live image/canvas flow; uses the existing FEAT-020 semantic topic producer and versioned `VisionUnderstandingResultV2` payload.
- Revision: 1
- Status: `SUPERSEDED_BY_APPROVED_BROADER_PLAN`
- Superseding plan: `SUBJECT_RECALL_AND_PIXI_MAIN_FLOW_HARDENING_PLAN_20260930.md`, which includes
  this bird alias/whole-subject-priority scope and adds the owner-approved adult correction and Pixi
  flow recovery work.
- Trigger: owner screenshot shows a clearly visible bird, a generic “chi tiết trong tranh” image label, and only branch/leaf topic cards.

## Evidence-based diagnosis

The screenshot is consistent with a claim surviving vision extraction but being lost after Qwen:

1. `tools/lightning_vision_v2_server.py` already tells Qwen to put the most specific central subject first, keep scenery last, use concise Vietnamese labels, and gives `con chim` as an example. The current evidence does not justify adding another Qwen pass or claiming that the prompt simply omitted subject priority.
2. Backend `application/services/topic_semantics.py` and mobile `AppContext.tsx` each have a closed, exact-match Vietnamese label table. An unlisted ASCII bird label becomes `chi tiết trong tranh` at both boundaries. Backend `build_topic_directions()` then filters that generic label, which can explain why valid branch/leaf claims remain as topic cards while the bird does not.
3. Backend candidate ranking treats branch/leaf and a whole animal as the same `subject` class, then relies on confidence. Thus, even a recognized lower-confidence bird can lose the first topic position or be pushed outside the three-direction limit.

The screenshot alone cannot prove the exact raw model label or whether the bird was omitted entirely: the live response labels were not logged, and no safe matching request payload was available. The leading diagnosis is closed-vocabulary normalization/filtering, with subject-vs-part ordering as a second concrete weakness. Do not log or commit raw image/model output to confirm it.

## Goal

When the existing single vision result contains a recognizable bird claim, show that bird as the primary topic and preserve branch/leaf as grounded secondary directions where space permits. Never invent a bird when the model did not return supporting evidence.

## Proposed scope

1. Add a reviewed, exact alias set for common bird labels and short phrases at the backend and mobile display boundaries (for example `bird`, `parrot`, `parakeet`, `budgie`, `sparrow`, `chim`, `con chim`, `vẹt`, and `con vẹt`). Use explicit phrase entries only; no substring/fuzzy conversion of arbitrary claims to “con chim”. Preserve meaningful known species labels where the closed vocabulary supports them.
2. Add a bounded whole-animal-versus-plant-part topic priority, based only on reviewed canonical labels. A sufficiently supported recognizable animal claim leads; branch/leaf can remain separate grounded secondary directions. Retain current confidence bands, provenance IDs, maximum of three directions and duplicate suppression.
3. Keep the current V2 subject-first prompt policy; do not add a repair/retry generation, another Qwen call, `/v2/localize`, SAM inference, or change the input/API/schema contract. If later sanitized evidence proves the model omitted a clearly visible animal entirely, that is a separate prompt/model task rather than a reason to infer a bird in code.
4. Cover the producer and consumer with synthetic non-child payloads for bird + branch + leaf, including common English aliases, Vietnamese aliases, low-confidence-but-valid animal ordering, duplicate spellings, unknown labels and the no-bird case.
5. Record all checks and limitations in FEAT-018/FEAT-020 feature-local evidence. Do not store the supplied screenshot, real artwork, raw labels from a live child image, credentials or provider payloads.

## Acceptance criteria

- AC-018-BIRD-01: A source-linked exact bird claim using a reviewed alias is displayed as a concrete Vietnamese bird label in backend topics and mobile claim chips; it is not downgraded to “chi tiết trong tranh”.
- AC-018-BIRD-02: When a sufficiently supported bird claim coexists with branch and leaf claims, the first direction is about the bird and up to two additional distinct directions may cover grounded context/parts; every direction retains correct source claim IDs.
- AC-018-BIRD-03: Unknown labels are not fuzzy-guessed as birds; with no bird claim in source evidence, no bird topic is created. Existing branch/leaf claims and unrelated-topic rejection remain correct.
- AC-018-BIRD-04: The normal initial flow makes one vision request only, does not call `/v2/localize`, and adds no Qwen retry, SAM request or schema/API migration.
- AC-018-BIRD-05: Backend semantic/topic tests, mobile mapper tests, type/lint checks, UI validation and synthetic non-child Android smoke pass; a live owner-run image check remains separately identified and is not represented as Codex-run provider evidence.

## Out of scope and risks

- No live provider request, model/checkpoint/dependency/runtime setting, schema, SAM rigging, Pixi playback, Gate A/B, narration, activity matching or child-data logging changes.
- The plan does not guarantee recognition when Qwen omits the bird from its source claims. The implementation must preserve this evidence boundary rather than fabricate detections.
- Alias lists in backend and mobile can drift; tests must exercise the same reviewed examples at both boundaries.

## Verification plan

- Reproduce the screenshot's post-processing shape with deterministic synthetic claims: one recognized bird/alias, one branch, one leaf and the existing at-most-three topic cap.
- Verify raw/source claim IDs and confidence stay intact through semantic ranking and frontend display mapping.
- Run focused and complete relevant backend tests, mobile tests/typecheck/UI validation, then a local synthetic Android flow. No Lightning credentials, real image, Qwen, SAM or localization endpoint are used by Codex.
- Request a separate owner-run live smoke after implementation; record only sanitized status/count metadata and the owner's visual verdict.
