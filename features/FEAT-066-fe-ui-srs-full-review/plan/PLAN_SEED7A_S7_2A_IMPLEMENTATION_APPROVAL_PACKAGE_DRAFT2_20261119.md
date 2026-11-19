# FEAT-066 SEED-7a — S7 item 2a (command-made Parent runs), with S5 found NOT_BUILT: implementation approval package (Draft 2)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package proposes one bounded implementation slice. It authorizes no script, database, command, stage, commit or push.
- **Date:** 2026-11-19. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2. Lane L1 is the owner's own work.
- **Supersedes:** Draft 1 (15,936 B, `B21C251E…`). Its cold review was round 1 (Sonnet 5.5, high): `tmp/seed7a-pkg-review/SEED7A_PACKAGE_DRAFT1_COLD_REVIEW_R1_20261119.md`. The file is local and ignored, 25,117 B, `9625A3C2…`. The verdict was NOT READY, 0 P1 / 4 P2 / 8 P3. §9 maps each finding to its fix.
- **Owner direction applied after Draft 1 (2026-11-19):** all BE work goes on the single local integration branch `feature/feat066-be-integration`. It is pushed to `dev` as one PR once stable. No separate seed branch is cut (§8 SP-2).

## 1. Authority and pins

| Input | Pin |
|---|---|
| Seed design (accepted, D-066-80) | `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT11_20261119.md`, 73,863 B, `6E4EFDE08E2763B6A0B0CCAE6CC4DC5301457961B22EB46BBF520D401C727CE8` |
| Decision record | `DECISIONS.md` in `.worktrees/seed1` with D-066-80 appended: 73,010 B, `A1C589570F17537B6B5118F0A2F69F1C90021138DE24F2FFB42241A791740C7A` (uncommitted) |
| SEED-1 (stage S1, implemented) | commit `4e2f6d96`; package `plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md` |
| Working SRS (D-209) | 701,157 B, `B9B1F42D…`: §11.1 item 3 (one active run per owner), §11.2 (owner scopes), §24.1 (synthetic data only) |
| Base and target | Local branch `feature/feat066-be-integration` in `.worktrees/be-integration`. It is `origin/dev`, then `feature/feat066-seed1` (merge `732111ee`), then FR-C-08 (merge `ed9ab3a6`, HEAD when this draft was written). `backend/tools/seed/` there is identical to `4e2f6d96`. The base includes FR-C-08. Every statement is re-checked at the implementation HEAD |

## 2. Scope

### 2.1 S5 is NOT_BUILT (design §3: a stage whose commands are missing is skipped and reported `NOT_BUILT`)

Design §11.2 seeds S5 through two sets of commands: "the `learning_content` publication commands" and "the `ai_policy` lifecycle and resource commands". At the base:

- **Stores exist, boundaries do not.** The production stores exist: `infrastructure/learning_content/sql.py` (`SqlContentStore`) and the `ai_policy` SQL stores. But `ContentCommands` (`application/learning_content_commands.py`), `AiPolicyCommands` (`application/ai_policy_commands.py`) and `ResourceAccountingService` (`application/ai_policy_accounting.py`) take injected boundaries: `ContentBoundary`, `PolicyCommandBoundary` and `ResourceAccountingBoundary`. **No production implementation of those boundaries exists.** The only ones are test fixtures:
  - `tests/learning_content_fixtures.py` `AssumedBoundary`;
  - `tests/unit/test_learning_content_eligibility.py` `FixtureBoundary`;
  - `tests/ai_policy_fixtures.py`.
- **Nothing composes the services.** `interfaces/http/routers/learning_content.py` is a router factory tagged `governance-candidate` that `interfaces/http/app.py` does not mount. `AiPolicyCommands` is referenced only by `application/ai_policy_governance.py`.
- **No current flow reads the result.** The Parent story modules (`application/services/parent_story_runs.py`, `routers/parent_story_runs.py`, `routers/parent_ai.py`, `infrastructure/persistence/parent_story_repository.py`) reference neither `learning_content` nor `ai_policy`.
- **Scope mismatch.** The catalog commands are organization-scoped (`execute(principal_id, organization_id, …)`), but SRS §11.2 keeps the Parent activity catalog in GLOBAL scope. Which organization a seeded catalog would use is a question for the module owner, not a seed choice.

