# FEAT-063 B4b — Real consent lifecycle (DRAFT, AWAITING_APPROVAL)

- Status: **DRAFT / AWAITING_APPROVAL.** This document authorizes no implementation, migration, database operation, or relaxation of an access guard.
- Task type: design and contract planning for real/legal consent lifecycle in the current BE1 flow, including the C022–C024 consent APIs.
- Baseline reviewed: `be1_models.py`, `be1_registry.py`, and `be1_common.py` at the current task baseline. This is a static source review only; no database or runtime behavior was exercised.

## 1. Scope

Plan a complete real-consent lifecycle that makes an authorized and evidenced transition from a recorded request to an effective legal-consent decision, preserves revocation, and keeps the existing legal guards fail-closed until that lifecycle is explicitly implemented and approved.

The design must account for `data_origin=REAL` and `LEGACY_UNCLASSIFIED`. A legacy or unclassified profile must not become eligible through a default, migration assumption, or synthetic proof. C022–C024 must describe and implement the same lifecycle once a later task is approved.

This task does not change the synthetic pilot. `SYNTHETIC_DEV` remains a separate typed eligibility basis and never becomes `consent_effective=true` or a consent-record state.

## 2. Verified source facts

1. `backend/src/sketch2life/infrastructure/persistence/be1_models.py:213-231` defines `ConsentRecordModel`. Its database check allows only `pending` and `revoked`; the mapped default is `pending` (`:216`, `:226`). There is no `effective` state in this model's allowed set.
2. `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:402-450` implements `record_consent`. It inserts `state="pending"` (`:415-424`), writes a pending audit/event (`:427-442`), and returns `effective: false` (`:443-449`).
3. `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:487-536` implements revocation. It changes the existing row to `revoked` (`:514`) and returns `effective: false` (`:531-535`).
4. `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:329-347` and `backend/src/sketch2life/interfaces/http/routers/be1_common.py:229-251` query for `state="effective"` before profile creation or a legal-consent check. The first route's success response reports `consent_state: "effective"` at `be1_registry.py:388-395` after that query.
5. Static search of BE1 persistence writes found the pending insert and revoked update above; no BE1 code path writes `ConsentRecordModel.state="effective"`. Other uses of the word `effective` elsewhere in the repository refer to unrelated models and are not evidence of legal-consent verification.

## 3. Problem statement

The writer and reader contracts do not currently meet: the only shown BE1 insert creates `pending`, the only lifecycle update creates `revoked`, while legal access requires `effective` and the table check rejects that value. Therefore the current source contains no reachable real-consent transition that can satisfy those reads. A profile cannot be made legal-consent-effective by changing its response, attaching an evidence reference, or treating the synthetic pilot proof as consent.

The immediate safety rule remains: do not add an implicit `effective` write and do not weaken any legal guard to make profile creation, records, gallery, or other routes proceed.

## 4. Options for owner decision

| Option | Proposed shape | Benefits | Reasons against / unresolved |
|---|---|---|---|
| A — explicit confirmation transition | Keep `pending`; add a separately authorized adult/Parent confirmation operation that checks the required evidence and scope before transitioning to `effective`; preserve `revoked` as terminal for that consent record. | Matches the current `effective` readers and provides an explicit decision point and audit event. | The product has not specified who may confirm, what evidence is sufficient, or whether a Teacher can make this decision. Adding a state alone would not establish lawful verification. |
| B — separate verification decision | Keep the recorded consent submission distinct from a verified decision; store a separately attributable and versioned verification outcome, and make the legal gate read only that outcome. | Separates evidence submission from the person/process that verifies it; avoids treating a submitted form as effective. | Adds a second authority/evidence lifecycle and requires explicit ownership, status, revocation, and consistency rules. No existing source contract establishes these. |
| C — keep legal access blocked until policy is specified | Continue recording `pending` and revocation; keep all `effective` reads fail-closed. Resolve product/legal authority and evidence requirements before a later schema/implementation plan. | Safest against inventing consent authority or treating unverified evidence as consent. | Real Child profile and downstream legal-consent paths remain unavailable until a decision and implementation are approved. |

