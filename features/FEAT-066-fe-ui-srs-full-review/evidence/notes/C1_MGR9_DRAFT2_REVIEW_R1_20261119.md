# C1 — Independent cold review of MGR-9 Draft 2 (round 1)

- **Reviewer model / effort:** Sonnet 5.5 (`claude-sonnet-5-5`), high. Read-only, separate session. Nothing was run except `git show`, hashing, `wc`, `grep` and file reads. No database, Docker, network, git-write or test command.
- **Date:** 2026-11-19. **Task:** program task C1 ("C-W1 Manager alignment").
- **Target:** `.worktrees/ui/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT2_20261119.md`

## 0. Pins verified

| Item | Result |
|---|---|
| Plan file | 16,575 B, SHA-256 `D2843E0D609F2535EA6D04444BA7FC8502449ED4DB499BD4D6FEB8039AB76940` — matches the pin `d2843e0d` |
| Web branch | `.worktrees/ui` HEAD = `c42d913a6b4f538b8711f3c0ad28f6643f253421` (matches plan §2.1); `git status` shows only FEAT-066 docs dirty, no `apps/` path |
| FE files (plan §2.2) | All 8 sizes and the first 8 hex of SHA-256 match (`git show c42d913a:<path>`) |
| BE files (plan §2.2) | All 5 sizes and first-8-hex hashes match `origin/dev` = `ba295f11…` (MGR-7 commit `08439b22` is an ancestor — confirmed) |
| SRS | 701,157 B, SHA-256 starts `b9b1f42d` — matches D-209 pin. Clause line numbers in the plan (§9.8 = 847, §21.1 = 1632, §21.2 = 1643, §21.4 = 1695, §31.2 = 2553, §31.3 = 2569) are correct |
| Draft 1 / owner notes | Not opened (not needed; nothing compared) |

One pin the plan does not carry: the program's BE truth for the final PR is **`feature/feat066-be-integration` (`5e20faf7`)**, not `origin/dev`. It already contains CONV-1 (merge `732111ee`; `error_envelope.py` introduced by `2dddc607`). See P2-3.

## 1. Findings

### P1 — blocking

**P1-1. G-5 / slice F1 describes a scenario the page cannot reach; F1 as written is a no-op.**
- Plan §5 G-5 and §6 F1: "If the user edits the group name before retrying, the same key is sent with a different payload."
- Real FE: while a retry key is held the name input is **disabled** — `ParentGroupsPage.tsx:153` `disabled={creating || requestOutcomeUnknown}` where `requestOutcomeUnknown = retryKey !== null` (`:105`). `setDisplayName` is reachable only from that input's `onChange` (`:149`) and from the success path (`:87`, which also clears the key at `:88`). So key and payload can never diverge. The button label for that state is "Gửi lại cùng yêu cầu" (`:162`) and the helper text (`:166`) says the retry reuses the same key — the page is deliberately built so the name cannot change.
- The "4xx clears the key" rule the plan says to keep already exists (`:95-99`, `:99` sets `retryKey` to `null` for 4xx except 408). So a `400 INVALID_IDEMPOTENCY_KEY` would already clear the key and the next submit mints a fresh one.
- Failure scenario for the plan: an implementer adds a name-bound key, adds tests, and nothing observable changes; or an implementer realises the input is disabled and re-enables editing, which is a **product decision** (the SRS is silent on the group-create UX) that the plan neither states nor justifies.
- A real, different defect exists in the same area (P3-1): the user cannot abandon an unknown-outcome retry without reloading the page.
- Required: drop G-5 as a gap (reclassify row 15 as M), or restate F1 as an explicit, SRS-backed UX change. Only the first is supportable today.

