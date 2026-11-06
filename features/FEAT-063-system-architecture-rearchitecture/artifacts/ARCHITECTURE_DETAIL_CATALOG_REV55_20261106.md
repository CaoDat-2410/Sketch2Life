# FEAT-063 Rev55 — architecture detail catalog

**Status:** Proposed logical specification accompanying the unsigned SRS v2.6-draft.
**Evidence boundary:** repository source read-only at `1431ef81972b71303fd4a7909748fd3005769a3c`; no OpenAPI generation, service startup, database query/migration, product test or provider call was performed for this catalog.
**Related:** [report remediation crosswalk](REPORT_REMEDIATION_CROSSWALK_REV55_20261106.md), SRS §§3, 6, 9, 19–22, 31–32, and Data Table Register §§2, 4–8, 14.

## 1. Actor and permission boundary

Product roles and internal actors are different dimensions. A backend permission check must combine the verified principal, action, resource owner, tenant/assignment, current grant version and field/media scope; a client role label never grants access.

| Actor | Scope and allowed responsibilities | Child profile/media boundary |
|---|---|---|
| Parent | Own account/profile; use an allowed lesson version; create and manage own runs; view permitted lesson history/feedback; issue or revoke profile-share invitations/grants. | Own child profile and own run media only. May read Teacher-owned fields only through an active, field-scoped grant. |
| Teacher | Assigned organization/class/occurrence; author lessons; review filtered lesson inputs; use presets; run the Teacher flow; generate an optional Sketch Deck; view/reply to feedback in assigned scope. | Assigned profiles and runs only, plus fields allowed by active share/assignment. Run access follows current assignment, not creator identity. |
| School Manager | One school organization; roster/entitlements, Teacher publication review, school feedback and billing actions as authorized. | No profile contents or child media by default. |
| Platform Admin | Platform policy/catalog administration, global moderation/hide and school-scoped feedback response where authorized. | No routine access to child profile contents or media. No break-glass route is defined. Any exceptional media permission is OPEN and disabled pending a separate owner-approved policy. |
| Content Admin | Catalog/content review only when granted the corresponding permission. | No private profile or child-media access from content-review responsibility alone. |
| System Operations | Service health, recovery and safe operational telemetry. | No product-data access. Telemetry excludes child content/media and secrets. |
| AI Provider Adapter | Processes one authorized job contract and returns typed output to the backend. | No independent identity, database access or broad storage access; only the job-scoped allowlisted inputs. |

“Organization admin” is not established as a role distinct from School Manager. Until the owner resolves Q-13/role mapping, it must not be used as a synonym that silently changes authorization. Use **School Manager** for the current product role; treat “organization-admin capability” as an unresolved permission label.

## 2. Logical relationship and lineage catalog

These are typed logical references and ownership rules, not physical DDL. Same-owner relationships may later use database FKs; cross-owner links remain opaque, versioned references resolved through the owning port.

