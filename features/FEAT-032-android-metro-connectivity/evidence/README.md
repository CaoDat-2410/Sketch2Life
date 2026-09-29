# FEAT-032 evidence

## Evidence index

| ID | Type | Command/input | Result | Limitation |
|---|---|---|---|---|
| E-032-01 | source/diagnostic | Attached Android error plus host Metro probe | The host serves Metro, but the Android URL is loopback and no ADB device is registered | Device reload cannot be claimed without Android connectivity |
| E-032-02 | test | LAN launcher on an isolated port | Expo published a LAN URL; Metro status and Android bundle both returned HTTP 200 | No physical/emulator reload was available |
| E-032-03 | test | Reverse launcher without ADB | Failed closed with an actionable missing-ADB message | Platform-tools/device are environment prerequisites |
| E-032-04 | validation | UI test, TypeScript check, harness/security validators | UI test and security passed; TypeScript is currently blocked by unrelated dirty `Flow2Screens.tsx` errors; harness still reports pre-existing FEAT-026 missing evidence folders | Existing user changes were preserved |
| E-032-05 | source/diagnostic | Android `MainApplication.kt` and `app/build.gradle` review | Debug uses `BuildConfig.DEBUG`; debug loading depends on Metro while release uses Expo `export:embed` | Native device build was not rerun without ADB/JDK |
| E-032-06 | source/fix | LAN host override in the Android launcher | The launcher now passes a detected private LAN IP to Expo instead of reusing a stale localhost setting | Device install remains environment-limited |
| E-032-07 | source/fix | `start:dev-client` script wiring | The normal documented dev-client command now uses the LAN host override helper instead of plain Expo CLI | Existing installed app still needs a fresh dev-client launch/reload |
| E-032-08 | screenshot/device | ADB emulator relaunch after `reverse tcp:8081 tcp:8081` | `com.sketch2life.mobile` loaded the Sketch2Life onboarding screen; no development-server error remained | Emulator-specific evidence; physical devices still need LAN or their own reverse mapping |
| E-032-09 | source/fix | ADB server-port discovery | Launcher now detects the healthy ADB server on 5037/5038 and targets the ready device explicitly | Other custom ADB ports remain outside the helper's bounded discovery list |

Detailed command output is recorded in `notes/VERIFICATION_20260928.md`.

No screenshot is claimed because this workspace has no connected Android device; the screenshots
directory is retained for the required feature-local evidence layout.
