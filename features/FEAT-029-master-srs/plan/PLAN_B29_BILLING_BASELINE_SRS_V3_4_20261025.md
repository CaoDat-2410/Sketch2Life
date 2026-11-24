# Plan — B29 billing baseline adoption and SRS v3.4

Date: 2026-10-25 (Asia/Saigon)
Status: APPROVED BY DIRECT OWNER REQUEST

## Objective
Promote the school-level payment and billing capability described in B29 into the product SRS baseline, document the complete target behavior and acceptance expectations, and distinguish baseline requirements from implementation status and proposed monetary amounts.

## Scope
1. Preserve the exact v3.3/B28 artifact and the original registration v1.2 source.
2. Publish SRS v3.4 in the canonical Master SRS and synchronized FEAT-039 SRS copy. Promote billing packages, entitlements, payment flows, roles/permissions, FR, NFR, business rules, typed errors/exceptions, privacy and platform safeguards to the baseline.
3. Mark billing as baseline scope with implementation status NOT IMPLEMENTED; no runtime code, migration, provider credentials, live transaction or release is included.
4. Treat package and add-on price amounts as PROPOSED only. Record the product package structure and included quota as baseline target choices; maintain unresolved financial/legal/provider configuration decisions as explicit TBDs.
5. Include the existing Teacher Desktop and Super Admin Portal, `billing:manage` permission, school-level `school_id` entitlements, MoMo/VNPay/VietQR routes, child-safe purchase boundaries, callback verification, idempotency, ledger and reconciliation requirements.
6. Keep technical architecture aligned with the current project (existing web surface, FastAPI application, PostgreSQL persistence and payment adapter boundary); provider-specific contracts and deployment configuration stay implementation decisions.
7. Update SRS version history, context, decisions, status, approvals, traceability and evidence.

## Acceptance criteria
- AC01: SRS v3.4 is authoritative and its FEAT-029 canonical and FEAT-039 current copies are byte-identical.
- AC02: The v3.3/B28 source remains preserved with its recorded hash; Registration v1.2 is not modified.
- AC03: Baseline payment/billing requirements have stable FR, NFR, BR and error/exception identifiers and explicit verification expectations.
- AC04: Baseline package structure and entitlement quotas are stated. Every Sketch2Life monetary amount alone is labeled PROPOSED; do not call the feature proposal-only.
- AC05: The SRS states billing is planned baseline scope but NOT IMPLEMENTED, and records provider, legal, platform, merchant, refund/tax and production release gates without claiming compliance or operational readiness.
- AC06: No runtime implementation or application tests are performed in this documentation task.
