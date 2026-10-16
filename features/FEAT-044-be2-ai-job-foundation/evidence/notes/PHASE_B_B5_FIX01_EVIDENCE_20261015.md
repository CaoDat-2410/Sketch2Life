# Phase B B5 fix01 evidence (B5-R01/B5-R02) — 2026-10-15

- Status: **B5-R01/B5-R02 FIXED_PENDING_REVIEW**. Q01 stays B5_NEEDS_REVISION until Codex reviews
  this source and package, the user runs it on Studio, and a focused closure review passes. B5
  is not closed and B6 has NOT_STARTED.
- Executor: Claude. Authority: the existing Phase B plan rev3 B1–B6 approval, unchanged; the user
  asked for this fix in chat. Only the two findings of notes/PHASE_B_B5_CODEX_REVIEW_20261015.md
  are addressed. No other B5 scope was opened.
- Metrics: metrics/PHASE_B_B5_FIX01_EVIDENCE_20261015.json. Ignored receipts are in
  local/b5-fix01-20261015/ and the package in local/b5fix01-studio-package-20261015/.

## B5-R01 — a failing audit prefix no longer starves a healthy quarantine

**Fix.** One `deliver_side_effects` invocation is now a keyset traversal over every undelivered
side-effect row, the same pattern already reviewed for B4-R01:
- `claim_side_effects(..., after)` leases a page strictly after the last claimed row's
  `(created_at, message_id)` and returns each claim's `cursor`.
- A row whose sink fails is released, as before, and the traversal moves past it.
- `now` is fixed per invocation. A page shorter than the limit ends the traversal, and a page
  longer than the limit raises.

Guarantees and what was left alone:
- Every row is attempted at most once per invocation, so an all-failing backlog terminates.
  Released rows are retried by the next invocation.
- Unchanged: owner+generation fencing, stale-holder no-ops, stored event ids and sink dedup,
  payload/token safety, and dispatch bookkeeping (no `dispatch_count` change).
- No LIMIT increase, job scan, new queue, scheduler, schema or persisted marker.

**SQL/fake parity.** SQL adds a strict row-value predicate on the existing `ORDER BY created_at,
message_id`. The fake uses a constant time plus the zero-padded write sequence as its keyset.

**Before** (Codex probe on the c7492097 source; local copy in local/b5-fix01-20261015/before/):
- three passes return `[0,0,0]`;
- 150 audit calls and 0 healthy quarantine calls.

**After** (local/b5-fix01-20261015/after/; only the final asserts became recorded outcomes):
- passes `[1,0,0]`;
- the quarantine is delivered and marked once (1 application);
- 51 audit rows stay pending and are tried once per pass.

## B5-R02 — malformed capability representations are rejected and redacted

**Strict acceptance.** `verify` first full-matches the whole token:
`wcap.v1.<key_id [a-z0-9_]{1,32}>.<base64url body>.<base64url 43-char MAC>`. Decoding is
canonical, unpadded base64url only:
- characters outside the alphabet are rejected;
- `=` padding is rejected;
- a length ≡ 1 (mod 4) is rejected;
- non-canonical trailing bits are rejected, by a re-encode round-trip.

Unchanged: the MAC is still checked before the claims are parsed, and claim types, job/attempt
binding, the 40 s expiry, key rotation and receipt-replay semantics are all as before.

**Defensive redaction.** The scrub pattern now covers anything starting with `wcap.v1.`,
case-insensitive, up to whitespace, a quote, a bracket or a separator, so malformed and
non-canonical forms are scrubbed too. The filter now also scrubs every non-standard LogRecord
extra, not only RQ's `arguments`/`kwargs`. Objects in the message, args or extras are rendered and
scrubbed, since a formatter would call `str()` on them.

**Before** (Codex probe on the c7492097 source):
- the `!!!`-prefixed signature verifies with the same claims;
- it survives the filter;
- DispatchWorker drives the job to `succeeded`.

**After:** that token does not verify and does not survive the filter, the worker returns
`rejected / WORKER_CAPABILITY_INVALID`, and the job stays `queued`. Reports hold booleans only;
no token or key is printed or stored.

## Regressions and before/after

New unit regressions, run on fakes and the real HMAC/filter:
- `test_malformed_representations_of_a_valid_token_are_denied`: 14 variants, namely non-alphabet
  prefix, suffix and interior characters, body non-alphabet, padding `=`/`==`, body padding, a
  trailing dot, leading/trailing space, a trailing newline, non-canonical spare bits, an
  uppercase prefix and the standard alphabet. The valid token still verifies.
- `test_service_and_worker_reject_a_noncanonical_token`: the provider is never called and the
  untampered token still completes.
- `test_redaction_covers_malformed_tokens_in_every_record_field`: message, args, an object arg,
  an object msg, `arguments`, a nested dict extra, a free-text extra and exception text.
- `test_failing_audit_backlog_never_starves_a_healthy_quarantine`: claim_limit+5 failing audits
  sit ahead of the quarantine. The quarantine is delivered and marked once and audits are
  retained. A later pass produces no duplicate effect, and the audits are delivered once their
  sink recovers.
- `test_all_failing_side_effects_terminate_with_each_row_tried_once`: 2×limit+3 rows, every one
  tried exactly once per invocation and released.

