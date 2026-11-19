# FEAT-066 C-M — School Manager per-role slice package (Draft 1)

- **Status:** DRAFT / NOT REVIEWED / NOT APPROVED / NOT LAUNCHED. This package plans Phase C work for the School Manager role only. It authorizes no code, migration, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Owner request:** "Viết C-M đi" (chat, 2026-11-18), after the coordinator explained C-M as the plan for wiring the School Manager web role to the backend: 7 register rows and 4 capability gaps.
- **What C-M is:** roadmap Draft 4 §4 row C ("per-role slices") for the School Manager, and register Draft 4 §5 row "C-M / W-*". It splits the role's work into five sub-slices (§4), each with a BE part and an FE part, in the order the roadmap's FE integration path requires (§5.6: BE verified first, then one FE slice per app).
- **Relation to MGR-9:** the FE plan `PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` (review R2: ACCEPT) already defines the FE slices M9-A (class creation), M9-B (assignment) and M9-C (exact-version review). C-M reuses them unchanged as the FE parts of C-M4, C-M3 and C-M2, and adds the FE part of C-M1, which MGR-9 left as an unowned gap ("Class-list pagination is not part of M9-B; it needs separate approved scope").

## 1. Authority and inputs

| Input | Location | Bytes | SHA-256 (prefix) |
|---|---|---:|---|
| Working SRS (D-209, D-066-64) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D…` |
| Mismatch register Draft 4 | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` (git-ignored) | 41,798 | `0F3F35FD…` |
| Roadmap Draft 4 | `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` | 42,628 | `63710A9F…` |
| MGR-9 FE plan Draft 1 (web worktree, untracked) | `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` | 43,006 | `1547F32C…` |
| MGR-9 review R2 (ACCEPT) | `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_9_COLD_REVIEW_DRAFT1_R2_20261118.md` | 3,419 | `C235A560…` |
| MGR-2 capacity contract Draft 1 | `plan/PLAN_MGR2_CLASS_CAPACITY_CONTRACT_DRAFT1_20261117.md` | 28,624 | `3F5AEA62…` |
| MGR-3 assignment contract Draft 1 | `plan/PLAN_MGR3_TEACHER_CANDIDATE_ASSIGNMENT_CONTRACT_DRAFT1_20261117.md` | 34,432 | `80762D84…` |
| MGR-6 lesson-version contract Draft 1 | `plan/PLAN_MGR6_IMMUTABLE_LESSON_VERSION_REVIEW_CONTRACT_DRAFT1_20261117.md` | 24,165 | `BEB43ECB…` |
| Decisions | `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` | — | D-066-62, 63, 65, 66, 68, 69, 71 |

**BE source base:** commit `2dddc607` (CONV-1) on the local-only branch `feature/feat066-conv1` (D-066-71, CV-B). **FE source base:** `.worktrees/ui`, branch `codex/fe-ui-web-remediation` at `297a28b1`, which is also the base the register audited.

**SRS clauses used:**

| Line | Content |
|---|---|
| 1649 | `POST /v1/organizations/{org_id}/classes`: School Manager of the organization; effective capacity checked in a transaction; 201 class ref or `CLASS_CAPACITY_REACHED` |
| 1650 | `POST /v1/classes/{class_id}/assignments`: School Manager of the organization; exactly one active responsible Teacher; 200 assignment revision |
| 1525 | UC-12: School Manager changes the responsible Teacher and offboards |
| 2586 | §31.3 permission table, Profile row, School Manager column: "Không đọc profile contents mặc định" (no profile contents by default) |
| §21.1 | Cursor pagination, default 25, maximum 100 (D-066-68 C-D8) |
| §21.4 | Idempotency and revision rules (D-066-68 C-D5 to C-D7) |
| §9.8 | Error envelope; uniform 404 out of scope, 403 in scope (D-066-68 C-D4; done in CONV-1) |
| FR-PL-05, BR-51, Q168, §31.2 | Teacher-authored lessons become public only after School Manager approval; versions are immutable (W-LESSON) |

## 2. What changed since the register (2026-11-18)

| Fact | Effect on C-M |
|---|---|
| **G0 closed:** S-LL (MGR-7 code, MGR-8 verified) committed as `08439b22` and pushed | The Lesson Library rows (A12, A13, G06) are no longer blocked by G0; W-LESSON edits start from that base |
| **CONV-1 coded and committed** `2dddc607` (local only): §9.8 envelope, `X-Request-ID`, uniform 404 / in-scope 403 in the shared BE1 guards, `limit_query()` helper | The global items E and PX are done for BE1 and Lesson Library routes. CONV-1 **explicitly left BE1 list paging out** ("no paging for BE1 lists", CONV-1 Draft 5 line 236), so A07, A09 and A10 paging belongs to C-M1 |
| **O-PRIV decided** (D-066-69): by default the School Manager receives no child-profile contents (no name, no age); roster views show counts and opaque references only; Teachers keep their granted fields | A09 has a decided target; C-M1 implements it |
| **Billing frozen** by the owner | B01 and G01 (W-CAP) cannot start; class creation stays disabled in the UI |
| **O-L3SCOPE still open** | A07, A09, A10, B01 and B02 sit on the BE1 compatibility surface (CB) that the M2 freeze marks "to be deprecated later" (D-171 item 7). CM-1 asks whether C-M may change them |
| **BE queue** (one slice at a time): FR-C-08 → SEED-1 → PAY-0 (PD-8, pending) | C-M BE work joins the queue after these, unless the owner reorders it (CM-5) |

