# B1 P2 Addendum 3 — STALE_CONTEXT diagnostic plan

**Status:** diagnostic plan; no production fix is authorized.

## Scope and pinned starting point

- Owner-approved diagnostic source: `evidence/B1_P2_ADDENDUM2_ORDERING_FIX_REPORT_20261104.md`, SHA-256 `3645DE2E2382BAC289F9EDFAC4DDF296CEE195A170330FA791D71A500282E2B0`.
- Checkout observed before this plan: branch `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, staged index empty, 101 status entries.
- PostgreSQL target, authorized by Addendum 3: retained task-owned database `s2l_b1_review_20261104_6a1af65b`, local PostgreSQL 17, loopback only. Credentials and connection URL are not recorded.
- Existing test file SHA-256 before diagnostic instrumentation: `4D81FDD3B4F73FF56027DB632EAB2AF0AF7C102CFEFB53990FAEC83A0D6FD0E6`.

## Diagnostic route map from source

`GuardedVisionJobProvider.run` invokes the real `VisionAnalysisService`; after the loopback stub succeeds, the provider returns a completion claim. `DispatchWorker.handle` passes that claim to `AiJobService.accept_completion`. The service starts with failure `STALE_CONTEXT`, runs at most `DECISION_ROUNDS=2`, calls `_check`, then `_decide_completion`; authoritative decisions call `_hold` before `cas_job` and `put_completion_receipt`. `_StaleOwnerDecision` rolls back that transaction and repeats the bounded round; exhaustion raises `_unresolved(failure)`.

`CurrentFactsBe1PilotEligibility.check` can reject an invalid job/scope, a failed or missing resolver result, any mismatched pinned request/facts field, non-synthetic facts, or an invalid owner fence. `_CombinedBe1OwnerFence.hold` can reject multiple auth fences, a non-transactional auth hold, a false authorization fence, or a stale facts fence; it also converts any caught exception to a stale fence. `PostgresBE1OwnerFence.hold` can reject a non-PostgreSQL/non-transactional connection, duplicate or malformed scopes, epoch mismatch, missing/ambiguous locked target rows, a changed resolved-facts fence, or an exception converted to `current=False`. `_decide_completion` separately returns a stale disposition if pinned and current context revisions differ.

## Allowed diagnostic changes and run protocol

1. Change only `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`. Add local wrappers around the real eligibility check, `_decide_completion`, `_hold`, combined owner-fence hold, authorization hold, and facts-fence hold. Each wrapper records sanitized booleans, revision values, transaction state, scope categories, return values, and caught exception type/SQLSTATE/safely masked message, then returns or re-raises exactly as the original did. Do not perform extra resolver reads or alter branch results.
2. Extend the test's existing post-dispatch state reader with read-only queries keyed only by the current test-created `job_id` and its attempt. Record job state/disposition/result count, attempt outcomes, dispatch outbox status, completion receipt count/disposition, analysis-head count, and invocation states. Do not query unrelated rows or log identifiers, payloads, digests, secrets, or connection data.
3. Run only `test_b1_succeeded_is_durable_before_real_app_result_acceptance` against the named retained task DB, at most five total times. Report every actual outcome and frequency. Do not reset, clean, migrate, create or drop any database.
4. Do not edit production code, schemas, migrations, approvals, prior evidence, or unrelated working-tree changes. Do not stage, commit, push, merge, reset, stash, or call external services.
5. Optional route-surface baseline and URL-guard rerun are not required for the diagnostic conclusion. Do not create an external worktree; mark those checks `NOT DETERMINED` / `NOT RUN` unless a safe, already-existing baseline is established without altering unrelated state.

## Completion checks and artifacts

- Save a new diagnostic report under `evidence/` with the exact test command, per-run output/exit code, H1–H4 findings, minimal proposed fix (not implemented), current checkout/status counts, file hashes, and checks actually run.
- Run the three repository validators and `git diff --check`; run Ruff check/format and mypy only on the changed PostgreSQL test file. No PostgreSQL suite beyond the single named test.
- Create a new snapshot under `.claude/handoff/snapshots/`; do not overwrite prior snapshots. Include a manifest with hashes and only the diagnostic plan, scoped test, and new report copies.
- Final status is `XONG-CHƯA REVIEW` or `BLOCKED`; this work does not fix or accept B1 P2 / Finding 2.
