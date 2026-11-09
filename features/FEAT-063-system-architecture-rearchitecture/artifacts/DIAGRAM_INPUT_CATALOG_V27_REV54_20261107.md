# FEAT-063 diagram input catalog — v2.7 draft, Rev54

- Document ID: SKETCH2LIFE-FEAT063-DIAGRAM-INPUT-CATALOG-REV54
- Date: 2026-11-07
- Status: DRAFT / TO-BE INPUTS ONLY / NOT SIGNED OFF
- Working baseline: 98cc34a39af279560b5f8d39f18939a376535834
- Current authority: FEAT-063 SRS v2.7-draft and matching Data Table Register v2.7-draft at the working baseline; both unsigned.
- Historical checklist sources: v2.6 SRS, v2.6 Data Table Register, Rev55 Architecture Detail Catalog and Rev55 Remediation Crosswalk at a711e78cf6586dd5b639d811e610a741efd7433d on docs/feat063-v25-report-remediation-20261106.
- Static implementation observation referenced by Rev55: 1431ef81972b71303fd4a7909748fd3005769a3c. No fresh source, runtime, API, database, migration, provider or dependency verification was performed for this catalog.

## 1. Purpose and limits

This catalog organizes the logical inputs needed to prepare draft diagrams from the current SRS/Register. It updates the Rev55 design inputs for v2.7, carries forward the supplied M/D/Q/R identifiers, and highlights what prevents an approved final diagram.

The catalog is not an approved SRS, an OpenAPI specification, a physical data dictionary, an as-built architecture map, an import-graph report or a final diagram. “Covered logical” means a requirement or proposal is described in documents; it does not mean owner-approved, implemented, migrated, mounted, tested or runtime-verified.

Final diagrams remain gated on formal owner approval of the SRS and Data Table Register and the owner decisions/technical evidence listed in the companion Rev54 crosswalk. The 92 active + 48 legacy/read-only = 140 value is a projected mapping count, not a database inventory. The local 41-table snapshot remains environment-specific.

## 2. Authority and drawing conventions

1. Use SRS §§1–31 and the matching Data Table Register as the current TO-BE baseline. Treat SRS §32 and cited source commits as dated evidence only.
2. Draw ownership boundaries before entities or messages. Same-owner database relationships may be modeled as candidate FKs; cross-owner links are typed opaque references through versioned contracts. Do not draw cross-owner SQL FKs.
3. Preserve cardinality and optionality as stated. An optional LessonVersionRef does not imply that every Parent run or occurrence has a preset.
4. Label unresolved actor, policy, guard and physical decisions OPEN. A proposed route or screen is not mounted solely because it appears in an SRS/catalog.
5. Keep every sensitive-media path server-authorized and deny-by-default. A role label, tenant administration or content permission does not itself grant access to child profile/media.

## 3. Actors and permission boundary

| Actor | Product or internal boundary | Draft diagram input | Explicit restriction or open gate |
|---|---|---|---|
| Parent | Product role; Parent account owns Parent child profiles and Parent quota | Create and manage own profile/run, use eligible lesson, review story/video, view permitted history, share/revoke a profile grant, send lesson feedback | Cannot join organization roster or initiate AI lesson/activity suggestion. No outdoor-activity selection before video. Parent no-preset catalog behavior remains open. |
| Teacher | Product role; organization assignment scopes class/managed-profile work | Manage currently assigned class/profile, prepare occurrence and approved plan, optionally use Teacher deck, create one-child sample run, review relevant feedback | Video quota resolves only to the occurrence’s school organization. Assignment/grant revocation fences access. Child eligibility/consent rules for random sample remain open. |
| School Manager | Product role scoped to one organization | Manage organization membership/roster, school quota administration as authorized, review school lesson/feedback | No child-media access by virtue of tenant role. Exact persisted role resolver and emergency force-close permission remain open. |
| Platform Admin | Product role scoped platform-wide | Platform lesson/library and moderation actions through explicit permissions; manage platform policy | Child-profile/media access is deny-by-default. No break-glass workflow is defined. |
| Content Admin | Permission/capability of Platform Admin, not an independent product role | Content author/review/publish actions only where assigned | Content permissions do not grant child-media access. Persistence, assignment and resolver details remain open. |
| System Operations | Internal operational actor | Operational metadata and bounded recovery functions as separately authorized | No routine child-content access is implied. Exact operator permission bundles are open. |
| AI Provider Adapter | Infrastructure actor behind an application-owned port | Receives only purpose-bounded, filtered/versioned job inputs and returns job output/status | It is not a product identity or permission authority; credentials/endpoints stay server-side. |

