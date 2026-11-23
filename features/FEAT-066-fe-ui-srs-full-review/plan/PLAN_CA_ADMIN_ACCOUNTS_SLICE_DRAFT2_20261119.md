# FEAT-066 C-A — Platform Admin accounts slice (Draft 2, goal v2 C5)

- **Status:** DRAFT for independent review (round 2). Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, 13,611 B, SHA-256 `5DFC1EDE…4795F8`, row C5). No code before the
  review verdict is READY (WITH NOTES).
- **Date:** 2026-11-19. **Supersedes:** Draft 1 (`PLAN_CA_ADMIN_ACCOUNTS_SLICE_DRAFT1_20261119.md`, 8,916 B,
  `C2CEC8B3…`; review R1 NOT READY 0 P1 / 6 P2 / 11 P3, `tmp/phase-bc/reviews/C5_CA_DRAFT1_REVIEW_R1.md`). Draft 1
  stays as written. §7 maps each R1 finding to its fix.
- **Base:** BE `feature/feat066-be-integration` after the C4 BE commit; web `codex/fe-ui-web-remediation` after the C4
  web commit.
- **Register rows (Draft 4, `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md`):** A03, A04,
  A05, B09; gaps G07, G08. Open questions O-ACCREV (A05) and O-CONTENTADMIN (B09, G07, G08).

## 1. Source facts (BE `63363081`, web `7e416725`; checked by review R1)

1. `interfaces/http/routers/platform_admin_accounts.py`: `GET /api/platform-admin/v1/accounts` pages by `limit`
   (default 50, max 100) and `offset`; order `created_at` desc, `account_id` asc; response `{items, total, limit,
   offset}`. With `search`, all filtered rows are read, provider profiles are loaded in chunks of 100, matched in
   memory, `total` = all matches, then sliced by offset.
2. POST and PATCH take no key and no `If-Match`. POST calls `provisioner.create_account` before the commit and deletes
   the provider account when the commit fails (409 `ACCOUNT_SETUP_UNAVAILABLE` on `IntegrityError`, 503 on other
   database errors). PATCH may call `provisioner.set_account_disabled` before the commit and reverts it on failure.
   `AccountResponse.revision` is `be1_adult_identities.role_revision`.
3. No table can hold these receipts: `core_idempotency_receipts` has a foreign key to canvas operations;
   `lesson.command_receipts` is Lesson-owned; `be1_session_command_receipts` is legacy and session-bound;
   `ai_jobs` receipts are job-bound. `20261110_ar_0001` has no dependant (a head on its lineage).
4. The three routes are **not** in the OpenAPI catalog: `tests/contract/test_openapi_contract_catalog.py` lists them
   in `PR22_UNCATALOGUED_OPERATIONS` (size 13, disjoint from `MOUNTED_OPERATIONS`). No functional test exercises them.
   `/api/platform-admin/v1` is a CONV-1 envelope family.
5. Two tests pin the migration graph: `tests/unit/test_synthetic_eligibility.py` (32 revision files; heads 14 and 10)
   and `tests/integration/test_m2_s2_g1_parent_story_postgres.py` (`_EXPECTED_VERSION_ROWS` contains
   `20261110_ar_0001`; env-gated).
6. Shared helpers exist: `api_conventions.limit_query()` and `parse_idempotency_key(request)`; an opaque cursor
   precedent exists in `parent_profile_repository.py` (`_encode_cursor`/`_decode_cursor`, versioned payload, field
   error `cursor`/`INVALID_FORMAT`).
7. Web: `backendApi.tsx` `listPlatformAccounts` sends `limit` and `offset`; create and update send no key.
   `UsersPage.tsx`: `PAGE_SIZE = 25`, offset state, "Trang X / Y" from `total`, previous/next buttons, an inline
   create form and per-row role/state buttons; no tests exist for the page or `userService.ts`.
8. Bruno 142 (`?limit=50&offset=0`), 143, 144 exist. Lesson moderation (B09) is mounted, keyed and preconditioned,
   and checked by role only (`lesson_library.py` `_platform_admin`).

