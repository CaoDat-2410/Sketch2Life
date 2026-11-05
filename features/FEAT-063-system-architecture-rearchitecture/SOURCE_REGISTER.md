# FEAT-063 source register

## Six-milestone Parent/Teacher roadmap review — current local record, independent round 3 — 2026-11-03

- Roadmap: `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`, reviewed round 3 at SHA-256 `DED4B89D6A3F66FD0570EEA11E2240840C47DE607667544708C7C394F7F49C86`, then owner-accepted as planning baseline; current SHA-256 `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA`. Use the existing SRS v2.3-draft unchanged; it remains unsigned. No M2–M6 implementation is approved.
- Review plans: Rev49 `plan/ROADMAP_REVIEW_FIX_PLAN_20261103.md` SHA-256 `BECC69238E5049649204E5F9C32D2CB9660E625B795E131C4A5553599D08901C`; Rev50 `plan/ROADMAP_REVIEW_FIX_PLAN_REV50_20261103.md` SHA-256 `0FFF0D9CAA01036E08A90120FC7067D38B564E80E72E4324B470D1E8E13C66DC`.
- Rev50A backlog supplement: `plan/ROADMAP_REVIEW_FIX_PLAN_REV50A_BACKLOG_POINTER_20261103.md` SHA-256 `27288634F301B7430C531E17B51EE15D35B0EB3735C26925767111447849661D`; backlog current bytes SHA-256 `380BF9F813CF809E35D9EA6F843E33A0DF892BA886E8C366AEB1C0F757A57391`.
- Current finding disposition and independent round-3 verdict **ACCEPTED**: `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`, SHA-256 `D44A754ECBF63E6DCB94D1037A6D76F39398D160BB9DAD9E6C6343FC77C9CDBB`. Review thread `01a1a205-1441-73e0-9170-6fdc4d591472` (`gpt-6-luna`, effort `max`); all 12 pinned hashes matched at review time. Owner's subsequent SRS baseline decision is D-132.
- Owner accepted the reviewed roadmap as a planning baseline under `approvals/TASK_APPROVAL.md`; D-132 records use of the current SRS v2.3-draft unchanged, with Parent-before-Teacher ordering per §8.1. Each milestone still needs separate implementation approval.
- Controlling sources: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §§5–8.1, 11, 13, 14.1, 19, 22, 29, 31; `artifacts/DATA_TABLE_REGISTER.md` §§1, 5.6. SRS remains unsigned.
- B0–B13 plan/report hashes differ by content, not only line endings. Owner reconfirmation or an addendum is required before the current plan is used as authority. DTR local CRLF/LF hash difference is line-ending-only; see disposition.
- M1 independent review round 3 is ACCEPTED for synthetic local demo only. A2 closeout records ACCEPTED/COMPLETE within its plans/addenda but discloses shared-DB rows, Alembic reconciliation and mypy baseline debt. The A2→B1→B2 chain is separate; its active phase status must be read from its live implementation thread.

## Six-milestone Parent/Teacher roadmap review — round-1 record (superseded) — 2026-11-03

- Rev49 roadmap SHA-256 `9DF3FECF0FFF45972ADFB4D49A50E31773CBAD8832F0B5C5B625C9702CEB49CC`; Rev49 disposition SHA-256 `72150BEC8A624D03E6205CE40C2AA9A48942BCF8A1D7CA0A40BAF8CC60851A1E`.
- This historical note incorrectly described the DTR discrepancy as unreproduced and assigned the OpenAPI decision D-130. Rev50 corrects those statements: DTR differs only by line endings; OpenAPI is D-131 because D-130 already identifies the full BE/Bruno decision.

## Modal AI setup scaffold — 2026-11-03

- Owner instruction: create the Modal configuration scaffold now; owner will configure environment values afterward.
- Approved plan: `plan/MODAL_AI_SETUP_SCAFFOLD_20261103.md`, SHA-256 `7FE03A68DF76877457DF5C5F652FCB705669A624B2E07F7B6F317C9FB510E391`; exact approval is in `approvals/TASK_APPROVAL.md`.
- Canonical source: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft §§6.2–6.3, 9.5, 22, 24.3–27, 31.4–31.5. Rev26 remains a pending model/flow amendment and does not authorize candidate promotion.
- Implementation: `deployment/modal/srs_v23/` contains the workload registry, path/hash-only contract, dev L4/L40S skeletons, placeholder environment sample and owner setup instructions. The existing legacy `deployment/modal/qwen_vision_v2.py` is unchanged.
- Evidence: `evidence/MODAL_AI_SETUP_SCAFFOLD_20261103.md`. No Modal account operation/deploy/GPU, model inference, backend/storage integration, actual `.env`, product test, or child data is claimed.

## Rev42 Swagger review and local commit — current — 2026-10-30

