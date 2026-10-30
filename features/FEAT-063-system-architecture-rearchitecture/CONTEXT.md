# FEAT-063 — Whole-repository architecture redesign

## Dev backend synchronization — 2026-10-30

Owner requested the latest dev backend in this feature branch for testing. Incoming tip `111ae547` adds existing Lesson Library/BE1 fixes and upstream evidence/UI drafts; Modal remains present. Revision numbers overlap across independent backend and UI/API work: use exact plan filenames and hashes for authority. Upstream UI Rev36 approval does not approve backend Rev36. See `evidence/notes/DEV_BACKEND_SYNC_20261030.md` for actual checks and limitations.

## Rev36 response to Rev35 review — 2026-10-29

Owner requested fixing the three P3 notes in the independent Rev35 PLAN_REVIEW_PASS. `plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` is the current documentation draft; implementation approval and applicable owner decisions remain pending. See `evidence/notes/REV36_REVIEW_RESPONSE_20261029.md`.

## Historical: Rev35 response to Rev34 review — 2026-10-29

The owner supplied a NEEDS_REVISION review of Rev34. `plan/PLAN_REV35_BACKEND_SRS23_ALIGNMENT_20261029.md` was the subsequent draft, with independently checked migration, job, identity, CI and FEAT-064 coordination corrections; Rev36 now supersedes it. Earlier revisions and approvals remain historical. S1 dispositions, owner decisions and implementation approval remain pending.

## Historical: Rev34 SRS 2.3 alignment — 2026-10-29

The owner requested aligning the backend plan to the FEAT-063 SRS 2.3 draft. `plan/PLAN_REV34_BACKEND_SRS23_ALIGNMENT_20261029.md` supersedes Rev33 for future planning; S1 operation disposition and implementation approval remain pending. The Parent activity ordering conflict across the SRS/register is documented, not silently resolved. See `evidence/notes/REV34_SRS23_PLAN_ALIGNMENT_20261029.md`.

## Historical: branch continuation — 2026-10-29

The owner selected SRS2.3 and instructed continuing in the existing merged branch. Current checkout: feature/feat063-be-foundation at4f071242, including Modal and CI repair history. Rev33 remains awaiting scoped approval; no S1/S2/S3 implementation is inferred from the merges. S1's candidate operation inventory and file boundaries are prepared in `plan/REV33_S1_EXECUTION_SCOPE_DRAFT_20261029.md`; review/error/operation dispositions must be approved before code. See `evidence/notes/BE_FOUNDATION_MERGED_BRANCH_CHECKPOINT_20261029.md` for the read-only findings.

## Backend slice 1 plan - Plan Rev33 (2026-10-29), AWAITING_APPROVAL

- Plan: `plan/PLAN_REV33_BACKEND_SLICE_1_LEGACY_FENCE_IDENTITY_JOB_TARGETS_20261029.md`, SHA-256 `B087E87CF0A27004ECAE54AF8623B3FD81A894E7C709EA83037A23841DF92919`.
- Three additive backend slices on the v2.3 baseline: S1 feature-flag fence for the classroom/demo surface, S2 Parent identity scope and `parent.*` profile tables, S3 AI job owner-scope and target-kind columns. Seven open decisions (OD-1 to OD-7) are listed in the plan.
- Documentation only. No code, migration, test run or approval record was changed; approval must be recorded against the exact hash in `approvals/TASK_APPROVAL.md`.
## UI component patterns and states — Plan Rev36 (2026-10-30)

- Lifecycle: REVIEW; nine generated component boards, group-specific prompt/motion notes, API mapping and evidence are complete. Owner visual approval is pending before any asset can be approved/applied.
- Approved Plan Rev36 SHA-256: `300104684514C4C6F67614F58DDE402668AAC24AF2204F9B1BCA7A5BBEA2D336`; approval and exact AC1–AC7 scope are in `approvals/TASK_APPROVAL.md`.
- Output index: `assets/generated/ui-components-rev36-20261030/COMPONENT_INDEX.md`; each group folder contains one PNG, `PROMPT.md` and `MOTION.md`; central `PROMPT_LOG.md` and `MOTION_SPEC.md` provide the shared reference.
- Coverage: visual foundations; Parent dialogs; web decision dialogs; toast/inline notices; loading/empty/auth/not-found/forbidden/stale/service states; filtered upload/extraction; quota/video job; separate lesson/profile grants; school-scoped feedback/notifications.
- API boundary is explicit: Rev31 Lesson Library covers lesson CRUD, filtered upload, lesson grants/Manager decisions/Parent lesson read and Admin moderation. Video/quota, child-profile grant, LessonOccurrence history/feedback and new AI/video flows remain SRS target APIs.
- Motion notes enforce true API state, byte-based upload progress, no fake job percentages/ETA, non-refundable accepted video quota and reduced-motion behavior.
- Samples are fictional. Palette numbers are proposals only. Assets remain under `assets/generated/`; no product UI/API/database code, tests or runtime operations were performed.
- Evidence: `evidence/EV-063-29_UI_COMPONENT_PATTERNS_REV36_20261030.md`.

