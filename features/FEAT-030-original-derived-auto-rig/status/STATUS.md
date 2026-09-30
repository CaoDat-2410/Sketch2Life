# FEAT-030 status

Status: IN_PROGRESS
Updated: 2026-09-30

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
