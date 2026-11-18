# FEAT-066 A-4 — Parent mobile reconciliation brief (O-MOB2, O-9)

- **Status:** PLANNING BRIEF / NOT APPROVED / NOT REVIEWED. It decides nothing and authorizes nothing. No file in the mobile worktree was changed, staged, resolved or restored. The unmerged file was not opened.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Parent documents:** Phase A addendum (`tmp/feat066-phase-a/roadmap-reconciliation/PHASE_A_ROADMAP_RECONCILIATION_20261118.md`), item A-4; A-1 register (`tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT1_20261118.md`), rows M01–M27.
- **Commands used:** read-only Git only — `status`, `log`, `rev-list`, `merge-base`, `diff --stat`, `diff --name-only`, and `show` of staged and committed blobs.

## 1. What is in the mobile worktree (observed 2026-11-18)

| Item | Observed |
|---|---|
| Branch / HEAD | `feature/fe-mobile-remediation` at `73fe001e` (= `origin/feature/fe-mobile-remediation`). 45 commits behind and 10 ahead of `origin/dev` |
| 10 commits ahead | 7 FEAT-081 commits by AnhKhoaa157, 2026-11-13 to 11-15: Waves 1, 2A+2B ("wire Parent flow to V1 profile and StoryRun APIs"), 3, R, the Wave L plan, UI consolidation and Rev67 flow gates.<br>3 commits by HieuNewBie, 2026-11-17: legacy splash cleanup, "align migrations and local compose runtime" (4 files under `backend/alembic`, plus `compose.yaml`) and "UI login".<br>Total vs the merge base: 233 files, +14,414/−3,163. 181 of those files are under `apps/ui-mobile`, 4 under `backend` |
| Staged (21 paths) | 14 Parent source files, among them `ParentApi.ts`, the use cases, the controller and the screens; 3 tests (`parentApiI2Contract`, `parentFlowV1`, `parentLearningI2`); 4 FEAT-081 records:<ul><li>`approvals/TASK_APPROVAL.md`, which adds **Addendum 34**;</li><li>`plan/PLAN_REVISION_19.md` (new);</li><li>`evidence/IMPLEMENTATION_REPORT_API_20261115.md` (new);</li><li>`status/STATUS.md`.</li></ul> |
| Unmerged | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` (`UU`). There is no `MERGE_HEAD`, `CHERRY_PICK_HEAD` or `REVERT_HEAD`, only `AUTO_MERGE`. That pattern fits a conflicting stash apply/pop or a `checkout -m`. **NOT VERIFIED** which one |
| What the staged work is | **FEAT-081 Plan Revision 19** (2026-11-15), carried out under staged Addendum 34. Its stated goal is to integrate 15 Parent and Lesson Library operations "declared in backend source", using the **branch's own backend at `888f0cb5`**. Plan 19 and its report pin SRS Rev60 and the Rev67 owner copy, not the D-209 copy. The report says its mocked tests assert "absence of an idempotency header" |

## 2. Why the staged work does not fit `dev` / M2 (correction to the addendum C-06)

The addendum called the staged `/api/parent/v1/child-profiles…` paths a drift "away from both the SRS and the M2 contract". That is true, but the cause is now known: **the staged work is not random drift.** It is an approved-looking FEAT-081 task built against the stale backend copy inside this 45-behind branch.

| Backend copy | `parent_profiles.py` routes |
|---|---|
| `888f0cb5` (Plan 19 base) and `HEAD` `73fe001e` | 7 `child-profiles` routes; no `/v1/parent` prefix |
| `origin/dev` and the M2 branch `833df677` | 0 `child-profiles` routes; `/v1/parent` prefix (M2 S1a-P, `c5a14a0e` on 2026-11-11, and S1a-P2, `77cf761d` on 2026-11-13) |

**Consequence:** the Plan 19 work encodes the legacy contract.
- **Rows that use removed routes:** the profile list, create, read, patch and delete paths, the consent policy, data authorization grant and revoke, and the StoryRun create path (register rows M01–M08 and M11).
- **What the tests assert:** these tests encode the legacy contract. They assert that no idempotency key is sent, while M2 requires one.
- **No backend route on `dev` or M2:** of these rows, M01, M06 and M07 have none, because M2 removed the legacy consent routes.

Before any of this work can serve the C-P slice (the 8 M2-allowed operations), it must be re-targeted.

## 3. Decisions for the owner

### D-A (O-MOB2): what happens to the staged Plan 19 work

| Option | What it means | For | Against |
|---|---|---|---|
| **(c) Preserve, then start C-P clean — recommended** | Save the staged work non-destructively (a patch of the staged diff plus both sides of the conflicted test, kept under `tmp/`, and/or a WIP commit on a separate backup branch). Bring the worktree back to a clean state, reconcile with `dev` (D-C), then build C-P from the M2 projection, reusing UI parts of Plan 19 where they still apply | Nothing is lost; no code is built twice against routes `dev` no longer has; the conflict is handled once, by its author | Plan 19 / Addendum 34 is not committed as such; a FEAT-081 record must say it was superseded |
| (a) Commit as is, rework later | Resolve the conflict, commit Plan 19 on the mobile branch, then a new task re-targets it | Keeps Addendum 34 history exactly | The commit contains calls and tests for removed routes; the merge with `dev` then conflicts on the same files; double work |
| (b) Rework in place before commit | Re-target the staged files to `/v1/parent/...` and add keys, then commit | One commit | Needs a new FEAT-081 approval anyway; mixes an approved-but-stale scope with new scope in one diff; still on the 45-behind base |

### D-B: the unmerged test file

**Recommended:** its author resolves it, or the owner tells a session exactly how, as part of D-A. Under option (c), first save both sides (`:2:` and `:3:` blobs) to `tmp/`. No session resolves it automatically.

Open fact: who staged the work and produced the conflict is **NOT VERIFIED**. The FEAT-081 commits are by AnhKhoaa157 (the Git user of this machine). The last three commits are by HieuNewBie.

### D-C (O-9): how the mobile branch catches up with `dev`

| Option | Notes |
|---|---|
| **Merge `origin/dev` into the branch — recommended** | The branch is pushed, so a merge needs no force-push. Expect conflicts in `backend/alembic` (HieuNewBie's 4 migration files versus `dev`'s migrations), `compose.yaml`, FEAT-081 records and Parent FE code. **The `backend/alembic` part needs HieuNewBie's input.** |
| Rebase the 10 commits onto `origin/dev` | Linear history, but needs a force-push of a shared branch |
| New branch from `origin/dev`, port the FE commits | Clean, but loses the branch's history; most work |

**Precondition (O-0):** C-P needs the M2 Parent contract on its base. That includes `run_revision`, flat profile DTOs and the delete-pending receipt. M2 (`833df677`) is not on `dev` yet. Either M2 reaches `dev` first, or the owner names the M2 branch as the base for the mobile merge and for local checks.

### D-D: which feature carries the C-P slice

**Recommended: a new FEAT-081 addendum.** FEAT-081 is the Parent mobile feature with its own approvals and plan chain. The addendum references the FEAT-066 register rows M02–M05 and M08–M11 and supersedes Plan 19 / Addendum 34 for those operations. The alternative is to carry it in FEAT-066.

### D-E (O-CONV, Parent ordering): wire the 8 operations before the conventions slice?

**Evidence for "yes, Parent can go first":**
- P3 states the M2 Parent profile and StoryRun error schemas already align with SRS §9.8.
- The M2 closure read the extra fields `request_id` and `current_version` as not blocking Parent integration.
- The paths are already `/v1/...`, so the PX prefix question does not apply.

**Risk:** if O-CONV later changes the envelope or the key format, the Parent parser changes once more. This is the owner's choice.

## 4. Sequence after the decisions (each step needs the owner's instruction)

1. D-A step: preserve the staged work and both conflict sides. Nothing is deleted.
2. Clean the worktree, by the owner or by a session the owner names.
3. Make M2 available on the base (O-0), then merge `dev` (D-C), with HieuNewBie for `backend/alembic`.
4. Write the FEAT-081 addendum for C-P (D-D): exact allowlist, the 8 operations, `Idempotency-Key` on profile create, patch and delete and on StoryRun create, cursor continuation, flat DTOs, `run_revision`. No cancel, no assistance, no consent routes.
5. Implement; run only separately approved FE checks; add the 3 missing Bruno requests (profile create, patch, delete); then an independent review.

## 5. Open facts

- Who staged Plan 19 and how the conflict arose — NOT VERIFIED.
- Whether Addendum 34 was ever committed elsewhere — only the staged copy was seen.
- The content of HieuNewBie's alembic changes and whether they collide with `dev` — not read.
- Whether the FEAT-081 Wave 2A+2B "V1" wiring (`3386d7e0`) matches the M2 contract — not compared here.
