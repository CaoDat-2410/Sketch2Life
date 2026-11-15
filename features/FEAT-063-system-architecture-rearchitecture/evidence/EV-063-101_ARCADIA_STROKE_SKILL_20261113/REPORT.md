# EV-063-101 — Arcadia SVG reference and stroke-authoring skill

**Date:** 2026-11-13<br>
**Plan:** Rev87.4, owner-approved defaults; this report records an incomplete runtime attempt.<br>
**SRS:** FEAT-063 v2.7-draft Rev69 as routed by `docs/context/SRS_AUTHORITY.md`; unsigned. No target requirement in §§1–31 was changed.

## Result

The source and authoring approach are implemented locally. The original Rev87.4 deployment failed before app update due to a Windows remote-path format. Rev87.5 then authorized one additional attempt; that Modal CLI command exited with a Windows `charmap` encoding error during image build log output, with no deployment success confirmation. Rev87.5 was stopped without a Modal health call, GPU inference, or Parent UI request. Whether Modal applied any part of the deployment is **unknown**. The generated chicken guide quality is **not verified**; no generated SVG, JSON response, or screenshot exists.

## Dataset source

- Arcadia Science, *Free Organism Illustration Library v1.0*, Zenodo DOI `10.5281/zenodo.17203578`, declared CC0-1.0.
- Downloaded archive size: `41,184,246` bytes. Published and verified MD5: `a845bf16730238334f39c7cfbc1d4703`.
- Selected archive member: `2025 Zoogle organisms/Tricolor + stroke SVGs/Gallus-gallus-tricolorstroke.svg`.
- Preserved SVG size: `24,251` bytes; SHA-256: `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`.
- Only this source SVG and its provenance record are packaged. The archive, unrelated organisms and raster images were not added. The asset is a visual/anatomical reference, not a stroke-order dataset.
- The original SVG contains vector paths and no script, image, external href, CSS `url()`, DTD or entity reference in the inspected source.

## Skill and code

- Installed upstream `iart-ai/explainer-video-skills/skills/whiteboard-animation`, version `0.1.0`, into `.agents/skills/whiteboard-animation/`; preserved its two references and added the upstream MIT license/provenance.
- The skill is an authoring reference, not a Modal runtime service. Its open-path, one-pen-action-per-path, human draw-order and progressive reveal rules are applied in the Qwen prompt and backend topology gate.
- The Modal worker now packages the selected SVG and manifest, verifies its pinned SHA-256, rasterizes it in memory with CairoSVG `2.7.1`, and passes the image to Qwen3.5 only for matching chicken topics. Other topics do not receive the chicken image. Generated response provenance is typed and shown in Parent/Teacher previews; the guide remains a private, unpersisted adult-reviewed draft.
- The backend adds a chicken anatomy topology gate for body, neck, head, beak, comb, wing, tail and two grounded legs. No parser limits were relaxed.

## Verification and runtime attempt

- Archive checksum, selected-file SHA-256, Python source syntax and the two JSON files: **PASS**.
- Teacher UI production build: **PASS**.
- Parent UI typecheck: **BLOCKED** by existing missing `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_FIREBASE_API_KEY`, `EXPO_PUBLIC_FIREBASE_PROJECT_ID`, `EXPO_PUBLIC_FIREBASE_APP_ID` and `EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL` declarations in `apps/ui-mobile/src/config/env`; the changed SVG types/screen produced no reported TypeScript error before those project-wide failures.
- Local Docker API `/health`: HTTP 200. Its currently running image does not expose `/api/parent/v1/ai/sketch-guides`; the OpenAPI route check returned false. No Parent AI route request was sent.
- The existing Modal dev app was listed as deployed before the attempt. `python -m modal deploy deployment/modal/srs_v23/language_audio_app.py --env dev` failed before deployment with `modal.InvalidError: image.add_local_file() currently only supports absolute remote_path values`. On Windows, converting `Path("/root/...")` produced a non-POSIX path. The local source was corrected to use literal POSIX remote-path strings afterward; it was not redeployed under this plan.
- No Modal `/health`, worker, inference, Android UI or emulator request was made. No database migration, `.env` edit, account creation, fixture response, warmup, FLUX, video or test suite was run. Existing Docker API/ClamAV containers were left untouched; the Modal health sidecar was not started because its current startup registry sends worker warmup requests.

## Rev87.5 bounded retry — 2026-11-13

