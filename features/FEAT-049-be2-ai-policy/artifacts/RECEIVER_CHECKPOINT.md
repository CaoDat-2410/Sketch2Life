# BE2-14 receiver entrypoint — component handoff, full acceptance OPEN

2026-10-18. Code checkpoint c43d258 on feature/be2-08-14; use that code plus the
commit introducing this C6c handoff, or a reviewed later checkpoint. Check
`git rev-parse HEAD` and `git status --short`; no fetch/push/merge performed here.
Owner already defers real BE1/P4 wiring to teammates. This document is a handoff,
not their sign-off or permission to choose runtime policy/provider/credentials.

## Delivered component

- Eight-action policy lifecycle, separate capabilities/exact two-dimensional
  reviews, version/hash/CAS/receipt history and immutable original provenance.
- Own ai_policy PostgreSQL branch ap_0001–0009 and SQL stores for policy/effective
  scope, resources and copies. Code/offline evidence exists; actual BE2-14 SQL
  runtime is NOT_RUN. Do not borrow FEAT-048's earlier33 SQL passes.
- Single CMD-48 AI branch through bind_ai_policy and existing router factory,
  strict payloads/safe errors. No new default app or permissive identity fallback.
- Current-use phase/pin checks, policy epoch stop history and resource accounting
  composition. These are separate held guards, not an all-in-one dispatch grant.
- Copy inventory/purge fence, immutable original operation keys, bounded candidate
  discovery, guarded claim-before-hook delivery, exact receipt verification and
  atomic lifecycle/proof/outbox reconciliation. Missing hook truthfully unsupported.
- Redacted policy/resource/health/queue/copy projections, unknown/null vs measured0,
  explicit fixture provenance, expiry and no invented overall deletion/cost.
- Exact source-pinned local pack1061 own +114 foundation +477 regression,
  Ruff/Mypy64 policy source files and governance/security checks. New evidence
  must use current source hashes, not only this historical count.

Source prefix below: backend/src/sketch2life/. These are explicit integration
seams, not an automatically mounted production application.

| Workflow | Existing owned entrypoint | Missing real dependency / receiver obligation |
|---|---|---|
| Policy commands/CMD-48 | application/ai_policy_commands.py AiPolicyCommands; application/ai_policy_governance.py bind_ai_policy; existing build_governance_commands_router | PolicyCommandBoundary/PolicyRegistryAccess: verified scoped capabilities, current exact reviews/definitions and fences; verified server identity. Other CMD-48 delegates stay with their owners |
| Request/attempt provenance | application/ai_policy_use.py PolicyUseLeases.begin/continue_use | PolicyUseBoundary.decide_use: current consent/session/source/purpose/terminal facts; consumer persists original PolicyUsePin and rechecks dispatch/retry/completion/exposure. Do not substitute newest pin |
| Resource accounting | application/ai_policy_accounting.py; infrastructure/ai_policy/accounting_sql.py SqlResourceLedgerStore | ResourceAccountingBoundary.quote/verify_settlement: adopted units/window/ceilings and authenticated terminal evidence; reconcile cleanup does not authorize new work |
| Emergency stop | application/ai_policy_control.py AiPolicyEmergencyStop; own immutable scope_transition | Generation-safe foundation cancellation contract and actual delivery still NOT implemented/adopted. Read CR_KILL_NOTICE_PIN_FENCE.md before creating notices; broad job_type fallback is unsafe |
| Copy inventory/report | application/ai_policy_copy_inventory.py ProviderCopyInventoryService; infrastructure/ai_policy/copy_registry_sql.py SqlProviderCopyInventoryStore | CopyInventoryBoundary exact BE1 data-request subject/purpose/expiry/current authority and authenticated source/coverage. Report is metadata, BE1 retains request closure |
| Copy dispatch | application/ai_policy_copy_dispatch.py; ports/ai_policy_copy_dispatch.py CopyDispatchBoundary; ports/ai_policy_copy_hook.py ProviderCopyOperationHook | BE2-04/08 original-profile hook + stable operation_key external dedup; authoritative phase/retry checks. Same key/different body conflicts; timeout/crash retry never invents new effect key |
| Receipt reconciliation | application/ai_policy_copy_reconciliation.py ProviderCopyOperationReceiptVerifier; application/ai_policy_copy_resolution.py ProviderCopyReconciliationService | CopyOperationReceiptBoundary verifies real bytes/hash/issuer/action/copy/profile. Receipt_available/sent is not deleted; fixtures never actual. Durable current-authority/deadline fencing through commit still requires adoption |
| Operations | application/ai_policy_operations.py AiPolicyOperations; infrastructure/ai_policy/operations_sql.py SqlResourceOperationsReader | Independent operations-read guard, optional OperationsTelemetryReader with exact source profile; adopt safe aggregate/privacy/health/expiry meanings. Ledger is recorded units, not actual cost |

