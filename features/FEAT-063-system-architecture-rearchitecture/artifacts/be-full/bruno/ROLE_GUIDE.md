# Bruno requests grouped by FE role

This guide labels the requests that the current Admin and Manager FE flows call
or have an API adapter for. It does not assert that an endpoint was verified at
runtime.

## Shared authenticated account

- `141-current-account-role.bru` — `GET /api/auth/v1/me`; requires a bearer token
  and returns the current caller's role/state.

## Platform Admin

- `142-list-accounts.bru` — read-only account list.
- `143-create-account.bru` — state-changing; use only disposable synthetic local
  accounts. The sample email uses the reserved `.test` domain.
- `144-update-account.bru` — state-changing; set the ID and body only for a
  disposable synthetic test account.

These requests require Platform Admin authorization. `142` pages with an opaque `cursor`
(default and example `limit=25`; `next_cursor` continues). `143` and `144` send an
`Idempotency-Key` (FEAT-066 C5); neither sends `If-Match`, because the SRS names no
expected-revision rule for the account role or state.

## Manager

The Manager FE-connected or adapter-backed requests are already in Bruno; their
request names are now prefixed with `[MANAGER]`:

| Seq | Method and path | FE status |
| --- | --- | --- |
| `021` | `GET /api/be1/v1/organizations/{organization_id}/me` | Called to verify the Manager assignment. |
| `003` | `GET /api/be1/v1/organizations/{organization_id}` | Called by the organization overview. |
| `006` | `GET /api/be1/v1/organizations/{organization_id}/classes` | Called by Manager class/roster views. |
| `007` | `POST /api/be1/v1/organizations/{organization_id}/classes` | Adapter exists, but the UI action is disabled pending the capacity contract. |
| `008` | `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | Called by the roster/consent view. |
| `012` | `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Called by the roster/consent view. |
| `068` | `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants?state=PENDING_REVIEW&audience_kind=PUBLIC` | Called for the public-review queue. |
| `073` | `GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Called to review the selected lesson. |
| `069` | `POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` | Called for an explicit review decision; state-changing. |
| `081` | `GET /api/lesson-library/v1/organizations/{organization_id}/parent-groups?limit=50` | Called for the first parent-group page; add `cursor` from `next_cursor` for later pages. |
| `082` | `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Called by the create-group form; state-changing. |

All FE-backed requests send bearer auth, `Accept`, and `X-Request-ID`; writes
also send `Content-Type`. The access-grant decision and parent-group creation
send `Idempotency-Key`; the decision also sends the selected grant revision in
`If-Match`. State-changing requests are for local synthetic data only.

Added for the first-Teacher assignment (FEAT-066 M9-B); not yet called by the FE:

- `145-list-teacher-candidates-...bru` — `GET /api/be1/v1/organizations/{organization_id}/teacher-candidates?limit=25`;
  read-only; `next_cursor` continues.
- `146-assign-class-teacher-...bru` — `POST /api/be1/v1/classes/{class_id}/assignments`; state-changing; sends
  `If-Match` (class assignment revision) and `Idempotency-Key`; body `{candidate_ref}`. Replaces the stale `004`
  and `005`.

Manager endpoints that remain blocked by missing contract/policy are not listed
as FE-integrated here.

## Parent mobile lifecycle

- `137`–`140` are Parent profile and StoryRun reads; they require a verified Parent bearer.
- `147`–`152` are Parent profile and StoryRun state-changing requests, labelled local-test-only. Profile PATCH carries `expected_revision` in the body. Context and script confirmations carry the expected revision/hash in the body. These requests use `Idempotency-Key`; they do not use `If-Match`.
- Use only disposable synthetic Parent data. Delete requests may be run only against the disposable local database/API.

## Portal authentication

- `153` is the unauthenticated Parent registration route. It can create an identity-provider account and is never run against a configured environment.

## Parent and Teacher AI

- `154`–`156` are Parent AI routes; `157`–`159` are Teacher AI routes. They are local-test-only examples and were not sent to the API.
- Requests `153`–`159` must never be run against a configured environment: registration may create an identity-provider account, and AI calls may reach a model provider.

## Service health

- `090` is the existing unauthenticated health request; it is not tied to an FE
  role.
