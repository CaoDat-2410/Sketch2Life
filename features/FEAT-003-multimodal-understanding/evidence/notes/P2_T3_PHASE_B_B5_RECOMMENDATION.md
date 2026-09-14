# P2-T3 Phase B B5 — recommendation gate

- Evidence ID: `EV-003-T3-17`
- Date: 2026-09-11 (superseding an internal same-day draft that proposed an
  infeasible and already-prohibited action; see "Correction" below)
- Status: evidence-only recommendation, within the already-approved P2-T3 Phase B
  B1–B5 scope (`approvals/TASK_APPROVAL.md`, 2026-09-01). This note is not itself
  an approval, does not freeze a profile, and does not select a runtime default
  (D-11 in `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md`).
- Basis: only already-recorded evidence in `evidence/P2_T3_LIVING_SUMMARY.md`,
  `evidence/notes/P2_T3_PHASE_B_B4_QUALITY_BENCHMARK_REPORT.json`,
  `evidence/metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE8_REPORT.json`,
  `evidence/notes/P2_T3_PHASE_B_B4_STEP2_DIAGNOSTIC_EXECUTION.md`,
  `evidence/notes/P2_T3_PHASE_B_B4_STEP3_REMEDY_DECISION_DRAFT.md`, and
  `DECISIONS.md`'s "Prompt-v3 Phase 8 acceptance/repeat decisions" entry. No new
  GPU session, model call, or prompt change was run to produce this note.

## Correction (2026-09-11)

An earlier same-day draft of this note recommended "re-score the existing frozen
B4/Phase-8 outputs under a relaxed matching rule, with no new model call or GPU
session." That recommendation was wrong on two independent grounds and is
withdrawn:

1. **Infeasible.** Every B4 and Phase-8 report was produced under
   `raw_output_mode: "CLASSIFY_ONLY"` (confirmed directly in
   `P2_T3_PHASE_B_B4_QUALITY_BENCHMARK_REPORT.json` and
   `P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE8_REPORT.json`) and the Phase 8 D-7
   decision (`approvals/TASK_APPROVAL.md`, "Phase 8 D-7 decision addendum")
   fixes `CLASSIFY_ONLY` as "persist only safe aggregate classification
   flags/counts and closed typed identifiers. Never persist raw provider
   output, prompt text, predicted text, or ground-truth text." No predicted
   text exists anywhere in this repository for either benchmark. There is
   nothing to re-score.
2. **Already prohibited even if the text existed.** `DECISIONS.md`'s "Prompt-v3
   Phase 8 acceptance/repeat decisions" entry states the Phase 8 result "must
   not be rerun, pooled, tuned against, or rescored under a changed rule." The
   pre-existing `evidence/notes/P2_T3_PHASE_B_B4_STEP3_REMEDY_DECISION_DRAFT.md`
   independently lists, as an explicit non-option: "Never tune, edit, or rerun
   a changed prompt, scorer, ground truth, or matching rule against the
   existing B4 fixtures. A changed prompt/rule/scorer/ground-truth creates a
   new experiment boundary; the B4 fixtures cannot silently become evidence for
   that changed experiment." Both records predate this note.

This corrected version replaces that proposal with the conclusion below. All
measured numbers in the comparison table are unchanged and exact — only the
recommendation changes.

## Candidate comparison table

D-9 authorized exactly one candidate profile, so this table has one row; there
is no second candidate to compare it against.

| Field | Value |
|---|---|
| Profile ID | `QWEN3_VL_8B_INSTRUCT_BF16_V1` |
| Model | `Qwen/Qwen3-VL-8B-Instruct` |
| Revision | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |
| Compute | NVIDIA L4, `GPU_BF16` |
| Decoding | greedy, beam `1`, `max_new_tokens=512`, `120s` timeout |
| Config hash | `3082f03f32a1cb26e6f5c25fe73813039460129b0f18a15e647b9f5ff08e3267` |
| Catalog hash | `72651b96d2c2259344efcb6fb3349807d42b56079a5422530db09c1590f00947` |
| Mapping readiness, prompt-v2 (C1) | `MAPPING_READY` — `16/16` schema/mapping-valid |
| Mapping readiness, prompt-v3 (phase 6) | `MAPPING_READY` — `7/8` + `7/8`; `v3-map-fixture-07` failed both passes |
| Original B4 held-out quality (prompt-v2) | `NO_GO` — entities `0.0`/`0.0`, actions `0.0`/`0.0`, relations/themes/ambiguous_regions not measured or zero-predicted |
| Direction A prompt-v3 phase 8 held-out quality | `QUALITY_NOT_READY` / `QUALITY_BELOW_THRESHOLD` — entities coverage/accuracy `0.111111` (`matched_count=2` of `18`), actions `0.0`/`0.0`, relations and themes coverage `0.0`, ambiguous-region count-rate `0.0` |
| Raw/predicted output persisted for either benchmark? | **No** — `raw_output_mode: CLASSIFY_ONLY` on every run; only aggregate counts and closed diagnostic-category tokens exist |
| Compute governance, phase 6 session | `CAP_EXCEEDED` by `00:24:41` (`00:44:41` billed vs. `00:20:00` authorized) |
| Compute governance, phase 8 session | `CAP_EXCEEDED` by `00:07:22` (`00:37:22` billed vs. `00:30:00` authorized) |
| Profile frozen? | No |
| Runtime default selected? | No |

