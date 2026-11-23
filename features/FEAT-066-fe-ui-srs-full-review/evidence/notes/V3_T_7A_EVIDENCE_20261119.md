# V3 T-7a C-M1 School Manager roster summary - evidence note (2026-11-20)

Status: 2 reviews: plan R1 READY WITH NOTES + implementation R1 ACCEPTABLE WITH NOTES (0 P1 / 1 P2 / 8 P3); owner final check pending. Accepted by the goal under program approval after implementation review R1; stage 2 applied (section 10). Plan: `plan/V3_T_7A_PLAN_DRAFT1_20261119.md` (plan review R1: READY WITH NOTES, 0 P1 / 0 P2 / 9 P3, all applied below). Branch `feature/backend-srs-api-v3`, HEAD `2f6cd906` (contains T0.11, commit `f7ab272c`, and T0.9).

Review rule that applies: **2 reviews** (the plan review R1, which passed, plus ONE implementation review). Why: the task touches authorization and scope guards (Manager and Teacher roster reads, the session roster role set) and changes response contracts that the web app already calls (A07, A09, A10). It adds no migration or DDL.

Hard scope kept: no capacity, subscription, quota, billing or payment code and no `CLASS_CAPACITY_REACHED`; class create, B01/G01 and UC-12 are untouched.

## 1. What changed

Source (under `backend/src/sketch2life/interfaces/http/`):
- `api_conventions.py`: new shared cursor helper. `encode_cursor(scope, sort_key, item_id)` writes a compact, key-sorted JSON `{"i","k","s","v":1}` as unpadded base64url; `decode_cursor(cursor, scope)` and `decode_time_cursor(cursor, scope)` accept only ASCII, strict base64, exactly the four keys, `type(v) is int` and `v == 1`, `s == scope`, `1 <= len(i) <= 128`, a sort key of 1-64 characters (the time variant also needs a timezone-aware ISO timestamp). Stage 2 (review P2-1, P3-1): the id and the sort key must be printable ASCII (no NUL or control characters), and the cursor must equal `encode_cursor` of its own decoded parts (no base64 padding, no `+` or `/`, no re-spelled JSON); `decode_time_cursor` also requires the timestamp spelled as `datetime.isoformat` writes it (no `Z`, no space separator). Any failure is 400 `INVALID_REQUEST` with `field_errors` `[{"field":"cursor","code":"INVALID_FORMAT"}]`. New `cursor_query()` (`min_length=1`, `max_length=1024`) and `CURSOR_MAX_LENGTH`. The cursor is opaque and not signed; the scope binding only stops replay across routes, organizations and classes.
- `routers/be1_registry.py` (HEAD line numbers in brackets):
  - A07 `list_classes` [l.438]: `limit` (1-100, default 25) and `cursor`; order `(created_at, class_id)` ascending; keyset `tuple_(created_at, class_id) > (k, i)`; fetch `limit + 1`; `next_cursor` from the last returned row when a further row exists, else `null` (key always present). Scope `be1.classes:{organization_id}`. The Teacher scope filter (`allowed_class_ids` or org-wide) runs before paging. Items are unchanged.
  - A09 `list_profiles` [l.599]: T0.11's interim `roles` allow-list is removed. After the uniform scope check and `get_class`, a new `_roster_audience` helper answers `"manager"` for a `school_admin` row and `"teacher"` only for an active `teacher` row whose `class_id` equals the class; every other row (org-wide `teacher`, `guide`, `observer`) is 403 `ACTION_NOT_ALLOWED`. Manager: 200 `Be1ClassRosterSummaryV1` `{contract, class_id, active_profile_count}`, the count of `ManagedProfileModel` rows of the organization and class with `state == "active"`; no consent lookup and no audit row. Teacher: the `Be1ManagedProfileListV1` body, the consent gate, the 409 and the audit row are exactly as before; not paged.
  - A10 `list_consents` [l.885]: `limit`, `cursor`; order `(recorded_at, consent_id)` descending; keyset `tuple_ < (k, i)`; scope `be1.consents:{organization_id}:{class_id}`; the same `_roster_audience` rule. Manager: `Be1ConsentListManagerV1` with items `{consent_id, state, effective}` (no `child_id`, no `purpose_ref`), `effective` stays `false`. Teacher: `Be1ConsentListV1` with today's items plus `next_cursor`.
  - The pilot-profiles route [l.666] is unchanged (T0.11 already sets `roles={"teacher"}`); its Manager-403 tests stay.
