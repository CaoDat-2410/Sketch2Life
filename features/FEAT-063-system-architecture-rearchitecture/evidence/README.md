# FEAT-063 evidence index

## EV-063-93 — SVG engine M1/M2 implementation (2026-11-13)

- Location: `EV-063-93_SVG_ENGINE_M1_M2_20261113/IMPLEMENTATION_REPORT.md`.
- Scope: source implementation record for owner-approved Rev83.4 M1/M2 only.
- Verification boundary: static source edits are not a test, build, migration, catalog approval, renderer performance measurement, or live workflow pass. The report lists unverified gates explicitly.
- As-built status: approved-manifest source edits are present; SRS Rev69 §32.9 records the exact unverified boundary. No API/UI/runtime/Modal/database verification was performed.

Evidence includes source/configuration and documentation reviews for earlier FEAT-063 slices. Rev33 adds local runtime and database evidence: the Lesson Library migration was applied, non-AI HTTP workflows were tested, and MinIO limitations are documented in EV-063-26.

EV-063-13 records the pre-platform table-reduction and relationship-integrity baseline. EV-063-18 supersedes its platform target counts through Q195; EV-063-24 records the Rev31 implementation crosswalk and complete API inventory. EV-063-14 documents the original architecture diagram package and its references/QA; EV-063-15 supersedes its artifact counts with the expanded master and detailed system-flows PDF. Earlier evidence files preserve historical review snapshots and must not be treated as the current baseline.

| ID | Type | Purpose | Artifact |
|---|---|---|---|
| EV-063-90 | Rev81 consolidated plan detail review | Record the screen/API/data/AI/Docker/work-package expansion, canonical Rev60 boundary, plan hash and planning-only validation limits | `EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/REV81_PLAN_DETAIL_REVIEW.md` |
| EV-063-71 | Single-root Firebase Auth and Docker configuration | Record the one-root-.env setup, Parent Auth client/backend verifier wiring, public/Admin credential boundary, focused checks and uncompleted credential/live-auth gates | `EV-063-71_SINGLE_ROOT_ENV_FIREBASE_AUTH_20261110.md` |
| EV-063-72 | Backend Firebase Auth registration | Record the local-only registration contract, backend/mobile implementation, 18 backend tests, 5 Parent auth tests, type/lint checks, live Firebase Admin account lookup and invalid Web API key blocker | `EV-063-72_BACKEND_FIREBASE_ACCOUNT_REGISTRATION_20261110.md` |
| EV-063-73 | Role-based authentication and Firebase account recovery | Record Rev63 code/document review for Parent role assignment, Teacher/Admin route gates, Platform Admin account API/UI, Firebase password recovery/change, additive migration/bootstrap and unverified runtime boundaries | `EV-063-73_ROLE_BASED_AUTH_AND_RECOVERY_20261110.md` |
| EV-063-74 | Parent/Teacher Modal UI E2E | Record the real Firebase/UI/backend/live-Modal results, per-operation status and timing, Qwen truncated-JSON failure, blocked Parent story, Teacher structured-form scope, screenshots, safe worker logs and cleanup | `EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md` plus its `logs/` and `screenshots/` |
| EV-063-75 | Teacher Sketch Deck presentation UI | Record the live Teacher UI-to-Modal draft/deck/visual run, 16:9 slide rendering, actual FLUX image display, slide/step controls, long-activity scrolling, worker-observability gap, Parent Android blocker and cleanup | `EV-063-75_TEACHER_PRESENTATION_UI_20261110.md` plus its `screenshots/` |
| EV-063-58 | Rev53 SRS v2.6 checklist remediation | Source/hash and visual-review provenance; detailed disposition of M-01–16, D-01–20, Q-01–13 and R-01–05; fixed/clarified/open gates and publication evidence | `EV-063-58_SRS_V26_CHECKLIST_REMEDIATION_20261107.md` |
| EV-063-56 | Rev51 source review and publication | Current `origin/dev` API/Modal source crosswalk, publication results and scope limits | `EV-063-56_SRS_PUBLICATION_REV51_20261106.md` |
| EV-063-55 | Rev45 SRS/code alignment | SRS model-role reconciliation and earlier local source crosswalk, reindexed to avoid the existing EV-063-34 collision | `EV-063-55_SRS_SYSTEM_CODE_ALIGNMENT_REV45_20261106.md` |
| EV-063-37 | Current FE Swagger | SRS v2.2 implementation scope and live/snapshot parity | EV-063-37_SWAGGER_SRS_V22_SCOPE_20261101.md |
| EV-063-38 | Swagger cleanup | Current-only file set, focused checks, and commit consolidation status | EV-063-38_SWAGGER_HISTORY_CLEANUP_20261101.md |
| EV-063-34 | Swagger review and local commit | Record contract/snapshot review, unsafe request-ID reflection fix, focused checks, security result and publication boundary | `EV-063-34_SWAGGER_REVIEW_AND_COMMIT_20261030.md` |
| EV-063-33 | Swagger overview presentation | Replace the dense intro paragraph with scannable coverage, authorization and unmounted-route notes; verify the served snapshot | `EV-063-33_SWAGGER_INFO_PRESENTATION_20261030.md` |
| EV-063-32 | Local Swagger QA kit and upload error parity | Record the contract-shaped 413 fix, synthetic demo request examples/PNG, focused checks, local Swagger restart, and Firebase-protected-route test limit | `EV-063-32_LOCAL_SWAGGER_QA_KIT_20261030.md` |
| EV-063-31 | Swagger navigation and role grouping | Replace broad surface tags with explicit Lesson Library role tags and BE1/Demo domain groups; include tag descriptions and preserve Rev37 parity | `EV-063-31_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md` |
| EV-063-30 | Swagger/OpenAPI contract alignment | Rev37 parity for 124 mounted and 11 unmounted operations, full request/authentication/response checks, reproducible snapshot, and upload 413 discrepancy evidence | `EV-063-30_SWAGGER_OPENAPI_FEAT063_REV37_20261030.md` |
| EV-063-01 | Source review | Current table inventory, architecture conventions, app/backend/runtime baseline | `SOURCE_REGISTER.md` and SRS §3, §11–§14 |
| EV-063-02 | Technical research | Official LTX/Modal capability and hardware requirements | SRS §9 and §19 |
| EV-063-03 | Regulatory source review | Current law status and child data / AI design boundary | SRS §10 and §19 |
| EV-063-04 | PDF visual QA | Rendered-page count, page map, clipping review, source/output hashes | `PDF_QA.md` (to be added after rendering) |
| EV-063-05 | Independent architecture review | Product fit, repository/schema consistency, security, workflow, technology, data model and prioritized implementation gates | `INDEPENDENT_ARCHITECTURE_AUDIT_20261027.md` |
| EV-063-06 | Audit remediation map | Cross-reference of AUD-01–AUD-14 to the revised SRS/register/ADR, owner answers and remaining implementation gates | `AUDIT_REMEDIATION_20261027.md` |
| EV-063-07 | Historical Markdown consistency review | Initial consistency baseline through Q126 / plan revision 9; superseded by EV-063-08 for the current decision set | `MARKDOWN_REMEDIATION_QA_20261027.md` |
| EV-063-08 | Follow-up remediation QA | Q127–Q133 integration and cross-document audit remediation; count/owner/state/queue/cost/security consistency | `FOLLOWUP_REMEDIATION_QA_20261027.md` |
| EV-063-09 | SRS v1.5 review remediation | Resolution of the follow-up SRS review: ownership/cost admission, state/retention/push, system context/requirements traceability and aligned M/S trace priorities, upload resume, risks and remaining gates across SRS/register/ADR/plan | `SRS_V16_REVIEW_REMEDIATION_20261027.md` |
| EV-063-10 | Q134-Q136 integration and static cross-document review | Reconcile current owner/offboarding, upload tables/chunk contract, verified-email reminder, table counts, trace matrices and review status | `Q134_Q136_CROSS_DOCUMENT_REVIEW_20261027.md` |
| EV-063-11 | Historical Q137-Q144 AI Sketch/video-pipeline cross-document review; table count superseded by EV-063-12 | Reconcile Teacher-only Sketch Deck, single-child story job, complete supplied Modal/LTX video pipeline, and prior document-only QA | `Q137_Q144_SKETCH_VIDEO_PIPELINE_CROSS_DOCUMENT_REVIEW_20261027.md` |
| EV-063-12 | Full data-model reduction and relation audit | Reconcile all 86 source mappings, 40 remaining target tables, owner/canonical-field relations, removed duplicate entities, counts and static cross-document checks | `DATA_MODEL_REDUCTION_AND_RELATION_AUDIT_20261027.md` |
| EV-063-13 | Data model simplification and integrity audit | Reconcile 86 source mappings to 78 active / 48 legacy / 126 projected physical; verify all 40 new targets have relationship entries; document reduced AI Policy writes, Story revision constraints, AI Job targets and composed reads | `DATA_MODEL_SIMPLIFICATION_AND_INTEGRITY_AUDIT_20261027.md` |
| EV-063-14 | Diagram package research and visual QA | Record authoritative SRS/UML/C4/draw.io sources, supplied-document reference review, diagram inventory, output paths/hashes, page count and render/visual checks | `DIAGRAM_PACKAGE_RESEARCH_AND_PDF_QA_20261027.md` |
| EV-063-15 | Expanded Draw.io package and complete system-flow PDF QA | Record 69-page master/full PDF, 24-page detailed flow PDF, full flow inventory, hashes, page-title verification, rendered-page/contact-sheet inspection and draft limitations | `SYSTEM_FLOWS_PDF_AND_DRAWIO_UPDATE_20261027.md` |

