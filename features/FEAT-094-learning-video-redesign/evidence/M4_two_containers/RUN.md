# Phase 2: one L40S prepares and renders (2026-11-26)

Dev workspace `siesta-6107/dev`, code not yet committed. Synthetic chick story, 5 scenes of 6 s, pipeline run inside the
video worker container with `check_pipeline.py` (no business state written, MP4 files stay local).

## Image checks before GPU time

`check_image.py` (`check_image_result.txt`): the renderer environment has the same 124 packages and lock hash as before
the rebuild; ffmpeg is still 7.1.5; the preparation environment imports with torch 2.8.0, diffusers 0.42.1,
transformers 5.22.1. `../M2_normalize/check_normalize.py` passed 6 of 6 after the rebuild.

## Runs

A warm-up call before run 1 loaded FLUX and SAM in 47.5 s (container start included).

| Stage | Run 1 (cold Qwen) | Run 2 (warm containers) |
|---|---|---|
| Video planning | 227 s | 14 s |
| 5 scene frames | 56 s | 55 s |
| First scene, renderer load included | 136 s (warm-up 83 s) | 109 s (warm-up 14 s) |
| Other scenes | 51 to 63 s | 50 to 60 s |
| Assembly and check | 9 s | 9 s |
| **Total** | **657 s** | **395 s** |

- All 10 scene frames used an AI background; speed profile `fast`, no out-of-memory fall-back.
- Run 2 switched the GPU from the loaded renderer back to preparation and again to the renderer without error.
- Run 1 probe: H.264 1280x720, 24 fps, 720 frames, 30.0 s.
- Earlier app run with up to three containers: 9 min 26 s with a cold Qwen.

## Picture (sampled frames of run 1, `run1_contact_sheet.png`; the owner has not judged the video)

No undrawn people or animals. Still present: zoom in scenes 1 and 3, the chick drifting off centre in scenes 2 and 4,
the chick hanging in front of the tree trunk in scene 3, the chick facing left although the drawing faces right.

## Not covered

The warm-up at story review (S6) was not exercised through the app.
