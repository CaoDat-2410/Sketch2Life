# BE2-04 SK1 implementation evidence

> Current follow-up results and corrected acceptance coverage are recorded in
> `SK1_CODEX_FOLLOWUP_20261018.md` and, latest, `SK1_CLAUDE_FOLLOWUP3_20261018.md` (exact mapping of
> partial rows); those notes supersede the earlier pending-Ruff status and the broad acceptance
> mapping below.

## Identity and authorization

- Feature/card: FEAT-050 / BE2-04, checkpoint `SKETCH_COMPONENT_OFFLINE` (SK1).
- Worktree: `D:\GitHub\Sketch2Life\.worktrees\be2-04-sketch-generation`.
- Branch/base: `feature/be2-04-sketch-generation`, based on `113cdf956a09336a0abf5561bd939f5e13b31ea0`.
- Approval: `approvals/TASK_APPROVAL.md`; plan revision 5 SHA256
  `461d06849899ea41f2c93432ed8b88c5a64428cf17bce5d2959a6d26ef4fa819`.
- The approved plan and approval remain unchanged. No staged changes, commits, push, merge, deploy,
  Studio, SQL, Redis, live provider, decoder, route, or migration work is part of this checkpoint.

## Implemented

- DATA-23 `SketchProposal` domain invariants, per-version level provenance, output validation,
  deterministic content/generation digests, status transitions, records/events and minimal device
  view contracts.
- Application ports and service for the 03/02 handoff resolver, cache-hit/open-by-id, idempotent
  creation/cancellation/revision, job scheduling, attempt-keyed output staging, C5/C8 gates,
  decision-token retries, revalidation, owner notices and cleanup.
- Fixture adapters for BE2-01 jobs, policy/eligibility, admission, provider-copy lifecycle,
  coordinated repository/artifact publication, and the versioned `SketchHandoffV1` projection.
- Offline chain harness rebuilding the A1 composition from its public parts; one coordinated
  artifact port is shared by both job services; the router selects job type before start and checks
  `started` before either route continues.
- Synthetic H-AI-REVIEW examples and regression tests, including retries, cancellation races,
  decision-token windows, artifact quarantine/redelivery, shared queue ordering, and A1-builder
  parity. The R03 lost-create-reply path now records terminal state and cleanup job identity in one
  proposal revision to avoid a CAS/revision conflict.

## Tests and checks (Codex follow-up, 2026-10-18)

All commands used the existing `D:\GitHub\Sketch2Life\backend\.venv\Scripts\python.exe`
(CPython 3.12.10), with `PYTHONPATH` and `MYPYPATH` pinned to this worktree's `backend/src`; no
dependency was installed in this follow-up. JUnit and console receipts are in the ignored
`evidence/local/codex-followup-20261018/` directory.

| Suite | Result | Raw output |
|---|---:|---|
| SK1 domain/service/adapter/chain/race/contracts | 166 passed, 0 skipped | `local/codex-followup2-20261018/focused-final.junit.xml` |
| X01 BE2-01 regression | 337 passed, 1 skipped | `local/codex-followup2-20261018/x01.junit.xml` |
| X02 BE2-02 regression | 411 passed, 1 skipped | `local/codex-followup2-20261018/x02.junit.xml` |
| X03 BE2-03 regression | 127 passed, 1 skipped | `local/codex-followup2-20261018/x03.junit.xml` |
| Ruff on 14 new Python files | PASS | `local/codex-followup2-20261018/ruff-final.log` |
| Strict mypy on 14 new Python files | PASS | `local/codex-followup2-20261018/mypy-final.log` |
| Harness/security/architecture/skeleton validators | PASS | `local/codex-followup2-20261018/validate_*.log` |

Each regression suite has one existing live-app contract skip because Pillow is not installed in
the permitted environment. These are skips, not passes. The first X01 attempt also hit a Windows
`tmp_path` permission error for 17 cases under the default user Temp directory; rerunning with a
fresh ignored `--basetemp` produced the passing result above. Its initial log is retained for an
auditable record of the environment issue.

## Acceptance coverage after follow-up

The Claude review gaps below were checked against executable assertions. This is a focused
correction, not a declaration that every row of the approved acceptance matrix is complete.

