# Phase B B6 conformance evidence — 2026-10-16

- Status (updated for CR01 r2): **B6_CR01_R2_PENDING_CODEX_REVIEW** (§12.6). Earlier for B6-CR01:
  **B6_CR01_FIXED_PENDING_RUNTIME_REVIEW** (§12); independent closure
  review CLOSE_WITH_NOTES (notes/PHASE_B_B6_CLOSURE_REVIEW_20261016.md). Earlier: B6_RUNTIME_PASS (§11).
- Earlier status line: **B6_RUNTIME_PASS — PENDING_INDEPENDENT_CLOSURE_REVIEW**
  (§11). Earlier: B6_FIX01_SELF_REVIEWED (§10); B6_FIX01_CODE_COMPLETE. Run 1
  FAILED on one test defect (B6-RT01, §9); the fix01 package has no runtime result yet. B6 is not
  closed, BE2-01 stays IN_PROGRESS, and full-card DONE is 0. Sections 1–8 describe the original
  B6 package and remain accurate for it.
- Executor: Claude. Authority: the existing Phase B plan rev3 B1–B6 approval
  (approvals/PHASE_B_TASK_APPROVAL.md, plan sha256 bb20d5be…, unchanged). The user started B6 in
  chat with step 2 of the reset handover. No approval was written and no card was opened.
- Baseline: base 993a26c plus the closed B5 manifest fix03 `3930046b…` (43 files), identical
  locally and on the last reported Studio run (193 B2–B5 + 224 Phase A PASS,
  USER_REPORTED_REMOTE).
- Handoff: notes/PHASE_B_B6_HANDOFF_20261016.md (B-12 receivers). Metrics:
  metrics/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.json. Receipts: ignored
  local/b6-local-checks-20261016/ and package local/b6-studio-package-20261016/.

## 1. What B6 adds (3 new files; no existing file changed)

| File | Purpose |
|---|---|
| features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py | Plan §4 B6 runner: A-01..A-20 mapped one by one; durable scenarios on the real SQL adapter + Redis/RQ; §7.1 crash matrix and B-01..B-12 resolved from this run's JUnit + Phase A evidence; report JSON; exit 0/1/2 |
| backend/tests/integration/ai_jobs/test_restart_recovery.py | Planned B-01 file: real process kill (`os._exit`) and restart; covers the windows not yet proven (W01, W02, W06, W08 restart) |
| backend/tests/unit/test_ai_job_b6_conformance.py | Offline proof of the runner's decisions: JUnit resolution, mapping freshness, exit codes, NOT_RUN without services, and no PASS from JUnit alone |

The delta is additive. All 43 fix03 files are byte-identical, so the closed B1–B5 code was not
reworked. New union manifest: 46 files.

## 2. Mapping: plan §8 acceptance

| ID | Proven before B6 (closed batches) | Added by B6 | Status in the B6 run |
|---|---|---|---|
| B-01 | B2 schema level only (committed rows read back by a new connection) | test_restart_recovery: kill before commit (nothing durable, same key creates); kill after commits (checksum of every ai_jobs row identical after restart; receipt id and fingerprint kept; pending outbox published; side effects delivered); start then kill (policy retry) | Required; from this run's JUnit |
| B-02 | B4 broker outage / RQ publish | — | Required; JUnit |
| B-03 | B3 two-process create races | — | Required; JUnit |
| B-04 | B4 receive-before-start, publish bound, dispatch loss, lease takeover | — | Required; JUnit |
| B-05 | B5 single authoritative completion, attempt-bound HMAC, token-free state/logs | A-05/A-06/A-17 durable scenarios | Required; JUnit and runner |
| B-06 | B4 (a/b) and B5 (c/d) windows, as separate tests | Consolidated §7.1 matrix W01–W12 plus the new restart tests | Required; all windows PASS |
| B-07 | B3 semantic isolation | A-03 R02 durable | Required; JUnit |
| B-08 | B3 create boundaries, B5 completion boundaries, incident 503 | A-06 rollback durable | Required; JUnit |
| B-09 | B3 owner fences (a–d), B5 notices (e–g) | A-14 durable | Required; JUnit |
| B-10 | B5 capability on real Redis/RQ | **Phase A scenarios on the SQL adapter** (A-03..A-17) with real Redis/RQ and HMAC | Required; runner |
| B-11 | B2 migration matrix; Phase A fake suites | Consolidated report: migrations JUnit, Phase A JUnit (0 skips), fixture runner report, this report | Required |
| B-12 | — | Explicit handoff list (owners) | **HANDOFF, never PASS** |

## 3. Mapping: plan §7.1 crash windows (W01–W12)

