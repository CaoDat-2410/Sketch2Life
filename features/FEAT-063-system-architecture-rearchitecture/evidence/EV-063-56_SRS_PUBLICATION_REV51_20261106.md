# EV-063-56 — Rev51 SRS source review and publication

- Feature: FEAT-063 — whole-repository architecture redesign.
- Date: 2026-11-06 (Asia/Saigon).
- Plan: `plan/PLAN_REV51_PUBLISH_REV45_SRS_20261106.md`.
- Plan SHA-256 at authorization: `919CD35DC42973A5FE06C9D99D56DC851B4FCDB1313E1AF0612CB525D78116A8`.
- Review base: fetched `origin/dev` commit `4749451080f49243464d40a464b8f83a03ae77bb`.
- State: REVIEW; source review and package publication are complete. This close-out record is carried in a follow-up documentation commit.

## Why the SRS includes a second source snapshot

The Rev45 review was prepared in the preserved local checkout before its history was synchronized with current `origin/dev`. Current dev contains later Modal/AI worker integration commits and additional FEAT-063 records. SRS §32.5 remains labeled as the earlier local working-tree review; §32.6 adds the current fetched-dev source crosswalk without changing product requirements.

## Current source findings

| Area | Source/evidence read | Finding recorded in SRS |
|---|---|---|
| Main FastAPI composition | `backend/src/sketch2life/interfaces/http/router_composition.py` | Main app composes health/BE1, local demo, and Lesson Library routes. It does not mount `routers.ai_jobs` or the separate StoryRun-lite app. |
| StoryRun-lite API | `interfaces/http/story_run_lite_app.py`; `interfaces/http/routers/story_run_lite.py`; `infrastructure/story_run_lite/photo_bridge.py` | A separate app provides drawing/story fixture operations. Drawing analysis and story generation are scheduled through FastAPI `BackgroundTasks`; this does not provide durable shared AI Jobs/outbox behavior. |
| Modal adapter | `infrastructure/ai/modal_function_client.py` | A Modal SDK drawing client is called from the StoryRun-lite bridge. This proves source wiring for the separate slice, not main-app API dispatch or production integration. |
| Dev model profiles | `deployment/modal/srs_v23/workloads.json`; `drawing_vlm_app.py`; `flux_image_app.py`; `language_audio_app.py` | Current dev configuration pins Qwen3.5-9B and FLUX.3 variants. The registry describes dev-only profiles and keeps workloads disabled. These pins do not change the product target or approve production use. |
| API counts and previous execution | `artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`; `evidence/AI_API_QWEN35_MODAL_VALIDATION_20261105.md`; `evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md`; `evidence/AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md` | Existing evidence records main OpenAPI 24 operations/17 path templates and StoryRun-lite 13 operations/12 paths, plus synthetic worker results and their failures/limits. Rev51 did not rerun them. |
| Video and data | `deployment/modal/srs_v23/wan_video_candidate_app.py`; canonical SRS Q144; Rev43 DB evidence | WAN remains a candidate and LTX-2.5 remains the target. The local 41-table DB count remains a Rev43 snapshot; no DB query or migration was performed for Rev51. |

## Reconciliation decisions

- Keep §§1–31 as the target requirements. Keep Rev43 runtime/database results, Rev45 local source observations and Rev51 fetched-dev source observations as separate dated evidence.
- Keep Qwen3.5-VL, FLUX.3 and Whisper as development directions; SAM 2.1 remains optional. Exact development profile pins do not become production requirements.
- Keep LTX-2.5/Modal L40S as the video target under Q144; the WAN code remains a development candidate.
- Retain the main-app AI Jobs, authenticated Parent/Teacher APIs, durable dispatch, deployment/safety/license/quality/cost gates as open gaps.
- Reindex the Rev45 SRS/code review as EV-063-55 because `origin/dev` already assigns EV-063-34 to the Swagger review artifact.

## Method and limits

- Read current source and existing evidence from the fetched Git tree; no source code was changed.
- Did not run tests/builds, start services, regenerate OpenAPI, query databases, call Modal/model providers, inspect credentials/secrets, or deploy anything.
- Existing Rev44–46 test and inference outcomes are summarized only from their attributed reports; Rev51 does not claim those results were reproduced.
- The product SRS and Data Table Register remain unsigned drafts. Code presence, route composition, dev profiles, and synthetic inference do not establish product acceptance or production readiness.

## Publication result

The exact 17-path package was committed as `620386fb227e2d8b76c48e72ad22892e3b0c1c53` (`docs(FEAT-063): publish SRS v2.5 alignment`) on `docs/feat063-rev45-srs-code-alignment-20261106` and pushed to origin without force. A fresh fetch confirmed `origin/docs/feat063-rev45-srs-code-alignment-20261106` matched the commit. The branch starts at fetched `origin/dev` `4749451080f49243464d40a464b8f83a03ae77bb`; `dev` was not changed.

`python tools/validate_repository_security.py` passed before commit and before push. Each run reported `REPOSITORY_SECURITY_VALID`, scanned 6,563 publishable files, excluded environment files/seed accounts/credentials/signing keys/external reference documents, and found no absolute machine paths. `git diff --cached --check` was clean. No product tests, builds, API/runtime calls, DB queries, Modal/provider calls or deployment were run for Rev51.

The original dirty checkout remains isolated. The package and companion are still unsigned drafts. The review close-out plan hash and any follow-up close-out commit are recorded in the final branch history; this report identifies the initial SRS package commit rather than trying to embed its own commit hash.