| Review item | Current evidence | State |
|---|---|---|
| F-1 schedule no-op CAS race | race test for worker linking then cancellation before schedule link | Addressed; pending Claude re-review |
| F-2 Child resource-existence leak | N17 asserts existing and missing proposal IDs both return not found | Addressed; pending Claude re-review |
| P07, R12, N13 timeout exhaustion | chain tests for retry attempt 2 promotion, dropped hint recovery, and exhausted `PROVIDER_TIMEOUT` | Added and passing |
| N12, N18 chain behavior | R30 asserts unsafe moderation/event/Teacher reason/Child unavailable; N18 rejects `canvas_operations` with unchanged source | Added and passing |
| SK-C10 teardown audit | autouse fixture teardown for every chain and race harness checks port identity, audit violations and deferred failures; adapter test proves raw bypass is detected | Added and passing |
| R06, R31, R32, R33 | tests cover nested-unit rejection/deferred cancel order, claimed outbox sink waiting for C8 commit, stale-lease/event dedupe, and both drainers; follow-up 3 adds R31/R33 variants with completion-generated intents; follow-up 3a makes R31 prove the actual C8 commit boundary (held-commit handshake, committed state at mutation, mutation probe) | Demonstrated; pending Codex review |
| F-4 owner notice cleanup | notice invalidates first, then cancels the linked job outside the transaction | Added and passing |
| F-5 retry eligibility in A1 instance | shared chain eligibility routes Sketch retries through `SketchEligibility` | Added and passing |
| F-6 retriable create result | replay by assistance ID reschedules a REQUESTED proposal with no linked job | Added and passing; caller-driven only |
| R03 requester loses authorization | orphan is recorded in `cleanup_job_ids`, then A1-facing dispatch cancels it with `SCHEDULE_REFUSED`; no second job/provider call | Addressed in second follow-up |
| R11 failure matrix | link, stage, cancel and owner-notice commit faults leave no partial proposal/receipt/event/staged row; retry/replay succeeds | Added in second follow-up |
| P08/P11 | chain promotes v1, revises level and checks v2 policy, job, provider and content digests | Added in second follow-up |
| N23 | chain tests consent, Teacher confirmation, render and policy changes after C8, plus unchanged read | Added in second follow-up |
| C05 | report is built from live registry state after fixture purge; fixture never claims actual deletion | Added in second follow-up |
| P3 lost-link cleanup reason | follow-up 3: orphan cancelled with the proposal's own reason (consent/Teacher), `SCHEDULE_REFUSED` fallback; three regressions | Fixed; pending Codex review |
| P02/P06 chain, C06 | follow-up 3: chain tests for level_fx_1 text-only and repeated hint/open-by-id; producer-built example bundle compared for equality | Demonstrated; pending Codex review |
| Chain/contract mapping | N15, C09, N19, P09 demonstrated by the mapped tests; N04/N08/N11 chain variants and C03/C03b contract column remain partial (exact mapping in follow-up 3 note) | Partial rows remain partial |
| A1 callback end to end; N16 | behaviour unchanged; plan forwards via `RecordingSketchStage`; N16 matches plan wording | NOT_RUN / pending owner disposition |
| SK-NI01 and runtime gates | durable multi-process outbox, SQL/Redis, live provider/decoder and Studio | Not implemented / not run, as scoped |

The remaining partial rows, the open dispositions above and the F-5 deviation keep SK1 open. The approved plan remains unchanged;
`SketchChainEligibility` is recorded as a bounded implementation deviation requiring owner
disposition in `DECISIONS.md`.

## Verification-environment deviation and cleanup

While preparing mypy, a `uv run --project backend --extra dev` command created `backend/.venv`,
`backend/uv.lock`, and a local package cache and downloaded the declared runtime/development
dependencies, contrary to the approved no-dependency-install boundary. I stopped using that
environment and removed exactly those generated paths; no dependency manifest or lockfile change
remains. The implementation-stage checks from that temporary environment predate cleanup; the
follow-up tests and strict mypy listed above were subsequently run with the existing external
Python 3.12.10 environment after cleanup, as recorded in the ignored receipts. The follow-up
results therefore do not depend on the removed environment.

## Current disposition

The Codex follow-up checks pass, but the remaining partial coverage and the pending independent
Claude re-review mean SK1 is not owner-accepted. BE2-04 remains IN_PROGRESS / NOT_DONE. Results
establish offline fixture/component behavior only; they do not establish PostgreSQL, Redis/RQ,
provider, decoder, cross-process, Studio, or production behavior.
