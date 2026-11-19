# FEAT-066 C6 part M9-B — first Teacher assignment (Draft 1, goal v2)

- **Status:** DRAFT for independent review. Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, 13,611 B, SHA-256 `5DFC1EDE…4795F8`) and the owner's added scope
  "C6 part M9-B, first Teacher assignment" in `tmp/phase-bc/GOAL_V2_CONTINUATION_C4_C5_20261119.md`. No code before
  the review verdict is READY (WITH NOTES).
- **Date:** 2026-11-19. **Base:** BE `feature/feat066-be-integration` after C4 (`bb57486d`) and C5; web
  `codex/fe-ui-web-remediation` after C4 (`b8bd3937`) and C5.
- **Inputs:** MGR-3 contract Draft 1 (`PLAN_MGR3_TEACHER_CANDIDATE_ASSIGNMENT_CONTRACT_DRAFT1_20261117.md`), C-M
  package Draft 4 §C-M3, MGR-9 Draft 1 slice M9-B (`.worktrees/ui`), C5 plan Draft 2 (receipt table
  `be1_command_receipts`).
- **Out of scope:** M9-C, M9-A, UC-12 reassignment and offboarding, UC-13 invitation and provisioning, C-M1 paging.

## 1. Source facts (BE `bb57486d` + C5 working tree; web `b8bd3937`)

1. `routers/be1_registry.py:129` `POST /api/be1/v1/classes/{class_id}/assignments`: locks the active class
   (`FOR UPDATE`), requires an organization-level `school_admin` assignment, refuses a second active Teacher with 409
   `CLASS_TEACHER_EXISTS`, then **trusts the body `subject`**: it creates an `AdultIdentityModel` for an unknown
   subject and only checks the issuer of a known one. It returns **201** with `subject` and no revision. No key, no
   precondition.
2. `CreateAssignmentRequest` (`contracts/schemas/be1_runtime.py`) has only `subject`. The OpenAPI catalog entry
   (`openapi_contract.py` ~10856) says 201 and `{subject*}`; the catalog test asserts the body properties are exactly
   `{"subject"}`.
3. Teachers belong to an organization only through `be1_organization_assignments` rows (`role="teacher"`, a class
   or `class_id` NULL). Rows are deactivated (`active=False`), never deleted by the BE1 runtime. Identities carry
   `account_role`, `state`, `account_id` (opaque UUID); display names live at the identity provider
   (`IdentityAccountProvisioner.get_account_profiles`). `email_verified` is a token claim and is not stored.
4. Callers of the assignment route: `tests/integration/test_be1_postgres_api.py:735` (body `subject`, expects 201),
   `tests/integration/test_m2_s1a_teacher_postgres.py:251` (concurrency, env-gated to the M2 gate database), the
   catalog and composition contract tests, Bruno (`organizations-classes` folder, if present), and an unused web
   helper `backendApi.createAssignment` that posts to a removed organization-level path.
5. `GET /organizations/{organization_id}/classes` (A07) returns `{class_id, display_name, state}` per class.
6. Web `RosterConsentPage.tsx` has a "Phân công Teacher" card marked "Chờ API".
7. The BE1 route-count test (`test_be1_postgres_api.py:302`, `len(be1_paths) == 55`) already fails at the base
   (54 vs 55). `test_app_composition.py` lists the allowed new paths.

## 2. SRS answers (owner's added scope; D-209 copy, 701,157 B)

| ID | Point | Answer | SRS basis |
|---|---|---|---|
| M9B-1 | Assignment command result | 200 with the assignment revision | §21.2 line 1650 |
| M9B-2 | One responsible Teacher | Exactly one active Teacher per class; a second assignment → 409 `CLASS_TEACHER_EXISTS` (kept). M9-B covers a class with no active Teacher only | §21.2 line 1650; O-3c |
| M9B-3 | Candidate source (O-3a) | Teachers of the same organization whose identity is active with `account_role="teacher"` and who hold an active `teacher` assignment row in that organization (class or organization level). UC-13 invitation is not built, so candidates are existing or seeded Teachers. Email verification is not stored, so it is not re-checked here (limit) | UC-13 lines 1537–1546; UC-12 line 1530 |
| M9B-4 | Candidate fields (O-3b) | `candidate_ref` (the opaque `account_id`) and `display_name` only. No email, no provider subject | NFR-02 deny by default; §9.8; UC-13 |
| M9B-5 | Expected revision and key (O-3d) | The command carries `If-Match` with the class assignment revision and an `Idempotency-Key`; stale → 409 `STALE_REVISION` with the current version and `ETag` | UC-12 "preflight assignment version"; §21.4 lines 1697, 1699 |
| M9B-6 | Persistence and resolver (OPEN-TECHNICAL) | The goal chooses: class assignment revision derived as `1 + number of teacher assignment rows of the class` (rows are never deleted, so it only grows); receipts in `be1_command_receipts` (C5) with the organization in the scope; eligibility checked by a query, no resolver table | §31.10(14); FR-T-02 |
| M9B-7 | Out-of-scope candidate | An unknown, inactive, non-Teacher or other-organization candidate → 404 `RESOURCE_NOT_FOUND` (same shape as missing) | §9.8 404 row |