**P1-2. G-7 / slice F2 targets the wrong module and the wrong error shape.**
- Plan §5 G-7 and §6 F2: change `errorFromResponse` in `apps/web/src/shared/api/backendApi.tsx`; claims "the English BE message … is shown as-is".
- Real FE: the only Manager route that can raise `INVALID_IDEMPOTENCY_KEY` for a payload mismatch is parent-group create, and it goes through `managerBusinessService.createParentGroup` → `adminApiRequest` in `modules/school-manager/be1/services/be1Client.ts:48-76`, **not** through `backendApi.backendRequest`/`errorFromResponse` (`backendApi.tsx:280-295`). `adminApiRequest` reads `message` and `code` from the **top level** of the body (`be1Client.ts:67-71`), never from `detail`.
  - On `origin/dev` (BE returns `{"detail":{"code","message"}}`, plan §3) that yields `AdminBe1Error("API request failed (400).", 400, "HTTP_ERROR")`. The BE English text is **not** displayed, and the code `INVALID_IDEMPOTENCY_KEY` is lost. The user sees an English generic string, which is itself a §9.8 localisation gap (SRS §9.8 `message` row, line 854: "đã Việt hóa").
  - On the integration branch (CONV-1, `error_envelope.py:80`, `app.py:581-598`) the BE already sends a top-level body with `code: "INVALID_IDEMPOTENCY_KEY"` and the Vietnamese message "Khóa yêu cầu trùng với một yêu cầu có nội dung khác." — `be1Client` already renders it correctly. An FE-side hard-coded message would duplicate the server's table and drift from it.
- The other Manager write that uses `backendApi` (decision, `ManagerScreens.tsx:167-182`, `backendApi.tsx:449-455`) binds its key to a signature that is a superset of the BE fingerprint (grant, revision, version, decision, reason), so it cannot produce a key/payload mismatch either.
- `backendApi.tsx` has no existing `INVALID_IDEMPOTENCY_KEY` handling and `backendMessage` (`:601-612`) falls through to `error.message`; changing it would not touch the ParentGroups path at all.
- Failure scenario: F2 is implemented as written, its unit test (a 400 through `backendRequest`) passes, and the Manager screen that can actually hit the code still shows "API request failed (400)." on `dev` or the server text on the integration branch.
- Required: re-scope the "message" work to the real path (`be1Client.ts` reading the body for both `detail`-wrapped and CONV-1 top-level shapes) and decide whether it belongs to C1 or to C2 (program C2 = "seven callers read the CONV-1 envelope"). On the integration branch the C1 message goal is already met by the BE.

### P2 — must fix before approval

**P2-1. The program's "paging 25/100" has no concrete FE slice.** Program C1 names paging 25/100 as something the FE can fix. The plan assigns all paging to the BE (G-1) and leaves only a test-only F3. The one real FE paging literal is not mentioned: `managerBusinessService.ts:65` `new URLSearchParams({ limit: "50" })` and its test `managerBusinessService.test.ts:46` (`?limit=50&cursor=next+page`). 50 is legal (≤ 100) but is neither the SRS default (25, §21.1 line 1642) nor named in the plan. Decide and write down: (a) omit `limit` and rely on the BE default 25, or (b) send a named constant 25; update the test line; add a test that a value above 100 is never sent. `ManagerScreens.tsx` access-grants (`backendApi.tsx:446-448`) already sends no `limit` and follows `next_cursor` through the "Tải thêm yêu cầu" button (`ManagerScreens.tsx:140-160`, `:231`), so that part is correct and only needs the F3 regression test.

**P2-2. Inconsistent gap rule; "19 match / 8 gaps" is not reliable.** G-4 flags Platform Admin POST/PATCH for sending no `Idempotency-Key` (SRS §21.4 line 1697: "Command đổi trạng thái phải có idempotency key"). Rows 18 (PATCH lesson), 19 (DELETE lesson) and 25 (DELETE upload-session) also send no key (`backendApi.tsx` lesson PATCH/DELETE use `If-Match` only; plan rows 18-19 say "no key") yet are marked **M**. Either the rule is "If-Match is enough for versioned commands" (then say so, with an SRS clause, and G-4 must be re-argued) or rows 18/19/25 are gaps. Combined with P1-1 (row 15 is not a gap) the totals in §1, §4 and §10 are wrong in both directions.

**P2-3. Wrong BE baseline for the work that will be merged.** Plan §2.1 and §3 take `origin/dev` as the BE truth and say the §9.8 envelope for these roles "is the CONV-1 work (`feature/feat066-conv1`, not yet in `dev`)". Per the program (§2) the web work is merged into `feature/feat066-be-integration`, which already includes CONV-1 for `/api/be1/v1`, `/api/lesson-library/v1`, `/api/platform-admin/v1`, `/api/auth/v1`, `/api/teacher/v1/` (`error_envelope.py:20-26`). The plan's behaviour statements (body shape `{"detail":…}`, English message) are true only for `dev` and false on the branch the FE is tested against. The plan needs both baselines pinned (dev `ba295f11`, integration `5e20faf7`) and every "BE returns X" statement labelled with which one.