## UI screen mockups and motion notes — Plan Rev35 (2026-10-30)

- Lifecycle: REVIEW; 14 visual drafts and their per-screen prompt/motion notes are complete. Owner visual review is pending before any asset can be approved/applied.
- Approved Plan Rev35 SHA-256: `0EBBE2D7E983663F448B167F39FE42AD6C89A2E38EE5390A054673FC2C42723C`; direct request and exact scope are recorded in `approvals/TASK_APPROVAL.md`.
- Output index: `assets/generated/ui-mockups-rev35-20261030/SCREEN_INDEX.md`; one PNG, `PROMPT.md` and `MOTION.md` per screen. `PROMPT_LOG.md` and `MOTION_SPEC.md` hold shared provenance and detailed behavior notes.
- Coverage: Parent lesson library/detail, optional line-sketch drawing, capture/subject confirmation, story review, video progress/playback/activities, history/feedback; Teacher workspace/authoring/filtered upload/session Sketch Deck; School Manager Public review; Platform Admin catalog moderation.
- Source baseline: SRS v2.3-draft §3, §6, §20, §21.5, §31.1–§31.7; Rev31 Lesson Library API contract; Rev31 API inventory; Rev32 API purpose catalog; existing Parent assets and Teacher/Admin UI source.
- All samples are fictional. Assets remain under `assets/generated/`; no product UI/API/database implementation was changed. No tests or runtime checks were requested or run.
- Evidence: `evidence/EV-063-28_UI_MOCKUPS_AND_MOTION_NOTES_REV35_20261030.md`.

## Current legacy API regression - Plan Rev34 (2026-10-29)

- Plan Rev34 SHA-256: `308F4FEA6576BAB08ACCD86B62616FE463C94D099FC27EBF301E855C4756F5B1`; direct owner approval is recorded in `approvals/TASK_APPROVAL.md`.
- “Old APIs” is scoped to pre-Lesson-Library BE1/classroom and Demo/local-flow surfaces from the Rev32 catalog. The newer Lesson Library and conditional local storage example are not part of this rerun.
- AI-dependent classifier, media/understanding, ranking, story/whiteboard-video, and AI planner endpoints are excluded. Candidate/unmounted route contracts are tracked separately from active APIs.
- Smoke-tested 77 active old non-AI method/path operations: 52 returned 401, 23 returned 422, 2 health endpoints returned 200, and 0 returned 5xx. Requests omitted credentials/valid write bodies, so this is route-dispatch evidence only.
- Existing API suites: 109 passed / 1 failed in the non-PostgreSQL batch; 3 passed / 1 failed in the BE1 PostgreSQL suite. Failures: stale app route-difference baseline after Lesson Library was mounted, and BE1 consent schema/runtime mismatch (`effective` required but not allowed by the DB constraint).
- Disposable `sketch2life_be1_acceptance` was dropped; persistent `sketch2life` remains at the Rev33 target. No AI call or product/test-expectation change was made. Full detail and uncovered success paths are in EV-063-27.

## Current local API verification - Plan Rev33 (2026-10-29)

- Plan Rev33 SHA-256: `513FEE246CF1DD2B062BE146996C362C7C726667A9529E0E2342962084CF4DE1`; direct owner approval and exact local scope are recorded in `approvals/TASK_APPROVAL.md`.
- The owner authorized non-AI API workflow tests and execution of the database migration. This supersedes Rev31's explicit test/migration exclusion only for the local Compose database and a separately isolated disposable `be1_acceptance` database.
- Applied `20261028_ll_0001` to local Compose PostgreSQL `sketch2life`; it was at `20261014_0004` before the run. Alembic applied prerequisite `20261024_0005`, leaving independent AI/media heads untouched. Main DB is verified at the Lesson Library target revision.
- Lesson Library HTTP integration suite: 5/5 passed. Existing BE1 HTTP suite: 3 passed, 1 failed with `409 CONSENT_NOT_EFFECTIVE`; the test exposed that runtime authorization requires consent state `effective`, while the model/database constraint permits only `pending` or `revoked`. The successful consent path is unrepresentable and needs separately scoped schema/domain remediation.
- A disposable `sketch2life_be1_acceptance` database was migrated and then dropped. ClamAV was healthy. MinIO pulls failed (Quay returned 401; Docker Hub denied access), so storage-example routes used an in-memory storage adapter; MinIO adapter and bucket initialization remain unverified.
- Targeted Ruff and `compileall` passed. No AI, AWS/Firebase, remote DB, real child data, `.env` edit, or deployment was used. See EV-063-26 for commands, defects fixed, results, and limitations.

## Current API purpose catalog - Plan Rev32 (2026-10-28)

