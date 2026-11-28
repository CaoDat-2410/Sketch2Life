# Errors and Conventions

- **Date:** 2026-11-25
- **Source tree:** Integration checkout: branch `feature/backend-srs-api-and-fe-integration`, commit `297f2849f9db26bb142123da5e1673dcd58673ae`
- **Canonical SRS authority:** `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (`v2.7-draft`, awaiting formal owner sign-off, per `docs/context/SRS_AUTHORITY.md`)
- **Generated from code by agy and checked by Claude.**
- **Scope note:** Route families implemented in `backend/src/sketch2life/interfaces/http/` (catalog assertions in `backend/tests/contract/test_openapi_contract_catalog.py:355, 384-391`: `183` catalog paths, `212` catalog operations, `232` base runtime operations plus admin and quota operations). Billing/subscription internals not built in integration are marked `owner: Billing/Capacity`.
- **Phase D and E additions:** `2` wire error code rows `PENDING-MERGE` (sources: working trees of the Phase D and E branches on 2026-11-25)

## Table of Contents

1. [Error Envelopes](#1-error-envelopes)
   - [1.1 CONV-1 Standard Envelope](#11-conv-1-standard-envelope)
   - [1.2 Conversion of BE1, Lesson Library, Lesson Occurrences, and Domain Errors into CONV-1](#12-conversion-of-be1-lesson-library-lesson-occurrences-and-domain-errors-into-conv-1)
   - [1.3 Separate and Legacy Envelopes That Still Differ](#13-separate-and-legacy-envelopes-that-still-differ)
2. [Wire Code Catalogue](#2-wire-code-catalogue)
   - [2.1 Authentication, Tokens, Actors, and Rate Limiting](#21-authentication-tokens-actors-and-rate-limiting)
   - [2.2 Request Validation, Idempotency, Concurrency, and Generic CONV-1 Codes](#22-request-validation-idempotency-concurrency-and-generic-conv-1-codes)
   - [2.3 BE1 Organizations, Classes, Enrollments, Consent, Sessions, Canvas, and Records](#23-be1-organizations-classes-enrollments-consent-sessions-canvas-and-records)
   - [2.4 Lesson Library, Moderation, Feedback, and Parent Groups](#24-lesson-library-moderation-feedback-and-parent-groups)
   - [2.5 Lesson Occurrences, Documents, Plans, Child Selection, and Projection](#25-lesson-occurrences-documents-plans-child-selection-and-projection)
   - [2.6 Upload Sessions and Media Validation](#26-upload-sessions-and-media-validation)
   - [2.7 StoryRun Lifecycle, Inputs, Script Review, and Video Generation](#27-storyrun-lifecycle-inputs-script-review-and-video-generation)
   - [2.8 Parent Profiles and Support Needs](#28-parent-profiles-and-support-needs)
   - [2.9 Notifications Inbox and Push Endpoints](#29-notifications-inbox-and-push-endpoints)
   - [2.10 Platform Admin, Audit Retention, Billing/Capacity Sandbox, and Payment Callbacks](#210-platform-admin-audit-retention-billingcapacity-sandbox-and-payment-callbacks)
   - [2.11 Legacy AI, Pilot Assistance, SVG Catalog, and Local Demo Routes](#211-legacy-ai-pilot-assistance-svg-catalog-and-local-demo-routes)
3. [Cross-Cutting Conventions](#3-cross-cutting-conventions)
   - [3.1 Idempotency-Key](#31-idempotency-key)
   - [3.2 ETag, If-Match, and If-None-Match (304)](#32-etag-if-match-and-if-none-match-304)
   - [3.3 Cursor Pagination and `limit`](#33-cursor-pagination-and-limit)
   - [3.4 Correlation ID and `X-Request-ID`](#34-correlation-id-and-x-request-id)
   - [3.5 Authentication, Roles, and Uniform 404 vs. 403](#35-authentication-roles-and-uniform-404-vs-403)
   - [3.6 Rate Limits](#36-rate-limits)

---

## 1. Error Envelopes

### 1.1 CONV-1 Standard Envelope

Per SRS §9.8 and CONV-1 (`backend/src/sketch2life/interfaces/http/error_envelope.py:16-39, 234-244`), requests matching the CONV-1 path families receive a single canonical JSON envelope from `handle_http_exception`, `handle_request_validation_error`, and `handle_unexpected_exception` (`backend/src/sketch2life/interfaces/http/app.py:689-708, 793-806, 930-949`).

**Covered paths (`is_conv1_path` at `error_envelope.py:234-244`, called via `conv1_path` in `app.py:452-455`):**
- Prefixes (`CONV1_PREFIXES`, `error_envelope.py:16-24`):
  - `/api/be1/v1`
  - `/api/lesson-library/v1`
  - `/api/platform-admin/v1`
  - `/api/auth/v1`
  - `/api/teacher/v1/`
  - `/v1/jobs/`
- Whole-segment prefixes (`error_envelope.py:30-38, 238-244`):
  - `/v1/lesson-occurrences`
  - `/v1/notifications` (inbox and `/v1/notifications/push-endpoints` routes)
  - `/v1/upload-sessions` (excluded when `STORYRUN_LITE_MAIN_DEMO_ENABLED=1` and demo routes are active, `app.py:452-455`)

**Wire JSON shape (`build_error_body` at `error_envelope.py:302-323`):**

```json
{
  "code": "STALE_REVISION",
  "message": "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "retryable": false,
  "retry_after_seconds": null,
  "field_errors": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_version": 4
}
```

Field rules in `build_error_body` (`error_envelope.py:302-323`):
- `code` (`string`): Stable `^[A-Z][A-Z0-9_]{0,63}$` machine code (`error_envelope.py:56, 251-261`).
- `message` (`string`): Vietnamese user-safe message resolved from `MESSAGES` (`error_envelope.py:93-164`, including `CLASS_CAPACITY_REACHED`, `CLASS_SELECTION_REQUIRED`, `INVALID_CAPACITY_DOWNGRADE`, `SUBSCRIPTION_PERIOD_ENDED`, `PUSH_PLATFORM_UNSUPPORTED`, `PUSH_REGISTRATION_UNAVAILABLE`, `STALE_SOURCE_VERSION`), or `STATUS_MESSAGES[status]` (`error_envelope.py:166-182`), or generic 4xx/5xx fallback (`error_envelope.py:183-184`). Route-supplied English `detail["message"]` text is never echoed verbatim (`error_envelope.py:5`).
- `correlation_id` (`string`): Always equal to `request_id` (`error_envelope.py:315`), echoed in response header `X-Request-ID` (`app.py:521-522, 707, 805, 948`).
- `request_id` (`string`): Same value as `correlation_id` (`error_envelope.py:319`).
- `retryable` (`boolean`): `true` if and only if `status in {429, 502, 503, 504}` (`error_envelope.py:316`).
- `retry_after_seconds` (`integer | null`): Parsed from response header `Retry-After` when digits-only, else `null` (`error_envelope.py:292-299, 317`).
- `field_errors` (`array | null`): List of `{"field": "<loc>", "code": "<FIELD_CODE>"}` or `null` when empty (`error_envelope.py:40-54, 273-289, 318`). `normalize_http_error` filters `field_errors` to `FIELD_ERROR_CODES` (`REQUIRED`, `TOO_LONG`, `OUT_OF_RANGE`, `EMPTY`, `INVALID_TYPE`, `INVALID_FORMAT`, `UNKNOWN_FIELD`, `NOT_SUPPORTED`, max field name `120` chars, `error_envelope.py:40-57, 273-289`). FastAPI validation errors on CONV-1 paths also pass through `field_errors_from_validation` (`api_conventions.py:222-247`), which maps `diagnosis_like` -> `DIAGNOSIS_LIKE` (`api_conventions.py:55`).
- `current_version` (`integer`, conditional): Included **only** when `code == "STALE_REVISION"` and `detail["current_version"]` is a strict `int` (`type(...) is int`, `error_envelope.py:321-322, 344`).

### 1.2 Conversion of BE1, Lesson Library, Lesson Occurrences, and Domain Errors into CONV-1

Routers and middleware in CONV-1 route families raise standard `HTTPException` or typed domain exceptions, which routers translate to `HTTPException(detail=...)` before `app.py` applies `normalize_http_error` (`error_envelope.py:326-344`):

1. **BE1 routers (`be1_common.py:72-97`):** `failure(status_code, code, message, etag=...)` raises `HTTPException(status_code=status_code, detail={"code": code, "message": message}, headers={"ETag": f'"{etag}"'} if etag)`. `handle_http_exception` drops the English `message` and wraps `code` into CONV-1 while preserving headers such as `ETag` and `Retry-After` (`app.py:707`).
2. **Lesson Library (`lesson_library.py:92-107`, `lesson_library/service.py:56-65`):** `fail(status, code, message)` raises `LessonLibraryError`. The `_call` wrapper (`lesson_library.py:92-107`) maps:
   - Missing optional dependency -> `503 DEPENDENCY_UNAVAILABLE` -> normalized to `503 PROVIDER_UNAVAILABLE` (`error_envelope.py:71`).
   - `code == "STALE_REVISION"` -> `raise_stale_revision(current_version=exc.current_revision, etag=str(exc.current_revision))` (`api_conventions.py:152-160`), emitting HTTP `409` with `ETag: "<rev>"` and `"current_version": <rev>`.
   - Any other `LessonLibraryError` -> `HTTPException(exc.status_code, detail={"code": exc.code, "message": exc.message, "field_errors": exc.field_errors})`. (`lesson_library/service.py` raises `400 INVALID_IDEMPOTENCY_KEY` directly on key reuse.)
3. **Lesson Occurrences (`lesson_occurrences.py:174-200`), Upload Sessions (`upload_sessions.py:59-83`), Notifications (`notifications.py:84-93`), Platform Admin (`platform_admin.py:95-100`, `platform_admin_accounts.py:224-229`):** Each helper converts its domain exception (`LessonOccurrenceError`, `DocumentError`, `UploadSessionError`, `NotificationError`, `PushEndpointError`, `AdminError`) to `HTTPException(status_code, detail={"code": ..., ...})`.
4. **Central normalization (`normalize_http_error` at `error_envelope.py:326-344`):**
   - **422 validation rewrite (`error_envelope.py:231, 334-342`):** If `exc.status_code == 422` and raw `code` is missing or in `{"INVALID_REQUEST", "IDEMPOTENCY_KEY_REQUIRED"}`, HTTP status is rewritten to **`400`** and `code` to **`INVALID_REQUEST`**. When raw code was `IDEMPOTENCY_KEY_REQUIRED`, it injects `field_errors=[{"field": "Idempotency-Key", "code": "INVALID_FORMAT" if idempotency_header_present else "REQUIRED"}]`.
   - **Generic code remapping (`GENERIC_CODE_MAP` at `error_envelope.py:60-72, 257-258`):**
     - `AUTHENTICATION_REQUIRED`, `UNAUTHENTICATED` -> `AUTH_REQUIRED`
     - `INVALID_IDENTITY_TOKEN` -> `INVALID_TOKEN`
     - `FORBIDDEN` -> `ACTION_NOT_ALLOWED`
     - `NOT_FOUND` -> `RESOURCE_NOT_FOUND`
     - `CONFLICT`, `INVALID_TRANSITION` -> `INVALID_STATE_TRANSITION`
     - `REQUEST_VALIDATION_FAILED` -> `INVALID_REQUEST`
     - `SERVICE_UNAVAILABLE`, `DEPENDENCY_UNAVAILABLE` -> `PROVIDER_UNAVAILABLE`
   - **404 normalization (`error_envelope.py:75, 259-260`):** Any `404` code ending with `_NOT_FOUND` (e.g., `CLASS_NOT_FOUND`, `SESSION_NOT_FOUND`, `LESSON_NOT_FOUND`, `CONSENT_NOT_FOUND`) becomes `RESOURCE_NOT_FOUND`, except `KEPT_404_CODES` (`JOIN_UNAVAILABLE`, `CANVAS_SOURCE_UNAVAILABLE`).
   - **Domain code preservation (`STATUS_MESSAGE_ONLY` at `error_envelope.py:188-228`):** Domain-specific codes listed in `STATUS_MESSAGE_ONLY` keep their exact `code` string on the wire and receive the Vietnamese `STATUS_MESSAGES[status]`.

### 1.3 Separate and Legacy Envelopes That Still Differ

Routes outside `is_conv1_path` use one of six separate or legacy error formats:

| Envelope family | Path scope | Wire JSON format & key differences from CONV-1 | Code reference |
|---|---|---|---|
| **StoryRun & `/v1/activities` & legacy Parent AI story/drawing** (`ParentStoryErrorEnvelopeV1`) | `/v1/story-runs*`, `/v1/activities*`, `/api/parent/v1/ai/story-runs/{id}/story-revisions`, `/api/parent/v1/ai/drawing-understandings` | `{code, message (Vietnamese), correlation_id, retryable (status in {429,502,503,504}), retry_after_seconds, field_errors}` plus `current_version` **only** on `/v1/story-runs*` for `409 STALE_REVISION`. **Differs:** omits `request_id`; keeps raw uppercase codes outside `safe_messages` (no `GENERIC_CODE_MAP`); attaches `"message": "Giá trị trường không hợp lệ."` to `field_errors`; on `/v1/story-runs*` a bad `Idempotency-Key` validation error emits plain `400 INVALID_REQUEST` with `field_errors: null`, while the non-`/v1/story-runs` subset emits `400 INVALID_IDEMPOTENCY_KEY`. | `app.py:529-627, 714-778, 886-909`, `contracts/schemas/parent_story.py` |
| **Parent Profiles** (`ParentErrorResponse`) | `/v1/parent/profiles*` | `parent_error_payload`: `{code, message (English), correlation_id, retryable (status in {429,503}), request_id}` plus optional `field_errors` (omitted when null/empty) and optional `current_version`. **Differs:** English messages, omits `retry_after_seconds`, excludes `502`/`504` from `retryable`, maps unknown codes to `default_codes` (`404->PROFILE_NOT_FOUND`, `409->INVALID_REQUEST`, `503->PARENT_STORE_UNAVAILABLE`), `RequestValidationError` returns `400 INVALID_REQUEST` via `parent_field_errors` (allows `DIAGNOSIS_LIKE`). | `app.py:628-686, 779-790, 910-927`, `contracts/schemas/parent_profiles.py:207-296` |
| **StoryRun-Lite Local Demo** | `/v1/upload-sessions*` and `/v1/story-runs*` when `STORYRUN_LITE_MAIN_DEMO_ENABLED=1` | `{code, message (English), correlation_id (honors X-Correlation-ID), retryable, field_errors?}` with `Cache-Control: no-store`. Validation errors return **422 `INVALID_REQUEST`**; unhandled returns **500 `INTERNAL_ERROR`**; non-loopback gets **403 `{"detail": "Local demo only"}`**. | `story_run_lite.py:316-368`, `app.py:484-503, 712-713, 884-885` |
| **Mobile Demo Workflow (`MobileWorkflowResultV1`) & Renderer/Media Demo** | `/v1/sessions*`, `/v1/profile*`, `/p1/context-options*`, `/v1/sessions/*/story-video*`, `/v1/sessions/*/whiteboard-video*`, renderer source endpoints | `MobileWorkflowResultV1` `{contract_version, status: "error", correlation_id, error: {code, message, retryable}, ...}` on session/profile/context-options routes. Renderer asset errors return `{"code"}` / `{"code", "message"}` / `{"code", "reason"}` (`supervised_flow.py:415-508`). `story_video.py` & `whiteboard_video.py` raise `HTTPException(detail="<STRING_CODE>")` -> `{"detail": "<CODE>"}`. | `sessions.py:32-75`, `supervised_flow.py:415-508, 570-584`, `images.py:261-276`, `child_preferences.py:103-116`, `app.py:851-880`, `story_video.py:24-125`, `whiteboard_video.py:23-115` |
| **BE2 Candidate Review / Knowledge Video** | `/api/v1/video-reviews*`, `/api/v1/knowledge-videos*` (candidate routers) | Nested `{"correlation_id": ..., "error": {"code": ..., "message": "Request could not be completed.", "retryable": status == 503}}`. | `video_review.py:66-75`, `knowledge_video.py:56-65` |
| **Default FastAPI Legacy & Payment Callbacks** | `/api/parent/v1/topics*`, `/api/teacher/v1/ai`? *(note: `/api/teacher/v1/` IS in CONV1_PREFIXES!)*, `/api/svg-catalog/v1*`, `/v1/pilot-assistance*`, `/api/learning-content/*`, `/api/parent/v1/ai/runs/{id}/lessons/*` (other unmapped paths), `/api/payment-callbacks/v1/*` | Non-CONV-1, non-StoryRun, non-ParentProfile paths fall through to FastAPI `http_exception_handler` (`{"detail": ...}`), `RequestValidationError` -> **422 `{"detail": "request contract invalid"}`**, unhandled 500 -> plain text `"Internal Server Error"`. **Payment Callbacks:** VNPay IPN/return responds HTTP 200 JSON `{"RspCode": "00"\|"01"\|"02"\|"04"\|"97"\|"99", "Message": ...}`; MoMo IPN returns HTTP 204 or FastAPI `{"detail": ...}`. | `app.py:687-688, 805-850, 929-935`, `payment_callbacks.py:58-171`, `parent_topic_suggestions.py:56-317`, `svg_catalog.py:52-409`, `pilot_assistance.py:323-527` |

---

## 2. Wire Code Catalogue

Every code below is verified from backend source files on integration commit `297f2849`. For CONV-1 paths, `normalize_http_error` (`error_envelope.py:326-344`) remaps legacy codes in `GENERIC_CODE_MAP` (`error_envelope.py:60-72`) and `404 *_NOT_FOUND` codes (except `KEPT_404_CODES`); both the raised internal code and the effective wire code are noted where they differ. Retryable reflects runtime HTTP status behavior: **`Yes`** for `429, 502, 503, 504` on CONV-1 and StoryRun envelopes (`429, 503` on Parent Profiles), **`No`** otherwise unless a domain envelope overrides it.

### 2.1 Authentication, Tokens, Actors, and Rate Limiting

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `AUTH_REQUIRED` | 401 | Missing or unverified Bearer ID token (also wire normalization of `AUTHENTICATION_REQUIRED` / `UNAUTHENTICATED`). | `be1_runtime.py:216` (`AUTHENTICATION_REQUIRED` -> `AUTH_REQUIRED`, `/api/be1/v1/*`, `/api/lesson-library/v1/*`, `/v1/jobs/*`, `/v1/lesson-occurrences*`, `/v1/upload-sessions*`, `/v1/notifications*`); `parent_runtime.py:63` (`/v1/parent/profiles*`, `/v1/story-runs*`, `/v1/activities*`); `probe_access.py:97` (probe auth) | No |
| `INVALID_TOKEN` | 401 | Malformed, revoked, or unverifiable Firebase ID token or video playback token (normalizes `INVALID_IDENTITY_TOKEN`). | `be1_runtime.py:224` (`INVALID_IDENTITY_TOKEN` -> `INVALID_TOKEN`, CONV-1 auth); `parent_runtime.py:92` (`/v1/parent/profiles*`, `/v1/story-runs*`); `services/story_run_playback.py:104` (`/v1/story-runs/{id}/video/play`, playback token) | No |
| `TOKEN_EXPIRED` | 401 | Expired Firebase ID token or expired video playback token. | `parent_runtime.py:88` (`/v1/parent/profiles*`, `/v1/story-runs*`); `services/story_run_playback.py:104` (`/v1/story-runs/{id}/video/play`, mapped in `app.py:574`) | No |
| `ACTION_NOT_ALLOWED` | 403 / 405 | Authenticated actor lacks permission for the operation or HTTP method (normalizes `FORBIDDEN` on CONV-1 paths). | `be1_common.py:151, 181` (`/api/be1/v1/*`); `lesson_library.py:167` (`FORBIDDEN` -> `ACTION_NOT_ALLOWED`, `/api/lesson-library/v1/*`); `platform_admin_accounts.py:234` (`FORBIDDEN`, `/api/platform-admin/v1/*`); `lesson_occurrences/child_selection.py:291`, `lesson_occurrences/scope.py:124`, `lesson_occurrences/projection.py:136` (`/v1/lesson-occurrences*`); `infrastructure/story_teacher/repository.py:316` (`/v1/story-runs*`); `error_envelope.py:64, 79, 81` (`405` default) | No |
| `ACCOUNT_SCOPE_UNAVAILABLE` | 403 | Authenticated adult has no active organization/account scope assignment for the route. | `routers/lesson_library.py:147` (`/api/lesson-library/v1/*`); `infrastructure/billing/quota_commerce.py:1265` (`/api/be1/v1/*` billing/quota); `error_envelope.py:175` | No |
| `EMAIL_VERIFICATION_REQUIRED` | 403 | Account email is not yet verified in Firebase / registration flow. | `routers/auth_registration.py:302` (`/api/auth/v1/*`) | No |
| `IDENTITY_PROVIDER_UNAVAILABLE` | 503 | Firebase Auth / identity provider dependency failed or is unconfigured. | `be1_runtime.py:221` (CONV-1); `parent_runtime.py:48, 68, 80` (`/v1/parent/profiles*`, `/v1/story-runs*`); `routers/auth_registration.py:219` (`/api/auth/v1/*`); `routers/platform_admin_accounts.py:383, 540, 801` (`/api/platform-admin/v1/*`) | Yes |
| `IDENTITY_ISSUER_MISMATCH` | 401 | Identity token issuer does not match expected project configuration (`STATUS_MESSAGE_ONLY`). | `error_envelope.py:192` (CONV-1 identity adapter) | No |
| `ACCOUNT_SETUP_UNAVAILABLE` | 409 / 503 | Account registration or `/me` setup cannot complete in current state or dependency is down. | `routers/auth_registration.py:211, 244, 257, 338` (`/api/auth/v1/*`); `routers/platform_admin_accounts.py:535, 616, 626` (`/api/platform-admin/v1/*`) | Yes (503) / No (409) |
| `ACCOUNT_UPDATE_UNAVAILABLE` | 503 | Account status/role update failed against persistence or identity store. | `routers/platform_admin_accounts.py:814` (`/api/platform-admin/v1/accounts*`) | Yes |
| `BE1_RUNTIME_UNAVAILABLE` | 503 | BE1 database runtime is not initialized in app state. | `be1_runtime.py:173` (BE1 / CONV-1 runtime routes) | Yes |
| `DATABASE_NOT_CONFIGURED` | 503 | Database URL / engine is not configured for the runtime. | `be1_runtime.py:175` (BE1); `routers/be1_canvas.py:88` (`/api/be1/v1/*`); `routers/jobs.py:139` (`/v1/jobs/{job_id}`) | Yes |
| `DATABASE_UNAVAILABLE` | 503 | Database connection or query execution failure in runtime dependency. | `be1_runtime.py:203` (BE1 / CONV-1); `routers/jobs.py:267` (`/v1/jobs/{job_id}`) | Yes |
| `DEVICE_AUTHENTICATION_REQUIRED` | 401 | Classroom child device request lacks current device credential header/proof. | `be1_runtime.py:234, 376` (`/api/be1/v1/*` device routes); `routers/be1_sessions.py:1259, 1488` | No |
| `INVALID_DEVICE_CREDENTIAL` | 401 | Submitted classroom device proof/grant token was rejected. | `be1_runtime.py:243, 389` (`/api/be1/v1/*` device routes); `routers/be1_sessions.py:1263, 1498, 1504` | No |
| `DEVICE_SCOPE_INACTIVE` | 403 | Classroom device grant exists but its session/classroom scope is inactive. | `be1_runtime.py:252, 395, 398, 414` (`/api/be1/v1/*` device routes) | No |
| `DEVICE_MEMBERSHIP_INACTIVE` | 403 | Child membership bound to device credential is inactive. | `be1_runtime.py:263, 433` (`/api/be1/v1/*` device routes) | No |
| `RATE_LIMITED` | 429 | Sliding-window account/IP rate limit exceeded; includes `Retry-After` seconds header. | `routers/be1_registry.py:1306` (`/api/be1/v1/classes/{id}/enrollments` real-profile gate); `routers/auth_registration.py:195` (`/api/auth/v1/*`); `routers/password_recovery.py:25` (`/api/auth/v1/*`); `application/services/assistance.py:619`; `error_envelope.py:85, 104` | Yes |

### 2.2 Request Validation, Idempotency, Concurrency, and Generic CONV-1 Codes

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `INVALID_REQUEST` | 400 (422 on StoryRun-lite / unmapped) | Malformed JSON, schema validation error, bad cursor/limit, missing/invalid `Idempotency-Key` or `If-Match`, or Phase B diagnosis-like text rejection. CONV-1 rewrites 422 `INVALID_REQUEST` / `IDEMPOTENCY_KEY_REQUIRED` to 400 (`error_envelope.py:231, 334-342`). | `app.py:763, 783, 795` (all routers); `api_conventions.py:70, 143, 145, 148`; `domain/parent_profiles.py:73-136` (`/v1/parent/profiles*`); `application/services/support_needs.py:62` (`PUT .../support-needs`); `infrastructure/lesson_occurrences/plans.py:426, 601, 616, 687`; `infrastructure/lesson_library/service.py:133-185, 211`; `domain/story_run_lite.py:120, 128, 178` (`422`) | No |
| `INVALID_IDEMPOTENCY_KEY` | 400 | Same `Idempotency-Key` reused with a different request fingerprint/payload (or malformed header on legacy AI routes `app.py:761`). | `routers/be1_registry.py:438, 642, 762, 1108, 1552, 1935, 2491, 2848, 2866` (`/api/be1/v1/*`); `infrastructure/lesson_library/service.py:1112, 1190, 2868` (`/api/lesson-library/v1/*`); `infrastructure/lesson_occurrences/*` (`service.py:160`, `documents.py:610, 827`, `plans.py:273`, `child_selection.py:541`, `projection.py:223`); `infrastructure/persistence/parent_profile_repository.py:498`; `infrastructure/persistence/support_needs_repository.py:247`; `infrastructure/persistence/parent_story_repository.py:854, 989, 5010` (`/v1/story-runs*`); `infrastructure/story_video/repository.py:133, 262, 300, 1047`; `application/services/push_endpoints.py:494, 514` | No |
| `IDEMPOTENCY_KEY_REQUIRED` | 422 (normalized to 400 `INVALID_REQUEST` on CONV-1) | Missing or invalid `Idempotency-Key` header in legacy `be1_sessions.py`; CONV-1 turns this into 400 `INVALID_REQUEST` with `field_errors` (`error_envelope.py:334-342`). | `routers/be1_sessions.py:129` (`/api/be1/v1/sessions*`); `error_envelope.py:231, 334-342` | No |
| `IDEMPOTENCY_KEY_REUSED` | 409 | Session command reuses `Idempotency-Key` for a different request in `be1_sessions`. | `routers/be1_sessions.py:435` (`/api/be1/v1/sessions*`); `error_envelope.py:206` (`STATUS_MESSAGE_ONLY`) | No |
| `IDEMPOTENCY_RECEIPT_INCOMPATIBLE` | 409 | Stored Lesson Library idempotency receipt cannot be replayed under current response contract. | `infrastructure/lesson_library/service.py:1260` (`/api/lesson-library/v1/*`) | No |
| `IDEMPOTENCY_CONFLICT` | 409 | Concurrent or conflicting idempotency key in billing commerce or pilot assistance. | `infrastructure/billing/quota_commerce.py:80, 286`; `application/services/assistance.py:353, 851` | No |
| `PRECONDITION_REQUIRED` | 428 | Required `If-Match` header omitted on platform admin, StoryRun-lite, or Lesson Library group member removal. | `routers/platform_admin.py:82` (`/api/platform-admin/v1/*`); `domain/story_run_lite.py:145`; `routers/lesson_library.py:134` (`DELETE .../members/{membership_id}`) | No |
| `INVALID_REVISION` | 422 | `If-Match` header could not be parsed as a valid positive revision integer in billing or platform admin. | `routers/be1_billing.py:359, 361, 386, 388` (`/api/be1/v1/*`); `routers/platform_admin.py:91` (`/api/platform-admin/v1/*`); `error_envelope.py:191` | No |
| `STALE_REVISION` | 409 | `If-Match` or expected version/hash disagrees with current resource revision; CONV-1 and StoryRun responses include `current_version` (`int`) and often `ETag`. | `api_conventions.py:155` (`/api/be1/v1/*`, `/api/lesson-library/v1/*`, `/v1/lesson-occurrences*`, `/v1/upload-sessions*`); `infrastructure/persistence/parent_profile_repository.py` + `support_needs_repository.py:134` (`/v1/parent/profiles*`); `infrastructure/persistence/parent_story_repository.py:1215, 1464, 1759, 2249, 2909, 3613, 4141, 4263` (Phase A remaps `PARENT_STORY_REVISION_STALE` -> `STALE_REVISION`); `infrastructure/story_video/repository.py:456, 485, 1058, 1065`; `application/services/push_endpoints.py:309, 349` | No |
| `RESOURCE_NOT_FOUND` | 404 | Target missing, outside caller's org/class/owner scope, or caller lacks role (anti-enumeration uniform 404). CONV-1 normalizes `NOT_FOUND` and most `*_NOT_FOUND` to `RESOURCE_NOT_FOUND`. | `be1_common.py:85`; `be1_registry.py:130`; `routers/jobs.py:156`; `story_run_actor.py:41`; `lesson_occurrences/scope.py:65`; `notifications/inbox_repository.py:74`; `infrastructure/persistence/parent_story_repository.py:298, 4549`; `infrastructure/story_video/repository.py:346`; `infrastructure/uploads/service.py:112`; `routers/lesson_library.py:165`; `application/services/push_endpoints.py:621` | No |
| `RESOURCE_CONFLICT` | 409 | Unique/integrity constraint conflict or resource already attached/exists. | `be1_common.py:74`; `be1_registry.py:474, 713, 860, 1507, 1819, 2261, 2330, 2629`; `lesson_library/service.py:656, 1601`; `lesson_occurrences/service.py:298`; `lesson_occurrences/documents.py:366, 475, 493, 681`; `uploads/service.py:345, 591` | No |
| `INVALID_STATE_TRANSITION` | 409 | Command disallowed in current resource/workflow state (CONV-1 normalizes `CONFLICT`/`INVALID_TRANSITION`; Phase A remaps `PARENT_STORY_CONFIRMATION_CONFLICT` and rewrite gate codes here). | `be1_common.py:205`; `be1_registry.py:451, 1163, 1740, 2072, 2103, 2110, 2566`; `lesson_library/service.py:2587, 2686`; `lesson_occurrences/*` (`plans.py:356, 671`, `child_selection.py:348, 789, 837`, `projection.py:111`); `parent_story_repository.py:877, 1032, 1221, 1367, 3596, 3617`; `parent_story_inputs.py:491-497`; `support_needs_repository.py:241` | No |
| `PROVIDER_UNAVAILABLE` | 503 / 504 | Downstream storage, DB, parser, AI, or external provider unavailable (CONV-1 normalizes `SERVICE_UNAVAILABLE` & `DEPENDENCY_UNAVAILABLE`). | `lesson_occurrences/documents.py:163, 394, 499`; `lesson_occurrences/plans.py:114`; `lesson_occurrences/service.py:304`; `lesson_occurrences/child_selection.py:257`; `lesson_occurrences/projection.py:103`; `routers/lesson_library.py:87` (`DEPENDENCY_UNAVAILABLE` -> `PROVIDER_UNAVAILABLE`); `routers/notifications.py:225, 275` (`DEPENDENCY_UNAVAILABLE` -> `PROVIDER_UNAVAILABLE`); `routers/be1_registry.py:668, 679, 734` (`DEPENDENCY_UNAVAILABLE` -> `PROVIDER_UNAVAILABLE`); `infrastructure/story_video/repository.py:502`; `uploads/service.py:348` | Yes |
| `PROVIDER_BAD_RESPONSE` | 502 | Upstream provider returned invalid/unexpected payload (`STATUS_DEFAULT_CODES`). | `error_envelope.py:87, 103`; `app.py:547, 585` | Yes |
| `INTERNAL_SERVER_ERROR` | 500 | Unhandled server exception on CONV-1, StoryRun, Parent Profile, or `/v1/jobs/{job_id}`. | `app.py:898, 917, 941`; `routers/jobs.py:277` | No |

**Validation `field_errors[].code` taxonomy (`error_envelope.py:40-54`, `api_conventions.py:36-56`, `contracts/schemas/parent_profiles.py:261-262`):**

| Field code | Source type / validator trigger | Envelope support | Source |
|---|---|---|---|
| `REQUIRED` | Missing required header/field/query (`missing`) | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:42`, `api_conventions.py:37` |
| `TOO_LONG` | String or array length above max (`string_too_long`, `too_long`) | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:43`, `api_conventions.py:38-39` |
| `OUT_OF_RANGE` | Numeric bound failure (`greater_than*`, `less_than*`, `limit` outside `1..100`) | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:44`, `api_conventions.py:40-43` |
| `EMPTY` | Blank/too-short string or empty required array (`string_too_short`, `too_short`) | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:45`, `api_conventions.py:44-45` |
| `INVALID_TYPE` | Type mismatch (`int_type`, `string_type`, etc.) | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:46`, `api_conventions.py:46-53` |
| `INVALID_FORMAT` | Pattern, UUID, cursor, date/time, NUL/surrogate, or `If-Match`/`Idempotency-Key` syntax failure | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:47`, `be1_registry.py:215`, `api_conventions.py:119` |
| `UNKNOWN_FIELD` | Extra forbidden field (`extra="forbid"`, `extra_forbidden`) | CONV-1, StoryRun, Parent Profiles | `error_envelope.py:48`, `api_conventions.py:54` |
| `NOT_SUPPORTED` | Explicitly unsupported feature/variant (e.g., `CUSTOM`/`CATALOG` plan activity without checklist) | CONV-1, StoryRun | `error_envelope.py:52`, `lesson_occurrences/plans.py:601` |
| `DIAGNOSIS_LIKE` | **Phase B (`T-12b-fix`, BR-20):** disallowed diagnostic/medical label in Parent profile `interests_summary` or support-needs `note` (`field_errors_from_validation` + `parent_field_errors`; note `normalize_http_error` whitelists `FIELD_ERROR_CODES`) | Parent Profiles (`/v1/parent/profiles*`), `support_needs`, Pydantic validation (`api_conventions.py:55`) | `domain/parent_profiles.py:124`, `api_conventions.py:55`, `contracts/schemas/parent_profiles.py:261-262` |
| `INVALID_VALUE` | Disallowed enum/value outside allowed reason codes (e.g., `video-unsuitable` `reason_code`) | StoryRun envelope (`_story_field_errors` accepts any string code) | `services/story_run_video.py:310`, `app.py:209-236` |
| `NOT_ALLOWED` | Disallowed context entry ID on `POST /v1/story-runs/{id}/context-confirmation` | StoryRun envelope | `parent_story_repository.py:1177` |

### 2.3 BE1 Organizations, Classes, Enrollments, Consent, Sessions, Canvas, and Records

*(Route family: `/api/be1/v1/*`, normalized into CONV-1 by `app.py:689-706`.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `CLASS_CAPACITY_REACHED` | 409 | Organization has no available class slots under its current effective capacity (`T-CAP1`). | `routers/be1_registry.py:996` (`POST /api/be1/v1/organizations/{organization_id}/classes`); `error_envelope.py:102` | No |
| `CLASS_TEACHER_EXISTS` | 409 | Classroom already has an active primary Teacher assigned. | `routers/be1_registry.py:446` (`PUT/POST /api/be1/v1/.../classes/{id}/teacher*`) | No |
| `CLASS_SCOPE_MISMATCH` | 422 | Body `class_id` or `session` does not match path class scope. | `routers/be1_registry.py:2662` (`/api/be1/v1/classes/{id}/...`); `routers/be1_records.py:343` (`/api/be1/v1/classes/{id}/observations`) | No |
| `CONSENT_NOT_EFFECTIVE` | 409 | Pending or unverified guardian consent / purpose approval blocks real child profile data. | `be1_common.py:498`, `be1_runtime.py:305, 455`, `routers/be1_records.py:430` (`/api/be1/v1/*`) | No |
| `PILOT_PROFILE_LOOKUP_UNAVAILABLE` | 409 | Synthetic pilot profile lookup disabled outside allowed lobby mode. | `routers/be1_registry.py:1038` (`/api/be1/v1/*`) | No |
| `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE` | 409 | Synthetic profile creation disabled in current configuration. | `routers/be1_registry.py:1241` (`/api/be1/v1/classes/{id}/profiles*`) | No |
| `AGGREGATE_SCOPE_CONFLICT` | 409 | Resource scope (`organization_id`, `class_id`, `session_id`) does not match aggregate root. | `be1_common.py:278` (`/api/be1/v1/*`) | No |
| `STALE_AGGREGATE` | 409 | Optimistic concurrency mismatch on BE1 aggregate write. | `be1_common.py:79` (`/api/be1/v1/*`) | No |
| `ROOM_CODE_UNAVAILABLE` | 503 | Room-code generator not configured or failed to allocate a unique code. | `routers/be1_sessions.py:107, 110, 136, 140, 1184` (`/api/be1/v1/sessions*`) | Yes |
| `ROOM_CODE_CLOSED` | 409 | Room code unavailable once session leaves lobby state. | `routers/be1_sessions.py:1172` (`/api/be1/v1/sessions*`) | No |
| `ROOM_CODE_RATE_LIMITED` | 429 | Exceeded per-session room-code join attempt limit (`_ROOM_CODE_RATE_LIMIT = 10`). | `routers/be1_sessions.py:93, 163, 1228` (`/api/be1/v1/sessions/join*`) | Yes |
| `JOIN_UNAVAILABLE` | 404 | Anti-enumeration `KEPT_404_CODES` code when session/room code is not accepting joins. | `routers/be1_sessions.py:1097, 1236, 1248`; `error_envelope.py:74` (`/api/be1/v1/sessions/join*`) | No |
| `JOIN_WINDOW_CLOSED` | 409 | Session join window closed; new join requests refused. | `routers/be1_sessions.py:1318` (`/api/be1/v1/sessions*`) | No |
| `MEMBER_ALREADY_ADMITTED` | 409 | Child already holds an admitted device grant in the session. | `routers/be1_sessions.py:1366` (`/api/be1/v1/sessions*`) | No |
| `DEVICE_GRANT_INACTIVE` | 409 | Session no longer accepts device credential refresh. | `routers/be1_sessions.py:1507` (`/api/be1/v1/sessions*`) | No |
| `RESERVED_CONFIGURATION_KEY` | 422 | Session config payload contains a server-reserved key. | `routers/be1_sessions.py:212` (`/api/be1/v1/sessions*`) | No |
| `SESSION_NOT_OPEN` | 409 | Groups/membership control requires an open (`lobby` or `active`) session. | `routers/be1_sessions.py:1549, 1704` (`/api/be1/v1/sessions*`) | No |
| `SESSION_NOT_IN_LOBBY` | 409 | Operation (pilot profile lookup) only permitted in `lobby` state. | `routers/be1_registry.py:1044` (`/api/be1/v1/*`) | No |
| `SESSION_NOT_ACTIVE` | 409 | Learning stage advances and turns require an active session. | `routers/be1_sessions.py:522, 1962` (`/api/be1/v1/sessions*`) | No |
| `SESSION_NOT_RUNNING` | 409 | Completion/end-early requires a started/running session. | `routers/be1_sessions.py:998` (`/api/be1/v1/sessions*`) | No |
| `SESSION_OUTCOME_ALREADY_RECORDED` | 409 | Session outcome was already recorded. | `routers/be1_sessions.py:1002` (`/api/be1/v1/sessions*`) | No |
| `STALE_SESSION_REVISION` | 409 | Session revision mismatch (`If-Match` / expected revision). | `routers/be1_sessions.py:737, 1622, 1702` (`/api/be1/v1/sessions*`) | No |
| `LEARNING_STAGE_UNAVAILABLE` | 409 | Classroom learning stage was not initialized for the session. | `routers/be1_sessions.py:288, 518, 992` (`/api/be1/v1/sessions*`) | No |
| `STALE_STAGE_REVISION` | 409 | Learning stage changed concurrently; reload before retrying. | `routers/be1_sessions.py:520, 994` (`/api/be1/v1/sessions*`) | No |
| `LEARNING_STAGE_CONFLICT` | 409 | Learning stage conflict (`be1_sessions`). | `routers/be1_sessions.py:753` (`/api/be1/v1/sessions*`) | No |
| `INVALID_STAGE_TRANSITION` | 409 | Requested SRS stage advance violates stage progression rules. | `routers/be1_sessions.py:528` (`/api/be1/v1/sessions*`) | No |
| `SRS_STAGE_CONTRACT_UNAVAILABLE` | 409 | Stage lacks required approved media, activity, or child-reflection contract before advance. | `routers/be1_sessions.py:567` (`/api/be1/v1/sessions*`) | No |
| `DRAWING_RECEIPT_REQUIRED` | 409 | Active group lacks server-issued drawing turn or durable checkpoint before leaving Explore & Draw. | `routers/be1_sessions.py:593, 619` (`/api/be1/v1/sessions*`) | No |
| `ASSISTANCE_REVIEW_PENDING` | 409 | Requested assistance lacks an approved completion contract before stage advance. | `routers/be1_sessions.py:540` (`/api/be1/v1/sessions*`) | No |
| `ASSISTANCE_DISPOSITION_REQUIRED` | 409 | Requires recording `not_needed` before leaving Assistance stage. | `routers/be1_sessions.py:546` (`/api/be1/v1/sessions*`) | No |
| `PUBLISHED_GALLERY_REQUIRED` | 409 | Requires publishing a consent-checked class gallery before continuing. | `routers/be1_sessions.py:561` (`/api/be1/v1/sessions*`) | No |
| `UNFINISHED_GROUP_SET_MISMATCH` | 409 | Client must declare every unfinished group before advancing stage. | `routers/be1_sessions.py:640` (`/api/be1/v1/sessions*`) | No |
| `GROUP_DRAFT_REQUIRED` | 409 | Unfinished group work must be saved before advancing. | `routers/be1_sessions.py:646` (`/api/be1/v1/sessions*`) | No |
| `COMPLETION_STAGE_REQUIRED` | 409 | Final SRS stage must be reached before completing session. | `routers/be1_sessions.py:996` (`/api/be1/v1/sessions*`) | No |
| `INVALID_GROUP_TRANSITION` | 409 | Archived session groups cannot be reopened. | `routers/be1_sessions.py:1723` (`/api/be1/v1/sessions*`) | No |
| `GROUP_NOT_WRITABLE` | 409 / 403 | Group is not writable for child turn submission. | `routers/be1_sessions.py:1972`; `be1_runtime.py:272` | No |
| `ADMITTED_MEMBER_REQUIRED` | 409 | Turn requires an admitted member with an assigned group. | `routers/be1_sessions.py:1983` | No |
| `ACTIVE_TURN_REQUIRED` | 403 | Device operation requires an active drawing turn (`be1_runtime`). | `be1_runtime.py:283` | No |
| `CANVAS_SOURCE_UNAVAILABLE` | 409 / 404 | `KEPT_404_CODES` anti-enumeration / unavailable canvas source code. | `routers/be1_canvas.py:83` (`409`); `routers/be1_artifacts.py:110` (`404`); `error_envelope.py:74` | No |
| `CANVAS_SOURCE_TOO_LARGE` | 409 | Canvas source exceeds pilot capacity. | `routers/be1_canvas.py:187`; `routers/be1_artifacts.py:73` | No |
| `CANVAS_CAPACITY_REACHED` | 409 | Canvas reached pilot operation/node limit. | `routers/be1_canvas.py:350` | No |
| `STALE_CANVAS_REVISION` | 409 | Canvas changed concurrently; reload before checkpointing, restoring, or rendering. | `routers/be1_canvas.py:588, 768, 780`; `routers/be1_artifacts.py:136` | No |
| `CHECKPOINT_OPERATION_REQUIRED` | 409 | Canvas checkpoint request missing accepted operation. | `routers/be1_canvas.py:598` | No |
| `CHECKPOINT_STORAGE_INTEGRITY` | 500 | Stored canvas checkpoint failed integrity verification on write. | `routers/be1_canvas.py:608` | No |
| `CHECKPOINT_UNAVAILABLE` | 410 | Canvas checkpoint bytes are missing or failed integrity check on read. | `routers/be1_canvas.py:658` | No |
| `CHECKPOINT_INVALID` | 410 | Stored canvas checkpoint payload/bytes invalid. | `routers/be1_canvas.py:666, 668` | No |
| `CANVAS_UNAVAILABLE` | 503 | Canvas service unavailable on device check. | `be1_runtime.py:319` | Yes |
| `CANVAS_RENDER_PILOT_DISABLED` | 503 | Server-side canvas rendering disabled in runtime settings. | `routers/be1_artifacts.py:102` | Yes |
| `CANVAS_RENDER_BUSY` | 503 | Canvas renderer busy; retry later. | `routers/be1_artifacts.py:77` | Yes |
| `CANVAS_RENDER_DEADLINE_EXCEEDED` | 503 | Canvas render exceeded time budget. | `routers/be1_artifacts.py:79` | Yes |
| `CANVAS_RENDER_INTEGRITY_FAILED` | 500 | Rendered canvas output failed integrity check. | `routers/be1_artifacts.py:144` | No |
| `ARTIFACT_PROVIDER_UNCONFIGURED` | 503 | Production artifact/checkpoint object storage backend not configured. | `routers/be1_canvas.py:553, 734`; `routers/be1_artifacts.py:293, 395` | Yes |
| `ARTIFACT_INTEGRITY_FAILED` | 410 | Stored artifact failed its SHA-256 integrity check. | `routers/be1_artifacts.py:438` | No |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Uploaded artwork is not PNG/JPEG/WebP or content type unsupported. | `routers/be1_artifacts.py:253` | No |
| `MEDIA_TYPE_MISMATCH` | 415 | Declared HTTP/metadata media type disagrees with file magic bytes. | `routers/be1_artifacts.py:275` | No |
| `CONTRIBUTORS_REQUIRED` | 422 | Artifact submission requires 1–40 explicit contributors. | `routers/be1_artifacts.py:303` | No |
| `UPLOAD_TOO_LARGE` | 413 | Artifact image exceeds 12 MiB upload limit. | `routers/be1_artifacts.py:337` | No |
| `INVALID_GALLERY_TRANSITION` | 409 | Only a `draft` gallery item may be published. | `routers/be1_records.py:229` | No |
| `GALLERY_NOT_PUBLISHED` | 409 | Only published gallery items accept teacher annotations. | `routers/be1_records.py:286` | No |
| `OBSERVATION_TOO_LARGE` | 413 | Teacher observation text exceeds maximum supported size. | `routers/be1_records.py:356` | No |

### 2.4 Lesson Library, Moderation, Feedback, and Parent Groups

*(Route family: `/api/lesson-library/v1/*`, normalized into CONV-1 by `error_envelope.py`.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `STALE_SOURCE_VERSION` | 409 | **`T-10b`**: `POST .../lessons/{lesson_id}/remixes` sent a `source_content_sha256` / version mismatching the current published source lesson version. | `infrastructure/lesson_library/service.py:1087`, `domain/lesson_library/model.py:32, 39`, `error_envelope.py:161` | No |
| `LESSON_FILE_TOO_LARGE` | 413 | Uploaded lesson source file exceeds 25 MB limit. | `infrastructure/lesson_library/service.py:710, 876` (`/api/lesson-library/v1/*`) | No |
| `INVALID_SOURCE_DOCUMENT` | 422 | Lesson Library upload part/source SHA-256 mismatch or invalid parser document. | `infrastructure/lesson_library/service.py:783, 881, 885` (`/api/lesson-library/v1/*`) | No |
| `MALWARE_DETECTED` | 422 | Security scanner rejected uploaded Lesson Library source document. | `infrastructure/lesson_library/service.py:897` (`/api/lesson-library/v1/*`) | No |
| `UPLOAD_PART_CONFLICT` | 409 | Resumable lesson upload part already committed with different bytes. | `infrastructure/lesson_library/service.py:792` (`/api/lesson-library/v1/*`) | No |
| `UPLOAD_SESSION_STATE_CONFLICT` | 409 | Lesson upload session is no longer open for parts/complete/abort. | `infrastructure/lesson_library/service.py:1095, 2088` (`/api/lesson-library/v1/*`) | No |
| `UPLOAD_SESSION_EXPIRED` | 410 | Lesson upload session TTL expired. | `infrastructure/lesson_library/service.py:1093, 1097, 2086` (`/api/lesson-library/v1/*`) | No |
| `UPLOAD_INCOMPLETE` | 422 | Not all expected upload parts arrived before completion. | `infrastructure/lesson_library/service.py:853` (`/api/lesson-library/v1/*`) | No |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | File type or sniffed bytes not unencrypted PDF/DOCX/PPTX. | `infrastructure/lesson_library/service.py:708, 920` (`/api/lesson-library/v1/*`) | No |
| `INVITATION_EXISTS` | 409 | Parent principal already holds an active group invitation or membership. | `infrastructure/lesson_library/service.py:1532` (`/api/lesson-library/v1/organizations/{id}/parent-groups/*`) | No |
| `INVITATION_EXPIRED` | 409 | Parent group invitation or lesson share invitation expired before accept/decline. | `infrastructure/lesson_library/service.py:1697, 1829` (`/api/lesson-library/v1/*`) | No |
| `AUTHOR_REQUIRED` | 403 | Lesson publication moderation requires an authorized author / permission. | `infrastructure/lesson_library/platform_publication.py:183, 248` (`/api/platform-admin/v1/*` / Lesson Library moderation) | No |
| `CONTENT_HASH_MISMATCH` | 409 | Submitted content hash disagrees with stored lesson/catalog revision hash. | `infrastructure/lesson_library/platform_publication.py:241`; `infrastructure/learning_content/admin_catalog.py:163` | No |
| `LESSON_RESTORE_REQUIRED` | 409 | Archived/removed lesson must be restored before review/re-publication. | `infrastructure/lesson_library/platform_publication.py:286` | No |
| `EXACT_REVIEW_REQUIRED` | 409 | Moderation decision must reference exact submitted version/review state. | `infrastructure/lesson_library/platform_publication.py:303` | No |
| `REVIEW_PERMISSION_REVOKED` | 403 | Reviewer's content moderation permission has been revoked. | `infrastructure/lesson_library/platform_publication.py:314`; `infrastructure/learning_content/admin_catalog.py:212` | No |
| `PARENT_REQUIRED` | 403 | Lesson feedback creation (`lesson_feedback.py`) requires a Parent role/principal. | `infrastructure/lesson_library/feedback.py:164` (`/api/lesson-library/v1/organizations/{id}/lessons/{id}/feedback`) | No |
| `LESSON_ACCESS_UNAVAILABLE` | 403 | Parent cannot post feedback on a lesson they lack active access to. | `infrastructure/lesson_library/feedback.py:114` (`/api/lesson-library/v1/*`) | No |

### 2.5 Lesson Occurrences, Documents, Plans, Child Selection, and Projection

*(Route family: `/v1/lesson-occurrences*`, CONV-1 envelope.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `TEACHER_ASSIGNMENT_REQUIRED` | 409 | Caller is in the organization's teacher family but is not an active assigned `teacher` of the target class when creating an occurrence. | `infrastructure/lesson_occurrences/scope.py:126` (`POST /v1/lesson-occurrences`) | No |
| `UNSUPPORTED_LESSON_TYPE` | 415 | Attached occurrence document extension or detected content is not PDF/DOCX/PPTX. | `infrastructure/lesson_occurrences/documents.py:364, 407` (`POST /v1/lesson-occurrences/{id}/documents`) | No |
| `LESSON_FILE_TOO_LARGE` | 413 | Attached occurrence document stream exceeds 25 MB. | `infrastructure/lesson_occurrences/documents.py:433` (`POST /v1/lesson-occurrences/{id}/documents`) | No |
| `INVALID_FILE_CONTENT` | 400 | Corrupted/unreadable document, empty/oversized extracted text, or NUL/lone surrogates. | `infrastructure/lesson_occurrences/documents.py:176, 182, 412` | No |
| `OCR_NOT_SUPPORTED` | 422 | Scanned image-only PDF/PPTX/DOCX with insufficient extractable text (mapped via parser). | `error_envelope.py:137-139` (`error_envelope.py` MESSAGE; `lesson_parser.py:59` raises `LessonDocumentRejected("OCR_NOT_SUPPORTED")`, mapped by `documents.py` parse gate) | No |
| `ENCRYPTED_DOCUMENT_UNSUPPORTED` | 422 | Password-protected or encrypted office/PDF document rejected by parser gate. | `error_envelope.py:140-142`; `infrastructure/documents/lesson_parser.py:99, 128` | No |
| `DOCUMENT_PAGE_LIMIT_EXCEEDED` | 422 | Document exceeds 100 pages/slides limit. | `error_envelope.py:143-145`; `infrastructure/documents/lesson_parser.py:130, 158` | No |
| `DOCUMENT_TEXT_LIMIT_EXCEEDED` | 422 | Extracted document text exceeds 2 MB cap. | `error_envelope.py:146-148`; `infrastructure/documents/lesson_parser.py:56` | No |
| `UPLOAD_INCOMPLETE` | 422 | Referenced upload session asset object missing in storage during document attach. | `infrastructure/lesson_occurrences/documents.py:426` | No |
| `UPLOAD_CHECKSUM_MISMATCH` | 422 | Stored asset byte size or SHA-256 disagrees with upload session metadata. | `infrastructure/lesson_occurrences/documents.py:446` | No |
| `STORAGE_UNAVAILABLE` | 503 | Object storage read/stream fault while attaching occurrence document. | `infrastructure/lesson_occurrences/documents.py:392, 424, 441` | Yes |
| `LESSON_PLAN_NOT_APPROVED` | 422 | Child selection (`POST .../child-selection` or `confirm`) attempted before the occurrence has an `APPROVED` plan revision. | `infrastructure/lesson_occurrences/child_selection.py:352`; `infrastructure/story_teacher/repository.py:342, 351` (`POST /v1/story-runs`) | No |
| `SAMPLE_VIDEO_ALREADY_EXISTS` | 409 | Occurrence's single sample-video slot is already `CLAIMED` (`sample_slot_state != AVAILABLE`) or already holds a sample run. | `infrastructure/lesson_occurrences/child_selection.py:354`; `infrastructure/lesson_occurrences/projection.py:245`; `infrastructure/story_teacher/repository.py:192` | No |

### 2.6 Upload Sessions and Media Validation

*(Route families: `/v1/upload-sessions*`, `/api/lesson-library/v1/.../upload-sessions*`, `/v1/story-runs/{id}/artwork-upload*`.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `UPLOAD_SESSION_EXPIRED` | 410 | Generic `/v1/upload-sessions/{id}` expired before upload part/complete/abort. | `infrastructure/uploads/service.py:434, 438, 617, 915, 917` | No |
| `UPLOAD_SESSION_STATE_CONFLICT` | 409 | Generic upload session is not in `OPEN` / `UPLOADING` / `COMPLETED` state required by operation. | `infrastructure/uploads/service.py:436, 919` | No |
| `UPLOAD_PART_CONFLICT` | 409 | Same `part_no` re-uploaded with a different byte SHA-256 or size. | `infrastructure/uploads/service.py:654` (`PUT /v1/upload-sessions/{id}/parts/{part_no}`) | No |
| `UPLOAD_CHECKSUM_MISMATCH` | 422 | Uploaded part or assembled object SHA-256/size disagrees with declared digest. | `infrastructure/uploads/service.py:649, 722`; `infrastructure/story_inputs/service.py:76` | No |
| `UPLOAD_CONTENT_MISMATCH` | 422 / 415 | Declared content type does not match sniffed file bytes (`policy.unsupported_code` / upload validator). | `error_envelope.py:119`; `app.py:593` (`/v1/upload-sessions*`, `/v1/story-runs*`) | No |
| `UPLOAD_INCOMPLETE` | 422 | `complete` called with missing parts or incomplete object in storage. | `infrastructure/uploads/service.py:725`; `infrastructure/story_inputs/service.py:60` | No |
| `MEDIA_TOO_LARGE` | 413 | Generic media upload (artwork/image/request body middleware) exceeds byte cap. | `infrastructure/story_inputs/service.py:143`; `bounded_image_upload.py:216` (`too_large_code`); `error_envelope.py:83, 105` | No |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Media type unsupported by generic upload policy (`story_artwork`, `voice_idea`, etc.). | `routers/upload_sessions.py:173`; `infrastructure/uploads/service.py:514, 610`; `infrastructure/story_inputs/service.py:137, 141`; `infrastructure/story_inputs/idea.py:120` | No |
| `STORAGE_UNAVAILABLE` | 503 | Object storage read/write failure during part staging, assembly, or cleanup. | `routers/upload_sessions.py:57`; `infrastructure/uploads/service.py:666, 755, 819, 821, 834`; `infrastructure/story_inputs/service.py:58, 72, 146` | Yes |
| `AUDIO_TOO_LARGE` | 413 | Voice idea audio upload exceeds `20,000,000` bytes or `120` seconds (SRS l.982). | `infrastructure/story_inputs/idea.py:122, 128, 134` (`POST /v1/story-runs/{id}/idea*`) | No |
| `IMAGE_DIMENSIONS_EXCEEDED` | 422 | Drawing image pixel dimensions exceed allowed maximum. | `app.py:582` (`/v1/story-runs*`); `infrastructure/story_inputs/` validator | No |

### 2.7 StoryRun Lifecycle, Inputs, Script Review, and Video Generation

*(Route families: `/v1/story-runs*`, `/v1/activities`, and legacy `/api/parent/v1/ai/story-runs/{id}/story-revisions`; formatted with `ParentStoryErrorEnvelopeV1` per `app.py:529-627`.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `ACTIVE_RUN_EXISTS` | 409 | Parent profile or Teacher already owns an active (non-closed) StoryRun. | `parent_story_repository.py:352, 424` (`POST /v1/story-runs`); `story_teacher/repository.py:149, 430` | No |
| `TEACHER_ACTIVE_RUN_CONFLICT` | 409 | Teacher already has an active run for this occurrence / account lock. | `story_teacher/repository.py:151, 431` (`POST /v1/story-runs`) | No |
| `MULTI_CHILD_NOT_SUPPORTED` | 422 | `POST /v1/story-runs` received multiple child profiles (one child per run only). | `routers/story_run_create_dispatch.py:202` (`POST /v1/story-runs`) | No |
| `SAMPLE_VIDEO_ALREADY_EXISTS` | 409 | Occurrence already holds a claimed sample run / ready sample video. | `story_teacher/repository.py:192` (`POST /v1/story-runs`) | No |
| `LESSON_PLAN_NOT_APPROVED` | 422 | Occurrence referenced by Teacher `POST /v1/story-runs` has no approved plan. | `story_teacher/repository.py:342, 351` (`POST /v1/story-runs`) | No |
| `PARENT_STORY_RUN_STORE_UNAVAILABLE` | 503 | StoryRun PostgreSQL store read/write failed. | `services/parent_story_runs.py:169`; `parent_story_repository.py:425, 497, 711`; `infrastructure/persistence/story_first_start.py:146`; `infrastructure/story_video/repository.py:263` (`_STORE_UNAVAILABLE`) | Yes |
| `PARENT_STORY_CONTEXT_UNAVAILABLE` | 409 / 503 | Profile context snapshot missing/unavailable when starting or confirming context. | `parent_story_repository.py:4785` (`409`), `4793` (`503`) | No (409) / Yes (503) |
| `PROFILE_CONTEXT_NOT_CONFIRMED` | 422 | Script/video generation attempted before profile context confirmation gate is satisfied. | `parent_story_repository.py:2526`; `infrastructure/story_video/repository.py:589` | No |
| `SUBJECT_NOT_CONFIRMED` | 422 | Story/activity/video generation attempted before drawing subject confirmation (`confirm_subject`). | `parent_story_repository.py:1355, 1379`; `infrastructure/story_video/repository.py:602` | No |
| `TRANSCRIPT_NOT_CONFIRMED` | 422 | Voice idea transcript still `NEEDS_CONFIRMATION` or `FAILED` when starting story generation. | `parent_story_repository.py:3855` (`/v1/story-runs/{id}/*`) | No |
| `PARENT_UNDERSTANDING_RESULT_TOO_LARGE` | 422 | Drawing understanding JSON exceeds storage bound (`_check_json_bound`). | `parent_story_repository.py:4839` | No |
| `PARENT_ACTIVITY_SELECTION_REQUIRED` | 409 | **Phase A (`T-2e-a`)**: legacy `POST /api/parent/v1/ai/story-runs/{id}/story-revisions` called without prior main activity selection. | `parent_story_repository.py:2651` (`/api/parent/v1/ai/story-runs/{id}/story-revisions`) | No |
| `STORY_REWRITE_LIMIT_REACHED` | 409 | Maximum script rewrites (`revision_no` cap 4 / rewrite slot cap) exhausted. | `parent_story_repository.py:2667, 2902` (`POST /v1/story-runs/{id}/story-rewrites`) | No |
| `VIDEO_REGENERATION_LIMIT_REACHED` | 409 | Run reached 3 accepted video generation requests or `MAX_REVIEW_EPOCH = 3` (Phase A `T-1b-fix`). | `parent_story_repository.py:3623`; `infrastructure/story_video/repository.py:495, 917` (`script-confirmation`, `video-generations`, `video-unsuitable`) | No |
| `AI_COST_LIMIT_REACHED` | 429 / 503 | Global AI video cost budget gate refused video generation admission (owner message at `app.py:568`). | `app.py:568` (`POST /v1/story-runs/{id}/video-generations` admission) | Yes |
| `SUBSCRIPTION_RESTRICTED` | 403 / 409 | **`owner: Billing/Capacity`**: subscription state (`RESTRICTED` / inactive) blocks video generation (`app.py:569`). | `app.py:569` (`POST /v1/story-runs/{id}/video-generations`) | No |
| `VIDEO_QUOTA_EXCEEDED` | 409 | **`owner: Billing/Capacity`**: period video quota exhausted (`app.py:570`, `sandbox_billing.py:344`). | `app.py:570`; `infrastructure/platform_admin/sandbox_billing.py:344` | No |
| `RANGE_NOT_SATISFIABLE` | 416 | HTTP `Range` header outside ready MP4 byte length on video stream endpoint. | `routers/story_run_video.py:507` (`GET /v1/story-runs/{id}/video/stream`) | No |
| `PARENT_STORY_REVISION_STALE` | 409 (legacy) | **Phase A (`T-1b-fix`)**: **remapped to `STALE_REVISION`** on `/v1/story-runs/{id}/script-confirmation` (`parent_story_repository.py:3613`). | `parent_story_repository.py:3613`; Phase A route table (`API_INVENTORY_V4:40`) | No |
| `PARENT_STORY_CONFIRMATION_CONFLICT` | 409 (legacy) | **Phase A (`T-1b-fix`)**: **remapped to `INVALID_STATE_TRANSITION`** on `/v1/story-runs/{id}/script-confirmation` (`parent_story_repository.py:3596, 3617`). | `parent_story_repository.py:3596, 3617`; Phase A route table (`API_INVENTORY_V4:40`) | No |
| `PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT` / `PARENT_STORY_REWRITE_NOT_ALLOWED` / `PARENT_UNDERSTANDING_REVISION_STALE` / `PARENT_STORY_ARTWORK_REQUIRED` / `PARENT_VISIBLE_FEATURES_UNAVAILABLE` | 409 (legacy) | Legacy internal repository codes **remapped to `INVALID_STATE_TRANSITION`** by `_REWRITE_CODE_MAP` on `/v1/story-runs/{id}/story-revisions` & `story-rewrites`; may still appear raw if raised on legacy `/api/parent/v1/ai/story-runs/{id}/story-revisions`. | `parent_story_repository.py:2117, 2503, 2528, 2544, 2640, 2673`; `routers/parent_story_inputs.py:491-497` | No |
| `PARENT_STORY_RUN_NOT_ACCEPTING_ARTWORK` / `PARENT_STORY_ARTWORK_ALREADY_ATTACHED` / `PARENT_STORY_ARTWORK_CONFLICT` / `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING` / `PARENT_STORY_INPUT_REPLACED` / `PARENT_UNDERSTANDING_UNAVAILABLE` / `PARENT_SUBJECT_CONFIRMATION_CONFLICT` / `PARENT_INITIAL_STORY_CANNOT_BE_REWRITE` / `PARENT_STORY_REVISION_NOT_GENERATING` | 409 | Legacy internal StoryRun repository state/conflict codes (raised inside `parent_story_repository.py`; `/v1/story-runs*` endpoints catch/map newer paths to `INVALID_STATE_TRANSITION`, while legacy `/api/parent/v1/ai/*` paths surface raw uppercase code with fallback Vietnamese message `app.py:596-612`). | `parent_story_repository.py:1568, 1571, 1667, 2107, 2114, 2257, 2367, 2434, 2669, 3087`; `routers/parent_ai.py:262` | No |

*Job & Generation failure codes embedded in resource payloads (`AiJobStatusV1.failure.code` and `StoryRunDetailV1.error_code`, not top-level HTTP error envelope codes):*
- `VIDEO_SAFETY_BLOCKED` (`domain/story_video/model.py:153, 161` — normalizes stored `SAFETY_BLOCKED`), `VIDEO_DEADLINE_EXCEEDED` (+6h generation deadline timeout, `domain/story_run_closeout.py:15, 18`), `VIDEO_TECHNICAL_FAILURE` (including `PLAN_SUPERSEDED` on Teacher occurrence plan change), `RUN_CANCELLED` (`infrastructure/story_video/repository.py:1515`), `PROVIDER_UNAVAILABLE`.

### 2.8 Parent Profiles and Support Needs

*(Route families: `/v1/parent/profiles*` (`parent_error_payload` English envelope, `app.py:628-686`) and `/api/be1/v1/.../support-needs` (CONV-1 envelope).)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `PROFILE_NOT_FOUND` | 404 | Target child profile does not exist or is not owned by the caller (`/v1/parent/profiles*` keeps `PROFILE_NOT_FOUND`; `/api/be1/v1/*` normalizes `404 PROFILE_NOT_FOUND` -> `RESOURCE_NOT_FOUND`). | `infrastructure/persistence/parent_profile_repository.py:122, 226, 304, 349`; `routers/parent_profiles.py:110` (`/v1/parent/profiles*`); `routers/be1_records.py:353, 427`; `routers/be1_registry.py:1738` (CONV-1 -> `RESOURCE_NOT_FOUND`) | No |
| `PARENT_STORE_UNAVAILABLE` | 503 | Parent profile PostgreSQL store read/write failure. | `parent_runtime.py:113, 149`; `parent_profile_repository.py:682`; `routers/parent_profiles.py:100` (`/v1/parent/profiles*`) | Yes |
| `SUPPORT_NEEDS_UNAVAILABLE` | 503 | **Phase B (`T-12c`)**: encrypted support-needs store/KMS dependency unavailable on `GET`/`PUT .../support-needs` (Parent or School Manager/Teacher route). | `application/services/support_needs.py:34`; `infrastructure/persistence/support_needs_repository.py:53` (`/v1/parent/profiles/{id}/support-needs`); `routers/be1_registry.py:2373` (`/api/be1/v1/.../support-needs`); `app.py:636`; `error_envelope.py:208` | Yes |
| `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE` | 409 | Synthetic test/dev Parent profile creation disabled in runtime settings. | `application/services/parent_profiles.py:37` (`POST /v1/parent/profiles*`); `app.py:640` | No |
| `DIAGNOSIS_LIKE` *(in `field_errors[].code`)* | 400 (`INVALID_REQUEST`) | **Phase B (`T-12b-fix`, BR-20)**: `interests_summary` or support-needs `note` matched disallowed diagnosis/medical screening pattern; returned inside `field_errors` with envelope `code: "INVALID_REQUEST"`. | `domain/parent_profiles.py:124`; `api_conventions.py:55`; `contracts/schemas/parent_profiles.py:261-262` (`/v1/parent/profiles*`, `/api/be1/v1/.../support-needs`) | No |

### 2.9 Notifications Inbox and Push Endpoints

*(Route family: `/v1/notifications*`, CONV-1 envelope.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `RESOURCE_NOT_FOUND` | 404 | Inbox item or push endpoint does not exist or belongs to another principal (uniform 404). | `infrastructure/notifications/inbox_repository.py:74` (`/v1/notifications*`); `application/services/push_endpoints.py:621` | No |
| `INVALID_IDEMPOTENCY_KEY` | 400 | Same `Idempotency-Key` reused with different payload on `mark-read`, `mark-all-read`, or push endpoint register/delete. | `notifications/inbox_repository.py:262`; `application/services/push_endpoints.py:494, 514` | No |
| `STALE_REVISION` | 409 | Push endpoint `If-Match` version disagrees with current version (carries `current_version`). | `application/services/push_endpoints.py:309, 349` (`DELETE /v1/notifications/push-endpoints/{endpoint_id}`) | No |
| `PUSH_PLATFORM_UNSUPPORTED` | 422 | **`T-8b`**: `POST /v1/notifications/push-endpoints` received `platform_kind` = `ANDROID` (`ANDROID_PUSH`) where only `WEB` (`WEB_PUSH`) is supported. | `application/services/push_endpoints.py:163`, `error_envelope.py:107` | No |
| `PUSH_REGISTRATION_UNAVAILABLE` | 503 | **`T-8b`**: push registration proof/key adapter is unavailable in current runtime configuration (production default without push adapters). | `application/services/push_endpoints.py:625`, `error_envelope.py:108` | Yes |
| `PROVIDER_UNAVAILABLE` | 503 | Normalized from `DEPENDENCY_UNAVAILABLE` when push repository/database dependency is unavailable. | `routers/notifications.py:225, 275`, `error_envelope.py:71` | Yes |

### 2.10 Platform Admin, Audit Retention, Billing/Capacity Sandbox, and Payment Callbacks

*(Route families: `/api/platform-admin/v1/*`, `/api/be1/v1/.../billing|quota*`, `/api/payment-callbacks/v1/*`. Items governing commercial billing/subscription/capacity rules are owned by **Billing/Capacity**.)*

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `SELF_DISABLE_DENIED` | 409 | Platform Admin attempted to disable their own account. | `routers/platform_admin_accounts.py:695` (`/api/platform-admin/v1/accounts*`) | No |
| `SELF_ROLE_CHANGE_DENIED` | 409 | Platform Admin attempted to remove their own Platform Admin role. | `routers/platform_admin_accounts.py:711` (`/api/platform-admin/v1/accounts*`) | No |
| `LAST_PLATFORM_ADMIN` | 409 | Operation would leave zero active Platform Admin accounts. | `routers/platform_admin_accounts.py:726` (`/api/platform-admin/v1/accounts*`) | No |
| `ACTIVE_PLATFORM_ADMIN_REQUIRED` | 422 | At least one active Platform Admin is required (`service.py`). | `infrastructure/platform_admin/service.py:458` | No |
| `SELF_PERMISSION_CHANGE_DENIED` | 403 | Admin attempted to modify their own permissions (`service.py`). | `infrastructure/platform_admin/service.py:456` | No |
| `INDEPENDENT_REVIEW_REQUIRED` | 403 | Same actor cannot both author and review/approve an item (`platform_admin`, `svg_catalog`). | `domain/platform_admin.py:17`; `routers/svg_catalog.py:276, 303, 346, 382` | No |
| `INDEPENDENT_CURATION_REQUIRED` | 403 | Separate curator required (`svg_catalog`). | `routers/svg_catalog.py:409` | No |
| `CONTENT_PERMISSION_REQUIRED` | 403 | Content curation/moderation permission required. | `infrastructure/platform_admin/service.py:78` | No |
| `ORGANIZATION_REQUIRED` | 422 | Selected role requires an `organization_id`. | `routers/platform_admin_accounts.py:704` | No |
| `ORGANIZATION_UNAVAILABLE` | 422 | Target organization is missing or inactive/unavailable. | `routers/platform_admin_accounts.py:276` | No |
| `AUDIT_RETENTION_POLICY_UNAVAILABLE` | 503 | Audit retention policy store/configuration unavailable. | `infrastructure/platform_admin/service.py:291` | Yes |
| `AUDIT_RETENTION_INDEFINITE` | 409 | Audit retention policy prevents purge while set to indefinite. | `infrastructure/platform_admin/service.py:389` | No |
| `AUDIT_RETENTION_CUTOFF_TOO_RECENT` | 409 | Requested purge cutoff violates minimum retention window. | `infrastructure/platform_admin/service.py:391` | No |
| `AUDIT_RETENTION_PREVIEW_STALE` | 409 | Retention purge preview hash/version no longer matches current eligible set. | `infrastructure/platform_admin/service.py:402, 407` | No |
| `BILLING_SANDBOX_DISABLED` | 403 | **`owner: Billing/Capacity`**: billing/capacity sandbox endpoints disabled in non-sandbox config. | `infrastructure/platform_admin/sandbox_billing.py:30` | No |
| `BILLING_SCOPE_REQUIRED` / `BILLING_SCOPE_SELECTION_REQUIRED` / `BILLING_PURCHASE_NOT_ALLOWED` | 422 / 409 / 403 | **`owner: Billing/Capacity`**: missing or disallowed billing owner scope on admin/commerce endpoints. | `routers/platform_admin.py:388`; `infrastructure/billing/quota_commerce.py:1269, 1291` | No |
| `QUOTA_PRODUCT_NOT_FOUND` / `QUOTA_PRODUCT_UNAVAILABLE` / `QUOTA_PRODUCT_OFFER_UNAVAILABLE` / `QUOTA_PRODUCT_SCOPE_IMMUTABLE` / `OFFER_UNAVAILABLE` | 404 / 409 / 422 | **`owner: Billing/Capacity`**: quota product/offer lookup, scope mutability, or availability refusal. | `infrastructure/billing/quota_commerce.py:113, 163, 169, 220, 227, 293, 296, 859`; `sandbox_billing.py:114` | No |
| `SUBSCRIPTION_REQUIRED` / `SUBSCRIPTION_ALREADY_EXISTS` / `SUBSCRIPTION_PERIOD_ENDED` / `CAPACITY_QUOTE_NOT_FOUND` / `CAPACITY_QUOTE_EXPIRED` / `INVALID_CAPACITY_QUOTE` / `INVALID_CAPACITY_DOWNGRADE` / `CLASS_SELECTION_REQUIRED` / `CAPACITY_INCREASE_REQUIRED` / `RENEWAL_NOT_DUE` / `PRICE_UNAVAILABLE` / `QUOTE_AMOUNT_UNAVAILABLE` / `INVALID_BILLING_PERIOD` | 404 / 409 / 422 | **`owner: Billing/Capacity`**: subscription & capacity quote lifecycle errors in `billing_capacity.py` / `sandbox_capacity.py`, and surfaced by `PATCH /api/be1/v1/organizations/{organization_id}/capacity` (`T-CAP1`: `CLASS_SELECTION_REQUIRED`, `INVALID_CAPACITY_DOWNGRADE`, `SUBSCRIPTION_PERIOD_ENDED`). | `domain/billing_capacity.py:12, 22`; `infrastructure/platform_admin/sandbox_capacity.py:173-318`; `routers/be1_registry.py:655-657`; `error_envelope.py:103-105` | No |
| `PAYMENT_PROVIDER_NOT_AVAILABLE` / `PAYMENT_PROVIDER_NOT_SUPPORTED` / `PAYMENT_CANCEL_PROVIDER_NOT_SUPPORTED` / `PAYMENT_ATTEMPT_ALREADY_OPEN` / `PAYMENT_ATTEMPT_NOT_RECONCILABLE` / `PAYMENT_EXPIRY_UNAVAILABLE` / `PAYMENT_CHECKOUT_STILL_ACTIVE` / `PAYMENT_TRANSACTION_DATE_UNAVAILABLE` / `PAYMENT_TRANSACTION_REF_REQUIRED` / `PAYMENT_AMOUNT_MISMATCH` / `PAYMENT_EVENT_CONFLICT` / `MOMO_AMOUNT_OUT_OF_RANGE` / `AUTO_RENEWAL_NOT_CONFIGURED` / `TEACHER_QUOTA_INSUFFICIENT` / `SCHOOL_QUOTA_INSUFFICIENT` / `QUOTA_ALLOCATION_NOT_FOUND` / `QUOTA_ADMISSION_CONFLICT` / `TEACHER_ASSIGNMENT_UNAVAILABLE` / `MONTHLY_GRANT_CONFLICT` | 409 / 422 / 503 | **`owner: Billing/Capacity`**: billing commerce, payment reconciliation, MoMo range check, and school/teacher quota ledger codes. | `infrastructure/billing/quota_commerce.py:266-1190`; `sandbox_billing.py:198-254` | Yes (`503`) / No (`4xx`) |
| `RspCode` `"00" \| "01" \| "02" \| "04" \| "97" \| "99"` *(VNPay)*; HTTP `204/400/401/409/422` *(MoMo)* | 200 (VNPay) / 204,4xx (MoMo) | **`owner: Billing/Capacity`**: vendor callback responses on `/api/payment-callbacks/v1/vnpay/*` & `/momo/ipn`. | `routers/payment_callbacks.py:47-171` | No |

### 2.11 Legacy AI, Pilot Assistance, SVG Catalog, and Local Demo Routes

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable |
|---|---:|---|---|---|
| `PARENT_ROLE_REQUIRED` | 403 | Legacy Parent topic suggestions route called without Parent role. | `routers/parent_topic_suggestions.py:56` (`/api/parent/v1/topics*`) | No |
| `PARENT_TOPIC_EXCLUDED_SET_INVALID` / `PARENT_TOPIC_EXCLUDED_SUBJECT_INVALID` / `PARENT_TOPIC_ID_LABEL_MISMATCH` / `PARENT_TOPIC_TEXT_NOT_ALLOWED` | 422 | Legacy topic suggestion input validation / PII-text block / ID-label mismatch. | `routers/parent_topic_suggestions.py:62, 99, 212, 217, 285` (`/api/parent/v1/topics*`) | No |
| `PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED` / `PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID` / `PARENT_TOPIC_SUBJECT_AI_OUTCOME_UNKNOWN` | 503 / 502 / 504 | Legacy topic suggestion AI provider feature flag, schema contract, or timeout error. | `routers/parent_topic_suggestions.py:81, 124, 152, 248, 316` | Yes (`502/503/504`) |
| `MODAL_AI_NOT_ENABLED` | 503 | Modal AI provider disabled in runtime settings. | `routers/parent_ai.py:100`; `routers/teacher_ai.py:67` (`/api/parent/v1/ai*`, `/api/teacher/v1/ai*`) | Yes |
| `MODAL_OUTCOME_UNKNOWN` | 504 | Upstream AI inference timed out or lost connection mid-call. | `routers/parent_ai.py:114`; `routers/teacher_ai.py:81` | Yes |
| `MODAL_OUTPUT_CONTRACT_INVALID` / `MODAL_MODEL_REVISION_MISMATCH` / `STORY_INPUT_CONTRACT_INVALID` | 502 | Upstream AI response failed schema/model-revision validation. | `routers/parent_ai.py:398, 421, 543`; `routers/teacher_ai.py:127, 131, 210, 269, 272` | Yes |
| `TEACHER_PLAN_FIELD_LIMIT_EXCEEDED` | 422 | Teacher AI plan assistant prompt fields exceed limit. | `routers/teacher_ai.py:60` (`/api/teacher/v1/ai*`) | No |
| `DRAWING_IMAGE_TYPE_NOT_ALLOWED` / `DRAWING_IMAGE_INVALID` / `PARENT_ARTWORK_STORAGE_UNAVAILABLE` / `PARENT_ARTWORK_SCAN_UNAVAILABLE` / `CURATED_SVG_GUIDE_NOT_FOUND` / `CURATED_SVG_GUIDE_UNAVAILABLE` | 404 / 415 / 422 / 503 | Legacy Parent AI artwork upload & SVG guide endpoints (`parent_ai.py`). | `routers/parent_ai.py:208, 217, 267, 272, 277, 285, 296, 340` | Yes (`503`) / No (`4xx`) |
| `PILOT_ASSISTANCE_DISABLED` / `PILOT_LEDGER_UNAVAILABLE` / `ASSISTANCE_REQUEST_NOT_FOUND` | 503 / 404 | Legacy/pilot classroom assistance endpoints (`pilot_assistance.py`). | `routers/pilot_assistance.py:323, 360, 444, 527` | Yes (`503`) / No (`404`) |
| `STORY_VIDEO_UNAVAILABLE` / `STORY_VIDEO_NOT_FOUND` / `STORY_VIDEO_NOT_READY` / `STORY_VIDEO_FILE_NOT_FOUND` / `STORY_VIDEO_FILE_HASH_MISMATCH` / `WHITEBOARD_VIDEO_*` / `IDEMPOTENCY_KEY_PAYLOAD_MISMATCH` | 404 / 409 / 503 | Legacy `/v1/sessions` video demo routes (`HTTPException(detail="<CODE>")`). | `routers/story_video.py:24-125`; `routers/whiteboard_video.py:23-115` | Yes (`503`) / No (`4xx`) |
| `WORKFLOW_STORAGE_UNAVAILABLE` / `SESSION_NOT_FOUND` / `SESSION_EXPIRED` / `STALE_SESSION_VERSION` / `WORKFLOW_STEP_NOT_ALLOWED` / `SESSION_ALREADY_EXISTS` / `IDEMPOTENCY_KEY_CONFLICT` / `SUPERVISED_FLOW_NOT_CONFIGURED` / `IMAGE_DEMO_NOT_CONFIGURED` / `RENDERER_NOT_CONFIGURED` / `RIG_*` / `PIXI_ASSET_*` | 409 / 410 / 422 / 503 / 504 | Local ephemeral demo / supervised flow / renderer demo routes (`MobileWorkflowResultV1`). | `application/services/ephemeral_sessions.py:92-432`; `routers/supervised_flow.py:110-541`; `routers/images.py:57-234` | Varies |
| `SERVICE_NOT_READY` / `CONTENT_LENGTH_REQUIRED` / `INVALID_CONTENT_LENGTH` / `CONTENT_LENGTH_MISMATCH` / `PART_TOO_LARGE` / `IMAGE_TOO_LARGE` / `PART_HASH_REQUIRED` / `PART_HASH_MISMATCH` / `INVALID_PART_NUMBER` / `UPLOAD_PART_GAP` / `STAGING_UNAVAILABLE` / `INVALID_ETAG` / `COMMAND_RECOVERY_HOLD` / `VISION_ATTEMPT_HOLD` / `STALE_STORY_GENERATION` / `INTERNAL_ERROR` | 400 / 404 / 409 / 410 / 411 / 413 / 415 / 422 / 428 / 500 / 503 | StoryRun-lite local demo envelope (when `STORYRUN_LITE_MAIN_DEMO_ENABLED=1`). | `domain/story_run_lite.py:88-187`; `routers/story_run_lite.py:37-359`; `infrastructure/story_run_lite/repository.py:136-3039` | `service/staging` `Yes` / `4xx` `No` |

---

## 3. Cross-Cutting Conventions

### 3.1 `Idempotency-Key`

Mutating command endpoints require an `Idempotency-Key` HTTP header validated and persisted with the caller's principal scope:

- **CONV-1 standard rule (`parse_idempotency_key` at `api_conventions.py:139-149`):**
  - Header must appear **once**; missing -> `400 INVALID_REQUEST` with `field_errors: [{"field": "Idempotency-Key", "code": "REQUIRED"}]` (`api_conventions.py:141-143`).
  - Multiple `Idempotency-Key` headers -> `400 INVALID_REQUEST` (`code: "INVALID_FORMAT"`, `api_conventions.py:144-145`).
  - Length must be **`1..128` characters** containing visible ASCII only (`33 <= ord(c) <= 126` — no spaces, control characters, or non-ASCII); violation -> `400 INVALID_REQUEST` (`code: "INVALID_FORMAT"`, `api_conventions.py:146-148`).
- **Durable receipt & replay semantics:**
  - Services compute a SHA-256 `request_fingerprint` of the normalized command inputs and look up `(principal, operation_scope, idempotency_key)` in a database receipt table (e.g., `Be1CommandReceiptModel` in `infrastructure/persistence/be1_models.py:101, 575`; `story.command_receipts` / `story_command_receipts` hashed via `_idempotency_key_hash` in `parent_story_repository.py:5007`; Lesson Library `COMMAND_RECEIPTS` in `lesson_library/service.py:565`; Upload Sessions in `uploads/service.py:530`).
  - **Same key + same fingerprint:** replays the stored outcome (preserving status code, response body, `ETag`, and `Location` where applicable) without re-executing mutations (`be1_registry.py:428`, `lesson_occurrences/documents.py:822-831`). For StoryRun `script-confirmation` (`parent_story_repository.py:3626-3730`), re-confirming a story revision after a spent video generation must use a **fresh** `Idempotency-Key` so the second review epoch is recorded rather than replaying epoch 1.
  - **Same key + different fingerprint:** raises **`400 INVALID_IDEMPOTENCY_KEY`** (`be1_registry.py:421`, `lesson_library/service.py:571` mapped by `lesson_library.py:89-90`, `parent_story_repository.py:5010`, `parent_profile_repository.py:498`, `notifications/inbox_repository.py:262`).
  - **Purged run replay:** on `/v1/story-runs/{id}` commands, replaying a key whose target run moved to `DELETE_PENDING` / `DELETED` returns a lifecycle/purged refusal or projection rather than stale content (`parent_story_repository.py:4684-4695`, `story_video/repository.py:386`).
- **Route-family variations:**
  - `/v1/story-runs*` (`app.py:215-236, 720-776`, `parent_story_runs.py:313, 584, 615`): declares `Idempotency-Key` (`1..128` or optional on cancel/delete) and runs `parse_idempotency_key` *after* role checks; `RequestValidationError` on `Idempotency-Key` strips `field_errors` and emits plain `400 INVALID_REQUEST` with `field_errors: null`. Non-`/v1/story-runs` paths in the StoryRun handler group (`/v1/activities`, `/api/parent/v1/ai/...`) emit `400 INVALID_IDEMPOTENCY_KEY` (`app.py:760-771`).
  - `/v1/parent/profiles*` (`routers/parent_profiles.py:126-136`): validates via `_idempotency_key(request)` with English `INVALID_REQUEST` / `INVALID_IDEMPOTENCY_KEY` messages; hashes keys with SHA-256 (`parent_profile_repository.py:51`).
  - Legacy `/api/be1/v1/sessions*` (`routers/be1_sessions.py:127-129, 435`): `_require_idempotency_key` raises `422 IDEMPOTENCY_KEY_REQUIRED` (rewritten to `400 INVALID_REQUEST` by `error_envelope.py:319-329`), while mismatch raises `409 IDEMPOTENCY_KEY_REUSED`.
  - Local demo routers (`routers/sessions.py:47, 57`, `routers/images.py:45, 102`, `routers/supervised_flow.py:371, 565`, `routers/parent_ai.py:468`): allow `max_length=200` and return `Idempotency-Replayed: true|false`.

### 3.2 `ETag`, `If-Match`, and `If-None-Match` (`304`)

- **Strong `ETag` emission:**
  - Integer revisions are formatted as strong quoted ETags `"{revision}"` (e.g., `be1_registry.py:428, 512, 866, 2152`, `lesson_library.py:118-119`, `upload_sessions.py:107-108`, `lesson_occurrences.py:234, 258, 774`, `admin_route.py:21`).
  - Composite / content-hash ETags are returned on `GET /v1/jobs/{job_id}` (`jobs.py:268`), `GET /v1/story-runs/{run_id}` (`detail_etag` at `parent_story_runs.py:546`), lesson occurrence source document revisions (`revision_etag` = text hash + review state at `lesson_occurrences.py:439`), and plan revisions (`plan_etag` = content hash + state at `lesson_occurrences/plans.py:210`).
- **Optimistic concurrency (`If-Match` -> `409 STALE_REVISION`):**
  - Required on BE1 class/assignment/enrollment/capacity mutations (`be1_registry.py:206-219, 844`), Lesson Library version/grant/group mutations (`lesson_library.py:110-137`, including `DELETE .../members/{membership_id}` which raises `428 PRECONDITION_REQUIRED` when missing), Upload Sessions complete/abort (`upload_sessions.py:86-105`), Lesson Occurrence child selection confirm & projection confirm (`lesson_occurrences.py:612-625`), Push Endpoint delete (`application/services/push_endpoints.py:309, 349`), Platform Admin (`platform_admin.py:80-91`, `428 PRECONDITION_REQUIRED` / `422 INVALID_REVISION`), and BE1 billing quota (`be1_billing.py:359-388`, `422 INVALID_REVISION`).
  - Missing/malformed `If-Match` returns `400 INVALID_REQUEST` with `field_errors` (`REQUIRED` or `INVALID_FORMAT`) on CONV-1 routers (`be1_registry.py:206-219`, `lesson_library.py:99-117`, `lesson_occurrences.py:612-625`, `upload_sessions.py:88-105`) unless noted otherwise (`428`/`422`).
  - On version mismatch, `raise_stale_revision` (`api_conventions.py:152-160`) returns **`409 STALE_REVISION`** carrying JSON `current_version` (`int`) and response header `ETag: "<current>"` where single-resource revision applies.
- **Conditional `GET` (`If-None-Match` -> `304 Not Modified`):**
  - Supported on `GET /v1/jobs/{job_id}` (`jobs.py:240-270`), `GET /v1/story-runs/{run_id}` (`parent_story_runs.py:533-551`), and `GET` endpoints for Lesson Occurrences, Source Documents, Document Revisions, Plan Revisions, and Child Selection (`lesson_occurrences.py:253-258, 362-367, 687-698`).
  - **Authorization-first invariant:** The server **always** authenticates, authorizes scope against live DB state, and recomputes/fetches the current state before comparing `If-None-Match` (`jobs.py:7-8`, `parent_story_runs.py:533-534`, `lesson_occurrences.py:4`). Conditional `304` responses include `ETag` and cache headers (`Cache-Control: private, no-cache` or `private, no-store` and `Vary: Authorization`) with an empty body. `GET /v1/lesson-occurrences/{id}/child-selection` only honors `304` when the stored selection state is immutable (`child_selection.py:235-237`, `lesson_occurrences.py:687-698`).

### 3.3 Cursor Pagination and `limit`

- **Bounds (`api_conventions.py:21-29, 59-67`):**
  - `limit`: default **`25`** (`PAGE_LIMIT_DEFAULT`), minimum `1`, maximum **`100`** (`PAGE_LIMIT_MAX`). Exceptions: Lesson Library catalog endpoint allows `1..500` (`lesson_library/service.py:2024`); `GET /v1/activities` returns an unpaged bounded list (`<= 12`, no `cursor` parameter, `parent_story_activities.py`).
  - `cursor`: optional query string, default max length `1024` (`CURSOR_MAX_LENGTH = 1024`; `lesson_feedback.py:40` sets `max_length=768`).
- **Scoped opaque keyset cursor (`encode_cursor` / `decode_cursor` at `api_conventions.py:76-136`):**
  - Encoded as **unpadded URL-safe Base64** (no `=`, `+`, or `/`) of canonical compact JSON `{"i":"<item_id>","k":"<sort_key>","s":"<scope>","v":1}`.
  - Decoding validates exact key set, `v == 1`, exact `scope` match for the route/organization, printable ASCII within max lengths (`sort_key <= 64`, `item_id <= 128`), and strict round-trip canonical encoding (`encode_cursor(...) == cursor`), plus timezone-aware ISO timestamp matching for `decode_time_cursor` (`api_conventions.py:122-136`).
  - Invalid/cross-scope/non-canonical cursors return `400 INVALID_REQUEST` with `field_errors: [{"field": "cursor", "code": "INVALID_FORMAT"}]` (`api_conventions.py:119`; adopted in `be1_registry.py:244, 2055`, `notifications.py:117`, `lesson_occurrences/service.py:330`, `platform_admin_accounts.py:136, 418`, `parent_profile_repository.py:397, 736`, and `lesson_library/service.py:211` for `T-10a`/`T-10c`). Note: legacy `platform_admin/pagination.py:65, 165` raises `422 INVALID_CURSOR`, and legacy `lesson_library/service.py` endpoints raise `422 INVALID_REQUEST`.

### 3.4 Correlation ID and `X-Request-ID`

- **Request middleware (`be1_request_context` at `app.py:505-525`):**
  - Reads optional `X-Request-ID` header on incoming HTTP requests; normalizes/validates it (or generates a fresh `uuid4()` string when absent/invalid).
  - Binds `request.state.be1_request_id` (and family-specific request IDs for Parent Profile and StoryRun handlers).
  - Guarantees response header `X-Request-ID` on every HTTP response (`app.py:521-522, 626, 685, 705, 777, 789, 803, 945`).
  - Populates `correlation_id` and `request_id` with the exact same ID in CONV-1 error bodies (`error_envelope.py:300, 305`).
- **StoryRun-Lite local demo (`story_run_lite.py:316-368`):** honors `X-Correlation-ID` for `correlation_id`.

### 3.5 Authentication, Roles, and Uniform 404 vs. 403

- **Authentication (`be1_runtime.py:165-230`, `parent_runtime.py:45-100`, `application/ports/identity.py`):**
  - Adult APIs require `Authorization: Bearer <Firebase ID Token>`. Verification produces a `VerifiedPrincipal` (immutable subject `uid`, issuer, token flags) and resolves an internal `AdultIdentityModel` / `OrganizationAssignmentModel` in PostgreSQL. Missing, malformed, or expired Bearer tokens fail with **`401 AUTH_REQUIRED`**, **`401 INVALID_TOKEN`**, or **`401 TOKEN_EXPIRED`**.
  - Classroom child-device endpoints verify device grant headers via `get_verified_device` / `get_verified_device_status` (`be1_runtime.py:232-458`), failing with `401 DEVICE_AUTHENTICATION_REQUIRED` / `INVALID_DEVICE_CREDENTIAL` or `403 DEVICE_SCOPE_INACTIVE` / `DEVICE_MEMBERSHIP_INACTIVE`.
- **Uniform 404 (`RESOURCE_NOT_FOUND`) vs. `403` (`ACTION_NOT_ALLOWED`) vs. `409`:**
  - **Uniform `404 RESOURCE_NOT_FOUND` (anti-enumeration, SRS l.865):** Returned whenever the resource does not exist, belongs to another owner/organization/class, is accessed by an account lacking a readable role/assignment for that route family, or is hidden by visibility rules (e.g., `ARCHIVED` classes hidden from Teachers via `hide_archived_from_teacher` in `be1_common.py`). Proven at `jobs.py:4-6, 156`, `story_run_actor.py:41`, `parent_story_repository.py:4549-4619`, `lesson_occurrences/scope.py:65` & `domain/lesson_occurrences/model.py:96-100`, `inbox_repository.py:74`, `uploads/service.py:112`, `lesson_library.py:165`, `push_endpoints.py:621`, `be1_registry.py:789` (non-Manager capacity read), and `be1_common.py:85`.
  - **`403 ACTION_NOT_ALLOWED` (or `ACCOUNT_SCOPE_UNAVAILABLE` / `FORBIDDEN`):** Returned when the caller is visible/authenticated inside the scope (e.g., active `guide` or `observer` inside the organization's class scope, or assigned `teacher` calling a `school_admin`-only operation), so existence is already authorized, but the caller's role lacks permission for the requested action (`be1_common.py:151, 181`, `lesson_occurrences/scope.py:124`, `child_selection.py:291`, `projection.py:136`, `story_teacher/repository.py:316`, `lesson_library/service.py:1301`, `platform_admin_accounts.py:234`).
  - **`409 TEACHER_ASSIGNMENT_REQUIRED`:** Returned on `POST /v1/lesson-occurrences` when an adult holds a teacher-family role in the organization (`guide`, `observer`, or `teacher` on other classes) but is not the active assigned `teacher` of the target `class_id` (`lesson_occurrences/scope.py:126`, `domain/lesson_occurrences/model.py:96-100`).

### 3.6 Rate Limits

- **Real-data profile & enrollment gate (`SlidingWindowLimiter` at `rate_limit.py:17-96`, `be1_runtime.py:75, 139-141`, `be1_registry.py:1295-1308`):**
  - Enforces SRS NFR-12 (l.637) using two in-memory sliding-window buckets per operation: `(operation, account)` (default **`5` requests / `60s`**) and `(operation, client_ip)` (default **`20` requests / `60s`**), configurable via `Settings` (`profile_gate_account_limit`, `profile_gate_ip_limit`), LRU-capped at `MAX_TRACKED_KEYS = 1024`. Never keyed by child ID or content.
  - Exceeding either bucket returns **`429 RATE_LIMITED`** with integer header `Retry-After` (minimum `1` second, set to `retry_after_seconds` in CONV-1) and writes no audit entry, receipt, or ID-bearing log line (`be1_registry.py:1299`).
  - *Implementation caveat (`rate_limit.py:5-6`):* state is process-local in-memory (`X-18`), so multiple worker processes multiply effective limits and restarts reset counters.
- **Room-code join gate (`be1_sessions.py:93, 163, 1228`):** caps attempts at `_ROOM_CODE_RATE_LIMIT = 10` and returns `429 ROOM_CODE_RATE_LIMITED`.
- **Auth registration & password recovery (`auth_registration.py:184, 195`, `password_recovery.py:25`):** returns `429 RATE_LIMITED` (with `Retry-After` on registration).

---

## Phase D and E additions (PENDING-MERGE)

All items below exist in the working trees of branches `feature/backend-srs-api-v4-d` (`v4d`), `feature/backend-srs-api-v4-d2` (`v4d2`), and `feature/backend-srs-api-v4-e` (`v4e`), and are not yet merged into integration (`297f2849`).

### New Wire Error Codes (`PENDING-MERGE`)

| Code | HTTP status | Meaning | Where it is raised (file:line, route family) | Retryable | Status |
|---|---|---|---|---|---|
| `ACTIVITY_DRAFT_PROVIDER_UNAVAILABLE` | `503` | Activity draft AI fallback generator is unavailable when catalog suggestions are exhausted; CONV-1 defines English copy in `MESSAGES`, while `ParentStoryErrorEnvelopeV1` emits the code verbatim with fallback `"Không thể hoàn tất yêu cầu."` (not in `safe_messages`). | `v4d2`: `backend/src/sketch2life/interfaces/http/error_envelope.py:164`, `backend/src/sketch2life/application/services/activity_suggestion_rounds.py:140, 169, 185, 189, 227-228`, `backend/src/sketch2life/interfaces/http/app.py:598-615`, `backend/src/sketch2life/interfaces/http/routers/parent_story_activity_suggestions.py:185-186` | `Yes` (`app.py:616`) | `PENDING-MERGE` (`v4d2`) |
| `ACTIVITY_DRAFT_QUALITY_FAILED` | `422` | AI-generated activity draft batch failed domain safety, contact/PII, length, or novelty checks; `ParentStoryErrorEnvelopeV1` emits the code verbatim with fallback `"Không thể hoàn tất yêu cầu."`. | `v4d2`: `backend/src/sketch2life/interfaces/http/error_envelope.py:165`, `backend/src/sketch2life/application/services/activity_suggestion_rounds.py:194, 206, 212, 216, 229`, `backend/src/sketch2life/infrastructure/story_activity/rounds_repository.py:43, 440, 444, 455`, `backend/src/sketch2life/interfaces/http/app.py:598-615`, `backend/src/sketch2life/interfaces/http/routers/parent_story_activity_suggestions.py:185-186` | `No` | `PENDING-MERGE` (`v4d2`) |

### Convention Extensions and Notable Route-Level Differences (`PENDING-MERGE`)

- **CONV-1 path allowlist extensions (`v4e`):** `PARENT_CONSENT_POLICY_PATH = "/v1/parent/consent-policy"` and `PARENT_SHARE_GRANTS_BASE = "/v1/parent/share-grants"` added to CONV-1 path matching (`v4e` `backend/src/sketch2life/interfaces/http/error_envelope.py:41-45, 248-252`).
- **`ParentStoryErrorEnvelopeV1` pass-through (`v4d2`):** `/v1/story-runs/{run_id}/activity-suggestions*` routes use `ParentStoryErrorEnvelopeV1` (`backend/src/sketch2life/interfaces/http/app.py:580-620`) instead of CONV-1; uppercase `[A-Z][A-Z0-9_]{0,63}` codes pass through verbatim and fall back to `"Không thể hoàn tất yêu cầu."` when absent from `safe_messages`.
- **Occupied-class assignment replaces `CLASS_TEACHER_EXISTS` (`v4d`):** `POST /api/be1/v1/classes/{class_id}/assignments` no longer fails with `409 CLASS_TEACHER_EXISTS` on an active occupied class; instead it starts a `202` `REASSIGN` saga (and returns `409 RESOURCE_CONFLICT` if a transfer is already `transfer_pending`, `v4d` `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:509-547`). Because `v4d`/`v4d2` branched before `T-CAP1` landed on integration, `CLASS_CAPACITY_REACHED`, `CLASS_SELECTION_REQUIRED`, `INVALID_CAPACITY_DOWNGRADE`, and `SUBSCRIPTION_PERIOD_ENDED` are absent from `v4d`/`v4d2` until rebased.
- **Internal transfer status diagnostic codes (`v4d`):** `Be1TeacherAssignmentTransferStatusV1.last_failure_code` records internal strings `STORY_TRANSFER_UNCERTAIN`, `STORY_RECEIPT_MISMATCH`, and `BE1_FINALIZE_UNCERTAIN` when entering `RECONCILE_REQUIRED` (`v4d` `backend/src/sketch2life/application/services/teacher_assignment_transfer.py:49, 55, 72`); these appear on status polling payloads, not HTTP error `code` envelopes.
- **Parent share-grants validation details (`v4e`):** missing/invalid `If-Match` on `POST /v1/parent/share-grants/{share_grant_id}/revoke` raises `400 INVALID_REQUEST` with `field_errors` (not `428`), and `cursor` length is capped at `2048` (`v4e` `backend/src/sketch2life/interfaces/http/routers/parent_share_grants.py:121-135`, `profile_sharing_errors.py:21-40`).
- **Lesson feedback `INVALID_LENGTH` (`v4e`):** `LessonFeedbackService.submit` emits `field_errors=[{"field": "feedback_text", "code": "INVALID_LENGTH"}]` (`v4e` `backend/src/sketch2life/infrastructure/lesson_library/feedback.py:278`), though Pydantic validation at the router runs first and CONV-1 filters `field_errors[].code` against `FIELD_ERROR_CODES` (`v4e` `backend/src/sketch2life/interfaces/http/error_envelope.py:46, 296`).

### NOT BUILT YET

- `T-6c` active-story-run conflict / force-close error codes (`GET .../active-story-run-conflict`, `POST .../story-runs/{run_id}/force-close`): routes and error codes are absent from `v4d`, `v4d2`, and `v4e`.
