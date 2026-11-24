# M0 — LTX pinned code: multi-image / end-frame conditioning

Date: 2026-11-24. Source: Lightricks/LTX-2 at pinned commit `f0f2f8607189c78a72420b2b63cb1975b5eca179` (v1.6.2) read from raw.githubusercontent.com (files `ltx_pipelines/utils/types.py`, `distilled.py`, `chunks/conditionings.py`).

## Findings
1. `DistilledPipeline.__call__(images: list[ImageConditioningInput], num_frames, ...)` accepts several conditioning stills.
2. `ImageConditioningInput` binds a still as `ImageReplace` or `ImageGuide`.
   - `ImageReplace.frame_idx` must be `0` or `1 + 8k` (causal VAE). The last frame of a clip is `8k` (clip length is `8k+1`), so it can NOT be an `ImageReplace`.
   - `ImageGuide.frame_idx` is any zero-based pixel frame, may lie outside the clip. `ImageConditioningInput.at(path, idx, strength)` = replace at 0, guide at every other index.
3. `assert_image_frames_in_clip` validates only replacements; guides are placed per chunk (`images_for_chunk`), so a guide at `num_frames-1` is supported.

## Conclusion — M0 PASSES (no pipeline change needed)
- Start still: `ImageConditioningInput.replace(K(i-1), 0, 1.0)` (as today).
- End still: `ImageConditioningInput.guide(K(i), generated_frame_count - 1, s_end)`. Do NOT use `.replace` at the last frame (raises ValueError).
- Caveat carried to M6: a guide is softer than a replacement; whether the last frame actually matches the keyframe is measured live in the M6 spike (s_end 1.0 vs 0.8), not assumed.
