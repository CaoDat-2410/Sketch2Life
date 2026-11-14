# FEAT-069 execution record

## Rev6 Parent home and Rev38 flow audit

Date: 2026-11-14 (Asia/Saigon)
Approved scope: `plan/PLAN_REV6_PARENT_HOME.md`, SHA-256 `B5AF1EB11C4DB22B2F4EC60F78786D5E62A3025E5638531BCC00BE0C24BA8CB1`.

- Removed the redundant selected-child summary from `UI_Project/parent-ui/src/App.tsx` and its styles. The child's selection remains in story setup and Family Profile. Added responsive Parent home layout refinements in `src/rev6.css`; no generated visual assets or API/auth wiring were added.
- `npm run build` from `UI_Project`: passed all five workspaces (Parent, Teacher, School Manager, Platform Admin and shared web portal).
- `git diff --check`: passed.
- Parent `http://127.0.0.1:5171/`: reopened after the change. The accessibility tree showed the home hero, “Bắt đầu kể” CTA and primary navigation and no “ĐANG DÙNG HỒ SƠ” card. This was a focused browser check, not a full Parent or Android runtime walkthrough.
- Read-only Rev38 comparison: see `REV38_FLOW_ALIGNMENT_20261114.md`. Result is partial alignment, not full parity. The UI/role workspaces remain local preview fixtures and do not make API/auth requests.
- No automated tests were added or run. No APK rebuild/install was performed in this Rev6 step; the browser page is a web preview, not proof of APK runtime.

Date: 2026-11-14 (Asia/Saigon)
Branch: `FE_UI_Project_Ver2`
Review basis: approved `plan/PLAN_REV2.md`, leader transcript referenced in `CONTEXT.md`, FEAT-063 SRS v2.5-draft and the mounted API/source crosswalk.

## Build and packaging

| Command | Result |
|---|---|
| `npm run build` from `UI_Project` | Passed for Parent, Teacher, School Manager, Platform Admin and the shared web portal (all 5 workspaces), including after the Parent scroll-reset adjustment. |
| `pnpm typecheck` from `UI_Project/parent-android` | Passed (`tsc --noEmit`). |
| `pnpm --dir apps/mobile android:apk:debug` from `UI_Project/parent-android`, with `ANDROID_HOME` / `ANDROID_SDK_ROOT` pointing to the local Android SDK | Passed after the final Parent bundle update; Gradle reported `BUILD SUCCESSFUL in 54s`. The package task embeds the latest built `parent-ui` page. APK path: `UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`. |
| `git diff --check` | Passed; Git reports line-ending normalization notices for two existing CRLF files. |

Gradle emitted existing Gradle 10 compatibility/deprecation notices and a Node child-process deprecation warning; none failed packaging. No automated tests were added or run, per the approved plan.

## Manual visual review

The updated local workspaces were reviewed through the in-app browser on 2026-11-14. Screenshots from the live review were inspected in the CUA session; the feature's `evidence/screenshots/` directory contains the Rev1 saved captures and is retained as historical evidence, not misrepresented as newly saved Rev2 captures.

- Parent `http://127.0.0.1:5171/`: reviewed the compact home and create flow; selected a profile and opened the optional guide. The three guide states displayed distinct static drawings and instructions (large starting shape, added details, then color choice), each with a step indicator and static/no-AI disclosure. Opened the child profile edit form and confirmed gender is optional and labeled session-only. The capture page correctly blocks continuation without an image; no user file or child media was selected. Parent review/script/audio paths that require a photo or microphone input were not manually completed.
- Teacher `http://127.0.0.1:5172/#session`: selected the configured class/lesson/activity, stepped through all three static slides, reached the interaction acknowledgement, then saw a separate sample-video gate. Opened `#sample` and confirmed it requires the fixture eligibility/consent step before continuing; the sample remains explicitly fixture-only and no child identity or media was uploaded.
- School Manager `http://127.0.0.1:5173/`: dashboard rendered with fixture/preview disclosure.
- Platform Admin `http://127.0.0.1:5174/`: dashboard rendered with fixture/preview disclosure.

This was a manual visual walkthrough of the paths listed above, not a full keyboard, focus, screen-reader or every-route audit. These browser checks do not prove APK runtime behavior or live backend integration.

## Android emulator installation attempt

The earlier Rev2 debug APK install on `emulator-5554` stalled for more than 90 seconds and was interrupted; Package Manager/system-server had returned `Broken pipe (32)` with system-server/GMS failure logs. No wipe/reset was performed. A Rev3 retry is recorded below.

Therefore, the debug APK is build-verified but this exact build has not been opened on the supplied emulator. Use the APK at the path above for a teammate/device install after the emulator's Package Manager recovers. The Parent browser phone view is only the same UI source in a web shell.

## Runtime/API boundaries

