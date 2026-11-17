# FEAT-030 runtime fix — SAM2 mask handoff and cutout playback

- Status: APPROVED_BY_DIRECT_OWNER_FIX_REQUEST; MASK_HANDOFF_IMPLEMENTED; STARTUP_BRIDGE_REPLAY_IMPLEMENTED_LOCALLY; ANDROID_ARTIFACT_RETEST_PENDING
- Date: 2026-09-27
- Scope: fix the runtime path where the Lightning worker reports SAM2.1 segmentation `SUCCEEDED`, but PixiJS does not consume the returned mask and the mobile screen later times out or appears to fall back.
- Authority: direct owner request “fallback rồi, dù sam 2 chạy success, check lỗi và fix”, current FEAT-030 approved requirements, and the existing `CUTOUT_MICRO_MOTION` tier requirement. This addendum does not activate a new model or provider.

## Diagnosis

The SAM2.1 adapter stores the mask and the package advertises an `ORIGINAL_DERIVED_MASK`, but the renderer currently treats that descriptor as a boolean only. It does not fetch or decode the mask. When no semantic parts are returned, the backend correctly avoids `FULL_AUTO_RIG`; however, the butterfly renderer still creates hard-coded left/right image crops from the SAM bounding box. Thus successful SAM subject segmentation is not actually the image used for rendering, and it can look like whole-image motion or a failed/fallback experience. Renderer startup failures are also not surfaced consistently to the native playback state.

## Planned change

1. Issue a separate short-lived, bounded read capability for the verified derived mask; expose a typed mask endpoint and additive optional V2 launch/load fields. Keep mask bytes off the React Native bridge.
2. In the WebView, fetch the mask with `no-store`, verify its SHA-256 and dimensions, decode it, and derive a foreground cutout from the immutable original. Patch only the segmented silhouette when bounded corner samples validate a near-uniform neutral paper background; otherwise reject cutout motion and downgrade safely.
3. For `CUTOUT_MICRO_MOTION` without semantic part masks, animate the actual subject cutout as one bounded subject layer. Do not synthesize anatomy by splitting a bbox. Keep the source drawing immutable and retain the original as the base/background.
4. If a mask is absent, unreadable, mismatched, or invalid, emit a bounded typed renderer failure/fallback reason and use the existing safe V1 fallback. Do not leave the app waiting with zero duration and no renderer event.
5. Record sanitized diagnostics and feature-local evidence; do not log tokens, mask pixels, source imagery, or child data.

## Acceptance criteria

- AC-FIX-030-01: a valid SAM2 `SUCCEEDED` mask is retrievable only through a short-lived, single-purpose capability and is hash-checked before rendering.
- AC-FIX-030-02: a valid subject-only mask produces `CUTOUT_MICRO_MOTION` using the SAM-derived silhouette; it does not use the hard-coded butterfly crop split or claim `FULL_AUTO_RIG`.
- AC-FIX-030-03: the original source remains immutable and visible as the renderer base; only the derived overlay moves, within existing motion bounds.
- AC-FIX-030-04: missing/expired/tampered masks deterministically downgrade to V1 and report a sanitized reason to the native screen; no indefinite `INTRO_LOADING` state.
- AC-FIX-030-05: Python and TypeScript contract/unit tests cover capability expiry/replay, mask hash/identity validation, successful cutout mode, missing-mask fallback, and legacy V2 launch compatibility.
- AC-FIX-030-06: repository security validation passes before any commit or push.

## Verification

- Focused backend unit/contract tests for derived-mask capability issuance and reads.
- Focused renderer tests for mask verification, alpha extraction, subject-only tier behavior, and deterministic downgrade.
- Typecheck/build the art-renderer demo bundle and mobile app typecheck where toolchain is available.
- Run `python tools/validate_repository_security.py` before any commit/push.
- Runtime Android/Lightning visual verification remains pending unless those services are available during this task.

## Explicit exclusions

- No new SAM/Qwen inference, model activation, extra provider, AI-generated image, or fabricated semantic part mask.
- No change to Gate A/Gate B, learning content, or the final video/activity workflow.
- No promotion from subject-only mask to full auto-rig without validated semantic part masks and rig criteria.

## Follow-up — renderer boot/bridge timeout, 2026-09-28

- Status: APPROVED_BY_DIRECT_OWNER_FIX_REQUEST; STARTUP_BRIDGE_REPLAY_IMPLEMENTED_LOCALLY; ANDROID_ARTIFACT_RETEST_PENDING
- Scope: continue the same unresolved renderer handoff covered by AC-FIX-030-04 and AC-FIX-030-07..09. The owner supplied a current Android screen showing that the first startup-handshake change still did not start playback.
- Evidence-based diagnosis (emulator retest, 2026-09-28): on `emulator-5554` (Pixel_10, Android 17, x86_64), WebGL 1 and WebGL 2 contexts were available. Pixi initialization completed and attached one canvas; the page then remained at “Pixi sẵn sàng, đang chờ launch của đúng phiên.” The native screen had received the bootstrap (it showed the post-handshake timeout), but the backend logged no source, rig-package, or rig-mask read. This rejects the earlier hypothesis that `Application.init()` itself was stuck: the native-to-WebView launch post sent with the initial bootstrap can be lost during WebView/renderer startup. The bridge must replay the same bounded launch after Pixi readiness, without creating another capability or inference.
- Planned changes:
  1. Keep the bridge installed before asynchronous Pixi initialization and send the initial bootstrap immediately.
  2. Cache one validated native launch command and replay the exact same command when the page re-announces bootstrap after Pixi becomes ready (or initialization fails); make replay idempotent so all artifact reads and playback happen at most once.
  3. Keep the native timeout bounded and stage-aware: distinguish missing bootstrap, Pixi initialization, and post-ready launch/load timeout; never describe these as a SAM2/mask fallback.
  4. Preserve sanitized initialization-failure reporting, all existing artifact-integrity checks, and focused replay/deduplication regression tests.
- Acceptance criteria:
  - AC-FIX-030-07: the initial bootstrap is posted before Pixi GPU initialization; the exact same validated launch is replayed after readiness and processed once even if the first native-to-WebView delivery is dropped.
  - AC-FIX-030-08: Pixi initialization rejection or a bounded stage-specific timeout is surfaced as a renderer-startup failure, not a segmentation/mask fallback; no indefinite loading state remains.
  - AC-FIX-030-09: regression tests cover queued/replayed delivery, duplicate suppression before and after ready/failure, and initialization failure; existing renderer tests and bundle build pass.
- Verification: art-renderer unit tests/typecheck/build, mobile typecheck, and renderer-host asset smoke checks. Android validation should confirm that replay causes one source/package/mask fetch and playback using a safe local fixture. Do not invoke live model inference for this bridge regression. Repository security validation is required before any commit/push.
- Authority: the owner’s approved request to fix the continuing renderer fallback, followed by the current failing screenshot. This refines the approved bounded one-command queue/replay under AC-FIX-030-07..09; no model/provider activation, external contract change, Gate change, or child-data handling is included.
- Local verification completed 2026-09-28: art-renderer tests (32 passed), art-renderer typecheck, Vite mobile renderer build, and mobile TypeScript check passed. Emulator retest reproduced working WebGL and successful Pixi init followed by a missing launch/artifact read. The idempotent replay change is implemented; full Android artifact-read retest remains pending because re-entering the flow may call the configured Lightning provider.
