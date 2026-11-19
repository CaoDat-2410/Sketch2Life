# FEAT-066 CONV-1 — BE implementation approval package (Draft 4)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package proposes a bounded BE slice. It authorizes no code, test, OpenAPI change, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 3 (40,443 B, `32C02616…`). Earlier review rounds:
  - Round 1, on Draft 1 (18,780 B, `7B638AE3…`): NOT READY with 1 P1, 8 P2 and 7 P3. Record: `evidence/notes/CONV_1_COLD_REVIEW_DRAFT1_20261118.md`.
  - Round 2, on Draft 2: NOT READY with 1 P1, 1 P2 and 13 P3. Record: `evidence/notes/CONV_1_COLD_REVIEW_DRAFT2_R2_20261118.md`.
  - Round 3, on Draft 3: NOT READY with 0 P1, 2 P2 and 8 P3. Record: `evidence/notes/CONV_1_COLD_REVIEW_DRAFT3_R3_20261118.md`. Both D-171 stop conditions were met, and the owner chose "Draft 4 + round 4" (2026-11-18).
  - §11 maps each round-1 finding to its fix, §12 does the same for round 2, and §13 for round 3.
- **Place in the plan:** Phase B, BE queue slot 1. The queue is CONV-1 → FR-C-08 → SEED-1 → Billing B-1.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, `B9B1F42D…`. Clauses: §9.8 (lines 847–875), §21.1 (lines 1632–1641), §21.4 (lines 1695–1701) |
| Conventions contract | `plan/PLAN_API_CONVENTIONS_CONTRACT_DRAFT1_20261118.md`, 13,999 B, `1F41B74AD0F0A8425D5843851FEBA0CCFFDCD6D1572EE159E967F528C7D9DB01` |
| Owner decisions | `DECISIONS.md` D-066-68 (C-D1 to C-D10) and D-066-69. The CONV-1 answers of 2026-11-18 are in §8. They are recorded as a decision row when this package is approved. That row records CV-1 as a **scoped deferral** of C-D1's "every route": `/api/parent/v1/ai` keeps its current body until C-P |
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
| `HTTPException(422, …)` raised by in-scope routes | <ul><li>**Lesson Library router and service:** `INVALID_REQUEST` at about 15 sites, including the malformed `If-Match` at `routers/lesson_library.py:91`; also `INVALID_SOURCE_DOCUMENT`, `MALWARE_DETECTED`, and a dynamic `exc.code` (`service.py:844`).</li><li>**BE1:** `IDEMPOTENCY_KEY_REQUIRED` (`routers/be1_sessions.py:128`); `CLASS_SCOPE_MISMATCH` (`be1_records.py:341`, `be1_registry.py:412` and `:505`); `CANVAS_IMAGE_NOT_ADMITTED`; `CANVAS_PROFILE_INVALID` (`be1_canvas.py:279`, `:369`); `CONTRIBUTORS_REQUIRED`; `IMAGE_INVALID`; `RESERVED_CONFIGURATION_KEY`; and dynamic `CoreRuleViolation` codes (`be1_registry.py:443`).</li><li>**Platform Admin:** `ORGANIZATION_UNAVAILABLE` and `ORGANIZATION_REQUIRED` (`platform_admin_accounts.py:149`, `:402`).</li><li>**Teacher AI:** `TEACHER_PLAN_FIELD_LIMIT_EXCEEDED`.</li></ul> |
| Error details sent by routes | Platform Admin, auth and Teacher AI send **dict** details with a `code` (`platform_admin_accounts.py:108`, `auth_registration.py:113`, `teacher_ai.py:64` and `:89`). Teacher AI's Modal errors also carry the route's own `request_id` (`teacher_ai.py:112`, `:122`). String details come only from Starlette (404 for an unknown path, 405) |
| Pre-guard checks in `be1_registry.py` | `_scope_denied()` is a uniform 403 `SCOPE_DENIED` (lines 57–58). It is used when the class lookup finds nothing in `assign_class_teacher` (lines 136–142) and `create_profile` (lines 421–430), and after the guard (line 439). The wrapper `_require_m2_assignment` (lines 61–83) rewrites the guard's 403 `ADULT_NOT_ASSIGNED` and `SCOPE_DENIED` to that same 403. An M2 design choice therefore makes "missing" and "not assigned" look identical |
| Other 403 checks in scope (kept) | Device guards in `interfaces/http/be1_runtime.py` (lines 210–241, 353–391); `be1_canvas.py:370–371`, which maps the device-bound domain codes `FORBIDDEN_ROLE`, `SCOPE_DENIED` and `INVALID_TURN` to 403; `teacher_ai.py:88` `TEACHER_ORGANIZATION_ACCESS_REQUIRED`; Lesson Library `_platform_admin` and `_parent_actor` (`lesson_library.py:119–144`); `platform_admin_accounts.py:107`; `auth_registration.py:197`, `ACCOUNT_SETUP_UNAVAILABLE`, which SRS §9.8 line 866 lists under 409 and which is deferred to C-A; the Lesson Library self-approval refusal (`service.py:1199`) |
| Code that branches on the guard's status | Two places only (static grep for `status_code` checks in `interfaces/http/`):<ul><li>`be1_registry.py:80`, handled in §3.2 item 3;</li><li>`lesson_library.py:611–617`, `revoke_parent_group_membership`. It calls `_manager` (`require_assignment` with `roles={"school_admin"}`) and swallows **only a 403**, so a caller who is not a manager falls through to the Parent self-revoke path (`service.py:1609`). A Parent account gets 403 `ACCOUNT_SCOPE_UNAVAILABLE` today; it would get 404 after §3.2 item 3.</li></ul> |
| Shared scope guard | `interfaces/http/routers/be1_common.py` `require_assignment` (lines 83–139):<ul><li>a missing, inactive, wrong-role or unassigned account gets 403 `ACCOUNT_SCOPE_UNAVAILABLE` (line 114);</li><li>a `Be1PolicyError` gets 403 with its code (line 137).</li></ul>The policy (`application/services/be1_runtime.py:45–70`) raises `ADULT_NOT_ASSIGNED`, `IDENTITY_ISSUER_MISMATCH`, or `SCOPE_DENIED` for an organization or class mismatch **and** for a role outside `roles` |
| Idempotency-key rule | `routers/parent_profiles.py` `_idempotency_key` (lines 103–115): exactly one value of 1–128 characters in ASCII 33–126. A missing key gives field code `REQUIRED`; anything else gives `INVALID_FORMAT`. Both return 400 `INVALID_REQUEST` |
| Field-error vocabulary | `contracts/schemas/parent_profiles.py` `parent_field_errors` (lines 81–122): codes `REQUIRED`, `TOO_LONG`, `OUT_OF_RANGE`, `EMPTY`, `INVALID_TYPE`, `INVALID_FORMAT` and `UNKNOWN_FIELD`. Unknown names become `<unknown>` |
| Revision | Lesson Library `If-Match`:<ul><li>missing gives 428 `PRECONDITION_REQUIRED` (`lesson_library.py:86`);</li><li>malformed gives **422** `INVALID_REQUEST` (line 91);</li><li>stale gives 409 `STALE_REVISION` with no `current_version` or ETag (`infrastructure/lesson_library/service.py:599`).</li></ul> |
| OpenAPI | `interfaces/http/openapi_contract.py` is generated from the FEAT-063 Rev37 catalog and carries hand amendments since MGR-7. Error rows are published through `interfaces/http/openapi_contract_amendments.py`:<ul><li>`BE1_EXPLICIT_ERROR_STATUSES = {"401","403","422"}` (line 9);</li><li>`RESTORE_CHECKPOINT_STATUS_CODES`, which includes `"422"` (lines 19–21), and the restore-checkpoint descriptions and examples (lines 19–130);</li><li>`published_responses` (line 1254), which groups errors only for `/api/be1/v1/` and returns catalog rows unchanged for every other path (lines 1279–1288).</li></ul>`app.py` `_apply_catalog_metadata` (lines 250–340) deletes undeclared runtime statuses only for `/api/be1/v1/` and `/v1/parent/profiles` (lines 296–299). FastAPI's automatic 422 therefore stays on the other families. `interfaces/http/openapi_srs_v22.py` renames `Be1Error` to `ApiError` (lines 213–235). `app.py` builds the runtime schema at lines 1174–1368 |

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
  - every other 422 code stays 422, including dynamic codes. These are domain codes, aligned in their own slices under CV-2 = A:

    | Family | Codes kept at 422 | Slice |
    |---|---|---|
    | Lesson Library | `INVALID_SOURCE_DOCUMENT`, `MALWARE_DETECTED`, dynamic `exc.code` | C-T, including the Lesson Library work |
    | BE1 | `CANVAS_IMAGE_NOT_ADMITTED`, `CANVAS_PROFILE_INVALID`, `CONTRIBUTORS_REQUIRED`, `IMAGE_INVALID`, `RESERVED_CONFIGURATION_KEY`, dynamic `CoreRuleViolation` codes, `CLASS_SCOPE_MISMATCH` | C-M and C-T |
    | Platform Admin | `ORGANIZATION_UNAVAILABLE`, `ORGANIZATION_REQUIRED` | C-A |
    | Teacher AI | `TEACHER_PLAN_FIELD_LIMIT_EXCEEDED` | C-T |

  - Several of these codes are validation-type, so **C-D3 is only partly applied in CONV-1**, as CV-2 = A intends. The rest is applied in the named slices.
  - `CLASS_SCOPE_MISMATCH` is also a route-specific scope check (C-D4: "route-specific checks change in their own slices"). `be1_records.py:341` can reveal that a session exists in another class.
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
  - **Every other domain code keeps its name.** This includes two 404 codes that do not end in `_NOT_FOUND`:
    - `JOIN_UNAVAILABLE`, which is already a uniform anti-enumeration code for join attempts;
    - `CANVAS_SOURCE_UNAVAILABLE`, which is listed for C-T.
  - **Status defaults** apply when a detail has no code. That happens for Starlette's string details (an unknown path gives 404, a wrong method gives 405) and for any route that omits a code. In-scope routes normally send dict details with codes.

    | Status | Default code |
    |---|---|
    | 400 | `INVALID_REQUEST` |
    | 401 | `AUTH_REQUIRED` |
    | 403 | `ACTION_NOT_ALLOWED` |
    | 404 | `RESOURCE_NOT_FOUND` |
    | 405 | `ACTION_NOT_ALLOWED` |
    | 409 | `INVALID_STATE_TRANSITION` |
    | 413 | `MEDIA_TOO_LARGE` |
    | 415 | `UNSUPPORTED_MEDIA_TYPE` |
    | 429 | `RATE_LIMITED` |
    | 500 | `INTERNAL_SERVER_ERROR` |
    | 502 | `PROVIDER_BAD_RESPONSE` |
    | 503, 504 | `PROVIDER_UNAVAILABLE` |
    | Any other 4xx | `INVALID_REQUEST` |
    | Any other 5xx | `INTERNAL_SERVER_ERROR` |

  - **Route-supplied `request_id` in a detail** (Teacher AI Modal errors) is not copied into the body. The body's `request_id` and `correlation_id` are always the `X-Request-ID` value. The web Teacher pages read `request_id` only from **success** responses (`TeacherAiLessonWorkflowPage.tsx:105`, `:111`, `:150`, `:169`). Making the Teacher AI route log the middleware ID is listed for C-T.
