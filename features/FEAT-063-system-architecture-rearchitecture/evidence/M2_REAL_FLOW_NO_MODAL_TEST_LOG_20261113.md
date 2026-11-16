# M2 real-flow test log (no Modal) - 2026-11-13

Status: WORKING LOG (evidence, not an approval record). Owner of the run: Person 2.
Scope: manual end-to-end test of the Parent flow on the integration build, with a real
PostgreSQL, real Firebase auth and the Android emulator. No Modal call was made by the backend
in this flow. This file records what was done, what failed, how it was resolved, and what is
still open. It contains no credentials, tokens, emails or local absolute paths.

## 1. Build under test

| Item | Value |
| --- | --- |
| Integration branch | `integration/dev-on-s1ap`, tip `9dfdd2d7` (merge of S1a-P2 `77cf761d`), local only at the time of writing |
| M2 branch | `feature/feat063-m2-parent-teacher-foundation`, HEAD `77cf761d` |
| Backend | Docker Compose project `s2l-int` (api + postgres), `--no-deps` (MinIO image pull returned 401) |
| Database | scratch PostgreSQL in the compose project, published on `127.0.0.1:55432` only |
| Mobile | Expo SDK 52 / RN 0.76 app in the mobile worktree, Android emulator `Pixel_6a`, backend reached at `10.0.2.2` |
| Auth | real Firebase project (email + password), then `GET /api/auth/v1/me` |
| Modal | `OWNER_MODAL_CALL_APPROVED=NO` for this flow; Modal testing paused until the AI fix lands |

Local override file (not in the repository) enabled `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true`
for the api service and moved the scratch database to host port 55432 (native PostgreSQL already
owned 5432).

## 2. Timeline of the test

| # | Step | Result |
| --- | --- | --- |
| 1 | Merge S1a-P2 into the integration branch | Done locally. DECISIONS.md merged append-only. Duplicate router mount found and fixed (`parent_profiles_router` mounted once). Catalog counts 134/118/150. One pre-existing BE1 route-description test failure accepted. |
| 2 | Gate A (offline suite) on integration | Pass, apart from the accepted pre-existing failure above. |
| 3 | Start backend in Docker | Needed fixes, see issues I-1 to I-5. Final: `GET /health` 200 repeatedly. |
| 4 | Apply migrations | `alembic upgrade heads` (multi-head). |
| 5 | Parent profile on real PostgreSQL | list 200, create 201, PATCH 200, DELETE 202 (`DELETE_PENDING`). Closes the open real-PostgreSQL item of S1a-P2. |
| 6 | Seed a lesson | Four fixed-UUID rows via the seed runbook (PUBLIC ACTIVE grant, APPROVED version). Verified with the verify SQL. |
| 7 | Create StoryRun | `POST /v1/story-runs` 201, run id `949cf06f...`. |
| 8 | Context confirmation | `POST .../context-confirmation` 200. |
| 9 | Login after emulator data clear | `GET /api/auth/v1/me` 200, `GET /v1/parent/profiles?limit=25` 200, `GET /v1/story-runs/active/current` 200. |
| 10 | Second run while one is active | UI guard observed: the Home screen shows an "open session" card ("finish the current session before starting a new one") so the app blocks a second run client-side. The backend 409 `ACTIVE_RUN_EXISTS` was NOT exercised on real PostgreSQL (no request reached the api; covered by offline route tests only). Owner decision 2026-11-13: the UI block is accepted for this verification; no separate backend 409 test is required now (the backend rule stays as a safety net for other clients and races). |
| 11 | Relaunch and restore active run | PASS at UI level: after relaunch and login, Home shows the open session with the banner that it is already past the context step and cannot continue in this verification step (expected, flow ends at context confirmation). Backend-side confirmation of this relaunch was not captured (api log tail held only `/health`). |
| 12 | Field-error 400 and second DELETE 409 | NOT RUN by owner decision (covered offline; PATCH 200 / DELETE 202 already seen on PostgreSQL). |
| 13 | Manual reset of the test run (scratch data) | Run `949cf06f...` was in `INPUT_PROCESSING` with the active-owner column set. The owner set `run_state='FAILED'` and cleared `active_owner_parent_account_id` directly in the scratch database (`s2l-int`) through a SQL client, after temporarily lifting that connection's read-only flag, to unblock a new run. The statement returned one row with `FAILED`. This is a manual data edit, not a product path (see I-11). |
| 14 | New run after reset | New run created and advanced in the app to wizard step 5 of 7. |
| 15 | Swipe-close the app, log in again, press "Continue open session" | FAIL as a product behaviour, expected by code: Home shows the open-session card, and pressing Continue shows the banner "already past the context step, cannot continue in this verification step". Restore therefore works only for `CONTEXT_PENDING`; a run past context confirmation is detected but cannot be resumed (see I-11). This corrects the PASS-at-UI-level reading of step 11, which only showed that the open run is detected. Database state read afterwards: the second run `08ac07b9-c30b-4bc2-a791-02e04995bc0a` was `INPUT_PROCESSING` (last updated 12:22:30 local time); the first run `949cf06f-...` was `FAILED` after the manual reset in step 13. The same `INPUT_PROCESSING` state (not `CONTEXT_PENDING`) was seen for the first run before the reset, so in this build a context-confirmed run sits in `INPUT_PROCESSING`, which the app does not resume. |
| 16 | Second manual reset (scratch data) | Run `08ac07b9-...` set to `FAILED` and its active-owner column cleared with the same manual statement as step 13; one row returned. Both test runs are now `FAILED`, so no active run remains. |

