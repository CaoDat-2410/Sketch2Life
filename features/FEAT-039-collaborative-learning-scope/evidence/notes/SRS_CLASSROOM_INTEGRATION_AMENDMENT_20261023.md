# SRS classroom integration amendment — evidence

- **Evidence ID:** E09
- **Date:** 2026-10-23 (Asia/Saigon)
- **Type:** Owner decision, source/document review, consistency check
- **Related approval:** FEAT-039 Plan Rev4, `approvals/TASK_APPROVAL.md`
- **Related SRS:** current `artifacts/Collaborative_Learning_SRS_v3.2.md` and canonical `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`; old `Collaborative_Learning_SRS_v3.1.md` remains preserved unchanged
- **Related integration evidence:** FEAT-060 `evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md`; proposed join/stage contracts under FEAT-060 `artifacts/`

## Authority and source

The owner directly requested: “ghi lại vào srs những điểm sửa đổi luôn nhé”. Exact v3.1 was preserved before editing at `features/FEAT-039-collaborative-learning-scope/artifacts/Sketch2Life_Master_SRS_v3.1_preserved_20261023.md`, SHA-256 `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`.

Owner-confirmed answers: both QR/deep-link and the shared six-digit room code close to new join requests when Teacher starts class; previously admitted devices retain their grants. The shared code is reused by multiple children and is not an OTP or child identity. The owner also confirms the saved product outcome must distinguish full completion from a Teacher stopping early.

## What changed in the SRS

- Published v3.2 from the exact v3.1 baseline; B27 records the amendment and targeted rows in B8/B17/B19/B20/B26 were reconciled to avoid contradiction.
- Recorded the room-code policy as `OWNER_CONFIRMED`: shared by the class, not an OTP, and closed for new joins through both QR/deep-link and numeric code when start succeeds; admitted children retain grants.
- Recorded the semantic outcome requirement as `OWNER_CONFIRMED`: full completion and Teacher early stop are distinct. API fields, guards, reason/evidence requirements and persistence remain for BE1 review.
- Clarified in plain Vietnamese that lifecycle `active` means a session is running, while a shared learning stage says which of the nine learning parts is active. Backend persistence/query/advance/CAS/event/schema details remain `PROPOSED_UNADOPTED`.
- Explained full completion versus a Teacher stopping early without treating current `/finish` lifecycle `finished` as proof of either. The product meaning is confirmed; the saved API/data contract awaits BE1 review.
- At this amendment's 2026-10-23 review point, FEAT-060 Plan Rev3 was still DRAFT; the owner approved its exact hash separately on 2026-10-24, as recorded in FEAT-060 `approvals/TASK_APPROVAL.md`.

## Verification and limits

- Preserved baseline SHA-256: `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`.
- At the 2026-10-23 amendment review, synchronized SRS v3.2 copies were byte-identical at SHA-256 `8CAB46A3E3D9C7E47B50AD39FD106E2B5CFD844945EA0FDFBA66986F25B03B00`. After FEAT-060 Rev3 was approved and implementation status was added to B27.4 on 2026-10-24, both current copies remain byte-identical at SHA-256 `9d7a71cc3fd0ab45b3175823c09780af0eb2e129d21a991d5470693dae25a21d`; the current static checker returned `DOCUMENTATION_VALID` with zero errors. Machine-readable results: `evidence/metrics/SRS_AMENDMENT_CHECKS_20261023.json` and `evidence/metrics/DOCUMENTATION_CHECK.json`.
- Review method: static documentation checker returned `DOCUMENTATION_VALID` (27 ordered sections, 66 FR, 38 use cases, 76 detailed acceptance criteria, 115 local links, no errors); canonical/feature copy hash check passed; targeted `git diff --check` produced no whitespace errors. No application tests were run or added.
- For the 2026-10-23 SRS amendment step, no product source/runtime/schema/migration/provider/deployment/Modal/Git publication action was taken. The documentation composer/checker was updated to preserve v3.1 and target v3.2. No application tests were run in that step. FEAT-060 implementation and checks occurred separately on 2026-10-24 under the later Rev3 approval.

## Clarifications sent to owner and answered

1. QR/deep-link after start? **Answered:** close both QR and six-digit code to new joins after start; already admitted children retain grants.
2. Should outcome distinguish “completed all required steps” from “Teacher stopped the class before it was complete”? **Answered:** yes, distinguish.

No product-level ambiguity remains on those two questions. Pending-request boundary handling and exact completion contract remain technical review items for BE1.

### Follow-up — 2026-10-24

The project owner subsequently answered the six outstanding classroom policy questions. SRS v3.3/B28 now records atomic pending-request revocation, shared-code controls and rate limit, stage/Assistance rules, the interim OD07 guard, required group `save_draft`, and early-stop reason category. This v3.2 amendment record remains historical; see `SRS_OWNER_DECISION_AMENDMENT_20261024.md` and the v3.3 current SRS. Technical BE1 contracts and migrations remain unadopted.
