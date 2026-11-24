# FEAT-085 context

The Parent Expo app previously showed its login screen on the Android emulator, but a login attempt did not produce a recorded submit callback, a navigation transition, or a backend auth request. The prior screenshot task was read-only and did not run inference. The owner now requests the fault be fixed and the real Parent workflow be exercised end to end. Existing repository changes are preserved.

## Runtime state — 2026-11-23 snapshot

After the owner replaced the Modal Hugging Face Secret again, the pinned LTX-2.5 access preflight passed, the 71.1 GB checkpoint was staged, and the existing synthetic Parent run reached a backend/UI-ready five-scene, 30-second silent video candidate through one real Modal request. Activity and story generation/review also passed in the same resumed workflow. The Android player was not verified: ADB shell/input stalled, and after transport recovery/reboot the app was back at sign-in; the attempted local re-entry was corrupted by emulator-console text input. The generated candidate was not resubmitted. Video and language/audio Modal apps used by this task are stopped; model volume is preserved. Full evidence: `evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md`.

## Playback verification — 2026-11-24

ADB login succeeded using the existing synthetic Parent credentials from the root `.env`; no credentials were added to evidence. The same run `c8ab4140-739e-496f-8b11-1c58e4a857a3` was resumed. The UI loaded its already-generated video candidate through the current-candidate endpoint, opened the authenticated preview, and played it to 0:08 / 0:30 with the video frame advancing. No new video or AI request was sent. The screenshot and detailed timeline are in `evidence/runtime/parent-video-playback-confirmed-20261124.png` and `evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md`. This establishes playback only; the technical preview remains unreviewed for safety/production use.