- `routers/be1_sessions.py`: session roster [l.300] `roles={"school_admin","teacher"}` becomes `roles={"teacher"}`: the School Manager gets 403 `ACTION_NOT_ALLOWED` and no longer sees `child_id`, `display_name`, `device_grant_id`, group names or turns (closes T0.11 review P2-1; CM-2). `get_session` still runs first (existing 404 order).
- `openapi_contract.py` (catalog): `request_inputs` of A07 and A10 list `query limit` and `query cursor`. The 400 row already exists for every BE1 operation (the validation 400), so no new row was needed. No route is added: `DECLARED_OPERATION_COUNT` and `MOUNTED_OPERATION_COUNT` are unchanged.
- `openapi_contract_amendments.py`: examples of A07 and A10 gain `next_cursor: null` (published as `["string","null"]`); new `ALTERNATE_RESPONSE_EXAMPLES` and `_variant_schema`; `add_response_examples` publishes `{"type":"object","oneOf":[teacher body, manager body]}` for A09 and A10, each variant's `contract` an `enum` of its own name, with the existing `syntheticResponse` example plus one named manager example. `type: object` is kept beside `oneOf` so the existing catalog test (`response_schema.get("type") == "object"`) holds unchanged.

Frozen FEAT-063 and FEAT-047 documents (`openapi-runtime-frozen.json`, `openapi-client-projection-frozen.json`, `OPENAPI_FEAT063_REV45_20261101.json`, `API_CONTRACT.md`) are NOT edited. They now differ from the live OpenAPI for A07 (new parameters, `next_cursor`), A09 and A10 (`oneOf`, `next_cursor`); recorded drift, no frozen-file test failed (see §4).

## 2. SRS and owner decisions

| Decision | Basis |
|---|---|
| A07 and A10 are cursor lists: default 25, maximum 100, explicit deterministic order | SRS l.1640; D-066-75 CM-7 |
| A09 for the School Manager is a count only: no name, age, age band or `child_id`; no consent gate and no audit row | SRS l.2586 (Profile row, Manager "no profile contents by default"); D-066-69 O-PRIV; D-066-75 CM-3, CM-5 |
| A10 for the Manager has no `child_id` and no `purpose_ref` | D-066-75 CM-4 |
| Session roster refuses the School Manager | D-066-75 CM-2; T0.11 review R1 P2-1 |
| Full A09 fields and A10 Teacher items only for a `teacher` row of that class; org-wide `teacher`, `guide`, `observer` get 403; 404 stays for out-of-scope callers and for an unknown class (the class is read before the role rule) | D-066-75 CM-11; SRS l.863-865 (403 only inside a known scope) |
| AC-64 (l.2733) is child media only and is not cited for profile fields | plan §1, review R1 ruling 2 |
| Cursor decoding happens after the scope and role checks, so an out-of-scope caller gets the uniform 404 whatever the cursor says (the Query-level length check runs earlier in FastAPI, as on every route) | plan review R1 P3-2 |

Draft decisions of this task (not appended to `DECISIONS.md`, per program §1.5):
- **T-7a-DEC-1** cursor scope strings: `be1.classes:{organization_id}` and `be1.consents:{organization_id}:{class_id}`; T-7b may extend the class scope with its state filter.
- **T-7a-DEC-2** cursor parameter length 1-1024 (plan said 512; plan review R1 P3-5: the longest consent cursor with two 128-character ids is about 490 characters, too thin a margin). Unit test `test_longest_consent_cursor_fits_the_published_maximum`.
- **T-7a-DEC-3** A09 and A10 use `require_assignment` without a `roles` argument and decide the audience afterwards, so `get_class` (404 `CLASS_NOT_FOUND`) always runs before the 403. The plan's A10 text kept `roles={"school_admin","teacher"}`, which would answer a `guide` or `observer` asking for an unknown class with 403 before the class lookup. The visible result for known classes is the same.
- **T-7a-DEC-4** CM-10 amendment (plan review R1 P3-9; source plan OD-05 option b): the queue position of C-M1 BE moves from "after FR-C-08, SEED-1, PAY-0a to 0c" to goal v3b, ahead of PAY-0 and Billing B-1. Recorded here instead of in `DECISIONS.md`.
- **T-7a-DEC-5** OpenAPI publishes the two role bodies as `{"type":"object","oneOf":[...]}` with a per-variant `contract` enum and one named example each.
- **T-7a-DEC-6** A09 and A10 keep answering 404 `CLASS_NOT_FOUND` for a class that is not `active` (plan review R1 P3-8; `get_class` filters `state == "active"`, `be1_common.py:159-169`). Settled with the T-7b plan (`V3_T_7B_PLAN_DRAFT1_20261119.md` D8): T-7b changes `get_class` to `write=False` for reads (A09, A10, portfolio) with no state filter, so a Manager reads A09 and A10 of a suspended or archived class and a Teacher on an archived class gets the uniform 404. T-7a does not pre-empt it; until T-7b lands no archived class exists to list. T-7b also extends the A07 cursor scope with the state filter (`be1.classes:{org}:{state}`) and closes Q-1.

