# C3c3c — guarded accounting application service

2026-10-17 Asia/Saigon, feature/be2-08-14 parent 74c89fa. Approved P3, matrix
plan/C3C3_ACCOUNTING.md. Previous turn committed persistence/tests: progress.
Old attached BE2-12 goal read before continuing; later direct BE2-14 approval
authorizes current card, not a claim that the original full goal is complete.

## Implemented

ResourceAccountingService reserve validates strict native request and actor/org,
holds current-use lease with exact supplied original pin, current authoritative
accounting quote guard and own ledger UoW. Stable original-pin/request/attempt id,
full command-scoped receipt fingerprint. Same/new client key cannot double hold;
replay still checks current use/quote/rights and cannot migrate terms or resume
terminal reservations. No default provider values or route/dispatcher action added.

Settle checks explicit backend feature scope, current accounting authority, exact
original reservation and reference-only terminal evidence. Rebuild nested native
proof/key dataclasses before accepting quantity/verified/outcome; reject coercions.
Consume/release require matching disposition, reconcile accepts either verified
terminal outcome. Receipt/evidence replay has no second charge/refund. Corrupt
receipt claiming settlement without committed terminal reservation fails closed.

Cleanup after stop can finish original ledger under accounting rights, never calls
use lease or creates dispatch permission. Own ledger receipt/counters/reservation/
audit commit together. An outer guard failure after commit reports safe uncertain
dependency outcome, not invented rollback/refund; exact retry inspects prior receipt.
Guard must pre-acquire owner fences; no outer lock/provider network under ledger.

## Checks and evidence

- 49 new service cases PASS. Actual use component with explicit ASSUMED accounting
  boundary and transactional MEMORY ledger; not current-owner/runtime proof.
- All 13 own contract/unit suites: 488 PASS /zero skipped. Raw ignored JUnit:
  .runtime/be2-14-c3c3c/component.xml. Command uses cwd backend, pytest -o addopts=,
  all test_ai_policy contract/unit suites, -q --tb=short.
- Focused Ruff/format checks PASS on five touched/new source/test files; Mypy PASS
  on two application/port files. Architecture, harness, security and whitespace
  checks PASS. Existing source-pinned 477-case regression pack PASS separately;
  ignored receipt .runtime/learning-content-component/20261017-162014-229116.
  No actual PostgreSQL executed.
- All actual SQL inventories collected: 15 lifecycle +10 activation/stop/use +19
  ledger =44. Two new ledger cases compose actual SQL policy/current-use/ledger
  service and after-stop reconciliation with ASSUMED external boundaries, NOT_RUN.
  Runner source pins now include new assumed accounting fixture dependency.

First service run: 38 PASS/one FAIL because the new test called stop() rather than
existing execute(); corrected test invocation without changing production stop API.
Ruff import/format/lambda issues corrected without rule suppression. Existing four
Alembic deprecation warnings and one intentional malformed allowed=1 serializer
warning remain; not skipped execution or actual SQL PASS.

Additional self-review added native nested-proof validation tests, corrupt receipt
rollback and guard-exit-after-commit replay behavior, not a claimed distributed UoW.
Current server cap/overrun checks use synthetic values/evidence. Fixture actual
usage flag remains false, not actual provider cost or production billing authority.

## Remaining

Actual PostgreSQL execution/current-owner fences/real quote and terminal receipt
adoption remain open. Runtime requires separately authorized profile, not silence
or inherited BE2-12 provisioning permission. C4 ProviderCopyLifecycle, stop-intent
delivery/real worker acknowledgments, C5 safe composition/redacted projections and
consolidated full-card acceptance also remain. No provider/owner default adapter,
install/server start, push/merge/deploy, or full BE2-14/goal-complete claim.
API/failure obligations: artifacts/C3C3_ACCOUNTING_HANDOFF.md.
