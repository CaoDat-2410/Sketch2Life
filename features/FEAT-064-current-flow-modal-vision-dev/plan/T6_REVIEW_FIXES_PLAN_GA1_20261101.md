# T6 independent-review fixes — GOAL A1

**Status:** Owner-authorized implementation plan; approval is appended separately.

## Authority and pinned inputs

- Owner V4: `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`, SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Goal A1: `.claude/handoff/CODEX_GOAL_G3G4_A1_20261101.md`, SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- Frozen T6 plan: `plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_GA1_20261101.md`, SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`.
- Review findings: `evidence/T6_INDEPENDENT_REVIEW_REPORT_GA1_20261101.md`.
- This plan is specific to the three T6 review findings and does not replace or edit the frozen T6 plan.

## Objective

Correct the guard/transport identity boundary, include DNS in the approved 160-second monotonic transport deadline, and make the competing-claim test synchronize at the claim boundary. Preserve the T6 single-request, durable-SENT-before-HTTP, no-retry, no-redirect, and TLS hostname-verification guarantees.

## Exact implementation scope

1. `backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py`
   - Require the wrapped V2 bridge to expose the exact same guard object used by the decorator before the decorator can be constructed.
   - Recheck that identity immediately before each inner call; refuse mismatches before invoking the bridge.
   - While state is `NEW`, pass through only an `ObservationFailed` with `provider_invoked=False`. Do not pass success and never rewrite an invoked outcome as not invoked. An unexpected NEW-state success/invoked result is rejected as an invariant violation; no terminal UNKNOWN is persisted from NEW.
2. `backend/src/sketch2life/infrastructure/vision_analysis/transport.py`
   - Expose the injected guard through a read-only identity property.
   - Resolve hostnames on a daemon resolver thread bounded by the remaining monotonic deadline; then connect using resolved addresses with remaining-time socket timeouts.
   - For HTTPS, use the `HTTPSConnection` default SSL context and the original URL hostname as `server_hostname`, with certificate and hostname checking enabled. Persist SENT only after DNS, TCP connect, and TLS handshake complete and before request bytes.
   - Permit resolver injection for deterministic tests; test resolution timeout with a blocked fake resolver and a loopback-only HTTP endpoint.
3. `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py`
   - Add only a read-only property that exposes the injected transport's guard identity; do not alter bridge behavior.
4. `backend/tests/unit/test_invocation_guard_transport_ga1.py`
   - Test mismatched or unguarded transport refusal before any HTTP send, matched-guard success, resolver deadline/fail-closed behavior, two independent workers synchronized at claim, an in-flight duplicate after SENT, and the existing crash/restart-after-SENT case as a separate test.

## Acceptance criteria

- A decorator cannot be built around an unguarded or differently guarded bridge. A runtime identity mismatch is refused before invoking the bridge; the loopback server observes zero sends.
- With a matched identity, successful V2 response handling remains unchanged and records one send and terminal success.
- When the guard is NEW, only local failures with `provider_invoked=False` pass through. Success and `provider_invoked=True` are not reclassified as no-send. No SENT or terminal UNKNOWN is written retroactively from NEW. If tests or inspection show a provider send can occur with guard state NEW despite the identity checks, stop and report the blocker; do not widen scope or claim completion.
- Resolver time is included in the same total monotonic deadline. A resolver that blocks past a short injected test deadline returns before any HTTP send, with a fail-closed non-invoked outcome and the durable claim unavailable for reuse. HTTPS continues to use the default verifying context and original hostname for SNI/hostname validation.
- The race test releases two independent attempts at a barrier located inside the shared ledger claim boundary, records exactly one successful claim, and observes no more than one HTTP request.
- The duplicate-after-SENT and restart-after-SENT tests remain separate and both prove zero extra sends.
- No files outside the implementation allowlist below are modified, except for the separately authorized task plan, append-only approval, new evidence report, append-only goal ledger entry, and one new ignored snapshot.

## Verification and evidence

- Run the focused T6 unit module and the same copied, offline GA1 regression runner used for snapshot `GA1_T6_20261101T205305`, with the updated T6 tests included. Record actual collected/passed/skipped/failed counts and exit codes.
- Run Ruff, mypy, `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check`; record actual verdicts.
- Do not run PostgreSQL/Alembic, Modal/GPU/provider calls, or external network. The DNS timeout test uses only an injected blocked resolver and a loopback server.
- Append a factual follow-up report and goal-ledger result, then create a new snapshot. Final status remains `XONG-CHƯA REVIEW` pending independent review.

## Allowlist and exclusions

Implementation files: the three named infrastructure files and `backend/tests/unit/test_invocation_guard_transport_ga1.py` only. Task records: this plan; one new append-only approval entry in `approvals/TASK_APPROVAL.md`; one new follow-up report in `evidence/`; one appended entry in `status/PILOT_GOAL_LEDGER_20261101.md`; and one new ignored GA1 snapshot.

Excluded: `ledger.py`, `tables.py`, all migrations/schema, application services, worker, route, composition, `ObservationRequest`, all other tests and source files, old plan/approval/report content, all unrelated working-tree changes, A2, PostgreSQL/Alembic, Modal/GPU/provider, external network, stage, commit, push, stash, reset, and destructive cleanup.
