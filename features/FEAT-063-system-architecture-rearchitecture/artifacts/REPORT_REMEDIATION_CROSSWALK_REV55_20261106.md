# FEAT-063 Rev55 — crosswalk for the v2.5 review report

**Source reviewed:** `Sketch2Life_Bao_cao_hop_nhat_Fix_1_luot_v2_5.docx`, owner-provided read-only copy (dated 2026-11-06).
**Authority:** FEAT-063 SRS and Data Table Register v2.6-draft after this remediation; both remain unsigned.
**Purpose:** disposition every report item against current authority and repository evidence. This is a design-document remediation record, not product implementation evidence.

## Status key

- **FIXED:** a supported contradiction or omission was corrected in the canonical draft or a linked specification.
- **COVERED:** current requirements already answered the finding; the crosswalk clarifies the controlling source.
- **OPEN:** an owner decision, legal/policy rule, exact physical schema, or runtime evidence is still required. No default is inferred.
- **PARTIAL:** a logical rule is documented, while the implementation or physical detail is deliberately deferred.

## M — contradictions and alignment

| ID | Finding from report | Disposition | Resolution / controlling reference |
|---|---|---|---|
| M-01 | Parent activity appears before video in UC-02 although the product flow puts activities after playback. | FIXED | UC-02 and BR/FR trace now pin an allowed lesson version before the run, keep activity selection out of the Parent pre-video path, and return the lesson activity list only after video playback is available. Teacher sample activity pin remains separate. |
| M-02 | Parent StoryRun does not pin a reusable lesson version. | FIXED, LOGICAL CONTRACT | A nullable, typed opaque `LessonVersionRefV1` plus version/hash lineage is specified for runs that use a lesson. No cross-owner SQL FK or physical column migration is authorized by this document change. See SRS §9.7/§9.9 and the relationship catalog. |
| M-03 | Product and operational roles differ across role sections and permission matrix. | FIXED | Product actors are Platform Admin, School Manager, Teacher and Parent. Content Admin, System Operations and AI Provider Adapter are separately scoped internal actors. One resource/action matrix replaces the mixed labels in SRS §§3, 20 and 31.3. |
| M-04 | “Organization admin” may be a separate role or an alias for School Manager. | OPEN | Do not merge roles or create a sixth product role by inference. School Manager is used as the current product-role name; “organization admin” remains a capability/legacy label whose identity mapping needs owner confirmation. |
| M-05 | Platform Admin media access conflicts with the permission baseline. | FIXED, DEFAULT DENY | Platform Admin has no routine child-media/profile-content access. Feedback/moderation permissions remain as specified. Any exceptional media-access permission and its lifecycle are not defined or enabled by this remediation; no break-glass path is added. |
| M-06 | SRS §9.9 has fewer AI job targets than §22 and the Data Register. | FIXED | §9.9 now uses the same eight target kinds as the job envelope and Data Register: story run, video generation, video scene, lesson source document, lesson library version, lesson-version visual asset, sketch-deck revision and Parent Sketch Guide. |
| M-07 | Historical design counts, Rev31 crosswalk and local Rev43 database count are conflated. | FIXED | Current target is 92 active + 48 legacy/read-only = 140 projected physical mappings. The 89-active/137 figure is the earlier v2.3 target; the 41-table local PostgreSQL result is a Rev43 environment snapshot. Current source mappings and target mappings are described separately. |
| M-08 | SAFETY_BLOCKED entry/exit and adult-wait timer are unclear. | FIXED, POLICY LIMIT PRESERVED | The state catalog defines the automated safety event, playback denial, adult action required after the job ends, eligible exits and the existing 144/168-hour adult-wait behavior. It is not a final human-video-review gate. |
| M-09 | Scene retry, accepted full-video failure, quality regeneration, quota and Teacher slot effects are mixed. | FIXED, EXISTING NUMBERS RETAINED | A separate request/retry matrix distinguishes per-scene technical retry, accepted full-video request, quality regeneration and pre-admission rejection. Existing limits/no-refund/sample-claim rules remain controlling; no new retry count is introduced. |
| M-10 | Lesson plan changes, STALE decks and in-flight run/job behavior are not fully specified. | PARTIAL / OPEN | Every run/job pins the exact lesson/plan revision and hash; stale completion cannot overwrite current state. A run is never silently retargeted. Whether an already accepted in-flight run may finish after the occurrence plan is superseded remains OPEN; no cancellation or completion default is added. |
| M-11 | Parent-shared profile context lacks a typed run association and revoke fence. | FIXED, LOGICAL CONTRACT | A Teacher run records opaque profile/grant/version refs and approved snapshot hash through a versioned contract; no cross-owner FK is added. Revoke blocks new reads and unaccepted jobs. Accepted run snapshot behavior follows existing lifecycle. Exact shared fields and invitation lifecycle remain OPEN. |
| M-12 | Quota scope and charge order are unclear across school/Teacher/Parent scopes. | PARTIAL / OPEN | Product quota remains owned by Billing and compute reservation by AI Policy. Already decided order within an eligible scope is retained; which school/Teacher pool applies and cross-pool fallback/precedence remains OPEN under Q-02/Q193. |
| M-13 | Logical dotted names and physical underscore names are mixed. | FIXED | The Data Register defines logical `schema.table`, physical SQL identifier, source Python mapping and implementation status as different labels; no physical table is renamed by this change. |
| M-14 | FR-PL-03/AC-59 conflict with the resolved Q159 restriction on Parent AI generation. | FIXED | Only Platform Admin and Teacher may initiate AI lesson/activity suggestion or AI rewrite. Parent may manually edit an authorized draft/personal copy within still-open field/safety policy; Parent cannot initiate an AI suggestion, publish a source version or change shared source content. |
| M-15 | Invitation acceptance actor/sequence is inconsistent. | OPEN | AC-49 no longer assigns acceptance to Parent or Teacher. A share is not effective until its grant is active, but who accepts, what the invitation actor is, expiry and exact state transitions require an owner decision. |
| M-16 | VideoAdmission summary skips `VIDEO_ADMISSION_PENDING`. | FIXED | Canonical path is `SCRIPT_REVIEW → VIDEO_ADMISSION_PENDING → (ADMISSION_REJECTED → SCRIPT_REVIEW) or (ACCEPTED → VIDEO_QUEUED)`. Uncertain receipts remain pending for reconciliation; admission rejection consumes no quota/request cap and dispatches no job. |

