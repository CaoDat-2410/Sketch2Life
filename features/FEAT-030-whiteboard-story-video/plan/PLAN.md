# FEAT-030 plan — narrated whiteboard story video

## Revision 10 — Milestone 2: source-preserving offline drawing engine (owner request 2026-10-09)

Baseline before edits: `codex/feat-018-contract-plan`, HEAD `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`; Milestone-1/1.5 changes are still uncommitted. Existing user edits in V1 stroke extraction and two V1 tests, plus untracked `assets/`, must not be overwritten. The required Milestone-1 and 1.5 reports, full audit, AGENTS rules and current V2/V1 code were read. Implement only a separate local V2 object-aware stroke contract/extractor, staged draw schedule, source-pixel brush reveal renderer, offline A/B MP4 pilots, metrics/golden contact sheets and focused regressions. No real child data, diffusion, GPU/paid call, V2 HTTP route, story motion/pose/transition engine, V1 `.run()` change, commit/push/deploy or Milestone 3. V2 remains OFF by default. For difficult extraction or timing, return a review/error state, never substitute generic shapes as a claimed success. Final comparison is to canonical `SceneStateComposer` target; untouched source-background fidelity is out of scope of the current registry. Visually inspect outputs and state `VISUAL_QA_NOT_PASSED` if stiffness/detail loss remains. Capture exact test/lint/security outcomes and artifacts in `SKETCH2LIFE_MILESTONE2_RESULT.md`, then stop for Architect review.

## Revision 9 — Milestone 1.5: gap fix and multi-drawing validation (owner approved 2026-10-09)

Baseline before this revision: branch `codex/feat-018-contract-plan`, HEAD `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`. Milestone-1 V2 files and governance files are already modified/untracked. Pre-existing whiteboard extractor/tests and `assets/` user changes must remain untouched. Read the Milestone-1 result and V2 implementation before editing.

Scope: add a distinct synthetic ocean drawing (fish/turtle/seaweed) with manual masks; exercise the same V2 registry, planner and composer for PNG and JPEG, continuity and mask/asset/action errors; generate separate A/B contact sheets. Audit Gate A/B and introduce only an *unimplemented* server-bound approval contract and Milestone-2 interface definitions. Caller `review_ref` is not authentication. No V2 HTTP route, automatic segmentation, durable store, animation/motion engine, approved new-asset generation, inference, Lightning run or production-readiness claim. V1 stays default and V2 feature flag OFF. Run focused V2/V1 tests, Ruff, Mypy, security/compatibility checks, disclose Vision V3 fixture exclusions, and write `SKETCH2LIFE_MILESTONE1_5_RESULT.md`. No commit/push/deploy. Stop for Architect review before Milestone 2.

## Revision 8 — Milestone 1: world/state prototype (owner approved 2026-10-09)

This is a bounded implementation slice, separate from the revision-7 visual-quality pilot. Baseline before edits: branch `codex/feat-018-contract-plan`, HEAD `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`, ahead of origin by four; pre-existing modifications to `whiteboard_stroke_extraction.py`, `test_whiteboard_mvp_renderer.py`, `test_whiteboard_stroke_extraction.py`, and untracked `assets/`. Preserve all of them. Read `D:/Codex/Sketch2Life/SKETCH2LIFE_FULL_WHITEBOARD_AUDIT.md` and `D:/Codex/Sketch2Life/IMAGE_TO_IMAGE_REVIEW.md` before implementation; both were accessible. Backend `.venv` has Python 3.12, Pydantic, pytest, Pillow, Ruff. Lightning revision/artifacts remain unverified.

Implement, in order: (1) independent V2 contracts and explicit reviewed event mapping linked to segment/fact/anchor IDs; interpretation beyond that mapping is `NEEDS_APPROVAL`, never implicit approval; (2) source asset registry from verified image and fixture/manual masks, fail closed with `NEEDS_MASK_REVIEW` for missing/invalid/overlapping/identity-ambiguous masks; preserve raw source pixels and SHA-256; (3) event-aware 3–6-scene planner with state continuity, 5–20 seconds/scene and 40–60 seconds total or structured error; (4) Pillow scene-state composer prototype with limited transforms/camera and explicit `UNSUPPORTED_ACTION`; (5) explicit V2 prototype method in story pipeline, controlled by `SKETCH2LIFE_STORY_RENDER_V2_ENABLED=false`. The existing `.run()` remains V1 and is never silently promoted to V2. No new paid/provider/render endpoint or production behavior in this milestone.

