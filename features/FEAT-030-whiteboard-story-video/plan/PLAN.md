# FEAT-030 plan — narrated whiteboard story video

- Status: APPROVED for local implementation and commit by owner instructions in this conversation.
- Revision: 3.
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
