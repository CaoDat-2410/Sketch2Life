# FEAT-066 CONV-1 — BE implementation approval package (Draft 2)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package proposes a bounded BE slice. It authorizes no code, test, OpenAPI change, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 1 (18,780 B, `7B638AE3…`). Draft 1's round-1 cold review was NOT READY with 1 P1, 8 P2 and 7 P3 (`evidence/notes/CONV_1_COLD_REVIEW_DRAFT1_20261118.md`). §11 maps each finding to its fix.
- **Place in the plan:** Phase B, BE queue slot 1. The queue is CONV-1 → FR-C-08 → SEED-1 → Billing B-1.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, `B9B1F42D…`. Clauses: §9.8 (lines 847–875), §21.1 (lines 1632–1641), §21.4 (lines 1695–1701) |
| Conventions contract | `plan/PLAN_API_CONVENTIONS_CONTRACT_DRAFT1_20261118.md`, 13,999 B, `1F41B74AD0F0A8425D5843851FEBA0CCFFDCD6D1572EE159E967F528C7D9DB01` |
| Owner decisions | `DECISIONS.md` D-066-68 (C-D1 to C-D10) and D-066-69. The CONV-1 answers of 2026-11-18 are in §8; they are recorded as a decision row when this package is approved |
| Source base | Root checkout, `feature/feat063-m2-parent-teacher-foundation`, HEAD `08439b22`. Static reading only |

## 2. Current state (evidence from the source at `08439b22`)

Paths are relative to `backend/src/sketch2life/`.

