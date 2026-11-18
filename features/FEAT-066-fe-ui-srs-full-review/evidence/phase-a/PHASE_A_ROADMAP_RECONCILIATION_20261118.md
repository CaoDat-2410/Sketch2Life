# FEAT-066 Phase A reconciliation — addendum to the API alignment roadmap Draft 4

- **Status:** PLANNING ONLY / NOT APPROVED / NOT REVIEWED. It authorizes no code edit, test, check, runtime, database, branch operation, approval or decision record. A route that exists in source, has a helper, appears in OpenAPI or has a Bruno request is **not** "ready" on that basis.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Form:** one addendum to `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` (FEAT-066, BE worktree; 42,628 bytes, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`, unchanged). Draft 4 is not edited: its review record and the Phase A prompt file pin it. No new draft chain is started. This file is kept in the repository `tmp/` area (git-ignored) because the handoff forbids changes in active task worktrees; moving it into `features/FEAT-066-fe-ui-srs-full-review/plan/` needs the owner's word.
- **Inputs read:** `AGENTS.md`, `.codex/sketch2life-harness.md`, `docs/context/SRS_AUTHORITY.md`, the `SOURCE_REGISTER.md` and `PROJECT_CONTEXT.md` SRS entries, roadmap Draft 4, the Phase A prompt file, the P2, P3 and P4 reports, and the owner's P1 summary. The SRS was not re-read in full; clause references come from the audits and Draft 4. Two path strings were checked directly in it (§7, C-06).

## 0. Executive summary

1. **P1 (S-LL / MGR-8 verification) is still BLOCKED ON ENVIRONMENT. MGR-8 is NOT VERIFIED.** There are two prerequisites: a disposable `be1_acceptance` database exposed as `BE1_TEST_DATABASE_URL`, and an interpreter or import path that resolves `sketch2life` to the BE worktree's `backend/src`. Neither exists today. No pytest command ran and no P1 evidence was written; the `tmp/feat066-phase-a/mgr8/` folder does not exist.
2. **P1 is on the critical path for every BE implementation slice, but not for planning or Parent mobile.** Every BE slice touches `openapi_contract.py`, so slices queue one at a time behind the S-LL commit. Parent mobile FE correction against the M2 contract shares no file with S-LL and can proceed once its own gates (O-9, O-MOB2, O-0) are met.
3. **Web (P2, 41 templates on `dev` plus dirty MGR-8):**
   - 27 page-called templates, 3 conditional Teacher AI calls, 9 nonconditional and 2 conditional templates with no page caller.
   - No unconnected template is cleared for new FE integration.
   - The cross-cutting gaps of Rev52 D07–D10 still hold against the adopted SRS: §9.8 envelope, idempotency, revision, pagination and the `/api/.../v1` prefix. They are partly changed only by the unverified MGR-8 edits.
4. **Parent mobile (P3, 27 product call rows):**
   - **The staged `ParentApi.ts` edits move profile create/patch/delete and StoryRun create away from both the SRS and the M2 contract.** They switch to `/api/parent/v1/child-profiles…` paths and drop `Idempotency-Key` and pagination. The adopted SRS names only `/v1/parent/profiles` (lines 795 and 1648).
   - Draft 4's plan to "start from the existing staged `ParentApi.ts` work" therefore needs an owner disposition first (new O-MOB2).
   - Of the 8 M2-allowed operations, 4 are called on their exact paths with DTO gaps, and 4 are called only through non-M2 counterpart paths.
5. **Bruno (P4, 151 frozen operations on the M2 branch, 145 request files in the root working tree):**
   - 134 operations have a matching request: 4 COVERED (positive assertions only), 130 PARTIAL. 17 are MISSING.
   - No negative case exists anywhere in the collection.
   - **Correction:** for the Parent first slice, 5 of 8 operations have a request, not 8 of 8 (C-04).
6. **Counts stay per inventory:** 41 web templates, 27 mobile product rows and 151 frozen operations are on different bases and are not added together.
7. **Safest next action:**
   - Owner: supply the P1 prerequisites (critical path).
   - In parallel, the coordinator continues the independent track: the merged BE–FE mismatch register (A-1), then reviews of the open contract drafts. Neither track waits on the other.

## 1. Live authority and pins (rechecked 2026-11-18)

| Item | Observed | Note |
|---|---|---|
| Canonical SRS (root checkout, M2 branch `833df677`) | 701,157 B, `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`; `SRS_AUTHORITY.md` there (5,120 B, `CACA7EC0…`) carries the D-209 pointer | v2.7-draft, unsigned; not formal product approval |
| Owner-supplied D-209 copy | Same bytes, but at the Downloads root, not in a `SKETCH2LIFE` subfolder (the handoff's path does not exist) | C-01 |
| SRS in the BE, web and mobile worktrees | 553,948 B, `70DA43A3…` (Rev60); their `SRS_AUTHORITY.md` has no D-209 pointer (`dev` not yet updated) | C-02 |
| BE worktree `.worktrees/manager-api` | `feature/feat066-manager-api-contracts`, HEAD `1c9148e8` = `origin/dev`; 10 tracked modified, 51 untracked; the six MGR-8 files equal the P1 preflight pins; `TASK_APPROVAL.md` 37,893 / `70919E3C…`, `DECISIONS.md` 38,951 / `A99E5AC9…`, `CONTEXT.md` 56,197 / `1A835DA5…`, `STATUS.md` 49,883 / `38FC4391…` — all equal to Draft 4 §1 | P1 wrote nothing |
| Web worktree `.worktrees/ui` | `codex/fe-ui-web-remediation` `297a28b1`; 2 modified, 4 untracked; Rev52 audit 63,453 / `8B1EB54A05A4B4A6FF502D45B278DBFE3B885EC278229A7ADEA98D3DA7ECA50A`; MGR-9 plan 43,006 / `1547F32C…` | C-03 |
| Mobile worktree `.worktrees/mobile` | `feature/fe-mobile-remediation` `73fe001e`; 21 staged (19 M, 2 A), 1 unmerged (`UU`); cached stat 21 files, +1,665 / −1,330 | untouched |
| M2 freeze (root) | runtime OpenAPI 847,426 / `E9C2D7C8…`; operation inventory 56,475 / `B72228CE…` | equal to P3 pins |
| Root Bruno collection | 145 `.bru` request files; under `artifacts/be-full/`, 13 modified and 5 untracked (owner's, uncommitted; includes `environments/local.bru`) | C-05 |
| Phase A reports | P2 34,713 / `8C3E809D…2A081A`; P3 21,787 / `E5A4485C…35734D`; P4 48,221 / `50BACD27…D8A419` | equal to the handoff |
| Phase A prompt file (local, ignored) | 13,094 B, `A5A5EADF…` | — |

## 2. What Phase A established (per inventory)

### 2.1 P1 — S-LL verification gate

| Check | Result |
|---|---|
| `BE1_TEST_DATABASE_URL` set / name contains `be1_acceptance` | no / no |
| `import sketch2life` resolves inside the BE worktree `backend/src` | **failed: ModuleNotFoundError** — import-path identity NOT VERIFIED |
| pytest commands | not run |
| Evidence file, CONTEXT/STATUS/approval notes | not written (record hashes unchanged) |
| MGR-8 | **NOT VERIFIED** |

The authorization for the two commands exists only in chat ("Đúng 2 lệnh này", "Codex chạy"); Draft 4 §5.1 already records that no repository record of it exists. This addendum grants no test authorization and does not change those limits.

### 2.2 P2 — web (Admin, Manager, Teacher), base `dev` `1c9148e8` plus the six dirty MGR-8 files

- 41 BE templates in the web scope: A01–A27 page-called (27), AI1–AI3 conditional calls (3), B01–B09 nonconditional without a page caller (9), C01–C02 conditional without a page caller (2). Separately, one Parent-only lesson lookup comes from the shared login resolver and is outside the 41.
- Rev52 D01–D12 against the adopted SRS:
  - **Still hold:** D01, D02, D05, D06, D10, D11, D12.
  - **Partly hold:** D03, D07, D08, D09. P2 shows that Rev52 overstated several revision cases, and the dirty MGR-8 source changes part of D07 and D09.
- 14 capability gaps, G01–G14. G11 (payment) is excluded.

### 2.3 P3 — Parent mobile, working tree including staged edits; BE `dev` and the M2 branch

- 27 product and auth call rows. Demo calls (`src/demo/api.ts`, 23 declared paths) and the dormant mock facade (`src/services/api.ts`, 8 paths) are listed separately and not audited for parity.
- M2 client projection: 8 Parent operations allowed. Cancel is not allowed. The three assistance operations are blocked.
- 15 SRS Parent capabilities have neither a mobile caller nor a BE route: 14 GAP rows, plus quota purchase, which is excluded under payment and Q193.

### 2.4 P4 — Bruno, 151 frozen operations (M2 branch) against the root working-tree collection

- Coverage: 134 matched, 4 COVERED, 130 PARTIAL, 17 MISSING. 0 negative cases. No `assert {}` block and no failure-status assertion.
- 9 unmatched request files:
  - 1 Firebase helper;
  - 2 org-level assignment requests, a stale path matching FE drift D01;
  - 6 `storyrun-lite` upload and asset requests that exist on `dev` routers but are not in the freeze.
- `local.bru` variable `bearerToken` flagged REVIEW. The value was not reproduced, and this addendum did not open the file.
- Evidence-chain limit: P4 reused its environment scan and dev-router matching from an earlier pass it does not include.

## 3. Classification by inventory (labels overlap; not endpoint totals)

| Class | Web (P2, IDs) | Parent mobile (P3, row numbers) | Bruno (P4) |
|---|---|---|---|
| **Already connected** (a caller exists; this is not readiness) | Page-called A01–A27. No route-specific defect recorded beyond the global envelope/prefix and NOT VERIFIED DTO cells: A02, A08, A17, A20, A22, A26, A27, plus A11, A14 and A15 pending S-LL verification | Exact M2 path in use: 2, 3, 9, 10. Outside the 8 but on existing BE routes: 15–22 (Lesson Library `/me`), 26–27 (auth) | 4 COVERED, all positive-only: profiles list and read, active/current, run read |
| **Genuine SRS / BE gap** | FIX-BE: A03, A04, A05 (key), A07, A09 (pagination), A16, A18, A19, A24, A25, B01, B02, B07, B08, B09. Missing capability: G01–G03, G06–G10, G12–G14 | Envelope (§9.8) on Lesson Library and auth routes: 17, 18, 20, 22, 26, 27. No route: 14 SRS GAP rows (assets, idea, jobs, video admission/unsuitable/complete/delete, playback token, video quota, notifications, push endpoints, StoryRun history (no SRS path), lesson history/feedback, child-profile sharing) | 17 MISSING requests; 0 negative cases; no envelope assertions |
| **FE contract correction** | A10 (state mapping), A13 and A23 (typed responses), B02 (helper path and body) | 2, 3, 9, 10 (cursor, flat DTO, `run_revision`); 4, 5, 8, 11 (path, DTO, `Idempotency-Key` — caused by the staged edits); 12, 13 (singular confirmation paths, outside the 8); 15, 16, 19, 21 (cursor/types); 23 (SVG 4–8 step target) | Stale requests 004/005 (assignment path drift) |
| **Owner decision** | PX prefix (all rows); A01 and A06 (scope shape); A09 (Manager-visible profile fields); A05 (account revision); A12/A13 (exact-version binding = O-6a..c); A21 (upload path mapping); B09/G07/G08 (Content Admin permission); B03–B06 and G04–G05 (excluded MGR-4/5) | 1, 6, 7 (Parent consent policy / data authorization: no route, no SRS path); 25 (activity suggestions: no route; see the 2026-11-11 Rev78 owner direction in the source register); 14, 23, 24 (assistance blocked by M2) | `bearerToken` REVIEW; Bruno run boundary (O-BRU) |
| **Conditional / demo** | AI1–AI3 (local/test + `modal_dev`); C01, C02 (synthetic, local/test) | `src/demo/api.ts`; `src/services/api.ts` (mock); the `drawing-understandings` legacy flow (24) | PO, LE and CD classes (5, 3 and 35 operations) |
| **Excluded — payment** | G11 | Quota purchase | No payment operation in the 151 |

## 4. Reconciled roadmap

| Phase | Deliverable | Dependencies | Owner / executor | Verification gate | Status |
|---|---|---|---|---|---|
| **G0** S-LL verification (P1) | Two pytest runs, the evidence note and three scoped record appends; then the independent evidence review and one commit | ENV-DB; interpreter/import-path preflight; the existing chat authorization; a revised P1 prompt with an interpreter step | Person 2 (environment) → Codex (run) → Sonnet 5.5 high (review) | Both commands exit 0; six pins unchanged; review PASS; owner commit word | **BLOCKED ON ENVIRONMENT; NOT VERIFIED** |
| **A-1** Merged mismatch register | One document joining P2 and P3 (and P4 coverage per row), with the five classes of §3 and a per-row next owner | none (static inputs pinned) | Claude (coordinator) | One Sonnet 5.5 high review | NOT STARTED |
| **A-2** Contract drafts to review | L1 seed design Draft 1; L2 Billing contract Draft 5 (round 5 of 5) | none | Claude; Sonnet review | Review verdict; Billing stops if a P2 repeats | DRAFTS EXIST, UNREVIEWED |
| **A-3** Conventions contract (O-CONV) | Plan for the §9.8 envelope, idempotency key, revision token, cursor 25/100, prefix mapping, compatibility with M2 `request_id`/`current_version`, and Parent ordering | O-CONV inputs; A-1 helps but is not required | Claude draft; Person 2 decides | Review; owner disposition | NOT STARTED |
| **A-4** Parent mobile reconciliation brief | Disposition options for the staged `ParentApi.ts` hunks and the unmerged test; a branch reconciliation method | O-MOB2, O-9 | Person 2 and the mobile worktree's owner (NOT VERIFIED who) | Owner instruction | NOT STARTED |
| **A-5** Bruno L5 plan | Negative-case template (404 out of scope, replay, same-key/different-payload 400, stale 409, pagination bounds, envelope); per-role folders; run boundary | O-BRU, O-TOKEN; A-1 for the per-operation dispositions | Claude plan; Person 2 decides | Review; owner approval of the runner | INVENTORY DONE (P4), PLAN NOT STARTED |
| **B-1** Conventions BE slice | One approved slice applying A-3 | G0 committed (or the owner parks S-LL), O-CONV, its own Task Approval (MGR-7 excludes `app.py`) | Person 2 / CaoDat (BE) | Authorized tests; evidence review | BLOCKED (G0, O-CONV) |
| **B-2** Seed implementation | Synthetic idempotent seed for all four roles | Seed design reviewed (A-2); a separate disposable `seed` database (ENV-SEED); Task Approval | Person 2 | Two identical runs; owner-run | BLOCKED (A-2, ENV-SEED) |
| **B-3** Billing module B-1 | Billing schema, ports, the subscription commands except payment | Billing contract READY; O-PAY agreement with the payment teammate; BE queue slot (Alembic head and catalog shared) | Person 2; payment teammate for the interface | Contract review; Task Approval | BLOCKED (A-2, O-PAY, queue) |
| **B-4** FE base reconciliation | Web branch (1 behind / 3 ahead at Draft 4) and mobile branch (45 / 10, staged + unmerged) reconciled by the owner's method | O-9; A-4 for mobile | Person 2 | Branch state recorded; dirty paths preserved | BLOCKED (O-9) |
| **B-5** Bruno baseline | Assertions for connected routes, without changing the owner's uncommitted edits until they are committed or the owner says so | A-5; O-TOKEN resolved; seed (B-2) to run | Person 2 | Approved run on the seeded environment | BLOCKED |
| **C-P** Parent mobile first slice | The 8 M2-allowed operations corrected to the frozen projection (P3 rows 2–5, 8–11); 3 missing Bruno profile-write requests | B-4 mobile; O-MOB2; O-0 (M2 branch reaching `dev`, or an owner-named BE base for checks); O-CONV Parent-ordering answer. **Not G0** | Person 2 | FE checks approved separately; Bruno for the 8; independent review | BLOCKED (decisions), independent of P1 |
| **C-M** School Manager slices | W-LESSON (after G0, shared files), W-ASSIGN (O-3a..d), W-CAP (after Billing B-2); then FE M9-A/B/C | B-1; per-slice decisions | Person 2 / CaoDat | Per-slice approval, tests, review | BLOCKED |
| **C-T** Teacher slices | Lesson Library key/pagination/upload fixes (A16, A18, A19, A24, A25, B07, B08 — Lesson Library files shared with S-LL, so after G0); G03 production profile; G14 occurrence and run surfaces planned under new IDs | B-1; G0 | Person 2 | Per slice | BLOCKED |
| **C-A** Platform Admin slices | A03–A05 pagination and keys; B09/G07/G08 after O-CONTENTADMIN | B-1 | Person 2 | Per slice | BLOCKED |
| **D** Completion | Full Bruno run on a clean seeded environment; register items closed or recorded OPEN; remaining GAPs (G09–G14, mobile GAP rows) planned or recorded OPEN | all above | Person 2 | Regression record; review | NOT STARTED |

**Work-in-progress limits (from Draft 4, unchanged):** one BE implementation slice at a time; one FE slice per app at a time, only on a verified BE base; documents (A-1 to A-5) have no file conflict and run alongside anything.

## 5. Phase cards — next action, owner dependency, acceptance, stop condition

| Phase | Safest next action | Owner dependency | Acceptance evidence | Stop condition |
|---|---|---|---|---|
| G0 | Owner provisions the disposable `be1_acceptance` database (Lesson Library migration applied; not `sketch2life_m2_s1a`, no shared database) and names the interpreter plus the import-path method, e.g. an explicit `PYTHONPATH` to the BE worktree `backend/src` (known editable-install trap); the coordinator then revises the P1 prompt with that preflight | ENV-DB; interpreter instruction | Evidence note with exit codes, summary lines, six pins before/after, yes/no environment checks; review PASS | Any preflight mismatch, a failing command (recorded once, no rerun), a pin change, or the URL appearing in output |
| A-1 | Coordinator builds the register from the three pinned reports only | none | One table, the five classes, per-row next owner, counts per inventory; review verdict | A source pin changes (re-pin first); a row cannot be classified without inventing a route |
| A-2 | Review Billing Draft 5, then seed Draft 1 | owner word to start each review | Review records | Billing: a P2 repeats or the P1/P2 count does not fall (D-171 item 11), so it returns to the owner |
| A-3 | Draft the conventions plan with the options per item | O-CONV answers after the draft | Plan + review | An item needs product intent the SRS does not give: list it, do not choose |
| A-4 | Coordinator writes the options (keep, rework or drop the staged path hunks; who resolves the unmerged test) as a brief, without touching the worktree | O-MOB2, O-9 | Owner instruction recorded | Authorship of the staged work unknown: ask, do not assume |
| A-5 | Coordinator drafts the L5 plan after A-1 | O-BRU; O-TOKEN (owner checks `local.bru` personally) | Plan + review | A real credential is found in a tracked or to-be-committed file: stop, owner only |
| B-1…B-5 | Each starts only after its row's dependencies | per row | Task Approval, authorized commands, evidence, review | Any unapproved file or command |
| C-P | After A-4 and B-4: one FE allowlist for the 8 operations | O-MOB2, O-9, O-0, O-CONV ordering | FE checks + Bruno for the 8 + review | Projection pins change; cancel or assistance creeping in |
| C-M/C-T/C-A | One slice at a time from the previous verified commit | per-slice decisions | per-slice | as Draft 4 §9 |
| D | Full run | O-BRU | Run record | — |

## 6. Role split

| Surface | App | Inventory | First work | Not before |
|---|---|---|---|---|
| Parent | mobile `apps/ui-mobile` | P3 (27 rows), M2 projection (8 allowed) | C-P after A-4/B-4 | O-MOB2, O-9, O-0 |
| School Manager | web `apps/web` | P2 A06–A15, B01–B06 | W-LESSON after G0; M9-A/B/C | G0, B-1, per-slice decisions |
| Teacher | web | P2 A16–A27, AI1–AI3, C01–C02 | Lesson Library fixes after G0 | G0, B-1 |
| Platform Admin | web | P2 A02–A05, B09 | accounts pagination and keys | B-1; O-CONTENTADMIN for moderation |
| Shared | web + mobile | A01 / P3 row 27 (`/api/auth/v1/me`) | O-CONV and the scope shape (A01/A06) | — |

## 7. Conflicts, stale pins and overlaps (nothing silently resolved)

| ID | Finding | Effect / handling |
|---|---|---|
| C-01 | The handoff's D-209 path (Downloads `SKETCH2LIFE` subfolder) does not exist; the identical bytes are at the Downloads root and in the root checkout's canonical SRS | None on content; cite the canonical repository path |
| C-02 | The BE, web and mobile worktrees still carry the Rev60 SRS and the pre-D-209 `SRS_AUTHORITY.md` (`dev` not updated); the root checkout (M2 branch) carries D-209 | Slice approvals in those worktrees must cite the canonical bytes; O-SRS / O-0 still open |
| C-03 | P2 cites the Rev52 audit pin with 63 hex digits (final `A` dropped); the live pin is `…DA7ECA50A` and unchanged | Transcription error in P2, not a content change; correct in A-1 |
| C-04 | P4 and the handoff say "8/8 requests exist" for the Parent first slice, while P4's own matrix shows 3 MISSING; correct figure: 5 of 8 have a request (4 COVERED positive-only, 1 PARTIAL `POST /v1/story-runs`), 3 missing (`POST`, `PATCH`, `DELETE /v1/parent/profiles…`) | Use 5/8 in A-1/A-5 |
| C-05 | `environments/local.bru` is among the owner's uncommitted root edits and is flagged REVIEW for `bearerToken` | Owner checks it personally before any commit of the root Bruno edits (O-TOKEN); the coordinator does not open it |
| C-06 | The staged mobile `ParentApi.ts` edits use `/api/parent/v1/child-profiles…` and plural confirmation paths that exist in neither the SRS (only `/v1/parent/profiles`, lines 795 and 1648) nor `dev`/M2, and drop `Idempotency-Key` and paging; Draft 4 §6 L4 said to start from that staged work | Draft 4 premise superseded: disposition first (O-MOB2); worktree untouched |
| C-07 | FE helper (D01/B02) and Bruno requests 004/005 share the same org-level assignment path drift; the frozen class-scoped assignment operation has no Bruno request | One fix decision in W-ASSIGN covers FE helper and Bruno |
| C-08 | Bases differ: P2 on `dev` + dirty MGR-8; P3 on `dev` and M2; P4 on the M2 freeze + root working-tree collection. The MGR-8 edits (list default 25, 400 `INVALID_IDEMPOTENCY_KEY`) are not in the M2 freeze; the 6 `storyrun-lite` upload requests are on `dev` only | Counts not added; after S-LL and M2 both reach `dev`, Bruno assertions target the combined behaviour (O-0) |
| C-09 | Draft 4 §3 ("no API audit of the mobile app exists") and §1A ("L1, L2 video quota, L3 audit, L5 Bruno: not started") are stale | Superseded by P3/P4 and the L1/L2 drafts; Draft 4 not edited |
| C-10 | Owner answers given in chat — O-SEED (all four roles), O-PAY ("Tôi: contract + port + Billing trừ thanh toán", pending the payment teammate), Q-L2-1..9 (e.g. 503 `BILLING_UNAVAILABLE`), Billing "BE1 tự đếm lớp" and "dấu version" — are not decision rows | They stay proposals for repository purposes until recorded on the owner's instruction |
| C-11 | Parent consent (P3 rows 1, 6, 7) is a Parent-side policy and data-authorization question, distinct from the excluded MGR-5 staff consent writes; Draft 4 has no decision for it | New O-PCONSENT; do not merge into O-5 |
| C-12 | P2 refers to an "MGR-6 R3" verdict; Draft 4's latest MGR-6 plan review is R6 `3E7BF9A4…` | Use R6 as the plan-quality pin; neither is implementation readiness |
| C-13 | Video quota appears as P2 G10, P3 GAP `GET /v1/video-quota` and L2 Billing Draft 5 | One owner: L2; FE quota read only after its BE slice is verified |
| C-14 | Teacher AI (AI1–AI3) and Parent assistance (rows 14, 23, 24) are conditional or blocked; Bruno has no request for them | Bruno for them only as auth-boundary/refusal cases (Draft 4 L5 rule) |

## 8. What this addendum changes in Draft 4's reading

- §1A status: L3 audit = P2/P3 drafts (static, unreviewed); L5 = P4 inventory (static); L1 and L2 = drafts exist. S-LL unchanged: AUTHORIZED / BLOCKED ON ENVIRONMENT / NOT RUN, now with a second blocker (import path).
- §4 Phase A: the audits and inventory ran; closing Phase A now means A-1 to A-5.
- §6 L4 Parent row: replace "starting from the existing staged `ParentApi.ts` work" with "after the O-MOB2 disposition of the staged work".
- §7 critical path, refined: G0 gates the BE queue; C-P is a second path gated by O-MOB2, O-9 and O-0, not by G0.
- §8: O-MOB is done (audit ran); the new decisions are listed in §9 below.
- Ready-for-new-FE-integration count: **still 0** (web: no unconnected template cleared; mobile: the 8 allowed operations need FE correction and their own FE task).

## 9. Open decisions

**Carried from Draft 4, unchanged and unresolved:**
- O-0, O-SEQ, O-CONV (including Parent ordering), O-PAY (chat answer pending agreement), O-SEED (chat answer, not recorded);
- O-2a/O-2b (chat answers via Q-L2, not recorded), O-2c;
- O-3a–O-3d, O-6a–O-6c, O-5, O-X;
- O-9, O-BRU, O-SRS;
- the Billing Draft 5 open items (§12 of that draft).

**New from Phase A:**

| ID | Question | Basis | Blocks |
|---|---|---|---|
| ENV-P1 (environment, not a decision) | Disposable `be1_acceptance` database plus interpreter/import-path method | P1 preflight | G0 |
| O-MOB2 | Keep, rework or drop the staged `ParentApi.ts` path/key/paging hunks; who resolves the unmerged `parentSrsBehavior.test.ts`, in which task | C-06 | A-4, B-4, C-P |
| O-PCONSENT | Parent consent-policy and data-authorization contract (rows 1, 6, 7) | SRS §31.3 (Parent is the consent actor); no route or path | Parent consent UI |
| O-PRIV | Which child-profile fields the School Manager may read (A09) | SRS §31.3 line 2586 | Manager roster |
| O-ASSIST | Parent assistance operations stay blocked (rows 14, 23, 24); target shape for activity suggestions (row 25, Rev78 owner direction) and sketch guides (SVG, 4–8 steps) | M2 closure; FR-P-11 | Parent AI UI |
| O-CONTENTADMIN | Content Admin permission resolver for moderation and catalog (B09, G07, G08) | P2 D06 | Admin moderation |
| O-ACCREV | Account revision semantics (A05) | §21.4 does not mandate If-Match for accounts | Admin edit |
| O-UPLOAD | Upload-session path mapping (A21); 202 completion (A24, D11) is SRS-specified | §21.2 lines 1654–1658 | Teacher import |
| O-TOKEN | Owner checks `local.bru` `bearerToken` before any commit of the root Bruno edits | C-05 | B-5, any Bruno commit |

**Added by the A-1 register (`tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT1_20261118.md` §6):**
- O-PROJ: extending the M2 client projection beyond the 8 operations.
- O-L3SCOPE: whether the 44 unaudited CB classroom/device operations are in scope.

## 10. Immediate next action

- **Owner (critical path):** supply ENV-P1. Provision the disposable `be1_acceptance` database and name the interpreter and import-path method. Then G0 can be retried with a revised P1 prompt. Until then, MGR-8 stays NOT VERIFIED and no BE implementation slice starts.
- **Coordinator (independent, now, on the owner's word):** A-1, the merged register, from the three pinned reports. It is a document only, with no file conflict.
- **Owner decisions that unlock the most parallel work:** O-MOB2 and O-9 for Parent mobile (independent of P1), then O-CONV.

## 11. Limits

- Static reading only: no test, build, validator, runtime, database, Docker, network, provider or Modal command; no file changed in any worktree, the root Bruno collection, the SRS, approvals or decisions.
- Read-only Git commands only: `status`, `worktree list`, `rev-parse`, `for-each-ref`, `diff --cached --stat`, `log -1`.
- The unmerged mobile file was not opened.
- P2, P3 and P4 are static audit evidence, not proof of runtime behaviour or implementation readiness.
- Their internal claims were spot-checked: pins, counts, the two SRS path strings, and the Bruno arithmetic. They were not re-derived row by row.
