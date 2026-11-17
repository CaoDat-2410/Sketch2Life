# FEAT-032 verification — 2026-09-28

## Environment

- Workspace: local repository checkout
- Host timezone: Asia/Saigon
- App: Expo SDK 52 / `sketch2life-mobile`
- Android package: `com.sketch2life.mobile`

## Diagnostic evidence

- `GET http://127.0.0.1:8081/status` returned HTTP 200 with Metro's running status.
- The virtual Android Metro bundle returned HTTP 200 and JavaScript content from the same host.
- `apps/ui-mobile/.expo/devices.json` contains an empty device list.
- `adb devices -l` could not be executed because `adb` is not on PATH and no standard SDK
  `platform-tools/adb.exe` path was found.
- Android source review confirms `MainApplication` enables developer support only for
  `BuildConfig.DEBUG`; `android/app/build.gradle` uses Expo `export:embed` for non-debug builds and
  leaves the default debug variant dependent on Metro.

## Interpretation

The supplied red screen is consistent with Android trying to reach the host Metro server through
its own loopback interface. The host-side server is healthy; the missing link is device transport.
The new launcher provides LAN mode for a physical device and explicit ADB reverse mode for an
emulator/device with platform-tools installed.

The follow-up black/red `Unable to load script` screen is consistent with opening a debug APK
directly while Metro is stopped. The new `android:dev` command makes the supported fresh-install
path explicit: Expo builds the debug variant, starts Metro, installs the app, and launches it.

## Verification status

Host probes: PASS.
LAN launcher smoke test on an isolated port: PASS; Expo announced a host LAN URL and both the
Metro status endpoint and Android virtual bundle returned HTTP 200.
Reverse launcher prerequisite test: PASS; it failed closed with a missing-ADB message.
`pnpm --dir apps/ui-mobile test`: PASS (`UI_COPY_AND_RECOVERY_VALID`).
`pnpm --dir apps/ui-mobile exec tsc --noEmit`: BLOCKED by pre-existing changes in
`apps/ui-mobile/src/screens/Flow2Screens.tsx` (`parentNotes`/`setParentNotes` missing from
`AppContextType` and `FeedbackObservationCode` string-type errors). This file was already dirty
before FEAT-032 and was not changed by this fix.
`python tools/validate_repository_security.py`: PASS after removing machine-local path text from
this evidence note.
`python tools/validate_harness.py`: still reports the pre-existing missing raw/metrics evidence
folders under FEAT-026; FEAT-032 now contains the required evidence layout.
`apps/ui-mobile/package.json` wiring: PASS; `android:dev` invokes the PowerShell launcher with
`-LaunchAndroid`, which selects LAN mode and runs the debug variant on port 8081.
LAN launcher rerun on isolated port 8082: PASS; it selected a private host address, Expo announced
`http://192.168.88.119:8082`, and the status endpoint and Android virtual bundle both returned
HTTP 200.
The `start:dev-client` package script now calls the same LAN launcher, so the standard documented
command also clears a stale `127.0.0.1` host override for the child Expo process.
Device reload: PASS on the running `Pixel_10` emulator. The default ADB server on port 5037 was
unhealthy, but Android Studio's ADB server on port 5038 exposed the emulator as
`127.0.0.1:5555`; after `adb -P 5038 -s 127.0.0.1:5555 reverse tcp:8081 tcp:8081`, force-stop and
relaunch, logcat reported `Running "main"` and the UI hierarchy contained the Sketch2Life onboarding
CTA. Screenshot: `evidence/screenshots/android-fixed-20260928.png`.
The earlier `android-relaunch-20260928.png` was captured before the React surface finished drawing
and is retained as intermediate evidence.
The launcher was subsequently hardened to probe ADB server ports 5037 and 5038, select the first
ready device, export `ADB_SERVER_SOCKET` for Expo child processes, and apply reverse to that device.
