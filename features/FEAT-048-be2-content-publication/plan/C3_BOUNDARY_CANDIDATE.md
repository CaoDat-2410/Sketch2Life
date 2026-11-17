# C3 owner boundary and resolution — candidate 0.1

Scope: approved revision 1/P1–P4, C3a eligibility projection. This is a typed
integration seam, NOT BE1/BE2-05 adoption or a production identity implementation.
Shared DATA-24 source is consumed unchanged; no new review command is introduced.

## Boundary obligations

`ContentBoundary.guard(principal_id, organization_id)` verifies the authenticated
principal, organization, current capabilities and a current owner-supplied policy.
The application checks the returned identity/scope again. No caller role or
source-classification boolean supplies authority. There is no default adapter.

The guard MUST fence authorization, policy, applicable source/usage/moderation and
review-effectiveness decisions through the entire content transaction commit or
rollback. Lock order is owner guard, then content parent record. A mere snapshot,
process lock or late recheck is not durable cross-owner revocation proof. An
adapter unable to satisfy the contract must deny access, never return permissive
values. Real fencing/adoption remains an integration gate.

Policy has owner-issued version/content-policy/age-policy refs and allowed content
kinds/purposes. BE2-12 does not choose these values, consent policy, TTL or budget.
Source assessment is server-derived and bound to organization/id/version/hash
and that policy version. Only generic-authored content with usage and moderation
approved is eligible. Child-derived and unknown classification remain closed.

`review_effective(content, proof)` must verify the exact stored proof's current
effectiveness and reviewer authority, not merely echo `proof.state`. Both safety
and pedagogical bindings still pass domain checks for exact target/hash/context,
audience, policy, non-author reviewer, decision and effective snapshot state.
Missing/stale dependencies produce safe ContentError codes, not raw content.

## Resolution contract

READ capability is required before storage access. Resolution is scoped by
organization/record, requested age in months and purpose. An explicit version
never substitutes another version, and optional expected hash requires an
explicit version. No HTTP/auth bypass is introduced in C3a.

Default resolution enumerates published versions descending, never the head
draft. It checks current policy/source/reviews, then the requested audience.
Audience-ineligible versions may be skipped. Policy/source/review denial or
dependency failure fails the request closed instead of silently falling back to
older content. An explicitly recalled/archived/draft version is never returned.

Audience hash v1 is canonical JSON of shared DATA-24 school-library scope,
age-policy ref and sorted unique purpose codes. Sorting the audience's set does
not alter the authored body hash or future receipt fingerprints.

SQL enumeration retains a SHARE lock on the content parent through the read
transaction. Recall/edit writers take UPDATE on the same parent. This is a
content-store boundary only; it does not prove the external owner guard.

## Remaining C3 work

Mutation orchestration, shared review-record response, command receipts/replay,
current guards on mutation, application/SQL lifecycle races and production owner
adapters are not completed by this projection. C4 routing/delegates and C5 full
handoff remain separate. Do not mark BE2-12 DONE from C3a component/SQL checks.
