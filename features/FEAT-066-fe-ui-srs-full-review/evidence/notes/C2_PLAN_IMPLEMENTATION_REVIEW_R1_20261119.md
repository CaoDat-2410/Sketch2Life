# C2 web error envelope: independent review R1 (plan + implementation)

Reviewer: Sonnet 5.5, high effort. Read-only review; the only file written is this report.
Target: `.worktrees/ui`, branch `codex/fe-ui-web-remediation`, HEAD 81e99210 (C1) plus the uncommitted C2 diff.
Plan: `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_C2_WEB_ERROR_ENVELOPE_DRAFT1_20261119.md`.
Authority: SRS 9.8; backend `error_envelope.py` and the handlers in `app.py`.

## Verdicts

- Plan: READY WITH NOTES (P1 0, P2 1, P3 2).
- Implementation: ACCEPTABLE WITH NOTES (P1 0, P2 1, P3 5). The P2 is the same scope gap as the plan's P2.

## Command results (cwd `.worktrees/ui/apps/web`, no install, no git write)

| Command | Result |
|---|---|
| `npm run test` | 8 files / 39 tests passed (C1 baseline 5 / 25; +3 files, +14 tests = 6 errorEnvelope + 2 backendApi + 3x2 be1Client via describe.each) |
| `npm run lint` | exit 0, 28 warnings (equals the baseline, none new) |
| `npm run build` | exit 0 (`dist` is git-ignored) |

Byte checks on the 6 changed or new files: 0 CR, no BOM, no absolute paths, no secrets. No new English user-visible string.

I also ran `parseApiError` on odd inputs through `node --experimental-strip-types`, writing no files. Results are in item (1).

## (1) parseApiError: shape separation and hostile bodies

Behaviour is correct and conservative.

- CONV-1 requires top-level string `code`, `message` and `correlation_id` (errorEnvelope.ts:89-92). A detail-wrapped body, a top-level `{code, message}` without `correlation_id`, an array, a string, `null` and a nested `detail.detail` all give `conv1=false`. They get a Vietnamese message by code, then by status, and the server text is never shown.
- No exception was thrown for any input tried: arrays, a `detail` array (FastAPI 422 style), `detail` as a string or `null`, numeric `code`, `__proto__` keys, and a 5000-character code.
- The code gate `^[A-Z][A-Z0-9_]{0,63}$` (line 22) rejects a huge or malformed code, which becomes `HTTP_<status>`. It also makes lookups in the plain-object tables safe from prototype keys, because `constructor`, `__proto__` and `toString` can never pass the gate.
- Trusting `message` for the CONV-1 shape is safe for every route family the web calls. All web calls go to `/api/be1`, `/api/lesson-library`, `/api/platform-admin`, `/api/auth` and `/api/teacher` (backendApi.tsx, be1Client.ts). The backend builds those messages from its own Vietnamese table and never copies route text (`error_envelope.py` docstring and `build_error_body`).

Residual risks, both P3 (see Implementation P3-1 and P3-2): the detection is shape-only, and a blank or oversized CONV-1 message is not guarded.

## (2) Callers of AdminBe1Error, BackendApiError and backendMessage

I grepped all uses. None is broken.

- `AdminBe1Error` is used by `ParentGroupsPage.tsx:95-98` (status only) and `managerBusinessPages.test.tsx:153` (3-argument constructor). The new constructor arguments 4 and 5 have defaults, so both still work.
- No production code depends on the removed `'HTTP_ERROR'` code or on the text "BE1/API request failed". Grep over `src` finds none.
- `BackendApiError` and `backendMessage` still work as before.
  - `backendMessage` (backendApi.tsx:590-601) keys on `status`, `CONSENT_NOT_EFFECTIVE`, `STALE_SESSION_REVISION` and `RESOURCE_CONFLICT`.
  - The 401/403 fallback texts in `STATUS_MESSAGES` are byte-identical to the removed inline ones (errorEnvelope.ts:43-44).
  - `UsersPage.tsx:20` still gets `status 401` and the client-made `AUTHENTICATION_REQUIRED`.
