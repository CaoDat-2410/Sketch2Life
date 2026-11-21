# V3 T-7d plan, Draft 1: enrollment move between classes (FR-T-05)

Date 2026-11-19. Goal v3b. Branch `feature/backend-srs-api-v3`, facts read at HEAD a076752d. Depends on T-7b (class revision column, `class_lock_any_state`, state vocabulary) and T-7c (profile create, same module). Status: plan review R1 passed (READY WITH NOTES, 0 P1 / 3 P2 / 10 P3, all applied); implemented at HEAD 34705cbf, implementation review pending. The plan body is a historical record: where it differs (line numbers, allowlist additions, rollback by explicit revision, the T-7d-DEC decisions), `evidence/notes/V3_T_7D_EVIDENCE_20261119.md` supersedes it. Source: Draft 5 WP-7 (route "TD-08"), TD-08, TD-28, AUD-T#7.
**Owner scope rule:** no capacity, subscription, quota, billing or payment code. SRS l.1896 ("chuyển lớp ... cần capacity") sits in the Billing capacity text; this task is the roster move of FR-T-05 and adds no capacity check (UC-03 l.1425: capacity does not block changes in an existing class). **Review rule: 2 reviews** (DDL, role guards across two classes, a new client contract).

## 1. HEAD facts

- No move exists. `be1_enrollments` (`20261014_0002_be1_runtime.py:66-75`, `be1_models.py:251-266`): `state IN ('active','withdrawn')`, **`uq_be1_enrollment UNIQUE (organization_id, class_id, child_id)`**; nothing enforces one active enrollment per child (REG l.102, l.248 and l.273 call for a partial unique index). Only `create_profile` writes enrollments (`be1_registry.py:794-800`).
- `be1_managed_profiles.class_id` is a NOT NULL FK and the "current class projection" (SRS l.830, l.1093: enrollment is the source, the projection is updated "in the same transaction").
- Other rows carry a class id: consents (`class_id`, `child_id`), synthetic proofs, session memberships (`SessionMembershipModel`, `be1_models.py:476`, states `join_pending/admitted/left/removed`, session states `configured/lobby/active/paused/finished`).

## 2. Decisions

| ID | Decision | SRS basis |
|---|---|---|
| D1 | Route `POST /api/be1/v1/classes/{class_id}/profiles/{child_id}/move` (`class_id` = source class, M9-B class-scoped shape; the org comes from the class row). Body `{"target_class_id": id, "target_class_revision": int >= 1}`; header `Idempotency-Key`; `If-Match: "<source class_revision>"`. TD-08 left the route open; this is the candidate, not an SRS path. | FR-T-05 l.544, l.1651 tree, l.1697, l.1699 |
| D2 | **Actor: the Teacher assigned to both classes.** The caller needs an active class-scoped `teacher` row for the source **and** the target class in the same organization (as `create_profile`: org-wide, guide and observer rows do not count). The School Manager gets 403: Manager roster writes and the references a Manager may hold are X-19 (D-066-69 O-PRIV: counts and opaque refs only; the Manager response to the roster is a count, so it cannot name a child). A Teacher naming a target class it is not assigned to gets the uniform 404. | l.1421, l.1709, l.2586, X-19 |
| D3 | **Close and keep:** the source enrollment becomes `withdrawn` (never deleted), a **new** enrollment row `active` is created in the target, `be1_managed_profiles.class_id` is set to the target, all in one transaction. A child can return to a class it left: history is `A withdrawn, B withdrawn, A active`. | l.544, l.1425, l.830, l.1093 |
| D4 | Both classes must be `active` (suspended and archived are read-only, T-7b D4): else 409 `INVALID_STATE_TRANSITION`. The child needs an active profile and an active enrollment in the source class; a profile without one is not auto-enrolled (l.1093 "quarantine"): 409 `INVALID_STATE_TRANSITION`. Unknown child in the source class: 404 `PROFILE_NOT_FOUND`. Same class: 400 `INVALID_REQUEST` (`target_class_id`, `INVALID_FORMAT`). | l.1093, l.1425 |
| D5 | **Revisions:** the source `If-Match` and the body `target_class_revision` are both checked (source first); stale -> 409 `STALE_REVISION` (`current_version` and ETag of the failing class). A successful move bumps **both** classes (T-7b D5). The response carries both new revisions; no `ETag` header (two resources). | l.1699, TD-28 |
| D6 | **Session guard (conservative, SRS silent):** refuse with 409 `INVALID_STATE_TRANSITION` while the child holds a membership in `join_pending` or `admitted` in a session of the source class whose state is not `finished`. Q-3. | integrity only |
| D7 | Consents, proofs and session history keep their old class id (history). A `REAL` profile that moves is no longer covered by a consent of the target class, so it stays blocked there until a consent is recorded for the target (the effective-consent lookup is class-scoped, `be1_common.py:263-285`); the consent model is X-19. | l.832, l.1096 |
| D8 | **DDL-H part 2** (section 4): replace `uq_be1_enrollment` by a partial unique index on active rows. Without it D3 cannot return a child to a former class. Fallback if the coordinator rules it out (Q-2): no migration, and a move into a class where the child already has a `withdrawn` row is refused with 409 `RESOURCE_CONFLICT`, a documented limit; the one-active rule is then held only by the class and profile row locks. | REG l.102, l.248, l.273 |