| Topic | What the source does today |
|---|---|
| Correlation middleware | `interfaces/http/app.py` `be1_request_context` (about lines 420–451) sets `X-Request-ID` only for paths starting with these prefixes:<ul><li>`/api/be1/v1`, `/api/lesson-library/v1`;</li><li>`/api/parent/v1/ai/story-runs/`, `/api/parent/v1/ai/drawing-understandings`;</li><li>`/v1/parent/profiles`, `/v1/story-runs`.</li></ul> |
| HTTP error handler (`app.py` lines 453–646) | Four branches:<ul><li>**story-runs:** §9.8 fields, Vietnamese. It also serves `/api/parent/v1/ai/story-runs/{id}/story-revisions` and `/api/parent/v1/ai/drawing-understandings` (`app.py` about lines 170–184 and 457–460).</li><li>**Parent profiles:** `parent_error_payload`, English, null fields omitted.</li><li>**Lesson Library:** `{code, message, request_id}`, with route-supplied English messages.</li><li>**BE1:** `Be1Error {code, message, request_id}`.</li></ul>Every other path gets FastAPI's `{"detail": …}` |
| Validation handler (`app.py` lines 648–816) | story-runs and Parent profiles: 400. BE1: 422 `REQUEST_VALIDATION_FAILED`. Lesson Library: 422 `INVALID_REQUEST`. P1 context options: `MobileWorkflowResultV1` at 422. Other paths: 422 `{"detail": …}` |
| Unhandled handler (`app.py` lines 818–897) | Envelopes for story-runs, Lesson Library, Parent profiles and BE1. Other paths get plain text, through Starlette's `ServerErrorMiddleware` |
| Outermost middleware | `interfaces/http/middleware/bounded_image_upload.py` (added at `app.py:899`). For a Lesson Library upload part over 4 MiB it sends 413 `{code: REQUEST_TOO_LARGE, message, request_id: "request-body-limit"}` with no `X-Request-ID` (lines 92–117). Its image, audio and storage-example branches serve legacy and dev paths |
| `HTTPException(422, …)` raised by in-scope routes | Lesson Library router and service: `INVALID_REQUEST` (about 15 sites, including the malformed `If-Match` at `routers/lesson_library.py:91`, and also `INVALID_SOURCE_DOCUMENT` and `MALWARE_DETECTED`). BE1: `IDEMPOTENCY_KEY_REQUIRED` (`routers/be1_sessions.py:128`), `CLASS_SCOPE_MISMATCH` (`be1_records.py:341`, `be1_registry.py:412` and `:505`), `CANVAS_IMAGE_NOT_ADMITTED`, `CONTRIBUTORS_REQUIRED`, `IMAGE_INVALID` and `RESERVED_CONFIGURATION_KEY`. Teacher AI: `TEACHER_PLAN_FIELD_LIMIT_EXCEEDED` |
| Shared scope guard | `interfaces/http/routers/be1_common.py` `require_assignment` (lines 83–139):<ul><li>a missing, inactive, wrong-role or unassigned account gets 403 `ACCOUNT_SCOPE_UNAVAILABLE` (line 114);</li><li>a `Be1PolicyError` gets 403 with its code (line 137).</li></ul>The policy (`application/services/be1_runtime.py:45–70`) raises `ADULT_NOT_ASSIGNED`, `IDENTITY_ISSUER_MISMATCH`, or `SCOPE_DENIED` for an organization or class mismatch **and** for a role outside `roles` |
| Idempotency-key rule | `routers/parent_profiles.py` `_idempotency_key` (lines 103–115): exactly one value of 1–128 characters in ASCII 33–126. A missing key gives field code `REQUIRED`; anything else gives `INVALID_FORMAT`. Both return 400 `INVALID_REQUEST` |
| Field-error vocabulary | `contracts/schemas/parent_profiles.py` `parent_field_errors` (lines 81–122): codes `REQUIRED`, `TOO_LONG`, `OUT_OF_RANGE`, `EMPTY`, `INVALID_TYPE`, `INVALID_FORMAT` and `UNKNOWN_FIELD`. Unknown names become `<unknown>` |
| Revision | Lesson Library `If-Match`:<ul><li>missing gives 428 `PRECONDITION_REQUIRED` (`lesson_library.py:86`);</li><li>malformed gives **422** `INVALID_REQUEST` (line 91);</li><li>stale gives 409 `STALE_REVISION` with no `current_version` or ETag (`infrastructure/lesson_library/service.py:599`).</li></ul> |
| OpenAPI | `interfaces/http/openapi_contract.py` is generated from the FEAT-063 Rev37 catalog; it has hand amendments since MGR-7. Error rows are published through `interfaces/http/openapi_contract_amendments.py`: `BE1_EXPLICIT_ERROR_STATUSES = {"401","403","422"}` (line 9) and `published_responses` (line 1254). `interfaces/http/openapi_srs_v22.py` renames `Be1Error` to `ApiError` (lines 213–235). `app.py` builds and post-processes the schema (lines 1174–1368) |

**Route families mounted in the combined profile** (`router_composition.py`):

| Family | Routers |
|---|---|
| `/api/be1/v1` | `be1_runtime`, `be1_sessions`, `be1_registry`, `be1_canvas`, `be1_artifacts`, `be1_records`, and `pilot_assistance` when mounted conditionally |
| `/api/lesson-library/v1` | `lesson_library` |
| `/api/platform-admin/v1` | `platform_admin_accounts` |
| `/api/auth/v1` | `auth_registration` |
| `/api/teacher/v1/organizations/{organization_id}/ai` | `teacher_ai` |
| `/api/parent/v1/ai` | `parent_ai` |
| `/v1/parent/profiles`, `/v1/story-runs` | M2 (frozen) |
| Legacy and demo | `/v1/sessions`, `/v1/profile`, `/v1/whiteboard`, `/v1` live understanding and story-run-lite, `/api/dev/v1`, health |

## 3. Proposed scope

### 3.1 Families

