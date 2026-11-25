# FEAT-085 status — updated 2026-11-24

**Current result: Parent flow reached and played a generated video candidate through the real Expo UI, backend, and Modal workers.** Playback was verified on Android on 2026-11-24 from the existing candidate; no new inference was sent. The HF token update worked on the second retry: pinned LTX-2.5 checkpoint access passed, the checkpoint was staged, and the one authorized video inference completed successfully. No fixture output was used; video admission and other hard gates remained enabled. No commit or push.

| Stage | Result | Evidence |
|---|---|---|
| Existing synthetic Parent run resumed in Android UI | PASS | Run `c8ab4140-739e-496f-8b11-1c58e4a857a3`; real persisted session. |
| Activity suggestion and selection | PASS | Modal call `fc-01M84FA02D9YQ715563AB38MAB`; three generated suggestions persisted; parent selected one. |
| Story generation and adult confirmation | PASS | Qwen3.8 call `fc-01M84G2DTWCRQZK2TKDSQAY8PD`; five-scene Vietnamese draft shown and confirmed in UI. |
| LTX access after latest Secret replacement | PASS | CPU-only access preflight accepted the pinned repository and revision; earlier 401 evidence is retained for history. |
| LTX checkpoint staging | PASS | 5 files, 71,114,917,404 bytes downloaded to the Modal model volume; volume preserved. |
| Video generation and backend/UI readiness | PASS | One UI POST returned 202; Modal LTX-2.5 call `fc-01M84HE5K6R6MPXAA3M2J63DMQ` completed five scenes, silent assembly, and final media validation. UI showed “Video đã sẵn sàng”, 30 seconds, 5 scenes, no audio. |
| Open and play candidate on Android | PASS (2026-11-24) | Signed into the synthetic Parent account via ADB, resumed the same run, loaded the existing candidate through the current-status API, opened its authenticated preview, and observed playback advance to 0:08 / 0:30. See `evidence/runtime/parent-video-playback-confirmed-20261124.png`. |
| Modal cleanup | PASS | The exact video and language/audio apps were stopped; Modal inventory showed `stopped`, 0 tasks. Model volumes were preserved. |

Full timeline, call references, and screenshot links: [RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md](evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md). The post-worker UI screenshot is [parent-video-after-worker.png](evidence/runtime/parent-video-after-worker.png); playback evidence is [parent-video-playback-confirmed-20261124.png](evidence/runtime/parent-video-playback-confirmed-20261124.png).

The earlier 2026-11-23 notes record the state before playback was verified. The video remains an unreviewed technical preview; production safety approval is not claimed.

## Two-run Android E2E attempt — 2026-11-25

**Status: BLOCKED before AI inference; the requested two successful runs are not complete.** The real Parent UI created the transport/bicycle run and attached an independently generated synthetic crayon drawing. Modal rejected `Function.spawn` twice before returning a call ID. After adding safe diagnostics and rebuilding only the FEAT-085 API, the approved UI resume was rejected again with `RESOURCE_EXHAUSTED` classified as `ACCOUNT_QUOTA_OR_LIMIT`. Under the separate one-request Addendum 20, a second-topic butterfly flow reached custom-subject validation, image selection, and one UI submit; Modal again rejected both bounded spawn attempts before a call ID. The UI retained the synthetic drawing and settled to an actionable error state. No drawing inference, activity list, story script, or video was produced in the 2026-11-25 E2E attempts.

API health and seven focused diagnostics tests pass. The Android UI settles to an actionable failure state after polling. The Modal workspace account/limit condition must be resolved before a new inference authorization can produce the two requested E2Es. Full timings, logs, screenshots, and exact limitations: [REPORT.md](evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md).

The custom topic/subject path was not blocked by catalog coverage in the second attempt: topic aliases normalize first; known subject aliases return deterministically; unknown or ambiguous subjects are intended to fall through to the gated topic-validation AI. `butterfly` matched the catalog alias for `con bướm`, so this particular validation did not call AI. The later Modal screenshot showed zero usage against the visible workspace concurrency, GPU, creation-rate, and Sandbox counters; therefore saturation of those displayed counters is not supported. The safe `ResourceExhaustedError` category is a text-pattern classification, not Modal's exact root cause. Billing/entitlement, function-specific queue/placement, and transient provider rejection remain unverified possibilities. The CPU Sandbox notice is a separate Modal feature from this `Function.spawn` path. Details are in the report's screenshot addendum.
