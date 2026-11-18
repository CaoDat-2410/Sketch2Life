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

These requests require Platform Admin authorization. They do not include an
`Idempotency-Key` or `If-Match`, matching the current FE adapter and BE contract.

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

Manager endpoints that remain blocked by missing contract/policy are not listed
as FE-integrated here.

## Service health

- `090` is the existing unauthenticated health request; it is not tied to an FE
  role.