**P2-4. Verification section is not implementable as written (§7).** It names no commands. The repo defines `build` (`tsc -b && vite build`), `lint` (`oxlint`), `test` (`vitest run`) and `check` in `apps/web/package.json`; the plan says "typecheck", "lint on touched files" and "the repository validators named in the harness". It names **no UI-copy check**, which program ground rule 9 requires for every FE task, and no such script exists in the repo (searched `tools/` and `docs/governance/`). Specify the exact commands, the baseline-vs-after comparison (failing test ids), and define the UI-copy check (for example: every user-visible string in the touched files is Vietnamese, no raw BE text, no `detail`/English fallback) or park it as OPEN.

**P2-5. No test specification.** F1/F2 say "its test"/"one test". Needed: file names, which existing test is extended (the parent-group page tests are in `be1/__tests__/managerBusinessPages.test.tsx:69-95`, not in `managerBusinessService.test.ts`, which the plan lists in §2.2), the fixtures, and the asserted outputs per acceptance line.

### P3 — notes

- **P3-1.** Real defect candidate beside G-5: after an unknown-outcome failure the page locks the input and offers only "Gửi lại cùng yêu cầu"; there is no way to abandon the retry (`ParentGroupsPage.tsx:93-99`, `:153`, `:162`). Any "new request" affordance is a UX decision the SRS does not cover → record as OPEN, not as a C1 slice.
- **P3-2.** The plan puts an English paraphrase in quotation marks as SRS text (§5 G-5: "keep the key when retrying the **same** command"). SRS §21.1 line 1639 says "giữ nguyên key khi retry cùng một command logic". Quote the Vietnamese or drop the quotation marks.
- **P3-3.** The 27-route inventory mixes two FE clients without saying so: Manager BE1 routes use `be1Client.adminBe1Request/adminApiRequest`; Teacher `T05ClassesScreen` uses `backendApi.classes/profiles/consents`. The error-parsing difference between them (P1-2) is exactly what C2 needs; record the client per row.
- **P3-4.** The plan's SRS clause column covers only §9.8/§21.1/§21.4 and §21.2 row "DELETE /v1/upload-sessions" (line 1658, verified). The Lesson Library routes (access-grants, parent-groups, lessons) are **not** in the SRS §21.2 table at all; rows 11-27 are verified FE↔BE only, not against the SRS. Say so.
- **P3-5.** §10 says "G-1..G-5" but §5 defines G-1..G-7; §1 says "two findings (G-5, G-7)". Make the numbering consistent.
- **P3-6.** Plan §3 point 3 states the 400 body goes "through `_call`"; not re-verified here (not needed for C1).

## 2. Answers to the four questions

1. **Real FE and BE?** BE side: yes for the MGR-7 facts — default 25 / max 100 at `lesson_library.py:442` (access-grants) and `:529` (parent-groups) on `origin/dev`; `service.py:506` 400 `INVALID_IDEMPOTENCY_KEY`; lessons list still 50 at `:187`. FE side: **no** for the two FE slices — P1-1 (`ParentGroupsPage.tsx:153`, `:95-99`) and P1-2 (`be1Client.ts:48-76` vs `backendApi.tsx:280-295`). The BE baseline is incomplete (P2-3).
2. **Precise enough for the C1 slice?** No. Paging has no FE slice (P2-1); retry-key and message slices target phantom behaviour (P1-1, P1-2); verification lacks commands, tests and a UI-copy check (P2-4, P2-5).
3. **Parked / OPEN (SRS silent).** SRS searched with: "parent group", "nhóm phụ huynh", "parent-group", "invitation", "lời mời", "membership", "ứng viên", "candidate", "versions/", "feedback", "archive", plus §21.2 and §31.2-31.3.