For use-case and context drafts, show only documented product actors and the external adapters relevant to that flow. Do not add “Organization Admin” as a sixth product role; where older material uses that label, record its mapping/authority as OPEN in the crosswalk.

## 4. Ownership and logical relationship inputs

| Owner/boundary | Canonical logical data and responsibility | Diagram relationship rule |
|---|---|---|
| BE1 / identity and classroom | Principal, organization, class, managed profiles, enrollments and current Teacher assignment | Source of current assignment. Teacher access is checked against current tenant/assignment. No Parent-profile identity match by display name. |
| Parent | Parent account-owned child profiles, profile revisions/context, consented profile-share grants | Parent profile remains Parent-owned. Grant/ref/version is a scoped authorization boundary, not an owner merge. |
| Lesson | Library lesson/version/review, occurrence, plan/document revisions, selected activity, sample claim, deck revisions/steps | Occurrence may optionally pin an exact LessonVersionRefV1 and content hash. Each plan revision preserves that exact ref/version/hash plus its own plan hash. Never resolve “latest”. |
| Learning Content | Global activity catalog record/version/review; published and approved versions are the source of eligible catalog content | A Parent run without a preset may or may not query the catalog. Query policy, filters, permissions, ordering/cardinality, response snapshot, empty behavior and revoke/unpublish behavior remain OPEN. |
| Story | One-child StoryRun, inputs/snapshots, reviews, revisions, video generation and current run state | Parent/Teacher run pins its input/context and references relevant Lesson/occurrence/plan through versioned typed refs. Never use a foreign owner’s display name as a join key. |
| AI Jobs | Durable job, target kind/ref, attempt and event lineage | One job targets exactly one supported aggregate/target kind. Job completion is accepted only against expected version/hash/fences. Target mapping must still be checked against as-built source before claiming implemented. |
| Core | Asset metadata/lineage, upload lifecycle, metadata-only audit and owner outboxes | Preserve originals and provenance. Asset bytes are private. Do not place raw child media/story in audit or telemetry. |
| Billing | Immutable video quota grants and usage, subscription/payment receipt and quota admission | One accepted full-video request consumes one usage unit from one eligible grant. Parent scope is Parent account; Teacher scope is organization from occurrence. |
| AI Policy | Platform compute/resource budget and reservation | Owns compute metering/reservation only; not product quota grants, quota balance or product usage. |
| Notifications | Inbox and delivery attempts | Inbox is source of notification state; recipient is a typed principal reference. Do not expose child content in delivery payloads. |

### 4.1 Lesson-version lineage

For a preset-backed occurrence, draw an optional LessonVersionRefV1 plus exact version/hash at the Lesson owner boundary. The occurrence, its approved plan revision and the Teacher StoryRun retain the same source version/hash lineage; each plan revision also has its own content hash. Changing a library head must not retarget the occurrence/run. Cross-owner links are opaque typed references; physical storage/DDL remains gated. See SRS FR-T-08 and Data Table Register §5.5.

### 4.2 Parent activity source after video

When a Parent run has a pinned lesson version, its configured activities become eligible for the post-video display. The global catalog owner is Learning Content, and only published, approved versions are eligible catalog content. For a Parent run without a preset, SRS FR-P-05 / BR-08–09 and the Data Register identify the source but deliberately leave whether it is queried and how it is filtered/versioned/presented OPEN. Do not draw a required catalog response, choose a list size, or invent a new catalog table. Empty results and content revocation also remain OPEN.

### 4.3 Profile sharing and delivery identity

Current logical boundary: Parent owns the profile; a scoped, consented, revocable grant is required for cross-role reads; BE1 owns Teacher managed profiles and assignments; Lesson delivery records identify recipients; StoryRun holds only an approved snapshot and typed references. The exact Parent Profile ↔ Managed Profile ↔ Delivery Recipient identity link, link owner, cardinality and history behavior after revoke are not yet specified. Do not connect records by name or draw an unverified FK. No read is permitted before the grant is ACTIVE.