- Direct owner request: `coi và commit cho tui`. Plan Rev42 SHA-256 `E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8` authorizes review, focused verification and one local commit on `dev`; it excludes push.
- Review corrected unsafe request-ID reflection in the typed middleware 413 response. Exported local OpenAPI still matches the served API and all previous contract counts.
- Check results and limitations: `evidence/EV-063-34_SWAGGER_REVIEW_AND_COMMIT_20261030.md`.

## Rev41 Swagger overview presentation — current — 2026-10-30

- Direct owner request: make the Swagger overview in the attached screenshot easier to scan. Plan Rev41 SHA-256 `8693C3B4165F9413775306260CCC9023404F2AB7F58C967632236951B1FC2BDB`.
- The info description is a compact summary of coverage, bearer authentication/tag behavior, and unmounted candidates. No operation or runtime changes.
- Current snapshot SHA-256 `C1F2B453E5D893AF5328C9091A51B183CB2D67FED2587411C0D45598F47A9466`; served counts and verification are recorded in `evidence/EV-063-33_SWAGGER_INFO_PRESENTATION_20261030.md`.

## Rev40 local Swagger QA kit — current — 2026-10-30

- Direct owner approval: `duyệt` for local synthetic workflow examples, 413 contract parity and focused verification. Plan Rev40 SHA-256 `701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9`.
- Rev37 contract source SHA-256 remains `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`. Snapshot SHA-256 `70BDA49D2E122C4CE0370211DCEF8EA03BEC477CFDE2C60673501EB2CCDF8208`.
- Synthetic fixture: `artifacts/qa-fixtures/synthetic-demo.png`, 128 × 96 RGBA, 504 bytes, SHA-256 `2A0D125A7B34306DF54407EA8B7C41BA189C061C24F6C43277502C38D3CA9B9F`; no personal/child content.
- Quickstart: `artifacts/LOCAL_SWAGGER_QA_QUICKSTART_20261030.md`. Verification and authenticated-route limits: `evidence/EV-063-32_LOCAL_SWAGGER_QA_KIT_20261030.md`.

## Rev39 professional Swagger navigation — current — 2026-10-30

- Direct owner request: organize Swagger by explicit role where known and otherwise by a clear professional grouping. Plan Rev39 SHA-256 `1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F`.
- Role grouping is based on current Lesson Library route guards; BE1 and Demo groupings use handler/domain workflows to avoid implying authorization that is not explicit in the contract.
- Snapshot SHA-256 `27BB19AC8A5938D239A300DB4BFC5028AA205A675AE9B09EE00CCD35CB3D3453`; review and results are recorded in `evidence/EV-063-31_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`.

## Rev37 contract-aligned Swagger/OpenAPI — current — 2026-10-30

- Owner-provided source: `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`, SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- Plan Rev38 is approved for exact OpenAPI documentation, contract completeness checks and reporting observed discrepancies; plan SHA-256 `C1E8C74AD57E7F053E0D1E093BAF7F97BE6F12E8EF8887A2C098632B9B863BCF`.
- Generated metadata, local Compose OpenAPI snapshot, focused tests and the known upload-413 mismatch are indexed in `evidence/EV-063-30_SWAGGER_OPENAPI_FEAT063_REV37_20261030.md`.
## Rev46 Swagger commit consolidation — current — 2026-11-01

- Owner requested one commit for the current Swagger work and removal of the two preceding Swagger commits from `dev` history.
- Exact target commits: `6d77d2ad41370f118386d9861fed4cd031ddea67` and `f68ed2b579c89e8fb1ee3dcf7e4c8f109acd31d8`; retained parent: `111ae547007801d7d171dd12f3ac6f1085d22199`.
- `origin/dev` was checked at the exact old tip. Plan Rev46 SHA-256 `4EE5DEF1E5AD7C544BBCF79921E8A7495EDE79C7765AE523D38BFFA1D9938B27` authorizes one consolidated commit and a lease-guarded update of `origin/dev`.
- Plans Rev47–48 remove obsolete snapshots, local-demo artifacts, and superseded standalone Swagger revision notes; retain the current Rev45 SRS v2.2 snapshot and EV-063-37.

## Rev45 FE Swagger scope from SRS v2.2 — current — 2026-11-01