| W | Window | Evidence (tests in the same run) | Note |
|---|---|---|---|
| W01 | Crash before create commit | **new** restart W01; create-boundary rollback ×6 | Nothing durable; same key retries |
| W02 | Commit done, before publish (process killed) | **new** kill-after-commit; rows read back | Checksum identical; restarted dispatcher publishes |
| W03 | Enqueued, crash before fenced mark | B4 real child kill + stale lease | Same attempt; start deduplicates |
| W04 | Broker down | B4 outage | Row stays pending; no extra attempt |
| W05 | Received, died before durable start | B5 real worker child; B4 republish/bound/loss/CAS | Same attempt, then dispatch loss |
| W06 | Started, died before provider result | **new** start-then-kill; B4 overdue sweeps | PROVIDER_TIMEOUT, then policy retry |
| W07 | Provider returned, died before completion commit | B5 real worker child; uncommitted output | **Bounded**: no same-claim recovery, no claim journal, no invented fingerprint; the provider may run twice |
| W08 | Completion committed, before audit/quarantine delivery | B5 restarted delivery; **new** kill-after-commit delivery | Same stored event ids |
| W09 | Quarantine applied, crash before mark | B5 crash-after-effect | Sink no-op; artifact changed once |
| W10 | Rejection/conflict before incident commit | B5 503, repeated incident, concurrent conflict | Committed once |
| W11 | Failure at any completion write boundary | B5 five completion boundaries | Whole rollback (B-08a) |
| W12 | Crash mid-notice | B5 notice crash and redelivery | No COMPLETE marker; nothing reopened |

## 4. Mapping: Phase A A-01..A-20 in the durable runner

| A | Classification | How it runs |
|---|---|---|
| A-01 | required | Provenance: import origin in this tree, source-manifest hashes, PostgreSQL 17, Redis, owner-fence port is the labelled ASSUMED_CONTRACT fixture |
| A-03..A-16 | required | Same scenarios as the Phase A runner on the SQL adapter. Each harness uses a fresh database cloned from a migrated template and its own RQ queue. Owner decisions are fixture rows; artifacts are lineage rows; audit/quarantine go to fixture sinks. Assertions read back from SQL, not fake internals |
| A-17 | required | Denied capabilities (missing, forged, other job, other key) plus B-10c end to end: dispatch → real RQ → RedactingSimpleWorker → completion. The token is absent from all SQL rows, sinks and log records |
| A-17-http | optional | CMD-44 fixture app over the SQL-backed service. NOT_RUN if FastAPI is unavailable; a FAIL still fails the run |
| A-02, A-19, A-20 | contract_only (NOT_APPLICABLE) | No storage meaning. They stay with the Phase A fixture runner, whose report B-11 consumes |
| A-18 | deferred | Durable ProviderCopyLifecycle belongs to BE2-14; the Phase A fake proof is the only one (B-12) |

**Runner rules.**
- Exit 1 if anything fails. Exit 2 if no item fails but a required item is NOT_RUN: a missing
  service, a missing JUnit or report, or a skipped mapped test.
- Nothing falls back to fakes, and a passing JUnit alone cannot make the run PASS (B-10 needs the
  durable scenarios).
- The report records the source manifest hash, the inputs' hashes, tool and server versions, and
  reasons for every NOT_RUN, NOT_APPLICABLE, DEFERRED and HANDOFF.
- It never prints a key, token or password.

## 5. Checks run (direct local, Windows, root venv; imports from this worktree's backend/src)

| Check | Result |
|---|---|
| Import origin | `…/.worktrees/be2-01-ai-job-foundation/backend/src/sketch2life/__init__.py` |
| B2–B6 pytest (integration ai_jobs + B3/B4/B5/B6 unit) | 103 passed, 99 skipped. The 99 are PostgreSQL/Redis cases, including the 3 new restart tests: **NOT_RUN** |
| B6 unit (runner logic) | 6 passed |
| Phase A suites | 223 passed, 1 skipped (Pillow; Studio has it) |
| Phase A fixture runner | exit 0, 20 PASS / 215 checks, d17f58a3 unchanged |
| Durable runner, no services | exit **2**: all required items NOT_RUN, A-18 DEFERRED, A-02/A-19/A-20 NOT_APPLICABLE, B-12 HANDOFF, no FAIL |
| Durable runner with the local JUnit (PG/Redis skipped) | exit **2**: every crash window NOT_RUN because skips never count as PASS |
| ruff (B6 files) / mypy src (18) / mypy tests + runner (20) | PASS |
| validate_harness / repository_security / architecture / skeleton; `git diff --check` | exit 0 / clean |

`ruff` over the whole B2–B6 scope reports 4 import-order (I001) findings. They are in fix03 files
whose hashes match the closed manifest, so they predate B6. They were left unchanged to keep the
B6 delta additive.

**NOT_RUN locally:** every PostgreSQL/Redis test and every durable runner scenario, because no
local services exist and none were installed. Studio is the runtime.

## 6. Package (ignored, local/b6-studio-package-20261016/)

| Item | SHA-256 |
|---|---|
| b6_previous.sha256 (= fix03 manifest) | 3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670 |
| b6_delta.patch (3 new files, additive) | f34d8b1a4bc8145c7e21b5dd661229e82daefe839e2636a7b51e2d81feb83f63 |
| b6_source.sha256 (46-file union manifest) | 3940e529e673f80f525591bb39bf3b2a99d892e27225f05c5b984ff7e2dc43ea |
| run_b6_on_studio.sh | aa9cc843bd7f316eda2ccf3d46010164aa8bbd5ac1ee3346b5016b33856e0696 |
| be2-b6-studio-20261016.zip | 5c2e4641ef5352370fab14089ee4037de4ced180d535aeb541d918b339f804bf |

