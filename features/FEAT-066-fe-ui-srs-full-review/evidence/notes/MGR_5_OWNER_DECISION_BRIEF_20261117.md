# MGR-5 owner decision brief — separate school-managed consent

Status: OPEN / OWNER DECISION REQUIRED. Manager consent writes remain unavailable pending a decision and subsequent contract review.

## What the current baseline says

Canonical repository SRS is FEAT-063 Rev60 under SRS_AUTHORITY.md. Rev60 §§31.3, FR-PL-07, and AC49 assign Parent-profile consent/grants to the Parent and do not define a separate school-managed consent policy. D-066-62, recorded in the current working-tree DECISIONS.md lines 260–268 and corroborated by the MGR-1 owner disposition, says staff cannot create or revoke effective Parent consent; staff-origin pending records are not effective Parent consent. D-066-62 is absent from pinned HEAD and is not represented as committed baseline. The existing BE route can create a pending record, but that implementation fact does not settle policy.

## Decision requested

Does the product require a separate School Manager/Teacher-managed consent workflow distinct from Parent-profile consent and grants?

If yes, specify the minimum policy before any write contract is drafted:

1. Purpose and legal basis; affected data/use and whether the action is consent, notice, attestation, or another record.
2. Authorized actor and organization/class/child scope; whether Parent action or notice is a prerequisite.
3. Effective-state meaning, evidence/provenance, transitions, expiry, revocation, and effect on already-running or future access.
4. Relationship to Parent-owned consent/grants, including precedence and conflict handling.
5. Manager read visibility, audit fields, retention, and correction process.

If no separate workflow is needed, confirm that Manager record/revoke actions stay absent and specify whether the existing read-only status display is permitted and which fields it may expose.

## Safety boundary until decided

Do not treat a staff-created pending row as Parent consent, as effective authorization, or as a legal determination. Keep Manager write actions unavailable. The current page may remain read-only only within an approved field-visibility policy. This brief does not select policy or authorize implementation.
