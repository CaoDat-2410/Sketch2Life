# GA1 migration graph head expectation alignment report (2026-11-01)

**Status:** Approved test-only follow-up complete; focused and aggregate offline regression are green. T6 has not started, so GOAL A1 is not complete.

## Approved scope

Plan: `plan/GA1_REVISION_GRAPH_HEAD_ALIGNMENT_PLAN_20261101.md` (SHA-256 `272B7C06546BABB86AFB1DBDCB2CB6CC73B0872CFC3667D9F40A80E9F5D84DF6`). The owner approved the exact scope in the append-only FEAT-064 approval record before implementation.

In `backend/tests/unit/test_synthetic_eligibility.py`, the approved follow-up changed the expected head counts to `(11, 9)`, made `20261102_pv_0001` the expected dependency-aware terminal head, and corrected the explanatory comment. The total revision count remains 25 under the earlier separately approved scope. No migration or product code changed.

## Verification

| Check | Result |
|---|---|
| Focused `test_head_counts_by_both_methods_match_the_derived_expectation` | 1 passed in 0.48 s. |
| Established GA1 offline regression, copied network-blocking runner, including the M1 canvas-render and T7a persistence unit add-ons | 618 passed, 4 skipped, 0 failed in 8.60 s; runner exit 0. |

The runner removed `SKETCH2LIFE_*`, `AWS_*`, and `BE1_*` environment values, disabled dotenv settings, blocked non-loopback socket connections, disabled pytest cache, and used a temporary directory outside the repository. The single earlier focused failure `(10, 10)` vs `(11, 9)` was corrected only after the separate owner approval; the full suite was run after the focused test passed.

## Boundary

The regression hard-stop is cleared. T6 remains not started and must follow V4 D3 with its own GA1-specific plan and append-only approval record before source changes. No PostgreSQL, Modal/GPU/provider, external network, real-child data, staging, commit, or push occurred.
