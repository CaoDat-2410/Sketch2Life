# BE2-14 cross-lane video policy scope addendum

- Status: DRAFT / AWAITING_OWNER_APPROVAL
- Card: FEAT-049 / BE2-14, policy-use and accounting ownership
- Addendum to: plan/PLAN.md revision 1; frozen plan remains unchanged
- Integration design: FEAT-057 plan revision 4, SHA256
  6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Proposed scope SHA256: fill after final review, before approval

## Purpose and approval boundary

BE2-14 has offline current-use and accounting components, but its status says real
owner/provider bindings, worker authorization, and atomic budget/concurrency
implementation remain open. This addendum proposes the BE2-14-owned policy boundary
needed by the BE2-08 video path. It does not activate a provider, certify production
policy, or delegate BE2-14 implementation ownership to BE2-08.

## Proposed implementation scope

1. Define the exact BE2-08 request identity and phase mapping to the versioned
   BE2-14 policy-use contract. At minimum distinguish create, dispatch/retry,
   completion/finalization, and exposure where applicable. Pin request ID/revision,
   input hash, purpose, feature scope, profile, policy reference, activation epoch
   and registry revision.
2. Hold current-use, review, registry and kill/disable eligibility through each
   enclosing BE2-08 commit that relies on it. Snapshot-only checks cannot be described
   as revocation fences.
3. Keep three decisions separate:
   - current-use eligibility and policy/kill state;
   - worker/provider execution authorization;
   - budget/concurrency reservation, settlement and retry accounting.
   An allowed PolicyUseDecision is not a provider grant or a budget reservation.
4. Define reservation semantics for the BE2-08 generation attempt: idempotent
   reservation identity, concurrency slot, budget amount/unit, expiry/renewal,
   settlement on success/failure/cancel, and safe behavior after lost acknowledgement.
   If the existing policy accounting contract cannot express these terms, record a
   versioned contract change request before implementation.
5. Fail closed on missing, expired, unknown, conflicting or unavailable policy,
   authorization or reservation state. Do not enable a real provider from fixture
   data or local-only bindings.

## Candidate allowed files

- Modify only for the agreed policy-use mapping:
  backend/src/sketch2life/contracts/schemas/ai_policy_use.py
  backend/src/sketch2life/application/ports/ai_policy_use.py
  backend/src/sketch2life/application/ai_policy_use.py
- Modify only if the approved reservation contract requires it:
  backend/src/sketch2life/contracts/schemas/ai_policy_accounting.py
  backend/src/sketch2life/application/ports/ai_policy_accounting.py
  backend/src/sketch2life/application/ai_policy_accounting.py
  backend/src/sketch2life/infrastructure/ai_policy/accounting_sql.py
- Card-owned tests:
  backend/tests/unit/test_ai_policy_use.py
  backend/tests/unit/test_ai_policy_accounting.py
  backend/tests/unit/test_ai_policy_accounting_service.py
  backend/tests/contract/test_ai_policy_accounting_contracts.py
- Excludes BE2-08 call sites, BE2-01 job schema/dispatch worker, BE2-07 source tables,
  provider credentials/adapters, BE1 policy core, and FEAT-057 composition tests.

This candidate list is not authority to edit every path. Approval freezes the minimal
manifest after the contract review. No migration is included. If the adopted policy
contract requires a schema change, prepare a schema-specific revision and approval.

## Acceptance criteria

| ID | Required result |
|---|---|
| P01 | Exact BE2-08 request/policy identity is validated from authoritative stored facts; callers cannot supply an allowed flag or substitute a pin. |
| P02 | Current-use eligibility is fenced through the consumer commit where required; kill, recall, expired consent, stale request or policy revision blocks use. |
| P03 | Worker/provider authorization is a separate explicit decision and fails closed when no adopted authority is bound. |
| P04 | Budget/concurrency reservation and settlement are separate from eligibility; duplicate/lost-ack/late settlement has a documented single-winner rule. |
| P05 | Create, dispatch/retry and completion gates use an approved phase mapping; a decision at one phase cannot authorize another phase. |
| P06 | Denial/unavailable authority at create or dispatch prevents generation dispatch; denial at completion prevents acceptance/finalization. No phase reports false reservation success, and evidence records the exact phase and outcome. |
| P07 | Existing BE2-14 offline and owned SQL suites remain green; local fixtures are not reported as real owner/provider adoption. |
| P08 | No provider activation, credential, runtime, BE2-08 source edit, or status/acceptance change is included. |

## Dependencies and stop conditions

- BE2-08 must approve the consumer call points and stable request/run mapping.
- BE2-01 must approve which persisted foundation identity is authoritative for dispatch.
- CR08-01 must define the transaction owner and whether reservation shares or precedes
  submission/finalization; policy cannot claim atomicity across an unowned UoW.
- If worker authorization or accounting requires an external owner contract, retain
  the gate as OPEN/BLOCKED and do not bypass it with a fixture adapter.

## Proposed implementation sequence

1. Review request identity and map each BE2-08 phase to a distinct policy-use phase.
2. Decide whether current contract fields cover execution authorization and accounting;
   if not, draft and review versioned CRs.
3. Freeze policy-owned file/schema manifest and obtain approval.
4. Implement policy-side decisions/reservations and race/replay tests.
5. Have BE2-08 integrate the consumer calls in its own approved files; run the complete
   offline cross-card composition only after both sides are ready.
6. Keep provider/runtime activation deferred under its separate environment approval.

## Approval state

No implementation approval is recorded. Existing BE2-14 revision 1 and isolated SQL
approvals do not authorize this cross-card policy binding.