Acceptance Level 1: synthetic reviewed-event/mask fixture, at least two scene states and contact sheet, stable IDs/provenance, unchanged source asset pixels/texture, no unauthorized new object, tests for error paths and V1 regression, no GPU or paid call. Level 2 (real consented image/narration, Lightning masks/fidelity/continuity/actions/video) is explicitly deferred and cannot be marked PASS from Level 1. Do not claim true whiteboard animation or a complete story MP4. Output `SKETCH2LIFE_MILESTONE1_RESULT.md` with tests and limits. Do not commit/push/deploy. If a task collides with user edits, stop that slice and report it.

- Status: APPROVED for local implementation and commit by owner instructions in this conversation.
- Revision: 7 (visual-quality architecture decision; within owner-approved revision-4 scope).
- Revision 7 quality reset: stop treating more raster-edge test coverage as evidence that the output resembles a hand-drawn explainer. Keep `whiteboard-stroke-v1` as a diagnostic/fallback only. Prototype an opt-in, scene-object/layer-aware vector drawing path and require owner visual acceptance of a short encoded pilot before scaling to four narrated scenes. No GPU/image-model calls or real child media are authorized by this revision.
- Revision 5 implementation detail within the approved revision-4 visual-quality scope: bind optional, reviewable visual-element cues to approved narration segments, compile them into measured-TTS drawing windows, carry them to the whiteboard renderer, and fail when a requested cue has no drawable strokes. Existing scripts without cues remain legacy and cannot claim object-to-narration alignment. Bounding boxes are an interim placement cue, not SAM masks or semantic recognition. No shared mobile flow or paid model invocation is added by this slice.
- Revision 6 implementation detail: allow an explicitly selected local SAM2 mode for cued story scenes. Segment each generated illustration with the cue boxes, verify masks and hashes, then use the masks (not only bounding-box centroids) to assign line paths to TTS windows. Preflight must fail if the opt-in runtime is unavailable; mask errors must block scene READY. The default remains no-SAM to preserve existing owner-operated tests. This is a local implementation of the reference's object-isolation concept, not a claim that SAM2 equals its SAM3 result or that L4 visual acceptance has passed.
- Scope: local source-derived stroke renderer; bounded scene plan from approved narration; selectable whiteboard/Wan scene adapter; narration-timed scene lengths, subtitles, MP4 assembly, status and download; session-scoped job listing and READY-only playback/handoff in the existing mobile flow; focused tests and honest evidence.

## Acceptance criteria

1. A scene image can be converted to line paths and a real progressive-drawing MP4 in a local test.
2. Approved narration determines scene timing; no final READY when required provider artifacts or the 40–60 second duration gate fail.
3. Scene artifacts are isolated by package; status exposes a download route only after READY.
4. Whiteboard mode does not require Wan weights. Wan remains opt-in.
5. Focused tests, lint and repository security validation pass before commit.
6. Mobile can discover an existing job for its session, display processing/failure states, play only a READY MP4 and withhold its continue action until READY. This consumer path does not create or authorize a story script.

## Exclusions and risks

- No claim of pixel-faithful original stroke order: raster line paths are inferred, not recovered from a recorded drawing session.
- No claim of complete one-image autonomous storytelling: an approved narration/fact/anchor package is required for 40–60 second story video.
- No live model, TTS, GPU, device UI or visual-fidelity acceptance is available in this workspace. SDXL image-to-image output and inter-scene continuity remain unproven.
- Script generation/authorization and a server-side content screen remain unresolved; the mobile consumer path cannot substitute for those missing gates. On-device playback remains unverified until an owner-operated device test.
- The 5–10 second SRS whiteboard micro-video and 40–60 second story-video are distinct outputs; they must not be presented as the same acceptance item.

## Verification

Run focused unit/contract tests, a real local silent-scene render and FFmpeg mux/subtitle test on synthetic art, Ruff, `git diff --check` and `python tools/validate_repository_security.py`. Live provider validation and human review are follow-up gates before claiming production readiness.

## Owner-approved completion order (revision 3)