A seed that supplied its own boundary would assert identity, review and policy authority that the product does not grant, which design rule 6 forbids. **S5 is reported `NOT_BUILT`** (SP-1).

### 2.2 S7: only item 2a is buildable

| Design item | State at the base | This package |
|---|---|---|
| §11.4 item 1: assets through the M2 artwork path | Route function only (`parent_ai.py` `/drawing-understandings`); `NOT_BUILT` | Out |
| §11.4 item 2a: `create_run` and `confirm_context` | Application methods of `ParentStoryRunService`, taking a `VerifiedPrincipal` | **In** |
| §11.4 item 2b: understanding, story, reviews and script | Needs item 1 and the extracted `/story-revisions` command; `NOT_BUILT` | Out |
| §11.4 item 3: video and quota | Needs item 2b, Billing and the video tables; `NOT_BUILT` | Out |
| §11.8: S1 lifecycle rows after FR-C-08 | FR-C-08 is in the base. The §11.8 SEED task (removing the direct-SQL `DELETE_PENDING` run, a `delete_run` case, a `cancel_run` case) is separate | Out. The runbook warning applies (§5) |

### 2.3 What SEED-7a gives

- Two more Parents in the S1 data set, **P4 with K4** and **P5 with K5** (design §11.4 "Parents"), written by S1's direct-SQL writer under the S1 rules. They have no S1 runs.
- One command-made StoryRun for each, in `INPUT_PROCESSING` with a confirmed context. The product's own service methods make these runs, so they are valid starting points for the later item 2b and video stages.
- Each run holds its Parent's one-active-run lock (SRS §11.1 item 3).
- **Stage class:** design §3 calls S7 to S10 one-shot per seed database. Item 2a is stricter than that: it is replayable through stable keys and the replay-safe start in §3.4. It consumes no quota and calls no provider. This is a recorded exception, not a conflict.

## 3. Proposed behaviour

### 3.1 Guard order (design rules 3 and 10)

1. **`check_s7a_environment()`** runs first, before any settings are read and before `guarded_engine()` (which calls `prepare_runtime`, `guard.py:167–178`). It checks only the process environment:
   - `STORYRUN_LITE_DATABASE_URL` is **unset**. Rule 3(c) alone also accepts the guarded URL; design §11.4 requires unset for S7.
   - `STORYRUN_LITE_VISION_MODE` is unset or `loopback`. `STORYRUN_LITE_STORY_MODE` is unset or `disabled`. `STORYRUN_LITE_VISION_LOOPBACK_URL` is unset or a loopback URL. `STORYRUN_LITE_MODAL_BASE_URL`, `STORYRUN_LITE_MODAL_TOKEN` and `STORYRUN_LITE_MODAL_RUN_ID` are unset.
   - No `MODAL_*` variable is set except `MODAL_CONFIG_PATH`.
   - It then sets `MODAL_CONFIG_PATH` for the process to a path that it computes at run time inside the run's own scratch folder and verifies does not exist. The path is never committed. No `modal` import happens before this.
2. **`guarded_engine()`**, the S1 guard, runs next and is unchanged (design rule 3, SEED-1 §3.1).
3. **`check_no_provider()`** runs after `prepare_runtime`, on the resolved settings:
   - `ai_provider = disabled` and `auth_provider = development`;
   - empty `firebase_project_id`, `firebase_credentials_file`, `firebase_admin_json_base64`, `lightning_ai_base_url`, `lightning_ai_token_file`, `runpod_endpoint_id` and `runpod_api_key_file`;
   - `clamav_host` unset or loopback.
