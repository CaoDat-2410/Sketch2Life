# Feature status

## Current SRS amendment — v3.5 / revision 7 — 2026-10-26

- Status: DONE — owner-directed school package/quota update recorded; billing implementation remains NOT IMPLEMENTED.
- Canonical and current feature copy: FEAT-029 `artifacts/Sketch2Life_Master_SRS.md` and `artifacts/Collaborative_Learning_SRS_v3.5.md`, byte-identical with SHA-256 `2fa7bcb91c821dabd239a4331e7a68dbc9e4740da25805657cd7fed5e4c89fa7`.
- Free Trial: 14 days, 1 active class, 3 shared AI credits, no payment method. Plus: 5 active classes, 10 Teacher seats, 100 shared credits. Top-ups: 15/45/80 one-time shared credits. Only monetary amounts remain PROPOSED.
- Exact v3.4, v3.3/B28 and Registration v1.2 remain preserved; no runtime, schema, migration, provider setup or checkout implementation was added.
- Plan/authorization: `../FEAT-029-master-srs/plan/PLAN_B29_SCHOOL_PACKAGE_UPDATE_SRS_V3_5_20261026.md` and approvals.

## Historical SRS amendment — v3.4 / revision 6 — 2026-10-25

- Status: DONE — owner-approved billing/payment baseline added; implementation remains NOT IMPLEMENTED.
- Canonical and feature copy: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` and `artifacts/Collaborative_Learning_SRS_v3.4.md`, byte-identical after final SRS edits.
- B29 includes baseline packages/quotas, FR/NFR/BR/error behavior, existing portal responsibilities, school-level ownership, MoMo/VNPay/VietQR target routes and child/platform/privacy safeguards. Only monetary amounts remain PROPOSED.
- Exact v3.3/B28, prior B29 proposal, v3.2 and older baselines remain preserved. No runtime, schema, migration, provider setup or checkout implementation was added.
- Plan/authorization: `plan/PLAN_REV5_SRS_OWNER_DECISIONS_20261024.md` is historical; current billing plan `../FEAT-029-master-srs/plan/PLAN_B29_BILLING_BASELINE_SRS_V3_4_20261025.md`; owner authorization is recorded in approvals.

## Current SRS amendment — 2026-10-24

- Status: DONE — revision 5 / v3.3, additive documentation amendment authorized by the project owner’s six direct answers.
- Current canonical and feature-copy SHA-256: `f7f401829955c26a793c94d468c74502dc0ed465f9f35084e364b728c243c646`; both copies are byte-identical and the static documentation checker returned `DOCUMENTATION_VALID` with zero errors.
- Exact prior v3.2 remains unchanged at `artifacts/Collaborative_Learning_SRS_v3.2.md`, SHA-256 `9d7a71cc3fd0ab45b3175823c09780af0eb2e129d21a991d5470693dae25a21d`.
- Owner-confirmed: pending join requests revoke atomically at successful start; shared room-code lifecycle/security package and 10 failed/IP/15-minute threshold; only next-stage transitions; Assistance can interleave or be explicitly `not_needed`; no rewind until OD07 is resolved; unfinished groups require `save_draft`; early stop requires a category (`time`, `safety`, `technical`, `other`) with optional Teacher note.
- Remaining implementation gates: BE1 endpoint/schema/guard/security contract and Alembic root/order review. FEAT-057 adoption and live Modal configuration remain separate gates. No runtime route, DB schema, or migration was added by this SRS amendment.
- Plan/approval: `plan/PLAN_REV5_SRS_OWNER_DECISIONS_20261024.md`; exact approved hash is in `approvals/TASK_APPROVAL.md`.
- Verification: see `evidence/metrics/SRS_AMENDMENT_CHECKS_20261024.json` after the static documentation checker completes.

## Historical SRS amendment — 2026-10-23 (revision 4 / v3.2)

- Status: DONE — documentation-only revision 4 authorized and recorded; no runtime implementation.
- Current SRS v3.2 SHA-256: `8CAB46A3E3D9C7E47B50AD39FD106E2B5CFD844945EA0FDFBA66986F25B03B00`; both current copies match byte-for-byte.
- Baseline: SRS v3.1 preserved byte-for-byte; SHA-256 `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`.
- Confirmed amendment: both QR/deep-link and shared six-digit code are no longer accepted for new joins after the Teacher starts the class; the product distinguishes full completion from Teacher stopping early.
- Remaining technical decisions: handling of requests already pending at start; completion receipt/guards/reason fields. These remain contract review items, not product ambiguities.
- Proposed contract notes: persistent shared stage remains distinct from session lifecycle and group/member progress; API, schema, and completion-result details are not adopted.
- Product source/runtime/application-test status: unchanged. Only the SRS documentation composer/checker was redirected to v3.2.

- Status: DONE — documentation only.
- Current artifact: canonical SRS v3.2, documentation revision 4, approved and completed.
- Previous baseline: v3.1 exact bytes preserved; see `Sketch2Life_Master_SRS_v3.1_preserved_20261023.md`.
- Documentation plan: revision 4 SRS integration amendment; revision 3 remains historical and approved.
- Runtime implementation: NOT_STARTED and outside this task.
- Completed: scope/context/source register/governance/working-tree and source review; independent backend/AI and client/renderer audits.
- Completed: exact v2.0 backup; canonical replacement SRS v3.0 and feature copy; reuse/architecture report; ADR-0014; owner answers and additive context/approval/evidence updates.
- Completed: independent review corrections, final QA with no findings, 14 modules/18 source ACs/66 FRs and local links/provenance checks.
- Validation: own feature harness/security-content and static documentation checks pass; ARCHITECTURE_VALID; diff check passes.
- Global repository checks: HARNESS_INVALID for pre-existing missing directories in FEAT-037/038; REPOSITORY_SECURITY_INVALID for existing local outputs/paths/PDFs. Details/raw logs in evidence; not corrected by changing unrelated user work.
- Remaining outside completed documentation task: SRS B17 decisions and separately approved runtime/stack/contract migration, device/model/load/pilot evidence. No provider call or commit/push occurred.

## Revision 3 closeout (historical — 2026-10-10)

- Completed: 26 SRS sections, 38 detailed use cases/76 ATs, 35 logical DTOs/66 route proposals, state/permissions/concurrency/recovery, 34 screen specs, 17 candidate quality targets/16 fixture families and all 66 FRs integrated traceability.
- Owner answered: single-school pilot with expansion preparation; managed child profiles + QR/code without own login; school-mediated guardian consent evidence recorded by authorized Teacher/Admin.
- Owner answered: 36–155 completed months inclusive; one simultaneous class/up to 40 children pilot target; default session/artwork retention 90 days after end, other data classes/copies separate.
- Completed: exact v3.0 preservation alongside v2.0; canonical/feature v3.1 equality; updated ADR/context/source/approval; independent review corrections and final QA, no remaining actionable documentation finding.
- Validation: DOCUMENTATION_VALID; own feature harness/security-content, reader anchors/local links/14 JSON blocks/hashes; ARCHITECTURE_VALID; documentation diff check passed. Details/raw logs in FOUNDATION_VALIDATION.md and metrics.
- Global harness/security still fail on the pre-existing unrelated findings described above. No commit/push or publication occurred.
- Runtime implementation remains outside this task; historical v3.0 checks above remain evidence for the earlier increment.
