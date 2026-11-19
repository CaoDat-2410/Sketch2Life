# FEAT-066 / FEAT-081 C3b — Parent run history list and mobile lifecycle screens (Draft 1, goal v2)

- **Status:** DRAFT for independent review. Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, SHA-256 `5DFC1EDE…4795F8`) and the owner's added scope "C3b" in
  `tmp/phase-bc/GOAL_V2_CONTINUATION_C4_C5_20261119.md`. No code before the review verdict is READY (WITH NOTES).
- **Date:** 2026-11-19. **Base:** BE `feature/feat066-be-integration` after M9-B; mobile
  `feature/fe-mobile-remediation` at `04e88ad9` (C3 client layer).
- **Out of scope:** Teacher web run or occurrence history; Bruno requests (B2 deferred).

## 1. Source facts (BE `bb57486d`; mobile `04e88ad9`)

1. Router `interfaces/http/routers/parent_story_runs.py`, prefix `/v1/story-runs`: POST create, GET
   `/active/current`, GET `/{run_id}`, POST `/{run_id}/cancel`, DELETE `/{run_id}`, confirmations. Every route calls
   `_require_parent` (active identity, `account_role="parent"`, matching issuer → else 403) and maps
   `ParentStoryRunError` to the family's error envelope (`ParentStoryErrorEnvelopeV1`). There is **no list route**.
2. Runs live in `story_run_lite/tables.py` `story_runs`: `run_id`, `actor_scope_kind` (`PARENT_ACCOUNT`),
   `actor_scope_ref` (SHA-256 of issuer+subject, `_principal_scope_ref`), `profile_ref` (nullable only for the
   `DELETED` tombstone), `run_state`, `revision`, `version`, `created_at`, `updated_at`. Ownership checks use
   `actor_scope_kind` + `actor_scope_ref` (`_owned_run`, 404 `RESOURCE_NOT_FOUND`).
3. `application/ports/story_run_lifecycle.py`: `CANCEL_ELIGIBLE_STATES` (every public state except `COMPLETED`,
   `FAILED`, `ABANDONED`, `DELETE_PENDING`, `DELETED`; SRS line 1518), `DELETE_ELIGIBLE_STATES` (`COMPLETED`,
   `FAILED`, `ABANDONED`; D-214 item 1), `PURGE_STATES` (`DELETE_PENDING`, `DELETED`).
4. OpenAPI: POST and GET `/{run_id}` are catalogued in `MOUNTED_OPERATIONS`; FR-C-08 cancel and delete are in the
   catalog test's `PR22_UNCATALOGUED_OPERATIONS`.
5. S1 seed has one `DELETE_PENDING` run (the known `r3` base failure in the seed T4 test).
6. Mobile (`apps/ui-mobile`): `ParentApi.listStoryRuns(profileId, cursor)`, `cancelStoryRun`, `deleteStoryRun`
   return `unavailable('run-history')`; `cancelStoryRunV1(runId, expectedRevision, key)` and
   `deleteStoryRunV1(runId, key)` exist (C3). `StoryHistoryScreen.tsx` exists with paging, confirm buttons and an
   unavailable state; it expects full `StoryRun` items and allows delete only for `COMPLETED`.
   `useParentPlatformController.ts` keeps `runs`, `runsCursor`, `runsBusy` and the `run-history` capability
   (`unavailable`). `npm test` runs vitest and `scripts/validate-ui-copy.mjs`.

## 2. SRS answers (D-209 copy, 701,157 B)

| ID | Point | Answer | SRS basis |
|---|---|---|---|
| C3B-1 | Need for a history list | The Parent Android screens include run history, complete/cancel and delete | §21.5 line 1707; FR-C-06 line 498 |
| C3B-2 | Paging | Opaque stable cursor, default 25, max 100, order `created_at` desc then `run_id` desc | §21.1 line 1640 |
| C3B-3 | Scope | Only the caller's own runs (`actor_scope_kind="PARENT_ACCOUNT"` and the caller's scope ref); optional `parent_profile_id` filter for the caller's own profile; a profile that is not the caller's → 404 `RESOURCE_NOT_FOUND` (same shape as missing) | §9.8 404 row; §21.1 "do not trust owner ID from the body" |
| C3B-4 | Projection | Summary only: `run_id`, `parent_profile_id` (null if absent), `run_state`, `revision`, `deleting`, `can_cancel`, `can_delete`, `created_at`, `updated_at`. No story, context, topic, media, asset or provider field | owner scope; NFR-02; DTR §6.5 content-free rule for purge states |
| C3B-5 | Lifecycle states | `DELETED` excluded; `DELETE_PENDING` listed with `deleting: true` and both capabilities false | FR-C-08; owner scope |
| C3B-6 | Capabilities | `can_cancel` = state in `CANCEL_ELIGIBLE_STATES`; `can_delete` = state in `DELETE_ELIGIBLE_STATES` (same sets the commands enforce) | SRS line 1518; D-214 item 1; line 383 |