- Owner instruction: update Swagger on `dev` according to SRS v2.2. This selects the source for this documentation task only; the source document still labels itself v2.2-draft and pending owner sign-off.
- SRS source: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md`, repository SHA-256 `D1C4AF0D42A160AAA08D1EC33F1FFD746C4EB33CA75C5D802616A5DD4502E4DE`. It matches the owner's attached copy after normalizing BOM/line endings, as reviewed before this plan.
- API source: current FastAPI route handlers, auth guards, DTOs, and `MOUNTED_OPERATIONS`; §9.6 route groups are logical proposals, not final OpenAPI paths.
- Approved Plan Rev45 SHA-256: `5D1DBABE161F92F08DE7FE8C1B81B1E5D57CFA3C2B8D57CBA6BE76ACADB0FD06`; direct approval is recorded in `approvals/TASK_APPROVAL.md`.
- Published FE snapshot: `artifacts/OPENAPI_FEAT063_REV45_20261101.json`, 24 operations / 17 paths / 4 tags, SHA-256 `C61D3ADD7FF906AC9E5B018A9CE428AF7B162D67510FEEE7B202B53DA05D74A2`. The shared error envelope is named `ApiError` in this FE document; its fields/runtime payload are unchanged. The overview is 50 words and tag descriptions are 5–7 words.
- Current implementation gaps are stated in the OpenAPI info block and detailed in `evidence/EV-063-37_SWAGGER_SRS_V22_SCOPE_20261101.md`. No new route is inferred from the target proposal table.

## Rev47–48 current-only Swagger cleanup — current — 2026-11-01

- Plan Rev47 removes superseded OpenAPI snapshots and retired local-demo fixture/quickstart artifacts.
- Plan Rev48 removes standalone Swagger plans/evidence for prior revisions from the current dev tree. The Rev45 SRS v2.2 snapshot and EV-063-37 remain current.
- Backend contract metadata and source code remain because they generate and validate the current FE projection.

## Rev36 UI component patterns and interaction states — current — 2026-10-30

- Plan Rev36 is approved for nine generated component/state boards; SHA-256 `300104684514C4C6F67614F58DDE402668AAC24AF2204F9B1BCA7A5BBEA2D336`.
- SRS baseline: §3, §20, §21.5–§21.6, §22.4, §31.2–§31.7; Rev31-reconciled Lesson Library contract; Rev31 route inventory; Rev32 purpose catalog; Rev35 UI visuals.
- Output: nine component boards plus per-group prompt/motion notes at `assets/generated/ui-components-rev36-20261030/`; index separates current Lesson Library APIs from SRS-only/unmounted states.
- EV-063-29 records source paths, final PNG hashes, review observations, limitations and visual-approval status.
- Palette tokens and unresolved age/quota/profile-share values remain illustrative; no application code uses the generated assets.

## Rev35 UI screen mockups and motion notes — current — 2026-10-30

- Plan Rev35 is approved for the exact 14-screen generated-visual scope; SHA-256 `0EBBE2D7E983663F448B167F39FE42AD6C89A2E38EE5390A054673FC2C42723C`.
- Visual baseline: SRS v2.3-draft §3, §6, §20, §21.5 and §31.1–§31.7; Rev31-reconciled Lesson Library API contract; Rev31 API inventory; Rev32 purpose catalog.
- Existing visual references: `apps/ui-mobile/assets/images/`, `apps/teacher-ui/src/`, `apps/admin-ui/src/`.
- Fourteen screen PNGs, fourteen per-screen prompt records and fourteen per-screen motion notes are under `assets/generated/ui-mockups-rev35-20261030/`; screen index and shared specifications are in that directory.
- EV-063-28 records image-generation source files, provenance, visual review observations and limits. Assets remain drafts pending owner visual approval; no application source uses them.

## Rev34 legacy non-AI API regression - current - 2026-10-29

- Plan Rev34 is approved for the exact test-only scope; SHA-256 `308F4FEA6576BAB08ACCD86B62616FE463C94D099FC27EBF301E855C4756F5B1`.
- “Old APIs” means pre-Lesson-Library BE1/classroom and Demo/local-flow routes. AI-dependent endpoints, new Lesson Library/storage-example routes, and candidate/unmounted declarations are reported separately.
- EV-063-27 records 77 active non-AI route-dispatch responses (0 HTTP 5xx), 109/110 non-PostgreSQL API tests, 3/4 BE1 PostgreSQL tests, the two failures, and uncovered success-path boundaries. The disposable DB was dropped; persistent DB remains at Rev33.

## Rev33 local migration and non-AI API verification - current - 2026-10-29

- Plan Rev33 is approved for local additive migration and non-AI workflow testing; SHA-256 `513FEE246CF1DD2B062BE146996C362C7C726667A9529E0E2342962084CF4DE1`.
- EV-063-26 records migration of the existing local `sketch2life` database to `20261028_ll_0001`, Lesson Library API tests (5/5), BE1 HTTP suite (3/4), and exact MinIO/test-database limits. The disposable test DB was dropped; the application DB was retained.
- No AI API, remote provider, AWS/Firebase, real child data, actual `.env` edit, commit, or push was used/performed.

## Complete API purpose catalog - current - 2026-10-28

- Plan Rev32 is approved for documentation-only work; SHA-256 `FD189D3E2684CE2930624AFD7412C54F9BB53339209790F7B319B534C41E087C`.
- `artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md` lists all 135 declared method/path operations with purpose, handler and runtime exposure; artifact SHA-256 `E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881`.
- No route or runtime behavior was changed. EV-063-25 records the static catalog and its limits.

## Lesson Library backend and full API inventory - current - 2026-10-28

- Plan Rev31 and Addendum A are approved; implementation has been completed at source level. Approved hashes: `BC948B27F5CFADD05EC6D12B0B7D989241CDEB6FC3CA6CAB1521988C712BBB8C` and `570BC65BE74A82261EC2455147EAF33FB0575B166B73EF506084BBF07A62727D`.
- API contract: `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`; original Rev29 pre-reconciliation hash `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`, current Rev31-reconciled hash `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`; 30 operations.
- Existing Parent, Teacher, BE1 and demo method/path declarations are preserved. New Lesson Library routes are additive under `/api/lesson-library/v1`; local storage examples remain gated to local development.
- EV-063-24 records scope and evidence limits. No tests/builds, Docker execution, security validation, database inspection/migration, provider/AWS access, or actual `.env` changes were performed. SRS v2.3 remains unsigned; the 92-active/140-physical count is a source-derived crosswalk only.

## Local Docker and MinIO storage example - historical Rev30 slice, incorporated in Rev31 - 2026-10-28

- Plan Rev30: `plan/PLAN_REV30_LOCAL_DOCKER_MINIO_STORAGE_EXAMPLE_20261028.md` (SHA-256 `F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794`), approved for implementation by the owner's direct instruction; lifecycle IN_PROGRESS.
- EV-063-23 records the implementation scope and evidence limits. This sample uses a provider-neutral application port and Boto3 S3-compatible adapter, with local-only MinIO wiring and a guarded example route.
- The formal 28-operation Lesson Library API contract remains a separate draft proposal under Rev29; Rev30 does not implement its routes, persistence, parsing, or sharing.
- MinIO is pinned for local synthetic use only; AWS account access/credentials and production selection are not included. Actual `.env` files remain untouched.

## Historical contract baseline - Rev29, implemented under Rev31 - 2026-10-28

- Plan Rev29: `plan/PLAN_REV29_BACKEND_LESSON_API_CONTRACT_AND_ENTITY_NAMING_20261028.md` (SHA-256 `B63B5BEC21C71BFD154EEA08741C167B3B144AF1133A17695D4C63E6760BCD6A`), AWAITING_APPROVAL.
- API contract: `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`; original Rev29 pre-reconciliation hash `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`, current Rev31-reconciled hash `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`; 30 operations.
- EV-063-22 records the convention review. Rev29 preserves the owner-selected Rev28 scope and clarifies entities, table ownership and DTO boundaries.
- Rev29 was a draft contract at the time; Rev31 and Addendum A supersede its approval status and implement the routes/persistence. See the current entry above.

## Historical backend lesson-platform plan — Rev28 (superseded by Rev29) — 2026-10-28

- Plan Rev28: `plan/PLAN_REV28_BACKEND_LESSON_LIBRARY_UPLOAD_REVIEW_PARENT_READ_20261028.md` (SHA-256 `22CBC9E4360B39BDD995B683B5B9681D962D3D1C54355F929F0B1C3BE2387FE6`), preserved and superseded by Rev29.
- Owner selected Teacher lesson upload, Manager approval/Public publication and Parent read/share. Rev28 plans structured CRUD, deterministic non-AI document extraction, versioned review/publication, revocable grants and Parent read-only access.
- EV-063-21 records the SRS/repository implications. Library uploads need library-owned source-document/revision records; occurrence-owned source documents are not reused. Rev28 proposes updating Data Table Register counts before migration.
- The full SRS/Data Table Register remain drafts. No implementation approval is recorded; Plan Rev26 AI research remains independent.

## Historical initial backend CRUD recommendation — Plan Rev27, superseded — 2026-10-28

- Plan Rev27: `plan/PLAN_REV27_BACKEND_BASIC_LESSON_CRUD_DRAFT_20261028.md` (SHA-256 `984B54DE505A4C86B9334079D6FC9086A0E5ABC9E1736C21BC0734096454E3BD`), preserved as the initial narrow recommendation and superseded by Rev28.
- Scope recommendation: Teacher's manual private lesson draft CRUD with structured text/activity fields, immutable versions and soft archive; no AI, upload, publication, Manager review, Parent access or runtime integration in the first slice.
- Repository review: EV-063-20 `evidence/BACKEND_BASIC_LESSON_CRUD_REPOSITORY_REVIEW_20261028.md`. Existing BE1 role/organization boundary is available; the generic learning_content router is candidate-only and not mounted in default composition.
- No implementation or test approval was recorded under Rev27. SRS/Data Table Register v2.3 remain drafts; Plan Rev26 AI research status is independent and unchanged.

## AI pipeline research — pending Plan Rev26 (2026-10-28)

- Current canonical source remains SRS and Data Table Register v2.3-draft; Plan Rev25 does not authorize this new model-selection/AI-flow amendment.
- Plan Rev26 is awaiting approval: `plan/PLAN_REV26_MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md` (SHA-256 `ECD0A0A6435193A903313409B699574FE9DB30BAAB8498A714A3FC54C75EEABC`).
- Research/evidence: `evidence/MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md` (EV-063-19). Recommendations remain provisional; no model, checkpoint, GPU profile, quota policy or sample-recovery policy is selected.

## Official AI/Modal sources for pending research (2026-10-28)

- LTX-2.5 capabilities/system requirements/license and Modal GPU/LTX example: `https://docs.ltx.io/models/ltx-2-5`, `https://docs.ltx.io/open-source-model/getting-started/system-requirements`, `https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x`, `https://modal.com/docs/guide/gpu`, `https://modal.com/docs/examples/ltx`.
- FLUX 3/2 and Modal image example: `https://github.com/black-forest-labs/flux-3-image-klein`, `https://github.com/black-forest-labs/flux2`, `https://modal.com/docs/examples/image_to_image`.
- Qwen3.5/3.6, Qwen3-ASR, Whisper, Modal Whisper example and Modal model catalog: `https://huggingface.co/Qwen/Qwen3.5-9B`, `https://huggingface.co/Qwen/Qwen3.6-27B`, `https://github.com/QwenLM/Qwen3-ASR`, `https://github.com/openai/whisper`, `https://modal.com/blog/how-to-deploy-whisper`, `https://modal.com/docs/guide/supported-models`.
- SAM 2/3, Wan2.2, VieNeu-TTS, Qwen3Guard and ShieldGemma 2: `https://github.com/facebookresearch/sam2`, `https://github.com/facebookresearch/sam3`, `https://github.com/Wan-Video/Wan2.2`, `https://github.com/pnnbao97/VieNeu-TTS`, `https://github.com/QwenLM/Qwen3Guard`, `https://ai.google.dev/gemma/docs/shieldgemma/model_card_2?hl=en`.

