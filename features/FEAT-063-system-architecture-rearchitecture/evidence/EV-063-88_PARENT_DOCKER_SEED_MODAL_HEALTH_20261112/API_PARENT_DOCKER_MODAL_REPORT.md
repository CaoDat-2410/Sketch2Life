# Parent Docker, seed and Modal health verification — 2026-11-12

## Scope and authority

- Plan: `plan/PLAN_REV79_PARENT_DOCKER_SEED_MODAL_HEALTH_20261112.md`.
- Approved plan SHA-256: `5B8375B7DEED983AAB33C69297C3F44C5B35B12985F17D39E7920035555C0380`.
- Requirements baseline: FEAT-063 v2.7-draft Rev60, unsigned; this work does not edit the SRS.
- Environment: one isolated Compose project named `rev79-parent-local-20261112`, synthetic Parent data only. No real child data was used.
- Credentials, Firebase app ID, tokens, account password, access token, and service-account data are intentionally omitted.

## Changes verified

- Parent fallback activity quality gate accepts punctuation-free fragments only in `materials_text` and `observation_notes`; `objective`, `preparation_text`, `instructions_text`, and `safety_notes` remain complete-sentence fields. Safety, outdoor setting, child agency, exploration, adult supervision, age/context, Vietnamese text, PII, deduplication, and exactly-three fallback rules remain.
- Qwen activity worker schema/parser has the same field-specific punctuation rule and retains required-field, length, language, age-band, and response-shape checks. The Modal worker source pins Qwen3.5-9B; local source preflight checks the required linear-attention kernels.
- Parent Expo walks upward to the project root containing `.git`, `compose.yaml`, and the single root `.env`, so a Codex worktree does not make the app ID appear missing. Expo's resolved public config matches the root `.env` app ID; the value is not recorded here.
- Local Compose API is configured for `modal_dev`. The ignored root `.env` contains the provider and the approved host-port mapping for the existing local stack; no credential values are included in this report. The API listens on 8000 inside Docker and publishes to host 58000, avoiding the pre-existing API on host 8000. Parent Android targets `http://10.0.2.2:58000`. Model routes run only when explicitly requested. Compose startup did not call an AI worker.
- Parent seed is insert-only with stable IDs. It creates or reuses the local Auth Emulator account and role, synthetic profile/revision/authorization, and one public lesson/version with three outdoor activities plus a public VIEW grant. Quota is a local, read-only configuration summary, not a Billing ledger or charged grant.
- The Parent context migration uses revision `20261110_parent_ctx` (fits Alembic's default 32-character version column); the dependent `20261110_parent_lesson_pin` migration points to it.
- Compose includes PostgreSQL, Redis, MinIO, MinIO bucket initialization, ClamAV, Firebase Auth Emulator, migrations, seed, API, and a dedicated Modal health sidecar. MinIO is built from the pinned upstream source because its prior anonymous image pull returned 401.

## Runtime results

| Check | Result |
|---|---|
| `docker compose config --quiet` with isolated port overrides | PASS |
| Published host ports | PASS; API 58000, PostgreSQL 55439, Redis 56390, MinIO 59023/59024, ClamAV 53313, Firebase Auth 9099 |
| `alembic upgrade heads` on the isolated empty PostgreSQL volume | PASS; migration service exited 0 |
| Parent seed first run | PASS; account, identity, profile/authorization, and lesson created |
| Parent seed second run | PASS; each existing seed row was reported as `existing` |
| Aggregate row counts after the second seed | PASS; parent identity 1, profile 1, profile revision 1, synthetic authorization 1, seeded lesson 1, version 1, activities 3, public grant 1 |
| Firebase Auth Emulator password sign-in | PASS; token was kept in process memory and not logged |
| `GET /api/auth/v1/me` | PASS; role `parent` |
| `GET /api/parent/v1/child-profiles` | PASS; one profile, authorization `GRANTED`, current policy true |
| `GET /api/parent/v1/consent-policy` | PASS; local synthetic policy version returned |
| `GET /api/billing/v1/video-quota` | PASS; `LOCAL_DEMO`, granted 5, used 0, available 5 |
| Parent lesson catalog/detail APIs | PASS; one public lesson, three activities, immutable version available |
| `GET /api/parent/v1/story-runs/active/current` | PASS; authenticated Parent receives own active-run response |
| API `GET /health` | PASS; HTTP 200 |
| Expo public config | PASS; resolved Firebase App ID matches root `.env`, API URL is `http://10.0.2.2:58000`, Auth Emulator URL is present |
| Targeted Parent activity service/worker contract tests | PASS; 28 passed |
| Punctuation-free fragment fields | PASS; `materials_text` and `observation_notes` accepted |
| Incomplete core sentence fields | PASS; service gate and worker parser reject incomplete `objective`, `preparation_text`, `instructions_text`, and `safety_notes` |
| Modal startup sidecar | PASS; app deployed, one `GET /health`, `health_request_count=1`, `inference_ready=false`, `gpu_allocated=false` |
| Modal provider setting in API container | PASS; `modal_dev` |
| Video | NOT CALLED |
| Model inference | NOT CALLED; this was deliberate. The sidecar health endpoint does not claim model readiness. |

The Compose API and supporting services were left running for local use. The dedicated health app is stopped when this Compose project is shut down; only that app is managed by the sidecar.

## Timings observed

- Modal health-app deployment: 2.241 seconds on the final restart (the earlier deploy was 2.469 seconds).
- Compose startup command: about 15 seconds initially; a later full restart completed in about 20 seconds after using the root `.env` explicitly from the worktree.
- Second seed invocation: about 4 seconds.
- Auth sign-in and Parent role/profile/policy/quota/catalog reads: about 5 seconds.
- Parent lesson detail read: about 4 seconds.

These are local run timings, not a latency or GPU availability guarantee for model inference.

## Limits and follow-up

- No Modal model inference was invoked. The targeted parser/gate tests pass, but Qwen3.5 weights and CUDA kernels on a remote worker, remote catalog selection, generated fallback quality, and end-to-end activity AI are not live-verified in this run. Startup's health check intentionally reports `inference_ready=false` and uses no GPU.
- No Android device/UI interaction was run. Expo configuration was evaluated with the actual Expo CLI, but the rendered Parent app and Google Sign-In UI were not exercised.
- TypeScript checking previously reported `process.env.EXPO_PUBLIC_API_URL` typing errors in existing API config/demo files; this task did not expand into those unrelated paths.
- Local quota is display-only and does not create or charge Billing rows. Synthetic authorization is not legal consent. Real-child processing remains gated by the canonical SRS and owner/legal policy.
- Video generation and all video endpoints remain untested and were not called.
