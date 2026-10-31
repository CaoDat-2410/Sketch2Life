# GA1 revision-count test alignment report (2026-11-01)

**Status:** BLOCKED after the approved count-only edit exposed a second stale graph expectation. The aggregate offline regression and T6 were not run/started.

## Approved scope and change

Owner-approved plan: `plan/GA1_REVISION_COUNT_TEST_ALIGNMENT_PLAN_20261101.md` (SHA-256 `B86D35814B73D759049BC06C23D75C050CAA6398CA5252726C2979A8D4C0C158`). The matching append-only approval is in `approvals/TASK_APPROVAL.md`.

Changed only the assertion and adjacent comment in `backend/tests/unit/test_synthetic_eligibility.py` to expect 25 total revisions, including the new pilot-vision revision. The test's total-count assertion now passes.

## Verification

Focused command, run from `backend/` with `PYTHONPATH=src`, `BE1_TEST_DATABASE_URL` unset, pytest cache disabled, and `--basetemp` outside the repository:

```text
python -m pytest tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation -q -o addopts= -p no:cacheprovider --tb=short --basetemp <external-temp>
```

Result: **1 failed** at line 463. The stale total of 24 no longer fails, but the next assertion expects `(10, 10)` heads and receives `(11, 9)`.

The new `20261102_pilot_vision.py` revision has `down_revision = None` and `depends_on = ("20261101_be1_age_0001", "20261015_ai_0001")`. Thus it adds a down-revision-only head while its dependency edges consume two previous dependency-aware heads and make the pilot revision the dependency-aware terminal head. The existing assertion that the age revision is also a dependency-aware head is stale as well.

The approved addendum requires stopping if the focused test reveals another failure. Therefore the full 618-pass/4-skip offline regression was **NOT RUN**. The prior aggregate remains 617 passed, 1 failed, 4 skipped; it is not represented as green. T6 has not started.

## Follow-up needed

Any further test edit is outside the approved count-only scope. A proposed follow-up scope is limited to updating the expected head counts to `(11, 9)`, asserting `20261102_pv_0001` as the dependency-aware head instead of `20261101_be1_age_0001`, and correcting the adjacent explanatory comment. No migration change is indicated by this test result. Obtain explicit owner approval before those edits, then rerun this focused test and the complete offline suite.

No PostgreSQL, Modal/GPU/provider, external network, real-child data, stage, commit, or push was used.