## Repository sources reviewed

- `docs/context/SOURCE_REGISTER.md` (global authority/source index; updated with the current FEAT-063 SRS source pointer)
- `docs/governance/{WORKFLOW,APPROVAL_POLICY,EVIDENCE_MANAGEMENT}.md`
- `docs/architecture/{OVERVIEW,PYTHON_BACKEND_ARCHITECTURE,DEPENDENCY_RULES,CONTRACTS_AND_INTEGRATION}.md`
- `docs/adr/ADR-0001-modular-monolith-first.md`
- `docs/adr/ADR-0017-be1-runtime-backend-boundaries.md`
- `docs/adr/ADR-0018-be2-durable-ai-job-runtime.md`
- `docs/adr/ADR-0019-review2-classroom-runtime-and-modal-direction.md`
- `docs/adr/ADR-0007-vision-runtime-dependency-pinning-and-qwen3-vl-candidate-profile.md`
- `features/FEAT-050-be2-knowledge-video/artifacts/RUNTIME_DECISION_SHEET.md`
- `features/FEAT-003-multimodal-understanding/evidence/P2_T3_LIVING_SUMMARY.md`
- `features/FEAT-062-parent-teacher-workflows-modal-architecture/` (historical Parent/Teacher planning input; its Q-01–Q-07 SRS draft is superseded by FEAT-063 SRS v2.3-draft and is not an owner-question source)
- Owner clarification in the 2026-10-28 conversation: Parent's optional sketch suggestion means an AI-generated 3–5-step line-sketch for a generic topic, with skip/non-blocking behavior and no child data sent to generation; Teacher AI Sketch Deck was then described as a main-flow step; Q167 later makes it opt-in by session. Recorded as historical Q146/D-92 and approved for documentation amendment by Plan Rev24. The interim text-only Q145 interpretation is superseded.
- Current SQLAlchemy/Core table definitions under `backend/src/sketch2life/infrastructure/` and Alembic revisions under `backend/alembic/versions/`.
- Current runtime manifests: `backend/pyproject.toml`, `compose.yaml`, `apps/mobile/package.json`, `apps/ui-mobile/package.json`, `apps/teacher-ui/package.json`.

