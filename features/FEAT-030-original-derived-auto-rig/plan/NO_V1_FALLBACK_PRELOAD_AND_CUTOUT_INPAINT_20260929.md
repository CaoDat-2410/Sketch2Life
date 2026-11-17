# No-V1-fallback renderer preparation and cutout reconstruction

- Feature: FEAT-030 original-derived auto-rig / FEAT-018 mobile Pixi playback consumer
- Plan revision: 1
- Status: APPROVED
- Approval source: owner’s direct implementation instruction in the current conversation, 2026-09-29
- Scope is additive to the existing V2 package/source/mask contracts; this plan supersedes the
  earlier automatic V2-to-V1 fallback behavior for the current mobile V2 experience.

## Runtime evidence and diagnosis

Android emulator `emulator-5554`, package `com.sketch2life.mobile`, loaded the latest bundle
`mobile-vRRuVPez.js` from the local backend. Backend access logs show successful renderer launch,
source/package reads, and four mask reads. Android WebView then logged
`Renderer V2 package could not start. MASK_BACKGROUND_PATCH_UNSAFE`.

The current cutout composer rejects valid subject masks unless all four source-image corners imply
a bright, neutral, nearly uniform paper color. Real photographed drawings can have shadows, framing,
or other art in those corners. The V2 catch then starts the classic V1 whole-art animation, hiding
the actual preparation failure and violating the requested no-fallback experience.

## Goal

Keep the selected V2 experience in a real preparation state until source, package, verified masks,
and a mask-bounded reconstructed background are ready. Start preparation as early as existing gates
allow, show visible progress instead of an empty canvas, and never silently switch a V2 launch to
the classic V1 whole-drawing animation.

## Approved implementation scope

1. Replace the global four-corner paper-color gate with deterministic local raster inpainting bounded
   strictly to the verified subject mask. Seed reconstruction from neighboring unmasked source pixels,
   propagate colors into the masked hole, and preserve the exact immutable source plus its provenance.
   Keep malformed, empty, oversized, or invalid masks rejected.
2. On V2 load failure, stop playback, retain the original-art view, post a typed `PLAYBACK_FAILED`
   event, and expose retry. Do not load `classicPlayer`, emit `FALLBACK_APPLIED`, or animate the whole
   original image as an automatic error path. Keep explicit V1 contract handling for genuine legacy
   launches; do not select V1 as V2 recovery.
3. Make existing Gate-A segmentation preparation visibly waitable, prepare the renderer launch/package
   immediately after Gate-B approval before navigation, and display an accessible native loading
   overlay while Pixi fetches/decodes the source, package and masks and computes cutout layers.
4. Extend post-handshake renderer preparation timeout to 90 seconds. Timeouts become explicit
   retryable errors with the original image visible; they never trigger V1 animation.
5. Add feature-local regression tests/evidence, update FEAT-030 decisions/context, and run focused
   renderer and mobile checks plus the repository security validator before any commit/push.

## Acceptance criteria

- AC-030-NF-01: A valid subject mask over synthetic paper with non-neutral/uneven image corners
  produces subject/background layers without `MASK_BACKGROUND_PATCH_UNSAFE`; all pixels outside the
  mask remain byte-identical, the subject retains source RGB/provenance, and only masked pixels are
  reconstructed.
- AC-030-NF-02: Invalid or dimensionally unsafe masks remain rejected before Pixi motion starts.
- AC-030-NF-03: A V2 preparation error emits `PLAYBACK_FAILED`, displays the immutable original and
  retry state, and never invokes the classic player's V1 fallback or emits `FALLBACK_APPLIED`.
- AC-030-NF-04: Gate-A confirmation exposes an in-progress preparation state; Gate-B approval requests
  renderer preparation before navigating; PixiIntro keeps a loading overlay visible until the V2
  launch is accepted or an explicit error/retry state is reached.
- AC-030-NF-05: Renderer tests, TypeScript checks and the mobile renderer bundle build pass. Android
  logcat from the same fixture shows no `MASK_BACKGROUND_PATCH_UNSAFE` and no V2-triggered
  `FALLBACK_APPLIED`; any unrelated GPU warning is recorded separately.

## Boundaries and risks

- The original image is never overwritten. Inpainting is a derived display layer only and is
  restricted to verified mask pixels; it does not alter package provenance, masks, contracts, Gate A/B,
  Qwen/SAM settings, or model calls.
- No provider/model request is issued by Codex. An owner-run flow is required for live SAM and visual
  acceptance; offline synthetic fixtures are used for deterministic tests.
- Inpainting can reveal imperfect seams when source art/background is complex. The UI must not conceal
  a technical failure by animating the whole image; it keeps the source visible and offers retry.
- Existing V1 contract support remains for explicit legacy commands only. This does not authorize
  V1 as an automatic V2 failure path.

## Verification plan

- Renderer: focused `subjectCutout` and auto-rig-player tests; full renderer tests; renderer typecheck;
  Vite mobile demo build.
- Mobile: TypeScript check and UI-copy test; inspect Gate-A/Gate-B busy states and loading/error/retry
  transitions in code.
- Runtime: rebuild and restart the local backend only if safe with the active session; probe health and
  hashed bundle. Do not submit a drawing to an AI provider. Capture Android logcat only for an
  owner-started synthetic/dev session; do not store source image or credentials in evidence.
- Governance/security: record evidence in FEAT-030 and run
  `python tools/validate_repository_security.py` before commit/push.