| EV-063-16 | Historical Parent text-starter SRS reconciliation; superseded by EV-063-17 | Records the interim Q145 text-only interpretation and Q146 open proposal as reviewed at the time; current baseline is in EV-063-17 | PARENT_SKETCH_STARTER_SRS_RECONCILIATION_20261028.md |
| EV-063-17 | Parent AI line-sketch SRS reconciliation | Q146 owner clarification incorporated in SRS/Data Table Register v2.2; Q145 text-only interpretation superseded; FEAT-062 points to FEAT-063 | PARENT_AI_LINE_SKETCH_SRS_RECONCILIATION_20261028.md |
| EV-063-18 | Platform lesson library, sharing and preserved-flow reconciliation | Plan Rev25 and Q147–Q195 incorporated in SRS/Data Table Register v2.3-draft and ADR-0022; old v2.2 files preserved; documentation-only static review | PLATFORM_LESSON_LIBRARY_ARCHITECTURE_RECONCILIATION_20261028.md |
| EV-063-19 | Modal-hosted AI model and pipeline reassessment | Official-source research against current v2.3, proposed candidate stack/flows and POC matrix; Plan Rev26 awaits approval; no model/runtime benchmark executed | MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md |
| EV-063-20 | Backend basic lesson CRUD repository review | Read-only inventory of BE1 auth/tenant boundary, generic learning_content candidate, Lesson v2.3 table targets and first-slice plan; no database/runtime/test work | BACKEND_BASIC_LESSON_CRUD_REPOSITORY_REVIEW_20261028.md |
| EV-063-21 | Backend Lesson library scope and upload review | Records owner choices to include Manager review/Public, Parent read/share and lesson upload; identifies occurrence-vs-library source-document ownership gap; no implementation/runtime work | BACKEND_LESSON_LIBRARY_SCOPE_AND_UPLOAD_REVIEW_20261028.md |
| EV-063-22 | API contract, naming and entity review | Reviews FEAT-047/SRS/API conventions and defines Lesson entity/table/DTO mapping, endpoint purpose/request/response/auth/error contracts; draft only | API_CONTRACT_NAMING_AND_ENTITY_REVIEW_20261028.md |
| EV-063-23 | Local Docker, MinIO and S3-compatible storage example | Records approved Rev30 implementation scope, Compose/storage wiring, local-only sample API, official MinIO maintenance source review and unrun runtime/test limits | DOCKER_MINIO_STORAGE_EXAMPLE_20261028.md |
| EV-063-24 | Backend implementation and API inventory | Record the approved Rev31 implementation scope, static route inventory, additive Lesson support tables and unrun runtime/database gates | REV31_LESSON_LIBRARY_IMPLEMENTATION_AND_API_INVENTORY_20261028.md |
| EV-063-25 | API purpose catalog | Record purpose and runtime exposure for all 135 declared routes; static source/composition limits | REV32_COMPLETE_API_PURPOSE_CATALOG_20261028.md |
| EV-063-26 | Local non-AI API workflow and migration verification | Record the additive local migration, Lesson Library HTTP results, legacy BE1 result, isolated test database cleanup, and MinIO pull limitation | REV33_NON_AI_API_TESTS_AND_LOCAL_MIGRATION_20261029.md |
| EV-063-27 | Legacy non-AI API regression | Record 77 active-route smoke responses, 109/110 non-DB tests, 3/4 BE1 tests, AI exclusions, candidate-route boundary, and the two failures | REV34_LEGACY_NON_AI_API_REGRESSION_20261029.md |
| EV-063-28 | UI screen mockups and motion notes | Record 14 generated screen drafts, per-screen prompt/motion files, API/SRS mapping, image provenance/hashes, and visual review limits | EV-063-28_UI_MOCKUPS_AND_MOTION_NOTES_REV35_20261030.md |
| EV-063-29 | UI component patterns and interaction states | Record nine reusable component/state boards, SRS/API mapping, motion notes, hashes, and current-versus-target API limits | EV-063-29_UI_COMPONENT_PATTERNS_REV36_20261030.md |
| EV-063-30 | Modal AI hosting wave | Record pinned Modal dev deployments, 88.59 GiB of direct-to-Volume checkpoint downloads, synthetic TTS/ASR and FLUX results, later Qwen-VL call success, the separate unreconciled API call, stopped drawing app, and remaining readiness limits | MODAL_AI_HOSTING_WAVE_20261103.md |
| EV-063-31 | Local API runtime availability smoke | Record live health/OpenAPI checks, missing StoryRun route and disabled provider configuration in the running Docker API, and why no request reached the newly deployed Modal workers | API_RUNTIME_AVAILABILITY_SMOKE_20261103.md |
| EV-063-39 | Backend API to Modal drawing VLM vertical slice | Record adapter, isolated migrations, HTTP checks, Modal call success after API timeout, unreconciled StoryRun, and stopped drawing app | MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md |

