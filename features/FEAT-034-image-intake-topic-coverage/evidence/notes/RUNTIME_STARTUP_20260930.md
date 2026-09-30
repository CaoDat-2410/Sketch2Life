# Runtime startup verification — 2026-09-30

Owner request: start emulator, backend, and frontend.

- Emulator `Pixel_10_2` booted; `emulator-5554` is online and reports boot completion.
- Backend starts from the backend workspace with its existing local configuration. Configuration checks confirm the Lightning adapter, SAM 2.1 flag, provider endpoint, token-file presence, and image decoder are configured. No credential values were printed. Local `/health` returns HTTP 200.
- Metro starts from `apps/ui-mobile` on port 8081. The native entry `/.expo/.virtual-metro-entry.bundle?platform=android&dev=true&minify=false` returns HTTP 200.
- Native Android debug APK rebuilt successfully using Java 21 and the existing Android SDK; the build includes `expo-image-manipulator` 13.0.6. The Android Studio bundled Java 25 initially failed Gradle configuration, so the installed Java 21 was used for the successful build.
- APK installation with replacement succeeded and retained app storage. App activity starts, React Native logs `Running main`, and the observed screen displays normal onboarding. No ReactNativeJS error or AndroidRuntime fatal exception was observed during startup.
- ADB reverse is active for both 8081 and 8000. Mobile workflow API defaults to `http://10.0.2.2:8000`, the emulator's host gateway.
- Backend, Metro, emulator, and filtered Android app logs continue under an ignored task-specific `runtime-output` directory. These logs and the local startup screenshot are not publication evidence.

Correction to the earlier Metro diagnosis: the prior `/index.bundle` request was not the native application's configured entry. Its 404 alone did not establish an incorrect server working directory. The current native entry succeeds and the installed app receives its bundle.

This verifies build, installation, bundle delivery, and app startup. Native image selection, format normalization, and the full recommendation flow still require synthetic-fixture device verification.
