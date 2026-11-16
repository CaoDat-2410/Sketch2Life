# T7b — OwnerFenceV1 and acceptance unit of work

- Status: **BLOCKED before implementation**.
- Group: G3. Owner’s direct instruction in the goal prompt §E.3 overrides waiting for actual co-signatures; this does not mean anyone has signed. Do not record a signature.
- Parent: `plan/PLAN.md`, T7b; T0 contract freeze §8, execution manifest O08/O15/O16, method inventory.
- Database/provider: no DB transaction or provider call in this blocker-only task.

## Inventory and blocker

T0 describes the intended fence facts and says acceptance must re-read current source authority, eligibility and fence in one transaction, commit analysis/current pending pointer/reservation settlement atomically, and never hold a DB transaction across provider work. The owner’s instruction explicitly permits proceeding while role signatures remain `CHƯA KÝ`; therefore missing signatures are recorded as unsigned, not used as the blocker.

Implementation still depends on T7a’s durable repositories and a concrete cross-owner transaction boundary. T0 manifest O16 has no exact adapter/UoW path or schema ownership. The current T0 method list does not establish how BE1’s source/eligibility epoch is advanced atomically with BE2 acceptance without editing BE1-owned persistence/composition paths, which are outside the T7 B5.1 new-path directories. Implementing a fixture fence or a separate BE2-only lock would not meet atomic acceptance and is expressly insufficient.

## Owner questions

1. After T7a is frozen, what exact BE1-owned transaction hook or versioned source-fence publication makes source/eligibility updates atomic with the shared acceptance decision?
2. Which exact UoW/fence paths and methods are approved within the existing BE1/BE2 ownership boundary?
3. Can the BE2 schema owner and integration owner confirm the concrete `OwnerFenceV1` field/version contract while all signatures remain explicitly unsigned until review?

## Layers and acceptance

| Layer | Planned scope | Status |
|---|---|---|
| L1 contracts/domain | Versioned fence key and stale/conflict outcomes | BLOCKED: concrete owner boundary unresolved |
| L2 application | Atomic acceptance UoW protocol | BLOCKED: requires T7a and BE1 transaction hook |
| L3 persistence/migration | Reuse T7a-owned state only; no second guessed schema | BLOCKED by T7a |
| L4 adapters | Runtime owner-fence adapter; never use fixture fence | BLOCKED by T7a and transaction-boundary question |
| L5 HTTP | No new route in T7b | NOT RUN |
| L6 UI | DEFERRED-BY-OWNER | DEFERRED |
| L7 integration | Race/stale-source acceptance test | BLOCKED by L2–L4 |

## Allowlist and exclusions

Candidate new-path boundary only: `backend/src/sketch2life/infrastructure/assistance/**` and `backend/src/sketch2life/infrastructure/vision_analysis/**`; tests only after T7a/fence path is frozen. For this blocker-only disposition, the actual write allowlist is only this plan, the G3 blocker report, the append-only FEAT-064 approval entry, and the goal ledger.

No fixture fence was wired to runtime, and no OwnerFence signature is claimed.
