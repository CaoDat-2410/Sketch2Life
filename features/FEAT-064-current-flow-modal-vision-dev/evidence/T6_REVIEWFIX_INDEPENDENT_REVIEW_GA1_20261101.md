# T6 review-fix independent review — NEEDS_REVISION

**Review status: NEEDS_REVISION**
**Date:** 2026-11-01
**Reviewed snapshot:** `.claude/handoff/snapshots/GA1_T6_REVIEWFIX_20261101T214519/`

## Scope and review basis

Read-only follow-up review of the three earlier T6 findings against V4 D3, Goal A1, the approved T6 implementation and review-fix plans, append-only approval, code, tests, report, and snapshot. V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`, Goal A1 SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`, review-fix plan SHA-256 `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`, and report SHA-256 `E5A68D793BD535F6B14E7B7A87D8B3E9E2258944F8C50A95C2133A7D77233FE3` match their recorded pins.

The prior findings appear addressed in source/tests: the decorator binds and rechecks the same guard identity; unexpected `NEW` outcomes are rejected; two workers synchronize at the ledger claim boundary; and DNS wait time is bounded for the caller by the monotonic deadline. The reviewer did not run tests or validators. Reported focused and aggregate results were checked against the saved runner and outputs.

## Findings

### [P1] The saved aggregate output does not include the T6 test module

The copied runner's default `files` list at `offline_check.py:21` does not contain `tests/unit/test_invocation_guard_transport_ga1.py`. It adds extra test paths only from command-line arguments at line 22. The saved aggregate output is `618 passed, 4 skipped`; the separately saved focused T6 output is `28 passed`. The report claims the aggregate invocation appended T6, but the 618-test output has no additional collected T6 cases. The T6 acceptance run is therefore not evidenced by this aggregate log.

**Required:** rerun the same established offline suite with its existing M1 and T7a add-ons plus `tests/unit/test_invocation_guard_transport_ga1.py` explicitly passed to the copied runner. Preserve the exact command/arguments and full result. The prior baseline is 618 and the focused T6 module has 28 tests, so 646 passed / 4 skipped is the expected count if the combined run has no failures; record the actual result. Append a factual correction to evidence and the goal ledger and create a new snapshot. Do not overwrite earlier records.

### [P2] Timed-out DNS calls can accumulate unbounded resolver threads

`backend/src/sketch2life/infrastructure/vision_analysis/transport.py:242` creates a new daemon thread for every DNS resolution. The monotonic deadline stops the request thread from waiting, but it cannot stop a resolver already blocked inside `getaddrinfo` or an injected resolver. Each concurrent timed-out call can therefore leave another live thread behind; repeated stalls have no concurrency bound and can exhaust process thread resources.

**Required direction:** before connecting this transport to a concurrent live caller, add an explicitly bounded resolver strategy (or another approach that both preserves the deadline and bounds outstanding resolver work). Add a deterministic test issuing multiple stalled lookups and prove that the number of active resolver workers remains capped and later calls fail closed without sending HTTP. This was not part of the current review-fix approval, whose plan explicitly allowed a per-resolution daemon thread; obtain a new narrow plan and owner approval before changing source.

## Gate result

T6 is **not independently accepted**. Keep GOAL A1 at `XONG-CHƯA REVIEW` and do not start A2. No source, test, approval, plan, or snapshot was changed by this review; no test or validator was run. Branch and HEAD remain `feature/feat063-be-foundation` / `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; the index was empty at review time. No PostgreSQL/Alembic, Modal/GPU/provider, or external network operation occurred.