- Plan Rev32 SHA-256: `FD189D3E2684CE2930624AFD7412C54F9BB53339209790F7B319B534C41E087C`; approval is recorded in `approvals/TASK_APPROVAL.md`.
- Catalog: `artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md`, SHA-256 `E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881`.
- The catalog assigns a purpose and runtime-exposure status to each of the 135 method/path declarations in the Rev31 inventory. It adds no routes or behavior.


## Current backend implementation and API inventory - Plan Rev31 (2026-10-28)

- Plan Rev31 and Addendum A are approved in `approvals/TASK_APPROVAL.md`; recorded SHA-256 values: `BC948B27F5CFADD05EC6D12B0B7D989241CDEB6FC3CA6CAB1521988C712BBB8C` and `570BC65BE74A82261EC2455147EAF33FB0575B166B73EF506084BBF07A62727D`.
- The Lesson Library API contract is implemented as an additive layer: Teacher CRUD/versioning, filtered upload and deterministic extraction, Manager review/publication, scoped sharing, Parent read/download and Platform Admin moderation. AI generation is not implemented.
- Existing Parent, Teacher, BE1 and demo method/path declarations are preserved. The complete static route list and mount status are in `artifacts/API_INVENTORY_FEAT063_REV31_20261028.md`: 135 declarations, 121 unconditional combined-app operations, 3 local-only storage examples and 11 candidate/fixture/unmounted declarations.
- Implementation includes additive Alembic migration source and three Lesson-owned support tables. The target-model crosswalk is 92 active + 48 legacy/read-only = 140 projected physical mappings; this is source-derived, not a live database count. The SRS remains an unsigned product-design draft.
- Static source review only. No test/build, Docker execution, database access or migration, security validator, provider/AWS call or deployment was performed. Runtime behavior and migration execution remain unverified.


## Historical local Docker and MinIO storage example - Plan Rev30 (incorporated in Rev31)

- Plan: `plan/PLAN_REV30_LOCAL_DOCKER_MINIO_STORAGE_EXAMPLE_20261028.md`, SHA-256 `F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794`.
- Owner authorized local Docker setup, MinIO as the first local object store, environment configuration that can later target AWS S3, and one example. The exact scope is recorded in `approvals/TASK_APPROVAL.md`.
- Implementation adds the API service, private local MinIO bucket initialization, a Boto3 S3-compatible port/adapter, and a local-only upload/read/delete example. It does not implement Lesson CRUD or persist lesson metadata.
- Lifecycle: IN_PROGRESS. Automated tests, Docker build/pulls, Compose startup, database changes, and AWS access are excluded from Rev30 and have not been run.
- MinIO is local-demo-only because the upstream Community repository is archived and distribution is source-only; the production storage provider remains open. See Rev30 and the official upstream references there.

## Historical backend lesson-platform plan — Rev28 (superseded by Rev29)

- Historical plan: `plan/PLAN_REV28_BACKEND_LESSON_LIBRARY_UPLOAD_REVIEW_PARENT_READ_20261028.md`, SHA-256 `22CBC9E4360B39BDD995B683B5B9681D962D3D1C54355F929F0B1C3BE2387FE6`; superseded by Rev29.
- Owner confirmed inclusion of lesson-plan upload, Manager approval/Public publication and Parent read/share. Plan Rev28 includes Teacher lesson CRUD, safe upload with deterministic non-AI extraction, Manager review, revocable audience grants, Parent read-only access and Admin hide.
- EV-063-21 records the scope answers and the library-upload ownership gap. The plan proposes library-owned source-document/revision records; the existing occurrence-owned upload tables are not reused.
- No AI, frontend work, child-profile/occurrence/video integration or production storage provider selection is included. Implementation remains blocked on explicit approval of the exact plan hash in `approvals/TASK_APPROVAL.md`.

## Historical initial recommendation — Plan Rev27 (superseded by Rev28)

- Draft plan: `plan/PLAN_REV27_BACKEND_BASIC_LESSON_CRUD_DRAFT_20261028.md`, SHA-256 `984B54DE505A4C86B9334079D6FC9086A0E5ABC9E1736C21BC0734096454E3BD`.
- Recommended first slice: manually authored, text-only Teacher lesson draft CRUD with ordered activities, versioned edits, soft archive and author/school isolation. No AI, upload/parser, public sharing, Manager approval, Parent read, occurrence or video flow is included.
- Repository inventory: EV-063-20 at `evidence/BACKEND_BASIC_LESSON_CRUD_REPOSITORY_REVIEW_20261028.md`. Existing BE1 authentication/assignments and generic `learning_content` candidate were reviewed; no live database was inspected.
- Status: historical narrow recommendation; owner answers are incorporated into Rev28. No implementation approval, code change, migration, test/build or AI/Modal operation was authorized by Rev27.

## Historical backend API contract - Plan Rev29 (implemented under Rev31)

