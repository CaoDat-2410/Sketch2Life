# FEAT-066 SEED-7a — S7 item 2a (command-made Parent runs), with S5 found NOT_BUILT: implementation approval package (Draft 1)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package proposes one bounded implementation slice. It authorizes no script, database, command, stage, commit or push.
- **Date:** 2026-11-19. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Asked for:** a package for stage S5 and stage S7 item 2a of the accepted seed design. §2 explains why only S7 item 2a can be built now: S5 is `NOT_BUILT` under the design's own rule.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Seed design (accepted, D-066-80) | `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT11_20261119.md`, 73,863 B, `6E4EFDE08E2763B6A0B0CCAE6CC4DC5301457961B22EB46BBF520D401C727CE8` |
| Decision record | `DECISIONS.md` in this worktree with D-066-80 appended: 73,010 B, `A1C589570F17537B6B5118F0A2F69F1C90021138DE24F2FFB42241A791740C7A` (uncommitted) |
| SEED-1 (stage S1, implemented) | commit `4e2f6d96` on local branch `feature/feat066-seed1`; package `plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md` |
| Working SRS (D-209) | 701,157 B, `B9B1F42D…`: §2.1, §11.1 item 3 (one active run per owner), §24.1 (synthetic data only) |
| Source base | Statements below were checked statically at `4e2f6d96`. The implementation base is fixed at approval (SP-2) and every statement is re-checked there |

## 2. Scope

### 2.1 S5 is NOT_BUILT (design §3: a stage whose commands are missing is skipped and reported `NOT_BUILT`)

Design §11.2 seeds S5 through "the `learning_content` publication commands" and "the `ai_policy` lifecycle and resource commands". At the base:

- `application/learning_content_commands.py` (`ContentCommands`) and `application/ai_policy_commands.py` (`AiPolicyCommands`) take an injected boundary (`ContentBoundary`, `PolicyCommandBoundary`; `ResourceAccountingBoundary` for `ai_policy_accounting.py`). **No production implementation of these boundaries exists.** The only ones are test fixtures (`tests/learning_content_fixtures.py` `AssumedBoundary`, `tests/unit/test_learning_content_eligibility.py` `FixtureBoundary`, `tests/ai_policy_fixtures.py`).
- No composition builds either service. `interfaces/http/routers/learning_content.py` is a router factory tagged `governance-candidate` and is not mounted in `interfaces/http/app.py`; `AiPolicyCommands` is referenced only by `application/ai_policy_governance.py`.
- **No current flow reads the result.** `application/services/parent_story_runs.py`, `interfaces/http/routers/parent_story_runs.py`, `interfaces/http/routers/parent_ai.py` and `infrastructure/persistence/parent_story_repository.py` reference neither `learning_content` nor `ai_policy`.
- The catalog commands are organization-scoped (`execute(principal_id, organization_id, …)`). The SRS keeps the Parent activity catalog in a GLOBAL scope (SRS §11.2). Which organization a seeded catalog would use is therefore an open question for the module's owner, not a seed choice.

A seed that supplied its own boundary would assert identity, review and policy authority that the product does not grant. Rule 6 of the design forbids that. **S5 is reported `NOT_BUILT`.** It becomes buildable when a slice adds the production boundaries and a consumer reads them (SP-1).

### 2.2 S7: only item 2a is buildable

| Design item | State at the base | This package |
|---|---|---|
| §11.4 item 1, assets through the M2 artwork path | Route function only (`parent_ai.py` `/drawing-understandings`); `NOT_BUILT` | Out |
| §11.4 item 2a, `create_run` and `confirm_context` | Application methods of `ParentStoryRunService` (`services/parent_story_runs.py:40`, `:112`), taking a `VerifiedPrincipal` | **In** |
| §11.4 item 2b, understanding, story, reviews and script | Needs item 1 and the extracted `/story-revisions` command; `NOT_BUILT` | Out |
| §11.4 item 3, video and quota | Needs item 2b, Billing and the video tables; `NOT_BUILT` | Out |
| §11.8, the lifecycle changes after FR-C-08 | FR-C-08 is not merged into the seed base | Out |

