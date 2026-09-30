# Bird topic omission — diagnosis and proposed correction

- Date: 2026-09-29
- State: diagnosis recorded; implementation plan awaits owner approval.
- Evidence: owner screenshot at Gate A; code-path inspection only. The screenshot is not copied here because it contains drawing artwork.

## Observed behavior

The drawing visibly contains a bird, but the detail label is generic (“chi tiết trong tranh”) while topic cards identify a branch and a leaf. No matching live response payload, request ID or backend label-level log was available, so the raw Qwen label cannot be asserted.

## Findings

- The Lightning V2 vision prompt already directs the model to prioritize the central recognizable subject and includes “con chim” as a Vietnamese example.
- `topic_semantics.display_label_vi()` and mobile `displayLabelVi()` use separate exact-match dictionaries. Unknown ASCII labels become the generic label; topic generation excludes that generic label.
- `build_topic_directions()` ranks all subject claims by confidence without distinguishing a whole animal from a plant part. This can demote a valid bird claim even after it is normalized.
- Existing tests cover the exact string `bird`, but not common alternate labels or a confidence-order case where a central animal competes with branch/leaf claims.

## Conclusion and limits

The strongest code-supported explanation is a post-Qwen closed-vocabulary drop, potentially compounded by confidence-only ordering. The screenshot does not distinguish that from Qwen omitting the bird entirely. Do not spend a second inference, add localization, or log raw child/model content to diagnose it. A synthetic regression can prove and fix the mapping/order defect; an owner-run live check is still needed to evaluate model perception.

Plan: `../plan/BIRD_SUBJECT_TOPIC_RECALL_FIX_PLAN_20260929.md` (revision 1, awaiting owner approval).
