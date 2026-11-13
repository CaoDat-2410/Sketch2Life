# Package the Parent UI in the Android app

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_STARTED

## Goal

Launch the Parent UI currently served at `http://127.0.0.1:5171/` as the visible experience inside the existing Android app on the supplied emulator.

## Scope

- Build the existing `UI_Project/parent-ui` Vite workspace into static files with a relative asset base.
- Add a reproducible Android Gradle build step that packages those built files as app-local assets; do not depend on `127.0.0.1:5171` at runtime.
- Replace the native Parent navigator entry surface with a small React Native WebView host that loads the bundled Parent home. Keep the existing React Native package/application ID and existing Child Expo source untouched.
- Configure the WebView and status-bar presentation so the supplied Android-sized UI is legible and does not display duplicate status bars. Preserve prototype navigation and scrolling inside the WebView.
- Handle Android back navigation within the web experience where possible; avoid a blank/error screen when the web history is empty.
- Build/install the debug app, launch it on `emulator-5554`, and capture app home plus key navigation evidence.
- Record any Android WebView limitations for camera, microphone, and external-font loading. Do not claim backend/auth/device capture is complete.

## Explicit boundaries

- The deliverable is a hybrid Android app preview: the outer app is React Native and the Parent prototype is rendered from bundled local WebView assets. It is not a screen-by-screen native React Native port.
- Do not change prototype business logic, product requirements, auth, API/backend, fixture records, design language, or route semantics except for necessary local asset-path compatibility.
- Do not add generated bitmap artwork. Existing source HTML/CSS artwork is the approved reference; `FRONTEND_ASSET_GATE.md` does not require a new generated/approved raster-asset cycle for this code-only packaging change.
- Do not commit or push.

## Steps

1. Integrate a deterministic Vite build and copy its output into the Android app asset bundle during the Gradle build.
2. Add a React Native WebView entry screen that opens the bundled `index.html`, hides the native status bar when needed, and provides Android back handling.
3. Build the Android debug APK and install it on `emulator-5554`.
4. Confirm the app opens the Parent home from the local bundle, then navigate Home → History/Lessons/Profile and one story-flow entry point. Check for RedBox, missing resources, overflow, or duplicate status UI.
5. Capture screenshots/log evidence in this feature folder; update context, decisions, and status.

## Acceptance criteria

- AC1: Android Gradle packages the Vite output inside the APK; the Parent UI loads when the `5171` Vite server is stopped.
- AC2: The installed app launches directly into the supplied Parent home design (brand/header, story hero/world selector, primary story card, create-story section, and bottom navigation) rather than the prior generic native Parent home or Child Expo UI.
- AC3: Parent prototype navigation for Home, History, Lessons, Profile, and one story-flow entry point renders and remains scrollable without React Native RedBox or WebView asset errors.
- AC4: Android system status UI does not duplicate the prototype's status row; Android back leaves the app in a stable state.
- AC5: Debug build, installation, runtime screenshots, and known limitations are recorded under FEAT-067 evidence.
- AC6: No product requirement, backend, auth, real child data, signing secret, commit, or push changes are introduced.

## Risks and mitigations

- A local HTML file can resolve Vite assets incorrectly unless Vite uses a relative build base; verify the actual APK, not only browser dev mode.
- WebView and Metro still require Android debug runtime support; bundle Vite assets locally so the separate port 5171 server is not a runtime dependency.
- Camera/microphone browser APIs may require Android WebView permission mediation; verify the visible fallback and report these capabilities as out of scope.
- Some fonts are imported from Google Fonts and may use the CSS system fallback when offline; note the observed result on the emulator.

## Verification plan

- Run the existing Parent UI production build as part of Android packaging.
- Run `assembleDebug`, install with ADB, cold-launch and manually inspect the Parent home and selected prototype screens on the supplied emulator.
- Stop only the Vite dev server for AC1 while keeping Metro available for the RN debug app; confirm the bundled site remains available.
- Capture `adb` screenshots and inspect filtered Android logs for WebView load errors and React Native RedBox/fatal exceptions.
- Run `git diff --check`. No automated test suite is added or run unless separately requested.

## Evidence plan

- `evidence/README.md`: AC-to-evidence map.
- `evidence/screenshots/parent-app-home.png`: app home on the emulator.
- `evidence/screenshots/parent-app-navigation.png`: key prototype navigation screen.
- `evidence/notes/EXECUTION.md`: build/install commands, server-stop check, device and runtime results, limitations.

Implementation is permitted only while the matching `approvals/TASK_APPROVAL.md` record is `APPROVED`.
