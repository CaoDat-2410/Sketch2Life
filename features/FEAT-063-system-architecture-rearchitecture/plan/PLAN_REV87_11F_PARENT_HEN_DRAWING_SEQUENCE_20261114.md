# Rev87.11-F — Parent hen drawing sequence aligned to the supplied HTML

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** Approved by the owner's latest direction after running and inspecting `sketch2life_svg_stroke_guide_demo.html`.<br>
**Baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned. Target §§1–31 remain unchanged.

## Objective

Replace the active Parent chicken guide with a recognizable, child-friendly hen drawing lesson. Its strokes must build the left-facing hen from the supplied reference, in the same progressive manner as the supplied HTML demo. Do not trace the full-color SVG or render it underneath the guide.

## Findings from the supplied HTML

- The demo has seven ordered steps: head, ears, eyes, nose/mouth, body, paws, tail/whiskers.
- Each step adds one part or a small related group; finished steps stay dark, the current step is blue.
- Current-step paths animate in order using SVG path length and staggered delays.
- The finished image is produced by the strokes themselves; no reference-art underlay is used.
- The current V4 guide starts with an oval body, batches multiple unrelated parts, and its final neck/tail proportions do not read like the supplied hen.

## Approved implementation

1. Preserve the existing V2, V3, and V4 guide files as historical versions; add immutable V5 and make it the active curated chicken guide.
2. Author a simple hen in the same pose as the supplied colored reference: facing left, small head and comb, short beak/wattle, plump feathered body, visible wing, raised feathered tail to the right, and two legs with feet. Use a small number of child-drawable, anatomically meaningful curves; simplify internal feather details rather than tracing the 77 source paths.
3. Use eight ordered stages, following the HTML's part-by-part progression: head; comb; beak/eye/wattle; connected neck and body; wing; raised tail; legs; feet plus a few feather marks. Each stage has a short Vietnamese instruction. Prior strokes remain dark; current strokes animate in blue one path at a time. No full-color artwork appears on the guide canvas.
4. Keep the pinned Arcadia SVG as a pose/feature-placement reference and preserve its source/license/hash lineage. Keep the separate full-color reference view as a distinct optional view that does not replace the stroke guide.
5. Preserve the sanitizer, source verification, age/topic contracts, anatomy/topology/schema hard gates, Parent optional-guide behavior, and unrelated-topic fallback. Do not weaken validation to make V5 pass.
6. Add focused regressions for V5, the preserved V4 hash, eight-stage ordered coverage, Parent guide mode without underlay, separate reference view, provenance and route behavior.
7. Call the actual local Parent source-derived route once for `gà mái` without Modal dispatch. Render every stage plus the final strokes at 1024×1024, inspect the sequence against the supplied HTML and reference pose, and save route logs, hashes, timings and images to a new FEAT-063 evidence folder.
8. Update FEAT-063 implementation records and SRS §32 only. Do not change target requirements in §§1–31 or imply educator approval.

## Acceptance criteria

- The final stroke drawing reads as the supplied left-facing hen with a raised tail, and can be drawn from the displayed steps without tracing an underlay.
- The lesson has eight ordered stages at most, with one part or a small related group per step and HTML-like progressive animation.
- The Parent route returns the V5 source-derived draft with valid provenance and unchanged hard gates; unsupported topics retain their existing behavior.
- V2/V3/V4 files and prior evidence remain intact. SRS §§1–31, unrelated worktree files and shared services remain unchanged.
- No child data, DB/account/consent/seed/`.env` mutation, Modal/GPU deployment or inference, shared-service restart, commit, push or merge.

## Scope

- `deployment/modal/srs_v23/data/arcadia_organism_strokes/arcadia-gallus-derived-guide-v5.json`
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`
- `backend/src/sketch2life/domain/svg_engine.py` only if V5 anatomy geometry needs a narrowly scoped validator correction; never relax its hard checks
- `backend/tests/unit/test_arcadia_gallus_derived_guide.py`
- `backend/tests/unit/test_svg_topic_guide_chicken_topology.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/tests/svgGuideSourceContract.test.mjs`
- new evidence under `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-105_PARENT_HEN_HTML_ALIGNED_DRAWING_SEQUENCE_20261114/`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`, and SRS §32 only
