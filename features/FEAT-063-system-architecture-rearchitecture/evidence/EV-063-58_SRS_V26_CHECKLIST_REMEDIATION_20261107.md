# EV-063-58 — Rev53 SRS v2.6 checklist remediation

**Date:** 2026-11-07 (Asia/Saigon)
**Plan:** Rev53, approved for the exact documentation-only 15-path manifest
**Result:** v2.7-draft SRS and Data Table Register prepared; formal owner sign-off remains pending.

## Source and review method

- Owner-provided source: `Sketch2Life_Checklist_Cuoi_Fix_1_Luot_v2_6.docx`.
- SHA-256: `5D23504F26C97977B07F40704BA1E020D69F80CDDD57562E9B3E179F69E37486`; 54,854 bytes.
- The report identifies itself as remediation guidance / not sign-off and references Rev55 artifacts on a separate branch. It is analysis input, not product-requirements authority, DDL approval, or a new owner decision.
- Read the DOCX text from its OOXML package and visually reviewed all 10 pages in Word (about 4,527 words, six tables). No comments or tracked changes were present. Several table edges are clipped on the left on pages 1, 3, and 10 of the supplied report; the text was cross-checked against the extracted document text. The report and extracted/rendered pages were not copied into this repository.
- Canonical baseline before this review: FEAT-063 SRS and Data Table Register v2.6-draft. Current working pair advances to v2.7-draft, unsigned. No source code, API, provider, runtime, database, migration, diagram, product test, or build change is included.

## Applied reconciliation

- **R-01:** SRS §31.2 and FR-T-08, plus Register §§5.5–5.6 and relationship notes, carry the optional typed `LessonVersionRefV1` with exact version/hash across occurrence, plan revision, and Teacher StoryRun. Parent pin remains optional. No `latest` resolution or cross-owner SQL FK is allowed; physical persistence/constraints remain behind approved DDL.
- **R-02:** SRS §6.1.1 now states separate AI Policy reservation, Billing usage receipt, and Story acceptance/outbox transactions coordinated by one idempotency key and reconciliation saga. Reject, ambiguous receipt, and accepted-usage behavior remain consistent with BR-38.
- **R-03:** Verified already resolved in canonical v2.6: Q159 permits Platform Admin/Teacher initiation and Parent editing of authorized drafts only. No stale AI-initiation open item exists in Register §14.3; role persistence remains open separately.
- **R-04:** SRS FR-P-05, UC-02, BR-55, FR-PL-16, and §31.10; Register `story.runs`, Learning Content relationship and §14.3 now say the global, published/approved catalog is owned by `learning_content`, while no-preset Parent query, filtering/order/cardinality, permission, version/hash snapshot, empty result, and revoke/unpublish behavior remain OPEN. Parent activity is not selected before video.
- **R-05:** Register TOC/§5 no longer labels the current dictionary “40 baseline tables.” The current 54 new mappings are stated as 51 §5 mappings plus three Rev31 support tables in §14.4; 92 active + 48 legacy/read-only = 140 remains current. Historical 40, 51/89/137, and local 41 counts remain scoped to their prior baseline or snapshot.
- Role terminology: where the current product role is established, “Organization Admin/admin tổ chức” is normalized to School Manager of the resource-owning organization. Content Admin remains a Platform Admin permission. Identity/assignment persistence, effective permission resolver, force-close grant/revoke, and audit mapping remain OPEN. Platform Admin child-media access remains deny-by-default.
- SRS §31.10 and Register §14.3 retain/add open gates for plan supersession after pin, profile identity/delivery matching, role persistence, legacy age 121–155 months, physical audit schema/retention, and physical DDL/migration. No table or column was approved by this review.

## Disposition matrix

### M findings

| ID | Disposition | Reconciliation |
|---|---|---|
| M-01 | FIXED (logical) | Regression-checked against canonical v2.6 requirements; retained in the v2.7 draft. |
| M-02 | FIXED (logical) | Regression-checked; retained without deriving implementation behavior from the report. |
| M-03 | FIXED (logical) | Regression-checked; existing owner/permission boundaries retained. |
| M-04 | PARTIAL / CLARIFIED | School Manager is the current tenant-management role label; emergency permission persistence/resolution remains OPEN (§31.10, BR-41, FR-T-17). |
| M-05 | FIXED (logical) | Regression-checked; no additional product rule inferred. |
| M-06 | FIXED (logical) | Regression-checked; existing one-child/run boundary retained. |
| M-07 | FIXED (logical) | Regression-checked; existing quota ownership boundaries retained. |
| M-08 | FIXED (logical) | Regression-checked; existing workflow/permission boundary retained. |
| M-09 | FIXED (logical) | Regression-checked; existing source/version behavior retained. |
| M-10 | PARTIAL / OPEN | Exact source pins and stale-output fences remain; accepted run/job behavior after approved-plan supersession remains OPEN. |
| M-11 | FIXED (logical) | Regression-checked; no additional state transition inferred. |
| M-12 | PARTIAL / CLARIFIED | Teacher uses only the occurrence’s school quota; no Teacher pool/fallback. Included amounts, prices, school allocation/purchase remain OPEN. |
| M-13 | FIXED (logical) | Regression-checked; existing grant/security behavior retained. |
| M-14 | FIXED (logical) | Regression-checked; existing tenant and lifecycle boundary retained. |
| M-15 | PARTIAL / CLARIFIED | Named Teacher acceptance activates the grant and Parent may revoke; full fields, expiry, offboarding, school-wide acceptor, and accepted-run behavior remain OPEN. |
| M-16 | FIXED (logical) | Regression-checked; existing version/provenance boundary retained. |