## 2. SRS answers

| ID | Point | Answer | SRS basis |
|---|---|---|---|
| CA-1 | Account list paging (A03) | Cursor pagination, opaque stable cursor, default 25, max 100, explicit order `created_at` desc, `account_id` asc | §21.1 line 1640 |
| CA-2 | Keep `offset` and `total` | Yes, as compatible extras during a compatibility period: an incompatible change needs a new major path or schema version, optional additions are allowed. `offset` is marked deprecated (removal once the web slice is the only caller); `cursor` with `offset > 0` → 400 | §21.1 line 1635 |
| CA-3 | Keys on create and update (A04, A05) | Required; same key and payload → original result; same key, other payload → 400 `INVALID_IDEMPOTENCY_KEY`; scope per principal, operation and target | §21.1 line 1636; §21.4 line 1697; §9.8 line 862 |
| CA-4 | Revision precondition on update (O-ACCREV) | **BLOCKED_OPEN.** Line 1699 names profile, lesson plan, story and script only; no clause requires an expected account revision. No `If-Match`; `revision` stays in the response. The row lock of §3 step 3 serialises concurrent updates without inventing a precondition | §21.4 line 1699 (silent) |
| CA-5 | Moderation permission, queue, catalog (B09, G07, G08, O-CONTENTADMIN) | **BLOCKED_OPEN.** Content Admin is a Platform Admin permission (lines 192, 226, 2578) and an independent second admin reviews admin-authored PUBLIC (line 2646), but the permission's storage, resolver and revoke are open (line 2755, §31.10(14); line 2774). Known standing deviation: moderation is checked by role only, unchanged | lines 226, 2755, 2774 |
| CA-6 | Where receipts live | A BE1-owned module receipt (register line 91: idempotency uses the receipt owned by the module). New table `be1_command_receipts`, generic for BE1 commands (C5 accounts now; C6 M9-B next). Physical choice recorded by the goal in the C5 evidence note as a **pending register amendment** for the owner's final check; the goal does not edit `DATA_TABLE_REGISTER.md`. It is not an invitation or token table (register line 622) | register lines 91, 622, 742; SRS §11 line 1000 |

## 3. BE design (one commit)

1. **Receipt table.** Migration `20261119_ar_0002_be1_command_receipts` (`down_revision = "20261110_ar_0001"`):
   `be1_command_receipts` (`principal_ref` String 256, `operation_scope` String 256, `idempotency_key` String 128 —
   primary key together; `request_fingerprint` String 64, check length 64; `response_json` JSONB; `created_at`).
   ORM model `Be1CommandReceiptModel` in `be1_models.py`. Only successful commits write a row; failures are not
   cached. `response_json` holds no email and no display name. The fingerprint is SHA-256 of the canonical payload;
   for create the payload contains the email, so the fingerprint is a guessable hash of PII at rest — recorded as a
   known limitation with the register amendment (retention: kept with the account audit trail; no purge job in C5).
2. **Create (A04).** Key via `parse_idempotency_key(request)` (missing → 400 `INVALID_REQUEST`, field
   `Idempotency-Key`/`REQUIRED`; bad → `INVALID_FORMAT`), declared as `Header(alias="Idempotency-Key")` for the
   runtime OpenAPI too. Order: replay (scope `POST /accounts`; fingerprint of the normalized payload) → organization
   check → provider create → identity, assignment, audit, receipt in one commit. Replay returns 201 with the stored
   `account_id`, `role`, `state`, `revision` and the email and display name of the current request (same fingerprint
   means the same payload); it calls no provider and writes no audit. On a commit `IntegrityError`: delete the
   provider account (as today), then re-read the receipt in a new transaction: same fingerprint → replay; other
   fingerprint → 400 `INVALID_IDEMPOTENCY_KEY`; none → 409 `ACCOUNT_SETUP_UNAVAILABLE` (as today). Known limits:
   the loser of a same-key, same-payload race gets 409 from the provider email conflict, and an immediate retry
   replays; an orphan provider account after a crash between provider create and commit keeps the email taken
   (existing behaviour; adopting a provider account is a security decision, not invented here).
