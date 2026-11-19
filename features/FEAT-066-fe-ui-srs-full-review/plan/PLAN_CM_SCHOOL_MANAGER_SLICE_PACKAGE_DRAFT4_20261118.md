# FEAT-066 C-M — School Manager per-role slice package (Draft 4)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package plans Phase C work for the School Manager role only. It authorizes no code, migration, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 3 (23,609 B, `B78DD5FF…`). Its round-3 review was NOT READY with 0 P1, 2 P2 and 7 P3 (`evidence/notes/CM_COLD_REVIEW_DRAFT3_20261118.md`, 3,317 B, `C861311E…`). §12 maps each round-3 finding to its fix; §10 and §11 keep the round-2 and round-1 maps.
- **Owner delegation:** on 2026-11-18 the owner asked that open package questions be settled from the SRS rather than asked one by one. §6 therefore lists the CM-1 to CM-12 answers as settled per the SRS or the package recommendation; the owner can override any of them when approving the package.
- **What C-M is:** roadmap Draft 4 §4 row C ("per-role slices") for the School Manager, and register Draft 4 §5 row "C-M / W-*". It splits the role's work into five sub-slices (§4), each with a BE part and an FE part, in the order of the roadmap's FE integration path (§5.6: BE verified first, then one FE slice per app).
- **Relation to MGR-9:** the FE plan `PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` (review R2: ACCEPT) defines the FE slices M9-A, M9-B and M9-C. C-M reuses them unchanged as the FE parts of C-M4, C-M3 and C-M2, and adds the FE part of C-M1, which MGR-9 left unowned ("Class-list pagination is not part of M9-B; it needs separate approved scope").
- **NEW in this package:** the sub-slice names C-M1 to C-M5, the questions CM-1 to CM-12, the contract `Be1ClassRosterSummaryV1`, the cursor helper, the School Manager denials of §4, and every response field marked NEW below.

## 1. Authority and inputs

| Input | Location | Bytes | SHA-256 (prefix) |
|---|---|---:|---|
| Working SRS (D-209, D-066-64) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D…` |
| Mismatch register Draft 4 | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` (git-ignored) | 41,798 | `0F3F35FD…` |
| Roadmap Draft 4 | `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` | 42,628 | `63710A9F…` |
| CONV-1 package Draft 5 (approved, D-066-71) | `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT5_20261118.md` | 47,483 | `3FCF4741…` |
| CONV-1 implementation evidence | `evidence/notes/CONV_1_IMPLEMENTATION_EVIDENCE_20261118.md` (committed in `2dddc607`) | 16,315 | `4498AF17…` |
| MGR-9 FE plan Draft 1 (web worktree, untracked) | `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` | 43,006 | `1547F32C…` |
| MGR-9 review R2 (ACCEPT) | `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_9_COLD_REVIEW_DRAFT1_R2_20261118.md` | 3,419 | `C235A560…` |
| MGR-2 capacity contract Draft 1 | `plan/PLAN_MGR2_CLASS_CAPACITY_CONTRACT_DRAFT1_20261117.md` | 28,624 | `3F5AEA62…` |
| MGR-3 assignment contract Draft 1 | `plan/PLAN_MGR3_TEACHER_CANDIDATE_ASSIGNMENT_CONTRACT_DRAFT1_20261117.md` | 34,432 | `80762D84…` |
| MGR-6 lesson-version contract Draft 1 | `plan/PLAN_MGR6_IMMUTABLE_LESSON_VERSION_REVIEW_CONTRACT_DRAFT1_20261117.md` | 24,165 | `BEB43ECB…` |
| Decisions (conv1 worktree; uncommitted, carries the D-066-72, D-066-73 and D-066-74 appends) | `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` | 62,660 | `94E68772…` |

Decisions used: D-066-62, D-066-63 as amended by D-066-66 and D-066-67, D-066-65, D-066-68, D-066-69, D-066-71, D-066-73 (PAY-0 queue position), D-066-74 (Billing unfrozen; School Manager pays for the school).

**BE source base:** commit `2dddc607` (CONV-1) on the local-only branch `feature/feat066-conv1` (D-066-71, CV-B). The "Today" column of §3 was checked against this source by the round-1 and round-2 reviews. **FE source base:** `.worktrees/ui`, branch `codex/fe-ui-web-remediation` at `297a28b1`.

**SRS and decision basis per row:**