## What the evidence supports and does not support

Restating `P2_T3_PHASE_B_B4_STEP2_DIAGNOSTIC_EXECUTION.md`'s own calibrated
conclusions, which remain the authoritative limits on this evidence:

- **Supported:** the original B4 diagnostic separated the `NO_GO` result into a
  collection-coverage-omission class (relations/themes/ambiguous_regions: the
  prompt never asked for them) and a separate exact-canonical-label-mismatch
  class (entities/actions: predictions were attempted at roughly the right
  count but matched nothing under the exact-string rule).
- **Not supported:** "this evidence does not prove semantic incorrectness
  (whether the model's actual wording was visually wrong, merely differently
  worded, or something else entirely remains unknown — **no predicted or
  ground-truth text was seen or recorded**); does not prove a scorer or
  ground-truth defect; and does not prove a frozen model/configuration
  limitation."

Owner-selected Direction A (a new prompt, `vision-v2-structured-output-prompt-
v3`, adding an active-search instruction per collection) targeted the
collection-coverage-omission class directly. It was implemented, mapping-
validated, and then benchmarked at held-out Phase 8. Result: entities moved
from `0/17` exact matches to `2/18` (`coverage/accuracy 0.111111`), while
actions, relations, themes, and ambiguous regions remained at `0.0`. Direction
A therefore produced a measurable but insufficient improvement and did not
clear the pre-registered D-5 quality gate.

`P2_T3_PHASE_B_B4_STEP3_REMEDY_DECISION_DRAFT.md` pre-registered what follows
each direction's outcome, before Step 1/Step 2 ran: **"Direction C — frozen
model/configuration limitation: if the owner judges neither A nor B worth
pursuing... record a no-go finding and do not tune the existing B4 fixtures,
prompt, rule, or ground truth to try to force a different result out of the
same held-out set."** It also pre-registered, as Direction B's own condition,
that pursuing the exact-canonical-label-mismatch hypothesis requires
"separately designed evidence" on "its own timeline" — never a rescore of the
existing fixtures — and lists rescoring the existing B4 fixtures as an
explicit non-option regardless of which direction is chosen.

## Recommendation: `NOT_ENOUGH_EVIDENCE`

Per D-11, B5 may recommend only a further controlled experiment or
`NOT_ENOUGH_EVIDENCE`; it may not freeze a profile or select a runtime default.
The repository contains no verified, approved artifact with the complete
predicted/ground-truth output that re-scoring would require, and re-scoring the
existing fixtures is independently prohibited by `DECISIONS.md` regardless. The
recommendation is therefore:

**`NOT_ENOUGH_EVIDENCE`** to freeze `QWEN3_VL_8B_INSTRUCT_BF16_V1`, or any
Qwen3-VL profile, as a production or runtime-default vision-understanding
candidate on the current evidence. The owner-selected remedy (Direction A) was
implemented and benchmarked and did not clear the quality gate; the existing
B4 and Phase-8 results are immutable and must not be rerun, pooled, tuned
against, or rescored, per `DECISIONS.md` and the Step 3 remedy draft's explicit
non-options.

**On Direction B (canonical-vocabulary mismatch):** it remains, in principle,
an open question — this note does not close it. But pursuing it is **not** a
continuation of B5 and is **not authorized by this note**. It would require, at
minimum: (a) a new plan and its own explicit owner approval, separate from this
B5 gate; (b) a new, separately designed and separately approved capture/scoring
boundary — since `CLASSIFY_ONLY` was a deliberate privacy/data-minimization
decision (D-7), reopening it to persist enough predicted-text detail for
scoring is itself a new decision, not a formality; and (c) entirely new
fixtures and new ground truth, per the Step 3 draft's own requirement, never
the existing B4/Phase-8 fixtures. No further Lightning/GPU session, prompt
change, or scoring-rule change is authorized by this note.

## Non-goals of this note

Does not authorize any GPU/Lightning work; does not change the immutable B4 or
Phase-8 results; does not modify the V1 or V2 contracts; does not approve
P2-T4 or P2-T5; and is not itself the P2-T3 completion decision — closing
P2-T3 overall, or authorizing any future Direction B experiment, remains a
separate owner action.
