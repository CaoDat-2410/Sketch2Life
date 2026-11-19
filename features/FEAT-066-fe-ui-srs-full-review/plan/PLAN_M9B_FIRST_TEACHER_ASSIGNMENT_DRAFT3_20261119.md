# FEAT-066 C6 part M9-B — first Teacher assignment (Draft 3, goal v2)

- **Status:** DRAFT for independent review (round 3, the last under D-171). Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, SHA-256 `5DFC1EDE…4795F8`) and the owner's added scope "C6 part
  M9-B" (`tmp/phase-bc/GOAL_V2_CONTINUATION_C4_C5_20261119.md`). No code before READY (WITH NOTES).
- **Supersedes:** Draft 2 (`PLAN_M9B_FIRST_TEACHER_ASSIGNMENT_DRAFT2_20261119.md`, SHA-256 `8F4C5744…`; review R2
  NOT READY 0 P1 / 1 P2 / 6 P3, `tmp/phase-bc/reviews/M9B_DRAFT2_REVIEW_R2.md`) and Draft 1 (`AFE49669…`; R1 NOT
  READY 0 / 6 / 11). §7 maps R1, §8 maps R2.
- **Base:** BE `feature/feat066-be-integration` at `e9c9a815` (C5 committed: table `be1_command_receipts`, Alembic
  head `20261119_ar_0002` is a prerequisite); web `codex/fe-ui-web-remediation` at `5cf800b6`.
- **SRS:** the repository copy is now 701,810 B (SHA-256 `443A3CA3…`, D-219 delete wording only); every line cited
  here is unchanged from the D-209 copy (701,157 B).
- **Order:** the owner's added scope runs M9-B now, before C-M1 FE and without an MGR-3 Draft 2 (C-M package Draft 4
  §C-M3 order overridden by that scope). This plan is the C6 settlement of O-3a..O-3d that MGR-9 Draft 4 waits for.
  The new A07 fields must survive the later C-M1 cursor page of A07.
- **Out of scope:** M9-C, M9-A, UC-12 reassignment and offboarding, UC-13 invitation and provisioning, C-M1 paging.

## 1. Source facts (checked by review R1)

1. `routers/be1_registry.py:129-207` `POST /api/be1/v1/classes/{class_id}/assignments`: locks the active class
   `FOR UPDATE` **before** authorization, then `require_assignment(..., roles={"school_admin"}, class_id=class_id)`
   (an organization-level or class-scoped `school_admin` row passes), 409 `CLASS_TEACHER_EXISTS` for a second active
   Teacher, then trusts the body `subject` (creates an identity for an unknown subject, issuer check for a known
   one), `add` + `flush` outside the `commit()` error mapping, 201 with `subject`, no revision, no key.
2. `CreateAssignmentRequest` has only `subject`. Catalog entry `openapi_contract.py:~10856` (201, `{subject*}`);
   `openapi_contract_amendments.py:259-266` gives the published response example (with `subject`), `:267-277` the
   A07 example; `openapi_srs_v22.py:23` lists the command in the FE projection `SRS_V22_INCLUDED_OPERATIONS`.
3. Teachers belong to an organization only through `be1_organization_assignments` rows. Rows are deactivated (by the
   Platform Admin router), never deleted; unique key `(organization_id, subject, class_id, role)`. Display names live
   at the identity provider. `email_verified` is not stored; an active Teacher row stands for an activated account.
