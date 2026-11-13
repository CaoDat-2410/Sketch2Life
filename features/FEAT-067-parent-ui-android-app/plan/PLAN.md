# Package and publish the Parent UI Android app

- Status: APPROVED
- Plan revision: 2
- Implementation status: IN_PROGRESS

## Goal

Make the Parent UI currently served at `http://127.0.0.1:5171/` launch and work inside the Android app on the supplied emulator, then publish the reviewed code to `FE_UI_Project_Ver2` so teammates can build it from a clone.

## Scope

- Build the existing `UI_Project/parent-ui` Vite workspace into one self-contained HTML document with all local CSS and JavaScript inlined. Keep browser development mode working at port 5171.
- Add a reproducible Android Gradle build step that copies this single HTML file into APK-local assets. The APK must not depend on the Vite server or its port at runtime.
- Keep the existing React Native app ID and use its WebView host. Open the Parent home directly, hide duplicate native status UI, and keep prototype navigation/scrolling usable.
- Resolve the Android `file://` CORS limitation found during Rev1 by loading only the generated single-file document; verify the WebView renders actual content on device.
- Add teammate run instructions covering dependency install, Metro, Android build/install, and the fact that Vite `5171` is only the browser prototype server.
- Preserve the three other role web workspaces (`teacher-ui`, `school-manager-ui`, `platform-admin-ui`) and `web-ui`; do not change their runtime/source behavior. Build their existing web workspaces and verify their dev URLs remain available.
- Include the already completed FEAT-066 Parent tab-role correction and its feature-local evidence in the publication. Record that the newest owner instruction supersedes FEAT-066's original no-push boundary for this branch publication.
- Build/install the app, test the Parent home and key navigation on `emulator-5554`, run repository security validation, then commit and push the scoped changes normally to `origin/FE_UI_Project_Ver2`.

## Explicit boundaries

- The deliverable is a hybrid Android app: a React Native shell renders the existing Parent prototype from one HTML file bundled locally in the APK. It is not a screen-by-screen native React Native rewrite.
- Do not alter Parent prototype flows/fixtures, product requirements, backend/API/auth behavior, real child data handling, or the three other role web apps.
- Do not add generated bitmap artwork. The requester supplied the existing Parent web page as the visual reference; no new raster assets are needed.
- Do not publish or sign a release APK; only push source and documentation to the requested branch. Never force-push.

## Steps

1. Preserve Plan Rev1 and record the owner-approved Rev2 SHA/scope in feature and root approvals.
2. Add a deterministic single-file Vite build script and wire it into the Android Gradle asset task.
3. Fix WebView local-file loading, then rebuild/install and verify app launch, navigation, back behavior, and no CORS/RedBox errors on the supplied emulator.
4. Build the other web workspaces and check their existing dev endpoints without changing their code.
5. Capture app screenshots, logs, build outputs, and limitations under this feature's evidence directory.
6. Run `git diff --check` and `python tools/validate_repository_security.py`; stage only approved files, commit, fetch/verify the target branch, and push normally to `origin/FE_UI_Project_Ver2`.

## Acceptance criteria

- AC1: The APK contains the self-contained Parent document; the app renders it after the Vite server on `5171` is unavailable.
- AC2: The emulator shows the supplied Parent home design in the installed app, with its story hero, category switcher, story card, create-story section, and bottom navigation.
- AC3: Home, History, Lessons, Profile, and at least one story-flow entry point render and navigate without a RedBox, blank WebView, or local-file CORS error.
- AC4: The browser Parent workspace continues to build/serve on its existing URL, and Teacher, School Manager, and Platform Admin workspaces build and their existing web URLs remain reachable.
- AC5: Teammate run steps are written in the mobile workspace README; debug build requirements and prototype-only limitations are clear.
- AC6: `python tools/validate_repository_security.py` passes before publication; only approved feature files are committed and pushed to `origin/FE_UI_Project_Ver2` without rewriting history.
- AC7: No product requirement, backend/API/auth, real child data, release signing, or other role UI changes are introduced.

## Risks and mitigations

- `file://` blocks separate Vite module/CSS files in Android WebView; inline the build output and verify the packaged APK on device.
- RN debug app startup needs Metro, while the Parent UI assets are local. Document both distinctly; build/install commands should set up Metro on standard port 8081 for a teammate clone.
- Camera/microphone/browser file APIs may need native WebView permission mediation; report these as prototype limitations unless they are needed to verify this request.
- External Google Fonts may fall back when the emulator has no internet; record the observed rendering.
- Push may be blocked by remote branch updates or security validation. Fetch and reconcile normally; do not force-push or silently drop other changes.

## Verification plan

- Build `parent-ui` plus the `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, and `web-ui` npm workspaces.
- Run TypeScript typecheck for the Android React Native host.
- Run `assembleDebug`, install with ADB, cold-launch and manually inspect the Parent home and selected prototype screens on the supplied emulator.
- Confirm the local HTML file works without port 5171, inspect logs for file/CORS and RedBox errors, and check the web workspace endpoints.
- Run `git diff --check` and `python tools/validate_repository_security.py` before commit/push. No automated test suite is added or run.

## Evidence plan

- `evidence/README.md`: acceptance-to-evidence map.
- `evidence/screenshots/parent-app-home.png`: Parent home on the emulator.
- `evidence/screenshots/parent-app-navigation.png`: key app navigation screen.
- `evidence/notes/EXECUTION.md`: build/install commands, Vite-independence check, role web build/URL checks, device/runtime results, limitations.
- `evidence/notes/PUBLICATION.md`: security validation, exact staged paths, commit and push result.

Implementation is permitted only while the matching `approvals/TASK_APPROVAL.md` record is `APPROVED`.
