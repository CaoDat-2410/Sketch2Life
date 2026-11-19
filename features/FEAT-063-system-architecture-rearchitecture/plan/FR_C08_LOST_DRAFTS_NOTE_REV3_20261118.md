# FR-C-08 planning record: lost drafts, authority, and successor chain — Revision 3

**Status:** Historical reconciliation note; not an approval or implementation instruction.
**Date:** 2026-11-18.

## 1. Lost worktree artifacts and provenance

Lifecycle Contract Draft 3 and Implementation Allowlist Draft 5 are unavailable in the current root checkout. The claim that a prior rollback removed five task-created files comes from the owner-provided rollback report in the earlier session. That report is not recorded as a versioned artifact in this checkout, so the rollback claim is not independently evidenced here. This note does not reconstruct or attest to the missing files' contents.

The historical review `evidence/FR_C08_DRAFT3_DRAFT5_COLD_REVIEW_20261116.md` records a stop at the input-pin gate because one SHA-256 string had an invalid length. It says the substantive contents of the lost drafts were not reviewed. Its `CHANGES REQUIRED` result is therefore a pin-gate result, not a content verdict on Draft 3 or Draft 5. The separate 2026-11-15 Draft 3 review evidence also applies only to the artifact and pin it names.

Numbering intentionally skips the unavailable drafts. Lifecycle Contract Draft 4 succeeded Contract Draft 2; this note's next successor is Lifecycle Contract Draft 5. Implementation Allowlist Draft 6 succeeded Allowlist Draft 4; this note's next successor is Allowlist Draft 7. No missing draft is recreated or treated as reviewed.

## 2. Current authority and prior D-208 directions

D-209 adopts the canonical FEAT-063 SRS as the single unsigned working SRS. It says the prior D-208 FR-C-08 planning dispositions stand only where consistent with the adopted copy. D-209 item 4 leaves open whether UC-07 and `21.2 deletion of a run that is “đã hoàn tất” includes FAILED and ABANDONED as well as COMPLETED. The answer remains an owner question; this note does not carry forward D-208 item 6 as settled current policy.

D-208 item 8 separately required reconciliation and pinning of the partial, dirty M2 baseline before FR-C-08 implementation. M2-S3 was later accepted and M2 closed with recorded debt and deviations. Whether that accepted closure satisfies the D-208 item 8 coordination gate remains OPEN for owner disposition; this note does not infer that it does or does not.

## 3. Surviving predecessor documents

| Predecessor | Current relevance |
|---|---|
| Implementation Spec Draft 4 | Still reads deletion eligibility from Rev68/D-208, including explicit DELETE for FAILED and ABANDONED. It is historical input and is not the current policy. |
| Lifecycle Plan Draft 4 | Still carries the D-208/Rev68 eligibility reading. It is historical input and is not the current policy. |
| Contract Draft 2 and Allowlist Draft 4 | Surviving predecessor records. Their pins and current observations are rechecked in `PIN_AUDIT_R4.md`. |

The canonical SRS at the D-209 path supersedes earlier Rev60, Rev67, and Rev68 copies for current requirements. The Data Table Register is a companion model source and does not override that SRS.

## 4. M2 closure and CONV-1 coordination

The current M2 closure is recorded in the FEAT-063 approval ledger at lines 3243–3247 and in `status/STATUS.md` at line 876. The text at line 873 saying M2 is not closed is an earlier snapshot and predates the owner's acceptance. M2 closure with debt does not authorize FR-C-08 implementation, client integration, or transfer of M2 approvals and command ceilings.

The historical M2-S2 worktree branch `feature/feat063-m2-s2` remains present at commit `bc124187d3b700de62d7f932e3cd10490b82d80c`. Its existence is branch provenance only; it does not establish the separate D-208 item 8 gate as satisfied.

The current root checkout's FEAT-066 `DECISIONS.md` contains D-066-68 through line 405, which says CONV-1 still needs its own Task Approval. The root `TASK_APPROVAL.md` contains the MGR-7 approval entry but no CONV-1-specific entry. D-066-71, the named CONV-1 implementation package, and its implementation evidence are not present at their expected root-checkout paths. These are root-checkout observations only.

Owner-provided coordination context and the 2026-11-18 cold-review record identify the local, never-pushed branch `feature/feat066-conv1` in worktree `.worktrees/conv1` at commit `2dddc6076c793b44cbcd5c0fa3e02a4ccc9902df`, parent `08439b22fc3c1f34786a3f45f34530075a3914e0`. Read-only local Git inspection confirmed commit identity, parent, worktree, and changed-path set; this pass did not independently inspect or approve that branch's implementation evidence. The root checkout's lack of CONV-1 records therefore does not imply their absence from the local CONV-1 branch.

The owner's queue order is CONV-1, then FR-C-08, then SEED-1 across local-only branches. This records sequencing context, not an owner decision about the exact FR-C-08 base or integration commit. Q-BASE remains open; no approval, launch, or exact implementation base is selected here.

## Revision history

| Finding ID | Successor disposition |
|---|---|
| R2-F1 | Corrected the Teacher source claim in Lifecycle Contract Draft 6, Owner Questions Revision 3, and Allowlist Draft 8; added assignment sources as H references in §6.1 and the refreshed pin audit. |
| R2-F2 | Split UC-11 and worker-check attribution in Lifecycle Contract Draft 6 §3.1; attributed the worker check to SRS line 1797 and labelled the purge-proof statement as coordinator interpretation. |
| R2-F3 | Reconciled root-checkout facts with the local CONV-1 branch and owner queue in this note, Owner Questions Revision 3 Q-BASE, and Allowlist Draft 8 §1. |
| R2-F4 | Replaced the CONV-1 overlap table in Allowlist Draft 8 §1 with the derived E-path intersection and chosen-base recheck rule. |
| R2-F5 | Removed review-round process labels from successor prose; this table is the sole finding-ID trace. |
| R2-F6 | Added exact SRS lines 270, 284, and 503 to Owner Questions Revision 3 Q-A, including the explicit unresolved eligibility statement. |
| R2-F7 | Added the fixed pending response and client-facing projection facts to Lifecycle Contract Draft 6; linked Q-READ option B to Q-STATES. |
| R2-F8 | Added the SRS state-inventory citation, corrected the model source range, and classified additional OpenAPI modules as H. |
| R2-F9 | Reclassified four H-only sources in PIN_AUDIT_R4.md and aligned counts with Allowlist Draft 8 §6.1. |

## 5. Boundary

This note records provenance and current planning context only. It creates no route, schema, state, owner assignment, migration, test ceiling, approval, launch, or implementation authorization. All FR-C-08 decisions remain open until the owner records them and a separate exact approval and launch instruction is issued.