## 3. Route contract

| Route | Auth | Request | Success | Errors |
|---|---|---|---|---|
| `POST /api/be1/v1/classes/{class_id}/profiles/{child_id}/move` | Teacher, class-scoped `teacher` rows on both classes | as D1 | 200 `{"contract":"Be1ProfileMoveV1","child_id","from_class_id","to_class_id","enrollment_id","from_class_revision","to_class_revision"}` | 400 `INVALID_REQUEST`, `INVALID_IDEMPOTENCY_KEY`; 403 `ACTION_NOT_ALLOWED` (Manager); 404 uniform, `PROFILE_NOT_FOUND`; 409 `STALE_REVISION`, `INVALID_STATE_TRANSITION` |

No name, age or consent state in the body or the receipt. Catalog +1 operation (`DECLARED_OPERATION_COUNT` +1 on what has landed); schemas `MoveProfileRequest`, `Be1ProfileMoveV1`. No new error code.
**Order:** (1) source class by id (any state), missing -> 404; (2) `_require_m2_assignment(roles={"teacher"}, class_id=source)` and the class-scoped `teacher` row check -> 404 (`school_manager` account: 403); (3) key, `If-Match`, body validation (same class -> 400); (4) target class by id **in the same organization**, missing or another organization -> 404; the target authorization `teacher` row -> else the same 404; (5) lock both class rows `FOR UPDATE` in ascending `class_id` order (no deadlock between A->B and B->A), then the profile row `FOR UPDATE` (`organization, child_id, class_id == source, state active` else 404 `PROFILE_NOT_FOUND`); (6) receipt `(principal.subject, "POST /classes/{class_id}/profiles/{child_id}/move", key)`: same fingerprint -> stored body (references and revisions), other -> 400 `INVALID_IDEMPOTENCY_KEY`; (7) stale source, then stale target; (8) both active; active enrollment present; session guard; (9) write; (10) receipt; `commit`. Fingerprint: sha256 of `{target_class_id, target_class_revision, if_match}` plus the child id in the scope. Replay is re-authorized (steps 2 and 4) first.

**Write:** `UPDATE enrollment SET state='withdrawn'` (source row), `INSERT` new enrollment (`uuid4`, `created_by=principal.subject`), `profile.class_id = target`, `source.revision += 1`, `target.revision += 1`, `audit("profile.move", resource_type="child_profile", resource_id=child_id)`, `event(aggregate_id=child_id, event_type="be1.profile.moved.v1", payload={child_id, from_class_id, to_class_id})`. Order of the two enrollment writes: withdraw (flush), then insert, so the partial unique index never sees two active rows.

## 4. DDL-H part 2: migration `backend/alembic/versions/20261120_cls_0002_enrollment_active_unique.py`

