# FEAT-067 — Package the Parent UI as an Android app

- Status: IN_PROGRESS under approved Plan Rev2.
- Owner: Project owner/requester.
- Goal: Make the Parent UI currently shown at `http://127.0.0.1:5171/` launch inside the existing Android app on the provided emulator.
- Scope: Package a single-file build of the existing `UI_Project/parent-ui` Vite app as local APK assets and display it in the existing React Native Android host at `UI_Project/parent-android/apps/mobile` using its installed `react-native-webview` dependency. The app should open the Parent home directly and work without the Vite server. Build/publish the approved changes to `FE_UI_Project_Ver2` and preserve the other three role web workspaces.
- Non-goals: Rebuild the 25-screen prototype as native React Native components, delete either source workspace, change Parent product flows or backend/API/auth behavior, make new generated artwork, or publish/sign a release APK.
- User intent: The requester clarified that the Parent UI at the supplied local URL must be a mobile app visible on the emulator, then explicitly directed that the fix be pushed to `FE_UI_Project_Ver2` while the other three role UIs remain available on web. This directly authorizes Plan Rev2, including publication after security validation.
- Visual reference: The requester-supplied Parent UI at `http://127.0.0.1:5171/` and its attached home screenshot. No new raster visuals will be generated; existing HTML/CSS artwork and screen design remain the source.
- Architecture note: The Android deliverable remains an installable React Native app shell, with the existing web prototype rendered in a bundled local WebView so it matches the supplied UI. This is a hybrid app preview, not a native reimplementation of each DOM screen.
- Requirements boundary: `docs/context/SRS_AUTHORITY.md` routes current product requirements to FEAT-063 SRS v2.5-draft, which remains unsigned. This packaging task changes no product requirements. Keep the SRS target `apps/mobile` and its required Parent behavior in view; do not infer prototype fixture behavior is backend-connected or production-ready.
- Dependencies: Existing `react-native-webview` in `apps/mobile`, npm/Vite dependencies for `parent-ui`, Android SDK/JDK, emulator `emulator-5554`, and Metro for the debug RN host.
- Risks: Separate local CSS/JS files failed in Android WebView because a `file://` page has an opaque origin; Rev2 inlines them into one HTML file. Android back handling needs runtime verification. Prototype camera/microphone/browser file APIs may need native permission bridges and are outside this preview packaging task. External Google fonts may fall back when the emulator has no internet.

## Relevant source context

- `UI_Project/parent-ui` is an Android-sized React/Vite interaction prototype with the requested home design and mock Parent screens.
- `UI_Project/parent-android/apps/mobile` is the Android React Native 0.87 host and already declares `react-native-webview`.
- FEAT-063 SRS v2.5-draft §14 / FR-P-01 keeps Parent Android on `apps/mobile`; this task packages the approved prototype in that app shell without changing current product flows or claiming native/API completeness.
- The previous FEAT-066 fix only corrected invalid `accessibilityRole` values in the native Parent navigator. It did not package or sync the browser prototype.

## Sources consulted

- `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.5-draft (`FR-P-01`, Android platform target, NFR-30).
- `docs/governance/WORKFLOW.md` and `docs/governance/FRONTEND_ASSET_GATE.md`.
- `UI_Project/parent-ui/PARENT_SCOPE.md`, `UI_Project/parent-ui/src/App.tsx`, `UI_Project/parent-ui/src/main.tsx`, Vite/package manifests.
- `UI_Project/parent-android/README.md`, `apps/mobile/package.json`, `apps/mobile/src/app/AppRoot.tsx`, and Android Gradle/manifest configuration.
