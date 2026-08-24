# Sketch2Life mobile app

Active Android-only React Native + TypeScript client boundary for the mobile MVP. It contains presentation, navigation, device adapters, API clients, and the narrow PixiJS/GSAP bridge. It must not contain backend business truth or Lightning AI access.

Native baseline: `com.sketch2life.mobile`, minSdk 29, targetSdk 36, compileSdk 37. There is no iOS target.

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

- `src/app`: startup, navigation, dependency composition.
- `src/features/capture`: drawing/audio capture and consent UX.
- `src/features/gate-a`: understanding review/correction.
- `src/features/gate-b`: activity/objective review/approval.
- `src/features/experience`: playback and duration guard.
- `src/features/activity-bridge`: off-screen handoff.
- `src/features/feedback`: adult/guide outcome capture.
- `src/bridge/pixi`: WebView/bridge protocol for deterministic original-art rendering.
- `src/infrastructure`: HTTP, secure storage, device/media APIs.
- `src/shared`: presentation primitives and client-only utilities.

## State rules

- Use server-state caching for API data; do not mirror the whole session into an unrelated global store.
- Keep drafts local until an explicit command is sent.
- Treat session/job versions from the backend as authoritative.
- Never infer Gate A/B approval from navigation or local UI state.
- Keep bridge messages versioned and validate them before rendering.
- Call only the Sketch2Life backend; never embed a model-provider URL, token, certificate, or secret.
- Access Firebase Authentication only through `AuthSessionPort`; do not add Firebase storage/database products.
- Never access S3 directly; the backend owns upload authorization and artifact provenance.

Build artifacts:

- `pnpm --dir apps/mobile android:apk:debug` for local/device testing.
- `pnpm --dir apps/mobile android:apk:release` only after CI release signing is configured.
- `pnpm --dir apps/mobile android:aab:release` for Google Play.

Visual assets follow `generated -> review -> approved -> applied`. Runtime code may reference only approved/applied assets.
