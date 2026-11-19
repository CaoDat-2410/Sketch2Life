# FR-C-08 planning record: lost drafts, authority, and successor chain — Revision 5

**Status:** Historical reconciliation note; not an approval or implementation instruction.
**Date:** 2026-11-19.

## 1. Unavailable artifacts and provenance

Lifecycle Contract Draft 3 and Implementation Allowlist Draft 5 are unavailable in the current root checkout. The claim that a prior rollback removed task-created files comes from the owner-provided rollback report in an earlier session and is not independently recorded as a versioned repository artifact. This note does not reconstruct or attest to the missing contents.

The pin-gate review is evidence/FR_C08_DRAFT3_DRAFT5_COLD_REVIEW_20261116.md. Its pin register begins at line 36. It records a stop at the input-pin gate because one SHA-256 string had an invalid length (63 hexadecimal characters), and it says the substantive review stopped at that failed gate. Its CHANGES REQUIRED result is therefore a pin-gate result, not a content verdict on the unavailable documents. Other historical reviews apply only to the exact artifacts and pins each names.

Numbering intentionally skips unavailable documents: Lifecycle Contract Draft 4 succeeded Contract Draft 2, and Implementation Allowlist Draft 6 succeeded Allowlist Draft 4. Lifecycle Contract Draft 8 succeeds Draft 7; Implementation Allowlist Draft 10 succeeds Draft 9; Owner Questions Revision 5 succeeds Revision 4; this note succeeds Revision 4. No missing draft is recreated or represented as reviewed.

## 2. Current authority and D-214

D-209 names the canonical FEAT-063 SRS as the single unsigned working SRS. Its current hash is recorded in the successor contract and allowlist. Earlier Rev60, Rev67, and Rev68 files are historical requirements sources. The Data Table Register is a companion model source.

D-214 adds owner planning dispositions to D-208 and D-209 and changes none of their prior items. It permits explicit user-requested deletion for COMPLETED, FAILED, and ABANDONED, with no automatic purge for FAILED or ABANDONED, while requiring a separate documentation-only SRS alignment before implementation. It selects Parent-only first scope, an existing-GET lifecycle projection, a typed Parent-scope DTR/schema delta, shared access/worker fencing, owner acknowledgements and reference closure, a DTR audit matrix, and acceptance of M2 closure for D-208 item 8. It grants no implementation or launch authority.

The current D-214 file is an uncommitted root working-tree change, 240,776 bytes / SHA-256 6E30C69B5E43C2124B9083B6904FEEAE80D7BCEE0917C635F381BA518D32C723. It is not present in the DECISIONS.md blob at provisional base 2dddc607, whose historical pin is recorded separately. Do not claim the provisional base contains D-214.

## 3. Surviving predecessor documents

| Predecessor | Current relevance |
|---|---|
| Implementation Spec Draft 4 | Still reads deletion eligibility from Rev68/D-208, including explicit DELETE for FAILED and ABANDONED. It is historical input and is not the current policy; D-214 item 1 now answers the eligibility question. |
| Lifecycle Plan Draft 4 | Still carries the D-208/Rev68 eligibility reading. It is historical input and is not the current policy. |
| Contract Draft 2 and Allowlist Draft 4 | Surviving predecessor records. Their pins and current observations were rechecked in the earlier local register PIN_AUDIT_R4.md. |

The canonical SRS at the D-209 path supersedes earlier Rev60, Rev67, and Rev68 copies for current requirements. The Data Table Register is a companion model source and does not override that SRS.

## 4. CONV-1 provenance and M2 gate

D-214 records the local, never-pushed branch feature/feat066-conv1 at commit 2dddc607 or later, parent 08439b22, as the provisional base after owner confirmation. The exact commit must be named later and all shared paths re-pinned. Read-only inspection confirms D-066-71, its Task Approval entry, and implementation evidence are present on commit 2dddc607. This note does not approve or integrate that branch.

D-214 item 11 selects that the owner-accepted M2 closure and limitation ledger satisfy D-208 item 8. The closure is recorded at approvals/TASK_APPROVAL.md lines 3243-3247 and status/STATUS.md line 876; line 873 of that status file is a stale snapshot that predates the owner acceptance. M2 approvals, allowlists, command ceilings, and evidence do not transfer. Re-pin FR-C-08 paths at the exact base selected under Q-BASE. The exact base and the relationship of the uncommitted D-214 record to that base remain to be pinned before implementation approval.