- **c. Messages** (CV-3 = A):
  - `message` comes from one code-to-Vietnamese table in `error_envelope.py`. Route-supplied message text is ignored.
  - A code missing from the table gets the Vietnamese message for its status.
  - **Coverage test.** It scans the source of these modules (all paths under `backend/src/sketch2life/`):
    - `interfaces/http/routers/` — `be1_common.py`, `be1_runtime.py`, `be1_sessions.py`, `be1_registry.py`, `be1_canvas.py`, `be1_artifacts.py`, `be1_records.py`, `pilot_assistance.py`, `lesson_library.py`, `platform_admin_accounts.py`, `auth_registration.py` and `teacher_ai.py`;
    - `interfaces/http/be1_runtime.py`;
    - `infrastructure/lesson_library/service.py`.

    It looks for string code literals passed to `failure(...)`, `fail(...)` and `HTTPException(detail={"code": …})`.
    - Each literal must be either in the table or in an explicit `STATUS_MESSAGE_ONLY` set. A new literal therefore fails the test until someone classifies it.
    - Codes built at run time (`exc.code` and `CoreRuleViolation` codes) cannot be seen by a scan. They always use the status message. The test asserts that.
    - The table holds the §9.8 generic codes and the codes the owner wants worded. Everything else goes in `STATUS_MESSAGE_ONLY`, so the table stays small.
