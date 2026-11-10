# Sketch2Life mobile app

Active Android-only Expo SDK 58 + React Native + TypeScript client boundary for the mobile MVP. It contains presentation, navigation, device adapters, API clients, and the narrow PixiJS/GSAP bridge. It must not contain backend business truth or Lightning AI access.

Native baseline: `com.sketch2life.mobile`, minSdk 29, targetSdk 36, compileSdk 37. There is no iOS target.

Expo SDK 58 uses React Native 0.88.1 and React 19.3 for this app. Use Expo CLI with the project development client. The existing `android/` project is retained and contains the active Gradle values; `expo-build-properties` mirrors those values for app configuration. The Parent demo remains local-only and does not call the API.

```powershell
pnpm install
pnpm --dir apps/mobile start
pnpm --dir apps/mobile android
```

The first Android command builds and installs the development client. Android Studio, JDK 17+, Android SDK Platform 37, Build Tools 37.0.0, and a running emulator or connected device are required. Once installed, `start` serves Metro to the development client. Do not run Expo Prebuild until the retained native project has been explicitly backed up and reviewed.

## Client layers

```text
screens/components/hooks
          |
feature view-models + client-side validation
          |
API/query ports + bridge ports
          |
HTTP/storage/media/device adapters
```

Server state and session truth come from the backend. Client state is limited to UI state, draft input, playback state, and device capability state.

## Planned modules

- `src/app`: startup, navigation and dependency composition.
- `src/features/parent-flow`: Parent Android screens, adult review gates and the typed `ParentWorkflowPort`.
- `src/features/fixture`: the existing isolated fixture lab; it is not the default Parent route.
- `src/infrastructure/auth`: provider-neutral authentication boundary for a later approved adapter.
- `src/infrastructure/api`: typed HTTP adapter after its versioned contract is approved.
- `src/infrastructure/demo`: centralized Parent demo records and the local `ParentDemoWorkflowAdapter`; its snapshot exposes demo content through the workflow port. Legacy fixture contracts remain isolated in `legacyFixtureFixtures.ts`.
- `src/bridge/pixi`: renderer protocol retained for the fixture lab; it does not represent Parent story/video playback.

## State rules

- Parent screens depend on `ParentWorkflowPort`, not on fixture records or backend DTOs.
- Demo data and transitions live under `src/infrastructure/demo`; the demo badge and copy must make synthetic behavior clear.
- Adult confirmation gates remain explicit for transcript, subject, context and final script.
- P06 opens a native preflight before final script approval and video admission. The local demo adapter records acceptance once, then P07 stays visible until the READY fixture action; playback is blocked before that state.
- Demo child profiles include a presentation-only gender choice for the matching child avatar. Gender stays out of run context and API contracts.
- A Parent run has one selected child profile. Activities are shown after the video-ready stage, not as a pre-video gate.
- Keep async stages and recoverable errors understandable; do not show invented percentages or provider diagnostics.
- The future API adapter owns server state, revisions, quota receipts and upload authorization.
- Call only the Sketch2Life backend; never embed model-provider URLs, credentials or secrets.
- Access Firebase Authentication only through `AuthSessionPort`; do not add Firebase Storage, Firestore or Realtime Database.
- Never access S3 directly; the backend owns upload authorization and artifact provenance.

Build artifacts:

- `pnpm --dir apps/mobile android:apk:debug` for local/device testing.
- `pnpm --dir apps/mobile android:apk:release` only after CI release signing is configured.
- `pnpm --dir apps/mobile android:aab:release` for Google Play.

Visual assets follow `generated -> review -> approved -> applied`. Runtime code may reference only approved/applied assets.

## Current Parent demo composition

`src/app/AppRoot.tsx` opens the Parent Android demo through `createDemoAppDependencies()`. The local `ParentDemoWorkflowAdapter` implements the feature-owned workflow port and loads all synthetic profiles, story, activity, quota and run values from `src/infrastructure/demo/parentDemoFixtures.ts`, exposed to screens through `ParentWorkflowSnapshot`. Screens do not import fixture records directly. The adapter can later be replaced in the composition root without changing the Parent screen flow.

The previous `FixtureFlowScreen` remains available under the separate Fixture lab route. Its contract data is centralized under `src/infrastructure/demo`; the flow remains a review harness and does not represent the SRS Parent story/video flow. Demo registration, recovery, camera/gallery selection, audio, guide, quota and playback do not make real auth, device, API or provider calls.

The Parent demo offers two synthetic child profiles, one-tap profile selection, gender-matched avatars and local quota replenishment controls. Every quota/payment action and video status is labeled demo-only; no payment or generation request leaves the application.
