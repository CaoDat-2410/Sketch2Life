# FEAT-066 CONV-1 — BE implementation approval package (Draft 1)

- **Status:** DRAFT / NOT REVIEWED / NOT APPROVED / NOT LAUNCHED. This package proposes a bounded BE slice. It authorizes no code, test, OpenAPI change, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Place in the plan:** Phase B, BE queue slot 1. The queue is CONV-1 → FR-C-08 → SEED-1 → Billing B-1, as the owner set on 2026-11-18. It follows the G0 commit `08439b22`.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, SHA-256 `B9B1F42D…`. Clauses: §9.8 error contract (lines 847–875), §21.1 shared HTTP rules (lines 1632–1641), §21.4 idempotency and concurrency (lines 1695–1701) |
| Conventions contract | `plan/PLAN_API_CONVENTIONS_CONTRACT_DRAFT1_20261118.md`, 13,999 B, SHA-256 `1F41B74AD0F0A8425D5843851FEBA0CCFFDCD6D1572EE159E967F528C7D9DB01` |
| Owner decisions | `DECISIONS.md` D-066-68 (C-D1 to C-D10); D-066-69 (O-ACCREV: accounts keep the key requirement and get no revision precondition) |
| Source base | Root checkout, branch `feature/feat063-m2-parent-teacher-foundation`, HEAD `08439b22` (pushed; PR #30 into `dev` is open). Static reading only |

**Branch proposal (decision CV-B, §8):** implement on a new branch `feature/feat066-conv1`, cut from `08439b22`. PR #30 then stays unchanged while it waits for a maintainer. CONV-1 gets its own PR after PR #30 merges, or a PR stacked on it.

## 2. Current state (evidence from the source)

All line numbers refer to `backend/src/sketch2life/interfaces/http/app.py` at `08439b22` unless another file is named.

| Topic | What the source does today |
|---|---|
| Correlation middleware | `be1_request_context` (about lines 420–451) gives an `X-Request-ID` only to paths starting with `/api/be1/v1`, `/api/lesson-library/v1`, `/api/parent/v1/ai/story-runs/`, `/api/parent/v1/ai/drawing-understandings`, `/v1/parent/profiles` and `/v1/story-runs`. A supplied ID is kept only if it matches `_SAFE_ID`. Other paths get no correlation header, but §21.1 asks for "correlation ID … trong mọi response" |
| `StarletteHTTPException` handler (lines 453–646) | Four branches:<ul><li>**story-runs** (§9.8 fields, Vietnamese messages, always all six fields);</li><li>**Parent profiles** (`parent_error_payload`: §9.8 fields plus `request_id`, English messages, null fields omitted);</li><li>**Lesson Library** (`{code, message, request_id}`, route-supplied English message, codes `UNAUTHENTICATED`, `FORBIDDEN`, `INVALID_TRANSITION`, `REQUEST_TOO_LARGE`, `PRECONDITION_REQUIRED`, `DEPENDENCY_UNAVAILABLE`);</li><li>**BE1** (`Be1Error {code, message, request_id}`, codes `AUTHENTICATION_REQUIRED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `REQUEST_VALIDATION_FAILED`, `SERVICE_UNAVAILABLE`; no `X-Request-ID` header on this branch).</li></ul>Every other path falls through to FastAPI's `{"detail": …}` |
| `RequestValidationError` handler (lines 648–816) | story-runs and Parent profiles: 400. BE1: 422 `REQUEST_VALIDATION_FAILED`. Lesson Library: 422 `INVALID_REQUEST`. The P1 context-options routes return a `MobileWorkflowResultV1` at 422. Everything else: 422 `{"detail": "request contract invalid"}` |
| Unhandled `Exception` handler (lines 818–900) | Envelopes for story-runs, Lesson Library, Parent profiles and BE1. Other paths get a plain-text 500 |
| Shared scope guard | `routers/be1_common.py` `require_assignment` (lines 83–139). An account that is missing, inactive, of the wrong role or not assigned to the organization gets 403 `ACCOUNT_SCOPE_UNAVAILABLE` (line 114). A policy refusal for an assigned account gets 403 with the policy code (line 137) |
| Idempotency-key rule | `routers/parent_profiles.py` `_idempotency_key` (lines 103–115): exactly one header value of 1–128 characters, each in ASCII 33–126. A missing key gives field error `REQUIRED`; anything else gives `INVALID_FORMAT`. This is the C-D5 rule |
| Revision | Parent: body `expected_revision`, 409 `STALE_REVISION` with `current_version`. Lesson Library: strong numeric `If-Match`. A missing header gives 428 `PRECONDITION_REQUIRED` (`routers/lesson_library.py:86`). A malformed header gives 400 `INVALID_REQUEST` (line 93). A stale header gives 409 `STALE_REVISION` (`infrastructure/lesson_library/service.py:599`) |
| `limit` | Lesson Library: `Query(default=25 or 50, ge=1, le=100)`. Platform Admin accounts: `Query(default=50, ge=1, le=100)` with offset paging. Parent profiles: default 25. BE1 canvas: `Query(default=200, ge=1, le=500)` (`be1_canvas.py:389`) |

**Route families mounted in the combined profile** (`router_composition.py`):

| Family | Router files |
|---|---|
| `/api/be1/v1` | `be1_runtime`, `be1_sessions`, `be1_registry`, `be1_canvas`, `be1_artifacts`, `be1_records` |
| `/api/lesson-library/v1` | `lesson_library` |
| `/api/platform-admin/v1` | `platform_admin_accounts` |
| `/api/auth/v1` | `auth_registration` |
| `/api/teacher/v1/organizations/{organization_id}/ai` | `teacher_ai` |
| `/api/parent/v1/ai` | `parent_ai`. The mobile `parentWorkflowApi.ts` calls it |
| `/v1/parent/profiles`, `/v1/story-runs` | M2 (frozen contract) |
| Legacy mobile workflow and demo | `/v1/sessions`, `/v1/profile`, `/v1/whiteboard`, `/v1` live understanding and story-run-lite, `/api/dev/v1` storage examples, health |

## 3. Proposed scope

### 3.1 Families

| Family | In CONV-1? | Why |
|---|---|---|
| `/api/be1/v1`, `/api/lesson-library/v1`, `/api/platform-admin/v1`, `/api/auth/v1`, `/api/teacher/v1/…/ai` | **Yes** | These are the four web roles' families, which FEAT-066 owns. They carry the non-conforming shapes |
| `/api/parent/v1/ai` | **Owner decision CV-1** | It is a Parent family that the mobile app calls. Option A puts it in CONV-1 (one envelope everywhere; the mobile parser already reads top-level fields). Option B leaves it for C-P |
| `/v1/parent/profiles`, `/v1/story-runs` | **No: unchanged, regression-guarded** | They already follow C-D1 and C-D2, and the M2 closure froze them |
| Legacy mobile workflow and demo families | **No** | They have their own versioned result contracts (for example `MobileWorkflowResultV1`) and are not FEAT-066 surfaces. Only the C-D2 header rule touches them (§3.2 item 3) |

### 3.2 Behaviour changes

1. **One envelope builder.** A new module, `interfaces/http/error_envelope.py`, builds the C-D1 body: `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, `field_errors`, plus `request_id` equal to `correlation_id`, and `current_version` only with `STALE_REVISION`. All six §9.8 fields are always present, with null where there is no value, as story-runs does today.
2. **Global handlers for the in-scope families.** The `StarletteHTTPException`, `RequestValidationError` and `Exception` handlers route every in-scope family through the builder. The story-runs and Parent-profiles branches stay byte-for-byte unchanged.
   - **Validation (C-D3):** 400 `INVALID_REQUEST`, with non-echoing `field_errors` (`{field, code}`). The field names are reduced the way the story-runs branch reduces them. An invalid `Idempotency-Key` header gives 400 `INVALID_IDEMPOTENCY_KEY`. As a result, a `limit` above 100 becomes 400 `INVALID_REQUEST` on every in-scope route that declares `le=100` (C-D8).
   - **Unhandled errors:** 500 `INTERNAL_SERVER_ERROR` in the envelope, logged with the request ID and exception type only.
3. **Correlation (C-D2).** Every response on every path carries `X-Request-ID`. A supplied safe ID is echoed; otherwise a UUID is generated. On in-scope families the body's `correlation_id` equals the header. Story-runs and Parent profiles keep their current header behaviour. On legacy families only the header is added; their bodies do not change.
4. **Code vocabulary (owner decision CV-2).** Option A, recommended: the handlers map the legacy BE1 and Lesson Library codes to the §9.8 codes:

   | Legacy code | §9.8 code |
   |---|---|
   | `AUTHENTICATION_REQUIRED`, `UNAUTHENTICATED` | `AUTH_REQUIRED` |
   | `INVALID_IDENTITY_TOKEN` | `INVALID_TOKEN` |
   | `FORBIDDEN` | `ACTION_NOT_ALLOWED` |
   | `NOT_FOUND` | `RESOURCE_NOT_FOUND` |
   | `CONFLICT`, `INVALID_TRANSITION` | `INVALID_STATE_TRANSITION` |
   | `REQUEST_VALIDATION_FAILED` | `INVALID_REQUEST` |
   | `REQUEST_TOO_LARGE` | `MEDIA_TOO_LARGE` |
   | `SERVICE_UNAVAILABLE`, `DEPENDENCY_UNAVAILABLE` | `PROVIDER_UNAVAILABLE` |

   Codes that §9.8 does not list but that name a real domain condition keep their name, because §9.8 says "Mã lỗi/ví dụ". Examples are `DEVICE_AUTHENTICATION_REQUIRED` and `ACCOUNT_SETUP_UNAVAILABLE`. Option B: keep every legacy code and change only the envelope fields. **Both options break the web callers that compare codes**; see §6.
5. **Messages (owner decision CV-3).** §9.8 requires a safe, Vietnamese `message`. Option A, recommended: the handlers take the message from one code-to-Vietnamese table and ignore route-supplied message text. This also stops a route string from leaking scope detail. Option B: keep route-supplied messages, which today are English.
6. **404 versus 403 (C-D4)** in `require_assignment`:
   - Missing, inactive, wrong-role or unassigned accounts, which are out of scope, get 404 `RESOURCE_NOT_FOUND`.
   - A policy refusal for an assigned account, which is in scope but where the action is not allowed, gets 403 `ACTION_NOT_ALLOWED`.
   - Route-specific checks stay with their own slices.
7. **Missing `If-Match` on Lesson Library (owner decision CV-4).** §9.8 has no 428 code. Option A, recommended: 400 `INVALID_REQUEST` with `field_errors: [{field: "If-Match", code: "REQUIRED"}]`, the same shape as a missing `Idempotency-Key` (C-D5). Option B: keep 428 with code `PRECONDITION_REQUIRED`.
8. **Shared helpers, adopted by no route except as listed:** a new module, `interfaces/http/api_conventions.py`, containing:
   - `parse_idempotency_key(request)`: the C-D5 rule. It returns the key, or raises 400 with field code `REQUIRED` or `INVALID_FORMAT`.
   - `PAGE_LIMIT_DEFAULT = 25`, `PAGE_LIMIT_MAX = 100`, and a `limit_query()` dependency factory.
   - `raise_stale_revision(current_version=…, etag=…)`: 409 `STALE_REVISION` with `current_version`, or with the current ETag in a header.

   Each capability slice adopts them for its own routes (contract §3). The Parent routes keep their own copy, because they are frozen.

### 3.3 Explicitly out of scope

- No route is moved, renamed or given a new prefix (C-D9).
- No route gains a new `Idempotency-Key` requirement. The missing-key rule applies only where a route already takes a key; other routes adopt it in their slices.
- No offset-to-cursor change on accounts (Platform Admin slice).
- No pagination is added to unpaginated BE1 lists (C-M slice).
- No change to the BE1 canvas `limit` (500), which is a domain bound outside the list rule. It is recorded for the C-T or C-M slice.
- No FE, mobile or Bruno file. The follow-ups are listed in §6.
- No migration, dependency, `uv.lock` or `pyproject.toml` change.
- No change to the story-runs, Parent-profiles or legacy-family bodies.

## 4. Proposed exact allowlist

**Source:**
1. `backend/src/sketch2life/interfaces/http/app.py`: the middleware and the three handlers.
2. `backend/src/sketch2life/interfaces/http/error_envelope.py` (new).
3. `backend/src/sketch2life/interfaces/http/api_conventions.py` (new).
4. `backend/src/sketch2life/interfaces/http/routers/be1_common.py`: `require_assignment` and the shared `responses` declarations.
5. `backend/src/sketch2life/contracts/schemas/be1_runtime.py`: only `Be1Error`, which becomes the envelope model or an alias of it.
6. `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`: only the missing-`If-Match` branch (lines 84–94), and only if CV-4 = A.
7. `backend/src/sketch2life/interfaces/http/openapi_contract.py`: the error response schemas of the in-scope operations. Every 422 becomes 400 for those operations, and the 428s become 400 if CV-4 = A.

**Tests, new:**

8. `backend/tests/unit/test_http_error_envelope.py`
9. `backend/tests/unit/test_http_api_conventions.py`
10. `backend/tests/contract/test_http_error_conventions.py`: one in-memory route per in-scope family, checking the envelope, the header-equals-body rule, 400 validation, `limit` above 100 and the unhandled 500.

**Tests, existing — edits limited to status, code, envelope and message assertions:**

11. `backend/tests/contract/test_openapi_contract_catalog.py`
12. `backend/tests/contract/test_app_composition.py`
13. `backend/tests/contract/test_auth_registration_api.py`
14. `backend/tests/contract/test_m2_s1a_teacher_routes.py`
15. `backend/tests/contract/test_activity_execution_http.py`
16. `backend/tests/contract/test_assistance_requests_api.py`
17. `backend/tests/contract/test_live_image_demo_api.py`
18. `backend/tests/integration/lesson_library/test_lesson_library_api.py`
19. `backend/tests/integration/test_be1_postgres_api.py`
20. `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
21. `backend/tests/integration/test_m2_s1a_teacher_postgres.py`
22. `backend/tests/unit/test_pilot_queue_composition_b1.py`
23. `backend/tests/unit/test_synthetic_status_guard.py`

Files 13–23 come from a static grep: test files that reach an in-scope family and assert 422, 403, a legacy code, `detail` or `PRECONDITION_REQUIRED`. Some may need no edit. Two rules apply:
- A file outside this list that turns out to need an edit stops the task. It needs an owner scope amendment.
- These four tests also matched the grep, but they must pass **unchanged**, as regression guards for the frozen families: `test_parent_profiles_routes.py`, `test_parent_story_run_request_contract.py`, `test_m2_s1a_parent_postgres.py` and `test_m2_s2_g1_parent_story_postgres.py`.

## 5. Acceptance criteria

1. Every in-scope family returns the C-D1 envelope on HTTP errors, validation errors and unhandled errors, with all six §9.8 fields. The `X-Request-ID` header equals `correlation_id`.
2. Validation errors on in-scope families return 400 `INVALID_REQUEST` with non-echoing `field_errors`. A `limit` above 100 returns 400. No in-scope family returns 422 except for a §9.8 semantic code.
3. Out-of-scope organization access through `require_assignment` returns 404 `RESOURCE_NOT_FOUND`, with the same body shape as a non-existent ID. An in-scope policy refusal returns 403 `ACTION_NOT_ALLOWED`.
4. The code mapping (CV-2) and the messages (CV-3) behave as decided. No message contains a route string, a stack trace, a path or an echoed input.
5. Every response on every path carries `X-Request-ID`.
6. The story-runs and Parent-profiles responses are unchanged. The four regression-guard tests pass unmodified.
7. The helpers have unit tests. The OpenAPI catalog shows the envelope schema and the 400s for the in-scope operations.
8. The FE, mobile and Bruno follow-ups in §6 are recorded in `STATUS.md`.

## 6. FE, mobile and Bruno follow-ups (not in CONV-1)

**Callers that read errors today:**

| Client | File |
|---|---|
| Web | `apps/web/src/shared/backendApi.tsx` |
| Web | `apps/web/src/modules/school-manager/be1/services/be1Client.ts` |
| Web | `apps/web/src/modules/platform-admin/pages/AdminScreens.tsx` |
| Web | `apps/web/src/modules/teacher/services/aiWorkflowService.ts` |
| Web | `apps/web/src/modules/teacher/pages/TeacherAiLessonWorkflowPage.tsx` |
| Mobile | `apps/mobile/src/infrastructure/api/parentWorkflowApi.ts`, which reaches `/api/parent/v1/ai`; only affected if CV-1 = A |

**Release order risk:** a web build that compares legacy codes, reads `detail`, or expects 422 or 403 will misreport errors once CONV-1 is deployed. That is why:
- the FEBASE item and the per-role FE slices take CONV-1's envelope as their base;
- until then, the `request_id` alias is the only field that is unchanged.

**Bruno:** assertions on status or code for in-scope families are updated in BRU-0.

## 7. Verification plan and command ceiling

- **Coordinator, without DB or network** (may run only after the Task Approval):
  - `ruff check` and `mypy` on the allowlisted source files;
  - the new unit tests;
  - the repository validators;
  - `git diff --check`.
- **Owner-run in their own terminal, because they need TestClient or the DB.** The Codex sandbox hangs on loopback sockets. Each command is run once against the disposable `be1_acceptance` database, with ClamAV absent as before:
  - the new contract test;
  - the catalog and app-composition tests;
  - the edited contract and integration files 13–23;
  - the four regression guards.
- **Evidence:** one note with the command set, exit codes, pass counts and log hashes. Then an independent evidence review on Sonnet 5.5 at high effort. Then one task commit on the owner's word.

## 8. Owner decisions needed

| ID | Question | Recommendation |
|---|---|---|
| CV-B | Implement on a new branch `feature/feat066-conv1` from `08439b22`? | Yes |
| CV-1 | Is `/api/parent/v1/ai` in CONV-1 (A) or left for C-P (B)? | A |
| CV-2 | Map legacy codes to §9.8 codes (A), or keep the codes and change only the fields (B)? | A |
| CV-3 | Vietnamese messages from one handler table (A), or route-supplied messages (B)? | A |
| CV-4 | Missing `If-Match`: 400 `INVALID_REQUEST` with a field error (A), or keep 428 (B)? | A |

## 9. Proposed Task Approval entry (draft text, not written)

> FEAT-066 CONV-1 — API conventions core. Status: APPROVED_FOR_IMPLEMENTATION once the owner approves this package at its reviewed pin. Branch `feature/feat066-conv1` from `08439b22`. The approved exact allowlist is files 1–23 of §4, with edits to tests 11–23 limited to status, code, envelope and message assertions. The approved behaviour is §3.2 items 1–8 with the CV-1 to CV-4 answers. Exclusions are §3.3. The verification boundary is §7: coordinator commands as listed, and owner-run TestClient and DB commands. Git: no stage, commit or push without a separate owner word.

## 10. Not verified

- The exact list of in-scope operations in `openapi_contract.py`, and the size of their error-schema edits.
- Whether each of test files 13–23 needs an edit.
- Whether any in-scope route returns 422 for a §9.8 semantic code that must keep 422.
- How `teacher_ai` and `parent_ai` shape their nested `detail` today. The handler reads `detail.code` when it exists; this was not read route by route.
- Whether a deployment proxy rewrites headers.
- The CRLF and whitespace state of the allowlisted files (the `.gitattributes` rules from Phase A apply).

No test, runtime, OpenAPI generation or validator was run for this draft.