- Request ids: `detail.request_id`, then `correlation_id`, then the `X-Request-ID` header (errorEnvelope.ts:96-101). This keeps the old behaviour and adds the CONV-1 id.
- Unconverted readers (this is the Plan P2 and Implementation P2 below):
  - `modules/teacher/services/aiWorkflowService.ts:74-79` reads `payload.detail.code` only.
  - `modules/school-manager/be1/services/authService.ts:50-53` reads top-level `message` only. This one is harmless: with a detail body it falls back to its own Vietnamese text.

## (3) Fallback table against the backend MESSAGES table

All 13 codes in `CODE_MESSAGES` are byte-identical to `error_envelope.py` `MESSAGES`: AUTH_REQUIRED, INVALID_TOKEN, TOKEN_EXPIRED, ACTION_NOT_ALLOWED, RESOURCE_NOT_FOUND, INVALID_STATE_TRANSITION, INVALID_REQUEST, INVALID_IDEMPOTENCY_KEY, STALE_REVISION, PROVIDER_UNAVAILABLE, RATE_LIMITED, MEDIA_TOO_LARGE and UNSUPPORTED_MEDIA_TYPE. The common codes you named (404/RESOURCE_NOT_FOUND, STALE_REVISION, INVALID_STATE_TRANSITION) are covered.

Differences (all minor, no user-visible English):

- `STATUS_MESSAGES` 401 and 403 are the legacy web texts: "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại." and "Tài khoản chưa được cấp quyền cho dữ liệu này.". The backend uses "Vui lòng đăng nhập để tiếp tục." and the ACTION_NOT_ALLOWED text. This is deliberate backward compatibility, but the plan says "copied from the backend table", which is not exact. These texts apply only when the body gives no known code.
- 405 is missing. The backend answers 405 with the ACTION_NOT_ALLOWED text. The web gives the generic 4xx text.
- PROVIDER_BAD_RESPONSE and INTERNAL_SERVER_ERROR are not code keys. They end up with the same text through the 502 entry and the `>= 500` branch, except that a body with code PROVIDER_BAD_RESPONSE on a status other than 502 would not match. This is not reachable from the backend table.
- ACTIVE_RUN_EXISTS: not in the table. It has no web caller. A top-level story-run body already carries its own Vietnamese message, and a detail body gets the 409 text.
- SRS 9.8 domain codes (CLASS_CAPACITY_REACHED, VIDEO_QUOTA_EXCEEDED and so on) have no code entry. Status fallback is acceptable, and the backend also answers them with the status message.

## (4) Test quality

Tests assert real behaviour and would fail on regression. Reverting `be1Client.ts` to the old readers would fail the English-detail and empty-503 cases (old text "BE1 request failed (503)."). Reverting `backendApi.tsx` would fail the English-detail case. Global state is cleaned: `vi.stubGlobal`, `vi.stubEnv`, `window.sketch2lifeConfig` and `sketch2lifeAuth` are restored in `afterEach`, and `restoreMocks: true` is set in the Vite config. The tests have no order dependency.

Gaps are listed as Implementation P3-3 and P3-4.

## Findings

### Plan