| Rows | Basis |
|---|---|
| A07, A10 (reads) | SRS 796: the `/v1/organizations/{org}/classes` family covers "Liệt kê/tạo lớp, phân công Teacher, quản lý roster"; SRS 1640: cursor pagination, default 25, maximum 100, explicit and deterministic order (D-066-68 C-D8) |
| A09, A10, session roster, pilot profiles (privacy and read rules) | SRS §31.3 line 2586: Teacher reads "Chỉ field được grant sau khi Teacher chấp nhận invitation và lớp được phân công"; School Manager: "Không đọc profile contents mặc định"; D-066-69 |
| B02, G02 | SRS 1650; D-066-62 |
| B01, G01 | SRS 1649; D-066-63, D-066-66, D-066-67 |
| A12, A13, G06 | FR-PL-05, BR-51, Q168 (line 2924), §31.2 |
| G09 | UC-12 (line 1525) |
| All | §9.8 envelope; uniform 404 and in-scope 403 (C-D4); `Idempotency-Key` (C-D5); revision transport (C-D7) |

## 2. What changed since the register (2026-11-18)

| Fact | Effect on C-M |
|---|---|
| **G0 closed:** S-LL committed as `08439b22` and pushed | Lesson Library rows are no longer blocked by G0. CONV-1 also changed `lesson_library.py`, so C-M2 starts from the queue tip that contains CONV-1 |
| **CONV-1 committed** `2dddc607` (local only) | §9.8 envelope, `X-Request-ID`, uniform 404 / in-scope 403 in the shared guards, `limit_query()`. On `/api/be1/v1` (in `CONV1_PREFIXES`), `map_code` already turns a 404 `*_NOT_FOUND` such as `CLASS_NOT_FOUND` into `RESOURCE_NOT_FOUND`. CONV-1 left BE1 list paging out (Draft 5 line 236) and provides no cursor helper |
| **O-PRIV decided** (D-066-69) | Applies server-side to every School-Manager-callable route that returns child names or ages (§4 C-M1). Routes that return other child material are listed as debt (§8) |
| **The A09 consent gate cannot pass today:** `consent_is_effective` needs a state the store's `CHECK` does not allow (`pending`, `revoked` only, `be1_models.py` line 241), so every non-empty class answers 409 | A09 paging is untestable and is deferred to the consent slice (MGR-5); C-M1 does not page A09 |
| **The cited A09 test is outdated:** `test_pending_consent_stays_pending…` in `test_be1_postgres_api.py` (lines 723–860) runs as a School Manager and creates a profile, which is Teacher-only; the CONV-1 evidence records it as failing with 403, so its 409 assertion (lines 757–759) is never reached | C-M1 **repairs** it: profile creation and the A09 read use a class-scoped Teacher actor, and its admission 409, `start` 409, device-canvas 401, stored consent and enrollment rows, audit and outbox assertions are kept; new cases are added (§4) |
| **Billing unfrozen** (D-066-74): the owner's lane builds Billing B-1 to B-5 | B01 and G01 (C-M4) wait for Billing B-1 and B-2 to be built, not for a freeze. D-066-74 also settles that the School Manager pays for the school |
| **O-L3SCOPE open** | A07, A09, A10, B01, B02, the session roster and pilot profiles sit on the BE1 compatibility surface (CB). CM-1 settles it for the C-M rows only |
| **O-5 open; consent writes excluded** (MGR-5, D-066-62) | A10 stays read-only; consent meaning and `record_consent` validation are not changed by C-M |
| **O-9 open for the web branch** | Every C-M FE part waits until the web branch is reconciled to a base containing the BE slice |
| **BE queue:** FR-C-08 → SEED-1 → PAY-0a, 0b, 0c (D-066-73, PD-8); D-066-74 leaves the order of C-M1 and Billing B-1 after PAY-0c open | CM-10 settles C-M1 before Billing B-1 |

## 3. Row map

