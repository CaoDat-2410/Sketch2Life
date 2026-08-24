# FEAT-009 decisions

- Mobile delivery is Android-only; iOS is outside the active product scope.
- Android namespace/application ID is `com.sketch2life.mobile`.
- Android baseline is minSdk 29, targetSdk 36, compileSdk 37.
- Bare React Native 0.87 remains the mobile framework; child, parent, and guide are role modes in one application.
- MVP async progress uses bounded HTTP polling; SSE/WebSocket require measured need and a later ADR revision.
- Mobile calls only the Sketch2Life backend. Lightning AI is reachable only from backend infrastructure through a private authenticated gateway.
- Long-lived provider credentials are forbidden in mobile, source control, logs, and fixtures.
- Cross-feature rationale is promoted to `docs/adr/ADR-0004-android-only-private-ai-boundary.md`.