- Plan: `plan/PLAN_REV29_BACKEND_LESSON_API_CONTRACT_AND_ENTITY_NAMING_20261028.md`, SHA-256 `B63B5BEC21C71BFD154EEA08741C167B3B144AF1133A17695D4C63E6760BCD6A`.
- API contract: `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`; Rev29 pre-reconciliation SHA-256 `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`, current Rev31-reconciled SHA-256 `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`.
- Rev29 makes the entity/storage mapping, versioned base path, actor/scope rules, method/path contracts, request/response names, purposes and errors explicit. Rev28's owner-selected scope is unchanged.
- Status: AWAITING_APPROVAL for the full product API implementation. Rev30 separately approves only the local Docker/MinIO storage example; no Lesson Library API routes or migration are authorized.

## Original documentation goal (historical)

The SRS and Data Table Register v2.3 remain unsigned product-design drafts. Rev31 separately authorizes and implements the Lesson Library backend slice as an additive layer; it does not sign off the SRS or authorize applying the migration to a live database.

## Current additive platform baseline through Q195 (2026-10-28)

- The platform is an additive architecture layer. Preserve the existing Parent and Teacher flows, image capture behavior, video-generation pipeline, quota, safety and lifecycle requirements except for the specific updates recorded in SRS §31.
- V1 is Vietnamese-first, Montessori-inspired and designed for children aged 3–10. Exact age-band boundaries inside 36–120 months remain open. Adults guide, observe and support; learning stays child-centered and accommodates multiple ages.
- Roles are Platform Admin, School Manager, Teacher and Parent. Each school is one organization. Permissions are scoped, server-authorized, audited and revocable.
- Parent and Teacher accounts/profile owners remain separate. A Parent may invite a Teacher/school to receive an accepted, field-scoped child-profile grant; either side’s access remains bounded and revocable.
- Reusable lessons and immutable versions are separate from class occurrences and Parent uses. Lessons may define drawing steps, subject knowledge, one or more outdoor activities and notes, optional script direction, and optional visual/slide assets. When reusing a lesson, Parent/Teacher may request AI-edited draft/personal copies with lineage; the published source remains unchanged.
- Lesson visibility is PRIVATE, SCHOOL, SELECTED_AUDIENCE or PUBLIC. Selected audiences may be groups or named invitees. Teacher lessons remain school-only until a Manager approves publication to PUBLIC; Platform Admin may moderate/hide under platform permissions.
- Used lesson versions and occurrence/history references remain stored when unpublished. Library discovery/download/content access is revoked and returns only after republication or a new valid grant.
- Teacher uploads use a structured template and allowlist filter. The original file and raw full text do not go to AI. Teacher reviews/corrects extracted structured fields before any AI assistance; generated lessons, activities and visuals start as drafts and require authorized human review.
- Parent flow: child starts drawing; during the drawing session an adult may enable a line-sketch guide; after drawing, capture the child’s artwork; generate a new video for that child through the existing pipeline; show configured outdoor activities after video. Teacher line-sketch generation is also opt-in per session; disabled means no job.
- Teacher keeps the existing occurrence and one-child sample flow, can use a lesson as a preset, chooses one eligible representative child at random, and pins one approved activity for the sample. Parent may generate a separate new personalized video from an authorized lesson.
- Videos are newly generated from each child’s drawing and approved profile context; no video is reused across children. A lesson script direction can be toggled; subject mismatches require adult confirmation/correction before another AI suggestion.
- Parent can see delivered lessons and authorized public/shared lessons, download permitted lesson content, and give lesson feedback. Teacher, Manager and Platform Admin may respond inside the responsible school scope. No general chat, completion mark or drawing-photo upload is added to feedback.
- The platform bears provider costs. Billing supports school, Teacher and Parent quota scopes; Managers can buy/allocate school quota and Parents can buy their own package/top-up. Package values and charge precedence remain open.
- The v2.3-draft logical baseline is 89 active + 48 legacy/read-only = 137 projected physical. Rev31 adds three Lesson support tables; the current source-derived implementation crosswalk is 92 active + 48 legacy/read-only = 140. These are not live database counts.
- Source of truth: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §31, `artifacts/DATA_TABLE_REGISTER.md` §14 and proposed ADR-0022. Do not lock a provider or final stack from this documentation amendment.

## AI model and Modal pipeline reassessment — Plan Rev26 pending approval (2026-10-28)

- Research note: `evidence/MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md` (EV-063-19).
- Plan Rev26: `plan/PLAN_REV26_MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md`, SHA-256 `ECD0A0A6435193A903313409B699574FE9DB30BAAB8498A714A3FC54C75EEABC`; status AWAITING_APPROVAL for the exact documentation amendment.
- Current canonical SRS and Data Table Register remain v2.3-draft. Research recommendations do not select a model/checkpoint, change a quota/sample rule, authorize a benchmark, or change the SRS.
- The v2.3 draft baseline and Rev31 implementation crosswalk are distinguished in the SRS: 89/137 and 92/140 respectively. Neither is a live database inventory; live-schema review and migration rehearsal remain open.
- No code, live database, Modal account, model inference, GPU spend, benchmark, product test/build, generated media or real-child data was used. User answers Q11/Q13 remain open on who can initiate AI lesson suggestions.

