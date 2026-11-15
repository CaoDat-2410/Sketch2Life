# Rev87.11-H — Build the Parent guide from the exact source SVG paths

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-14<br>
**Status:** Approved by the owner's direct instruction to correct the AI guide so its strokes form the pictured animal.<br>
**Baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §31.17 is the target and §32 is as-built evidence only.

## Objective

Replace the rejected V6 hand-drawn chicken geometry with a progressive, stroke-only guide made from the exact path geometry in the pinned, high-quality Arcadia Gallus gallus SVG. The line guide must build the same chicken shown by that SVG. It must not imitate a child's drawing or approximate the animal with newly authored generic shapes.

The supplied HTML contributes only the progressive reveal interaction: earlier lines remain visible, current lines draw in order, later lines stay hidden, and the learner advances through steps. It is not the chicken geometry source.

## Confirmed defect and source

- The pinned source is Arcadia Science Free Organism Illustration Library v1.0, Gallus gallus, CC0-1.0, SHA-256 `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`.
- The sanitized source contains 77 paths in viewBox `0 0 252 252`; its metadata says it has no stroke order. It is an adult-quality vector illustration, not child drawing data.
- Active V6 instead uses 24 newly authored paths in a 512×512 viewBox, each with 3.8-unit strokes. The mobile renderer forces `fill="none"`, a thick rounded stroke, and child-like simplification. This differs visibly from the source and has been rejected by the owner. Preserve V6 files and evidence as history; do not continue its geometry.

## Approved implementation

1. Preserve all V2–V6 manifests, hashes, and prior evidence. Add immutable V7 path-order metadata containing only the source hash, supported topic aliases, provenance, eight Vietnamese stage descriptions, and the IDs assigned to each stage. Do not store a second, editable copy of path geometry in the V7 manifest.
2. At request time, load and sanitize the pinned SVG using the existing source loader. For every V7 guide path, use the matching source path ID and exact `d` string. Do not scale, redraw, simplify, concatenate, or substitute path geometry. The guide uses an unfilled dark line derived from the source path boundary; the current path is temporarily blue while it animates. Keep source stroke widths and line-cap/join/miter settings where available. The existing full-color illustration remains a separate view and is never placed under the line guide.
3. Assign every one of the 77 source path IDs exactly once across eight semantic stages: main silhouette; head details; legs/feet; wing and tail masses; first body-feather group; second body-feather group; tail feather details; wing/back feather details. Keep each stage below contract collection limits. Stage order may differ from source paint order; geometry and path IDs may not.
4. Add V7 derivation/provenance values to the strict API contracts and support 77 paths in the source-guide response. Use a source-specific validator for this route: verify the pinned file hash, sanitizer result, exact source path ID and `d` equality, path/style bounds, complete one-time path coverage, valid 4–8 stage order, and stage/part consistency. Do not route trusted source paths through the generic AI topology gate that requires newly drawn open geometry; do not relax or change that gate for Modal-generated drafts.
5. Update Parent rendering for V7: hide future paths; draw the current exact source path in blue without fill; keep finished paths as unfilled dark outlines; when the current step animation completes, retain it as a finished outline. The separate reference toggle continues to show the original colored source and preserves the selected step. Respect reduced-motion/accessibility behavior already supported by the screen. Keep V5/V6 rendering backward-compatible for old drafts.
6. Test exact source identity and guide coverage at unit level; test the authenticated-route composition with the existing focused Parent test harness and an explicit assertion that the Modal client is never called for the pinned topic; test the mobile V7 renderer and stage navigation. Render all eight cumulative stages and the final line guide at 1024×1024, compare the final guide with the pinned source, and inspect every stage. Record the rejected V6 versus corrected V7 and all hashes, request timing, route status, Modal-dispatch state, test output, and images in a new FEAT-063 evidence folder.
7. Update the current SRS **§32 only** with this dated as-built outcome and the prior V6 visual rejection. Update FEAT-063 context, decisions, source register, status, and evidence index. Do not alter §§1–31, claim educator approval, or claim Firebase/Android E2E based on route tests.

## Acceptance criteria

- V7's 77 guide paths have the same IDs and exact `d` data as the 77 sanitized paths from the pinned source, with no missing, repeated, or newly authored geometry.
- All 77 paths appear exactly once in eight semantically ordered steps. The guide is stroke-only on a plain canvas; it does not show source fills or an underlay. The completed line art must clearly read as the same chicken and preserve the source pose, proportions, comb, beak, body, wing, tail, and feet.
- The current path visibly animates, prior outlines remain dark, and future paths remain hidden. After animation completion the complete guide remains visible; the reference toggle shows the original colored image separately.
- The Parent API returns the V7 source-derived contract for supported chicken aliases without dispatching Modal. Unsupported topics keep the existing AI path and its safety/quality gates.
- Focused backend and mobile checks pass; all cumulative renders are saved and visually inspected. No claims of full-system/Android E2E are made unless actually run.
- V2–V6 evidence and manifests are preserved; no DB, `.env`, credentials, accounts, child data, shared service, or unrelated dirty changes are touched. No Modal deploy/inference, video, commit, push, or merge.

## In-scope files

- `deployment/modal/srs_v23/data/arcadia_organism_strokes/` — add V7 ordering manifest only.
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
- Existing focused backend tests under `backend/tests/unit/` and `backend/tests/contract/`; existing focused mobile source-contract test under `apps/ui-mobile/tests/`.
- New evidence: `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-107_PARENT_EXACT_SOURCE_PATH_GUIDE_20261114/`.
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, `evidence/README.md`, SRS §32 only, and `approvals/TASK_APPROVAL.md`.

## Limits

No Modal deployment or GPU inference; the pinned source path must be served locally. No database migration, seed/account/consent/`.env`/credential/child-data mutation, shared-service restart, quality-gate bypass for AI-generated SVG, edits outside the listed scope, commit, push, or merge. SRS §§1–31 remain unchanged.
