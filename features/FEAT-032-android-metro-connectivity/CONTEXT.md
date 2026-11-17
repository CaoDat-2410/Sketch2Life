# FEAT-032 Android Metro connectivity context

- Status: REVIEW; IMPLEMENTED_LOCALLY; DEVICE_RETEST_PASS
- Owner: Project owner / Codex
- Goal: make the Android development client reliably reach the Expo Metro server during local development.
- Scope: the `apps/ui-mobile` dev-client entrypoint, host-reachable Metro mode, optional ADB reverse setup, and operator troubleshooting evidence.
- Non-goals: release networking, backend authentication, production endpoints, provider credentials, Android signing, or product UI changes.
- Dependencies: Expo SDK 52 app in `apps/ui-mobile`, the local Android SDK/ADB when available, and the local-development rules in `docs/setup/LOCAL_DEVELOPMENT.md`.
- Risks: LAN mode depends on the host firewall and trusted local network; emulator loopback mode depends on an available ADB executable and a connected device.

## Context snapshot

The attached Android screen reports that the development server cannot be reached and shows a
bundle URL at `http://127.0.0.1:8081`. A host probe confirms that Metro can serve the bundle on
port 8081, while the repository's Expo device registry is empty and `adb` is not currently on
PATH. `127.0.0.1` therefore identifies the Android runtime itself unless an ADB reverse mapping
exists; it is not a reliable physical-device address.

The fix preserves the existing Expo/native app and backend boundaries. It only improves the local
development launch path and documents the two supported connection modes:

- LAN mode for a physical device or an emulator that can reach the host IP.
- ADB reverse mode for a local emulator/device when Android SDK platform-tools are installed.

The follow-up native error is the expected failure mode for opening a debug APK directly while
Metro is stopped. `MainApplication` enables developer support only for `BuildConfig.DEBUG`, and
the Gradle React Native configuration leaves debug JavaScript loading to Metro.

Relevant authority: `PROJECT_CONTEXT`, `SOURCE_REGISTER`, `FEAT-018` Android integration guidance,
and the direct owner request in the current task.
