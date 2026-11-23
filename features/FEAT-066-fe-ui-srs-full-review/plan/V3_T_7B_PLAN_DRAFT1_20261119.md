# V3 T-7b plan, Draft 1: class state (archive, manual suspend), state filter, class revision

> **Superseded in part by `evidence/notes/V3_T_7B_EVIDENCE_20261119.md`** (plan review R1 rulings and implementation review R1 fix pass applied there): the rollback is `alembic downgrade 20261119_oc_0001` (explicit target, not `-1`), the any-state lock is `class_lock_select` (no `class_lock_any_state`), the suspend-versus-assign race answers 409 (not 404), an organization-wide teacher-family row no longer lists every class, and the session lifecycle is guarded (T-7b-DEC-13). Where this draft and the evidence note differ, the evidence note rules.

Date 2026-11-19. Goal v3b. Branch `feature/backend-srs-api-v3`, facts read at HEAD a076752d. T-7a (C-M1, `V3_T_7A_PLAN_DRAFT1_20261119.md` + review R1) lands first and rewrites the A07 handler: `be1_registry.py` line numbers below are HEAD numbers, re-pinned at implementation. Status: plan, not implemented, not reviewed. Source: BE API plan Draft 5 WP-7, TD-08, TD-28, P-14a/b, DDL-H.
**Owner scope rule:** no capacity, subscription, quota, billing or payment code; no `CLASS_CAPACITY_REACHED`. A downgrade-driven suspension (FR-B-07 l.593, l.1849) is X-13: not built, no suspension reason stored. **Review rule: 2 reviews** (DDL, role guards, a list contract the web uses).

## 1. Findings that change Draft 5

- **No class-state CHECK exists.** DDL-H assumed one on the class table (`20261014_0002_be1_runtime.py:149`); that line is the CHECK of `be1_session_groups` (l.143-153). `be1_classrooms` (l.40-48) and `ClassroomModel` (`be1_models.py:124-142`) have `state varchar(24) DEFAULT 'active'` and no CHECK, so `suspended` is storable today: **TD-08 needs no DDL**. A fixture already writes `state="locked"` on a class (`test_auth_me_scope_postgres.py:137`), so a new CHECK is not added.
- Every class read filters `state == "active"` (`be1_common.get_class` l.159-169; `be1_registry.py:120, 323, 448, 762`; `account_scope.py:146`): a suspended class would be unreadable. A read/write split is needed.
- T-3a already refuses an occurrence create on a non-active class with 409 `INVALID_STATE_TRANSITION` (`lesson_occurrences/service.py:230`) and takes `FOR SHARE` on the class (`scope.py:142`). T-7b follows both.

## 2. Decisions

| ID | Decision | SRS basis |
|---|---|---|
| D1 | One command per state change: `POST /api/be1/v1/classes/{class_id}/suspend` and `.../archive` (class-scoped like M9-B `.../assignments`; org from the class row). Actor: School Manager only. | l.1709, l.1697, TD-08 default |
| D2 | States `active`, `suspended`, `archived`. `suspended` is **not** mapped to `locked`: `locked` is no SRS class term (l.1461, l.1709, FR-B-07 say "tạm ngưng"). | l.1461, l.593, l.842 |
| D3 | Transitions `active->suspended`, `active->archived`, `suspended->archived`; `archived` terminal; any other pair (also the same state again) 409 `INVALID_STATE_TRANSITION`. **No reactivate or unarchive**: l.1896 says reactivation needs capacity (X-13). | l.866, l.1896 |
| D4 | Suspended is read-only (reads stay, writes refused). **Archived read-only too: an inference** (UC-03/UC-06 name suspended only). Write on a non-active class: 409 `INVALID_STATE_TRANSITION` (as T-3a). | l.1425, l.1461, l.593 |
| D5 | **TD-28: the "expected class revision" (l.1651) is a new stored counter `be1_classrooms.revision`**, start 1, `+1` on a state change, a Teacher assignment (T-7b edits `assign_class_teacher`) and an enrollment move out or in (T-7d). Profile create does not bump it (T-7c D2). `assignment_revision` (1 + teacher rows, `be1_registry.py:82`) is unchanged and stays the token of l.1650. | l.1651, l.1699, TD-28 |
| D6 | **DDL-H = the revision column** (section 4); Draft 5's state CHECK is not needed. Fallback if the coordinator rules it out: the counter is `core_aggregate_revisions` for aggregate `class_id` (bumped via `event(revision=...)`, plus a class event in `assign_class_teacher`); no migration. Q-1. | OD-01, program §1.4 |
| D7 | List filter `state=active\|suspended\|archived\|all`, default `active` (today). Manager: any value. Teacher: only classes with a class-scoped Teacher row, states `active` and `suspended` only (`archived` alone gives an empty page). **Closes T-7a Q-1**: an org-wide `teacher` row (a membership marker, `be1_registry.py:87`) no longer lists every class. Items gain `class_revision`; the T-7a cursor scope gets the filter (`be1.classes:{org}:{state}`). | l.796, l.1640, l.1708, l.2586, P-14b |
| D8 | `be1_common.get_class(db, org, class_id, *, write=True)`: no state filter; missing 404 `CLASS_NOT_FOUND`; `write` and not active 409. Reads (A09, A10, portfolio) pass `write=False`; a Teacher on an `archived` class gets the uniform 404. Switched to write: `create_session` (`be1_sessions.py:209`), `create_observation` (`be1_records.py:338`), `record_consent` (no class check today). **`revoke_consent` stays allowed** (consent withdrawal; SRS silent). | D4, l.502 |
| D9 | Unchanged: `/v1/me` scope (`account_scope.py:146`, pinned), running sessions of a later-suspended class, `create_class`. Residual, Q-3/Q-4. | |

