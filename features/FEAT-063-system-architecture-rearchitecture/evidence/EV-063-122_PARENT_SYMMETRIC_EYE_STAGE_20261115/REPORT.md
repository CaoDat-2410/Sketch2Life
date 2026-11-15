# EV-063-122 — Parent paired-eye step correction

**Date:** 2026-11-15<br>
**Plan:** Rev87.28<br>
**Result:** Prior stage split confirmed; local source-specific grouping corrected and visually verified. No Modal call was made.

## Finding

In the genuine Rev87.27 response, stage 4 introduced the inner ring of the right eye (`P12`) along with both inner-ear marks (`P10–P11`). Stage 5 then introduced the remaining eye details (`P13–P15`). The render therefore completed the two eyes at different times, matching the reported issue.

## Correction

For the same exact asset ID and raw source hash only, the deterministic sequence now groups `P10–P15` into one stage. Its Vietnamese direction says to add the inner-ear lines and finish both eyes together. The guide now has six stages: head arc, face outline, ears/eyes/mouth outline, inner ears plus both eyes, tail, and feet. All 20 original path geometries remain unchanged and assigned exactly once. Other source assets and their Qwen flow are unchanged.

## Offline visual verification

`render_symmetric_eye_preview.py` loaded the saved genuine Rev87.27 Parent route response, applied the current source-hash-pinned worker mapping, and rendered the result locally. It did not send a request or invoke a model. The original response at `../EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/attempt_003/response.json` remains unchanged. The derivative is explicitly marked `live_api_response: false` in `response_resequenced_offline.json`.

- Six-stage contact sheet: `rendered_symmetric_eye_stage/cumulative_stage_review.png`.
- Paired-eye step detail: `rendered_symmetric_eye_stage/cumulative_stage_04.png`.
- Render manifest: `rendered_symmetric_eye_stage/render_manifest.json`.
- Original successful API response and Modal call evidence: EV-063-121 `attempt_003`; it is still the original seven-stage live response.

Visual acceptance: stage 4 shows both eyes' inner rings in blue simultaneously, with both inner ears also added; later stages add the tail and feet. This confirms the requested paired-eye behavior in the deterministic local preview.

## Checks and limits

- Modal worker contract tests: **50 passed**, two Modal asyncio deprecation warnings.
- `py_compile` passed for the worker, focused test module and offline renderer.
- Offline renderer completed and produced six cumulative stage images; stage 4 was inspected directly.
- Ruff was unavailable in `.venv-modal` (`No module named ruff`); no Ruff result is claimed for this correction.
- No new API/Modal inference, deployment, Android/Firebase E2E or child data was used. The code change is not yet live in Modal `dev`; the original live response remains seven stages until a separately authorized deploy/request.
