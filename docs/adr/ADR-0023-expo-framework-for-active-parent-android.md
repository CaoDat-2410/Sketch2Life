# ADR-0023 — Expo framework for the active Parent Android app

- Date: 2026-11-10
- Status: ACCEPTED for the active apps/mobile client under FEAT-079.
- Authority: project owner request in the active conversation: “Chuyển toàn bộ qua expo cho tôi đi”.
- Scope: framework, developer tooling, Android app configuration, and local build workflow for apps/mobile only.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, unsigned. The SRS requires Parent Android behavior and preserves the Android identity/API levels; it does not require Expo.

## Context

The active apps/mobile client uses React Native 0.87 and the React Native CLI. The separate apps/ui-mobile client already uses Expo SDK 52 and React Native 0.76.9 as a legacy behavior reference. The owner selected Expo for the active app.

As of 2026-11-10, the official Expo SDK 58 reference pairs Expo 58 with React Native 0.88, React 19.3, Node 22.13+, compileSdk 37, and targetSdk 36. This is the current stable pairing closest to the active app’s React Native 0.87 baseline and preserves the project’s compile/target SDK constraints.

## Decision

1. Use Expo SDK 58 and its aligned React Native 0.88 / React 19.3 dependency set for the active apps/mobile app. Expo CLI and a project development client become the supported start/build workflow. React Native remains the underlying UI runtime.
2. Keep the app Android-only, with application ID com.sketch2life.mobile, minSdk 29, targetSdk 36, and compileSdk 37.
3. Adopt Expo incrementally in the existing Android project. Keep apps/mobile/android and integrate Expo module autolinking, Expo entry/bundling, and Expo CLI. Do not use clean prebuild or discard the native project in this task.
4. Keep apps/ui-mobile as the separate legacy Expo SDK 52 behavior reference. Do not merge, upgrade, or delete it.
5. Keep the Parent demo flow and local-only data boundary. No API/backend/auth/persistence/provider integration is authorized by this decision.
6. This scoped app/tooling choice supersedes the bare React Native CLI workflow answer for apps/mobile in ADR-0003/ADR-0004 and the 2026-08-24 mobile workflow answer in docs/setup/SYSTEM_QUESTIONS.md. It does not change the Android product requirements, the other clients, or the unsigned SRS.

## Consequences

- The active mobile package and workspace lockfile must be aligned to Expo SDK 58.
- Local Android development uses Expo CLI and a development build. Android Studio, JDK, Android SDK and an emulator are still needed for native local builds.
- Future Expo/RN upgrades must update the compatibility pins together and be recorded through the project feature/ADR process.
- Expo app config documents the Android settings for future prebuilds; the retained native Gradle files remain the immediate source for current local builds.
- Expo Go is not the required runtime for this app; use the project development client so native dependencies match the app.

## References

- expo-sdk58-compatibility: https://docs.expo.dev/versions/v58.0.0/
- expo-existing-rn-adoption: https://docs.expo.dev/bare/overview/
- expo-existing-rn-install: https://docs.expo.dev/bare/installing-expo-modules/
- expo-build-properties: https://docs.expo.dev/versions/v58.0.0/sdk/build-properties/
- FEAT-079 Plan Rev1 and its feature approval/evidence records.
- Canonical product source: FEAT-063 SRS v2.7-draft Rev57; no SRS amendment is made.
