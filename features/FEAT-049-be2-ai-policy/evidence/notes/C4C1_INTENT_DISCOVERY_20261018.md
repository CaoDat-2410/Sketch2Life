# C4c1 — revision-bound internal intent discovery

2026-10-18 Asia/Saigon, feature/be2-08-14, parent c3a1423. Previous goal turn
made progress via exact operation intent checkpoint. Re-read original goal and
actual later BE2-14 approval, current context/plan/source register and clean HEAD.
Original BE2-12 goal remains uncompleted; later approval governs BE2-14 work.
C4c1 subplan recorded before code. No schema/foundation/shared contract changes.

## Implemented and consumer boundary

ProviderCopyRegistryTransaction.operation_page(limit, after, expected_revision)
returns CopyOperationPage(revision, operation_keys, next_after). Internal SQL
query is scoped org/scope, sorted SHA256 keys, limit+1. Limit1..256/native integer,
strict digest continuation and expected revision required; stale scope fails.
Missing scope returns rev0/empty with no post-absence query. Malformed/duplicate/
out-of-order/out-of-cursor DB keys fail closed. New intent invalidates old page;
no write/claim/delivery flag is applied by reading. No public route/default adapter.

IMPORTANT: This enumerates ALL stored intents, not pending/eligible work. State
and claim protocol remain unimplemented. Consumers hold adopted current owner read
guard outside own SHARE UoW, then use returned keys only for historical lookup.
Recheck current actor/org/original command/profile/expiry before future dispatch;
an enumeration result or old envelope is never permission or a claim. No provider
network under scope locks. No fresh completeness/deletion or overall BE1 closure.

## Evidence

- 19 new offline query/validation cases PASS, including scoped SQL binds, empty/
  final/continued page, strict limits/revision/digest, malformed persisted keys.
- 708 own contract/unit PASS, 0 fail/error/skip; ignored raw JUnit
  .runtime/be2-14-c4c1/component.xml. Existing eighteen known warnings unchanged.
- 477 source-pinned selected BE2-12/foundation regression PASS:
  .runtime/learning-content-component/20261017-171947-994156.
- Targeted foundation application/review-regression/q00:114 PASS, no skip;
  .runtime/be2-14-c4c1/foundation.xml.
- Two new actual SQL discovery cases collected. Inventory lifecycle15 +activation10
  +ledger19 +copy36 =80 prepared NOT_RUN, no PG server started/provisioned.
- Focused Ruff/format, Mypy(two changed source files), architecture, harness,
  security and whitespace PASS. Initial missing tuple annotation, long lines and
  nested-context lint fixed normally without suppression. No backend test failure.

## Remaining

Delivery state/pending filter/claim, typed hook dispatch and acknowledgment,
verified receipt/current copy lifecycle, crash/late-result handling, kill delivery,
C5 safe bindings/projections, C6 consolidated acceptance and separately adopted
real owner/provider/SQL runtime. Full card/goal NOT DONE; no provider call, actual
cancel/deletion, push/merge/deploy. Existing PG command/preconditions/report-return
remain artifacts/C2_SQL_RUNTIME.md; no provisioning permission inferred.
