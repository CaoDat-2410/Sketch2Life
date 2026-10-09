# FEAT-030 plan — narrated whiteboard story video

- Status: APPROVED for local implementation and commit by owner instructions in this conversation.
- Revision: 6 (implementation detail; within owner-approved revision-4 scope).
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
