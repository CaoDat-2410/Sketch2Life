# Rev87.22 — Parent primitive renderer live result

**Date:** 2026-11-15<br>
**Status:** PARTIAL — Parent API/schema succeeded once; the rendered guide failed visual acceptance.<br>
**Plan:** `plan/PLAN_REV87_22_PARENT_PRIMITIVE_STROKE_RENDERER_20261115.md`<br>
**Approved plan SHA-256:** `78D82BCE3E36C69CAD474882B9B31F3D1025D689EE819AE5E40AF0EAE6DFF12E`

## Outcome

Rev87.22 replaced model-authored free-form SVG `d` values with bounded ellipse, cubic, and polyline primitives. The worker deterministically rendered those primitives into the existing public SVG contract. All existing hard validation gates remained enabled.

The first real synthetic Parent route request failed because two generated primitives produced identical geometry. A narrowly scoped sampling change removed that duplication on the second request, which then exposed invalid stage structure. The final request passed the Parent route and returned a private, non-persisted draft with eight strokes and four steps. Visual inspection of the genuine response showed that the guide does **not** form the selected kitten: the output is a few disconnected/overlapping curves and facial marks, without the reference's recognizable head silhouette, ears, body/paws, or tail. The stage-one instruction also describes a body and head that are not present in the rendered paths; the second instruction asks for two ears while only one curve is added. Therefore HTTP 200 is not a quality pass and the guide is not usable for a child.

## Local verification

See `test_results.txt`. Final checks passed: Modal worker **34/34**, backend **12/12**, and Parent mobile **3/3**. Python compilation and scoped whitespace checks passed. Ruff was not installed in the selected virtual environment and was not installed for this task.

## Real Parent route → Modal attempts

All requests used only the synthetic topic `con mèo`; no child profile, child image, voice, consent, personal data, video, account, or production data was used. The runner bypassed only local identity/database authorization wrappers and exercised the Parent route, Modal client, Qwen worker, validators, and API response assembly. Calls were sequential, with no retry inside a call.

| Call | Modal call ID | Route time | Qwen inference | Result |
|---|---|---:|---:|---|
| 1 | `fc-01M7EV9JDF4FAQ6AD0MSCGZ4K8` | 170.536 s | 99.370 s | HTTP 502; duplicate geometry at stroke 2; 1 unique geometry among 2 parsed strokes. Not a timeout. |
| 2 | `fc-01M7EVPE385TY37RFTPBGN2SMS` | 151.828 s | 67.874 s | HTTP 502; all 8 geometries were distinct; stage validator rejected the model plan. Not a timeout. |
| 3 | `fc-01M7EW0PZJ91A32K5FKMPMH6DB` | 152.067 s | 65.450 s | HTTP 200; 8 generated paths, 4 stages, all worker/API schema and hard gates passed; rendered result failed visual inspection. |

Across the three calls, Parent route wait totaled **474.431 s** and recorded model-inference time totaled **232.694 s**. The Modal usage/credit cost was not available from these worker logs and is not estimated here.

The successful response used Openclipart CC0 asset `openclipart-friendly-kitten-icon` from dataset revision `df38e5ef633be067d397df7da19a9f009e69b3bd`; source SHA-256 `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`. The response is marked `DRAFT`, `review_required=true`, and `persisted=false`; it is not approved content. Response document SHA-256: `b361db79c5987b4e4995d8cef24ed5d36029f394093e6c4f300ae8cd2629657d`.

## Visual evidence

- `renders/contact_sheet.png` shows all four cumulative guide steps beside the original catalog reference.
- `renders/guide_stage_01.png` through `guide_stage_04.png` are individual genuine response renders.
- `renders/source_color_reference.png` is the separate original color reference from the API response.
- The matching `.svg` files and `visual_review.html` preserve the vector inputs used for rendering.
- `attempt_003_response.json` is the actual Parent API response; no fixture or hand-authored replacement was substituted.

The contact sheet confirms the failure: the guide shows a partial curved outline at the upper-left/head area, later adds two round eyes and a small nose/mouth, while the reference is a complete kitten silhouette with ears, paws, and tail. Stage instructions do not match the visible geometry. The worker's geometry, stage, source-anchor, and SVG-safety gates did not measure source-shape coverage or semantic alignment, so an API-valid result passed while remaining visually wrong.

## Runtime and cleanup

The CPU `/health` preflights before calls reported Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` and the Openclipart catalog as `ready`, with `gpu_allocated=false` and `inference_executed=false`. Health checks did not trigger inference. The language/audio Modal app was stopped after the third call; `modal_app_stopped.txt` records `State: stopped` at 12:57 SE Asia time. The catalog Volume was not mutated.

## Evidence index

- `attempt_001_*`, `attempt_002_*`, `attempt_003_*`: per-request summaries, sanitized Parent responses, route logs, and call-specific Modal worker logs.
- `health_preflight.json`, `health_after_sampling_fix.json`, `health_before_final_call.json`: CPU-only readiness records.
- `modal_app_stopped.txt`: final Modal app state.
- `run_parent_construction_guide.py`: one-shot synthetic Parent route runner; no child payload.
- `render_actual_response.py`, `renders/`: deterministic render script and genuine response previews.

## Conclusion and next correction

The implementation solved the decoder's repeated-geometry problem and produced a valid API response, but primitive coordinates generated by Qwen do not reliably reconstruct the source subject. Do not mark this guide usable and do not relax the existing gates. The next bounded experiment should derive drawable segments from the selected, sanitized source SVG and let Qwen choose their pedagogical ordering/instructions; deterministic rendering can then preserve the subject silhouette and source lineage. Add a visual/source-alignment acceptance check before treating an API-valid response as successful. This recommendation is an implementation follow-up only and does not amend SRS target requirements §§1–31.

No commit, push, merge, video generation, database/account/seed change, secret/`.env` change, or dataset/Modal Volume mutation occurred. The SRS remains unsigned; §32 records only this environment-specific result.
