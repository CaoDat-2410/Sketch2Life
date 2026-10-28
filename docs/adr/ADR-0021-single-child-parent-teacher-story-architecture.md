# ADR-0021: Single-child Parent/Teacher story architecture

- Date: 2026-10-27
- Status: PROPOSED — owner product decisions through Q146 are recorded; owner review of the SRS/table register and technical baseline remains pending.
- Authority: User-confirmed product decisions in FEAT-063. Technology, schema and operations details are proposed against current repository architecture.
- Scope: Parent Android, Teacher web, Teacher AI Sketch deck, one-child AI story/video flow, organization class capacity/billing, target data model and local Docker + Modal demo.
- Supersedes for the target flows: conflicting assumptions in ADR-0019/ADR-0020 about collaborative classroom runtime, shared canvas, PixiJS drawing motion, multi-child/session-scoped story runs and final-video review. Historical ADRs are not modified.

## Context

The repository has a legacy Parent flow, a newer Android foundation, a Teacher web app, a Python modular monolith, organization/class/roster records, collaborative classroom entities and a separate video pipeline. The owner’s target has two distinct product flows: Parent Android and Teacher web. The old collaborative classroom runtime is removed from these flows while simple organization-owned classes and a Teacher roster remain.

The intended outcome has three distinct AI capabilities. Teacher first imports and approves one lesson plan for an occurrence; a separate Teacher-only AI Sketch process turns every approved activity into a shared, white 16:9 teaching surface with progressive line-sketch guidance and short explanations. This deck remains a main-flow step in Teacher. In the separate video flow, Teacher selects one activity and one sample child. Parent follows profile → optional generic-topic AI line-sketch guide → child drawing/capture → idea → post-capture subject confirmation → approved catalog activity → story. The adult can request a temporary 3–5-step guide or skip it; only generic topic/difficulty is sent to its generator, with no child profile, age, voice, photo or artwork. Guide output is private, provenance-tracked and cleaned up on expiry; failure never blocks drawing/capture. Teacher Sketch Deck and Parent Sketch Guide are separate targets and experiences. Both story flows create one-child image-to-video stories and use adult transcript/subject/context/script review. Video plays after automated technical and safety checks, without a final human video approval. A Teacher may project the occurrence's one-child sample to the class after an auditable, per-occurrence confirmation; the class receives no reusable playback access or export.

The owner has also requested a repository-wide entity/table redesign and a detailed SRS, data register, code architecture, error contract, operations, monitoring, rate limits and local Docker setup. This ADR records the coherent proposal; it does not authorize implementation.

## Confirmed product decisions

### Roles and ownership

- Parent Android uses apps/mobile; apps/ui-mobile is a behavior reference. Teacher web uses apps/teacher-ui.
- Parent and Teacher accounts are separate. Parent-owned and organization-owned Teacher profiles are never linked/shared.
- Parent profile is owner-only. Teacher-managed profile belongs to the organization. Organization admin manages roster/class assignments but has no default access to private story/media.
- Each organization starts with 10 class slots and may purchase additional capacity at one configurable per-slot rate, monthly or annual. One responsible Teacher is assigned to each class; a Teacher may hold multiple classes. Each managed child is in at most one active class at a time.
- Teacher-created profile intake uses a structured form and may be based on parent-survey answers; no questionnaire OCR or file-import flow.
- Teacher run content is accessible to the currently assigned Teacher. On class reassignment, transfer run/media access to the new responsible Teacher with metadata audit; the former Teacher immediately loses access and old playback tokens are invalidated. Organization admins retain roster/billing access but no default media access.

### Single-child lessons and runs

- Remove QR/lobby/admission, collaboration, shared canvas, group drawing, multi-child runs, class-wide video batches and stage progression.
- A story run and AI job bind exactly one scalar child profile. Every adult account has at most one active run.
- One teaching occurrence has one approved lesson plan. A plan may contain multiple activities, but a single sample run chooses one activity and one child.
- Each Teacher occurrence may produce at most one safety-passed representative sample video. A technical run failure or safety block before the first playable claim does not consume the sample slot; a failed pre-claim run can be replaced. After the first playable claim, the slot never reopens, including when the video is hidden and all quality re-generations fail or are exhausted (Q127). Deleting/canceling/transferring a run preserves the consumed claim.
- Parent activity choices come only from globally approved catalog entries. Teacher may define an occurrence-specific activity and confirm it via a safety checklist.

