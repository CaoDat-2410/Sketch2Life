# T2B: implemented design vs owner decision record `9f337aff` — divergence note (2026-11-01)

Status: **RESOLVED by the owner's direct instruction, using decision record `9f337aff` as the T2B authority.**

## Resolution applied

The owner directed this rework to follow the unchanged decision record at `9f337aff`. T2B now uses persisted `age_revision` and `age_source` columns with the pinned three-value enum and migration `20261101_be1_age_0001`; the context digest is a separate versioned `sha256:<64 lowercase hex>` field beside the compatibility integer. The rework does not add an age-edit route, does not add a digest to the public Vision claim or AI Jobs contract, and keeps the integer-only provider boundary fail-closed. The PostgreSQL `BE1FactSource` adapter and an end-to-end synthetic Vision request remain NOT DONE; A4/A5 and T3 implementation remain deferred.

This status records reconciliation of the prior implementation divergence. It is not evidence of provider execution, production readiness, or completion of the deferred work.

## Prior divergence before rework

The following table preserves the earlier discrepancy for audit history; it does not describe the current reworked implementation.

The owner decision record `evidence/OWNER_DECISIONS_T2B_T3_20261101.md` (commit `9f337aff`, kept unchanged) and its plans `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md` / `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_20261101.md` were written before the T2B code existed on the branch (the record states T2B is `NOT_STARTED`). The T2B code and plan that were implemented earlier the same day are kept under new names so that the pinned hashes of the record stay valid:

- implemented T2B plan: `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md`
- first T3 draft: `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_DRAFT1_20261101.md`; T3 decision plan REV2: `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_REV2_20261101.md`

| Item | Owner decision record (`9f337aff`) | Implemented in this branch |
|---|---|---|
| A1 | Add `age_revision` and `age_source` columns (default revision 1, unknown history = `LEGACY_UNKNOWN`) | `age_revision` is the constant 1 with provenance `be1-profile-age-v1:{child_id}`; a write-once guard test (`test_profile_age_invariant.py`) fails if any code path other than the profile-creation paths writes `age_months`; no migration |
| A3 | Separate versioned SHA-256 digest field beside the integer `context_revision`; contract change needs its own approval | A 31-bit value derived from a versioned canonical-JSON SHA-256 digest is stored in the existing integer `context_revision` and only compared for equality; no contract change |
| A4, A5 | Deferred | Deferred (T2C) |
| B8 | No T3 source/test path authorised until the allowlist is restored | Same; T3 code is not started |

## Independent review assessment (two Sonnet 5.5 reviews, evidence-based, not authoritative)

- BE2 consumers of `ContextDecision.context_revision` on the vision and ai_jobs paths compare for equality only; ordered comparisons and `+1` elsewhere belong to unrelated aggregates.
- A1: the constant is acceptable while no route can change age and no REAL data exists. Real provenance needs columns; adding them is cheapest in the same task as the PostgreSQL adapter of `BE1FactSource.current_facts()` (not written yet). Must be done before any age-editing route or REAL data.
- A3: 31 bits gives about 4.7e-10 accidental-collision probability per comparison, but an actor who controls free-text snapshot fields could search for a collision in minutes. Acceptable for the operator-controlled synthetic pilot, not for REAL data. Review recommendation: keep the integer as the compatibility fence and additionally emit the 256-bit digest from the same canonical JSON; move comparisons to the digest when REAL data or B4b is introduced.

## Disposition recorded

The owner selected the decision record as the authority and approved the bounded rework plan. The BE2 provider claim remains integer-only by design in this scope, so contexts carrying the new digest are refused before provider execution until a separately approved cross-process contract carries the digest.