| EV-063-40 | Parent image-to-script API/AI retest | `PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md` | Parent run/upload routes passed through upload READY; Modal L4 drawing result and detached story result remained unknown; video calls zero; all deployed Modal dev apps stopped. |
| EV-063-41 | Parent generated-image, story, and activity-selection retest | `PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md` | New synthetic image; successful Modal drawing and five-scene story calls; legacy selectable activity; timing, factual issues, and verified shutdown. |

## EV-063-42 - AI flow SRS alignment and Teacher deck POC

- Full results/API matrix: [`AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md`](AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md).
- Synthetic request/response traces, guards, Teacher Deck JSON/HTML preview, and FLUX provenance: `assets/ai_flow_srs_alignment_20261104/`.
- Parent synthetic image and provenance: `assets/parent_generated_image_activity_retest_20261103/`.
- Status: partial; live story generation failed on the deployed manifest schema before model inference, and FLUX produced no image because L4 capacity was unavailable. No retries were sent.
## EV-063-43 - Full non-video AI workload retest

- Approved plan and acceptance criteria: [`plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md`](../plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md).
- Direct owner authorization is recorded in `approvals/TASK_APPROVAL.md`.
- Outputs and timing are stored under `assets/ai_nonvideo_full_retest_20261104/`; video generation was excluded.

## EV-063-44 - Full non-video AI workload retest results

- Execution report: [`AI_NONVIDEO_WORKLOAD_FULL_RETEST_RESULTS_20261104.md`](AI_NONVIDEO_WORKLOAD_FULL_RETEST_RESULTS_20261104.md).
- Per-workload dispatch, output, API contract, synthetic audio, SAM2 checkpoint, and timeout evidence: `assets/ai_nonvideo_full_retest_20261104/`.
- Status: partial; TTS and ASR succeeded. Fresh GPU-backed inference attempts ended at bounded L4 queue timeouts. All Modal apps stopped with zero tasks; task DB/cache removed. No video inference or product enablement.

## EV-063-45 - 30-minute non-video AI queue retest

- Approved plan and acceptance criteria: [AI_NONVIDEO_30MIN_QUEUE_RETEST_20261104.md](../plan/AI_NONVIDEO_30MIN_QUEUE_RETEST_20261104.md).
- Execution report: [AI_NONVIDEO_30MIN_QUEUE_RETEST_RESULTS_20261104.md](AI_NONVIDEO_30MIN_QUEUE_RETEST_RESULTS_20261104.md).
- Per-workload dispatch/results, output hashes, shutdown verification, and the generated Parent Sketch Guide: assets/ai_nonvideo_30min_queue_retest_20261104/.
- Status: partial; Parent Sketch Guide and Teacher Deck succeeded, while drawing, story, lesson visual, and SAM2 remained queued for GPU_L4 through the 30-minute bound. No video inference. All Modal dev apps stopped with zero tasks.

## EV-063-46 - Modal L4 Qwen story readiness diagnostic

- Approved plan: [`MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md`](../plan/MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md); execution closeout and the one-call scope deviation are in `approvals/TASK_APPROVAL.md`.
- Execution report: [`MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md`](MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md).
- Health/model and story-call queue records: `assets/modal_l4_qwen_story_readiness_20261104/`.
- Result: Qwen2.5 checkpoint/model readiness passed on a temporary L4 container; story calls never received a GPU container because Modal was acquiring GPU_L4 capacity. No story output or video inference. Task-owned apps stopped; no active containers.


## EV-063-47 - Modal serverless Parent story latency experiment

- Approved plan: [`MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`](../plan/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md), SHA-256 `E18267CD3B9D5AC5F75F3A5F80DAD6958AEFF9EDCFF3A36C2C00BF579F2C8711`.
- Execution report: [`MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`](MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md).
- Call, dispatch intent, worker log/timings, and post-stop state: `assets/modal_serverless_story_latency_20261105/`.
- Result: ordered L4/L40S/A10 fallback allocated an A10; the model generated 722 tokens and then failed strict story parsing. The call was not retried. The Modal app is stopped with zero active tasks; video calls were zero.

## EV-063-48 - Modal Parent story content/timeline boundary

- Approved plan: [`MODAL_STORY_CONTENT_BOUNDARY_20261105.md`](../plan/MODAL_STORY_CONTENT_BOUNDARY_20261105.md), SHA-256 `DEEC2263B3148A855AE090D1A513B1D57174CD9800FAC9BA8BC0E3A3F6F23917`.
- Execution report: [`MODAL_STORY_CONTENT_BOUNDARY_20261105.md`](MODAL_STORY_CONTENT_BOUNDARY_20261105.md).
- Dispatch intent, result metadata/output hash, worker timings/logs, local validation, and shutdown state: `assets/modal_story_content_boundary_20261105/`.
- Result: one synthetic call produced five scenes/30 seconds accepted by the unchanged worker parser, backend story model and butterfly lifecycle validator. 46 focused tests passed. No video call; app stopped with zero tasks. Raw prompt/story text was not retained.

## EV-063-49 - Parent StoryRun-lite API and AI retest

