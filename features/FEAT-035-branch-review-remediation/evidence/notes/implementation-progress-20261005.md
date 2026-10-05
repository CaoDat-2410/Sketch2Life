# FEAT-035 implementation progress — 2026-10-05

- Evidence ID: FEAT-035-EV-003
- Related: H-04, H-05, M-08, M-10, L-11
- Type: local Android/Metro/backend smoke, synthetic UI navigation, build and packaging verification
- Branch/baseline: `codex/pixi-ai-show-20261001`, HEAD `7a65890`; changes remain uncommitted.
- Provider/model calls: none. No real child media or credentials were used.

## Approval reconciliation

The owner explicitly approved continuation with “approve”. The plan was not edited. `TASK_APPROVAL.md`
now records the current plan SHA-256 `DCA28C79763AF55C6CC083CD500F19655EEB760D4206928E8334DEE5DEE94A1E`.

## Android/Metro work

1. Metro was isolated to `apps/ui-mobile` and the shared renderer. The resolver now prioritizes the
   app's React Native 0.76.9 and enumerates pnpm package node-module roots, avoiding the sibling
   `apps/mobile` React Native 0.87.0 collision. Android bundle request returned HTTP 200 and a
   bundle of 8.4 MB; Metro logged a successful 1,018-module bundle.
2. Nine assets whose bytes were JPEG but whose names ended in `.png` were renamed to `.jpg`, and
   all mobile references were updated. This fixed the AAPT resource-compile failure without
   deleting or changing asset bytes.
3. Debug native build passed with `x86_64` and temporary command-line SDK overrides
   `compileSdkVersion=35`, `targetSdkVersion=35`, `buildToolsVersion=35.0.0`; the APK installed
   successfully on `emulator-5554` (API 37, `targetSdk=35`). The configured repository baseline
   remains compile 37/target 36; the override was needed because the local SDK has
   `platforms/android-37.0`, not the exact `platforms/android-37` package path.
4. The debug app initially used `10.0.2.2:8081`; the emulator's debug preference was set to
   `127.0.0.1:8081` and ADB reverse `tcp:8081` was active. The app then loaded the current bundle.

5. The release CMake loop was reproduced at the Ninja level: `expo-av` regenerated its graph on
   every pass because of the pnpm content-addressed package path. A tracked pnpm patch now sets
   `CMAKE_SUPPRESS_REGENERATION` for `expo-av@15.0.2`. Expo 52's Metro graph is also pinned to
   Metro 0.81 through `packageExtensions`, preventing the sibling React Native 0.87 app from
   supplying Metro 0.87 internals.

## Emulator and backend smoke

- Onboarding screenshot: `evidence/screenshots/emulator-debug-current-20261005.png`.
- Home after tapping “Bắt đầu hành trình nào!”: `evidence/screenshots/emulator-flow-next-20261005.png`.
- Child profile after tapping “Tạo câu chuyện mới”: `evidence/screenshots/emulator-create-20261005.png`.
- Android log contained `ReactNativeJS: Running "main"`; no `FATAL EXCEPTION`, `AndroidRuntime`,
  `Unable to load`, or JS `TypeError` was observed in the smoke window.
- Host backend `/health` and `/openapi.json` both returned HTTP 200. A TCP/HTTP probe from the
  emulator reached Uvicorn at `10.0.2.2:8000`; the shell probe's malformed line endings yielded
  Uvicorn HTTP 400, proving connectivity but not endpoint semantics.

## Verification

| Check | Result |
|---|---|
| `pnpm --dir apps/ui-mobile test` | pass, 22 tests and `UI_COPY_AND_RECOVERY_VALID` |
| `pnpm --dir apps/ui-mobile exec tsc --noEmit` | pass after web export completed |
| `pnpm --dir apps/ui-mobile build:web` | pass, 582 modules and 29 assets |
| Android debug `app:assembleDebug` | pass with temporary x86_64/SDK overrides |
| Android emulator install/navigation | pass; screenshots and log evidence above |
| Android `app:verifyReleaseSigning` | expected fail-closed; no owner-provided secret-managed keystore |
| Android `app:assembleRelease` | partial: JS/assets and corrected image resources passed; `expo-av` RelWithDebInfo CMake/Ninja failed with `build.ninja still dirty after 100 tries` |

| `pnpm install --frozen-lockfile` | pass after tracked `expo-av` patch and Expo/Metro 0.81 package-graph pin |
| `:expo-av:assembleRelease` | pass with temporary x86_64/SDK overrides |
| app release pre-signing tasks (`createBundleReleaseJsAndAssets`, resource/native merge, Java/Kotlin compilation) | pass; 896 modules, 29 assets |
| changed-scope Ruff | pass; all backend/tools checks clean |

## Final local gate rerun

- `pnpm -r test` passed: art-renderer 58, apps/mobile 7, and apps/ui-mobile 22 tests; the UI copy/recovery validator also passed.
- `python tools/validate_repository_security.py` passed with 1,935 publishable files scanned; `python tools/validate_skeleton.py` passed; `git diff --check` passed.
- No stale `.png` references remain for the nine corrected JPEG assets. Host backend `/health` and `/openapi.json` returned 200; Metro Android bundle returned 200 with an 8.4 MB response.
- `emulator-5554` remained online (API 37), with the debug APK installed at `versionCode=1`, `minSdk=29`, and `targetSdk=35`.

## Remaining gates

- No signed release APK was installed or claimed as passed: signing secrets are absent by policy.
  Release JavaScript/assets/resource/native compilation now passes; only the signing step remains
  owner/secret-manager controlled.
- SDK baseline needs a real Android SDK package named `platforms;android-37` (or an owner-approved
  environment/config decision); do not commit a local SDK workaround.
- Orientation, peak memory, EXIF behavior, permission-denial UX, Firebase verification, strict mypy,
  Docker resource-root, live Lightning integration, the exact local Android `platforms;android-37`
  package, and owner-managed release signing remain separate open gates.

No commit, push, deployment, provider call, secret provisioning, asset-rights promotion, or asset
deletion was performed.
