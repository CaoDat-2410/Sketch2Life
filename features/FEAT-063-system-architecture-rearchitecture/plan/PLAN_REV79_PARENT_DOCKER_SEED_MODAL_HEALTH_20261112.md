# Plan Rev79 — Parent local workflow, seed, and Modal health lifecycle

**Date:** 2026-11-12<br>
**Status:** APPROVED — implementation in progress.<br>
**Product authority:** `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.7-draft Rev60, unsigned. This plan does not amend or sign the SRS.

## Goal

Make the non-video Parent workflow easier to run locally and correct the unfinished catalog activity AI path. A single root `.env` continues to supply local configuration. Docker should migrate the database, seed only missing synthetic demo records, start the API and Auth Emulator, and deploy a dedicated CPU-only Modal health app that receives `GET /health` only. Model inference is an explicit Parent API/UI action; container startup must never dispatch it.

## Scope

1. **Parent activity gate and Qwen worker alignment.** Permit punctuation-free fragments only in `materials_text` and `observation_notes`; keep `objective`, `preparation_text`, `instructions_text`, and `safety_notes` as complete, punctuated sentences. Keep required fields, minimum lengths, outdoor relevance, explicit child agency, Montessori exploration, adult support, safety language/actions, age/context alignment, exactly-three fallback drafts, deduplication, Vietnamese script, and PII checks. Align the Modal output parser/schema with the backend. Add the supported Qwen3.5 linear-attention CUDA kernel package and a startup preflight that logs the available kernels; do not claim inference success without a separate model request.
2. **Firebase config in Parent Expo.** Carry `VITE_FIREBASE_APP_ID` from the root `.env` through Expo `extra`, `parentConfig`, and Parent public settings. Add the optional local Auth Emulator URL to the same config and route REST sign-in/refresh/sign-up calls to that emulator when configured. No Firebase database or storage emulator is enabled.
3. **Synthetic local authentication and data seed.** Add Firebase Authentication Emulator to Compose. Add one idempotent, insert-only seed command for an optional local Parent account, Parent role, synthetic profile and synthetic-only authorization, and one approved/public synthetic lesson with outdoor activities that exercises catalog selection. Stable IDs are used; existing matching rows are verified and skipped; conflicting rows stop with a clear error. Never reset/truncate volumes or change existing user data. Credentials are read only from the ignored root `.env`; blank credentials skip account/profile seeding. Consent is marked synthetic and is not represented as legal consent for real-child data.
4. **Local quota display.** Add the missing Parent quota read API as a local-only demo summary backed by a development setting. The UI labels it as demo data; it does not reserve, spend, or represent a real Billing grant. Video generation remains out of scope.
5. **Docker lifecycle and migration lineage.** Correct the Parent context migration's duplicate Alembic merge ancestors: the pilot/story revision chain already carries the AI-job, profile-age and pilot-vision revisions, so the Parent merge must depend on its leaf story revision without listing those ancestors again. Keep the Parent context revision identifier within Alembic's default 32-character `version_num` column and update the dependent Parent lesson-pin migration to point to that identifier, preserving the migration order. Build the pinned MinIO release from the official upstream source because its configured public Quay image now rejects anonymous pulls. Build the Parent renderer bundle from the locked workspace source instead of requiring the ignored generated `dist-demo` directory. Add migration and seed one-shot services with health-based dependencies. Add a Modal health sidecar that deploys a uniquely named, dedicated CPU-only app, calls its HTTP `/health` once, records local health state, and stops only that dedicated app on Compose shutdown or failed startup. The endpoint reports `inference_ready=false`; it does not deploy, warm, or call Qwen/FLUX/Whisper/SAM/video workers. Configure the local Compose API to use `modal_dev` so explicit Parent AI API calls can reach the configured Modal functions; set the local root `.env` provider key to `modal_dev` while preserving all other local values. Startup still makes no AI function call: only the health sidecar's one `GET /health` is sent. Missing Modal credentials skip the optional sidecar without blocking the backend.
6. **Documentation and evidence.** Record the exact environment variables, local-only account behavior, seed scope, app lifecycle, no-inference startup guarantee, checks, and unresolved production Billing/consent boundaries under FEAT-063.

## Acceptance criteria

- Parent Expo runtime receives the root Firebase Web App ID and local Auth Emulator URL without hardcoded project credentials. The ignored root `.env` may hold generated local-only seed credentials; it must remain untracked and unpublished.
- With emulator/account values configured, Docker starts Auth Emulator, applies Alembic heads, seeds only missing stable demo rows, then starts the API. Running the seed twice creates no duplicate account, profile/revision/authorization, lesson/version/activity, or public grant. Missing optional seed credentials do not fabricate an account.
- `alembic upgrade heads` succeeds on an isolated empty PostgreSQL database; revision identifiers fit the default Alembic version column, the dependent lesson-pin migration points at the compact Parent context revision, and the Parent merge does not list ancestors already carried by its pilot/story dependency chain.
- The Compose API enables the synthetic pilot only in its local-only service configuration, so seeded synthetic authorization can exercise the Parent workflow without making synthetic eligibility available to staging or production.
- A clean local Compose build does not depend on the unavailable anonymous MinIO Quay image; it builds the same pinned upstream release from source.
- A clean local Compose build includes `/renderer` from `packages/art-renderer` and the committed pnpm lockfile; it does not require a previously generated local output directory.
- Seeded media/profile values are synthetic, the authorization row is marked synthetic, and no production Firebase identity or real-child data is created.
- Parent quota endpoint returns a local demo summary only in local mode; the UI clearly says the values are not billed or consumed.
- The Parent fallback quality gate accepts concise punctuation-free fragments only in `materials_text` and `observation_notes`; it rejects incomplete core sentences in `objective`, `preparation_text`, `instructions_text`, and `safety_notes`. Worker output schema/parser and backend gate agree.
- Docker startup performs only Modal deploy plus one `GET /health`; it makes zero AI worker calls and allocates no GPU. Health response distinguishes control-plane availability from model/inference readiness. Compose shutdown stops only the Docker-managed health app.
- The local Compose API uses `modal_dev` only for explicit AI routes; `docker compose up` never invokes an AI worker or allocates a model GPU. The local root `.env` provider change is untracked runtime configuration and must not be staged or published.
- No video route is called, no model output is claimed as live-verified unless a separate synthetic inference completes, and no credential is written to tracked files.
- `docker compose config`, static/type checks needed for touched code, the repository security validator, and one isolated local startup/seed-idempotency/Modal-health lifecycle check are recorded. No full test suite is run unless separately requested.

## Exact implementation manifest

### Backend

- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/src/sketch2life/application/services/local_parent_video_quota.py`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `backend/src/sketch2life/contracts/schemas/parent_video_quota.py`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_admin_app.py`
- `backend/src/sketch2life/infrastructure/local_demo/parent_seed.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_video_quota.py`
- `backend/Dockerfile`
- `backend/alembic/versions/20261110_parent_profile_story_context.py`
- `backend/alembic/versions/20261110_parent_lesson_pin.py`

### Modal, Firebase Auth Emulator, and Docker

- `compose.yaml`
- `.dockerignore`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/docker_health_app.py`
- `deployment/modal/srs_v23/docker_health_lifecycle.py`
- `deployment/modal/srs_v23/Dockerfile.health`
- `deployment/firebase-auth/Dockerfile`
- `deployment/firebase-auth/firebase.json`
- `deployment/firebase-auth/entrypoint.sh`
- `deployment/minio/Dockerfile`

