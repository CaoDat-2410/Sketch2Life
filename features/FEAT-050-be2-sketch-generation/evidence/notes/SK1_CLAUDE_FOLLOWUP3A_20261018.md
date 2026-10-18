# SK1 follow-up 3a — R31 commit-boundary proof and wording corrections (Claude)

## Disposition

Response to `SK1_CODEX_FOLLOWUP3_REVIEW_20261018.md` (NEEDS_CHANGES: 0 P1, 1 P2 F3-R31, 2 P3
wording notes N1/N2). State after this follow-up: **READY_FOR_CODEX_REVIEW**. SK1 remains
**NOT_ACCEPTED**; BE2-04 remains **IN_PROGRESS / NOT_DONE**. F-5 and the other recorded residual
owner decisions are unchanged and still open. No production code changed.

## Identity and boundaries

- Worktree `D:\GitHub\Sketch2Life\.worktrees\be2-04-sketch-generation`, branch
  `feature/be2-04-sketch-generation`, HEAD/base `113cdf956a09336a0abf5561bd939f5e13b31ea0`,
  staged 0 before and after; SK1 remains uncommitted by design.
- Approval (`0f356d32…7d25`), approved plan (`461d0684…a819`), the follow-up 3 note
  (`fb3b2e1f…cdc7`, reviewed bytes), its metrics (`82136e02…506d`) and the Codex review records are
  unchanged. This note supersedes two sentences of the follow-up 3 note (§3) without editing it.
- New: this note, `metrics/SK1_CHECKS_FOLLOWUP3A_20261018.json`, ignored receipts in
  `evidence/local/claude-followup3a-20261018/`.
- No branch, stage, commit, push, merge, Studio, SQL/Redis, real provider, decoder, route,
  migration or dependency installation.

## 1. F3-R31 (P2) — R31 now proves the actual commit boundary

Only `backend/tests/unit/test_sketch_generation_races.py` changed
(`28f55bd5…9bad` → `964cb21c67ca0c34e658f3d5601da3eb607f2c372a87a7a1d83a00db05ec615f`, 70 668 B).
`test_r31_real_completion_intent_sink_waits_for_c8_commit` keeps the completion-generated intent
(real Sketch UNSAFE completion, failing immediate sink) and now:

1. **Handshake while C8 is deliberately held.** The C8 unit's before-commit hook releases the
   paused worker and then **waits until the worker reaches `coordinator.request_publication`**
   (observed on the shared coordinator, only for the worker thread). It fails if the sink never
   reaches the coordinated publication.
2. **Held-window assertions** (still inside the unit, worker blocked on the lock): refs not
   quarantined, `artifact:<ref>` epochs unchanged, intent not marked delivered, committed proposal
   state still `analyzing`.
3. **Committed state at the raw mutation.** A wrapper on the raw `FakeArtifacts.owner_quarantine`
   records the committed proposal state (lock-free `store.peek`) at the moment of mutation; the test
   requires exactly `[blocked_unsafe]`, i.e. after the C8 publication.
4. **Order** `c8_holding → publication_attempted → c8_commit → raw_quarantine → drain_returned`,
   epochs +1 per ref after release, intent delivered, one `bumped=True` audit entry per ref by
   `h.jobs`, no `proposal_ready`.

Mutation proof (ignored probe `r31_mutation_probe.py`, log `r31_mutation_probe.log`): with the
artifact sink replaced by a no-coordinator mutation (fail injection, raw mutation and audit kept),
the rewritten test **fails** (`AssertionError: the sink never reached the coordinated
publication`); with the real coordinated sink it passes. Codex's original review probe
`codex-followup3-review-20261018/r31_boundary_probe.py`, rerun read-only against the new test, now
also fails (exit 1, same assertion; log `codex_r31_probe_rerun.log`). The R31 test passed in three
consecutive isolated runs (`r31-repeat.log`).

R31 state: **demonstrated** (completion provenance + actual commit boundary); pending Codex review.

## 2. N1 / N2 (P3) — corrected wording

- **N1 (C06):** `test_c06_committed_examples_match_deterministic_producer_build` proves **JSON value
  equality** between the committed fixture and the producer build (and build determinism), not
  byte equality; whitespace, escaping and key order are not compared.
- **N2 (P09):** `test_p09_teacher_record_fields_and_minimal_device_view` checks the record field set
  for `requested` and `pending_teacher_review`, and the minimal device view for the sampled states
  `requested` (pending), `pending_teacher_review` (pending) and `cancelled` (unavailable). Other
  evidence, cited separately: the chain R30 test asserts device view `unavailable` for
  `blocked_unsafe`; the domain test `test_device_status_never_implies_content` evaluates the pure
  `device_status` function for every `PipelineState` value and asserts only `pending`/`unavailable`
  are produced, with explicit values checked for `pending_teacher_review` and `blocked_unsafe`. The
  service test does **not** exercise the device view at every state.

## 3. Superseded statements in the follow-up 3 note

| Follow-up 3 note | Superseded by |
|---|---|
| line 37: "asserts byte-level JSON equality" | §2 N1: JSON value equality and determinism |
| line 68: "device view at every state" | §2 N2: sampled states requested / pending_teacher_review / cancelled, plus the separately cited R30 and domain tests |
| R31 row and residual statement that R31 waits for the C8 commit | §1: proof now rests on the rewritten test (handshake + committed-state observation + mutation probe) |

## 4. Checks on the final snapshot

Interpreter: existing repository venv (`<repo-root>/backend/.venv`, CPython 3.12.10; ruff 0.16.4,
mypy 1.20.2, pytest 8.4.2); `PYTHONPATH`/`MYPYPATH` pinned to this worktree's `backend/src`. No
package installed.

| Check | Exit | Result |
|---|---|---|
| Ruff, 14 SK1 Python files (cwd backend) | 0 | All checks passed |
| Strict mypy, 14 files | 0 | no issues in 14 files |
| Focused SK1, 6 test files | 0 | **175 passed, 0 skipped**; JUnit SHA256 `163dd1068213889b83520b36a6f0917a072181ddd44c0f0a95c4051dc747d92f` |
| R31 mutation probe | 0 | bypassed sink FAILS the test; coordinated sink PASSES |
| Codex R31 probe rerun | 1 (expected) | the mutant no longer passes R31 |
| Validators + `git diff --check` | see metrics | — |

X01–X03 were not rerun: this follow-up changes one SK1 test file only, the suites do not import
SK1 code, and their follow-up 3 receipts (875 passed, 3 Pillow skips) remain source-bound to
unchanged production files.

## 5. Still open (unchanged)

F-5 owner disposition; partial mapping rows (N04/N08/N11 chain, C03/C03b contract column); A1
callback end to end NOT_RUN pending disposition; N16 owner acknowledgement. Then SK1 acceptance and
a separately authorized commit.
