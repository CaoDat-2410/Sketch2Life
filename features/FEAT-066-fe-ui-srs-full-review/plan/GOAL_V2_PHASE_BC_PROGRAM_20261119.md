# Goal v2 — Phase B and Phase C program

- **Date:** 2026-11-19. **Owner:** Person 2. **Status:** APPROVED BY THE OWNER (program approval entry in FEAT-066
  `approvals/TASK_APPROVAL.md`), NOT LAUNCHED. Nothing runs until the owner says to launch it.
- **Idea:** the owner approves the whole program once, up front. The goal then works through Phase B and Phase C
  **per the SRS, without asking the owner anything**. The owner's only gates are at the end: check the final
  result and its tests, then decide whether the PR goes into `dev`.

## 0. Before launch (owner, once)

| Step | What | Why |
|---|---|---|
| 0.1 ✅ | Read this program and approve it. The coordinator then appends ONE program-approval entry to FEAT-066 `approvals/TASK_APPROVAL.md` (and a pointer entry to FEAT-063 for the SRS wording edit) | The repository rules need a Task Approval before any implementation; one program approval replaces the per-task owner approvals |
| 0.2 ✅ | Setup, run by the coordinator on the owner's instruction: `pnpm install --frozen-lockfile` in `.worktrees/ui` and `.worktrees/mobile` | The goal can then run web and mobile typecheck, tests and lint itself |
| 0.3 | The owner gives the launch word | Launch |

## 1. Ground rules (fixed; the goal never relaxes them)

1. **SRS first.** Every product question is settled from the SRS (D-209 copy, 701,157 B), the data table register
   and the accepted decisions. Each answer is recorded append-only in the feature's `DECISIONS.md` as "decided by
   the goal under program approval <entry>", with the SRS clause. A question the SRS does not answer, or an SRS
   conflict, is recorded OPEN and the affected task is parked (`BLOCKED_OPEN`); the goal moves on. It never
   invents product intent and never asks the owner.
2. **No owner approval is faked.** Records say "goal", never "owner". The owner's approval is the program entry
   (0.1) and the final check (§5).