| Family | In CONV-1? |
|---|---|
| `/api/be1/v1` (including `pilot_assistance`), `/api/lesson-library/v1`, `/api/platform-admin/v1`, `/api/auth/v1`, `/api/teacher/v1/…/ai` | **Yes** |
| `/api/parent/v1/ai` | **No.** Owner CV-1 = leave it for C-P. The mobile parser reads only `payload.detail` (`apps/mobile/src/infrastructure/api/parentWorkflowApi.ts:268–270`), so the body and the parser change together in C-P. The two paths already served by the story-runs branch stay as they are. Regression-guarded by `test_parent_ai_late_result_guards.py` |
| `/v1/parent/profiles`, `/v1/story-runs` | **No: unchanged, regression-guarded** |
| Legacy and demo families | **No.** Only the header rule in §3.2 item 4 touches them. The `story_run_lite` `X-Correlation-ID` alias in contract C-2 is **not in CONV-1**; it belongs to a legacy demo family |

### 3.2 Behaviour changes

**1. Envelope builder** (new module `interfaces/http/error_envelope.py`).
- `build_error(status, code, *, request_id, field_errors=None, current_version=None, retry_after_header=None)` returns the C-D1 body. All six §9.8 fields are always present (null when empty), plus `request_id` equal to `correlation_id`. `current_version` appears only with `STALE_REVISION`.
- **Derivation:** `retryable` is true for status 429, 502, 503 and 504. `retry_after_seconds` is the integer `Retry-After` value when that header is all digits; otherwise it is null.
- **Two variants will coexist:** this builder, and the frozen Parent-profiles variant, which omits null fields and uses English messages. FE parsers must tolerate missing optional fields.

**2. Handlers for in-scope families** (`app.py`). The HTTP-error, validation and unhandled handlers route every in-scope family through the builder. The story-runs, Parent-profiles and P1 branches are not changed. Inside the new path, in this order:

- **a. Status remap** for 422 sent with `HTTPException`:
  - code `INVALID_REQUEST` (or no code) becomes **400 `INVALID_REQUEST`**;
  - `IDEMPOTENCY_KEY_REQUIRED` becomes **400 `INVALID_REQUEST`**, with `field_errors` `[{field: "Idempotency-Key", code: "REQUIRED"}]` when the header is absent and `INVALID_FORMAT` otherwise;
  - every other 422 code stays 422. These are domain codes, aligned in their own slices under CV-2 = A: `INVALID_SOURCE_DOCUMENT`, `MALWARE_DETECTED`, `CANVAS_IMAGE_NOT_ADMITTED`, `CONTRIBUTORS_REQUIRED`, `IMAGE_INVALID`, `RESERVED_CONFIGURATION_KEY`, `TEACHER_PLAN_FIELD_LIMIT_EXCEEDED` and `CLASS_SCOPE_MISMATCH`.
  - `CLASS_SCOPE_MISMATCH` is a route-specific check (C-D4: "route-specific checks change in their own slices"). It is listed for the C-M and C-T slices, because `be1_records.py:341` can reveal that a session exists in another class.
