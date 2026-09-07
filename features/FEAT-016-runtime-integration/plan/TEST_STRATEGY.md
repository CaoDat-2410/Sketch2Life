# Runtime Integration test strategy

- Status: AWAITING_APPROVAL
- Revision: 1
- Test data: synthetic fixtures only.
- Baseline: FEAT-015 revision-2, 23 passed.

The first runtime slice is fixture-only and in-memory. It must prove state semantics before external infrastructure is added.

## Required gates

1. Standalone regression for P1, P2, P3 and P4.
2. Contract round-trip and negative schema tests.
3. Application state and stale-version tests.
4. Local HTTP/job polling and idempotency tests.
5. P3/P4 failure and fallback tests.
6. Fixture-only client/E2E flow with screenshots/recordings only when visual review is approved.

## Required negative cases

- invalid media and source hash mismatch;
- ASR/vision disagreement before Gate A;
- Gate A correction version and stale confirmation;
- missing age/readiness/material/supervision context;
- no eligible activity;
- Gate B activity/objective mismatch;
- stale/duplicate/out-of-order job completion;
- P3 missing/corrupt asset and stale renderer event;
- P4 cache miss, generation exception, timeout, unsafe/block and fallback;
- feedback before handoff and duplicate feedback.

All tests must record exact command, environment, fixture hash, source commit(s), result and interpretation in FEAT-016 evidence. A skipped check remains a limitation, not a pass.