- **Approved plan:** `plan/PLAN_REV87_5_CURATED_SVG_MODAL_RETRY_20261113.md`; final approved SHA-256 `94547CEC22E0638788358EEEE8DAFBD304D3BF49837DC9CA246CE0DB7D3BF155`.
- Preflight found the existing Modal dev app deployed. Root `.env` presence and required key names were checked without printing values. The live synthetic `rev79-parent-local-20261112` PostgreSQL/Firebase Auth stack remained untouched; its Postgres Alembic head was `20261110_parent_lesson_pin`.
- A temporary API image was built from the current worktree and served on port 8001 in the existing Rev79 network. Docker health checks returned HTTP 200. The mounted Parent guide path returned 405 to an unauthenticated GET (route is present); `/openapi.json` returned 500 because `SVG catalog contract` is absent from runtime OpenAPI components. No authenticated route call was made.
- An initial attempt to start the default `sketch2life` PostgreSQL/Firebase services failed because host port `127.0.0.1:55439` was occupied by the already-running Rev79 Postgres. A Firebase container created in `Created` state was removed without deleting its volume; `sketch2life-postgres-1` remains `Created` and inactive after Compose recreation, with its volume preserved. The original `sketch2life-api-1` was not replaced. The temporary API process was stopped and auto-removed; its local image remains cached.
- One Modal deploy command ran for 16.107 seconds and exited 1. Modal emitted image-build logs, then the Windows console failed with `'charmap' codec can't encode characters in position 3-42`. The deploy result is unknown; no status/health call was made after failure, as required by the stop rule. No GPU worker inference was requested.
- Parent Expo UI was not started; no login, consent, AI POST, generated SVG/render, or screenshot occurred. No migration, seed, account creation, `.env` edit, test suite, video, FLUX or child data was used. Existing Rev79 services and `sketch2life-api-1` remain untouched.
- The one-attempt allowance is consumed. A further deploy/health/inference requires a new written plan and explicit approval; likely runtime correction is to force UTF-8 for Modal CLI output, then separately address the OpenAPI schema gap if the UI depends on it.

## Rev87.6 Android Parent UI attempt — 2026-11-13

- **Approved plan:** `plan/PLAN_REV87_6_OPENAPI_AND_MODAL_UTF8_FIX_20261113.md`; final approved SHA-256 `20DABC39EDEF01959FFFF26B72344C8DB2662E9243216005D20F3933718AC8E2`.
- Both changed OpenAPI modules compiled in the temporary API container. Local API `/health` and `/openapi.json` returned HTTP 200. OpenAPI contained the Parent sketch-guide route and all 12 SVG catalog operations with concrete response schemas and 200/201 success statuses.
- Built/bundled the real Expo Android app for Pixel_10 (`Android Bundled 11777ms`, 949 modules), installed and launched it, and connected it to the temporary API and Firebase Auth Emulator. Sign-in succeeded after correcting an incomplete first UI text entry; no backend request was made by that failed sign-in. The synthetic Parent profile loaded with current authorization/consent.
- The account already had an open run. Resuming it showed: “Buổi đang mở chưa có dữ liệu đủ để khôi phục màn tiếp theo. Không tạo buổi mới để tránh trùng.” The UI therefore could not reach topic/guide. No run/profile/consent was created, deleted or changed. The plan's stop gate was applied; there was no Modal deploy, Modal health call, GPU inference, generated JSON/SVG, or guide render.
- Captured the actual Android auth, home and resume-blocked screens in `screenshots/`. Stopped Metro, removed only the temporary API container, and shut down the Pixel_10 emulator. Shared PostgreSQL/Firebase Auth remained untouched; `.env` was not edited.
- Exact runtime details: `runtime-attempt-3.json`. This is an Android/UI resume-state blocker, not evidence of an SVG-generation or Modal worker failure. A future attempt needs a separately approved way to recover/use a clean synthetic Parent workflow without deleting or bypassing an existing run.

## Rev87.9 — real Android Parent flow with Modal AI — 2026-11-13

**Outcome: PARTIAL; the tested real flow stopped before story inference.** This run used the approved Rev87.9 plan, a newly created synthetic Parent identity/profile through the actual Android UI, the current-worktree API in a temporary Docker container, Firebase Auth Emulator, and real Modal Qwen3.5 workers. No fixtures, seeded records, direct activity injection, migration, video, FLUX, or retry were used. The FEAT-063 v2.7-draft Rev69 target remains unchanged and unsigned.

### Stage results