- Parent UI source is `UI_Project/parent-ui`; the Android app `UI_Project/parent-android/apps/mobile` bundles that source into its local WebView. The Parent Vite URL is only a browser preview.
- Teacher, School Manager and Platform Admin are web workspaces. At Rev2, dashboard counts and lists were fixtures; see the Rev3 supplement below for the limited conditional reads now wired for Teacher lessons/assignments and Manager classes. Platform Admin remains fixture preview.
- Parent library, invitation and selected lesson-detail reads plus user-triggered invitation accept/decline are conditionally wired to mounted Lesson Library routes when auth is injected. Parent profile state, lesson activity selection, mismatch result and story flow remain preview state. Gender is not persisted. The optional activity-before-video presentation intentionally follows the leader-review prototype and conflicts with the unsigned SRS; see `OPEN_QUESTIONS.md`.
- End-to-end auth/dashboard, ASR, line-sketch AI, generated Teacher deck, session persistence, image analysis, Parent profile/story/video API or playback is not runtime-verified or claimed.
- No real child media/profile data was used, and no API writes or AI/provider requests were made.

## Review result

The approved Rev2 UI scope and Rev3 API-aware screens are implemented in source. See the Rev3 supplement for final builds and the emulator result. Product conflicts and missing contracts remain explicit in `OPEN_QUESTIONS.md`; the UI is not a claim that every leader request is signed off in the canonical SRS or supported by live APIs.

## Rev3 API-backed UI update

- Updated `UI_Project/shared/webWorkspace.tsx` to use typed current-branch GET methods only in Teacher/Manager workspaces when runtime Firebase token bridge and organization ID are present. Teacher loads lesson summaries plus adult assignments; Manager loads classes. Their connected dashboards derive the displayed counts from those API responses, with copy clarifying that there is no dedicated analytics endpoint.
- Added the approved Parent Library addendum and wired `UI_Project/parent-ui/src/App.tsx` to read public/shared lesson summaries and invitations when an auth token bridge exists, fetch selected lesson detail on open, and call the typed idempotent accept/decline method only after a button press. The invitation contract omits teacher/school display names, so the UI uses neutral copy rather than inventing identities.
- The default local/no-auth workspace stays an explicitly labeled fixture preview. Authenticated mode with missing organization context, request failure, or timeout shows loading/unavailable/error state; it does not replace API data with fixtures or interpret failure as an empty collection. Admin remains preview-only because a queue-list API is absent. Parent profile/story APIs remain unavailable on the delivery branch and preview-only.
- No API call or write was issued against a backend during implementation/review. The branch API routes were inspected locally, not runtime-smoke-tested. `/api/auth/v1/me` and the expected `window.sketch2lifeAuth` implementation are absent in this checkout; external auth/runtime configuration has not been verified.
- Allowed newer API comparison: `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e86826447d975ef2757aa1fefdc876c8c`, read-only. No source from screenshot-excluded branches, top-level `apps/`, or Child Expo was used. Exact mapping is in `API_UI_CROSSWALK_REV3.md`.
- Final `npm run build` from `UI_Project` passed all five workspaces after Parent and web API UI changes. `pnpm --dir apps/mobile typecheck` passed; `pnpm --dir apps/mobile android:apk:debug` passed and embedded `parent-ui` into `dist/parent-ui-webview.html` (438,792 bytes). APK path: `UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`.
- CUA review of Parent `/` and both Library tabs confirmed the no-auth preview badge/disclosure, public/shared categories, invitation card and mobile shell. Teacher and Manager preview screens show source labels in this no-auth checkout. Connected API mode was not runtime-tested because no auth bridge/config is present.
- The emulator returned `sys.boot_completed=1`, but installing the new APK did not respond within about 40 seconds. A read-only `pm path com.sketch2life.mobile` check also hung and was interrupted. No wipe/reset was performed. This APK is build-verified but still not runtime-verified on this emulator.
- `git diff --check` and `python tools/validate_repository_security.py` passed; the security validator scanned 7,577 publishable files and found no absolute machine paths. The implementation was committed as `be8aa646` and pushed normally as a fast-forward from `ae2a8c81` to `origin/FE_UI_Project_Ver2`. No automated tests were run.

## Rev4 UI-only closeout

Plan: `plan/PLAN_REV4_UI_ONLY.md`, SHA-256 `EE85CB380638985969419A38646B1D72383C74CC390027C903D1950C387FF4C3`. The owner clarified that APIs are business-flow references only and asked for the leader-requested UI/UX without API integration. Rev4 removes the Rev3 API client/auth bridge conditions from the role interfaces.

### Current UI behavior

