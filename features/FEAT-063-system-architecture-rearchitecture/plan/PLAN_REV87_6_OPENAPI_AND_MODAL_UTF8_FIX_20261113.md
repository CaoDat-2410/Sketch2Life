# Plan Rev87.6 — Fix runtime OpenAPI schema and retry Modal with UTF-8

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct instructions “tôi cho phép chạy để fix” and “chạy trên android emu đi”; scope clarifications recorded below.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned. No changes to §§1–31; append as-built evidence to §32 only.

## 1. Diagnosed blockers

1. `modal deploy` built/streamed images, then exited 1 when Python's Windows console codec could not encode build output (`charmap`). The deployment result is unknown; Rev87.5 intentionally made no post-failure Modal request.
2. Current-worktree API's `/openapi.json` failed while building the `SVG catalog contract` response because `openapi_contract.py` assigned that non-schema label to every SVG catalog operation. The catalog router declares concrete response models per operation; the public contract must use those actual model names and successful status codes.
3. After the concrete response schemas were fixed, `/openapi.json` returned 200 but still omitted all 12 SVG catalog routes. The router is mounted; `openapi_srs_v22.py` filters published paths to an allowlist that does not include `/api/svg-catalog/v1/`. This is an additional necessary OpenAPI projection fix within the owner's explicit authorization to run and fix the issue.
4. The owner steered the real UI verification from an isolated browser to the Android emulator. Android emulator execution replaces the web UI attempt; no web login or AI request was made.

## 2. Approved implementation

- Fix the SVG catalog response metadata in `backend/src/sketch2life/interfaces/http/openapi_contract.py`: bind each catalog route to its declared Pydantic response schema and success status (`200` or `201`), removing the invalid generic `SVG catalog contract` alias and success status codes that do not apply to the route.
- Add `/api/svg-catalog/v1/` to the active OpenAPI projection in `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` and assign a dedicated SVG catalog tag, so the mounted contract is actually visible to clients. Do not alter unrelated path families.
- Do not weaken authentication, validation, SVG safety gates, quality thresholds, persistence behavior, or other OpenAPI contracts.
- Do not edit `.env`. For the one Modal deployment process only, set `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and the PowerShell console output encoding to UTF-8; do not persist these settings.

## 3. Bounded runtime run

1. Static-compile both changed Python modules; build/run one temporary API container from the current worktree in the existing `rev79-parent-local-20261112` network, using the project-root `.env` without printing values. No migrations, seeding, account creation, or volume changes.
2. Verify local API `/health` returns 200; verify `/openapi.json` returns 200, includes the Parent sketch-guide route and all 12 SVG catalog routes, and every SVG catalog operation references its concrete response component with the declared success status. Check `adb devices`; use an available Android emulator or start one installed AVD. Start the real Parent Expo Android UI with process-local `SKETCH2LIFE_MOBILE_API_BASE_URL=http://10.0.2.2:8001` and `VITE_FIREBASE_AUTH_EMULATOR_URL=http://10.0.2.2:9099`, leaving root `.env` unchanged. Log in with only the pre-existing synthetic Parent account and confirm consent/profile workflow access. If ADB, emulator boot, app install/launch, login, or consent/profile preflight fails, do not deploy or call GPU.
3. Read-only list the existing Modal dev app, then deploy the corrected existing app once with process-local UTF-8 settings. No other app, secret, model, or minimum-container configuration changes.
4. Call the existing CPU `health_api` exactly once. No warmup and no GPU/model load in this health call.
5. If all previous gates pass, issue at most one real authenticated Parent UI request for the non-personal topic `gà`, through the current API to Qwen3.5. Use the pinned Arcadia SVG visual reference only for chicken. The response must pass the existing strict schema/sanitizer/anatomy/progression gates, remain private, unpersisted and adult-review-required, and render in the Parent UI. Save only actual response and screenshots.

## 4. Limits and stop rules

- One Modal deployment, one CPU health call, and at most one authenticated Parent UI GPU inference; 1,800-second request hard cap. No retry or second inference.
- No fixtures/canned output, video, FLUX, warmup, test suite, production identity, real child data, migration, seed/account creation, lesson/catalog write, publication, `.env`/secret edits, existing API replacement, shared Docker/Modal service stop, volume deletion, commit, push, or merge.
- Use the already-running Rev79 PostgreSQL/Firebase Auth services and their existing data. Run the temporary API on port 8001 so the pre-existing API on 8000 remains untouched. Stop only the temporary API/UI/browser process started by this run.
- If static compile, API health/OpenAPI, existing synthetic login/consent, deploy, Modal health, UI call, response gate, or render fails or has unknown outcome, preserve diagnostics and stop. No retry; another attempt needs a new plan/approval.

## 5. Acceptance criteria

- Runtime OpenAPI serves HTTP 200, includes the Parent sketch-guide route and all 12 SVG catalog operations, with concrete response component references and correct success statuses.
- The Modal CLI completes one deploy with UTF-8 output handling; the CPU health function passes without a GPU request.
- One real Parent UI→API→Modal request yields a valid, clearly recognizable chicken guide with 4–8 progressive stages; output is visually reviewed and remains an ephemeral adult-reviewed draft.
- Every result, failure boundary and timing is recorded in EV-063-101. No generated evidence is fabricated.

## 6. Exact path manifest

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_6_OPENAPI_AND_MODAL_UTF8_FIX_20261113.md` (new)
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append exact plan hash)
3. `backend/src/sketch2life/interfaces/http/openapi_contract.py` (fix only SVG catalog response metadata)
4. `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` (publish only the already-mounted SVG catalog prefix and dedicated tag)
5. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md` (append/update outcome)
6. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-3.json` (actual diagnostics only)
7. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-draft.json` (actual response only, if returned)
8. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide.svg` (actual response only, if returned)
9. Actual Parent Android screenshots under the same EV-063-101 directory, if produced
10. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 only)
11. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
12. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
13. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
14. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
15. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

No other repository path may change in Rev87.6.