## Historical product baseline through Q146

Historical statements below preserve prior decisions. Where they conflict with Q147–Q195, the current additive baseline above and SRS §31 take precedence. Specifically, Q147–Q195 supersede the earlier “never linked” profile statement with revocable grants, make both sketch capabilities opt-in during a session, set age to 3–10, and place Parent outdoor activities after video.

- Two separate flows and accounts: Parent Android and Teacher web. Parent and Teacher profiles are private to their respective ownership scopes and never linked.
- Teacher retains organization-owned classes and profiles. Each class has one responsible Teacher; a Teacher may be assigned multiple classes. Organization admin manages roster/assignment, not media. Run/media access follows the currently responsible Teacher; the mutable current-run owner/lock is separate from immutable `created_by` provenance. Reassignment uses a durable BE1/Story transfer, fences the former Teacher and old playback tokens, then transfers access with metadata audit. Offboarding normally requires replacement assignment first; an authorized organization admin may force-close a conflicting run through a reasoned, metadata-only audited command, without media access and without releasing quota or sample claims (Q130/Q134).
- Organization's paid base subscription includes 10 class slots. Extra class capacity uses one configurable per-slot price, monthly or annual; MoMo and VNPAY are the initial recurring-payment adapters, VND. VietQR is out of scope. Add-on slots activate after payment and are prorated. Cancellation leaves paid access through period end; V1 has no automatic prorated refund. Failed renewal has 7-day grace, then blocks new classes/story runs while retaining existing data access. Downgrade requires admin to select classes to suspend; their data is read-only, not deleted. Billing admin receives in-app/email reminders 7 days and 1 day before due and payment/grace notices.
- No collaborative classroom runtime: no QR/lobby/admission, shared canvas, group session, multi-child run, collaborative drawing or stage progression. No PixiJS motion.
- Teacher-only AI Sketch generates one shared teaching deck for each approved lesson occurrence. It covers every approved outdoor activity in the plan and provides age-appropriate 3–5-step line-sketch sequences, concise layout/placement hints, and short explanations for children. Teacher presents on a white landscape web surface using Back/Next, activity/subject selection, skip, or per-sketch regeneration. Children draw on paper. No freehand shared drawing, manual arbitrary text/layout editing, or PPTX export. The deck has no child/profile/artwork input and does not use video quota; sketch rate and compute caps are separate and benchmark-configured.
- Parent has no Teacher AI Sketch Deck and does not preselect the subject of the child's artwork. Before drawing, an adult may optionally request a separate AI line-sketch guide with 3–5 progressive steps for a generic topic/difficulty, or skip it. The guide request contains no child profile, exact age, voice, photo or artwork; output is private, temporary, provenance-tracked, and uses separate sketch resource caps outside video quota. Parent captures the child's artwork first, then VLM proposes subjects and the adult confirms/corrects them before choosing an approved outdoor activity. Skip/failure does not block drawing/capture.
- A story run/job has exactly one child. Each adult account has at most one active run; Teacher uniqueness follows the current responsible Teacher owner field, not immutable creator identity. A Teacher lesson occurrence has one approved plan, can list multiple activities, selects one activity and one child for its sample. There is at most one safety-passed sample video per occurrence. A technical/safety failure before playback does not consume the slot; after first playable claim the slot stays consumed even if all quality regeneration fails; no recovery run is allowed (Q127).
- A Teacher may project the one-child sample to the class after a separate, auditable confirmation by the responsible Teacher for that occurrence. This is not final-video approval and gives class members no reusable account/playback access.
- Parent chooses an activity from the globally approved catalog. Teacher custom activities are occurrence-specific and require the responsible Teacher’s safety checklist.
- Both flows accept text and voice idea; Whisper is used and an adult confirms/corrects transcript. Teacher can capture with browser camera or upload a phone photo.
- Teacher imports text-bearing PDF/PPTX/DOCX up to 25 MB and 100 pages/slides. No scanned-page OCR; reject encrypted/password-protected files. Teacher reviews extraction and can save corrected text as a revision. Teacher profiles use structured quick entry, not questionnaire OCR.
- Profile stores age in months and age band, interests, learning observations, achievements and outside experiences with sources/approximate dates where available. App-generated run history and adult-entered events/daycare/trips remain separate sources. Adult approves a minimal context snapshot per run. Names/nicknames and support-needs notes are not sent to AI by default. Support needs are adult-authored, not diagnosis.
- Each story has one first draft plus at most three AI rewrites. Parent can suggest rewrites without directly editing scenes; Teacher can additionally set story direction from lesson/class plan. Each new story revision requires review and confirmation.
- Video quota follows calendar months in `Asia/Ho_Chi_Minh` and is scoped separately to Parent account and Teacher organization. An accepted full-video request consumes one quota unit before dispatch even if it fails technically or is safety-blocked; no accepted unit is refunded (Q128). Scene retries consume no extra unit. Billing owns the grants and append-only usage ledger; AI Policy owns only platform GPU/compute accounting (Q132). Allocation uses current-month included first, then purchased grants FIFO; included quota expires at month end, top-ups carry forward until used. Included amounts are configured separately and finalized after synthetic cost/latency benchmarking.
- Only explicit pre-video approval is the final story/script/storyboard confirmation. No final video approval. `DRAFT` and all other no-job states waiting for an adult enter adult-wait; `VIDEO_ADMISSION_PENDING` remains system work. At 144 hours create one in-app reminder, attempt push best-effort and send email only if the current owner has a verified address; inbox is authoritative. At 168 hours `VIDEO_READY` becomes `COMPLETED`, other adult-wait states become `ABANDONED`, and the current-owner lock is released while content remains until manual deletion. Admission rejection returns to `SCRIPT_REVIEW` with a new adult-wait timer; active AI jobs have a separate six-hour deadline from acceptance (Q129/Q133/Q134/Q136). An adult may cancel any unfinished run to release the lock and start lifecycle deletion.
- Video pipeline: one child's drawing → VLM image understanding/visual identity anchors → structured LLM story (opening/middle/ending) → 5–15-scene storyboard with system-selected 30–90s duration → adult script/storyboard review and confirmation → Character Bible/scene references → LTX-2.5 image-to-video per scene on Modal L40S → consistency validation → FFmpeg composition → neutral Vietnamese adult TTS/subtitles, no music → automated output-safety validation → private playback immediately when safe. Each scene gets one initial attempt plus at most two technical retries; no public gallery/download or final human video approval. If marked unsuitable, return to script review and regenerate under the existing request/quota limits.
- Output is MP4, 720p, 16:9, system-selected 30–90 seconds, neutral adult Vietnamese voice, Vietnamese subtitles and music always off. No download/export. Playback uses short-lived authorization. Teacher's one-child sample may be projected to the class only after per-occurrence audience confirmation.
- Deleting a completed run removes linked art/audio/transcripts/context snapshot/story/video through lifecycle; keep minimum metadata-only audit. No separate video-delete action.
- Demo data is synthetic. Real-child data is excluded until a separate authorization/purpose/provider-transfer/retention/access policy is reviewed.
- Modal is the AI host; no Lightning AI. Owner selected L40S for LTX-2.5 after its 32GB+ VRAM requirement was compared with L4 24GB; L4 remains a smaller-model candidate.

