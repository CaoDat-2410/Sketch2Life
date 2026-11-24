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