- Approved scope baseline: Plan revision 43 in `plan/PARENT_STORY_API_RETEST_20261105.md`; final closeout SHA-256 is recorded in `approvals/TASK_APPROVAL.md`.
- Execution report: [`PARENT_STORY_API_RETEST_20261105.md`](PARENT_STORY_API_RETEST_20261105.md).
- Safe per-request trace, full result, VLM/story outcomes, and runner evaluation: `assets/parent_story_api_retest_20261105/attempt_02/`; initial no-dispatch invalid-profile attempt is preserved in `attempt_01_invalid_synthetic_run_request/`.
- Result: 13/13 mounted operations covered by the no-AI matrix; one real VLM request ended unknown after 303.762 s, and one fixture-backed story request returned 502 after `EDUCATIONAL_FACT_INVALID`. No video. Both task Modal apps stopped with zero tasks; disposable PostgreSQL stopped; shared services and Volumes preserved.

## EV-063-50 - Rev44 AI API coverage and Qwen3.5 Modal validation

- Approved plan and exact owner role clarification: `../plan/PLAN_REV44_AI_API_COVERAGE_QWEN35_MODAL_20261105.md`; approval hash/status in `../approvals/TASK_APPROVAL.md`.
- Complete workload/API crosswalk: [`AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`](../artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md).
- Execution results, model pin, timing, errors, remaining API gaps and shutdown evidence: [`AI_API_QWEN35_MODAL_VALIDATION_20261105.md`](AI_API_QWEN35_MODAL_VALIDATION_20261105.md).
- Synthetic request/result metadata and output hashes: `assets/ai_api_qwen35_modal_validation_20261105/`; no real child media or credentials.
- Outcome: Teacher Deck passed once; drawing failed output parsing; story/lesson failed before generation and their decoder fix is verified only by tests/runtime imports; TTS succeeded and ASR had a one-word mismatch; FLUX.3 blocked by HTTP 401/no Secret; SAM2 remained GPU-capacity UNKNOWN; video deferred. All product workloads remain disabled.
- Verification: 59 Modal worker/parser tests passed; 79 backend API/contract tests passed, 6 skipped; repository security validator passed across 6,388 publishable files. Task-owned Modal apps stopped with zero tasks; shared Volumes retained.

## EV-063-51 - Rev45 non-video AI end-to-end execution

- Approved plan: [`PLAN_REV45_NONVIDEO_AI_END_TO_END_20261105.md`](../plan/PLAN_REV45_NONVIDEO_AI_END_TO_END_20261105.md); execution outcome and blockers: [`AI_NONVIDEO_AI_END_TO_END_20261105.md`](AI_NONVIDEO_AI_END_TO_END_20261105.md).
- Per-call intents/results, model outputs/hashes, and synthetic audio: `assets/ai_nonvideo_ai_end_to_end_20261105/vietnamese_alphabet_retest_12/` and `assets/ai_nonvideo_ai_end_to_end_20261105/speech_retest_13/`.
- Result: Qwen drawing, Parent story/storyboard, Teacher Deck, lesson suggestion, TTS, and exact-text ASR passed. FLUX.3 is blocked by the absent Modal HF Secret; SAM2 was not re-dispatched, and its last attempt waited 1,800 seconds without GPU scheduling. No video call. All production workload flags remain disabled.
- Verification: 76 Modal tests passed; 61 backend API/OpenAPI tests passed, 6 skipped; targeted Ruff, Python compilation, repository security validation (6,556 files), and `git diff --check` passed. Both task-used Modal apps stopped with zero tasks; shared Volumes retained.


## EV-063-52 ? Qwen3.5-only active profile and FLUX Rev46A

- Approved scope and execution closure: `../plan/PLAN_REV46_QWEN35_ONLY_FLUX_SECRET_RETEST_20261105.md` and `../plan/PLAN_REV46A_FLUX_COMPONENT_FILES_AND_FAILED_FLOW_RETEST_20261105.md`; hashes and owner authorization are recorded in repository and FEAT-063 task approvals.
- Report: [`AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md`](AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md).
- Dispatch/results and both generated images: `assets/flux_component_retest_rev46a_20261105/`.
- Result: active Qwen config is Qwen3.5 only; FLUX staging, Parent Sketch Guide, and lesson visual passed once each. Both images are private synthetic DRAFTs; no product API, SAM2, or video call.
- Verification: 27 focused tests passed; Ruff/compileall passed; app stopped with zero tasks and Volumes retained. Repository security validation passed across 6,581 publishable files; `git diff --check` passed.

## SRS v2.4 evidence ID reconciliation

The imported as-built SRS evidence keeps its original filename (`EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md`) because the approved Rev43/44 plans cite it. In this combined index it is assigned EV-063-53 to avoid colliding with the pre-existing Swagger EV-063-33 record. The source report itself is unchanged.

| EV-063-53 | As-built SRS alignment | Read-only reconciliation of canonical SRS with backend/router composition, mounted local OpenAPI, local PostgreSQL table inventory, AI/database access boundary and owner-supplied Modal dashboard observation; records target-versus-current implementation boundary | `EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md` |


## EV-063-54 ? dev duplicate repair and SRS integration

Records the six patch-equivalent local `dev` commits, preservation backup, full Modal AI integration, SRS v2.4 conflict disposition, security checks, and fast-forward publication to `origin/dev`. See [`EV-063-54_DEV_HISTORY_AND_SRS_MERGE_20261106.md`](EV-063-54_DEV_HISTORY_AND_SRS_MERGE_20261106.md).

## Rev51 bounded Modal AI and legacy API retest - 2026-11-06

- Main report and complete API operation inventory: `modal_ai_and_legacy_api_retest_20261106/API_TONG_HOP_VA_SAN_PHAM_AI_MODAL_20261106.md`.
- Machine-readable API/workload/test matrices, read-only API probe, Modal app inventory, and SHA-256 provenance manifest are in the same folder.
- 16 previously captured synthetic products and safe historical failures are grouped under its `products/` directory; originals remain in their source evidence folders.
- Backend API/contract suite: 1,454 passed / 6 failed; Modal worker contracts: 79 passed / 2 skipped. No inference was dispatched in this retest.


## Rev52 non-video Modal AI reliability and observability - 2026-11-06

- Plan: `../plan/PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md` (approved SHA-256 `9703A6CFE3AAF6108A1443B4E7F93805481475A0C60C64C50414106441158938`).
- Results folder: `nonvideo_modal_ai_reliability_20261106/`.
- Scope: structured worker/caller telemetry and synthetic verification for registered non-video Modal AI workloads; no video.
- Status: complete with findings; see `nonvideo_modal_ai_reliability_20261106/API_AND_AI_MODAL_RESULTS_20261106.md` and the Rev52 closeout below.

## EV-063-57 - SRS v2.5 and Modal AI integration to dev

