# FEAT-066 / FEAT-081 C3b — Parent run history list and mobile lifecycle screens (Draft 3, goal v2)

- **Status:** DRAFT for independent review (round 3, the last under D-171). Goal v2 coordinator, program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, SHA-256 `5DFC1EDE…4795F8`) and the owner's added scope "C3b"
  (`tmp/phase-bc/GOAL_V2_CONTINUATION_C4_C5_20261119.md`). No code before READY (WITH NOTES).
- **Supersedes:** Draft 2 (`PLAN_C3B_PARENT_RUN_HISTORY_DRAFT2_20261119.md`, SHA-256 `F3D22153…`; review R2 NOT READY
  0 P1 / 1 P2 / 6 P3, `tmp/phase-bc/reviews/C3B_DRAFT2_REVIEW_R2.md`) and Draft 1 (`D2AAD893…`; R1 NOT READY 0 / 7 /
  13). §7 maps R1, §8 maps R2.
- **Order and base:** BE `feature/feat066-be-integration` at `6f10ec24` (M9-B committed);
  catalog counts are "+1 relative to the tree at implementation time". Mobile `feature/fe-mobile-remediation` at
  `04e88ad9`. SRS repository copy 701,810 B (`443A3CA3…`); cited lines unchanged.
- **Out of scope:** Teacher web history; Bruno; "Hoàn tất" (complete run): SRS 1707 lists it, but there is no BE
  complete route for the Parent family, so the `completeRun` stub stays unavailable.

## 1. Source facts (checked by review R1)

1. `routers/parent_story_runs.py`, prefix `/v1/story-runs`: create, GET `/active/current` (marked "[PROPOSAL]"),
   GET `/{run_id}`, cancel, delete, confirmations; `_require_parent` → 403. No list route. A GET on the bare prefix
   cannot collide with the other GET routes (they need a further segment).
2. Errors in this family (`app.py:449-520, 600-693`): every `HTTPException` becomes the family envelope with
   `field_errors: null`; a `RequestValidationError` becomes 400 `INVALID_REQUEST` with
   `field_errors: [{field, code: "INVALID_FIELD", message}]`. Query validation runs before the handler (so before
   the 403).
3. `story_runs` (`story_run_lite/tables.py`): owner by `actor_scope_kind="PARENT_ACCOUNT"` + `actor_scope_ref`
   (SHA-256 of issuer+subject); `profile_ref` becomes NULL at purge step 4 while the run is still `DELETE_PENDING`
   (`story_lifecycle_store.py:58-70, 181-186`) and stays NULL for `DELETED`; the state check allows ten states plus
   `DELETED` (no `ABANDONED`); index `(actor_scope_kind, actor_scope_ref, updated_at)`.
4. `story_run_lifecycle.py`: `CANCEL_ELIGIBLE_STATES`, `DELETE_ELIGIBLE_STATES` (`COMPLETED`, `FAILED`,
   `ABANDONED`), `PURGE_STATES`, `PUBLIC_RUN_STATES`.
5. Profile ownership: `parent_models.ParentChildProfileModel` has `owner_issuer`, `owner_subject`, `state`,
   `deleted_at`. `SqlParentStoryProfileLookup` returns only `ACTIVE` profiles and reads the revision (create rules).
6. OpenAPI: POST and GET `/{run_id}` are catalogued; cancel and delete are uncatalogued (PR22) and absent from the FE
   projection `SRS_V22_INCLUDED_OPERATIONS`. Catalog pins: `test_openapi_contract_catalog.py:279` and `:623`
   (operations), `:283` and `MOUNTED_OPERATION_COUNT` (`openapi_contract.py:15`), request inputs compared exactly
   (`:391-398`), responses compared to the declared set (`:360`). Offline harness:
   `tests/contract/test_parent_story_run_request_contract.py` (fake service, error-shape checks, "seven routes").
7. Seed S1 inserts runs without `created_at` (same `now()`: ties) and one `DELETE_PENDING` run; it also has an own
   profile in `DELETE_PENDING` (`k2`).
8. Mobile: `ParentApi.listStoryRuns`, `cancelStoryRun`, `deleteStoryRun` return `unavailable`; `cancelStoryRunV1` and
   `deleteStoryRunV1` exist. `useParentPlatformController.ts` is a stateless stub (`runs: []`, `runsError:
   unavailableMessage` literals; capability constant). `ParentApplicationModule.platform` picks `listRuns`,
   `cancelRun`, `deleteRun` but not `cancelRunV1`/`deleteRunV1`. `StoryHistoryScreen.tsx` exists. No React test
   renderer is installed; controller and screen tests are source-text checks and pure functions
   (`tests/parentSrsBehavior.test.ts`). `scripts/validate-ui-copy.mjs` does not scan `src/parent/**`.