4. The installed Modal SDK is version **1.6.3** (`backend/pyproject.toml`); rule 10 cites 1.6.4. Test 5 re-checks against the installed version that `modal.config.user_config_path` equals the computed missing path, in a subprocess.

**Storage:** S7a writes no object, so design rule 9 does not apply. The three R5 notes that D-066-80 carries concern object keys, so they move to the first object-writing stage task (S7 item 1 or S8).

**Messages:** refusals and errors raise fixed messages with `from None`. They never contain a URL, an ID, a secret or content, as in SEED-1. `ParentStoryRunError` and `ParentStoryRunServiceError` are mapped to fixed S7a messages that carry only the error code.

### 3.2 S1 additions (direct SQL, S1 rules unchanged)

**New `PARENT_PROFILE_SPECS` rows,** in the existing style:
- `("k4", "p4", "ACTIVE", (("[SEED] K4", 72, "Thích vẽ chim"),))`
- `("k5", "p5", "ACTIVE", (("[SEED] K5", 96, "Thích vẽ nhà"),))`

**New Parent subjects:** `seed-parent-p4` and `seed-parent-p5` in `PARENT_SUBJECTS`. Each gets the S1 issuer (SD-5 coupling unchanged), a UUIDv5 `account_id`, `account_role = parent` and `role_revision = 1`.

**Other rules:**
- Synthetic origin with no consent, as for K1 to K3.
- `revision_hash` comes from the domain snapshot function.
- No S1 StoryRun is added for P4 or P5.

**`EXPECTED_COUNTS` changes:**

| Table | Before | After |
|---|---:|---:|
| `be1_adult_identities` | 23 | 25 |
| `parent.child_profiles` | 3 | 5 |
| `parent.profile_revisions` | 5 | 7 |

Every other value is unchanged.

**Counting scope (fixes R1 F-01):** `s1_core.py` today counts whole tables (`s1_core.py:101–107`). S7a adds rows to `story.runs` and `story.run_inputs`, so a whole-table S1 count would fail after S7a. `s1_core.py` therefore changes to count **only S1-owned rows**, by the S1 key sets that `data.py` already builds: the S1 `run_id` set for `story.runs` and `story.run_inputs`, and the S1 ID sets for the other tables. The allowlist adds `s1_core.py`. S1's run-twice behaviour and its insert-if-absent writer are unchanged.

**Upgrade rule (Draft 11 §11.4):**
- A seed database created before SEED-7a is **re-seeded**: drop it, recreate it, run `upgrade heads`, run S1, then run S7a.
- Running the new S1 on an old seed database would add only the P4 and P5 rows (insert-if-absent). That is a convenience; it is not asserted or tested.

### 3.3 The S7a writer

Command: `python -m tools.seed.s7a_runs`, run from `backend/`. Guard order as in §3.1. For P4 and then P5:

1. **Identity check:** re-implement the route's `_require_parent` check against `AdultIdentityModel`. The identity must be active, with `account_role == "parent"`. The writer does not import the router module.
2. **Principal:** `VerifiedPrincipal(subject=…, issuer=<S1 issuer>, roles=frozenset())`. The Parent path checks the identity row, not the roles.
3. **Service:** build it on a session from `create_core_session_factory(engine)`, over the guarded engine, exactly as the route builds it: `ParentStoryRunService(SqlParentStoryRunRepository(session), SqlParentStoryProfileLookup(session))` (`routers/parent_story_runs.py`).
4. **Decision table:**

   | `get_active_run(principal=…, account_id=…)` | Context | Action |
   |---|---|---|
   | none | — | `create_run(…)`, then `confirm_context(…)` |
   | the seed's run | unconfirmed | `confirm_context(…)` only. This is crash recovery between the two commits |
   | the seed's run | confirmed | nothing |
   | any other run | — | stop with `S7A_FOREIGN_ACTIVE_RUN` |

   "The seed's run" means the run is on the seeded profile, its topic and idea equal the seed's values, and its context snapshot SHA-256 equals the value recomputed from them.
