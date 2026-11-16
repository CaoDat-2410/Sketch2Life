# FEAT-063 diagram input catalog — v2.7 draft, Rev57

- **Document ID:** SKETCH2LIFE-FEAT063-DIAGRAM-INPUT-CATALOG-REV57
- **Date:** 2026-11-09 (Asia/Saigon)
- **Branch baseline:** docs/feat063-diagram-readiness-20261107 at ae5707ca188d01d9719ed959b62d768ae927912d
- **Canonical target:** SRS v2.7-draft Rev57 and Data Table Register v2.7-draft Rev57; both unsigned.
- **Source-only review:** same repository commit; no runtime, database, migration, provider or deployment verification.
- **Purpose:** handoff contract for 13 diagram outputs (11 kinds; ERD has conceptual, logical and physical outputs). These are input/readiness statuses, not diagram approval.

## 1. Disposition

READY-FOR-REVIEW means the logical input can be reviewed against this draft; it does not mean approved. Any owner policy or physical/source evidence gate keeps the final diagram DRAFT or BLOCKED. No final diagrams are created or labeled APPROVED in Rev57. TO-BE/PROPOSED contracts are separate from AS-BUILT evidence.

## 2. Thirteen diagram inputs

| Output | Requirement / decision anchors | Available input and required content | Status | Dependency / reason |
|---|---|---|---|---|
| Context | §§2–3, 9, 20, 31.3; Q-13 | Four product roles; external identity, storage, AI/payment systems; tenant/trust and child-media boundary. System Operations and provider adapter remain internal/infrastructure actors. | DRAFT | Product SRS is unsigned; production boundary/ADR evidence is not in this source-only review. |
| Use Case | UC-01–UC-18; FR/AC; Q-01–Q-13 | Actor/permission map, pre/postconditions, alternate paths, Teacher random selection and Parent no-preset branches. | DRAFT | Q-01/Q-04/Q-13 and policy decisions remain OPEN-OWNER. |
| Workflow | §§5, 31.5–31.8; BR-09/41/55; Q-01/Q-02/Q-04/Q-13 | Parent and Teacher main flows, plan and occurrence ownership, quota admission, sharing, review/publication and revoke. | DRAFT | Parent no-preset and supersession policies remain open; school quota amounts/authority remain open. |
| Activity | §§5.2, 6, 7, 22–23; G01/G04/G08 | Swimlanes, guards, async work, timeout/retry/cancel, grant revoke and exceptions. | BLOCKED | Transition matrix includes defined flows but profile, publication, delivery and quota lifecycle gaps remain open. |
| Sequence | §§9.5–9.7, 21–23; D-18/R-02; Q-01/Q-02 | Proposed commands/events, per-owner receipts/outboxes, authorization, idempotency, provider callback, reconciliation and compensation. | BLOCKED | Exact endpoint schemas and mounted status are incomplete; main composition does not mount the AI Jobs router in source. |
| Screen Flow | §§5, 21.5–21.6; UC-01–UC-18; D-17 | Role-specific screen IDs, navigation, back/cancel/resume, loading/empty/denied/error and recovery. | BLOCKED | Screen IDs and route/deep links are proposed only; detailed design and owner decisions remain open. |
| Class | §§3, 6, 9, 31.3; D-07/D-19 | Domain owners, typed references, fields/types, operations, ports, multiplicities and invariants. | DRAFT | Profile-link multiplicity and permission persistence remain open; draft contract is not source implementation. |
| ERD Conceptual | DTR §§2–6; M-11/M-15; D-09/Q-04 | Profile/grant/recipient concepts, lesson, occurrence, run/job, quota and owner boundaries. | DRAFT | Profile identity/cardinality and post-revoke history remain open. |
| ERD Logical | DTR §§4–6; D-01–D-04/D-16 | Candidate keys, optionality, same-owner FK, opaque cross-owner refs, exact lesson version/hash pin. | DRAFT | Logical relationships are specified, but approved owner/link cardinality and full constraints are not. |
| ERD Physical | DTR §§4–7/10/14; D-01–D-04/OI-11 | Approved SQL types, null/default, PK/FK/actions, uniqueness/checks/index predicates and migration mapping. | BLOCKED | No complete approved physical DDL/dictionary, migration crosswalk or production/as-built schema proof. |
| State Machine | SRS §§6/22–23; D-10/D-11; Q-01/Q-04/Q-13 | Per-aggregate source states, events, guards/effects, timeouts/retries/revoke/cancel and terminal/error outcomes. | BLOCKED | Several lifecycle state sets and policy effects are not specified; do not invent them. |
| System Architecture | §§2, 9, 11, 14, 20–23; ADR references | TO-BE owner modules, trust/external boundaries, AI and data flows. | DRAFT | SRS remains unsigned; production hosting/ADR and deployment evidence are not established here. |
| Package | §9.2, DTR §2; D-20/OI-17 | Target ownership/dependency matrix plus source graph/cycle evidence. | BLOCKED | Target modules are proposed; source scan found one canvas-render import cycle; runtime wiring not inspected. |