### Teacher AI Sketch teaching deck

- Teacher AI Sketch Deck is Teacher-only and remains a main-flow step after plan approval. Parent may request or skip a separate AI-generated line-sketch guide before drawing. The guide uses only a generic topic/difficulty, no child/profile/voice/photo/artwork; it is temporary/private, provenance-tracked, and subject review remains after photo capture.
- Generate one immutable, shared deck revision for the approved occurrence plan. It covers all activities in that plan and does not consume a child profile, child artwork or video quota.
- For each drawing guide, produce 3–5 progressive line-sketch steps with simple placement/layout hints and short child-facing prompts/explanations appropriate to the occurrence's target age band.
- Teacher presents on a white landscape surface, navigates Back/Next, selects activity/subject, skips a guide or regenerates an individual sketch. Children draw on paper. No shared digital drawing canvas, freehand editing, arbitrary slide-text/layout editing or PPTX export.
- Sketch generation uses a versioned structured-output contract and an independent AI compute reservation/rate limit. Numeric limits, model, license, cost and quality remain synthetic POC gates. Lesson owns deck/step rows; Core owns generated asset metadata/lineage; AI Jobs dispatches a distinct lesson target without any child/profile ref.
- Q146 owner decision: Parent may optionally request a 3–5-step AI line-sketch guide for a generic topic such as a butterfly, with skip/non-blocking behavior, no child data in model input, temporary private output with provenance/cleanup, and separate sketch compute/rate accounting outside video quota. This is a product baseline decision; implementation remains gated by the separate exact-scope approval and technical/model/retention evidence.

### Story-video pipeline

For each one-child drawing/story run: image understanding by VLM → structured Vietnamese story by LLM → 5–15-scene storyboard (about six seconds per scene, with system-selected total duration of 30–90 seconds) → adult reviews/requests rewrites and confirms the script/storyboard → prepare a per-drawing Character Bible and scene references → generate each scene with image-to-video LTX-2.5 on Modal L40S → validate identity/color/style/action consistency → compose scenes in storyboard order with FFmpeg → generate a fixed neutral Vietnamese adult voice, synchronize narration and Vietnamese subtitles, and mux the audio/subtitles (music and sound effects off) → run automated safety checks across assembled frames/narration/subtitles → issue private playback when all technical and safety checks pass. Scene generation has one initial attempt plus two automatic technical retries. The exact LTX workflow/runtime and quality thresholds remain POC gates. If an adult marks the output unsuitable, hide it once its replacement request is accepted, return to script review, and require confirmation before retrying; the video request and quota limits remain as previously confirmed. Do not create a public gallery, downloadable file or final human-video approval step.

### Content, reviews and media

- Parent drawing and idea flow supports text and recorded voice. Whisper transcribes voice; an adult reviews/corrects the transcript. Teacher can use browser camera or upload a phone photo.
- Lesson import accepts text-bearing PDF, PPTX and DOCX up to 25 MB and 100 pages/slides. Reject encrypted/password-protected files. Scanned-page OCR is not supported. Preserve source and text revisions.
- Profile stores age in months and age band, adult-entered interests, observations, achievements, app-generated run history and separate adult-entered outside experiences. Support needs are adult-authored, not diagnoses, restricted and excluded from AI context by default. Child name/nickname is never sent to AI.
- Each run pins a minimal, adult-approved profile context snapshot.
- Each story has one initial draft and at most three AI rewrites. Parent may suggest changes but cannot edit generated story/scene content directly. Teacher additionally sets story direction from the approved lesson/class plan. Superseded revisions remain internal and are hidden from normal UI.
- Transcript, subject, activity, lesson and context are confirmed at their own prerequisites. The explicit approval gate before video is the final story/script/storyboard revision confirmation. No final video approval gate exists.
- Output is MP4 720p, 16:9, system-selected 30–90 seconds, neutral adult Vietnamese narration, Vietnamese subtitles and background music always off. Video is displayed immediately after technical validation. No file download/export or public URL.
- If an adult considers the video unsuitable, return to script review and require confirmation before regenerating. Permit one initial full-video request and at most two quality-regeneration requests in the run; every accepted request counts even if it later fails. Per scene, permit one initial attempt plus at most two automatic technical retries.
- `DRAFT` and every other state requiring adult action enter adult-wait only when no AI job is active. At +144 hours create one deduplicated in-app reminder, attempt push best-effort, and attempt email only if the current Parent/Teacher owner has a verified address; inbox is authoritative and delivery failure does not change run state. At +168 hours `VIDEO_READY` auto-completes, while other adult-wait states become `ABANDONED`; both release the current-owner lock but keep content until manual deletion. `VIDEO_ADMISSION_PENDING` is system work, not adult-wait; rejection returns to `SCRIPT_REVIEW` with a new adult-wait timer. AI jobs have a separate six-hour deadline from acceptance, including queue time. Cancellation of unfinished runs releases the lock immediately and starts lifecycle deletion. Neither cancellation nor idle closeout refunds quota or reopens a successful Teacher sample claim (Q129, Q133, Q134, Q136).
- Deleting a completed run removes linked drawing/audio/transcript/context snapshot/story/video content through lifecycle; preserve only minimal metadata audit. There is no separate video-delete action.

