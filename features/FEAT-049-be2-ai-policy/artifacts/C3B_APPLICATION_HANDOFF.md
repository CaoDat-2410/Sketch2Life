# BE2-14 C3b application / effective-pin handoff

AiPolicyCommands.execute(principal_id, organization_id, AiPolicyCommand,
expected_revision=...) implements all eight actions and returns existing typed
DelegateResult. Identity is supplied by trusted composition, never body role claims.
Current PolicyCommandBoundary supplies registry rights, review governance version
and review_effective for existing AND newly proposed local proofs. Unknown/revoked
decisions must fail closed. No production boundary/default adapter is supplied.

Lock order: entered owner/registry guard -> exact own feature scope -> own record.
One store transaction covers lifecycle/review/event/outbox/effective-scope transition/
receipt. Publish updates one org/feature pin and epoch; recall/archive disables
only that exact active pin. An older version/record retirement must not disable a
replacement. Published historical versions/requests are not silently rewritten.
Edit cannot move a record to another feature; new scope needs a separate record.

No default application route mounted. Positive tests bind the real handler through
existing StrictDelegateBinding; C5 still must translate the closed AI_POLICY error
catalogue into safe public HTTP outcomes and complete authorized composition.
Do not let PolicyError become a raw exception body or borrow content permissions.

## Replay / failure

Key is org/principal/client_request_id; fingerprint includes full validated command
and record precondition. Same key/different body conflicts. Replays recheck current
rights/definitions/proof effectiveness; publication replay cannot re-enable retired
or disabled content. Receipt carries recorded metadata plus current revision/state,
not an activation/usage grant. Integrity conflict rolls back whole candidate, then
at most one fresh receipt read; no blind write retry. Nonexistent winner still fails.

Negative review and retirement remain available when a definition is withdrawn.
Create/edit/submit/positive-review/publication require exact adopted definitions.
Unknown target/version/hash, self-review/publish or stale record/review are denied.

## Scope transition intent, not a cancellation receipt

Forward migration ap_0002 adds effective_scope + scope_transition. Scope event
stores org/feature/epoch/exact record/version/hash/disabled/reason and is immutable
except delivery marker. Pending intent does not prove worker/provider stopped.
It does not authorize a wildcard cancellation of a newer pin: later delivery must
revalidate epoch/exact target and preserve source history. Foundation cancellation
adapter mapping and bounded operations policy remain to implement/adopt.

Epoch0/null pin is unusable even with disabled=false. Runtime code must never treat
that boolean alone, a validation receipt or a cached event as permission to run AI.
Emergency stop before publication is now supplied separately by AiPolicyEmergencyStop
with strict backend-only EmergencyStopCommand. It requires current DISABLE, exact
scope epoch and reason, atomically records stop intent/receipt, and rejects stale
replay after reactivation. No endpoint or CMD-48 ninth action is added. Atomic
budget/concurrency remain later C3c work. Current-work policy eligibility now has
PolicyUseLeases.begin / continue_use: exact selected profile, immutable request
context and original policy pin; held current owner guard plus feature SHARE lock.
Continuation checks exact activation history and any intervening stop. A snapshot
outside lease is metadata, not permission. No real owner adapter or atomic budget
reservation is supplied by this check. Consumer must persist original pin and
commit nested work under adopted guard; never use a returned pin as a bearer token.

## Verification status

Latest 617 own component cases PASS +477 existing selected regression PASS. Components use
assumed boundary and transactional MEMORY store; not durable SQL/fence proof.
Actual PostgreSQL 15 lifecycle +10 activation/stop/use +19 ledger +21 copy inventory
cases prepared, NOT_RUN.
Runtime command pack: artifacts/C2_SQL_RUNTIME.md. No real provider/owner integration,
cost/load/purge/cancellation proof. Full-card BE2-14 remains IN_PROGRESS.

## Accounting contract checkpoint (C3c3a)

ResourceReservationRequest binds exact original request/pin/attempt and phase.
ResourceSettlementRequest accepts an evidence reference, not actual units or a
client verified flag. ResourceAccountingBoundary must resolve current adopted
quote values and authenticate terminal evidence while retaining guards to commit.
bind_resource_quote checks exact current observation/actor/org/attempt and maps
original policy/request provenance to immutable domain accounting terms. A bound
quote is not an authorization token and this mapper does not reserve anything.

Pure domain reserve/settle transitions cover per-bucket held/spent, global scope
slots, exact replay, verified release, actual overrun and original-window cleanup.
No automatic expiry/cancellation refund, numeric production default or provider
receipt verifier supplied. C3c3b must still implement own atomic SQL ledger/UoW,
services/receipt+outbox and actual concurrent/restart/rollback verification. Do not
dispatch work using the pure transition or treat fixture evidence as actual cost.

## Ledger persistence checkpoint (C3c3b)

SqlResourceLedgerStore now supplies own UoW with global org/feature serialization,
per-budget-bucket counters, exact reservation/attempt identity and scoped command
receipts. Reserve and settle compute domain transitions and persist counters,
reservation and pending resource_event in the same database transaction; add_receipt
joins that UoW. Replays produce no delta/event. Forward ap_0003 protects immutable
terms/terminal states/history; no old migration changed. Resource events are both
audit and pending outbox intent, not completed delivery/provider receipts.

This completes persistence code, NOT actual SQL verification. C3c3c now supplies
ResourceAccountingService with held current-use/quote/proof guards, safe command
replay and after-stop cleanup without reauthorizing AI. Real owner/evidence guard
adapters remain unbound; see artifacts/C3C3_ACCOUNTING_HANDOFF.md. Never acquire owner
policy locks from inside ledger lock or run provider network work under that lock.
No route/default adapter mounted. AC06 and full BE2-14 remain open.

## Copy verification checkpoint (C4a)

ProviderCopyReceiptVerifier now supplies held current owner/profile/evidence
verification bridge to existing foundation PurgeReceipt; foundation lifecycle
and shared models unchanged. It does not dispatch, persist registry results or
prove actual deletion. See artifacts/C4_COPY_VERIFICATION_HANDOFF.md and open
artifacts/CR_PROVIDER_COPY_ADOPTION.md for missing coverage/registry/acknowledgment
and exact immutable profile/operation/commit-fence requirements. C4b remains open.

C4b1 now adds own scoped inventory port/SQL/ap_0004 with immutable original profile,
monotonic scope purge fence, late initial quarantine, revision-bound pages and
scoped coverage reports. See artifacts/C4B1_COPY_INVENTORY_HANDOFF.md. These are
inventory/initial metadata, NOT current lifecycle/dispatch or provider completeness.
Current-owner service/operation intent orchestration remains C4b2; CR remains OPEN.

C4b2a now supplies ProviderCopyInventoryService with current action-specific
authority/source proof validation and precommit confirmation over own registry.
See artifacts/C4B2A_INVENTORY_SERVICE_HANDOFF.md. No production owner/source adapter
or durable operation/evidence history supplied yet; CR remains OPEN, C4b2b/C4c open.
