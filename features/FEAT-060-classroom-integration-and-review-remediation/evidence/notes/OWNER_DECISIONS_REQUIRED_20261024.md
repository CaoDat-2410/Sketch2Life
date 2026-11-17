# Owner decision record for classroom BE1 contracts — 2026-10-24

The owner approved FEAT-060 Plan Rev3 and answered the six product-policy questions together on 2026-10-24. These answers are recorded in SRS v3.3 B28, FEAT-039 D27–D32, and FEAT-060 D15–D20. Product semantics are resolved; implementation contracts below remain gated and no new route/schema/migration was created by these answers.

## 1. Pending Child requests when Teacher starts

Owner-confirmed: after start, QR and numeric code accept no new join requests; already admitted devices keep their grants. SRS v3.3 B28.1 specifies the pending-at-start disposition below.

**Owner-confirmed:** atomically revoke every request that is still pending when `start` succeeds; Child refresh then receives `revoked`. Teacher cannot admit them after start. BE1 must review start/admit concurrency, transaction semantics and the durable receipt.

## 2. Shared six-digit room-code controls

Owner-confirmed: this is one shared room code for the class, not an OTP; code and QR both close to new joins after start.

**Owner-confirmed:** code active for the whole lobby; Teacher may rotate before start; cryptographic randomness; collision-safe among joinable rooms; keyed-hash-only storage; generic response for invalid/rotated/closed values; persistent limit of 10 invalid entries per source IP per 15 minutes; no plaintext code in logs. Khoa/BE1 must still review trusted-proxy/source-IP attribution, cross-replica enforcement, key lifecycle, collision retry and audit/storage details. An implementation concern does not silently change the approved threshold; alternatives return to the owner.

## 3. Shared-stage transitions and Assistance

The nine ordered stages and separation from lifecycle/group progress are already recorded in SRS v3.3 B28 and B19.4–B19.5. Assistance may also occur between stages.

**Owner-confirmed:** Teacher advances only to the next ordered stage after backend guards and a durable receipt. Assistance may interleave without moving the shared stage or be explicitly recorded as `not_needed`; arbitrary skips are forbidden. Stage rewind remains disabled until OD07 is resolved; OD07 itself remains open.

## 4. Unfinished group work when the class advances

SRS/CS-006 requires an explicit outcome and forbids silently marking unfinished work complete or losing it.

**Owner-confirmed:** require `save_draft` before advancing past incomplete work. Keep the durable draft attached to its group; it neither blocks other groups nor claims completion. BE1 must review save receipts, transactionality, restore/read, and failure recovery.

## 5. Early-stop reason format

Owner-confirmed: product outcomes distinguish `completed` from `ended_early`. The approved Plan Rev3 also requires an explicit reason for early stop and preservation of saved/incomplete work.

**Owner-confirmed:** require category `time`, `safety`, `technical`, or `other`; allow an optional short Teacher note. The completion command must retain the current stage, evidence references and unfinished-work dispositions; it must not convert incomplete work into success. Exact receipt fields/guards remain BE1 review.

## Decisions already answered by authoritative SRS/session context

- A 40-child class is an owner-confirmed, unmeasured pilot capacity target (SRS B17/OD12), not a hard admission cap. Do not reject the 41st admission without a new owner decision; measure capacity separately.
- QR and six-digit code both stop accepting new requests after Teacher start; admitted Child grants remain, and pending requests are revoked atomically.
- Product outcome distinguishes `completed` and `ended_early`; early end requires a reason category and has an optional note.
- Stage progression, OD07 interim guard, group draft and approved room-code control package are recorded in SRS v3.3 B28.

## Technical approvals still required after the product decisions are recorded

- **Khoa / BE1 contract and migration review:**
  1. Final route/version, DTO fields, authorization scope, generic errors, idempotency and receipt format for room-code create/rotate/join; Teacher display must not leak the raw code through general session reads.
  2. Atomic start/admit behavior: reject new QR/code joins after Start, revoke all still-pending requests in the Start transaction, preserve admitted grants, and define concurrency/retry response behavior.
  3. Storage/security implementation for collision-safe random codes, keyed-hash key lifecycle, the approved persistent 10-invalid/source-IP/15-minute threshold, trusted-proxy/source-IP attribution, cross-replica rate-limit durability, and audit/log redaction.
  4. Authorized read contract for current admitted roster, groups, memberships, progress, and active turns so Teacher can reload after browser/device restart; do not expose device keys or unrelated child data.
  5. Stage read/advance/history route shapes, separate stage revision, next-stage guard, idempotency/stale revision behavior, durable transition receipts, Assistance interleaving/`not_needed`, and disabled rewind until OD07 is resolved.
  6. Group-draft contract: persist `save_draft` and its canvas/checkpoint revision before stage advance; define group ownership, restore/read, failure/retry and atomicity.
  7. Completion contract: distinct `completed`/`ended_early` result, required category for early stop, optional note, current stage/evidence/draft snapshot, completion guards, retention/audit behavior, and transaction with lifecycle finish.
  8. Choose/approve the physical persistence model and Alembic lineage. The workspace has nine migration heads; BE1 must define a single clean-install/upgrade/rollback path before any migration is added.
- **FEAT-057 card owners:** approve each BE2 candidate route/runtime adoption, payload/version, safety review and human approval path before AI/video/activity wiring.
- **Project owner / AI provider:** Modal remains selected behind the backend provider adapter; app/function URL, model, GPU, region, scaling, timeout, auth/secret policy, spend cap, and live synthetic endpoint test are still unconfigured. No deployment/GPU call has been made.
- This document does not authorize sending a message to Khoa, database migration, deployment, GPU provisioning, or real child data. No external message has been sent.