3. **Update (A05).** Required key. Order: `SELECT … FOR UPDATE` the identity row by `account_id` (404 if absent) →
   replay under the lock (scope `PATCH /accounts/<real account_id>`; fingerprint covers the account ID and the
   payload) → existing validations (`LAST_PLATFORM_ADMIN` count now runs under the row lock of the target) → provider
   call → commit with the receipt. Replay returns the stored role, state and revision with the current profile. On a
   receipt `IntegrityError` at commit: no provider revert unless this request changed the provider state and its own
   transaction failed; then re-read the receipt and replay or return 400 `INVALID_IDEMPOTENCY_KEY`.
4. **List (A03).** `limit` via `limit_query()` (default 25, max 100). New `cursor` (versioned base64url payload of
   `created_at` with time zone and microseconds plus `account_id`, as the Parent precedent; bad → 400 field error
   `cursor`/`INVALID_FORMAT`); `cursor` with `offset > 0` → 400 field error `offset`/`INVALID_FORMAT`. `next_cursor`
   is returned in both modes (null at the end); in cursor mode `offset` echoes 0.
   - **Without search:** keyset predicate `created_at < c OR (created_at = c AND account_id > a)`, read `limit + 1`,
     `total` = count of all filtered rows (unchanged).
   - **With search:** keep today's full ordered scan and in-memory match; `total` = all matches (unchanged, so the
     page counter stays right); then return the matches after the cursor position (keyset comparison on the match
     list), `limit` of them, `next_cursor` from the last returned match when more remain. Cost stays one provider
     lookup per 100 filtered rows per page (accepted existing debt). No index on `(created_at, account_id)`; noted.
5. **OpenAPI:** option (a) of R1-01. The routes stay uncatalogued (`PR22_UNCATALOGUED_OPERATIONS` size 13, catalog
   constants and `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` unchanged). The runtime OpenAPI shows `cursor`, the
   `Idempotency-Key` header and a 400 response for the mismatch through the router declarations; a contract test
   asserts those three on the runtime schema.
6. **Migration-pinned tests:** `test_synthetic_eligibility.py` 32 → 33 files (heads stay 14 and 10, because
   `ar_0002` replaces `ar_0001` as head); `test_m2_s2_g1_parent_story_postgres.py` pinned set: `20261110_ar_0001` →
   `20261119_ar_0002` with a comment, as FR-C-08 did.
7. **New PostgreSQL test** `tests/integration/test_platform_admin_accounts_postgres.py` (fresh database whose name
   contains `be1_acceptance` on `127.0.0.1:55458`; fake provisioner via `create_app(identity_account_provisioner=…)`;
   no network): default 25 and max 100; cursor walk over 30 accounts with ties on `created_at`, no gaps or repeats;
   search + cursor walk with a constant `total`; legacy `offset` path; bad cursor and cursor + offset → 400;
   non-admin → 403 on all three routes; create and update without key → 400; same key replays without a second
   provider create or audit row; other payload → 400 `INVALID_IDEMPOTENCY_KEY`; no email in `response_json`;
   create commit failure → provider account deleted and no receipt; provider-down → 503; two concurrent identical
   PATCHes → one change, provider and database agree; `alembic upgrade heads` and the head count.
8. **Bruno** 142 (`?limit=25`), 143 and 144 (key header placeholder); not run.

**Allowlist (BE):** `routers/platform_admin_accounts.py`; `infrastructure/persistence/be1_models.py` (the receipt
model only); `alembic/versions/20261119_ar_0002_be1_command_receipts.py` (new);
`tests/integration/test_platform_admin_accounts_postgres.py` (new); a runtime-OpenAPI assertion in
`tests/contract/test_openapi_contract_catalog.py` or a new contract test file; `tests/unit/test_synthetic_eligibility.py`;
`tests/integration/test_m2_s2_g1_parent_story_postgres.py`; Bruno 142–144; this plan and the C5 evidence note
(which carries the pending register amendment text).