- **d. Validation errors** (C-D3): 400 `INVALID_REQUEST` with `field_errors` `[{field, code}]`, as follows.
  - **Codes:** the Parent vocabulary — `REQUIRED`, `TOO_LONG`, `OUT_OF_RANGE`, `EMPTY`, `INVALID_TYPE`, `INVALID_FORMAT`, `UNKNOWN_FIELD`. Pydantic error types map as follows:

    | Pydantic error type | Code |
    |---|---|
    | `missing` | `REQUIRED` |
    | `string_too_long`, `too_long` | `TOO_LONG` |
    | `greater_than`, `greater_than_equal`, `less_than`, `less_than_equal` | `OUT_OF_RANGE` |
    | `string_too_short`, `too_short` | `EMPTY` |
    | `int_type`, `int_parsing`, `float_type`, `string_type`, `bool_type`, `model_type`, `list_type`, `dict_type` | `INVALID_TYPE` |
    | `extra_forbidden` | `UNKNOWN_FIELD`, with field `<unknown>` |
    | anything else, including `value_error` | `INVALID_FORMAT` (deliberately different from the frozen Parent-profiles code, which maps `value_error` to `EMPTY`) |

    **Exception:** for the `Idempotency-Key` header, `missing` gives `REQUIRED` and every other issue gives `INVALID_FORMAT` (item 2e).
  - **Field names:** only names the route itself declares. That means its query, path and header parameter names, under both their alias (for example `If-Match`, `Idempotency-Key`) and their Python name, and the field names and aliases of its body models.
    - The model walk is recursive, with a visited-set guard against recursive models.
    - Anything else becomes `<unknown>`: keys of free-form dictionaries, `extra_forbidden` keys, and names longer than 120 characters. List indexes are dropped.
    - This lives in `api_conventions.py` as `field_errors_from_validation(route, issues)`. It reads the route from `request.scope["route"]`.
  - **Field errors from a route's `HTTPException` detail** are accepted only when they are a list of `{field, code}` with `code` in the vocabulary above and `field` a string of 120 characters or fewer. This is how item 6's `If-Match` errors reach the body. Any other shape is dropped.
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
- **Issuer mismatch → 404** is the coordinator's reading of CV-5. It is an account-level identity failure, like an inactive account. The owner may change it at approval (§8).
- **Pre-guard checks in `be1_registry.py`.** If these were left alone, a missing class (uniform 403) and an existing but unassigned class (404 from the guard) would become distinguishable. CONV-1 therefore changes them:
  - `_scope_denied()` returns **404 `RESOURCE_NOT_FOUND`**. This covers the missing-class lookups in `assign_class_teacher` (line 142) and `create_profile` (line 430), and the not-a-teacher-of-this-class check (line 439).
  - `_require_m2_assignment` rewrites the guard's **404** to `_scope_denied()`, so every out-of-scope case on these routes has one body. It passes the guard's in-scope **403 `ACTION_NOT_ALLOWED`** (role refusal) through unchanged.
  - Test 15 checks, for both routes, that a missing class and an existing but unassigned class return byte-identical bodies apart from `correlation_id` and `request_id`.