### 2.3 What SEED-7a gives

- Two more Parents in the S1 data set, **P4 with K4** and **P5 with K5** (design §11.4 "Parents"). They are written by S1's direct-SQL writer with the S1 rules and have no S1 runs.
- One command-made StoryRun for each, in `INPUT_PROCESSING` with its context confirmed. These runs are made by the product's own service methods, not by direct SQL, so they are valid starting points for the later 2b and video stages.
- Each run holds its Parent's one-active-run lock (SRS §11.1 item 3). P4 and P5 have no other run.

## 3. Proposed behaviour

### 3.1 Guards

- **Database:** the S1 guard (`tools/seed/guard.py`, design rule 3, SEED-1 §3.1) runs unchanged before anything else.
- **StoryRun-lite runtime:** design §11.4 requires `STORYRUN_LITE_DATABASE_URL` to be **unset** for S7 (rule 3(c) alone also accepts the guarded URL). The S7a entry point refuses to start otherwise. It never calls the StoryRun-lite `build_runtime` and never imports its entry module.
- **Providers:** a new guard function `check_no_provider()` implements design rule 10 as an environment and settings check only:
  - the resolved `ai_provider` is `disabled` and `auth_provider` is `development`;
  - the provider fields of rule 10 are empty and `clamav_host` is unset or loopback;
  - the `STORYRUN_LITE_*` switches take their allowed values;
  - no `MODAL_*` variable is set except `MODAL_CONFIG_PATH`, which the seed sets to a missing file before any `modal` import.
  It opens no connection. S7a itself calls no provider: `create_run` and `confirm_context` do not.
- **Storage:** S7a writes no object, so design rule 9 does not apply. The three R5 notes that D-066-80 carries concern object keys, so they move on to the first object-writing stage task (S7 item 1 or S8).
- **No URL or secret is printed.** Refusals raise fixed messages with `from None`, as in SEED-1.

### 3.2 S1 additions (direct SQL, S1 rules unchanged)

- `data.py` adds the Parent subjects `seed-parent-p4` and `seed-parent-p5` with the S1 issuer (SD-5 coupling unchanged), UUIDv5 `account_id`, `account_role = parent` and `role_revision = 1`.
- It adds the Parent profiles K4 and K5 (`parent.child_profiles` with the first `parent.profile_revisions` row). `revision_hash` comes from the domain snapshot function, ages lie between 36 and 120 months, and `data_origin` is synthetic with no consent, as for K1 to K3.
- No S1 StoryRun is added for P4 or P5.
- `EXPECTED_COUNTS` grows by the new identity, profile and revision rows. The S1 writer stays insert-if-absent in one transaction. On a seed database that already holds the old S1, a new S1 run adds exactly the P4 and P5 rows. This is allowed because S3 has not run (design §3).

### 3.3 The S7a writer

`python -m tools.seed.s7a_runs`, run from `backend/`, in one process, for P4 and then P5:

1. Build the principal as the Parent route would accept it: `VerifiedPrincipal(subject, issuer, roles)` with the seeded subject and issuer. The roles are re-derived at implementation from the Parent verifier path (§7). Check the identity as the route's `_require_parent` does: active, with `account_role == parent`.
2. Build the service exactly as the route does: `ParentStoryRunService(SqlParentStoryRunRepository(session), SqlParentStoryProfileLookup(session))` (`routers/parent_story_runs.py:68–72`), on a session from the guarded engine.
3. **Replay-safe start:** call `get_active_run(principal)`.
   - If no run is active, call `create_run` with:
     - the seeded `account_id`;
     - `parent_profile_id = K4` (or `K5`);
     - the stable key `seed:s7a:p4:create-1` (or `p5`);
     - a fixed synthetic `topic` and `adult_confirmed_idea` with the `[SEED]` prefix.
   - If a run is active and it is the seed's run, keep it. "The seed's run" means it sits on the seeded profile and its context snapshot equals the seed's values. If the active run is any other run, stop with `S7A_FOREIGN_ACTIVE_RUN`.