## Architecture and repository facts

- Current source declares 86 production tables across 10 owner groups plus 5 test-only fixture tables; 22 Alembic migration files are present. Counts are source declarations, not a live DB inspection.
- Current target after the full source/relationship/canonical-field audit is 38 retained/refactored + 40 new = 78 active. All 86 repository-declared production mappings are accounted for; 48 source mappings remain legacy/read-only (the earlier 35 collaboration/canvas/video/activity/preset tables plus 13 deferred AI Policy provider-copy/resource-receipt tables). Thus 78 active + 48 legacy = 126 projected physical after a non-destructive transition. Four proposed helper/snapshot entities are removed because their facts already have canonical owners. The 40 new tables each have an explicit owner and relationship; no new table exists only to duplicate a ref, result asset, or context snapshot. Existing rows/IDs are preserved; no table is dropped or copied to a duplicate archive. This is a source-declaration count, not live database introspection.
- Parent target is apps/mobile (React Native 0.87 + TypeScript), using apps/ui-mobile as prior behavior reference. Teacher target is apps/teacher-ui (React 19 + Vite 8).
- Backend target: Python 3.13/FastAPI/Pydantic v2/SQLAlchemy 2/Alembic modular monolith; PostgreSQL 17, Redis 8/RQ and MinIO. Python 3.13 is proposed within the current `<3.14` project range; current 3.12 workloads remain until approved compatibility work. Local Compose target adds API/worker, ClamAV scanner, OTel Collector, Prometheus, Grafana and Mailpit. Current Compose is smaller; uploads remain quarantined until clean scan and scanner errors fail closed.
- Firebase Authentication only; no Firebase Storage, Firestore, Realtime Database or Firebase Messaging in this baseline. Browser push uses Web Push; Android push uses a non-Firebase provider adapter candidate pending synthetic POC.
- Modal is backend-only. LTX-2.5 uses Modal L40S candidate; smaller ASR/VLM/LLM/TTS and Teacher Sketch stages may use L4 only after POC. Existing Qwen3-VL evidence is NO_GO; Qwen2.5-VL, Qwen2.5 story LLM, faster-whisper, VieNeu-TTS and an unspecified line-art generator remain candidates pending version/license/quality/latency/cost evidence.
- AI Jobs target discriminator is `STORY_RUN` (exactly one child/profile subject) or `LESSON_SKETCH_DECK` (no child/profile subject); they share dispatch infrastructure but write to distinct aggregates through distinct application completion commands. Sketch jobs have compute/rate caps but no Billing video-quota usage.
- Domain rules remain independent of frameworks, databases, queues, providers and UI. Cross-module behavior uses versioned contracts and opaque references, not direct private-table coupling.
- Local MinIO is not directly reachable from Modal. The SRS now specifies per-attempt Modal Volume scratch transfer, path/hash references, 48 MiB input/256 MiB output proposed synthetic caps, validation, cleanup and a real-data region gate; verify by a synthetic POC before video integration.
- Prior Mermaid sources/renders in evidence/mermaid_draft_20261026 are historical, unapproved drafts and do not match current target counts. Do not reuse them as final.