## 3. BE design (one commit)

1. **Candidate list (new):** `GET /api/be1/v1/organizations/{organization_id}/teacher-candidates`, School Manager
   of the organization only (the existing `_require_m2_assignment` rule used by the command). `limit_query()`
   (25/100), opaque `cursor` (versioned base64url of the last `account_id`), order `account_id` ascending.
   Response `Be1TeacherCandidatePageV1 {contract, items: [{candidate_ref, display_name}], next_cursor}`. Display
   names come from `get_account_profiles` for the page only (provider down → 503). Eligibility as M9B-3.
2. **Class list (A07), additive:** each item gains `assignment_revision` (M9B-6) and `has_active_teacher`; nothing
   removed (§21.1 line 1635 allows optional fields). Needed by the screen to send `If-Match`; this is the smallest
   C-M1 piece M9-B needs; C-M1 paging stays out.
3. **Assignment command:** request body `candidate_ref` (new) or `subject` (deprecated, kept for compatibility),
   exactly one (else 400). Order: lock class → School Manager check → key (required, `Header` without default so a
   missing key is `REQUIRED`) and `If-Match` (required, strong integer) → replay from `be1_command_receipts`
   (scope `POST /organizations/<org>/classes/<class>/assignments`, fingerprint of the body and `If-Match`) →
   revision check → one-active-Teacher check → resolve the candidate by eligibility (no identity creation any more)
   → insert assignment, audit, outbox event, receipt → one commit. Response **200**
   `{contract, assignment_id, candidate_ref, role, class_id, active, assignment_revision}` and `ETag`. `subject` is
   no longer returned (O-3b). A concurrent second command waits on the class lock and then gets 409.
4. **OpenAPI:** catalog entry of the command: 200, request inputs with `If-Match*` and `Idempotency-Key*`, body
   `CreateAssignmentRequest {subject:string, candidate_ref:string}`; the command joins
   `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` only if that set accepts BE1 paths, otherwise its 400 row text says so. The
   candidate route is added to `PR22_UNCATALOGUED_OPERATIONS` in the catalog test (13 → 14; operations 152 → 153)
   and to the composition test's allowed paths. The BE1 route-count test moves from 55 expected / 54 actual to the
   same mismatch plus one (recorded; it already fails at the base).
5. **Tests:** new `tests/integration/test_m9b_first_assignment_postgres.py` (fresh `*be1_acceptance` database, fake
   provisioner): candidate eligibility (same-org active Teacher in; other-org Teacher, parent, disabled Teacher
   out), default 25, cursor walk, School Manager only; command: missing key or `If-Match` → 400; stale → 409 with
   `current_version` and `ETag`; success → 200, revision 2, `ETag`; replay with the same key → same body, one row;
   other payload → 400 `INVALID_IDEMPOTENCY_KEY`; second Teacher → 409 `CLASS_TEACHER_EXISTS`; ineligible candidate
   → 404 and no identity row created; legacy `subject` of an eligible Teacher works; class list shows the revision
   and the flag. Existing tests updated: `test_be1_postgres_api.py:735` (headers, 200),
   `test_m2_s1a_teacher_postgres.py:251` (headers, env-gated), catalog and composition tests.

**Allowlist (BE):** `routers/be1_registry.py`; `contracts/schemas/be1_runtime.py`; `openapi_contract.py` (the
command entry); the two contract tests; the two existing integration tests; the new integration test; Bruno
requests for the command if they exist; this plan and the M9-B evidence note. No migration (C5 table reused).

## 4. Web design (one commit)

- `classService.ts`: `Be1Class` gains `assignment_revision`, `has_active_teacher`; new `listTeacherCandidates(cursor)`
  and `assignTeacher(classId, candidateRef, revision, key)`; the wrong `backendApi.createAssignment` helper is
  removed (no caller).
- `RosterConsentPage.tsx` "Phân công Teacher" card: for the selected class with no active Teacher, a candidate
  select (display name only; "Tải thêm" while `next_cursor`), and a "Phân công" button. Key per (class, candidate,
  revision), reused for a retry. Answers: 200 → notice and class reload; 409 `CLASS_TEACHER_EXISTS` or
  `STALE_REVISION` → reload classes and say so; 404 → reload candidates ("Teacher không còn khả dụng"). A class
  that has a Teacher shows that changing the Teacher is not supported yet (UC-12). No free-typed identity.
- Tests next to the service and page; `npm run test`, lint (no new warnings), build.

## 5. Checks

As C4/C5: ruff and mypy 0 new; unit+contract against `tmp/be-integration/fail_ids.txt`; the new PostgreSQL test
on a fresh database; four validators; `git diff --check`; security validator before the commit; web checks after a
teammate-branch fetch. Implementation review (Sonnet 5.5 high) before each commit.