### Organization billing

- Each organization pays for a base subscription that includes 10 class slots, plus add-on slots at one configurable per-slot price, monthly or annually, in VND. Exact amounts are versioned commercial configuration and are not specified. No tier ladder.
- MoMo and VNPAY are the initial recurring payment adapters; VietQR is excluded from V1.
- New slots activate after verified payment; mid-cycle upgrade is prorated for remaining time without changing renewal date. Admin can turn off auto-renew; paid access remains to period end. V1 has no automatic prorated refund.
- Failed renewal has seven days of grace. Afterwards block creating new classes and story runs while preserving existing class, roster, history and payment access.
- Downgrade requires selecting classes to suspend; preserve their records in read-only state.
- Send billing admin in-app and email reminders 7 and 1 day before due, plus payment success/failure and grace-expiry notices.
- Video quota uses calendar months in `Asia/Ho_Chi_Minh` and is separate by Parent account and Teacher organization. Each accepted full-video request consumes one unit, including provider/technical/safety failures; no accepted unit is refunded (Q128). Scene retries do not consume additional quota. When exhausted, reject new video requests but keep existing playback/saved-data access. Allocate current-month included grant first, then purchased grants FIFO. Included units expire at month end; purchased top-ups carry forward until consumed. Starting mid-month receives the full included grant. Included amounts remain configurable until synthetic cost benchmarking (Q115–Q121, Q126).
- Once an adult accepts a request to replace a video marked unsuitable, hide the prior video from playback immediately; keep it internal until run deletion, and do not restore playback if replacement generation fails (Q116).
- Deleting a run after a video request was accepted does not refund the consumed quota unit; delete linked content but retain minimum quota usage ledger metadata (Q119). Quota top-ups are one-time purchases and never auto-renew (Q120).

## Proposed architecture decision

### Product/application boundary

Keep two independent entry points backed by one modular monolith:

- Parent client authenticates its Parent account and addresses Parent profile/run resources.
- Teacher client authenticates a separate Teacher account and addresses organization/class/managed-profile/lesson resources.
- Backend resolves all role and resource authorization. The UI cannot authorize itself from local state.
- Cross-feature work travels through versioned command/event contracts and opaque references. No module reads/writes another module’s private tables.

### Data ownership and source of truth

| Fact | Authoritative owner |
|---|---|
| Authentication identity | Firebase Authentication; backend verifies token and derives UID |
| Organization/classes/assignments/Teacher roster | BE1 |
| Parent-owned profile | Parent module |
| Published activity catalog | Learning Content |
| Lesson source/extraction/occurrence/approved plan | Lesson module |
| Lesson Sketch Deck revisions/steps and current-plan validity | Lesson module; asset bytes/lineage remain in Core |
| Story run, script, review decisions and video generations | Story module |
| AI dispatch, attempts and completion receipts | Durable AI Jobs with one typed target among STORY_RUN, VIDEO_GENERATION, VIDEO_GENERATION_SCENE, LESSON_SOURCE_DOCUMENT or LESSON_SKETCH_DECK_REVISION |
| AI policy/model profile/resource/copy evidence | AI Policy |
| Product video quota grants and usage | Billing `video_quota_grants` + `video_quota_usage`; AI Policy resource rows only meter platform GPU/compute |
| Asset metadata and original/derived lineage | Core Asset port; binary in private object storage |
| Organization subscription, invoice and class capacity | Billing |
| In-app/email delivery state | Notifications |

