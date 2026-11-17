# Feature decisions

## D01 — Integrate through versioned BE1 contracts

- Date: 2026-10-23.
- Authority: Direct owner request and repository contract/integration rules.
- Decision: Start from the current BE1 v1 route and schema set. Do not create a parallel client-owned DTO model or add undocumented backend behavior. Any missing workflow capability requires a versioned contract and its owning feature/card approval before implementation.
- Consequence: Admin features with no matching backend contract remain visibly unsupported until a contract is approved; no empty-success or mock-token fallback may masquerade as a connected runtime.

## D02 — One vertical workflow before expansion

- Date: 2026-10-23.
- Authority: `docs/architecture/CONTRACTS_AND_INTEGRATION.md`.
- Decision: Prove WF-01 session preparation/admission and WF-02 child drawing/recovery first, then expand to WF-03 AI sketch review and WF-04 reviewed learning/session close.
- Consequence: The overall plan covers all four; BE2-dependent steps remain behind FEAT-057 owner/card gates.

## D03 — Preserve privacy, migration, and state decision gates

- Date: 2026-10-23.
- Authority: Attached SR-03–SR-05 and repository governance.
- Decision: Use synthetic data for verification. Preserve the registered 90-day session/artwork default as the current baseline, but do not invent unresolved purpose taxonomy, consent verification, purge guarantees, migration ordering, or `EndedEarly` semantics. Record a proposal and request the responsible decision before changing those rules.
- Consequence: No production child-data pilot or schema rollout can be claimed from local integration evidence.

## D04 — Modal test is conditional on an existing configured target

- Date: 2026-10-23.
- Authority: Direct owner request, ADR-0019, and the local environment preflight.
- Decision: Attempt a bounded synthetic request only when a deployed Modal endpoint, model/profile, authentication path, and spending limit are configured through local secret management. Do not deploy or provision paid GPU resources as part of this feature without an explicit profile/budget approval.
- Consequence: If those prerequisites remain absent, record a blocked live-provider test and complete only deterministic adapter/contract checks.

## D05 — Current FEAT-059 worktree is the source of truth for edits

- Date: 2026-10-23.
- Authority: User-provided AGENTS.md and current Git status.
- Decision: Continue on local `dev`; preserve its 96 pre-existing dirty/untracked entries, including FEAT-059 UI/backend cleanup. Do not reset, stash, merge, cherry-pick, commit, or push during this feature.
- Consequence: All edits must be targeted and listed in this feature’s evidence manifest.

## D06 — Child joins by QR/deep link and six-digit fallback

- Date: 2026-10-23.
- Authority: Direct owner reply to the integration clarification.
- Decision: Support both QR/deep link and a six-digit classroom code. Modal setup can follow the FE/BE integration.
- Consequence: The six-digit route is a new BE1 contract, not a relaxation of the existing high-entropy join payload. It must create only a pending join request, preserve explicit Teacher admission, and include uniqueness/expiry/throttle controls. If those controls cannot be proven, QR remains the only enabled path until the six-digit route is safe.

## D07 — Detailed API integration is plan-first

- Date: 2026-10-23.
- Authority: Direct owner instruction: “lên plan trc và ghi lại, đừng có làm ngay”.
- Decision: Prepare Plan revision 3 and API traceability artifacts before further code changes. Treat Plan revision 2 as the historical approval boundary; Plan revision 3 expands the design to a persisted shared SRS stage, numeric join, roster reads, completion outcomes, and stage-by-stage acceptance.
- Consequence: No additional implementation, tests, schema, migration, route, Modal call, or deployment is authorized by the planning request. New work proceeds after the owner reviews and approves the exact draft and BE1-owned contract/migration questions are resolved.

## D08 — Shared learning stage is separate from session lifecycle

- Date: 2026-10-23.
- Authority: Master SRS B5 and B19.4/B19.5; owner directed SRS-exact flow and approved preparing a BE contract proposal for review.
- Decision: Propose the exact shared-stage enum and separate completion outcome contract. Do not translate `/finish`'s persisted `finished` value into `Completed` or `EndedEarly`; do not conflate shared stage with individual membership progress.
- Consequence: `artifacts/BE1_SHARED_STAGE_CONTRACT_PROPOSAL.md` remains NOT IMPLEMENTED until its contract, guard matrix, idempotency/revision and migration approach are reviewed and approved.