### Parent Expo

- `apps/ui-mobile/app.config.js`
- `apps/ui-mobile/src/parent/infrastructure/config.ts`
- `apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts`
- `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
- `apps/ui-mobile/src/parent/domain/types.ts`
- `apps/ui-mobile/src/parent/ParentModule.ts`
- `apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/AuthScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/QuotaScreen.tsx`

### Configuration, documentation, and records

- `.env.example`
- `docs/local-development/parent-docker-setup.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV79_PARENT_DOCKER_SEED_MODAL_HEALTH_20261112.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-88_PARENT_DOCKER_SEED_MODAL_HEALTH_20261112/`

The ignored repository-root `.env` is a local runtime input for the generated synthetic demo account, Firebase public app configuration, Modal credentials and the local AI-provider toggle. This plan allows changing only `SKETCH2LIFE_AI_PROVIDER` to `modal_dev`; preserve every other existing value. It is never a deliverable, staged file, or evidence artifact.

No file outside this manifest is in scope. If implementation requires a schema, business-rule, API, or path expansion, stop and revise the plan/approval first.

## Verification boundary

- Use a unique Compose project name and isolated named volumes for runtime verification; preserve any existing containers/volumes.
- Verify migration/seed/startup ordering, run the idempotent seed twice, and call the Docker-managed Modal `/health` endpoint. Do not dispatch an AI request during service startup.
- A separate synthetic non-video Parent inference may be attempted only after the health lifecycle is verified and only once per selected API; record queue/model/kernel timings and stop on an unknown outcome. Do not call video. The UI/API remains usable with AI disabled or unavailable and must show safe errors.
- Do not commit or push in this plan. Run `python tools/validate_repository_security.py` before any later commit request.

### Plan Rev79 amendment — Parent API host port collision

- **Status:** APPROVED under the project owner's direct request on 2026-11-12 to make the Parent Docker/UI workflow runnable.
- **Reason:** Runtime inspection found the pre-existing `sketch2life-api-1` container owns host port 8000. Docker created the new API healthy inside its container but did not publish its port, so the Android app could not reach it.
- **Approved local configuration changes:** Persist the isolated stack's current host ports in the ignored repository-root `.env`: API 58000, PostgreSQL 55439, Redis 56390, MinIO 59023, MinIO console 59024, ClamAV 53313, and Firebase Auth Emulator 9099; set `SKETCH2LIFE_MOBILE_API_BASE_URL=http://10.0.2.2:58000`. Preserve the existing service/container and all other `.env` values. Container-internal service ports remain unchanged.
- This amendment supersedes the earlier Rev79 restriction that allowed changing only `SKETCH2LIFE_AI_PROVIDER`; the listed host port and mobile API URL keys are the only additional `.env` changes authorized.
- **Additional acceptance:** Confirm Compose publishes each host port above and run Parent API calls through the mapped API endpoint after configuration.
- **Additional manifest:** `backend/src/sketch2life/interfaces/http/router_composition.py` is included because it mounts the local Parent quota route.
- **Boundaries:** No stopping or changing unrelated containers, no secret output, and no change to the startup rule that Modal receives only `/health` and no inference request.

## Risks and limits

- Firebase Emulator tokens are unsigned and accepted only when Firebase Admin is explicitly pointed at the local Auth Emulator; never set that host in staging/production.
- The seeded Parent/consent is synthetic demo state, not proof of legal consent. Real-child processing remains governed by the canonical SRS and its sign-off gates.
- Local quota is a display-only stub because production Billing tables, purchase rules, and quota allocation remain open in the SRS. It cannot authorize video creation.
- The upstream MinIO community repository is archived and no longer publishes the current public Quay image; the source-built pinned release is a local development bridge only, consistent with the planned move to AWS S3.
- Modal `/health` proves only the dedicated health app is reachable. It does not prove worker deployment, model weights, GPU availability, or inference readiness.
- Qwen3.5 acceleration depends on the pinned Torch/CUDA runtime and compatible kernels; a successful package build is not a successful inference.
