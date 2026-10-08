# FEAT-030 plan — narrated whiteboard story video

- Status: APPROVED for local implementation and commit by owner instructions in this conversation.
- Revision: 1.
- Scope: local source-derived stroke renderer; bounded scene plan from approved narration; selectable whiteboard/Wan scene adapter; narration-timed scene lengths, subtitles, MP4 assembly, status and download; focused tests and honest evidence.

## Acceptance criteria

1. A scene image can be converted to line paths and a real progressive-drawing MP4 in a local test.
2. Approved narration determines scene timing; no final READY when required provider artifacts or the 40–60 second duration gate fail.
3. Scene artifacts are isolated by package; status exposes a download route only after READY.
4. Whiteboard mode does not require Wan weights. Wan remains opt-in.
5. Focused tests, lint and repository security validation pass before commit.

## Exclusions and risks

- No claim of pixel-faithful original stroke order: raster line paths are inferred, not recovered from a recorded drawing session.
- No claim of complete one-image autonomous storytelling: an approved narration/fact/anchor package is required for 40–60 second story video.
- No live model, TTS, GPU, device UI or visual-fidelity acceptance is available in this workspace. SDXL image-to-image output and inter-scene continuity remain unproven.
- The 5–10 second SRS whiteboard micro-video and 40–60 second story-video are distinct outputs; they must not be presented as the same acceptance item.

## Verification

Run focused unit/contract tests, a real local silent-scene render and FFmpeg mux/subtitle test on synthetic art, Ruff, `git diff --check` and `python tools/validate_repository_security.py`. Live provider validation and human review are follow-up gates before claiming production readiness.
