# C5 C-A — Platform Admin accounts BE slice, implementation evidence (goal v2)

- **Date:** 2026-11-19. **Task:** goal v2 row C5: A03 (cursor paging), A04 and A05 (keys). Accepted by the goal under
  program approval (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, 13,611 B, SHA-256 `5DFC1EDE…4795F8`); owner final
  check pending. Nothing pushed.
- **Plan:** `plan/PLAN_CA_ADMIN_ACCOUNTS_SLICE_DRAFT2_20261119.md` (SHA-256 `A0391334…`). Reviews (Sonnet 5.5, effort
  high, fresh non-forked subagent, because starting a session was refused on this automated turn): Draft 1 R1 NOT
  READY 0 P1 / 6 P2 / 11 P3; Draft 2 R2 READY WITH NOTES 0 / 0 / 6. Reports: `tmp/phase-bc/reviews/C5_CA_DRAFT1_REVIEW_R1.md`,
  `C5_CA_DRAFT2_REVIEW_R2.md`.

## Decisions taken by the goal (SRS D-209 copy, 701,157 B)

| ID | Decision | SRS clause |
|---|---|---|
| CA-1 | Account list uses an opaque cursor, default 25, max 100, order `created_at` desc, `account_id` asc | §21.1 line 1640 |
| CA-2 | `offset` and `total` stay as compatible extras; `offset` is deprecated; `cursor` with `offset > 0` → 400 | §21.1 line 1635 |
| CA-3 | Create and update require an `Idempotency-Key`; same key and payload → original result; other payload → 400 `INVALID_IDEMPOTENCY_KEY` | §21.1 line 1636; §21.4 line 1697; §9.8 line 862 |
| CA-4 | **BLOCKED_OPEN (O-ACCREV):** no `If-Match` on account update; the SRS names no expected-revision rule for account role or state | §21.4 line 1699 (silent) |
| CA-5 | **BLOCKED_OPEN (O-CONTENTADMIN):** moderation permission, queue and catalog (B09, G07, G08); permission storage, resolver and revoke are open. Known standing deviation: moderation is still checked by role only | lines 226, 2755, 2774 |
| CA-6 | Receipts in a BE1-owned table `be1_command_receipts` (migration `20261119_ar_0002`, after `20261110_ar_0001`; heads stay 14) | register line 91 |

## Pending register amendment (for the owner; the goal does not edit `DATA_TABLE_REGISTER.md`)

Proposed row: `be1_command_receipts` — owner BE1 (identity commands); purpose: idempotency receipts of BE1 commands
(Platform Admin account create and update now; later BE1 commands); key (`principal_ref`, `operation_scope`,
`idempotency_key`); optional `organization_id`; `request_fingerprint` (SHA-256 of the canonical payload);
`response_json` without email, display name or child data; retention: kept with the account audit trail, no purge job
yet. It is a module receipt (register line 91), outside the 92 active / 140 mapping count until the owner adds it, and
not an invitation or token table (register line 622). A tenant-scoped command must put its organization in
`operation_scope`, record `organization_id`, and re-authorise the caller before a replay.

## What changed (BE)

- `routers/platform_admin_accounts.py`: `limit_query()` (25/100), `cursor` with keyset paging and `next_cursor`;
  search keeps the full scan, `total` over all matches, cursor located by scan position; deprecated `offset`.
  Create and update read the key with `parse_idempotency_key` (optional header declared for the runtime OpenAPI,
  400 row documented); create: replay → organization → provider → one commit with the receipt; on a commit
  `IntegrityError` the provider account is deleted, then the receipt is re-read (replay, 400, or 409 as before).
  Update: locks the active Platform Admin rows in subject order and then the target (`populate_existing`), replays
  under the lock, writes the receipt in the same commit.
- `be1_models.py`: `Be1CommandReceiptModel`. Migration `20261119_ar_0002_be1_command_receipts.py`.
- Tests: new `tests/integration/test_platform_admin_accounts_postgres.py`; runtime-OpenAPI test in
  `test_openapi_contract_catalog.py`; pinned migration counts in `test_synthetic_eligibility.py` (32 → 33) and
  `test_m2_s2_g1_parent_story_postgres.py` (`ar_0001` → `ar_0002`). Bruno 142–144.

## Checks

- Fresh database `frc08_be1_acceptance_c5_20261119171402` on `127.0.0.1:55458`: `alembic upgrade heads` exit 0,
  14 heads. `tests/integration/test_platform_admin_accounts_postgres.py`: 8 pass (paging, search cursor, legacy
  offset, field errors, 403 on all routes, keyed create with replay and no PII, create failures, keyed update with
  replay, two concurrent identical updates with a forced overlap, update with the provider down).
- `pytest tests/unit tests/contract` in a clean environment: 8,558 tests; 83 failing ids, identical to
  `tmp/be-integration/fail_ids.txt` (0 new). Focused: `test_synthetic_eligibility.py`, catalog and composition
  contract tests pass.
- Ruff: router findings identical to the base (9); new files clean. Mypy (`--follow-imports=silent`) on the router
  and `be1_models.py`: no issues.
- Four validators and `git diff --check`: exit 0.
- Implementation review (Sonnet 5.5 high, subagent): R1 NOT ACCEPTABLE 0 / 2 P2 (test gaps) / 9 P3; the P2s were
  fixed and the locks changed to `FOR NO KEY UPDATE`; R2 ACCEPTABLE WITH NOTES 0 / 0 / 3
  (`tmp/phase-bc/reviews/C5_IMPL_REVIEW_R1.md`, `C5_IMPL_REVIEW_R2.md`).

## Limits recorded

- The create fingerprint is a plain SHA-256 of a payload that contains the email (guessable hash of PII at rest).
- The loser of a same-key, same-payload create race gets 409 from the provider email conflict; a retry replays. An
  orphan provider account after a crash between provider create and commit keeps the email taken (existing).
- The update's provider call runs while the row locks are held; a provider timeout holds them.
- Search pages still read provider profiles for every filtered row (existing cost).
- A Teacher promoted to Platform Admin by a concurrent request is not in another request's lock set (rare deadlock,
  answered as an error); the search fallback compares `account_id` in Python, not in the database collation; the
  provider-down update test stops at the profile read, so the `set_account_disabled` failure branch is not exercised;
  `AUTH_ROLE_API_CONTRACT_REV63` still describes offset paging; `keyForSignature` (web) duplicates the C4 helper.
- No index on `(created_at, account_id)`.