## 3. BE design (one commit)

1. **Route:** `GET /v1/story-runs` (same path as create, method GET), `_require_parent`, query `limit`
   (`limit_query()`), `cursor` (versioned base64url of `created_at` with time zone and microseconds plus `run_id`; a
   bad cursor → 400 `INVALID_REQUEST` with field error `cursor`/`INVALID_FORMAT`), `parent_profile_id` (UUID,
   optional). Response `ParentStoryRunHistoryPageV1 {request_id, items: [ParentStoryRunSummaryV1], next_cursor}`
   (the contract name the mobile type already uses). Errors use the family's envelope, like the other routes.
2. **Repository:** `SqlParentStoryRunRepository.list_runs(principal, profile_id, limit, cursor)` — one query on
   `story_runs` filtered by the owner scope, `run_state != 'DELETED'`, optional `profile_ref`, keyset
   `(created_at, run_id) < cursor` in descending order, `limit + 1` rows; no joins to inputs, stories or profiles.
   The profile filter checks ownership through the existing profile lookup (`SqlParentStoryProfileLookup`) before
   the query. Service method `ParentStoryRunService.list_runs` passes through.
3. **OpenAPI:** a `MOUNTED_OPERATIONS[('get', '/v1/story-runs')]` entry in the style of the GET `/{run_id}` entry
   (catalogued like its neighbours); the catalog counts move by one (operations and mounted count; the path already
   exists). The route-composition test already lists `/v1/story-runs` (`["POST"]` → `["GET", "POST"]`).
4. **Tests:** new `tests/integration/test_parent_story_run_history_postgres.py` on a fresh `*be1_acceptance`
   database: own runs only (another Parent's runs invisible); `DELETED` excluded; `DELETE_PENDING` shown with
   `deleting` and no capabilities; capabilities per state (`COMPLETED`, `FAILED`, an active state); default 25 and
   max 100 (`limit=101` → 400); cursor walk newest first with ties on `created_at`, no gaps or repeats; bad cursor →
   400; profile filter (own profile → its runs; other Parent's profile → 404); no story, context or asset key in the
   body; non-Parent → 403. Rows are inserted directly into `story_runs` (synthetic data only). Catalog and
   composition contract tests updated.

**Allowlist (BE):** `routers/parent_story_runs.py`; `contracts/schemas/parent_story_runs.py`;
`application/services/parent_story_runs.py`; `application/ports/parent_story_runs.py` (port signature);
`infrastructure/persistence/parent_story_repository.py`; `openapi_contract.py` (one entry); the catalog and
composition tests; the new integration test; this plan and the C3b evidence note. No migration.

## 4. Mobile design (one commit, `.worktrees/mobile`)

- `domain/types.ts`: `ParentStoryRunSummary` and `ParentStoryRunHistoryPage.items: ParentStoryRunSummary[]`.
- `ParentApi.listStoryRuns(profileId, cursor)` calls `GET /v1/story-runs?limit=25[&cursor][&parent_profile_id]`;
  the legacy `cancelStoryRun`/`deleteStoryRun` stubs stay unused.
- Controller: the `run-history` capability becomes available when the live API is configured; `loadRuns` keeps the
  cursor; cancel calls `cancelStoryRunV1(runId, revision, key)` and delete `deleteStoryRunV1(runId, key)` with one
  key per (action, run, revision), reused for a retry; after 202 the run is refreshed in the list as deleting;
  409 `STALE_REVISION` or `INVALID_STATE_TRANSITION` reloads the list with a message; 404 removes the item.
- `StoryHistoryScreen.tsx`: renders summaries (date and state label instead of story title and topic), uses
  `can_cancel` and `can_delete` from the server, shows "Đang xóa" for `deleting`, keeps the existing confirmation
  dialogs; delete is offered for `COMPLETED`, `FAILED` and `ABANDONED` (server flag).
- Tests (vitest) for the API call, the controller actions and the screen states; `npm test` (includes the UI-copy
  validator) and `npm run typecheck`.

## 5. Checks

As the other tasks: ruff and mypy 0 new; unit+contract against `tmp/be-integration/fail_ids.txt`; the new
PostgreSQL test; four validators; `git diff --check`; security validator before the commit; mobile `npm test` and
typecheck. Implementation review (Sonnet 5.5 high) before each commit. Then the mobile branch is merged into the
integration branch again and the mobile checks join D2.
