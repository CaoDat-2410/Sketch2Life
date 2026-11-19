# C1 — Independent cold re-check of MGR-9 Draft 3 (round 2)

- **Reviewer model / effort:** Sonnet 5.5 (`claude-sonnet-5-5`), high. Read-only, separate session. Only file reads, `git show`/`rev-parse`, hashing, `ls`, `grep` were used. No install, test, database, Docker, network or git-write command.
- **Date:** 2026-11-19. **Round:** 2 (round 1 = `C1_MGR9_DRAFT2_REVIEW_R1.md`, NOT READY, 2 P1 / 5 P2 / 6 P3).
- **Target:** `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT3_20261119.md`
- **Size / SHA-256 (computed first):** 10,041 B, `52BFA6517EF3CC9499D5EE3625C5D416570EB33E8AAE24BF308D7679A86275E8`
- **Context checked:** web worktree HEAD still `c42d913a…`; `origin/codex/fe-ui-web-remediation` = `c42d913a…` (equal, as the plan §2 says).

## 1. Is every R1 finding fixed? (question 1)

| R1 | Result | Evidence |
|---|---|---|
| P1-1 (F1 phantom) | **Fixed.** F1 dropped, row 15 = M, abandon-retry OPEN (§1, §5, §6) | Matches `ParentGroupsPage.tsx:153`, `:95-99`, `:162` |
| P1-2 (F2 wrong client) | **Fixed by moving to C2**, reason stated correctly (`be1Client` top-level parse) (§1) | See P3-1 about the scope reduction record |
| P2-1 (paging literal) | **Fixed** by S1 (§3) | Literal is at `managerBusinessService.ts:65`; test at `managerBusinessService.test.ts:43-49` — both correct. See P3-3, P3-4 for wording gaps |
| P2-2 (gap rule) | **Mostly fixed** (§5): rule stated, rows 18/19/25 stay M, `If-Match` question OPEN for C4. Verified: lesson PATCH/DELETE require `If-Match` on the integration branch (`lesson_library.py:231-258`, `_strong_revision` `:83-98`). One loss: see P2-1 | |
| P2-3 (baselines) | **Fixed** (§2 rows A and B, "every statement says which baseline") | |
| P2-4 (commands) | **Not fixed — new error.** See P1-1 | |
| P2-5 (tests) | **Partly fixed**; two assertions are vague (P3-3, P3-5); items 3-4 are feasible (§3 below) | |
| P3-1 .. P3-6 | P3-1, P3-2 (Vietnamese quote at line 1639 — verified in SRS), P3-3, P3-4, P3-5, P3-6 handled as mapped in §9. One residual: the 27-row table now lives only in a superseded draft (P3-2) | |

## 2. Findings

### P1 — blocking

**P1-1. §7 uses the wrong package manager; the commands do not match how `apps/web` is built and tested.**
- Plan §7 header: "the package manager of the install step is pnpm"; rows 1-3 use `pnpm test -- --run`, `pnpm build`, `pnpm lint`.
- Real repo: `apps/web` is **not** a pnpm workspace member. `pnpm-workspace.yaml` lists only `apps/mobile`, `apps/ui-mobile`, `packages/art-renderer`. `apps/web` has its own `package-lock.json` (npm lockfile) and no `pnpm-lock.yaml` entry for it. CI installs and checks it with npm: `.github/workflows/ci.yml:97` (`cache: npm`, `cache-dependency-path: apps/web/package-lock.json`), `:101` `npm ci --prefix apps/web`, `:104` `npm run check --prefix apps/web`. `apps/web/README.md:8-9` says `npm ci` / `npm run dev`. Root scripts also route to npm: `package.json` `check:active-ui` = `npm --prefix apps/web run check`, `test:active-ui` = `npm --prefix apps/web run test`.
- The installed tree is npm's: `apps/web/node_modules/.package-lock.json` exists (created 2026-11-19 14:36 during this review window; it was absent at the start of the first read, so another session installed it). The `pnpm` install of program step 0.2 covered the workspace root and mobile only.
- Failure scenario: an implementer following §7 runs `pnpm test` in `apps/web` outside any workspace; it either resolves a different dependency tree than the npm-locked CI tree or fails; the baseline-vs-after comparison the plan demands is then not comparable to CI.
- Fix: use `npm run test` / `npx vitest run <paths>`, `npm run build`, `npm run lint` (or `npm run check`, which is exactly build + lint + test, `apps/web/package.json` `check`). For the two touched test files: `npm run test -- src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx` (path filters are passed through to `vitest run`). Name `npm ci --prefix apps/web` as the install step if `node_modules` is missing at implementation time.

### P2 — must fix before approval