## 3. FE and client impact (no FE or Bruno file edited)

- Web `classService.ts`, `managerBusinessService.ts`, `ClassesPage.tsx`, the `RosterConsentPage.tsx` class picker: follow `next_cursor` ("load more"); the Manager roster reads `Be1ClassRosterSummaryV1` and shows the count only; the consent table reads `Be1ConsentListManagerV1` (no purpose column); labels `pending`, `revoked` (CM-6).
- Web `shared/api/backendApi.tsx`, `T05ClassesScreen.tsx`, `TeacherWorkbenchPage.tsx`: follow `next_cursor` to the end for classes and consents (they join consents to profiles and look a class up by id).
- BE-before-FE window (CM-8, local development only): Teacher screens see only the first 25 classes and consents; `RosterConsentPage` breaks on the summary body (it already shows the refusal line after T0.11). Mobile has no caller.
- Bruno 012 (class roster) and 050 (session roster), and the pilot-profiles variants, must expect the summary and the 403s. `.worktrees/bruno-next` was NOT touched; this is a handoff to the Bruno tasks (decisions 86-89, relayed by the coordinator).

## 4. Tests and checks (real results)

Plan review R1 conditions on the base-test repair (P3-6): the repair was done in this order. (1) Before editing the test, it was run at the new code state and failed exactly as at base: the first `POST .../profiles` as the School Manager got 403 `ACTION_NOT_ALLOWED`, expected 201 (`tmp/phase-v3/T_7A/repair_base_run.txt`). (2) The only change then made was the actor swap: profile create and the A09 reads run as the class-scoped Teacher the test already builds (`app.dependency_overrides[get_verified_adult]` swapped, then the Manager override restored for the later steps). (3) The test then passed without any other change; no further failure appeared and the repair stayed inside what the approved package lists. The 409 `CONSENT_NOT_EFFECTIVE` for the Teacher, the admission 409, the `start` 409, the device-canvas 401, the stored consent, enrollment and grant rows, the audit row and the outbox row assertions are kept; added: the Manager A09 call returns exactly the summary, "Synthetic Child" does not appear in it, and the `profile.list` audit count is unchanged by the Manager call. **This test leaves the PostgreSQL known-failing set of the context pack ("BE1 consent 403 test").**

