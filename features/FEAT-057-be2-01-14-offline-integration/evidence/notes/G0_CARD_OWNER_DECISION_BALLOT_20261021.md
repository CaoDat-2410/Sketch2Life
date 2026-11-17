# FEAT-057 G0 card-owner decision ballot — 2026-10-21

## Purpose and authority

This ballot records the owner's direct responses to the open G0 contract
questions. It has **not been routed externally**. The user identified themself
in this conversation as owner of the affected cards and selected the proposed
dispositions below. These adopt contract direction only; they are **not
implementation approval**, card acceptance, or runtime authorization.

## Owner response — 2026-10-21

The owner approved the proposed selections with `Chốt theo đề xuất`, then
clarified they own the affected BE2 cards. Record B1–B5 and B7 as
`ADOPT_WITH_CHANGES`; record B6 as `BLOCKED` because no already-adopted
current-source resolver/fence has been identified. This records contract
direction only; it does not authorize implementation or mark any card
accepted/done.

Reviewed plan: `../../plan/CROSS_LANE_X01_X05_SLICE_PLAN_REV3_20261021.md`
(revision 3, SHA256
`5500B0CA5ED839C4FF5150D66FC19F2751F6C1F93261DE37BB1629747FF41C04`).
Adoption question packet: `G0_CARD_OWNER_ADOPTION_PACKET_20261021.md` (SHA256
`8BD324DFA446E3EEBE976A5E1018F9141EE0FA20BB2C6C23F0BABDCA025C6D75`).
Candidate branch/HEAD: `feature/be2-backend-ai-integration` /
`1649b72978877d82b4d7662040ff3555dee0a3a7`.

## Recommended selections

| ID | Owning cards / question | Recommended selection | Proposed decision to record | Owner response |
|---|---|---|---|---|
| B1 | BE2-07 / BE2-08 — X01 exact-source fence | `ADOPT_WITH_CHANGES` | Adopt exact bundle/version/hash and audience/context identity. Name the fence owner, scope, lifetime and commit linearization point; hold or atomically validate the fence through BE2-08 finalization, including revoke/invalidation races. | `ADOPT_WITH_CHANGES — direct owner response` |
| B2 | BE2-01 / BE2-08 — X05a atomic boundaries | `ADOPT_WITH_CHANGES` | Adopt two separate transaction boundaries: submission commits run/job/dispatch receipt together; finalization commits completion/exact artifact/receipt/outbox with job/run CAS, current fences and recovery lookup. Provider work remains between them. Name enlisted records, UoW authority, receipt owner and rollback/recovery behavior. | `ADOPT_WITH_CHANGES — direct owner response` |
| B3 | BE2-01 / BE2-08 — replay, duplicate and late result | `ADOPT_WITH_CHANGES` | Retry or lost acknowledgement returns the authoritative existing receipt/run, without creating another job, run or artifact. Define replay authorization and the duplicate winner. A late result commits only while its attempt still wins the adopted CAS and current source/policy fences remain valid. Confirm receipt scope and recovery semantics in the owner contract. | `ADOPT_WITH_CHANGES — direct owner response` |
| B4 | BE2-01 / BE2-08 — X09-08 typed route | `ADOPT_WITH_CHANGES` | Adopt only a typed route to BE2-08 `VideoWorker`; unknown job types fail closed. Map subject/session, exact source pin and idempotency key from immutable job/request/run fields if those fields are contractually stable; otherwise define a separately approved versioned envelope. Do not register BE2-13. | `ADOPT_WITH_CHANGES — direct owner response` |
| B5 | BE2-09 — X05b / CR09-01 | `ADOPT_WITH_CHANGES` | Adopt a canonical review head and DATA-27 projection bound to the exact committed BE2-08 artifact hash/version. Keep review-head/projection ownership with BE2-09; do not rewrite BE2-08 rows or migrations. | `ADOPT_WITH_CHANGES — direct owner response` |
| B6 | BE2-07 / BE2-09 — X05d current-source fence | `BLOCKED` unless an existing adopted resolver/fence is identified | Proceed only if the owner cites an already-adopted current-source resolver/fence that covers review commit and playback intent. Do not add a new receiver/event in this slice. If no such boundary exists, record `BLOCKED`; X05 remains incomplete and X02 stays out of scope. | `BLOCKED — no adopted resolver/fence identified` |
| B7 | BE2-08 / BE2-14 — POLICY-08 | `ADOPT_WITH_CHANGES` | Adopt fail-closed policy/disable/kill checks for each applicable phase through finalization. Separately name worker/provider execution authorization and budget/concurrency reserve, settle and release owners, keys, and retry/replay behavior. Current-use eligibility does not grant execution or budget authority. | `ADOPT_WITH_CHANGES — direct owner response` |

These are now the owner's contract-direction responses. Detailed implementation
scope, allowed files, evidence and any card-specific approval still need to be
recorded before changing card-owned source/schema or tests. B6 remains blocked
until evidence of an already-adopted resolver/fence is supplied.

Repository-owner verbatim decision: `Chốt theo đề xuất`.

## Kept open or deferred

- **X05c / CR09-02:** remains `OPEN`. The actual session/access receipt and
  each-use gateway are outside this ballot; playback intent does not prove
  actual session start or playable access.
- **X05d / X02:** X05d is `BLOCKED` pending evidence of an already-adopted
  resolver/fence. Do not pull X02 into this slice to fill the gap.
- **Modal:** remains deferred pending a separate explicit resume instruction.
- **Implementation and card acceptance:** remain gated on explicit
  implementation scope/approval and each card's acceptance criteria. Contract
  direction is adopted above, but these gates are not cleared. X01 remains
  `PARTIAL`; X02–X09 remain `NOT_IMPLEMENTED`; no card status or acceptance
  changes here.

## Per-card implementation handoff fields

The owner responses are recorded in the table. Before implementing card-owned
changes, record the detailed contract revision, allowed files, evidence, and
implementation approval in the owning card using this template:

```text
Ballot ID:
Owner and owning card:
Response: ADOPT / ADOPT_WITH_CHANGES / DECLINE / BLOCKED
Public contract and version/revision:
Accepted changes or blocker:
Identity mapping and transaction/fence/replay boundary:
Allowed source/test/schema/migration files:
Required evidence and approval record path:
Owner response date:
```

The owner response is recorded above. This ballot alone authorizes no
source/test/schema changes, test execution, Modal/Lightning,
database/provider/runtime activity, staging, commit, push, or merge.