- **Runner** (remote folder `be2-b6-package`). It accepts exactly two source states and refuses
  any other source untouched:
  - fix03 `3930046b`, where the delta is applied;
  - the B6 manifest, as a verify-only retry.
- **What it runs**, in order:
  1. B2–B6 pytest with a JUnit file;
  2. Phase A with a JUnit file;
  3. the fixture runner report;
  4. the durable runner, given the manifest, both JUnits and the fixture report.
  - Every suite, tee and outer exit is kept, and any skip fails the run.
  - The summary prints the restart and B6 unit lines, every A/W/B row, both runners' summaries
    and the hashes of the reports.
- **Builder self-check:** all PASS.
  - fix03 3930046b is rebuilt; previous plus delta equals the 46-file manifest.
  - The delta is additive only; a second apply is refused; the worktree reverse check exits 0.
  - ZIP members are byte-identical, and the 60 files of the older packages are unchanged.
- **Host simulation:** 9/9 PASS, with real scratch Git and a Docker stub.
  - Apply and verify-only retry pass.
  - Docker failure gives 125 and FAIL, then the retry passes.
  - Foreign tracked or untracked file, known-file edit, tampered delta and the unrun fix02 state
    are each refused before Docker.
  - The inner script passes `bash -n`. This is not runtime proof.

Expected Studio result (counts not preset):
- B2–B6 pytest: everything passed, 0 skipped;
- Phase A: 224 / 0 skipped;
- fixture runner: exit 0;
- **durable runner: exit 0**, with every required A/W/B item PASS, A-18 DEFERRED, A-02/A-19/A-20
  NOT_APPLICABLE and B-12 HANDOFF;
- `RUNNER_RESULT=PASS`.

## 7. Limits (kept, not hidden)

- OwnerFence, the audit sink and the artifact sink are **ASSUMED_CONTRACT** component fixtures.
  B-12 lists the real adapters and their owners.
- Fake provider only. W07 has no durable claim journal and no exactly-once provider execution
  (plan §7.1).
- The durable runner's PASS is component conformance on synthetic data. It is not live router,
  provider, production policy or deployment proof.

## 8. Next

1. Codex reviews the B6 code and package.
2. The user runs it on Studio per local/claude/prompts/B6_STUDIO_RUN_20261016.md. The result is
   recorded as USER_REPORTED_REMOTE.
3. A focused B6/BE2-01 Phase B closure review follows. Per decision 116, review and integration
   into dev come after the card's closure. Not all 14 cards are closed.

No staging, commit, push, deploy, install or service change was made, and no approval was
written.

## 9. Studio run 1 and B6-fix01 (2026-10-16)

### 9.1 Run 1 — USER_REPORTED_REMOTE, FAIL

The user ran package b6 on Studio `sketch2life-backend-test` and pasted the summary (kept
verbatim in ignored local/b6-fix01-20261016/studio_b6_run1_user_report.txt).
- run_utc 2026-10-15T18:19:36Z (2026-10-16 01:19:36 Asia/Saigon); source_state b5fix03_snapshot;
  manifest 3940e529, 46 files verified; Python 3.12.15, SQLAlchemy 2.1.4, Alembic 1.20.0, psycopg
  3.3.6, pytest 8.4.2, redis-py 6.4.0, RQ 2.12.0, Redis server 8.10.2.
- B2–B6 pytest: 201 passed / **1 failed** / 0 skipped. Phase A: 224 passed / 0 skipped. Fixture
  runner: 20 PASS / 215 checks, d17f58a3.
- Durable runner: exit 1. A-01, A-03..A-17 PASS (127 checks, 0 failed); A-17-http PASS; A-18
  DEFERRED; A-02/A-19/A-20 NOT_APPLICABLE; W01, W03–W07, W09–W12 PASS; B-02..B-05, B-07..B-11
  PASS; B-12 HANDOFF. **FAIL: W02, W08, B-01, B-06**, and the required items had no NOT_RUN.
- outer_runner_exit=1, RUNNER_RESULT=FAIL. Report hashes as reported: durable-conformance.json
  f507161e…, junit-b2-b6.xml 397e150a…, junit-phase-a.xml c8d9d6e2…, runner-report.json cf8a57ee….
- The runner did what it was designed to do: a failed mapped test made the items FAIL. It did not
  fall back or report PASS.

### 9.2 B6-RT01 — cause

`test_kill_after_commit_keeps_rows_then_restart_publishes_and_delivers` failed at line 156 with
psycopg `ProgrammingError: cannot adapt type 'Attempt'`. The crash child (line 136) piped
`"attempt": attempt`, the domain object, and the parent passed it to
`get_completion_receipt(job_id, attempt_id)`.
- Every assertion before line 156 passed: child exit 23, the checksum of every ai_jobs row
  identical after restart, and the job blocked_unsafe at revision ≥ 3.
- The receipt, publication and delivery assertions after it were never reached. W02, W08, B-01 and
  B-06 all map to this test, which explains all four FAIL rows.
- This is a test defect, not a product or runner defect. Locally the test is skipped without
  PostgreSQL, so it was NOT_RUN before Studio.
