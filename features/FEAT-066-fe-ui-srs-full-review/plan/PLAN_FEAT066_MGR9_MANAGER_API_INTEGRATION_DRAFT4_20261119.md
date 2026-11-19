# FEAT-066 MGR-9 / C-W1 Manager alignment plan — Draft 4

**Status:** DRAFT. Written by the goal under the program approval; independent review pending. It changes no source.
**Supersedes:** Draft 3 (10,041 B, `52BFA651…`; review R2 of 2026-11-19, Sonnet 5.5 high: NOT READY, 1 P1 / 2 P2 / 7 P3, report `tmp/phase-bc/reviews/C1_MGR9_DRAFT3_REVIEW_R2.md`; §10 maps each finding to its fix) and, before it, Draft 2 (16,575 B, `D2843E0D…`). Review R1 of Draft 2 (Sonnet 5.5, high, 2026-11-19): NOT READY, 2 P1 / 5 P2 / 6 P3; report `tmp/phase-bc/reviews/C1_MGR9_DRAFT2_REVIEW_R1.md`. §9 maps each finding to its fix. Draft 1 and the owner's notes are untouched.
**Goal task:** program task C1 "C-W1 Manager alignment" (paging 25/100, idempotency key retry, `INVALID_IDEMPOTENCY_KEY` message), reduced to what the FE can fix now.

## 1. What Draft 3 changes

Draft 2's two FE fix slices rested on a misreading of the FE. Draft 3 and Draft 4 replace them with the slice the reviewer called safe:

| Draft 2 | Draft 3 |
|---|---|
| F1: bind the ParentGroups retry key to the payload | **Dropped.** The page cannot reach that state: while a retry key is held the name input is disabled (`ParentGroupsPage.tsx:153`), and a 4xx already clears the key (`:95-99`). Row 15 is **M**. The "cannot abandon an unknown-outcome retry" defect is recorded OPEN (SRS silent), not built |
| F2: Vietnamese message in `backendApi.errorFromResponse` | **Moved to C2.** The route that can raise `INVALID_IDEMPOTENCY_KEY` (parent-group create) goes through `adminApiRequest` in `be1Client.ts`, which reads `code` and `message` from the top level only. On the integration branch the BE already sends the CONV-1 top-level body with a Vietnamese message. The `be1Client` body parsing is part of C2 "the seven callers read the CONV-1 envelope" and is done once there |
| F3: regression tests | Kept, made concrete (§4) |
| paging | New concrete slice S1: the `limit: "50"` literal (§3) |

## 2. Pins and baselines

| Item | Value |
|---|---|
| Web branch (FE truth) | `codex/fe-ui-web-remediation` = `c42d913a6b4f538b8711f3c0ad28f6643f253421`. `git fetch` at implementation time; the teammate branch `origin/codex/fe-ui-web-remediation` was equal to it when this draft was written |
| BE baseline A (the base of the web branch) | `origin/dev` = `ba295f11`: Lesson Library body `{"detail":{"code","message"}}`, English messages |
| BE baseline B (what the final PR candidate tests against) | `feature/feat066-be-integration` at `5e20faf7`: CONV-1 envelope (`error_envelope.py`, `app.py`) for `/api/be1/v1`, `/api/lesson-library/v1`, `/api/platform-admin/v1`, `/api/auth/v1`, `/api/teacher/v1/`: top-level `code`, Vietnamese `message`, `INVALID_IDEMPOTENCY_KEY` on payload mismatch |
| SRS | D-209 copy, 701,157 B, `B9B1F42D…`. §21.1 line 1632-1642: cursor paging, default 25, max 100, idempotency key per state-changing command, keep the key when retrying the same logical command ("giữ nguyên key khi retry cùng một command logic", line 1639); §21.4 line 1695; §9.8 line 847, `message` row line 854 |
| FE files (from Draft 2 §2.2) | unchanged at `c42d913a`; sizes and 8-hex hashes verified by review R1 |

Every statement about BE behaviour below says which baseline it refers to.

## 3. Slice S1 — the paging literal (SRS §21.1)

