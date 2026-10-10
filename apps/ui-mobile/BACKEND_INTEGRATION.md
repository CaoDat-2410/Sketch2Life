# FEAT-018 Android demo: UI ↔ backend ↔ Lightning Vision

This guide covers the historical FEAT-018 Android demo and the additive experimental
FEAT-030 story-video playback lane. Authentication and persistent child profiles remain
future seams; generated story media has the separate approvals and limits described below. Sessions,
uploaded drawings, and renderer grants are process-local and expire; restarting the backend loses
them. Use synthetic, non-child drawings only.

## What is connected

The app calls the versioned `/v1` API for ephemeral session creation, synthetic image upload,
explicit Vision analysis, Gate A review/correction, age-and-anchor-filtered P1 options, P1
selection, experience preparation, Gate B approval, caregiver handoff, feedback, and gallery.
After Gate B, an explicit Pixi launch opens the original drawing in a same-origin WebView. Pixi
receives a short-lived source capability, not image bytes in the native bridge; it reveals the
whole original drawing and does not load the unreviewed asset atlas, generate images, or play video.

Only tapping **“Gửi phân tích ảnh tới Lightning”** invokes Vision. Session creation, upload, Gate A,
P1, Gate B, and Pixi do not call Lightning. The app does not automatically retry provider requests.
For this demo the operator watches the existing Lightning balance (about 25 credits); there is no
credit purchase and no application-enforced per-request credit estimate/cap. Avoid repeated taps:
the model's actual charge is provider-controlled. Codex's checks use fake providers and do not send
live requests.

## Prerequisites

- Node.js and pnpm compatible with the repository lockfile.
- Python 3.12 and the backend virtual environment/dependencies.
- Android Studio, Android SDK, and a running Android Emulator. This repository environment did not
  have an SDK/emulator available, so the device build and live call remain for the operator to run.
- A Lightning Vision V2 endpoint and token that you configure privately on the backend host.

From the repository root:

```powershell
pnpm install --frozen-lockfile
pnpm --filter @sketch2life/art-renderer build:demo
```

The backend serves the Pixi bundle from `packages/art-renderer/dist-demo`; build it before starting
the API. Install backend dependencies if needed (`python -m pip install -e .` from `backend`).

## Configure and start the backend

Set provider settings only in an ignored local `backend/.env` or a private runtime secret manager.
Never put a Lightning token in mobile config, source control, terminal output, or a client-side
`EXPO_PUBLIC_*` variable. Configure `SKETCH2LIFE_LIGHTNING_AI_BASE_URL`,
`SKETCH2LIFE_LIGHTNING_AI_TOKEN_FILE` (a restricted-permission file containing only the token), and
`SKETCH2LIFE_LIGHTNING_VISION_V2_PATH` privately on the backend. The endpoint path defaults to
`/v2/vision`.

```dotenv
SKETCH2LIFE_ENV=local
SKETCH2LIFE_AI_PROVIDER=lightning_dev
```

From `backend/`, start the API bound to the host so the emulator can reach it:

```powershell
.venv\Scripts\python.exe -m uvicorn sketch2life.interfaces.http.app:create_app --factory --host 0.0.0.0 --port 8000
```

If using a different virtual-environment path, substitute its Python executable. Keep the API on a
trusted local network and configure the host firewall; do not expose this unauthenticated demo API
to the public internet. Check `http://127.0.0.1:8000/health` on the host before opening the app.

## Build and run on Android Emulator

The emulator's `10.0.2.2` address maps to the development host. The app defaults to
`http://10.0.2.2:8000`. If needed, set `EXPO_PUBLIC_API_URL` to another reachable backend origin
before starting Expo. Local HTTP is allowed only in the generated Android **debug** manifest; do
not carry that setting into a release build.

`react-native-webview` requires a native development build; Expo Go is not sufficient. From the
repository root:

```powershell
pnpm --dir apps/ui-mobile android:dev
```

This is the preferred fresh-install path: Expo builds the debug variant, starts Metro on port
8081, installs the native app, and launches it. The Android Gradle project uses
`BuildConfig.DEBUG`, so a debug APK intentionally expects Metro and does not contain a release
JavaScript bundle. Do not open an old debug APK directly from Android Studio/app icon while Metro
is stopped; that produces the native `Unable to load script` screen shown in the bug report.

If the native debug build is already installed, start Metro separately:

```powershell
pnpm --dir apps/ui-mobile start:dev-client
```

This uses Expo LAN mode so a physical Android device can reach the host. For an emulator or USB
device with Android SDK Platform-Tools installed, the localhost/reverse path is also supported:

```powershell
pnpm --dir apps/ui-mobile start:android-reverse
```

If the app shows `Could not connect to development server` and the URL contains
`127.0.0.1:8081`, either use the LAN command above or verify the reverse mapping with
`adb reverse tcp:8081 tcp:8081`. A successful host probe is:

```powershell
Invoke-WebRequest http://127.0.0.1:8081/status -UseBasicParsing
```