- Independently, Codex's ignored local review folder (local/b6-codex-review-20261016/restart/)
  has a no-service probe that reproduces the same adaptation error at lines 136/156.

### 9.3 Fix (one line)

Line 136 now sends `"attempt": attempt.attempt_id`. Lines 142–173 were re-reviewed statically:
- receipt id and fingerprint;
- one republished create;
- pending audit/quarantine rows;
- delivery count;
- the quarantine reason;
- the second delivery returning 0.

No other file changed.

Local checks after the fix:
- ruff 0 and mypy 0 (3 B6 files);
- B2–B6 103 passed / 99 PG-Redis skipped (NOT_RUN, not PASS);
- the four validators 0.

### 9.4 Package b6fix01 (ignored, local/b6fix01-studio-package-20261016/)

| Item | SHA-256 |
|---|---|
| b6fix01_previous.sha256 (= b6 manifest, the Studio state now) | 3940e529e673f80f525591bb39bf3b2a99d892e27225f05c5b984ff7e2dc43ea |
| b6fix01_delta.patch (1 modified file, 1 line) | 11e238c782f9e08d257dbbfcb74a1bfe99553e2021ea7de978a6dc707feff3b2 |
| b6fix01_source.sha256 (46 files) | 90724453b77b0cbf3a5843f1e78165a27155a8f76eb832ca0324e6a753a9dfec |
| run_b6fix01_on_studio.sh | 55695aeffb626155ddb581ae639277a8c17257e27f3987f7710e51caabab3683 |
| be2-b6-fix01-studio-20261016.zip | e813a48b0751d5f17742935df6d9a6b6b2d2d6315061275a9cbc1265335a6941 |

- **Runner.** It is the b6 runner with new names and pins only; the test commands and the durable
  runner invocation are unchanged. Remote folder: `be2-b6-fix01-package`. It accepts exactly two
  states and refuses any other source untouched:
  - the B6 snapshot 3940e529, where the delta is applied;
  - the fixed manifest, as a verify-only retry.
- **Builder self-check.** All PASS:
  - the B6 snapshot is rebuilt as 43 fix03 files plus the shipped b6 delta, and all 46 hashes
    equal 3940e529;
  - previous plus delta equals 90724453;
  - a second apply is refused, and the worktree reverse check exits 0;
  - ZIP members are byte-identical, and the 66 files of the older packages are unchanged.
- **Host simulation.** 9/9 PASS with real scratch Git and a Docker stub:
  - B6 snapshot to fix01;
  - verify-only retry;
  - Docker failure (125, FAIL), then the retry passes;
  - foreign tracked or untracked file, known-file edit, tampered delta, and a Studio still on fix03
    (B6 never applied) are each refused before Docker.

  This is not runtime proof.

Expected Studio result (counts not preset):
- every pytest test passed, with 0 skipped;
- Phase A 224 / 0 skipped;
- the fixture runner exits 0;
- **the durable runner exits 0**, with W01..W12 and B-01..B-11 PASS and B-12 HANDOFF;
- `RUNNER_RESULT=PASS`.

### 9.5 Next

1. Codex reviews the fix and package b6fix01.
2. The user runs it per local/claude/prompts/B6_FIX01_STUDIO_RUN_20261016.md. The result is
   recorded as USER_REPORTED_REMOTE.
3. A focused B6/BE2-01 Phase B closure review follows.

No staging, commit, push, deploy, install or service change was made, and no approval was
written.

## 10. Pre-run review of B6-fix01 — AUTHOR SELF-REVIEW (2026-10-16)

Codex ran out of tokens. The user directed Claude to do this step ("codex hết token r phần này bạn làm lun đi xong tôi đi ngủ"). Claude wrote the
fix, so **this is not an independent review**. It authorizes only the Studio run of b6fix01.

### 10.1 Package audit — PASS

Ignored receipts: local/b6fix01-review-20261016/package_audit.py and .json. The audit takes a path
different from the builder:
- **Studio's bytes.** Studio's test file was recovered from the shipped b6_delta.patch, which holds
  the bytes Studio received in run 1. It hashes to the 3940e529 entry. The fixed file differs from
  it only at line 136: `"attempt": attempt,` → `"attempt": attempt.attempt_id,`.
- **Both directions.** In scratch, the 46 fixed files reverse-patched give exactly 3940e529, and
  forward-patched give 90724453. A second apply is refused.
- **Runner.** After name and pin normalisation, the runner differs from the b6 runner in exactly
  10 lines: the two accepted state labels and their refusal messages. The test commands, the
  skip and exit guards and the durable runner call are identical. Outer and inner scripts pass
  `bash -n`.
- **ZIP.** The 4 members are byte-identical, there are no path tricks, and no secret markers were
  found. Nothing is staged.

### 10.2 Static trace of lines 142–173 (never executed on PostgreSQL) — no defect found

- **Line 156.** `SqlAiJobUnitOfWork.get_completion_receipt(job_id, attempt_id)` selects by two
  strings. The stored receipt is the same CompletionReceipt that accept_completion returned
  (`put_completion_receipt` in the same transaction), so its receipt_id and fingerprint match.
