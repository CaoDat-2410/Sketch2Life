# Phase B B5 implementation evidence — 2026-10-15

> Current independent review: NEEDS_REVISION, two P2 findings B5-R01/R02 OPEN.
> See PHASE_B_B5_CODEX_REVIEW_20261015.md; do not run the current B5 ZIP as the next acceptance step.
> Executor implementation/package checks below remain attributed historical evidence.

- Status: **B5_CODE_COMPLETE — PENDING_CODEX_REVIEW**. No PostgreSQL/Redis runtime result exists
  for B5 yet: B5 is not closed, B6 NOT_STARTED, parent BE2-01 IN_PROGRESS (14 cards, WIP 1,
  full-card DONE 0).
- Executor: Claude (backend). Authority: the existing Phase B plan rev3 B1–B6 approval
  (approvals/PHASE_B_TASK_APPROVAL.md, unchanged) and B5 scope Δ8/Δ9/Δ10/Δ12/Δ14/Δ15. The user
  confirmed the B5 request in chat. No new card or approval was written.
- Base: 993a26c plus the closed B4 snapshot (32-file manifest f1c6834f), identical locally and on
  the last reported Studio run.
- Metrics: metrics/PHASE_B_B5_IMPLEMENTATION_EVIDENCE_20261015.json. Ignored local receipts are in
  local/b5-local-checks-20261015/ and the package in local/b5-studio-package-20261015/.

## A. Δ8/Δ14 — attempt-bound capability and real worker

- **`infrastructure/ai_jobs/worker_capability.py`** (new). Stateless HMAC-SHA256 tokens
  `wcap.v1.<key_id>.<claims>.<mac>`.
  - Claims `j` (job), `a` (attempt), `iat`, `exp` in epoch ms. Fixture TTL is 40 s
    (5 s start timeout + 30 s attempt timeout + 5 s slack, decision record §5.1; PROPOSED).
  - `verify(token)` returns a `VerifiedCapability(job_id, attempt_id, issued_at, expires_at,
    key_id)` or `None`. It authenticates before parsing the claims. It denies malformed,
    tampered, unknown-key, wrong-type and expired tokens; expiry is exclusive.
  - Several verification keys are accepted to allow rotation overlap. Key bytes never appear in
    `repr`, tokens, exceptions or logs. Provisioning and rotation stay with INTG-02.
- **Service `_require_worker(token, job_id, attempt_id)`.** Used by `start_attempt`,
  `report_progress` and `accept_completion` (with `claim.attempt_id`).
  - Both ids must match, and the service clock must be before `expires_at` (a second check that
    does not rely on the verifier).
  - There is no job-only fallback. Stored-receipt replay, including a raced one, needs a live
    token for exactly that attempt.
- **`infrastructure/ai_jobs/worker.py`** (new). `DispatchWorker.handle(envelope)` does a durable
  start, then reports a progress stage, runs the fake provider and submits the completion.
  - A duplicate or settled delivery never reaches the provider.
  - A provider exception produces no claim; the overdue sweep and policy retry recover the
    attempt. There is no claim journal and no exactly-once provider guarantee.
  - `CapabilityRedactionFilter` removes RQ's `arguments`/`kwargs` extras and scrubs
    capability-shaped strings from the message, args, exception text and stack before handlers
    run.
- **RQ (`rq_queue.py`).**
  - `receive_dispatch` is now the real entry point. RQ identity is unchanged (same dotted path,
    `description=message_id`, `result_ttl=0`, `failure_ttl=60`, no RQ retries). It never raises,
    so RQ's default failure handler, which logs `job.args`, is never reached.
  - `RedactingSimpleWorker` overrides `handle_exception` to log only the job id and exception
    type, and installs the filter on the `rq*` loggers.
- **Test coordinator** (tests/integration/ai_jobs/b5_support.py). One ephemeral HMAC key per test
  run is passed to spawned worker child processes only through the multiprocessing pipe: no
  file, environment variable or log. Child exit codes report a death before start or after the
  provider ran.

## B. Δ9/Δ15 — completion and incident atomicity, durable side effects