## 2. Decisions

| ID | Point | Answer | Basis |
|---|---|---|---|
| C3B-1 | Need | Run history, cancel and delete on the Parent Android screens; "Hoàn tất" stays out (no route) | SRS §21.5 line 1707; FR-C-06 line 498 |
| C3B-2 | Paging | Opaque cursor, default 25, max 100; `limit` outside 1–100 → 400 `INVALID_REQUEST` (CONV-1 C-D8 rule, family validation shape); order newest first, `run_id` desc tie-break (owner scope) | §21.1 line 1640; §9.8 400 |
| C3B-3 | Scope | The caller's runs only; optional `parent_profile_id` of the caller's own profile (any profile state); unknown or foreign → 404 `RESOURCE_NOT_FOUND` | NFR-02 line 627; AC-27 line 1150; §9.8 404 |
| C3B-4 | Projection | `run_id`, `parent_profile_id` (null for purge states), `run_state`, `revision`, `deleting`, `can_cancel`, `can_delete`, `created_at`, `updated_at`. Nothing else | owner scope; DTR §6.5 content-free rule |
| C3B-5 | Lifecycle | `DELETED` excluded; `DELETE_PENDING` listed with `deleting: true`, `parent_profile_id: null`, no capability; with a profile filter only live (non-purge) runs are listed (a purge row has no profile after step 4) | FR-C-08; owner scope |
| C3B-6 | Capabilities | `can_cancel` = state ∈ `CANCEL_ELIGIBLE_STATES`; `can_delete` = state ∈ `DELETE_ELIGIBLE_STATES` | SRS line 1518; D-214 item 1; line 383 |
| C3B-7 | Proposal marker | The route is not in §21.2 (the table has only GET by id); summary marked "[PROPOSAL]" and catalog verification text says so, as `/active/current` | §21.2 gap; B4 recorded |

## 3. BE design (one commit)

1. **Route** `@router.get("")` placed after create: `_require_parent`; `limit: int = limit_query()`; `cursor: str |
   None = Query(None, min_length=1, max_length=512)`; `parent_profile_id: UUID | None`. The handler decodes the cursor
   (versioned base64url JSON `{created_at (time-zone aware, microseconds), run_id (UUID), v: 1}`); any defect →
   `HTTPException(400, {"code": "INVALID_REQUEST"})` (family shape: `field_errors` null). Order of answers: query
   validation 400 → 403 non-Parent → cursor 400 → profile 404. The cursor is not bound to the filter (the owner
   predicate always applies). `responses=` declares 200, 400, 401, 403, 404, 422, 500, 503 (422 mapped to the family
   envelope, as the neighbours: FastAPI otherwise adds its own 422 `HTTPValidationError` for an operation with
   parameters); no 409. Response
   `ParentStoryRunHistoryPageV1 {request_id, items, next_cursor}`, items `ParentStoryRunSummaryV1` with
   `parent_profile_id: UUID | None`.
2. **Service** `ParentStoryRunService.list_runs(principal, profile_id, limit, cursor)`: when `profile_id` is given,
   `profile_lookup.is_owned_profile(principal, profile_id)` — a new method on the existing read-only port
   `ParentStoryProfileLookupPort` and `SqlParentStoryProfileLookup` (ownership-only query on `ParentChildProfileModel`
   by owner issuer and subject, any state, no revision read; a database error → 503
   `PARENT_PROFILE_REVISION_UNAVAILABLE`) → else 404; then `repository.list_runs(...)`. The Story repository does not
   import the profile models.
3. **Repository** `list_runs`: one query on `story_runs` — owner scope, `run_state != 'DELETED'`; with a profile:
   `profile_ref = :id` and `run_state NOT IN purge states`; keyset `(created_at, run_id) < (c, r)` descending;
   `limit + 1`. Mapping: purge states → `parent_profile_id = None`; a live row with a NULL or malformed `profile_ref`
   (not expected; the code keeps it set) also maps to `None` so one defective row cannot fail the page. Capability mapping as a pure function `run_summary_capabilities(state)` in the repository module, unit
   tested over `PUBLIC_RUN_STATES` (covers `ABANDONED`, which the table cannot store). The existing owner index does not
   cover the sort; acceptable per account (no migration).