- **Line 161.** `dispatch_outbox` claims both pending dispatch rows (claim_limit 50; the clock is
  equal to available_at, and the query uses `<=`).
  - The first job is blocked_unsafe, so `_dispatchable` is false and its row is disposed.
  - The second job is queued and its request is seeded eligible. No re-seed happens on rig
    rebuild, so the row is published with an HMAC capability and acknowledged.
  - The method returns enqueued = 1.
- **Lines 164–167.** `_deliver_now` never marks delivery, so every committed audit and quarantine
  intent is still pending. `pending_side_effects_count` uses the same filter as the test (kinds
  audit/quarantine, delivered_at NULL). On restart, both sinks are the persistent fixture sinks
  and are healthy, so marked = count.
- **Lines 168–173.**
  - `FixtureArtifacts.quarantine` writes reason `UNSAFE_CONTENT` (service line 986) and one
    quarantine_applied row with the stored event id.
  - `OwnerFixture.read` returns `(payload, fence)`.
  - The second delivery finds 0 pending.

### 10.3 No-service probe — PASS

Ignored receipts: local/b6fix01-review-20261016/restart_flow_probe.py and .json.
- **A. Driver adaptation.** The exact receipt query was compiled for psycopg and each bound value
  dumped. The fixed str payload adapts. The run-1 Attempt payload reproduces "cannot adapt type
  'Attempt' …".
- **B. Same service code on the in-memory store, fake ports.** The probe ran the child scenario
  (two creates, a direct start, an unsafe completion with both sinks down), then a restart with
  healthy sinks. Results:
  - blocked_unsafe and the receipt matches;
  - dispatch_outbox = 1, and the second job is enqueued;
  - pending kinds are {audit, quarantine}, 4 rows (1 quarantine);
  - deliver = 4, the quarantine reason is UNSAFE_CONTENT and the applied ids equal the pending
    ids;
  - the second deliver = 0.
- This is service-logic evidence only. It is not SQL or PostgreSQL proof.

### 10.4 Verdict and limits

**PASS for the Studio run** (author self-review). No finding blocks the run. Limits:
1. **Not independent.** The B6/Phase B closure review must be independent of the author: Codex,
   or a genuinely separate reviewer session.
2. **Still unproven on PostgreSQL.** Lines 157–173 have never run there. Only the b6fix01 Studio
   run proves them.
3. **Codex's B6 review record is inconsistent.**
   local/b6-codex-review-20261016/package/review_summary.json lists `actionable_findings: []`,
   while its restart probe (restart/probe_restart_payload.json) reproduced B6-RT01. The closure
   review must reconcile this. It is not treated here as a Codex PASS of B6.

## 11. B6-fix01 Studio run — USER_REPORTED_REMOTE, PASS (2026-10-16)

The user ran package b6fix01 and pasted the output. It is kept in ignored
local/b6-fix01-20261016/studio_b6fix01_run_user_report.txt; the summary block's repeat of the
A/W/B rows is elided there and marked.

- **Source.** run_utc 2026-10-15T18:49:30Z (2026-10-16 01:49:30 Asia/Saigon); source_state
  b6_snapshot.
  - previous 3940e529 → delta 11e238c7 → manifest 90724453, 46 files verified before each suite;
  - the toolchain is the same as run 1 (Python 3.12.15, SQLAlchemy 2.1.4, Alembic 1.20.0, psycopg
    3.3.6, pytest 8.4.2, redis-py 6.4.0, RQ 2.12.0, Redis server 8.10.2);
  - Alembic heads are be1_core and ai_jobs.
- **Suites.**
  - B2–B6 pytest: **202 passed / 0 failed / 0 skipped**, including all three
    test_restart_recovery tests and the six test_ai_job_b6_conformance tests;
  - Phase A: **224 passed / 0 skipped**;
  - fixture runner: 20 PASS / 215 checks, results d17f58a3 unchanged, with optional HTTP NOT_RUN 1.
- **Durable runner: exit 0.**
  - 45 items: PASS 40, DEFERRED 1, HANDOFF 1, NOT_APPLICABLE 3;
  - **required 39/39 PASS**, required NOT_RUN none, FAIL none, 127 checks / 0 failed;
  - A-01 and A-03..A-17 PASS, and the optional A-17-http PASS;
  - W01..W12 PASS and B-01..B-11 PASS;
  - A-18 DEFERRED (BE2-14), A-02/A-19/A-20 NOT_APPLICABLE, **B-12 HANDOFF** (not PASS).
- **Exits.** b2_b6, phase_a, fixture and durable runner (each with its log) all 0; skips 0;
  outer_runner_exit 0; **RUNNER_RESULT=PASS**; studio_command_exit 0.
- **Report hashes, as reported:**
  - durable-conformance.json afe8b51261a61a7923be2d7c83c1e0a066dceef82a034b30cdc38f912071e2c1;
  - junit-b2-b6.xml 205d2017e123fd2a782c1b783dbcb285f2783eed793a84bcc8c4a93fe8b8d4a6;
  - junit-phase-a.xml 1547705be1785de70848d70347c5b7b4515bf13d5b49c3f61f1fbb597186e130;
  - runner-report.json cf8a57ee021fa0a8a0a47ce92d641d8add36934cfe7e679a64b2382170b1e87c (byte-identical
    to run 1, as expected of the deterministic fixture runner).