1. Product input is the child's drawing and description. The system may propose a story and three to six scenes from confirmed meaning and the approved learning objective; it must distinguish the child's own words from suggested wording and must not invent confirmed facts.
2. An adult reviews and may edit the **exact narration and scene content**. Render authorization must bind the final text/scene revision and hashes to the current session/source/spec; an edit revokes the old authorization. Gate B alone is not script approval. A server-side content/grounding screen is still required before paid media work.
3. Validate media independently on Lightning first, using a non-child drawing and reviewed narration/prompts through the provider-only smoke path. Inspect a real 40–60 second MP4 for stroke progression, continuity, voice, captions and source identity. This media test bypasses the backend and cannot prove the adult-approval workflow.
4. Only after the real media output is accepted, finish backend/mobile draft-review-render wiring, backend READY handoff enforcement and device end-to-end verification. Do not claim steps 2–4 complete based on synthetic local tests.

Revision 3 authorizes video-owned planning and validation preparation now. Shared mobile/workflow edits are deferred until the media gate and exact script-approval contract have been reviewed; the owner did not authorize unrelated feature changes or an unreviewed paid/GPU run.

## Visual-quality correction (revision 4)

Owner reviewed the first L4 synthetic output: 53.496 seconds and valid MP4, but four near-identical house/tree drawings restarted from white, monochrome ink, tiny marker, and no color reveal. This is a **failed visual acceptance**, not product completion. The owner resumed the paused goal with the explicit target of a richer narrated whiteboard result comparable in *quality and function* to the supplied reference; no reference code/assets are copied.

Implementation sequence stays video-owned before shared backend/mobile work:

1. Preserve approved/generated illustration colors and source hashes in the stroke artifact; draw black/colored line paths and reveal existing color regions after their outlines. Never invent a color from a grayscale source.
2. Add automated visual guardrails for consecutive near-duplicate scene illustrations, with a bounded failure before further scene rendering or READY. Recap may intentionally resemble the opening, but repeated full redraws are not accepted as distinct story beats.
3. Move from generic per-scene prompts toward explicit, adult-reviewed scene elements/draw order and narration cues. A reviewable storyboard must identify what new visual appears during each spoken beat; raster strokes alone cannot infer semantic timing.
4. Re-test a non-child storyboard on Lightning, inspect the actual complete MP4 against the owner reference for scene variety, legible subtitles, natural stroke/color progression and voice-to-visual timing. Only after this visual gate succeeds, resume backend/mobile approval and READY wiring.

Local deterministic media tests prove only renderer mechanics. Live scene generation, semantic alignment and reference-level visual quality require new owner-reviewed evidence and are not implied by this revision.

## Quality reset and exit gate (revision 7)

Code review of `Atharva-Kanherkar/chalkboard` (MIT, `main` at `1a37083`) found useful renderer mechanics: RoughJS creates stable, imperfect vector outlines; cached paths avoid per-frame jitter; path-length reveal traces each outline; concurrent rough passes avoid a visible second retrace; fill follows the outline; narration schedules element windows. Its default animation is fade, `--draw` is opt-in, and raster image/SVG elements still fade instead of being stroke-traced. It is a diagram-oriented prompt-to-video system, not a drop-in child-drawing-to-story renderer. Do not copy its remote CDN/font loading into a privacy-sensitive production path; any selected dependencies/assets must be pinned, bundled and licensed appropriately.

The next video-only pilot must use **one non-child, source-grounded scene**, with separate reviewed object layers and an explicit ordered draw path for each visible object. A line-art/style pass supplies appealing, consistent artwork *before* animation; SAM2 may help assign object masks but cannot improve a weak illustration. The vector renderer should reveal stable curved contours by path length, vary brush weight subtly, follow the active path with an approved hand asset only if available, and paint constrained source/approved color inside the completed object. Previous objects stay on the board; narration cues govern when the next object begins. A raster image without reliable object paths must be rejected or sent to a clearly labeled fallback, not silently presented as equivalent quality.

Ship a 5–8 second encoded pilot and three still frames (early/mid/final), alongside the same-source `whiteboard-stroke-v1` comparison. Owner must judge whether line quality, hand motion, color, composition and content match the reference's intent; tests alone cannot pass this gate. If the pilot still looks stiff, revise scene artwork/path authoring **before** any 40–60 second L4 run. Only after the pilot is visually accepted should the four distinct scenes, reviewed narration/TTS, captions and full MP4 be re-run on Lightning. The old 53.496-second L4 MP4 remains a rejected baseline. Use preview/contact-sheet review and content hashes to limit repeated inference cost; do not use the owner's child's drawing for this pilot without separate permission.