| Source owner/resource | Target owner/resource | Cardinality / typed reference | Required fence and revoke/lifecycle behavior |
|---|---|---|---|
| Parent profile | Profile revision | One profile to ordered immutable revisions; `ParentProfileRefV1` / `ProfileRevisionRefV1` | Owner edits create a new revision; Story stores the reviewed revision/hash, not a mutable profile copy. |
| Parent profile | Profile share grant | Zero or more invitations/grants; `ProfileShareGrantRefV1` | Grant carries issuer/recipient/tenant, purpose, field scope, version and lifecycle. Effective access requires ACTIVE grant. Exact accepter, expiry and field list remain OPEN. Revoke denies new reads and unaccepted jobs. |
| Teacher managed profile | BE1 enrollment/class | One active enrollment at a time; `ManagedProfileRefV1`, `EnrollmentRefV1`, assignment version | BE1 owns enrollment and assignment. Access is checked against the current assignment at read, playback and completion. |
| Parent/Teacher profile access | Story run input snapshot | Exactly one profile per run; `ProfileRefV1` plus owner-kind discriminator, grant/assignment version and approved snapshot hash | Never join by display name. Cross-role resolution is through BE1/Parent owner ports, not cross-owner FK. Accepted snapshots follow existing run lifecycle after later revoke. |
| Story run | Reusable lesson version | Zero or one `LessonVersionRefV1` for a run that uses a preset; exact version and content hash | Nullable for a run created without a lesson. Never resolve `latest`; a new lesson version does not retarget an existing run. Physical column/migration is a separate approved task. |
| Lesson occurrence | Lesson library version / plan revision | One pinned source version where reused, one current approved plan revision; opaque version ref plus plan revision/hash | A changed/reapproved plan creates a new revision and makes its Sketch Deck STALE. Existing references remain immutable. In-flight completion after supersession is OPEN; stale output cannot replace current head. |
| Story run | Parent activity list snapshot | Parent run may pin the lesson/version and activity-list snapshot/hash, but does not select one activity before video | Activity list is returned after video. Teacher sample remains pinned to one approved occurrence activity. |
| AI job | Exactly one target aggregate | Exactly one `target_kind` + opaque `target_ref` among the eight kinds in SRS §§9.9/22 | Includes expected target revision and input hash. The owner validates authorization and hash on admission/completion/reconciliation. No parallel nullable target refs. |
| Story/Lesson/AI job | Core asset and asset lineage | Owner holds typed `AssetRefV1`; Core owns bytes metadata, version, hash and lineage | Original asset is immutable. Each transform creates a derived asset/version edge; outputs never replace source. Modal scratch is attempt-scoped and cleaned by job lifecycle. |
| Billing quota grant | Accepted video-generation request | One immutable usage unit per accepted full-video request; `QuotaGrantRefV1`/`QuotaUsageRefV1` | Billing owns product quota. AI Policy owns compute reservations. Admission rejection produces no usage. No cross-module SQL transaction. |
| Teacher occurrence | Sample run / class projection confirmation | At most one successful sample claim per occurrence; `OccurrenceRefV1` and one-child run ref | Claim is retained after deletion/reassignment. Projection confirmation is a separate Teacher action and does not grant School Manager media access. |

### Logical name mapping

- **Logical names** use `schema.table`, for example `story.runs`.
- **Physical SQL identifiers** may use underscore names, for example `story_runs`, only when defined by reviewed DDL/mapping.
- **Python source names** identify a module/table declaration and are evidence of code, not a physical database observation.
- **Local database names** are the exact names observed in a dated environment snapshot.

These four labels are not interchangeable. Rev55 changes no table or identifier.

## 3. State and transition matrix

The table describes target business lifecycle from the current SRS. It is not a migration enum or a complete implementation. Polling, heartbeat and push receipt do not reset adult-wait time.

