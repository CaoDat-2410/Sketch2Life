# FR-C-08 planning record: lost drafts, authority, and successor chain

**Status:** Historical reconciliation note; not an approval or implementation instruction.
**Date:** 2026-11-18.

## 1. Lost worktree artifacts and provenance

Lifecycle Contract Draft 3 and Implementation Allowlist Draft 5 are unavailable in the current root checkout. The claim that a prior rollback removed five task-created files comes from the owner-provided rollback report in the earlier session. That report is not recorded as a versioned artifact in this checkout, so the rollback claim is not independently evidenced here. This note does not reconstruct or attest to the missing files' contents.

The historical review `evidence/FR_C08_DRAFT3_DRAFT5_COLD_REVIEW_20261116.md` records a stop at the input-pin gate because one SHA-256 string had an invalid length. It says the substantive contents of the lost drafts were not reviewed. Its `CHANGES REQUIRED` result is therefore a pin-gate result, not a content verdict on Draft 3 or Draft 5. The separate 2026-11-15 Draft 3 review evidence also applies only to the artifact and pin it names.

Numbering intentionally skips the unavailable drafts. Lifecycle Contract Draft 4 succeeded Contract Draft 2; this note's next successor is Lifecycle Contract Draft 5. Implementation Allowlist Draft 6 succeeded Allowlist Draft 4; this note's next successor is Allowlist Draft 7. No missing draft is recreated or treated as reviewed.

## 2. Current authority and prior D-208 directions

D-209 adopts the canonical FEAT-063 SRS as the single unsigned working SRS. It says the prior D-208 FR-C-08 planning dispositions stand only where consistent with the adopted copy. D-209 item 4 leaves open whether UC-07 and §21.2 deletion of a run that is “đã hoàn tất” includes FAILED and ABANDONED as well as COMPLETED. The answer remains an owner question; this note does not carry forward D-208 item 6 as settled current policy.

D-208 item 8 separately required reconciliation and pinning of the partial, dirty M2 baseline before FR-C-08 implementation. M2-S3 was later accepted and M2 closed with recorded debt and deviations. Whether that accepted closure satisfies the D-208 item 8 coordination gate remains OPEN for owner disposition; this note does not infer that it does or does not.

## 3. Surviving predecessor documents

| Predecessor | Current relevance |
|---|---|
| Implementation Spec Draft 4 | Still reads deletion eligibility from Rev68/D-208, including explicit DELETE for FAILED and ABANDONED. It is historical input and is not the current policy. |
| Lifecycle Plan Draft 4 | Still carries the D-208/Rev68 eligibility reading. It is historical input and is not the current policy. |
| Contract Draft 2 and Allowlist Draft 4 | Surviving predecessor records. Their pins and current observations are rechecked in the R3 pin audit. |

The canonical SRS at the D-209 path supersedes earlier Rev60, Rev67, and Rev68 copies for current requirements. The Data Table Register is a companion model source and does not override that SRS.

## 4. M2 closure and current CONV-1 coordination evidence

The current M2 closure is recorded in the FEAT-063 approval ledger at lines 3243–3247 and in `status/STATUS.md` at line 876. The text at line 873 saying M2 is not closed is an earlier snapshot and predates the owner's acceptance. M2 closure with debt does not authorize FR-C-08 implementation, client integration, or transfer of M2 approvals and command ceilings.

The historical M2-S2 worktree branch `feature/feat063-m2-s2` remains present at commit `bc124187d3b700de62d7f932e3cd10490b82d80c`. Its existence is branch provenance only; it does not establish the separate D-208 item 8 gate as satisfied.

The current root checkout's FEAT-066 `DECISIONS.md` contains D-066-68 through line 405; that entry says CONV-1 still needs its own Task Approval. The inspected `TASK_APPROVAL.md` contains a MGR-7 approval entry at lines 366–374, but no CONV-1-specific approval entry was found. D-066-71, the named CONV-1 implementation package, and its implementation evidence were not present at their expected root-checkout paths during this observation. Both governance files are tracked and clean in this checkout at the time of observation. Therefore the requested later CONV-1 approval/launch status and exact approved file set are not verified from this checkout. Do not label CONV-1 approved, unapproved, launched, or not launched from the missing records. The R1 finding and R3 task prompt contain claims that are not substantiated by the current root records; preserve the discrepancy. FR-C-08 still needs an owner decision about its own implementation base and sequencing relative to any CONV-1 commit and integration.

The local-only R3 pin audit is a companion verification artifact, not a source of product requirements. The successor allowlist carries the pins for its candidate files; the audit records the broader input/reference rehashes and marks the FEAT-066 records as current root-checkout observations. It does not establish a CONV-1 approval or implementation state.

## 5. Boundary

This note records provenance and current planning context only. It creates no route, schema, state, owner assignment, migration, test ceiling, approval, launch, or implementation authorization. All FR-C-08 decisions remain open until the owner records them and a separate exact approval and launch instruction is issued.
