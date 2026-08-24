# React Native frontend architecture guide

## Goal

Keep the mobile client focused on user interaction, device capabilities, playback, and review gates. Business truth remains on the backend.

The active target is Android only. Namespace/application ID is `com.sketch2life.mobile`; minSdk/targetSdk/compileSdk are 29/36/37. Child, parent, and guide experiences are role modes composed inside one application, not separate native apps.

## Directory contract

```text
apps/mobile/src/
├─ app/
│  ├─ navigation/                # role/mode routes and guarded transitions
│  ├─ providers/                 # query/cache, theme, auth/session context
│  └─ composition/               # dependency wiring
├─ features/
│  ├─ capture/
│  ├─ gate-a/
│  ├─ gate-b/
│  ├─ experience/
│  ├─ activity-bridge/
│  └─ feedback/
├─ bridge/pixi/
│  ├─ protocol/                  # versioned RN <-> WebView messages
│  ├─ adapter/                   # transport and lifecycle adapter
│  └─ validation/                # message/asset validation
├─ infrastructure/
│  ├─ api/                       # HTTP client and generated contract types
│  ├─ storage/                   # secure/local storage
│  ├─ media/                     # camera, microphone, file handling
│  └─ permissions/               # device permission adapters
├─ shared/
│  ├─ ui/                        # approved design primitives
│  ├─ hooks/                     # client-only hooks
│  └─ utils/                     # formatting and safe helpers
└─ assets/                       # feature-approved assets only
```

## Feature slice rules

Each feature owns its screen/container, view-model/hook, client-side validators, and tests. A feature must call an application/API port rather than importing another feature's private store.

Recommended split:

- Server state: TanStack Query or equivalent, keyed by session/job/version.
- Local UI state: a small store such as Zustand or component state.
- Navigation state: React Navigation; navigation is not business state.
- Forms/drafts: feature-local state with explicit submit commands.

The exact libraries remain a tooling decision; the dependency rules do not.

## Android and network rules

- Main/release manifests prohibit cleartext traffic; the debug manifest permits it only for local Metro development.
- Release builds are never signed with the checked-in debug key. CI injects production signing material from a secret store.
- The app calls only the Sketch2Life backend over HTTPS. It never calls Lightning AI or stores provider credentials/endpoints.
- Firebase Authentication is isolated behind `infrastructure/auth/AuthSessionPort`. Feature screens do not import Firebase directly.
- Firebase Storage, Firestore, Realtime Database, and direct S3 access are forbidden; all artifacts travel through backend workflows.
- Permissions are added feature-by-feature at the point of use and must have denial/fallback tests; the foundation requests only internet access.
- Async job status uses bounded polling as specified by ADR-0004. Server job/version state remains authoritative.

## PixiJS/GSAP bridge rules

- General screens do not import PixiJS directly.
- The bridge protocol is versioned and includes asset IDs, plan IDs, scene IDs, and provenance metadata.
- The WebView renderer accepts only validated `ArtAnimationPlan` messages.
- Renderer failures return typed fallback results; they do not silently replace original artwork.
- Playback emits start/end/error/metrics events back through the bridge.

## Testing map

- Components/view-models: deterministic interaction tests.
- API adapters: mocked contract/error tests.
- Bridge: protocol validation, fallback, lifecycle, and asset provenance tests.
- Device: capture/permission/media smoke tests on the agreed device matrix.
- E2E: fixture-only session flow across review, playback, off-screen handoff, and feedback.
- Android matrix: API 29 compatibility emulator/device plus API 36 behavior target; add a current API 37 test when the stable system image/toolchain is available.