- Parent Settings is accessible only from the Family Profile page; the home header and story flow no longer show the Settings gear.
- Parent activity selection happens after the story/video preview, in accordance with the leader disposition and canonical FEAT-063 SRS. Parent preview video remains explicitly unavailable.
- The unsupported gender field is removed from Parent profile UI.
- Teacher, School Manager, and Platform Admin remain role-specific web previews with demonstration data. Current role UIs make no backend API/auth requests; AI, playback, persistence and operational metrics are not represented as live capabilities.

### Rev4 verification

| Command / review | Result |
|---|---|
| `npm run build` from `UI_Project` | Passed for all five workspaces: Parent, Teacher, School Manager, Platform Admin and shared web portal. |
| `pnpm --dir apps/mobile typecheck` from `UI_Project/parent-android` | Passed. |
| `pnpm --dir apps/mobile android:apk:debug` with `ANDROID_HOME` and `ANDROID_SDK_ROOT` set to the installed local Android SDK | Passed; Gradle reported `BUILD SUCCESSFUL in 1m 26s`. The package includes `parent-ui-webview.html` (424,924 bytes). APK: `UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`. |
| Manual visual review in CUA | Parent home showed no Settings button; Family Profile showed the Settings button and opened the existing Settings sheet. History → completed story → “Xem hoạt động cùng bé” reached the post-story activity page, and selecting an activity updated its selected state. Teacher, School Manager and Platform Admin previews were also visually reviewed. |
| API/auth behavior | Source search found no `backendApi`, auth bridge, or `fetch(` in the current Parent/shared role UI files. No API/auth calls were made. |

No automated tests were added or run. The Rev4 APK packaging passed, but installation/runtime on the supplied emulator was not retried in this closeout; earlier install/package-manager attempts stalled. No emulator wipe/reset was performed. The CUA session visually inspected the screens; no new screenshots were saved, so the existing PNGs remain historical captures.

Repository security validation passed before commit (7,578 publishable files scanned) and immediately before push (7,577 publishable files scanned); both runs reported no absolute machine paths. `git diff --cached --check` passed. Commit `11294211911506a7dae73a5ab78aee0bb51311f0` was pushed normally as a fast-forward from `26de23d54f16917c3c98230df36a5da6dd039238` to `origin/FE_UI_Project_Ver2`.

## Rev5 preview completion

Plan: `../plan/PLAN_REV5_PREVIEW_COMPLETION.md`, SHA-256 `F49F00D71E5E0D84B2EA695A1BB63010DA2E82E8A8FAC356542BDA145279262A`. Scope is preview-only. The source/API contracts informed screen states and Teacher dashboard vocabulary; no API, authentication, analytics, ASR, persistence, or AI request was wired or issued.

### Verification

| Command / review | Result |
|---|---|
| `npm run build` from `UI_Project` | Passed all five workspaces (Parent, Teacher, School Manager, Platform Admin, shared web portal), including the final Parent sample artwork and transcript affordance changes. |
| `pnpm typecheck` from `UI_Project/parent-android` | Passed (`tsc --noEmit`). |
| `pnpm --filter @sketch2life/mobile android:apk:debug` with `ANDROID_HOME` and `ANDROID_SDK_ROOT` set to the existing local SDK | Passed; Gradle reported `BUILD SUCCESSFUL in 1m 4s`. It generated the self-contained `parent-ui-webview.html` bundle (433,611 bytes). APK: `UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk` (131,832,792 bytes). |
| `git diff --check` | Passed; Git noted CRLF-to-LF normalization for `UI_Project/README.md`. |
| Manual CUA visual review | Reviewed Parent child picker, profile gender edit, guide topic/difficulty/three steps, local sample artwork, sample transcript insertion, mismatch decision modal and subsequent script direction; reviewed Teacher dashboard fixture totals, lessons, assignment and preview disclosure. Live screenshots were inspected but not saved as new evidence images; files under `screenshots/` remain historical Rev1 captures. |

No automated tests were run. Gender is a session-only fixture because the canonical FEAT-063 SRS and current reviewed contracts do not define it. Transcript and drawing analysis are illustrative local states and do not prove ASR or AI functionality.

### Browser preview and Android runtime

The preferred workspace URLs returned HTTP 200 with the expected page titles: Parent `5171`, Teacher `5172`, School Manager `5173`, Platform Admin `5174`, and shared portal `5175`. Parent's served module included the new sample-transcript action. An additional `npm run dev` launcher found those ports already occupied and selected fallback ports; those extra instances were stopped while the already-running previews were left intact. The tested handoff URLs are recorded in `STATUS.md`.

The supplied Android emulator reached `sys.boot_completed=1`. `adb install -r` of the newly built APK produced no response for an extended period and was interrupted. The app was not launched; emulator runtime is unverified. No device data was wiped/reset. The APK is build-verified and available at the path above.

No real child media/profile data was used. No mic permission, API request, backend write, or provider request was made.