## 3. Issues found and how they were resolved

| ID | Symptom | Cause | Resolution |
| --- | --- | --- | --- |
| I-1 | `docker compose up` failed pulling MinIO (401) | Registry pull denied | Started with `--no-deps`; MinIO not needed for this flow. |
| I-2 | Image build failed on `COPY packages/art-renderer/dist-demo` | Directory absent in the worktree | Created an empty placeholder directory. It is untracked and must not be committed. |
| I-3 | DBeaver showed "database sketch2life does not exist" and connected to the wrong server | Native Windows PostgreSQL already listens on 5432 | Published the scratch DB on `127.0.0.1:55432` via the override file. |
| I-4 | Profile creation returned 409 `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE` | Creation gate needs env `local`/`test` and `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true` | Set the flag in the override file. Use the override file on every `up`. |
| I-5 | Alembic reported several heads | Parallel migration branches | Use `alembic upgrade heads`. |
| I-6 | PATCH/DELETE failed in Gate P2 attempt 1 | Ownership pre-check ran inside the same transaction as the mutation | Fixed in `parent_profile_repository.py` (pre-check in its own transaction). Verified PATCH 200 / DELETE 202 on PostgreSQL. |
| I-7 | Mobile app showed "Thiếu API URL" | Metro cached the old environment | Cleared `.expo` and `node_modules/.cache`, restarted Metro. |
| I-8 | adb reported no ready device | Emulator not started | Start the emulator first, then `android:dev`. |
| I-9 | Lesson library empty on the Topic screen | No lesson rows | Seeded the lesson rows (step 6). |
| I-10 | Login showed a red error box with status 0 | See section 4 | Cleared app data, logged in again, login succeeded. |
| I-11 | Home "Continue open session" button shows the banner "already past the context step, cannot continue in this verification step" instead of navigating | Expected by current design: `resumeActiveRun` in `useParentController.ts` only resumes a run whose `run_state` is `CONTEXT_PENDING`; the test run was already context-confirmed. Dead end: no cancel action is reachable from Home, so the active run blocks new runs. The History screen has a cancel action, but the mobile client calls `/api/parent/v1/story-runs/{id}/cancel`, which was not verified against the backend routes in this build. | Open item for the mobile and BE lanes: reachable cancel/abandon path for an active run, and resume for states after context confirmation. Not a regression of this test. |

## 4. Detail: login red box, status 0 (I-10)

- Symptom: after relaunching the app the login screen showed a red box with `status 0`.
  In React Native, `whatwg-fetch` reports status 0 when the request fails at the network layer
  (no HTTP response), so this is not an HTTP error from Firebase or from the backend.
- The failing call was the Firebase `signInWithPassword` request, not the backend call.
- Checked and ruled out: Firebase API key and project configuration, host-side connectivity to
  the Firebase endpoint, emulator internet access (Chrome loaded external sites), emulator to
  backend (`10.0.2.2` reached `/health`), proxy settings, DNS.
- Remaining cause: stale emulator or app state. Fix applied: `adb shell pm clear` on the dev app
  package, then reopen and sign in again.
- Result: login succeeded. Backend log after the fix shows
  `GET /api/auth/v1/me` 200, `GET /v1/parent/profiles?limit=25` 200,
  `GET /v1/story-runs/active/current` 200.
- If it recurs: Cold Boot the emulator, then reinstall the dev build.
- Follow-up for the mobile lane: add a request timeout and explicit status-0 handling in the app
  fetch layer so a network-layer failure shows a readable message instead of a raw error box.

## 5. Open items

1. Complete steps 10 to 12 and append the results to this file.
2. Record the real-PostgreSQL evidence (steps 5, 7, 8) as an S1a-P2 addendum through the normal
   approval path. This log is supporting evidence only.
3. Push of the M2 and integration branches needs an explicit `PUSH APPROVED`.
4. Remove the untracked placeholder `packages/art-renderer/dist-demo` from the integration
   worktree when finished. Do not commit it.
5. Modal: no further testing until the AI fix is delivered. Any later Modal use needs a bounded
   owner approval.
6. Scratch containers (`s2l-int`) are still running on the owner's machine.
