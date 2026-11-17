# BE2-03 A1-CR03-F1 / F2 follow-up fixes — 2026-10-17

State: **A1_CR03_F1_F2_FIXED_PENDING_CODEX_REREVIEW**. Bounded fix within the existing A1
approval (`approvals/TASK_APPROVAL.md`, SHA256 f6a266c9…) and the frozen plan revision 3
(`plan/PLAN_REV3_APPROVED.md`, SHA256 e1fce645…), both unchanged. The re-review
`A1_CODEX_REREVIEW_20261017.md` (NEEDS_REVISION, 0 P1 / 2 P2) and all older implementation,
review and fix evidence are unchanged history. No acceptance, Git action, install or Studio run.

Identity: worktree `.worktrees/be2-03-assistance-orchestration`, branch
`feature/be2-03-assistance-orchestration`, HEAD f120c4f, staged 0. Before editing, all 32 hashes
in `../metrics/A1_CODEX_REREVIEW_20261017.json` (source, protected records, prerequisites)
matched the files.

## Root causes

- **F1:** `AssistanceCommitCoordinator.request_publication` deferred only while a *foundation*
  unit was open. Inside an assistance unit the same thread re-entered the `RLock`, so an owner
  publication requested after the unit's decision-epoch guard committed before the unit's own
  publication (consent/handoff and disclosure/cache manifestations).
- **F2:** BE2-02 Vision commits (invalidation, correction) were outside the decision protocol:
  the Vision store was an independent, uncoordinated repository and nothing advanced the
  decision token, so a Vision commit between the BE2-03 analysis read and its commit was
  invisible to cache acceptance and handoff.

## Regressions first

New `backend/tests/unit/test_assistance_cr03_followup.py` (10 tests) was run against the
reviewed source before any product edit: **8 failed, 2 passed**. The 2 passes are unchanged
guards (an owner publication committed before the decision still stales the handoff; a failed
Vision commit does not move the token — vacuously true before the mechanism existed). A first
attempt had one test bug (it expected the raw storage message, while Vision wraps it as
`DEPENDENCY_UNAVAILABLE`); it was corrected before the recorded baseline, and the first log is
kept. Raw: ignored `../local/a1-cr03-followup-20261017/before.log`, `before-junit.xml`
(`before-attempt1.*` for the earlier run).

| Test | Invariant / commit order | Before | After |
|---|---|---|---|
| `test_f1_consent_publication_inside_handoff_unit_runs_after_commit` | Publication requested inside the handoff unit is deferred; the callback observes committed `analysis_ready` + 1 intent (handoff legitimately first) | fail (ran immediately) | pass |
| `test_f1_disclosure_publication_inside_cache_unit_runs_after_commit` | Deferred; callback observes the committed cache-hit request | fail | pass |
| `test_f1_publication_committed_before_decision_still_blocks_handoff` | Publication before the decision → stale, no intent | pass | pass |
| `test_f1_rollback_with_queued_publication_publishes_nothing_staged` | Assistance rollback: no staged request/receipt/intent/request-epoch; callback sees old committed state; owner epoch +1 only; next reconcile re-decides to stale | fail | pass |
| `test_f1_failed_deferred_callback_inside_unit_is_recorded_and_releases` | Failed deferred callback recorded, outer commit intact, lock free | fail (raised inside unit) | pass |
| `test_f2_vision_invalidation_between_cache_read_and_commit` | Actual `apply_invalidation` after the cache read → re-decision, no cache, created later | fail (cache_hit) | pass |
| `test_f2_vision_invalidation_between_handoff_gate_and_commit` | Actual invalidation after the gate → stale `CONTEXT_CHANGED`, no intent | fail (analysis_ready) | pass |
| `test_f2_teacher_correction_commit_between_read_and_commit_is_re_decided` | Actual `submit_correction` commit forces a fresh decision; still applicable → cache hit | fail (no re-decision) | pass |
| `test_f2_vision_call_inside_assistance_unit_is_refused` | A Vision unit cannot open inside an assistance unit | fail (allowed) | pass |
| `test_f2_failed_vision_commit_does_not_move_the_decision_epoch` | Rolled-back Vision write moves no token; lock free | pass (vacuous) | pass |