## 3. Group readiness and cross-artifact dependencies

| Group | Trace anchors | Rev57 input added | Status | Remaining gate |
|---|---|---|---|---|
| G01 Teacher random child | UC-05, FR-T-10, FR-PL-20, AC-56, Q-01, D-06 | SRS §5.2 case table; explicit distinction between occurrence selection evidence and required run-input snapshot. | PARTIAL | Owner must approve eligibility, consent/notice, exclusions, reselection, empty-set response, evidence and concurrency policy. |
| G02 Identity and sharing | §§31.3/31.6, M-11/M-15, D-09, Q-04 | Separate logical owners/references, tenant and grant gates; no-name-join/no-cross-owner-FK rules. | PARTIAL | Confirm identity link owner/cardinality/optionality, whole-school/class acceptance, fields, expiry and history/revoke behavior. |
| G03 Role and permission | §§3/20/31.3/31.10(14), M-03–05, D-07, Q-13 | Correct UC-14 and §21.5 actor; server resolver proposal and deny-by-default matrix. | PARTIAL | Physical grant/version model and force-close authorization/audit details need owner decision. |
| G04 Plan supersession | FR-T-08/20, §31.8.2, M-10 | Case matrix for accepted, queued, running, ready/playable, failed and cancelled work; exact pin/stale fence preserved. | PARTIAL | Owner must choose continuation, cancel, visibility, approval, claim, quota and projection effects. |
| G05 Parent no preset | UC-02/18, FR-P-05, SRS §31.10(13), R-04 | Both query and no-query branches, after-video timing, response/filter/revoke fields left open. | PARTIAL | Product/Learning Content owner must choose whether catalog is queried and approve detailed contract. |
| G06 Open policy set | §31.10(1–17), Q-01–Q-13 | Decision Register with exact questions, options/consequences, role-owner status and update targets. | PARTIAL | No owner approvals were supplied; all unresolved entries remain OPEN-OWNER. |
| G07 Physical database | DTR §§3–7/10/14, D-01–04/D-16/OI-11 | Inventory for all 92 active mappings, logical-field pointers, source evidence/status and migration gaps. | BLOCKED | Approved physical DDL, field constraints, all-column crosswalk, backfill validation/rollback and DB as-built evidence. |
| G08 State/activity | §§6/22–23, D-10/D-11 | Defined transitions plus explicit gaps for non-enumerated aggregate states. | PARTIAL | Product/engineering owners must resolve policy-dependent transition and event semantics. |
| G09 API/sequence | §§9.5–9.7/21–23, D-18/R-02 | Proposed message contracts, receipts/outbox order, async/retry/reconcile paths; source mount finding recorded. | PARTIAL | Exact schemas/route approval, mounted API proof, timeouts/compensation need review. |
| G10 Screen/class/package | §§9.2/11/21.5–21.6, D-17/19/20/OI-17 | Proposed navigation IDs, conceptual class operations, owner matrix and AST import scan result. | PARTIAL | Design approval, physical routes and resolution of the observed import cycle. |

## 4. Trace and baseline rule

Per-element trace is in DIAGRAM_TRACE_MATRIX_REV57_20261109.md. A final artifact must use one owner-approved SRS/Register baseline and cite requirement/decision IDs on its elements. SRS/DTR v2.7-draft are unsigned, so none of the 13 outputs is approved.

## 5. Evidence boundary

EV-063-62 records the source SHA, code paths, static AST result and checks. AS-BUILT status here applies only to inspected source at the selected commit. It does not establish production deployment, live API mounting, database state, migration execution or operational behavior.