- **Local and Studio source match.** The local worktree matches 90724453.

### 11.1 Timing, Studio state and observations

- **Timing.** The run started at 01:49:30 (Studio clock), while the §10 author self-review was
  finishing. The package audit had passed at 01:46. The restart probe ran at 01:49:38 and the
  review record at about 01:50:46 (Windows clock; the cross-machine comparison is approximate).
  The run used exactly the reviewed bytes: every pin matched, as printed.
- **Studio state.** The user stopped the Studio after the run (to avoid charges), so its Docker services, network and venv volume may be gone; any later runtime starts with an inventory and recreates nothing without the owner-approved procedure.
- **O-1 (non-blocking).** `backend/pyproject.toml` has `addopts = "-q"`, which cancels the runner's
  `-v`. So the summary's `test_(restart_recovery|ai_job_b6_conformance).py::` lines are empty in
  both runs. The per-test outcomes are in junit-b2-b6.xml, and the durable runner resolved
  W/B items from that JUnit. A later summary could pass `-o addopts=` or read the JUnit instead.
  No change is made now.

### 11.2 What this does and does not show

It shows component conformance of the B1–B6 durable foundation on the synthetic Studio:
PostgreSQL 17 SQL adapter, Redis 8/RQ, HMAC capability and the ASSUMED_CONTRACT owner fixture.

It does not prove real BE1, child-data, consent or artifact owner integration, a live router or
provider, production policy, or deployment. All of those are B-12 HANDOFF
(notes/PHASE_B_B6_HANDOFF_20261016.md).

### 11.3 Next

1. An independent B6/Phase B closure review: Codex when available, or a genuinely separate
   reviewer session. It must:
   - check §9–§11 and the code;
   - reconcile Codex's B6 review record (summary with no findings, probe that reproduced RT01);
   - decide whether B6 closes.
2. Then the BE2-01 card review and integration into dev per decision 116. The publication plan
   (COMMIT_PLAN_V2 proposal) is still awaiting the user.

B6 is not closed, BE2-01 is IN_PROGRESS, and no staging, commit, push or deploy was done.

## 12. B6-CR01 hardening (2026-10-16) — FIXED_PENDING_RUNTIME_REVIEW

The independent closure review found B6-CR01 (M): the durable runner on its own was not a
self-sufficient gate. Person 2 chose to harden it (DECISIONS 122). Only the runner and its offline
tests changed.

### 12.1 What the runner now requires (runner_version b6.2)

| Gate | Rule |
|---|---|
| G-01 B2-B6 JUnit | All cases are aggregated against the case ids pytest collects from SUITE_B2_B6 in the running tree (17 files, parameter ids included). A failed or errored case → FAIL. A case outside the inventory → FAIL. A missing or skipped inventory test → NOT_RUN. |
| G-02 Phase A JUnit | The same rule against SUITE_PHASE_A (6 files). |
| G-03 fixture report | Must be readable, list exactly A-01..A-20 all PASS, have summary PASS 20, checks > 0, 0 failed, and a 64-hex results digest. |
| G-04 source manifest | `--manifest-sha256` is pinned and equal. Every line has the form `<sha256>  <relative path>`, with no duplicates and no traversal. The manifest is non-empty, every file matches its hash, and every Phase B surface file present in the tree is listed. |

- **W/B patterns.** Each must also cover every inventory test it names. A wildcard therefore no
  longer passes on a subset.
- **A-01** checks that G-04 passed. **B-11** uses G-02 and G-03.
- **Exit codes** are unchanged: 1 = any FAIL, 2 = required NOT_RUN.
- **Inventory.** It is `pytest --collect-only` over the suite files of the running tree, with
  parameter ids. Locally it collects 213 B2-B6 cases and 224 Phase A cases. A collection error
  or a suite file with no case gives an empty inventory, which FAILs the gate.

### 12.2 Regressions (test_ai_job_b6_conformance.py: 17 tests, 11 new)

Each test feeds complete passing evidence and changes one part:
- an unmapped test failing → G-01 FAIL, exit 1 (probe P1);
- three dispatch-recovery tests dropped, or skipped → G-01 and B-04 NOT_RUN, exit 2, no FAIL (P2);
- one parameter variant (`[120]`) missing while its sibling `[81]` ran → G-01/B-11 NOT_RUN;
- a foreign case → FAIL;
- a Phase A JUnit with one arbitrary test → G-02/B-11 FAIL; one real test only → NOT_RUN (P4);
- a fixture report with 0 checks, 19 items or no results → G-03/B-11 FAIL (P3);
- the manifest gate:
  - absent → NOT_RUN;
  - unpinned, wrong pin, empty, a surface file unlisted, tampered, or a malformed line → FAIL
    (P7);
  - correct → PASS;
- an empty, unpinned manifest through main() → exit 1.

### 12.3 Local checks (DIRECT_LOCAL, Windows; PostgreSQL/Redis NOT_RUN)

