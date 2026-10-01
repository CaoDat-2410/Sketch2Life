# FEAT-030 status

Status: IN_PROGRESS
Updated: 2026-10-01

- The approved revision-4 SAM2.1 worker and integrated quality workstream are implemented locally;
  multimask candidates are bounded and filtered by existing prompt/area constraints.
- Synthetic metric/selector benchmark is reproducible independently of pytest. Its analytic masks
  are not human-reviewed drawings and do not establish SAM accuracy. The current constructed run
  improves region/boundary metrics but loses thin detail unless the feature is explicitly anchored.
- Full backend suite: 1,650 passed, 10 skipped. Local BE/Metro/emulator connectivity is verified,
  but no fresh visual playback with live SAM was performed.
- Still pending: reviewed held-out references, owner/reviewer-approved quality thresholds, L4 latency
  and VRAM with Qwen resident, Android visual acceptance, and the existing model ADR gate. Live SAM
  activation remains disabled/gated.
- Evidence: `evidence/notes/SAM21_BENCHMARK_RUNABILITY_20260930.md`.
- Pixi follow-up: the repeated `MASK_BACKGROUND_RECONSTRUCTION_FAILED` was isolated from successful
  HTTP 200 artifact reads to local paper-donor reconstruction. Added same-image credible-paper
  seeding for dense outlines, strictly within the verified mask. Renderer suite 49, typecheck/build,
  and mobile typecheck/UI-copy validation pass; rebuilt page/bundle return HTTP 200. Fresh Android
  visual acceptance remains pending. See `evidence/notes/PIXI_MASK_BACKGROUND_RECONSTRUCTION_FIX_FOLLOWUP_20260930.md`.

- SAM 2.1 prompt/refinement follow-up plan revision 1 is owner-approved and implementation is in
  locally implemented. It reuses current multimask selection, adds target-grounded point prompts,
  connected-component/boundary tie-breaks, and one bounded mask-input refinement for at most one
  subject plus one eligible part per source image. No fine-tuning or model call has been run.
  Held-out quality review, L4 latency/VRAM measurement, and Android visual acceptance remain open.
  See
  `plan/SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md` and
  `evidence/notes/SAM21_PROMPT_REFINEMENT_BASELINE_20260930.md` and
  `evidence/notes/SAM21_PROMPT_REFINEMENT_IMPLEMENTATION_20260930.md`.

## Approved Pixi sprite show plan — implementation in progress (2026-10-01)

- Revision 4 of `plan/PIXI_SPRITE_SHOW_AND_AI_MOTION_MATCHING_20261001.md` records all four owner
  choices: visual beats only (narration/captions deferred), companion characters allowed, a bounded
  image/crop permitted in the one post-Gate-B planner call, and visible typed failure with no
  automatic retry or substitute show. It retains gap-driven sprite coverage across supported
  behavior classes and the owner's visual approval of 144 frames; rights clearance/runtime remain
  pending.
- Plan revision 4 was explicitly approved; the exact pre-approval hash, branch and scope are recorded
  in `approvals/TASK_APPROVAL.md`. Implementation is authorized on `codex/pixi-ai-show-20261001`.
  FEAT-028 rights/runtime eligibility and live provider/Android gates remain separate constraints.

- Offline implementation is in place on `codex/pixi-ai-show-20261001`: additive versioned show
  contracts, one bounded post-Gate-B planner adapter (disabled by default), deterministic validator/
  compiler, capability-bound sprite reads, and mobile-to-Pixi V3 bridge. V1/V2 contracts remain
  unchanged; failures are visible and preserve the original with no automatic retry/fallback.
- Image-processing part proposals require visible connected-color evidence inside the verified
  subject mask; uniform silhouettes return no parts. Full backend suite reached 100%; workspace
  typecheck/tests/build and focused Ruff passed. See
  `evidence/notes/PIXI_SHOW_IMPLEMENTATION_20261001.md`.
- FEAT-028 gap audit found only static one-pose catalog frames. Walker and flyer draft cycles were
  added under FEAT-028 `assets/generated/`; they are not visually approved, catalogued, rights-cleared,
  or runtime-referenced. Existing 144 visual approvals do not clear their rights.
- Still gated: caregiver subject-reconfirmation round-trip, per-frame review/provenance and rights
  for new sprite drafts, external-provider privacy/retention, live Qwen single-call validation,
  Lightning L4 latency/VRAM, and fresh Android playback. No live model request or Android run was
  performed. Runtime planner remains disabled.
