# Parent cold resume and video preview — Rev62

**Date:** 2026-11-22 (Asia/Saigon)  
**Branch:** `feature/fe-mobile-remediation`  
**Scope:** approved Rev62; existing synthetic Parent run and video candidate only.

## Result

Rev62 passed its main UI checks. After a full app restart and sign-in with the existing local synthetic Parent account, **Tiếp tục** reopened the persisted, adult-confirmed story review. Opening the video screen loaded the existing ready candidate. The authenticated preview played on the Android emulator; Play advanced the timeline, Pause held it, and Play resumed from the paused position.

No new drawing, activity, story, or video inference was sent. No video-generation POST, quota/payment call, database mutation, or Modal deploy/warm-up occurred.

## Implementation

- Cold hydration now compares client revisions only when the client already holds the same run ID. A fresh controller's default revision `0` no longer invalidates a persisted server story.
- Entering the video screen starts the current-candidate GET before enabling video generation. The screen's own initial refresh shares the in-flight GET, avoiding duplicate requests. A failed lookup keeps generation disabled until a successful status refresh.

## Verification

| Check | Result |
|---|---|
| `pnpm --dir apps/ui-mobile typecheck` | PASS, exit 0 |
| API health `GET /health` | HTTP 200, `status=ok` |
| Cold app restart and Parent sign-in | PASS, existing synthetic account |
| Resume current run | PASS, opened confirmed story review |
| `GET /v1/story-runs/active/current` | 2 requests, HTTP 200 at 09:38:16 and 09:38:34 local time |
| `GET /v1/story-runs/{run}/video-generations/current` | HTTP 200 at 09:39:21; existing `CANDIDATE_READY` shown |
| `GET /v1/story-runs/{run}/video-generations/{candidate}/preview` | HTTP 200 at 09:39:42; Android decoder loaded video |
| Playback | PASS: 0:00 → 0:03; Pause remained at 0:18 across two captures; Resume advanced to 0:21; clip reached 0:30 and showed Replay |
| Video-generation/activity POSTs in API logs | None during this verification |
| Modal `dev` inventory | 3 existing apps deployed; all showed 0 active tasks |

## Evidence

- `resumed-run.png` — confirmed story restored after cold login.
- `video-screen.png` — existing ready candidate loaded.
- `player-loaded.png` — authenticated preview rendered the child's drawing.
- `player-playing.png` — playback advanced to 0:03.
- `player-paused-a.png` and `player-paused-b.png` — paused at 0:18 across both captures.
- `player-resumed.png` — playback resumed and advanced to 0:21.
- `player-final.png` — playback completed at 0:30.

## Remaining issue observed

The restored Story screen still displays **“Chọn hoạt động chính trước khi tiếp tục.”** even though it shows the persisted confirmed story and the existing video candidate. The API's `ParentStoryRunV1` response does not include the prior activity selection, and `adoptServerUnderstanding` resets the activity-review UI. This mismatch did not prevent opening the confirmed story or existing video, and was outside Rev62's approved change scope. It needs a separate contract/UI decision before claiming activity selection is fully restored after cold login.

## Safety and product status

The candidate is a private technical preview only. This check did not run safety or consistency validation; it does not establish `product_playable=true`. No real-child data was used. No commit or push was made.
