# SAM 2.1 mask-quality diagnosis — 2026-09-29

- Type: documentation-only source inspection
- Status: diagnosis complete; proposed follow-up awaits owner approval
- Runtime/model execution: not performed
- User screenshots or child artwork: not copied into this repository

## Findings

The SAM adapter currently asks for a single candidate mask and checks basic output shape/area. The
Lightning worker batches the existing grounded subject/part prompts and shares an image embedding;
downstream checks enforce some containment, overlap, confidence and coverage conditions. Those
checks are useful structural guards but are not a pixel-boundary accuracy evaluation. The runtime's
success status therefore does not establish that the intended bird/body/wing/leaf pixels were
correctly separated.

The screenshot-level report cannot by itself distinguish wrong topic grounding, prompt ambiguity,
mask under/over-segmentation, deterministic part partitioning, and renderer cutout/inpainting. The
separate high-pigment cutout plan covers downstream reconstruction. A fixed ground-truth benchmark
and staged comparisons are needed before assigning the symptom to SAM or selecting thresholds.

## Source pointers

- `backend/src/sketch2life/infrastructure/ai/sam21_runtime.py`
- `tools/lightning_vision_v2_server.py`
- FEAT-030's backend SAM adapter/package validation and Pixi part-mask handoff
- Proposed follow-up: `../../plan/SAM21_MASK_ACCURACY_AND_AUTO_RIG_QUALITY_PLAN_20260929.md`

This note contains no implementation result and does not authorize a provider/model run.
