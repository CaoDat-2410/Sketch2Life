# Pixi renderer diagnostics — partial verification — 2026-09-30

- Evidence ID: `EV-018-PIXI-RENDERER-DIAGNOSTICS-PARTIAL-20260930`
- Plan: `../../plan/PIXI_RENDERER_PLAYBACK_FAILURE_DIAGNOSIS_AND_FIX_PLAN_20260930.md`
- Scope: approved Pixi/WebView playback diagnosis; synthetic/non-child media only.

## Implementation and offline checks

- Moved renderer failure-code normalization into a shared allowlist. Arbitrary exception text,
  URLs, tokens, payloads, and object details collapse to `RENDERER_V2_START_FAILED`.
- The mobile host now logs the allowlisted `PLAYBACK_FAILED` code only in development; production
  continues to show generic child-safe copy.
- Added regression tests for accepted codes and rejection of untrusted diagnostic strings.
- Passed: renderer tests (47), renderer typecheck, renderer static demo build, mobile TypeScript
  check, and mobile UI-copy/recovery test.

## Emulator boundary and incomplete acceptance

- The synthetic image was admitted locally, but the subsequent understanding result was `BLOCKED`
  with sanitized progress reason `VISION_RESULT_FAILED`. The UI never created a renderer launch,
  so this run cannot identify a Pixi/WebView failure or confirm playback.
- During the emulator attempt, the explicit “Bắt đầu khám phá” control was tapped and triggered one
  configured live Lightning request unintentionally. This violated FEAT-018's owner-run provider
  boundary. The result was blocked before Pixi; Codex stopped further provider calls immediately.
  Whether the request consumed billable/credit usage is unknown from local evidence.
- No image bytes, child/profile content, request identifiers, capabilities, credentials, endpoint
  values, or screenshots are retained in this record.
- AC-PIXI-FAIL-01's code path is implemented and covered offline. AC-PIXI-FAIL-02 and
  AC-PIXI-FAIL-04 remain unmet: the exact runtime code and visible Pixi animation were not observed.
  No speculative animation/canvas change is claimed as a fix.

## Next safe step

The project owner must initiate a fresh synthetic/non-child run in the configured live environment
after the updated mobile bundle is loaded, then share only the visible `Pixi lỗi: <CODE>` string or
the corresponding `[pixi-bridge] renderer playback failed <CODE>` development log. Codex can then
make a narrowly targeted renderer fix without initiating another provider call.

## Follow-up after owner supplied renderer code — 2026-09-30

The next owner screenshot supplied the exact safe renderer code `MASK_BACKGROUND_RECONSTRUCTION_FAILED`.
Inspection traced it to the bounded local paper donor search in `subjectCutout.ts`; a synthetic
seven-pixel saturated outline reproduced the same failure. The search now reaches up to 12 pixels
while remaining local, rejecting saturated donors and preserving exact outside-mask pixels. The
regression fails before and passes after the change; 48 renderer tests, renderer typecheck/build,
mobile typecheck and UI-copy tests pass. Details are in FEAT-030
[`E-030-FIX-013`](../../../FEAT-030-original-derived-auto-rig/evidence/notes/PIXI_MASK_BACKGROUND_RECONSTRUCTION_FIX_20260930.md).

No Android visual acceptance is claimed: although `emulator-5554` is connected, a fresh current-flow
launch requires the live backend rig/mask path and was not initiated by Codex. No image/provider
request was made. The separate bird-topic issue remains under its awaiting-approval plan.
