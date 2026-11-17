# C4c3 — current-authorized claim/dispatch/completion composition

2026-10-18 Asia/Saigon, feature/be2-08-14 parent2ac80d4. Previous goal checkpoint
made progress; original attached goal, actual later BE2-14 approval, context/source
register/plan and clean HEAD revalidated. No original goal completion claim or
new provider/provisioning approval. C4c3 plan recorded before code.

## Implemented / consumer handoff

ProviderCopyDispatcher.dispatch(actor, org, strict original command, operation_key,
expected_revision) requires explicit CopyDispatchBoundary and optional adopted
ProviderCopyOperationHook. No route/default live adapter is mounted. Read authorized
before lookup, immutable actor/org/command/key and original exact profile checked.
authorize_delivery binds full envelope/state/phase and actual worker/retry policy;
strict grant/deadline validated, explicit deadline cannot exceed grant. This output
comes from trusted backend only, never a caller field or inferred legacy config.

Claim commits under current guard with unchanged-authority confirmation. Dispatch
rechecks exact claim and current rights under SHARE, exits transaction then calls
hook. Owner guard stays held. Real adapter must pre-acquire fences before SQL;
confirmation cannot acquire new outer locks/network. Real remote-start and commit
deadline fences/adopted retry ceilings remain unproven by application clock checks.

Missing hook records Unsupported/HOOK_UNAVAILABLE. Hook exception or malformed/
wrong-key/body response records Exception with safe symbolic reason, no raw private
message. Reference-bearing output remains receipt_available, not authenticated
deletion/cancel acknowledgment. Completion requires unchanged current authority
and claim in own UPDATE UoW. Postclaim/prehook errors preserve claim without effect;
posthook revocation/expiry/stale state cannot fabricate external rollback/success.
Explicit current authorized retry keeps original provider key; no auto retry loop.

Memory fixture now implements actual pure delivery transitions transactionally,
with synthetic current clock. This is still MEMORY/ASSUMED, not production adoption.
Existing SQL state/history persists phases' state transitions, but actual phase
grant evidence is not yet stored as immutable authority history. Keep that open.

## Evidence

- 23 new dispatcher unit cases PASS: committed-before-hook/no-open-DB, phase denial,
  original profile/command binding, missing hook, private exceptions, malformed output,
  receipt reference, deadline bounds, stale revision/current retry, late result,
  posthook revocation and prehook commit failure. No backend functional failure.
- All own809 local tests PASS, zero failure/error/skip; ignored JUnit
  .runtime/be2-14-c4c3/component.xml. Existing18 known warnings retained.
- Selected BE2-12/foundation regression477 PASS, source-pinned receipt
  .runtime/learning-content-component/20261017-173048-559847.
- Targeted foundation114 PASS/zero skip, .runtime/be2-14-c4c3/foundation.xml.
- Lifecycle15+activation10+ledger19+copy44 =88 actual PG cases collected only,
  two new SQL composition cases prepared NOT_RUN; no server started/provisioned.
- Focused Ruff/format7 files, Mypy3 source files, architecture/harness/security and
  whitespace checked before commit. Formatting/import/line findings fixed normally.
  One Ruff ignored-cache write access warning did not affect checks; no rule disabled.

## Next and limits

Durable phase authority/source evidence, pending state query filter, verified purge
receipt and typed cancel acknowledgment/current-copy reconciliation, restart/late-
result/provider dedup adoption, kill delivery, C5 safe wiring/projections and C6
acceptance. SQL/real owner/provider NOT_RUN. No actual cancellation/deletion/cost,
BE1 closure, full-card/goal DONE, push/merge/deploy. C2_SQL_RUNTIME.md retains exact
profile/impact/commands/log-return instructions; provisioning authority not inferred.