## D09 — Six-digit entry is a shared room code

- Date: 2026-10-23.
- Authority: Direct owner clarification: “mã để vào phòng như quiz.com đồ ấy”.
- Decision: Treat six digits as the shared room code for the class, reusable by multiple children during the room's join window; it is not a one-time password or per-child identity token. QR and typed code lead to the same pending join/admission path.
- Consequence: Remove the proposed 10-minute expiry. Keep the room-code contract as a draft; Khoa/BE1 must review uniqueness, join-window/rotation, persistent anti-guess/spam controls, and authorized Teacher display before implementation.

## D10 — All admission paths close when the class starts

- Date: 2026-10-23.
- Authority: Direct owner replies: “Đóng mã khi bắt đầu lớp” and “Đóng cả QR và mã 6 số”.
- Decision: After the Teacher's start command succeeds, reject all new join requests through QR/deep-link or the shared six-digit code. Children already admitted keep their grants.
- Consequence: Add a post-start rejection check for both entry methods to the BE1 contract and verification matrix. The owner later confirmed atomic revocation of pending-at-start requests in D15; BE1 still reviews transaction/receipt semantics. The contract remains PROPOSED/NOT IMPLEMENTED.

## D11 — Persist a distinct early-stop outcome

- Date: 2026-10-23.
- Authority: Direct owner reply: “Có, cần phân biệt”, to whether a fully completed class and a class stopped early should have different saved outcomes.
- Decision: Product records must distinguish full completion (`completed`) from a Teacher stopping before completion (`ended_early`). This confirms the product meaning, not the API shape, mandatory reason fields, snapshot policy, or DB schema.
- Consequence: Existing `/finish` lifecycle value `finished` cannot by itself prove either outcome. FEAT-060 must propose a versioned result contract and BE1 must review it before implementation.

## D12 — Plan revision 3 approved for implementation within its gates

- Date: 2026-10-24.
- Authority: Direct project-owner reply: “tiến hành đi, duyệt”.
- Decision: Proceed with the detailed nine-stage BE/FE integration plan in `plan/PLAN_REV3_DETAILED_API_INTEGRATION_DRAFT.md`, using the exact approved hash recorded in `approvals/TASK_APPROVAL.md`.
- Consequence: Start with a preservation baseline and the existing versioned BE1 contracts. New stage, numeric-join, completion, roster, persistence, or migration behavior remains gated until the exact BE1 contract and migration approach are reviewed and approved; FEAT-057 and Modal gates remain unchanged.

## D13 — Implement and report only the currently adopted BE1 slice

- Date: 2026-10-24.
- Authority: D12 and the exact owner-approved Plan Rev3; repository contract/security rules.
- Decision: Connect the QR-based WF-01/WF-02 path only through existing BE1 v1 APIs. Keep the six-digit room code, shared SRS stage, completion outcome API, new roster contract, and schema/migrations unimplemented while their technical approvals are awaiting review. Product meanings are recorded in SRS v3.3; the six owner policy decisions are D15–D20.
- Consequence: Child/Teacher/Admin interfaces now issue the documented existing calls and show unsupported work as blocked. Local UI and isolated backend tests are evidence of mapping/contract behavior only; they are not represented as a live database-backed classroom flow.

## D14 — Treat 40 learners as a pilot target, not a hard admission rule

- Date: 2026-10-24.
- Authority: Owner-confirmed SRS source register `SRC-ANS4`, SRS v3.2 B17/OD12 and B20; it states one class with up to 40 concurrent children is a target that has not been benchmarked.
- Decision: Do not add a hard backend count rejection at 40 based on the current SRS. Keep capacity evidence as an unmeasured target; ask for a new owner decision before changing it into an admission cap.
- Consequence: No frontend-only count is treated as enforcement. A capacity/load run and device/network profile remain future evidence; no claim of 40-child support is made.

## D15 — Revoke pending admission requests at successful Start