| Row | Endpoint / capability | Today (BE `2dddc607`, web `297a28b1`) | Target | Sub-slice |
|---|---|---|---|---|
| A07 | GET `/api/be1/v1/organizations/{organization_id}/classes` | Unpaginated; `created_at` order | Cursor page | C-M1 |
| A09 | GET `…/classes/{class_id}/profiles` | Unpaginated; `roles=None`, so any assignment row of the organization (including org-wide `teacher` rows with `class_id` NULL, `guide`, `observer`, `school_admin`) reaches it. Returns `display_name` and `age_months`. Consent gate: 409 `CONSENT_NOT_EFFECTIVE` plus an audit row whenever any active profile lacks effective consent, which today is every non-empty class | School Manager: `Be1ClassRosterSummaryV1` (count only, CM-3), no gate (CM-5). Full fields: class-scoped `teacher` row only (CM-11); others 403. Not paged (deferred to MGR-5) | C-M1 |
| A10 | GET `…/classes/{class_id}/consents` | Unpaginated; `recorded_at` newest first; allows `school_admin` and `teacher`; returns `consent_id`, `child_id`, `purpose_ref`, `state` (`pending`, `revoked`), `effective`. `child_id` and `purpose_ref` are free 1–128 character strings that `record_consent` stores without a profile check; an org-wide `teacher` row also passes | Paged; School Manager response `Be1ConsentListManagerV1` without `child_id` and `purpose_ref` (CM-4); Teacher items only for a class-scoped `teacher` row (CM-11) | C-M1 |
| Session roster | GET `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` | Allows `school_admin`; returns `display_name` of admitted children (`be1_sessions.py` lines 299–360). No web caller | 403 for `school_admin` (CM-2) | C-M1 |
| Pilot profiles | GET `…/sessions/{session_id}/pilot-profiles` | Allows `school_admin`; returns `child_id` and required `display_name`; local/test synthetic only (`be1_registry.py` 326–396). No web caller | 403 for `school_admin` (CM-2) | C-M1 |
| A12 | GET `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Current head only | Exact immutable version read | C-M2 (W-LESSON) |
| A13 | POST `…/access-grants/{access_grant_id}/decision` | Not bound to a reviewed version | Decision bound to the exact version (O-6a..c) | C-M2 |
| G06 | Exact LessonVersion read; grant-bound decision | Absent | New read and binding | C-M2 |
| B02 | POST `/api/be1/v1/classes/{class_id}/assignments` | 201 without revision; no key; trusts the body `subject`; FE helper posts an org-level path | 200 + revision; key; one active Teacher | C-M3 (W-ASSIGN) |
| G02 | Teacher-candidate discovery | Absent | Same-organization verified Teachers (D-066-62) | C-M3 |
| B01 | POST `…/organizations/{organization_id}/classes` | No capacity admission; no key | Billing admission | C-M4 (W-CAP) — **waits for Billing B-1 and B-2** |
| G01 | Capacity-safe class creation | Absent | Billing B-2 | C-M4 — **waits for Billing B-1 and B-2** |
| G09 | Class archive, suspend, reassignment (UC-12) | Absent | UC-12 flows | C-M5 — deferred (CM-12) |

**Web callers of A07, A09, A10** (confirmed by both reviews): `be1/services/classService.ts`, `managerBusinessService.ts`, `ClassesPage.tsx`, `RosterConsentPage.tsx` (its class picker uses A07), `shared/api/backendApi.tsx`, and the Teacher screens `modules/teacher/pages/T05ClassesScreen.tsx` and `TeacherWorkbenchPage.tsx`. The session roster and pilot profiles have no web caller.

## 4. Sub-slices

### C-M1 — Roster reads and School Manager privacy

**Gate:** package approved with the §6 answers; queue slot open (CM-10); branch set (CM-9). The FE part also needs O-9.

**BE part (one Task Approval, one commit):**

1. **Cursor helper (NEW):** `encode_cursor` and `decode_cursor` in `interfaces/http/api_conventions.py`, following the base64-JSON precedent of `parent_profile_repository.py` (lines 347–395). The cursor carries the last sort key and ID and is bound to the route and its scope; a cursor that does not decode, or decodes for another scope, gives 400 `INVALID_REQUEST` with field error `cursor` / `INVALID_FORMAT`.
2. **Paging on A07 and A10** with `limit_query()` (default 25, max 100; above 100 → 400). Response keeps `contract` and `items` and adds `next_cursor` (**NEW**). Order: A07 `created_at` ascending then `class_id`; A10 `recorded_at` descending then `consent_id` descending (today's direction, made deterministic, SRS 1640). **A09 is not paged** (CM-7).
3. **A09 for a School Manager (CM-3, CM-5):** a separate response contract `Be1ClassRosterSummaryV1` (**NEW**: `contract`, `class_id`, `active_profile_count`). It carries no contents, so the consent gate does not run for it and no audit row is written. In OpenAPI the operation documents both bodies as `oneOf`, discriminated by `contract`, with one example each.
4. **A09 and A10 Teacher rule (CM-11):** full A09 fields and full A10 items only for a caller with a `teacher` assignment row whose `class_id` equals the requested class (SRS 2586: "lớp được phân công"). `require_assignment` cannot express a class-scoped check (its coverage accepts rows with `class_id` NULL), so the route adds an explicit post-check on the returned rows, as `create_profile` does around `be1_registry.py` line 438. Every other row of the organization (org-wide `teacher` with `class_id` NULL, `guide`, `observer`) gets 403 `ACTION_NOT_ALLOWED`. **403, not the 404 that `create_profile` returns:** the caller holds an assignment in the class's organization, so the class is in scope and C-D4 gives 403 for an in-scope refusal. **This is a stated behaviour change** for those rows; no web caller relies on them (round-2 and round-3 reviews). For an allowed Teacher the gate, the 409 and its audit row stay exactly as today.
5. **A10 for a School Manager (CM-4):** a distinct page contract `Be1ConsentListManagerV1` (**NEW**) whose items have `consent_id`, `state` and `effective` only, without `child_id` and `purpose_ref` (both are free caller-typed strings). The operation documents the two page contracts as `oneOf`, discriminated by the page `contract` field. Teachers keep the current page contract.
6. **Session roster and pilot profiles (CM-2):** a `school_admin` caller gets 403 `ACTION_NOT_ALLOWED`; Teachers are unchanged. The existing response models stay as they are. The pilot-profile tests in `test_be1_synthetic_pilot_postgres.py` (T9, around lines 1325, 1386, 1400 and 1411) call the route as a School Manager today; their harness gains a class-scoped Teacher principal for those calls, and a School Manager 403 case is added.
7. **OpenAPI:** the new contracts, `next_cursor`, the 400 cursor error, the 403 rows and examples, through `openapi_contract.py` and its amendments module (which already handles `oneOf`).
8. **Frozen snapshots:** `openapi-runtime-frozen.json`, `openapi-client-projection-frozen.json` and `API_CONTRACT.md` under FEAT-063 and FEAT-047, and `OPENAPI_FEAT063_REV45_20261101.json`, pin these operations. No test reads them. They stay unchanged, and the C-M1 evidence note records the drift.

**Proposed allowlist (exact paths fixed in the C-M1 Task Approval):** `interfaces/http/api_conventions.py`; `interfaces/http/routers/be1_registry.py`; `interfaces/http/routers/be1_sessions.py`; `contracts/schemas/be1_runtime.py`; `interfaces/http/openapi_contract.py` and `openapi_contract_amendments.py`; the CONV-1 tests that touch these routes; BE1 contract and unit tests; `tests/integration/.../test_be1_postgres_api.py` (the outdated test is **repaired** with a class-scoped Teacher actor, keeping its admission, `start`, canvas, stored-row, audit and outbox assertions; a class-scoped and an org-wide Teacher fixture are added on `be1_acceptance` following the pattern at lines 233–265; the new cases below are added); `tests/integration/.../test_be1_synthetic_pilot_postgres.py` (step 6); Bruno request 012 (list profiles), 050 (pilot profiles) and the related requests (L5 per-slice update); the C-M1 evidence note.

**Required PostgreSQL cases** (disposable database whose name contains `be1_acceptance`; never `sketch2life_m2_s1a`; never ports 5432 or 5433; **run by the owner**):
- School Manager A09 → 200 `Be1ClassRosterSummaryV1` with the right count, and no audit row;
- class-scoped Teacher A09 on a class with a pending consent → 409 `CONSENT_NOT_EFFECTIVE` with its audit row;
- org-wide Teacher, guide and observer on A09 and A10 → 403;
- School Manager A10 → `Be1ConsentListManagerV1`, items without `child_id` and `purpose_ref`; class-scoped Teacher A10 → current items;
- A07 and A10 paging: default 25, `limit=101` → 400, cursor replay, foreign cursor → 400, stable order across pages;
- School Manager on the session roster and pilot profiles → 403; Teacher unchanged; the T9 pilot-profile tests pass with the Teacher principal;
- the repaired outdated test passes with all its kept assertions.

**Other checks:** contract catalog; unit tests for the cursor helper and the role rule; repository validators.

**FE part (one Task Approval, after the BE part is verified, the web branch is reconciled (O-9), and before M9-A and M9-B, which edit the same files):**
- `classService.ts` and `managerBusinessService.ts`: page parameters and `next_cursor` for A07 and A10; the Manager roster call reads `Be1ClassRosterSummaryV1`.
- `ClassesPage.tsx` and the `RosterConsentPage.tsx` class picker: "load more" with the cursor.
- `RosterConsentPage.tsx`: the School Manager roster shows the count only; the initial-and-age rows are removed; the consent table reads `Be1ConsentListManagerV1` (record number, state, effective; the purpose column is removed) and the label map uses the BE values (CM-6).
- `shared/api/backendApi.tsx`, `T05ClassesScreen.tsx` and `TeacherWorkbenchPage.tsx`: follow `next_cursor` to completion for the class list and consents, because these screens join consents to profiles and look a class up by ID. A09 for Teachers is unchanged.
- Tests next to each changed module.

**BE-before-FE window (CM-8):** between the BE commit and the FE commit (local development only; no deployed environment): Teacher screens read the first 25 classes and consents; `ClassesPage` and the class picker show 25 classes; `RosterConsentPage` breaks on the summary body (`setProfiles(result.items)` on a body without `items`).

**Acceptance:** list defaults and maximum as C-D8; invalid or foreign cursor → 400; School Manager responses of A09 and A10 contain no name, no age, no `child_id` and no `purpose_ref`; School Manager is refused on the session roster and pilot profiles; Teacher responses unchanged except paging and the stated 403s; the routes in §8 are outside this acceptance.

### C-M2 — W-LESSON exact version review (A12, A13, G06)

- **Gate:** owner answers O-6a, O-6b and O-6c from the MGR-6 contract, one at a time; then MGR-6 contract Draft 2 and its review.
- **BE part:** as roadmap §5.4, from the queue tip that contains CONV-1.
- **FE part:** MGR-9 slice M9-C unchanged.

### C-M3 — W-ASSIGN first assignment (B02, G02)

- **Gate:** owner answers O-3a to O-3d from the MGR-3 contract; then MGR-3 contract Draft 2 and its review. D-066-62 already settles eligibility.
- **BE part:** as roadmap §5.3; 200 + revision (SRS 1650); `Idempotency-Key` (C-D5); one active Teacher under concurrency.
- **FE part:** MGR-9 slice M9-B unchanged, after C-M1 FE.

### C-M4 — W-CAP class creation (B01, G01) — waits for Billing B-1 and B-2

Billing is no longer frozen (D-066-74), but admission needs Billing B-1 and B-2 to be built (D-066-63 as amended by D-066-66 and D-066-67). Until then the class-create control stays disabled (MGR-9 M9-A). D-066-74 confirms the School Manager is the payer for the organization's capacity.

### C-M5 — UC-12 (G09) — deferred

UC-12 needs O-3c and, for suspension, Billing B-5 (CM-12).

## 5. Order, branches and queue

1. C-M1 BE, then C-M1 FE.
2. C-M2 or C-M3; the order between them is settled when C-M1 is done.
3. C-M4 after Billing B-1 and B-2; C-M5 after C-M3.

- Each BE part is one Task Approval and one commit on its own local-only branch, cut from the BE queue tip when its slot opens; the pins of this package are refreshed then (CM-9).
- FE parts run one at a time in the web app, only on a verified BE slice, after the web branch is reconciled to a base that contains it (O-9). The web worktree shares the repository, so a local-only BE branch can be merged into it locally on the owner's word. **The web branch is then not pushed** until an owner-approved publication step covers the BE commits it carries.
- Bruno requests are updated in L5 after each slice is verified.

## 6. Settled answers (per the SRS or the recommendation; owner delegation of 2026-11-18)

The owner can override any line when approving the package.

| ID | Point | Settled answer | Basis |
|---|---|---|---|
| CM-1 | O-L3SCOPE for the C-M rows: may C-M change A07, A09, A10, B01, B02, the session roster and pilot profiles, although the M2 freeze calls the BE1 surface "a frozen compatibility surface to be deprecated later" (D-171 item 7)? | Yes, for these rows only; the other untouched operations stay under O-L3SCOPE | SRS 796 names this route family as the School Manager's class and roster surface; the web callers use these routes today |
| CM-2 | Refuse the School Manager (403) on the session roster and the synthetic pilot-profiles route | Yes | SRS 2586 and D-066-69: no profile contents by default; neither route has a School Manager caller, so a refusal is the smallest change |
| CM-3 | A09 for the School Manager returns the count only (`Be1ClassRosterSummaryV1`) | Yes | D-066-69: "counts and opaque references only"; rows without names give the screen nothing |
| CM-4 | A10 for the School Manager drops `child_id` and `purpose_ref` (`Be1ConsentListManagerV1`) | Yes | Both are free caller-typed strings with no profile check, so they can carry profile contents; the validation gap stays as MGR-5 debt (§8) |
| CM-5 | The School Manager summary skips the A09 consent gate | Yes | The gate protects profile contents; a count carries none |
| CM-6 | A10 labels: `pending` → "Đang chờ xác nhận", `revoked` → "Đã thu hồi"; drop the unused "Đã ghi nhận" label; no BE change | Yes | The store allows only `pending` and `revoked` (`be1_models.py` line 241); consent meaning is MGR-5 scope |
| CM-7 | Page A07 and A10 now; defer A09 paging to MGR-5 | Yes | SRS 1640 requires paging, but the A09 gate makes paging untestable until MGR-5 defines effective consent |
| CM-8 | Accept the BE-before-FE window of §4 | Yes | Local development only; there is no deployed environment to break |
| CM-9 | Branch policy: a new local-only branch `feature/feat066-cm1` from the BE queue tip when the slot opens, never pushed, pins refreshed then | Yes, as one decision | Same policy as CONV-1 (D-066-71 CV-B) and SEED-1 (D-066-72 SD-4) |
| CM-10 | Queue: C-M1 BE after FR-C-08, SEED-1 and PAY-0c, and before Billing B-1 | Yes | C-M1 does not depend on Billing; Billing B-1 first needs the Draft 7 revision for the PAY-0 edits (PAY-0 §6.1) and D-066-74 |
| CM-11 | A09 full fields and A10 Teacher items only for a `teacher` row of that class; org-wide `teacher`, `guide` and `observer` rows get 403 | Yes | SRS 2586: a Teacher reads "Chỉ field được grant sau khi Teacher chấp nhận invitation và lớp được phân công" |
| CM-12 | Keep UC-12 (G09) out of the first Phase C pass and plan it after C-M3 | Yes | UC-12 needs O-3c (C-M3) and Billing B-5 |

O-6a..c (C-M2), O-3a..d (C-M3) and the order between C-M2 and C-M3 are settled the same way when those sub-slices start.

## 7. Not verified

- Runtime behaviour: no test was run for this draft; the A09 gate and the outdated test come from source and the CONV-1 evidence.
- FE unit tests and Bruno request content beyond file presence.
- Mobile code outside `apps/`.
- A12, A13 and G06 behaviour beyond route existence (C-M2 re-checks it).

No code, test or command was run for this draft beyond read-only searches.

## 8. Limits and known privacy debt (not changed by C-M1)

C-M does not change consent writes (MGR-5), Parent-group invitations (MGR-4), Billing, payment, or Teacher-only routes. The routes below are reachable by a School Manager and return child material or teacher free text. SRS §31.3 (line 2586 area) denies the School Manager occurrence and child media. Today most are blocked only by consent gates that cannot pass. They are recorded as open privacy debt for the owner, outside C-M1:

| Route (BE1) | Material |
|---|---|
| Checkpoint latest, save, restore (`be1_canvas.py` around 560, 688, 741) | Child canvas content |
| Artifact download (`be1_artifacts.py` around 396; any role) | Child artifacts |
| Gallery list, annotate, publish (`be1_records.py` around 151–196) | Child media, `contributors`, captions and annotations |
| Observation create; portfolio (`be1_records.py` around 403; no role restriction; portfolio answers 409 today) | Child records |
| Session read (`be1_sessions.py` around 262–271; no role restriction; not behind a consent gate) | Free-form session `configuration` (up to 8 KB) |
| Session outcome `teacher_note` (`be1_sessions.py` around 395) | Teacher free text |
| Group `display_name` (`be1_sessions.py` around 1521–1570) | Teacher free text |
| Pilot assistance pending list (`pilot_assistance.py` around 509–560) | `participant_id` and `request_reason` |
| `record_consent` `child_id` and `purpose_ref` (write side) | Caller-typed strings stored without a profile check (MGR-5); C-M1 removes them from the School Manager read |

## 9. Owner-run and evidence rule

PostgreSQL cases are run by the owner, as for CONV-1. The coordinator prepares one command and records the output in the C-M1 evidence note.

## 10. Round-2 findings and their fixes

| Finding | Fixed in |
|---|---|
| CM-R2-01 | §2 row "The cited A09 test is outdated"; §4 allowlist (new class-scoped Teacher fixture) and the named PostgreSQL cases |
| CM-R2-02 | §2 and CM-7: A09 paging deferred to MGR-5; §4 step 2 pages A07 and A10 only; FE Teacher A09 unchanged |
| CM-R2-03 | CM-4 re-grounded: `child_id` is not guaranteed opaque on consent rows, so the School Manager response drops it; §8 records the validation gap |
| CM-R2-04 | §4 step 4 and CM-11: class-scoped `teacher` row only; the 403 for other rows is a stated behaviour change |
| CM-R2-05 | §8 known privacy debt list |
| CM-R2-06 | §4 steps 3 and 5 (`oneOf` by `contract`); CM-2 refuses the School Manager on pilot profiles and the session roster, so no second model is needed |
| CM-R2-07 | §4 step 8: the four snapshot files named; left unchanged with the drift recorded, as in CONV-1 |
| CM-R2-08 | §4 window paragraph and CM-8 cover the School Manager screens |
| CM-R2-09 | CM-5 is a single ask; CM-1 includes pilot profiles; "the other untouched operations" replaces the count |
| CM-R2-10 | §1 basis cites SRS 796 and 1640 |
| CM-R2-11 | §5: the web branch carrying a local BE merge is not pushed before an owner-approved publication step |

## 11. Round-1 findings and where they are now

| Finding | Where |
|---|---|
| CM-R1-01 (P1) | §3 session roster and pilot profiles; §4 step 6; CM-2 |
| CM-R1-02 | §2, §3 A09, §4 steps 3 and 4; CM-5, CM-7 |
| CM-R1-03 | CM-4 |
| CM-R1-04 | §4 FE part and window; CM-8 |
| CM-R1-05 | §5; CM-9 |
| CM-R1-06 | CM-3 |
| CM-R1-07 | §4 steps 1, 2, 3, 5, 7, 8 and the allowlist |
| CM-R1-08 | §3 callers; §4 FE part order |
| CM-R1-09 | §1 basis; §2 O-5 and O-9 |
| CM-R1-10 | §3 A10; CM-6 |
| CM-R1-11 | §2 CONV-1 row |
| CM-R1-12 | §4 step 4; CM-11 |
| CM-R1-13 | §6 single asks |
| CM-R1-14 | §1 pins; NEW markers; §9 |
| CM-R1-15 | §4 allowlist; §5 |

## 12. Round-3 findings and their fixes

| Finding | Fixed in |
|---|---|
| CM-R3-01 (P2) | §4 step 6 and allowlist: `test_be1_synthetic_pilot_postgres.py` named; its T9 calls move to a class-scoped Teacher principal; a School Manager 403 case added; PostgreSQL case list |
| CM-R3-02 (P2) | §1 pins DECISIONS 62,660 B and lists D-066-73 and D-066-74; §2, §3, §4 C-M4 and §5 say C-M4 waits for Billing B-1 and B-2; CM-1 includes B01; CM-10 settles C-M1 before Billing B-1 |
| CM-R3-03 | §4 step 5: distinct page contract `Be1ConsentListManagerV1`, `oneOf` discriminated by the page `contract` |
| CM-R3-04 | §4 step 4: explicit post-check (as `create_profile` does), 403 versus 404 explained under C-D4, SRS 2586 cited for reads, rule applied to A10 too |
| CM-R3-05 | §4 step 8: the CONV-1 precedent claim removed; files stay unchanged and the C-M1 evidence records the drift |
| CM-R3-06 | §4 step 5, CM-4 and acceptance: `purpose_ref` dropped from the School Manager read too |
| CM-R3-07 | §8: file and line for gallery and group `display_name`; session read `configuration` and the pilot assistance pending list added |
| CM-R3-08 | §2 and allowlist: the outdated test is repaired with a Teacher actor and keeps its other assertions |
| CM-R3-09 | §6: each answer has a basis; CM-9 accepted as one branch-policy decision |