| Item | Status | SRS evidence |
|---|---|---|
| Parent-group create/list route, name rules (max 120), archive/rename, group-create UX after unknown outcome | OPEN | Only role text (lines 223, 2574, 2580) and BR-58 (line 2538); no route, field or lifecycle contract |
| Parent invitation / membership / revoke (page "Chờ API") | OPEN | §31.3 says Manager "quản lý … Parent groups" but no invitation/membership contract; Parent lookup absent |
| Consent writes by School Manager | OPEN / excluded | §31.3: Parent grants consent; Manager does not read profile contents |
| M9-A class create with capacity | BLOCKED by program §6 (Billing deferred), not by silence | §21.2 line 1649 defines the route and `CLASS_CAPACITY_REACHED`; capacity contract waits for Billing |
| M9-B Teacher assignment (candidate list, replace/unassign rules) | OPEN until O-3a..d settled | §21.2 line 1650 gives only "exactly one active Teacher"; no candidate-list or replacement route |
| M9-C exact-version review (GET by version) | OPEN | §31.2 requires Manager approval for PUBLIC, but no version-fetch route (`versions/` hits are unrelated) |
| Manager view/feedback on SCHOOL-scope lessons | OPEN | §31.3 table row "School lesson: Xem/feedback"; no route |
| Class / profile / consent list pagination (G-2), Admin accounts cursor + keys (G-3/G-4), lessons default 25 (G-1) | SRS **does** settle the rule (§21.1 line 1642: default 25, max 100; §21.4) — BE-first, not FE | n/a |
| DELETE upload-session expected-state (G-6) | SRS settles it (§21.2 line 1658) — BE decision, not FE | n/a |

4. **Invented intent / wrong route / wrong field / SRS conflict?** No wrong routes or fields found in the 27-row table for the rows I checked. Two items amount to invented behaviour: the G-5 "edit then retry" scenario (P1-1) and a Vietnamese hard-coded message in the wrong client (P1-2). One SRS-consistency gap: P2-2.

## 3. Verdict

**NOT READY** — P1: 2, P2: 5, P3: 6.

Draft 2's BE half (MGR-7 facts, pins, hashes, SRS line numbers) is accurate and well sourced. Its FE half is not: both C1 fix slices are built on a misreading of two FE files. A Draft 3 limited to the points above can be re-reviewed quickly.

## 4. C1 implementation slice that is safe to build now

Safe (no SRS question, no BE change, no new route), to be written up in Draft 3 and then implemented:

1. **Paging literal (P2-1).** In `managerBusinessService.ts:65` stop sending `limit: "50"` — either omit it (BE default 25) or use one named constant `25`; update `managerBusinessService.test.ts:46`. Add a test that no request carries `limit` > 100. (Pick one option in the plan; both satisfy SRS §21.1.)
2. **F3 regression tests, test-only.** (a) `ParentGroupsPage`: with `next_cursor` set, "Tiếp" requests the cursor and the page does not assume 50 items; (b) `ManagerApiReviewPage`: access-grants page 1 → "Tải thêm yêu cầu" with the cursor → merged by id (`ManagerScreens.tsx:140-160`); (c) decision key stays stable for the same signature after a failure and changes when reason/revision changes (`:167-172`).
3. **Retry-key regression test for ParentGroups, no code change.** Failure with network error/timeout/5xx/408 keeps the key and sends the same key on resubmit with the input disabled; 4xx (including `INVALID_IDEMPOTENCY_KEY`) clears it and the next submit mints a new key; success clears it. This pins the current correct behaviour (`ParentGroupsPage.tsx:81-99`).
4. **Error parsing in `be1Client` (only if the owner wants it in C1; otherwise hand to C2).** `adminApiRequest`/`adminBe1Request` read `code`/`message` from the top level only. Making them accept both `detail`-wrapped and CONV-1 top-level bodies, and always showing a Vietnamese message (never a raw English BE string or "API request failed"), is the real fix for the `INVALID_IDEMPOTENCY_KEY` message goal. It touches the same client C2 will touch, so record it once and do it once.

Not safe / must not be built in C1: the F1 name-bound key as drafted (P1-1), the F2 `backendApi.errorFromResponse` change as drafted (P1-2), any G-1..G-4, G-6 FE change, M9-A/B/C, group edit/archive/invitation UI, consent writes.

## 5. Notes for the next draft

- Pin both BE baselines (dev and the integration branch) and label each BE statement.
- Name the exact commands (`npm run build`, `npm run lint`, `npm run test` in `apps/web`; `package-lock.json` is present there — check which package manager the program's setup step used) and the baseline comparison.
- Define the UI-copy check or record it as OPEN.
- Keep the goal's log rule: any decision taken from the SRS must cite the clause; the items in §2 Q3 are OPEN and park their tasks.

*Scratch note: a temporary file I wrote earlier in `tmp/phase-bc/` while reading was deleted; this report is the only file written.*
