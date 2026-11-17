# EV-063-32 — Local Swagger QA kit and upload error parity

## Scope and authority

- Approved plan: `plan/PLAN_REV40_LOCAL_SWAGGER_QA_KIT_20261030.md`; SHA-256 `701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9`.
- Approval: project owner directly said `duyệt` in this chat; exact scope is recorded in `approvals/TASK_APPROVAL.md`.
- Source contract: owner-supplied `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`; SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.

## Delivered

- `/v1/sessions/{session_id}/media/image` and `/media/audio` body-limit rejections now return HTTP 413 with a valid `MobileWorkflowResultV1`, `status: FAILED`, `failure.domain: MEDIA`, and `failure.code: UPLOAD_TOO_LARGE`. The caller's safe request ID and expected session version are retained when valid. Other middleware-managed upload routes keep their previous generic payload.
- Swagger 413 responses for those two routes now point only to `MobileWorkflowResultV1`; the Rev38 runtime-mismatch extension and dual-shape `oneOf` were removed.
- Swagger includes a create-session JSON example, a multipart image example, header examples, and per-operation steps for the local synthetic workflow.
- The supplied deterministic 128 × 96 synthetic sun-and-hills PNG is `artifacts/qa-fixtures/synthetic-demo.png` (504 bytes; SHA-256 `2A0D125A7B34306DF54407EA8B7C41BA189C061C24F6C43277502C38D3CA9B9F`). It is abstract artwork, not a photograph or person/child data.
- The owner-facing instructions are in `artifacts/LOCAL_SWAGGER_QA_QUICKSTART_20261030.md`.

## Verification results

- Focused pytest command: `python -m pytest tests/contract/test_live_image_demo_api.py::test_media_upload_transport_enforces_a_typed_hard_multipart_body_cap tests/contract/test_openapi_contract_catalog.py -q` — **4 passed**. This covers both image and audio over-limit responses plus Swagger parity and example assertions.
- OpenAPI exporter with `SKETCH2LIFE_ENV=local` and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true` — **passed**: 124 mounted operations, 111 paths, 11 unmounted candidates.
- Ruff check across the changed Python files (`--ignore E501`) — **passed**. `compileall` on `app.py` and the upload middleware — **passed**. `git diff --check` — **passed**.
- In-memory TestClient workflow with `SKETCH2LIFE_AI_PROVIDER=disabled`: session creation returned HTTP 201/version 0; uploading the supplied PNG returned HTTP 200/`ADMITTED`/version 1. No database write or external AI/provider call was made.
- Restarted the loopback Swagger API at `http://127.0.0.1:8000`. `/docs` and `/openapi.json` returned HTTP 200; live OpenAPI reports 124 operations, 111 paths and 18 tags, includes both request examples, and declares `MobileWorkflowResultV1` for both 413 responses. Snapshot SHA-256: `70BDA49D2E122C4CE0370211DCEF8EA03BEC477CFDE2C60673501EB2CCDF8208`.

## Limits

- The interactive synthetic Demo flow is ready to try from Swagger. Protected Lesson Library/BE1 routes still require a valid Firebase ID token and the relevant local persistence services.
- At verification time, `FIREBASE_AUTH_EMULATOR_HOST` and `BE1_TEST_DATABASE_URL` were unset; the Firebase CLI and local Auth Emulator/PostgreSQL listeners on ports 9099/5432 were unavailable. No Firebase user, test bearer token, persistent test account, or authentication bypass was created. The existing integration tests' `X-Test-Principal` override applies only inside their disposable test harness and is not a Swagger credential.
- The attempt to open a new browser tab was blocked by the desktop command policy. The API is running at the URL above; refresh the existing Swagger tab or open that URL manually.
- No commit, push, deployment, persistent application-database operation, real child data, or external provider call occurred.