- **P2-1 (scope claim wrong).** The plan says three readers "serve all the callers (... Teacher pages)". There are more fetch sites that read errors. `aiWorkflowService.ts:63-79` (Teacher AI lesson workflow, route `/api/teacher/v1/organizations/{id}/ai`, which is in CONV-1 `CONV1_PREFIXES`) reads `payload.detail.code` only. With the CONV-1 top-level body, every error becomes `Yêu cầu AI thất bại (HTTP_400).` and the real code (for example `RATE_LIMITED`, `ACTION_NOT_ALLOWED`) and the Vietnamese message are lost. The plan should either include this reader in C2 (use `parseApiError`, keep the "(code)" suffix or show the message) or explicitly defer it with a named task. The text is still Vietnamese, so the impact is information loss, not English leakage.
- **P3-1.** The Change section says the table "mirrors `error_envelope.py`". It does not, for 401, 403 and 405 (item 3). State that 401/403 intentionally keep the legacy texts.
- **P3-2.** The Checks section pins the C1 baseline (5 files / 25 tests). The current state is 8 / 39. Update the number when the plan is recorded. The plan also says nothing about the trust rule's limit (Implementation P3-1).

### Implementation

- **P2-1.** `aiWorkflowService.ts:74-79` is the unconverted reader described in Plan P2-1. No C2 test covers it, and it contradicts the C2 goal of showing a Vietnamese message plus code against both bodies for Teacher AI calls.
- **P3-1 (shape-only trust).** `conv1` is decided by the body shape only (errorEnvelope.ts:89-92), not by route family. `/v1/parent/profiles` also emits top-level `code/message/correlation_id` with English messages (`app.py` parent-profile branch, `parent_error_payload`, and the English 500 in the unexpected-exception handler). The web does not call that family today, so there is no live leak. Add a comment that the helper must not be pointed at `/v1/parent/*` or gate the message by route family. This matters for C3 if the helper is ever shared.
- **P3-2 (blank or oversized message, non-finite retry).** For CONV-1, `message` is used as-is (line 105). An empty string, whitespace, or a very long string would render as blank or huge text. My run showed `message:""` giving an empty UI string. Fall back to `fallbackMessage` when `message.trim()` is empty, and optionally cap `message` and `requestId` length. `retry_after_seconds` accepts `Infinity` (`typeof number && >= 0`, line 108); use `Number.isFinite`. The backend never sends any of these, so this is a hardening note.
- **P3-3 (missing test for the key trust gate).** No test shows that a top-level `{code, message}` without `correlation_id`, with an English message, is not trusted. This is the core separation rule (lines 89-92); a regression that drops the `correlation_id` check would pass every current test. Also missing: CONV-1 `field_errors: null`, a request id taken from the `X-Request-ID` header through the be1Client and backendApi paths (only `parseApiError` is tested for it), and an invalid `retry_after_seconds`.
- **P3-4 (weak fallback assertion).** `errorEnvelope.test.ts` "has a Vietnamese fallback for every status family" uses a loose regex (`...|Không|Yêu|Máy`) over 14 statuses. It would catch English, but it does not pin the exact texts, and it skips 405, 418 and 501. Assert exact strings for at least 401, 403, 405 and 500.
- **P3-5 (API ergonomics).** `AdminBe1Error(message, status, code, requestId?, retryable = false)` takes two more positional arguments. This works with the existing 3-argument callers, but an options object would be safer for later additions. Not blocking.

## Summary (5 lines)

1. Plan READY WITH NOTES (0 P1 / 1 P2 / 2 P3); implementation ACCEPTABLE WITH NOTES (0 P1 / 1 P2 / 5 P3).
2. `parseApiError` separates CONV-1, detail-wrapped and odd bodies correctly. It never threw and never shows English for non-CONV-1 bodies. All 13 table messages match the backend byte for byte.
3. The one real gap: `aiWorkflowService.ts` (Teacher AI) still reads `detail.code` only, so CONV-1 errors there lose their code and message. The plan's "three readers" claim is wrong. No caller of AdminBe1Error, BackendApiError or backendMessage was broken.
4. Tests are real and non-vacuous with clean global state. They lack the `correlation_id` trust-gate case and the header-request-id case; the status-fallback assertion is loose.
5. Numbers: test 8 files / 39 tests passed, lint exit 0 with 28 warnings, build exit 0. The six changed or new files have no CR, BOM, absolute path or secret.
