# FEAT-009 Android and private-AI foundation context

- Status: DONE
- Owner: four-person Sketch2Life team
- Goal: freeze the Android-only native baseline and the secure backend-to-Lightning-AI boundary.
- Scope: Android native skeleton, application ID/SDK levels, progress-transport default, security/config skeleton, architecture/setup documentation, and validation evidence.
- Non-goals: product screens, visual assets, authentication-provider implementation, model calls, cloud provisioning, and production deployment.
- Dependencies: FEAT-008 foundation skeleton, React Native 0.87, Python backend skeleton, and the project governance harness.
- Risks: choosing an unsupported SDK baseline, leaking model credentials to mobile, mistaking target SDK for minimum device support, or creating provider coupling in application/domain code.

## Context snapshot

The project owner confirmed `com.sketch2life.mobile`, Android-only delivery, bare React Native CLI, one app with role-based child/parent/guide modes, and private secure Lightning AI access. The owner asked for a 2026 web check before choosing Android support and has not selected a progress protocol.

The public Android distribution page no longer exposes version percentages; it directs developers to Android Studio's Create New Project wizard and Play Console Reach and devices. The baseline therefore does not claim an unverifiable market percentage. It uses Android 10/API 29 as an explicit product compatibility floor, Android 16/API 36 as the 2026 Google Play target, and compile SDK 37 because React Native 0.87 requires it.

Reference inputs remain `handbook-v7` and `sprint-task-breakdown` from `docs/context/SOURCE_REGISTER.md`; neither source overrides the owner's decisions.