- **Finding:** `managerBusinessService.ts:65` sends `limit=50` for the parent-group list. 50 is legal (at most 100) but is neither the SRS default (25) nor named. Access grants already send no `limit` and follow `next_cursor` (`backendApi.tsx:446-448`, `ManagerScreens.tsx:140-160`).
- **Decision (goal, SRS §21.1 line 1642):** omit `limit`; the BE default of 25 applies on both baselines (MGR-7, `lesson_library.py:529`).
- **Files:** `apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts`, `apps/web/src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts`.
- **Change:** build the query with only `cursor` when present, and append `?` plus the query string only when the query string is non-empty (otherwise the first-page URL would end in `?`). No other code change.
- **Tests:** update the existing test "lists parent groups with an opaque cursor" (expected URL `…/parent-groups?cursor=next+page`); add "lists the first page without a limit" (expected URL `…/parent-groups`, no query string); add "never sends a limit" (for `parentGroups(undefined)` and `parentGroups("c")` the requested URL does not contain `limit=`).

## 4. Slice S2 — regression tests, no code change

All in `apps/web/src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx` unless noted, using the file's existing mocks (`vi.spyOn(managerBusinessService, …)`, `vi.stubGlobal("crypto", …)`):

1. **ParentGroups paging:** `parentGroups` mocked to return one item with `next_cursor: "c2"`, then a second page; assert: the first load calls `parentGroups(undefined, expect.anything())` (the page passes `(cursor, signal)`, `ParentGroupsPage.tsx:56`); clicking "Tiếp" (accessible name "Tiếp", icon `aria-hidden`, `:222`) calls `parentGroups("c2", expect.anything())` and renders the second page; "Trước" returns to `undefined`; with `next_cursor: null` "Tiếp" is disabled (`:220`). Wait with `findBy…`/`waitFor`, because the buttons are disabled while loading (`:207`, `:220`).
2. **ParentGroups retry key:** `createParentGroup` mocked to reject with a network error; assert that after the failure the same key is sent on resubmit with the same name; assert a 4xx (`AdminBe1Error` status 400, code `INVALID_IDEMPOTENCY_KEY`) clears the key so the next submit mints a new one (the `randomUUID` stub is a counter returning a different value per call); assert success clears the key. This pins the current behaviour (`ParentGroupsPage.tsx:81-99`).
3. **Access grants cursor:** a new test file `apps/web/src/modules/school-manager/pages/__tests__/ManagerScreens.test.tsx` rendering the exported `M01PublicationReviewPage` (`ManagerScreens.tsx:276`; the inner `ManagerApiReviewPage` is not exported). It sets the runtime bridge as `PortalEntryPage.auth.test.tsx:41-50` does (`window.sketch2lifeConfig = { organizationId }`, `window.sketch2lifeAuth = { getIdToken, … }`, cleaned up afterwards) and uses `vi.spyOn(backendApi, …)` for `assignments`, `accessGrants`, `teacherLesson` and `decideAccessGrant` (the page calls them as properties). Fixtures: an `AccessGrant` (`backendApi.tsx:125-140`, `audience_kind: "PUBLIC"`, `state: "PENDING_REVIEW"`) and, for item 4, a `TeacherLessonDetail` whose `current_version.version_id` equals the grant's and has non-null `content`; a `showToast` stub. Assertions: page 1 with `next_cursor`, click "Tải thêm yêu cầu" (`:231`), `backendApi.accessGrants` called with the cursor, list merged by `access_grant_id`.
4. **Decision key stability:** same grant, revision, version, decision and reason after a failed decision sends the same key; a changed reason sends a new key (`ManagerScreens.tsx:167-172`). Same file as item 3. Flow: wait for the lesson to load, tick the review checkbox (`:258`), click "Duyệt công khai" (`:265`), mock `decideAccessGrant` to reject once, click again and assert the same key (fifth argument) on both calls. For the reason case use `REQUEST_CHANGES` (non-empty reason required, `:164-165`): reason "A", fail, change to "B" gives a different key; returning to "A" gives the first key again (the map is keyed by the whole signature, `:167-172`).

## 5. Corrected gap view (27 routes, Draft 2 §4 table otherwise unchanged)