| Aggregate / current state | Event and guard | Next state / action | Actor/owner and timer | Boundary/open item |
|---|---|---|---|---|
| StoryRun `SCRIPT_REVIEW` | Adult confirms exact script revision/hash and requests video; idempotency key is new | `VIDEO_ADMISSION_PENDING`; create/reuse durable intent and start admission reconciliation | Story command; no adult-wait while admission is pending | Do not jump directly to `VIDEO_QUEUED`. |
| VideoGeneration `ADMISSION_PENDING` | AI Policy reservation and Billing quota receipt both confirmed under same key | `ACCEPTED`, then assign generation number, consume one unit, write outbox/job | Story/Billing/AI Policy owners; accepted deadline begins | Only accepted request consumes request cap/quota. |
| VideoGeneration `ADMISSION_PENDING` | Budget or quota is rejected before acceptance | `ADMISSION_REJECTED`; release reservation if held; StoryRun returns to `SCRIPT_REVIEW`; no job dispatch | Reconciliation resolves uncertain receipts before rejecting/releasing | No quota/request-cap charge. |
| VideoGeneration `ADMISSION_PENDING` | One or both owner responses are unknown/ambiguous | Keep pending; query the same idempotency key; do not dispatch or issue a second charge | Reconciler/system work; no adult-wait timer | No blind retry with a new key. |
| StoryRun `VIDEO_QUEUED` / `VIDEO_GENERATING` | Accepted job starts and advances; target revision/hash still current | Continue job stage; retries stay within the same accepted request | AI Jobs owner; deadline is the accepted request deadline | Scene retry is distinct from a new full-video request. |
| VideoGeneration `GENERATING` / `TECHNICAL_VALIDATING` | Scene retries exhausted or technical validation fails | `FAILED`; preserve the accepted usage unit; do not claim a Teacher playable sample slot | Story/Video owner; terminal status follows current retry policy | No extra refund or retry number is added here. |
| VideoGeneration `SAFETY_VALIDATING` | Automated check passes with required coverage and technical checks pass | `READY`; StoryRun projects to `VIDEO_READY`; issue playback only after authorization | Safety system + Story owner | No human final-video approval. |
| VideoGeneration `SAFETY_VALIDATING` | Automated safety fails, is incomplete or is indeterminate | `SAFETY_BLOCKED`; deny playback; surface safe finding code and request adult action on script | Safety system; adult-wait begins only when no job remains and adult command is required | Not a request for a person to inspect/approve the rendered video. |
| StoryRun `SAFETY_BLOCKED` | Adult edits/re-writes and confirms a permitted script revision, then submits a new allowed request | `STORY_GENERATING` or `SCRIPT_REVIEW`, then admission path; current blocked media remains non-playable | Parent/Teacher authorized for the run | Limits and quota from BR-11 remain; no hidden automatic reattempt. |
| StoryRun `SAFETY_BLOCKED` | Adult abandons or cancels; or existing idle closeout expires | `ABANDONED` or `DELETE_PENDING`; release active lock / start lifecycle purge as applicable | Current owner/system closeout | 144-hour reminder and 168-hour closeout follow BR-39 when the state is adult-wait. |
| AiJob `QUEUED` / `RUNNING` / `RETRY_WAIT` | Worker lease/attempt runs; expected hashes match | `RUNNING` then `SUCCEEDED`; owner applies typed completion | AI Jobs; bounded attempts and deadline | Provider output is untrusted until contract validation. |
| AiJob in progress | Cancel, stale revision or uncertain provider result | `CANCEL_REQUESTED`/`CANCELLED`, `STALE`, or `AWAITING_RECONCILIATION` | AI Jobs/reconciler | Do not overwrite aggregate head with stale output. |
| Lesson plan revision approved | Plan content changes and new revision is approved | New immutable plan revision; current deck becomes `STALE`; generate a new deck only if the Teacher enables it | Lesson owner | Existing runs remain pinned; whether accepted in-flight work may finish on superseded revision is OPEN. |
| Profile-share invitation/grant | Invitation issued, accepted, revoked or expires | Effective access only for active grant; revoke fences new access and unaccepted jobs | Parent/recipient/grant owner | Exact accepter, state labels, expiry and revocation effects for accepted work remain OPEN. |
| Lesson visibility/review | Teacher submits for PUBLIC; authorized School Manager reviews | Publish only after approval; deny/revise/hide actions retain version/history | Lesson/organization owner | Platform Admin-authored lesson approval record remains OPEN. No duplicate table implied. |
| Subscription / PaymentAttempt | Verified payment event, renewal failure or period end | Use the states in SRS §6.1.1; only verified provider event changes paid state/entitlement | Billing owner | Provider wire signature/merchant details require separate sandbox/ADR evidence. |

### Video request and retry accounting