- Date: 2026-10-24.
- Authority: Direct owner answer to the consolidated FEAT-060 contract-policy questions; recorded in SRS v3.3 B28.1.
- Decision: Atomically revoke every still-pending Child join request when Teacher Start succeeds. Child's next refresh returns `revoked`; already admitted grants remain.
- Consequence: BE1 must review transaction boundary, concurrent admit/start behavior, response/receipt and contract tests. No new API/schema/migration is implied by the product decision.

## D16 — Approve the shared room-code security policy

- Date: 2026-10-24.
- Authority: Direct owner answer; recorded in SRS v3.3 B28.2.
- Decision: Shared code stays active for the Lobby lifetime, Teacher may rotate before Start, generated with cryptographic randomness and collision checking, stored as a server-side keyed hash, generic invalid/closed response, and persistent throttling at 10 invalid attempts per source IP per 15 minutes.
- Consequence: BE1 must approve trusted-proxy/source-IP attribution, cross-replica persistence, key lifecycle, collision retry and audit behavior before implementing/enabling the route. If the approved threshold cannot be safely enforced, return an alternative to the owner.

## D17 — Use next-stage transitions and interleaved Assistance

- Date: 2026-10-24.
- Authority: Direct owner answer; recorded in SRS v3.3 B28.3.
- Decision: Teacher advances only to the next ordered stage after backend guards and a durable receipt. Assistance may interleave without moving the shared stage; Teacher may explicitly mark it `not_needed`. Arbitrary stage skips are forbidden.
- Consequence: Shared stage remains separate from lifecycle and per-group progress; route/schema/guard remain BE1 review items.

## D18 — Keep stage rewind disabled pending OD07 resolution

- Date: 2026-10-24.
- Authority: Direct owner answer; recorded in SRS v3.3 B28.4.
- Decision: Reject stage-return commands until OD07 is resolved.
- Consequence: This interim restriction does not settle the final pedagogical return policy; OD07 stays open in the SRS.

## D19 — Require a saved draft for unfinished group work

- Date: 2026-10-24.
- Authority: Direct owner answer; recorded in SRS v3.3 B28.5.
- Decision: Before advancing past an unfinished group, Teacher must select `save_draft`; retain the incomplete draft against its group without marking it complete or blocking other groups.
- Consequence: BE1 must review durable draft receipt, atomicity, recovery and read contract before implementation.

## D20 — Require an early-stop reason category

- Date: 2026-10-24.
- Authority: Direct owner answer; recorded in SRS v3.3 B28.6.
- Decision: `ended_early` requires `time`, `safety`, `technical`, or `other`; a short Teacher note is optional.
- Consequence: Completion outcome remains separate from lifecycle `finished`; BE1 must review exact fields, snapshot, guard and migration before implementation.

## D21 — Implement the owner-confirmed integration contracts

- Date: 2026-10-24.
- Authority: Direct project-owner instruction “implement”, after the six policy answers and prior direct instruction that the owner decides the FE/BE connection.
- Decision: Implement the local BE1/Child/Teacher scope and acceptance criteria in Plan Rev4, including the additive migration on the documented `be1_core` lineage. The exact plan hash and approval are recorded in `approvals/TASK_APPROVAL.md`.
- Consequence: The earlier implementation gate against these owner-confirmed semantics is superseded only for Rev4's stated scope. FEAT-057, live Modal, production DB/deploy, external review claims, and all other retained gates remain. PostgreSQL/proxy deployment verification must be evidenced separately.

## D22 — Enforce a true rolling room-code attempt window

- Date: 2026-10-24.
- Authority: D16's owner-approved limit of 10 invalid attempts per source IP per 15 minutes and Plan Rev4's rolling-window acceptance criterion.
- Decision: Persist only the recent invalid-attempt timestamps under the HMAC of the source IP; serialize each source with a PostgreSQL advisory transaction lock; expire attempts individually against `now - 15 minutes`. A valid code does not consume an attempt.
- Consequence: BE1 can enforce a sliding 15-minute window across processes instead of a fixed window anchored to the first attempt. The additive migration stores the bounded recent timestamp list as JSONB. Production proxy attribution remains a deployment review gate.
- Related integrity fix: the SQL outcome constraint explicitly requires a non-null allowed category for `ended_early`; SQL `CHECK` alone accepts `UNKNOWN`, so the explicit `IS NOT NULL` is required even though the request schema already rejects a missing category.
