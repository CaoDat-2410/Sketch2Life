# C1 — Independent cold re-check of MGR-9 Draft 4 (round 3)

- **Reviewer model / effort:** Sonnet 5.5 (`claude-sonnet-5-5`), high. Read-only, separate session. Only file reads, `git show`/`rev-parse`, hashing, `ls`, `grep`. No install, test, build, database, Docker, network or git-write command.
- **Date:** 2026-11-19. **Round:** 3 (last under D-171). Earlier rounds: R1 on Draft 2 (NOT READY, 2 P1 / 5 P2 / 6 P3); R2 on Draft 3 (NOT READY, 1 P1 / 2 P2 / 7 P3).
- **Target:** `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT4_20261119.md`
- **Pin (verified first):** 15,614 B, SHA-256 `B88980303E69CA7A5C09E464D839E255758FDD05E244C77685CEFAC007219CD1` — starts `B8898030`, matches.

## 1. Are the R2 findings really fixed?

| R2 | Result | Evidence |
|---|---|---|
| **P1-1** npm commands | **Fixed.** §7 uses `npm run test -- <paths>`, `npm run build`, `npm run lint`, `npm run check`; cites CI. Correct: `apps/web` has `package-lock.json`; `pnpm-workspace.yaml` lists only `apps/mobile`, `apps/ui-mobile`, `packages/art-renderer`; CI `.github/workflows/ci.yml:97` (`cache: npm`), `:101` `npm ci --prefix`, `:104` `npm run check --prefix`. The `check` description is exact: `apps/web/package.json` `check` = `npm run build && npm run lint && npm run test` (so "rows 2, 3 and 1 in sequence" is right). Test path filters after `--` are valid for `vitest run` | OK |
| **P2-1** row 25 | **Fixed.** §5 states row 25 stays M, the SRS §21.2 line 1658 expected-state/version gap is a BE-first item for C4, and says it is not an OPEN question and not an FE change. Verified: the BE abort route takes only the principal and service — no `If-Match`, no key (`lesson_library.py:298-305`, integration branch); FE sends none (R1). SRS line 1658 re-read: "Expected state/version; idempotent" | OK |
| **P2-2** seven-row table | **Fixed.** §5 lists rows 3, 4, 5, 7, 9, 10, 16 with route, gap and owner. All seven match Draft 2's table (rows 3-5 Admin accounts offset paging / no key → C5; rows 7, 9, 10 unpaginated BE1 lists → new BE paging item; row 16 lessons default 50 → C4; BE default 50 at `lesson_library.py:187` on `origin/dev`). 27 − 7 = 20 M is correct | OK (see P3-1) |
| **P3-3** vague limit test | **Fixed.** §3 test 3: for `parentGroups(undefined)` and `parentGroups("c")` the URL contains no `limit=` | OK |
| **P3-4** trailing `?` | **Fixed.** §3 "Change" appends `?` only for a non-empty query; matches the current code shape (`managerBusinessService.ts:64-71`) | OK |
| **P3-5** S2-1 assertions | **Fixed.** Concrete assertions; every cited line checks out: `(cursor, signal)` call at `ParentGroupsPage.tsx:56`; "Trước" disabled when `pageNumber <= 1` at `:207`; "Tiếp" disabled when `loading \|\| !nextCursor` at `:220`; `aria-hidden` icon at `:222` | OK (see P3-3) |
| **P3-6** review copies | **Fixed.** §8 names the three files under `evidence/notes/` | OK |
| R2 §3 (items 3-4) | **Fixed.** Escape hatch removed; file, bridge, spies, fixtures named | OK (see P3-4, P3-5) |
| P3-1 (decision record) | §11 gives the goal-decision text and the C2 brief item; accurate (`be1Client.ts:48-76`, `:33-40`) | OK |

## 2. Baseline numbers (§7)

Read `tmp/phase-bc/c1/web_baseline_test.log`: `Test Files 4 passed (4)`, `Tests 18 passed (18)`, `exit=0` (vitest 5.0.5). Counted in the tree: `PortalEntryPage.auth.test.tsx` 5, `app.test.tsx` 3, `managerBusinessPages.test.tsx` 5, `managerBusinessService.test.ts` 5 = 18 tests in 4 files. **§7 is correct.** `web_baseline_build.log` ends `built in 1.82s`, `exit=0`; `web_baseline_lint.log` ends `exit=0` with warnings (28 lines containing "warning"), including three in `ManagerScreens.tsx` (`:76`, `:118`, `:122`) that the new test file does not change. "Baseline exit 0 with the warnings recorded" is accurate.

## 3. Are the test descriptions implementable with existing mocks?

