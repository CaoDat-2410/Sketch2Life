# EV-063-105 — Parent hen drawing sequence aligned to the HTML demo

**Date:** 2026-11-14<br>
**Plan:** Rev87.11-F, approved after the supplied HTML was run and inspected<br>
**Result:** PASS for the focused source-derived Parent route and visual renderer checks; private draft only

## What the supplied HTML does

The supplied `sketch2life_svg_stroke_guide_demo.html` was opened in headless Microsoft Edge and captured at each of its seven selected steps. It draws a cat as ordered SVG paths: head, ears, eyes, nose/mouth, body, paws, then tail/whiskers. The previous step stays dark; new paths are blue and animate with `pathLength=100`, a 950 ms dash animation, and 220 ms delay between paths in the same step. It has no finished-picture underlay.

The earlier Parent chicken V4 was unlike that behavior in two ways: it began with a generic body oval and bundled several unrelated parts into one stage, and the completed figure's head, neck, wing and tail did not read like the supplied hen. V4 remains preserved as a historical draft.

## V5 change

V5 is a new immutable guide revision from the pinned Arcadia CC0 Gallus gallus reference. The source informs pose and feature placement only; source paths are not reused as child strokes. The colored source remains in the separate reference view and is absent from the drawing canvas.

V5 has 16 authored paths in eight progressive Vietnamese stages:

1. Head.
2. Comb.
3. Beak, eye and wattle.
4. Connected neck and body.
5. Wing with a feathered edge.
6. Three raised tail feathers.
7. Two legs.
8. Feet and a few wing/tail feather marks.

The resulting stroke figure faces left and includes the small head/comb, beak and wattle, rounded chest/body, visible feathered wing, raised tail, legs and feet. No ground line, belly stripe or reference underlay was added. Current-step animation remains blue and staggered; completed steps remain dark. The UI's existing guide/reference toggle preserves the selected step.

## Actual route and render

`POST /api/parent/v1/ai/sketch-guides` for `gà mái` / `beginner` returned HTTP 200 in 0.082 seconds from the local backend Docker image. Response contract: `SvgTopicStrokeGuideSourceDraftV1`; source: `CURATED_SOURCE_DERIVATION`; engine revision: `5.0.0`; 16 paths; 8 stages; pinned source has 77 paths and SHA-256 `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`. Guide document SHA-256: `f88713263264585418b4fe5f58c87f4f2f5071dc0c2db9d24dafc10fb063ead0`. Modal was not dispatched.

The route response was rendered in Edge from its actual SVG outputs. Eight stage PNGs, the final stroke image and the separately rendered color reference are 1024×1024; the step contact sheets are additional review aids. The exact HTML's seven stages are captured in `reference-html-step-1.png` through `reference-html-step-7.png`.

## Verification

- Backend focused tests: **12/12 passed** (`test_arcadia_gallus_derived_guide.py`, `test_svg_topic_guide_chicken_topology.py`, `test_parent_svg_source_derived_guide.py`). Pytest was installed only in the disposable test container.
- Parent UI guide contract tests: **3/3 passed** via the installed local Vitest executable. The `pnpm exec` wrapper could not resolve the sandboxed worktree (`EPERM`); running Vitest directly succeeded.
- Existing source hash, sanitizer, source-lineage checks, chicken anatomy/topology hard gates, V2/V3 history and V4 hash checks pass. No gate was loosened.
- V4 manifest SHA-256 remains `e901533285ef887507e9c6e6623d919e7eb3b6bb499582af0007da3d95ea8665`; V5 manifest SHA-256 is `ef05700d09ea5569373fe4746da78b36dd5e0fcbdd34536dd01707f6b9df46b9`.

## Limits

The route runner uses FastAPI `TestClient` and overrides only the Parent identity and database dependencies. It verifies the actual pinned-source route and response, but does not prove Firebase-authenticated production or Android end-to-end behavior. This is a chicken-only private draft and has not had educator review or publication approval. No child data, database change, Modal/GPU request, account/consent/seed/`.env` mutation, shared-service restart, commit or push occurred. SRS §§1–31 are unchanged and remain part of an unsigned draft.

## Files

- `run_parent_hen_v5_api.py` — bounded local Parent route runner; fails if Modal is dispatched.
- `runtime-attempt.json`, `parent-svg-guide-response.json` — actual route metadata and response.
- `parent-chicken-v5-step-1.svg`…`parent-chicken-v5-step-8.svg` and matching `*-1024.png` — staged route outputs and renders.
- `parent-chicken-v5-final-strokes.svg`, `parent-chicken-v5-final-strokes-1024.png` — final guide.
- `parent-chicken-v5-reference-separate.svg`, `parent-chicken-v5-reference-separate-1024.png` — separate color reference.
- `render_svg_evidence.ps1` — reproducible local Edge screenshot renderer.
- `parent-chicken-v5-stage-sheet-1.png`, `parent-chicken-v5-stage-sheet-2.png` — review contact sheets.
- `reference-html-step-1.png`…`reference-html-step-7.png` — screenshots of the supplied HTML demo at each selected step.
