# EV-076-01 — Native Parent flow implementation and Android build

- Date: 2026-11-10.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- App: apps/mobile — React Native 0.87 + TypeScript, Android target.
- Requirement baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned working baseline.
- Data boundary: local in-memory fixtures only. No API, backend, real auth, device capture, upload, payment, provider, or media playback was invoked.

## Implementation delivered

- P06 story review now opens a native preflight sheet. The explicit **Tạo video ngay** action approves the final script and submits the demo admission as one state transition.
- Successful admission spends one demo quota unit at most once, closes the sheet, and shows P07. A zero-quota rejection leaves the run on P06. Accepted requests remain marked when navigating back, so they cannot be admitted a second time.
- P07 represents processing separately from READY. It shows no fabricated percentage; the demo user can simulate READY or a recoverable error. Retry continues the accepted demo request without an extra quota decrement. P08 playback remains guarded by READY, and activities remain after playback.
- The profile chooser has two synthetic children and single-tap selection. Profile creation includes gender and matching boy/girl avatars. Existing run child identity is used for context review and cannot be rewritten by changing the current profile selection; a second active run is blocked.
- Quota now has a child-friendly balance, local +3/+5/+10 demo top-up selection, payment-method preview, and run-use history. The action updates only synthetic state and explicitly says there is no transaction.
- Settings are grouped into “Tài khoản & cài đặt” and “Bảo mật”. Account details, child profiles, privacy/AI data and password copy are labeled as local demo behavior.
- Updated apps/mobile/README.md with the native flow and demo boundaries. Fixed the Windows Gradle runner so the standard package command invokes gradlew.bat through cmd.exe without shell interpolation of arbitrary task strings.

## Verification

| Check | Result |
|---|---|
| `pnpm --dir apps/mobile typecheck` | Passed (`tsc --noEmit`). |
| `node --check apps/mobile/scripts/run-gradle.mjs` | Passed. |
| `git diff --check` | Passed; Git emitted line-ending normalization warnings for already modified worktree files. No whitespace errors. |
| `pnpm --dir apps/mobile android:apk:debug` | Runner now launches Gradle. Gradle stops at Android project configuration because no Android SDK path is configured (`ANDROID_HOME`, `ANDROID_SDK_ROOT`, or `android/local.properties`). |
| Android UI/emulator run | Not performed; this environment has no configured Android SDK/ADB/emulator. |

No APK was produced. The expected local artifact path, if a valid SDK is configured and the same command succeeds, is `apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`.

## SRS flow mapped in the native UI

`Sign-in → Profiles → Home → Drawing/idea → Upload → Transcript review → Subject review → Context review → Story review (P06) → Preflight → Video status (P07) → READY → Playback → Post-video activity → History`.

The configured demo has a pinned lesson fixture. No fallback activity behavior was added; the no-preset activity policy remains OPEN under SRS §31.10(13). The flow was reviewed by source/transition inspection and TypeScript compilation, not by claiming a device-run manual acceptance pass.

## Limits

- The debug APK remains blocked until Android SDK is installed and `ANDROID_HOME` or the project-local `sdk.dir` is configured.
- This report does not establish API behavior, device permissions, payment, persistence, real video generation/playback, or production accessibility on Android hardware.
- No automated test suite, release build, signing, commit, push, deployment or publication was run.