## 3. Row map

| Row | Endpoint / capability | Today (BE `2dddc607`, web `297a28b1`) | Target | Fix side | Sub-slice |
|---|---|---|---|---|---|
| A07 | GET `/api/be1/v1/organizations/{organization_id}/classes` | Unpaginated; `ClassesPage` and the Teacher screens read one page | Cursor page, default 25, max 100, opaque cursor | BE + FE | C-M1 |
| A09 | GET `…/classes/{class_id}/profiles` | Returns `display_name` and `age_months` to the School Manager; unpaginated | School Manager: count plus opaque refs only (D-066-69); Teacher: unchanged fields; paginated | BE + FE | C-M1 |
| A10 | GET `…/classes/{class_id}/consents` | Read only; FE label expects uppercase states, BE returns lowercase; unpaginated | Paginated; FE maps the BE values; read stays read-only (writes excluded, MGR-5) | BE + FE | C-M1 |
| A12 | GET `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Current head only | Exact immutable version read for review | BE + FE | C-M2 (W-LESSON) |
| A13 | POST `…/access-grants/{access_grant_id}/decision` | Not bound to a reviewed version; FE response untyped | Decision bound to the exact version (O-6a..c) | BE + FE | C-M2 |
| G06 | Exact LessonVersion read; grant-bound decision | Absent | New read and binding | BE | C-M2 |
| B02 | POST `/api/be1/v1/classes/{class_id}/assignments` | 201 without revision; no key; FE helper posts an org-level path | 200 + assignment revision; `Idempotency-Key`; exactly one active Teacher | BE + FE | C-M3 (W-ASSIGN) |
| G02 | Scoped Teacher-candidate discovery | Absent | Same-organization verified Teachers only (D-066-62) | BE | C-M3 |
| B01 | POST `…/organizations/{organization_id}/classes` | No capacity admission; no key | Billing admission (D-066-63) | BE + FE | C-M4 (W-CAP) — **blocked** |
| G01 | Capacity-safe class creation | Absent | Billing B-2 | BE | C-M4 — **blocked** |
| G09 | Class archive, suspend, reassignment (UC-12) | Absent | UC-12 flows | BE + FE | C-M5 — deferred (CM-6) |

**Shared callers:** A07, A09 and A10 are also called by the Teacher web role through `shared/api/backendApi.tsx` (`classes`, `profiles`, `consents`), used by `modules/teacher/pages/T05ClassesScreen.tsx` and `TeacherWorkbenchPage.tsx`. Paging these routes changes their response for the Teacher too, so the C-M1 FE part must update those callers in the same slice (CM-2).

## 4. Sub-slices

### C-M1 — Roster reads (A07, A09, A10)

**Ready to plan now**: no product decision is open except CM-1 to CM-4 below.

**BE part (one Task Approval, one commit):**
- Add cursor pagination to the three BE1 list routes using the CONV-1 helper `limit_query()` (default 25, max 100; above 100 → 400 `INVALID_REQUEST`, C-D8). Stable ordering by `created_at` then ID; opaque cursor; response keeps `contract` and `items` and adds `next_cursor` (**NEW** for these routes).
- A09: a role-dependent projection. For a School Manager caller: per item only an opaque profile reference and the enrollment state, plus a `total_count` for the class; no `display_name`, no `age_months`, no child media (D-066-69, SRS 2586). For an assigned Teacher: the current fields. The role is taken from the verified assignment, never from the request.
- A10: the consent list keeps its fields for Teachers. For a School Manager, child names are already absent (the list carries IDs and states); the item `child_id` is replaced by the same opaque reference A09 uses, so the two lists can be joined without exposing more (CM-4).
- No write route changes. Consent writes stay excluded (MGR-5, D-066-62).
- **Files (proposed allowlist):** `interfaces/http/routers/be1_registry.py`, `contracts/schemas/be1_runtime.py`, `interfaces/http/openapi_contract.py` and its amendments module, BE1 contract and unit tests, and `tests/integration/.../test_be1_postgres_api.py` for paging and projection. Exact paths are fixed in the C-M1 Task Approval.
- **Checks:** contract catalog test; unit tests for the cursor; PostgreSQL integration on a disposable database (`be1_acceptance` name rule; never `sketch2life_m2_s1a`, never ports 5432 or 5433); repository validators.

**FE part (after the BE part is verified and the web branch is reconciled, O-9):**
- `modules/school-manager/be1/services/classService.ts` and `managerBusinessService.ts`: page parameters and `next_cursor`.
- `ClassesPage.tsx` and `SchoolOverviewPage.tsx`: "load more" with the cursor; empty and error states kept distinct.
- `RosterConsentPage.tsx`: the School Manager roster shows counts and opaque references only; the consent label function maps the BE lowercase values (CM-3).
- `shared/api/backendApi.tsx` and the Teacher screens `T05ClassesScreen.tsx`, `TeacherWorkbenchPage.tsx`: follow the page shape without changing what the Teacher sees.
- Tests next to each changed module.

**Acceptance:** list defaults and maximum as C-D8; replaying a cursor returns the same next page; the School Manager response never contains a name or an age (asserted in the BE test and in the FE test); Teacher screens unchanged apart from paging.

### C-M2 — W-LESSON exact version review (A12, A13, G06)

- **Gate:** owner answers O-6a (binding option A hash snapshot, or B immutable version row), O-6b (superseded pending-grant outcome) and O-6c (decision precondition), asked one at a time from the MGR-6 contract (roadmap §8). Then MGR-6 contract Draft 2 and its review.
- **BE part:** as roadmap §5.4, from base `08439b22` or later (G0 closed). Files: `routers/lesson_library.py`, `contracts/schemas/lesson_library.py`, `infrastructure/lesson_library/service.py`, `tables.py` only if option B, OpenAPI files, `test_lesson_library_api.py`.
- **FE part:** MGR-9 slice M9-C unchanged.

### C-M3 — W-ASSIGN first assignment (B02, G02)

- **Gate:** owner answers O-3a (source of verified same-organization Teachers), O-3b (candidate fields and privacy), O-3c (UC-12 kept separate) and O-3d (assignment revision token), asked one at a time from the MGR-3 contract. Then MGR-3 contract Draft 2 and its review. D-066-62 already settles eligibility.
- **BE part:** as roadmap §5.3; 200 + revision (SRS 1650); `Idempotency-Key` (C-D5); one active Teacher under concurrency.
- **FE part:** MGR-9 slice M9-B unchanged.

### C-M4 — W-CAP class creation (B01, G01) — blocked

- Blocked while Billing is frozen (owner, 2026-11-18): admission needs Billing B-1 and B-2 (D-066-63, D-066-66).
- Until then the class-create control stays disabled in the UI (MGR-9 M9-A), and the BE route is not changed by C-M.

### C-M5 — UC-12 archive, suspension, reassignment (G09) — deferred

- UC-12 needs O-3c and, for suspension, Billing B-5. Recommendation: keep it out of the first Phase C pass and plan it after C-M3 (CM-6).

## 5. Order and queue

1. C-M1 BE, then C-M1 FE.
2. C-M2 or C-M3, whichever the owner names first (CM-5); each needs its own contract answers first.
3. C-M4 when Billing is unfrozen; C-M5 after C-M3.

The BE parts join the one-at-a-time BE queue after FR-C-08 and SEED-1 (and PAY-0 if PD-8 keeps it there). FE parts run one at a time in the web app and only on a verified BE slice. Every FE part needs the web branch reconciled to a base that contains the BE slice; today the web branch `297a28b1` does not contain CONV-1 or S-LL.

## 6. Owner questions (one at a time, with the SRS or decision sentence)

| ID | Question | Recommendation |
|---|---|---|
| CM-1 | O-L3SCOPE, for the touched School Manager rows only: may C-M change A07, A09, A10 and B02, although the M2 freeze calls the BE1 surface "a frozen compatibility surface to be deprecated later" (D-171 item 7)? The SRS target routes (1649, 1650) and the current web callers use them | Yes, for these rows only; the 86 untouched operations stay under O-L3SCOPE |
| CM-2 | Apply C-D8 paging (default 25, max 100) to the three BE1 lists, and update the Teacher callers in the same FE slice? | Yes |
| CM-3 | A10: the FE adopts the BE lowercase consent states, with no BE rename? | Yes; the BE values are the frozen contract |
| CM-4 | A10 for the School Manager: replace `child_id` with the opaque reference used by A09, so the consent list exposes no more than the roster (D-066-69: "counts and opaque references only")? | Yes |
| CM-5 | O-SEQ for the School Manager: after C-M1, W-LESSON (C-M2) or W-ASSIGN (C-M3) first? | W-LESSON: G0 is closed, its routes are already page-called, and its contract draft exists |
| CM-6 | Keep UC-12 (G09) out of the first Phase C pass and plan it after C-M3? | Yes |

O-6a..c (C-M2) and O-3a..d (C-M3) are asked from their own contracts when that sub-slice starts, not here.

## 7. Not verified

- The exact fields the A09 and A10 routes return today were read from the register (P2 audit) and the FE types in `backendApi.tsx`, not from a run.
- Whether any other web or mobile caller reads A07, A09 or A10 (the search covered `apps/web/src` at `297a28b1` only).
- The opaque-reference format for profiles (to be fixed in the C-M1 Task Approval).
- Whether the BE1 integration tests can run on the owner's machine after CONV-1 (the fixture amendment of CONV-1 applies).

No code, test or command was run for this draft beyond read-only searches.