A `story.runs` row stores exactly one typed scalar profile reference. The immutable `story.run_inputs` revision pins the selected profile revision and the bounded, approved context snapshot/hash alongside the matching drawing and idea/transcript refs. Parent and Teacher profile tables remain separate. Application ports validate cross-owner references; no generic shared child table or cross-owner foreign key links them.

### Target table disposition

Repository source declares 86 production mappings plus five test-only fixtures; this is not a live database count. After the full source/target relation and canonical-field audit, the proposed target keeps/refactors 38 current tables and adds 40 new tables, for 78 active. The 48 legacy/read-only source mappings are the earlier 35 collaboration/canvas/video/activity/preset tables plus 12 AI Policy provider-copy registries and `ai_policy.resource_receipt`; 78 active + 48 legacy = 126 projected physical. The four proposed helper/snapshot entities removed are `ai_jobs.job_subject_refs` (the StoryRun target already resolves the sole profile), `ai_jobs.job_result_assets` (Story/Lesson aggregates own output refs), and `story.profile_context_snapshots` plus `story.profile_context_snapshot_items` (the bounded approved snapshot belongs in immutable `story.run_inputs`). No source rows are dropped or copied, and the target ERD excludes legacy tables.

The target count is not a goal to minimize at the expense of history or privacy boundaries. Keep a separate table when it has an independent owner, access policy, immutable revision/event history, retry/receipt lifecycle or retention/deletion behavior. The AI Policy reduction defers 13 current source tables that only support provider-copy registry/receipt workflows absent from the synthetic V1 demo. Synthetic Modal transfer is tracked on existing `ai_jobs.attempt`/`job_events` and Core asset lineage. New resource-command idempotency and bounded result snapshots are stored on `ai_policy.resource_event`; historical `resource_receipt` rows remain read-only. Reintroducing provider-copy tables requires a separate real-data retention/authorization review.

All 40 new target tables have a relationship entry in §6 of DATA_TABLE_REGISTER.md. Same-owner relationships use internal FK/unique/check constraints; cross-owner links use typed, versioned opaque references validated through owner ports. Parent and Teacher profiles stay intentionally separate. The register identifies canonical field ownership so profile attributes, run context, media metadata, output asset refs and quota usage are not stored twice. Story enforces same-revision integrity with composite keys across video generation, generation scene and storyboard scene; the repeated scene revision key is immutable constraint data. Story commands update current input/story/video pointers and the user-facing run-state projection atomically under an aggregate version check, with `video_generations.state` canonical for generation state. AI Jobs have exactly one target kind/ref/revision, and each generation-scene row points back to its exact scene job. A composed StoryRun detail endpoint reads through owner ports; it does not add a read-model table or query private schemas directly.

Do not drop/truncate/copy a table as part of this design. Preserve old identifiers and meanings; never convert a collaborative session ID into a story run. Any future archive/purge plan needs separate review, backup/restore evidence and approval. Full source-to-target disposition and logical dictionary are in FEAT-063 DATA_TABLE_REGISTER.md.

### Proposed implementation baseline