4. If the run's context is not yet confirmed, call `confirm_context` with:
   - the record's `context_revision` and `context_snapshot_sha256`;
   - the stable key `seed:s7a:p4:confirm-1` (or `p5`).
5. The run must now be in `INPUT_PROCESSING` with a confirmed context. Any other state stops the task.
6. Commit as the route does (§7). Print only the counts and the two run states, never IDs, URLs or content.

**Markers and counts (design rule 4, §10):**
- Product-made run IDs are random. The runs are counted through the seeded Parent principal.
- The command receipts are counted through the stable seed keys.

### 3.4 Idempotency

- A second S7a run finds each active run through `get_active_run` and its context already confirmed, so it calls neither command.
- The second run creates **zero** rows. The owner-run test asserts this.
- S7a never cancels, deletes or advances a run.

## 4. Proposed allowlist

| # | File | Class | Note |
|---|---|---|---|
| 1 | `backend/tools/seed/data.py` | E | P4, P5, K4, K5 rows; new `EXPECTED_COUNTS`; the S7a keys, topics and ideas; `EXPECTED_S7A_COUNTS` (per-table deltas) |
| 2 | `backend/tools/seed/guard.py` | E | `check_no_provider()` and the S7a `STORYRUN_LITE_DATABASE_URL` check; the S1 guard is unchanged |
| 3 | `backend/tools/seed/s7a_runs.py` | N | §3.3 writer |
| 4 | `backend/tests/unit/test_seed_data.py` | E | P4/P5 markers, ages, synthetic origin, one profile each, no S1 run for P4 or P5, `EXPECTED_COUNTS` |
| 5 | `backend/tests/unit/test_seed_guard.py` | E | Every refusal case of `check_no_provider()`, each asserting that no secret or URL fragment is printed; `MODAL_CONFIG_PATH` set before any `modal` import, and `modal.config.user_config_path` equal to it, checked in a subprocess |
| 6 | `backend/tests/unit/test_seed_s7a.py` | N | Pure: the writer's decision table (no active run → create; seed run → keep; foreign run → stop; confirmed → no confirm) against a fake service |
| 7 | `backend/tests/integration/test_seed_s1_postgres.py` | E | Expected counts include P4 and P5 |
| 8 | `backend/tests/integration/test_seed_s7a_postgres.py` | N | Owner-run. It calls the guards first and skips when `S2L_SEED_DATABASE_URL` is unset. Steps: run S1, then S7a twice. Check: zero new rows on the second S7a run; `EXPECTED_S7A_COUNTS`; for P4 and P5, one active run in `INPUT_PROCESSING` with a confirmed context, read back through `get_active_run` and validated through `ParentStoryRunResponseV1`; P1 to P3 unchanged |
| 9 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S7A_<date>.md` | N | Runbook: fresh seed database, `upgrade heads`, S1, S7a twice, the tests, the provider-variable list in PowerShell form |
| 10 | `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/SEED_7A_IMPLEMENTATION_EVIDENCE_<date>.md` | N | Evidence note, written by the coordinator |

- **Read-only imports:**
  - `ParentStoryRunService`, `SqlParentStoryRunRepository` and `SqlParentStoryProfileLookup`;
  - `VerifiedPrincipal` and the adult-identity model;
  - `ParentStoryRunResponseV1`, in test 8 only;
  - the SEED-1 imports listed in SEED-1 §4.

  A change to any product module stops the task for an owner scope amendment.
- **Governance records**, outside the code allowlist: the Task Approval entry, a decision row for SP-1, and the `STATUS.md` and `CONTEXT.md` entries. The coordinator writes them append-only, on the owner's word, and they go into the same task commit.
- **Naming cautions** (SEED-1 §4):
  - no path combines `seed` with `account`, `credential` or `user`;
  - no UPPER-case name contains TOKEN, SECRET, PASSWORD, API_KEY or PRIVATE_KEY.

  The provider-variable names appear only as string literals in a lower-case tuple.

## 5. Verification and command ceiling

**Coordinator, without a database:** run in PowerShell, each command from its stated working directory.

| # | Working directory | Command |
|---|---|---|
| 1 | `backend/` | `ruff check tools/seed tests/unit/test_seed_guard.py tests/unit/test_seed_data.py tests/unit/test_seed_s7a.py tests/integration/test_seed_s1_postgres.py tests/integration/test_seed_s7a_postgres.py` |
| 2 | `backend/` | `MYPYPATH=src`, then `mypy --explicit-package-bases tools/seed` |
| 3 | `backend/` | `pytest tests/unit/test_seed_guard.py tests/unit/test_seed_data.py tests/unit/test_seed_s7a.py` |
| 4 | `backend/` | `pytest tests/unit tests/contract`, compared with the base by failing test id. Only failures that are new against the base count |
| 5 | repository root | the four repository validators |
| 6 | repository root | `git add -N` on the four new paths only, then `git diff --check` |

**Owner-run, in the owner's own terminal, against a fresh seed database only.** The name contains `seed`. The port is a loopback port that is neither 5432 nor 5433. The database is never `be1_acceptance`, `sketch2life_m2_s1a` or an M2 gate database. No local secrets directory is read.

1. `alembic upgrade heads` with `S1A_P_ALEMBIC_DATABASE_URL` set explicitly to the seed URL (SEED-1 §5).
2. S1, then S7a run 1 and S7a run 2.
3. Tests 7 and 8.

The runbook repeats SEED-1's warning: never `upgrade` a database that is already seeded; re-seed instead. It also carries design §11.8's warning: never run the FR-C-08 reconciliation command, its consumer, an outbox publisher or a sweep on a seed database.

**Evidence:** counts before and after S7a run 2, exit codes, log hashes, no URL. Then an independent evidence review on Sonnet 5.5 at high effort. Then one task commit, on the owner's word, with no push.

## 6. Acceptance

- Every refusal case of §3.1 is refused, without printing any part of a URL or secret.
- S1 creates `EXPECTED_COUNTS`, including P4 and P5.
- S7a run 1 creates `EXPECTED_S7A_COUNTS` and run 2 creates zero rows.
- P4 and P5 each have exactly one active run, in `INPUT_PROCESSING` with a confirmed context, readable through `get_active_run`.
- P1 to P3 and their S1 runs are unchanged.
- Tests 1 to 8 pass and the unit/contract suite has no new failures against the base.
- The diff contains no secret.
- **Deferred, as in SEED-1:** "each role can open its main FE screen with data" waits for SD-5 (adult sign-in).

## 7. Not verified (each is re-checked at the implementation base; any surprise stops the task)

- The `roles` that the Parent verifier path gives a Parent principal. `_require_parent` checks the identity row, not the roles.
- Where the repository commits. Does `create_run` or `confirm_context` commit itself, or does the route's session dependency commit? The writer must follow the same rule. Check this at `parent_story_repository.py` and in `get_db`.
- How `create_run` replays a reused idempotency key. The design avoids depending on it by checking `get_active_run` first.
- Whether `create_run` needs any lesson or catalog input beyond the optional lesson pin. It is called without one.
- Whether the FR-C-08 merge changes `create_run` or `confirm_context`. SEED-7a is planned on the pre-merge base.

## 8. Owner decisions

| ID | Question | Recommendation |
|---|---|---|
| SP-1 | Record S5 as `NOT_BUILT` (§2.1) and park it until a slice adds the production content and policy boundaries and a flow reads them? | Yes. The design already says a stage with missing commands is `NOT_BUILT`; this records it with the evidence |
| SP-2 | Base and branch. The Draft 7 to 11 design files and D-066-80 are uncommitted in `.worktrees/seed1`. Commit them first as one docs commit on `feature/feat066-seed1`, then cut a new local branch `feature/feat066-seed7a` from it for the code? | Yes: one docs commit, then the new branch; no push |
| SP-3 | Slot. SEED-7a changes only `backend/tools/seed/`, seed tests and FEAT-066 docs, with no product module. May it run in parallel with the BE queue? | Yes, because it shares no file with FR-C-08 or Billing |
