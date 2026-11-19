# C6 part M9-B — first Teacher assignment, BE evidence (goal v2)

- **Date:** 2026-11-19. **Task:** the owner's added scope "C6 part M9-B" in
  `tmp/phase-bc/GOAL_V2_CONTINUATION_C4_C5_20261119.md`, under the goal v2 program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, SHA-256 `5DFC1EDE…4795F8`). Accepted by the goal; owner final check
  pending. Nothing pushed.
- **Plan:** `plan/PLAN_M9B_FIRST_TEACHER_ASSIGNMENT_DRAFT3_20261119.md` (SHA-256 `FF1C7A73…`). Reviews (Sonnet 5.5,
  effort high, fresh non-forked subagent, because starting a session is refused on these automated turns): Draft 1
  R1 NOT READY 0 / 6 / 11; Draft 2 R2 NOT READY 0 / 1 / 6; Draft 3 R3 READY WITH NOTES 0 / 0 / 3
  (`tmp/phase-bc/reviews/M9B_DRAFT1_REVIEW_R1.md`, `M9B_DRAFT2_REVIEW_R2.md`, `M9B_DRAFT3_REVIEW_R3.md`).
- **SRS:** repository copy 701,810 B (`443A3CA3…`, D-219 wording only); cited lines are the same as in the D-209 copy.

## Decisions (with SRS clauses)

| ID | Decision | Clause |
|---|---|---|
| O-3a | Candidates are identities with `state="active"`, `account_role="teacher"` and an active `teacher` row in the organization; the active row stands for the activated account of UC-13 (invitation flow not built, so candidates are existing or seeded Teachers) | UC-13 lines 1537–1546; UC-12 line 1530 |
| O-3b | Candidate fields `candidate_ref` (opaque `account_id`) and `display_name` only; the command accepts `candidate_ref` only (no subject, no identity creation) | NFR-02; §9.8; UC-13; §21.1 line 1637 |
| O-3c | M9-B covers a class without an active Teacher; reassignment and offboarding are UC-12, out of scope | UC-12 |
| O-3d | The command needs `If-Match` with the class assignment revision and an `Idempotency-Key`; stale → 409 `STALE_REVISION` with `current_version` and `ETag` | UC-12 line 1534; §21.4 lines 1697, 1699 |
| M9B-1 | 200 with `assignment_revision` | §21.2 line 1650 |
| M9B-2 | One active Teacher: 409 `CLASS_TEACHER_EXISTS` | line 1650; decision D-157 O3 |
| M9B-6 | OPEN-TECHNICAL choice: revision = 1 + teacher rows of the class (rows never deleted; a deactivation does not change it, so it serves this command only); receipts in `be1_command_receipts` (migration `20261119_ar_0002`, committed in `e9c9a815`, no new migration); eligibility by one locked query | §31.10(14); FR-T-02 |
| M9B-7 | Ineligible candidate → 404 `RESOURCE_NOT_FOUND` | §9.8 404 row |

The later O-3a/O-3b scope supersedes the "preserve AdultIdentity upsert and 409 `IDENTITY_ISSUER_MISMATCH`" part of
D-158 B1. The response changes 201 → 200 and drops `subject`, accepted for the local, undeployed BE-before-FE window
(CM-8). A candidate with an earlier inactive row for the same class gets 409 `RESOURCE_CONFLICT` (reassignment of a
removed Teacher needs a stored revision and belongs to UC-12).

## What changed

- `routers/be1_registry.py`: `GET /organizations/{organization_id}/teacher-candidates` (School Manager only;
  `limit_query()`; opaque cursor; `EXISTS` eligibility; display names from the identity provider); A07 items gain
  `assignment_revision` and `has_active_teacher` (one grouped query); the command: class read → authorization →
  `If-Match` → class `FOR UPDATE` → replay → revision → one-Teacher check → candidate `FOR SHARE` in one statement →
  insert (flush mapped to 409) → audit, event, receipt → commit; helpers `class_lock_select`,
  `candidate_lock_select`, `eligible_teachers_select`, `class_assignment_revision`.
- `schemas/be1_runtime.py`: `CreateAssignmentRequest {candidate_ref}`.
- `openapi_contract.py` (entry 200, inputs, body; key set +1), `openapi_contract_amendments.py` (two examples).
- Tests: new `tests/integration/test_m9b_first_assignment_postgres.py`; `test_m2_s1a_teacher_routes.py` (schema test,
  compile-level lock tests, missing-class test); catalog (153 operations, PR22 14, key set 17, body
  `{candidate_ref}`, candidate-route OpenAPI test) and composition tests; `test_be1_postgres_api.py` (eligible
  Teacher by `candidate_ref`); `test_m2_s1a_teacher_postgres.py` (fixture roles, race with two keys → one 200, one
  409 `STALE_REVISION`) — **edited, NOT RUN** (gate-only, `S1A_T_TEST_DATABASE_URL`);
  `tests/unit/test_be1_scope_guard_404_403.py` (handler signature; outside the plan allowlist).
- Plan Draft 3 still has two text lines that mention a reactivation (review R3-01); the code and tests are
  insert-only with 409 `RESOURCE_CONFLICT`. The pinned plan is not edited.

## Checks

- Fresh database `frc08_be1_acceptance_m9b_20261119174731` on `127.0.0.1:55458` (`alembic upgrade heads` exit 0):
  `test_m9b_first_assignment_postgres.py` 4 pass (candidates incl. 503 and 403/404; headers, stale, replay, key
  mismatch, `has_active_teacher` true/false, 403 for a Teacher caller, earlier inactive row → 409, ineligible → 404
  with no rows, concurrent commands behind a `Barrier`).
- `test_be1_postgres_api.py` on the same database: the BE1 route-count test now **passes** (54/59 → 55/60 as
  computed); the two known failures remain (canvas profile 409; consent 403, now after the rewritten assignment
  step).
- `pytest tests/unit tests/contract` (clean environment): 8,560 tests, 84 failing ids = the 83 baseline ids plus
  `test_be1_scope_guard_404_403::test_assign_class_teacher_missing_and_unassigned_class_look_the_same` (old handler
  signature). That test was updated and passes; it was not in the plan allowlist (deviation found by the full run).
  Focused re-run of the changed contract and unit files: pass.
- Ruff clean on the touched files; mypy: one pre-existing error on the unchanged router declaration.
- Implementation review (Sonnet 5.5 high, subagent): ACCEPTABLE WITH NOTES 0 / 0 / 6
  (`tmp/phase-bc/reviews/M9B_IMPL_REVIEW_R1.md`); R1-01 (Barrier), R1-02 (503, 403, active flag) and the web R1-03/04
  notes were applied.

## Limits

- Global `account_id` as `candidate_ref` lets two organizations correlate the same Teacher (opaque, not a provider id).
- Teachers created by a Platform Admin are not candidates until an organization Teacher row exists (UC-13 not built).
- Two candidates with the same display name cannot be told apart (no email allowed).
- A candidate disabled while the command waits on its lock is covered by the lock design only (not scripted).
- The derived revision counts every teacher row of the class, so a class-scoped Teacher row created another way (for
  example by the seed) also moves it.
- The key header follows C4 (`1–128` characters) and does not check the 33–126 character range of the C5 helper.