- Plan Rev54 and approval hash: `../plan/PLAN_REV54_MERGE_SRS_V25_AND_MODAL_AI_TO_DEV_20261106.md`, SHA-256 `C6882123DF3F1671AF7014784651E9F6A37AD799BA3763223BFC10C9E2A9F937`.
- Integration report: [`EV-063-57_SRS_V25_AND_MODAL_AI_DEV_INTEGRATION_20261106.md`](EV-063-57_SRS_V25_AND_MODAL_AI_DEV_INTEGRATION_20261106.md).
- Source commits: SRS `fae180dcf3ea2771b41546aa6925b94636821df1`; Modal AI `c6818490d0d889ab17dc9f8de3830987eb2a230d`.
- Status: complete; `origin/dev` was verified at integration commit `47e5308a5c547df8dab5f3c560f949ee925f441e`; final closeout is also recorded on `dev`.

## EV-063-57 — Rev52 SRS contradiction reconciliation

Maps report findings M01–M09, the additional current-count mismatch M10, D01–D12 and Q01–Q08 to corrected SRS/Register sections or remaining open items; records the three owner clarifications and report provenance.

See [EV-063-57_SRS_V25_CONTRADICTION_REVIEW_20261106.md](EV-063-57_SRS_V25_CONTRADICTION_REVIEW_20261106.md).

## EV-063-58 — Rev53 v2.6 checklist remediation

Records the owner-supplied checklist provenance and visual review, exact logical SRS/Register changes, every M/D/Q/R disposition, open policy/schema gates, scoped checks and publication status. The checklist is analysis evidence only; the v2.7-draft SRS remains unsigned.

See [EV-063-58_SRS_V26_CHECKLIST_REMEDIATION_20261107.md](EV-063-58_SRS_V26_CHECKLIST_REMEDIATION_20261107.md).

## EV-063-59 — Rev54 v2.6 checklist audit and diagram readiness

Rechecks all M-01–M-16, D-01–D-20, Q-01–Q-13 and R-01–R-05 against the same-commit v2.6/Rev55 source set and current v2.7-draft SRS/Register. Records status corrections, owner clarifications by scope, future verification scenarios and the limits of the review.

- Full code-by-code crosswalk: [DIAGRAM_READINESS_CROSSWALK_REV54_20261107.md](../artifacts/DIAGRAM_READINESS_CROSSWALK_REV54_20261107.md).
- Draft TO-BE diagram inputs: [DIAGRAM_INPUT_CATALOG_V27_REV54_20261107.md](../artifacts/DIAGRAM_INPUT_CATALOG_V27_REV54_20261107.md).
- Evidence: [EV-063-59_DIAGRAM_CHECKLIST_REVIEW_20261107.md](EV-063-59_DIAGRAM_CHECKLIST_REVIEW_20261107.md).
- Status: documentary cross-check complete; final diagrams and as-built claims remain gated; SRS v2.7-draft remains unsigned.

## EV-063-60 — two-agent diagram readiness assessment

Records two independent reviews of the canonical FEAT-063 v2.7-draft SRS and Data Table Register for all requested diagram types. Includes per-diagram readiness, verified contradictions, open gates, and the distinction between target requirements and dated as-built evidence.

See [EV-063-60_TWO_AGENT_DIAGRAM_READINESS_ASSESSMENT_20261107.md](EV-063-60_TWO_AGENT_DIAGRAM_READINESS_ASSESSMENT_20261107.md). The SRS/Register remain unsigned; no diagrams were created.

- [EV-063-61 — Ten-group diagram-readiness alignment](EV-063-61_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md) — documentation-only synchronization; owner and technical gates remain open.

| EV-063-62 | Rev57 substantive diagram-input remediation | Source-only baseline review, G01–G10 detailed requirements, 17-question decision map, 13 diagram readiness, physical/state/API/screen/class/package contracts and static import-cycle evidence | EV-063-62_REV57_SUBSTANTIVE_DIAGRAM_INPUT_REMEDIATION_20261109.md |

## EV-063-87 — Parent non-video API/UI and Rev78 activity suggestions

Records synthetic Parent signup/profile/context, drawing analysis, activity suggestion and story-draft path; catalog/fallback contract, worker logs summarized as safe JSON, quality-gate outcomes, runtime timings and limitations. Selected screenshots show subject confirmation, activity suggestion/review and story result. No video was called. The final Rev78A inference was cancelled before output; the gate verdict is unknown. The migration was not applied to PostgreSQL.

## EV-063-88 — Parent Docker, seed and Modal health verification

Records the isolated Compose migration/startup, persisted host ports, seed idempotency, Firebase Auth Emulator sign-in, Parent profile/consent/quota/catalog/active-run API reads, Expo Firebase App ID/API URL resolution, 28 targeted activity gate/parser tests, Modal health-only startup and limitations. Core activity sentences remain punctuated; only materials/observation fragments may omit punctuation. No model inference or video was called.

See [API_PARENT_DOCKER_MODAL_REPORT.md](EV-063-88_PARENT_DOCKER_SEED_MODAL_HEALTH_20261112/API_PARENT_DOCKER_MODAL_REPORT.md).

## EV-063-90 — Rev81 consolidated Parent/Teacher implementation

Records the owner-approved implementation scope, changed real API/UI/Modal/Docker paths, no-fixture acceptance checks, focused test/build results, non-video Modal calls, failures, timings and cleanup. Synthetic local entities/media are clearly distinguished from fixture responses; no video inference or production data is included.

See `EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/IMPLEMENTATION_STATUS.md`.

### EV-063-90 — Rev81 Android/Modal E2E results

Parent Android and live non-video Modal results, exact worker failure stages, Teacher presentation blockers, API statuses and Docker/Modal health findings are recorded in [`REPORT_PARENT_TEACHER_ANDROID_MODAL_E2E_20261112.md`](EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/parent_teacher_e2e_20261112/REPORT_PARENT_TEACHER_ANDROID_MODAL_E2E_20261112.md). Synthetic drawing input only; no fixture output, video inference, real-child data, or screenshots of non-AI UI. AI output and screenshot folders remain empty because no generated artifact passed its contract/quality gate.


### EV-063-90 — Rev82 post-fix Docker/Modal verification

Records the successful Teacher Qwen lesson-plan and Sketch Deck APIs, the single post-fix FLUX lesson-visual API failure with exact transition measurements and phase timings, local Docker service health, Modal scale-to-zero status, no-retry boundaries, and why the fresh Parent AI run was stopped. No video or fixture output is represented as a pass.

See [REPORT_REV82_POSTFIX_DOCKER_MODAL_20261112.md](EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/parent_teacher_e2e_20261112/REPORT_REV82_POSTFIX_DOCKER_MODAL_20261112.md).

### EV-063-90 — Rev82 §22 bounded Parent/Teacher AI continuation