Existing tests changed:
- `tests/unit/test_be1_scope_guard_404_403.py`: the two T0.11 Manager 403 tests of the class profile list (`test_t011_list_profiles_school_manager_is_403`, `test_t011_list_profiles_school_manager_with_class_row_is_403`) become one parametrised `test_t7a_list_profiles_school_manager_gets_the_count_summary` (org-wide and class-scoped row); the guide and observer cases keep reaching `get_class` (404 `CLASS_NOT_FOUND`) because the class lookup comes first. The pilot-profiles Manager-403 tests stay.
- `tests/integration/test_be1_synthetic_pilot_postgres.py` (T0.11's Manager class-roster case): `test_t011_school_manager_is_refused_on_class_profile_list` becomes `test_t011_school_manager_gets_the_count_summary_on_class_profile_list` (200 summary, count 0 then 1, no child fields; unknown class 404; unknown organization 404). The pilot-profiles Manager-403 PostgreSQL test stays.
- `tests/integration/test_be1_postgres_api.py::test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas`: repaired as above.
- `tests/contract/test_openapi_contract_catalog.py` (hot): two new tests, `test_t7a_class_and_consent_lists_publish_paging` (limit default 25, minimum 1, maximum 100; optional `cursor`; the 400 row; `next_cursor` required and nullable) and `test_t7a_roster_and_consent_reads_publish_both_role_bodies` (`oneOf` variants, `contract` enums, two named examples, manager item keys).

New tests: `tests/unit/test_api_conventions_cursor.py`, `tests/unit/test_be1_roster_privacy_guards.py` (own fake session that answers each query by its table, per plan review R1 P3-3), `tests/integration/test_t7a_roster_privacy_postgres.py` (16 cases: Manager summary with count 2 of 3 profiles and no audit row; class-scoped Teacher 200 on an empty class and 409 with its audit row on a non-empty class; org-wide teacher, org-wide and class-scoped guide and observer 403 on A09 and A10; foreign Teacher, foreign Manager, other-class Teacher and unknown organization one uniform 404 body, unknown class 404 for everyone; Manager A10 without `child_id` and `purpose_ref`, Teacher A10 unchanged; A10 newest first and stable for equal timestamps with limits 1 and 2; bad, foreign-scope, other-class and wrong-route cursors 400 and scope checks first; A07 walk over 6 classes with a tie on `created_at`, with a class inserted between pages; default page 25 of 26; limit 0, 101, -1 and empty cursor 400; foreign-organization and consents cursors 400; Teacher scope filter before paging; session roster Manager 403, class-scoped Teacher 200 with the unchanged key set, foreign and other-class 404, class guide 403).

Unit and contract, changed or new files (clean env, only `PYTHONPATH`): `test_api_conventions_cursor.py` (34 cases after stage 2; 24 before), `test_be1_roster_privacy_guards.py` (22 cases), `test_be1_scope_guard_404_403.py` (22) and `test_openapi_contract_catalog.py` (9 tests, two new) all pass.

PostgreSQL (fresh database below, `alembic upgrade heads`): files `test_t7a_roster_privacy_postgres.py` (16), `test_be1_postgres_api.py` (4), `test_be1_synthetic_pilot_postgres.py` (121), `test_m9b_first_assignment_postgres.py` (4): 145 tests, 144 passed, 1 failed, 0 skipped (junit `tmp/phase-v3/T_7A/junit_pg2.xml`). The one failure is `test_be1_postgres_api.py::test_room_code_start_revocation_stage_and_early_outcome_are_durable` (canvas 409 `CANVAS_PROFILE_MISMATCH` at the drawing step), the context pack's known-failing "BE1 canvas 409 test"; it also failed in the first run (`junit_pg.xml`) and is not touched by this task. The first run (`junit_pg.xml`) showed one more failure, `test_t011_school_manager_is_refused_on_class_profile_list`, which asserted the interim 403 that this task replaces; it was flipped (see above) and passes. The repaired consent test passes (it left the known-failing set).

Full unit+contract run in a clean env (no DB variables), junit `tmp/phase-v3/T_7A/junit_uc.xml`: 9365 test cases, 65 failed, 18 errors (collection), 26 skipped. The 83 failing ids equal the 83-id base list (`tmp/be-integration/fail_ids.txt`) exactly: **0 new failures**, 0 fixed.

Static checks: `ruff check` on the touched source files (`api_conventions.py`, `be1_registry.py`, `be1_sessions.py`, `openapi_contract_amendments.py`, `openapi_contract.py`) and the three new test files: 0 findings. On the edited test files (`test_openapi_contract_catalog.py`, `test_be1_postgres_api.py`, `test_be1_synthetic_pilot_postgres.py`, `test_be1_scope_guard_404_403.py`) only the pre-existing import-order `I001` findings remain (none in lines this task added); counts equal HEAD. `mypy` on the five touched source files: 8 errors, the same 8 as at HEAD (review P3-5 corrected the first count of 7: `openapi_contract.py` line 11784 (HEAD 11772, the generated catalog), `openapi_contract_amendments.py` lines 992-998 and 1487 in `_schema_for_example` and `published_responses`, and the `APIRouter(responses=...)` argument in `be1_registry.py` and `be1_sessions.py`), 0 new; the three new test files: 0 errors. Stage 2 re-run: the same 8, 0 new.

Validators (worktree root, separate commands): `validate_harness.py` HARNESS_VALID; `validate_repository_security.py` REPOSITORY_SECURITY_VALID; `validate_architecture.py` valid; `git diff --check` clean (exit 0). New files were checked with a byte check: no CR, no trailing whitespace, final newline. `validate_skeleton.py` was run for information only (no structure change); its known Android applicationId failure is not this task's.

## 5. Databases created

- `frc08_v3_t7a_20261120181725_be1_acceptance` (fresh, migrated with `alembic upgrade heads`, never dropped). Name contains `be1_acceptance` because the BE1 PostgreSQL harnesses require it.
- `frc08_v3_t7as2_20261120185108_be1_acceptance` (stage 2 re-run, fresh, migrated, never dropped).
- The implementation reviewer created `frc08_v3_t7arev_20261120183922_be1_acceptance` (never dropped).

## 6. Files

Changed (`git status --short`):
- `backend/src/sketch2life/interfaces/http/api_conventions.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py`
- `backend/tests/contract/test_openapi_contract_catalog.py`
- `backend/tests/integration/test_be1_postgres_api.py`
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
- `backend/tests/unit/test_be1_scope_guard_404_403.py`

New:
- `backend/tests/unit/test_api_conventions_cursor.py`
- `backend/tests/unit/test_be1_roster_privacy_guards.py`
- `backend/tests/integration/test_t7a_roster_privacy_postgres.py`
- `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/V3_T_7A_EVIDENCE_20261119.md` (this note)

The plan file `plan/V3_T_7A_PLAN_DRAFT1_20261119.md` is untracked and unchanged; it goes into the commit with the task. Other untracked plan files are left alone. Scratch and logs: `tmp/phase-v3/T_7A/`.

## 7. Deviations from the plan, the package and the allowlist

- (a) The base moved from `2dddc607` to HEAD `2f6cd906`; all line numbers were re-pinned (HEAD numbers are in §1). T0.11 and T0.9 are in HEAD, so no working-tree baseline problem remains (review P3-1).
- (b) CM-9 branch policy (`feature/feat066-cm1`) is replaced by the goal program approval; CM-9 and R-14 are moot.
- (c) T0.11 already did CM-2 for pilot-profiles and an interim class-roster 403; T-7a replaces the interim 403 with the Manager summary.
- (d) The session-roster 403 is closed here (T0.11 review P2-1).
- (e) Bruno 012 and 050 from the package allowlist are left to decisions 86-89 (handoff in §3; `.worktrees/bruno-next` untouched). Review P3-7.
- (f) The package's "required PostgreSQL cases run by the owner" run here on the goal's fresh database. Review P3-7.
- (g) Cursor length 1024 instead of 512 (T-7a-DEC-2); A09 and A10 without a `roles` argument (T-7a-DEC-3). Allowlist files outside the plan text: `tests/integration/test_be1_synthetic_pilot_postgres.py` is named in the plan (T0.11's Manager class-roster case only); no other file outside the allowlist was edited. `contracts/schemas/be1_runtime.py` (optional) was not touched: the handlers return dicts.
- (h) A09 and A10 for archived or suspended classes: T-7a-DEC-6 (settled with T-7b D8).

## 8. Parked and open items (none blocks)

- Q-1 (A07 for a Teacher with an org-wide `teacher` row still lists every class): unchanged here; T-7b plan D7 closes it.
- **OWNER-VISIBLE OPEN ITEM, Q-2** (CM-11 is not applied to the session roster and pilot-profiles): an org-wide `teacher` row still reads child `display_name` and `age_months` through pilot-profiles and child names, `child_id` and `device_grant_id` through the session roster. This is a gap against SRS l.2586 (the Teacher reads profile fields after accepting the invitation and being assigned to the class), recorded and accepted by implementation review R1 only as a residual (its P3-3), not as a closed risk. It needs an owner word or a later task (T-7b or a CM-11 extension: a class-row check like `_roster_audience` on those two routes). Until then the Manager is private but an org-wide Teacher can read the same names one route over.
- Q-3 (consent writes still echo `child_id` and `purpose_ref` to a Manager, MGR-5, X-16 debt): unchanged. The D-066-75 debt list (canvas, artifacts, gallery, observations, portfolio, session `configuration`, `teacher_note`, group `display_name`, pilot assistance list, consent-write echoes) is unchanged.
- Q-4 (guide and observer lose A09, CM-11): a stated behaviour change; no web caller per the package reviews and no mobile caller found in `apps/ui-mobile/src` and `apps/mobile/src`.
- Concurrency residual (review P3-4): `created_at` and `recorded_at` come from `server_default=func.now()`, the transaction start time. A row committed after page 1 but from a transaction that started earlier than the cursor key can sort before the cursor and be skipped. "A class inserted between pages neither duplicates nor skips" holds for normal inserts and for the test, not as a general guarantee.
- Index (review P3-9): no performance index was added. A07's query filters on organization and state and can use `ix_be1_class_org_state`; the consents query filters on organization and class and uses only the `organization_id` prefix of `ix_be1_consent_child` (`(organization_id, child_id, state)`). Acceptable at pilot scale; a performance index would be a separate DDL task.
- `be1_models.py` (hot) is not touched; no DDL.

## 9. Rollback

Revert the single local commit: no data, DDL or flag. `next_cursor` is additive; the visible changes are the Manager bodies of A09 and A10, the new 403s (org-wide `teacher`, `guide`, `observer` on A09 and A10; Manager on the session roster) and the first-page limit of 25 on A07 and A10 (risk R-17 and the BE-before-FE window of CM-8).

## 10. Implementation review R1 and stage 2 (ACCEPTABLE WITH NOTES: 0 P1, 1 P2, 8 P3; reviewer Sonnet 5.5 high)

Handled in one pass (review cap: each review once):
- **P2-1 (NUL in cursor gave 503) - fixed.** `decode_cursor` rejects any id or sort key that is not printable ASCII and requires the canonical re-encoding; `decode_time_cursor` requires the `isoformat` spelling. Unit: `test_api_conventions_cursor.py` adds NUL, newline, DEL, non-ASCII (id and key), canonical-only, standard-alphabet and `Z`/space-timestamp cases (10 new cases, 34 total). PostgreSQL: `test_crafted_cursors_with_nul_or_noncanonical_form_are_400_not_503` (NUL in id and key, non-ASCII, `Z` timestamp, padded genuine cursor; on A07 and A10 as the Manager: 400 `INVALID_REQUEST` with `field_errors` cursor/`INVALID_FORMAT`, never 503). The old `_decode_candidate_cursor` (`be1_registry.py`) has the same gap but is outside this allowlist; left as debt.
- **P3-1 (non-canonical base64 accepted) - fixed** by the same canonical re-encoding check.
- **P3-5 (mypy count) - fixed** (8, equal to HEAD; section 4). `ruff format` is not enforced by the repository: not applied, so no unrelated reformatting enters the diff.
- **P3-7 (plan contradicts implementation) - fixed** with a supersession header in the plan file pointing to section 2 (T-7a-DEC-2, T-7a-DEC-3).
- **P3-6 (FE must read `contract` first) - recorded:** the FE slice must read `contract` first to choose the body of A09 and A10, and A09 is not paged (no `next_cursor`). Add to the FE handoff in section 3.
- **P3-2 (cursor not signed, leaks the last row's sort time) - debt:** T-7b and T-7c must not reuse the helper for a list whose scope filter runs after paging; the timestamp is not child data.
- **P3-3 (Q-2) - OWNER-VISIBLE open item, section 8.**
- **P3-4 (A07 lists classes that A09 and A10 refuse for an org-wide Teacher) - debt:** T-7b D7 owns it; the FE note: an org-wide Teacher gets 403 on a class they can list.
- **P3-8 (scratch paths) - no action** beyond P3-5 (the evidence cites `tmp/phase-v3/T_7A/` and `t_7a/` scratch; not versioned).

Stage 2 re-runs (databases and logs in section 5; logs under `tmp/phase-v3/t_7a/`):
- PostgreSQL on `frc08_v3_t7as2_20261120185108_be1_acceptance` (`test_t7a_roster_privacy_postgres.py`, `test_be1_postgres_api.py`, `test_be1_synthetic_pilot_postgres.py`, `test_m9b_first_assignment_postgres.py`): 146 tests, 145 passed, 1 failed, 0 skipped, 0 errors (junit `junit_pg_s2.xml`). The one failure is the known-base `test_room_code_start_revocation_stage_and_early_outcome_are_durable` (canvas 409 `CANVAS_PROFILE_MISMATCH`), unchanged. The new `test_crafted_cursors_with_nul_or_noncanonical_form_are_400_not_503` passes (the new PG file now has 17 cases).
- Unit and contract, touched files: `test_api_conventions_cursor.py` 34/34, `test_be1_roster_privacy_guards.py`, `test_be1_scope_guard_404_403.py`, `test_openapi_contract_catalog.py` all pass.
- Full unit+contract, clean env (only `PYTHONPATH`), junit `junit_uc_s2.xml`: 9365 test cases, 65 failed, 18 collection errors, 26 skipped. The 83 failing ids equal the 83-id base list: **0 new failures**.
- `ruff check` on the five touched source files and the three new test files: all checks passed. `mypy`: 8 errors in the touched source files, equal to HEAD; new test files 0.
- Validators, separate commands at the worktree root: `validate_harness.py` exit 0, `validate_repository_security.py` exit 0, `validate_architecture.py` exit 0, `git diff --check` exit 0; byte check of all changed and new files (no CR, no trailing whitespace, final newline). `validate_skeleton.py` not run (no structure change). The security validator is run once more after the last edit of this note, before the commit.