- **Parent self-revoke in `lesson_library.py:611–617`.** The catch is widened to **403 and 404**, so a Parent account (404 after this item) and a School Manager or Teacher whose role is refused (403) both still fall through to the Parent self-revoke path, as they do today. Any other status is re-raised. Test 22 gains a Parent self-revoke case through this route.
- **Audit of the other in-scope routers** (coordinator, static grep, 2026-11-18):
  - **403 raises:** every 403 raised in the in-scope modules was listed. Apart from `be1_common.py` and `be1_registry.py`, they are the kept checks in §2: device guards, Teacher AI organization access, the Lesson Library actor guards, Platform Admin, auth and Lesson Library self-approval. None of them depends on whether a target resource exists.
  - **Other statuses, not audited:** non-403 errors raised **before** a guard (for example a 409 or 422 after a lookup) were not checked. The one known case, `be1_records.py:341`, runs after the guard.
  - **Consumers of the guard's status:** only `be1_registry.py:80` and `lesson_library.py:616` (see above).
  - **Implementer steps:** before editing, the implementer repeats both audits for every in-scope router. The first covers any non-404 error that depends on existence and is raised before `require_assignment`. The second covers every `except HTTPException` around `require_assignment`, `_manager`, `_teacher` or the `be1_registry` wrapper. Any new case stops the task for an owner scope amendment.
- **Not in CONV-1:** route-specific checks (`CLASS_SCOPE_MISMATCH` above) and the kept 403 checks listed in §2 keep their status. Only their codes are renamed, where item 2b applies. They are listed for the C-M, C-T and C-A slices.