| Stage | Result | Timing / evidence |
|---|---|---|
| Signup and Firebase Auth Emulator | PASS | Parent registration HTTP 201; sign-in succeeded. Credentials and tokens were not recorded. |
| Synthetic profile and local notice | PASS | UI-created synthetic profile, 84 months, animal interest. No legal consent or real-child data was used. |
| Optional topic / lesson | PASS | Entered `con ga` because Android adb text entry did not preserve Vietnamese diacritics; no lesson was pinned. |
| Optional SVG guide lookup | FAIL, then skipped in UI | Two catalog lookups returned `DATABASE_UNAVAILABLE`. Read-only inspection found the shared DB at Alembic `20261110_parent_lesson_pin` without `core_svg_catalog_assets`, `core_svg_catalog_guide_revisions`, or `core_svg_catalog_reviews`. No migration was run. No guide inference, SVG response, or render exists. |
| Mandatory drawing upload and context confirmation | PASS | Generated synthetic chicken drawing selected through Android's gallery and confirmed through the real UI. Source gallery image SHA-256: `67BC81722774315984980F3AAFEE05D885F86D6C3F67C13D38732A50DF541855`; worker-verified request asset SHA-256: `63aa479fd3bc6be0bfedbb5577a671ffad4b867d84458bae63fa0faab92d868d` (the picker/upload path re-encoded the selected asset). |
| Qwen3.5-VL drawing analysis | PASS | HTTP 200; 38.191 s end-to-end. Modal call `fc-01M7A527SPGTG5XWAVG6SZ4KRH`; model revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. It returned `con gà`, confidence 0.90, `NEEDS_ADULT_CONFIRMATION`; the adult confirmed it in the UI. Actual model output: `drawing-analysis-response.json`. |
| Catalog-first activity suggestions | TECHNICAL PASS; product-quality/selection FAIL | HTTP 200; 121.894 s end-to-end, worker wait 120.355 s. Catalog supplied two butterfly candidates for a chicken image/topic. Qwen returned `NO_MATCH` and three fallback drafts. The Android screen had no activity-selection control; accessibility inspection found no selectable activity node. One draft recommends small grains/beans despite a supervision warning; the current gate allowed it. Actual model output: `activity-selection-response.json`. |
| Story request | BLOCKED, HTTP 422 before inference | The actual UI's `Tiếp tục đến kịch bản` action sent one request, then stopped. Initial story contract requires both `primary_activity_request_id` and `primary_activity_ref`; `ParentApi.generateStory` sends only `expected_understanding_revision`, and the activity screen has no selector. FastAPI rejected the body before the handler/provider call. No activity ID was injected and no Modal story call was made. UI screenshot: `screenshots/android-parent-story-error.png`; observed response record: `story-generation-http-422-observation.json`. |
| Story confirmation / video | NOT REACHED / NOT RUN | No story was generated or confirmed. Video remained excluded by plan. |

The two successful GPU calls used Qwen/Qwen3.5-9B, pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; neither timed out or retried. The missing terminal-event telemetry persisted: API wait summaries reported `worker_started_without_terminal_event` and no output hash for successful drawing/activity results. The returned Modal call results were retrieved and saved, but the diagnostic inconsistency remains open.

### Defects exposed

1. **SVG catalog schema is not migrated in the shared development database.** The optional Parent guide appears as unavailable even though the API health check is green; its route reports a generic `DATABASE_UNAVAILABLE`. The test correctly skipped the optional step rather than changing shared schema.
2. **Activity selection is missing from the real Parent UI and request adapter.** The UI can display fallback cards and continue, but cannot choose/persist the mandatory primary activity required by the story API and FEAT-063 BR-08, BR-15, FR-P-05 and FR-P-13. This is the immediate end-to-end blocker.
3. **Catalog matching/content quality need work.** The two available catalog candidates were both butterflies; fallback produced three chicken drafts, including one with a small-object choking exposure despite a warning. The backend response passed technical parsing, but this is not a content-quality approval.
4. **Worker diagnostics are misleading after successful inference.** The API summary recorded no terminal event or output hash although the actual calls returned model output.
5. **Capture UI state appears stale.** The selected photo was visible on the Parent preview while the “Cần có ảnh” notice remained. The continue action still worked; record for UI follow-up.

### Modal setup and cleanup

The existing language-audio app was reused. The drawing/VLM app was deployed once from the current worktree (101.473 s) and received one CPU-only `/health` call (HTTP 200, `gpu_allocated=false`, `inference_executed=false`). No warmup inference or minimum-container setting was added. Exactly two authenticated GPU inference calls were made: drawing analysis and activity suggestions. The story request did not reach Modal.

After evidence capture, the task-started Metro session was stopped, temporary `rev87-9-parent-api` container was removed, and `emulator-5554` was shut down. Shared Postgres, Firebase Auth Emulator, Redis, MinIO, ClamAV, Modal apps and model volume were left untouched. `.env` was not edited. No migration, seed, source change, test suite, commit, or push was performed. The exact runtime record is `runtime-attempt-4.json`; all actual Android screens are in `screenshots/`.

### Required follow-up before another full-flow claim

- Apply and verify the additive SVG catalog migration in a separately authorized test database, then verify Parent guide lookup/render from the actual UI.
- Implement primary activity selection/persistence in Parent UI and send the pair of IDs required by the story request contract; ensure AI fallback drafts are treated as drafts and reviewed for child safety.
- Fix API worker terminal-event/output-hash reconciliation, then separately authorize one story inference and adult confirmation. Do not infer video readiness from this partial run.

## Rev87.5 stop note (historical)