## 3. Routes and authorization

| Route | Request | Success | Errors |
|---|---|---|---|
| `POST .../classes/{class_id}/suspend` and `/archive` | `Idempotency-Key` (1-128), `If-Match: "<class_revision>"`, no body | 200 `{"contract":"Be1ClassStateV1","class_id","state","class_revision"}`, `ETag` | 400 `INVALID_REQUEST`; 400 `INVALID_IDEMPOTENCY_KEY`; 403 `ACTION_NOT_ALLOWED`; 404; 409 `STALE_REVISION` (+`current_version`, ETag); 409 `INVALID_STATE_TRANSITION` |
| `GET .../organizations/{org}/classes?state=` (T-7a handler) | `state`, `limit`, `cursor` | items add `class_revision` | 400 bad `state` |

The body has no name, age, child reference or count. Catalog +2 operations (`DECLARED_OPERATION_COUNT` +2 on what has landed).
**Order** (mirrors `assign_class_teacher`, l.307-434): (1) class by id, no state filter, missing -> uniform 404; (2) `_require_m2_assignment(roles={"school_admin"}, class_id)`: unassigned, other organization, Parent, Platform Admin, inactive -> one 404 body; a Teacher account assigned in the organization (class-scoped or org-wide row) -> 403 (resource known, role refused, l.864-865); (3) key and strong `If-Match`; (4) `FOR UPDATE` on the class row, any state (new `class_lock_any_state`; `class_lock_select` filters `active` and stays for assign); (5) receipt `(principal.subject, "POST /classes/{class_id}/suspend", key)`: same fingerprint -> stored body, other -> 400 `INVALID_IDEMPOTENCY_KEY`; (6) `If-Match != revision` -> 409 `STALE_REVISION`; (7) transition check; (8) write. Fingerprint sha256 of `{"command","if_match"}`. The receipt stores class id, state, revision only (receipt rule `be1_models.py:69-74`); replay is re-authorized first.

## 4. Writes and DDL-H

One transaction: `state`, `revision += 1`, `audit("class.suspend"|"class.archive")`, `event(aggregate_id=class_id, event_type="be1.class.suspended.v1"|"be1.class.archived.v1", payload={class_id, from_state, to_state}, revision=classroom.revision)`, receipt, `commit`; `IntegrityError` on the receipt key -> rollback and replay (as `create_class` l.579-594). `assign_class_teacher` gets one line, `classroom.revision += 1`, on the row it already locks (response unchanged).

**Migration** `backend/alembic/versions/20261120_cls_0001_class_revision.py`: `revision="20261120_cls_0001"` (17 chars), `down_revision="20261119_oc_0001"`, no label, no `depends_on`. Parent: `alembic heads` shows the lesson_library chain ending at `20261119_oc_0001` (`ar_0001 -> ar_0002 -> uf_0001 -> oc_0001`; T-3b/c/d add no migration; T-2c and T-1a use the separate Story chain). Re-read `alembic heads` at implementation.
```
upgrade():   op.add_column("be1_classrooms", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
             op.create_check_constraint("ck_be1_class_revision", "be1_classrooms", "revision > 0")
downgrade(): op.drop_constraint("ck_be1_class_revision", "be1_classrooms", type_="check")
             op.drop_column("be1_classrooms", "revision")
```
No backfill (existing classes start at 1; constant default is metadata-only). Downgrade loses the counter: after T-7c/T-7d ship it needs the code revert too. ORM mirror in `be1_models.py` (`default=1, server_default="1"`, same CHECK text).
Pinned tests: `test_synthetic_eligibility.py:463` (graph count 35 -> current+1; head counts (14, 10) stay), `test_m2_s2_g1_parent_story_postgres.py` `_EXPECTED_VERSION_ROWS` (`20261120_cls_0001` replaces `20261119_oc_0001`; gate databases only: NOT CHECKABLE here); `test_lesson_occurrence_ddl.py` keeps passing. New `test_class_revision_ddl.py` (chain, single child, CHECK text equals ORM, no `create_table`, up/down mirror) and a round trip `upgrade heads -> downgrade -1 -> upgrade heads` on a fresh database (never drop).