Reclassified: row 15 is **M** (no payload/key divergence is reachable). G-5 and G-7 are removed as C-W1 gaps (G-7 moves to C2 as the `be1Client` error body work). Rows 18 and 19 (PATCH and DELETE lesson, `If-Match` only) are treated as follows: SRS §21.4 line 1697 requires a key for state-changing commands; `If-Match` versioning is accepted by the BE for lesson PATCH/DELETE on both baselines, so these rows stay **M for C1** and the question "does `If-Match` alone satisfy §21.4" is recorded OPEN for the BE task C4. Row 25 (DELETE upload-session) stays **M for C1**: SRS §21.2 line 1658 ("Expected state/version; idempotent") settles that the BE should take an expected state or version, and neither the BE nor the FE sends one. That is a BE-first item for C4, not an OPEN question and not an FE change. Totals for C1: 20 M and 7 BE-first rows. The seven, with the owner task of each (route table of Draft 2 §4 kept as `D2843E0D…` for the other 20 rows):

| Row | Route | Gap | Owner task |
|---:|---|---|---|
| 3 | GET /api/platform-admin/v1/accounts | offset paging, not cursor (SRS §21.1) | C5 |
| 4 | POST /api/platform-admin/v1/accounts | no `Idempotency-Key` (§21.4) | C5 |
| 5 | PATCH /api/platform-admin/v1/accounts/{account_id} | no `Idempotency-Key` (§21.4) | C5 |
| 7 | GET /api/be1/v1/organizations/{org}/classes | unpaginated (§21.1) | new BE paging item for class, profile and consent lists, parked until the BE queue has a slot |
| 9 | GET …/classes/{class}/profiles | unpaginated | same item |
| 10 | GET …/classes/{class}/consents | unpaginated | same item |
| 16 | GET …/lessons | default 50, SRS default 25 (§21.1) | C4 |

Row 25 and rows 18, 19 are M here and carry the C4 notes above. The Lesson Library routes (access grants, parent groups, lessons) are not in the SRS §21.2 table; their rows are verified FE-to-BE only, not against the SRS. Teacher `T05ClassesScreen` uses `backendApi`; Manager BE1 routes use `be1Client`; this matters for C2.

## 6. OPEN items (SRS silent; each stays parked)

| Item | SRS searched | Status |
|---|---|---|
| Parent-group rename, archive, invitation, membership, revoke; abandoning an unknown-outcome group-create retry | "parent group", "nhóm phụ huynh", "invitation", "lời mời", "membership"; §31.3 (line 2569) | OPEN, no route or lifecycle contract |
| Consent writes by the School Manager | §31.3 | OPEN, excluded |
| M9-A class create with capacity | §21.2 line 1649 | Billing deferred (program §6) |
| M9-B Teacher assignment candidate list and replacement | §21.2 line 1650 | Parked until C6 settles O-3a..d from the SRS |
| M9-C exact-version review route | §31.2 (line 2553) | Parked until C6 |
| Manager view and feedback of SCHOOL-scope lessons | §31.3 table row | OPEN |
| `If-Match` alone as the key for PATCH/DELETE lesson (§21.4) | §21.4 line 1695-1697 | OPEN, for C4 |
| UI-copy check script | none exists in the repository | defined in §7 as a manual check |

## 7. Verification (commands run from `apps/web` of the web worktree; `apps/web` is npm-locked: `package-lock.json`, CI `npm ci --prefix apps/web` and `npm run check --prefix apps/web` in `.github/workflows/ci.yml:97-104`, not a member of the pnpm workspace)