Records the passing Teacher FLUX visual output, real Parent signup/profile/drawing/subject-confirmation calls, the activity worker's valid fallback JSON and the backend safety-gate rejection. Includes safe worker phase diagnostics, synthetic AI output, revised activity prompt and 30 focused offline tests. No retry/story/video inference is represented as passing.

See [REPORT_REV82_LIMITED_PARENT_TEACHER_20261112.md](EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/parent_teacher_e2e_20261112/REPORT_REV82_LIMITED_PARENT_TEACHER_20261112.md).

## EV-063-94 — Rev84 Teacher SVG Modal UI verification (2026-11-13)

Records one real authenticated Teacher UI request through the backend to pinned Qwen3.5 on Modal, the validated 18-path SVG draft, rendered screenshot, timings and worker diagnostics. No fixture/dataset, FLUX, video, real-child data, persistence or publication was used. The local capability flag was disabled and the isolated Docker/UI/browser processes were stopped; the Modal app remains deployed with zero live containers. See [REPORT.md](EV-063-94_TEACHER_SVG_MODAL_UI_20261113/REPORT.md).
## EV-063-95 — Teacher SVG dataset-conditioned quality attempt (2026-11-13)

Records one real authenticated Teacher UI/API request against the dataset-conditioned Qwen3.5 Modal worker. The request failed before model inference because an unrelated cat exemplar in the whole-pack validation had stroke width 20, exceeding the unchanged parser maximum of 12. The preserved JSON is the HTTP 502 error body only; no SVG output, rendered screenshot, or quality comparison exists. No retry was made; the dataset-conditioned flow is not verified as working.

See [REPORT.md](EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/REPORT.md).


## EV-063-96 — Rev86 Teacher SVG dataset-pack correction and comparison (2026-11-13)

Records the corrected active pack and preserved raw source, exact-parser preflight, one real authenticated Teacher UI → API → Modal request, worker timing, actual sanitized JSON/SVG/browser render, and a five-criterion comparison with Rev84. Runtime integration passed, but deer recognition failed and overall visual quality is not accepted. Includes worker terminal-event and local API port-conflict limitations; no retry, scale-to-zero claim, or broad quality claim is made.

See [REPORT.md](EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/REPORT.md).

## EV-063-101 — Arcadia SVG source + stroke-authoring skill (2026-11-13)

Records the curated CC0 Arcadia `Gallus gallus` SVG reference, MIT whiteboard-animation skill provenance, local implementation, static/UI checks, and one Modal deploy attempt that failed before app update. No runtime health, inference, generated SVG, or screenshot was obtained; the local path defect was corrected but no retry was authorized. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md).
## EV-063-101 — Rev87.5 bounded Modal retry (2026-11-13)

Records the owner-approved single reattempt, local API preflight and the Modal CLI Windows encoding failure. Deployment status is unknown; no Modal health, GPU inference, Parent UI AI request, generated SVG, or screenshot exists. The temporary API was stopped; shared services were left untouched. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-2.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-2.json).

## EV-063-101 — Rev87.6 Android Parent UI attempt (2026-11-13)

The Android app authenticated and loaded the authorized synthetic profile, but could not resume an existing incomplete open run. No new run or Modal request was made. Actual screenshots and the exact stop boundary are recorded in [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md), [runtime-attempt-3.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-3.json), and the `screenshots/` directory.


## EV-063-101 — Rev87.9 Parent Android E2E with Modal (2026-11-13)

Records the real Android Parent flow from signup through drawing analysis and activity suggestions, with two successful Qwen3.5 Modal inferences and per-stage screenshots. The optional guide failed on missing SVG catalog DB tables; story generation stopped at HTTP 422 because the UI cannot select and submit the required primary activity. No activity was injected, and no story/video was generated. Includes actual AI response JSON, the observed 422 record, call IDs, timings and cleanup status. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-4.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-4.json).

## EV-063-101 — Rev87.10-A Parent SVG attempt (2026-11-13)

Records the actual Parent Android optional-guide path and the newly reachable AI-draft fallback after a catalog error. The catalog GET and one SVG-draft POST returned `INVALID_IDENTITY_TOKEN`; no Modal dispatch, SVG output or render occurred. The task API, Metro and emulator were stopped, shared services preserved, and no `.env` or migration changes were made. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md), [runtime-attempt-5.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-5.json), and the `screenshots/` directory.


## EV-063-101 — Rev87.10-B/C Parent Auth and SVG API attempt (2026-11-13)

Records the stale API's missing Firebase Auth Emulator host, the corrected current-worktree Docker API configuration, fresh emulator sign-in and `/api/auth/v1/me` success, then one real Parent SVG API attempt. The catalog returned `DATABASE_UNAVAILABLE`; Qwen3.5 Modal failed path parsing with `SVG_TOPIC_GUIDE_PATH_INVALID`, so no valid SVG or screenshot exists. Android UI was unavailable (no SDK/adb/emulator); no retry or migration was run. The corrected task API remains on port 58000; the old port-18000 API was not changed. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-6.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-6.json).


## EV-063-101 — Rev87.10-D SVG catalog database repair (2026-11-13)

Records the read-only compatibility preflight, targeted transactional migration to `20261113_svg_catalog_review`, unchanged Core asset count, verified catalog/review tables and constraints, and authenticated Parent catalog API HTTP 200 with zero items. No seed, fixture, unrelated migration head or AI call was used. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-7.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-7.json).
## EV-063-101 — Rev87.10-E real Parent SVG inference attempt (2026-11-13)

Records a real authenticated Parent request after the SVG catalog database migration. Auth Emulator sign-in and catalog lookup passed; the empty catalog triggered one Qwen3.5 Modal inference. The worker failed at output parsing with `SVG_TOPIC_GUIDE_PATH_INVALID`, HTTP 502, after 223 seconds; no validated SVG or rendering exists and no retry occurred. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-8.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-8.json).

## EV-063-101 — Rev87.10-F/G/H SVG decoder fix and final Parent API attempt (2026-11-13)

Records the LMFE schema compatibility correction, 4/4 focused tests, worker compile, one Modal deployment, and one final real Parent API-to-Modal inference. The first call failed from LMFE schema incompatibility ([runtime-attempt-9.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-9.json)); after the fix, decoder setup passed, but Qwen3.5 generation failed at JSON parsing (`SVG_TOPIC_GUIDE_JSON_INVALID`) after 364.985 seconds of inference. API logged 502; no validated SVG/render exists. It also records the client `TypeError` at 307.345 seconds and the unresolved malformed-versus-truncated output diagnostic. No retry/video. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-10.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-10.json).
## EV-063-101 — Rev87.10-I SVG truncation diagnosis and one real Parent API attempt (2026-11-13)