4. **OpenAPI:** `MOUNTED_OPERATIONS[('get', '/v1/story-runs')]` in the style of the `/active/current` entry
   ("[PROPOSAL]" verification text), request inputs `query \`limit\`: integer; query \`cursor\`: string; query
   \`parent_profile_id\`: uuid` (no star), the eight response rows (200, 400, 401, 403, 404, 422, 500, 503). Pins +1: operations (two pins), mounted count (test
   `:283` and `MOUNTED_OPERATION_COUNT`); paths and PR22 unchanged. FE projection: the route joins
   `SRS_V22_INCLUDED_OPERATIONS` (the mobile team reads the projected spec; C3 cancel/delete stay as they are). The
   composition test: `/v1/story-runs` → `["GET", "POST"]`.
5. **Tests.**
   - Offline (`tests/contract/test_parent_story_run_request_contract.py`, default suite): `limit=101` and `limit=0` →
     400 family shape with `field=limit`; bad cursor → 400, `field_errors` null; bad `parent_profile_id` → 400;
     non-Parent → 403 (a second fake database whose identity has `account_role="teacher"`); success key set
     `{request_id, items, next_cursor}` and item keys exactly C3B-4 (`_FakeStoryRunService.list_runs` returns a page);
     an empty or over-512 `cursor` gives the validation shape (`field_errors` with `INVALID_FIELD`), a malformed
     non-empty cursor gives `field_errors: null`; the "seven routes" test lists nine requests and its name drops the
     number.
   - Catalog: the runtime response set equals the declared set for the new entry (the existing row test).
   - Unit: cursor encode/decode (version, naive time, non-UUID, length) and `run_summary_capabilities` over all public
     states.
   - PostgreSQL (`tests/integration/test_parent_story_run_history_postgres.py`, fresh `*be1_acceptance` database, same
     skip guard as its neighbours, run by the goal): own runs only; `DELETED` excluded; `DELETE_PENDING` with and
     without `profile_ref` (null in the item; excluded under a filter); capabilities for `COMPLETED`, `FAILED`, an
     active state; ties on `created_at` walked without gaps; profile filter (own `ACTIVE`, own `DELETE_PENDING`
     profile, foreign → 404); no story/context/asset keys; the S1 seed rows (one `DELETE_PENDING`, tied timestamps)
     list correctly when the seed is loaded in that database.

**Allowlist (BE):** `routers/parent_story_runs.py`; `contracts/schemas/parent_story_runs.py`;
`application/services/parent_story_runs.py`; `application/ports/parent_story_runs.py`;
`application/ports/parent_story_profile_lookup.py`; `infrastructure/persistence/parent_story_profile_lookup.py`;
`infrastructure/persistence/parent_story_repository.py`; `openapi_contract.py` (entry and count);
`openapi_srs_v22.py`; the catalog, composition and request-contract tests; one new unit test file; the new
integration test; this plan and the evidence note. No migration.

## 4. Mobile design (one commit)

**Allowlist (mobile, `apps/ui-mobile`):** `src/parent/domain/types.ts`, `src/parent/infrastructure/http/ParentApi.ts`,
`src/parent/application/ports/ParentApplicationModule.ts`, `src/parent/application/parentRunHistory.ts` (new, pure),
`src/parent/presentation/navigation/useParentPlatformController.ts`, `src/parent/presentation/ParentExpoApp.tsx` (only
if the list must reset when the selected profile changes; otherwise untouched; `ParentVisualPreviewHarness.tsx`
stays untouched),
`src/parent/presentation/screens/StoryHistoryScreen.tsx`, `tests/parentSrsBehavior.test.ts` (amended),
`tests/parentRunHistory.test.ts` (new), the evidence note.

- Types: `ParentStoryRunSummary`; `ParentStoryRunHistoryPage {request_id, items: ParentStoryRunSummary[],
  next_cursor}` (the `contract` field dropped).
- `ParentApi.listStoryRuns(profileId, cursor)` stays at its position and calls `GET /v1/story-runs?limit=25
  [&cursor][&parent_profile_id]`. The legacy `cancelStoryRun`/`deleteStoryRun` stubs stay unused.
- `ParentApplicationModule.platform` adds `cancelRunV1` and `deleteRunV1`.
- Pure module `parentRunHistory.ts`: page merge (cursor null replaces; a cursor appends with `run_id`
  de-duplication; a cursor that does not advance stops paging), key retention by `(action, runId, revision)` (a new
  revision gets a new key: the BE fingerprint includes the expected revision), outcome mapping (202 → item becomes
  deleting; 409 `STALE_REVISION`/`INVALID_STATE_TRANSITION` → reload with a message; 404 → remove the item), item →
  view model (state label, date, `deleting`). After a 202 the item is patched locally from the lifecycle projection
  (`run_state`, `revision`; `deleting: true`, no capabilities); no extra request; the next page load replaces it.
