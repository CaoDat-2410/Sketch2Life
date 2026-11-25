# FEAT-085 context

The Parent Expo app previously showed its login screen on the Android emulator, but a login attempt did not produce a recorded submit callback, a navigation transition, or a backend auth request. The prior screenshot task was read-only and did not run inference. The owner now requests the fault be fixed and the real Parent workflow be exercised end to end. Existing repository changes are preserved.

## Runtime state — 2026-11-23 snapshot

After the owner replaced the Modal Hugging Face Secret again, the pinned LTX-2.5 access preflight passed, the 71.1 GB checkpoint was staged, and the existing synthetic Parent run reached a backend/UI-ready five-scene, 30-second silent video candidate through one real Modal request. Activity and story generation/review also passed in the same resumed workflow. The Android player was not verified: ADB shell/input stalled, and after transport recovery/reboot the app was back at sign-in; the attempted local re-entry was corrupted by emulator-console text input. The generated candidate was not resubmitted. Video and language/audio Modal apps used by this task are stopped; model volume is preserved. Full evidence: `evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md`.

## Playback verification — 2026-11-24

ADB login succeeded using the existing synthetic Parent credentials from the root `.env`; no credentials were added to evidence. The same run `c8ab4140-739e-496f-8b11-1c58e4a857a3` was resumed. The UI loaded its already-generated video candidate through the current-candidate endpoint, opened the authenticated preview, and played it to 0:08 / 0:30 with the video frame advancing. No new video or AI request was sent. The screenshot and detailed timeline are in `evidence/runtime/parent-video-playback-confirmed-20261124.png` and `evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md`. This establishes playback only; the technical preview remains unreviewed for safety/production use.

## Android HMR repair — 2026-11-24

The separate root Expo startup issue is fixed and verified on the Android emulator. Expo SDK 52's global Metro condition list selected Babel Runtime's ESM interop helper for a CommonJS call; the root Metro config now leaves import-kind conditions to Metro and preserves platform conditions. The Parent login screen rendered with no HMR or JS startup fatal error. The 16 KB native-library warning remains a separate unresolved compatibility item. See `evidence/ANDROID_HMR_RUNTIME_FIX_20261124.md`.

## Parent post-login crash repair — 2026-11-24

Logcat showed Firebase password sign-in and backend Parent-scope resolution both succeeding, followed by a render exception because the authenticated bottom bar called `useSafeAreaInsets()` without a root `SafeAreaProvider`. The root `apps/ui-mobile/App.tsx` now wraps `ParentExpoApp` in that provider. A real emulator login then rendered the authenticated Parent home screen; filtered logcat showed both auth stages succeeding and no SafeArea exception or `parent_auth_ui_failure`. No AI request or backend data mutation was made. Evidence is in `evidence/PARENT_POST_LOGIN_SAFE_AREA_FIX_20261124.md` and `evidence/runtime/`.

## Drawing output and resume failure — 2026-11-25

The authenticated Android Parent flow reached the deployed Qwen3.8-27B-FP8 drawing worker. Model inference completed, but the V2 parser rejected the generated box. Read-only run state: INPUT_REVIEW / FAILED, input revision 2, both input revisions retained, and no understanding accepted. The one replacement drawing was already consumed, so the accepted call was not retried. Source repairs now clarify box geometry without relaxing validation and restore the server-owned retake count after app restart. Mobile error/status recovery was also wired. These changes have offline tests only so far; live deployment and the two successful E2E runs remain outstanding. See evidence/DRAWING_BOX_AND_RESUME_RECOVERY_20261125.md.

## Two-run E2E attempt — 2026-11-25

The FEAT-085 API is running from the root checkout on `18001`; its health endpoint passed after the Rev12 repository-signature fix and Rev13 diagnostics rebuild. On Android, the real Parent flow created a synthetic transport/bicycle run and attached the generated child-style bicycle drawing. Modal staged the normalized image, then returned `RESOURCE_EXHAUSTED` on both bounded spawn attempts before any call ID. One post-diagnostics status/resume action was approved; it was also rejected before acceptance and classified safely as `ACCOUNT_QUOTA_OR_LIMIT`. The UI settles to a terminal/restart choice after polling. No Qwen inference, activity suggestions, story, or video was produced in Run 1. The later Addendum 20 continuation is recorded below. See `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`.

## One bounded retry and second-topic UI attempt — 2026-11-25

Addendum 20 separately authorized one authenticated Parent UI drawing request to compare the CPU Sandbox limits notice with the actual failure. The stale idea carried across topic paths was cleared and the focused mobile regression passed. The second topic was `Côn trùng`; `butterfly` matched the catalog alias for `con bướm`, so custom-subject validation returned `ON_TOPIC` without calling AI. After attaching the second synthetic crayon drawing, the single UI submit caused two bounded Modal `Function.spawn` attempts, both rejected with `ResourceExhaustedError` and no call ID. The UI settled and retained the drawing. No drawing inference, activity, story, or video was produced. The CPU Sandbox banner is separate from this GPU Function invocation path; the exact account/compute/rate limit remains unknown. Addendum 20's stop condition is now met. See `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`.

## Root `.env` reload and real Parent retry — 2026-11-25

After the owner updated the root `.env`, the real Android Parent run `c1004974-7634-4399-a55f-3d4fc1cbee62` reached Modal successfully. Qwen3.8-27B-FP8 returned a valid butterfly analysis through one accepted call; the adult confirmed it. The API was subsequently rebuilt/recreated alone to apply the approved Rev17 projection and activity-handoff fix; `/health` returned OK. The run read and activity-list calls both returned HTTP 200, and the stale-profile error cleared. The activity list was empty because this task database has zero `lesson.library_items` and zero `lesson.library_versions`. Story/video cannot proceed until a published/shared lesson is available or a separately approved no-candidate AI fallback is implemented. The run and drawing remain preserved. Detailed evidence: `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`.