Records the EOS/token-cap diagnostic correction, 6/6 focused worker tests, worker compile, backend safe-log-summary test, one Modal deployment, task API rebuild/health check, and one real Parent API-to-Qwen3.5 request. API/Auth/catalog preflight passed; the worker used all 6,144 output tokens without EOS and returned `MODAL_SVG_TOPIC_GUIDE_OUTPUT_TRUNCATED` after 361.621 seconds of inference. API returned HTTP 502 after 395.670 seconds. No validated SVG/render or retry exists. See [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md) and [runtime-attempt-11.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-11.json).
## EV-063-101 — Rev87.10-M/N/O/P Parent SVG geometry diagnosis (2026-11-14)

Records the chicken-specific prompt changes, focused checks, one bounded Modal deployment and the final real Parent API request. Qwen3.5 and worker parsing completed in about four minutes; backend geometry validation rejected the result because the neck endpoint missed the head, while beak length and leg descent also remained below hard thresholds. This was not a timeout, and the 1,800-second deadline was retained. No validated SVG/render or retry exists. Safe terminal timings and topology booleans: [runtime-attempt-20.json](EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-20.json); narrative: [REPORT.md](EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md).

## EV-063-102 — Rev87.11 Arcadia-derived Parent chicken guide (2026-11-14)

Records the deterministic SVG guide derived from the pinned Arcadia CC0 Gallus gallus source, including its separately versioned stroke manifest and provenance. A real call to the Parent API route in the final Docker image returned HTTP 200 with 19 paths and six progressive stages in 0.027 seconds; Modal was not dispatched. Includes response JSON, generated SVG, 1024×1024 raster render, runtime metadata and reproducible test runner. Focused TestClient overrides identity/database dependencies, so this is not Firebase or Android E2E evidence. See REPORT.md.

### Rev87.11-C correction

Adds the v2 20-path/six-stage left-facing guide and separates it from the full-color Arcadia SVG in the Parent UI. Contains the actual route response, six 1024×1024 stroke-stage renders, a separate full-color reference render, hashes/timing, and reproducible runners. Route returned HTTP 200 in 0.045 s without Modal dispatch; focused backend checks passed 9/9 and mobile checks 5/5. Firebase/Android E2E and educator approval are not claimed. See `EV-063-102_ARCADIA_PARENT_SOURCE_DERIVED_GUIDE_20261114/REPORT.md`.

## EV-063-105 — Rev87.11-F Parent hen guide aligned to the supplied HTML (2026-11-14)

The supplied drawing demo was run and inspected at all seven stages. A new V5 guide builds the left-facing hen in eight progressive stages, with a separate 1024×1024 render for each route-derived stage, the final strokes and the optional color reference. The local Parent route returned HTTP 200 in 0.082 s, with 16 paths/eight stages and no Modal dispatch. Backend tests passed 12/12; mobile guide contract tests passed 3/3. V2/V3/V4 remain preserved. Focused TestClient overrides identity/database and does not prove Firebase/Android E2E; V5 remains a private chicken-only draft pending educator review. See [REPORT.md](EV-063-105_PARENT_HEN_HTML_ALIGNED_DRAWING_SEQUENCE_20261114/REPORT.md).

## EV-063-107 — Rev87.11-H Parent guide from exact source paths (2026-11-14)

Records the V7 correction after V6's hand-authored childlike geometry failed the requested match. The local Parent route returns the exact 77 sanitized paths from the pinned Arcadia chicken SVG in eight progressive stages; all eight 1024×1024 stages were rendered and visually inspected. Backend focused tests passed 9/9; mobile guide/path tests passed 8/8; Modal dispatch was guarded and not called. TestClient overrides identity/database and is not Firebase/Android E2E. The chicken draft remains private and needs adult/educator review; unsupported topics retain Qwen/Modal. See [REPORT.md](EV-063-107_PARENT_EXACT_SOURCE_PATH_GUIDE_20261114/REPORT.md).

## EV-063-108 — Rev87.13 Parent multi-dataset SVG guide curation and UI connection (2026-11-14)

Records the selected OpenMoji 17.0.0 turtle/butterfly/dog source pairs, pinned hashes and CC BY-SA 4.0 provenance; Noto candidates were visually rejected and are not in the runtime pack. It contains manually rendered cumulative stages and original-color previews plus the implementation/source audit. These are source-artwork previews, not app screenshots or Parent API output. No tests, build, API/Android run, Modal request/deploy, or runtime confirmation was performed. See [REPORT.md](EV-063-108_PARENT_MULTI_DATASET_SVG_GUIDES_20261114/REPORT.md).

## EV-063-109 — Rev87.14 richer Openclipart Parent guide sources (2026-11-14)

Records the selected Openclipart butterfly/turtle color and line-art pairs, source hashes, CC0 notice, six-stage previews, and rejected dog/alternate-turtle candidates. These are manually rendered source previews, not app screenshots or API results. The source changes and Docker pack were inspected; no tests, build, API/Android run, Modal request/deploy, or runtime confirmation was performed. See [REPORT.md](EV-063-109_PARENT_RICHER_OPENCLIPART_GUIDES_20261114/REPORT.md).

## EV-063-110 — Rev87.15 Openclipart corpus import to Modal Volume (2026-11-14)

Records the full 18-shard Openclipart import and Qwen worker test on Modal. Volume v2 reached `READY` with 178,561 rows, 1,923 guide-eligible SVGs and 110,284,614,262 bytes total; no dataset copy went to Docker or the repository. The deployed Qwen app `/health` passed. One real synthetic inference failed path-coverage validation and was not retried; Parent API/UI, Android, and Teacher presentation were not run. See [REPORT.md](EV-063-110_OPENCLIPART_MODAL_VOLUME_CATALOG_20261114/REPORT.md), [runtime-attempt.json](EV-063-110_OPENCLIPART_MODAL_VOLUME_CATALOG_20261114/runtime-attempt.json), importer logs and worker logs.

## EV-063-111 — Rev87.16 Modal Qwen path-assignment fix (2026-11-15)

Records the required-key assignment schema/parser fix, focused worker tests, redeployment and one successful synthetic Modal catalog-to-Qwen worker request. The returned CC0 kitten guide contains 11 exact source paths across six stages; all eight runner quality checks passed, including complete one-time stage coverage and matching color-reference paths. Includes the validated worker output, bounded Modal logs, health, runtime summary, cumulative stage SVGs and an HTML preview. No retry, child data, video, Parent API/UI/Android, or Teacher runtime. See [REPORT.md](EV-063-111_MODAL_QWEN_CATALOG_PATH_ASSIGNMENT_FIX_20261115/REPORT.md).

## EV-063-112 — Rev87.17 Parent API runtime schema rejection (2026-11-15)

