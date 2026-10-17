# C4c5 — bounded candidate discovery / consumer handoff

2026-10-18 Asia/Saigon, feature/be2-08-14 parentc99384a. Prior goal turn made
progress via phase history. Re-read original attached goal/current branch/clean
HEAD, actual later BE2-14 approval/context/source register/plan. C4c5 subplan before
code; original BE2-12 goal not completed/redefined, frozen approval unchanged.

## Implementation and use

ProviderCopyRegistryTransaction.delivery_candidates(CopyCandidateRequest) returns
CopyCandidatePage(revision, as_of, operation_keys, next_cursor). Caller holds
adopted current owner read guard before own scope SHARE UoW. Internal, no default
adapter/public endpoint/worker mounted. No schema/migration or foundation edit.

Request limit native integer1..256. First page supplies aware as_of; continuation
supplies only CopyCandidateCursor(org/scope/revision/as_of/SHA256 after-key). Bad
native DTO/cursor, cross-scope or stale revision fails before SQL. Explicit cursor
pins cutoff instead of replacing it on each page. Internal cursor is unsigned
metadata, NOT a public bearer capability or permission. Missing scope returns
rev0/empty without a query that could mix later inserted candidates.

SQL joins org/scope/key to own current delivery state, filters queued/no state,
pending/exception and in-flight claim expiry <=cutoff, orders by key and limit+1.
No unbounded Python materialization or caller expression. Unsupported and
receipt_available excluded, as are unexpired claims at cutoff. JSON deadline uses
typed PostgreSQL timestamp cast; invalid persisted timestamp may fail through
sanitized storage-unavailable outcome, never fallback grant or guessed expiry.

Candidate is only scheduling metadata. It does not prove current eligibility,
retry ceiling, source validity, actual expiry now, deletion or provider-wide
completeness. Future cutoff does not authorize early takeover: dispatcher uses
actual current policy/clock/guard and revision CAS. Any mutation invalidates old
scan; restart from first page with fresh cutoff, not skip/reconstruct a cursor.
Existing operation_page remains ALL-intent history and is not silently filtered.

## Verification

- 18 new offline request/cursor/query shape cases PASS: scope/cutoff/status SQL
  binds, bounded join/ordering, continuation, native/aware/limit/extra-field
  rejection, cross-scope/stale cursor, missing-scope no-phantom, invalid DB keys.
- All own846 unit/contract PASS, zero failure/error/skip; raw ignored JUnit
  .runtime/be2-14-c4c5/component.xml. Nineteen existing known warnings retained.
- Selected source-pinned BE2-12/foundation477 PASS:
  .runtime/learning-content-component/20261017-174018-010135.
- Targeted foundation114 PASS/zero skip, .runtime/be2-14-c4c5/foundation.xml.
- Actual PG collection lifecycle15+activation10+ledger19+copy49 =93 prepared
  NOT_RUN. Two actual query/membership/reconnect/scan cases added, not executed.
- Focused Ruff/format5 files, Mypy3 source files, architecture/harness/security
  and whitespace PASS before commit. Normal import/line/format findings fixed;
  transient ignored Ruff cache access warning, final no-cache lint PASS.
  No backend functional failures or suppressed rules.

## Open

Verified purge receipt and typed cancel acknowledgment/current-copy reconciliation,
late-result/restart/provider dedup conformance, kill delivery, C5 safe bindings/
projections, C6 acceptance and actual SQL/current-owner/provider integration.
No actual provider cancellation/deletion/cost, BE1 closure, full-card/goal DONE,
server install/start, push/merge/deploy. Approved-profile commands/preconditions/
impact/log return remain artifacts/C2_SQL_RUNTIME.md; no new authority inferred.