## 5. Workflow, state and admission inputs

### 5.1 Video admission saga

Draw separate owner transactions coordinated by one application-level idempotency key; do not draw a cross-owner SQL transaction.

1. Story/application validates actor, run version, active-owner lock and request limits.
2. AI Policy reserves bounded compute budget with a lease/expiry.
3. Billing admits quota in its own transaction and records a receipt/one usage unit for an accepted request.
4. Story records accepted admission and its outbox/event in the Story owner transaction.
5. Dispatch occurs only after confirmed reservations/receipts. Uncertain outcomes stay pending for idempotent reconciliation before another dispatch.
6. Rejection before acceptance creates no accepted generation/job, no quota usage and no request-cap usage. If quota admission fails after compute reservation, release that reservation. An accepted request consumes one unit even if provider/technical/safety processing later fails; there is no refund. Scene retry is not a new full-video request.

Use the current error contract and request/retry limits in the SRS. This catalog does not alter quota policy or introduce a new compensation/refund.

### 5.2 Other state inputs

| Aggregate | State rule available for a draft | Still open or evidence-gated |
|---|---|---|
| StoryRun / video generation | SRS §6 and §§22–23 define run/admission/safety, retry, cancellation and playback gates. Admission pending is explicit; playback is blocked until required safety checks pass. | Regression of all transitions, timeout/recovery and concurrency; do not infer runtime correctness from this state catalog. |
| Lesson plan / Teacher deck | Plan revisions are immutable; deck pins approved plan revision/hash. A changed plan makes the prior deck STALE and blocks its presentation until a READY revision exists. | Effect of superseding a plan on already accepted/running/playable work, sample claim and approval is OPEN under M-10. |
| Profile-share grant | Grant required before cross-role read; named Teacher acceptance activates the invitation grant; Parent may revoke; revoke denies new reads/unaccepted jobs. | Invitation scope/consent fields, expiration/renewal, school-wide acceptor, offboarding and accepted-job/run/history behavior are incomplete. |
| Teacher sample claim | One representative child/run/activity per occurrence under existing single-claim rule; failed pre-playable run does not consume initial claim; after claim it is retained. | Eligibility, consent, exclusion, selection evidence and no-eligible-child branch are OPEN under Q-01/D-06. |
| Moderation/publication | AI outputs default to draft; human review/publication gates remain. School Manager approval is required for Teacher lesson publication to PUBLIC. | Review/author separation for Platform Admin-authored public content and exact review-record lifecycle are OPEN. |
| Legacy profile age | New product range is 36–120 months; preserve source values and do not clamp/delete older records by inference. | Read/edit/new-run/archive/delete and migration treatment of 121–155-month profiles are OPEN. |

## 6. API and sequence inputs

API entries in the SRS and Rev55 catalog are target/proposed interactions unless separately marked mounted by source evidence. The diagram must show actor → interface → application use case → owner port/adapter and async outbox/job/receipt boundary. It must label scope derivation, authorization decision, version/hash fence, idempotency key, safe response/error and reconciliation path when those are defined.

Candidate sequence families:

- Parent profile/run/upload/review/video/playback/delete.
- Parent post-video activity response (preset-backed defined; no-preset response OPEN).
- Teacher occurrence/plan/document/deck/sample/video/projection.
- Profile-share invitation, activation, revoke and access fence (details OPEN).
- AI lesson suggestion/review/publish/moderation.
- Video quota/compute admission saga and payment receipt.
- Safety-block, retry, cancellation, timeout and uncertain-receipt recovery.

Do not label a target route as mounted without current OpenAPI/router evidence. Rev55’s source scan is dated at 1431ef8; this task did not re-run it. D-18 remains a proposed API/event contract, not production OpenAPI.

## 7. Screen-flow inputs

Draft route groups only: Parent profile/run/review/playback/history/lesson/feedback/settings; Teacher roster/profile/lesson-source/plan/occurrence/deck/sample/projection/feedback; School Manager roster/assignment/quota/review; Platform Admin lesson authoring/review/publish/hide/role-policy. Content Admin is a permission bundle within Platform Admin.

For each screen, final IA still needs an approved screen ID, entry/exit and back/deep-link behavior, loading/empty/permission/error states, server-state gate and authorized next action. Do not assume screens/routes already exist. Parent history-window choice, Parent no-preset activity response and unresolved permissions block final flow decisions.