| Unit of work | Counts toward full-video request cap? | Product quota | Failure/result rule |
|---|---:|---:|---|
| Admission rejected before acceptance | No | No usage | Return to script review; reconcile uncertain owner receipts first. |
| Accepted initial full-video request | Yes, one | One immutable Billing usage unit | Unit is retained after technical/provider/safety failure. |
| Automatic scene technical retry | No additional full-video request | No additional usage | Bounded by existing scene retry rule in BR-45. |
| Adult quality regeneration after an existing video | Yes, one within current run limit | One additional unit when accepted | Script revision must be re-confirmed; old rejected video stays hidden. |
| Story rewrite request | Not a video request | No video usage | Separate rewrite cap; outputs are immutable story revisions. |

No item above changes the existing numeric limits in BR-11/BR-45 or the Teacher sample-claim behavior in BR-26/FR-T-16.

## 4. API workflow contract inventory

All paths below are **logical target candidates**, not final OpenAPI. Shared transport rules, idempotency, error shapes and security requirements remain in SRS §§9.6, 21.1–21.7. Main application source, the separate StoryRun-lite fixture app and Modal functions are different surfaces.

| Workflow / proposed resource | Actor and owner check | Input/version fence | Sync or async | Expected safe outcomes |
|---|---|---|---|---|
| Identity and role resolution: `/v1/me` | Verified Firebase principal; BE1/product permission resolution | Issuer/UID; current role and assignment versions | Sync | `AUTH_REQUIRED`, `ACTION_NOT_ALLOWED`; never trust client role claim. |
| Parent profile and sharing: `/v1/parent/profiles`, `/v1/parent/profile-share-invitations`, `/v1/profile-share-grants/{grant_id}` | Parent owns profile; invitee/org scope resolved; active grant required for recipient reads | Profile/grant opaque refs, expected revision, idempotency; exact acceptance sequence OPEN | Sync command/read | `RESOURCE_NOT_FOUND`, `STALE_REVISION`, `ACTION_NOT_ALLOWED`; denied cross-tenant reads do not reveal existence. |
| Parent lesson discovery/reuse: `/v1/lessons`, `/v1/lessons/{lesson_id}/versions/{version_id}` | Public or active selected/school grant; Parent actor | Exact version ref/hash, visibility/grant version | Sync read | Not found/denied uniformly; no lookup of `latest` after pin. |
| Parent optional Sketch Guide: `/v1/parent/sketch-guides`, `/v1/jobs/{job_id}` | Parent authenticated; generic topic/difficulty only | Guide contract version, topic catalog ref, idempotency; no profile/artwork/age | Async generation + polling | Rate-limit/output-invalid/provider-safe errors; all failures return to drawing; no video quota. |
| Parent StoryRun and capture: `/v1/story-runs`, `/v1/story-runs/{id}` | Parent owns one profile; one active run per adult | One profile ref, source asset hash, optional exact lesson version, context/script revision | Command/read plus AI Jobs | `ACTIVE_RUN_EXISTS`, `MULTI_CHILD_NOT_SUPPORTED`, upload validation, `STALE_REVISION`; never select a Parent activity before video. |
| Parent story review/video: `/v1/story-runs/{id}/...`, `/v1/jobs/{job_id}`, `/v1/story-runs/{id}/playback-token` | Current run owner/permission; authorized script gate | Expected run/script/context/lesson hash; idempotency for commands | Review sync; admission and generation async | `TRANSCRIPT_NOT_CONFIRMED`, `SUBJECT_NOT_CONFIRMED`, `VIDEO_QUOTA_EXCEEDED`, `AWAITING_RECONCILIATION`, `SAFETY_BLOCKED`; no final human video approval. |
| Post-video Parent activities: `/v1/story-runs/{id}` detail or an owner-defined lesson-delivery resource | Parent run owner and current lesson visibility/share rules | Pinned version/activity list hash | Read after video availability | Return only the activity list pinned to that version; no pre-video activity selector. Exact endpoint remains OPEN until OpenAPI task. |
| Teacher lesson upload/filter/review: `/v1/lessons`, `/v1/lessons/{id}/source-documents`, `/v1/lesson-occurrences/{id}/plan-revisions` | Assigned Teacher and organization | File allowlist/limits, source hash, parser version, reviewer and plan revision | Upload/extraction async; preview/review sync | `UNSUPPORTED_LESSON_TYPE`, `LESSON_FILE_TOO_LARGE`, `OCR_NOT_SUPPORTED`, parse-uncertain/review errors; raw source is not sent to AI. |
| Teacher Sketch Deck: `/v1/lesson-occurrences/{id}/sketch-decks`, `/v1/jobs/{job_id}` | Currently assigned Teacher/occurrence | Approved plan revision/hash, enabled switch, idempotency and sketch cost admission | Async generation; revision-specific reads | No job if disabled; `LESSON_PLAN_NOT_APPROVED`, `STALE_REVISION`, rate/cost rejection; not video quota. |
| Teacher sample and class projection: `/v1/lesson-occurrences/{id}/sample-runs`, `/v1/lesson-occurrences/{id}/projection-confirmation` | Current responsible Teacher; eligible child selection policy remains OPEN | Occurrence/plan/activity/profile/assignment versions; single sample claim | Command + async video job | Capacity/assignment/plan errors; at most one successful sample; confirmation is separate from generation. |
| Lesson publication/share/moderation: `/v1/lessons/{id}/visibility`, `/v1/lessons/{id}/review`, `/v1/lessons/{id}/grants` | Author/School Manager/platform permission within tenant | Source/version/review/grant revision, idempotency | Sync command/read | Manager approval before Teacher PUBLIC; hide/revoke fences new library access; Platform Admin lesson approval detail OPEN. |
| Lesson feedback/history: `/v1/lesson-feedback`, `/v1/parent/lesson-history` | Parent linked profile or authorized school participant | Lesson/delivery ref, tenant, history window config | Sync paginated read/write | Feedback thread only; no direct chat/media attachments; history 30/60-day value OPEN. |
| Quota and payment: `/v1/video-quota`, `/v1/video-quota/purchases`, `/v1/payments/{provider}/callback` | Parent account or authorized School Manager billing scope; provider callback verified | Server-resolved scope, price version, idempotency/provider event ID | Sync summary; async payment/admission | `VIDEO_QUOTA_EXCEEDED`, duplicate callback idempotent; school-vs-Teacher pool precedence OPEN. |

