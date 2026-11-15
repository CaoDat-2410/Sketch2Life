# Plan Rev87.22 — Parent semantic stroke primitives and deterministic SVG renderer

**Date:** 2026-11-15<br>
**Status:** APPROVED by the owner's continuing direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; this is implementation only, with append-only evidence in §32.<br>
**Predecessor:** Rev87.21 closed as partial in EV-063-117 / SRS §32.35 after three real outputs failed duplicate/path-complexity gates.

## 1. Problem

Qwen/Qwen3.5-9B repeatedly fails when asked to write free-form SVG `d` strings: outputs duplicate identical paths or use a path that violates the command-complexity limit. Increasing limits or relaxing the hard geometry gate would hide the defect and risk poor drawing guidance. Rev87.21 also demonstrated that required object keys can ensure a fixed number of records, but not valid or distinct SVG geometry.

## 2. Goal

Have Qwen output a compact semantic construction plan using bounded drawing primitives and coordinates. Deterministic worker code converts those primitives into short, valid SVG paths, then the unchanged public Parent API contract validates/returns the guide. The final result must form a recognizable child-friendly drawing progressively and remain anchored to the selected catalog reference.

## 3. Implementation

1. Keep the external `SvgTopicStrokeGuideConstructionContentV1` and Parent API response schemas unchanged.
2. Replace internal model-authored path strings with a private generation schema containing exactly eight required stroke records, semantic `feature_vi`, role, source path anchors, and a geometry primitive with bounded coordinates. Initial primitive set: `ellipse`, `cubic`, and `polyline`; all coordinates are bounded to the 512×512 guide viewBox.
3. Use four explicit points for each primitive. Define deterministic render rules: ellipse from four cardinal points, cubic Bézier from start/control/control/end points, and polyline from four ordered points. Emit canonical `d` strings in code, never accept model-provided raw SVG commands for this workload.
4. Validate coordinate types/bounds, non-degenerate geometry, primitive-specific point constraints, generated command count, path length, unique generated geometry, source anchors, unique semantic labels, exact stroke assignment, first-stage construction-only rule, final-stage feature rule, 4–8 ordered stages, source identity and SVG safety. Preserve every existing hard gate; add no auto-repair or gate bypass.
5. Normalize valid primitive records into the unchanged public content shape and reuse existing Parent/API assembly. Preserve the separate original color reference and adult-review status.
6. Add worker/backend/mobile contract tests, including deterministic primitive rendering and invalid/degenerate/duplicate geometry. Add bounded diagnostics for primitive counts, generated command counts and rejected stroke index; never log raw model content.
7. Run focused local checks, then deploy only the language/audio worker to Modal `dev`. Do not mutate the catalog Volume. Confirm CPU `/health` reports Qwen/catalog ready with no GPU/inference.
8. Run the actual synthetic Parent route → Modal → API path sequentially, topic `con mèo` only. For each failure, retrieve call logs, make a narrowly evidence-based code/prompt correction, rerun focused checks, redeploy, and then issue the next call.
9. On first valid API response, save the genuine output, render all cumulative stages plus its separate color reference using the response paths, inspect them visually and stop further calls. Do not use hand-authored/model-independent art as evidence.
10. Stop the Modal app and verify `stopped` after success or exhaustion.

## 4. Bounded runtime, privacy and cost

- Maximum **three real GPU inference calls**, sequential. Stop immediately after the first result passes worker, Parent API, SVG and rendered-stage checks.
- Every call after failure requires an evidence-based correction, passing local checks and a redeploy. No retry within a call, concurrent request, gate bypass, or unmodified repeat.
- Generic synthetic topic only; no child/account/profile/photo/voice/consent/personal/production data, no video or teacher presentation.
- CPU `/health` is allowed but must allocate no GPU and perform no inference.
- No Modal Volume/catalog mutation, `.env`/secret/credential changes, database/account/seed changes, production deploy, SRS §§1–31 change, commit, push or merge.
- If three calls fail, stop and report exact terminal errors. Any further cycle requires a new plan.

## 5. Acceptance criteria

- [ ] Worker emits no free-form model-authored SVG path string; deterministic renderer creates canonical bounded SVG paths from the private primitive contract.
- [ ] Local worker/backend/mobile tests pass before each live call; all previous hard gates stay enabled.
- [ ] A real synthetic Parent API → Modal response passes source/anchor, geometry, stage, role, final-feature, SVG safety and public API schema checks.
- [ ] All eight distinct strokes render into 4–8 progressive stages; first stage is simple construction, later stages build recognizable major parts, final stage supplies identifying details.
- [ ] Real cumulative-stage renders and the separate original color reference are inspected and saved; stage instructions match visible strokes in natural Vietnamese.
- [ ] At most three inference calls occur, sequentially; stop on success or cap.
- [ ] Modal app is stopped and verified at closeout.

## 6. Allowed files

Implementation/tests:

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- `backend/src/sketch2life/domain/svg_engine.py` only if required for an unchanged-contract compatibility fix
- `backend/tests/unit/test_svg_construction_guide.py`
- `backend/tests/contract/test_parent_svg_construction_guide_api.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `apps/ui-mobile/src/parent/domain/svgGuide.ts` and `apps/ui-mobile/tests/svgGuideSourceContract.test.mjs` only if a genuine API response exposes a renderer contract defect

Task records/evidence:

- This plan and `approvals/TASK_APPROVAL.md`
- `evidence/EV-063-118_PARENT_PRIMITIVE_STROKE_RENDERER_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

Do not edit other paths without a new plan amendment.

## 7. Exclusions

No product requirement or public API changes, visual redesign, dataset/catalog changes, Docker, Firebase, consent/database/account changes, Teacher presentation, video, child-data use, production deployment, SRS §§1–31 edits, or unrelated dirty-worktree changes.

## 8. Closeout

Record this exact plan SHA-256 in `TASK_APPROVAL.md` before implementation. Mark complete only if a real API result and its rendered guide satisfy the acceptance criteria; otherwise mark partial and stop after the three-call cap. No commit or push.
