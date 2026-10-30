# FEAT-063 source register

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