At the time Rev87.5 ended, its single deploy retry was consumed and no follow-up Modal health/inference was authorized. That stop note was superseded by the separately approved Rev87.9 runtime plan above. The earlier Rev87.5 state remains “deployment outcome unknown”; it is not evidence for the Rev87.9 worker deployment or outputs.

## Rev87.10-A — Parent optional SVG guide attempt — 2026-11-13

**Outcome: STOPPED BEFORE MODAL INFERENCE.** The Parent Android UI reached the optional progressive SVG guide using the generic topic `Con ga`. The catalog-first lookup and the subsequent AI-draft request were both rejected by backend authentication. No SVG was generated or rendered, and no Modal call or GPU inference was made for this amendment.

| Stage | Result | Evidence |
|---|---|---|
| Task API preflight | HTTP 200 `/health`; the Parent sketch-guide POST route is present in OpenAPI. | Task container `rev87-10-parent-api`, port 18001. |
| Catalog-first lookup | HTTP 401 `INVALID_IDENTITY_TOKEN` before database access. The temporary API initially used fallback Firebase project `sketch2life-local`; the existing app/Auth Emulator use `sketch2life-dev`. | `screenshots/parent-svg-catalog-result.png`; task API access log. No catalog result was obtained. |
| Task API correction | Recreated only the task API with `SKETCH2LIFE_FIREBASE_PROJECT_ID=sketch2life-dev`, `SKETCH2LIFE_SVG_TOPIC_STROKE_GUIDE_GENERATION_ENABLED=true`, and the already approved soft activity gate setting. `/health` remained HTTP 200. No `.env`, shared service, database, or Modal app was changed. | Runtime task configuration; see `runtime-attempt-5.json`. |
| Parent UI fallback | PASS. The catalog error remained visible and the UI exposed “Tạo bản nháp SVG bằng AI” without requiring another catalog request. | `screenshots/parent-svg-auth-failure.png`. |
| AI draft POST | HTTP 401 `INVALID_IDENTITY_TOKEN` even after the task API used `sketch2life-dev`. The API verifier suppresses its underlying provider details, so the exact token claim/signature/expiry failure is unknown. Request was rejected before Modal dispatch; call ID is absent. | UI correlation ID `parent-expo-mweywacb`; task API returned 401. No response SVG/JSON exists. |
| SVG validation and rendering | NOT REACHED. No model output existed to pass through the strict sanitizer/guide gates or the renderer. | No output artifact. |
| Story/video | NOT RUN. The earlier activity request returned HTTP 502 without a candidate; no activity was fabricated and no story request was sent. | Activity Modal call `fc-01M7ADJ06FW4F14C4J9QNWP6HJ`; its worker stopped at `model_inference` without a terminal event/output. |

The Android Parent fallback bug was fixed locally: after a catalog failure, the screen now marks that lookup attempt complete, preserves the error, and permits the explicit AI-draft fallback. Focused mobile test: **4 passed**. This does not fix Firebase token verification or establish an SVG generation result. The project-ID mismatch was corrected in the task container, but the following SVG POST still failed authentication; do not report the project mismatch as the complete root cause.

Two earlier GPU inference calls in this combined task were attempted (drawing analysis and activity suggestions); the SVG GPU slot remained unused. There was no SVG retry, Modal deployment/health request, video, migration, seed, or `.env` edit. The task API container, Metro and Pixel_10 emulator were stopped; shared Postgres, Firebase Auth Emulator, Redis, MinIO and ClamAV remained running. Screenshots and the structured record are in `screenshots/` and `runtime-attempt-5.json`. Rev87.10-A is partial and stopped at the approved API-failure gate.


## Rev87.10-B/C — Parent Firebase Auth correction and one SVG attempt (2026-11-13)

**Outcome: AUTH FIX VERIFIED; SVG GENERATION FAILED IN THE WORKER.** This used the existing synthetic local Parent identity, the root `.env`, the running Firebase Auth Emulator, a task API built from the current worktree, and one authenticated real Parent API request. It did not use Android UI because Android SDK/`adb` and an emulator device were unavailable in the checked machine paths. No fixture output was used.