**P2-1. The SRS-backed expected-state gap on DELETE upload-session was dropped.** Draft 2 row 25 carried "matches with note G-6" (SRS §21.2 line 1658: "Expected state/version; idempotent"). Draft 3 §5 lists row 25 as "DELETE upload-session with nothing", lumps it under the `If-Match` OPEN item, and §6 has no row for it. `If-Match` is not involved for upload sessions at all (plan's reasoning does not cover it), and the SRS settles this clause (it is not an SRS-silent item). Add an explicit line: row 25 stays M for C1; the missing expected-state/version is a BE-first item for C4 (SRS §21.2 line 1658).

**P2-2. "20 M / 7 with a BE-first or OPEN note" is arithmetically right but not checkable from Draft 3.** Count verified against Draft 2's table: gaps were rows 3, 4, 5, 7, 9, 10, 15, 16 (8); removing row 15 gives 7 gaps (3, 4, 5, 7, 9, 10, 16) and 20 M — correct. However §5 says "Draft 2 §4 table otherwise unchanged", i.e. the authoritative table sits in a document the plan itself supersedes, and the seven rows are not mapped to their owner (rows 3-5 → C5; rows 7, 9, 10 → new BE item for class/profile/consent paging; row 16 → C4 lessons default 25). Without this a reader cannot tell what "BE-first" means for each row. Carry the 7-row mapping (route, owner task) into Draft 3, or pin Draft 2 §4 by file hash as a normative table.

### P3 — notes

- **P3-1. Scope reduction against the program text is not recorded as a decision.** Program C1 names three goals (paging 25/100, key retry, `INVALID_IDEMPOTENCY_KEY` message). Draft 3 delivers paging (S1), pins the existing retry behaviour with tests (S2-2), and moves the message to C2. The coordinator should log it once as a goal decision (D-066-81+ lineage) and make sure C2's brief contains the `be1Client` top-level parse (`be1Client.ts:67-71` and the same pattern in `adminBe1Request`, `:33-40`: `error.message`/`error.code` read from the top level only).
- **P3-2.** Draft 3 §5 refers to "Draft 2 §4 table" for the 27 routes (see P2-2) — also, the "Clauses used" line numbers from Draft 2 §1 are not repeated; the SRS pin in §2 is enough for C1.
- **P3-3. S1 test 3 is vague/near-vacuous.** "never sends a limit above 100 (asserts that no call of the service in this file carries a `limit` parameter greater than 100)". After S1 no call carries any `limit`; only `parentGroups` builds a query (`managerBusinessService.ts:64-71`). Replace with: for `parentGroups(undefined)` and `parentGroups("c")` the URL contains no `limit=`.
- **P3-4. S1 implementation detail missing.** The current code builds `"/parent-groups?" + query.toString()` (`managerBusinessService.ts:67-69`). Removing `limit` leaves a trailing `?` when no cursor is given; the new test expects `…/parent-groups` with no query. State: append `?` + query only when the query string is non-empty.
- **P3-5. S2 item 1 assertion "the page does not assume 50 items" is not testable as worded.** The page has no page-size constant (`ParentGroupsPage.tsx:36-52`, `:196-225`). Replace with concrete assertions: first load calls `parentGroups(undefined, <AbortSignal>)`; clicking "Tiếp" (accessible name "Tiếp"; icon is `aria-hidden`, `:222`) calls `parentGroups("c2", <AbortSignal>)` and renders the second page; "Trước" returns to `undefined`; with `next_cursor: null` "Tiếp" is disabled (`:220`). Use `expect.anything()` for the signal because the page passes `(cursor, signal)` (`:56`).
- **P3-6.** Plan §8 lists "the review record" as a file to commit; the reviewer reports live under `tmp/phase-bc/reviews/` which is git-ignored. Say which review file (copied into `features/FEAT-066-…/evidence/`) is meant.
- **P3-7.** Plan §2 cites SRS §21.1 line 1632-1642 for the paging default; the paging sentence is line 1642 and the key sentence is line 1639 — both inside the stated range; fine. No action.

## 3. Are S1 and S2 implementable as written? (question 3)

| Item | Feasible? | Notes (file:line) |
|---|---|---|
| S1 change | Yes | After fixing P3-4. Both BE baselines default parent-groups to 25 (`origin/dev` `lesson_library.py:529`; integration branch `:535`) |
| S1 test 1 (update existing) | Yes | Existing test `managerBusinessService.test.ts:43-49`; new expected `…/parent-groups?cursor=next+page`; `adminApiRequest` is mocked at `:3-9` |
| S1 test 2 (first page, no query) | Yes | Needs P3-4 |
| S1 test 3 | Yes, but rewrite (P3-3) | |
| S2-1 ParentGroups paging | Yes | `vi.spyOn(managerBusinessService, "parentGroups")` already used in `managerBusinessPages.test.tsx:70-74`; use `mockResolvedValueOnce` per page; wait with `findBy…`/`waitFor` because the buttons are disabled while `loading` (`:207`, `:220`) |
| S2-2 retry key | Yes | Existing pattern `vi.stubGlobal("crypto", { randomUUID })` (`managerBusinessPages.test.tsx:70`); give it a counter so each mint differs; network error = plain `Error` (not `AdminBe1Error`) keeps the key (`ParentGroupsPage.tsx:95-99`); `new AdminBe1Error("…", 400, "INVALID_IDEMPOTENCY_KEY")` (constructor `be1Client.ts:3-12`) clears it. After a failure the name input is disabled but the submit button stays enabled while `displayName` is non-empty (`:153`, `:159`), so the resubmit click works; after success the name is cleared (`:87`) so the test must re-enter it. Assert `randomUUID` call count and each `createParentGroup` key argument. `restoreMocks: true` is set in `vite.config.ts` and the file already does `unstubAllGlobals` in `afterEach` (`:12-16`) |
| S2-3 access-grants cursor | **Yes, without new test infrastructure** | The page is exported as `M01PublicationReviewPage` (`ManagerScreens.tsx:276`; the inner `ManagerApiReviewPage` at `:53` is not exported — import the exported name). Precedent for the runtime bridge exists: `PortalEntryPage.auth.test.tsx:41-50` sets `window.sketch2lifeConfig = { organizationId }` and `window.sketch2lifeAuth = { getIdToken, … }` and cleans up at `:75-76`; `hasFirebaseAuthBridge()` (`backendApi.tsx:268-270`) and `configuredOrganizationId()` (`:264-266`) then pass. `backendApi` is an exported object (`:355`), so `vi.spyOn(backendApi, "assignments" | "accessGrants" | "teacherLesson" | "decideAccessGrant")` works because the page calls them as properties (`ManagerScreens.tsx:93`, `:98`, `:133`, `:147`, `:176`). Fixtures needed: an `AccessGrant` (`backendApi.tsx:125-140`, `audience_kind: "PUBLIC"`, `state: "PENDING_REVIEW"`) and, for item 4 only, a `TeacherLessonDetail` with `current_version.version_id` equal to the grant's and non-null `content`. Pass a `showToast` stub. The plan's "only if … otherwise OPEN" escape hatch can therefore be removed |
| S2-4 decision key stability | Yes | Same file and mocks. Flow: wait for the lesson to load, tick the review checkbox (`:258`), click "Duyệt công khai" (`:265`); mock `decideAccessGrant` to reject once; click again and assert the same 5th argument (key) on both calls. For "changed reason → new key": `REQUEST_CHANGES` needs a non-empty reason (`:264`, `:165`); the reason textarea is not cleared after a failure (it resets only when the selection changes, `:116-124`), so type reason "A", fail, change to "B", assert a different key; returning to "A" returns the first key (the map is keyed by the full signature, `:167-172`) |

Neither item 3 nor 4 needs a new mock library or a fetch layer; both are feasible with `vi.spyOn` plus the existing runtime-bridge pattern.

## 4. Did the fixes add new errors? (question 2)

- **20 M / 7:** correct (P2-2 explains how it was checked).
- **Test descriptions vs real files/page text:** file names, test title "lists parent groups with an opaque cursor" (`managerBusinessService.test.ts:43`), `AdminBe1Error`, `ParentGroupsPage.tsx:81-99`, `ManagerScreens.tsx:140-160` and `:167-172`, the control texts "Tiếp", "Tải thêm yêu cầu" (`ManagerScreens.tsx:231`) are all accurate. Vague assertions are listed as P3-3/P3-5.
- **Commands:** wrong package manager — P1-1.
- **No new SRS conflict or invented intent** found: S1 is directly §21.1 line 1642; S2 only pins existing behaviour; the OPEN list in §6 is consistent with my R1 search results (no new SRS reading was needed).
- **Baselines:** the §2 claim that baseline B returns the CONV-1 top-level body with `INVALID_IDEMPOTENCY_KEY` and a Vietnamese message is correct (`error_envelope.py:80`, `app.py` handler `:581-600`).

## 5. Verdict

**NOT READY** — P1: 1, P2: 2, P3: 7 (P3-7 is "no action", so 6 actionable).

The conceptual repair from R1 is sound and the slice is the right size. What blocks approval is one concrete, easy fix: replace every `pnpm` command with the npm commands that CI and the lockfile use (P1-1). With P1-1 fixed and P2-1/P2-2 added as two short paragraphs, I expect a READY WITH NOTES re-check (a short round 3 limited to §5 and §7).

Safe to build once P1-1 is corrected: S1 (with P3-4 wording), S2-1, S2-2, S2-3, S2-4 as described in §3 of this report.

## 6. Summary

- Draft 3: 10,041 B, SHA-256 `52BFA651…6275E8`.
- R1 findings: 12 of 13 fixed or correctly re-scoped; P2-4 (commands) fixed in form but wrong in content.
- New error: package manager (`pnpm` vs the npm-locked `apps/web`).
- S1 and S2 items 1-4 are feasible with existing mocks.
- Report: `D:\GitHub\Sketch2Life\tmp\phase-bc\reviews\C1_MGR9_DRAFT3_REVIEW_R2.md`.