## External primary sources consulted (2026-10-26)

- Official LTX-2.5 model/system requirements and open-source runtime docs: `https://docs.ltx.io/models/ltx-2-5`, `https://docs.ltx.io/open-source-model/getting-started/system-requirements`, `https://github.com/Lightricks/LTX-2`.
- Official Modal GPU and pricing docs: `https://modal.com/docs/guide/gpu`, `https://modal.com/pricing`.
- Official Qwen model cards: `https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct`, `https://huggingface.co/Qwen/Qwen2.5-7B-Instruct`.
- VieNeu-TTS model card/project: `https://huggingface.co/pnnbao-ump/VieNeu-TTS`, `https://github.com/pnnbao97/VieNeu-TTS`.
- Government legal sources: Law 91/2025/QH15 effective 2026-01-01, `https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160`; Law 134/2025/QH15 effective 2026-03-01, `https://vanban.chinhphu.vn/?docid=216334&pageid=27160`; Ministry of Public Security summary, `https://mps.gov.vn/bai-viet/bao-ve-du-lieu-ca-nhan-trong-mot-so-hoat-dong-1754989261`.

## Additional primary sources checked for the Q01–Q104 review baseline (2026-10-27)

- Firebase Authentication server-side ID token verification: https://firebase.google.com/docs/auth/admin/verify-id-tokens.
- PostgreSQL 17 index/partial-index documentation: https://www.postgresql.org/docs/17/indexes.html.
- MoMo recurring subscription API: https://developers.momo.vn/v3/docs/payment/api/wallet/subscription/.
- VNPAY recurring payment technical specification v2.1.0: https://sandbox.vnpayment.vn/apis/files/VNPAYGW_RecurringPayment_Techspec2.1.0-VN.pdf.
- LTX system requirements and Modal GPU guide were re-opened on 2026-10-27 to confirm the L40S/L4 design constraints: https://docs.ltx.io/open-source-model/getting-started/system-requirements and https://modal.com/docs/guide/gpu.

