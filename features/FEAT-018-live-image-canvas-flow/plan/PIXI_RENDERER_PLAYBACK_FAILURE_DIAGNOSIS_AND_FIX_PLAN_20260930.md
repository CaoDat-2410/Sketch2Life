# Pixi renderer playback failure diagnosis and fix — 2026-09-30

## Status

`APPROVED` by the project owner in the current conversation before implementation.

## Problem

The Pixi intro shows its generic playback-failure state and preserves the source artwork as a static
fallback. Backend access logs for the observed run show HTTP 200 for the renderer page, bundle,
source image, rig package, and part masks; they do not capture failures inside the WebView renderer.
The renderer already sends a bounded, safe `PLAYBACK_FAILED.reason`, but the mobile host drops that
reason and displays only generic copy. Android logcat did not expose the WebView console error.

## Goal

Identify the exact Pixi/WebView failure stage from a synthetic emulator run and correct the client
renderer defect so a valid rig starts playback. Keep the original artwork safe and retain a generic,
child-friendly failure message for unrecoverable cases.

## Scope

1. Surface only the renderer's allowlisted failure code and phase to local development diagnostics;
   never log artwork, launch payloads, capabilities, tokens, or child-profile values.
2. Add focused regression coverage for diagnostic propagation and any confirmed failure condition.
3. Reproduce the current issue with a synthetic/non-child drawing on the connected Android emulator.
4. Fix the confirmed renderer or bridge defect, rebuild the static Pixi bundle, and verify the same
   flow renders and begins animation.
5. Record sanitized findings and test/emulator evidence in this feature's `evidence/` directory.

## Exclusions

No backend AI/SAM/model changes, provider calls, image-generation requests, API/contract changes,
credential changes, persistence, unrelated Montessori changes, visual redesign, commit, or push.
Do not use real child media or place artwork/screenshots containing child data in evidence.

## Acceptance criteria

- AC-PIXI-FAIL-01: A safe, bounded renderer failure code and phase reach local diagnostics without
  exposing request data, capabilities, source bytes, or profile data.
- AC-PIXI-FAIL-02: A synthetic reproduction identifies the failing renderer stage; the failure is
  not inferred from HTTP 200 responses alone.
- AC-PIXI-FAIL-03: The confirmed defect has a regression test and the focused renderer test suite,
  renderer typecheck/build, and mobile typecheck pass.
- AC-PIXI-FAIL-04: The connected emulator completes a fresh Pixi launch with visible animation and
  playback controls; if a failure remains, the UI preserves the original image and reports a safe
  diagnostic code in developer-only output.
- AC-PIXI-FAIL-05: Existing backend-only provider boundaries and all unrelated worktree changes are
  preserved.

## Execution record

Pending implementation and verification.