- **Ports.**
  - `AuditEvent.event_id`, which is deterministic.
  - `QuarantineIntent(event_id, organization_id, job_id, attempt_id, artifact_refs,
    reason_code)`, with `ArtifactPort.quarantine(intent)`.
  - New unit-of-work methods `add_quarantine_intent`, `side_effect_recorded`,
    `claim_side_effects` and `mark_side_effect`.
- **Job-changing completion** (accepted, stale, rejected unsafe/malformed, eligibility cancel).
  The job CAS, the authoritative receipt, the completion audit intent and the owned quarantine
  intents are written in one transaction, after the fence hold. Success is returned only after
  commit.
- **Guard verdicts that leave the job unchanged** commit an audit-only incident before
  answering. This covers `ATTEMPT_SUPERSEDED`, `JOB_TERMINAL`, `JOB_CANCELLED`, `INVALID_STATE`,
  `INPUT_MISMATCH`, `MALFORMED_CLAIM`, and `COMPLETION_CONFLICT` on direct and raced replay.
  - Committed-final verdicts also commit an owned quarantine intent.
  - The incident never takes the authoritative receipt slot, so a later valid claim still lands.
  - An incident commit failure returns `503 DEPENDENCY_UNAVAILABLE` (retryable), never the 409 or
    a receipt.
- **Identity.**
  - Audit: `sha256(kind, event_type, job, attempt, claim fingerprint, reason)`.
  - Quarantine: the same plus the sorted owned refs. It is computed once, inside the committing
    transaction and only from `_owned_refs`, so loser or rolled-back rounds produce none and
    foreign lineage is never included.
  - Neither depends on the receipt id, the clock or the token.
  - Create and cancel keep their B3 ids. Direct (non-outbox) audits get a revision-based id.
- **Dedup.** Each intent is skipped if its event id is already durable.
  - A concurrent identical incident loses on the unique key. The whole transaction rolls back,
    with no work in an aborted PostgreSQL transaction, and the next round finds the stored id.
  - A `UniqueConflict` of any other kind is re-raised, never swallowed.
- **Delivery.**
  - Right after commit the service delivers each intent once on a best-effort basis; this keeps
    the Phase A behaviour observable. Create and cancel now deliver their stored event instead of
    a second, id-less event.
  - `deliver_side_effects(owner)` leases undelivered audit/quarantine rows (SKIP LOCKED,
    generation+1), applies them outside SQL with the stored id, then marks them as the current
    holder. A failing sink releases the lease; a stale holder's mark or release is a no-op.
  - Side-effect delivery never uses `ack_dispatch` and never touches `dispatch_count`.
  - Sinks deduplicate by event id: `FakeAudit`, `FakeArtifacts`, and the component sinks
    `FixtureAuditSink` and `FixtureArtifacts.quarantine` (one owner transaction plus a dedup row
    in `owner_fence_fixture`). No BE1 storage was written.

## C. Δ10 — atomic cancellation notices

- `apply_cancellation_notice` runs in one transaction:
  1. `notice_seen`;
  2. `jobs_for_notice` locks every match `FOR UPDATE` in job-id order, with no limit or paging;
  3. each match is cancelled with a durable audit intent;
  4. `record_notice(notice, applied_count, now)` writes `COMPLETE`.
- The selection predicate is `notice_matches`: same organization, cancellable state, and the
  notice's session, job type or subject. It is shared by the fake and mirrored in SQL (JSONB `@>`
  for subjects).
- `notice_atomic_max = 100` (fixture only). Above it, `NOTICE_ATOMIC_LIMIT` (409, not retryable)
  is raised with nothing changed or recorded.
- A concurrent duplicate loses on the notice key, rolls back and then sees the notice recorded.
  An overlapping notice only gets the rows that are still open.
- The SQL `notice_seen`/`record_notice` stubs are replaced. The owner epoch and notice fixture
  stay ASSUMED_CONTRACT.

## D. Δ12 — compatibility