## D — missing specification

| ID | Missing detail | Disposition | Resolution / remaining boundary |
|---|---|---|---|
| D-01 | Physical SQL types, lengths, nullability, defaults, checks, FK/index actions. | OPEN / NOT SPECIFIED | Logical contracts are not executable DDL. Exact physical definitions require owner-approved target DDL and a migration inventory; none are invented here. |
| D-02 | Field-level mapping for retained/refactored source tables. | PARTIAL | Data Register §4.1 records source declarations and target actions where available. Remaining mappings require current owner-code/DDL evidence; undocumented fields are not guessed or backfilled. |
| D-03 | Partial unique indexes and concurrency predicates. | PARTIAL / OPEN | Existing logical invariants remain in the Register. A predicate is not declared executable until its state set and physical DDL are reviewed; no index migration is added. |
| D-04 | Media-access audit fields and retention. | PARTIAL / OPEN | Logical audit records actor, action, opaque resource/scope, permission/grant version where applicable, reason, result and timestamp, without media/content. Audit owner/schema already exists; exact retention and any exceptional media permission remain OPEN. |
| D-05 | Publication review/moderation history. | COVERED, NO NEW TABLE | Reuse immutable lesson versions, review state/history already owned by Learning Content/Lesson, grants and metadata-only audit. No duplicate review table is introduced absent a proven lifecycle gap. |
| D-06 | Random sample eligibility, consent and evidence. | OPEN | Q-01 controls eligibility, selection, exclusion and guardian notice. Existing random representative requirement is preserved; no algorithm or synthetic eligibility evidence is fabricated. |
| D-07 | Persisted role/assignment scopes. | PARTIAL | BE1 owns identity, organization, class and assignment; permission checks also bind resource and actor. Exact role persistence/claim projection is a source/implementation mapping task, not a new table decision. |
| D-08 | Quota allocation and charge order. | OPEN | Q-02 controls cross-pool allocation/fallback/precedence. Billing ledger vs AI compute accounting is specified; commercial allocation and price are not. |
| D-09 | Parent–Teacher–delivery profile association. | FIXED, LOGICAL CONTRACT | Typed opaque profile/grant/version references and a snapshot fence are specified; no display-name join, owner merge or cross-owner FK. Field scope and invitation lifecycle remain OPEN. |
| D-10 | Full aggregate state transition rules. | FIXED, LOGICAL SPEC | Rev55 state catalog covers StoryRun, VideoGeneration, AiJob, Lesson/Deck, grants/membership, subscription and payment, separating defined transitions from open guards. |
| D-11 | Lesson/grant/feedback/membership lifecycle states. | PARTIAL / OPEN | Existing named states are preserved and mapped to owners. Invitation acceptance actor, exact expiry semantics and any unspecified feedback moderation states remain OPEN. |
| D-12 | Detailed use cases for reuse/share/history/quota/sample/moderation. | FIXED, REQUIREMENTS LEVEL | UC-02/05 are corrected; UC-18–UC-23 cover lesson reuse, profile grant, feedback/history, quota admission, Teacher sample and moderation. Open decisions are called out inside each case. |
| D-13 | Lesson document owner, lineage, upload allowlist and AI boundary. | COVERED | Lesson library source documents/revisions remain distinct from occurrence-owned documents. Original bytes/provenance are preserved; only reviewed allowlisted structured fields can reach AI. |
| D-14 | Migration treatment for legacy 121–155-month profiles. | OPEN | New target validation remains 36–120 months. Do not clamp, delete, or reinterpret legacy values; migration/read/use disposition awaits owner policy and data review. |
| D-15 | FK vs opaque cross-owner references, cardinality and lifecycle. | FIXED, LOGICAL CATALOG | Register relationship catalog names owner, direction, typed ref, cardinality, version fence and integrity owner; FK/cascade/DDL are limited to same-owner rules and remain subject to physical design review. |
| D-16 | Target-vs-as-built/migration mapping. | FIXED, EVIDENCE-BOUNDED | SRS §32 and Register §14 distinguish target mappings from the Rev43 local 41-table snapshot and Rev51/current source-only observations. No target mapping is claimed migrated without migration evidence. |
| D-17 | Role-specific screen/navigation/state/action inventory. | FIXED, PROPOSED INVENTORY | Rev55 screen catalog adds Parent, Teacher, School Manager and Platform Admin screens with states, primary actions and API groups. Final IA/design approval remains pending. |
| D-18 | API workflow contract and actual-vs-target distinction. | FIXED, PROPOSED CONTRACT | Route inventory includes actor/scope, purpose, input fences, async behavior and safe errors; mounted main-app source, StoryRun-lite fixture app and target APIs are separate. No endpoint is claimed live solely from SRS. |
| D-19 | Domain classes/ports, responsibilities and implementation status. | FIXED, LOGICAL CATALOG | Aggregate/port catalog maps behavior and invariants to owners; one class is not inferred per table. Existing code presence is separated from target semantics. |
| D-20 | Package dependency map: target vs repository source. | FIXED, STATIC SOURCE REVIEW | Catalog maps domain/application/ports/infrastructure/interfaces/contracts and composition at commit `1431ef81972b71303fd4a7909748fd3005769a3c`. This is a static source review; it is not an import-graph test or runtime proof. |