`revision="20261120_cls_0002"` (17 chars), `down_revision="20261120_cls_0001"` (the T-7b migration, a single child; re-read `alembic heads` at implementation: if T-7b's id differs, use it), no label, no `depends_on`.
```
upgrade():
  op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM be1_enrollments WHERE state = 'active' "
             "GROUP BY organization_id, child_id HAVING count(*) > 1) THEN "
             "RAISE EXCEPTION 'DDL-H part 2: a child has several active enrollments'; "
             "END IF; END $$")
  op.drop_constraint("uq_be1_enrollment", "be1_enrollments", type_="unique")
  op.create_index("ix_be1_enrollment_class_child", "be1_enrollments",
                  ["organization_id", "class_id", "child_id"])
  op.create_index("uq_be1_enrollment_active", "be1_enrollments", ["organization_id", "child_id"],
                  unique=True, postgresql_where=sa.text("state = 'active'"))
downgrade():
  op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM be1_enrollments "
             "GROUP BY organization_id, class_id, child_id HAVING count(*) > 1) THEN "
             "RAISE EXCEPTION 'DDL-H part 2 downgrade refused: a child returned to a former class'; "
             "END IF; END $$")
  op.drop_index("uq_be1_enrollment_active", table_name="be1_enrollments")
  op.drop_index("ix_be1_enrollment_class_child", table_name="be1_enrollments")
  op.create_unique_constraint("uq_be1_enrollment", "be1_enrollments",
                              ["organization_id", "class_id", "child_id"])
```
Guards refuse; nothing is deleted. ORM mirror in `EnrollmentModel` (`be1_models.py:253-256`): the unique constraint is replaced by the two `Index` entries (`postgresql_where=text("state = 'active'")`); a unit test compares the index names, columns, uniqueness and WHERE text with the migration. Data effect: none (dev data has at most one enrollment per child; a violation fails the guard loudly). Pinned tests: `test_synthetic_eligibility.py:463` (graph count +1 again, heads (14, 10) stay), `test_m2_s2_g1_parent_story_postgres.py` `_EXPECTED_VERSION_ROWS` (`20261120_cls_0002` replaces the T-7b id; gate databases only: NOT CHECKABLE here). Round trip on a fresh database: up, down, up, then down refused after a return move.

## 5. Tests

Unit: schema; step order with a fake session; fingerprint; lock ordering helper (ascending ids). Contract: catalog row, headers, body schema, errors, route table (+1).
PostgreSQL (fresh database; harness of `test_m2_s1a_teacher_postgres.py:183-230` plus two classes with the same Teacher): move A->B: source enrollment `withdrawn` and kept, target `active`, `profile.class_id == B`, both revisions +1, audit and outbox rows, no name in the receipt; move B->A (needs the partial index) keeps three rows, one active; two concurrent moves of one child to different classes -> one 200, one 409 `STALE_REVISION`; A->B and B->A of two children at once -> no deadlock; same key replay; same key other body -> 400; stale source and stale target; suspended or archived source or target -> 409; Manager -> 403 and no child data; Teacher of A only (target not assigned), Teacher of B only, org-wide Teacher, foreign-organization Teacher and target in another organization -> one 404 body; unknown child -> `PROFILE_NOT_FOUND`; child in another class -> `PROFILE_NOT_FOUND`; profile without an enrollment -> 409; open session membership -> 409; consents and proofs untouched; DB rejects two active enrollments for one child (raw insert) and accepts a withdrawn plus an active one; migration round trip and downgrade refusal.
Existing tests touched: `test_synthetic_eligibility.py`, `test_m2_s2_g1_parent_story_postgres.py`, `test_openapi_contract_catalog.py` (**hot**), `test_app_composition.py`; `test_be1_postgres_api.py:893` and `test_seed_data.py` only run (no unique-constraint name is referenced in tests or src: grep of `uq_be1_enrollment` finds the model and the migration). Then unit+contract vs the 83-id base, PostgreSQL run, ruff and mypy on touched files, validators, `git diff --check`.

## 6. Allowlist

Under `backend/src/sketch2life/`: `interfaces/http/routers/be1_registry.py` (**hot**; or a new `routers/be1_roster_moves.py` mounted in `router_composition.py` if the file is too long: the implementer decides and records it), `contracts/schemas/be1_runtime.py`, `infrastructure/persistence/be1_models.py` (**hot**), `interfaces/http/openapi_contract.py` and `openapi_contract_amendments.py` (**hot**). New: the migration; tests `unit/test_enrollment_move.py`, `unit/test_enrollment_active_unique_ddl.py`, `contract/test_profile_move_route.py`, `integration/test_t7d_profile_move_postgres.py`; evidence `.../evidence/notes/V3_T_7D_EVIDENCE_20261119.md`. **Not touched:** `error_envelope.py`, consents, sessions, `core_store.py`, billing or capacity files, web, mobile, Bruno, DECISIONS and approval files.

## 7. FE, rollback, risks

Web Teacher roster: "move to class" for a class the Teacher also teaches, with both revisions from the class list. Rollback: revert the commit and `downgrade -1` (refused after a return move; keep the index then). Risks: two-class locking (ordered, tested); history rows keep the old class id (intended).

## 8. BLOCKED_OPEN and questions

- **Q-1 (SRS silent, X-19):** "Who may move a child between two classes that have different Teachers: the School Manager (l.1709 "quản trị roster"), the source Teacher, or both, and what may the Manager see to choose the child?" Built: Teacher of both classes only; cross-Teacher moves wait.
- **Q-2 (coordinator):** Does OD-01's "DDL-H" cover this second migration (D8)? Default yes (same package, roster uniqueness SRS asks for); no -> fallback in D8.
- **Q-3 (SRS silent):** "Must a move be refused while the child is in an unfinished session (D6)?" Default refuse.
- **Q-4 (SRS silent):** "May the target class need its own consent record before a `REAL` child is usable there (D7)?" The move does not check `data_origin` or the real-data flag; real rows stay blocked by the consent gate.
- Draft decisions from D-066-92 (route, actor rule, close-and-keep, partial index, session guard).
