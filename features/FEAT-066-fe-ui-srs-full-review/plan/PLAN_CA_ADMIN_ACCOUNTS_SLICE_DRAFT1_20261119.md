# FEAT-066 C-A — Platform Admin accounts slice (Draft 1, goal v2 C5)

- **Status:** DRAFT for independent review. Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, 13,611 B, SHA-256 `5DFC1EDE…4795F8`, row C5). No code before the
  review verdict is READY (WITH NOTES).
- **Date:** 2026-11-19. **Base:** BE `feature/feat066-be-integration` (after the C4 BE commit); web
  `codex/fe-ui-web-remediation` (after the C4 web commit).
- **Register rows (Draft 4, `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md`):** A03, A04,
  A05, B09; gaps G07, G08. Open questions O-ACCREV (A05) and O-CONTENTADMIN (B09, G07, G08).

## 1. Source facts (BE `63363081`, web `7e416725`)

1. `interfaces/http/routers/platform_admin_accounts.py` (489 lines): `GET /api/platform-admin/v1/accounts` pages by
   `limit` (default 50, max 100) and `offset`; order `created_at` desc, `account_id` asc; response
   `{items, total, limit, offset}`. With `search`, all filtered rows are read, profiles are loaded from the identity
   provider in chunks of 100, matched in memory, then sliced by offset.
2. `POST /accounts` and `PATCH /accounts/{account_id}` take no `Idempotency-Key` and no `If-Match`. POST calls the
   identity provider (`provisioner.create_account`) before the database commit and deletes the provider account when
   the commit fails. PATCH may call `provisioner.set_account_disabled` before the commit and reverts it on failure.
   `AccountResponse` carries `revision` (`be1_adult_identities.role_revision`).
3. No table can hold a Platform Admin command receipt: `core_idempotency_receipts` is bound to canvas operations
   (foreign key), `lesson.command_receipts` and the Parent `command_receipts` belong to other modules. The newest
   migration on the account-role line, `20261110_ar_0001` (adds `account_id`, `account_role`, `role_revision`), is a
   head; nothing depends on it.
4. No functional test exercises these three routes; only route-mounting and envelope-prefix checks exist
   (`tests/contract/test_app_composition.py`, `tests/unit/test_http_error_envelope.py`). The `/api/platform-admin/v1`
   family already uses the CONV-1 envelope (`error_envelope.CONV1_PREFIXES`).
5. Web: `shared/api/backendApi.tsx` `listPlatformAccounts` sends `limit` and `offset`; `createPlatformAccount` and
   `updatePlatformAccount` send no key. `modules/platform-admin/pages/UsersPage.tsx` uses `PAGE_SIZE = 25`, offset
   paging, "Trang X / Y" from `total`, and previous/next buttons.
6. Bruno files 142 (`?limit=50&offset=0`), 143 and 144 exist for these routes.
7. Lesson moderation (B09) is mounted at `PATCH /api/lesson-library/v1/platform/lessons/{lesson_id}/moderation`,
   already keyed and preconditioned, checked by role only.

## 2. SRS answers

| ID | Point | Answer | SRS basis |
|---|---|---|---|
| CA-1 | Account list paging (A03) | Cursor pagination with an opaque, stable cursor; default 25, max 100; explicit deterministic order (`created_at` desc, `account_id` asc) | §21.1 line 1642 |
| CA-2 | Keep `offset` and `total`? | Yes, as compatible extras: §21.1 line 1636 makes removing a field or parameter an incompatible change that needs a new major path; adding optional fields is allowed. `offset` stays accepted but cannot be combined with `cursor` (400); the response adds `next_cursor` | §21.1 lines 1636, 1642 |
| CA-3 | Keys on create and update (A04, A05) | Required. Same key and payload → the original result; same key, other payload → 400 `INVALID_IDEMPOTENCY_KEY`; the key is scoped by principal, operation and target | §21.4 line 1697; §21.1 line 1639; §9.8 line 854 |
| CA-4 | Revision precondition on update (A05, O-ACCREV) | **BLOCKED_OPEN.** §21.4 line 1699 names profile, lesson plan, story and script changes; account role and state are not named, and no other clause requires an expected account revision. No `If-Match` is added; `revision` stays in the response | §21.4 line 1699 (silent on accounts) |
| CA-5 | Moderation permission, queue, catalog (B09, G07, G08, O-CONTENTADMIN) | **BLOCKED_OPEN.** The SRS settles that Content Admin is a permission of Platform Admin (lines 192, 226, 2578) and that an independent second Platform Admin reviews Platform-Admin-authored PUBLIC lessons (FR-PL-05, line 2646), but it leaves the permission's storage, resolver and revoke open (§31.10 item 14, line 2755; line 2774). Without a defined permission source the goal cannot implement a check or queue | lines 2755, 2774 |