## Q — decisions intentionally left open

| Report ID | Question retained | Current disposition / dependency |
|---|---|---|
| Q-01 | Teacher random representative eligibility, exclusion, consent/guardian notice and selection evidence. | OPEN; blocks production sample policy and acceptance evidence. |
| Q-02 | Whether Teacher quota is school or Teacher pool, precedence/fallback, allocation and commercial units. | OPEN; do not infer cross-pool charge order. Existing within-scope grant rules remain. |
| Q-03 | Parent history window: 30 or 60 days; any plan/quota variation. | OPEN; SRS §31.10(3). |
| Q-04 | Exact shared profile fields, expiry and invitation acceptance/revoke lifecycle. | OPEN; share must be grant-backed and revoked access is denied. |
| Q-05 | Montessori age subgroups and age-band versioning. | OPEN; outer eligibility remains 36–120 months. |
| Q-06 | Parent editable fields and their validation/safety boundaries. | OPEN; Q159 role gate still prohibits Parent-initiated AI generation. |
| Q-07 | Script-following default and allowed override/variation. | OPEN; current flow can honor a pinned lesson direction when explicitly enabled. |
| Q-08 | Approval/review record for Platform Admin-authored public lessons. | OPEN; Teacher public publication still requires School Manager approval. |
| Q-09 | Generated visual/slide ownership, review and approval. | OPEN; generation remains optional and cannot replace original lesson or child drawing. |
| Q-10 | Trace the short owner answer recorded as Q192 to its original question. | OPEN; do not infer a broader permission. |
| Q-11 | Use/migration disposition for legacy profiles aged 121–155 months. | OPEN; preserve existing source data and do not silently clamp/delete. |
| Q-12 | Prices, top-up packages and commercial quota values after benchmark. | OPEN; no values added. |
| Q-13 | Whether Content Admin/Operator are product roles, operational roles or permission bundles and how they are persisted. | OPEN; they remain separate non-product actors in the matrix pending owner/ADR decision. |

## Review result

The report is treated as a review input, not as authority to override answered SRS decisions. Supported contradictions were repaired; evidence-limited implementation or physical-schema gaps are labeled; Q-01–Q-13 remain unresolved. The v2.6-draft is still unsigned, and no code, schema migration, API runtime, provider, deployment, or product test was performed for this remediation.

The related UI review's S7 claim that Teacher Sketch Deck is mandatory is stale against the controlling v2.5 SRS: BR-42 already records Q167's later decision that the Deck is opt-in per session. Rev55 preserves that rule and specifies that an enabled Deck is generated after the approved plan and must be ready before it is presented. The earlier v2.2 version-history wording (“main step”) is historical, not the current rule.