No route above should be described as implemented unless mounted in the relevant application composition and supported by source/runtime evidence. The Rev51 source snapshot reported main FastAPI composition without AI Jobs/StoryRun-lite and a separate ephemeral StoryRun-lite app. Rev55 statically reviewed the merged source at commit in the header: `lesson_library` is included by the main router composition; `ai_jobs` is not; StoryRun-lite remains a separate app. No route count or runtime behavior was re-tested.

## 5. Role-specific screen and navigation inventory

Proposed screen IDs describe workflow coverage and primary state/action. They do not approve the visual design, exact menu labels, pricing or final IA. “Continue” means follow the current server state; hidden/disabled AI actions are not called.

| ID | Role / screen | Key states and primary actions | API/resource groups |
|---|---|---|---|
| P-01 | Parent sign-in and child profiles | Signed out, empty, list, create/edit, delete pending; sign in, select/manage profile | `/v1/me`, `/v1/parent/profiles` |
| P-02 | Lesson discovery/detail | Public/shared visibility, age/topic filter, unavailable/revoked; inspect and select an exact lesson version or continue without one | `/v1/lessons`, lesson version refs |
| P-03 | Drawing setup / optional guide | Topic/age-band general prompt, guide off, loading, ready, limited/failed; enable or skip guide | `/v1/parent/sketch-guides`, jobs |
| P-04 | Draw and capture | Camera preview, capture, retake, gallery upload, upload error; capture/upload artwork | StoryRun input/media |
| P-05 | Subject confirmation | Candidate/confidence, confirm, edit subject, re-suggest, mismatch; adult confirms/corrects | VLM job/run revision |
| P-06 | Context and script review | Context pending/confirmed, script initial/rewrite/review, remaining rewrite count; confirm exact revision | StoryRun/context/story APIs |
| P-07 | Video admission/progress | Admission pending/rejected, queued, scene generation, safety validation, failed/blocked; background status/cancel where allowed | Video admission, AI Jobs |
| P-08 | Playback and activities | Private playback, captions, complete/regenerate, post-video activity list; no Parent activity selector before video | Playback token, pinned lesson version/activity list |
| P-09 | History and feedback | 30/60-day policy pending, list/detail, feedback thread, deleted/unavailable lesson | Parent history and feedback |
| T-01 | Teacher dashboard/classes/roster | Assignment list, empty roster, profile list, permission denied; choose assigned class/child | BE1 roster and assignment |
| T-02 | Lesson author/import/filter | Draft, upload, quarantined, parse issue, teacher correction/review; upload or edit allowlisted fields | Lesson source/extraction APIs |
| T-03 | Occurrence plan review | Draft, missing safety review, pending approval, approved, stale; add activities and approve plan | Occurrence/plan/activity APIs |
| T-04 | Sketch Deck author/run state | Disabled, generating, partial-ready, ready, stale, failed; enable, preview, present, skip/regenerate permitted step | Deck and AI Job APIs |
| T-05 | Teacher sample setup | Eligible roster unresolved, sample slot available/used, child/plan/activity selection; begin one-child run | Occurrence, roster, StoryRun |
| T-06 | Teacher capture/context/script review | Upload/capture, transcript/subject/context review, lesson-direction on/off, script review; confirm exact script | StoryRun and review APIs |
| T-07 | Teacher video progress | Admission, generation, safety, ready, blocked, failed; progress, retry only when policy allows | Video Job APIs |
| T-08 | Class projection and completion | Private preview, projection confirmation, playing, complete/quality regenerate; record projection explicitly | Playback, occurrence confirmation |
| M-01 | School Manager lesson review | Pending/approved/needs changes/public/hidden; compare revisions, review, approve Teacher public request | Lesson review/moderation |
| M-02 | School organization/roster/quota | School scope, assignments, capacity, quota summary, purchases; manage within billing/tenant permissions | Organization, BE1, Billing |
| A-01 | Platform Admin catalog/moderation | Draft, pending review, public, hidden; author/review/hide and preserve version history | Learning Content/Lesson moderation |
| A-02 | Platform policy/roles/entitlements | Permission, quota and provider policy views; exact role/capability mapping partly OPEN | Policy/permission/Billing |
| A-03 | School feedback response | School-scoped feedback thread; reply without exposing it to another organization | Feedback APIs |

