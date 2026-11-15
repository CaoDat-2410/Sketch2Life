# Plan Rev87.1 — Dataset-backed progressive SVG strokes

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct request to add a stroke dataset after reviewing the supplied HTML drawing demo. This amendment adds a dataset-backed source path to Rev87; all unrelated Rev87 limits remain active.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §6.2.1, BR-42/46, FR-P-11, FR-T-18/20, FR-AI-14/15, AC-34/44, AT-15/18. Update SRS §32 only.

## 1. Finding and supplied reference

The supplied `sketch2life_svg_stroke_guide_demo.html` illustrates the required visual behavior: recognizable contour paths, one clear part added at a time, visible retained strokes, a highlighted current addition, short child-facing instructions, step navigation and replayable stroke animation. Treat it as a visual/interaction reference only; do not copy its cat paths or embed its HTML as product output.

Rev87's free-form Qwen geometry can satisfy structural JSON checks yet still look like detached primitive blocks. This amendment makes a real, topic-matched ordered stroke source the first AI-draft source. When a reference exists, Qwen assigns semantic parts, groups existing paths into progressive stages and writes Vietnamese instructions; the service constructs the SVG from the reference strokes. Qwen must not redraw those paths as circles, rectangles or detached shapes.

## 2. Dataset and runtime behavior

- Use a small, curated subset of the official Google Quick, Draw! **cat** category. The upstream dataset provides per-drawing ordered vector strokes, a `recognized` flag, and declares CC BY 4.0. Fetch only the category file needed for this amendment; retain only a small reviewed subset in `deployment/modal/srs_v23/data/quickdraw_stroke_references/cat-v1.json`.
- Filter to `recognized=true`; remove country, timestamp and all other contributor metadata. Retain only the upstream drawing key for attribution/provenance, normalized strokes, source URL, upstream revision/file digest, selected-record digest and license metadata. Include the required attribution in the adjacent README. Do not include the whole corpus or send contributor metadata to Qwen.
- Parent keeps lesson-guide/catalog-first lookup. An adult explicitly requests AI only after a successful catalog miss. Exact supported dataset topic: cat/mèo. A dataset hit sends only the non-personal topic, coarse difficulty and normalized reference stroke IDs/coordinates to the existing pinned Qwen3.5 worker. The worker returns semantic part assignments, 4–8 progressive groups, short Vietnamese instructions and dataset lineage. Backend builds and sanitizes `SvgDocumentV1` from the retrieved strokes; model output cannot alter path geometry.
- For topics without a curated dataset item, Qwen may use the existing generated-SVG fallback under Rev87's strict schema, path, progression and topic-anatomy gates. If that fallback fails, show an unavailable/draft-rejected state and allow capture; never substitute a static illustration or unrelated dataset class.
- Response provenance distinguishes `DATASET_STROKES` from `QWEN_GENERATED`; include dataset/license/source hashes when applicable. All generated outputs remain private `DRAFT`, `review_required=true`, `persisted=false`. Parent adult preview and explicit accept/skip remain mandatory for an AI draft. Teacher sees a separate private draft preview.
- Renderer behavior follows the supplied demo: prior paths remain solid, current-step paths are highlighted/dashed and optionally animate as drawn, future paths remain hidden. Keep reduced-motion behavior and explicit step controls. Do not render the full final animal before its last step.

## 3. Safety, quality and runtime caps

- Keep existing SVG sanitizer and progressive path coverage gates unchanged or stricter. A dataset hit is accepted only when normalized paths are in bounds, have valid non-empty geometry, have no duplicate strokes and all strokes are assigned exactly once to ordered 4–8 stages. No fills, XML/HTML, scripts, external references, backgrounds or unrelated props.
- Preserve Rev87's deer anatomy checks for generated deer fallback. Dataset retrieval must be exact-topic only; a cat sample cannot be used for deer or another topic.
- Adult preview remains a human review gate because Quick, Draw! is a doodle dataset, not an educator-authored lesson sequence. Dataset recognizability metadata is a retrieval filter, not proof of pedagogical quality.
- Update only the existing `sketch2life-srs23-language-audio-dev` app once; at most one CPU `/health` call and one authenticated Parent UI-triggered GPU inference for **mèo/con mèo**. No warm-up, retry, second topic, video, FLUX call, test suite, `.env` or secret edit, production identity, child data, DB migration, publication, shared app stop, commit, push or merge. Keep 1,800 seconds maximum and restore the local capability flag to false.
- If public category data cannot be fetched, license/provenance is unclear, no acceptable cat sample is available, Modal/model/UI is unavailable, or hard gates reject the result, stop and record the blocker; do not claim the guide passed and do not retry.

## 4. Acceptance criteria

1. For `mèo`, real catalog lookup precedes the explicit AI request. The real Modal worker uses the curated, source-pinned dataset item and Qwen outputs only the stage/semantic mapping; returned SVG path geometry matches the curated source subset after deterministic normalization.
2. The rendered progressive guide is a recognizable line drawing with meaningful parts added over 4–8 steps, visually comparable to the supplied demo. No completed image appears at the first step; prior/current/future stroke states behave as described.
3. API response states its source and provenance, passes strict backend contract/sanitizer/path/step gates, stays an unpersisted draft, and includes no child/account data.
4. Parent app displays adult review, explicit accept and skip-to-capture. Teacher Web exposes the separate guide draft page and labels dataset versus Qwen source.
5. Evidence contains the curated-data manifest/source hash/license, actual request/response, actual SVG, progressive-render screenshots, timing and gate outcomes. No fixture output or the supplied demo's embedded paths count as model output.

## 5. Exact cumulative file manifest

Rev87's manifest remains in force, with these additions only:

34. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_1_DATASET_STROKE_REFERENCE_AMENDMENT_20261113.md` (new)<br>
35. `deployment/modal/srs_v23/data/quickdraw_stroke_references/cat-v1.json` (new curated data)<br>
36. `deployment/modal/srs_v23/data/quickdraw_stroke_references/README.md` (new attribution/provenance)<br>
37. The Rev87.1 evidence folder may add the actual dataset-derived output and attribution evidence specified in Rev87 §6.

No other source or data path may change without another explicit amendment. Preserve pre-existing worktree changes outside the combined manifests.