## 3. BE design (one commit)

1. **Receipts.** New table `be1_platform_admin_command_receipts` (`principal_ref`, `operation_scope`,
   `idempotency_key` as primary key; `request_fingerprint` 64 hex; `response_json` JSONB; `created_at`) by migration
   `20261119_ar_0002` with `down_revision = "20261110_ar_0001"` (the number of heads stays the same), plus its ORM
   model next to `AdultIdentityModel` in `be1_models.py`. The stored response holds no email or display name: replay
   rebuilds them, for create from the request (same fingerprint means the same payload), for update from the identity
   provider as the original call did.
2. **Create (A04).** Required `Idempotency-Key` header (1–128 characters; missing → 400 `INVALID_REQUEST` with field
   error `Idempotency-Key`/`REQUIRED`, the CONV-1 rule). Order: replay check (scope `POST /accounts`, fingerprint of
   the normalized payload) → organization check → provider create → identity row, assignment, audit and receipt in
   one commit. A commit failure still deletes the provider account. A concurrent duplicate fails at the provider
   (email conflict → 409 `ACCOUNT_SETUP_UNAVAILABLE`) or at the receipt key.
3. **Update (A05).** Required key. Replay check (scope `PATCH /accounts/{account_id}`, fingerprint of the payload)
   before the account lookup's checks; then the existing logic; the receipt is written in the same commit. Replay
   returns the stored role, state and revision with the current profile.
4. **List (A03).** `limit` default 25 (max 100); new `cursor` (opaque base64url of the last item's `created_at` and
   `account_id`; a bad cursor → 400 `INVALID_REQUEST`); `cursor` with `offset` > 0 → 400; keyset filter
   `(created_at < c) OR (created_at = c AND account_id > a)`; read `limit + 1` to set `next_cursor` (null at the end).
   With `search`, the keyset filter applies before the in-memory match and `next_cursor` points at the last returned
   match. `total` keeps its meaning (all matches).
5. **OpenAPI** (`openapi_contract.py` catalog entries of the three routes): request inputs name `cursor` and
   `Idempotency-Key`; POST and PATCH join `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` (16 → 18 after C4) and the test set;
   the list response schema gains `next_cursor`.
6. **Tests.** New PostgreSQL integration test `tests/integration/test_platform_admin_accounts_postgres.py` (fresh
   `*be1_acceptance` database on `127.0.0.1:55458`, fake provisioner, no network): default 25 and max 100; cursor
   walk over 30 accounts without gaps or repeats; bad cursor and cursor+offset → 400; create and update without key
   → 400; same key replays without a second provider call; other payload → 400 `INVALID_IDEMPOTENCY_KEY`; no email
   in `response_json`. Contract: catalog constant and set.
7. **Bruno** 142 (`?limit=25`), 143 and 144 (key header placeholder); not run.

**Allowlist:** `routers/platform_admin_accounts.py`; `infrastructure/persistence/be1_models.py` (the new model only);
`alembic/versions/20261119_ar_0002_platform_admin_command_receipts.py` (new); `openapi_contract.py` (three entries and
the constant); `tests/contract/test_openapi_contract_catalog.py`; the new integration test; Bruno 142–144; this plan
and the C5 evidence note.

## 4. Web design (one commit)

- `backendApi.tsx`: `PlatformAccountPage.next_cursor`; `listPlatformAccounts` sends `cursor` (no `offset`);
  `createPlatformAccount` and `updatePlatformAccount` take an `idempotencyKey` and send it.
- `userService.ts`: pass-through of `cursor` and the keys.
- `UsersPage.tsx`: cursor paging with a stack of page-start cursors (next pushes `next_cursor`, previous pops),
  "Trang X / Y" from the stack depth and `total`; filters reset the stack. One key per create or update command,
  kept while the Platform Admin retries the same dialog submission, replaced after success or after the form
  changes.
- Tests next to the changed modules; `npm run test`, lint (no new warnings), build.

## 5. Checks

As C4: ruff and mypy on touched files; unit+contract compared with `tmp/be-integration/fail_ids.txt`; `alembic
upgrade heads` and the new integration test on a fresh database; the four validators; `git diff --check`; security
validator before the commit; web tests, lint, build after a fetch of the teammate branch. Implementation review
(Sonnet 5.5 high) before each commit.