- ruff 0 and mypy 0 on both files. Repository style does not use `ruff format`.
- B6 unit: 17 passed.
- B2-B6: 114 passed / 99 skipped (NOT_RUN).
- Phase A: 223 passed / 1 Pillow skip.
- Fixture: 20 PASS / 215, d17f58a3.
- The hardened runner on the real local evidence with the package manifest and pin exits 2:
  - G-03 PASS and G-04 PASS;
  - G-01 is NOT_RUN (99 skips) and G-02 is NOT_RUN (1 skip);
  - the scenarios are NOT_RUN;
  - no FAIL.
- Validators 0; `diff --check` clean; nothing staged.

### 12.4 Package b6cr01 (ignored, local/b6cr01-studio-package-20261016/)

| Item | SHA-256 |
|---|---|
| b6cr01_previous.sha256 (= b6fix01 manifest, the last Studio source) | 90724453b77b0cbf3a5843f1e78165a27155a8f76eb832ca0324e6a753a9dfec |
| b6cr01_delta.patch (runner + its unit tests) | 5e1f6012f2c7209e7c11f755df65c7fccde2ce89b881da2845fe7b0d4907b898 |
| b6cr01_source.sha256 (46 files) | a75841e03a793ed436aa4714eb41a3ba57294d6884fa2b161085d40e2b162a95 |
| run_b6cr01_on_studio.sh | 5f8858d71a6152f62119890b2da187e1d68f2fb914b36d378e3256e145a637cf |
| be2-b6-cr01-studio-20261016.zip | d0b9f27ba5e692c80457dc233a185440692b33d6c6323dd174a9e409f4f70018 |

- **Runner.** It differs from the b6fix01 runner only in names, pins and state labels, plus:
  - `--manifest-sha256 "$BE2_MANIFEST_SHA256"` on the durable call;
  - G- rows in the summary.
- **Accepted states.** 90724453 (apply) or a75841e0 (verify-only retry).
- **Self-check PASS.**
  - The previous snapshot is rebuilt as fix03 + b6 + b6fix01 = 90724453.
  - Previous plus delta equals a75841e0, and a second apply is refused.
  - The 72 older package files are unchanged.
- **Host simulation 9/9 PASS.** It includes refusal of the B6 3940e529 state and of the other
  tamper cases.
- **Studio state.** The Studio was stopped after the b6fix01 run. Run the reviewed
  `rebuild_be2_env.sh` first (local copy sha 28950e63; it reuses the private password and venv
  volume and deletes nothing).

**Expected Studio result** (counts not preset):
- G-01..G-04 PASS;
- every pytest test passed with 0 skipped;
- Phase A 0 skipped;
- the durable runner exits 0 with every required A/G/W/B item PASS and B-12 HANDOFF;
- `RUNNER_RESULT=PASS`.

After the run, the fix must be reviewed before CR01 closes. No staging, commit, push or merge was
done.

### 12.5 Codex pre-commit review P2 and its fix (2026-10-16)

While the hardening was in progress, a Codex review wrote
notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md. Its verdict was NEEDS_REVISION, with
one P2 on runner bytes 87f0961f.
- **The problem.** The first inventory compared function names. One executed parameter variant
  therefore stood for all of them: dropping
  `test_contract_valid_opaque_ids_round_trip_all_five_columns[120]` while `[81]` ran still gave
  G-01 PASS.
- **Reproduced.** Claude reproduced it before fixing: the new regression failed on the unfixed
  runner, whose inventory had no `[120]` at all.
- **Fix.** The inventory now uses pytest-collected case ids, parameter ids included. G-01/G-02 and
  the W/B pattern coverage compare full ids. The regression now passes (17/17).
- **Package.** It was rebuilt after the fix; §12.4 shows the current hashes. Codex's note covered
  an earlier byte state and has not re-reviewed these bytes.

### 12.6 CR01 revision r2 (2026-10-16) — PENDING_CODEX_REVIEW, runtime NOT_RUN

**Finding.** `notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md` (runner 87f0961f): G-01 compared function names, so dropping
`test_contract_valid_opaque_ids_round_trip_all_five_columns[120]` while `[81]` ran still passed.
The current source was compared with the finding first, without restoring old bytes into the
tree.
- The §12.5 collected-id change already covered the core of the finding.
- r2 adds identity normalisation, all-or-nothing collection and the remaining regressions.

