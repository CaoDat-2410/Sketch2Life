# FEAT-066 execution evidence

- Evidence IDs: EV-066-00 through EV-066-03
- Date: 2026-11-13, Asia/Saigon
- Reviewer: Codex
- Repository branch/commit at start: `FE_UI_Project_Ver2` / `5c8b9e54` (matching `origin/FE_UI_Project_Ver2`)
- Device: Android Emulator Pixel_6, serial `emulator-5554`, Android 17 / API 37
- App: `com.sketch2life.mobile`, React Native 0.87.0

## Change

Changed the two Parent tab-group wrappers from `accessibilityRole="tabbar"` to `accessibilityRole="tablist"`:

- `UI_Project/parent-android/apps/mobile/src/shared/ui/ParentBottomNavigation.tsx`
- `UI_Project/parent-android/apps/mobile/src/features/lesson/ParentLessonLibraryScreen.tsx`

The individual controls retain `accessibilityRole="tab"`, selected states, labels, actions, and styling.

## Build and install

Command from `UI_Project/parent-android/apps/mobile/android`:

With local `JAVA_HOME` and Android SDK environment variables configured, run from `UI_Project/parent-android/apps/mobile/android`:

```powershell
.\gradlew.bat assembleDebug --console=plain
```

Result: `BUILD SUCCESSFUL in 2m 56s`; 93 Gradle tasks (83 executed, 10 up-to-date). Existing Gradle deprecation and CMake path-length warnings were non-fatal.

Installed with:

```powershell
adb -s emulator-5554 install -r UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

Result: `Success`. APK size: 131,341,313 bytes. SHA-256: `68DEC1E9121624E8E0949E246639ABCBD7C5D51AB7ECB4F3C14678CDAE3883AC`.

The Android debug APK loads the JavaScript bundle from the development Metro process. Metro was restarted on `127.0.0.1:8081` with `--max-workers 4`; `/status` returned HTTP 200 with `packager-status:running`. ADB reverse was present as `host-15 tcp:8081 tcp:8081`. After the restart, the app was cold-launched and Android logged `ReactNativeJS: Running "Sketch2LifeMobile"` at 16:08:05.

## Runtime actions and results

1. Started the installed app on `emulator-5554` and verified the Parent login screen (`screenshots/parent-login.png`).
2. Dismissed the non-blocking React Native debugger warning and tapped “Xem bản trải nghiệm”. Parent home rendered with “Chào ba mẹ!” and the four-item bottom navigation; no invalid-role RedBox appeared (`screenshots/parent-preview-home.png`).
3. Opened the lesson library, selected “Công khai”, and confirmed the selected tab and sample lesson list rendered without an invalid-role RedBox (`screenshots/parent-lesson-library.png`).
4. Returned the emulator to Parent home. The resumed Android activity was `com.sketch2life.mobile/.MainActivity`.
5. Stopped the Child Expo server and closed its browser tab. Port 5180 no longer listened. The Child Expo source was not deleted or modified.

The filtered post-fix `adb logcat` query for `Invalid accessibility role value`, `FATAL EXCEPTION`, and `Error while updating property` returned no matches during the final preview/library interactions. The pre-fix RedBox is preserved at `screenshots/parent-redbox-before.png`.

## Limitations

- The Parent preview banner identifies this as local/sample data; authentication and backend services are not connected or tested.
- The debug APK depends on Metro for cold starts and Fast Refresh. The app was cold-started successfully after restarting Metro; Metro is left running on loopback for the user's emulator session.
- No automated test suite, commit, or push was performed.