3. **Local only: commit, never push.** No `git push` of any branch, no PR, no merge on a remote, no GitHub change.
   Each finished task is committed locally and left there. The owner checks the result and does the push.
   **The web branch `codex/fe-ui-web-remediation` is also being worked on by a teammate:** before every web
   task the goal runs `git fetch` and compares the local branch with `origin/codex/fe-ui-web-remediation`. If the
   teammate pushed new commits, the goal merges `origin/codex/fe-ui-web-remediation` into the local branch
   (local merge only; the teammate's work kept as it is; record conflicts resolved verbatim) before it starts, and
   lists the teammate's new commits in the log and the final report. It never rewrites, reverts or force-anything
   on that branch.
4. **Never:** `sketch2life_m2_s1a`; ports 5432 or 5433; `D:\s2l-gate-secrets`; gate containers or volumes; Modal,
   provider, payment or other non-loopback network calls (`OWNER_MODAL_CALL_APPROVED=NO`); deleting files,
   branches, worktrees, containers, volumes, databases or anything in `tmp\`; rewriting or amending a commit;
   the owner's uncommitted files in `.worktrees/ui`.
5. **Databases and storage:** only the existing disposable loopback containers `frc08-pg-20261119110418`
   (127.0.0.1:55458) and `frc08-s3mock-20261119110418` (127.0.0.1:59458). The goal may **create** a fresh
   database or bucket whose name contains the task tag (for example `frc08_seed7a_<stamp>`) and run migrations and
   tests on it. It never drops, truncates or reuses another database, and never touches another container.
6. **Records:** `TASK_APPROVAL.md` and `DECISIONS.md` append-only, head-hash check first, LF, no dollar sign.
   FEAT-066 decisions continue from D-066-81; cite D-066-62..79 with their lineage.
7. **Reviews:** every plan and every implementation gets an independent review on Sonnet 5.5 high (a separate
   session, or a fresh non-forked subagent if a session cannot be started; the form is recorded). D-171 applies:
   if a finding class repeats or P1+P2 does not fall, at most 3 rounds, then the task is parked
   (`BLOCKED_REVIEW`) and the goal moves on.
8. **One commit per finished task**, by explicit paths, after the implementation review is ACCEPTABLE
   (WITH NOTES) and the checks are green. The task record says "accepted by the goal under program approval;
   owner final check pending".
9. **Checks for every BE task:** ruff and mypy (0 new against the branch base), the full `tests/unit` and
   `tests/contract` suites compared with the base by failing test id (0 new), the PostgreSQL tests of the task on
   a fresh disposable database, the four validators, `git diff --check`, the security validator again before the
   commit. **For every FE task:** typecheck, tests, lint, UI-copy check of the app.
10. **A blocked command is not worked around.** No safety verdict, a denied permission or a time-out: log
    `SKIPPED_BLOCKED`, park the step, continue elsewhere.
11. **Log** every step in `tmp/phase-bc/GOAL_V2_LOG_<date>.md` (time, step, result, files, pins, commit hashes).

## 2. Branches

| Work | Branch | Worktree |
|---|---|---|
| All BE work (Phase B and the BE side of Phase C) | `feature/feat066-be-integration` (from `origin/dev` + seed1 + FR-C-08) | `.worktrees/be-integration` |
| Web FE (Admin, School Manager, Teacher) | `codex/fe-ui-web-remediation` | `.worktrees/ui` |
| Mobile FE (Parent) | `feature/fe-mobile-remediation` | `.worktrees/mobile` |
| Final | the two FE branches are merged into `feature/feat066-be-integration` at the end, so the owner sees **one PR candidate into `dev`** | `.worktrees/be-integration` |

The two FE branches stay separate while the work runs (two different apps, no shared files, web and mobile
slices can run in parallel, one conflict resolution at the end); confirmed with the owner on 2026-11-19.

## 3. The work, in order

The goal runs the lines below. A line waits only for the steps it names; otherwise lines run one after another
in this order (one BE task at a time, one FE task per app at a time).

### Phase B — backend foundations

| # | Task | Content (SRS basis) | Done when |
|---|---|---|---|
| B1 | **Carry the seed docs** | Seed design Drafts 7–11 and D-066-80 from `.worktrees/seed1` onto the integration branch as one docs commit | Commit |
| B2 | **BRU-0a** (Bruno L5 frame) | **Latest state:** Codex finished the rework in `.worktrees/bru0` (branch `feature/feat066-bru0`): six new untracked files, hashes verified by the BRU-0 coordinator (LF only, no machine paths, four validators exit 0); the loopback guard and request A02 have **never been run**. The goal: (1) starts the local API on loopback against a fresh disposable database on the `frc08` container, seeded with S1; (2) runs the positive and the negative control of the collection guard and A02; (3) fixes what fails; (4) runs an implementation review; (5) carries the six files and the uncommitted BRU-0a entry and addendum (in `.worktrees/conv1`) onto the integration branch and commits once. No token in Git | Controls pass, review ACCEPTABLE, commit on the integration branch |
| B3 | **SEED-7a** (taken over from the stopped seed session) | **Latest state:** the seed session wrote package Draft 2 (`.worktrees/seed1/.../plan/PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT2_20261119.md`, 21,950 B, `4F9782B3…`; it fixes the 4 P2 and 8 P3 of review R1, uses the integration branch, and splits the work into one docs commit and one task commit). Its review round 2 was stopped before it finished, so the goal starts with a fresh review of Draft 2. History: package Draft 1 `.worktrees/seed1/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT1_20261119.md` (15,936 B, `B21C251E…`), its cold review R1 `tmp/seed7a-pkg-review/SEED7A_PACKAGE_DRAFT1_COLD_REVIEW_R1_20261119.md` (25,117 B, `9625A3C2…`: NOT READY, 0 P1, 4 P2) and the queued changes `tmp/seed7a-pkg-review/PENDING_DRAFT2_CHANGES.md` (integration branch as base and target; base now includes FR-C-08; runbook warning mandatory). Review Draft 2 (fix it as Draft 3 if the review asks), then implement: P4/K4, P5/K5 in S1; one run each via `create_run` + `confirm_context`, re-checked against the FR-C-08 service; provider guards; S5 parked as NOT_BUILT (no mounted router) | Package review READY (WITH NOTES); seed runs twice on a fresh `seed` database (2nd run 0 new rows); implementation review; commit |
| B4 | **SRS wording edit** (FR-C-08 follow-up) | Apply SRS edit Draft 2 (14 sites) to the canonical SRS copy in the repository and re-pin it | Review, commit |
| B5 | **Billing B-1 — DEFERRED by the owner (2026-11-19), not in this goal** | See §6 | — |
| B6 | **Seed S2–S4 — DEFERRED with Billing, not in this goal** | See §6 | — |

### Phase C — API into FE, four roles

| # | Task | Role / app | Content | Waits for | Done when |
|---|---|---|---|---|---|
| C1 | **C-W1** Manager alignment | School Manager / web | MGR-9 Draft 2 (already written, unreviewed): review it, then fix the gaps the FE can fix now (paging 25/100, idempotency key retry, `INVALID_IDEMPOTENCY_KEY` message) | — | Review, web checks, commit |
| C2 | **C-W2** error envelope | Admin, Manager, Teacher / web | The seven callers read the CONV-1 envelope and codes | C1 | Review, web checks, commit |
| C3 | **C-P2** Parent lifecycle | Parent / mobile | Cancel, DELETE, lifecycle GET client and UI states (pending, deleting, deleted, 409, 404); Bruno requests | — | Review, mobile checks, commit |
| C4 | **C-T** Teacher Lesson Library | Teacher / BE then web | Key, paging and upload fixes (A16, A18, A19, A24, A25, B07, B08) per SRS §21 | C2 (web slot) | BE commit, FE commit |
| C5 | **C-A** Admin accounts | Platform Admin / BE then web | Paging and keys (A03–A05); moderation only if O-CONTENTADMIN is answered by the SRS, else parked | C4 (web slot) | BE commit, FE commit |
| C6 | **Manager features** | School Manager / BE then web | M9-B Teacher assignment and M9-C exact-version review only where the SRS settles O-3a..d and the MGR-6 option; else parked. M9-A capacity create is DEFERRED with Billing (§6) | C5 | BE + FE commits, or BLOCKED_OPEN |

### End — Phase D and the owner's check

| # | Task | Content |
|---|---|---|
| D1 | **Merge the FE branches** into `feature/feat066-be-integration` (records resolved verbatim with a lineage note) | One branch holds everything |
| D2 | **Full verification on a fresh environment** | Fresh disposable database: `alembic upgrade heads`, seed S1 + every built stage, BE unit + contract + PostgreSQL suites, web and mobile checks, the full Bruno collection against the local API on loopback |
| D3 | **Final report** `tmp/phase-bc/GOAL_V2_FINAL_REPORT_<date>.md` | Per task: commit hash, review verdicts, test counts; every decision taken from the SRS (ID + clause); everything parked (BLOCKED_OPEN / BLOCKED_REVIEW / SKIPPED_BLOCKED) and why; the PR title and body ready to paste; the one command the owner runs to re-check everything |
| D4 | **Stop** | One short Vietnamese message to the owner pointing at D3 |

## 4. What the goal does when something goes wrong

| Situation | The goal does |
|---|---|
| SRS silent or conflicting | Records OPEN, parks the task, continues |
| Review keeps failing (D-171) | Parks the task after 3 rounds, continues |
| A test fails that also fails on the base | Records it as pre-existing, continues |
| A new failure it cannot fix in 3 attempts | Reverts nothing that is committed; leaves the task uncommitted, parks it, continues |
| A command is blocked | Logs SKIPPED_BLOCKED, continues |
| Everything left is parked | Goes straight to D2–D4 |

## 5. The owner's part at the end (the only gates)

1. Read `GOAL_V2_FINAL_REPORT_<date>.md`.
2. Run its ONE re-check command (all suites again on a fresh disposable database, web and mobile checks, Bruno).
3. Decide: push `feature/feat066-be-integration` and open the PR into `dev` (the title and body are ready), or
   tell the goal what to fix.

## 6. Deferred by the owner: Billing (not part of this goal)

The owner deferred Billing on 2026-11-19. The goal does not start any of these, does not write
Billing schema or code, and lists them in the final report as DEFERRED.

| Item | What it is | Why it waits | What it unblocks later |
|---|---|---|---|
| Billing B-1 | Billing module: price versions, organization subscriptions (10 base class slots plus paid slots), capacity periods, GRACE and RESTRICTED states, video-quota grants and the immutable usage ledger; payment stays a port with no provider adapter | Owner deferral; O-PAY (payment interface with the payment teammate) still open; BE queue PAY-0a → PAY-0b → PAY-0c → C-M1 BE comes first | Seed S2–S4, M9-A, the video-quota reads |
| PAY-0a, PAY-0b, PAY-0c, C-M1 BE | The BE queue tasks before Billing B-1 | Deferred together with Billing | Billing B-1 |
| Seed S2–S4 | Price version, subscriptions, the capacity and lifecycle cases of orgs A–H, video quota top-up | Needs Billing B-1 to B-5, O-SEED-PAY and O-SEED-CLOCK | Bruno negative cases (409 capacity, restricted, quota exceeded) |
| M9-A | School Manager class creation with capacity admission | Needs Billing and the MGR-2 contract | The Manager create-class screen |
| Billing inputs kept as they are | Billing contract Draft 9 (`plan/PLAN_L2_BILLING_CONTRACT_DRAFT9_…` in FEAT-066), seed design Draft 11 §3–§4 (S2–S4), D-066 Billing decisions | — | Starting point when the owner resumes Billing |

When the owner resumes Billing, it becomes its own goal or program with its own approval.
