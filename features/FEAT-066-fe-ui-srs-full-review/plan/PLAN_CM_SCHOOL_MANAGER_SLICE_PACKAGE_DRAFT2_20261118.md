# FEAT-066 C-M — School Manager per-role slice package (Draft 2)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package plans Phase C work for the School Manager role only. It authorizes no code, migration, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 1 (14,598 B, `550CD244…`). Its round-1 review was NOT READY with 1 P1, 6 P2 and 8 P3 (`evidence/notes/CM_COLD_REVIEW_DRAFT1_20261118.md`, 4,758 B, `E435B65D…`). §9 maps each finding to its fix.
- **Owner request:** "Viết C-M đi" (chat, 2026-11-18), after the coordinator explained C-M as the plan for wiring the School Manager web role to the backend.
- **What C-M is:** roadmap Draft 4 §4 row C ("per-role slices") for the School Manager, and register Draft 4 §5 row "C-M / W-*". It splits the role's work into five sub-slices (§4), each with a BE part and an FE part, in the order of the roadmap's FE integration path (§5.6: BE verified first, then one FE slice per app).
- **Relation to MGR-9:** the FE plan `PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` (review R2: ACCEPT) defines the FE slices M9-A (class creation), M9-B (assignment) and M9-C (exact-version review). C-M reuses them unchanged as the FE parts of C-M4, C-M3 and C-M2, and adds the FE part of C-M1, which MGR-9 left unowned ("Class-list pagination is not part of M9-B; it needs separate approved scope").
- **NEW in this package:** the sub-slice names C-M1 to C-M5, the questions CM-1 to CM-12, the School Manager roster summary of §4 (C-M1), the cursor helper, and every response field marked NEW below.

## 1. Authority and inputs

| Input | Location | Bytes | SHA-256 (prefix) |
|---|---|---:|---|
| Working SRS (D-209, D-066-64) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D…` |
| Mismatch register Draft 4 | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` (git-ignored) | 41,798 | `0F3F35FD…` |
| Roadmap Draft 4 | `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` | 42,628 | `63710A9F…` |
| CONV-1 package Draft 5 (approved, D-066-71) | `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT5_20261118.md` | 47,483 | `3FCF4741…` |
| MGR-9 FE plan Draft 1 (web worktree, untracked) | `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` | 43,006 | `1547F32C…` |
| MGR-9 review R2 (ACCEPT) | `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_9_COLD_REVIEW_DRAFT1_R2_20261118.md` | 3,419 | `C235A560…` |
| MGR-2 capacity contract Draft 1 | `plan/PLAN_MGR2_CLASS_CAPACITY_CONTRACT_DRAFT1_20261117.md` | 28,624 | `3F5AEA62…` |
| MGR-3 assignment contract Draft 1 | `plan/PLAN_MGR3_TEACHER_CANDIDATE_ASSIGNMENT_CONTRACT_DRAFT1_20261117.md` | 34,432 | `80762D84…` |
| MGR-6 lesson-version contract Draft 1 | `plan/PLAN_MGR6_IMMUTABLE_LESSON_VERSION_REVIEW_CONTRACT_DRAFT1_20261117.md` | 24,165 | `BEB43ECB…` |
| Decisions (conv1 worktree; uncommitted, it carries the D-066-72 append) | `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` | 55,334 | `8B65AA3C…` |

Decisions used: D-066-62, D-066-63 as amended by D-066-66 and D-066-67, D-066-65, D-066-68, D-066-69, D-066-71.

**BE source base:** commit `2dddc607` (CONV-1) on the local-only branch `feature/feat066-conv1` (D-066-71, CV-B). The "Today" column of §3 was checked against this source by the round-1 review, not only against the register (which audited `dev` `1c9148e8`). **FE source base:** `.worktrees/ui`, branch `codex/fe-ui-web-remediation` at `297a28b1`.

**SRS and decision basis per row:**

| Rows | Basis |
|---|---|
| A07, A09, A10 (reads) | §21.1 cursor pagination, default 25, maximum 100 (D-066-68 C-D8); §31.3 line 2586, School Manager: "Không đọc profile contents mặc định" (D-066-69). §21.2 names no route for these reads |
| B02, G02 | SRS 1650: `POST /v1/classes/{class_id}/assignments`, exactly one active responsible Teacher, 200 assignment revision; D-066-62 |
| B01, G01 | SRS 1649: `POST /v1/organizations/{org_id}/classes`, capacity checked in a transaction; D-066-63, D-066-66, D-066-67 |
| A12, A13, G06 | FR-PL-05, BR-51, Q168 (line 2924), §31.2 immutable versions |
| G09 | UC-12 (line 1525) |
| All | §9.8 envelope; uniform 404 and in-scope 403 (C-D4); `Idempotency-Key` (C-D5); revision transport (C-D7) |

