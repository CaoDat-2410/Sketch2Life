# FEAT-064 chain — GOAL B2 revision 2 plan

- Status: **DRAFT / AWAITING OWNER REVIEW**. Not an implementation approval, T13 live-call approval, or launch prompt.
- Chain position: third only after B1 has an independent **ACCEPTED** review and the owner sends a separate B2 launch. B2 stops at `B2 XONG-CHƯA REVIEW` or `BLOCKED`; it does not call Modal. No stage/commit/push/merge.
- Goal: implement the four T9 assistance gateway operations, create and dry-run the T13 synthetic script with a stub loopback provider, and complete T12 PostgreSQL acceptance only on a separately verified task-owned local-loopback database.
- Authority: V4 §1, §3 D6 (T9), D8 (T13), D9 (live-call sequence is reserved for the owner after B2; not authorization for Codex).

## 1. Planning base and start gate

This plan was drafted against branch `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, and snapshot `.claude/handoff/snapshots/FEAT064_CHAIN_BASE_20261103T165013/manifest.json`, SHA-256 `249C34A8E3FA6B1C98076AEC629E02F4158A5F19905378EBEBF6B81F4AEB4D7C`. This is not B2's execution baseline. A B2 launch must create a fresh post-B1 byte-copy/hash snapshot and pin the then-current branch, HEAD, working-tree paths, exact allowlist, and database identity. Preserve unrelated dirty paths; do not reuse old `1e93bc3f…` pins or assume current OpenAPI counts.

Start only after B1 is independently **ACCEPTED**, the ledger is updated by the owner, and a separate owner launch explicitly pins this plan hash and a safe T12 DB gate. B2 must not begin merely because this plan is approved.

## 2. T9 — four assistance gateway operations

Add exactly these pilot operations under `/api/be1/v1/...`, reusing `build_assistance_requests_router(prefix)` and the existing registration point:

1. Child request: `POST`.
2. Child cancel: `POST`.
3. Child status: `GET`, restricted to the requesting child's own verified device/session and active-or-paused eligibility described by V4.
4. Teacher pending: `GET`, requires verified adult plus current assignment, returns metadata only, and remains readable while paused or with no active turn.

Required behavior: pilot gate is local/test-only and returns 503 when disabled; preserve `AssistanceRequestCommandV1` semantics (`source_ref`/`source_sha256`/`document_revision`, server-owned `context_revision`); resolve principal through the existing dependency boundary; do not add `UNKNOWN` to the public `RequestStatus` contract—keep it in the ledger/projection. Child sees only permitted processing/submitted-to-teacher states, never raw model output. Teacher pending is not approve/reject. The gate is status-only and must not trigger a model call.

There is already a separate teacher pilot-profile lookup route in the current working-tree baseline. It is not one of these four T9 assistance operations. Preserve its source and current OpenAPI catalog/test diff; recalculate operation/path totals from the actual post-B1 baseline and add only the four new operations. Do not revert or claim the profile lookup as part of T9 gateway work.

## 3. T13 — synthetic stub-loopback dry run only

- Create `features/FEAT-064-current-flow-modal-vision-dev/tools/t13_synthetic_pilot_dry_run.py`.
- Build the classroom app using `create_classroom_app()` with local settings, then inject the pilot runtime with `dataclasses.replace`; do not set the Modal URL/token in application settings.
- The script accepts only file paths for any URL/token input and must never print credential contents. The dry-run path must not read or require a provider token.
- `OWNER_MODAL_CALL_APPROVED` remains `NO` and defaults to `NO`. This task cannot set it to `YES`, call Modal, invoke a GPU/provider, or access external network.
- Exercise the complete synthetic flow through a stub HTTP loopback server: organization → class → session → synthetic proof → accepted stroke → request → child status → teacher pending. Include the slow response beyond the fixed deadline and verify fail-closed `UNKNOWN`/one-send behavior. Use new synthetic IDs per run; no real child data.
- This is a dry-run script, not permission to perform either of V4 D9's later owner-run live calls.

## 4. T12 — PostgreSQL acceptance safety gate

T12 may run only after a separate launch supplies/authorizes a **task-owned, disposable PostgreSQL database on local loopback** and records its exact database identity without recording the connection string. Before connecting:

1. Verify the endpoint is a loopback address and the database name exactly matches the launch approval. Never print the URL/credentials.
2. Verify the database is dedicated to this task, not `sketch2life`, a shared development database, or a database with unknown ownership. Check expected schema/table inventory read-only before any migration.
3. If identity, ownership, or inventory is unclear or unexpected, mark T12 `NOT RUN / BLOCKED`; do not reset, drop, truncate, recreate, or clean it.
4. Only the explicitly approved migration upgrade/downgrade round-trip may run against the task-owned database. A downgrade may drop only the new pilot branch objects explicitly covered by V4; never drop a database or pre-existing shared schema. Clean only rows whose synthetic IDs were created by the current test run, in foreign-key-safe order. Never delete possible prior leaked or unknown rows.
5. Run full BE1 + pilot assistance/analysis integration acceptance on that isolated DB, report table counts before/after and the actual status of the existing migration-head assertion. Do not change `test_migrations.py` under this goal merely to make the test green.

The DB path/identity is not presently verified by this planning task. Do not infer it from the historical `*_be1_acceptance` report or assume a local `.url` file still points to a task-owned DB.

## 5. Exact proposed allowlist

T9 source:

- New `backend/src/sketch2life/interfaces/http/routers/pilot_assistance.py` — the four operations and pilot gate.
- `backend/src/sketch2life/interfaces/http/router_composition.py` — registration only.
- `backend/src/sketch2life/interfaces/http/be1_runtime.py` — route/runtime wiring only; do not alter the B1 pilot field beyond the exact wiring necessary.
- `backend/src/sketch2life/contracts/schemas/assistance_requests.py` — only if a route-specific request/response projection requires it; `AssistanceRequestCommandV1` remains unchanged.

Tests and T13 script:

- `backend/tests/contract/test_openapi_contract_catalog.py` — update only for the four T9 operations, preserving the pre-existing pilot-profile lookup operation.
- `backend/tests/contract/test_app_composition.py` — route composition/gate cases only.
- `backend/tests/integration/test_be1_postgres_api.py` — route-count/assertion section only; preserve unrelated current test diffs byte-for-byte.
- New `backend/tests/integration/test_pilot_assistance_routes_t9.py`.
- New `backend/tests/contract/test_t13_synthetic_pilot_dry_run.py`.
- New `features/FEAT-064-current-flow-modal-vision-dev/tools/t13_synthetic_pilot_dry_run.py`.

Task records after a separate B2 launch approval: this plan, one T9/T13/T12 report, append-only approval/ledger entries, and one ignored `GB2_*` snapshot.

Explicit exclusions: `backend/src/sketch2life/interfaces/http/openapi_contract.py`; pilot-profile lookup route implementation; all A2/B1 sources beyond the small runtime wiring listed; `services/ai_jobs.py` and AI Jobs ports/contracts/tables/repository; UI; Modal app/config/secrets; provider/GPU/live call; external network; database provisioning; and all other paths. Any extra source/test/schema path is a hard stop until separately approved.

## 6. Acceptance and stop conditions

| Area | Required evidence |
|---|---|
| T9 | Exactly four operations added; route/pilot gate/auth/projection semantics above pass focused tests; actual OpenAPI paths/operation totals recounted from post-B1 baseline. |
| T13 | Script completes end-to-end with only synthetic fixture data and a stub loopback server; slow response produces bounded fail-closed behavior; captured count proves no automatic retry or external call. |
| T12 | DB safety gate verified; migrations round-trip on the dedicated task-owned DB; scoped integration suites pass; table counts and migration-head assertion status recorded. Otherwise mark NOT RUN/BLOCKED, never substitute a shared database. |
| Static | Ruff with `backend/pyproject.toml`, focused strict mypy, three repository validators, `git diff --check`, and exact-path diff/hashes recorded. |
| Chain | Goal ends XONG-CHƯA REVIEW; wait for independent ACCEPTED review. `READY_FOR_T13` is only a local readiness report, not authorization for a live call. |

If any DB safety gate fails, continue only independent T9/T13 stub work if safe and in scope, but T12 and `READY_FOR_T13` remain BLOCKED/CHƯA. If route authentication, status semantics, migration ownership, or external-call exclusion cannot be proved, stop and report the precise blocker. Never set `OWNER_MODAL_CALL_APPROVED=YES`.

## 7. Approval required before implementation

Owner must separately review this plan and, only after B1 acceptance, send a B2 launch that pins this plan hash, a fresh post-B1 snapshot, exact allowlist, and the task-owned loopback DB identity/ownership. Approval must explicitly state the maximum T12 migration operations and the cleanup boundary. This draft does not write `TASK_APPROVAL.md`, provision a DB, or authorize implementation/live calls.

## 8. Authority checked

- V4 `OWNER_DECISIONS_G3G4_V4_20261101.md`: SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Old B2 goal `CODEX_GOAL_G3G4_B2_20261101.md`: SHA-256 `DCC900204C53CFC1961BB00729B7A91821D878C548603BAD7C97C5511EDDD99A`.
- T12 procedure `CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md`: SHA-256 `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C5063657`.
- The old B2 `1e93bc3f…` HEAD pin and old expected route counts are historical; the B2 launch must use new baselines and real counts.