## What must still be implemented or proven

1. **SQL execution:** run all104 disposable-PG cases, inspect migration/rollback/
   concurrency/restart failures and fix in owner scope. No current BE2-14 PG PASS.
2. **Authority/registry adapters and consumer composition:** actual capability/
   review/source/consent/purpose/expiry and terminal fences; approved registry/profile/
   resource definitions; original request/attempt pin persistence. Missing policy
   values require owner decision, not guessed constants. Interfaces alone do not
   mean these adapters are done. BE1 owns core authority, integration owners wire.
3. **Generation-safe kill delivery:** foundation owner adopts exact original-generation
   semantics and bounded/idempotent cancellation proof; receiver then implements
   delivery/ack/recovery. Current epoch blocks new use only in consumers actually
   bound to it. Never claim every running job/provider stopped from intent commit.
4. **Provider/telemetry implementations:** provider-specific BE2-04/08 hooks and
   authenticated verifier, actual discovery completeness/external dedup, safe scoped
   telemetry producer. Preserve pending/unsupported/exception/fixture labels. P4
   wires producers; this does not transfer provider implementation to P4.
5. **Real integration acceptance:** consumer/provider restart/revocation/expiry/
   duplicate/late-response/no-resurrection and redaction conformance, actual
   receipts, required owner review and final AC01–12 evidence. Local component
   handoff is useful now but does not waive these steps.

These five groups include code/integration gaps, not merely five test commands or
five new backlog cards. Existing assignment/handoff governs who takes each; no
invented runtime approval/teammate agreement. Real BE1/P4 wiring is deferred per
owner instruction, not silently executed by this checkpoint.

## Test and evidence entrypoints

- CONSOLIDATED_TEST_HANDOFF.md: one local command and four actual-PG commands,
  exact counts/hash expectations, preconditions/effects and log-return checklist.
- ACCEPTANCE_AUDIT_20261018.md: AC01–12 source/proof/open gates; executor audit,
  not independent owner concurrence. C6b closes only local telemetry projection gap.
- C2_SQL_RUNTIME.md: authorized disposable PG17 only; creates/drops only generated
  per-case DBs. Does not start/install a service, adopt production migration or
  request credentials. Tests don't need GPU/Lightning. No provision authority inferred.
- H_OPERATIONS_TELEMETRY_HANDOFF.md, C3C3_ACCOUNTING_HANDOFF.md and C4C2_DELIVERY_STATE_HANDOFF.md:
  specific port/ordering semantics; dated earlier counts are historical.
- CR_PROVIDER_COPY_ADOPTION.md and CR_KILL_NOTICE_PIN_FENCE.md: open adoption
  requests. Source inspection/evidence is not approval to alter foundation.

No blanket live-provider command can be given before source/profile/owner adapters
are adopted. A Lightning GPU does not satisfy PG/identity/receipt/policy gates.
Never paste credentials/real child data into returned logs or commit runtime/model
outputs. Use exact checkpoint/logs, stop on first root failure, no blind rerun.

## Original BE2-12 and scope boundary

BE2-12 remains separately component-handoff available (FEAT-048 RECEIVER_CHECKPOINT),
with real owner integration deferred and full original goal NOT DONE. BE2-14 code
does not complete preset/core-policy delegates or all seven BE2-08–14 cards. Keep
original source/provenance, do not write foreign tables or change published
foundation contracts without adoption. No default app mount, dependency/model
install, provider choice, push/merge/deploy or full-card/goal-complete declaration.