**4. Correlation header** (C-D2, §21.1):
- Every response produced inside the app carries `X-Request-ID`. A supplied safe ID is echoed; otherwise a UUID is generated.
- On in-scope families the body's `correlation_id` equals the header.
- The middleware sets the header for every path, but **never overwrites an `X-Request-ID` that the route already put on the response**. Today that exception covers only story-runs and Parent profiles (`app.py:446–450`). It is widened to every path, so that a route that sets its own header keeps it. Today only the Parent-profiles routes set one. The legacy routers (`images.py:43`, `sessions.py:55`, `supervised_flow.py`) only **require** the inbound header, and they are unaffected.
- The unhandled-exception handler adds the header on every path, including the legacy paths, where the body stays plain text.
- **Exception:** a crash before the app stack (Starlette's `ServerErrorMiddleware` when the handler itself fails). AC5 is limited to responses produced inside the app stack.

**5. Upload-limit middleware** (`bounded_image_upload.py`, Lesson Library part branch only):
- The `else` branch of `_send_too_large` is shared with `/api/dev/v1/storage-examples`. The change is therefore **conditioned on the path starting with `/api/lesson-library/v1/`**.
- For that path, the 413 body becomes the envelope. The code stays `REQUEST_TOO_LARGE` until C-T, per item 2b.
- The response gets an `X-Request-ID` header, taken from a safe supplied ID or newly generated. The `"request-body-limit"` placeholder is dropped.
- The image, audio, demo and storage-example responses are not changed. The storage-example 413 keeps having no header; it is a dev-only path and is named as an exception in AC5.

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

**8. OpenAPI**, for the **catalogued families only**: BE1 and Lesson Library.
- **Why only these two:** `_apply_catalog_metadata` skips any operation that has no catalog row (`app.py:273–275`). `openapi_contract.py` has rows for BE1 and Lesson Library, and none for Platform Admin, auth or Teacher AI.
- **Platform Admin, auth and Teacher AI:**
  - Their **runtime** errors change (items 2 to 4).
  - Their OpenAPI documentation keeps FastAPI's automatic 422 until their slices: C-A for Platform Admin and auth, C-T for Teacher AI (§6).
  - This mismatch between documentation and runtime is accepted and recorded.
- **BE1 operations** (`/api/be1/v1/`), in `openapi_contract_amendments.py`:
  - `BE1_EXPLICIT_ERROR_STATUSES` becomes `{"400", "401", "403", "404"}`;
  - `published_responses` publishes **400** for every BE1 operation;
  - it keeps a **422** row only for the operations on a named list, `BE1_KEPT_422_OPERATIONS`. Catalog rows carry no error code, so the rule cannot read one. The list holds the operations whose handlers can raise a kept 422 code from the item 2a table (for example the `create_profile`, canvas and artifact operations). The implementer builds it from the handlers, records it in the evidence note, and test 16 asserts it.
  - The restore-checkpoint constants (`RESTORE_CHECKPOINT_STATUS_CODES` and the restore-checkpoint descriptions and examples, lines 19–130) get 400 in place of the validation 422, and the new codes.
- **Lesson Library operations:**
  - `published_responses` gets a branch for the `/api/lesson-library/v1/` prefix, beside the non-BE1 return at lines 1279–1288. It publishes 400 with the envelope schema, and keeps 422 only on the operations listed in `LESSON_LIBRARY_KEPT_422_OPERATIONS`, built the same way (`INVALID_SOURCE_DOCUMENT`, `MALWARE_DETECTED` and the dynamic code).
  - `app.py` `_apply_catalog_metadata` is extended at lines 296–299 so that the Lesson Library prefix also loses undeclared runtime statuses, including FastAPI's automatic 422, as BE1 and Parent profiles already do.
- `/api/parent/v1/ai` and the legacy families are not touched.
- **Schema:** `Be1Error` becomes the envelope model. `openapi_srs_v22.py` still publishes it as `ApiError`.
- **The generated `openapi_contract.py`:** edited only if the catalog rows themselves must change. Any such edit is recorded as a hand amendment, as MGR-7's were, and the Rev37 source pin is not changed.

### 3.3 Explicitly out of scope

- No route move, rename or new prefix (C-D9).
- No new `Idempotency-Key` requirement on a route that takes no key today.
- No cursor paging for accounts, no paging for BE1 lists, and no change to the BE1 canvas `limit` of 500.
- No `/api/parent/v1/ai` change (CV-1).
- No upload or file code or status alignment (CV-2 = A).
- No route-specific scope check change, apart from the `be1_registry.py` pre-guard fix in §3.2 item 3. No change to the kept 403 checks listed in §2.
- No Lesson Library stale-revision payload change.
- No FE, mobile or Bruno file.
- No change to `assistance_requests.py`. It is mounted under `/api/be1/v1` through `pilot_assistance` and builds its own `CollaborationErrorV1` response (`assistance_requests.py:207`), which the handlers never see. It is excluded from AC1 and listed for C-T.
- No OpenAPI change for Platform Admin, auth or Teacher AI (item 8).
- No migration, dependency, `uv.lock` or `pyproject.toml` change.
- `application/services/be1_runtime.py` is not changed.

## 4. Proposed exact allowlist

All paths are under `backend/`.

**Source**

| # | File | Limit |
|---|---|---|
| 1 | `src/sketch2life/interfaces/http/app.py` | The middleware, the three handlers, and `_apply_catalog_metadata` (lines 250–340) for the 400 |
| 2 | `src/sketch2life/interfaces/http/error_envelope.py` | New |
| 3 | `src/sketch2life/interfaces/http/api_conventions.py` | New |
| 4 | `src/sketch2life/interfaces/http/routers/be1_common.py` | `require_assignment` and the shared `responses` declarations |
| 5 | `src/sketch2life/contracts/schemas/be1_runtime.py` | `Be1Error` only |
| 6 | `src/sketch2life/interfaces/http/routers/lesson_library.py` | The `If-Match` helper (lines 80–95) and the `revoke_parent_group_membership` catch (lines 611–617) only |
| 7 | `src/sketch2life/interfaces/http/middleware/bounded_image_upload.py` | The Lesson Library part branch of `_send_too_large` only |
| 8 | `src/sketch2life/interfaces/http/openapi_contract_amendments.py` | `BE1_EXPLICIT_ERROR_STATUSES`; the restore-checkpoint constants, descriptions and examples (lines 19–130); `_RESPONSE_DESCRIPTIONS_BY_STATUS`; `published_responses` |
| 9 | `src/sketch2life/interfaces/http/openapi_srs_v22.py` | Only if the `Be1Error` → `ApiError` projection needs an edit |
| 10 | `src/sketch2life/interfaces/http/openapi_contract.py` | Only the error-response rows of in-scope operations, only if item 8 cannot express the change, recorded as a hand amendment |
| 29 | `src/sketch2life/interfaces/http/routers/be1_registry.py` | `_scope_denied` and `_require_m2_assignment` only (§3.2 item 3). Numbers are kept from Draft 3, so row 29 sits here |

**Tool**

| # | File |
|---|---|
| 11 | `tools/be1_api_smoke.py` (its 422, `REQUEST_VALIDATION_FAILED` and `Be1Error` checks) |

**Tests, new**

| # | File | Covers |
|---|---|---|
| 12 | `tests/unit/test_http_error_envelope.py` | Builder, derivation, message table, coverage scan |
| 13 | `tests/unit/test_http_api_conventions.py` | Key parser, `limit`, stale helper, field-error reduction including `<unknown>` |
| 14 | `tests/contract/test_http_error_conventions.py` | Through `create_app`:<ul><li>each in-scope family's envelope, with the header equal to the body;</li><li>400 validation and `limit` above 100;</li><li>the 422 remap;</li><li>the unhandled 500;</li><li>the Lesson Library 413 from the middleware;</li><li>the `If-Match` cases;</li><li>a route-set `X-Request-ID` is not overwritten;</li><li>a `/api/parent/v1/ai` 4xx body still uses `{"detail": …}` (CV-1).</li></ul> |
| 15 | `tests/unit/test_be1_scope_guard_404_403.py` | Each §3.2 item 3 branch: missing, inactive, wrong role, organization not covered, class not covered, issuer mismatch, and role refused in scope. Also, for `assign_class_teacher` and `create_profile`: a missing class and an existing but unassigned class give the same body. Uses a fake `Session` |

**Tests, existing.** Edits are limited to status, code, envelope and message assertions:

| # | File |
|---|---|
| 16 | `tests/contract/test_openapi_contract_catalog.py` |
| 17 | `tests/contract/test_openapi_schema_catalog_mapping.py` |
| 18 | `tests/contract/test_app_composition.py` |
| 19 | `tests/contract/test_auth_registration_api.py` |
| 20 | `tests/contract/test_m2_s1a_teacher_routes.py` |
| 21 | `tests/contract/test_assistance_requests_api.py` |
| 22 | `tests/integration/lesson_library/test_lesson_library_api.py` (also gains a Parent self-revoke case, §3.2 item 3) |
| 23 | `tests/integration/test_be1_postgres_api.py` |
| 24 | `tests/integration/test_be1_synthetic_pilot_postgres.py` |
| 25 | `tests/integration/test_m2_s1a_teacher_postgres.py` |
| 26 | `tests/integration/test_pilot_assistance_routes_t9.py` |
| 27 | `tests/unit/test_pilot_queue_composition_b1.py` |
| 28 | `tests/unit/test_synthetic_status_guard.py` |

- **Dropped from the edit list since Draft 1:** `test_activity_execution_http.py` and `test_live_image_demo_api.py`. They do not pass through the in-scope handlers.
- **If another file needs an edit,** the task stops and needs an owner scope amendment.
- **Regression guards, which must pass unchanged:**
  - `tests/contract/test_parent_profiles_routes.py`
  - `tests/contract/test_parent_story_run_request_contract.py`
  - `tests/contract/test_parent_ai_late_result_guards.py`
  - `tests/integration/test_m2_s1a_parent_postgres.py`
  - `tests/integration/test_m2_s2_g1_parent_story_postgres.py`
  - `tests/integration/test_m2_s1a_p2_parent_postgres.py`
  - `tests/contract/test_parent_story_run_cancel_route.py`
  - `tests/contract/test_live_image_demo_api.py` (legacy `X-Request-ID` handling)
  - `tests/contract/test_session_http_api.py` (legacy `X-Request-ID` handling)
  - `tests/contract/test_be1_synthetic_pilot.py` (structure checks on `be1_registry`)

**Governance documents** (outside the BE allowlist, written by the coordinator, append-only): the FEAT-066 `STATUS.md` and `CONTEXT.md` entries, the decision row in `DECISIONS.md`, the Task Approval entry, and the CONV-1 evidence note under `evidence/notes/`.

## 5. Acceptance criteria

1. In-scope families (except `assistance_requests.py`, §3.3) return the C-D1 envelope, with all six fields, on HTTP errors, validation errors and unhandled errors, and on the Lesson Library 413 from the middleware. The `X-Request-ID` header equals `correlation_id`.
2. In-scope validation errors return 400 `INVALID_REQUEST` with field errors from the Parent vocabulary and only declared field names. A `limit` above 100 gives 400. HTTP 422 with `INVALID_REQUEST` or `IDEMPOTENCY_KEY_REQUIRED` is remapped to 400. The listed domain 422 codes stay 422.
3. Every §3.2 item 3 branch returns the stated status and code. A non-existent ID and an out-of-scope resource give the same 404 body shape.
4. Codes follow the §3.2 item 2b table. Messages come only from the Vietnamese table or the status fallback. The coverage test passes. No body contains a route string, a stack trace, a path or an echoed input.
5. Every response produced inside the app stack carries `X-Request-ID`, and a header set by a route is not overwritten. There are two exceptions:
   - a crash outside the app stack (Starlette's `ServerErrorMiddleware`);
   - the dev-only `/api/dev/v1/storage-examples` and legacy demo 413s from the upload middleware.
6. Missing and malformed `If-Match` give 400 with the field errors in §3.2 item 6.
7. Story-runs, Parent-profiles and `/api/parent/v1/ai` responses keep their status and body. Adding an `X-Request-ID` header where none was set is allowed. The ten regression guards pass unmodified.
8. For BE1 and Lesson Library operations, the OpenAPI document shows the envelope (`ApiError`) and 400, and 422 only on the named kept-422 operations. The catalog and mapping tests pass. Platform Admin, auth and Teacher AI documentation is unchanged (item 8).
9. The FE, Bruno and slice follow-ups in §6 are recorded in `STATUS.md`.
10. A Parent self-revoke through `revoke_parent_group_membership` still succeeds (test 22).

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
- **Mobile:**
  - `/api/parent/v1/ai` stays out of scope, so C-P changes that BE body and `parentWorkflowApi.ts` together.
  - `apps/ui-mobile` (the Parent app being ported) also calls in-scope routes. Its `ParentAuth.ts` (lines 67 and 171) calls `/api/auth/v1/registrations` and `/me`. Its `ParentApi.ts` (lines 126–166) calls `/api/lesson-library/v1/me/...`. A read-only check in FEBASE (mobile) covers both apps.
  - `apps/mobile/src/infrastructure/auth/firebaseAuthSession.ts:185` and `:232` call `/api/auth/v1/registrations` and `/me`, which are in scope. They read the top-level `payload.code`, which stays compatible. A validation failure there changes from no code to `INVALID_REQUEST`. This needs a read-only check in FEBASE (mobile).
- **Bruno:** BRU-0 updates the in-scope status and code assertions.

**Slices that pick up deferred items:**

| Slice | Deferred item |
|---|---|
| C-T, including the Lesson Library work | Upload and file code and status alignment; the Lesson Library and Teacher AI domain 422 codes; Teacher AI logging the middleware request ID; Teacher AI OpenAPI errors; `assistance_requests.py` envelope; ClamAV |
| C-M and C-T | The BE1 domain 422 codes; `CLASS_SCOPE_MISMATCH` and route-specific scope checks |
| C-A | The Platform Admin domain 422 codes (`ORGANIZATION_UNAVAILABLE`, `ORGANIZATION_REQUIRED`); the Platform Admin and auth OpenAPI errors; the account `Idempotency-Key` requirement (D-066-69 O-ACCREV, C-D5); `ACCOUNT_SETUP_UNAVAILABLE` status (403 today, 409 in §9.8) |
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
  - the ten regression guards;
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
| CV-5 (extension) | An identity-issuer mismatch also gives 404. This is the coordinator's reading of CV-5, open to the owner's change at approval | Not yet confirmed by the owner |

## 9. Proposed Task Approval entry (draft text, not written)

> FEAT-066 CONV-1 — API conventions core. Status: APPROVED_FOR_IMPLEMENTATION when the owner approves this package at its reviewed pin.
> - **Branch:** `feature/feat066-conv1` from `08439b22`, local only, with no push.
> - **Allowlist:** files 1–29 of §4, within each row's stated limit, plus the governance documents named in §4. Edits to tests 16–28 are limited to status, code, envelope and message assertions.
> - **Behaviour:** §3.2 items 1–8, with the §8 answers.
> - **Exclusions:** §3.3.
> - **Verification:** §7.
> - **Git:** no stage or commit without a separate owner word, and never a push.

## 10. Not verified

- Whether every test file in 16–28 needs an edit, and whether another file does. That is a stop condition (§4).
- Whether `_apply_catalog_metadata` (`app.py` lines 250–340) is the only place that keeps FastAPI's automatic 422 for non-BE1 paths. The runtime builder (lines 1174–1368) was not traced line by line.
- Non-404 errors raised before a guard in `be1_sessions.py`, `be1_canvas.py`, `be1_artifacts.py` and `pilot_assistance.py`. This is the implementer step in §3.2 item 3.
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

## 12. Round-2 findings and their fixes

| Finding | Fixed in |
|---|---|
| N1 (P1) | §2 (`be1_registry.py` pre-guard row); §3.2 item 3 (`_scope_denied` gives 404, the wrapper maps the guard's 404, and an audit plus implementer step); §4 row 29; test 15 checks that both bodies are identical |
| N2 (P2) | §2 OpenAPI row (cites `app.py` lines 250–340 and amendments lines 1279–1288); §3.2 item 8 (separate BE1 and non-BE1 mechanisms; the restore-checkpoint constants); §4 rows 1 and 8 |
| N3 | §2 "error details" row; §3.2 item 2b (status-default table with 4xx and 5xx fallbacks; `JOIN_UNAVAILABLE` and `CANVAS_SOURCE_UNAVAILABLE` kept; Teacher AI `request_id` handling) |
| N4 | §2 "other 403 checks (kept)" row; §3.2 item 3 issuer note; §8 CV-5 extension row |
| N5 | §2 422 row; §3.2 item 2a table with slices; §6 slice table |
| N6 | §6 mobile line |
| N7 | §3.2 item 2d error-type table, the `Idempotency-Key` exception, and the detail `field_errors` whitelist |
| N8 | §3.2 item 2c module list and dynamic-code rule |
| N9 | Test 14 `/api/parent/v1/ai` assertion; AC7 reworded |
| N10 | §3.2 item 4 (never overwrite a route-set header); test 14; four legacy and Parent tests added as guards |
| N11 | §3.2 item 5 (Lesson Library prefix condition); AC5 exceptions |
| N12 | §4 governance-documents line; §9 |
| N13 | §3.2 item 2d (aliases, cycle guard) |
| N14 | §1 decision-row note |

## 13. Round-3 findings and their fixes

| Finding | Fixed in |
|---|---|
| R3-01 (P2) | §2 "code that branches on the guard's status" row; §3.2 item 3 (Parent self-revoke catch widened to 403 and 404; a second implementer audit for `except HTTPException` around the guard); §4 row 6 widened; test 22; AC10 |
| R3-02 (P2) | §3.2 item 8 narrowed to the catalogued families BE1 and Lesson Library; Platform Admin, auth and Teacher AI documentation deferred to C-A and C-T and recorded as a known mismatch; §3.3; AC8; §6 |
| R3-03 | §3.2 item 8: named kept-422 operation lists built by the implementer, recorded and asserted |
| R3-04 | §2 kept-403 row adds `be1_canvas.py:370–371` |
| R3-05 | §6 mobile adds `apps/ui-mobile` |
| R3-06 | §3.3 exclusion of `assistance_requests.py`; AC1; §6 C-T |
| R3-07 | §3.2 item 4 rationale reworded |
| R3-08 | §6 C-A row adds the account `Idempotency-Key` requirement |
| R3-09 | Row 29 note; `value_error` difference declared; Lesson Library slice name unified; `ACCOUNT_SETUP_UNAVAILABLE` noted in §2 and §6 |
