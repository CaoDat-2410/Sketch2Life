# EV-063-74 — Parent/Teacher UI-to-Modal E2E

**Observed:** 2026-11-10 09:04 Asia/Saigon
**Plan:** Rev64 — `plan/PLAN_REV64_PARENT_TEACHER_MODAL_E2E_20261110.md`
**Approved scope SHA-256:** `C6A217BB2114C7D64621E6B50E3A92F6E7E20063866EF6977667F40581BBF9A3`
**Final plan SHA-256:** `B791E6E552FF16A6A99D5758D7A2226FA6DD561AE852A40DF6BC2B87E32015C8`
**Status:** PARTIAL — real Parent and Teacher UIs reached live Modal. Parent optional sketch guide and Teacher lesson suggestion/deck/visual passed. Parent drawing-understanding failed on truncated Qwen JSON, blocking Parent story; Teacher file upload/parser was not exercised.

## Scope

Owner requested real Parent Android and Teacher Web UI flows connected through the application backend to live Modal AI, with screenshots. Fixture flows, backend-only E2E, smoke tests as workflow evidence, and video generation are excluded.

## Initial preflight observations (before the Rev64 deployment and UI run)

| Check | Result | Evidence |
|---|---|---|
| Canonical SRS | Read FEAT-063 SRS v2.7-draft and relevant Parent/Teacher, AI and as-built sections | §5.1–5.2, §6.2, §31.4–31.5 and §32.2 |
| Parent app | Not connected as a real workflow | `AppRoot` mounts `FixtureFlowScreen` after auth; the screen labels its AI action as fixture-only and makes no Modal request. |
| Teacher app | Partial BE1 session wiring; lesson and AI screens remain prototype/demo surfaces | `App.tsx` wraps several routes in `PrototypeOnly`; `activityService`/`videoService` return empty fixture values. |
| Backend AI selection | Not configured for Modal | Root `.env` has `SKETCH2LIFE_AI_PROVIDER=disabled`; no Modal app/function settings are configured. |
| Modal SDK/profile | Read-only access works | Installed Modal SDK 1.6.3 in ignored `backend/.venv`; profile list shows active `docaodat24-10`. No token or secret value was printed or recorded. |
| Modal deployments | No current deployment; source available | Local `dev` commit `1431ef81972b71303fd4a7909748fd3005769a3c` contains `deployment/modal/srs_v23` worker source. Rev52/Rev44 evidence records synthetic worker/API calls and stops the task-used apps at 0 tasks; the empty current app list is consistent with that cleanup. |
| Docker baseline | Pre-existing API and ClamAV are healthy; PostgreSQL and Redis containers are stopped | Existing API/ClamAV were left untouched. No database, identity, UI, or AI request was made for this Rev64 run. |
| Screenshot evidence | Not captured | No real AI-backed workflow can reach a result screen while the required Modal functions are absent. No fixture screenshot was substituted. |

## Initial interpretation and next gate (pre-run)

Modal SDK 1.6.3 was installed in ignored `backend/.venv`; the app list was empty at preflight because the prior task had stopped its deployments. The non-video deployment source and contracts were available on local `dev` and `origin/dev` at `1431ef81972b71303fd4a7909748fd3005769a3c`. Earlier Rev45 worker/API results were not authenticated Parent/Teacher UI acceptance. The preflight blocker was resolved during this Rev64 run; final results follow below.

The approved non-video apps were redeployed from `dev`, exercised through the real UIs, and stopped after testing. No token or secret was recorded.

## UI-to-backend-to-Modal execution results

