# FEAT-066 C2 (C-W2) web error envelope: plan, Draft 1

Status: DRAFT written by the goal under the program approval; reviewed together with its implementation (one independent review of plan and diff).

## Scope

SRS section 9.8 (line 847): every API error carries `code`, a safe Vietnamese `message`, `correlation_id`, `retryable`, optional `retry_after_seconds` and `field_errors`. The CONV-1 backend sends this envelope at the top level of the body for `/api/be1/v1`, `/api/lesson-library/v1`, `/api/platform-admin/v1`, `/api/auth/v1` and `/api/teacher/v1/` (`error_envelope.py`). `origin/dev` still sends `{"detail": {"code", "message"}}` with English messages. The web app must show Vietnamese text against both.

The web has four error readers: `adminApiRequest` and `adminBe1Request` in `be1Client.ts`, `errorFromResponse` in `backendApi.tsx`, and the Teacher AI reader `post` in `modules/teacher/services/aiWorkflowService.ts` (found by the review of this plan; it read `detail.code` only). Before this task the two `be1Client` readers read `code` and `message` from the top level only (an English `detail` body gave "API request failed (400).") and `errorFromResponse` showed any server message as is.

## Change

- New `apps/web/src/shared/api/errorEnvelope.ts`: `parseApiError(body, status, headerRequestId)` returns code, message, request id, retryable, retry-after and field errors. The server message is used only for a CONV-1 envelope (top-level `code`, `message` and `correlation_id`); any other body gets a Vietnamese message chosen by code, then by status (the table mirrors `error_envelope.py`).
- `be1Client.ts`: both readers use it; `AdminBe1Error` gains optional `requestId` and `retryable` (constructor arguments 4 and 5, defaults keep existing callers).
- `backendApi.tsx`: `errorFromResponse` uses it; `BackendApiError` is unchanged.
- `aiWorkflowService.ts`: the error text becomes `Yêu cầu AI thất bại (<code>). <Vietnamese message>`.
- Hardening after the review: a CONV-1 body is trusted only when `code`, a non-blank `message` of at most 500 characters and `correlation_id` are present; `retry_after_seconds` must be finite.
- No new route, header or UI string outside the fallback table; no change to retry or key logic (C1 pins that).

## Tests

`shared/api/__tests__/errorEnvelope.test.ts` (shapes, fallbacks, malformed code), `modules/school-manager/be1/__tests__/be1Client.test.ts` (both readers: CONV-1 body, English detail body, empty 503 body), `shared/api/__tests__/backendApi.errors.test.ts` (CONV-1 body and English detail body through `backendRequest`), `modules/teacher/services/__tests__/aiWorkflowService.test.ts` (both body shapes), and the trust-gate cases in `errorEnvelope.test.ts`.

## Checks

`npm run test`, `npm run build`, `npm run lint` in `apps/web` against the C1 state (5 files, 25 tests; 28 lint warnings); repository validators; manual UI-copy check (the only new user-visible strings are the fallback table, in Vietnamese, copied from the backend table).

## Not in this task

Surfacing `retryable`, `retry_after_seconds` and `field_errors` in screens (the SRS gives no screen rule for them; the values are parsed and carried only). The Parent mobile app has its own client (task C3).
