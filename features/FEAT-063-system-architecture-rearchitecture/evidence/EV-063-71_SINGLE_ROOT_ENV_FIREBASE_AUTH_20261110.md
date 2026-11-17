# EV-063-71 — Single-root Firebase Auth and Docker setup

**Date:** 2026-11-10
**Plan:** Rev61, SHA-256 `27D6D8735FF1F23D9B31F0152AD80EEB0A33085CDC5A1C5096AE1E8452950D30`
**Approval:** FEAT-063 `approvals/TASK_APPROVAL.md`, Plan Rev61

## Scope completed

- Kept all task changes inside the existing `repository root` checkout; no sibling checkout/worktree was created, removed or edited in this slice.
- Updated `.env.example` with placeholders for Firebase web client config and the backend-only Base64 Admin credential. Created one ignored root `.env` from that template and populated it with the owner's public Firebase web config and Admin credential. The JSON key was read from Downloads and was not copied into the project; no nested `.env` was created.
- Configured Docker Compose to pass the Firebase provider, project ID, Admin Base64 value and revoked-token policy only to the API container.
- Configured backend API and database settings to read the root `.env`, ignore keys owned by Compose/Vite, and accept Firebase Admin service-account JSON from a strict Base64 decoder that checks project ID and does not log credential contents. Existing file/ADC fallback remains for backward compatibility.
- Configured Teacher Vite and Parent Android to read the same root `.env`. The mobile Babel plugin inlines only the four allow-listed public `VITE_FIREBASE_*` values.
- Added Parent Android Firebase Authentication REST sign-up/sign-in, in-process refresh and local sign-out behind `AuthSessionPort`; credential errors are mapped to safe Vietnamese copy. Firebase Auth tokens are memory-only. Signup creates a Firebase Authentication identity; Parent role/profile provisioning is not implemented by this slice.
- The root `.env` now sets `SKETCH2LIFE_AUTH_PROVIDER=firebase`. `firebase-admin` 7.7.0 was installed into the existing `backend/.venv`; the dependency was already declared in `backend/pyproject.toml` and no manifest/lockfile changed.

## Verification

| Check | Result |
|---|---|
| Backend Firebase credential + settings tests | 12 passed. The test command overrode local-only `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=false` and `SKETCH2LIFE_AUTH_PROVIDER=development` for existing isolated settings tests; pytest cache was disabled. |
| Local Firebase Admin credential check | Passed: Base64 decoded, required service-account fields were present, project ID matched `sketch2life-dev`, and the configured Admin app initialized and was disposed through the backend adapter. No network request was made. |
| Parent Android TypeScript | `tsc --noEmit -p apps/mobile/tsconfig.json` passed. |
| Parent Android auth adapter runtime smoke | Passed with a synthetic fetcher for signup, signin, token refresh and signout; no Firebase request was made. |
| Parent Android Jest auth tests | Not run: Jest stopped before test discovery because Node `realpathSync.native` returned `EPERM` for the workspace path, including when invoking the suite directly. |
| Teacher Web production build | Passed. Vite reports the existing advisory that a generated JS chunk exceeds 500 kB. |
| Docker Compose configuration | `docker compose config -q` passed with the configured Base64 value; no services were started or stopped. |
| Mobile Babel environment check | Passed: the root public Firebase key was inlined; the allow-list transform does not read or inline the Admin credential. |
| `git diff --check` | Reports an existing unrelated blank line at EOF in `features/FEAT-058-review2-document-package/evidence/README.md:161`; that file was not edited. |

## Boundaries and remaining setup

- No live Firebase request or account was created, so live Firebase Auth and ID-token verification have not been demonstrated.
- The local credential was accepted by the Admin SDK constructor, but no live Firebase ID token was verified and no Firebase account was created. The key and its Base64 value remain only in ignored root `.env`; do not put them in chat or source control.
- `apps/mobile` keeps refresh tokens only in memory; clearing the process requires the adult to sign in again. No Firebase Storage, Firestore or Realtime Database is used.
- Parent backend role/profile provisioning and the full Parent product workflow remain separate work.
- The canonical FEAT-063 v2.7-draft SRS was not edited and remains unsigned.
- No database/migration, Docker lifecycle, Firebase Console, Modal, commit or push operation was performed.
