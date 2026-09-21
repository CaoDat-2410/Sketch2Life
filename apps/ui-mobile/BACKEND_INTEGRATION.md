# FEAT-018 Android demo: UI ↔ backend ↔ Lightning Vision

This guide is for the approved image-only demo on Android Emulator. It does not enable
authentication, persistent child profiles, video, audio, or generated story media. Sessions,
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
pnpm --filter sketch2life-mobile exec expo run:android
```

After the development build is installed, start Metro for the dev client in another terminal:

```powershell
pnpm --filter sketch2life-mobile exec expo start --dev-client
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
5. Optionally test caregiver handoff, non-identifying feedback, and the session gallery. These are
   temporary session data, not account history.

The main API contract is available at `/docs`. Important routes include `POST /v1/sessions`,
`POST /v1/sessions/{id}/media/image`, `POST /v1/sessions/{id}/understanding`, Gate A/P1/Gate B
commands under `/v1/sessions/{id}`, `POST /v1/sessions/{id}/renderer/launch`, and
`GET /v1/renderer/source` (short-lived capability required). The OpenAPI schemas and backend tests
are the source of truth for exact request/response contracts.

## Limits and future auth seam

The frontend API client accepts an optional `AuthTokenProvider`; no token provider is configured
for this demo. When auth is approved later, the provider can add a bearer token without moving
Lightning credentials to the mobile app. Backend ownership/persistent storage still needs an
approved contract and adapter; this demo intentionally does not save sessions across process
restarts or users.
