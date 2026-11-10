# FEAT-079 Context — Expo migration for the active mobile app

- Status: APPROVED; implementation complete, device build pending local Android tooling.
- Goal: use Expo for the active Parent Android app in apps/mobile.
- Scope: toolchain/framework migration only; preserve existing app flow and demo-only behavior.
- Non-goals: API/backend integration, authentication, persistence, real device/media/provider work, SRS or product-policy changes, UI redesign, release signing, commit, push, or deployment.
- Dependencies: pnpm workspace, apps/mobile native Android project, packages/art-renderer, current Parent demo implementation in FEAT-076.
- Risks: SDK compatibility, workspace Metro graph isolation, native Gradle integration, and unavailable local Android SDK/emulator.
- Canonical product source: FEAT-063 SRS v2.7-draft Rev57 (unsigned), SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. Use Android-only, com.sketch2life.mobile, minSdk 29, targetSdk 36, and compileSdk 37 as constraints; the SRS does not require Expo.
- Current source context: apps/mobile is the active Parent Android app; apps/ui-mobile is a separate Expo SDK 52 reference app. The SRS and older records describe the prior bare React Native CLI baseline and are not silently rewritten.
- User authorization: direct instruction in this conversation, 2026-11-10: “Chuyển toàn bộ qua expo cho tôi đi”.
- Product boundary: local demo data only. No API, backend, auth, persistence, payment, camera, gallery, microphone, upload, AI, or video service is connected.
- Current source evidence: apps/mobile package metadata uses React Native 0.87 and the React Native CLI. Expo SDK 58 official reference pairs with React Native 0.88, React 19.3, Node 22.13+, compile SDK 37, and target SDK 36.
- Official sources are registered in docs/context/SOURCE_REGISTER.md as expo-sdk58-compatibility and expo-existing-rn-adoption.

## Context snapshot

This migration changes the selected app framework and developer workflow, not the Parent product requirements. The implementation will keep the existing native Android directory and integrate Expo modules/CLI; it will not run a destructive clean prebuild. The current Parent feature boundary and FEAT-076 workflow port remain in place.

- Implementation outcome: SDK 58 configuration and dependency diagnostics pass; native Expo integration is applied in the retained Android project. No Android Studio/SDK/emulator is available in this environment, so no device build or launch is claimed. See feature-local evidence.
