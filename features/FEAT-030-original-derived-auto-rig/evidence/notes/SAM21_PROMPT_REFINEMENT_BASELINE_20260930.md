# SAM 2.1 prompt-refinement baseline review — 2026-09-30

- Type: read-only repository review supporting plan `SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md`
- Model/provider/runtime: not invoked
- User artwork or child data: not read or retained

## Verified current behavior

- `sam21_runtime.py` requests multimask output and chooses among candidates using existing
  prompt/area checks. Multimask selection is already implemented; it is not part of the proposed
  new work except for improving its inputs and scoring evidence.
- `SubjectSegmentationRequest` defines `prompt_region`, `positive_points`, and `negative_points`,
  but `AutoRigService.start_gate_a_preparation` currently constructs the request without those
  values. The adapter then proposes a colored-ink region from the largest connected component.
- The Lightning worker creates a center positive point for each generated part region and forwards
  negative points, but no negative seeds are currently produced by the service path.
- The runtime does not pass the previous low-resolution logits as `mask_input`; one-step iterative
  correction is a genuine gap.
- Existing synthetic mask-selection evidence records a thin-detail recall decrease from 1.0000 to
  0.6394 for one constructed candidate comparison. This is selector plumbing evidence only, not a
  live SAM result.

## Scope interpretation

The follow-up should focus on target-grounded positive/negative points, carefully scored mask
boundaries and a strictly bounded refinement step. The source image must remain the exact SAM input;
color/edge analysis may propose or score prompts but may not silently rewrite pixels or synthesize a
mask. Current area/provenance/fallback policies stay intact. Fine-tuning is explicitly excluded.

## Repository pointers

- `backend/src/sketch2life/application/services/auto_rig/service.py`
- `backend/src/sketch2life/application/ports/segmentation.py`
- `backend/src/sketch2life/infrastructure/ai/lightning_sam21.py`
- `backend/src/sketch2life/infrastructure/ai/sam21_runtime.py`
- `tools/lightning_vision_v2_server.py`
- Existing implementation/limits: `INTEGRATED_MASK_AND_CUTOUT_QUALITY_20260929.md` and
  `SAM21_BENCHMARK_RUNABILITY_20260930.md`