## Limits

- No live database was introspected. “86 production tables” means source-declared SQLAlchemy/Core runtime mappings, cross-checked by table factory and module inventories; it is not a claim that a particular deployed database currently contains all 86 tables.
- Five owner-fence tables in `owner_fence_fixture.py` are test fixtures, excluded from production counts.
- No model weights were downloaded or benchmarked. Candidate VLM/LLM/TTS choices are design candidates pending exact revision, license, synthetic quality, and latency evidence.
- No final PDF exists at this review stage. A future PDF must be generated only after owner approval of the two Markdown documents and will remain a summary of the proposed repository target, not legal advice or runtime proof.


## StoryRun-lite S1→S2 implementation sources — 2026-11-02

- `plan/STORYRUN_LITE_S1_S2_LAUNCH_PROMPT_20261102.md` — owner-approved continuous S1→S2 launch authority and constraints; SHA-256 `13067726F17892EDD4E8A10EF0EF24DE65ED4F8FAB913FE1C7753612177A070C`.
- `plan/STORYRUN_LITE_S1_S2_MASTER_GOAL_20261102.md` — pinned aggregate goal; SHA-256 `C5E8B15839FA3470596DAC4B964450BD56428D481EA1A78B8AEC70B2E6A02B42`.
- `plan/STORYRUN_LITE_VISION_M0_V12_FINAL_DRAFT_20261102.md` — image safety and current byte/pixel limits in §10; SHA-256 `D0560C4B7821EA76A50780D00161DE1D1AC9917168B9C975547077C457FB448B`. This draft is not described as independently accepted.
- `plan/STORYRUN_LITE_GOAL_1_PLAN_20261102.md` and `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md` — approved workflow decisions and prior scope constraints; both pinned hashes were verified before implementation.
- `plan/STORYRUN_LITE_S1_S2_EXECUTION_PLAN_20261102.md` and `approvals/TASK_APPROVAL.md` — scoped implementation plan and explicit approval record.
- `artifacts/storyrun-lite/openapi.json`, `artifacts/storyrun-lite/bruno/`, and `artifacts/DATA_TABLE_REGISTER.md` — synthetic local API handoff and additive source-derived persistence crosswalk.
- `backend/src/sketch2life/{domain,application,contracts,infrastructure,interfaces}` StoryRun-lite modules and `backend/alembic/versions/20261102_story_run_lite.py` — implementation source; the migration branch was enumerated but not applied.
- `evidence/STORYRUN_LITE_S1_CHECKPOINT_20261102.md` and `evidence/STORYRUN_LITE_S2_READINESS_20261102.md` — local test, worker, fixture provenance, environment and readiness evidence. No provider or production database source was used.
- `evidence/STORYRUN_LITE_S1_S2_FINAL_20261102.md` and `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_20261102/` — final stage-gate summary and scope/hash handoff snapshot.

## StoryRun-lite final runtime evidence update — 2026-11-02

- `evidence/STORYRUN_LITE_S1_CHECKPOINT_20261102.md` — final PostgreSQL owner/migration and real ClamAV verification; focused StoryRun-lite/A1 suite result **125 passed, 0 skipped**; prior Windows Job Object measurements retained.
- `evidence/STORYRUN_LITE_S2_READINESS_20261102.md` — goal-owned PostgreSQL loopback/recovery integration and Bruno CLI 4.3.0 results: main 8/8, cancel 2/2, abort 3/3; all ten request files passed assertions.
- `evidence/STORYRUN_LITE_S1_S2_ENVIRONMENT_20261102.md` — temporary loopback resource ownership and exact cleanup record. Existing PostgreSQL services were not changed or used.
- `evidence/STORYRUN_LITE_S1_S2_FINAL_20261102.md` — final SL-0–SL-8 status. Technical/runtime stages pass; strict acceptance remains NOT VERIFIED because one unrelated preserved initial-hash discrepancy is outside the allowlist.
- The final snapshot inventories the current workspace state. All 35 FEAT-061/FEAT-064 protected paths remain hash-identical; no local A2 or FEAT-061 content was edited by this goal.


