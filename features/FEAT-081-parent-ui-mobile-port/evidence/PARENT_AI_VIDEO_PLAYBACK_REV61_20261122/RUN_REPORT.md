# Parent AI and video-player verification — Rev61

**Date:** 2026-11-22  
**Environment:** Android emulator `emulator-5554`, FEAT-081 API Docker, Modal `dev`  
**Plan/approval:** Plan Rev61 / Addendum 120  
**Result:** Existing AI outputs and video candidate are present. A new Activity AI request was rejected by the backend before Modal dispatch. The post-Rev60 Play/Pause UI could not be reached after a fresh app resume, so playback remains unverified.

## Environment

| Check | Result |
|---|---|
| FEAT-081 API `/health` | `ok` |
| Android app | Running on `emulator-5554` |
| Modal `dev` apps | Language/audio, drawing VLM, and video apps are deployed; each reported zero tasks |
| Modal work started by this check | None; no deploy, warm-up, or shutdown performed |

## Existing real synthetic AI outputs

Read-only database inspection found a completed Parent run (ID `0af8455f…a40ea7`):

| Stage | Persisted result |
|---|---|
| Activity suggestions | One `AI_GENERATED_FALLBACK` set, zero catalog candidates, provider call reference present |
| Activity selection | Selection records exist |
| Story | Revision 1 is `CONFIRMED`; five scenes; 30 seconds; provider call reference present |
| Video | Candidate `65312f2a…9803bbfda910` is `CANDIDATE_READY`; Modal call reference present; 4,289,168 bytes; 30.209 seconds; 1280×720; five scenes |

The video candidate was created 2026-11-22 00:26 UTC and reached its last persisted update at 00:35 UTC. This confirms that AI had already produced and persisted the activity, story, and video outputs before this check. The candidate is still a private technical preview; this report does not mark its safety/consistency validation complete or make it product-playable.

## Attempt made from Android

At `2026-11-22T01:48:25Z`, the real Parent UI's **“Thử lấy gợi ý lại”** action sent one request to:

`POST /api/parent/v1/ai/story-runs/{run_id}/activity-suggestions`

The API returned **HTTP 409** at `01:48:27Z`. The run was already `SCRIPT_REVIEW`, with a confirmed story and a ready video candidate. The handler only admits a new activity set while the run is `PREPARATION_REVIEW`; therefore it rejected the stale Activity action as `PARENT_STORY_RUN_NOT_READY_FOR_ACTIVITY`. The request did not reach Modal. No language/audio function-call log appeared in the request window, and the app remained at zero tasks.

No retry was sent. There was no new AI inference, video generation, database write, quota/payment action, or gate bypass.

## Resume/player blocker

After restarting the app and signing in with the configured synthetic Parent, the home screen displayed an open run. Resuming it returned to the Activity screen with no suggestions, rather than reopening the confirmed story or ready video. The backend reports the saved run as `SCRIPT_REVIEW` and the ready candidate remains attached to it.

Source inspection points to the resume-state handling in `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`: a fresh controller starts with `understandingRevision = 0`; `adoptServerUnderstanding` treats the server's saved revision `1` as a revision change and routes to Activity instead of adopting the already saved story. The Video screen also does not hydrate the current candidate until its status action is called. These paths need a separately approved code amendment before the existing candidate can be reopened from a cold app start.

Therefore **Play/Pause/Resume on the updated player was not verified**. The existing Rev60 before-change screenshot shows the old native player problem; this Rev61 run has no post-change playback claim.

## Evidence

- `screenshots/activity-request-started.png` — real Android Activity screen after entering the step.
- `screenshots/activity-ai-request.png` — real Android screen after the single backend-rejected request.
- `screenshots/resume-after-profile-select.png` and `screenshots/resume-cta.png` — actual resume result, showing the Activity step rather than the saved story/video.
- API access log timestamps and read-only database state are summarized above; no credentials, account email, or raw model output are stored here.

## Cleanup and limits

- No Modal apps were started by this check. Existing `dev` deployments remain deployed and idle with zero tasks; unrelated app state was left untouched.
- No product code changed in Rev61. The approved plan excludes code edits; the resume/player re-entry repair requires a new approval addendum.
- No commit or push.
