# Goal v3 program: every missing and deviating API in one run (2026-11-19)

**Status:** APPROVED by the owner (Person 2) on 2026-11-19 and launched on that word.

**Replaces:** `GOAL_V3A_PROGRAM_20261119.md`. The owner asked for the four planned goals (v3a, v3b, v4, v5) as **one goal**.

**Source plan:** `tmp/be-api-plan/BE_API_COMPLETION_PLAN_DRAFT5_20261119.md` (131,036 B, SHA-256 `0DAD8A13…7CD1`). Its history: review R3 READY WITH NOTES (0/0/12), then the P3 fixes, then the owner answers. Each task is defined there: Wave 0 in §2.2, the WP rows in §3, the Part B deviation rows in §7, and the gates in §4.3. This program does not restate those definitions.

## 1. Ground rules
1. **SRS first.** Every decision comes from the canonical SRS: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,810 B, `443A3CA3…`. Cite the clause for each decision. When the SRS does not settle a point, park it as `BLOCKED_OPEN` with the exact question. The owner is not asked anything during the run.
2. **Per task:**
   1. plan;
   2. independent plan review on Sonnet 5.5 high, set explicitly. Use a fresh non-forked subagent when starting a session is refused. Follow D-171, at most 3 rounds;
   3. implement;
   4. run unit, contract and PostgreSQL tests;
   5. implementation review;
   6. run the validators;
   7. make **one local commit per changed branch**, staging by explicit path.

   **Only one backend task runs at a time.** Planning and reviews may run ahead in parallel.
3. **Order:** run the phases A → B → C → D below in order, and inside each phase follow the order of the table. If a task's gate (column "Gate") is not met when its turn comes, park it as `BLOCKED_GATE` and continue with the next task.
4. **DDL:** OD-01 approves DDL-A, F, B1, H, C, D, B2 and G by name, each only after its task plan review has passed. A migration lands only after that review. E1, E2 and G2 stay excluded.
5. **Records:** append nothing to `TASK_APPROVAL.md` or `DECISIONS.md`. Every decision stays in the per-task evidence notes. T0.8 is a **draft** decision pack whose numbers start at **D-066-92** (81..85 are used, 86..89 are reserved for Bruno, 90 is PAY-0, 91 is quota). The owner's approval of this program, appended by the coordinator, is the Task Approval for every task listed here, including T-7a (OD-05 option b).
6. **Git:**
   - **Backend:** branch `feature/backend-srs-api-v3`, in a new worktree `.worktrees/v3`, cut from `feature/backend-srs-api-and-fe-integration` at `d40f0514`.
   - **Web:** branch `codex/fe-ui-web-remediation` in `.worktrees/ui`. This branch is shared with a teammate. Fetch it and merge the teammate's commits before each web commit; never rewrite them.
   - **Mobile:** branch `feature/fe-mobile-remediation` in `.worktrees/mobile`.
   - Never touch the owner's untracked files.
   - **No push, no PR, no remote merge.** PR #31 goes into `dev` separately. If `dev` changes during the run, do not rebase; report it at the end.
7. **Environment:**
   - Use only the loopback containers `frc08-pg-20261119110418` (127.0.0.1:55458) and `frc08-s3mock-20261119110418` (127.0.0.1:59458). Start them with `docker start`, and stop them at the end.
   - Create fresh databases with new names and never drop one. Every S3 bucket carries the task tag.
   - Run the local API on 127.0.0.1:8020.
