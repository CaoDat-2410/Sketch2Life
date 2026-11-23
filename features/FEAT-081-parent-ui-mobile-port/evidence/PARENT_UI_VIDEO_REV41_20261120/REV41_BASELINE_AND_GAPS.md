# FEAT-081 Rev41 — baseline and gap audit

**Date:** 2026-11-20 (Asia/Saigon)  
**Branch/worktree:** `feature/fe-mobile-remediation`, `<local-machine-path>  
**Plan/approval:** Plan Revision 41 / TASK_APPROVAL Addendum 67.  
**Data:** synthetic Parent/profile/artwork only.

## Runtime observed

- Android device `emulator-5554` is online and runs `com.sketch2life.parentexpo.dev/.MainActivity`.
- The active Parent app is the real Expo app, not `ParentVisualPreviewHarness`.
- Task API `127.0.0.1:58100/health` returned HTTP 200. Task Metro `127.0.0.1:8081/status` reported `packager-status:running`.
- The task API belongs to Compose project `s2l-feat081-rev23`; its API, Redis, PostgreSQL, MinIO, and ClamAV are running. Other Compose projects are also active and are outside this task; none were stopped or changed.
- ADB is available at `D:\AndroidStudio\platform-tools\adb.exe` although it is not on PATH.
- Live pre-change capture: `00-before.png`. The UI reports the story as adult-confirmed; no video call is being made until the server confirms the exact current revision/hash and admission.

## Parent UI audit

The story screen uses the current purple Parent design. It visibly contains generated prose contamination: character-count strings such as `(149 ký tự)` and stray trailing numeric fragments such as `68` and `69`. The activity copy fix is present in the source/bundle, but the current emulator session previously retained stale activity text; it needs a real app reload and visual verification.

These six screen files still use the default `ScreenFrame` visual tone, while current workflow screens use the `creative` tone:

- `ContextScreen.tsx`
- `HandoffScreen.tsx`
- `DrawingGuideScreen.tsx`
- `LessonPickerScreen.tsx`
- `TranscriptReviewScreen.tsx`
- `SketchGuideScreen.tsx`

## Video contract/source audit

- Served API OpenAPI contains Parent topic, drawing, activity-selection, story-revision, and StoryRun lifecycle routes, but no Parent video request/status/playback routes.
- `useParentPlatformController` returns unavailable for Parent video operations, and Story/Handoff only display the unavailable capability message.
- Existing `story_video.py` and `StoryVideoJobService` use the legacy session-oriented video workflow and Lightning adapter; they do not satisfy the Parent StoryRun + LTX-2.5 contract and will not be used as a substitute.
- `deployment/modal/srs_v23/video_app.py` validates the dev envelope and then raises `MODAL_WORKLOAD_NOT_CONFIGURED`; there is no LTX inference implementation or real video readiness.
- The Data Table Register already defines `story.video_generations` and `story.video_generation_scenes`, plus AI Job, Billing admission, and Core Asset ownership. Source search found no corresponding Parent video persistence mapping/migration in this worktree. M2 must align code to those mappings; add a migration only if the disposable task database is verified and the exact mapping is missing.
- One official source check confirmed the LTX-2.5 model is split into transformer/text encoder/VAE/upscaler assets and the official image-to-video pipeline conditions frame 0 from the source image. References: [official LTX-2 repository](https://github.com/Lightricks/LTX-2), [LTX-2.5 model card](https://huggingface.co/Lightricks/LTX-2.5), [Modal LTX example](https://modal.com/docs/examples/ltx), [Modal Volumes](https://modal.com/docs/guide/volumes). This is implementation guidance only; runtime/model access is not yet verified.

## Current gates and actions

- No new drawing or activity inference has been sent.
- No story rewrite or video inference has been sent under Rev41.
- The story screen displays an adult-confirmation badge, but the exact server-owned confirmation hash has not yet been read; do not infer admission eligibility from the badge.
- Real quota/compute admission and automatic video safety remain required. No quota bypass, direct database mutation, or fixture is permitted.
- No code tests have been run for Rev41 yet. Docker, Metro, emulator, and Modal lifecycle have not been modified by the audit.