Records one real synthetic Parent API request that reached and completed the Modal Qwen3.5 worker but was rejected at the API boundary because the worker content schema was compared to the API entity schema. This was not a timeout; no retry was made. The emulator identity and backend row were deleted. See REPORT.md and the sanitized runtime summary in EV-063-112_PARENT_MODAL_API_GUIDE_RUNTIME_20261115.

## EV-063-113 — Rev87.18 Parent API schema fix and fresh Modal test (2026-11-15)

Records the corrected content-schema validation and one fresh real Parent API → Modal → API success (HTTP 200). The non-persisted private draft contains 11 exact Openclipart CC0 source paths in six stages, a separate matching color reference, and all eight quality gates passed. Includes the API response, worker summary, six cumulative stage SVGs, color SVG and browser preview. All seven SVGs parsed as XML. No child data, video or Android UI was used; focused pytest collection is blocked by host Python missing sqlalchemy. See REPORT.md in EV-063-113_PARENT_MODAL_API_GUIDE_SCHEMA_FIX_20261115.

## EV-063-114 — Parent pedagogical stroke-guide review (2026-11-15)

Reviews the real Rev87.18 kitten response and the active Modal source-path sequencing implementation. The first step reveals the source outline, and the worker cannot split, simplify, or omit source paths. This review led to the approved Rev87.19 construction-guide redesign. See [REPORT.md](EV-063-114_PARENT_STROKE_CONSTRUCTION_REVIEW_20261115/REPORT.md).

## EV-063-115 — Rev87.19 Parent construction-guide bounded verification (2026-11-15)

Records the source-conditioned construction-guide contract, focused backend/Modal/mobile tests, and one real synthetic-topic Qwen3.5 Modal inference. The model completed, but the worker rejected its output with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`; no SVG or rendered image exists. The local aggregate-size/diagnostic correction was deployed afterward, then the Modal app was stopped; no second inference was run, so the correction has no live-generation proof. No child data, video, or Android UI was used. See [REPORT.md](EV-063-115_PARENT_CONSTRUCTION_MODAL_TEST_20261115/REPORT.md) and the sanitized [worker logs](EV-063-115_PARENT_CONSTRUCTION_MODAL_TEST_20261115/modal_worker_logs.txt).

## EV-063-116 — Rev87.20 Parent construction-stroke correction and final live attempt (2026-11-15)

Records the exact first failure (`SVG_CONSTRUCTION_GUIDE_FINAL_FEATURE_MISSING`), prompt/diagnostic correction, post-fix focused tests (Modal 27/27, backend 12/12, mobile 3/3), deployment v2 and CPU health. The one final synthetic `con mèo` inference returned HTTP 502 after 189.152 s: Qwen emitted only two duplicate strokes for eight stages (70 geometry chars), rejected as `DUPLICATE_STROKE_GEOMETRY`. This was not a timeout; no SVG or render exists and no third inference was sent. Modal app was stopped and verified stopped. See [REPORT.md](EV-063-116_PARENT_STROKE_LIVE_FIX_20261115/REPORT.md), [worker logs](EV-063-116_PARENT_STROKE_LIVE_FIX_20261115/modal_worker_final_logs.txt), and test/runtime records.

## EV-063-117 — Rev87.21 constrained Parent stroke-generation experiment (2026-11-15)

Records the fixed-key stroke decoder, prompt/diagnostic changes and three sequential synthetic Parent route → Modal calls. Results: duplicate geometry at stroke 5; duplicate at stroke 9 after eight unique paths; and first-path complexity failure at 768 characters. API returned HTTP 502 after 193.140 s, 211.341 s and 446.930 s; none was a timeout. Focused tests passed (Modal 30/30, backend 12/12, mobile 3/3). No valid guide/render exists; the Modal app was stopped and verified stopped. See [REPORT.md](EV-063-117_PARENT_STROKE_CONSTRAINED_GENERATION_20261115/REPORT.md) and call-specific worker logs.

## EV-063-118 — Rev87.22 Parent primitive renderer live result (2026-11-15)

Records three real synthetic Parent API → Modal calls after replacing model-authored SVG strings with deterministic primitive rendering. Calls one and two failed worker validation; call three returned HTTP 200 and passed schema/hard gates. Rendered visual review rejected the result: it did not form the source kitten and stage copy did not match visible geometry. Focused checks passed (Modal 34/34, backend 12/12, mobile 3/3). The Modal app is stopped. The report, genuine API responses, sanitized worker logs and rendered SVG/PNG evidence are in [REPORT.md](EV-063-118_PARENT_PRIMITIVE_STROKE_RENDERER_20261115/REPORT.md).

## EV-063-121 — Rev87.26/27 Parent pinned-source stage sequence (2026-11-15)

Records two Rev87.26 attempts (caption visual failure, then empty-stage hard rejection) and one Rev87.27 real synthetic Parent route → Modal success. The final request returned HTTP 200 in 73.116 s with 20 exact source paths across seven stages; the rendered cumulative guide was visually accepted for this pinned monochrome kitten asset. Focused Modal/backend checks passed (49/49 and 12/12); the response remains a private draft requiring adult review. The Modal app is stopped and verified with zero tasks. Android/Firebase E2E, other source assets, colored reference, educator approval and child comprehension remain unverified. See [REPORT.md](EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/REPORT.md) and its per-attempt logs and renders.

## EV-063-122 — Rev87.28 Parent paired-eye stage correction (2026-11-15)

Records the confirmed defect in the genuine Rev87.27 response: right-eye details appeared in stage 4 and the other eye details in stage 5. The exact pinned source now groups segments 10–15 in one paired-eye stage. The worker tests passed 50/50 and the saved genuine response was re-rendered offline as a six-stage guide; the stage-4 render shows both eyes' inner details together. No Modal request/deploy was made, so the original live result remains seven stages. See [REPORT.md](EV-063-122_PARENT_SYMMETRIC_EYE_STAGE_20261115/REPORT.md), the offline render script, preview payload and images.


## EV-063-123 — Rev87.29 Parent non-kitten Modal/catalog verification (2026-11-15)

Records one pre-dispatch butterfly 503 caused by the local 32-path cap, plus one genuine Modal/Qwen3.5 request each for elephant and fish. Both APIs returned 200, but manual review rejected both: elephant stage/caption alignment is incoherent; fish selected a kitchen-scale source and emitted repeated/mixed-language copy. The Modal app was stopped and its server list is empty. Includes raw request/response, sanitized worker logs, health preflight, rendered source SVGs and cumulative stage images. See [REPORT.md](EV-063-123_PARENT_NON_KITTEN_MODAL_SMOKE_20261115/REPORT.md).
