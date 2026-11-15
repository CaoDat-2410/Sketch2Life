# Parent local Docker setup

This setup starts the backend and local infrastructure. The Expo app remains a separate process.
All local configuration comes from the single repository-root `.env` file.

## Root `.env` values

Start from `.env.example`, then set these values in the root `.env`:

```dotenv
SKETCH2LIFE_API_PORT=58000
SKETCH2LIFE_MOBILE_API_BASE_URL=http://10.0.2.2:58000
SKETCH2LIFE_POSTGRES_PORT=55439
SKETCH2LIFE_REDIS_PORT=56390
SKETCH2LIFE_MINIO_PORT=59023
SKETCH2LIFE_MINIO_CONSOLE_PORT=59024
SKETCH2LIFE_CLAMAV_PORT=53313
SKETCH2LIFE_FIREBASE_AUTH_PORT=9099
SKETCH2LIFE_AUTH_PROVIDER=firebase
SKETCH2LIFE_FIREBASE_PROJECT_ID=the-same-project-id-as-VITE_FIREBASE_PROJECT_ID
SKETCH2LIFE_FIREBASE_ADMIN_JSON_BASE64=placeholder
VITE_FIREBASE_PROJECT_ID=the-same-project-id-as-SKETCH2LIFE_FIREBASE_PROJECT_ID
VITE_FIREBASE_APP_ID=your-firebase-web-app-id
VITE_FIREBASE_AUTH_EMULATOR_URL=http://localhost:9099
MODAL_TOKEN_ID=placeholder
MODAL_TOKEN_SECRET=placeholder
SKETCH2LIFE_MODAL_ENVIRONMENT=dev
SKETCH2LIFE_AI_PROVIDER=modal_dev
```

`SKETCH2LIFE_API_PORT` is the host port published by Compose; the backend still listens on port
8000 inside Docker. `SKETCH2LIFE_MOBILE_API_BASE_URL` must use the same host port. The values
above avoid the existing local API already using port 8000 on this development machine. On a
clean machine, you can use `8000` in both values instead. For a physical Android device, replace
`10.0.2.2` with the development computer's reachable LAN address.

`VITE_FIREBASE_APP_ID` is public client configuration. The Admin service-account value and Modal
tokens are backend-only. Do not copy the Admin credential or Modal tokens into Expo variables.
Optional synthetic seed credentials belong only in the ignored root `.env`. If either is missing, Docker does
not create a Firebase account or child profile; the sample public lesson and local quota display
are still prepared. Do not use a real child name or real child data in this synthetic profile.

Compose uses the Firebase Authentication emulator only. Its host-side endpoint is
`http://localhost:9099`; the Parent app automatically changes this to `10.0.2.2` on Android.
Backend Admin SDK calls and token verification are pointed at `firebase-auth:9099`, so local
sign-up and seed account creation cannot write to the production Firebase project. Firebase
Storage, Firestore and Realtime Database are not started.

The local fallback consent policy says it is synthetic development data. It is not legal consent
for real-child data. The seeded child is 84 months old, uses the display label “Trẻ thử nghiệm”,
and has a synthetic-only authorization record.

## Start and stop

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 100 migrate seed-parent-demo api modal-health
```

When running from the repository root, Compose reads that directory's `.env` automatically. If
the checkout is a nested worktree and the only `.env` is in `<repo-root>`, pass it
explicitly:

```powershell
docker compose --env-file ..\..\.env up --build -d
docker compose --env-file ..\..\.env ps
```

Startup order is PostgreSQL readiness → Alembic migrations → insert-only Parent demo seed → API.
The seed uses stable identifiers, verifies existing records and inserts only missing rows. It
does not truncate or reset existing volumes. Existing Parent profiles are preserved; if the
seeded Parent already owns a profile, no additional profile is inserted. The synthetic public
butterfly lesson contains three outdoor activities for catalog-first Parent suggestions.

The local quota endpoint is a display-only development projection. Its values come from
`SKETCH2LIFE_LOCAL_DEMO_PARENT_VIDEO_QUOTA_GRANTED` and
`SKETCH2LIFE_LOCAL_DEMO_PARENT_VIDEO_QUOTA_USED`; no quota is reserved, consumed or billed.
Video generation is not enabled by this seed.

If you add synthetic seed credentials to the ignored root `.env` after the first `docker compose up`, rerun the one-shot seed:

```powershell
docker compose run --rm seed-parent-demo
```

Then start the Expo app from `apps/ui-mobile` and sign in with the synthetic local account configured in the ignored root `.env`. Firebase Auth Emulator persists user data in a named volume; never store the seed identity or password in Git.

Stop the stack with:

```powershell
docker compose down
```

This stops the local Modal startup controller and preserves the already-deployed Modal Apps,
PostgreSQL, Auth Emulator, MinIO and other named-volume data. `docker compose down -v` deletes
those local volumes and should only be used when intentionally resetting the development data.

## Modal startup behavior

When both Modal token variables are present, `modal-health` uses the already-deployed drawing-VLM,
language-audio and FLUX Apps in `SKETCH2LIFE_MODAL_ENVIRONMENT`. It invokes each configured
non-video worker once with the exact internal warmup control envelope. This is a real Modal
Function call to allocate a worker and load its pinned model, but it is not a product request: it
does not run inference, create a product output, or carry a user prompt, child profile, drawing, or
audio. The controller then calls `/health` on each existing App. The health endpoint checks the
App only; worker readiness is reported separately by the warmup result.

The controller does not create a dedicated health App, deploy/update the shared Apps, set a
minimum GPU container count, or stop the shared Apps. Deployed Apps may remain visible in Modal
after `docker compose down`; an App being listed does not mean its GPU containers are running.
Warmup/model-load time and each worker's configured idle scaledown window are billable. After
scale-to-zero there are no live worker containers/compute charges; a later product request will
cold-start again. A product request made while a warmed container is still alive may reuse the
loaded model. Docker startup is not a guarantee of a permanently warm worker.

The Apps must already be deployed with the current worker source, including the warmup contract
and `/health` function. Docker deliberately does not rebuild/redeploy shared Modal Apps at every
local restart. After changing a worker, deploy that App once from the project root:

```powershell
modal deploy --env dev deployment/modal/srs_v23/drawing_vlm_app.py
modal deploy --env dev deployment/modal/srs_v23/language_audio_app.py
modal deploy --env dev deployment/modal/srs_v23/flux_image_app.py
```

The Modal dashboard's **Containers** view lists live runtime instances and provides tools to
inspect their logs, execute commands, or stop them. It is useful for observing/debugging the
temporary worker containers created by warmup and real requests. It is not where Sketch2Life
deploys its AI services. The Apps/Functions are the deployable product services; Docker only
invokes their warmup control path and health endpoints.

When Modal credentials are blank, the sidecar records `SKIPPED` and does not contact Modal. A
missing App, unhealthy model worker or failed `/health` probe is visible in
`docker compose logs modal-health` and marks the optional sidecar `DEGRADED`; it does not block the
local backend API. The local API uses `modal_dev`, and product AI inference remains tied to an
explicit user action rather than Docker startup.

To inspect startup progress and verify the controller state:

```powershell
docker compose logs -f modal-health
docker compose exec modal-health python docker_health_lifecycle.py --check
```

Docker shutdown cancels any task-started, still-pending warmup input when possible, then stops the
local controller. It never calls `modal app stop` and leaves shared Apps available for future
startup or explicit product requests.