## 8. Domain class and package inputs

### 8.1 Domain aggregates and ports

Use business aggregates and value objects from SRS §9.9 and owners in §4; do not assume one class per table. Candidate ports include identity/assignment authorization, profile-grant authorization, lesson-version/occurrence lookup, Learning Content published-version lookup, StoryRun admission and event publication, Billing quota admission/receipt, AI Policy compute reservation, AI Jobs dispatch/reconciliation, Core asset/audit/outbox and payment/notification adapters. Mark unresolved policies as use-case guards or explicit open interfaces; do not invent persistence.

### 8.2 Package direction

Target dependency direction is interfaces/adapters → application → domain; infrastructure implements ports and points inward. Contracts are versioned. Do not import framework, provider, storage, queue or UI packages into domain. The target layering is a proposal; the Rev55 package note was a static source review at commit 1431ef8, not a fresh import graph/cycle test and not evidence that current source complies.

## 9. Diagram handoff matrix

The checklist calls these 11 diagram categories; ERD has three levels, so the handoff has 13 rows.

| Diagram | Draft input available | Blocker before final diagram |
|---|---|---|
| Context | Product/internal actors, tenant and owner boundaries, core external adapters, child-data/media/quota/AI trust boundaries | M-04/Q-13 identity and operational permission resolver; final environment/external integration evidence |
| Use Case | Parent, Teacher, School Manager, Platform Admin and internal actor actions; UC-01–UC-23 and permission gates | M-04/M-15; Q-04/Q-13; full resolver and grant lifecycle |
| Workflow | Parent, Teacher, lesson, billing, sharing, moderation and recovery families | M-10/M-15; quota allocation subparts; Q-01/Q-02/Q-04; open branches |
| Activity | Owner swimlanes, decisions, async waits, rejection and reconciliation paths | D-06/D-10/D-11/D-18; R-04; owner guards still open |
| Conceptual ERD | Business entities and owner/cardinality boundaries | R-01 optional preset lineage already described; D-09 exact profile/delivery identity link unresolved |
| Logical ERD | Active logical mappings, typed opaque refs, version fences, ownership and optionality | D-09; R-04 catalog behavior; open invitation, role and plan-supersession lifecycle |
| Physical ERD | Data Register logical mappings, current local snapshot boundary | D-01/D-02/D-03/D-14; approved DDL and migration inventory absent |
| State Machine | StoryRun/video/job, lesson/deck, grant, subscription/payment state inputs | M-10/M-15; D-10/D-11 guards/evidence and Q-01 eligibility |
| Sequence | Proposed owner ports, receipts, outbox/job dispatch, provider boundary and idempotency | D-18 mounted/proposed evidence split; R-02 wording fixed but runtime receipts not reverified; Q-02 allocation |
| Screen Flow | Four product roles and route groups with server-state gates | D-17 final IA/empty/error states; Q-03 history, Q-06 editing, R-04 activity response |
| Class | Domain aggregates, value objects, operations, ports and invariants | D-19 final operation/relationship detail; D-07 role resolver |
| System Architecture | Target modules, ingress, storage, AI, security and deployment boundaries | ADR/production stack decisions and current integration evidence; SRS remains unsigned |
| Package | Target layering and dated source observations | D-20 current import graph, cycles and adapter-boundary verification not performed |

## 10. Open decision and evidence gates

All questions Q-01–Q-13 remain OPEN-OWNER as complete checklist items. Their answered subparts are scoped in the Rev54 crosswalk. Open questions must appear as notes or blockers in draft diagrams, not as invented states, endpoints, joins, attributes, role grants or defaults.

Physical schema, source mappings, constraints, migration history, audit retention, screen IA, API mounting, code dependency direction and production integration require separately attributable technical evidence and any applicable plan/approval. Nothing in this catalog upgrades source-declared mappings to deployed tables.

## 11. Review record

Reviewed against the checklist’s same-commit sources and current canonical v2.7-draft SRS/Register. Detailed finding-to-source and verification trace is in DIAGRAM_READINESS_CROSSWALK_REV54_20261107.md; the execution limits and commands are in evidence/EV-063-59_DIAGRAM_CHECKLIST_REVIEW_20261107.md.