- `useParentPlatformController.ts`: real state for runs, cursor, busy, error and per-run action; the `run-history`
  capability is available when `parentConfig.apiBaseUrl` is not empty (else unavailable as today); the initial error
  is empty. Cancel and delete go through `application.platform.cancelRunV1/deleteRunV1`. After a cancel the Parent
  controller's active-run check runs again on its next resume (existing); the history item is patched locally.
- `StoryHistoryScreen.tsx`: summaries (date and state label; no story title or topic), server flags (a
  `const canCancel = run.can_cancel` line keeps the source anchor), "Đang xóa" for `deleting`, confirmation dialogs;
  cancel copy says the session content will be deleted and cannot be restored (SRS lines 500, 1518–1520).
- Amended tests (deliberately): `parentSrsBehavior.test.ts` line ~441 (remove only the `listStoryRuns` row from the
  absent-route table; the legacy `cancelStoryRun` and `deleteStoryRun` rows stay; add a positive list-call test),
  lines ~420/772 (the set of names matched by `application\.platform\.(\w+)` in the controller source equals
  `{listRuns, cancelRunV1, deleteRunV1}`), keep the screen anchors at ~794–796 and ~618–619, keep `listStoryRuns`
  after `createStoryRevisionV1` (~723), keep the controller lines at ~765–773 (`jobStatus`, `video`, `requestVideo`,
  `completeRun`, `videoOperationState: unavailableShareOperation`). New `parentRunHistory.test.ts` for the pure module and the API request shape, plus
  source-text checks that the new Vietnamese strings exist (the copy validator does not scan `src/parent`). No new
  dependency.
- `npm test` and `npm run typecheck`.

## 5. Checks

Ruff and mypy 0 new; unit+contract against `tmp/be-integration/fail_ids.txt`; the PostgreSQL test on a fresh
database; four validators; `git diff --check`; security validator before the commit; mobile `npm test` and
typecheck. Implementation review (Sonnet 5.5 high). Then the mobile branch is merged into the integration branch and
the mobile checks join D2.

## 6. Limits

No sort index (per-account sets are small). A cursor reused with another filter seeks within that filter. "Hoàn tất"
not delivered (no route).

## 7. Review R1 findings and their fixes

| Finding | Fix |
|---|---|
| C3B-R1-01 (P2) error shape | §1 fact 2; C3B-2; §3 step 1 |
| C3B-R1-02 (P2) purge `profile_ref` | §1 fact 3; C3B-4/5; §3 step 3; tests |
| C3B-R1-03 (P2) profile check | §3 step 2 ownership-only query; tests |
| C3B-R1-04 (P2) offline tests | §3 step 5 offline block |
| C3B-R1-05 (P2) mobile tests to amend | §4 amended tests |
| C3B-R1-06 (P2) controller rewrite | §4 controller, module, availability |
| C3B-R1-07 (P2) test harness | §4 pure module, no new dependency |
| C3B-R1-08 (P3) basis | C3B-2, C3B-3 |
| C3B-R1-09 (P3) proposal, "Hoàn tất" | C3B-1, C3B-7 |
| C3B-R1-10 (P3) counts | §1 fact 6; §3 step 4 |
| C3B-R1-11 (P3) cursor | §3 step 1 |
| C3B-R1-12 (P3) collision | §1 fact 1 |
| C3B-R1-13 (P3) `ABANDONED` | §3 step 3 unit test |
| C3B-R1-14 (P3) seed and ties | §3 step 5 |
| C3B-R1-15 (P3) base | header |
| C3B-R1-16 (P3) types | §4 |
| C3B-R1-17 (P3) cancel copy | §4 screen |
| C3B-R1-18 (P3) copy validator | §4 source-text checks |
| C3B-R1-19 (P3) staleness | §4 controller note |
| C3B-R1-20 (P3) keys | §4 pure module |

## 8. Review R2 findings and their fixes

| Finding | Fix |
|---|---|
| C3B-R2-01 (P2) auto-422 | §3 step 1 and step 4: eight declared rows incl. 422; catalog set test |
| C3B-R2-02 (P3) ownership placement | §3 step 2: method on the profile lookup port; allowlist; 503 mapping |
| C3B-R2-03 (P3) offline details | §3 step 5 offline block |
| C3B-R2-04 (P3) mobile test wording | §4 amended tests |
| C3B-R2-05 (P3) `ParentExpoApp.tsx` | §4 allowlist note |
| C3B-R2-06 (P3) NULL `profile_ref` | §3 step 3 |
| C3B-R2-07 (P3) 202 handling | §4 local patch |
