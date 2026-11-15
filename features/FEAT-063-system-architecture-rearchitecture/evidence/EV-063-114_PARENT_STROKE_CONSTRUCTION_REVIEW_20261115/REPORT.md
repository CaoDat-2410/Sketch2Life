# EV-063-114 — Parent stroke-guide pedagogy review

**Date:** 2026-11-15<br>
**Review scope:** successful Rev87.18 Parent API response, Modal worker prompt/parser/renderer, Parent mobile guide screen, and current FEAT-063 SRS target.

## Finding

The current output is not a construction-based drawing lesson. The Modal source-plan worker explicitly says not to redraw or create geometry, and its schema requires every source SVG path to be assigned to exactly one stage. The backend then copies those exact source paths into the progressive guide.

The real `con mèo` result has 11 source paths. Its stages are:

1. `oc_path_001` — “Vẽ đường viền con mèo.” (`d` length 2,558 characters)
2. `oc_path_002` and `oc_path_003` — ears
3. `oc_path_004` and `oc_path_005` — eyes
4. `oc_path_006` — nose
5. `oc_path_007` — mouth
6. `oc_path_008` through `oc_path_011` — fur marks

This reveals the source illustration's outer contour first, then facial details. It does not start with simple construction shapes or teach how to build the animal. Since the worker cannot modify, split, or omit source paths, a better prompt or more steps alone cannot produce the requested pedagogy.

The Parent screen displays these instructions and strokes progressively; its renderer is not the root cause. The required change is to separate the original color SVG from a newly authored, simplified construction-guide geometry contract. Use the source as a pose/feature reference; let the guide use its own simple strokes, with optional feature anchors back to the source. Keep it a private adult-review draft.

## Evidence inspected

- The real API response and six stage SVGs in `EV-063-113_PARENT_MODAL_API_GUIDE_SCHEMA_FIX_20261115/`.
- Modal source-plan prompt: `deployment/modal/srs_v23/language_audio_app.py`, `_svg_catalog_source_plan_prompt`.
- Modal deterministic assembly: `deployment/modal/srs_v23/language_audio_app.py`, `_build_openclipart_source_guide`.
- Parent display: `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx` and `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`.
- FEAT-063 §31.17 requires 4–8 progressive steps that build from basic marks toward a recognizable subject; §32.32 is the latest as-built runtime record.

## Limitations

This review used the actual saved API response and source/stage metadata. A new raster screenshot was not produced in the review pass, so this report does not claim a fresh pixel-level visual inspection. The owner has now approved Plan Rev87.19, which authorizes implementation and at most one new real Modal inference. This report remains the original review record; implementation and runtime evidence will be added after that work completes.
