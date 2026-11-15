# Rev87.11-G — Make Parent chicken guide match the pictured SVG

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** Approved under the owner's direct request to compare the two drawings and fix the mismatch.<br>
**Baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; target §§1–31 unchanged.

## Objective

Replace the active V5 Parent chicken drawing with a new immutable guide whose completed strokes depict the same recognizable chicken as the pinned full-color SVG, simplified for a child to draw. Use the supplied HTML only as the interaction/teaching reference: each step adds ordered strokes that form the image; it is not a source of animal geometry.

## Verified findings

- The currently pinned reference is Arcadia Science Free Organism Illustration Library v1.0, CC0-1.0, asset `Gallus gallus`; its metadata explicitly says it is not child-drawing data and has no stroke order.
- The supplied HTML is a cat drawing demo. Its seven steps progressively add head, ears, eyes, nose/mouth, body, paws, and tail/whiskers. Existing strokes remain visible; current paths draw in order; the finished picture is made from those paths without a picture underlay.
- V5 and the supplied chicken illustration share left-facing orientation and broad semantic parts (comb, beak, wattle, body, wing, raised tail, legs), but their drawings do not visually match. V5's round oversized head, egg-shaped body, straight narrow neck, simple inner wing, three detached leaf-like tail feathers, and fork-like feet lose the reference's head/body proportions, sloping integrated neck/chest, feathered wing, layered fan tail, and characteristic leg/foot stance.
- The defect is in the guide geometry and decomposition, not evidence that the pinned Arcadia source is from children's drawings. V5 remains immutable historical evidence.

## Approved implementation

1. Preserve V2–V5 byte-for-byte. Add a V6 immutable manifest and make it the active curated derivation for the existing supported chicken aliases.
2. Author fresh child-drawable paths in the same normalized pose and visual proportions as the pinned SVG. Simplify detail, but retain the reference's identifying silhouette: smaller forward head and comb, short pointed beak and wattle, neck flowing into a deep sloped chest/body contour, broad body, visible scalloped wing, raised multi-feather fan tail attached at the rump, and the two-legged stance with distinct toes/feet. Do not use a generic circle-head/oval-body template, detached tail rays, or an illustration underlay.
3. Arrange the paths into 6–8 clear Vietnamese steps. Each step adds one coherent body part or small related group, ordered so the strokes themselves build the final chicken. Keep prior paths dark, reveal/animate only current-step paths in blue in sequence, and hide future paths. Retain the existing HTML-like animation contract.
4. Keep the full-color Arcadia SVG in its separate reference view. Continue to preserve source/license/hash lineage; V6 paths are new authored paths, not literal copies of source path data. Do not use any children's drawing dataset as the geometry reference for this curated chicken.
5. Keep all sanitizer, provenance, schema, anatomy and topology hard gates enabled. Add semantic regressions for the V6 feature geometry and stage coverage; do not weaken a gate to make the guide pass.
6. Exercise the real local Parent source-derived route without Modal dispatch. Render every cumulative stage, final guide, and separate reference at 1024×1024. Produce a side-by-side comparison and inspect whether the stroke-only final and reference share the intended silhouette/feature placement. Record route output, hashes, timings, focused tests and image evidence in a new EV-063 folder.
7. Update FEAT-063 implementation records and SRS §32 only. Do not change target requirements in §§1–31 or imply educator approval.

## Acceptance criteria

- The final stroke-only V6 is immediately recognizable as the same left-facing chicken as the supplied Arcadia SVG, with matching relative placement and proportions for head/comb/beak/wattle, neck/chest/body, wing, fan tail, legs and feet.
- At least four visible features that distinguish the reference from a generic chicken are retained (integrated sloping neck/chest, scalloped wing, raised layered fan tail, and the reference's asymmetric leg/foot stance); child-irrelevant feather detail may be omitted.
- Every stage is drawable from its ordered paths, prior strokes remain, current strokes animate sequentially, later strokes are hidden, and no finished-art underlay appears.
- The actual Parent route returns V6 with correct provenance and passes unchanged hard gates; no Modal/GPU call is made.
- V2–V5, their manifests/hashes and prior evidence remain intact. SRS §§1–31, unrelated worktree changes, shared services and user data remain untouched.

## Scope

- New `deployment/modal/srs_v23/data/arcadia_organism_strokes/arcadia-gallus-derived-guide-v6.json`.
- Active V6 selection and versioned method/schema in `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`, `backend/src/sketch2life/contracts/schemas/svg_engine.py`, and `apps/ui-mobile/src/parent/domain/svgGuide.ts`.
- Focused V6 geometry/topology/source-route/UI contract tests under the existing relevant test paths only.
- New `evidence/EV-063-106_PARENT_GALLUS_REFERENCE_MATCHED_STROKES_20261114/`.
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`, and SRS §32 only.

## Limits

No Modal deployment/warmup/inference, FLUX, video, fixture response, database migration, account/consent/seed/`.env` mutation, child data, shared-service restart, gate bypass, commit, push or merge. No changes outside the listed files except the new evidence folder.