- **b. Code mapping** (CV-2 = A, generic codes only):

  | Today | After CONV-1 |
  |---|---|
  | `AUTHENTICATION_REQUIRED`, `UNAUTHENTICATED` | 401 `AUTH_REQUIRED` |
  | `INVALID_IDENTITY_TOKEN` | 401 `INVALID_TOKEN` |
  | `FORBIDDEN` | 403 `ACTION_NOT_ALLOWED` |
  | `NOT_FOUND` and every 404 code ending in `_NOT_FOUND` | 404 `RESOURCE_NOT_FOUND` (C-D4 uniform shape) |
  | `CONFLICT`, `INVALID_TRANSITION` | 409 `INVALID_STATE_TRANSITION` |
  | `REQUEST_VALIDATION_FAILED` | 400 `INVALID_REQUEST` |
  | `SERVICE_UNAVAILABLE`, `DEPENDENCY_UNAVAILABLE` | 503 `PROVIDER_UNAVAILABLE` |
  | `PRECONDITION_REQUIRED` | removed by CV-4 (item 6) |

  - **Kept unchanged, for their own slices:** the upload and file codes, whose status also changes under §9.8. These are `REQUEST_TOO_LARGE` (to `LESSON_FILE_TOO_LARGE` or `MEDIA_TOO_LARGE`), `PART_CONFLICT` (to `UPLOAD_PART_CONFLICT`), `UPLOAD_EXPIRED` (409 to 410 `UPLOAD_SESSION_EXPIRED`) and `UPLOAD_INCOMPLETE` (409 to 422). They are listed for C-T.
  - **Every other domain code keeps its name.**
  - **Status defaults** for a detail without a code (`platform_admin_accounts`, `auth_registration` and `teacher_ai` send string details): 400 `INVALID_REQUEST`, 401 `AUTH_REQUIRED`, 403 `ACTION_NOT_ALLOWED`, 404 `RESOURCE_NOT_FOUND`, 409 `INVALID_STATE_TRANSITION`, 413 `MEDIA_TOO_LARGE`, 415 `UNSUPPORTED_MEDIA_TYPE`, 429 `RATE_LIMITED`, 500 `INTERNAL_SERVER_ERROR`, 502 `PROVIDER_BAD_RESPONSE`, 503 and 504 `PROVIDER_UNAVAILABLE`.
- **c. Messages** (CV-3 = A):
  - `message` comes from one code-to-Vietnamese table in `error_envelope.py`. Route-supplied message text is ignored.
  - A code missing from the table gets the Vietnamese message for its status.
  - **Coverage test:** it scans the in-scope router and service modules for code literals passed to `failure(...)`, `fail(...)` and `HTTPException(detail={"code": …})`. Each code must be either in the table or in an explicit `STATUS_MESSAGE_ONLY` set. A new code therefore fails the test until someone classifies it.
- **d. Validation errors** (C-D3): 400 `INVALID_REQUEST` with `field_errors` `[{field, code}]`, as follows.
  - **Codes:** the Parent vocabulary — `REQUIRED`, `TOO_LONG`, `OUT_OF_RANGE`, `EMPTY`, `INVALID_TYPE`, `INVALID_FORMAT`, `UNKNOWN_FIELD`.
  - **Field names:** only names the route itself declares, meaning its query, path and header parameter names and the field names of its body models, collected recursively. Anything else, including keys of free-form dictionaries and `extra_forbidden` keys, becomes `<unknown>`. List indexes are dropped. This lives in `api_conventions.py` as `field_errors_from_validation(route, issues)`.
  - **Effect:** a `limit` above 100 on any route that declares `le=100` returns 400 `INVALID_REQUEST` with `{field: "limit", code: "OUT_OF_RANGE"}` (C-D8).
- **e. Idempotency key** (C-D5, §21.4):
  - a missing or malformed key is 400 `INVALID_REQUEST` with field code `REQUIRED` or `INVALID_FORMAT`;
  - `INVALID_IDEMPOTENCY_KEY` is used only when a key is reused with a different payload, as Lesson Library already does at `service.py:506`.
  - This differs from the story-runs branch, which stays frozen.
- **f. Unhandled errors:** 500 `INTERNAL_SERVER_ERROR` in the envelope, with the `X-Request-ID` header. Only the request ID and the exception type are logged.

**3. 404 versus 403 in `require_assignment`** (C-D4, owner CV-5 = 404):
- These cases give **404 `RESOURCE_NOT_FOUND`**:
  - the identity is missing or inactive;
  - the `account_role` is not School Manager or Teacher;
  - no active assignment covers the organization;
  - `class_id` is given and no active assignment for that organization covers the class, whatever the role;
  - the policy raises `ADULT_NOT_ASSIGNED` or `IDENTITY_ISSUER_MISMATCH`.
