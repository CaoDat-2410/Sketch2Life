# C4b1 — original copy inventory / revision pages / scope purge fence

2026-10-17 Asia/Saigon, feature/be2-08-14 parent 7f38760. Approved P4/P5;
plan/C4_COPY_LIFECYCLE.md updated before code. Previous goal turn committed C4a:
progress. Original attached goal read again; later direct BE2-14 approval governs
current work, not completion/redefinition of BE2-12 or new provisioning authority.

## Implemented

Own scoped port/DTOs and PostgreSQL adapter with four-table metadata/forward
ap_0004. Exact immutable original copy kind/id/org/scope/profile ref/version/hash,
initial late-registration quarantine. Duplicate exact registration no-op; changed
provenance rejected. Monotonic scope purge fence and revision-CAS, audit/outbox
same UoW. No new lifecycle or foundation/shared bytes rewritten. initial_copy
reuses foundation request_purge only for original registration metadata.

Scope SHARE read/keyset pages bind expected revision; any intervening mutation
invalidates old cursor. Missing scope observation freezes empty revision0 without
querying rows inserted afterwards. Coverage is scope-bound source-attestation
metadata with explicit required/observed sources and CAS; new registration/fence
invalidates prior observation. reported_complete is declared-source report, not
provider-wide discovery/deletion or BE1 closure. No real authority/default adapter.

## Evidence

- 27 new offline/codec/page-shape/native-input checks +2 runner cases PASS;
  own component 561 PASS /zero skipped, ignored JUnit
  .runtime/be2-14-c4b1/component.xml. All 15 own contract/unit suites executed with
  cwd backend, existing venv/pytest -o addopts=, -q --tb=short.
- Ten warnings: six existing Alembic offline path_separator deprecations and four
  intentional malformed native-model serializer warnings. No skipped runtime PASS.
- 19 actual copy inventory PG cases collected; total all PG inventory63. Exact
  optional --copies runner/JUnit/source hash gate, missing opt-in returns NOT_RUN.
  Actual execution remains NOT_RUN, no server provision/start/download.
- Focused Ruff PASS on eight touched/new source/test/migration/env files; format
  PASS on seven, Mypy PASS on four source files. Architecture/harness/security/
  whitespace PASS. Existing source-pinned 477-case pack PASS, ignored receipt
  .runtime/learning-content-component/20261017-164203-873038. Targeted foundation
  application/review-regressions/q00 suites also rerun: 114 PASS.

First Mypy required broad RowMapping-compatible key typing in decoder; corrected
without ignores. Formatting/import/line-length issues corrected without lint rule
suppression. Self-review added missing-row phantom prevention, explicit org/scope
coverage binding and clock validation/audit advance before immutable registration
insert. Controlled connection tests prove call ordering only, not DB atomicity.

Prepared actual PG cases cover reconnect (not process restart), exact duplicate,
three original provenance conflicts, rollback, stable/stale pages, coverage
invalidation/stale/cross-scope, purge-registration race/late quarantine, concurrent
duplicate, five raw SQL immutability/unpurge checks, scope/read-only isolation and
absent-reader/later-insert snapshot. Schema/API impact/commands/log return:
artifacts/C2_SQL_RUNTIME.md. No source/receipt/profile values adopted for production.

## Remaining

C4b2 current-owner registration/discovery/coverage service and durable exact
operation intents; C4c typed hook dispatch/acknowledgment, immutable verified
receipt application/current copy lifecycle and expiry commit fence. Real source/
provider/foundation CR adoption and BE1/P4 wiring separate; C5 safe projections/
bindings, actual PG proof and consolidated acceptance remain open. Registry event
intent is not completed delivery/cancel/purge. No actual provider call/deletion,
overall request closure, full card/goal DONE, dependency install, push/merge/deploy.