**Fix.** case identities are the full pytest ids (file path relative to backend/, class parts, parameter id) taken from `pytest --collect-only` of the running tree and normalised identically from JUnit; collection is all-or-nothing (exit code, pytest's own total, no case outside the suite files, every file collected). The W/B pattern coverage uses the same identities.

**Regressions** (test_ai_job_b6_conformance.py now has 21 tests):
- B2-B6 `[120]` missing while `[81]` ran → G-01 NOT_RUN;
- a real Phase A variant missing (`test_r04a_non_string_failure_code_is_non_authoritative[set]`) →
  G-02/B-11 NOT_RUN;
- a complete inventory → G-01/G-02 PASS;
- a failure plus a missing case → G-01 FAIL, exit 1;
- nodeid/JUnit identities agree and keep variants;
- a collection error → empty inventory → FAIL.

**Before/after proof** (ignored: local/b6-cr01r2-20261016/probe_before_after.py and .json). Each
runner got a scratch copy of backend/ and the feature src/fixtures; the real source was never
swapped. The synthetic JUnit came from the real collection (217 B2-B6, 224 Phase A cases). There
were no services, so exit 2 means no FAIL but the durable scenarios were NOT_RUN.

| Input | 87f0961f G-01 / G-02 / exit | current G-01 / G-02 / exit |
|---|---|---|
| complete | PASS / PASS / 2 | PASS / PASS / 2 |
| B2-B6 `[120]` missing | **PASS** / PASS / 2 | **NOT_RUN** / PASS / 2 |
| Phase A variant missing | PASS / **PASS** / 2 | PASS / **NOT_RUN** / 2 |
| failure + `[120]` missing | FAIL / PASS / 1 | FAIL / PASS / 1 |

Scratch fidelity note: a first attempt without the feature fixtures collected only 157 Phase A
cases, because the contract tests parametrize from them. The current runner reported this
mismatch as FAIL rather than passing a partial inventory. The probe then copied the fixtures.

**Local checks.** Local: ruff/mypy 0; B6 unit 21 passed; B2-B6 118 passed / 99 PG-Redis skipped (NOT_RUN); Phase A 223 / 1 Pillow skip; fixture d17f58a3; collected identities equal the real JUnit identities (217/217 B2-B6, 224/224 Phase A); runner on real local evidence exit 2 with G-03/G-04 PASS and no FAIL; validators 0.

**Package b6cr01r2** (ignored, local/b6cr01r2-studio-package-20261016/):

| Item | SHA-256 |
|---|---|
| b6cr01r2_previous.sha256 (= b6fix01, the last Studio source) | 90724453b77b0cbf3a5843f1e78165a27155a8f76eb832ca0324e6a753a9dfec |
| b6cr01r2_delta.patch (runner + its unit tests) | 9d9146c6c165cce698562321457d5819c30147d4cfb409a149890ad688395259 |
| b6cr01r2_source.sha256 (46 files) | cb527d7f1739480a6312a0c497f65e1b6aca7ef5acdad28ce93f082e88cc1cca |
| run_b6cr01r2_on_studio.sh | d027d05c8067d9827ceaa05ba852422c25abf089fa50fbbee2a4bb1b1f19bcd9 |
| be2-b6-cr01r2-studio-20261016.zip | 3a9d6ef263572f12083b7cbc8f606e0f7c678d4b3180586519d7b634b474b97c |

- **Runner.** It equals the b6cr01 runner except for names and pins. It checks the source and
  manifest, applies only to 90724453, gives a verify-only retry on cb527d7f, and passes every exit
  code through.
- **Self-check PASS.** All 78 older package files are unchanged, including b6cr01 (d0b9f27b).
- **Host simulation 10/10.** A new case refuses the superseded, never-run b6cr01 state.
- **Earlier build overwritten.** The first b6cr01 build (575aa8f4) was overwritten in place by its
  rebuild in the previous turn. It was never run.

**Next.** Codex reviews the r2 fix and package. Then the Studio run per
local/claude/prompts/B6_CR01R2_STUDIO_RUN_20261016.md, then a review before CR01 closes. r2 has
no runtime PASS.


### 12.7 Codex R2 code/package pre-run review —2026-10-16

**Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** on 46-file manifest cb527d7f and ZIP 3a9d6ef2. The reviewed source is runner d42d697c / B6 unit b1d3bced. Independent local21 B6 tests PASS; heldout missing B2-B6/Phase A parameter variants are NOT_RUN; unmapped failure with a missing variant yields FAIL/exit1; collection errors fail closed. R2 package audit PASS: 46/46 current hashes, ZIP4 members, two-file delta from90724453, scratch apply/reverse, shell syntax, source-state pins and exit/skip guards. No actionable finding remains in this focused pre-run scope. Studio runtime is NOT_RUN; CR01 remains FIXED_PENDING_RUNTIME_REVIEW, not closed. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md, latest R2 addendum. Next: run only b6cr01r2 on the approved synthetic Studio, review the source-bound results, then refresh publication documents and dry run. BE2-01 IN_PROGRESS, B-12 HANDOFF; approvals and source/packages unchanged by review. No staging/commit/push/merge/deploy.

### 12.8 Local checkpoint decision —2026-10-16

Person 2 allowed local checkpoint commits of the reviewed state before the r2 Studio run, because the
Lightning Studio is not usable (DECISIONS 124). The checkpoint is **not** acceptance:
- runtime r2 NOT_RUN and B6-CR01 FIXED_PENDING_RUNTIME_REVIEW; source and package bytes are unchanged
  (runner d42d697c, B6 unit b1d3bced, manifest cb527d7f 46/46, ZIP 3a9d6ef2, re-verified before the commits);
- the last Studio runtime remains B6-fix01 / 90724453 (USER_REPORTED_REMOTE), not r2;
- three source commits reproduce Studio snapshots that had failing tests, corrected by the next commit;
  not every commit is test-green;
- the Studio keeps base 993a26c and source 90724453 and runs the existing b6cr01r2 package later, with no
  pull; its results are recorded by a follow-up commit, not by amending the checkpoint chain.