## Fixes (paths under `backend/src/sketch2life/`; no foundation/Vision source edit)

| Finding | Change |
|---|---|
| F1 | `infrastructure/assistance/fakes.py`: coordinator units generalized (`foundation`, `vision`, `assistance`); `request_publication` defers while **any** atomic unit is open on the thread; the queue drains only when the thread leaves its outermost unit, on commit or exception, after releasing the hold, each callback separately under the lock; failures recorded. Re-entrant `RLock`, lock order (coordinator → store) and the no-foundation/vision-inside-assistance rule kept |
| F2 | `infrastructure/assistance/adapters.py`: new `CoordinatedAnalysisRepository` decorator over the existing `AnalysisRepository` port — every Vision transaction is a coordinated `vision` unit, and a committed write bumps the `analysis:<org>` epoch before the unit releases (rolled-back writes bump nothing). `fakes.py`: `decision_epoch` returns the token (owner/request epoch, analysis epoch). `application/ports/assistance.py` and `services/assistance.py`: token type `tuple[int, ...]` (logic unchanged — submit/cache, handoff and cancel already compare the token at commit). `harness.py`: Vision service and `VisionAnalysisOutcomes` use the coordinated repository |

The analysis epoch is a separate fence scope, so BE2-01's eligibility fence is not disturbed by
Vision writes.

## After results

Runner (ignored `../local/a1-cr03-followup-20261017/run_checks.py`; existing venv; base Pillow
and existing multipart process-local; external network blocked, loopback allowed; import
origin asserted to this worktree):

| Group | Files | Tests | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|---|
| A1 (incl. 10 new follow-up tests) | 8 | 128 | 128 | 0 | 0 | 0 |
| BE2-01 regression | 11 | 338 | 338 | 0 | 0 | 0 |
| BE2-02 regression | 12 | 412 | 412 | 0 | 0 | 0 |

Re-review probes re-run on copies (ignored `../local/a1-cr03-followup-20261017/after-probes/`;
Codex receipts untouched): the in-unit disclosure publication no longer runs immediately (the
probe's old-behavior assertion fails); the Vision-invalidation probe no longer gets a cache hit
(re-decided, then debounced in its window); the semantics probe shows the in-transaction
publication deferred, its callback observing committed `analysis_ready` + 1 intent, and the
pre-transaction publication still ending `stale` with 0 intents.

Static/repository: ruff PASS (18 paths); `mypy --strict` PASS on 10 source files;
`mypy --strict --follow-imports=silent` PASS on 18 source+test files; harness, security,
architecture, skeleton VALID; `git diff --check` clean; 53 new files with no trailing space/CR;
no tracked source/test modified.

## Changed files (SHA256 prefix; full values in metrics)

| File | SHA256 |
|---|---|
| `infrastructure/assistance/fakes.py` | bdbb4317cfa2dc21… |
| `infrastructure/assistance/adapters.py` | a3f4f721423d5897… |
| `infrastructure/assistance/harness.py` | ffc688b437f45b95… |
| `application/ports/assistance.py` | 5e205659f2abbe3f… |
| `application/services/assistance.py` | 5bfff0481f7d3015… |
| `backend/tests/unit/test_assistance_cr03_followup.py` (new) | 361867f6a9e8de8d… |

All other A1 sources/tests, the handoff examples, the approved plan and the approval are
unchanged since the re-review.

## Remaining limits

Fake composition only: one coordinator lock, coarse org-wide owner/request and analysis epochs,
bounded re-decision rounds (heavy unrelated churn can delay a handoff until a later reconcile).
Vision reads are also serialized through the coordinator in this composition. No PostgreSQL
isolation, real OwnerFence, durable outbox or production fencing claim. Earlier A1 limits
remain. BE2-01 WAITING_STUDIO, BE2-02 PARKED, BE2-03 IN_PROGRESS / NOT_DONE. Next: Codex
re-review; findings are not self-closed.
