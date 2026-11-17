# Plan Rev5 — SRS owner-decision amendment

- **Status:** APPROVED from the project owner's direct request to record the clarified decisions in the SRS and the six returned answers on 2026-10-24.
- **Feature:** FEAT-039, coordinated with FEAT-060 contract proposals.
- **Scope:** publish an additive SRS v3.3 amendment while preserving the exact v3.2 artifact; reconcile directly affected B19.5/OD07/CS-006 rules; update source, approval, decision, context, status, API proposal, traceability, and validation records.
- **Out of scope:** new BE1 routes or schemas, Alembic migrations, client behavior dependent on missing contracts, FEAT-057 AI integration, Modal configuration/call/deployment, external messages, Git publication, production/child data.

## Owner-confirmed decisions to record

1. Revoke every still-pending Child admission request atomically when Teacher start succeeds; refresh returns `revoked`.
2. Shared six-digit code lasts for the open Lobby; Teacher may rotate before start; use cryptographically random collision-safe codes, keyed-hash storage, a generic failure, and persistent throttling at 10 invalid attempts per source IP per 15 minutes. BE1 must review trusted-proxy/IP attribution and cross-replica persistence.
3. Teacher may advance only to the next shared stage after backend guards and a durable receipt. Assistance may interleave or be marked `not_needed`; no arbitrary skips.
4. Keep stage rewind disabled until OD07 is resolved; OD07 remains an open product decision.
5. Require `save_draft` before advancing past unfinished group work; retain the draft against its group without claiming completion.
6. Require an early-stop reason category (`time`, `safety`, `technical`, `other`); a short Teacher note is optional.

## Steps and acceptance

1. Preserve v3.2 bytes and SHA-256 before creating v3.3. **AC1:** v3.2 hash remains exactly `9d7a71cc3fd0ab45b3175823c09780af0eb2e129d21a991d5470693dae25a21d`.
2. Add B28 with all six choices, authority, limitations, and explicit BE1 implementation gates. Reconcile current transition/decision rows so no earlier section contradicts B28. **AC2:** each choice is present and correctly labeled `OWNER_CONFIRMED`; OD07 itself remains unresolved.
3. Synchronize the FEAT-039 v3.3 artifact and FEAT-029 canonical copy. **AC3:** byte-identical and hash recorded.
4. Update the static checker and all relevant feature/source/contract/traceability records. **AC4:** no unsupported implementation claim; schema/migration/API review gates remain visible.
5. Run the feature documentation validator, JSON parsing, hash/copy checks, and targeted `git diff --check`. **AC5:** checker valid with zero errors; all required machine-readable records parse.

## Verification boundary

This amendment records product policy only. It does not count as BE1 technical approval, migration ownership approval, FEAT-057 card approval, live-provider configuration, or end-to-end product verification.
