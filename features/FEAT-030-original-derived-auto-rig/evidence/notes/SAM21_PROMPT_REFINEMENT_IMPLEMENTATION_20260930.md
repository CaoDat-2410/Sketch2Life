# SAM 2.1 prompt/refinement implementation — 2026-09-30

- Plan/approval: `plan/SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md`, revision 1; explicit owner
  approval is recorded in `approvals/TASK_APPROVAL.md` before implementation.
- Runtime/model: no SAM checkpoint, Lightning provider, Qwen inference, or real child artwork was
  accessed. No fine-tuning, dependency/checkpoint change, or fallback-policy change was made.
- State: local code path implemented and repository tests pass; real-image quality and activation
  gates remain open.

## Implementation

- The application forwards an existing normalized region only when it is keyed to the confirmed
  Gate-A target. Otherwise the adapter uses the existing bounded colored-ink region proposal.
- The adapter proposes a positive point from a dense, actual ink core inside the prompt region.
  It proposes a negative point only on bright, low-chroma paper outside the box and away from ink;
  uncertain points are omitted. These are SAM prompts only and never synthesize mask pixels.
- Part prompts use actual ink points inside their archetype role boxes, not geometric box centers.
  The runtime removes a part positive point unless it also lies inside the accepted subject mask.
  Part correction points are likewise constrained to that mask; the worker's existing hard parent
  clipping and part admission checks remain in force.
- Multimask choice keeps SAM confidence as the main signal, with small prompt-fit,
  8-connected-component coherence, and source-boundary contrast tie-breaks. These scores select a
  candidate; they do not edit it.
- If a coherent ink point is missing just outside the selected mask and low-resolution logits are
  available, the runtime makes one `mask_input` correction prediction. The total is hard-capped at
  two additional predictions per image: one subject and one eligible part. A failed or worse
  correction leaves the first valid result intact; no generic retry loop is added.
- Subject prompt, refinement-group, and non-square normalized-coordinate tests use generated
  fixtures only. Existing nine-archetype synthetic metric tests remain synthetic selector evidence,
  not a live model-quality result.

## Verification

Passed locally:

- Focused SAM/runtime/adapter/server/auto-rig suites, including the new prompt normalization,
  safe-background, component-coherence, parent-constrained part-seed, and two-call-cap tests.
- Full backend suite: `backend/.venv/Scripts/python.exe -m pytest -q backend/tests -p no:cacheprovider`
  (exit code 0; synthetic/unit/contract tests only).
- Ruff on every changed Python source/test file: `All checks passed!`.
- `python -m compileall -q` on the changed application, adapter, runtime, and Lightning worker files.

## Remaining gates / limitations

- Synthetic fixtures do not establish correct masks for real crayon, marker, photographed, touching,
  or weak-outline drawings. In particular, absent a target-keyed region, a deterministic color/ink
  proposal is not semantic recognition and can still localize the wrong object. Existing explicit
  failure/admission behavior remains the safety boundary.
- The implementation has not been measured with the approved SAM2.1 checkpoint on the target L4;
  latency and peak VRAM with Qwen resident still need the existing benchmark path.
- No reviewer-scored held-out references or Android visual playback were used. Do not describe mask
  accuracy as validated and do not activate a changed quality policy until those gates are reviewed.