| Concern | Proposed baseline | Confidence/status |
|---|---|---|
| Parent | React Native 0.87 + TypeScript, apps/mobile | Exact repository baseline; React Native 0.88 is the latest upstream release as of 2026-10-27 and requires a compatibility review before upgrade |
| Teacher | React 19 + Vite 8.3, apps/teacher-ui | Existing repository foundation |
| Backend | Python 3.13 target, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | Verify dependency/model compatibility before changing current 3.12 workloads |
| Domain/application | Modular monolith, explicit module owners, ports and versioned contracts | Architecture direction; implementation structure proposed in SRS |
| Database | PostgreSQL 17 | Existing Compose baseline and durable business/job source of truth; evaluate PostgreSQL 18 before an approved deployment/migration |
| Queue/limits | Redis 8 + RQ | Delivery/backpressure/rate limits; PostgreSQL outbox/receipts remain durable |
| Local object storage | MinIO, private S3-compatible API | Local demo canonical media store; Modal uses isolated per-attempt Volume scratch transfer |
| Authentication | Firebase Authentication only | Backend verifies ID tokens and authorizes resources; no Firebase data products |
| Push notifications | Standard Web Push for browsers; Android provider not selected | Best-effort only; select an adapter only after a synthetic device/distributor POC covers distribution, opt-in, invalidation and background delivery. Do not treat UnifiedPush as the default. FCM/Firebase messaging is excluded by the repository's Firebase-Authentication-only rule |
| ASR | Existing faster-whisper adapter; Modal L4 candidate | Pin and validate Vietnamese latency/quality |
| VLM | Qwen2.5-VL-7B candidate; Modal L4 candidate | Not a promoted default. Existing Qwen3-VL quality evidence is NO_GO |
| Story LLM | Qwen2.5-7B candidate; Modal L4 candidate | Validate schema, safety, Vietnamese quality, license and latency |
| Teacher Sketch line-art | Versioned sketch-generation provider port; exact image model/checkpoint is open | Modal L4 candidate | Must create progressive age-appropriate line-art; evaluate synthetic fixtures, stability, safety, license and cost |
| Structured outputs | Pydantic v2 + versioned JSON Schema | API/application/worker boundary | Validate VLM entities/anchors, story/storyboard, Character Bible, Sketch Deck and safety result before persistence |
| Image/reference preparation | Python, OpenCV, Pillow; SAM/SAM2 optional after POC | Worker/container | Preserve original artwork and write derived reference assets with separate lineage |
| Vietnamese TTS | VieNeu-TTS candidate; Modal L4 candidate | Validate neutral adult voice and subtitle alignment |
| Video | Official LTX-2.5 pipeline on Modal L40S GPU class | Owner selected GPU class. Exact image/model/runtime is not pinned or benchmarked |
| Consistency validation | OpenCV metrics plus versioned vision adapter | Modal L4 candidate or CPU path by stage | Fail closed when visual identity anchors or action/safety checks fail or are indeterminate |
| Composition | FFmpeg in local worker/container | Pin binary and validate output |
| Monitoring | structlog JSON, OpenTelemetry Collector, Prometheus, Grafana | Local demo proposal; production alert destination is open |
| Email | Mailpit locally; production provider via port | Production choice open |
| Containers | Docker Compose for API/worker/PostgreSQL/Redis/MinIO/ClamAV/monitoring/Mailpit | Local demo; production host/region not selected |