- **Fakes and harness.** The fakes implement every new port method. `FakeWorkerCapability` is
  attempt-bound with expiry. `h.capability(job_id, attempt_id=None)` and
  `SqlRig.capability(...)` issue for the active attempt. `FakeArtifacts.owner_quarantine` and
  `FixtureArtifacts.owner_quarantine` keep the owner-side test helpers.
- **Callers updated.** Only call sites changed: Phase A, B3 and B4 tests, the fixture runner A-11
  and the catalog's retry-attempt token.
- **One Phase A test tightened on purpose.** `test_progress_reports_keep_unknown_null_and_ignore_
  stale_attempts` now uses the stale attempt's own token and also asserts that the active
  attempt's token is refused for another attempt (403).
- **Phase A fixture runner.** 20 PASS / 215 checks, results digest **d17f58a3… unchanged**.
- **Not changed.** Schema/migration, RQ identity, B3 single-statement read, B4 generation ack,
  recovery and keyset paging, domain contracts, D1–D7, and the profile 5 s / 3 publishes /
  3×30 s / 40 s / 100.

## Acceptance mapping (component scope; runtime pending)

| Acceptance | Offline (fakes, direct local) | Real adapter (Studio, NOT_RUN locally) |
|---|---|---|
| B-05 one winner, identical replay, conflict never overwrites | test_ai_job_b5_effects replay/conflict | test_completion_recovery concurrent ×2 |
| B-05e / B-10c token scope, tamper, expiry; token only in the envelope; token-free SQL/logs | test_ai_job_b5_capability (12 HMAC/service + redaction + entry point) | test_capability: RQ worker end to end, RQ failure path, cross-attempt on SQL |
| B-06c committed incident survives restart; redelivery dedup; crash after sink effect before mark | effects: crash-before-delivery, crash-after-effect, stale holder | test_audit_durability restart redelivery, crash-after-effect, stale lease |
| B-06d no loser/rolled-back delivery; owned refs only | effects: rolled-back round + foreign ref | test_audit_durability rolled-back + foreign lineage |
| B-08a/b rollback leaves nothing partial; audit-only failure 503 | effects: 5 boundaries; 503 for superseded/malformed/conflict; dedup; unrelated conflict | test_completion_recovery 5 boundaries; test_audit_durability 503, repeat, concurrent conflict |
| B-09e–g notices | effects: 51 matches in 1 transaction, >100, duplicate, crash, concurrent duplicate, unrelated conflict | test_notice_coverage: 51 invisible until commit, 101, duplicate, concurrent duplicate/overlap, crash + redelivery, owner bump with withheld notice |
| B-04a / B-06b worker death and the provider/completion window | worker on fakes: start-before-provider, duplicate, provider crash → policy retry | test_capability: child dies before start → same attempt; duplicate receive; dies after provider → timeout → retry; test_completion_recovery: no same-claim recovery |

## Verification (direct local, Windows, root venv; PYTHONPATH/MYPYPATH pinned to this worktree)

| Check | Result |
|---|---|
| Phase A 6 suites | 223 passed, 1 skipped (live-app import needs Pillow, absent in the local environment) |
| B2–B5: integration ai_jobs + B3/B4/B5 unit | 89 passed, 94 skipped. The 94 are PostgreSQL/Redis cases (64 B2–B4 + 30 B5), **NOT_RUN, not PASS** |
| B5 unit tests | 49 (24 capability/worker/redaction + 25 completion/effects/notices), all passing |
| Fixture runner | exit 0, 20 PASS / 215 checks, digest d17f58a3…, optional HTTP NOT_RUN 1 |
| Mutation probe (scratch copy) | 10/10 removed guarantees each fail ≥ 1 B5 test (mutation_probe.json) |
| ruff check (B2–B5 sources/tests, runner) / mypy src (18 files) / mypy tests (20 files) | PASS |
| validate_harness / repository_security / architecture / skeleton | exit 0 |
| `git diff --check`; CR bytes in the 25 delta files | clean / 0 |

Notes:
- `mypy` on `test_ai_job_q00_followups.py` reports 2 errors at lines 136–137. Those lines are
  unchanged from HEAD, so this is pre-existing and not a B5 gate. The receipt is kept as
  `mypy_tests_with_q00_preexisting.txt`.
