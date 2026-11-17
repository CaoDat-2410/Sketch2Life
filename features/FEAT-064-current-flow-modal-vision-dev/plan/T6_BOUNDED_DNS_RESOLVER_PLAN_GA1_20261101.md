# T6 bounded DNS resolver capacity plan — GOAL A1

**Status:** DRAFT — source and test changes are not authorized until a separate append-only approval cites this plan hash.
**Date:** 2026-11-01

## Authority and evidence pins

- V4 `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`: SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Goal A1 `.claude/handoff/CODEX_GOAL_G3G4_A1_20261101.md`: SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- Frozen T6 implementation plan: SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`.
- Previous T6 review-fix plan: SHA-256 `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`.
- Follow-up independent review `evidence/T6_REVIEWFIX_INDEPENDENT_REVIEW_GA1_20261101.md`: SHA-256 `317EEB31B91E0D4A580314E53E0DA89F0F4BF7715C76506E9B93294703F25897`.
- Regression correction `evidence/T6_REGRESSION_CORRECTION_REPORT_GA1_20261101.md`: SHA-256 `0E6870260AB74BB3C2CC64B0C81C3086DAEC6AD17E0399FB0F7B6BF74681D1DE`.
- Baseline transport SHA-256: `857BBEBA0A9BA252F498ADC5B4A077395B455AE6AAB7592DAB0723BA3A25EBF8`.
- Baseline focused T6 test SHA-256: `DE2D5DC20B12526B9C9251DF570A4BF6E25A36B822E36FE2FF15A7ABD597930B`.
- Regression snapshot: `.claude/handoff/snapshots/GA1_T6_REGRESSION_CORRECTION_20261101T222500/`; copied runner SHA-256 `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`; run was 646 passed / 4 skipped / 0 failed with all three requested add-ons.

## Finding and objective

The review found that a caller timeout cannot stop a resolver already blocked in `getaddrinfo` or an injected resolver. Creating one daemon thread per DNS lookup therefore allows timed-out resolver threads to accumulate without a bound. Keep the existing 160-second monotonic end-to-end transport deadline while placing a hard bound on resolver work process-wide. When all resolver capacity is occupied, later calls must fail closed before writing any HTTP request bytes.

## Proposed design for owner decision

**Recommendation: a shared process-wide resolver capacity of 2 active workers, with no unbounded submission queue.** The cap applies across all `HttpJsonTransport` instances in the process, not per transport. A resolver slot remains occupied until the resolver function actually returns or raises; expiration of the caller's deadline does not release a slot while the underlying resolver still runs. A call that finds capacity saturated fails immediately through the existing local, non-invoked transport-failure mapping. It must not create another thread, mark the invocation SENT, or send HTTP bytes. Retain daemon behavior so a permanently blocked system resolver cannot hold interpreter shutdown open; the cap bounds the maximum such stranded workers to two.

This is a proposal, not an owner decision. Its deliberate tradeoff is that two permanently stuck lookups disable further DNS-dependent provider attempts in that process until a worker exits. Alternatives for owner review:

- **Cap 1:** smallest resource ceiling, but one stuck lookup blocks all later DNS work.
- **Cap 2 (recommended):** tolerates one stuck worker while limiting the process to two resolver workers.
- **Cancellable resolver subprocess or OS-specific async resolver:** can provide stronger cancellation, but adds platform/process complexity beyond this narrow T6 fix.

Owner approval must confirm or replace the numeric cap and the process-wide scope before implementation. Do not silently fall back to a per-transport cap, because multiple transport objects would then defeat the resource bound.

## Exact proposed scope after approval

Implementation paths only:

1. `backend/src/sketch2life/infrastructure/vision_analysis/transport.py`
2. `backend/tests/unit/test_invocation_guard_transport_ga1.py`

Task records after approval: one new append-only T6 approval entry, one new implementation evidence report, one append-only entry in `status/PILOT_GOAL_LEDGER_20261101.md`, and one new ignored GA1 snapshot. No previous approval, plan, report, ledger entry, or snapshot is to be edited or removed.

Excluded: `invocation_guard.py`, `legacy_v2.py`, `ledger.py`, tables, schema, migration, service, worker, route, composition, all other source/tests, A2, PostgreSQL/Alembic, Modal/GPU/provider, and external network.

## Acceptance criteria

1. The default resolver coordinator has a fixed, owner-approved process-wide maximum of active resolver workers. It has no unbounded executor queue and cannot create a worker once the cap is occupied.
2. Resolver-capacity acquisition and DNS resolution remain within the same total monotonic deadline already used for TCP, TLS, request, response, and decode. Saturation fails closed before any HTTP request bytes and before the guard's SENT transition. The outcome remains non-invoked; the existing attempt is not made reusable by resetting or rewriting the durable claim.
3. A deterministic test creates more simultaneous calls than the approved cap, using barriers/events and an injected resolver that blocks. It observes exactly the approved maximum entering the resolver, proves the active count never exceeds that value, and proves every saturated call fails closed with zero HTTP sends. The test releases all fake resolvers in `finally` and joins the test-owned callers so it leaves no blocked fake thread behind.
4. A second assertion/test proves a timed-out caller does not release capacity while its resolver is still blocked. Once an underlying resolver exits, its slot becomes available again; a later loopback-only request can exercise recovery without external network.
5. Existing guard-identity, NEW-state, TLS hostname/certificate validation, deadline, independent-claim race, duplicate-after-SENT, and crash/restart tests continue to pass. No assertion is weakened and no new retry or SENT/UNKNOWN ledger transition is added.
6. Tests use fake resolvers and loopback HTTP only. No external network, provider, Modal/GPU, database, or migration operation occurs.

If these behaviors cannot be achieved using only the two implementation files, stop and request new scope. Do not weaken the 160-second total-deadline contract or create an unbounded queue to avoid the cap.

## Verification after approval

- Run the focused T6 module.
- Run the copied, network-blocking GA1 offline runner from a new snapshot directory with these explicit add-ons: `tests/unit/test_canvas_render_limits_ga1.py`, `tests/unit/test_pilot_vision_persistence_ga1.py`, and `tests/unit/test_invocation_guard_transport_ga1.py`. Preserve exact command, complete output, and exit code; the corrected baseline was 646 passed / 4 skipped, but report actual results.
- Run Ruff and mypy for the touched paths, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check`.
- Append a new evidence report and ledger entry and create a fresh snapshot. Stop at `XONG-CHƯA REVIEW` pending independent review. No stage, commit, push, or A2.

## Approval request

Owner: explicitly approve this exact plan SHA-256 and confirm the process-wide resolver-worker cap (recommended: 2). Approval must be recorded before any source or test edit. Until then, this file is planning only and implementation remains NOT AUTHORIZED.