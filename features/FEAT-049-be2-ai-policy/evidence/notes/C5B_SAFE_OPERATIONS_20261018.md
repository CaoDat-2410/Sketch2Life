# C5b — current-authorized safe operations / consumer handoff

2026-10-18 Asia/Saigon, feature/be2-08-14 parentf00f515. Previous continuation
made concrete progress/commit. Re-read original pasted goal, clean current branch/
HEAD, AGENTS/context/source register, actual BE2-14 approval and current feature
status/context. Approved revision1 P2/P5/AC11 governs this increment; original
BE2-12 goal not redefined or declared complete. C5 operations subplan before code.

## Implemented and field rationale

AiPolicyOperations.read(actor, org, strict PolicyOperationsRequest) requires
current OPERATIONS_READ before storage, keeps registry/identity guard through own
policy read UoW and rechecks rights before result. No author/publish/role shortcut.
Registry feature withdrawal does not hide authorized stopped metadata. Read exact
scope org/feature/epoch and pin/version/hash/feature/state, validate body hash but
never return body/title/author/reason/review/prompt/media/source/request/attempt/
receipt/secret/provider URL. Public fields are strict allowlist, not dictionary
copy/redaction after serializing private records.

- scope null: no stored effective scope, not enabled or disabled permission.
- epoch/disabled/policy_ref/policy_state: stored activation metadata, not current
  registry approval, new-use entitlement or worker/provider stop confirmation.
- optional budget_window: caller filter for exact historical definition/unit/window,
  no numeric limits/default windows and no claim of current policy adoption.
- ledger occupied_slots: stored global org/feature count; missing reader/scope null.
- bucket_available/recorded_held_units/recorded_spent_units: exact stored bucket;
  unavailable bucket null, actual stored zero preserved. Do not aggregate units or
  windows, infer completeness or re-label fixture-inclusive spend as real cost.
- accounting_semantics fixed recorded_ledger_not_actual_cost; actual_cost null
  only. No actual provider billing/usage definition/adoption supplied here.

SqlResourceOperationsReader reads existing own tables under scope SHARE then exact
bucket SHARE; no INSERT, migration or foreign-owner/job-table access. Missing scope
returns immediately to avoid mixing later phantom bucket. Original key canonical
comparison distinguishes bool from integer and rejects changed window/definition.
Strict native snapshot revalidation catches bad counters/response binding; denial/
malformed data/private dependency failures never become zero success. Reader and
policy snapshot have local read semantics, not distributed atomic execution proof.

## Verification

- 34 new local cases PASS: missing/zero/read-only behavior; exact active/stopped
  metadata with withdrawn registry; capability/cross-org denial before storage;
  final revocation; wrong/native malformed ledger binding/counters; scope/pin/hash/
  bool mismatch; DTO absence/pairing/strictness; no money/private fields; SQL exact
  scope/bucket SHARE-only shape/absence/changed key; private exceptions sanitized.
- Own980 unit/contract PASS, zero fail/error/skip:
  ignored .runtime/be2-14-c5b/component.xml. 22 known warnings: six Alembic offline
  deprecations and sixteen intentionally malformed-model serializer warnings.
- Selected source-pinned regression477 PASS:
  .runtime/learning-content-component/20261017-180402-733403.
- Targeted foundation114 PASS: .runtime/be2-14-c5b/foundation.xml.
- Focused Ruff8 Python files/Mypy4 source files and architecture/harness/security/
  whitespace checks PASS before commit. Initial long-line check corrected by normal
  formatting; no functional failing test or warning suppression in this increment.
- Actual PG101 collected, NOT_RUN: lifecycle15 +activation10 +accounting21 +copies55.
  Two new reader cases check no row creation, reconnect/fixture recorded counters,
  org/feature/window isolation and no read-side mutation. No server/actual provider.

## Consumer composition and remaining gates

Inject AiPolicyOperations(policy_store, policy_registry_boundary,
SqlResourceOperationsReader(approved_engine)) into the owning backend/gateway
application, not a new route or default app mount. Verified actor/org context is
server-supplied. Independent operations rights required; monitor is not lifecycle
execution, accounting reservation or content/child access. No default identity,
approved window/limit or fake provider cost supplied. Without ledger adapter,
projection truthfully unavailable; configured reader failure is an error, not an
empty valid report. Use strict request with feature_scope and optionally exact
BudgetWindowRef; no arbitrary JSON queries or caller numeric limits.

Batch external SQL runner command/preconditions/impact/artifacts remain in
artifacts/C2_SQL_RUNTIME.md, using commit containing this note; --accounting exact21
identities, all four packs101. No need for piecemeal user test now. Real BE1/P4
adoption deferred to teammates; stop-generation CR remains open, actual provider/
SQL/runtime authority not proven. Safe copy projection/conformance and C6 review
remain local work. No full card/goal DONE, push/merge/deploy/provider activation.
