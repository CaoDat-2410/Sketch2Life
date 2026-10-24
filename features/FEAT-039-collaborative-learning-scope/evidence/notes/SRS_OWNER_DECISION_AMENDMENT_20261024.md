# SRS owner-decision amendment — evidence

- **Evidence ID:** E10
- **Date:** 2026-10-24 (Asia/Saigon)
- **Type:** Direct owner decisions and SRS/contract consistency update
- **Plan:** FEAT-039 Plan Rev5; exact approval hash recorded in `approvals/TASK_APPROVAL.md`
- **Current SRS:** v3.3, B28; canonical FEAT-029 copy synchronized after validation
- **Preserved prior artifact:** v3.2 at `artifacts/Collaborative_Learning_SRS_v3.2.md`, SHA-256 `9d7a71cc3fd0ab45b3175823c09780af0eb2e129d21a991d5470693dae25a21d`

## Authority

The project owner instructed that changes be recorded in the SRS and answered all six consolidated questions on 2026-10-24. These answers authorize the product-policy text below. They do not authorize implementation of new BE1 routes, schemas, Alembic migrations, FEAT-057 integrations, Modal deployment, production data, or Git publication.

## Decisions recorded in B28

1. At successful Teacher start, revoke all still-pending join requests atomically; Child grant refresh returns `revoked`. Existing admitted grants remain valid; both QR/code entry reject new requests after start.
2. The shared six-digit room code lasts for the open Lobby, may be rotated by Teacher before start, is generated cryptographically and collision-safely, is stored only as a server-side keyed hash, and returns a generic error for unknown/rotated/closed/wrong codes. The owner approved a persistent limit of 10 invalid entries per source IP per 15 minutes. BE1 must review trusted-proxy attribution and cross-replica persistence.
3. Teacher advances only to the next SRS stage after backend guards and a durable receipt. Assistance can interleave; if no assistance is needed, Teacher may record `not_needed`. Arbitrary stage skips are forbidden.
4. Keep stage-return commands disabled until OD07 is resolved. OD07's final pedagogical rule remains open; this is an interim guard, not a decision that rewind is permanently forbidden.
5. Before advancing past unfinished group work, Teacher must choose `save_draft`; retain it against the group and do not claim completion. Other groups can continue.
6. `ended_early` requires a reason category: `time`, `safety`, `technical`, or `other`. An optional short Teacher note may accompany it; preserve the current stage and incomplete work refs.

## Verification and technical boundary

The exact v3.2 artifact was copied to v3.3 before edits, preserving the prior hash above. B19.5, OD07, CS-006, UC-010 and B27 reconciliation rows were checked against B28. The v3.3 feature artifact and FEAT-029 canonical copy are byte-identical at SHA-256 `f7f401829955c26a793c94d468c74502dc0ed465f9f35084e364b728c243c646`. Static documentation coverage/link/security-content checks are recorded in `../metrics/SRS_AMENDMENT_CHECKS_20261024.json`; this is not a product/API test.

BE1 review is still required for route/version, transaction boundaries, request/receipt fields, rate-limit IP trust and shared storage, keyed-hash key lifecycle, code collision retry, group-draft durability/recovery, completion snapshot/guard fields, and clean-install/upgrade/rollback order for the repository's nine Alembic heads. No migration or new runtime route was added in this amendment.