| # | Command | Rule |
|---|---|---|
| 1 | `npm run test -- src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx src/modules/school-manager/pages/__tests__/ManagerScreens.test.tsx`, then `npm run test` (all `vitest run`) | baseline: 4 files, 18 tests, all pass (run at the start of the goal, `tmp/phase-bc/c1/web_baseline_test.log`); 0 new failures |
| 2 | `npm run build` (`tsc -b && vite build`) | baseline exit 0; typecheck 0 new errors |
| 3 | `npm run lint` (`oxlint`) | baseline exit 0 with the warnings recorded in `tmp/phase-bc/c1/web_baseline_lint.log`; 0 new warnings |
| 4 | UI-copy check (manual, recorded): every user-visible string added or changed in the diff is Vietnamese; no raw BE text and no "API request failed" is rendered by the touched pages; S1 and S2 add no new string | recorded in the evidence note |
| 5 | repository root: `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `git diff --check` | exit 0 |

`npm run check` runs rows 2, 3 and 1 in sequence and may replace them. If `node_modules` is missing at implementation time the install step is `npm ci --prefix apps/web`; the goal does not run installs itself (it was done for it under the program's step 0.2). No browser runtime, database or network step is part of C1.

## 8. Commit

One commit on `codex/fe-ui-web-remediation`, by explicit paths: `managerBusinessService.ts`, the three test files, this plan (Draft 4), the reviews copied to `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/` as `C1_MGR9_DRAFT2_REVIEW_R1_20261119.md`, `C1_MGR9_DRAFT3_REVIEW_R2_20261119.md` and the round-3 report, and the evidence note. The goal decision of §11 is appended to `DECISIONS.md` on the integration branch, not on the web branch. The owner's modified and untracked files in `.worktrees/ui` are never staged. Before the work: `git fetch` and merge `origin/codex/fe-ui-web-remediation` locally if the teammate pushed; list their commits in the log and final report.

## 9. Review R1 findings and their fixes

| ID | Fix |
|---|---|
| P1-1 | F1 dropped; row 15 M; unknown-outcome abandon recorded OPEN (§1, §5, §6) |
| P1-2 | F2 moved to C2 with the `be1Client` finding (§1) |
| P2-1 | S1: omit `limit`, tests (§3) |
| P2-2 | §5: rule stated, rows 18, 19, 25 stay M, the `If-Match` question recorded OPEN for C4; totals recomputed |
| P2-3 | §2: both BE baselines pinned and labelled |
| P2-4 | §7: exact commands, baseline comparison, manual UI-copy check defined |
| P2-5 | §3 and §4: test files, mocks and assertions named |
| P3-1 | §6 first row |
| P3-2 | §2: SRS quoted in Vietnamese |
| P3-3 | §5 last sentence: client per row family |
| P3-4 | §5: the Lesson Library routes are not in SRS §21.2 |
| P3-5 | Gap numbering reduced to the slices of this draft; no G-n labels remain |
| P3-6 | Not needed for C1; dropped |

## 10. Review R2 findings and their fixes (Draft 4)

| ID | Fix |
|---|---|
| P1-1 | §7: npm commands, CI reference, baseline numbers, `npm run check`, install note |
| P2-1 | §5: row 25 stays M for C1; the SRS §21.2 line 1658 expected-state gap is a BE-first item for C4, stated separately from the `If-Match` question |
| P2-2 | §5: the seven BE-first rows listed with route, gap and owner task |
| P3-1 | §11 decision text for the goal log; C2 brief item recorded there |
| P3-2 | §5 now carries the seven rows; the Draft 2 table is pinned by hash for the remaining 20 |
| P3-3 | §3: the "never sends a limit" test is concrete |
| P3-4 | §3: `?` appended only for a non-empty query |
| P3-5 | §4 item 1: concrete assertions |
| P3-6 | §8: review files copied to `evidence/notes/` with names |
| P3-7 | no action |
| Review R2 §3 | §4 items 3 and 4: file, bridge, spies and fixtures stated; the escape hatch removed |

## 11. Goal decision (to be appended to FEAT-066 `DECISIONS.md` with the C1 task, lineage "goal v2")

C1 is reduced to S1 and S2 (§3, §4). The retry-key rule is pinned by tests and not changed, because the page already keeps the key through unknown outcomes and clears it on a 4xx (`ParentGroupsPage.tsx:95-99`, `:153`). The `INVALID_IDEMPOTENCY_KEY` message is not fixed in `backendApi.errorFromResponse`; it is part of C2. **C2 brief item:** `be1Client.ts` (`adminApiRequest` `:48-76` and `adminBe1Request` `:33-40`) reads `code` and `message` from the top level only; C2 makes both accept the `detail`-wrapped body of `origin/dev` and the CONV-1 top-level body, and always shows a Vietnamese message (never a raw English BE string or "API request failed"). SRS basis: §21.1 line 1642 (default 25), §21.1 line 1639 (key per logical command), §9.8 (message localized, line 854).
