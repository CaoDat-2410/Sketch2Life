# FR-C-08 planning record: lost drafts, authority, and successor chain — Revision 4

**Status:** Historical reconciliation note; not an approval or implementation instruction.
**Date:** 2026-11-18.

## 1. Unavailable artifacts and provenance

Lifecycle Contract Draft 3 and Implementation Allowlist Draft 5 are unavailable in the current root checkout. The claim that a prior rollback removed task-created files comes from the owner-provided rollback report in an earlier session and is not independently recorded as a versioned repository artifact. This note does not reconstruct or attest to the missing contents.

The surviving historical pin-gate review states that its stop was caused by an invalid-length digest and was not a content verdict on the unavailable documents. Other historical reviews apply only to the exact artifacts and pins each names.

Numbering intentionally skips unavailable documents. Lifecycle Contract Draft 7 succeeds Draft 6; Implementation Allowlist Draft 9 succeeds Draft 8; Owner Questions Revision 4 succeeds Revision 3; this note succeeds Revision 3. No missing draft is recreated or represented as reviewed.

## 2. Current authority and D-214

D-209 names the canonical FEAT-063 SRS as the single unsigned working SRS. Its current hash is recorded in the successor contract and allowlist. Earlier Rev60, Rev67, and Rev68 files are historical requirements sources. The Data Table Register is a companion model source.

D-214 adds owner planning dispositions to D-208 and D-209 and changes none of their prior items. It permits explicit user-requested deletion for COMPLETED, FAILED, and ABANDONED, with no automatic purge for FAILED or ABANDONED, while requiring a separate documentation-only SRS alignment before implementation. It selects Parent-only first scope, an existing-GET lifecycle projection, a typed Parent-scope DTR/schema delta, shared access/worker fencing, owner acknowledgements and reference closure, a DTR audit matrix, and acceptance of M2 closure for D-208 item 8. It grants no implementation or launch authority.

The current D-214 file is an uncommitted root working-tree change, 240,776 bytes / SHA-256 6E30C69B5E43C2124B9083B6904FEEAE80D7BCEE0917C635F381BA518D32C723. It is not present in the DECISIONS.md blob at provisional base 2dddc607, whose historical pin is recorded separately. Do not claim the provisional base contains D-214.

## 3. CONV-1 provenance and M2 gate

D-214 records the local, never-pushed branch feature/feat066-conv1 at commit 2dddc607 or later, parent 08439b22, as the provisional base after owner confirmation. The exact commit must be named later and all shared paths re-pinned. Read-only inspection confirms D-066-71, its Task Approval entry, and implementation evidence are present on commit 2dddc607. This note does not approve or integrate that branch.

D-214 selects that the owner-accepted M2 closure and limitation ledger satisfy D-208 item 8. M2 approvals, allowlists, command ceilings, and evidence do not transfer. Re-pin FR-C-08 paths at the exact base selected under Q-BASE. The exact base and the relationship of the uncommitted D-214 record to that base remain to be pinned before implementation approval.

## 4. Local pin audit boundary

PIN_AUDIT_R5.md is a local, git-ignored scratch register under tmp/frc08-wave1/. It is not a durable repository record and must not be cited as committed evidence. It rehashes predecessor rows and candidate path pins; it does not establish semantic correctness, runtime behavior, approval, or database state.

## 5. Revision history

| Finding | Successor correction |
|---|---|
| R3-F1 | Restored section signs in the successor contract, owner questions, and allowlist. The SRS line 1164 quotation in Owner Questions Revision 4 now ends exactly with §9.5–§9.7; §22.4; NFR-05/10 \|. |
| R3-F2 | Re-pinned source ranges at the provisional base: be1_models.py:555-578; be1_common.py:83-156; be1_registry.py:107-125. The shorter 83-138 range is not the complete helper at this base. |
| R3-F3 | Corrected history: Draft 6 listed four model/table paths as E; Draft 7 moved them to H; Draft 8 kept them H. Draft 8 added four H references: be1_common.py, be1_registry.py, openapi_contract_amendments.py, and openapi_srs_v22.py. |
| R3-F4 | Kept the Contract source-facts table contiguous with no blank row and removed malformed inline-code delimiters from successor prose. |
| R3-F5 | Recomputed and listed five CONV-1 overlaps: app.py and test_openapi_contract_catalog.py as E; be1_common.py, be1_registry.py, and openapi_contract_amendments.py as H. |
| R3-F6 | Removed stale process wording. Recorded D-066-71, the CONV-1 approval entry, and implementation evidence at local commit 2dddc607; required re-pinning after the exact base is named. |
| R3-F7 | Attributed INVALID_IDEMPOTENCY_KEY to SRS §21.4; attributed HTTP 400 to D-200 and M2 source. |
| R3-F8 | Added the StoryRun-lite demo cancel source fact and classified it H, separate from the Parent product operation. |
| R3-F9 | Reconciled the allowlist to 54 candidate/reference path pins and included openapi_contract.py and M2_S2_IMPLEMENTATION_REPORT_20261114.md in both the H list and refreshed local audit. |
| R3-F10 | Added the explicit local, git-ignored, non-durable caveat for the pin audit. |

## 6. Boundary

These successors record planning provenance only. They create no route, schema, state, DTR row, migration, owner assignment, command ceiling, approval, launch, or implementation authorization. No existing file was edited.
