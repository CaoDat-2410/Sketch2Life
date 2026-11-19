# C1 - Independent implementation review (round 1)

- **Reviewer model / effort:** Sonnet 5.5 (`claude-sonnet-5-5`), high. Read-only. I ran `npm run test`, `npm run lint`, `npm run build` and a 5x repeat of the school-manager vitest folder. I installed nothing, ran no git write command and used no network. The only file written is this report.
- **Date:** 2026-11-19. **Worktree:** `D:\GitHub\Sketch2Life\.worktrees\ui`, branch `codex/fe-ui-web-remediation`, base `c42d913a`.
- **Target:** the uncommitted diff in `apps/web` (3 modified files, +93/-3) plus the untracked `apps/web/src/modules/school-manager/pages/__tests__/ManagerScreens.test.tsx`.
- **Plan:** `PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT4_20261119.md` sections 3, 4, 7. Plan review: `C1_MGR9_DRAFT4_REVIEW_R3.md` (READY WITH NOTES).

## 1. Is the code change exactly slice S1?

**Yes.** The only source file touched is `apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts`, in `parentGroups` (hunk at lines 62-73).

- `new URLSearchParams({ limit: "50" })` became `new URLSearchParams()`.
- `cursor` is still set only when present.
- `"?" + queryString` is appended only when the query string is non-empty, so the first page has no trailing `?`.
- One English code comment was added (SRS 21.1). It is not user-visible.
- `git status` for `apps/web` lists only the 3 modified files and the new `pages/__tests__/` folder. `apps/web/dist` (from my build) is git-ignored (`git check-ignore` confirms).
- No other service function, page or message was changed.
- The change matches section 3 and plan review P3-4. The URL contract is `...parent-groups` for page 1 and `...parent-groups?cursor=next+page` for a cursor.

## 2. Test-by-test check (plan sections 3 and 4)

| Plan item | Where | Exists | Would fail on regression? |
|---|---|---|---|
| S1 update "lists parent groups with an opaque cursor" | `managerBusinessService.test.ts:43-49` | yes, URL `...?cursor=next+page` | yes: any `limit=` or reordering breaks the exact URL |
| S1 "first page without a limit" | `:51-57` | yes, exact URL with no `?` | yes: catches `limit` and a trailing `?` |
| S1 "never sends a limit" | `:59-65` | yes, `parentGroups(undefined)` and `parentGroups("c")`, `toHaveLength(2)` plus `not.toContain("limit=")` | yes, and not vacuous: the length check proves both calls were captured |
| S2-1 paging | `managerBusinessPages.test.tsx:113-146` | yes: per-cursor `mockImplementation` (review P3-3 applied), first call `(undefined, anything)` via `toHaveBeenNthCalledWith`, Tiếp gives `("c2", anything)`, Tiếp disabled when `next_cursor` is null, Trước gives `(undefined, anything)` | yes. Waits use `findByText`/`waitFor` because the buttons are disabled while loading. The first page hides during loading, so `findByText(g2)` cannot match stale g1 |
| S2-2 retry key | `:148-180` | partly: network error keeps the key (call 2 reuses `key-1`); 400 `AdminBe1Error` clears it (call 3 mints `key-2`); success "clears" it (call 4 mints `key-3`) | network and 4xx: yes. **Success: no, see P2-1** |
| S2-3 access grants cursor | `ManagerScreens.test.tsx:96-115` | yes: `accessGrants` last called with `("org-test", { state, audience_kind, cursor: "c2" })`; button disappears when the cursor is null | cursor assertion: yes. Merge assertion: weak, see P3-1 |
| S2-4 decision key | `:117-144` | yes, reason case only (A, A, B, A) | yes for key reuse, reason change and return-to-A. APPROVE path not covered, see P3-2 |

For S2-3 and S2-4 I checked the selectors against `ManagerScreens.tsx`: the label `Lý do yêu cầu chỉnh sửa` is at `:261`, the button text "Yêu cầu chỉnh sửa" at `:264`, "Tải thêm yêu cầu" at `:231`, and the key is the fifth argument of `decideAccessGrant` (`:176`; the test reads `call[4]`). The decide signature at `:167` is `[grant id, revision, version, decision, reason]`, which is what the test varies.

**Hygiene.**

- Global state is cleaned up. `ManagerScreens.test.tsx:88-93` runs `cleanup`, `vi.restoreAllMocks`, and `delete window.sketch2lifeConfig/sketch2lifeAuth`.
- The `crypto` stub is cleared by `vi.unstubAllGlobals()` in the `afterEach` at `managerBusinessPages.test.tsx:11-15`. `restoreMocks: true` is set in `vite.config.ts`.
- Spies are on the `backendApi` and `managerBusinessService` objects, as the plan specified.
- Fixtures are complete typed objects. `npm run build` type-checks them (`tsc -b` covers `src`), and the only cast is the `assignments` mock (`as unknown as ...` at `ManagerScreens.test.tsx:82`). I ran the school-manager folder 5 times with no flake.

## 3. Intent, language, secrets

