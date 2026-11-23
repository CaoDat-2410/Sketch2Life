# Plan Revision 60 — Parent video playback and compact preview UI

**Feature:** FEAT-081 Parent UI mobile port  
**Date:** 2026-11-22  
**Status:** APPROVED FOR IMPLEMENTATION by the owner's direct request to fix playback and simplify this screen  
**Authority:** FEAT-063 v2.7-draft SRS; this is a UI/runtime repair and does not change product requirements.

## User-visible problem

The existing Android screen shows the first frame and native player controls, but tapping Play leaves the time at `00:00`. The screen also repeats long technical and safety copy and shows implementation metadata (revision, timestamp, resolution, FPS, scene count) that obscures the drawing/video.

The preview endpoint returned HTTP 200 for the existing synthetic candidate. `VideoCandidateScreen` currently suppresses player errors with `onError={() => undefined}`, so the UI cannot explain a playback failure. The current screen is the reproduction baseline; no new video has been generated.

## Goal

Make the existing candidate straightforward to play on Android, make playback failures visible and recoverable, and let the video and the child's drawing take visual priority while retaining a concise and accurate experimental/safety notice.

## Authorized scope

- `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx`
- This plan and FEAT-081 approval, status, context, and feature-local evidence records.

No backend, SRS, video-generation worker, dependency, account, run, candidate, quota, or payment changes.

## Implementation

1. Replace the native-control-only interaction with explicit accessible Play/Pause/Replay actions backed by the existing Expo AV `Video` instance. Track playback status and elapsed/duration values; do not force the player to remain paused after a user action.
2. Show a short loading/buffering state. Surface a safe, concise playback error instead of swallowing `onError`; allow reloading the existing private preview through the existing `onPreview` action.
3. Reorder the ready state so the video player is the primary content. Remove revision timestamp, resolution and FPS from the parent-facing screen; keep only compact duration and scene-count information when available.
4. Replace repeated paragraphs with one concise notice: “Bản thử nghiệm · Chưa kiểm tra an toàn”. Preserve the synthetic-only restriction and the fact that the video is not product-approved. Do not imply that safety/consistency validation ran.
5. Keep the current palette, card/button components, typography scale, accessibility labels, authentication headers, and private preview endpoint.

## Acceptance criteria

- On the Android emulator, the existing candidate responds to Play: playback state changes and the elapsed time advances. Pause stops it; Play resumes; after completion Replay starts it again.
- Any playback error appears in the UI with a retry action; no silent no-op error handler remains.
- The video is prominent and the ready screen removes redundant technical details and long repeated notices.
- The concise notice continues to identify this as an experimental preview that has not passed safety review.
- Typecheck passes and the existing candidate is used for manual verification. No new generation request or Modal inference is sent.
- Evidence includes ready, playing, and error/retry states if the existing candidate can reproduce them; do not fabricate an error state if none occurs.

## Exclusions

No new video inference, Modal deploy/warmup, database mutation, quota/payment call, gate bypass, safety/consistency status change, product-playable change, API contract change, or commit/push.

## Implementation outcome — 2026-11-22

- Player controls, progress/error handling, and compact copy are implemented; mobile typecheck passed.
- The original issue was reproduced before the change: authenticated preview returned HTTP 200 and rendered the first frame, while native Play remained at `00:00`.
- **Acceptance remains partial:** after reload, the authenticated Parent resumes at activity selection. Existing history does not expose the already-ready candidate, and continuing would require an AI activity request. No such request was sent, so post-change Play/Pause has not been verified on-device.
- Evidence: `../evidence/PARENT_VIDEO_PLAYER_UI_REV60_20261122/RUN_REPORT.md`.