## Owner-approved baseline rebaseline record — 2026-11-02

- `evidence/STORYRUN_LITE_SL0_SL8_REBASELINE_20261102.md` records the local provenance review, owner-selected B disposition, exact initial/current hashes and acceptance limitation.
- `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REBASELINE_20261102/` is the additive post-decision inventory. The initial S1→S2 baseline manifest and original snapshot are retained unchanged.

## Milestone 1 review round 1 and fixes — 2026-11-03

- Independent findings: `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND1_20261103.md`.
- Approved plan: `plan/STORYRUN_LITE_MILESTONE1_INDEPENDENT_REVIEW_FIX_20261103.md`; owner explicitly allowed the approval entry and six fixes.
- Fix evidence: `evidence/MILESTONE1_REVIEW_FIX_REPORT_20261103.md`; PostgreSQL output: `evidence/MILESTONE1_REVIEW_FIX_POSTGRES_20261103.log`.

## Milestone 1 review round 2 and fixes — 2026-11-03

- Independent findings: `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND2_20261103.md`.
- Round-2 implementation and test evidence: `evidence/MILESTONE1_REVIEW_ROUND2_FIX_REPORT_20261103.md`, `evidence/MILESTONE1_REVIEW_ROUND2_OFFLINE_20261103.log`, `evidence/MILESTONE1_REVIEW_ROUND2_POSTGRES_20261103.log`, and the sanitized Bruno summary JSON beside them.
- Source/test snapshot: `.claude/handoff/snapshots/MILESTONE1_REVIEW_ROUND2_CLOSEOUT_20261103/`; read-only independent review prompt: `plan/MILESTONE1_REVIEW_ROUND3_PROMPT_20261103.md`.


## Milestone 1 independent review round 3 — 2026-11-03

- Verdict ACCEPTED: `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND3_20261103.md`.
- Review thread: `01a19ff8-ecf5-7843-ac8b-e5b8f5a62dc6`; all 38 closeout snapshot paths matched at review time.


## Full BE Bruno collection — 2026-11-03

- Approved task plan: plan/BE_FULL_BRUNO_COLLECTION_PLAN_20261103.md, SHA-256 4488A7B739FDCC80246AFB590DDFC229B6DCB37FEB9600C5B9501B160E5E80ED; approval is appended to approvals/TASK_APPROVAL.md.
- Source of active operations: backend/src/sketch2life/interfaces/http/app.py application factory and its state.runtime_openapi_schema, generated for combined/classroom/demo profiles with local optional groups separately measured. The FE/SRS public /openapi.json projection is not the full API source.
- Historical comparison: artifacts/API_INVENTORY_FEAT063_REV31_20261028.md and backend/src/sketch2life/interfaces/http/openapi_contract.py MOUNTED_OPERATIONS / UNMOUNTED_OPERATIONS. Current runtime adds one mounted pilot-profiles GET absent from the static Rev31 catalog; three local storage examples remain optional; 11 candidate declarations remain unmounted.
- Deliverables: artifacts/be-full/openapi.runtime.json, artifacts/be-full/API_COVERAGE.csv, artifacts/be-full/bruno/, README and evidence/BE_FULL_BRUNO_COLLECTION_REPORT_20261103.md. Generator/validator helper scripts remain local-only and are excluded from the requested collection commit. Snapshot path is recorded in the report.
- Validation: Bruno CLI 4.3.0 parsed and documented all 136 request names. Safe loopback smoke passed `GET /health` (200), process-local synthetic `POST /v1/sessions` (201), and `GET /v1/sessions/{session_id}` (200) with AI disabled and no DB URL. Sanitized transcript: evidence/BE_FULL_BRUNO_VALIDATION_20261103.log. DB-backed BE1/Lesson Library routes and StoryRun-lite runtime were not run. The MCP request-list tool exposes only the existing StoryRun-lite collection.

## Modal drawing VLM L4 POC — 2026-11-03

- Owner instruction: after Modal environment setup, continue and host the AI workload the system needs; exact bounded scope is approved in plan/MODAL_DRAWING_VLM_L4_POC_20261103.md, SHA-256 F2AF6433EFE812BBD8144CBCD3E4ECFDE09FCF0A9952280BCE814314A7008E72.
- Canonical requirements: SRS v2.3-draft §§6.2–6.3, 24.3, 27, 29, 31; drawing VLM is the first AI stage. No production candidate is selected.
- External sources: Qwen2.5-VL-7B model card/revision (Apache-2.0), Transformers v4.53.0 model documentation, Modal GPU and Volumes v2/model-weight docs; exact URLs and applicability are recorded in the approved plan and POC evidence.
- Preflight: Modal CLI 1.6.3 authenticated; dev environment exists but app/volume/secret inventory is empty; current-month dev metered-cost summary 0.00. No inference has run at this point.