5. **`create_run` inputs:**
   - the seeded `account_id`;
   - `parent_profile_id` = K4 or K5;
   - `idempotency_key` = `seed:s7a:p4:create-1` (or `p5`);
   - a fixed `[SEED]` topic and `adult_confirmed_idea` from `data.py`;
   - no lesson pin.
6. **`confirm_context` inputs:** the record's `context_revision` and `context_snapshot_sha256`, with `idempotency_key` = `seed:s7a:p4:confirm-1` (or `p5`).
7. **End check:** the run must be in `INPUT_PROCESSING` with a confirmed context. Any other state stops the task.
8. **Commits:** the repository commits inside each command (`parent_story_repository.py`). `get_db` does not commit and the router does not commit. The writer adds no commit of its own.
   - S7a is **not atomic per Parent**: there are two committed transactions.
   - A crash after the create leaves an unconfirmed seed run. Row 2 of the decision table recovers it.
9. **Output:** only the counts and the two run states. It prints no ID, URL or content.

**Clock:** `create_run` and `confirm_context` stamp wall-clock time (`datetime.now(UTC)`), while S1 uses the fixed `SEED_TIME`. S7a uses wall-clock time, and no clock-sensitive case is asserted (Draft 11 §11.9).

### 3.4 Idempotency and counts

**Replay:** a second S7a run takes row 3 of the decision table for both Parents. It calls no command and creates **zero** rows.

**`EXPECTED_S7A_COUNTS`** gives the rows S7a run 1 adds:

| Table | Rows | Counted through |
|---|---:|---|
| `story.runs` | 2 | The seeded Parent principals (`active_owner_parent_account_id`, `actor_scope_ref`) |
| `story.run_inputs` | 2 | The FK to those runs |
| `story.command_receipts` | 4 | The FK `resource_ref` → those runs: one `CREATE_RUN` and one `CONFIRM_CONTEXT` per Parent. The table stores only the hash of the key, so the stable key is not the counting handle |

`story.command_receipts` is not among the S1 tables. The S7a counts are S7a-scoped, in the same way as the S1 counts in §3.2.

## 4. Proposed allowlist

| # | File | Class | Note |
|---|---|---|---|
| 1 | `backend/tools/seed/data.py` | E | P4, P5, K4, K5; new `EXPECTED_COUNTS`; S7a keys, topics and ideas; `EXPECTED_S7A_COUNTS` |
| 2 | `backend/tools/seed/guard.py` | E | `check_s7a_environment()` and `check_no_provider()`; the S1 guard is unchanged |
| 3 | `backend/tools/seed/s1_core.py` | E | S1-scoped counting (§3.2); writer unchanged |
| 4 | `backend/tools/seed/s7a_runs.py` | N | §3.3 writer |
| 5 | `backend/tests/unit/test_seed_data.py` | E | P4/P5 markers, ages, synthetic origin, one profile each, no S1 run for P4 or P5, new `EXPECTED_COUNTS`, the S1 key sets used for counting |
| 6 | `backend/tests/unit/test_seed_guard.py` | E | Every refusal of the two new checks, each asserting that nothing secret or URL-like is printed. Variables whose names contain TOKEN or SECRET use placeholder values. The `MODAL_CONFIG_PATH` subprocess check |
| 7 | `backend/tests/unit/test_seed_s7a.py` | N | Pure: the four rows of the decision table and the error mapping, against a fake service |
| 8 | `backend/tests/integration/test_seed_s1_postgres.py` | E | S1-scoped counts; still passes when S7a rows exist |
| 9 | `backend/tests/integration/test_seed_s7a_postgres.py` | N | Owner-run; skips when `S2L_SEED_DATABASE_URL` is unset. It calls the guards in §3.1 order, then: S1, S7a twice, zero new rows on the second S7a run, `EXPECTED_S7A_COUNTS`. For P4 and P5, `get_active_run` returns a `ParentStoryRunRecord` (not the lifecycle record of the `ParentStoryRunView` union) in `INPUT_PROCESSING` with a confirmed context, and validated through `ParentStoryRunResponseV1`. P1 to P3 and their S1 runs are unchanged |
| 10 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S1_20261119.md` | E | Counts updated (identities 25, Parent profiles 5, revisions 7) and the re-seed rule of §3.2 |
| 11 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S7A_<date>.md` | N | Runbook (§5) |
| 12 | `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/SEED_7A_IMPLEMENTATION_EVIDENCE_<date>.md` | N | Evidence note, written by the coordinator |