New SQL regression, `test_failing_audit_backlog_never_starves_quarantine_on_sql`
(test_audit_durability.py): claim_limit 3, 6 failing audit rows ahead of the quarantine. The
quarantine is applied once, every audit is tried once and stays pending and released, the second
pass is a no-op, and the audits are delivered after recovery. **NOT_RUN locally**: there is no
PostgreSQL. This is not runtime proof.

Optional strengthening in `test_capability.py`, the duplicate-receive test: it now also asserts
that the owner epochs of the child's output scopes are unchanged. A second provider run would
bump them, so this proves the provider did not run again. It is not a new finding or gate.

`before_after.py` rebuilds the exact reviewed B5 source c7492097 outside the repository and runs
the 5 new unit regressions against it:
- on c7492097: **5 failed**;
- on the fix: **5 passed**.

## Local checks (direct, Windows, root venv; local RQ 2.11, Studio RQ 2.12 not exercised)

| Check | Result |
|---|---|
| Phase A 6 suites | 223 passed, 1 skipped: test_ai_job_polling.py:180, the live app import needs Pillow |
| B2–B5 integration + B3/B4/B5 unit | 94 passed, 95 skipped. The 95 are PostgreSQL/Redis cases (64 B2–B4 + 31 B5), **NOT_RUN** |
| B5 unit | 54 (27 capability/worker/redaction + 27 effects/notices) |
| Fixture runner | exit 0, 20 PASS / 215 checks, digest d17f58a3… unchanged, optional HTTP NOT_RUN 1 |
| ruff check / mypy src (18) / mypy tests (20) | PASS. The pre-existing q00_followups mypy errors stay excluded and unchanged |
| validate_harness / repository_security / architecture / skeleton; `git diff --check` | exit 0 / clean |

## Changed files (reviewed c7492097 hash → fix hash)

ports/ai_jobs.py 7ae97729→b402d247; services/ai_jobs.py 08291990→f28f8316; fakes.py
e60720da→4d598ac9; sql/repository.py 4ec3f65b→cc546d0f; worker.py 3c47c1bc→c7473056;
worker_capability.py 99555272→f93963ea; test_ai_job_b5_capability.py e8f717e0→37727191;
test_ai_job_b5_effects.py 823e730b→30044628; test_audit_durability.py cec15c7b→5178b981;
test_capability.py f391cbb0→5d526ae3. No new paths: the union manifest is still 43 files.

## Package (ignored, local/b5fix01-studio-package-20261015/)

| Item | SHA-256 |
|---|---|
| b5fix01_previous.sha256 (= closed B4 Studio manifest) | f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4 |
| b5fix01_delta.patch (25 files, from f1c6834f) | c7a2d4089d6409902ede40ca3a5629f9ad32e0d53bae5fb101a293bae08caa28 |
| b5fix01_source.sha256 (43-file union manifest) | 831147fabe0ceb65f55a10cf128fae2dc143de314ebd7540347671a109e3e6a7 |
| run_b5fix01_on_studio.sh | f5a3cbd6c634f66164a6d2e470dcae4b81c1036a216e3a2d69f10fad96e0a42e |
| be2-b5-fix01-studio-20261015.zip | fa06d8794e0ce525c7f9eb1b00fcc3de37457f8b2fcc377f990ab0b55545a266 |

- **Runner** (remote folder `be2-b5-fix01-package`). It accepts only two source states and
  refuses anything else untouched:
  - the closed B4 snapshot f1c6834f, where the delta is applied;
  - the exact corrected manifest, as a verify-only retry.
  - The earlier unrun B5 source (ZIP 9475fe27 / c7492097) is not an accepted state.
- **Builder self-check:** PASS.
  - f1c6834f is rebuilt from base plus six patches; the 11 added paths are at base.
  - Previous plus delta equals the 43-file manifest; a second apply is refused; the worktree
    reverse check exits 0.
  - No other packaged-area change exists and ZIP members are byte-identical.
  - The 42 files of the seven older packages, including the old B5, are unchanged.
- **Host simulation:** 9/9 PASS, using real scratch Git and a Docker stub.
  - Apply and verify-only retry pass.
  - Docker failure gives 125 and FAIL, then the retry passes.
  - Foreign tracked or untracked file, known-file edit, tampered delta and **unrun old B5 source**
    are each refused before Docker.
  - The inner script passes `bash -n`. This is not runtime proof.
- The disclosed Q00 EOF disposition of test_ai_job_q00_followups.py is carried as before.

Expected Studio result: **B2–B5 189 passed / 0 skipped** (the closed B4 104, plus 54 B5 unit and
31 B5 PostgreSQL/Redis tests), **Phase A 224 / 0 skipped**, fixture runner exit 0,
`RUNNER_RESULT=PASS`.

## Next

1. Codex reviews fix01 source and package.
2. Only then does the user run it, per local/claude/prompts/B5_FIX01_STUDIO_RUN_20261015.md. The
   result is recorded as USER_REPORTED_REMOTE.
3. A focused B5 closure review follows. B6 starts only after that.

No staging, commit, push, deploy, install or service change was made. The old B5 package (ZIP
9475fe27) and all B2–B4 packages are preserved as history.
