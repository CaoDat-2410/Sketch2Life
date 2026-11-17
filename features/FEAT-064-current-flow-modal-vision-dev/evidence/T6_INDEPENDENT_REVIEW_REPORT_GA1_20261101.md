# T6 independent review — GOAL A1

**Review status: NEEDS_REVISION**  
**Date:** 2026-11-01  
**Reviewed implementation snapshot:** `.claude/handoff/snapshots/GA1_T6_20261101T205305/`

## Scope and review basis

Reviewed the T6 implementation against V4 D3, Goal A1, the approved T6 plan, its approval entry, report, tests, and snapshot. V4 and Goal A1 SHA-256 pins match the owner-provided values. All twelve T6 source/test/plan/approval/ledger/report files listed in the snapshot match the current working files byte-for-byte. The approval and progress ledger preserve the pre-T6 lines and append new entries only.

The implementation report records 637 passed / 4 skipped, static checks, and three passing validators. Those commands were not rerun during this review; this review is based on source inspection and the stored snapshot outputs. No source or approval file was changed. No PostgreSQL, Modal, provider, or external network call was made.

## Findings

### [P1] The decorator can report an unguarded provider call as not sent

`backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:208` passes through an `ObservationSucceeded` while the guard is still `NEW`. In the same branch, it rewrites an `ObservationFailed(provider_invoked=True)` to `provider_invoked=False`. If a bridge is miswired to an unguarded transport or a different guard, the bridge can send a request while this decorator's guard remains `NEW`; the decorator can then accept the success without this guard's durable `SENT`, or tell the caller no provider call occurred. That can enable an unsafe retry and defeats the guard boundary.

**Required direction:** allow only genuine no-send local failures through `NEW`; reject success and any outcome claiming invocation before this guard's `SENT`. Bind or verify that the bridge transport uses the same per-attempt guard. Add a regression test for an unguarded/mismatched transport.

### [P2] The race test begins after the first claim has already sent

`backend/tests/unit/test_invocation_guard_transport_ga1.py:400` starts the second worker only after the first request handler signals `entered`. That signal is set inside `do_POST`, after the first worker has claimed the ledger row, persisted `SENT`, and sent the request. The test proves that a later duplicate is refused, but does not exercise two workers racing to claim the same run concurrently, as the acceptance criterion requires.

**Required direction:** synchronize both workers at the claim boundary (with a barrier/test double) and prove that exactly one obtains the claim and at most one HTTP request is observed. Keep the existing after-SENT replay test as a separate case.

### [P2] The 160-second deadline does not bound synchronous DNS resolution

`backend/src/sketch2life/infrastructure/vision_analysis/transport.py:84` calls `HTTPConnection.connect()` with a socket timeout. `http.client` resolves a hostname synchronously before socket connect; socket timeout does not bound a stalled system resolver. A DNS stall can therefore make the exchange exceed the approved total 160-second deadline even though remaining-time socket timeouts are set for connect and later phases.

**Required direction:** ensure hostname resolution is bounded by the same monotonic deadline, or obtain an explicit owner decision that narrows the deadline contract. Add a deterministic resolver-timeout test without external network access.

## Gate result

T6 is **not independently accepted yet**. Return these findings to the implementer for an in-scope fix and a new snapshot. Keep A1 at XONG-CHUA REVIEW and do not start A2 until a follow-up review passes. The implementation report's test and validator results remain recorded as reported; this review adds no claim that they were rerun.