The official LTX system-requirements page states a 32GB+ GPU VRAM minimum. Modal’s current GPU guide lists L40S at 48GB GPU RAM and L4 as a separate option. This supports L40S for LTX and does not prove an exact pipeline is already deployed. [LTX requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements), [Modal GPU guide](https://modal.com/docs/guide/gpu).

React Native 0.87 remains the pinned repository baseline, although 0.88 was released on 2026-10-19. Vite 8.3 is the current Teacher web lockfile range. PostgreSQL 17 stays aligned with the repository's Compose image; PostgreSQL 18 is a separately evaluated future migration. Do not perform these framework/database upgrades as part of this documentation task. [React Native releases](https://reactnative.dev/releases/overview), [Vite releases](https://vite.dev/releases), [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/).

The current repository's `apps/mobile` is a fixture/contract harness, while `apps/ui-mobile` is a behavior reference; camera, microphone and persistent profile integrations are not all implemented. Treat Parent as a port/rebuild guided by the older flow, not as a complete feature restoration. Teacher web and the expanded local Compose services also require implementation. The production host/region remains open.

The official MoMo subscription documentation describes recurring frequency, initial authorization, scheduled payment and request identifiers. VNPAY recurring-payment details are subject to merchant contract/sandbox validation. [MoMo Subscription](https://developers.momo.vn/v3/docs/payment/api/wallet/subscription/), [VNPAY recurring specification](https://sandbox.vnpayment.vn/apis/files/VNPAYGW_RecurringPayment_Techspec2.1.0-VN.pdf).

### Clean-code and data consistency rules

- Domain entities own state transitions/invariants; no ORM or API DTO is treated as a domain model.
- Application commands load aggregates through repository ports, authorize the actor, run a transaction, persist state/outbox and return typed results.
- Routes and workers are thin adapters. Workers never update Story or Lesson rows directly after AI calls; they submit a target-specific completion command with expected aggregate revision/hash.
- Infrastructure owns SQLAlchemy mappings, queues, storage and provider SDKs. Model output is untrusted until validated against versioned contracts.
- Tables have one source-of-truth owner. Other modules store opaque versioned refs/hashes, never a second mutable copy.
- Parent profile and organization profile remain physically and logically separate. Adult-approved context is a run snapshot; profile source data is not modified by AI.
- Originals are immutable; derived assets receive new IDs/versions and source lineage.
- An AI Job has exactly one discriminated target: StoryRun, Lesson Sketch Deck or Parent Sketch Guide. Story/video jobs resolve exactly one child profile from the canonical StoryRun; neither sketch target contains child/profile refs. Parent guide uses generic topic/difficulty and a temporary private Core Asset result with expiry/lineage; it is not attached to a profile or StoryRun. All targets share dispatch/attempt/outbox infrastructure but use separate application use cases and owner ports. A worker result must match target kind/ref, expected revision/hash and applicable assignment fence before it updates the target owner.
- A lesson Sketch Deck revision pins the approved plan revision/hash, includes all approved activities and validates every instruction group as 3–5 ordered sketch steps before READY. Changing the plan makes the old deck STALE. A per-step regeneration creates a new immutable deck revision and preserves unchanged asset lineage.
- Database constraints enforce one-child runs, one-active-run-per-adult, one active enrollment per profile, one responsible Teacher per class, one successful sample per occurrence, bounded story/video/scene retries and one quota unit per accepted video request. Deleting a successful Teacher sample retains the consumed occurrence claim.
- Billing owns immutable monthly included/top-up quota grants and the immutable `video_quota_usage` ledger. Parent usage is keyed to its Parent account; Teacher usage to its organization. Allocate the current calendar-month included grant before purchased grants FIFO. Accepted requests are never refunded, even after provider/technical/safety failure or deletion; scene retries do not create new usage. AI Policy resource reservations/events meter platform GPU/compute only. Admission is an idempotent application saga, not a cross-module SQL transaction: persist `VideoGeneration=ADMISSION_PENDING`, reserve compute budget with a lease at AI Policy, and record quota usage in Billing's own transaction. Only confirmed receipts transition the Story intent to accepted and dispatchable; release the tentative reservation if Billing rejects, and reconcile ambiguous receipts by request key before dispatch. Expired orphan reservations are cleaned up; a reservation bound to an accepted request is retained/settled with the job. No duplicate inference is dispatched. No mutable remaining-balance field is authoritative and modules do not join/write another module's private tables.
- Teacher Sketch does not consume `video_quota_usage`. It uses a separate request-rate bucket and compute-cost reservation/ceiling through AI Policy. Configure numeric caps after synthetic model/cost benchmarking. Do not apply the 1+2 video request cap to Sketch.
- Each class projection is separately confirmed by the responsible Teacher for that occurrence and recorded with actor/time. That confirmation is not a final video approval.
- Idempotency and transactional outbox protect run creation, AI dispatch, payment callbacks and notifications. Stale AI output is recorded but cannot overwrite newer state.

### Operations and security

- Local Compose targets API, worker, PostgreSQL, Redis, MinIO, ClamAV scanner, OTel Collector, Prometheus, Grafana and Mailpit, with health checks/persistent volumes. Uploads remain quarantined until clean malware scan; scanner failure fails closed.
- Q135: Image/audio/lesson upload uses authenticated resumable sessions through the backend. `core.upload_sessions` owns session scope, expected metadata, lifecycle and expiry; `core.upload_parts` owns per-chunk receipt, hash, size and opaque object ref. Store each application chunk (maximum 4 MiB) as its own private quarantine object with `PutObject`; after continuity/size/SHA-256 checks, assemble with bounded resources and write the completed asset with one final `PutObject`. Do not use the S3 Multipart Upload API. Only a complete, checksum/media validated and AV-clean asset may attach to Story/Lesson. The mobile/web client never receives MinIO/S3 credentials or endpoints. Verify the pinned MinIO SDK's object-write, replay, abort and expiry behavior in a synthetic network-interruption POC before integration.
- Teacher Sketch input transfer contains only the approved lesson/plan revision and required activity text, never a roster, child profile or child drawing. Generated line-art is a derived Core asset with hash/lineage and stays in the private Lesson deck; malformed, unsafe or stale outputs do not become presentable.
- Modal calls originate only from the backend worker adapter. Mobile/web contain no Modal, payment, database or object-store credentials.
- Local MinIO remains private and canonical. Backend stages a validated input copy to an isolated Modal Volume prefix per job/generation/attempt, invokes Modal with only small versioned refs/hashes, validates returned manifest/hash/codec/duration/safety, stores only accepted output in private MinIO and removes scratch data. Synthetic proposal caps are 48 MiB input/256 MiB output, 300-second transfer timeout, 900-second scene attempt, one active LTX job plus five queued and 24-hour orphan cleanup; benchmark before enabling.
- Automated, versioned output-safety validation checks sampled frames, complete narration transcript and subtitles after video composition. No playback capability or persistent playable output is issued on block/indeterminate result.
- On Teacher reassignment, BE1 enters durable transfer-pending and fences the former Teacher and playback tokens. A separate Story transaction transfers `active_owner_teacher_id` and the active-run lock; BE1 finalizes the new assignment only after a Story receipt. During the pending window no Teacher receives media access. If the target Teacher already has an active run, reject with 409; if an owner step fails ambiguously, keep access fenced and reconcile/compensate before retry. `created_by_actor_ref` is immutable provenance and does not grant access. A valid same-organization AI job is not canceled and may complete if input/run hashes remain current; only the current assigned Teacher can view or continue it. For emergency offboarding, an organization admin may use a separate reasoned, metadata-only force-close command to release a conflicting run lock; retain quota/sample claims and never grant admin media access (Q130, Q134).
- `StoryRun.run_state` records story business lifecycle; ASR/VLM/story/video processing uses durable `AiJob.job_state` and `job_stage`. `SketchDeckRevision` has a Lesson-owned lifecycle and its own status resource; a Sketch job is never represented as a StoryRun state. Only StoryRun states with no active AI job and a required adult action enter adult-wait. Set `adult_wait_started_at` server-side in UTC; at +144 hours write one deduplicated inbox item, attempt push best-effort, and send email only to the current owner's verified address through the notification/identity ports. Do not store raw recipient email in notice content or logs. Close at +168 hours: `VIDEO_READY` becomes `COMPLETED`, other adult-wait states become `ABANDONED`. Both release the current-owner lock and retain content until manual deletion. `VIDEO_ADMISSION_PENDING` is not adult-wait; rejection returns to `SCRIPT_REVIEW`. Accepted video jobs have a separate six-hour deadline. Polling, heartbeat and delivery receipt do not reset inactivity (Q133, Q134, Q136).
- Apply a calendar-month video quota separately to Parent accounts and Teacher organizations. Billing atomically records one usage row in its own transaction before dispatch for each accepted request; compute budget must first be reserved at AI Policy and the two receipts reconciled by idempotency key. No refund is issued for provider/technical/safety failure or run deletion (Q128). Scene retries remain within the same unit. Current-month included grants are allocated before purchased grants FIFO; included units expire at month-end and purchased units carry forward (Q126). Initial allowance values are set after synthetic cost benchmarking.
- Schedule AI work round-robin across eligible owner scopes and FIFO within each scope, with global/per-scope queue bounds. Before Billing admission, reserve worst-case GPU seconds through AI Policy using a bound of 45 scene attempts per full-video request. Ordinary daily-cap exhaustion cannot stop already-reserved work; the circuit breaker closes admission to new requests. Numeric per-request/daily caps are required before live generation and set after synthetic benchmark. An emergency operator/safety abort may stop work after admission and does not refund quota under Q128; communicate this accepted product risk before confirmation.
- Teacher Sketch has its own rate-limit and compute budget/cost cap; no Sketch command creates a Billing video-quota usage row. Numeric limits are set after synthetic benchmark and reported separately from story-video usage.
- Before external model transfer, perform bounded text/PII preflight on drawing input. Keep the original immutable; if personal text is detected, send only a masked derived asset with lineage, or fail closed when it cannot be safely masked. This reduces risk but does not guarantee OCR of all handwriting.
- PostgreSQL outbox/job records remain the durable workflow source; RQ only delivers work. Modal inference uses `Function.spawn()` and persisted `FunctionCall` IDs, followed by nonblocking polling/reconciliation, so no RQ worker waits for GPU completion. Before implementation, compare this baseline with Temporal for crash recovery, durable timers, cancellation/compensation and operational cost; record the decision in a separate ADR.
- Use PostgreSQL RLS and least-privilege runtime roles as defense-in-depth; runtime role must not own tables or have BYPASSRLS. Require MFA for organization/billing administrators and Android Play Integrity through a backend adapter (no Firebase App Check). The threat model covers client/API, DB, Redis/RQ, MinIO, Modal, payment, and push boundaries.
- Notifications keep the in-app inbox as source of truth. Push payloads contain only a notice kind and opaque route; no child/story/media/playback details. Web Push uses standard browser push; Android uses a non-Firebase provider port pending a delivery POC.
- Initial server limits are 60 authenticated requests/min/account, 20 unauthenticated requests/min/IP, 2 run creates/min/account and one active run/current-owner scope. Upload control/status and chunk requests have separate limits so resume works: control create/complete/abort 10/min/account; chunk PUT 60/min/account with 40 MiB new bytes/minute and at most three active sessions/account; status 30/minute/session. Exact same-digest retries count as requests but not new bytes. Teacher Sketch uses a separate configurable bucket/cost cap, finalized after synthetic benchmark. Return 429 and `Retry-After`; enforce file/audio caps independently.
- Redacted structured logs, OpenTelemetry traces, Prometheus metrics and Grafana dashboards cover API, queue, story-video and Sketch stages, GPU-seconds, retries, storage lifecycle, billing webhooks and notification delivery. Keep Sketch compute and video quota panels separate. No media/text/child identifiers in metric labels.
- Standard error envelope: stable code, safe localized message, correlation ID, retryable flag, optional retry-after and safe field errors. Detailed mapping is in the SRS.
- Synthetic profiles/artwork/audio only for the live demo. Actual child data is excluded pending separate purpose/authorization/provider transfer/retention/access review.
- Manual PostgreSQL and MinIO backup/restore are documented for local demo; production recovery targets remain open.

## Consequences

- One active backend with explicit modules avoids premature distributed services while preserving future service seams.
- Parent does not receive organization/class permissions; organization admin does not automatically receive story/media access.
- AI job state is durable; Redis/RQ is a delivery mechanism, not the source of truth.
- Teacher Sketch is occurrence-wide teaching guidance; it has no child subject and remains separate from one-child story/video runs even though both use the durable AI Jobs dispatch layer.
- A Teacher occurrence’s sample uniqueness is separate from a run’s video-generation cap and monthly quota. One initial plus up to two quality regenerations remain one sample run; every accepted full-video request consumes both a run-cap slot and one scoped quota unit.
- Technical or safety failure before the first playable sample claim leaves the occurrence slot available. Once claimed, the slot remains consumed even when the video is later hidden and all quality regenerations fail; no recovery run is available for that occurrence.
- The target schema grows from the source declarations because normalized Parent/profile/lesson/story/billing/notification entities are added while historical data is retained.
- Production provider transfer, payments, hosting, real child data and destructive archive cleanup are later implementation decisions.

## Owner review gate and implementation boundary

The owner requires the detailed SRS and table register to be Vietnamese (retaining established technical names) and reviewed/approved before final diagrams or PDF are produced. ADR acceptance and runtime code/schema approval are separate. This document is a proposal; it does not authorize migrations, provider calls, Modal deployment, payment execution, tests/builds, real-child data use, production deployment or Git publication.

## Related records and sources

- FEAT-063 SRS: features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md
- FEAT-063 table register: features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md
- Historical related ADRs: ADR-0019 and ADR-0020.
- [LTX system requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements)
- [Modal GPU guide](https://modal.com/docs/guide/gpu)
- [Firebase ID token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [Modal function invocation methods](https://modal.com/docs/guide/function-invocation-methods) and [Modal FunctionCall SDK](https://modal.com/docs/sdk/py/latest/FunctionCall)
- [PostgreSQL 17 row security](https://www.postgresql.org/docs/17/ddl-rowsecurity.html), [Android Play Integrity](https://developer.android.com/google/play/integrity), [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API), [UnifiedPush Android specification](https://unifiedpush.org/developers/spec/android/) (one option to evaluate, not selected), and [ClamAV usage](https://docs.clamav.net/manual/Usage)
- [Temporal workflow execution](https://docs.temporal.io/workflow-execution) and [tasks/timers](https://docs.temporal.io/tasks) as an alternative to compare; Temporal is not selected for the current baseline.
- [MoMo Subscription](https://developers.momo.vn/v3/docs/payment/api/wallet/subscription/)
- [VNPAY recurring specification](https://sandbox.vnpayment.vn/apis/files/VNPAYGW_RecurringPayment_Techspec2.1.0-VN.pdf)