| Flow/API operation | Status | Observed result |
|---|---|---|
| Parent signup and role resolution | PASS | Real Android UI registration; backend `/api/auth/v1/me` resolved `parent`. Synthetic identity was deleted during cleanup. |
| Parent optional line-sketch guide — `POST /api/parent/v1/ai/sketch-guides` | PASS after one approved UI-render recovery | Live FLUX output rendered in Parent UI. First call completed at Modal but React Native crashed on an unsupported accessibility role; after the narrow UI fix, the one authorized recovery call rendered the 3-step butterfly guide. Recovery backend duration: 52.9 s. |
| Parent drawing understanding — `POST /api/parent/v1/ai/drawing-understandings` | FAIL | UI request `f54c995f-64dd-43cf-bc22-622f34b74de3` returned HTTP 504 `MODAL_OUTCOME_UNKNOWN` after about 44 s. Modal call `fc-01M71JFYS8YR7V5CM5TC6MABTX` used `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`; model load took 17.755 s and inference 18.555 s. It generated 256 tokens, then strict JSON parsing failed with `JSONDecodeError: Unterminated string` and terminal code `MODAL_MODEL_OUTPUT_INVALID` about 7 s after the API had returned. This is an output-length/parser failure, not a GPU cold-start diagnosis. No retry was made. |
| Parent story/storyboard | BLOCKED | Not called because drawing understanding produced no candidate for adult confirmation. No video call was made. |
| Teacher authentication/role gate | PASS | Real Teacher Web Firebase login resolved `teacher` through `/api/auth/v1/me`; Teacher route opened. The app reached the AI authoring page via its built-in screen switcher. |
| Teacher lesson/activity suggestion — `POST /api/teacher/v1/organizations/{org_id}/ai/lesson-plan-suggestions` | PASS | Qwen3.5 API returned 200 in about 130 s (worker wait 125.503 s). Request `bc5a5efc-d81d-4066-b68b-28c34faf343f`. Draft contained 5 steps and 2 activities. Teacher reviewed/edited unsafe and inaccurate draft text in the UI before continuing. |
| Teacher Sketch Deck — `POST /api/teacher/v1/organizations/{org_id}/ai/sketch-decks` | PASS | Qwen3.5 API returned 200 in about 60 s. The UI displayed a 5-slide DRAFT with two approved activity references. |
| Teacher lesson visual — `POST /api/teacher/v1/organizations/{org_id}/ai/lesson-visuals` | PASS | FLUX API returned 200 in about 65 s; 768×432 visual rendered in Teacher UI. |

## Acceptance gaps and fixes

- Parent profile creation/selection and profile snapshot are not available in the tested screen; age was entered manually as 60 months. The Parent story gate depends on a successful drawing candidate and remains untested.
- Teacher AI screen accepts structured lesson fields. It does not expose the planned raw file upload/parser/review flow, so only structured authoring and human AI-draft review were exercised.
- Teacher lesson suggestion initially included inaccurate content and an unsafe close-observation suggestion. The teacher edited the draft in the UI and reviewed it before Deck generation; this confirms the human review gate is usable but does not establish model output quality without review.
- `npm run typecheck` in `apps/mobile` passed. Ruff passed for the Firebase verifier. These are supporting checks, not workflow acceptance.
- Screenshots are stored in `screenshots/`: Parent login/guide/pending/error/drawing states and Teacher login, authoring, Qwen, review, Deck and FLUX states. Parent account headers were cropped. Sanitized timing/model/worker log is in `logs/EV-063-74_UI_TO_MODAL_RUN_20261110.log`.

## Cleanup and final state

- Modal apps `sketch2life-srs23-drawing-vlm-dev`, `sketch2life-srs23-language-audio-dev` and `sketch2life-srs23-flux-image-dev`: STOPPED, 0 tasks. An older already-stopped drawing app entry was left untouched.
- Deleted both synthetic Firebase identities and the temporary credentials JSON; dropped `rev64_e2e` and verified it absent; stopped task-started Postgres/Redis containers and the Android emulator.
- Preserved pre-existing `sketch2life-api-1` and `sketch2life-clamav-1`; no video, fixture, payment, Whisper, SAM2 or other additional AI request was made. No commit or push was made.

## Interpretation

The user’s observation about `dev` was correct: local `dev` and `origin/dev` both point to `1431ef81972b71303fd4a7909748fd3005769a3c`, which contains the Modal worker source and deployment definitions. Earlier Rev45 worker tests passed and the optional Parent guide passed here. This run shows drawing analysis is not generally still waiting for a GPU: the worker loaded and ran Qwen, then rejected a truncated 256-token JSON result. The API surfaced 504 before the worker terminal failure arrived. Overall Rev64 remains PARTIAL until output-length/contract handling is corrected and an explicitly approved new live run covers Parent analysis/story, plus the Teacher upload/parser gap is implemented and exercised.

## Follow-up — drawing output cap and Parent runtime availability (2026-11-10)

- The approved drawing-worker output bound was raised from 256 to 512 in `deployment/modal/srs_v23/drawing_vlm_app.py`; the file compiled and the updated drawing app was deployed, then stopped with zero tasks.
- The one approved Parent drawing-understanding recovery call was **not sent** because this test host had no `adb`, Android SDK/platform-tools or emulator. The previous live 256-token parser failure remains the last verified Parent analysis result; the 512-token fix is not yet validated through the Parent UI.
- A separate Rev65 Teacher UI run is recorded in `EV-063-75_TEACHER_PRESENTATION_UI_20261110.md`. It does not change Rev64's PARTIAL status.