- `ruff format` drift predates B5 (see the B4-R01 note).
- PG/Redis tests were written and statically reviewed only. One setup-ordering bug was found and
  fixed in that review: the hook pausing concurrent completions now arms only after setup.

## Package (ignored, local/b5-studio-package-20261015/)

| Item | SHA-256 |
|---|---|
| b5_previous.sha256 (= closed B4 manifest) | f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4 |
| b5_delta.patch (25 files: 14 changed + 11 added paths) | 671a8617e8245b186dc58d83a80f5cf1f97c56cafe2db5ed5cde0833f67f271a |
| b5_source.sha256 (43-file union manifest, includes every new file) | c74920973da54ccc48bdb0996cb4db2a13dedf6366e2766dae9622a093fee143 |
| run_b5_on_studio.sh | e781341995d74954f55e30034d5d4a9e631b58507170c57e334b41a9734d8c25 |
| be2-b5-studio-20261015.zip (4 members) | 9475fe27457818a8890424a92eaf55115dc962fa002e960ae8072fa41a956a5b |

- **Runner.** It accepts exactly two source states and refuses any other source untouched:
  - the closed B4 snapshot f1c6834f, where the delta is applied;
  - the B5 manifest, as a verify-only retry.
  - It reverse-checks the delta, runs B2–B5, Phase A and the fixture runner, fails on any skip,
    prints a summary (B5 PG test lines and any FAILED/ERROR lines), and propagates the exit as
    `outer_runner_exit` / `RUNNER_RESULT`.
- **Builder self-check** (b5-local-checks-20261015/package_checks.json): all PASS.
  - The f1c6834f snapshot is rebuilt from base and six patches; the 11 added paths are at base.
  - Previous plus delta equals the 43-file manifest; a second apply is refused; the worktree
    reverse check exits 0.
  - No other packaged-area change exists, ZIP members are byte-identical, the 36 files of the
    six older packages are unchanged, and the real index was not touched.
- **Host simulation** (verify_runner_host.json): 8/8 PASS, using real scratch Git and a Docker
  stub.
  - Closed B4 → B5 apply and verify-only retry: exit 0.
  - Docker failure: 125 and FAIL, then the retry passes.
  - Foreign tracked or untracked file, known-file edit and tampered delta are each refused before
    Docker.
  - The inner script passes `bash -n`. The stub runs no tests, so this is not runtime proof.
- **Disclosure.** On Studio `test_ai_job_q00_followups.py` is at base, so its delta also carries
  the earlier owner-approved Q00 EOF fix (one trailing blank line removed) together with the B5
  `owner_quarantine` call change. The hash recorded in Q00_FOLLOWUPS_EOF_DISPOSITION_20261015.md is
  now the pre-B5 state.

Expected Studio result: **B2–B5 183 passed / 0 skipped** (the closed B4 104, plus 49 B5 unit and
30 B5 PostgreSQL/Redis tests), **Phase A 224 / 0 skipped**, fixture runner exit 0,
`RUNNER_RESULT=PASS`.

## Known limits (not hidden)

- Provider output that exists before an uncommitted completion is not recovered as the same
  claim. The attempt times out and policy retry may run the provider again. This is as planned.
- An oversized notice locks and reads all its matches before failing typed. Nothing changes.
- The deliberate RQ failure test leaves its synthetic token in that job's failed-registry data
  until the fixture deletes the job. The real entry point never raises.
- Direct post-commit delivery swallows sink errors on purpose; the leased pass owns durability.
- Not done: B6 conformance, crash matrix and Phase A on SQL; real owner fence (B-12); provider;
  live router; production key provisioning; durable ProviderCopyLifecycle.

## Next conditions

1. Codex reviews the B5 code and package before the user runs it.
2. The user runs `run_b5_on_studio.sh` on Studio. The result is recorded as USER_REPORTED_REMOTE.
3. A focused B5 closure review follows. B6 starts only after that.

No staging, commit, push, deploy, install or service rebuild was done. The package and logs contain
no secret, key, real token, media or child data.
