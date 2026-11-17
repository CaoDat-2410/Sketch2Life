# Revision 4 SAM 2.1 implementation — 2026-09-26

## Implemented

- Added `Sam21SegmentationResponseV1` and bounded point/region contract types.
- Extended `SubjectSegmentationPort` with optional box/point prompts and semantic-part slots.
- Added `LightningSam21SegmentationAdapter` at the backend boundary. It validates the source
  digest, calls only `/v2/rig/segment`, validates the typed response, stores a returned PNG mask
  as a session-scoped derived artifact, and never forwards provider errors to mobile.
- Added a deterministic colored-ink connected-component box proposal. It is a prompt only; the
  model must return the final mask. Full-canvas proposals are rejected.
- Added lazy `Sam21ImageSegmenter` runtime. It imports SAM2/torch only on first use, keeps the
  model process-scoped, accepts box/point prompts, rejects empty/full-frame masks, and encodes a
  bounded grayscale PNG mask.
- Added Lightning `/v2/rig/segment`, returning typed `SUCCEEDED`/`FAILED` responses instead of
  HTTP 503 for model unavailability or mask rejection.
- Added mask provenance to `RiggedArtworkPackageV1` when a validated mask artifact is present.
- Enforced the revision-4 safety gate that a subject-only mask cannot receive `FULL_AUTO_RIG`;
  without accepted semantic parts the package remains `CUTOUT_MICRO_MOTION`.
- Added opt-in settings and safe `.env.example` placeholders. Mobile and PixiJS never receive
  provider credentials or call the model directly.

## Verification

Command:

```text
$env:PYTHONPATH='backend/src'; python -m pytest backend/tests/unit/test_lightning_sam21.py backend/tests/unit/test_lightning_vision_v2_server.py backend/tests/unit/test_auto_rig.py
```

Result: 29 passed. Ruff and Python compile checks passed for the changed modules.

## Runtime activation

Install the official SAM2.1 runtime/checkpoint in the private Lightning environment, set
`SKETCH2LIFE_SAM21_CHECKPOINT`, `SKETCH2LIFE_SAM21_MODEL_CONFIG`, and
`SKETCH2LIFE_SAM21_DEVICE=cuda`, then enable the backend adapter with
`SKETCH2LIFE_LIGHTNING_SAM21_ENABLED=true`. Do not enable it as the demo default until the
10-fixture L4 smoke benchmark records warm latency, peak VRAM, mask acceptance and serialized
Qwen/SAM2.1 headroom in the feature evidence directory.

## Limitation

The repository does not download model weights and no L4 inference was run in this change. The
current SAM2 route returns a subject mask; semantic-part extraction and the independent part-mesh
promotion remain benchmark-gated follow-up work. The deterministic Pixi template/fallback remains
the safe path until those gates pass.
