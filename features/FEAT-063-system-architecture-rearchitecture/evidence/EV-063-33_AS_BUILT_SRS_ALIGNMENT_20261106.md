# EV-063-33 — As-built SRS alignment

- **Date:** 2026-11-06 (Asia/Saigon)
- **Feature / plan:** FEAT-063, Plan Rev43
- **Plan SHA-256 at owner authorization:** `000A4D0C22BB92666C60C4597BB5B8AEB126E0D4C1F654B610909CC7BBDED945`
- **Current reviewed plan SHA-256:** `1F10B3F447F7AFB59FAD847E6BE05F0C898B4CE4F6F51B0536258BBD1806F185` (later edits update lifecycle and clarify the AI/database table boundary within the owner's documentation request).
- **Reviewer / approver:** Project owner authorized the documentation task directly in the conversation. This evidence does not constitute formal SRS sign-off.
- **Scope:** read-only comparison of the canonical SRS with current backend source, local OpenAPI, local PostgreSQL, owner-selected AI direction and owner-provided Modal dashboard screenshot.

## 1. Findings

### Local API runtime

Read `http://127.0.0.1:8000/openapi.json` without sending a write request. Result: **111 paths and 124 operations**.

Main-app route composition includes health, BE1 runtime, child preferences, sessions, image/audio upload and understanding, supervised flow/context/activity suggestions, renderer, whiteboard storyboard/video, story-video, and Lesson Library. These existing session/demo routes are not the complete dedicated Parent API set in the SRS. The AI Jobs router is implemented separately and is mounted in `backend/src/sketch2life/interfaces/http/ai_jobs_fixture_app.py`; it is not included by `router_composition.py` in the main app.

Lesson Library operations are mounted under `/api/lesson-library/v1`. The runtime OpenAPI count agrees with the latest Rev37 catalog snapshot. The API catalog is a route inventory, not evidence every end-to-end product flow is complete.

### Local database

Read-only command used:

```powershell
docker exec sketch2life-postgres-1 psql -U sketch2life -d sketch2life -Atc "select 'alembic=' || version_num from alembic_version; select 'schema=' || schema_name from information_schema.schemata where schema_name not like 'pg_%' and schema_name <> 'information_schema' order by schema_name; select 'table=' || table_schema || '.' || table_name from information_schema.tables where table_type='BASE TABLE' and table_schema not like 'pg_%' and table_schema <> 'information_schema' order by table_schema, table_name;"
```

Observed non-system schemas: `public` and `lesson`. Alembic revision: `20261028_ll_0001`. There are **41 application base tables**: 34 under `public` and 7 under `lesson`. `alembic_version` is bookkeeping and excluded from the application count. The complete names are recorded in `artifacts/DATA_TABLE_REGISTER.md` §14.5.

The 41-table local snapshot is not the 92-active/48-legacy target crosswalk. The latter remains a source-derived design target, 140 projected physical mappings in total. Table presence does not prove active traffic or acceptance. No database writes or migration commands were run.

### AI-to-database boundary

The only non-system schemas observed are `public` and `lesson`. No AI Jobs, AI Policy, Story, Billing or dedicated Parent schema is present in this database. Core asset/upload, BE1 profile/consent/observation, and Lesson Library tables exist and may be read/written by the backend under the target contracts; no SQL query trace or row-level telemetry was inspected to establish request-specific use. Modal workers are not database clients. SRS §32.4 and Data Table Register §14.6 record the table groups and limitations.

### Backend provider wiring

The current backend source contains prior-slice adapters such as `LightningVisionV2Adapter`, `LightningAsrV2Adapter`, `LightningActivityRanker`, `LightningStoryVideoAdapter`, and `LightningSam21SegmentationAdapter` in the HTTP application composition. The inspected main route composition does not contain a Modal adapter for the owner-visible dev app functions. This is a source-level finding; Rev43 did not dispatch a paid provider request.

### Owner-provided Modal dashboard observation

The owner-provided dashboard screenshot shows these three dev apps as live:

| App shown | Function labels shown | What the screenshot establishes |
|---|---|---|
| `sketch2life-srs23-language-audio-dev` | `download-language-audio-models`, `generate-story-and-storyboard`, `synthesize-vietnamese-narration`, `transcribe-vietnamese-audio` | Dev functions are deployed/listed; checkpoint, inference success and backend routing are not established. |
| `sketch2life-srs23-video-candidate-dev` | `download-wan-video-candidate-model`, `generate-wan-video-candidate` | A WAN video candidate is deployed/listed; it is not evidence of the SRS LTX-2.5 pipeline. |
| `sketch2life-srs23-flux-image-dev` | `download-flux-pinned-model`, `generate-line-sketch-guide-candidate` | An image/line-sketch candidate is deployed/listed; exact checkpoint and request result are not established. |

The chosen development directions recorded in SRS §31.12 (Qwen3.5-VL, FLUX.3, Whisper, optional SAM 2.1, Modal) come from the owner's instructions. The screenshot does not display enough model metadata to independently establish those model IDs. No inference, GPU startup, app stop/start, secret inspection or spend check was done for Rev43.

## 2. SRS alignment decisions

- Canonical SRS is updated to **v2.4-draft**, still unsigned. The v2.3 product requirements and flows remain the target; §32 separates implementation status from requirements.
- Removed Qwen2.5 from active model-choice rows. Historical Qwen3-VL NO_GO evidence is explicitly limited to the evaluated profile and is not used as a result for Qwen3.5-VL.
- Recorded Q159 as resolved by the owner: Platform Admin and Teacher may initiate lesson/activity AI suggestions; Parent may edit an authorized draft only.
- FLUX.3 is the current development direction for line-sketch and lesson visuals. Whisper is the speech-to-text direction. SAM 2.1 stays optional and needs Modal integration/quality verification. LTX-2.5 remains the video target; the WAN candidate does not replace it. Video remains unverified/deferred.
- Added local API/database/Modal status as a dated snapshot and retained all target requirements, target data counts and preserved historical SRS documents.

## 3. Limitations and interpretation

- Local DB and API observations apply only to the inspected development environment on 2026-11-06.
- The Modal screenshot is user-supplied; the current live dashboard was not independently reopened in this task.
- A deployed function name is not proof of a successful request, correct schema, safety, quality, latency, or connection through the main backend.
- No full AI flow, model benchmark, video generation, tests, or production behavior was tested as part of this documentation update.
- The SRS and companion register remain drafts pending owner, engineering and privacy/legal/commercial reviews as applicable.

## 4. Verification performed

- Read-only main OpenAPI fetch: 111 paths / 124 operations.
- Read-only PostgreSQL schema and Alembic inspection: 41 application tables / revision `20261028_ll_0001`.
- Static source review of router composition, AI Jobs fixture mounting, and current provider adapters.
- Static consistency review of SRS model rows, Q159, local/target database counts, authority pointers and FEAT-063 tracking records.
- No automated tests were run; this plan is documentation-only.