## Modal AI hosting wave — 2026-11-03

- Authority and pin: `plan/MODAL_AI_HOSTING_WAVE_20261103.md` (approved hash `C8FCB03681F2145E727F89E55DDD159AA354814E30B868CD745B930A83FCA5BA`); SRS v2.3-draft remains the canonical product source.
- Runtime/model sources: official Modal GPU and Volume guides; Hugging Face model cards for Qwen2.5-7B-Instruct, faster-whisper large-v3, VieNeu-TTS v3 Turbo, MOSS Audio Tokenizer Nano ONNX, FLUX.2 Klein 4B, and Wan2.2 TI2V-5B; official Wan2.2 runtime pinned at `1ea34ff48f87168174e12956e200b1d908b1c5ff`. LTX-2.5 access remains gated and unused.
- Results and limitations: `evidence/MODAL_AI_HOSTING_WAVE_20261103.md` records deployed apps/call IDs, 88.59 GiB of pinned checkpoints, and successful synthetic TTS-to-ASR and FLUX POCs. The corrective Qwen-VL call later reached terminal success. A separate API-triggered call later reached Modal success after API timeout, but its result was not persisted by the API; see the vertical-slice evidence. Modal billing after downloads has not been checked. No production readiness, model certification, or product enablement is claimed.

## Local API runtime availability smoke - 2026-11-03

- Owner-authorized read-only plan: `plan/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`, SHA-256 `7DA01D9CF5D5C4E98BA45C88815BBBE3589D0A5E9F94E512DDD9B995D570C5BA`.
- Evidence: `evidence/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`. Local Compose `/health` and `/openapi.json` returned 200, but the active API image has no StoryRun route, AI provider is unset, and no HTTP route dispatches to the new Modal function apps. A read-only StoryRun GET returned 404; no mutation or inference request was sent.
- The earlier one-request backend-to-temporary-Modal Vision success is separately recorded in `evidence/STORYRUN_LITE_MAIN_BE_INTEGRATION_20261103.md`; it is not evidence of integration to the current hosted workers.


## Backend API to Modal drawing VLM vertical slice - 2026-11-03

- Plan and owner authorization: `plan/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`; operative approval and cumulative SHA-256 are in `approvals/TASK_APPROVAL.md`.
- Modal function invocation: [official function invocation methods](https://modal.com/docs/guide/function-invocation-methods); deployed call history: [Modal function CLI](https://modal.com/docs/cli/latest/function); scratch storage uses [Modal Volumes](https://modal.com/docs/guide/volumes).
- Temporary Windows PostgreSQL source: [PostgreSQL Windows download guidance](https://www.postgresql.org/download/windows/) identifies the EDB binary ZIP for advanced users. The downloaded EDB 17.11-4 archive was SHA-256 checked against the value recorded in [EnterpriseDB's installer repository](https://github.com/EnterpriseDB/edb-installers/issues/706).
- Implementation and current call status: `evidence/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`. The single API-triggered call reached Modal terminal `success` after the API timeout, but its result was not persisted by the API; the run still awaits operator reconciliation. The drawing app is stopped; no end-to-end API result or production readiness is inferred.

| EV-063-40 | Parent image-to-script API/AI retest | Record synthetic Parent run/upload API results, Modal L4 scheduling timeout, unresolved subject confirmation, detached story worker unknown outcome, zero video calls, and verified shutdown of all deployed Modal dev apps | PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md |
| EV-063-41 | Parent generated-image, story, and activity-selection retest | Record synthetic image upload/admission, successful drawing VLM and direct story worker calls, legacy activity-list selection and boundary, timings, model-output factual errors, and verified shutdown | PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md |

| EV-063-42 | AI flow SRS alignment and Teacher deck POC | Record Parent story contract/business-rule correction, Modal schema failure and local adapter fix, synthetic Teacher deck text result, unavailable FLUX visual, 13-operation API matrix, tests, and verified shutdown | `evidence/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md` |
| EV-063-43 | Full non-video AI workload retest | Approved scope for a fresh synthetic retest of all callable non-video Modal workloads, including bounded SAM2.1 feasibility; video generation excluded | `plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md` |
| EV-063-44 | Full non-video AI workload retest results | Record SRS-aligned backend changes, fresh synthetic Modal workload/API results, L4-capacity timeouts, 14 contract checks, focused tests, and verified shutdown/cleanup | `evidence/AI_NONVIDEO_WORKLOAD_FULL_RETEST_RESULTS_20261104.md` |
