# B1 P2 Addendum 5b — owner-run PostgreSQL verification plan

**Status:** `WAITING_FOR_OWNER_RUN`  
**Purpose:** continue Addendum 5 by having the owner run the approved PostgreSQL nodes locally; this Codex session will inspect logs only.

## Pinned inputs and checkout

- Prior Addendum 5 report: `evidence/B1_P2_ADDENDUM5_FINDINGS_CLOSURE_REPORT_20261104.md`, SHA-256 `BB5EDC9DFD9D8C052DC636C2437B0A9F0BB65922BF76F5887E5456063723CA2A`.
- Prior Addendum 5 plan: `plan/B1_P2_ADDENDUM5_FINDINGS_CLOSURE_PLAN_20261104.md`, SHA-256 `F52C1B733900CEDF8391C2DD2A619560EB8B630CE06BCF0426626004AD94A3AC`.
- Prior snapshot manifest: `.claude/handoff/snapshots/GB1_P2_A5_20261104T163618/manifest.json`, SHA-256 `D2D63B42B85037A50D89C063942438729DA4493A0F4D0A867C9323485D319E2D`.
- Checkout at plan creation: `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, index empty.
- Four A5-pinned source/test hashes were rechecked and matched the values in the owner launch prompt.

## Scope and owner-run execution

The owner runs the seven focused PostgreSQL nodes using the local runner and the already-approved task-owned database `s2l_b1_review_20261104_6a1af65b` (PostgreSQL 17, loopback `127.0.0.1:5433`, user `postgres`). This plan records the owner authorization in the launch message; it does not authorize this Codex process to connect to PostgreSQL. No database URL or credential is to be copied into chat, logs, this plan, reports, or Git.

Run nodes 1, 4, and 7 three times each; nodes 2, 3, 5, and 6 once each; then run all seven once more as the final round. Total: 20 invocations. A skipped node is not a pass. Preserve each command, stdout, stderr, exit status, run context, summary, and before/after status-name lists in the owner runner's `GB1_P2_A5B_<timestamp>` log directory.

The seven test names must match the live test file:

1. `test_b1_succeeded_is_durable_before_real_app_result_acceptance`
2. `test_b1_unknown_after_sent_is_not_accepted_or_replayed`
3. `test_b1_hold_before_send_creates_no_result_or_invocation`
4. `test_b1_stale_owner_fence_rejects_result_after_provider_success`
5. `test_b1_stale_artifact_fence_rejects_result_after_provider_success`
6. `test_b1_concurrent_duplicate_delivery_uses_one_attempt_and_one_send`
7. `test_b1_sent_invocation_survives_process_rebuild_without_second_provider_call`

## Log review gate

After the owner provides the exact log-directory name, inspect `run-context.txt`, `summary.txt`, `status-names-before/after.txt`, and every `*.command.txt`, `*.stdout.txt`, and `*.stderr.txt`. Verify checkout/index and all four file hashes, all 20 invocations, command/file/node alignment, and actual passed/failed/skipped counts from stdout. Do not copy credentials, URLs with credentials, or disallowed absolute local paths into evidence. If a run skipped, authentication failed, a hash/checkout changed, or a failure is outside the narrowly authorized test-assertion corrections, report `BLOCKED` and stop.

If every PostgreSQL node passes with zero skips, run the pinned Addendum 4 offline regression and the artifact-fence plus queue-composition unit tests in this session, then the required Ruff, strict mypy, validators, and `git diff --check`. Do not reuse historic results as current evidence. Any assertion correction must follow the original Addendum 5 constraints, including exact observed state, no loose inequalities, and the two-round-per-node limit.

## Boundaries and deliverables

- This Codex session does not connect to PostgreSQL and does not rerun PostgreSQL tests.
- No Modal/GPU/provider, external network, Alembic, database creation/reset/drop/truncate, cleanup outside exact fixture-owned rows, approval/status edits, staging, commit, push, merge, reset, stash, or clean.
- After creating this plan and a preflight snapshot, stop at `WAITING_FOR_OWNER_RUN`. The owner must send the exact `GB1_P2_A5B_<timestamp>` log-directory name before analysis resumes.
- The eventual verification report is `evidence/B1_P2_ADDENDUM5B_PG_VERIFICATION_REPORT_20261104.md`; its final disposition may only be `XONG-CHƯA REVIEW` or `BLOCKED`, and requires independent review with a separate PostgreSQL gate.
