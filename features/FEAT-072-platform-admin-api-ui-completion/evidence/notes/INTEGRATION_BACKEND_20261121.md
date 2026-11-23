# FEAT-072 backend integration note (2026-11-21)

Source: commit `a77bb2a8` ("feat(admin): complete admin workflows and polish UI", author HieuNewBie) on `origin/codex/fe-ui-web-remediation`.
Target: `feature/backend-srs-api-and-fe-integration` at `8eda5e4e` (goal v3 Phase A squash), staged on `feature/int-admin-be`.

## Scope taken

- `backend/**`: src, alembic versions and `env.py`, tests, `tools/run_admin_acceptance.py`.
- `features/FEAT-072-platform-admin-api-ui-completion/**`.
- `compose.yaml` (email worker profile, sandbox, SMTP and Redis variables) and `.env.example` (placeholders only, no secrets).
- Not taken: `apps/web/**` (the Admin UI is being redesigned on the FE branch). Web files that both sides changed (`backendApi.tsx`, `WebAppShell.tsx`, Platform Admin modules) are not part of this commit and must be re-checked when the FE branch is rebased.
- Trailing blank lines at the end of the four teammate feature documents were removed so `git diff --check` passes.
- Added by the integrator because the harness validator requires them: `DECISIONS.md`, `evidence/README.md`, and `.gitkeep` in `evidence/raw`, `evidence/screenshots`, `evidence/metrics`.

## Conflicts and how each was resolved

Text conflicts (3 files) and semantic overlaps (5 files that merged cleanly) were all reviewed.

| File | Resolution |
|---|---|
| `routers/auth_registration.py` | Union of imports. Goal v3 `GrantedScope`/`load_granted_scope` (T0.2 `/me` scope object) kept; the teammate's email-verification activation in `/me` kept and runs before the scope load. |
| `routers/platform_admin_accounts.py` | Base = goal v3 C5 version (opaque keyset cursor with `next_cursor`, `Idempotency-Key` through `parse_idempotency_key`, receipts in `be1_command_receipts`, last-Platform-Admin row lock, no `If-Match` on PATCH per C5 CA-4). Teammate additions layered on top: `pending_verification` state, password-setup email outbox row on create, `pending_activation` on School Manager assignments (set on create, cleared on `/me` verification, revoked with the assignment), `content_admin` grant revocation when the account stops being an active Platform Admin, `SELF_DISABLE_DENIED`, `AdminRoute` (no-store, ETag). Dropped (superseded by C5): the teammate's own cursor module use here, `AdminCommandReceiptModel` receipts, `If-Match` 428, the advisory lock. |
| `tests/contract/test_openapi_contract_catalog.py` | Operation counts are now `174 + len(ADMIN_OPERATIONS - PR22_UNCATALOGUED_OPERATIONS)` (174 is the goal v3 Phase A count; the teammate's `151 + ...` was based on the older count). |
| `infrastructure/config/settings.py` | Both sides' fields kept (`redis_url`; SMTP, `billing_sandbox_enabled`). |
| `infrastructure/lesson_library/tables.py`, `persistence/be1_models.py` | Merged cleanly; goal v3 lesson tables untouched apart from the teammate's `PLATFORM` owner kind and nullable `organization_id`. |
| `interfaces/http/openapi_srs_v22.py`, `router_composition.py`, `tests/contract/test_app_composition.py` | Merged cleanly; both sides' routers and route lists are present. |

## Idempotency-Key and error envelope on the admin routes

- `/api/platform-admin/v1` and `/api/auth/v1` were already inside the shared CONV-1 error envelope.
- The admin routers now read the key with `parse_idempotency_key` (same rule as FEAT-066: required, 1-128 printable characters, `400 INVALID_REQUEST` with an `Idempotency-Key` field error). The header stays declared in OpenAPI.
- Reusing a key with another payload now returns `400 INVALID_IDEMPOTENCY_KEY` (was `409 IDEMPOTENCY_CONFLICT`) in the admin command service and the sandbox billing service.
- Other admin routes keep their own `If-Match` (428/422/409 `STALE_REVISION`) behavior.

## Migrations

- The seven admin revisions (`20261119_admin_foundation` to `20261120_admin_ops_retention`) are unchanged and not re-parented; they branch from `20261110_ar_0001`. `alembic heads` goes from 14 to 15 (the only new head is `20261120_admin_ops_retention`). No test pins the head count.
- `upgrade heads` on a fresh database on the loopback container succeeded; a second `upgrade heads` is a no-op.
- Downgrade/upgrade round trip is **not possible**: all seven admin revisions raise in `downgrade()` by design (retention-aware, forward-only). Nothing was changed there.
- Billing and capacity tables (`billing.*`) are owned by the admin chain. Goal v3 Phase A defines no billing table; the later goal v3 Billing adapter (T-1a) must reuse these tables and keep only its port and adapter.

## Source and test adjustments made at integration

- `error_envelope.py`: `SELF_DISABLE_DENIED` and `EMAIL_VERIFICATION_REQUIRED` added to the status-message-only codes (the envelope classification test requires every code literal to be classified).
- `infrastructure/platform_admin/operations.py`: `redis_url` is read with `getattr`, so a settings stand-in without it no longer raises (the teammate's own acceptance test failed on this).
- `tests/integration/lesson_library/test_lesson_library_api.py`: the Platform Admin fixture now holds the `content_admin` grant, because the teammate's change makes lesson moderation require it (`_platform_admin` in `routers/lesson_library.py`).
- `tests/integration/test_platform_admin_workflows.py`: the concurrent cross-demotion test disables the admins left by earlier tests of the same disposable database and accepts 409 `LAST_PLATFORM_ADMIN` (goal v3 lock order) as well as 403 for the losing request.
- Revision-graph tests updated for the 7 new revisions: `test_synthetic_eligibility` (42 revisions, 15 down-only heads, 10 dependency heads), `test_lesson_occurrence_ddl` (the admin chain is an independent branch from `20261110_ar_0001`), `test_learning_content_persistence_shape` (the frozen DDL predates `review.permission_revision`, added by `20261119_admin_publication`).
- `test_http_error_conventions`: Admin operations (lesson feedback) are not held to the catalogued-family 422 rule.
- `test_platform_admin_account_api` (unit, SQLite): C5 contract status codes (400 for a missing key, a reused key and a bad cursor; no `If-Match`), `be1_command_receipts` and `ClassroomModel` tables in the fixture, JSONB compiled as JSON on SQLite, and the keyset second-page check left to the PostgreSQL suite (SQLite timestamps are naive).

## Gate results

- Backend unit and contract: 9174 passed, 65 failed, 26 skipped, 18 collection errors; failing-id diff against `tmp/be-integration/fail_ids.txt`: 0 new, 0 fixed (baseline unchanged).
- PostgreSQL on the loopback container: Platform Admin accounts, Lesson Library and BE1 suites 22 passed and the 3 known expected failures only; `run_admin_acceptance.py` 13 passed; learning content, FR-C-08 lifecycle and migration-graph suites without failures.
- Harness, repository security, architecture and skeleton validators and `git diff --check`: see the commit message.

## Open points for the owner

- Goal v3 Phase B+ must be re-checked against `platform_admin_accounts.py` and the admin `Key` dependency before squashing.
- Teammate's account tests assumed `If-Match` and 422/409 key errors; they were adjusted to the C5 contract (see the commit body).
