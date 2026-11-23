# FR-C-08 planning record: lost drafts and current authority

**Status:** Historical reconciliation note; not an approval or implementation instruction.  
**Date:** 2026-11-18.

## Lost worktree artifacts

The former M2-S2 worktree `feature/feat063-m2-s2` was rolled back by removing only five verified task-created files. The FR-C-08 Lifecycle Contract Draft 3 and Implementation Allowlist Draft 5 were among those files and are no longer available in the current root checkout. Their contents must not be reconstructed as if they were reviewed artifacts.

The independent report `evidence/FR_C08_DRAFT3_DRAFT5_COLD_REVIEW_20261116.md` records that the reviewer stopped at the input-pin gate because one repeated SHA-256 value had 63 hexadecimal characters. The cited evidence file was 3,449 bytes; the report gives its verified 64-character SHA-256 as `42A94A0E228ED403A4FA234FA54E25D0B236083AE5686FA95165761FADFF0054`. The malformed value appears in the historical Draft 3 and Draft 5 registers. The report explicitly says the substantive document review did not occur. Its `CHANGES REQUIRED` verdict therefore records a failed pin gate, not a finding that the lost drafts' content was reviewed.

The review did not find a missing referenced file. It assessed the listed pin rows, but did not substantively assess the lost Contract Draft 3 or Allowlist Draft 5. The report is historical evidence only; it does not validate the new successor documents.

## Numbering and successor chain

The numbering intentionally skips the lost drafts. This rebuild creates **Lifecycle Contract Draft 4** as a successor to surviving Contract Draft 2, and **Implementation Allowlist Draft 6** as a successor to surviving Allowlist Draft 4. Draft 3 and Draft 5 are not recreated, silently repaired, or treated as approved.

The following surviving records are inputs to the current planning pass: Contract Draft 2, Allowlist Draft 4, Specification Draft 4, Lifecycle Plan Draft 4, the route-scope correction, Readiness Addendum Draft 2, and the named review evidence. Each input is pinned in the companion `tmp/frc08-wave1/PIN_AUDIT.md`.

## Current SRS and M2 status

D-209 adopts the current canonical SRS bytes as the single unsigned working SRS for FEAT-063. Older Rev60, Rev68, and Rev67 copies are historical and do not control this planning revision. D-209 states that prior D-208 lifecycle dispositions stand only where consistent with the adopted SRS, and leaves deletion eligibility for FAILED and ABANDONED runs open. The current lifecycle contract therefore does not copy the older Rev68/D-208 completed-delete selection as settled policy.

M2-S3 has since been accepted and M2 closed by the owner with recorded debt and deviations. The authoritative record is `approvals/TASK_APPROVAL.md` at the M2-S3 acceptance entry and `status/STATUS.md` at the matching 2026-11-18 entry. Older snapshots saying M2 was not closed predate that owner acceptance and are superseded for current status. Closure does not authorize FR-C-08 implementation, client work, a new gate, or a push. FR-C-08 remains unapproved. The OpenAPI P3, deferred M2-AT-09, and the absence of the cancel operation from the client-facing projection remain recorded debt.

## Boundary

This note records provenance and authority only. It creates no endpoint, schema, data mapping, owner assignment, migration, test ceiling, approval, or launch. The new Contract Draft 4 and Allowlist Draft 6 remain drafts until separately reviewed and approved.