8. **Never:**
   - the database `sketch2life_m2_s1a`, or ports 5432 and 5433;
   - `D:\s2l-gate-secrets`;
   - Modal or any other provider call; a Firebase write; real e-mail or push;
   - deleting anything in `tmp\`, or any container or volume;
   - touching `.worktrees/be-integration`, `.worktrees/bruno-next`, or the PAY-0 and quota-plan worktrees;
   - Billing, PAY-0 or quota work, which is planned separately and built later.
9. Docs are in English. Temp files go under `tmp/phase-v3/`. Append progress lines to `tmp/phase-v3/GOAL_V3_LOG_<date>.md`.

## 2. Tasks
### Phase A: base and Wave 1 (plan goal v3a)
| Task | What | Gate |
|---|---|---|
| T0.8 | Decision pack (draft): TD-01, 03, 05, 15, 18, 20, 25, 29 | — |
| T0.1 | Residual conventions (keys 1–128, `INVALID_REQUEST`, revisions; Part B rows) | OD-18a: check the Android client first; if it depends on current behaviour, only the non-M2 routes change |
| T0.2 | `/v1/me` granted scopes | — |
| T0.3 | `/health/live`, `/health/ready`, `/metrics` | — |
| T0.4 | Mount `GET /v1/jobs/{job_id}` | — |
| T0.5 | Demo flag collision with `/v1/story-runs` | — |
| T0.11 | Interim School Manager roster guard (SRS l.2586) | — |
| T-2z | Local S3Mock storage and scanner adapters (TD-29) | — |
| T-2a | Parent upload sessions | DDL-F after plan review |
| T-3a, T-3b, T-3c, T-3d | Lesson occurrence; documents; plan revisions; plan confirm | DDL-A after plan review |

### Phase B: Parent flow, classes, video (plan goal v3b)
| Task | What | Gate |
|---|---|---|
| T0.9 | Scope-guard uniformity (404 for a wrong role) | OD-18b plus the Android check |
| T-7a | C-M1: Manager roster summary (counts and opaque refs) | OD-05 (b); covered by this program's approval |
| T-7b, T-7c, T-7d | Class paging, archive, suspend; real-data profile create | DDL-H after plan review |
| T-2b | `POST /story-runs/{id}/assets` | DDL-B1 after plan review |
| T-2c | `POST /story-runs/{id}/idea` (text or audio and an ASR job) | DDL-B1 |
| T-2d | Re-home the dev-only AI routes; `subject-confirmation` returns 202 | OD-18c plus the Android check |
| T-1a, T-1b, T-1c | Video generations (202 and admission through the local/test Billing adapter, OD-03), playback token, video-unsuitable, complete | OD-03 |
| T-1d1 | Adult-wait closeout (FR-C-11) | — |

### Phase C: notifications, library, profiles (plan goal v4)
| Task | What | Gate |
|---|---|---|
| T-8a, T-8b | Inbox; push endpoints (no real delivery) | DDL-C; TD-30 |
| T-1d2 | Reminder producer | T-8a |
| T-10a, T-10b, T-10c, T-10d | Version list and get; remix; parent-group gaps; approved-version gate | — |
| T-4a1 | Teacher run actor guard | — |
| T-13a | FR-C-08 for Teacher | T-4a1 |
| T-12a, T-12b, T-12c | Parent context entries; Teacher profile revisions; support needs | DDL-D; TD-30 |
| T-7e | Teacher roster paging | OD-17 |
| T0.10 | Accounts list cleanup (drop `offset`/`total`) | The web admin reads `next_cursor` first; the web change is part of this task |

### Phase D: Teacher run, projection, organization, Admin content (plan goal v5)
| Task | What | Gate |
|---|---|---|
| T-4b1, T-4b2 | Teacher run with occurrence/plan pins; random-child select and confirm | OD-02; DDL-B2 |
| T-5a | Projection confirmation and token | OD-14 |
| T-6a, T-6b, T-6c | Reassign/offboard/force-close (UC-12); Teacher invite (UC-13) | Any provider or e-mail action stays on ports with local adapters (OD-13 open) |
| T-9a, T-9c, T-9d, T-9e, T-9f | Content Admin permission; activity catalog; Admin-authored PUBLIC lesson with independent review; moderation list; policy routes | DDL-G |

**Not in this goal:**
- T0.6 (OD-16 open).
- T0.7 (owner-run).
- Every exclusion X-… and stay S-… in plan Draft 5: sketch/slides/SVG, profile share (OD-04), personal copy, top-up.
- Billing, PAY-0 and quota.

## 3. When something goes wrong
- **A review is still NOT READY after round 3:** park the task as `BLOCKED_REVIEW` and move to the next independent task.
- **The SRS does not settle a point:** park it as `BLOCKED_OPEN` and continue.
- **A gate is not met:** park the task as `BLOCKED_GATE`.
- **A safety check refuses an action or gives no verdict:** park it as `SKIPPED_BLOCKED`. Do not work around the refusal.
- **A test fails:** only a failure that is new against the base list blocks the commit.
- **A task depends on a parked task:** park it as well and record the chain.

## 4. End
1. Run a full re-check on the backend branch:
   - unit and contract tests, compared with the 83-id base list;
   - the PostgreSQL suites on a fresh database;
   - the five validators;
   - web `npm run check`;
   - mobile tests and typecheck.
2. Write the final report, `tmp/phase-v3/GOAL_V3_FINAL_REPORT_<date>.md`. For each task, give the commits, the review verdicts and the tests. Also include the SRS decisions with their clauses, everything parked and why, the path of the T0.8 draft, a PR title and body, and a single re-check command.
3. Send one short Vietnamese message, then stop.