**Read-only imports:**
- `ParentStoryRunService`, `SqlParentStoryRunRepository`, `SqlParentStoryProfileLookup` and `create_core_session_factory`;
- `VerifiedPrincipal` and `AdultIdentityModel`;
- `ParentStoryRunRecord` and the service and repository error types;
- `ParentStoryRunResponseV1`, in test 9 only;
- the SEED-1 imports (SEED-1 §4).

A change to any product module stops the task for an owner scope amendment. The implementer traces the import graph of `parent_story_repository.py` once and records whether it reads settings at import time. If it does, that is a stop for amendment.

**Governance records** sit outside the code allowlist: the Task Approval entry, a decision row for SP-1, and the `STATUS.md` and `CONTEXT.md` entries. The coordinator writes them append-only on the owner's word.

**Naming cautions:**
- no path combines `seed` with `account`, `credential` or `user`;
- no UPPER-case name contains TOKEN, SECRET, PASSWORD, API_KEY or PRIVATE_KEY;
- the variable names in §3.1 appear only as string literals in a lower-case tuple.

## 5. Verification and command ceiling

**Coordinator, without a database.** PowerShell; each command names its working directory, inside `.worktrees/be-integration`.

| # | Working directory | Command |
|---|---|---|
| 1 | `backend/` | `ruff check tools/seed tests/unit/test_seed_guard.py tests/unit/test_seed_data.py tests/unit/test_seed_s7a.py tests/integration/test_seed_s1_postgres.py tests/integration/test_seed_s7a_postgres.py` |
| 2 | `backend/` | `MYPYPATH=src`, then `mypy --explicit-package-bases tools/seed` |
| 3 | `backend/` | `pytest tests/unit/test_seed_guard.py tests/unit/test_seed_data.py tests/unit/test_seed_s7a.py` |
| 4 | `backend/` | `pytest tests/unit tests/contract`, compared with the base by failing test id; only failures new against the base count |
| 5 | repository root | `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `python tools/validate_skeleton.py` |
| 6 | repository root | `git add -N` on the six new paths only, then `git diff --check` |

**Owner-run, in the owner's own terminal, against a fresh seed database only.**
- The database name contains `seed`.
- The port is a loopback port that is neither 5432 nor 5433.
- The database is never `be1_acceptance`, `sketch2life_m2_s1a` or an M2 gate database.
- No local secrets directory is read.

Steps:
1. Run `alembic upgrade heads` with `S1A_P_ALEMBIC_DATABASE_URL` set explicitly to the seed URL (SEED-1 §5).
2. Run S1, then S7a run 1, then S7a run 2.
3. Run tests 8 and 9.

**Runbook warnings:**
- Never `upgrade` a database that is already seeded; re-seed it instead.
- Never run, on a seed database:
  - the FR-C-08 reconciliation command;
  - its lifecycle consumer;
  - an outbox publisher;
  - a sweep runner.

  The base contains FR-C-08, and the S1 direct-SQL `DELETE_PENDING` run has no event (design §11.8).

**Evidence and review:**
- Evidence: counts before and after S7a run 2, exit codes and log hashes, with no URL.
- Then an independent evidence review on Sonnet 5.5 high.

**Commit plan (fixes R1 F-08), on the owner's word only, with no push except as the integration PR:**
1. **Docs commit:** the seed design Drafts 7 to 11, D-066-80, this package (all drafts), and the Task Approval entry once approved. It is carried from `.worktrees/seed1` onto the integration branch as one docs commit. It is a separate finished task: the design acceptance and the package.
2. **SEED-7a task commit:** the code and tests of §4, the runbooks, the evidence note, its review record, and the `STATUS.md` and `CONTEXT.md` entries.

## 6. Acceptance

- Every refusal of §3.1 happens in the stated order, without printing any part of a URL or secret.
- S1 creates `EXPECTED_COUNTS` with P4 and P5, and its S1-scoped counts still pass after S7a.
- S7a run 1 creates `EXPECTED_S7A_COUNTS`, and run 2 creates zero rows.
- P4 and P5 each have exactly one active run, a `ParentStoryRunRecord` in `INPUT_PROCESSING` with a confirmed context.
- P1 to P3 and their S1 runs are unchanged.
- Tests 1 to 9 pass, and the unit and contract suite has no new failures against the base.
- The diff contains no secret.
- **Deferred, as in SEED-1:** "each role can open its main FE screen with data" waits for SD-5 (adult sign-in).

## 7. Not verified (re-checked at the implementation HEAD; any surprise stops the task)

- That `create_run` and `confirm_context` write rows only to the three tables in §3.4. No trigger or migration side effect was traced.
- That importing the Parent story repository reads no settings and imports no entry module (§4).
- The post-FR-C-08 behaviour of `create_run`, `confirm_context` and `get_active_run`. The signatures were checked at `ed9ab3a6`: `create_run` and `get_active_run` take `principal` and `account_id` and return `ParentStoryRunView`. The behaviour was not.
- The Modal 1.6.3 variable list against rule 10 (test 5 checks it).

## 8. Owner decisions

| ID | Question | Recommendation |
|---|---|---|
| SP-1 | Record S5 as `NOT_BUILT` (§2.1) and park it until a slice adds the production content and policy boundaries and a flow reads them? | Yes |
| SP-2 | Base and target. Owner direction (2026-11-19): `feature/feat066-be-integration`, with the docs commit and the task commit of §5. Nothing is written into `.worktrees/be-integration` before this package is approved. | Recorded as given |
| SP-3 | Slot. SEED-7a changes only `backend/tools/seed/`, seed tests and FEAT-066 docs, and no product module. May it run as the next integration-branch slice, alongside other BE planning? | Yes |

## 9. Round-1 findings and their fixes

| ID | Fix |
|---|---|
| F-01 | §3.2 counting scope: `s1_core.py` counts S1-owned rows by the S1 key sets; allowlist row 3; test 8 passes after S7a |
| F-02 | §3.3 step 8: the repository commits; no writer commit; non-atomic per Parent, recovered by decision row 2; `create_core_session_factory` named |
| F-03 | Allowlist row 10: the S1 runbook updated; one upgrade rule (re-seed), with insert-if-absent not asserted |
| F-04 | §3.1 order: `check_s7a_environment()` before `guarded_engine()`, `check_no_provider()` after `prepare_runtime` |
| F-05 | §3.1: the `STORYRUN_LITE_*` names and values listed, `MODAL_CONFIG_PATH` computed at run time, Modal 1.6.3 noted; test 5 uses placeholder values |
| F-06 | §3.4: `EXPECTED_S7A_COUNTS` with `story.command_receipts` counted through the run FK |
| F-07 | §3.3: `account_id` passed; recovery row added; `_require_parent` re-implemented without importing the router; `roles=frozenset()`; error mapping |
| F-08 | §5 commit plan: one docs commit and one task commit, each a finished task; base restated (SP-2) |
| F-09 | §3.2: K4 and K5 specs and the new counts 25, 5 and 7 |
| F-10 | §5 row 5: the four validators named |
| F-11 | §3.3 clock line |
| F-12 | §2.3 stage-class exception; §2.1 names `SqlContentStore` and the `ai_policy` SQL stores |