## 5. Tests

Unit (fake-session pattern of `test_be1_scope_guard_404_403.py`): all 3x3 transitions; `get_class` read/write matrix; Teacher visibility; 404 before 403; stale before transition. Contract: catalog rows, `state` parameter, `class_revision` on items, route table (+2).
PostgreSQL (fresh database, `be1_acceptance` in the name if the harness needs it; harness of `test_t01_create_class_postgres.py`): both commands with ETag; replay (one audit row, one outbox row); same key other `If-Match` -> 400; concurrent same key -> one transition; two keys -> one 200, one 409; suspend racing `assign_class_teacher` serializes (the loser gets `STALE_REVISION`); every refused pair; Teacher (class-scoped, org-wide, guide), Parent, foreign Manager, unknown id -> 403/404, one 404 body; list filter per role and state; cursor of another filter -> 400; suspended class: A09 and A10 readable, `create_session`, `create_observation`, `record_consent`, occurrence create refused 409, `revoke_consent` works; archived class hidden from the Teacher, visible to the Manager with `state=all`; migration round trip.
Existing tests that change: `test_m2_s1a_teacher_routes.py` (assign fake gets a `revision`), `test_openapi_contract_catalog.py` (hot), `test_app_composition.py`, `test_be1_scope_guard_404_403.py` (`get_class` signature), T-7a's A07 tests, `test_m9b_first_assignment_postgres.py` (class revision moves with an assignment; `assignment_revision` assertions stay), the two migration pins. No test lists classes as an org-wide Teacher (every GET caller is the Manager). Then: unit+contract vs the 83-id base, PostgreSQL run, ruff and mypy on touched files, validators, `git diff --check`.

## 6. Allowlist

Under `backend/src/sketch2life/`: `interfaces/http/routers/be1_registry.py` (**hot**), `routers/be1_common.py`, `routers/be1_records.py`, `routers/be1_sessions.py` (one call), `infrastructure/persistence/be1_models.py` (**hot**), `interfaces/http/openapi_contract.py` and `openapi_contract_amendments.py` (**hot**), optional `contracts/schemas/be1_runtime.py`. New: the migration; tests `unit/test_class_revision_ddl.py`, `unit/test_class_state_machine.py`, `contract/test_class_state_routes.py`, `integration/test_t7b_class_state_postgres.py`; evidence `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/V3_T_7B_EVIDENCE_20261119.md`. **Not touched:** `error_envelope.py` (existing codes only), `account_scope.py`, billing or capacity files, web, mobile, Bruno, DECISIONS and approval files.

## 7. FE, rollback, risks

Web `classService.ts`/`ClassesPage.tsx`: `state` filter and badge, archive and suspend buttons (Manager), `class_revision` as `If-Match`; no reactivate button. Rollback: revert the commit, `downgrade -1`; no flag. Risks: A07 handler shared with T-7a (strictly after it); org-wide-row Teachers lose classes in the list (intended); `/v1/me` still hides suspended classes (Q-4).

## 8. BLOCKED_OPEN and coordinator questions

- **Q-1 (coordinator, before the migration file):** Does OD-01's "DDL-H" cover the revision column (D6) instead of the state CHECK in Draft 5? Default yes; no -> aggregate-revision fallback.
- **Q-2 (SRS silent):** "May a School Manager reactivate a manually suspended class or unarchive one, with which verb, and is a capacity check required (l.1896)?" Not built.
- **Q-3 (SRS silent):** "Must suspending or archiving a class refuse or close a session of that class in lobby, active or paused?" Default: no check.
- **Q-4 (SRS silent):** "Should a Teacher's `/v1/me` granted scope keep listing a suspended class (read-only), as l.1425 and l.1461 imply?" Default: unchanged (T0.2 contract).
- Draft decisions for the evidence note start at D-066-92 (state vocabulary, archived inference, revision counter, Teacher list rule, `revoke_consent` not blocked).