## 5. Local pin audit boundary

PIN_AUDIT_R6.md is a local, git-ignored scratch register under tmp/frc08-wave1/. It is not a durable repository record and must not be cited as committed evidence. It rehashes predecessor rows and candidate path pins; it does not establish semantic correctness, runtime behavior, approval, or database state.

## 6. Revision history

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
| R3-F1 | Restored section signs in the successor contract, owner questions, and allowlist. The SRS line 1164 quotation in Owner Questions Revision 4 now ends exactly with §9.5–§9.7; §22.4; NFR-05/10 \|. |
| R3-F2 | Re-pinned source ranges at the provisional base: be1_models.py:555-578; be1_common.py:88-156; be1_registry.py:107-125. |
| R3-F3 | Corrected history: Draft 6 listed four model/table paths as E; Draft 7 moved them to H; Draft 8 kept them H. Draft 8 added four H references: be1_common.py, be1_registry.py, openapi_contract_amendments.py, and openapi_srs_v22.py. |
| R3-F4 | Kept the Contract source-facts table contiguous with no blank row and removed malformed inline-code delimiters from successor prose. |
| R3-F5 | Recomputed and listed five CONV-1 overlaps: app.py and test_openapi_contract_catalog.py as E; be1_common.py, be1_registry.py, and openapi_contract_amendments.py as H. |
| R3-F6 | Removed stale process wording. Recorded D-066-71, the CONV-1 approval entry, and implementation evidence at local commit 2dddc607; required re-pinning after the exact base is named. |
| R3-F7 | Attributed INVALID_IDEMPOTENCY_KEY to SRS §21.4; attributed HTTP 400 to D-200 and M2 source. |
| R3-F8 | Added the StoryRun-lite demo cancel source fact and classified it H, separate from the Parent product operation. |
| R3-F9 | Reconciled the allowlist to 54 candidate/reference path pins and included openapi_contract.py and M2_S2_IMPLEMENTATION_REPORT_20261114.md in both the H list and refreshed local audit. |
| R3-F10 | Added the explicit local, git-ignored, non-durable caveat for the pin audit. |
| R4-F1 | Restored four source facts in Lifecycle Contract Draft 8 section 4, each re-read at base 2dddc607: the organization-scoped AI Jobs cancellation notice (ai_jobs.py port, lines 249-257); the Idempotency-Key range mismatch (five Parent routes at max_length=256 against the CONV-1 range of 1 to 128 at api_conventions.py:67); the cancel persistence row with the transport conventions (new section 4.1); and the existing owner-scoped GET (parent_story_runs.py:232-250). |
| R4-F2 | Carried D-214 item 11 into Lifecycle Contract Draft 8 section 1 (M2 approvals, allowlists, and command ceilings do not transfer) and cited approvals/TASK_APPROVAL.md lines 3243-3247 and status/STATUS.md line 876 in the contract, in Owner Questions Revision 5 Q-M2-GATE, and in section 4 of this note. |
| R4-F3 | Cited be1_common.py:88-156 (the helper at the base) in the contract and in the R3-F2 row above, and removed the 83-138 sentence. |
| R4-F4 | Allowlist Draft 10 section 8 now says Draft 8's two root-checkout FEAT-066 pins are not carried because CONV-1 changes both files. |
| R4-F5 | Classified api_conventions.py and error_envelope.py (added by CONV-1) and bounded_image_upload.py (modified by CONV-1) as H references with base pins in Allowlist Draft 10; counts are now 57 path rows (22 E, 6 D, 29 H) and eight CONV-1 overlaps. |
| R4-F6 | Owner Questions Revision 5 now says the SRS is read together with D-214 and that D-214 amends nothing in the SRS; the Q-BASE disposition copies D-214 item 10 (local, never-pushed branch, commit 2dddc607 or later, after the owner confirms CONV-1, exact commit named when the base is fixed). |
| R4-F7 | Named the pin-gate review file in section 1, restored the predecessor table (section 3) and the earlier history rows, and appended these rows. |
| R4-F8 | Added a blank line before the contract source-facts table; removed the self-referential history sentence from the allowlist; cited story_run_lite.py:193-208; stated that the pin audit register is local, git-ignored, and not a durable repository record wherever the allowlist names it. |

## 7. Boundary

These successors record planning provenance only. They create no route, schema, state, DTR row, migration, owner assignment, command ceiling, approval, launch, or implementation authorization. No existing file was edited.
