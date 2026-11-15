# Amendment Rev87.11-D — Align Parent chicken guide strokes to the exact SVG reference

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** Approved by the owner's direct request to correct the guide so children draw the pictured chicken, using a simplified sequence of strokes placed on that same image.<br>
**Baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned. §§1–31 remain unchanged.

## Objective

Replace the active generic chicken guide with a child-friendly guide whose progressive paths are registered to the pinned Arcadia *Gallus gallus* hen illustration returned by the same Parent API response. The faint reference image must be visible under the guide strokes so each new line can be compared directly with the final pictured hen. Simplify the drawing by selecting a few recognizable contours and details from the actual image; do not invent a different pose or add features absent from it.

## Approved implementation

1. Preserve `arcadia-gallus-derived-guide-v2.json` unchanged as historical evidence. Add and activate immutable `arcadia-gallus-derived-guide-v3.json`, retaining the pinned source SHA-256, source path count, CC0 provenance, sanitizer, and per-path lineage.
2. Trace a child-sized sequence against the actual source artwork: rounded body contour; connected neck and head; the source-facing beak, comb, wattle and eye; source-positioned wing and raised tail; both legs and feet; then only a small number of useful wing/tail marks. Use 4–8 stages and open paths. Exclude the invented ground line, invented belly line, generic parallel legs, and excess feather strokes.
3. Register the guide to the source illustration's square canvas and landmarks. Do not use the old generic guide coordinates as the alignment reference. Keep the existing hard schema, sanitizer, source hash, and chicken topology gates. Do not relax hard gates to make a visually mismatched guide pass.
4. In Parent stroke-guide mode, render the pinned sanitized Arcadia illustration beneath the guide at low opacity, then render completed/current strokes in their existing colors and order. The strokes must coincide with the pictured hen's head, neck, body, beak, comb, wing, raised tail, legs and feet. Keep the existing full-color illustration toggle and preserve the selected step when switching views.
5. Render every real API response stage, including a final guide-over-reference composition, at 1024×1024. Inspect the alignment visually and retain the SVG, PNG, response, hashes, timing and check results in a new FEAT-063 evidence folder. No Modal or GPU call is needed for this pinned-source topic.
6. Add regression checks that pin V3 as active, preserve V2, validate source provenance and path lineage, forbid the added ground/belly paths, verify the 4–8 stage sequence and reference-underlay renderer, and exercise the real source-derived route.
7. Append a dated as-built record to FEAT-063 SRS §32 only and update feature context, decisions, source register, status and evidence index. Do not alter target requirements in §§1–31 or claim educator approval.

## Acceptance criteria

- The active Parent `con gà` response uses an immutable V3 guide; the V2 file and its recorded hash remain unchanged.
- The guide and sanitized color reference show the same left-facing hen at the same size and position. During drawing, the actual hen is visible as a faint underlay; newly animated strokes land on the corresponding contours/details rather than a second, offset chicken.
- The source-derived path is selected for both `con gà` and the explicit `gà mái` topic aliases shown in the picture.
- The sequence has 4–8 stages, starts with the large body form, builds connected head/neck and source-facing features, and finishes with legs/feet and only a few helpful details. No ground line or invented belly line is present.
- Existing source SHA, path lineage, sanitizer, response contract, and hard topology checks pass without weakening any safety or anatomy rule.
- A real local Parent route call through the source-derived builder returns HTTP 200 without dispatching Modal. Focused backend and mobile checks pass; rendered stage evidence is visually inspected.
- SRS §§1–31 and unrelated dirty worktree content remain untouched. No child data, DB/account/consent/seed/`.env` mutation, Modal deployment/inference, shared-service restart, commit, push, or merge.

## Scope

- `deployment/modal/srs_v23/data/arcadia_organism_strokes/arcadia-gallus-derived-guide-v3.json`
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/domain/svg_engine.py` (supported chicken topic aliases only; no gate relaxation)
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`
- `backend/tests/unit/test_arcadia_gallus_derived_guide.py`
- `backend/tests/unit/test_svg_topic_guide_chicken_topology.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/tests/svgGuideSourceContract.test.mjs`
- new evidence under `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-103_PARENT_CHICKEN_SOURCE_ALIGNED_STROKES_20261114/`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`, and SRS §32 only
