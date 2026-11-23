# Parent video player and screen copy — Rev60

**Date:** 2026-11-22  
**Environment:** FEAT-081 Expo Android emulator + local API  
**Plan/approval:** Plan Rev60 / Addendum 119  
**Result:** UI repair implemented; typecheck passed; post-change playback on the existing candidate could not be re-opened without leaving the approved no-inference boundary.

## Observed issue

The emulator showed the existing private candidate's first frame and its native controls. After tapping Play, the control remained at `00:00` and still exposed the accessibility action `Play`. The API log recorded HTTP 200 for the authenticated preview request, so the first frame had reached the device. The current screen used `onError={() => undefined}`, discarding playback errors.

The ready screen also repeated two technical/safety warnings and showed script revision, creation timestamp, resolution, FPS, scene count, and silent-video details in separate blocks.

## Code change

`apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx` now:

- Uses explicit accessible Play/Pause/Replay actions that call the Expo AV player methods.
- Tracks `isPlaying`, buffering, current position, duration, and completion to update the control and progress line.
- Shows a concise safe playback error and a “Tải lại video” action instead of ignoring player errors.
- Makes the player the primary content and reduces technical metadata to duration, scene count, and no-audio information.
- Keeps one short warning: “Bản thử nghiệm · Chưa kiểm tra an toàn.”

The authenticated preview endpoint, private headers, candidate data, safety status, and product-playable gate were not changed.

## Verification

| Check | Result |
|---|---|
| `pnpm --dir apps/ui-mobile typecheck` | Passed |
| Existing candidate preview request before the code change | HTTP 200; first frame rendered |
| Existing native Play after tapping before the code change | Reproduced at `00:00` |
| Post-change bundle | Reloaded from the FEAT-081 Metro server; no JS runtime error was observed in the inspected log window |
| Post-change Play/Pause on the candidate | **Not verified on-device** |

The app's Parent session is held in memory and was lost on the full bundle reload. After signing back in with the configured local synthetic account, the app resumed at activity selection. The history screen lists run status but has no action to reopen a stored video candidate. Proceeding from that screen would require an activity suggestion/inference. No such inference was sent, and no new video request was sent.

This report does not claim runtime playback is fully verified. To complete that check, reopen the existing ready candidate through a supported UI route or add an approved read-only route to it; then confirm that Play advances the displayed time and Pause stops it.

## Evidence and limits

- `screenshots/before-native-player-controls.png` — real emulator screen before the UI change, showing the paused native player.
- `screenshots/history-after-reload.png` — history screen after reauthentication; it exposes no direct action to open the ready video.
- No child media or credentials were added to evidence.
- No new run/candidate, inference, Modal deployment/warmup, DB mutation, quota/payment operation, gate bypass, commit, or push.
