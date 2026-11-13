# Parent Android app workspace

The current Parent Android target is `apps/mobile`, an Android-only React Native app. Its app entry opens the Parent prototype from the sibling `UI_Project/parent-ui` workspace in a locally bundled WebView, so the emulator shows the same Parent UI as the browser preview.

`apps/ui-mobile` is a separate legacy Expo experience. It is not the Parent Android app target; both source workspaces remain side by side.

## Install

Use Node.js 22.13+ and pnpm 11.19+. The Parent Vite app is a separate npm workspace, so install both workspaces once after cloning:

```powershell
cd UI_Project
npm ci
cd parent-android
pnpm install
```

## Run Parent on an Android emulator

From this folder, start the React Native host bundle in one terminal:

```powershell
pnpm start
```

In a second terminal with an Android SDK and emulator configured:

```powershell
pnpm android
```

The debug app uses Metro on port 8081 for its React Native host. The Parent UI itself is packaged locally in the Android app and does not need the Vite preview on port 5171.

On Windows, if Android CMake reports paths longer than 260 characters, clone the repository into a shorter folder and build again.

To build the debug APK without launching it:

```powershell
pnpm --dir apps/mobile android:apk:debug
```

## Other workspaces

Teacher, School Manager, Platform Admin, and the unified web portal stay under `UI_Project` as web workspaces. Start them from `UI_Project` with `npm run dev:teacher`, `npm run dev:manager`, `npm run dev:admin`, or `npm run dev:web`.