| Stage | Result | Evidence |
|---|---|---|
| Existing API configuration diagnosis | **Root cause found.** The stale `s2l-parent-e2e-20261111-api-1` container had project `sketch2life-dev` but `FIREBASE_AUTH_EMULATOR_HOST` was unset. It therefore lacked the Admin SDK emulator-verification mode needed for emulator-issued tokens. Current `compose.yaml` already declares `FIREBASE_AUTH_EMULATOR_HOST=firebase-auth:9099`; no source code or `.env` change was needed. | Allowlisted `docker inspect` of project/provider/emulator settings only; no secret values were read. |
| Correct task API | **PASS.** Built from this worktree, attached to the existing Rev79 network and started from the one root `.env`; API health HTTP 200. Runtime had project `sketch2life-dev`, emulator host `firebase-auth:9099`, Firebase provider, and `check_revoked=true`. SVG capability was enabled only in this task container. | Container `rev87-parent-authfix-20261113-api-1`, host port 58000. |
| Firebase Auth Emulator sign-in | **PASS.** Existing local seed identity returned HTTP 200 and issued a fresh ID token held only in process memory. No account was created or changed; no credential/token/UID/email was printed or recorded. | `runtime-attempt-6.json`. |
| Authenticated Parent `/api/auth/v1/me` | **PASS.** HTTP 200, role `parent`, state `active`. Signature, issuer, revocation, role and consent policy were not bypassed; no verifier code change was required. | Same fresh emulator token and task API, `runtime-attempt-6.json`. |
| Parent SVG catalog | **FAIL, HTTP 503 `DATABASE_UNAVAILABLE`.** The shared DB still lacks the SVG catalog/review schema. No migration was run; no catalog item count was obtained. | One read-only GET; runtime record. |
| Parent SVG draft API | **FAIL, HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`; 820.282 s end-to-end.** The authenticated request sent only generic topic `con gà` and `beginner`. Modal call `fc-01M7AGHYQ0DH0Q65V3EW079BRB`; job `4df2bb9c587711b6`, generation `a66fe24bf6e51dc8`, attempt `3fe86e83c6b2319d`. | One real API request; no retry or direct worker call. |
| Modal Qwen3.5 worker | **Terminal failure**, not auth or timeout. Model `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; worker duration 805.853 s, model load 32.320 s, inference 766.801 s. Failure at `output_parse_and_contract_validation`, `SVG_TOPIC_GUIDE_PATH_INVALID` (`RuntimeError`). GPU class recorded by Modal: `L40S|L4|A10`. | Structured Modal worker logs, 26 events; safe stage/error metadata stored in `runtime-attempt-6.json`. No valid SVG output or rendered image was returned. |
| Worker diagnostic reconciliation | **Telemetry gap observed.** At API failure time, `summarize_worker_call_logs` reported `worker_started_without_terminal_event` and last stage `model_inference`. A later read-only `FunctionCall.from_id` log query found the terminal `worker_failed` event and path error above. | Same Modal call ID; no additional inference. |
| Android UI / screenshots | **NOT RUN.** No Android SDK/`adb` executable or emulator device was available. The CUA inventory found Android Studio installed but not an emulator. No screenshot is claimed for this attempt. | Execution fallback Rev87.10-C. |

The 401 is fixed when the API is started with the current Compose configuration: a fresh Auth Emulator token now authenticates and resolves the active Parent role. The stale API container on port 18000 was not modified; it still lacks the emulator-host setting. The corrected task API is running on port 58000, matching the root `.env` mobile API URL. Recreate any API instance that still returns `INVALID_IDENTITY_TOKEN` from the current `compose.yaml` so it receives `FIREBASE_AUTH_EMULATOR_HOST`.

The SVG attempt consumed its one approved GPU inference. It did not return a validated draft, so there is no SVG asset or screenshot to review. A further SVG attempt or worker change needs a separate bounded plan/approval. No story, video, migration, seed command, account/profile mutation, `.env` edit, Modal deploy/warmup, shared-service stop, commit or push occurred. Shared Docker services remained running. Detailed safe trace: `runtime-attempt-6.json`.


## Rev87.10-D — repair Parent SVG catalog database (2026-11-13)

**Outcome: PASS.** Applied the exact approved Alembic revision to the existing local development PostgreSQL database used by the task API. No AI/Modal request was made.

| Check | Result |
|---|---|
| Before revision | `20261110_parent_lesson_pin` |
| Missing schema | `core_svg_catalog_assets`, `core_svg_catalog_guide_revisions`, `core_svg_catalog_reviews` were all absent. |
| Existing data preflight | `core_asset_metadata` had 14 rows; all 14 satisfied the new owner-scope check. No row content was read or printed. |
| Migration | `alembic upgrade 20261113_svg_catalog_review` completed transactionally. No `upgrade heads`; unrelated Alembic heads were left untouched. |
| After revision | `20261113_svg_catalog_review`; all three tables exist; owner-scope check is validated; two immutable triggers exist. Existing `core_asset_metadata` row count remains 14. |
| API verification | `/health` HTTP 200. Existing synthetic Parent authenticated through Firebase Auth Emulator; `GET /api/svg-catalog/v1/parent/guides?topic_key=con-ga&limit=50` returned HTTP 200 and contract `SvgGuideCatalogPageV1` with 0 items. |
| Data/AI | No seed, fixture, row mutation, account/profile/consent change, Modal call, video, or retry. |