- This case gives **403 `ACTION_NOT_ALLOWED`:** an active assignment covers the organization and class, but its role is outside `roles`. The guard computes "covers the scope" from the rows before it calls the policy, so `SCOPE_DENIED` after that point means a role refusal only.
- `application/services/be1_runtime.py` is not changed.
- **Not in CONV-1:** route-specific checks (`CLASS_SCOPE_MISMATCH` above) and the Lesson Library authorization functions keep their status. Only their codes are renamed by item 2b. They are listed for the C-M and C-T slices.

**4. Correlation header** (C-D2, §21.1):
- Every response produced inside the app carries `X-Request-ID`. A supplied safe ID is echoed; otherwise a UUID is generated.
- On in-scope families the body's `correlation_id` equals the header.
- The middleware sets the header for every path. The story-runs and Parent-profiles header behaviour is unchanged.
- The unhandled-exception handler adds the header on every path, including the legacy paths, where the body stays plain text.
- **Exception:** a crash before the app stack (Starlette's `ServerErrorMiddleware` when the handler itself fails). AC5 is limited to responses produced inside the app stack.

**5. Upload-limit middleware** (`bounded_image_upload.py`, Lesson Library part branch only):
- The 413 body becomes the envelope. The code stays `REQUEST_TOO_LARGE` until C-T, per item 2b.
- The response gets an `X-Request-ID` header, taken from a safe supplied ID or newly generated. The `"request-body-limit"` placeholder is dropped.
- The image, audio, demo and storage-example branches are not changed.

**6. Lesson Library `If-Match`** (CV-4 = A), in `routers/lesson_library.py` lines 80–95 only:
- missing: 400 `INVALID_REQUEST` with `[{field: "If-Match", code: "REQUIRED"}]`;
- malformed: 400 `INVALID_REQUEST` with `[{field: "If-Match", code: "INVALID_FORMAT"}]`.
- The stale case keeps 409 `STALE_REVISION`. Adding the current ETag or `current_version` to it (C-D7) is **deferred** to the Lesson Library adoption slice.

**7. Shared helpers** (new module `interfaces/http/api_conventions.py`), adopted by no route except as listed in this package:
- `parse_idempotency_key(request)` implements item 2e;
- `PAGE_LIMIT_DEFAULT = 25`, `PAGE_LIMIT_MAX = 100` and `limit_query()`;
- `raise_stale_revision(current_version=None, etag=None)`;
- `field_errors_from_validation(route, issues)` implements item 2d.

The Parent routes keep their own copies, because they are frozen.

**8. OpenAPI.**
- **What changes:** the error documentation of the in-scope operations moves through the amendments layer:
  - `BE1_EXPLICIT_ERROR_STATUSES` becomes `{"400", "401", "403", "404"}`;
  - `published_responses` publishes 400 instead of 422 for the in-scope operations, keeping 422 only where a §9.8 semantic or kept domain 422 code is documented;
  - `Be1Error` becomes the envelope model, which `openapi_srs_v22.py` still publishes as `ApiError`;
  - FastAPI's automatic `HTTPValidationError` 422 is replaced by the 400 envelope response in the runtime-schema post-processing in `app.py`, for in-scope operations.
- **The generated `openapi_contract.py`:** edited only if the catalog rows themselves must change. Any such edit is recorded as a hand amendment, as MGR-7's were, and the Rev37 source pin is not changed.

### 3.3 Explicitly out of scope

- No route move, rename or new prefix (C-D9).
- No new `Idempotency-Key` requirement on a route that takes no key today.
- No cursor paging for accounts, no paging for BE1 lists, and no change to the BE1 canvas `limit` of 500.
- No `/api/parent/v1/ai` change (CV-1).
- No upload or file code or status alignment (CV-2 = A).
- No route-specific scope check change.
- No Lesson Library stale-revision payload change.
- No FE, mobile or Bruno file.
- No migration, dependency, `uv.lock` or `pyproject.toml` change.
- `application/services/be1_runtime.py` is not changed.

## 4. Proposed exact allowlist

All paths are under `backend/`.

**Source**

| # | File | Limit |
|---|---|---|
| 1 | `src/sketch2life/interfaces/http/app.py` | The middleware, the three handlers, and runtime-schema post-processing for the 400 |
| 2 | `src/sketch2life/interfaces/http/error_envelope.py` | New |
| 3 | `src/sketch2life/interfaces/http/api_conventions.py` | New |
| 4 | `src/sketch2life/interfaces/http/routers/be1_common.py` | `require_assignment` and the shared `responses` declarations |
| 5 | `src/sketch2life/contracts/schemas/be1_runtime.py` | `Be1Error` only |
| 6 | `src/sketch2life/interfaces/http/routers/lesson_library.py` | The `If-Match` helper, lines 80–95, only |
| 7 | `src/sketch2life/interfaces/http/middleware/bounded_image_upload.py` | The Lesson Library part branch of `_send_too_large` only |
| 8 | `src/sketch2life/interfaces/http/openapi_contract_amendments.py` | |
| 9 | `src/sketch2life/interfaces/http/openapi_srs_v22.py` | Only if the `Be1Error` → `ApiError` projection needs an edit |
| 10 | `src/sketch2life/interfaces/http/openapi_contract.py` | Only the error-response rows of in-scope operations, only if item 8 cannot express the change, recorded as a hand amendment |

**Tool**

| # | File |
|---|---|
| 11 | `tools/be1_api_smoke.py` (its 422, `REQUEST_VALIDATION_FAILED` and `Be1Error` checks) |

**Tests, new**

| # | File | Covers |
|---|---|---|
| 12 | `tests/unit/test_http_error_envelope.py` | Builder, derivation, message table, coverage scan |
| 13 | `tests/unit/test_http_api_conventions.py` | Key parser, `limit`, stale helper, field-error reduction including `<unknown>` |
| 14 | `tests/contract/test_http_error_conventions.py` | Through `create_app`: each in-scope family's envelope and header equal to body, 400 validation, `limit` above 100, the 422 remap, the unhandled 500, the Lesson Library 413 from the middleware, and the `If-Match` cases |
| 15 | `tests/unit/test_be1_scope_guard_404_403.py` | Each §3.2 item 3 branch: missing, inactive, wrong role, organization not covered, class not covered, issuer mismatch, and role refused in scope |

**Tests, existing.** Edits are limited to status, code, envelope and message assertions:

| # | File |
|---|---|
| 16 | `tests/contract/test_openapi_contract_catalog.py` |
| 17 | `tests/contract/test_openapi_schema_catalog_mapping.py` |
| 18 | `tests/contract/test_app_composition.py` |
| 19 | `tests/contract/test_auth_registration_api.py` |
| 20 | `tests/contract/test_m2_s1a_teacher_routes.py` |
| 21 | `tests/contract/test_assistance_requests_api.py` |
| 22 | `tests/integration/lesson_library/test_lesson_library_api.py` |
| 23 | `tests/integration/test_be1_postgres_api.py` |
| 24 | `tests/integration/test_be1_synthetic_pilot_postgres.py` |
| 25 | `tests/integration/test_m2_s1a_teacher_postgres.py` |
| 26 | `tests/integration/test_pilot_assistance_routes_t9.py` |
| 27 | `tests/unit/test_pilot_queue_composition_b1.py` |
| 28 | `tests/unit/test_synthetic_status_guard.py` |

- **Dropped since Draft 1:** `test_activity_execution_http.py` and `test_live_image_demo_api.py`. They do not pass through the in-scope handlers.
- **If another file needs an edit,** the task stops and needs an owner scope amendment.
- **Regression guards, which must pass unchanged:**
  - `tests/contract/test_parent_profiles_routes.py`
  - `tests/contract/test_parent_story_run_request_contract.py`
  - `tests/contract/test_parent_ai_late_result_guards.py`
  - `tests/integration/test_m2_s1a_parent_postgres.py`
  - `tests/integration/test_m2_s2_g1_parent_story_postgres.py`

## 5. Acceptance criteria

1. In-scope families return the C-D1 envelope, with all six fields, on HTTP errors, validation errors and unhandled errors, and on the Lesson Library 413 from the middleware. The `X-Request-ID` header equals `correlation_id`.
2. In-scope validation errors return 400 `INVALID_REQUEST` with field errors from the Parent vocabulary and only declared field names. A `limit` above 100 gives 400. HTTP 422 with `INVALID_REQUEST` or `IDEMPOTENCY_KEY_REQUIRED` is remapped to 400. The listed domain 422 codes stay 422.
3. Every §3.2 item 3 branch returns the stated status and code. A non-existent ID and an out-of-scope resource give the same 404 body shape.
4. Codes follow the §3.2 item 2b table. Messages come only from the Vietnamese table or the status fallback. The coverage test passes. No body contains a route string, a stack trace, a path or an echoed input.
5. Every response produced inside the app stack carries `X-Request-ID`.
6. Missing and malformed `If-Match` give 400 with the field errors in §3.2 item 6.
7. Story-runs, Parent-profiles and `/api/parent/v1/ai` responses are unchanged. The five regression guards pass unmodified.
8. The OpenAPI document shows the envelope (`ApiError`) and 400 for in-scope operations. The catalog and mapping tests pass.
9. The FE, Bruno and slice follow-ups in §6 are recorded in `STATUS.md`.

## 6. Follow-ups (not in CONV-1)

**Web callers that read errors:**

| File | Reads |
|---|---|
| `apps/web/src/shared/backendApi.tsx` | Accepts flat and nested shapes (about lines 282–297); shows a 403-specific message (about line 609), which CV-5 makes unreachable for scope cases |
| `apps/web/src/modules/school-manager/be1/services/be1Client.ts` | |
| `apps/web/src/modules/school-manager/be1/services/authService.ts` | Flat `message` from `/api/auth/v1/me`, about lines 51–53 |
| `apps/web/src/modules/platform-admin/services/userService.ts` | |
| `apps/web/src/modules/platform-admin/pages/UsersPage.tsx` | `limit` and `offset` |
| `apps/web/src/modules/teacher/services/aiWorkflowService.ts` | |
| `apps/web/src/modules/teacher/pages/TeacherAiLessonWorkflowPage.tsx` | |

- **Release order:** web code that compares the old codes, reads `detail`, or expects 422 or 403 will misreport errors after CONV-1. FEBASE and the per-role FE slices take CONV-1 as their base. The `request_id` alias is the one field that does not change.
- **Mobile:** none, because `/api/parent/v1/ai` stays out of scope. C-P changes the BE body and `parentWorkflowApi.ts` together.
- **Bruno:** BRU-0 updates the in-scope status and code assertions.

**Slices that pick up deferred items:**

| Slice | Deferred item |
|---|---|
| C-T | Upload and file code and status alignment; the remaining domain 422 codes; ClamAV |
| C-M and C-T | `CLASS_SCOPE_MISMATCH` and route-specific scope checks |
| Lesson Library | The `STALE_REVISION` current ETag |
| Platform Admin | Account cursor paging |
| C-P | `/api/parent/v1/ai` envelope plus the mobile parser |

## 7. Verification plan and command ceiling

- **Coordinator, after the Task Approval, without DB or TestClient:**
  - `ruff check` and `mypy` on the allowlisted source files;
  - the new unit tests 12, 13 and 15, if they need no TestClient;
  - `python tools/validate_harness.py`, `validate_repository_security.py` and `validate_architecture.py`;
  - `git diff --check`.
- **Owner-run in their own terminal**, each once, against the disposable `be1_acceptance` database with ClamAV absent as before (the Codex sandbox hangs on loopback sockets):
  - test 14;
  - tests 16–28;
  - the five regression guards;
  - `test_app_composition.py`.
- **Evidence:** one note with the commands, exit codes, pass counts and log hashes. Then an independent evidence review on Sonnet 5.5 at high effort. Then one task commit on the local-only branch, on the owner's word.

## 8. Owner decisions

| ID | Answer | Source |
|---|---|---|
| CV-B | New branch `feature/feat066-conv1` from `08439b22`, **local only, never pushed** | Chat, 2026-11-18 ("nhánh này là nhánh chỉ ở máy ko đẩy lên github cho tôi") |
| CV-1 | **B — leave `/api/parent/v1/ai` for C-P** (asked again after review F5) | Chat answer, 2026-11-18 |
| CV-2 | **A — generic codes only**; upload and file codes go to their slices | Chat answer, 2026-11-18 |
| CV-3 | **A — Vietnamese messages from one table** | Chat, 2026-11-18 ("còn lại có hết") |
| CV-4 | **A — missing `If-Match` gives 400 `INVALID_REQUEST` with a field error** | Chat, 2026-11-18 ("còn lại có hết") |
| CV-5 | **404 `RESOURCE_NOT_FOUND`** for an inactive or wrong-role account | Chat answer, 2026-11-18 |

## 9. Proposed Task Approval entry (draft text, not written)

> FEAT-066 CONV-1 — API conventions core. Status: APPROVED_FOR_IMPLEMENTATION when the owner approves this package at its reviewed pin.
> - **Branch:** `feature/feat066-conv1` from `08439b22`, local only, with no push.
> - **Allowlist:** files 1–28 of §4, within each row's stated limit. Edits to tests 16–28 are limited to status, code, envelope and message assertions.
> - **Behaviour:** §3.2 items 1–8, with the §8 answers.
> - **Exclusions:** §3.3.
> - **Verification:** §7.
> - **Git:** no stage or commit without a separate owner word, and never a push.

## 10. Not verified

- Whether every test file in 16–28 needs an edit, and whether another file does. That is a stop condition (§4).
- The exact runtime-schema code path that publishes FastAPI's automatic 422 for families with no `responses=` (`app.py` lines 1174–1368, not traced line by line).
- The `detail` shapes of every `teacher_ai`, `platform_admin_accounts` and `auth_registration` error.
- Whether the root `backend/.venv` (FastAPI 0.141.1, not lock-exact) changes any handler behaviour compared with the lock (0.162.0).
- Deployment proxy behaviour.

No test, runtime, OpenAPI generation or validator was run for this draft.

## 11. Round-1 findings and their fixes

| Finding | Fixed in |
|---|---|
| F1 (P1) | §3.2 item 3: the coverage check runs before the policy call, so scope mismatches give 404 and role refusals give 403; test 15 |
| F2 | §2 OpenAPI row; §3.2 item 8; §4 rows 8, 9, 10 and 17 |
| F3 | §3.2 items 4 and 5; §4 row 7; AC5 narrowed |
| F4 | §2 corrected (422 at line 91); §3.2 item 2a remap and classification |
| F5 | CV-1 asked again, answer B; §3.1; regression guard added |
| F6 | §3.2 item 2e |
| F7 | CV-2 asked for its extent, answer A; §3.2 item 2b table and the kept list |
| F8 | §3.2 item 2c fallback and coverage test |
| F9 | §3.2 item 2d vocabulary and declared-names rule; §3.2 item 7 |
| F10 | Two tests dropped; tool row 11 added |
| F11 | §2 mount table |
| F12 | §3.1 legacy row |
| F13 | §3.2 item 1 |
| F14 | §3.2 item 6 (deferred) |
| F15 | §6 caller list |
| F16 | CV-5 asked, answer 404; §3.2 item 3 |