No option is selected by this draft. Option A is a discussion candidate only, not a recommendation that grants authority to any current role.

## 5. Required invariants for any selected design

- A submission is not effective merely because an adult or Teacher called `record_consent`.
- The effective decision is attributable to an explicitly authorized actor/process and carries evidence provenance, exact organization/class/child/purpose scope, and a revision or equivalent immutable history.
- Revocation is recorded, idempotent, and causes every applicable current legal gate to deny; a revoked record cannot be silently reactivated.
- `REAL` requires the selected legal verification path. `LEGACY_UNCLASSIFIED` remains denied until explicitly classified with evidence under a separately approved rule.
- `SYNTHETIC_DEV` proof remains separate and cannot write or satisfy a legal consent record.
- Existing legal guards remain enabled throughout any migration. No temporary bypass, permissive fallback, or response-only status change is allowed.
- A migration must preserve pending and revoked history and must not backfill `effective` from existing pending rows or from the presence of an evidence reference alone.

## 6. Questions for the owner

1. Which actor or external process is authorized to verify a parent's consent and make it effective? Is the Parent directly authenticated in this product, or does a separate verified workflow decide?
2. What evidence is accepted, how is its provenance retained, and which organization/class/child/purpose fields must be bound to it?
3. Is `effective` a state on the submitted consent record (Option A) or a separate verification decision (Option B)? What is the terminal/replacement behavior after revocation?
4. How should existing `LEGACY_UNCLASSIFIED` profiles be handled: remain denied, or be classified only after a fresh verified consent workflow? Who owns that process?
5. Which audit/event record is required for submission, verification, refusal, and revocation, including actor and policy version?
6. Which API contract and response semantics should C022–C024 expose for pending, effective, revoked, and unavailable verification?

## 7. Proposed implementation phases after a separate approval

1. Freeze the owner's answers above and the legal/evidence authority in a reviewed contract/ADR.
2. Produce a schema and migration plan with a preserved history model and a forward-only, fail-closed transition; identify the single schema owner and migration parent before editing.
3. Add the explicit verification/revocation application path, with audit and event behavior, while leaving existing readers fail-closed until the authoritative record is available.
4. Update the C022–C024 contracts and legal reads as one coordinated task; keep synthetic eligibility in its separate typed gate.
5. Verify tests for pending denial, authorized effective transition, wrong scope/actor denial, revocation, legacy denial, and synthetic/legal non-interference. Any PostgreSQL rehearsal requires its own safe, approved test database.

## 8. Acceptance for a future implementation task

- A pending consent cannot authorize profile creation or any existing legal-consent-protected operation.
- Only the owner-approved authority and evidence path can produce an effective legal decision; wrong actor, missing evidence, wrong scope, or unsupported origin fails closed.
- Revocation immediately prevents subsequent legal access and is idempotent; no path reactivates a revoked record without an explicit owner-approved replacement lifecycle.
- `LEGACY_UNCLASSIFIED` stays denied unless a separately specified classification process succeeds.
- Synthetic proof decisions do not create consent records and do not make either `consent_effective` or a legal-purpose flag true.
- C022–C024, the response schema, persisted state constraints, audit/event trail, and legal read helpers agree on the same lifecycle.
- Migration and API tests run against the approved isolated database plan; no test is reported as passed unless actually run.

## 9. Risks and exclusions

- Adding `effective` to the CHECK constraint without a real authorized verification transition would convert an unreachable state into a writable but unverified state.
- Treating `evidence_ref` as proof of validity without an evidence-verification rule would create a false grant path.
- Misclassifying legacy profiles or conflating synthetic and real origins could make old records eligible without current authority.
- This draft does not change code, SRS, contracts, migration, database, any runtime setting, synthetic guard, provider, or API behavior. Every such change requires a separate plan approval and an explicit allowlist.
