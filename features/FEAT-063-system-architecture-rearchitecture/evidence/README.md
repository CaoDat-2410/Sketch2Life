# FEAT-063 evidence index

Evidence includes source/configuration and documentation reviews for earlier FEAT-063 slices. Rev33 adds local runtime and database evidence: the Lesson Library migration was applied, non-AI HTTP workflows were tested, and MinIO limitations are documented in EV-063-26.

EV-063-13 records the pre-platform table-reduction and relationship-integrity baseline. EV-063-18 supersedes its platform target counts through Q195; EV-063-24 records the Rev31 implementation crosswalk and complete API inventory. EV-063-14 documents the original architecture diagram package and its references/QA; EV-063-15 supersedes its artifact counts with the expanded master and detailed system-flows PDF. Earlier evidence files preserve historical review snapshots and must not be treated as the current baseline.

| ID | Type | Purpose | Artifact |
| EV-063-37 | Current FE Swagger | SRS v2.2 implementation scope and live/snapshot parity | EV-063-37_SWAGGER_SRS_V22_SCOPE_20261101.md |
| EV-063-38 | Swagger cleanup | Current-only file set, focused checks, and commit consolidation status | EV-063-38_SWAGGER_HISTORY_CLEANUP_20261101.md |
|---|---|---|---|
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