## 4. Web design (one commit)

- `backendApi.tsx`: `PlatformAccountPage.next_cursor`; `listPlatformAccounts` sends `cursor` (no `offset`);
  `createPlatformAccount(payload, idempotencyKey)` and `updatePlatformAccount(accountId, payload, idempotencyKey)`
  send the key (generated with the existing `createRequestId()`).
- `userService.ts`: pass `cursor` and the keys through.
- `UsersPage.tsx`: a stack of page-start cursors (first page `undefined`); next pushes `next_cursor`, previous pops;
  page number = stack depth, "Trang X / Y" from `total` and `PAGE_SIZE`; range "X–Y" = (depth − 1) × `PAGE_SIZE` + 1
  to that + items; a filter change resets the stack; after a role or state change the current page reloads from its
  own start cursor. Keys: one per create form content (kept for a retry of the same content, replaced after success
  or after the form changes); one per (account, intended change) for row buttons, replaced after success.
- New tests: `UsersPage` (stack push and pop, filter reset, reload after mutation, key reuse on retry, new key after
  success) and `userService`/`backendApi` (cursor and key headers), with the existing session and auth-bridge mocks.
- `npm run test`, lint (no new warnings), build.
- **Rollout:** the BE refuses a missing key, so both commits stay local and are pushed together by the owner.

**Allowlist (web):** `shared/api/backendApi.tsx`; `modules/platform-admin/services/userService.ts`;
`modules/platform-admin/pages/UsersPage.tsx`; new test files next to them; the C5 web evidence note.

## 5. Checks

Ruff and mypy on touched files; `pytest tests/unit tests/contract` in a clean environment compared with
`tmp/be-integration/fail_ids.txt` (0 new), including `test_synthetic_eligibility.py` and the error-envelope coverage
test; `alembic upgrade heads` on a fresh database and the new integration test; the four validators; `git diff
--check`; the security validator before the commit. Web: fetch the teammate branch first; tests, lint, build.
Implementation review (Sonnet 5.5 high) before each commit.

## 6. Parked

- O-ACCREV (CA-4) and O-CONTENTADMIN (CA-5): `BLOCKED_OPEN`, reasons above.
- Register amendment for `be1_command_receipts`: written in the evidence note, applied by the owner (not the goal).

## 7. Review R1 findings and their fixes

| Finding | Fix in Draft 2 |
|---|---|
| C5-R1-01 (P2) routes uncatalogued | §1 fact 4; §3 step 5 option (a) |
| C5-R1-02 (P2) migration-pinned tests | §1 fact 5; §3 step 6; allowlist |
| C5-R1-03 (P2) search `total` | §3 step 4 search path |
| C5-R1-04 (P2) PATCH concurrency | §3 step 3: row lock, replay under lock, no stray revert; race test |
| C5-R1-05 (P2) register | CA-6; §6; evidence note carries the amendment for the owner |
| C5-R1-06 (P2) create collisions | §3 step 2 |
| C5-R1-07 (P3) citations | §2 lines 1635, 1636, 1640, 862 |
| C5-R1-08 (P3) scope and fingerprint | §3 steps 1–3 |
| C5-R1-09 (P3) PII and retention | §3 step 1 limitation and retention |
| C5-R1-10 (P3) shared helpers | §3 steps 2 and 4 |
| C5-R1-11 (P3) keyset details | §3 step 4 |
| C5-R1-12 (P3) compatibility fields | CA-2; §3 step 4 |
| C5-R1-13 (P3) CA-5 deviation | CA-5 |
| C5-R1-14 (P3) orphan provider account | §3 step 2 known limits |
| C5-R1-15 (P3) test list | §3 step 7 |
| C5-R1-16 (P3) web | §4 |
| C5-R1-17 (P3) search cost | §3 step 4 |