The app uses Android's system image picker only. It requests a single image, with camera, audio,
video, and broad media/storage permissions blocked. Accepted upload formats are PNG/JPEG, at most
5 MB. Confirm that the selected file is synthetic and contains no real child data before upload.

## Manual smoke test

1. Create an ephemeral session and select a synthetic PNG/JPEG. Uploading stores it only in backend
   process memory; it does not call Lightning.
2. Review the Gate A analysis and confirm/correct what is actually present. This button is the
   explicit live Vision request. Check the Lightning balance yourself and do not tap repeatedly.
3. Enter the test age and choose only P1 options that fit the confirmed drawing and real
   supervision/material availability. Approve the exact Gate B spec before continuing.
4. Try the Pixi “reveal whole drawing” action. If the Pixi route is unavailable, the app still keeps
   the native original-image preview; the reveal is an optional demo enhancement.
5. For the FEAT-030 story-video lane, wait for a valid READY artifact and successful player load
   before caregiver handoff. A session without a READY video remains blocked at this step; the
   current experimental lane has no automatic skip/fallback. Feedback and gallery are temporary
   session data, not account history.

The main API contract is available at `/docs`. Important routes include `POST /v1/sessions`,
`POST /v1/sessions/{id}/media/image`, `POST /v1/sessions/{id}/understanding`, Gate A/P1/Gate B
commands under `/v1/sessions/{id}`, `POST /v1/sessions/{id}/renderer/launch`, and
`GET /v1/renderer/source` (short-lived capability required). The OpenAPI schemas and backend tests
are the source of truth for exact request/response contracts.

For the approved session-only child-profile test, the app preserves
`GET /v1/sessions/{id}/p1/context-options` when no profile is supplied and sends a versioned
`POST` to the same route with `P1ContextOptionsRequestV1` when an adult has enabled profile filters.
The POST checks the same actor/session/version and returns baseline-vs-personalized options plus
exclusion counts; it neither mutates session version nor calls Qwen again. Current profile state is
volatile app memory only. Do not add a saved-profile API or storage adapter without the separate
privacy/authorization/storage approval in ADR-0010.

## Limits and future auth seam

The frontend API client accepts an optional `AuthTokenProvider`; no token provider is configured
for this demo. When auth is approved later, the provider can add a bearer token without moving
Lightning credentials to the mobile app. Backend ownership/persistent storage still needs an
approved contract and adapter; this demo intentionally does not save sessions across process
restarts or users.

# Local Pixi runtime test — 2026-10-05

Start the API from the repository root with `powershell -File tools/start_local_backend.ps1`.
This uses ignored backend provider settings and enables the previously approved local/test
Pixi planner and QA-passed sprite preview. Starting the API does not submit inference.
Use `-SourceOnly` only when intentionally testing the older source-only path. A bare uvicorn
launch retains the settings defaults, which disable both planner and sprite preview.

For a repeatable emulator test without Metro, build the internal debug APK with
`-Psketch2life.bundledPreview=true`. This embeds the optimized JS bundle and 29 image/font
assets and disables native developer support for that debug build. Normal debug hot reload
and release signing remain unchanged. The APK is still an internal debug-signed artifact.

Only `motion.walker-corgi.v2` and `motion.walker-avian.v1` currently pass the local preview
allowlist. Other subject/action cycles remain independently gated; enabling the preview flag
does not make the complete 29-class registry playable. The source artwork remains separate.

## Experimental FEAT-030 story-video playback — merge clarification 2026-10-10

The existing native app keeps its versioned `/v1` API and Pixi workflow. Its video surface
now polls `GET /v1/sessions/{id}/story-video-jobs` and plays only a READY job's artifact from
the configured backend origin at `/v1/sessions/{id}/story-video/{job_id}/file`. Job/session
identity, URL origin/path, player loading, polling errors and playback errors gate continuation;
`completeActivityHandoff` also checks the latest job is READY. Polling reads status and does
not create a job or invoke a provider. Exact payloads remain defined by OpenAPI and backend
contract tests, rather than historical illustrative `/api/*` examples.

Story creation/review/rendering remains owned by FEAT-030 approvals and backend contracts.
A newly created FEAT-018 session does not automatically have a story job. Provider/device/visual
acceptance is incomplete: FEAT-030 records EXPERIMENTAL_HANDOFF, STORY_VISUAL_QA_NOT_PASSED
and WAN_L4_RENDER_FAILED_OOM. The V2 renderer retains its disabled-by-default boundary.
Do not treat this merge or a passing offline test as approval for a paid run, production use,
real child media or finished visual quality.

`src/demo/BaoStandaloneApp.tsx` and `src/screens/modules/` are legacy demo/scaffold files;
`App.tsx` still exports the existing `BaoApp`. Added target PNG/crop assets remain inactive
and are not visually approved by this merge. The canonical classroom SRS supersedes older
product assumptions; this merge preserves committed implementation history and does not
implement that replacement scope.
