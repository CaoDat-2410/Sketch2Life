# Milestone 1 review round-2 fixes — 2026-11-03

Status: **FIXED — CHỜ REVIEW ĐỘC LẬP**. This is implementation evidence, not an independent acceptance. It supplements the six round-1 fixes and does not begin Milestone 2.

Pinned plan: `plan/STORYRUN_LITE_MILESTONE1_INDEPENDENT_REVIEW_FIX_20261103.md`, SHA-256 `B054B44289EA9DE32F26878F719E06A1EA34591518BDDF5690EA62AB3BB295C4`.

## Findings and disposition

| Finding | Disposition and evidence |
| --- | --- |
| Round-1 P1 — a second demo after confirmation | The existing cancel command accepts PREPARATION_REVIEW, atomically moves the run to DELETE_PENDING and releases the active-owner identity, retaining the upload, result and receipts. No new state or migration. PostgreSQL tests now cover both cancel/create orderings, duplicate cancel replay, stale version/revision, and retained results. Two Bruno runs on one task DB use different synthetic image bytes and each complete a new Parent run, confirm, GET PREPARATION_REVIEW, cancel and close. |
| Round-1 P2 — committed Story result versus ledger finalization | The existing reconciliation remains identity/hash-based and is not limited to SUBJECT_REVIEW. The PostgreSQL/loopback suite covers confirm/cancel state changes between Story commit and A1 ledger finalization, matching and mismatching identities, and no redispatch. No provider inference was repeated for this review fix. |
| Round-1 P2 / round-2 P2 — attach replay race | Service checks the scoped receipt before mutable validation, then performs a locked durable recheck if target/admission validation fails. HTTP/PostgreSQL concurrency tests pause after the first miss, let a competing initial attach commit or leave a recoverable PENDING receipt and cancel the run, then verify the immutable 202 snapshot or COMMAND_RECOVERY_HOLD. The path does not dispatch again. Different actor/fingerprint behavior remains covered. |
| Round-1 P2 / round-2 P2 — singleton loss and readiness | Added GET `/v1/story-runs/readiness`, separate from liveness `/health`. Readiness calls the runtime probe and returns 503 after lock loss. Tests serialize concurrent probes and terminate the actual PostgreSQL lock-owner session; the old instance becomes unready and a new instance can acquire the lock. |
| Round-1 P2 — upload bytes in Bruno guide | README directs the operator through request 03 before completion and checks size/hash against the exact bytes. Both real Bruno CLI runs execute request 03 and its assertion before upload completion. |
| Round-1 P3 — post-confirm GET state | Request 07 remains the pre-confirm SUBJECT_REVIEW check. Separate request 11 checks PREPARATION_REVIEW after the 202 confirmation. Both Bruno runs pass request 11. |

## Verification actually run

- Offline regression, with all DB URL and PG environment variables removed from the test process and pytest basetemp outside the repository: **170 passed, 1 skipped, 0 failed** in 27.35 seconds. The single skipped case requires PostgreSQL and is exercised in the isolated DB suite. The sanitized per-test output is `evidence/MILESTONE1_REVIEW_ROUND2_OFFLINE_20261103.log`.
- PostgreSQL 17.11 isolated task cluster and new database, synthetic legacy Organization seeded before the StoryRun migration: **46 passed, 0 failed, 0 skipped, 0 timeout** in 12.11 seconds. Included PostgreSQL, V2 loopback/reconciliation, replay-concurrency and singleton/readiness tests. The cluster stopped successfully; its task data directory is retained outside the repository. Sanitized raw output: `evidence/MILESTONE1_REVIEW_ROUND2_POSTGRES_20261103.log`.
- Bruno CLI 4.3.0, same isolated task database and local StoryRun API, **two different synthetic PNGs, two complete runs, 11/11 requests and 11/11 tests passed per run**. Request status sequence: readiness 200, create run 201, create upload 201, upload bytes 200, complete 202, upload GET 200, attach 202, run GET 200, confirm 202, post-confirm GET 200, explicit cancel 202. The post-confirm body was PREPARATION_REVIEW. Real ClamAV 1.5.4 returned CLEAN for each PNG and INFECTED for in-memory EICAR. The Windows Job Object image normalizer was used. Vision was a V2 HTTP loopback stub; it sent exactly two stub requests, one per run. Sanitized result summary: `evidence/MILESTONE1_REVIEW_ROUND2_BRUNO_SUMMARY_20261103.json`.
- Ruff check and format check: **12 scoped files pass**. Strict mypy on five changed production source modules: **no issues**. This is not a whole-repository type-check claim.
- `validate_harness.py`, `validate_repository_security.py` (6,227 publishable files), `validate_architecture.py`, and `git diff --check`: **PASS** after documentation/evidence closeout.

## Limits and preserved state

- Modal/GPU/provider: **NOT RUN** after these fixes; invocation count in this review round is **0**. The earlier one-request Modal smoke is historical evidence and was not repeated. The Bruno Vision implementation is a loopback stub, not a live AI call.
- Full BE/A2 regression and production authentication/CORS: **NOT RUN / NOT VERIFIED**. This is synthetic local demo coverage only.
- The configured project mypy target is the production package; only the five changed production modules are claimed clean. No test-module mypy-clean claim is made.
- The 55 pre-existing local A2 paths still match the preserved pre-merge snapshot byte-for-byte: 55/55. No A2 implementation was changed.
- Checkout remains on `feature/feat063-be-foundation`, HEAD `c4edf51fd5af69a327d6776625cf387447f4ec59`, index empty. No stage, commit, push, merge, existing-database reset, or provider call occurred.

Supplemental snapshot: `.claude/handoff/snapshots/MILESTONE1_REVIEW_ROUND2_CLOSEOUT_20261103/`. The reviewer must inspect the current working tree and this snapshot; HEAD alone does not contain the uncommitted fixes.
