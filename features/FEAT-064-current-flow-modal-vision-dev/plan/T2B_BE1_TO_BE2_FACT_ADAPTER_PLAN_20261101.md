# T2B — BE1 to BE2 fact adapter plan (2026-11-01)

- Status: **DESIGN DECISIONS RECORDED; implementation requires a separate task approval**.
- Feature: FEAT-064, synthetic-only current-flow pilot.
- Parent plan: `plan/PLAN.md` revision 6. This task plan does not change the parent status (`DRAFT / NOT_STARTED`).

## Goal

Define the narrow no-fallback adapter that constructs BE2 `MemberFact` and `ContextDecision` from one coherent, authoritative BE1 read. Preserve legal-consent behavior and keep synthetic eligibility explicitly non-legal.

## Approved design decisions

### A1 — age source and age revision (**Sửa**)

- BE1 `ManagedProfileModel.age_months` is the source value. Add persisted `age_revision` (integer, initial value 1) and `age_source` using an allowlisted source enum.
- Increment `age_revision` only when the age value changes. A source correction without an age change does not increment it; the whole-context digest still changes because the source changed.
- Existing rows whose source cannot be established are backfilled as `LEGACY_UNKNOWN`; do not infer provenance from a profile identifier, creation/update timestamp or session revision.
- Synthetic pilot profiles use the explicit synthetic source value. Other values must come from an authoritative writer/source; an implementation approval must pin the enum before code or migration is written.
- Construct the BE2 age provenance reference from the persisted `age_source` and `age_revision` only. The BE1 owner must review the migration/backfill design before implementation approval.

### A2 — synthetic consent fields (**Đồng ý**)

Version the BE2 `MemberFact` contract so consent reference/revision can be absent only when `eligibility_basis == SYNTHETIC_DEV`. Enforce all of the following:

- `LEGAL_CONSENT`: consent reference and revision are present and valid; the existing legal gate remains authoritative.
- `SYNTHETIC_DEV`: both consent fields are `None`; `consent_effective` remains `false`; a separately verified, current synthetic proof and purpose/policy gate are required.
- Missing basis, partial consent references, stale/revoked proof, or any other origin fails closed. Never create a fake `effective` consent row.

### A3 — whole-context freshness (**Sửa**)

Source review found the current BE2 `ContextDecision.context_revision` is an integer. The relevant vision consumers compare it for equality (`!=`/`==`); they do not order it. The string digest therefore must not be coerced into that integer field.

- Add a versioned `context_digest`/fingerprint field to the BE2 context contract used by the BE1 adapter. Preserve the numeric field for compatibility and any session-local revision semantics.
- Compute a strict, canonical SHA-256 over one coherent snapshot of the profile and age provenance/revision, consent state/revision, synthetic proof status/scope/expiry/revocation, class/session membership and session state/configuration relevant to eligibility.
- Recompute the digest at the admission/decision boundary and compare for equality. A changed digest means stale; digest ordering has no meaning.
- Treat the digest as an opaque freshness token, not a credential, proof of consent, or anonymization. Do not include volatile read timestamps. Any change in eligibility-relevant inputs must change the digest or produce a denial.
- Align the BE1 adapter with the existing BE2 canonical context-digest rules where possible; any contract version or consumer changes must be listed in a separate implementation approval.

## Scope boundary (A4–A6)

T2B supplies only `MemberFact` and `ContextDecision`. It does not create `CanvasFacts`, `GroupRoster`, `current_turn`, status/reconnect adapters, or canvas APIs. Those remain separate later tasks. The adapter reads server-owned facts; it does not accept client-provided consent, age provenance, proof, membership or revision values.

## Future implementation sequence

1. BE1 owner reviews the exact age-source enum, legacy backfill, migration parent and age-revision write path.
2. BE2 owner reviews the versioned nullable-consent `MemberFact` and digest-bearing `ContextDecision` contract and all affected equality/stale checks.
3. Add the no-fallback BE1 adapter over one transactionally coherent read.
4. Add unit and contract cases for legal, synthetic, legacy, missing, revoked, expired, mismatched and concurrent/stale snapshots.
5. Run the approved T12 rehearsal only against a disposable local PostgreSQL database with `BE1_TEST_DATABASE_URL` supplied outside chat. Migration application requires its own approval.

## Acceptance criteria for the future implementation

- AC1: one adapter call yields a coherent `MemberFact`/`ContextDecision`; it never combines facts from separate reads without a consistency boundary.
- AC2: age revision/provenance follow A1 exactly; source changes are represented even when age does not change.
- AC3: legal consent stays required and unchanged; synthetic records have nullable consent refs, `consent_effective=false`, and require valid proof.
- AC4: stale detection compares the versioned full-context digest for equality, including pre/post-provider checks; a digest mismatch fails closed.
- AC5: no `CanvasFacts`, `GroupRoster`, `current_turn`, Parent flow or production/real-child scope is added.
- AC6: tests prove no age/consent/proof/membership/session value is inferred or substituted from client/session IDs, timestamps or another revision.

## Approval and environment gates

This plan records approved design choices only. It does not authorize source edits, tests, Alembic files/commands, database setup, services, Docker, Modal/GPU calls or real-child data. Before implementation, create a task-specific plan/addendum with the exact file allowlist, migration identity/parent, named reviewers, checks and separate owner approval. A T12 PostgreSQL database is not available in this record.
