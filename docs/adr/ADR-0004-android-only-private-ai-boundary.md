# ADR-0004: Android-only client and private AI boundary

- Status: ACCEPTED FOR ANDROID; AI PROVIDER DETAILS SUPERSEDED BY ADR-0005
- Date: 2026-08-24
- Owners: Sketch2Life project owner and four-person team
- Supersedes: the iOS/native-platform uncertainty in ADR-0003
- Refined by: ADR-0005; its backend-only AI boundary remains, but Lightning is now fixture/dev and Runpod is the production provider.

## Context

The owner selected Android-only delivery, `com.sketch2life.mobile`, bare React Native, one application with child/parent/guide role modes, real-model testing on Lightning AI, and private secure AI access. Progress transport was left open.

Google's public distribution dashboard no longer publishes platform-version percentages; it directs developers to Android Studio and Play Console for that data. Google Play requires new apps and updates to target Android 16/API 36 from 2026-08-31. React Native 0.87 requires Node 22.13+, AGP 9, Kotlin 2+, and compile SDK/build tools 37.

## Decision

- Ship one Android application; iOS is out of scope.
- Use namespace/application ID `com.sketch2life.mobile`.
- Use `minSdk 29` (Android 10), `targetSdk 36` (Android 16), and `compileSdk 37`.
- Treat minSdk 29 as a project compatibility tradeoff, not a claim about public market share. Re-check actual Play Console reach before release.
- Use bounded HTTP polling for MVP job progress. Start at 2 seconds, back off to at most 10 seconds, use an ETag or job version, stop at terminal state, and stop/pause when the app is backgrounded. SSE/WebSocket needs measured evidence and an ADR revision.
- Mobile communicates only with the Sketch2Life backend over HTTPS. It never calls Lightning AI and never stores AI credentials.
- Backend infrastructure reaches AI providers through an authenticated adapter; application/domain code depends only on `AiGateway`. Current provider details are defined by ADR-0005.
- Release signing material is injected by CI from an approved secret store; release builds must never use the checked-in debug key.

## Consequences

- The team maintains one native target and one role-aware client composition root.
- Android 9/API 28 and older cannot install the application.
- Polling is simpler to operate but must be bounded to avoid battery/backend load.
- AI provider details remain isolated to an infrastructure adapter and deployment configuration.
- Authentication and the current Lightning-dev/Runpod-production split are defined by ADR-0005.

## Evidence

- [Android distribution dashboard](https://developer.android.com/about/dashboards)
- [Google Play target API requirements](https://support.google.com/googleplay/android-developer/answer/11926878)
- [React Native 0.87 release](https://reactnative.dev/blog/2026/08/11/react-native-0.87)
- [Android API-level mapping](https://developer.android.com/guide/topics/manifest/uses-sdk-element.html)
- [Lightning deployment options](https://lightning.ai/docs/security/privacy/deployment-options)
- [Lightning managed secrets](https://lightning.ai/docs/overview/ai-studio/managed-secrets)
- Feature-local record: `features/FEAT-009-android-private-ai-foundation/`
