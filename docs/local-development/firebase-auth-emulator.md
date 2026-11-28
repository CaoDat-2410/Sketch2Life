# Firebase Authentication Emulator

The Firebase Authentication Emulator is for local and test use only. Never connect it to production or real accounts. It runs only the Authentication emulator; Sketch2Life product files and data remain outside Firebase.

## Start

The service is opt-in through the **firebase-emulator** Compose profile. The default host port is **9099**; set **SKETCH2LIFE_FIREBASE_AUTH_PORT** to another free port if needed.

~~~sh
docker compose --profile firebase-emulator up -d firebase-auth
~~~

For API token verification, configure the API container with:

~~~text
SKETCH2LIFE_AUTH_PROVIDER=firebase
SKETCH2LIFE_FIREBASE_PROJECT_ID=sketch2life-local
SKETCH2LIFE_FIREBASE_EMULATOR_HOST=firebase-auth:9099
~~~

Compose passes that last value to **FIREBASE_AUTH_EMULATOR_HOST** only when explicitly set. Start the API with the emulator profile enabled. The verifier refuses to start with that host in staging or production.

## Local end-to-end stack without ClamAV

`compose.e2e.yaml` is an optional overlay for local/test only. It swaps ClamAV for the fixture-hash
allowlist scanner (`deployment/e2e/scanner-allowlist.json`) and moves ClamAV behind the `clamav`
profile. Without the overlay the default behaviour of `compose.yaml` is unchanged.

~~~sh
docker compose -f compose.yaml -f compose.e2e.yaml -p s2le2e --env-file <your env file>   --profile firebase-emulator up -d --build
~~~

The API image no longer needs the git-ignored `packages/art-renderer/dist-demo` folder: it is copied
only when present, and without it the API simply does not serve `/renderer`.

## Docker BuildKit note

On some Docker Desktop installs BuildKit fails an API image build with
`failed to commit ... snapshot ... does not exist: not found` on a `COPY` step. A retry does not help.
Build with the legacy builder instead, then start without rebuilding:

~~~sh
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f compose.yaml -f compose.e2e.yaml -p s2le2e --env-file <env> build api
docker compose -f compose.yaml -f compose.e2e.yaml -p s2le2e --env-file <env> up -d --no-build api
~~~

(PowerShell: set `$env:DOCKER_BUILDKIT=0; $env:COMPOSE_DOCKER_CLI_BUILD=0` first.) If the error persists,
restart Docker Desktop or prune its build cache.

For web sign-up, configure:

~~~text
VITE_FIREBASE_AUTH_EMULATOR_URL=http://localhost:9099
VITE_FIREBASE_API_KEY=placeholder
VITE_FIREBASE_AUTH_DOMAIN=sketch2life-local.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=sketch2life-local
VITE_FIREBASE_APP_ID=placeholder
~~~

These **VITE_FIREBASE_*** values are local placeholders. The project ID **sketch2life-local** is fake and must not be replaced with a real project ID for emulator use.

From an Android emulator, configure the Auth emulator host as **10.0.2.2:9099**. A physical device must use the host machine's LAN IP and a Compose port binding that exposes the port on the LAN; the default binding is loopback-only.

### Client environment names

The web and Android clients read the emulator URL from exactly these names (they are already defined as commented examples in `.env.example`):

- Web (Vite): `VITE_FIREBASE_AUTH_EMULATOR_URL=http://localhost:9099`
- Android Parent app (Expo): `EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL=http://localhost:9099` (localhost is rewritten to `10.0.2.2` on the Android emulator)

The backend and compose names stay separate: `FIREBASE_AUTH_EMULATOR_HOST` (set inside the api container through `SKETCH2LIFE_FIREBASE_EMULATOR_HOST=firebase-auth:9099`). Never set any emulator URL or host in a release build; the backend refuses `FIREBASE_AUTH_EMULATOR_HOST` when `SKETCH2LIFE_ENV` is not `local` or `test`.

### Google sign-in caveat (UNVERIFIED)

The native Google account picker on Android stays on real Google; only the token exchange (the Firebase Auth call that turns the Google credential into a Firebase session) is meant to go to the emulator. This has not been verified end to end. Use email and password accounts for local tests until it is checked.

## Test accounts and state

Create one emulator account for each role under test: Parent, Teacher, School Manager, and Platform Admin. Create them through the emulator REST endpoints or the web sign-up flow. Use a throwaway password of your choice; never reuse a real one.

Auth emulator data is imported from and exported to **/data**, backed by the logical Compose volume **sketch2life-firebase-auth**. Remove only that volume to reset emulator accounts; Compose may prefix the volume name with the project name. The emulator cache is stored separately in **sketch2life-firebase-cache**.

## Troubleshooting

If host port **9099** is already in use, set **SKETCH2LIFE_FIREBASE_AUTH_PORT** to another free port and use that port in client emulator URLs.
