# FEAT-067 runtime and build evidence

## Android Parent app

- `apps/mobile` TypeScript typecheck passed.
- Teammate command `pnpm --dir apps/mobile android:apk:debug` completed successfully on Windows with the Android SDK environment variables set.
- Installed `app-debug.apk` on emulator `emulator-5554` and launched `com.sketch2life.mobile`.
- The Parent home rendered with the same design as `http://127.0.0.1:5171/`; screenshot: `../screenshots/parent-app-home.png`.
- Navigated to History, Lessons, Profile, and the story creation entry flow; screenshots are saved in `../screenshots/`.
- APK inspection found `assets/parent-ui/index.html` (402,752 bytes), with no external script or stylesheet references. The packaged Parent page does not need Vite on port 5171.
- Cold-launch verification succeeded with Metro on port 8081; fresh logs showed React Native starting with no RedBox or WebView file/CORS error. The React Native debug host still needs Metro. Teammates can start it with `pnpm start` from `UI_Project/parent-android`, then run `pnpm android` in a second terminal.

## Web workspaces

`npm run build` completed successfully for all five `UI_Project` workspaces: Parent, Teacher, School Manager, Platform Admin, and the unified web portal. Existing local servers returned HTTP 200:

- `http://127.0.0.1:5171/` — Parent web preview
- `http://127.0.0.1:5172/` — Teacher
- `http://127.0.0.1:5173/` — School Manager
- `http://127.0.0.1:5174/` — Platform Admin
- `http://127.0.0.1:5175/` — unified web portal

The other role source workspaces were not changed.

## Scope limits

This is a Parent UI prototype hosted by a React Native Android shell. Its screens remain mock UI and are not evidence of production backend/auth integration. Native camera and microphone integration are outside this task.
