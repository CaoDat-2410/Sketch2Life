# FEAT-079 implementation evidence — 2026-11-11

## Scope and baseline

- Worktree: `F:\Github\Sketch2Life-worktrees\fe-ui-full-remediation`.
- App: active Parent Android client `apps/mobile`; existing user edits in the app flow were preserved.
- Product boundary: local demo only; no backend/API, auth, persistence, payment, provider, media, or iOS behavior was added.
- Product source: followed the owner-provided root `AGENTS.md` authority, which names FEAT-063 SRS v2.7-draft Rev57 (unsigned; SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`). The target worktree's older `SRS_AUTHORITY.md` and SRS snapshot still identify v2.5-draft; this migration does not alter either requirements document. Reconcile that source-version mismatch in a separate authority update.

## Implementation

- Added Expo SDK 58 app configuration and Expo entry registration.
- Aligned active mobile runtime to React Native 0.88.1 and React 19.3; added Expo CLI-compatible Babel, Metro and Jest configuration, Expo Dev Client, and Build Properties.
- Updated workspace dependency resolution and lockfile; left `apps/ui-mobile` as its separate legacy Expo SDK 52 reference.
- Integrated Expo autolinking, Expo bundle entry/CLI, React Native host factory, activity delegate wrapper, and lifecycle dispatch into the retained `apps/mobile/android` project.
- Kept Android-only platform, app ID `com.sketch2life.mobile`, minSdk 29, targetSdk 36, compileSdk 37, and Kotlin 2.2.0.
- Updated active mobile developer documentation and recorded the scoped decision in ADR-0023.

## Checks and limits

1. `pnpm --filter @sketch2life/mobile exec expo config --type public` — passed. Output reports SDK 58.0.0, Android-only platform, app ID `com.sketch2life.mobile`, and min/compile/target SDK values 29/37/36 in the Expo Build Properties config.
2. `pnpm --filter @sketch2life/mobile exec expo install --check` — passed: “Dependencies are up to date”.
3. `pnpm install` — completed after allowing the existing no-op `@parcel/watcher` install hook and `esbuild` workspace build; the root lockfile reflects the Expo SDK 58 dependency graph. Existing peer/deprecation warnings were emitted.
4. `pnpm peers check` — workspace-wide diagnostic still reports React 19 against React 18 peer variants from `react-dom@18.3.1` and `react-native-web@0.19.13`. `pnpm why` shows those older variants in the mixed SDK 52/58 workspace and the legacy `apps/ui-mobile` package. The active `apps/mobile` direct peers are now Expo 58's `react-dom@19.3.0` and `react-native-web@0.21.4`; the workspace diagnostic remains unresolved, and the legacy package was left unchanged per scope.
5. Android emulator build attempt (2026-11-11): the Pixel 6a / API 33 emulator booted (`emulator-5554`, `sys.boot_completed=1`). `pnpm android` reached Gradle but failed at `:app:buildCMakeDebug[x86_64]`; Ninja rejected the generated `react-native-webview` `ComponentDescriptors.cpp` source path as longer than 260 characters. A follow-up with regenerated autolinking got past that file but failed in `expo-modules-core` CMake after object-directory path warnings and `ninja: error: manifest 'build.ninja' still dirty after 100 tries`. No APK was produced or installed, and the app never launched; no UI-flow result is claimed. The owner then asked to stop emulator work. Temporary dependency junctions were restored and temporary package copies removed.

## Native project preservation incident

An initial `expo prebuild --platform android --no-install` unexpectedly cleared and regenerated `apps/mobile/android` even though `--clean` was not supplied. The Android directory was clean before that command. The generated changes and artifacts were immediately restored/removed against that known clean baseline. Expo integration was then applied manually to the retained native project. Final Android changes are limited to `settings.gradle`, `app/build.gradle`, `MainActivity.kt`, and `MainApplication.kt`; no regenerated Prebuild output remains. Do not run Expo Prebuild on this project until the native directory is backed up and reviewed.

## Final review

- Expo config and SDK-specific dependency check pass; the workspace-wide peer diagnostic remains as described above.
- Android API/app identity settings match the SRS working target.
- The Expo choice is a developer-tooling/framework choice from the owner; product requirements and the unsigned SRS were not changed.
- The exact worktree is the owner-designated `fe-ui-full-remediation`. The owner has authorized one local commit covering all current eligible worktree changes; no push, deployment, or other worktree is part of this authorization.