4. Callers and pins: `tests/contract/test_m2_s1a_teacher_routes.py` (schema test `:28-35`; three handler tests
   `:91-175` calling the handler with a fake session); `tests/integration/test_be1_postgres_api.py:723-737`
   (assigns the School Manager's own subject; the test already fails at the base later with 403);
   `tests/integration/test_m2_s1a_teacher_postgres.py:173-330` (gated by `S1A_T_TEST_DATABASE_URL`, S1a-T gate
   evidence); catalog test pins (`:42` expected keys, `:279` and `:623` operations 152, `:297` PR22 size 13,
   `:307-313` body properties `{"subject"}`, `:559` key-set size 16, `:212` FE projection); composition test allowed
   paths. Bruno `organizations-classes/004-…` and `005-…` target the removed organization-level path; no Bruno
   request calls the class command.
5. BE1 route-count test (`test_be1_postgres_api.py:302-309`) expects 55 paths and 60 operations; the base has 54
   and 59. One new BE1 route makes them equal; the numbers are not edited.
6. Web: `RosterConsentPage.tsx:260-267` and `SchoolOverviewPage.tsx:127-136` show "Chờ API" placeholders for
   Teacher assignment; `managerBusinessPages.test.tsx` mocks `Be1Class` without the new fields.

## 2. SRS answers

| ID | Point | Answer | Basis |
|---|---|---|---|
| M9B-1 | Command result | 200 with the assignment revision | §21.2 line 1650 |
| M9B-2 | One responsible Teacher | Exactly one active Teacher; a second → 409 `CLASS_TEACHER_EXISTS` | line 1650; code from decision D-157 O3 |
| M9B-3 | Candidates (O-3a) | Identity `state="active"`, `account_role="teacher"`, with at least one active `teacher` row in the organization (the active row stands for the activated, verified account of UC-13). Teachers created by a Platform Admin have no such row until one is seeded or invited (UC-13 not built), so the list can be empty — recorded, not hidden | UC-13 lines 1537–1546; UC-12 line 1530 |
| M9B-4 | Fields (O-3b) | `candidate_ref` (opaque `account_id`) and `display_name` (null when the provider has none). No email, no provider subject; the request accepts `candidate_ref` only | NFR-02; §9.8; UC-13; §21.1 line 1637 |
| M9B-5 | Precondition and key (O-3d) | `If-Match` with the class assignment revision and a required `Idempotency-Key`; stale → 409 `STALE_REVISION` with `current_version` and `ETag` | UC-12 line 1534; §21.4 lines 1697, 1699 |
| M9B-6 | Persistence (OPEN-TECHNICAL, goal's choice) | Revision = `1 + count of teacher rows of the class` (grows on every assignment; unchanged by a deactivation, so it serves this command only, not a general class version); receipts in `be1_command_receipts`; eligibility by a locked query | §31.10(14); FR-T-02 |
| M9B-7 | Ineligible candidate | 404 `RESOURCE_NOT_FOUND` (same shape as missing) | §9.8 404 row |

The response keeps `contract: Be1AdultAssignmentV1` but changes 201 → 200, drops `subject` and adds fields: an
incompatible change accepted for this local, undeployed BE-before-FE window (CM-8). The later O-3a/O-3b scope
supersedes the "preserve AdultIdentity upsert" part of D-158 B1; `IDENTITY_ISSUER_MISMATCH` is no longer raised.

## 3. BE design (one commit)

1. **Candidate route (new, runtime-only like the C5 account routes):** `GET
   /api/be1/v1/organizations/{organization_id}/teacher-candidates`. Authorization by `_require_m2_assignment(roles=
   {"school_admin"})` (404 out of scope, 403 for a same-organization non-manager). `limit_query()` (25/100), `cursor`
   (versioned base64url of the last `account_id`; bad → 400 field `cursor`/`INVALID_FORMAT`), order `account_id`
   ascending, keyset `account_id > cursor` (a Teacher removed between pages does not break the walk). One query with
   `EXISTS` on an active teacher row (a Teacher with several rows appears once). Display names from
   `request.app.state.identity_account_provisioner.get_account_profiles` for the page only (provider down → 503).
   Response `Be1TeacherCandidatePageV1 {contract, items: [{candidate_ref, display_name}], next_cursor}`.
2. **Class list A07 (additive):** `assignment_revision` and `has_active_teacher` (an active `teacher` row for the
   class, whatever the identity state, as the 409 check) computed by one grouped query; shown to every caller that
   can list the class (they reveal no person).
3. **Command:** body `CreateAssignmentRequest {candidate_ref}` only (`extra="forbid"`). Key as C4
   (`Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]` without a default: FastAPI
   rejects a missing key with 400 `REQUIRED` before the handler); `If-Match` read with `Header(default=None)` and
   parsed to a strong integer (missing → 400 `REQUIRED`, malformed → `INVALID_FORMAT`). Handler order: read the
   active class **without** a lock → authorization → lock the class `FOR UPDATE` (same `state="active"` filter;
   gone → the uniform 404) → replay from
   `be1_command_receipts` (scope `POST /classes/{class_id}/assignments`, `organization_id` column filled,
   fingerprint of `candidate_ref` + `If-Match`) → revision check → one-active-Teacher check → lock the candidate
   identity `FOR SHARE` in **one** statement with the eligibility predicate (`account_id`, `state="active"`,
   `account_role="teacher"`, `EXISTS` active teacher row in the organization; `populate_existing`), which blocks a
   concurrent Platform Admin role or state change (`FOR NO KEY UPDATE` on the identity; lock order class → identity,
   no cycle with `update_account`) → insert one new row (no reactivation: a reactivated row would not move the
   derived revision; a candidate with an earlier inactive row for this class gets 409 `RESOURCE_CONFLICT` from the
   unique key inside the commit mapping; reassigning a removed Teacher is UC-12) → audit and outbox event
   (unchanged payload: assignment id and role) → receipt `{assignment_id, candidate_ref, role, class_id, active,
   assignment_revision}` → one commit (the flush is inside the error mapping; an `IntegrityError` becomes 409
   `RESOURCE_CONFLICT`). Response 200 with that body and `ETag`.
4. **OpenAPI and contract tests:** catalog entry → 200, request inputs `If-Match` (optional in the schema, as C4) and
   `Idempotency-Key*`, body `{candidate_ref*}`; the command joins `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` and the
   expected set (16 → 17); amendments examples (command response, A07 items); catalog test pins: body properties
   `{"candidate_ref"}`, operations 152 → 153 (both pins), PR22 13 → 14 (the candidate route), a runtime-OpenAPI test
   for the candidate route (`limit` 25/100, `cursor`); FE projection: the command stays in
   `SRS_V22_INCLUDED_OPERATIONS`, the candidate route stays out (runtime-only), the `:212` assertion unchanged;
   composition test: allowed path added.
5. **Existing tests:** `test_m2_s1a_teacher_routes.py` — schema test asserts `{candidate_ref}` and the extra-field
   refusal; the three fake-session handler tests are replaced by cases in the new PostgreSQL test (they cannot model
   the new queries). `test_be1_postgres_api.py:723-737` — creates an eligible Teacher and assigns it by
   `candidate_ref` with headers, expects 200; the test stays red later for its pre-existing 403 (C-M1 owns it).
   `test_m2_s1a_teacher_postgres.py` — fixture Teachers get `account_role="teacher"` and an organization-level
   Teacher row; requests use `candidate_ref`, two keys, `If-Match: "1"`, expect one 200 and one 409, compare
   subjects resolved from `account_id`; the fixture gives the manager `account_role="school_manager"` and every
   Teacher `account_role="teacher"`; the race loser expects 409 `STALE_REVISION`. It is gate-only
   (`S1A_T_TEST_DATABASE_URL`), so it is edited but NOT RUN here.
6. **New PostgreSQL test** `tests/integration/test_m9b_first_assignment_postgres.py` (fresh `*be1_acceptance`
   database, fake provisioner): candidates (same-org active Teacher listed once even with two rows; other-org Teacher,
   Parent, disabled Teacher, Teacher without a row excluded; null display name; default 25; cursor walk; bad cursor;
   403 same-org Teacher; 404 other-org manager); command: missing key → 400, missing `If-Match` → 400, stale → 409
   with `current_version` and `ETag`, success → 200 revision 2 and `ETag`, replay after the revision moved → stored
   body, same key other candidate → 400 `INVALID_IDEMPOTENCY_KEY`, second Teacher → 409 `CLASS_TEACHER_EXISTS`,
   ineligible candidates → 404 with no row and no identity created, reactivation of an inactive row, deactivation
   leaves the revision unchanged and `has_active_teacher` false, a candidate with an earlier inactive row for the
   class → 409 `RESOURCE_CONFLICT`, malformed `If-Match` → 400, two concurrent commands with two keys → one 200 and
   one 409 `STALE_REVISION` (both send `If-Match: "1"`; the revision check runs first), same key twice → one row;
   A07 fields. A candidate disabled while the command waits on its lock is covered by the lock design only (NOT RUN,
   recorded). Unit (default suite): compile the class and candidate locking selects and assert `FOR UPDATE` and
   `FOR SHARE` in the SQL (replaces the coverage of the removed fake-session tests).

**Allowlist (BE):** `routers/be1_registry.py`; `contracts/schemas/be1_runtime.py`; `openapi_contract.py` (entry and
key set); `openapi_contract_amendments.py` (two examples); the catalog, composition and `test_m2_s1a_teacher_routes.py`
contract tests; `test_be1_postgres_api.py`, `test_m2_s1a_teacher_postgres.py`; the new integration test; this plan and
the M9-B evidence note. No migration.

## 4. Web design (one commit)

**Allowlist (web):** `modules/school-manager/be1/services/classService.ts`, `pages/RosterConsentPage.tsx`,
`pages/SchoolOverviewPage.tsx`, `shared/api/backendApi.tsx` (remove the unused `createAssignment` helper), the touched
test files and new tests next to them, the M9-B web evidence note.

- `classService.ts`: `Be1Class.assignment_revision?` and `has_active_teacher?` (optional, so existing mocks stay
  valid; without a revision the "Phân công" button is disabled with a neutral message and no `If-Match` is built); `listTeacherCandidates(cursor)`; `assignTeacher(classId, candidateRef, revision, key)` with `If-Match:
  "<revision>"` (quoted integer).
- `RosterConsentPage.tsx` assignment card: for the selected class without an active Teacher, a candidate select
  (display name, or "Teacher chưa có tên hiển thị"; "Tải thêm" while `next_cursor`), and "Phân công". Key per
  (class, candidate, revision), reused for a retry. Answers: 200 → notice, reload classes; 409 → reload classes
  ("Lớp đã thay đổi hoặc đã có Teacher; đã tải lại"); 404 → neutral "Không thể hoàn tất phân công; danh sách đã được
  tải lại" and reload classes and candidates; 403 → "Tài khoản không có quyền phân công". Empty list: "Chưa có Teacher
  nào của tổ chức đủ điều kiện." A class with a Teacher: "Lớp đã có Teacher phụ trách; đổi Teacher chưa được hỗ trợ."
  Two Teachers with the same name cannot be told apart (no email allowed) — recorded limit.
- `SchoolOverviewPage.tsx`: the assignment half of the "Chờ API" copy changes to point at the roster page; the
  capacity half stays.
- Tests: service request shape (headers, query), page states (candidates, assign success, 409, 404, empty).
  `npm run test`, lint (no new warnings), build.

Key header: as C4 (`min_length=1, max_length=128`), accepting that it does not check the 33–126 character range the
C5 helper checks (recorded).

The M9-B evidence note records: the O-3a..O-3d readings with the SRS clauses, the route-count arithmetic (54/59 →
55/60), the S1a-T gate test edited and not run, the D-158 B1 supersession, and that no migration is needed
(`be1_command_receipts` is committed in `e9c9a815`).

## 5. Checks

Ruff and mypy 0 new; unit+contract against `tmp/be-integration/fail_ids.txt`; the new PostgreSQL test on a fresh
database; the BE1 route-count assertions are expected to pass; four validators; `git diff --check`; security
validator before the commit; web checks after a teammate-branch fetch. Implementation review (Sonnet 5.5 high).

## 6. Recorded limits

Global `account_id` as `candidate_ref` allows cross-organization correlation of the same Teacher (accepted: opaque,
not a provider id). The derived revision is not a general class version (UC-12 needs its own). Teachers created by a
Platform Admin are not candidates until an organization row exists (UC-13).

## 7. Review R1 findings and their fixes

| Finding | Fix |
|---|---|
| M9B-R1-01 (P2) handler tests | §1 fact 4; §3 step 5 |
| M9B-R1-02 (P2) integration test rewrites | §3 step 5 |
| M9B-R1-03 (P2) OpenAPI and contract impacts | §1 facts 2, 4; §3 step 4; allowlist |
| M9B-R1-04 (P2) route count | §1 fact 5; §5 |
| M9B-R1-05 (P2) candidate lock | §3 step 3 (`FOR SHARE`, lock order) |
| M9B-R1-06 (P2) `subject` path | removed; M9B-4 |
| M9B-R1-07 (P3) key and lock order | §3 step 3 |
| M9B-R1-08 (P3) revision meaning | M9B-6; §6; test |
| M9B-R1-09 (P3) inactive duplicate row | §3 step 3 reactivation; test |
| M9B-R1-10 (P3) global ref | §6 |
| M9B-R1-11 (P3) candidate route details | §3 step 1 |
| M9B-R1-12 (P3) empty candidates | M9B-3; web empty state |
| M9B-R1-13 (P3) pins and order | header |
| M9B-R1-14 (P3) contract, codes, receipt | §2 notes; §3 step 3 |
| M9B-R1-15 (P3) A07 fields | §3 step 2; optional web fields |
| M9B-R1-16 (P3) web gaps | §4 |
| M9B-R1-17 (P3) tests | §3 step 6 |

## 8. Review R2 findings and their fixes

| Finding | Fix |
|---|---|
| M9B-R2-01 (P2) reactivation does not move the revision | §3 step 3: insert only; earlier inactive row → 409 `RESOURCE_CONFLICT`; test |
| M9B-R2-02 (P3) single locked statement, class re-read | §3 step 3 |
| M9B-R2-03 (P3) S1a-T fixture and race code | §3 step 5 |
| M9B-R2-04 (P3) undefined revision on the web | §4 |
| M9B-R2-05 (P3) unit coverage of the locks | §3 step 6 compile-level test |
| M9B-R2-06 (P3) key range, extra tests | §4 note; §3 step 6 |
| M9B-R2-07 (P3) evidence content | §4 note |