## Clarifications confirmed through Q146

- Q122/Q129: `VIDEO_READY` remains active until adult completion/regeneration, but closes automatically after 168 hours without meaningful adult action; send an in-app/push reminder at 144 hours. This is not video approval; content remains until manual deletion.
- Q123: the adult may cancel any unfinished run; the active-run lock is released immediately, then linked content is purged through the lifecycle. Accepted video quota is not refunded, and a successful Teacher sample claim remains consumed.
- Q124 initially selected rollover for unused included quota; this interpretation was superseded.
- Q125 then stated that neither grant type carries forward, conflicting with the prior Q114 and Q124 answers. Q126 is the controlling clarification: unused monthly included quota expires at calendar-month end, while purchased top-up quota carries forward until used.
- Existing FIFO order remains current-month included first, then purchased top-ups FIFO.
- Q127: Once the first playable Teacher sample claims an occurrence, its slot never reopens; failed quality regenerations do not permit another run. A technical/safety failure before first playable claim leaves the slot available.
- Q128: Never refund quota for an accepted full-video request, including technical/provider/safety failure or deletion. A retry of a scene is not a new request.
- Q130: On class reassignment, transfer run/media access to the new responsible Teacher, revoke the former Teacher immediately and audit the transfer. A class cannot be left active without an assigned Teacher; offboarding requires a replacement assignment. If the replacement has an active run, reject reassignment safely.
- Q131: Deliver mobile and browser push in addition to the in-app inbox. Use Web Push for browser; Android provider remains unselected until a synthetic POC verifies distributor, app reach, opt-in, invalidation and background delivery. Do not treat UnifiedPush as the default; Firebase Messaging remains excluded by repository governance. Push carries no child/story/media content and inbox is authoritative.
- Q132: Billing is canonical owner of video quota grants and an immutable usage ledger; AI Policy resource tables account only for platform capacity/compute.
- Q133: Apply the 168-hour adult-wait closeout to all states requiring adult action, with 144-hour reminder; preserve content after closeout until user deletion. An active AI job retains its separate six-hour deadline and is not idle-closed.
- Q134: `DRAFT` participates in adult-wait closeout; a run current owner/lock is distinct from immutable creator and transfers through a durable BE1/Story workflow. Emergency organization-admin force-close is explicit, metadata-only/audited and does not expose media or release accepted quota/sample claims.
- Q135: Add `core.upload_sessions` and `core.upload_parts`; store each application chunk up to 4 MiB as a separate object via `PutObject`, assemble and hash-check with bounded resources, then write the final asset via one `PutObject`. Do not use S3 Multipart Upload API. The historical count at Q135 was 42 new/93 active/128 physical; Q138–Q139 temporarily raised it to 44/95/130. The later full data-model audit removes four duplicate helper/snapshot entities, defers 13 AI Policy source mappings from active writes and reconciles to 40 new/78 active/126 projected physical (D-83). SDK behavior remains a synthetic POC gate.
- Q136: At 144 hours, also attempt email to the current Parent/Teacher owner only when a verified email address exists. In-app inbox remains authoritative; push and email are best-effort.
- Q137: Teacher AI Sketch Deck belongs only to Teacher. Parent does not preselect the subject of the child's artwork or use the Teacher Deck; the no-Parent-suggestion part is superseded by the optional Parent guide in Q146.
- Q138: Each Teacher drawing guide uses 3–5 progressive line-sketch steps, with concise placement/layout hints appropriate to the occurrence's target age band.
- Q139: One shared deck covers all approved activities in one lesson occurrence; video sample remains a separate one-child/one-activity run.
- Q140: Teacher uses a white presentation surface with line sketches, short suggestions/explanations, outdoor activity content, and in-occurrence playback of the completed child's story-video. No PPTX export.
- Q141: Parent confirms/corrects the subject only after capturing the artwork; no subject preselection.
- Q142: Teacher may navigate Back/Next, select activity/subject, skip or regenerate one sketch; no freehand/slide-content editing.
- Q143: Sketch rate/compute caps are separate from video quota; values remain configuration/benchmark gates and no video usage ledger entry is written.
- Q144: Full video uses the supplied VLM → structured story → 5–15-scene storyboard → adult script review → Character Bible/references → per-scene LTX-2.5 on Modal L40S → consistency → FFmpeg → Vietnamese narration/subtitles, no music → automated safety → private playback pipeline. Preserve previously confirmed one-child runs, no final video approval, and retry/quota limits.
- Q145: The text-only Parent starter was an interim interpretation and is superseded by Q146; it is not a separate current product feature.
- Q146: Owner clarified that the Parent option is an AI-generated 3–5-step line-sketch guide for a generic adult-selected topic, such as a butterfly. It is optional, skippable, non-blocking, uses no child profile/voice/photo/artwork input, has temporary private output with provenance/cleanup, and uses separate sketch compute/rate caps outside video quota. Teacher's occurrence-wide approved-plan deck remains the main Teacher flow.

