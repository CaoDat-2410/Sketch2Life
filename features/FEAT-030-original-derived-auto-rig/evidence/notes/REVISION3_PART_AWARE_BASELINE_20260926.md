# Revision 3 part-aware baseline — 2026-09-26

## Implemented

- Timeline compilation moved from first `play()` into renderer `load()`, so `READY` exposes a stable non-zero duration.
- Pause stops both GSAP and deformation ticker; resume preserves position; seek-to, seek-relative and replay share one clock.
- Android controls now include visible seek back/forward 3 seconds, play/pause, press/drag scrub, time display and replay. Chrome auto-hides only while playing and remains visible while paused.
- Intro plans and captions now span 12 seconds. A low-amplitude deterministic idle loop starts after intro completion.
- Full-frame meshes are rejected as V2 subject motion.
- The paper-removed source is component-scanned to select a plausible interior subject region. The original scene becomes a background plate with that region cleared.
- Butterfly playback uses independent left-wing, right-wing and body/root meshes with separate pivots and offset bounded motion instead of stretching the whole drawing.
- Other archetypes keep the validated subject-region mesh and explicit lower tier until their part-mask visual evidence is accepted.
- Public UI stays child-friendly; renderer failures remain technical-console/evidence only.

## Verification completed

- Renderer TypeScript typecheck: PASS.
- Renderer tests: PASS, 21/21.
- Renderer production build: PASS, 821 modules transformed.
- Backend focused auto-rig and contract tests: PASS, 36/36.
- Full backend test suite: PASS. Pytest used an isolated workspace `--basetemp` because the host's default Windows temp directory denied fixture access.
- Ruff on changed Python: PASS.
- Mobile TypeScript typecheck: PASS.
- Mobile UI copy/recovery validator: PASS.
- Android emulator: Metro bundle reloaded successfully; reverse ports `8081` and `8000` are active and the app process is running.

## Remaining gated work

- A live SAM 2.1 adapter is not silently activated by this baseline. Revision 3 requires an authorized drawing corpus benchmark, exact model/config/license record, L4 cold/warm latency and VRAM evidence, then an ADR selecting the adapter.
- Android recording must still demonstrate pause stability, ±3-second seek, scrub, replay, control auto-hide and independent butterfly wing motion on a fresh session.
- Subject component scanning is a deterministic safe baseline, not a claim of semantic AI segmentation. Failure rejects V2 full-frame deformation and uses the existing safe fallback.

## Privacy

No real child image, provider output, token, prompt or model credential is stored in this evidence record.