- No invented product intent. Fixtures use `org-test`, `org-qa`, `grant-N`, `lesson-N`; behaviour pinned is existing behaviour (plan section 4).
- No English user-visible string added. The page strings used in the tests are the existing Vietnamese ones. The fixture strings the tests add are Vietnamese ("Nhóm g1", "Mất kết nối", "Khóa yêu cầu trùng.", "Giáo án mẫu"). English appears only in test titles, code comments and technical fixture values (`PENDING_REVIEW`, `vi-VN`), none of it rendered text.
- No BE URL, real id or secret. The only token-like value is the fake `"unit-test-id-token"` (`ManagerScreens.test.tsx:77`), the same pattern as `PortalEntryPage.auth.test.tsx`. It is a lowercase string, not an uppercase `TOKEN = ...` constant, so it does not hit the known validator rule. I did not run `validate_repository_security.py` (outside the allowed commands).

## 4. Numbers

| Command | Baseline | Now |
|---|---|---|
| `npm run test` | 4 files / 18 tests | **5 files / 24 tests, all pass** (+2 service, +2 pages, +2 ManagerScreens = +6, matches S1 + S2) |
| `npm run lint` | exit 0, 28 warnings | **exit 0, 28 warnings** (`grep -c "warning react"` equals the baseline log's count; 0 warnings mention `__tests__`) |
| `npm run build` (`tsc -b && vite build`) | exit 0 | **exit 0**, built in 424 ms |
| repeat of `vitest run src/modules/school-manager` x5 | n/a | 19/19 passed every time |

## 5. Findings

### P1 - none

### P2

- **P2-1. "Success clears the key" is not actually pinned.** Plan section 4 item 2 requires: "assert success clears the key". In `managerBusinessPages.test.tsx:148-180` the successful create is call 3, which came after the 4xx. At that point `retryKey` is already `null`, so call 3 mints `key-2` itself. If `setRetryKey(null)` were removed from the success path (`ParentGroupsPage.tsx:88`), `retryKey` would still be `null`, call 4 would still mint `key-3`, and the test would pass. The success branch only matters when it follows an unknown-outcome failure that left a key. The fix is to make a success follow a kept key: network failure (key-1), resend succeeds with `key-1`, then submit a new name and assert it gets `key-2`. A test that did this would fail if the key were not cleared.

### P3

- **P3-1. S2-3 merge check cannot tell merge from replace.** `ManagerScreens.test.tsx:96-115`: page 2 is `[grant 2, grant 1]`, so replacing the list with page 2 also yields one `lesson-1` and one `lesson-2`. It catches a missing dedupe (two `lesson-1`) but not "replaced instead of merged". Return only `grant 2` on page 2 plus a duplicate case, or assert both are present in a fixed order (`ManagerScreens.tsx:149-153` keeps current items first).
- **P3-2. S2-4 does not run the APPROVE path.** Plan section 4 item 4 describes a first flow (tick the review checkbox, click "Duyệt công khai", same key on a repeat). The implementation tests only `REQUEST_CHANGES` with reasons A, B, A. The reason-change rule is covered; the APPROVE key (signature with an empty reason, checkbox flow) is not. Add one APPROVE failure-retry assertion, or record the narrowing in the evidence note.
- **P3-3. Possible timing sensitivity.** `managerBusinessPages.test.tsx:171-177`: after `findByText(/Đã tạo nhóm/)` the test immediately edits the input and clicks "Tạo nhóm". In `ParentGroupsPage.tsx:86-101` the success text appears before `finally { setCreating(false) }`, and both inputs are disabled while `creating` is true. It passed 5/5 here because the mocks resolve in microtasks, but a waited-for enabled state (`await waitFor(() => expect(input.hasAttribute("disabled")).toBe(false))`) would remove the dependency on scheduling.
- **P3-4. S2-1 does not assert the list is shown only for the requested page.** Weaker point only: `findByText(/Nhóm g2/)` proves page 2 is rendered, and the "Trước" step proves page 1 again. It does not assert that g1 is gone after Tiếp. The loading state hides the list, so it is covered indirectly. No action needed.
- **P3-5. Plan wording.** Plan section 4 item 3 says the access-grant test sets `window.sketch2lifeAuth = { getIdToken, ... }`. The test supplies `signIn`, `getIdToken` and `signOut`, which is a superset of what the page needs. No action.

## 6. Verdict

**ACCEPTABLE WITH NOTES** - P1: 0, P2: 1, P3: 5.

Slice S1 is exact and minimal, the S2 tests exist and are mostly sound, the numbers are as expected (24 tests, lint 28 warnings, build exit 0), there is no leaked global state, no invented intent, no English user text and no secret. The one real gap is P2-1: the "success clears the key" assertion passes even if that behaviour regressed. I recommend fixing P2-1 before the commit (a small test-only change) and treating the P3 items as optional.

## 7. Summary

- Reviewer: Sonnet 5.5 high, read-only; report at `D:\GitHub\Sketch2Life\tmp\phase-bc\reviews\C1_IMPL_REVIEW_R1.md`.
- Code change is exactly S1 (`managerBusinessService.ts` `parentGroups`: no `limit`, `?` only for a non-empty query); nothing else changed.
- Numbers: test 5 files / 24 tests pass (baseline 4 / 18); lint exit 0 with 28 warnings (equal to baseline); build exit 0.
- P2-1: the "success clears the key" test is vacuous (retryKey is already null at that point) and should be reworked so a success follows a kept key; P3-1 (merge vs replace), P3-2 (APPROVE path), P3-3 (timing), P3-4, P3-5 are optional.
- Verdict: ACCEPTABLE WITH NOTES (P1 0 / P2 1 / P3 5).