### D findings

| ID | Disposition | Reconciliation |
|---|---|---|
| D-01 | OPEN — technical | Logical mapping is not approved physical DDL; types, constraints, indexes, FK actions and migrations remain gated. |
| D-02 | PARTIAL — technical | Retained/refactored source-to-target column/backfill and migration evidence is incomplete. |
| D-03 | PARTIAL — technical | Logical invariants exist; SQL predicates, lock/concurrency strategy and approved constraints remain open. |
| D-04 | PARTIAL — privacy/technical | Metadata-only audit and deny-by-default are preserved; physical audit fields and retention remain open. |
| D-05 | FIXED (logical; regression checked) | Existing logical mapping and trace retained; no new DDL inferred. |
| D-06 | OPEN — owner policy | Random sample eligibility, consent/exclusion, no-eligible-child and selection evidence remain undecided. |
| D-07 | PARTIAL — identity | Product-role labels and Content Admin permission are clear; persisted identity, scope, assignment/revoke and resolver remain open. |
| D-08 | PARTIAL — billing | School-only Teacher quota scope is resolved; allocation/grant lifecycle and commercial terms remain open. |
| D-09 | PARTIAL — identity | Parent profile ↔ managed profile ↔ delivery recipient contract and history behavior after revoke remain open. |
| D-10 | PARTIAL — state | Existing state logic is preserved; full transition/guard/timeout matrix remains a diagram/technical gate. |
| D-11 | PARTIAL — state | Named Teacher acceptance is clarified; expiry, school-wide acceptance, offboarding, moderation and related transitions remain open. |
| D-12 | FIXED (logical; regression checked) | Existing owner boundaries retained; no new cross-owner FK inferred. |
| D-13 | FIXED (logical; regression checked) | Existing versioned contract boundary retained. |
| D-14 | OPEN — migration/privacy | Legacy 121–155-month records have no approved read/edit/run/archive/delete or migration policy. |
| D-15 | FIXED (logical; regression checked) | Existing asset/provenance boundary retained. |
| D-16 | FIXED (logical; regression checked) | Existing provider/runtime boundary retained; no deployment/readiness claim added. |
| D-17 | OPEN — diagram detail | Screen navigation and loading/empty/permission/error states need a separately scoped UI specification. |
| D-18 | OPEN — API detail | Versioned API/event payload, errors, mounted-vs-proposed status, idempotency and reconciliation detail remain a separate contract gate. |
| D-19 | OPEN — domain detail | Domain classes, operations, invariants and ports need approved logical modeling; table equivalence is not inferred. |
| D-20 | OPEN — source evidence | Package dependency direction/cycles require commit-specific source evidence and are outside this documentation reconciliation. |

### Q findings

| ID | Disposition | Remaining question |
|---|---|---|
| Q-01 | OPEN | Teacher sample eligibility, consent, exclusion, notification, and selection evidence. |
| Q-02 | PARTIAL | School-only Teacher quota and established included-current-month then top-up FIFO order are retained; allocation, amounts, prices and grant lifecycle remain open. |
| Q-03 | OPEN | Parent history window and plan/package variation. |
| Q-04 | PARTIAL | Named Teacher acceptance and Parent revoke are settled; field scope, expiry, school-wide acceptor/offboarding, and accepted-run effects remain open. |
| Q-05 | OPEN | Age bands within 36–120 months and versioning. |
| Q-06 | OPEN | Parent personal-copy editable fields and validation. |
| Q-07 | OPEN | Script-following defaults, override scope and variation. |
| Q-08 | OPEN | Publication/reviewer record for Platform Admin-authored public lesson. |
| Q-09 | OPEN | Ownership, review, visibility and provenance for generated visual/slide assets. |
| Q-10 | OPEN | Source question and exact scope for answer 46; no permission expansion. |
| Q-11 | OPEN | Existing legacy ages 121–155 months and transition/migration behavior. |
| Q-12 | PARTIAL | Quota scope/charge order partly resolved; package terms, included amounts, pricing and purchase/allocation details remain open. |
| Q-13 | PARTIAL | Content Admin is a Platform Admin permission and School Manager is the tenant role label; identity/permission persistence and other operational-role mapping remain open. |

### R findings

| ID | Disposition | Reconciliation |
|---|---|---|
| R-01 | FIXED (logical) | Exact optional LessonVersion ref/version/hash lineage is carried across occurrence, plan revision and Teacher run; physical storage remains gated. |
| R-02 | FIXED (logical) | One idempotency key coordinates separate AI Policy, Billing and Story owner transactions via saga/reconciliation. |
| R-03 | ALREADY RESOLVED | Q159 is resolved in canonical v2.6; Register §14.3 has no stale AI-initiation open item. Permission persistence stays open. |
| R-04 | PARTIAL / OPEN | Global catalog owner/version qualification is stated; Parent no-preset query/snapshot/permission/empty/revoke contract remains open. |
| R-05 | FIXED (editorial) | Current 54 new mapping count and 92+48 target are explicit; historical counts remain labeled by source/version/snapshot. |

## Checks and publication

- Final path-scoped review is limited to the 15 paths listed in Plan Rev53. No DOCX/report copy or extracted pages are tracked.
- `git diff --check`: PASS.
- `python tools/validate_repository_security.py`: PASS; scanned 6,567 publishable files, with absolute machine paths absent. Run again immediately before commit and before push per repository rule.
- Product tests/builds and provider/runtime/database operations: not run; outside this documentation scope.
- Commit/push: pending normal publication to `origin/docs/feat063-srs-v26-checklist-20261107` after the required checks. No PR, merge, force-push or `dev` update is authorized.
