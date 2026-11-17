# Task approval

- Status: APPROVED
- Approver: Project owner (direct instruction in this conversation: “tiến hành nối backend với lại frontend, sau đó nếu đc thì có thể test thử modal xem có hoạt động ko”; expanded by “fix cả mấy cái này nữa, lên 1 plan fix và nối be fe tổng đi” for attached findings SR-01–SR-10; follow-up selected both QR and six-digit Child admission and deferred Modal setup until after integration).
- Approved scope: FEAT-060 Plan revision 2 in full, subject to its explicit owner/card/security/provider gates. Implement integration through existing versioned BE1 contracts, remediate supported SR-01–SR-10 items, and gather focused verification evidence. No implicit approval for production deployment, paid GPU provisioning, real child data, unresolved schema/state/purpose semantics, branch merge, commit, push, or tag.
- Plan revision: 2
- Approved plan SHA-256: 44233029F1929AF934A4CBD813FAE11945CF004396851DA1CB52968F694D97F3
- Approved at: 2026-10-23 (owner follow-up on QR + six-digit join and Modal setup order)
- Notes: The direct request authorizes the implementation scope described in the plan. Provider/live runtime work is limited to an already configured endpoint and synthetic input. Any missing Modal profile, migration decision, state decision, official class/project value, or owning-card approval remains a recorded gate.

## Approval addendum — Plan revision 3

- **Status:** APPROVED for the exact expanded plan below.
- **Approver:** Project owner, direct reply on 2026-10-24: “tiến hành đi, duyệt”.
- **Plan revision:** 3.
- **Plan file:** `plan/PLAN_REV3_DETAILED_API_INTEGRATION_DRAFT.md` (approved artifact; historical filename retained).
- **Approved plan SHA-256:** `777F364AFC9ED01456D4F60879BD8377111B6B15A754A6F7826153A767BD2FB4`.
- **Scope:** implement the detailed nine-stage BE1/Child/Teacher/Admin integration and remediation sequence in Plan Rev3; run the selected build/typecheck/lint and synthetic main-flow verification; preserve pre-existing dirty files and keep evidence feature-local.
- **Still gated:** exact BE1-owned schema/transition/migration decisions until reviewed and recorded; FEAT-057 cross-lane BE2 adoption; live Modal unless a configured endpoint/profile and spend limit are supplied; production deployment, paid GPU provisioning, real child data, merge/commit/push/tag, or other work excluded by Plan Rev3.
- **Owner-confirmed product behavior carried into this approval:** close both QR/deep-link and shared six-digit room-code entry to new requests after successful Teacher start; preserve already admitted grants; distinguish full completion from Teacher early stop. These do not approve unreviewed field names, schema, migration order, guard semantics, or handling of requests pending at the start boundary.

## Owner contract-policy answers — 2026-10-24

- The project owner answered all six consolidated policy questions on 2026-10-24; those answers authorize recording the policy in SRS v3.3 B28 and FEAT-060 D15–D20 under approved Plan Rev3.
- The earlier approval paragraph's note that the pending-at-start behavior was not yet confirmed reflects the state before those answers and is superseded by the atomic-revocation decision below.
- Confirmed: atomically revoke pending join requests on successful Start; approve the shared room-code lifecycle/security package including persistent 10-invalid/source-IP/15-minute throttling; next-stage-only transitions with interleaved/`not_needed` Assistance and no arbitrary skips; no rewind until OD07 is resolved; require `save_draft` for unfinished groups; require an early-stop category with optional note.
- This records project policy, not BE1 endpoint/schema/migration sign-off. BE1 owner review, FEAT-057 card approvals, and live Modal profile/config remain outstanding. No message to Khoa was sent.

## Implementation approval addendum — Plan revision 4

- **Status:** APPROVED for local implementation.
- **Approver:** Project owner, direct instruction on 2026-10-24: “implement”, following the six recorded policy decisions and prior direction that the owner decides the BE/FE connection.
- **Plan:** `plan/PLAN_REV4_IMPLEMENTATION_20261024.md`.
- **Plan SHA-256:** `61ECCDA79033BA5EBDE15FBA22B553B9D92C6947D2B224D5BA0EC686E984C11D`.
- **Scope:** additive BE1 contracts/migration on the documented `be1_core` lineage for shared room code and persistent throttle, atomic pending-grant revocation on Start, durable roster reads, next-stage-only SRS progression, unfinished-group draft disposition, distinct terminal outcomes; connect matching Child and Teacher UI paths and verify them as listed in Rev4.
- **Retained gates:** live/prod migration or deployment, external messaging, secrets, real child data, commit/push, Modal deployment/GPU/spend, FEAT-057 AI/video/activity adoption, and any claim of complete nine-stage product readiness or measured 40-child capacity.
- **Clarification:** this addendum authorizes this project's local implementation from the approved owner policy. It does not record that another engineer reviewed the code. Runtime proxy topology and PostgreSQL-backed verification remain explicit acceptance checks.

## Approval addendum — Plan revision 5: CI and Iteration 1 verification

- **Status:** APPROVED for the bounded CI and verification scope below.
- **Approver:** Project owner, direct reply on 2026-10-24: “Có, sau khi gate đạt,” answering whether CI preparation, Iteration 1 checks, BM02 on the final baseline, and creation of `review-2` after gates are authorized.
- **Plan:** `plan/PLAN_REV5_CI_AND_ITERATION1_VERIFICATION_20261024.md`.
- **Plan SHA-256:** `41A8068A61AE706507883736BC7AB5E8310C11E392CF22745779F997162E7CFF`.
- **Scope:** inspect and add a credential-free GitHub Actions workflow using existing locked dependencies/check commands; run and record current baseline checks; inspect and run reproducible independent fixture/contract runners under ADR-0006; distinguish offline evidence from runtime/FE-to-BE acceptance.
- **Retained gates:** no product runtime, schema/migration, provider, secret, real child data, live database, deployment, or end-to-end claim. The `review-2` tag is allowed only after all CI, Iteration 1, document QA, clean-tree, and security gates pass at one exact commit.
