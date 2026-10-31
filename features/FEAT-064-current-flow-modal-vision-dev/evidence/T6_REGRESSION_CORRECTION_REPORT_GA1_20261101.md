# T6 aggregate regression correction — GOAL A1

**Result:** the prior saved aggregate omitted the T6 test module; the correction run explicitly included it and met the expected count.
**Date:** 2026-11-01
**Review finding:** `T6_REVIEWFIX_INDEPENDENT_REVIEW_GA1_20261101.md`, SHA-256 `317EEB31B91E0D4A580314E53E0DA89F0F4BF7715C76506E9B93294703F25897`.
**Authority:** V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`; frozen T6 plan SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`; previous review-fix plan SHA-256 `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`.

## Correction

The previous T6 review-fix report stated that the aggregate runner invocation appended the T6 module. The independent review found that its saved 618/4 output did not include that module. This report corrects the evidence record only; the previous report and snapshot remain unchanged.

A new snapshot directory was used so the runner could write its `offline-latest.txt` without overwriting an earlier snapshot. The runner was copied byte-for-byte from `GA1_T6_REVIEWFIX_20261101T214519/offline_check.py`; SHA-256 is `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`.

Exact command and arguments:

```powershell
& "backend/.venv/Scripts/python.exe" -u ".claude/handoff/snapshots/GA1_T6_REGRESSION_CORRECTION_20261101T222500/offline_check.py" tests/unit/test_canvas_render_limits_ga1.py tests/unit/test_pilot_vision_persistence_ga1.py tests/unit/test_invocation_guard_transport_ga1.py
```

Actual output: **646 passed, 4 skipped, 0 failed** in 21.07 seconds; runner `TEST_EXIT 0`; outer process exit code `0`. This matches the expected 646/4 count. The exact runner console output, runner-captured pytest output, command, and exit code are stored in the new snapshot.

The offline runner blocks external network and clears provider/database environment configuration. These tests use synthetic fixtures, the test-local blocked resolver, and loopback HTTP only. No PostgreSQL/Alembic, Modal/GPU/provider call, or external network call was made.

## Snapshot

`.claude/handoff/snapshots/GA1_T6_REGRESSION_CORRECTION_20261101T222500/`

This is a factual correction to the regression evidence; it does not approve T6 or change the independent-review gate. T6 remains `XONG-CHƯA REVIEW` pending the bounded-resolver follow-up and another independent review.