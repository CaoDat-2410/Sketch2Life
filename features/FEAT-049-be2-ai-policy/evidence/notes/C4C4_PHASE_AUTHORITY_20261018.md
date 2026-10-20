# C4c4 — durable phase authority history / consumer handoff

2026-10-18 Asia/Saigon, feature/be2-08-14 parent48282b0. Previous goal turn made
progress with guarded dispatcher. Re-read original goal, current approval/context/
source register/plan and clean branch/HEAD. Later actual BE2-14 approval applies;
original BE2-12 goal/full card not completed. C4c4 subplan before implementation.

## Implemented and consuming safely

CopyDeliveryAuthorityEvidence binds actor/org/scope/original operation key, phase,
BEFORE delivery revision, current approved grant/deadline and observed time. Own
SqlProviderCopyRegistryTransaction.record_delivery_authority requires write UoW,
matching actor/scope and original operation; source snapshot is reconstructed from
immutable delivery history (rev0 derives queued only). Full phase digest/identity/
expiry revalidated and permitted pure transition must match current snapshot.

Own forward ap_0008 creates append-only copy_delivery_authority with scoped FK to
immutable operation and history trigger. No frozen migration/foundation changes.
Claim/completion proofs and events commit/roll back with corresponding mutation.
Dispatch proof writes in separate UPDATE UoW committed before hook, after exact
claim/right check. It is evidence of preparation, NOT actual transmission/ack.
No DB transaction held across hook; current guard/deadline checked afterwards as
before. Every custom transaction implementation must support this method, no
permissive/no-op fallback. Memory fixture records exact source delivery history.

For audit after restart: retrieve immutable operation, evidence and source state
revision; after-state is source revision+1 for claim/completion, same revision for
dispatch. validate_delivery_evidence checks exact historical grant and transitions.
Never pass a later current snapshot as that historical after-state or reuse any
old grant to dispatch. Actual live adapters must enforce current-owner/source/
profile/deadline/retry fences; opaque recorded revision is not adoption proof.

## Verification

- 19 new tests PASS: reconstruct three phases, wrong actor/org/scope/key/revision/
  phase/native grant, expiry/future observation and wrong after-state, phase insert
  rollback semantics, committed prehook proofs, SQL write binding/read-only/scope,
  frozen DDL and immutable trigger. No backend functional failures this turn.
- All own828 contract/unit PASS, zero failure/error/skip; raw ignored JUnit
  .runtime/be2-14-c4c4/component.xml. Nineteen known warnings: six offline Alembic
  deprecations and thirteen deliberately malformed-model serializer outputs.
- Selected source-pinned BE2-12/foundation477 regression PASS:
  .runtime/learning-content-component/20261017-173629-975454.
- Targeted foundation application/review-regression/q00:114 PASS/zero skip,
  .runtime/be2-14-c4c4/foundation.xml. Shared source remains unchanged.
- Actual PG collection15 lifecycle+10 activation+19 ledger+47 copy =91 prepared
  NOT_RUN. Three new actual cases and two strengthened composition assertions;
  no actual DB service/provisioning/provider calls.
- Focused Ruff/format11 files, Mypy5 source files, architecture/harness/security/
  whitespace PASS before commit. First multi-file patch failed context atomically
  with no edits; re-read fixture, corrected patch. Normal formatting/import fixes,
  no suppressed rule or reduced tests.

## Open acceptance

Pending filter, verified purge receipt/current-copy and typed cancel acknowledgment,
late-result/restart/provider dedup conformance, kill delivery, C5 safe composition/
projections, C6 review and actual SQL/owner/provider integration. No actual deletion,
cost, BE1 closure, production-ready/full-card/goal DONE or push/merge/deploy.
Authorized PG profile/commands/impact/report-return: artifacts/C2_SQL_RUNTIME.md.
