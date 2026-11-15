# Amendment Rev87.11-E — Build the Parent chicken guide from construction strokes

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** Approved by the owner's latest direction and supplied `sketch2life_svg_stroke_guide_demo.html`.<br>
**Baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned. §§1–31 remain unchanged.

## Objective

Replace the source-traced Parent chicken draft with a construction-based drawing lesson like the supplied HTML demo. The child should make a simplified, recognizable left-facing hen by adding basic shapes and anatomical parts in order. The Arcadia illustration may inform pose and feature placement, but its contours must not be traced or shown beneath the strokes. Keep the full-color illustration as a separate optional reference view.

## Approved implementation

1. Preserve V2 and V3 manifest files and their recorded hashes unchanged as historical drafts. Add immutable `arcadia-gallus-derived-guide-v4.json` and make it the active pinned-source derivation.
2. Use simple authored open SVG paths that progressively construct a child-friendly hen: large horizontal body form; connected neck and head; beak/comb/eye/wattle; wing and raised rear tail; two descending legs; feet and a few optional-looking feather marks. Keep the guide left-facing with the raised tail on the right, as in the supplied source image. Do not copy or approximate its full external contour; do not add a ground line or belly stripe.
3. Use six short instructions in Vietnamese, one part group per stage, with current-step blue animation and earlier paths dark, following the HTML demo. Maintain 4–8 stages, unique path coverage, part dependencies, lineage, source hash and truthful draft provenance.
4. Parent guide mode uses a plain white canvas with strokes only. Remove the source illustration underlay. Keep the existing separate full-color reference toggle and preserve the selected guide step when switching views.
5. Keep the existing sanitizer, source verification and all hard chicken topology/schema gates. Do not relax hard checks to accept invalid/disconnected construction geometry.
6. Call the actual local Parent source-derived route once for `gà mái`; it must return V4 and HTTP 200 without Modal dispatch. Render all six stroke-only stages plus the separate reference at 1024×1024, visually inspect that the stages build the hen rather than trace it, and save SVG/PNG, response hashes, timing, test results and screenshots to a new FEAT-063 evidence folder.
7. Add regression checks for active V4, immutable V2/V3, construction-stage ordering, absence of source underlay in guide mode, separate reference toggle, source provenance and route behavior. Append the as-built result in SRS §32 and update FEAT-063 records; do not change §§1–31 or claim educator approval.

## Acceptance criteria

- The first step is a simple body form; later steps build the neck/head and recognizable chicken features in a child-usable order, like the HTML sample.
- The final guide is a simplified drawn-from-strokes hen facing left with an upright tail at the right. It is not a tracing, does not overlay or reconstruct the full-color Arcadia artwork, and contains no ground line or invented belly stripe.
- Guide mode has no reference artwork behind it. The full-color Arcadia SVG remains available only through its separate toggle; switching back preserves the guide stage.
- The active source-derived route returns `SvgTopicStrokeGuideSourceDraftV1`, 4–8 stages, valid provenance and hard topology, HTTP 200, with Modal not dispatched.
- Focused backend/mobile checks pass and actual route SVGs are rendered and visually inspected at 1024×1024.
- V2/V3 manifests and prior evidence remain unchanged; SRS §§1–31, unrelated worktree content and shared services remain unchanged.
- No child data, database/account/consent/seed/`.env` mutation, Modal/GPU deployment or inference, shared-service restart, commit, push or merge.

## Scope

- `deployment/modal/srs_v23/data/arcadia_organism_strokes/arcadia-gallus-derived-guide-v4.json`
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`
- `backend/tests/unit/test_arcadia_gallus_derived_guide.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/tests/svgGuideSourceContract.test.mjs`
- new evidence under `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-104_PARENT_CHICKEN_CONSTRUCTION_STROKES_20261114/`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`, and SRS §32 only
