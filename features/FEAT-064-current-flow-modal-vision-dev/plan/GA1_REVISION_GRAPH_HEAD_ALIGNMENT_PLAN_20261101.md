# GA1 migration graph head expectation alignment (2026-11-01)

**Status:** Owner-approved follow-up test-only scope. Approval is recorded append-only in `approvals/TASK_APPROVAL.md` before implementation.

## Diagnosis

The prior focused run confirmed the revision count of 25, then failed because the test expected head counts `(10, 10)` while the graph has `(11, 9)`. The T7a pilot revision is an independent root (`down_revision = None`) and declares `depends_on` for the age-provenance and AI revisions. It therefore adds a down-revision-only head and becomes the dependency-aware terminal head.

## Exact scope and allowlist

In `backend/tests/unit/test_synthetic_eligibility.py`, make only these updates inside `test_head_counts_by_both_methods_match_the_derived_expectation`:

1. Change the expected head-count tuple from `(10, 10)` to `(11, 9)`.
2. Replace the dependency-aware terminal-head assertion for `20261101_be1_age_0001` with one for `20261102_pv_0001`; keep the age revision assertion in `heads_down_only`.
3. Correct the adjacent comment to explain that the age revision remains a `down_revision` leaf while the pilot revision depends on the age and AI revisions and is the dependency-aware terminal head.

The earlier approved total revision expectation of 25 stays unchanged. No migration or product code is in scope. Other allowlisted records are this plan, one append-only approval entry, one new evidence report, one appended FEAT-064 ledger result, and local snapshot `.claude/handoff/snapshots/GA1_HEADFIX_20261101T201542/`.

## Acceptance criteria

1. The focused test `test_head_counts_by_both_methods_match_the_derived_expectation` passes.
2. Rerun the established GA1 offline suite using the copied network-blocking runner with both add-ons: `test_canvas_render_limits_ga1.py` and `test_pilot_vision_persistence_ga1.py`. Remove database-test configuration and keep pytest temporary files outside the repository.
3. Expected aggregate result is 618 passed, 4 skipped, 0 failed. Record actual results; any other failure is a hard stop and does not clear the regression gate.

## Exclusions

No migration/source/schema/runtime change, T6 work, PostgreSQL operation, Modal/GPU/provider call, external network, real-child data, stage, commit, or push is authorized by this addendum.
