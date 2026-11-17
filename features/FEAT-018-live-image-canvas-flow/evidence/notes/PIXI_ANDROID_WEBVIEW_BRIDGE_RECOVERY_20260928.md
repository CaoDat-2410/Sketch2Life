# Pixi Android WebView bridge recovery — 2026-09-28

- Evidence ID: `EV-018-PIXI-WEBVIEW-BRIDGE-RECOVERY-20260928`
- Scope: approved FEAT-018 bridge recovery only; synthetic/non-child demo; no live AI/provider call.
- Plan: `../plan/PIXI_ANDROID_WEBVIEW_BRIDGE_RECOVERY_20260928.md`

## Diagnosis from runtime logs

The local backend log showed session creation, image admission, understanding, Gate A, P1, Gate B,
and the renderer launch succeeding (HTTP 200/201). The renderer page and hashed chunks loaded, but
the source/rig endpoints were not requested while the UI remained on “Đang mở…”. The page was
rejecting the inbound launch because the 4 KiB renderer-event cap was also being used for the much
larger native launch command. Separately, duplicate page bootstrap was incorrectly allowed to look
like renderer readiness.

After the bridge-size correction, a renderer source request reached the backend but returned 404:
the source/package grant had exceeded its 90-second TTL. A rebuild also changed content-addressed
chunk names while a retry reused the old page shell, causing requests for removed hashed chunks.
On the later manual retry, the renewed launch request returned HTTP 410 because the in-memory demo
session had already exceeded its 30-minute idle TTL. This final 410 is session expiry, not evidence
that the bridge still rejects the command.

## Changes and validation

- Native-to-page launch/control messages now use a safely serialized JavaScript bridge and a
  separate 128 KiB limit; page-to-native renderer events remain capped at 4 KiB.
- Bootstrap and renderer readiness are distinct; only a matching renderer response advances the
  state. Retries receive a fresh page-shell URL and explicitly refresh renderer source/package
  capabilities before remounting.
- Added renderer bridge tests, plus an offline same-session API regression that reissues source and
  package grants and reads them without increasing the vision/provider call count.
- Passed: `pnpm --filter @sketch2life/art-renderer test` (36 tests); renderer typecheck and
  `build:demo`; `pnpm --filter sketch2life-mobile exec tsc --noEmit -p tsconfig.json`;
  `pnpm --filter sketch2life-mobile test` (`UI_COPY_AND_RECOVERY_VALID`); and
  `backend/tests/contract/test_live_image_demo_api.py::test_fake_only_image_session_completes_p1_gate_b_p4_handoff_feedback_and_gallery`
  (pytest passed; only a pytest-cache permission warning).
- Final local service probe returned HTTP 200 from backend `/health`. `adb` is not available on this
  shell, so this turn did not independently reload or drive the emulator.

## Acceptance boundary

The currently observed Android session was stale by the time the explicit retry ran, so a fresh
session could not be used to complete end-to-end playback verification without starting a new
owner-controlled flow. The backend trace did show the renderer source request after bridge delivery,
and the offline contract test proves successful renewed source/package reads. Fresh-session Android
source/package HTTP 200s, playback progress, and controls remain pending. Codex did not initiate a
Qwen, SAM, Lightning, ASR, or other provider request, and no drawing, token, or signed capability is
stored in this evidence record.