Navigation hierarchy, final labels, design tokens, visual states and screen approval remain product/design work. The inventory adds no new role or ability.

## 6. Domain aggregates and ports

Use aggregates for lifecycle/invariants, not one class per table. Domain packages remain independent of frameworks, providers, storage and queues.

| Aggregate / contract | Owner and invariants | Main ports/contracts | Repository implementation status at reviewed source |
|---|---|---|---|
| AdultIdentity / Organization / Assignment | BE1; verified actor scope, tenant and current class assignment | Identity/Assignment query ports, `ActorScopeV1`, assignment version | BE1 domain/application/infrastructure and HTTP routers exist; target cross-role permissions not runtime-verified. |
| ParentChildProfile / ProfileRevision | Parent; owner edits create immutable revision, age 36–120 months, no exact DOB | Parent profile repository, consent/context contract | Target only in this SRS/register; not present in Rev43 local DB snapshot. |
| ProfileShareGrant | Parent/BE1 boundary; field-scoped, versioned, revocable, no owner merge | Invitation/grant command/query port, `ProfileShareGrantV1` | Target contract; exact acceptance actor/field set/expiry OPEN. |
| LessonLibraryItem / LessonVersion | Lesson; immutable version, visibility, lineage, review gate | Lesson repository, source filter, activity catalog port | Lesson Library source/routes exist; database/API proof remains bounded to cited source/evidence. |
| LessonOccurrence / PlanRevision / SketchDeckRevision | Lesson; exact approved plan pin, activity safety review, deck stale fence | Lesson command/query ports, `LessonPlanApprovedV1`, Sketch Deck job contract | Source packages and routes exist; not every target transition is proven live. |
| StoryRun / RunInput / StoryRevision | Story; exactly one profile, immutable inputs/context/script refs, owner epoch | Story repository, profile/lesson/asset ports, commands/review contracts | StoryRun-lite domain/application/HTTP slice exists separately; main durable Parent target is not mounted. |
| VideoGeneration / Scene | Story/video lifecycle; admission receipt, request cap, generation and scene fences | Billing admission, AI Policy reservation, AI Jobs dispatch, Core asset validation | Target architecture; main durable API/runtime not established. |
| AiJob / Attempt / Outbox | AI Jobs; one target, idempotent dispatch/completion, bounded retry/deadline/reconciliation | Job repository, queue dispatch, provider port, completion command | Packages/routes exist; AI Jobs router is not included in main router composition at reviewed commit. |
| CoreAsset / AssetLineage / UploadSession | Core; immutable source and derived version, private access, scoped lifecycle | Object storage, media validation, upload-session port | Core/media source exists; exact target DB coverage differs from Rev43 snapshot. |
| VideoQuotaGrant / Usage / Subscription / PaymentAttempt | Billing; immutable grants/usage, verified callback, no cross-owner SQL | Billing repository, payment-provider adapter, admission receipt | Target data model; billing schema absent from local Rev43 DB snapshot. |
| FeedbackThread / Notification | Lesson/Notification; school scope, inbox as source for notices, minimal payload | Feedback and delivery ports, outbox consumers | Target capabilities; do not infer routes from isolated modules. |

