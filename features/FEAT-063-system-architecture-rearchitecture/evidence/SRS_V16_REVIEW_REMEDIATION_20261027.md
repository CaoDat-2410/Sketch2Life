# FEAT-063 — SRS v1.5 follow-up review remediation

**Evidence ID:** EV-063-09  
**Date:** 2026-10-27 (Asia/Saigon)  
**Scope:** Documentation reconciliation only; no runtime code, schema, database, product tests, builds, provider calls, benchmark, migration or deployment.

## Outcome

The review findings were incorporated into the Vietnamese SRS v1.6-draft, `DATA_TABLE_REGISTER.md`, proposed ADR-0021, feature plan and records. A second static pass found and corrected an NFR trace-table alignment defect before owner review. The documents remain drafts awaiting owner review. Final diagrams and PDF remain explicitly deferred until the owner approves both Markdown baselines.

## Finding disposition

| Review finding | SRS/register resolution | Status / remaining gate |
|---|---|---|
| Teacher access after class reassignment conflicted between “creator” and new assignment | Current responsible Teacher receives historical run/media access; old Teacher and playback tokens are revoked immediately; `created_by` is provenance only; assignment and audit rules are reflected in BR-06, FR-T-14, permissions, UC-12, risk R-06 and Q130 traceability. | Documentation resolved; no live authorization test run. |
| Quota ownership crossed Billing, AI Policy and Story; no-refund cost risk | Billing owns quota grants and immutable usage. AI Policy owns compute reservation/metering; Story stores opaque refs. Persist `ADMISSION_PENDING`, reserve worst-case compute under idempotency/lease, record Billing usage in its own transaction, reconcile ambiguous outcomes and dispatch only after receipts. Accepted requests remain non-refundable per Q128; emergency abort remains an explicit risk. | Architecture resolved; unit economics and configured GPU caps await synthetic benchmark. |
| Adult-wait run lock could persist; completion data retention was unbounded | All adult-wait states notify at 144 hours and close at 168 hours; `VIDEO_READY` completes, other review states abandon; active AI jobs have a separate 6-hour deadline. Content remains until user deletion for synthetic demo; production use is blocked pending maximum retention and backup deletion policy. | Product rule reconciled; privacy/legal/production gate remains open. |
| ASR/VLM state and push delivery were underspecified | `INPUT_PROCESSING` and separate run/job/generation states expose ASR/VLM progress; admission reconciliation is not adult-wait. Inbox is authoritative; Web Push is selected for browser; Android provider is unselected pending device/distributor POC. Firebase Messaging remains excluded by repository governance. | State contract documented; Android delivery POC remains open. |
| Teacher offboarding/reassignment could orphan media | Active class requires responsible Teacher; reassignment transfers authorized access, revokes old access, keeps creator provenance and rejects conflict with target Teacher's active run. | Documentation resolved; implementation and security verification pending. |
| Legal/privacy architecture was delayed | SRS adds a production gate for organization/platform roles, DSR, incident response, cross-border provider transfer, retention, backup expiry/deletion, DPIA applicability, legal review, Play Families, hosting and payment/tax. No legal conclusion is asserted. | Must be completed with privacy/legal/accounting owners before real-child data or production. |
| Quota ledger ownership was split and transaction semantics unclear | SRS, register and ADR assign product quota ledger to Billing. Compute reservation and Billing admission are separate owner transactions coordinated by an idempotent application saga; there is no cross-module SQL or distributed DB transaction. | Architecture resolved; contract/chaos verification not run. |
| Missing SRS wrapper, requirement metadata and traceability | Added stakeholders/personas, system boundary/context, sign-off and revision register, phases, priority/verification/status metadata, per-ID FR/NFR/BR matrices, GWT acceptance AC-01–AC-29, edge cases AT-01–AT-10, consolidated issues and probability/impact/owner/treatment risk register. | Draft complete for owner review; formal standards conformance is not claimed. |
| Cost caps could interrupt an already charged generation | Reserve worst-case request GPU budget before Billing admission; ordinary daily-cap exhaustion closes new admission and cannot cut reserved jobs. Emergency safety/operator abort can still terminate an admitted request without quota refund. | Rule documented; the residual Q128 risk is explicit in R-18 and must be explained before confirmation. |
| Platform/technical topics lacked verification detail | Added SLO/RPO/RTO targets as unmeasured proposals, storage-capacity formula, WCAG 2.2 AA/WCAG2ICT targets, Android API 29/browser matrix, workflow-engine comparison gate, security threat-model/MFA/RLS/Play Integrity/AV requirements, PII masking, fairness/cost controls, billing/tax gates and sandbox contract gates. | Targets remain proposals until owner/operations/benchmark evidence exists. |
| Upload interruption on mobile could force re-upload | Added resumable API upload sessions, chunk digest/idempotency, resume state and progress, bounded expiry, private quarantine and AV/hash/media validation. Session state extends existing `core_asset_metadata`; no new table or count change. Mobile/browser clients receive no storage credentials or endpoint. | Adapter semantics and reconnect/replay/abort behavior remain synthetic POC OI-18. |
| Error-code and status mapping had obsolete scope codes | Standardized ID unknown/out-of-scope as identical 404; 403 is only an in-scope known-resource action denial; role conflict does not reveal UID; stale scope-specific codes removed; upload conflict/expiry/checksum codes added. | Static document inspection only; no API implementation/test run. |
| Requirement priorities and trace-column alignment were ambiguous for NFRs | Added explicit M/S priority to every NFR catalogue entry; rebuilt §30.3 as eight named columns and aligned all 74 FR and 32 NFR rows with their catalogue priorities, use-case coverage and owner/entity mappings. | Static checks: 106 unique trace rows, eight cells each, catalogue/trace priority equality; no runtime tests. |
| SRS/register table counts were questioned | Both documents state 51 retained/refactored + 40 new = 91 active; +35 legacy read-only = 126 physical, based on 86 repository-declared production mappings and excluding five fixtures. New tables remain quota usage and push endpoints; resumable upload uses existing Core Asset metadata. | Not verified against a live database. |

## Records updated

- `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` — v1.6-draft.
- `artifacts/DATA_TABLE_REGISTER.md` — v1.6-draft.
- `docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md`.
- `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `plan/PLAN.md` revision 15, `approvals/TASK_APPROVAL.md`.

## Remaining open gates

The SRS keeps production privacy/retention/transfer, workflow-engine comparison, live DB inventory, synthetic AI/storage benchmark, Android push delivery, MinIO resumable multipart POC, payment sandbox, VAT/e-invoice, production host/region/SLO, wireframes and other rollout items in OI-01–OI-18. These are not silently treated as completed owner decisions.