## Workflow and review gate

- Documentation-only scope: SRS, data-table register, proposed ADR and feature records.
- The SRS and Data Table Register remain drafts. The owner directly requested the single draw.io/PDF package on 2026-10-27, explicitly superseding the earlier diagram/PDF hold; this output request is not content sign-off of the Markdown sources.
- No product source changes, migrations, database access, product tests/builds, provider/payment/Modal calls, deployment or real child data in this phase.
- Product implementation requires a separate exact-scope plan and approval.

## Independent architecture review (2026-10-27)

- A read-only independent review was recorded at `evidence/INDEPENDENT_ARCHITECTURE_AUDIT_20261027.md` (EV-063-05). Documentation remediation is recorded at `evidence/AUDIT_REMEDIATION_20261027.md` (EV-063-06). It does not authorize implementation.
- The documents now specify transfer, automated output-safety, BE1 schema/data-origin mapping, exclusive principal scope, 51-table declared-column crosswalk and requirement-based ledger classification, canonical owners/projections, assignment-revocation fences, sample audience/deletion rules, video quotas, aggregate AI backpressure, Parent AI line-sketch, Teacher AI Sketch, the supplied video pipeline and owner answers through Q146. Billing owns video quota usage; both sketch capabilities use separate compute/rate accounting; Parent guide output uses temporary Core Asset lifecycle and no child input. These are design proposals, not runtime evidence.
- Production hosting, real-data privacy/legal activation, merchant approval, exact model revisions and cost/latency benchmarks remain unapproved gates.
- The follow-up SRS review remediation updates the requirement wrapper, ID-level traceability, Given/When/Then coverage, risk/open-issue registers, retention/legal gates, SLO/storage/accessibility/browser environment and resumable media upload. Billing is the sole product quota owner; AI Policy compute reservation and Billing quota admission are separate idempotent owner transactions coordinated by an application saga with leases/reconciliation. `created_by` remains provenance after Teacher reassignment. Android push is not selected. Q135 adds durable Core upload session/part tables; S3 multipart is not used. These are architecture/document resolutions, not live implementation evidence; the MinIO chunk/replay/abort behavior still needs a synthetic POC.
- The owner selected Vietnamese for both review documents; the full translation and consistency review are part of the current revision. The SRS v2.2 target catalogue has 46 BR, 82 FR, 33 NFR, 45 Given/When/Then acceptance criteria and 19 edge scenarios. All IDs have explicit priorities and per-ID trace rows; this is documentation evidence, not implementation evidence.

## Related project records

- docs/governance/WORKFLOW.md, APPROVAL_POLICY.md, EVIDENCE_MANAGEMENT.md
- docs/architecture/OVERVIEW.md, PYTHON_BACKEND_ARCHITECTURE.md, DEPENDENCY_RULES.md, CONTRACTS_AND_INTEGRATION.md
- docs/adr/ADR-0001, ADR-0006, ADR-0016 through ADR-0022
- features/FEAT-050-be2-knowledge-video/artifacts/RUNTIME_DECISION_SHEET.md
- features/FEAT-003-multimodal-understanding/evidence/P2_T3_LIVING_SUMMARY.md

## Diagram and PDF package (2026-10-27)

- The owner authorized one native multi-page Draw.io master, a matching complete PDF and a separate system-flows PDF in `owner-selected local document directory`. The later flow request extends the same master and supersedes the earlier two-output count; it does not approve either SRS source or product implementation.
- The current master and complete PDF have 69 pages. They include the context/use-case/screen-flow views, conceptual and owner-partitioned logical ERDs, architecture/package/class, activity/sequence/state, deployment/trust/operations, migration/traceability and 24 flow-section pages. The separate flow-only PDF has 24 pages: one index and 23 detailed user, staff/admin, AI/media, billing/quota, notification, lifecycle, catalog, operations and migration flows.
- All 78 active target tables appear once; 48 legacy mappings are listed separately. Both PDFs are monochrome and rendered for QA. EV-063-15 records hashes, page maps and visual checks. The model remains a logical proposal from repository declarations, not a live database inspection; the SRS and register remain drafts.