## 7. Package dependency map (target and observed source)

### Target dependency direction

```text
interfaces / transports
        ↓
application commands, queries, services
        ↓
domain aggregates and policies
        ↑
infrastructure adapters implement application/domain ports

contracts are versioned boundary schemas; they do not own business rules.
```

### Static source observations

| Package | Intended responsibility | Observed source at `1431ef8` | Status/limit |
|---|---|---|---|
| `sketch2life.domain` | Framework-free entities, value objects and policy | `domain/` contains BE1, story-adjacent, vision, lesson, AI Jobs, billing and legacy/demo subpackages | Presence does not establish that every aggregate is mounted or production-ready. |
| `sketch2life.application` | Commands, queries, services and ports | `application/commands`, `queries`, `services`, `ports`; includes story-run-lite and multiple older feature modules | Static tree only; no complete dependency/import graph generated. |
| `sketch2life.contracts` | Versioned request/result/event/provider contracts | `contracts/schemas`, including AI/story/job schemas | Contract presence is not route availability. |
| `sketch2life.infrastructure` | SQL, queue, object storage, AI/provider adapters and composition | `infrastructure/` contains persistence, AI, AI Jobs, Lesson Library, object storage, queue and story-run-lite | Source providers/adapters may be disabled or unmounted. |
| `sketch2life.interfaces.http` | Thin routers and app composition | `router_composition.py` mounts health, BE1, demo routers and Lesson Library; it does not mount `ai_jobs` | Read-only source inspection. No runtime/OpenAPI regeneration. |
| `story_run_lite_app.py` | Separate local synthetic Parent slice | Builds a separate FastAPI app and mounts `routers/story_run_lite.py` with in-process `BackgroundTasks` | Not equivalent to main API, durable outbox/AI Jobs or production tenancy. |
| `deployment/modal/srs_v23` | Development Modal worker code/config | Merged source contains Qwen/FLUX/audio/SAM worker files and workload registry | Workload enabled state/inference quality require the existing separate evidence; no Modal call here. |

No package-layer refactor or implementation is part of Rev55. A machine-checked import graph, dependency rule test, mounted OpenAPI inventory and runtime database crosswalk remain separate verification tasks.