The `DATABASE_UNAVAILABLE` catalog failure is resolved for the current database. The catalog is empty, so no approved guide is available yet; no demo assets were seeded. A new bounded Parent SVG attempt is recorded under Rev87.10-E below. The task API remains healthy on port 58000. No `.env` edit, shared-service restart, commit, push or merge occurred. Full migration record: `runtime-attempt-7.json`.


## Rev87.10-E — real Parent SVG guide request after database repair (2026-11-13)

**Outcome: FAILED IN MODAL OUTPUT PARSING; no validated SVG was returned.** This was one authenticated Parent API request after the catalog migration, with the existing local synthetic identity. No fixture or child data was supplied.

| Check | Result |
|---|---|
| Task API | `/health` HTTP 200 on port 58000. Read-only Modal lookup confirmed the deployed `generate-topic-svg-stroke-guide-draft` function. |
| Auth | Firebase Auth Emulator sign-in HTTP 200; token stayed in process memory. |
| Catalog-first | `GET /api/svg-catalog/v1/parent/guides?topic_key=con-ga&limit=50` returned HTTP 200 with 0 items. |
| Parent SVG API | One `POST /api/parent/v1/ai/sketch-guides`, topic `con gà`, beginner; HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`, 223 seconds end-to-end. |
| Modal call | `fc-01M7AKKGC21Z4HFMGX8KYRCJ10`; Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; terminal stage `output_parse_and_contract_validation`; worker duration 212,954 ms. |
| Exact failure | `SVG_TOPIC_GUIDE_PATH_INVALID` (`RuntimeError`). The worker parser rejects a path when its strict path-field checks fail. Those checks include exact fields, unique safe path IDs, supported path-data characters/length, `fill: none`, six-digit hex stroke, width 1.5–10, unique path geometry and a consistent stroke color. The worker intentionally did not log raw model output, so logs do not identify which individual field failed. |
| Output/retry | No validated response, SVG file, rendering or screenshot. No retry or second inference. |

This was a terminal parser/contract failure, not an authentication, database, or request-timeout failure. The likely defect is the generated SVG path contract mismatch; the exact offending value is unavailable because raw model output is not retained. Fixing the worker prompt/parser and attempting another inference requires a new bounded approval. Safe structured trace: `runtime-attempt-8.json`.


## Rev87.10-F/G/H — Parent SVG decoder and final runtime attempt (2026-11-13)

**Outcome: DECODER CRASH FIXED; SVG GENERATION STILL FAILS.** The real Parent request passed auth and catalog preflight and reached Qwen3.5. The constrained decoder now initializes and starts generation, but the worker output was rejected as invalid JSON. No SVG/PNG/render was produced. Rev87.10-H's one final inference allowance is consumed; no retry was made.

### Worker change and verification

- The first Rev87.10-F/G attempt (Modal call `fc-01M7AP59BDGMX83146DPZQM6F1`, request `55d6e393-a356-446c-a78b-770e61c30050`) failed during `model_inference`: inference-stage duration was 38.044 seconds and total worker duration was 60.136 seconds. The error was `LMFormatEnforcerException`: `path_id` and `d` schemas combined `pattern` with `minLength`/`maxLength`, which pinned `lm-format-enforcer==0.11.3` does not support. Full safe trace: `runtime-attempt-9.json`.
- Removed only those redundant length keywords from the two patterned schema fields. Their ASCII/path-command regex patterns remain, and the worker parser retains its 96-character ID and 1–4096-character path-data checks. No SVG validation or quality gate was weakened.
- Focused tests in the Modal health-sidecar image: **4 passed**. Worker `py_compile`: **passed**.
- Deployed `language_audio_app.py` once to `sketch2life-srs23-language-audio-dev` (`dev`) through the already-authenticated sidecar; Modal reported deployment complete in 8.442 seconds. The temporary copied source directory was removed afterward.

### One real Parent API request

| Stage | Result |
|---|---|
| API health | HTTP 200 |
| Firebase Auth Emulator sign-in | HTTP 200; existing synthetic Parent identity, credentials/token kept out of files/logs |
| Authenticated `/api/auth/v1/me` | HTTP 200 |
| Parent SVG catalog | HTTP 200, zero approved guide items; no fixture was inserted |
| Request | One `POST /api/parent/v1/ai/sketch-guides`, generic `con gà`, `beginner`; no profile, artwork, audio or child data |
| Modal | `fc-01M7AQ14QMS06Z00GR5P8X17AH`; job `e84050b6fe28c7a6`, generation `6c69240b3016dabd`, attempt `fba5c1b03246daf7` |
| Model | `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Decoder | `constrained_decoder_setup` passed in 3.677 seconds; the previous `LMFormatEnforcerException` is resolved |
| Generation | `model_inference` completed in 364.985 seconds; total Modal worker duration 388.003 seconds |
| Terminal failure | `output_parse_and_contract_validation`, `SVG_TOPIC_GUIDE_JSON_INVALID` (`RuntimeError`); API logged HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`, request ID `cda21ec2-0531-4025-b637-bd7228e193fc` |
| Client observation | The Node API caller surfaced `TypeError` after 307.345 seconds before receiving the server's terminal response; exact transport cause was not captured. The backend/Modal call continued and logged the terminal 502 at 15:11:21 UTC. |
| Output | No validated response JSON, SVG artifact, image render or screenshot; raw model output was not logged. |

The exact invalid JSON cause cannot be separated from truncation using current telemetry. Source review found the worker calls `_parse_svg_topic_stroke_guide(text)` **before** checking whether generation reached EOS or hit `max_new_tokens=6144`; truncated output can therefore be reported only as `SVG_TOPIC_GUIDE_JSON_INVALID`. A future bounded fix should check EOS/token truncation first and record safe token-count/EOS diagnostics, then separately address generation format/latency. The current real attempt is not a successful SVG result.

The first PowerShell preflight had a local system-proxy issue; a direct loopback health check with proxy disabled returned 200. That probe did not dispatch AI. The single GPU inference above is the only inference in Rev87.10-H. No fixture, retry, warmup, story, video, gate relaxation, seed, `.env` edit or database mutation occurred. No commit/push was made. Full safe record: `runtime-attempt-10.json`. The Modal function is deployed but configured with `min_containers=0` and a 120-second scale-down window; this run did not request an additional warmup.

## Rev87.10-I — diagnose one final Parent SVG attempt (2026-11-13)

**Outcome: diagnostics now distinguish truncation; the SVG guide still does not generate.** The worker checks EOS/token-cap completion before parsing and emits safe token/EOS diagnostics; the backend log summarizer accepts only the SVG workload's allowlisted event fields. No model output text is logged.

### Focused checks and deployment

- Modal worker contract tests: **6 passed**; worker `py_compile`: **passed**.
- Backend safe worker-log-summary regression: **passed** against the amended client source. It preserves safe counters/error location and excludes a deliberately supplied `generated_text` field.
- Deployed `language_audio_app.py` once to `sketch2life-srs23-language-audio-dev` in `dev`; Modal completed in 10.747 seconds. Modal applied the file's full language/audio function set; no request was sent to its other functions, and the drawing/VLM and video/FLUX apps were not deployed or invoked. Only the existing task API container was rebuilt/recreated. Its post-recreate `/health` returned HTTP 200; shared Postgres, Firebase Auth Emulator, Redis, MinIO and ClamAV were not restarted.
- The task API remains healthy on port 58000. Compose created five project-scoped volumes while processing the `api` service despite `--no-deps`: `rev87-parent-authfix-20261113_sketch2life-clamav-database`, `..._sketch2life-firebase-auth`, `..._sketch2life-firebase-cache`, `..._sketch2life-minio`, and `..._sketch2life-postgres`. No running container uses them; they were left untouched.

### One real Parent API request

| Stage | Result |
|---|---|
| API health | HTTP 200 |
| Firebase Auth Emulator sign-in | HTTP 200; synthetic adult credentials and token remained in process memory |
| Authenticated `/api/auth/v1/me` | HTTP 200; Parent role confirmed |
| Parent SVG catalog | HTTP 200; zero approved `con-ga` guide entries |
| Request | Exactly one `POST /api/parent/v1/ai/sketch-guides`, generic `con gà`, `beginner`; no child profile, drawing, photo, audio, story or video |
| API result | HTTP 502 `MODAL_WORKER_FAILED_TERMINAL`, request `5a6b5e49-bfb0-4b23-a03e-2e29295247d0`, 395.670 seconds end-to-end |
| Modal call | `fc-01M7AVABJR7AVEJS9F89B19ZDM`; Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Model/GPU startup | Model load 17.459 seconds; constrained decoder setup 3.483 seconds; worker was configured for `L40S|L4|A10`. The terminal event did not identify which GPU was allocated. |
| Exact worker failure | `MODAL_SVG_TOPIC_GUIDE_OUTPUT_TRUNCATED` at the post-generation EOS/token-cap check. Generation used all 6,144 allowed output tokens, did not end with model EOS, and decoded to 6,534 characters; model inference took 361.621 seconds and total worker duration was 384.513 seconds. |
| Output | No validated Parent response or SVG was returned; no render file was created. No retry or second inference. |

This is now an identified **output-budget/truncation** failure rather than an unknown JSON parse failure, cold-start timeout, auth, catalog, or decoder-setup failure. The worker completed model loading and inference; its generated response reached the fixed token ceiling without EOS. Raw generated content is intentionally unavailable, so the evidence cannot say whether a larger output budget alone would produce a valid guide. The one inference authorized by Rev87.10-I is consumed; another prompt/token-budget change, deployment or inference needs a new bounded plan and approval.

The Modal app remains deployed. The worker is configured with `min_containers=0` and a 120-second scale-down window; no explicit warmup or shared-app stop was issued. Safe counters and call details: `runtime-attempt-11.json`. No `.env`, credentials, account, profile, consent, database rows, fixtures, or product SRS target sections were changed; §§1–31 remain unchanged.


## Rev87.10-M/N/O/P — Parent chicken SVG geometry diagnosis and bounded fix (2026-11-14)

**Outcome: worker/parser and request timing are healthy; the generated chicken SVG still fails backend anatomy gates.** The prompt was tightened in bounded revisions to require a sufficiently large body, unique geometry for each part, a visible beak, and grounded legs. The backend now reports body-shape failure separately from connection failure. Hard topology and safety checks were not weakened. The final P request completed in about 253 seconds under the existing 1,800-second deadline, then returned HTTP 502 because the actual SVG geometry remained disconnected/incomplete. This is not a timeout.

### Local checks and bounded deployment

- Rev87.10-P focused SVG worker/LMFE contract tests: **10 passed**; worker `py_compile`: **passed**; focused backend chicken-topology tests in the API container: **2 passed**; `git diff --check`: **passed** for the scoped worker/test edits.
- One deployment of `sketch2life-srs23-language-audio-dev` completed (about 8.250 seconds). The final call reused the healthy task API on port 58000. Health, Firebase Auth Emulator sign-in, authenticated Parent `/me`, and catalog preflight passed; the catalog contained zero approved `con-ga` guides.
- Two earlier preflight-only requests did not dispatch a worker: attempt 16 was rejected as `CAPABILITY_DISABLED` (HTTP 503, 2.208 seconds) because a Compose feature flag was absent; attempt 17 returned `MODAL_OUTCOME_UNKNOWN` (HTTP 504, 2.497 seconds) from Modal `AuthError` with no call ID because that worktree invocation omitted the root `.env`. Both runtime-only configuration causes were corrected; no credential value was printed or recorded.

### Geometry attempts

| Amendment / attempt | API result | Worker result | Diagnosis |
|---|---|---|---|
| M / 15 | HTTP 502 in 263.834 s | Qwen3.5 inference 221.568 s; worker 247.983 s; 9 paths, 9 parts, 8 stages; parser passed | `SVG_CHICKEN_ANATOMY_CONNECTION_INVALID` was then a combined diagnostic. Safe in-memory checks isolated the body minimum-height check as false; body width/aspect and bbox overlaps were true. |
| N / 18 | HTTP 502 in 375.878 s | Inference 317.372 s; worker 356.531 s; complete EOS-terminated JSON; parser rejected after 32 ms | `SVG_TOPIC_GUIDE_PATH_DUPLICATE_GEOMETRY`; all 9 paths had not yet been made geometrically distinct. No raw output was retained. |
| O / 19 | HTTP 502 in 244.770 s | Inference 207.062 s; worker 230.224 s; 2,820 output tokens; 9 distinct paths, 8 stages | `SVG_CHICKEN_BEAK_CONNECTION_INVALID`. Safe checks showed beak start and body/part overlaps passed, but beak length was below 12 units and both legs rose no more than 40 units. |
| P / 20 | HTTP 502; request `353fcb85-1fae-4b41-b584-3a2ef468b6fe`; about 253 s from first dispatch log | Modal call `fc-01M7B5C1W8JNVY4061Z2Y7ZKKQ`; Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; inference 212.486 s; worker 240.556 s; API wait 247.307 s; parser passed; 2,878 output tokens; 9 paths, 9 parts, 8 stages | `SVG_CHICKEN_ANATOMY_ENDPOINT_DISCONNECTED`: neck does not end inside the head bounds. The beak still fails the 12-unit minimum and both legs still fail the >40-unit descent check. Body dimensions, body/part overlaps, neck start, wing/tail/comb endpoints, beak start, leg starts/ground baseline, and foot alignment pass. |

The detailed P booleans are in [`runtime-attempt-20.json`](runtime-attempt-20.json). Coordinates and raw SVG/model text were analyzed only in memory; they were not printed or stored. The API response contains no validated SVG, and no render asset was created. The actual GPU allocation is unknown; `L40S|L4|A10` is the worker's configured class only.

### Root cause and stop boundary

The failure occurs after successful Modal scheduling, model load, constrained decoding, JSON parsing, and worker completion. Backend SVG topology then rejects the output. Increasing the 1,800-second timeout would not change this result; observed AI requests failed validation in roughly 4–6 minutes, not at the timeout. The existing quality gates remain intact. Rev87.10-P's one-inference allowance is consumed, so no retry, raw-output repair, gate bypass, or further deployment/inference was performed. No child data, fixture output, story/video, database mutation, account/profile/consent change, `.env` change, or shared-service stop occurred.