## 2. What changed since the register (2026-11-18)

| Fact | Effect on C-M |
|---|---|
| **G0 closed:** S-LL committed as `08439b22` and pushed | Lesson Library rows are no longer blocked by G0. But CONV-1 also changed `lesson_library.py`, so C-M2 starts from the queue tip that contains CONV-1, not from `08439b22` |
| **CONV-1 committed** `2dddc607` (local only) | §9.8 envelope, `X-Request-ID`, uniform 404 / in-scope 403 in the shared guards, and `limit_query()`. On CONV-1 paths (`/api/be1/v1` is in `CONV1_PREFIXES`), `map_code` already turns any 404 `*_NOT_FOUND` (such as `get_class`'s `CLASS_NOT_FOUND`) into the public code `RESOURCE_NOT_FOUND`, so C-M1 needs no route change for that. CONV-1 **left BE1 list paging out** (CONV-1 Draft 5 line 236), and provides **no cursor helper** |
| **O-PRIV decided** (D-066-69): the School Manager receives no child-profile contents by default; roster views show counts and opaque references only | Applies server-side to **every** School-Manager-callable route that returns child names or ages, not only A09 (§4 C-M1, CM-2) |
| **Billing frozen** | B01 and G01 cannot start; class creation stays disabled |
| **O-L3SCOPE open** | A07, A09, A10, B01, B02 and the session roster sit on the BE1 compatibility surface (CB) that the M2 freeze calls "a frozen compatibility surface to be deprecated later" (D-171 item 7). CM-1 asks for these rows only |
| **O-5 open, consent writes excluded** (MGR-5, D-066-62) | A10 stays read-only; the consent meaning is not changed by C-M |
| **O-9 open for the web branch** | Every C-M FE part waits until the web branch is reconciled to a base containing the BE slice |
| **BE queue:** FR-C-08 → SEED-1 → PAY-0 (PD-8 pending) | C-M BE parts join after these unless the owner reorders (CM-10) |

## 3. Row map

| Row | Endpoint / capability | Today (BE `2dddc607`, web `297a28b1`) | Target | Sub-slice |
|---|---|---|---|---|
| A07 | GET `/api/be1/v1/organizations/{organization_id}/classes` | Unpaginated; sorted by `created_at` | Cursor page (§4) | C-M1 |
| A09 | GET `…/classes/{class_id}/profiles` | Unpaginated. Returns `display_name` and `age_months` to School Manager and Teacher. **Consent gate:** if any active profile lacks effective consent, the route writes an audit row and returns 409 `CONSENT_NOT_EFFECTIVE`; because the store allows only `pending` and `revoked` consent states (`be1_models.py` line 241), every non-empty class answers 409 today (asserted by `test_be1_postgres_api.py` lines 757–759) | School Manager: a roster summary (CM-3); Teacher: unchanged fields and gate, paged | C-M1 |
| A10 | GET `…/classes/{class_id}/consents` | Unpaginated; sorted `recorded_at` newest first; returns `consent_id`, `child_id`, `purpose_ref`, `state` (`pending` or `revoked`), `effective` | Paged; School Manager field set per CM-4 | C-M1 |
| Session roster | GET `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` | Allows `school_admin`; returns `display_name` of admitted children (`be1_sessions.py` lines 299–360) | No name for a School Manager (D-066-69) | C-M1 (CM-2) |
| Pilot profiles | GET `…/sessions/{session_id}/pilot-profiles` | Allows `school_admin`; returns `child_id` and `display_name`; mounted in local/test with synthetic data only (`be1_registry.py` 326–396) | No name for a School Manager | C-M1 (CM-2) |
| A12 | GET `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Current head only | Exact immutable version read for review | C-M2 (W-LESSON) |
| A13 | POST `…/access-grants/{access_grant_id}/decision` | Not bound to a reviewed version; FE response untyped | Decision bound to the exact version (O-6a..c) | C-M2 |
| G06 | Exact LessonVersion read; grant-bound decision | Absent | New read and binding | C-M2 |
| B02 | POST `/api/be1/v1/classes/{class_id}/assignments` | 201 without revision; no key; trusts the body `subject`; FE helper posts an org-level path | 200 + revision; `Idempotency-Key`; one active Teacher | C-M3 (W-ASSIGN) |
| G02 | Scoped Teacher-candidate discovery | Absent | Same-organization verified Teachers (D-066-62) | C-M3 |
| B01 | POST `…/organizations/{organization_id}/classes` | No capacity admission; no key | Billing admission | C-M4 (W-CAP) — **blocked** |
| G01 | Capacity-safe class creation | Absent | Billing B-2 | C-M4 — **blocked** |
| G09 | Class archive, suspend, reassignment (UC-12) | Absent | UC-12 flows | C-M5 — deferred (CM-12) |

**Callers of A07, A09, A10** (round-1 review confirmed the list): the School Manager services `be1/services/classService.ts` and `managerBusinessService.ts`, the pages `ClassesPage.tsx` and `RosterConsentPage.tsx` (its class picker uses A07), `shared/api/backendApi.tsx`, and the Teacher screens `modules/teacher/pages/T05ClassesScreen.tsx` and `TeacherWorkbenchPage.tsx`. `SchoolOverviewPage.tsx` calls only the organization read.

## 4. Sub-slices

### C-M1 — Roster reads and School Manager privacy (A07, A09, A10, session roster, pilot profiles)

**Gate:** CM-1 to CM-9 answered; queue slot open (CM-10); branch and base set (CM-9). The FE part also needs O-9 for the web branch.

**BE part (one Task Approval, one commit):**

1. **Cursor helper (NEW):** `encode_cursor` and `decode_cursor` in `interfaces/http/api_conventions.py`, following the base64-JSON precedent of `parent_profile_repository.py`. The cursor carries the last sort key and ID and is bound to the route and its scope (organization and class); a cursor that does not decode, or decodes for another scope, gives 400 `INVALID_REQUEST` with field error `cursor` / `INVALID_FORMAT`.
2. **Paging** with `limit_query()` (default 25, max 100; above 100 → 400) on A07, A09 (Teacher path) and A10. Response keeps `contract` and `items` and adds `next_cursor` (**NEW**). Ordering: A07 `created_at` ascending then `class_id`; A09 `created_at` ascending then `child_id`; A10 keeps today's `recorded_at` **descending** then `consent_id` descending.
3. **A09 consent gate (CM-5):** for the Teacher path the gate keeps today's whole-class meaning: it is evaluated over all active profiles of the class before paging, so a page never hides a non-effective profile. The audit row written on 409 stays as today.
4. **A09 School Manager path (CM-3):** returns a distinct contract `Be1ClassRosterSummaryV1` (**NEW**) with `class_id` and `active_profile_count` only. It carries no contents, so the consent gate does not apply to it (CM-5). No paging is needed.
5. **Role rule:** full profile fields only when the caller's assignment role for the class is `teacher`; any other role (`school_admin` gets the summary; `guide`, `observer` or anything else) is denied by default with the in-scope 403 `ACTION_NOT_ALLOWED`. The role comes from the verified assignment, never from the request.
6. **A10 School Manager fields (CM-4):** per the owner's choice.
7. **Session roster and pilot profiles (CM-2):** for a `school_admin` caller, omit `display_name` (and any age field) and keep only opaque IDs and states. Teacher responses unchanged.
8. **OpenAPI:** the new contract, `next_cursor`, the 400 cursor error and one example per shape, through `openapi_contract.py` and its amendments module.

**Proposed allowlist (exact paths fixed in the C-M1 Task Approval):** `interfaces/http/api_conventions.py`; `interfaces/http/routers/be1_registry.py`; `interfaces/http/routers/be1_sessions.py`; `contracts/schemas/be1_runtime.py`; `interfaces/http/openapi_contract.py` and `openapi_contract_amendments.py`; the CONV-1 tests that touch these routes; BE1 contract, unit and PostgreSQL integration tests including `test_be1_postgres_api.py` (the 409 assertion at 757–759 is kept for the Teacher path and extended); the frozen OpenAPI snapshots under FEAT-063 `m2-s3` and FEAT-047 `API_CONTRACT.md` only if they pin these operations (to be confirmed); Bruno request 012 (list profiles) and the related requests (L5 per-slice update).

**Checks:** contract catalog; unit tests for the cursor helper and the role rule; PostgreSQL integration on a disposable database whose name contains `be1_acceptance` (never `sketch2life_m2_s1a`, never ports 5432 or 5433), **run by the owner** as for CONV-1; repository validators.

**FE part (one Task Approval, after the BE part is verified, the web branch is reconciled (O-9), and before M9-A and M9-B, which edit the same files):**

- `classService.ts` and `managerBusinessService.ts`: page parameters and `next_cursor`; the Manager roster call reads `Be1ClassRosterSummaryV1`.
- `ClassesPage.tsx` and the `RosterConsentPage.tsx` class picker: "load more" with the cursor.
- `RosterConsentPage.tsx`: the School Manager roster shows the count only (CM-3); the initial-and-age rows are removed; the consent label map uses the BE values (CM-6).
- `shared/api/backendApi.tsx`, `T05ClassesScreen.tsx` and `TeacherWorkbenchPage.tsx`: **follow `next_cursor` to completion** for the class list, profiles and consents, because these screens join profiles to consents and look a class up by ID (CM-7). What the Teacher sees does not change.
- Tests next to each changed module.

**BE-before-FE window (CM-8):** between the BE commit and the FE commit, Teacher screens read only the first 25 rows. This affects local development only (there is no deployed environment).

**Acceptance:** list defaults and maximum as C-D8; invalid or foreign cursor → 400; the School Manager responses of A09, A10, the session roster and pilot profiles contain no name and no age (BE tests per route); Teacher responses unchanged apart from paging; Teacher screens show the same data as before with more than 25 rows.

### C-M2 — W-LESSON exact version review (A12, A13, G06)

- **Gate:** owner answers O-6a (binding option A hash snapshot, or B immutable version row), O-6b (superseded pending-grant outcome) and O-6c (decision precondition), asked one at a time from the MGR-6 contract; then MGR-6 contract Draft 2 and its review.
- **BE part:** as roadmap §5.4, from the queue tip that contains CONV-1. Files: `routers/lesson_library.py`, `contracts/schemas/lesson_library.py`, `infrastructure/lesson_library/service.py`, `tables.py` only if option B, OpenAPI files, `test_lesson_library_api.py`.
- **FE part:** MGR-9 slice M9-C unchanged.

### C-M3 — W-ASSIGN first assignment (B02, G02)

- **Gate:** owner answers O-3a to O-3d from the MGR-3 contract; then MGR-3 contract Draft 2 and its review. D-066-62 already settles eligibility.
- **BE part:** as roadmap §5.3; 200 + revision (SRS 1650); `Idempotency-Key` (C-D5); one active Teacher under concurrency.
- **FE part:** MGR-9 slice M9-B unchanged, after C-M1 FE.

### C-M4 — W-CAP class creation (B01, G01) — blocked

Blocked while Billing is frozen: admission needs Billing B-1 and B-2 (D-066-63 as amended by D-066-66 and D-066-67). The class-create control stays disabled (MGR-9 M9-A); C-M does not change the BE route.

### C-M5 — UC-12 archive, suspension, reassignment (G09) — deferred

UC-12 needs O-3c and, for suspension, Billing B-5. Recommendation in CM-12.

## 5. Order, branches and queue

1. C-M1 BE, then C-M1 FE.
2. C-M2 or C-M3 (CM-11), each after its contract answers.
3. C-M4 when Billing is unfrozen; C-M5 after C-M3.

- Each BE part is one Task Approval and one commit on its own local branch, cut from the BE queue tip when its slot opens; the pins of this package are refreshed then (CM-9).
- FE parts run one at a time in the web app, only on a verified BE slice, and after the web branch is reconciled to a base that contains it (O-9). The web worktree shares the repository, so a local-only BE branch can be merged into it locally on the owner's word without a push.
- Bruno requests for each slice are updated in L5 after the slice is verified.

## 6. Owner questions (one at a time, with the SRS or decision sentence)

| ID | Question | Recommendation |
|---|---|---|
| CM-1 | O-L3SCOPE, for the School Manager rows only: may C-M change A07, A09, A10, B02 and the session roster, although the M2 freeze calls the BE1 surface "a frozen compatibility surface to be deprecated later" (D-171 item 7)? | Yes, for these rows only; the 86 untouched operations stay under O-L3SCOPE |
| CM-2 | D-066-69 ("no child-profile contents by default") is a server rule: also remove `display_name` for a School Manager from the session roster and the synthetic pilot-profiles route in C-M1? | Yes; otherwise record both as open privacy debt |
| CM-3 | What does the School Manager roster (A09) show: the count only, or the count plus opaque rows? | Count only (`Be1ClassRosterSummaryV1`); D-066-69 allows "counts and opaque references", and the screen gains nothing from rows without names |
| CM-4 | A10 for the School Manager: (a) keep `child_id`, which is already an internal opaque ID (SRS FR-T-04, `synthetic-<24 hex>`), or (b) drop `child_id` from the School Manager response? A new derived reference is not proposed (it needs storage and fails for consent rows with no profile) | (a): no extra change; the School Manager screen never shows it |
| CM-5 | A09 consent gate: keep it unchanged for the Teacher path (whole class, before paging), and let the School Manager summary bypass it because it returns no contents? | Yes |
| CM-6 | A10 labels: the FE maps the BE states `pending` → "Đang chờ xác nhận" and `revoked` → "Đã thu hồi", and drops the unused "Đã ghi nhận" (`ACTIVE`) label, with no BE change? | Yes |
| CM-7 | Apply C-D8 paging (default 25, max 100) to A07, A09 and A10? | Yes |
| CM-8 | Accept that Teacher screens read only the first 25 rows between the C-M1 BE commit and the C-M1 FE commit (local development only)? | Yes; the FE part follows `next_cursor` to completion |
| CM-9 | C-M1 BE branch: a new local-only branch `feature/feat066-cm1` cut from the BE queue tip when its slot opens, never pushed (as CV-B), with the pins refreshed then? | Yes |
| CM-10 | Queue position of C-M1 BE: after FR-C-08 and SEED-1 (and after PAY-0 if PD-8 keeps it there)? | Yes |
| CM-11 | After C-M1, W-LESSON (C-M2) or W-ASSIGN (C-M3) first? The SRS sets no order and the roadmap O-SEQ gives no recommendation | W-LESSON: its routes are already page-called, and the live review screen shows current-head content today (M9-C fixes a correctness gap); assignment is disabled and harms nothing while it waits |
| CM-12 | Keep UC-12 (G09) out of the first Phase C pass and plan it after C-M3? | Yes |

O-6a..c (C-M2) and O-3a..d (C-M3) are asked from their own contracts when that sub-slice starts.

## 7. Not verified

- Runtime behaviour: no test was run for this draft; the A09 409 behaviour comes from source and the committed assertion.
- Whether the FEAT-063 `m2-s3` OpenAPI snapshots and FEAT-047 `API_CONTRACT.md` pin these operations.
- Existing FE unit tests and Bruno requests beyond file presence.
- Mobile code outside `apps/` (no Parent caller of these BE1 reads is expected).
- A12, A13 and G06 behaviour beyond route existence (C-M2 re-checks it).

No code, test or command was run for this draft beyond read-only searches.

## 8. Limits

C-M does not change consent writes (MGR-5), Parent-group invitations (MGR-4), Billing, payment, or any Teacher-only route. The School Manager overview page is unchanged.

## 9. Round-1 findings and their fixes

| Finding | Fixed in |
|---|---|
| CM-R1-01 (P1) | §3 rows "Session roster" and "Pilot profiles"; §4 C-M1 BE step 7; acceptance per route; CM-2 |
| CM-R1-02 | §3 A09 "Today" describes the gate and the 409; §4 BE step 3 and 4; CM-5; the asserting test listed |
| CM-R1-03 | CM-4 offers (a) keep `child_id` or (b) drop it; no new reference |
| CM-R1-04 | §4 FE part (Teacher screens follow the cursor to completion); BE-before-FE window and CM-8; paging and Teacher questions split (CM-7, CM-8) |
| CM-R1-05 | §5 branches and pin refresh; CM-9; C-M2 starts from the queue tip with CONV-1 (§2, §4) |
| CM-R1-06 | CM-3 (count only recommended); `Be1ClassRosterSummaryV1` replaces the `profiles.length` chip |
| CM-R1-07 | §4 BE steps 1, 2, 4 and 8 (cursor helper, invalid cursor, per-route ordering, distinct contract, examples); allowlist names the CONV-1 tests, snapshots, `API_CONTRACT.md` and Bruno 012 |
| CM-R1-08 | §3 callers list; §4 FE part drops `SchoolOverviewPage`, adds the class picker, and orders C-M1 FE before M9-A and M9-B |
| CM-R1-09 | §1 basis table (A07/A09/A10 rest on §21.1 and D-066-69); §2 O-5 and O-9 rows; CM-1 reworded |
| CM-R1-10 | §3 A10 lists the BE states; CM-6 gives the exact mapping |
| CM-R1-11 | §2 CONV-1 row: `map_code` already makes `CLASS_NOT_FOUND` public `RESOURCE_NOT_FOUND` on CONV-1 paths |
| CM-R1-12 | §4 BE step 5 (Teacher-only full fields, default deny); the "enrollment state" field is dropped with CM-3 |
| CM-R1-13 | CM-1 to CM-12 are single asks; CM-11 recommendation regrounded |
| CM-R1-14 | §1 pins CONV-1 Draft 5 and DECISIONS; "Today" source stated; NEW markers; D-066-66/67 cited; owner-run PostgreSQL tests |
| CM-R1-15 | §4 allowlist and §5 (Bruno L5 per-slice update) |