| Item | Verdict | Check |
|---|---|---|
| S1 (3 tests) | Yes | Existing test `managerBusinessService.test.ts:43-49` is the one to update; `adminApiRequest` mocked at `:3-9` |
| S2-1 | Yes | `vi.spyOn(managerBusinessService, "parentGroups")` is already used (`managerBusinessPages.test.tsx:70-74`). Needs per-cursor mock answers (P3-3) |
| S2-2 | Yes | `vi.stubGlobal("crypto", …)` precedent at `:70`; `AdminBe1Error(message, status, code)` constructor `be1Client.ts:3-12`; network failure = plain `Error` → key kept; 400 `AdminBe1Error` → key cleared (`ParentGroupsPage.tsx:95-99`); name input disabled but submit button stays enabled (`:153`, `:159`); success clears name (`:87`) so re-enter it |
| S2-3 / S2-4 | Yes | `M01PublicationReviewPage` exported (`ManagerScreens.tsx:276`); runtime bridge pattern at `PortalEntryPage.auth.test.tsx:41-50`, cleanup `:75-76`; `FirebaseAuthBridge` needs only `getIdToken` (`backendApi.tsx:29-33`, `signIn`/`signOut` optional) so `{ getIdToken, … }` type-checks; `hasFirebaseAuthBridge`/`configuredOrganizationId` at `:264-270`; `backendApi` object export `:355`; page calls `backendApi.assignments` (`ManagerScreens.tsx:93`), `accessGrants` (`:98`, `:147`), `teacherLesson` (`:133`), `decideAccessGrant` (`:176`) as properties, so `vi.spyOn` works. UI texts and lines verified: "Tải thêm yêu cầu" `:231`; review checkbox `:258`; "Duyệt công khai" `:265`; reason rule `:164-165`; key map `:167-172`; fifth argument of `decideAccessGrant` is the key (`backendApi.tsx:449`). `restoreMocks: true` in `vite.config.ts` and `afterEach` cleanup pattern as in the existing file |

## 4. Findings

### P1 — none
### P2 — none

### P3 — notes (none blocks implementation)

- **P3-1. §5 pins the other 20 rows to a file the commit will not contain.** "route table of Draft 2 §4 kept as `D2843E0D…`": Draft 2 is an untracked file in `.worktrees/ui` and §8 lists only Draft 4 among the plan files to commit. A later reader cannot resolve the hash. Either add Draft 2 to the commit list (it is the authoritative 27-row table) or note that the table is archived in `tmp/` with that hash.
- **P3-2. Stale headings.** §1 is titled "What Draft 3 changes" with columns "Draft 2 | Draft 3" while saying "Draft 3 and Draft 4"; §9's P2-4 line still reads as if §7 were the original. Cosmetic; keep §10 as the current mapping.
- **P3-3. S2-1 needs a per-cursor mock, not a short `mockResolvedValueOnce` chain.** The flow calls `parentGroups` three times (first load → `c2` → back to `undefined`). Say `mockImplementation((cursor) => …)` keyed by cursor, otherwise the "Trước" step gets no mocked value and fails.
- **P3-4. New test files are type-checked by `npm run build`.** `tsconfig.app.json` has `"include": ["src"]`, `noUnusedLocals` and `noUnusedParameters`, so `tsc -b` covers the tests. Fixtures must be complete typed objects: `AccessGrant` (14 fields, `backendApi.tsx:125-140`), `TeacherLessonDetail` and `LessonContent` (`:159-198`, e.g. `locale`, `target_age_band_ref`, `script_direction`, `script_following_allowed`, `activities`). Worth one sentence in §4 item 3/4.
- **P3-5. §3 cites `lesson_library.py:529` for "both baselines".** That line number is `origin/dev`; on `feature/feat066-be-integration` the same default is at `:535`. Behaviour is the same on both; label the line.
- **P3-6. New test file adds to the lint scope.** Baseline has 28 warnings; "0 new warnings" is the right rule, but say that oxlint also scans the new `ManagerScreens.test.tsx`.

## 5. Verdict

**READY WITH NOTES** — P1: 0, P2: 0, P3: 6.

All R1 and R2 findings are fixed or correctly re-scoped; baseline numbers match the log (4 files / 18 tests); commands match the repo (npm-locked `apps/web`); S1 and S2 items 1-4 are implementable with the existing mocks and the established runtime-bridge pattern. No new SRS conflict, wrong route, wrong field or invented intent was found. The six P3 items are wording or hygiene and can be applied while implementing.

### Slice safe to build now
S1 (omit `limit`, append `?` only for a non-empty query; update one test, add two) and S2-1 to S2-4 as written in §3-§4, using the P3-3 and P3-4 refinements. Not part of C1: the `be1Client` error-body work (C2), and every BE-first or OPEN item in §5-§6.

## 6. Summary

- Draft 4: 15,614 B, `B8898030…`.
- Verdict READY WITH NOTES, P1 0 / P2 0 / P3 6.
- Report: `D:\GitHub\Sketch2Life\tmp\phase-bc\reviews\C1_MGR9_DRAFT4_REVIEW_R3.md`.
