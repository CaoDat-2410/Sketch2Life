# Local development setup

## Prerequisites

- Python 3.12.
- Node.js 22.13 or newer.
- pnpm 11.
- Docker Desktop for the FastAPI backend, PostgreSQL, Redis, MinIO and ClamAV (ClamAV needs several GiB of memory for signature data).
- Android Studio with JDK 17+ support, Android SDK Platform 37, Build Tools 37.0.0, and an Android emulator/device.

## First checkout

1. If `.env` does not exist, copy `.env.example` to `.env` and edit the local PostgreSQL/MinIO placeholder credentials. Do not overwrite an existing ignored `.env`.
2. Start the local stack with `docker compose up --build -d`.
3. Apply the additive database migrations with `docker compose exec api alembic upgrade heads` before using persistent BE1 or Lesson Library routes. This command is documented only; it has not been run for this handoff.
4. Compose already runs the API. Create a backend virtual environment only if you want to run Python tooling or the API directly on the host.
5. Install JavaScript dependencies with `pnpm install`.
6. Run harness and architecture checks before feature work.

## Backend commands

These are for host-run development. Do not run a host Uvicorn process on port 8000 while the
Compose `api` service is running. To switch to host-run mode, stop the container with
`docker compose stop api`; use `http://localhost:9000` for `SKETCH2LIFE_S3_ENDPOINT` in
`backend/.env`, and enable the local example flag only when you want to exercise its routes.

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -e "backend[dev]"
backend/.venv/Scripts/python -m pytest backend/tests
backend/.venv/Scripts/python -m uvicorn sketch2life.main:app --app-dir backend/src --reload
```

The backend exposes `GET /health`. The local Compose profile also enables a development-only
S3-compatible lesson-source example when `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true`:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/dev/v1/storage-examples/lesson-source-documents` | Upload a PDF, DOCX, or PPTX to a private MinIO bucket |
| `GET` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | Stream the private object through the backend |
| `DELETE` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | Delete the example object |

This example stores the original bytes and minimal metadata only. It does not create a `Lesson` or
write database metadata. Use synthetic documents without child data. It has no authentication
because it is mounted only for `local` mode and Compose publishes the API on `127.0.0.1`.

Open `http://localhost:8000/docs` to use the example from Swagger UI. From PowerShell, upload a
local synthetic PDF with:

```powershell
curl.exe -X POST "http://localhost:8000/api/dev/v1/storage-examples/lesson-source-documents" -F "file=@C:\path\to\lesson.pdf"
```

Use the returned `object_id` with the GET or DELETE route. MinIO's API is at `http://localhost:9000`
and its Console is at `http://localhost:9001`; credentials come from the ignored root `.env`.
The bucket is private. The backend holds storage credentials; clients receive no S3 URL or key.

The adapter uses the same Boto3 S3 API for MinIO and AWS S3. For a future AWS deployment, omit
`SKETCH2LIFE_S3_ENDPOINT`, set the bucket and region, and use the AWS default credential chain or
an IAM role; do not add AWS access keys to the mobile app. The Compose example remains local-MinIO
oriented. MinIO's upstream community repository is archived and its community distribution is
source-only now, so the pinned MinIO image is for this synthetic local example, not a production
recommendation ([upstream status](https://github.com/minio/minio), [last upstream security release](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z)).

The Rev31 Lesson Library API is mounted under `/api/lesson-library/v1` in the combined app. It
requires Firebase bearer-token verification, the PostgreSQL migration above, private MinIO storage,
and ClamAV. Source documents are malware-scanned and parsed deterministically; Teachers review the
allowlisted extraction before saving a LessonVersion. This flow has no AI or OCR.

See [the full API inventory](../../features/FEAT-063-system-architecture-rearchitecture/artifacts/API_INVENTORY_FEAT063_REV31_20261028.md)
for all active, conditional and unmounted route declarations. FastAPI's `/docs` page describes the
combined app, though candidate/fixture routes listed in the inventory are not mounted there.

Stop the stack with `docker compose down`. This keeps the PostgreSQL, Redis, MinIO and ClamAV
database named volumes.

The backend dependency set uses FastAPI 0.141+ and HTTPX2 for current Starlette test-client compatibility.

## JavaScript workspace commands

```powershell
pnpm install
pnpm typecheck
pnpm test
pnpm --dir apps/mobile start
pnpm --dir apps/mobile android
pnpm --dir apps/mobile android:apk:debug
```

### Android dev-client and Metro connectivity

The current Android app is `apps/ui-mobile` (`sketch2life-mobile`). Start its development client
with LAN mode when using a physical device or when ADB is unavailable:

```powershell
pnpm --dir apps/ui-mobile start:dev-client
```

For a fresh native debug install, use the one-command path so Expo builds the debug variant,
starts Metro, and launches the app against that server:

```powershell
pnpm --dir apps/ui-mobile android:dev
```

Do not launch an old debug APK directly from Android Studio/app icon and expect it to contain the
JavaScript bundle: this project intentionally leaves the JS out of debug APKs and loads it from
Metro. A direct launch without Metro produces the native `Unable to load script` screen.

For an emulator or USB-connected device, use the helper to install the loopback reverse mapping
before starting Metro:

```powershell
pnpm --dir apps/ui-mobile start:android-reverse
```

The reverse mode requires Android SDK Platform-Tools and a running/connected device. If the app
shows `Could not connect to development server` with a URL at `127.0.0.1:8081`, check the host
server first:

```powershell
Invoke-WebRequest http://127.0.0.1:8081/status -UseBasicParsing
```

If that probe succeeds, reload the app after either using LAN mode or confirming:

```powershell
adb reverse tcp:8081 tcp:8081
adb devices -l
```

`127.0.0.1` is the Android runtime's own loopback address unless the reverse mapping exists. Do
not put a host IP, backend token, provider URL, or secret into the mobile bundle or an `EXPO_PUBLIC_*`
variable.

The official React Native 0.87 Android native project is committed under `apps/mobile/android/`. There is no iOS target. Use an API 29 emulator/device for compatibility checks and API 36 for target-behavior checks.

Android constants are frozen by ADR-0004:

- namespace/application ID: `com.sketch2life.mobile`
- minSdk: 29 (Android 10)
- targetSdk: 36 (Android 16)
- compileSdk/build tools: 37/37.0.0

Debug builds rely on the developer-local Android debug key generated by the Android toolchain; no debug keystore is stored in this repository. Release signing must be injected by the project owner or protected CI and must never reuse the debug key.

Lightning/Runpod environment values are backend-only. Keep them in a local ignored `.env` or runtime secret store; never place them in React Native `.env` files, Gradle resources, or JavaScript bundles.

Firebase is Authentication-only. Local fixture development may use development identities or the Firebase Auth Emulator after its integration feature. Do not enable Firebase Storage/Firestore/Realtime Database for application data.

See `docs/setup/ANDROID_RELEASE.md` before sharing any APK or creating the Google Play app. Public Play release uses an AAB, not the local debug APK.

## Harness commands

```powershell
python tools/validate_harness.py
python tools/validate_skeleton.py
python tools/validate_architecture.py
python tools/new_feature.py 10 example-feature
```

Do not commit `.env`, credentials, runtime child data, or unapproved generated visuals.
