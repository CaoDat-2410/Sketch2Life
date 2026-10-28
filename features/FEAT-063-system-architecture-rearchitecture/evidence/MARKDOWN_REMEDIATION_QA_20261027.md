# Markdown consistency review — 2026-10-27

Historical evidence for the Q01–Q126 / plan-revision-9 review. Its counts and status are superseded by `FOLLOWUP_REMEDIATION_QA_20261027.md` (EV-063-08), which records the controlling Q127–Q133 baseline.

## Scope

Static review of the Vietnamese SRS, data-table register, feature plan/approval/status/context/decisions, and proposed ADR-0021 after reconciling owner answers through Q126. This evidence does not authorize implementation or final diagram/PDF production.

## Reconciled decisions

- Q122: `VIDEO_READY` remains an active run until the adult explicitly completes or regenerates it; completion is not a video approval.
- Q123: an adult may cancel an unfinished run. Cancellation releases the active-run lock immediately and starts lifecycle deletion. Accepted quota is not refunded, and a successful Teacher sample claim remains consumed.
- Q124 and the initial Q125 interpretation are historical only. D-56 is explicitly superseded by D-57.
- Q126 finalizes quota lifetime: unused monthly included quota expires at calendar-month end in `Asia/Ho_Chi_Minh`; purchased top-up quota carries forward until consumed. Allocation remains current-month included grant first, then purchased grants FIFO.
- Parent and Teacher quota scopes remain separate. An accepted full-video request consumes one unit even if it later fails technically or is safety-blocked; scene retries do not consume another unit. Mid-month eligible accounts receive the full included allowance for that month.

## Static checks

- Plan revision is 9; approval revision is 9 and its recorded SHA-256 matches the plan: `7874B033034E19BB6B1205EBD0B53779DA330C5012004333D380CC49423C5A55`.
- No pending Q122–Q124 marker remains in current SRS, register, context, decisions, status or ADR records.
- SRS and data register contain zero Unicode replacement characters. SRS table-of-contents entries and section anchors both number 30 and match in order.
- Unique SRS requirement definitions: 40 BR, 70 FR, 23 NFR and 21 AC; no duplicate IDs were found.
- The SRS and data register contain no final Mermaid blocks. Historical draft diagrams remain identified as unapproved and are not part of the review baseline.
- Table arithmetic remains 86 declared production mappings = 51 active existing/refactored + 35 read-only legacy; 38 proposed new tables produce 89 active and 124 physical including legacy.
- `story.runs` does not declare a duplicated mutable `active_flag`; active-run uniqueness is derived from the durable run state.

## Work not performed

No product tests/builds, database access or migration, provider/payment/Modal calls, deployment, real-child data processing, final diagram generation, or PDF generation was performed. Final diagrams and PDF remain gated on the owner's explicit approval of both Markdown files.
