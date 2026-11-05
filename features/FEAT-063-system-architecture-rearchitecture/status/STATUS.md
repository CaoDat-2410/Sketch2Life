# Status

## Six-milestone Parent/Teacher roadmap independent review round 3 — 2026-11-03

- Documentation review **ACCEPTED** by an independent read-only Codex thread (`01a1a205-1441-73e0-9170-6fdc4d591472`, `gpt-6-luna`, effort `max`). Reviewer verified all 12 pinned hashes and reported no remaining finding in scope on the reviewed roadmap hash `DED4B89D6A3F66FD0570EEA11E2240840C47DE607667544708C7C394F7F49C86`.
- Owner then accepted the roadmap as a planning baseline using the existing SRS v2.3-draft unchanged; Parent-before-Teacher follows SRS §8.1. Current roadmap hash after recording that owner decision is `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA`.
- SRS remains unsigned and unmodified; no M2–M6 implementation is approved. Each milestone still requires its own detailed plan, acceptance criteria, data/migration boundary and explicit approval. Remaining model/version, line-sketch schedule, optional lesson access and B0 provenance gates remain open.
- Evidence: `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`, SHA-256 `D44A754ECBF63E6DCB94D1037A6D76F39398D160BB9DAD9E6C6343FC77C9CDBB`.
- Owner decision: D-132 in `DECISIONS.md`, recorded in `approvals/TASK_APPROVAL.md`; no tests/validators, DB or Modal/provider/network operation. Branch/HEAD remain `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index remains empty.
- Review was read-only: no tests/validators, DB, Modal/provider/network, or Git operations. Branch/HEAD remain `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index remains empty. Existing local changes were preserved.

## Six-milestone Parent/Teacher roadmap review round 2 — 2026-11-03 (superseded by round 3 ACCEPTED)

- Documentation correction **FIXED — XONG-CHƯA REVIEW** under Plans Rev50 and Rev50A; roadmap remains DRAFT and SRS v2.3 remains unsigned. N1–N7 and the related P2/P3 notes are recorded with owner gates; no M2–M6 implementation is approved.
- Corrected Rev49's D-130 reassignment: OpenAPI is now D-131; D-130 remains the full-BE/Bruno decision. Historical Swagger summaries no longer reuse D-114–D-119 as decision IDs. DTR mismatch is documented as line-ending-only; B0 plan/report provenance remains unresolved and needs owner confirmation before reuse as authority.
- A2 local closeout remains ACCEPTED/COMPLETE within scope, with residuals disclosed (58 synthetic shared-DB rows, schema/Alembic reconciliation, mypy baseline). M2 must address these before migration; this task did not touch the DB. Current A2/B1/B2 launch status still comes from its active implementation thread.
- Plan: `plan/ROADMAP_REVIEW_FIX_PLAN_REV50_20261103.md`, SHA-256 `0FFF0D9CAA01036E08A90120FC7067D38B564E80E72E4324B470D1E8E13C66DC`. Evidence: `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`.
- Verification: `git diff --check` exit 0 (Git emitted only CRLF-normalization warnings); defined decision-ID duplicate scan found none; no placeholders remain. Roadmap SHA-256 `DED4B89D6A3F66FD0570EEA11E2240840C47DE607667544708C7C394F7F49C86`; disposition SHA-256 `3FF823141E8366DC4AA8090989AFD97640DC65D6791BF3178A1DE271ACBE85DF`.
- No tests/validator suite, DB, Modal/provider or network call. Branch/HEAD remain `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index is empty. Existing local source/A2 changes were preserved. No stage/commit/push/merge.

## Six-milestone Parent/Teacher roadmap review round 1 — 2026-11-03 (superseded)

- Documentation correction **COMPLETE** under Plan Rev49; the roadmap remains DRAFT. Accepted cloud findings are incorporated, unresolved product choices remain owner-gated, and no M2–M6 implementation approval is implied.
- Local state checked: M1 review round 3 **ACCEPTED** for the synthetic local demo; A2 **ACCEPTED / COMPLETE** per the local FEAT-064 closeout. The latter is local-only and was not visible to the cloud reviewer. The local A2→B1→B2 document header says DRAFT; any later phase launch must be verified from the active FEAT-064 thread.
- DTR pinned hash matches local bytes; B0–B13 current-plan/report hash mismatch remains a provenance gap and is explicitly documented. Duplicate decision ID was corrected to D-130.
- Evidence: `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`. No tests, validator suite, DB, Modal/provider or network operation was run for this doc-only correction.

## B3 manifest and owner decisions — 2026-10-31

- B3 complete as a document: ownership matrix (18 boundaries, 18 shared-file rows, all co-signatures unsigned) and manifest with three migration-order options left open. Evidence: `evidence/B3_OWNERSHIP_MIGRATION_MANIFEST_20261031.md`, `evidence/B3_OWNER_MATRIX_20261031.csv`.
- Owner decision slip recorded in `evidence/OWNER_DECISION_SLIP_20261031.md`: scoped BE2 exception, migration option X, three-party `OwnerFenceV1` signing, pilot before Rev36, no temporary DB yet, and B2 Q2-Q8 answered.
- Still open: named P4, actual co-signatures, per-file reviewers, approvals for FEAT-064 T0, Rev36 S1-S3 and B2A, and the B1 update. No code, database, provider or deployment change.

## B2 Parent activity ordering - 2026-10-31

- B2 reviewed 225 source passages: POST_VIDEO 26, PRE_VIDEO 9, TEACHER_PRE_VIDEO 82, NEUTRAL 81, AMBIGUOUS 27.
- Owner selected A for Q1 only; Q2-Q8 remain unconfirmed working assumptions.
- B2A amendment plan is DRAFT / AWAITING_APPROVAL; 42/45 proposed edits remain owner-gated, none applied.
- B1 rows T018-T031, T046 and T047 remain blocked_by=B2.
- No SRS or Data Table Register source was changed; B2 does not block the FEAT-064 pilot.

## B0 closeout and B1 API crosswalk — 2026-10-30

- B0a complete (offline snapshot baseline, 124 catalog rows matched, 11 absent). B0b open: `EV-063-30` files not found; Rev37 historical provenance and runtime results unverified. Evidence: `evidence/B0_CLOSEOUT_20261030.md`.
- B1 complete as a document: `evidence/B1_API_CROSSWALK_20261030.md` and `.csv` (192 rows: KEEP 54, MODIFY 3, LEGACY_HOLD 64, FIXTURE 14, NEW_TARGET 57; evidence E0 57, E1 11, E2 83, E3 41; pilot Y 18, MAYBE 2). Dispositions are proposals for owner review; no route is claimed to have passed.
- Open for the owner: 23 low-confidence rows, 16 rows blocked by B2, the C070 evidence level, and the B0b source files. Next planned task: B2 (Parent activity ordering), which does not block the FEAT-064 pilot.
- No code, approval beyond the B1 entry, database, provider or deployment change.

## Dev backend synchronized for local testing — 2026-10-30

- Incoming dev tip: `111ae547`, destination existing feature/feat063-be-foundation. Existing Modal wrapper and backend Rev36 plan preserved; no S1/S2/S3 implementation approval inferred from upstream UI/API approvals.
- 26 focused non-DB contract/unit tests passed; harness/security/architecture checks passed. Upstream JUnit evidence has two pre-existing whitespace findings; preserved as historical bytes. No DB migration, running service or AI call in this synchronization.
- Evidence: `evidence/notes/DEV_BACKEND_SYNC_20261030.md`. PostgreSQL/MinIO and end-to-end AI tests remain separate.

## Remaining AI model recommendations — 2026-10-30

- Publisher-source research proposes FLUX.2-klein-4B for line-sketch, Qwen3-VL reuse plus OpenCV for consistency, and Qwen3Guard-Gen-4B / ShieldGemma 2 4B for text/image moderation. See `evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md`.
- These are evaluation proposals, not SRS changes, quality acceptance or deployment. No models downloaded, GPU calls or runtime changes.

## Video flow comparison — 2026-10-30

- Owner left task allocation to the backend team and requested a comparison of video flows. Read-only findings: `evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md`.
- SRS 2.3 retains the core video pipeline already in SRS 2.2; it differs substantially from legacy demo/whiteboard/Lightning source. Current Modal wrapper remains Vision-only. No implementation or provider test follows from this comparison.

## Current-machine continuation — 2026-10-30

- Rev35 → Rev36 independently checked: DELTA_REVIEW_PASS for the three P3 corrections, not implementation approval or a full re-audit. Earlier BA handoff statements about pending final delta review describe the publication checkpoint.
- `plan/S1_DECISION_CARD_20261030.md` proposes exact 24 BLOCK / 5 KEEP dispositions for owner review. Parent and original S1 hashes are unchanged. S1 remains NOT_STARTED pending disposition, applicable OD/allocation and execution approval.
- Evidence: `evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md`. Documentation only; no source/runtime/DB/provider changes or publication in this continuation.

## BA handoff — 2026-10-30

- Use `plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` as the latest backend foundation draft and `plan/REV36_S1_EXECUTION_SCOPE_DRAFT_20261029.md` for the S1 candidate inventory. Rev35 passed independent plan review; Rev36 addresses its three P3 notes but has not yet received an independent final review.
- S1–S3 are proposed foundations only. StoryRun, actual provider integration, voice, video and other end-to-end work need later plans. The SRS/register remain drafts, S1 dispositions and applicable OD decisions remain open, and implementation is AWAITING_APPROVAL. Sharing this material with BA is not approval to implement.

## Rev36 response to Rev35 review — 2026-10-29

- `plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` is the current draft for review, superseding Rev35; implementation approval remains pending.
- Clarifies existing/new guards, adds OD-8–OD-14, and records P4 composition ownership alongside FEAT-064 coordination. See `evidence/notes/REV36_REVIEW_RESPONSE_20261029.md`.
- Documentation only; no product code, approvals, DB/provider execution or publication.

## Historical: Rev35 response to independent review — 2026-10-29

- `plan/PLAN_REV35_BACKEND_SRS23_ALIGNMENT_20261029.md` supersedes Rev34 for future review and remains AWAITING_APPROVAL. `plan/REV35_S1_EXECUTION_SCOPE_DRAFT_20261029.md` retains the candidate inventory; exact dispositions remain open.
- Addresses the reviewed migration graph, legacy/typed job compatibility, identity onboarding safety, CI and disposable-DB acceptance gates, and FEAT-064 coordination. See `evidence/notes/REV35_REVIEW_RESPONSE_20261029.md`.
- Documentation only: no product implementation, approval edit, DB/provider execution or publication.

## Historical: SRS 2.3 plan alignment — 2026-10-29

- `plan/PLAN_REV34_BACKEND_SRS23_ALIGNMENT_20261029.md` supersedes Rev33 for future planning; AWAITING_APPROVAL, no implementation approved. S1 inventory remains a subordinate draft with individual operation dispositions pending.
- Records the Parent-after-video and Teacher-before-video distinction, unresolved SRS/register contradictions, eight AI target kinds, consent fail-closed requirements, Teacher age migration gap and SRS cutover gates. Qwen3 smoke is not a quality acceptance.
- See `evidence/notes/REV34_SRS23_PLAN_ALIGNMENT_20261029.md`. No SRS content, historical approvals, runtime source, DB or provider changed.

## Historical: backend-foundation preparation — 2026-10-29

- Branch: `feature/feat063-be-foundation`, baseline `4f071242`; contains Modal and CI repair through the merged history.
- Rev33 remains AWAITING_APPROVAL; S1/S2/S3 source implementation not started. All earlier approvals retain their scope.
- First-slice preparation: `plan/REV33_S1_EXECUTION_SCOPE_DRAFT_20261029.md`, DRAFT. Static command inventory and exceptions prepared; owner disposition/error choice and exact subset approval remain pending.
- Checkpoint: `evidence/notes/BE_FOUNDATION_MERGED_BRANCH_CHECKPOINT_20261029.md`.
- No runtime source, schema/migration, approval, service/DB/Modal execution or Git publication in this preparation step.

## Swagger review and local commit — Plan Rev42 (2026-10-30)

- Lifecycle: REVIEW and verification complete for the approved single local commit scope; push is excluded.
- Approved Plan Rev42 SHA-256: `E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8`.
- Review confirmed the 124-operation/111-path/18-tag local OpenAPI snapshot matches the served API and records 11 unmounted candidates. A middleware review finding was fixed: invalid request IDs are now sanitized before being echoed in typed 413 responses, media-route matching is exact, and oversized version values are capped.
- Focused Swagger/upload suite: 5 passed; Ruff, compile, exporter, live snapshot parity, plan hash checks, `git diff --check` and repository security validation passed.
- Evidence: `evidence/EV-063-34_SWAGGER_REVIEW_AND_COMMIT_20261030.md`.

## Swagger overview presentation — Plan Rev41 (2026-10-30)

- Lifecycle: COMPLETE for the approved overview-copy change.
- Approved Plan Rev41 SHA-256: `8693C3B4165F9413775306260CCC9023404F2AB7F58C967632236951B1FC2BDB`.
- Replaced the dense info paragraph with a concise intro and labeled coverage, authorization/Try it out and unmounted-route notes. No API routes, tags, schemas or behavior changed.
- Snapshot SHA-256: `C1F2B453E5D893AF5328C9091A51B183CB2D67FED2587411C0D45598F47A9466`; it matches the live OpenAPI (124 operations, 111 paths, 18 tags). `/docs` and `/openapi.json` return 200.
- Evidence: `evidence/EV-063-33_SWAGGER_INFO_PRESENTATION_20261030.md`.

## Local Swagger QA kit — Plan Rev40 (2026-10-30)

- Lifecycle: COMPLETE for the approved local synthetic workflow and 413 parity scope.
- Approved Plan Rev40 SHA-256: `701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9`.
- Oversized image/audio requests now return HTTP 413 with `MobileWorkflowResultV1` / `UPLOAD_TOO_LARGE`; OpenAPI 413 schemas match. Focused tests: 4 passed; exporter, Ruff, compile and `git diff --check` passed.
- The documented synthetic session/image flow passed in memory: 201/version 0, then 200/`ADMITTED`/version 1. Snapshot SHA-256: `70BDA49D2E122C4CE0370211DCEF8EA03BEC477CFDE2C60673501EB2CCDF8208`.
- The loopback API was restarted; `/docs` and `/openapi.json` return 200 with 124 operations, 111 paths, 18 tags and two Try it out examples. The synthetic Demo workflow is ready for interactive testing. Protected routes still require Firebase ID tokens and their persistence services; no Auth Emulator, test DB URL, or fake credential path is configured. Evidence: `evidence/EV-063-32_LOCAL_SWAGGER_QA_KIT_20261030.md`.

## Professional Swagger navigation — Plan Rev39 (2026-10-30)

- Lifecycle: COMPLETE for the approved tag/navigation scope.
- Approved Plan Rev39 SHA-256: `1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F`.
- Swagger has 18 descriptive groups. Explicit Lesson Library roles are shown where source guards establish them; other routes are grouped by BE1/Demo domain and workflow.
- Contract parity remains 124 mounted operations across 111 paths and 11 unmounted candidates. Focused Swagger test: 2 passed; exporter passed.
- Snapshot SHA-256: `27BB19AC8A5938D239A300DB4BFC5028AA205A675AE9B09EE00CCD35CB3D3453`. Local server restarted at `/docs`; existing upload 413 mismatch remains documented under EV-063-30.
- Evidence: `evidence/EV-063-31_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`.

## Contract-aligned Swagger/OpenAPI — Plan Rev38 (2026-10-30)

- Lifecycle: COMPLETE for the approved documentation scope; one existing upload body-limit API/test mismatch is reported in EV-063-30 and remains outside this behavior-preserving change.
- Approved Plan Rev38 SHA-256: `C1E8C74AD57E7F053E0D1E093BAF7F97BE6F12E8EF8887A2C098632B9B863BCF`.
- `/docs` and `/openapi.json` returned HTTP 200. Local profile OpenAPI 3.1.0 contains all 124 mounted operations across 111 paths and records all 11 unmounted candidates. Request, authentication, response and schema parity checks passed.
- Snapshot `artifacts/OPENAPI_FEAT063_REV37_20261030.json`; SHA-256 `A45748B8715F1934BED86F89795F71C3559CD0E2122140EC3D346194E9B2F9F5`.
- Focused Swagger checks: 2 passed; exporter validation and targeted Ruff/compile checks passed. The existing upload body-cap test fails because its expected `failure.code=UPLOAD_TOO_LARGE` payload differs from the middleware's generic `REQUEST_TOO_LARGE` body. No route behavior, database, Docker, provider, commit, or push changes were made.
- Evidence: `evidence/EV-063-30_SWAGGER_OPENAPI_FEAT063_REV37_20261030.md`.
## Current Swagger cleanup — Plans Rev47–48 (2026-11-01)

- Lifecycle: COMPLETE for the current-only documentation cleanup and local commit amendment; remote publication is pending GitHub authentication.
- Removed the superseded OpenAPI snapshots/local-demo artifacts under Rev47 and the 12 standalone Swagger documents for prior revisions under Rev48.
- Retained baseline: Rev45 SRS v2.2 snapshot, source contract metadata, and EV-063-37. No API route or runtime behavior was changed by this cleanup.
- Exporter, targeted Ruff, whitespace check, and repository security validation passed. Backend test suites were not run.
- The amended consolidated commit retains parent 111ae547007801d7d171dd12f3ac6f1085d22199; remote publication is guarded by the expected old tip recorded in EV-063-38.
- Evidence: evidence/EV-063-38_SWAGGER_HISTORY_CLEANUP_20261101.md.

## Swagger commit consolidation — Plan Rev46 (2026-11-01)

- Lifecycle: Local consolidated commit complete; remote ref update is pending GitHub authentication.
- Approved Plan Rev46 SHA-256: `4EE5DEF1E5AD7C544BBCF79921E8A7495EDE79C7765AE523D38BFFA1D9938B27`.
- Current remote tip before rewrite: `6d77d2ad41370f118386d9861fed4cd031ddea67`; retained parent: `111ae547007801d7d171dd12f3ac6f1085d22199`.
- Completion and resulting ref verification will be recorded in EV-063-38.

## FE Swagger SRS v2.2 scope — Plan Rev45 (2026-11-01)

- Lifecycle: COMPLETE for the approved documentation-only projection scope.
- Approved Plan Rev45 SHA-256: `5D1DBABE161F92F08DE7FE8C1B81B1E5D57CFA3C2B8D57CBA6BE76ACADB0FD06`.
- The FE OpenAPI projection contains exactly 24 mounted operations across 17 paths and four tags. The full 124-operation runtime schema remains available internally; no route, auth guard, request/response behavior, or persistence flow changed.
- Exporter verification passed with the backend virtualenv and confirmed exact allowlist equality, four public tags, schema references, no `x-` extensions, a 50-word overview, and tag descriptions of at most seven words. The public error model is labeled `ApiError`; its fields/payload are unchanged. Snapshot `artifacts/OPENAPI_FEAT063_REV45_20261101.json`, SHA-256 `C61D3ADD7FF906AC9E5B018A9CE428AF7B162D67510FEEE7B202B53DA05D74A2`.
- Local `/docs` and `/openapi.json` returned 200 and the served JSON equals the snapshot (24 operations / 17 paths / 4 tags). URL: `http://127.0.0.1:8000/docs`.
- The overview identifies the implemented scope and missing Parent story/activity, Teacher occurrence/Sketch Deck/sample-video, playback/job, quota/payment, and notification APIs. Runtime-local/collaborative routes are not deleted; they are omitted from this FE documentation view.
- Backend tests were not run. `git diff --check` passed. No commit or push was made. Evidence: `evidence/EV-063-37_SWAGGER_SRS_V22_SCOPE_20261101.md`.

## UI component patterns and interaction states — Plan Rev36 (2026-10-30)

- Lifecycle: REVIEW; nine component/state images and all per-group prompt/motion/index/evidence records are complete.
- Approved Plan Rev36 SHA-256: `300104684514C4C6F67614F58DDE402668AAC24AF2204F9B1BCA7A5BBEA2D336`.
- Output: nine 1,586 × 992 PNG boards, nine `PROMPT.md` files and nine `MOTION.md` files under `assets/generated/ui-components-rev36-20261030/`.
- Includes modal/bottom-sheet, decision dialog, toast/snackbar, error/empty/auth states, upload/extraction, quota/video-job, sharing/revoke, and feedback/notification patterns.
- Current-versus-SRS-target API boundary is documented in the index. Visual approval remains pending; no app code/API/database change or test/build was performed.
- Evidence: EV-063-29; index: `assets/generated/ui-components-rev36-20261030/COMPONENT_INDEX.md`.

## UI screen mockups and motion notes — Plan Rev35 (2026-10-30)

- Lifecycle: REVIEW; generation, per-screen organization, prompt/motion notes and feature-local provenance are complete.
- Approved Plan Rev35 SHA-256: `0EBBE2D7E983663F448B167F39FE42AD6C89A2E38EE5390A054673FC2C42723C`.
- Output: 14 valid PNG screens, each in its role/screen folder with `PROMPT.md` and `MOTION.md`; dimensions are portrait Android (approximately 790–864 × 1,821–1,989) or desktop web (1,586 × 992).
- Detailed motion suggestions cover explicit guide reveal, capture feedback, backend-confirmed job stages, video/activity transitions, filtered-upload stages, classroom Deck opt-in, publication decisions and moderation. Reduced-motion behavior is documented.
- All assets remain generated drafts pending owner visual approval. No code, API, database, migration, test/build, provider call or deployment was performed.
- Evidence: EV-063-28; index: `assets/generated/ui-mockups-rev35-20261030/SCREEN_INDEX.md`.

## Legacy non-AI API regression - Plan Rev34 (2026-10-29)

- Lifecycle: REVIEW; execution and feature-local evidence EV-063-27 are complete, with two test failures recorded.
- Approved Plan Rev34 SHA-256: `308F4FEA6576BAB08ACCD86B62616FE463C94D099FC27EBF301E855C4756F5B1`.
- Safe dispatch smoke: 77 active legacy non-AI routes returned HTTP responses; 52 returned 401, 23 returned 422, 2 health endpoints returned 200, and none returned 5xx. This does not replace success-path coverage.
- Existing API suites: non-PostgreSQL batch 109 passed / 1 failed; BE1 PostgreSQL suite 3 passed / 1 failed. Failures are an outdated route-composition baseline and the BE1 unrepresentable `effective` consent state, detailed in EV-063-27.
- AI-dependent routes were excluded. Newer Lesson Library/storage routes and unmounted candidates are separated in EV-063-27. The disposable test DB was dropped; the persistent DB remains unchanged at the Rev33 target.
- No product-code or existing test-expectation change was made. No AI/provider call, real child data, `.env` edit, commit, or push.

## Current non-AI API workflow verification - Plan Rev33 (2026-10-29)

- Lifecycle: REVIEW; execution is complete and evidence EV-063-26 records the partial verification and remaining limits.
- Approved Plan Rev33 SHA-256: `513FEE246CF1DD2B062BE146996C362C7C726667A9529E0E2342962084CF4DE1`.
- Applied `20261028_ll_0001` to the existing local Compose database `sketch2life`; Alembic also applied prerequisite `20261024_0005`. Main DB revision is verified and its named volume/data were retained.
- Lesson Library HTTP integration suite: 5/5 passed against PostgreSQL with synthetic data. Existing BE1 suite: 3 passed, 1 failed; the run exposed that BE1 authorization requires consent state `effective`, while the database constraint only permits `pending`/`revoked`. The successful consent path cannot be represented; details are in EV-063-26.
- A disposable `sketch2life_be1_acceptance` database was migrated, used for the tests, and dropped afterward. ClamAV was healthy. MinIO image pulls failed (Quay 401; Docker Hub access denied), so storage-example routes used an in-memory object-store test adapter; MinIO adapter/bucket behavior remains unverified.
- Targeted Ruff and compile checks passed. AI APIs, remote databases, real child data, actual `.env` edits and deployment were excluded. No commit or push was performed.

## Current API purpose catalog - Plan Rev32 (2026-10-28)

- Lifecycle: COMPLETE; documentation-only catalog generated and reconciled against the 135-route Rev31 inventory.
- Approved Plan Rev32 SHA-256: `FD189D3E2684CE2930624AFD7412C54F9BB53339209790F7B319B534C41E087C`.
- Artifact: `artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md` (SHA-256 `E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881`).
- No endpoint, code, schema, migration, or runtime behavior changed. Static route inventory only; no tests, Docker, database, provider, or deployment operation was performed.

## Current Lesson Library backend and API inventory - Plan Rev31 (2026-10-28)

- Lifecycle: IMPLEMENTED; static source review complete. Runtime validation and database migration are pending and were outside this approved slice.
- Approved Plan Rev31 SHA-256: `BC948B27F5CFADD05EC6D12B0B7D989241CDEB6FC3CA6CAB1521988C712BBB8C`; Addendum A SHA-256: `570BC65BE74A82261EC2455147EAF33FB0575B166B73EF506084BBF07A62727D`.
- Scope delivered: 30 Lesson Library operations, additive persistence/migration source, owner-scoped resumable uploads, deterministic PDF/DOCX/PPTX extraction and ClamAV scan boundary, Manager moderation, Parent read/share, default-router mounting, and the complete static API inventory.
- Existing Parent, Teacher, BE1 and demo route paths were preserved. Evidence: EV-063-24 at `evidence/REV31_LESSON_LIBRARY_IMPLEMENTATION_AND_API_INVENTORY_20261028.md`.
- Inventory: 135 route declarations total; 121 unconditional routes in the combined app, 3 conditional local storage-example routes, and 11 candidate/fixture/unmounted declarations. FastAPI docs endpoints are noted separately in the inventory.
- No tests/builds, security validation, Docker pulls/start, live database or migration, AWS operation, provider call, deployment, or actual `.env`/secret edit was performed. The Alembic migration is present but unrun. SRS and Data Table Register v2.3 remain unsigned drafts; Rev31's 92/140 count is an implementation crosswalk, not a database observation.

## Historical local Docker and storage example - Plan Rev30 (incorporated in Rev31)

- Lifecycle: IN_PROGRESS. Owner approval for this exact slice is recorded in `approvals/TASK_APPROVAL.md`.
- Approved plan SHA-256: `F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794`.
- Scope: backend Compose service, local MinIO/private bucket initialization, placeholder env templates, Boto3 S3-compatible adapter, and local-only source-document upload/read/delete example.
- No tests, builds, security validation, Docker pulls, Compose service startup, database changes, or AWS operations have been run.
- Rev29 was a contract-only draft at the time. Rev31 and Addendum A later approve and implement the API; see the current status above.

## Historical backend API contract plan - Plan Rev29 (implemented under Rev31)

- Lifecycle: AWAITING_APPROVAL. Plan Rev29 SHA-256: `B63B5BEC21C71BFD154EEA08741C167B3B144AF1133A17695D4C63E6760BCD6A`.
- Rev29 pre-reconciliation API contract SHA-256: `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`; current Rev31-reconciled contract SHA-256: `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`.
- Rev29 clarifies domain entities vs tables vs DTOs and lists routes, actors, purposes, schemas and errors. Scope continues to include Teacher CRUD/upload, deterministic no-AI extraction, Manager Public review, Parent read/share and Admin hide.
- Evidence: EV-063-22, `evidence/API_CONTRACT_NAMING_AND_ENTITY_REVIEW_20261028.md`.
- Rev29 was a contract-only draft at the time. Rev31 and Addendum A later authorize and implement the API; their current status is recorded above.

## Historical backend implementation plan — Plan Rev28 (superseded by Rev29)

- Lifecycle: superseded by Plan Rev29; implementation approval was not recorded. Plan Rev28 SHA-256: `22CBC9E4360B39BDD995B683B5B9681D962D3D1C54355F929F0B1C3BE2387FE6`.
- Scope: Teacher lesson CRUD and upload, deterministic no-AI extraction with Teacher review, Manager approval for Teacher Public content, selected/group sharing, Parent read-only access to Public/active shares, and Platform Admin hide.
- Schema gap: current occurrence-owned document records cannot own reusable library uploads. Rev28 proposes library-scoped source-document/revision records and an additive Data Table Register update before migration.
- Evidence: EV-063-21, `evidence/BACKEND_LESSON_LIBRARY_SCOPE_AND_UPLOAD_REVIEW_20261028.md`.
- No code, migrations, tests/builds, live database or provider operation was performed. `approvals/TASK_APPROVAL.md` remains unchanged.

## Historical initial recommendation — Plan Rev27 (superseded by Rev28)

## Draft backend implementation plan — Plan Rev27 (2026-10-28)

- Lifecycle: superseded initial narrow recommendation; no implementation approval was recorded. Plan Rev27 SHA-256: `984B54DE505A4C86B9334079D6FC9086A0E5ABC9E1736C21BC0734096454E3BD`.
- Proposed slice: Teacher-only private lesson draft CRUD, manually entered structured text and activities, immutable versioned edits, soft archive, verified school/author scope.
- The owner subsequently chose to include Manager publication, Parent read/share and lesson upload; those choices are incorporated into Rev28.
- Evidence: EV-063-20, `evidence/BACKEND_BASIC_LESSON_CRUD_REPOSITORY_REVIEW_20261028.md`.
- `approvals/TASK_APPROVAL.md` is unchanged. No source code, migration, test/build, live database, AI/Modal or deployment work was done.

## Pending amendment — Plan Rev26 (2026-10-28)

- Lifecycle: AWAITING_APPROVAL for a documentation-only AI model/Modal flow reassessment. Plan Rev26 SHA-256: `ECD0A0A6435193A903313409B699574FE9DB30BAAB8498A714A3FC54C75EEABC`.
- Research evidence: EV-063-19, `evidence/MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md`.
- Historical Rev26 status: the v2.3 draft carried a stale 91/126 note, later corrected. Current SRS distinguishes v2.3 baseline 89/137 from the Rev31 92/140 implementation crosswalk; neither describes a live database.
- Recommendations are not owner decisions. No model/provider/checkpoint is selected; Q11/Q13, quota-refund behavior and Teacher sample recovery remain open.
- No SRS/register/ADR content change, product implementation, database inspection, Modal operation, provider call, benchmark, GPU spend, test/build, deployment or real-child processing was performed.

## Historical product-design state - Plan Rev25 (extended by later records)

- Lifecycle: DOCUMENTATION_ONLY. Plan Rev25 is approved for updating SRS, Data Table Register and architecture records. Product implementation, schema/migration work, providers, tests/builds and deployment remain unapproved.
- Authority: owner answers Q147–Q195. They extend Q01–Q146 and preserve the earlier Parent/Teacher flows, image-to-video pipeline and historical records.
- SRS: v2.3-draft, Vietnamese, age 36–120 months. The platform adds Platform Admin, School Manager, scoped/revocable access, one-school-per-organization tenancy, reusable lesson versions, filtered authoring, lesson visibility/publication, Parent history/feedback and multi-scope quota.
- Runtime order: Parent child draws; an adult may enable line-sketch during drawing; after drawing capture artwork, generate a new video through the existing child-specific pipeline, then show lesson activities. Teacher flow and one-child sample remain, with line-sketch generated only when enabled in-session.
- Requirements: 107 FR, 60 BR, 38 NFR, 65 Given/When/Then acceptance criteria and 19 edge scenarios. This amendment adds FR-PL-01–25, BR-47–60, NFR-34–38 and AC-46–65.
- Data Table Register: v2.3-draft; 11 logical platform tables added. Target is 38 retained/refactored + 51 new = 89 active, plus 48 legacy/read-only = 137 projected physical. Counts are repository-derived and are not a live database inspection.
- Proposed architecture record: ADR-0022, additive platform lesson library and sharing; no final stack/provider is selected.
- Current sources: SRS §31, Data Table Register §14, ADR-0022, Plan Rev25 and `approvals/TASK_APPROVAL.md`. The SRS and register remain unsigned drafts.
- Open decisions remain explicit in SRS §31.10 and Data Table Register §14.3, including exact age bands, AI lesson suggestion roles, 30/60-day history, share fields/expiry, sample eligibility, script defaults, visual approval, quota precedence and answer 46.
- Evidence: EV-063-18 records document-only scope, preserved v2.2 snapshots and static reconciliation. No product tests/builds, database, provider, Modal, payment, migration, deployment or real-child data was used.
- Diagram/PDF outputs are historical snapshots based on an earlier SRS. They were not refreshed by this Markdown amendment and are not evidence for the v2.3 content.

## Historical snapshot through Plan Rev24 (superseded by the current state above)

- Lifecycle: DOCUMENTATION_ONLY. Plan revision 22's Draw.io/PDF request is complete. Revision 23 corrected the SRS source; revision 24 is approved for the Parent AI line-sketch documentation amendment. The SRS and Data Table Register remain drafts; product implementation remains unapproved.
- Plan: revision 22; the approved scope is documentation-only under `approvals/TASK_APPROVAL.md`. The approval hash matches this plan revision.
- Follow-up amendment: plan revision 23 corrected the SRS source and retired FEAT-062's stale question list. Plan revision 24 is approved for documentation-only scope: Q146 records the Parent AI line-sketch as an optional feature; Q145's text-only interpretation is superseded.
- Owner decisions: Q01–Q146 are represented in the SRS, data-table register, ADR and feature decision/context records. Parent/Teacher flows remain separate; Parent can request or skip a generic 3–5-step AI line-sketch guide and confirms the child's artwork subject only after capture; Teacher AI Sketch remains an occurrence-wide main-flow deck; every story/video run has exactly one child.
- SRS: revision 2.2-draft, Vietnamese, with 46 BR, 82 FR and 33 NFR IDs; 45 Given/When/Then acceptance criteria and 19 edge scenarios. It includes the full VLM → structured story/storyboard → script review → Character Bible/reference → per-scene LTX-2.5 on Modal L40S → consistency → FFmpeg/TTS/subtitles → automated safety → private playback pipeline. Final video approval and public gallery/download are excluded. SRS content remains unsigned.
- Data-table register: revision 2.2-draft. Parent Sketch Guide uses existing AI Job/Core Asset/AI Policy owners, with target kind `PARENT_SKETCH_GUIDE`, private temporary asset provenance/expiry/cleanup and independent resource accounting; no new table is currently proposed. All 86 repository-declared production mappings are dispositioned and five fixtures are excluded. The target is 38 retained/refactored + 40 new = 78 active, plus 48 read-only legacy = 126 projected physical. Each of the 40 new tables has a matching relationship entry. This is a logical target, not a live database count.
- AI job architecture baseline: one discriminated target per StoryRun, Teacher Sketch Deck, or Parent Sketch Guide. Story/video jobs resolve one child from StoryRun; neither sketch target contains child/profile refs.
- Architecture record: proposed ADR-0021 reconciles target counts, Teacher Sketch Deck, optional Parent AI guide, video pipeline, current-owner transfer, upload lifecycle and async job boundaries. D-73–D-79 record Q137–Q144; D-91 is the historical text-only interpretation and D-92 records the owner clarification for Q146. D-80 records the target-discriminated AI Job contract; D-83 records the current full data-model audit and supersedes D-82's count. D-84–D-85 record relationship integrity and the composed read contract.
- Evidence: EV-063-13 records all-source/target table disposition, relation and canonical-field checks, the 78 active/48 legacy/126 projected physical arithmetic, and static cross-document consistency review. No product tests/builds, database, provider, Modal, payment, migration or benchmark was run.
- Parent guide amendment: EV-063-17 records the Q146 SRS/Data Table Register/ADR/source reconciliation, Plan Rev24 scope and static checks; exact model/license/cost/rate/retention gates remain open.
- Markdown language: Vietnamese with technical identifiers retained. Both files remain drafts and have not received content sign-off.
- Diagrams/PDF: the existing monochrome 69-page Draw.io master and matching full-package PDF, plus 24-page flow-only PDF, are revision 2.0 outputs and predate the Parent AI guide. They are historical snapshots; refresh only if the owner requests a new diagram/PDF package. EV-063-15 records their original hashes and QA. All 78 active target tables appear once; 48 legacy mappings remain separate.
- Product code/schema changes, database access, tests/builds, provider/payment/Modal calls, deployment and real-child data: not performed or approved.
- Working tree: documentation changes are limited to FEAT-063, the FEAT-062 retirement redirect/records, ADR-0021 and the global source-register pointer; unrelated existing changes were not modified.

## StoryRun-lite S1 checkpoint — 2026-11-02

- Goal: continuous approved S1→S2 implementation from `plan/STORYRUN_LITE_S1_S2_LAUNCH_PROMPT_20261102.md`; execution plan SHA-256 `225FAAEBD6186130214DF2523D0B4ACABEFCEB94C9C235048750430BBA8F1B09`.
- S1 overall: **NOT VERIFIED** pending a goal-owned PostgreSQL migration/transaction run and compatible ClamAV verification. Offline contract/domain/API/worker checks passed (38 tests), Ruff passed, and mypy passed (22 files). Windows Job Object process kill, limit readback and 40MP synthetic measurement passed; see `evidence/STORYRUN_LITE_S1_CHECKPOINT_20261102.md`.
- No PostgreSQL URL or usable local maintenance connection was available. No database was created or contacted beyond loopback maintenance probes; no A2 or application database was used. ClamAV is absent from PATH and no real `CLEAN` verdict was claimed.
- Per owner instruction, transition directly to S2 without another review gate. S2’s PG-backed bridge/receipt integration remains NOT VERIFIED until the environment gate is available.

## StoryRun-lite S2 checkpoint — 2026-11-02

- S2 implementation slice and offline contract checks are complete, but S2 readiness is **NOT VERIFIED**: five PostgreSQL-backed StoryRun-lite test cases skipped because no goal-owned loopback database could be created; ClamAV is unavailable. See `evidence/STORYRUN_LITE_S2_READINESS_20261102.md`.
- Final focused/A1 regression run: 118 passed, 5 skipped. Ruff, mypy, repository harness, architecture, security, and migration-graph checks passed. Bruno CLI execution was not run; static operation matching passed.
- Protected local changes: FEAT-061 and FEAT-064 baseline paths remain hash-identical. One unrelated FEAT-063 roadmap file differs from its initial captured hash and was retained untouched; overall 83-path preservation is therefore NOT VERIFIED. No changes were staged.
- Resume only after a local compatible ClamAV daemon and a create-capable local PostgreSQL configuration are available. Use a new owner-verified `storyrun_lite_*` DB, then run the StoryRun-lite branch and skipped integrations. Do not use A2 or any pre-existing application DB.

## StoryRun-lite final handoff — 2026-11-02

- S1→S2 implementation work is recorded in `evidence/STORYRUN_LITE_S1_S2_FINAL_20261102.md`. Overall acceptance remains NOT VERIFIED for the explicitly recorded ClamAV, PostgreSQL, Bruno CLI, and one unrelated baseline-hash discrepancy.
- Final scope snapshot: `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_20261102/`. No local A2 or FEAT-061 path changed; no database was created or used; the index remains clean.

## StoryRun-lite final continuation — 2026-11-02

- Goal: one continuous S1→S2 execution; this is not A2. The pinned launch-prompt SHA-256 matched. S1 and S2 technical/runtime gates are **VERIFIED** after creating and later cleaning only goal-owned loopback PostgreSQL/ClamAV/HTTP-stub resources.
- Final focused StoryRun-lite/A1 regression result: **125 passed, 0 skipped**. Ruff, mypy (14 source files), harness, architecture, repository-security, Alembic-current and `git diff --check` passed. Bruno CLI 4.3.0 passed all ten request files across main, cancel and abort flows.
- Strict overall acceptance is **NOT VERIFIED** because the initial 83-path comparison contains one unrelated FEAT-063 roadmap hash mismatch outside the allowlist. It was retained untouched. Three allowed FEAT-063 files contain only goal-scoped append records. All 35 FEAT-061/FEAT-064 protected paths, including A2 and the three FEAT-061 documents, remain byte-identical.
- The exact temporary goal databases and local service processes were cleaned up. No provider, stage, commit, push, merge or deployment occurred. Do not use the strict acceptance label `XONG-CHƯA REVIEW IMPLEMENTATION` while the baseline exception remains unresolved.


## StoryRun-lite SL-0/SL-8 owner-approved rebaseline — 2026-11-02

- The owner selected **B — Rebaseline 875**. The current roadmap bytes are accepted for that single path under an explicit exception; the original B881 hash remains historical and is not described as preserved.
- SL-0 and SL-8: **PASS WITH APPROVED REBASELINE**. The other baseline records remain 79 byte-identical paths, three approved append-only FEAT-063 paths, and 35/35 protected FEAT-061/FEAT-064 paths unchanged; no original path is missing.
- S1 and S2 technical gates were already verified. This documentation-only disposition changes no source, test, migration or roadmap content. The original snapshot remains unchanged; see the additive rebaseline evidence/snapshot.
- No A2 or FEAT-061 content was changed. Index remains unstaged; no commit/push/merge/deploy/provider/database operation occurred.


- Post-rebaseline checks: `validate_harness.py --feature ...` returned `HARNESS_VALID`; `git diff --check` exited 0 with CRLF normalization notices only. No tests were rerun because source/tests/migrations were unchanged.


## StoryRun-lite independent review fixes — three findings — 2026-11-02

- Status: **APPROVED / IN PROGRESS** under `plan/STORYRUN_LITE_S1_S2_REVIEW_FIX_3_FINDINGS_20261102.md`, SHA-256 `D68FFBC1F251E367797DCAD0C6252D08797EA7ED19CC35DC2033B906C9A09D47`; approval is appended in `approvals/TASK_APPROVAL.md` before source changes.
- Scope is limited to P2 upload/cancel concurrency and cleanup, P2 published expiry enforcement, and P3 runtime/OpenAPI response parity. Existing `ABORTED` and `EXPIRED` states are reused; no migration/schema change is planned.
- Preserve the existing S1→S2, A2, FEAT-061/FEAT-064 and roadmap rebaseline records and bytes outside the exact allowlist. Final fix status will be recorded after focused regression and validators.


## StoryRun-lite independent review fixes — implementation result — 2026-11-02

- Status: **FIXED — XONG-CHƯA REVIEW**. The two P2 lifecycle/expiry findings and one P3 OpenAPI/runtime parity finding are implemented under the approved narrow plan.
- Focused offline S1→S2/A1 regression: **126 passed, 9 skipped**; all nine skipped cases require the unavailable task-owned PostgreSQL database. The PostgreSQL race and expiry integration tests remain **NOT RUN**, so database-backed acceptance is not claimed.
- Ruff, mypy (three changed production files), harness, architecture, repository-security and `git diff --check` passed. Evidence: `evidence/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102.md`.
- The review-fix snapshot is additive at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/`. All 35/35 protected FEAT-061/FEAT-064 paths remain byte-identical; branch, HEAD and empty index are unchanged.
- Independent review is pending. No database/provider operation, stage, commit, push, merge or deploy occurred.


## StoryRun-lite review-fix hash-gate clarification — 2026-11-02

- The prior comparison used the pre-rebaseline S1→S2 snapshot (`6171A9…`); the owner-approved rebaseline snapshot is the applicable baseline and its `FC7ED78A…` hash matches the current final report and review-fix snapshot. The original snapshot remains unchanged as history.
- Status remains **FIXED — XONG-CHƯA REVIEW**. PostgreSQL integration tests remain **NOT RUN**; independent review is pending.


## StoryRun-lite independent review — round 2 implementation — 2026-11-02

- Status: **FIXED — XONG-CHƯA REVIEW**. Round-2 P2 lock-wait expiry, P2 cancel/admission race and P3 OpenAPI/runtime parity changes are implemented under the same approved scope.
- Focused offline S1→S2/A1 regression: **135 passed, 15 skipped**. All skipped cases require the unavailable task-owned PostgreSQL database; PostgreSQL expiry and race acceptance remain **NOT RUN**.
- Ruff, mypy (two changed production files), harness, architecture, repository-security and `git diff --check` passed. Detailed test commands and limitations are in `evidence/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102.md`.
- Standalone StoryRun-lite API runner was **NOT RUN** because no safe task-owned DB could be created or verified. The previous review-fix snapshot, plan, approval, final report, roadmap, A2 and FEAT-061/FEAT-064 files remain preserved.
- Round-2 snapshot was captured additively at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/ROUND2_20261102/`. All 35/35 protected FEAT-061/FEAT-064 paths match their prior snapshot hashes. Independent review is pending; no stage/commit/push/merge/deploy occurred.


## StoryRun-lite independent review - round 3 P3 OpenAPI persisted errors - 2026-11-02

- Status: **FIXED — XONG-CHƯA REVIEW**. OpenAPI `Error.code.enum` now covers all 17 StoryRun and 17 UploadSession runtime codes traced through the production GET projections, including `VISION_LOOPBACK_NOT_CONFIGURED` and `MODEL_INPUT_TOO_LARGE`; the enum remains closed.
- Added a contract test that exercises both GET routes using the repository error projection and verifies their response schemas and every enumerated runtime code against OpenAPI. Focused contract tests: **20 passed**; Ruff and OpenAPI JSON parsing passed.
- Harness, repository-security, architecture and `git diff --check` passed. Mypy returned an internal error (1.20.2), so no type-check verdict is claimed.
- PostgreSQL tests and the DB-backed runner remain **NOT RUN**; no task-owned DB URL was set and no database was touched. No Modal/GPU/provider/external-network call was made.
- Additive snapshot: `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/ROUND3_20261102/`. Branch `feature/feat063-be-foundation`, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, index empty; all 35/35 protected FEAT-061/FEAT-064 paths remain hash-identical. Independent review is pending; no stage/commit/push/merge/deploy occurred.


## StoryRun-lite independent review - round 4 projection test strengthening - 2026-11-02

- Status: **FIXED — XONG-CHƯA REVIEW**. Only the approved contract test and append-only evidence/status records changed; OpenAPI and production source remain unchanged.
- Added separate GET StoryRun and GET UploadSession tests using the real `StoryRunLiteService` and `SqlStoryRunLiteRepository` projections. Fake rows carry saved error codes; the fake UploadSession connection returns no parts. Each HTTP response code is checked against the row and OpenAPI `Error.code.enum`. Runtime code inventory coverage remains.
- Focused contract suite: **22 passed**; Ruff, harness, repository-security, architecture and `git diff --check` passed. Mypy 1.20.2 returned an internal error without a verdict.
- PostgreSQL tests/runner **NOT RUN**; task-owned DB URL and other database URLs were unset. No database or provider/network operation occurred.
- Additive snapshot: `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/ROUND4_20261102/`. Branch `feature/feat063-be-foundation`, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, index empty; protected FEAT-061/FEAT-064 paths and prior snapshots are preserved. Independent review round 4 is pending; no stage/commit/push/merge/deploy occurred.


## StoryRun-lite review round 4 verdict recorded - 2026-11-02

- The owner reports independent review **ACCEPTED** for the P3 production GET projection tests in round 4. This closes that review finding only; runtime verification is still pending.
- PostgreSQL tests remain **NOT RUN** at this point. Mypy 1.20.2 returned an internal error and has no verdict. The immutable S1-S2 plan and its Modal/provider boundary remain unchanged.
- Additive checkpoint snapshot: `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_RUNTIME_VERIFY_20261102/STEP1_REVIEW_ACCEPTED_20261102/`. No database/provider call, stage, commit, push, merge or deploy occurred.


- Snapshot correction note: two preliminary step-1 captures were retained unchanged but are non-authoritative due to inventory defects. The upcoming `STEP1_REVIEW_ACCEPTED_FINAL_20261102` capture is the authoritative checkpoint with the complete Git-visible inventory and task-scoped snapshot list.


## StoryRun-lite runtime verification - PostgreSQL gate blocked - 2026-11-02

- Review round 4 P3 verdict remains **ACCEPTED**. Runtime verification is blocked at PostgreSQL: all three DB URL variables are unset; PostgreSQL 17/18 services exist but no task-owned connection/owner could be verified. No existing database was contacted or used.
- PostgreSQL integration test command: **0 passed, 0 failed, 12 skipped**; the fixture skipped before connecting because `STORYRUN_LITE_DATABASE_URL` was unset. This does not verify database behavior.
- Per the stop rule, Bruno and Modal steps are **NOT RUN**; Modal invocation count is **0**. Mypy still has no verdict from the prior 1.20.2 internal error.
- Additive blocked-gate snapshot: `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_RUNTIME_VERIFY_20261102/STEP2_DATABASE_GATE_BLOCKED_20261102/`. No source/UI change, database/provider/network call, stage, commit, push, merge or deploy occurred.

## StoryRun-lite runtime verification closeout - 2026-11-02

The post-review execution record is `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_POST_REVIEW_RUNTIME_VERIFY_20261102.md` (SHA-256 `7BF55D4B95F8E3887502DC2889BC50D1F531DA172AC4465AAF32CB3DC8E74807`). Its final additive snapshot is `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_RUNTIME_VERIFY_20261102/STEP2_DATABASE_GATE_BLOCKED_CLOSEOUT_20261102/`, captured against the previous database-gate checkpoint and including the plan plus final evidence/status. Earlier snapshots remain unchanged.

Runtime verification is **BLOCKED** at the PostgreSQL task-owned database gate: 0 passed, 0 failed, 12 skipped before connection. Bruno and Modal are **NOT RUN**; Modal invocation count is 0. The P3 implementation remains **FIXED — XONG-CHƯA REVIEW**; this does not claim runtime completion. No source, database, provider, or external-network operation occurred.
## StoryRun-lite PostgreSQL owner assertion — 2026-11-03

- The owner-approved test-only change compares the verified owner to both PostgreSQL `current_user` and the real database owner; runtime source and migration are unchanged. Independent review remains pending.
- On a newly created task-owned PostgreSQL 17.11 loopback DB with owner/user `postgres`, the pre-Story migration synthetic legacy Organization fixture was created and verified in order. The full integration file returned **12 setup errors, 0 passed, 0 failed, 0 skipped**, before test bodies, because pytest could not access its default local temporary directory. See `evidence/STORYRUN_LITE_POSTGRES_OWNER_20261103.md` and its sanitized pytest log.
- PostgreSQL gate **NOT VERIFIED**; Bruno and ClamAV/worker readiness **NOT RUN**. The exact task cluster was stopped and preserved; no Modal/provider invocation or stage/commit/push/merge occurred.
## StoryRun-lite PostgreSQL suite on existing loopback service — 2026-11-03

- New task DB `storyrun_lite_e4eb465c9dd34d75be56`, PostgreSQL 17.11 `127.0.0.1:5433`, user/owner `postgres`: verified. The synthetic legacy Organization asset was committed before the StoryRun-lite migration and verified afterwards.
- Full 12-item suite: **5 passed, 2 reported failed, 1 interrupted at timeout, 4 not run**. The owner assertion and both legacy tests passed. The runner killed the test process tree at 600 seconds while the expiry lock-wait `[get]` case was running; pytest did not produce tracebacks for the two earlier race failures. PostgreSQL gate **NOT PASSED**.
- See `evidence/STORYRUN_LITE_POSTGRES_5433_20261103.md` and its sanitized output. The task DB is retained. Bruno and scanner/worker readiness are **NOT RUN**; no Modal/provider call, stage, commit, push or merge occurred.
## StoryRun-lite PostgreSQL diagnostics — 2026-11-03

- The two race cases were rerun separately: both **FAIL**, with tracebacks showing unset coordination events at test lines 792 and 800. The expiry lock-wait `[get]` case was **TIMEOUT** after 75 seconds; its 20-second thread dump shows a DB worker in `_owned_run` and the main thread waiting for executor shutdown.
- The test hooks look for `story_runs`, whereas the compiled PostgreSQL lock query uses `story.runs`; see `evidence/STORYRUN_LITE_POSTGRES_5433_DIAGNOSTICS_20261103.md` and the sanitized trace/dump log. A narrow test repair is proposed, not applied. Production race behavior and full suite remain unverified.
- No source, test or migration was edited in this diagnostic; no DB was reset or deleted, Bruno and Modal were not run, and no stage/commit/push/merge occurred.
## StoryRun-lite PostgreSQL coordination test-only fix — 2026-11-03

- Owner-approved test changes recognize `story.runs` lock SQL and release blocking events/transactions before executor shutdown; runtime source and migrations are unchanged. Independent review is pending.
- Nine individually bounded focused cases on the verified task DB: **7 passed, 2 failed, 0 skipped, 0 timed out**. Both admission/cancel races and all three expiry lock-wait variants passed. Recovery lock-wait counted three expired sessions instead of one; startup cleanup found the parts directory absent after the injected failure. Reused DB state is a possible factor, not a proven cause.
- Full PostgreSQL suite, ClamAV/worker and Bruno **NOT RUN** because focused tests did not all pass. See `evidence/STORYRUN_LITE_POSTGRES_COORDINATION_FIX_20261103.md` and its sanitized traceback log. No database reset/delete, Modal/provider, stage, commit, push or merge occurred.
## StoryRun-lite recovery diagnosis on fresh databases — 2026-11-03

- Both recovery cases passed separately, each on a newly provisioned PostgreSQL 17.11 task DB with a legacy synthetic asset seeded before StoryRun-lite migration. On a third fresh task DB, nine sequential focused cases returned **7 passed, 2 failed, 0 skipped, 0 timed out**; the same two recovery tests failed after the preceding cases accumulated state.
- The recovery code scans DB-wide rows while the tests use per-test quarantine paths and exact global counts/first-call injection. This explains a possible interference mechanism; the specific prior rows were not independently enumerated. Production correctness is not established. See `evidence/STORYRUN_LITE_FRESH_RECOVERY_20261103.md` and its sanitized log.
- Full suite, ClamAV/worker and Bruno **NOT RUN** because the focused gate failed. Three new task DBs were retained, no existing DB reset or deleted. No source/test/migration changes, Modal/provider calls, stage/commit/push/merge occurred.
## StoryRun-lite recovery test independence — 2026-11-03

- Test-only change computes exact DB-wide recovery candidates and verifies the test-created upload independently; the injected cleanup failure targets that upload and its retry is asserted. Runtime source and migrations remain unchanged.
- Two recovery cases passed individually on separate new PostgreSQL 17.11 task DBs; focused **9 passed, 0 failed, 0 skipped**; full PostgreSQL integration file on a fourth fresh DB **12 passed, 0 failed, 0 skipped**, no timeout. All had synthetic Organization fixture committed before StoryRun-lite migration.
- Worker synthetic suite **18 passed, 0 skipped**, including Job Object limits/kill and 40 MP. Real ClamAV and configured loopback Vision stub **NOT VERIFIED**; Bruno flow **NOT RUN**, Modal/provider invocation **0**. See `evidence/STORYRUN_LITE_RECOVERY_ISOLATION_20261103.md` and sanitized log. Local Parent flow remains blocked; independent review of the test changes is pending.
- Task DBs were retained; no existing DB reset or deleted, no stage/commit/push/merge.
- Type-check update: mypy on the integration test file returned **25 errors**; Ruff, harness, repository security, architecture and `git diff --check` passed. No clean mypy verdict is claimed.
## StoryRun-lite local readiness and mypy classification — 2026-11-03

- PostgreSQL **12 passed** and worker synthetic suite **18 passed** remain the previously recorded results; not rerun. Real ClamAV and Vision loopback stub are **NOT VERIFIED** in the current environment, so synthetic CLEAN/EICAR INFECTED, API startup and Bruno flow are **NOT RUN**. No Modal/provider call occurred.
- Mypy comparison using the same mypy 1.20.2/config on hash-verified pre-recovery-isolation and current test bytes: **24 existing, 1 new, 0 unclassified**. The new `no-untyped-def` concerns nested `ControlledDateTime.now` in the startup recovery test. Mypy is not clean; see `evidence/STORYRUN_LITE_LOCAL_READINESS_MYPY_20261103.md`.
## StoryRun-lite local Bruno flow — 2026-11-03

- Real ClamAV 1.5.4 with official signatures returned **CLEAN** for synthetic image and **INFECTED / CLAMAV_FOUND** for in-memory EICAR. A task-local fake Vision stub passed V2 HTTP/schema/bridge verification; this is not live AI inference.
- On a new owner-verified PG17 task DB, Bruno **9 requests / 9 tests passed**: upload READY, run SUBJECT_REVIEW, confirm 202 and post-confirm GET PREPARATION_REVIEW. An initial attempt on the prior test DB returned 409 `ACTIVE_RUN_EXISTS`; the DB/run were preserved. See `evidence/STORYRUN_LITE_LOCAL_BRUNO_20261103.md` and sanitized summary JSON.
- The single new test mypy diagnostic was fixed. Targeted recovery **1 passed**, Ruff passed; mypy now reports **24 baseline errors**, not clean. Previous full PostgreSQL suite **12 passed** and worker **18 passed** were not rerun in full for this type-only fix.
- Temporary API, ClamAV and fake Vision processes were stopped and listeners absent; PostgreSQL services remain running. No Modal/provider call, stage/commit/push/merge/deploy occurred. New task DB was retained; its generated name was printed in the helper console but not captured in the task log.
## StoryRun-lite guarded Modal integration — 2026-11-03

- Explicit, run-bound live configuration implemented; default loopback retained. Offline bridge/A1 tests **78 passed**, PostgreSQL loopback regression **3 passed**, worker **18 passed**. Real ClamAV returned CLEAN for the selected synthetic image and INFECTED for EICAR. Mypy on the two source files returned **2 repository/port mismatch errors**, not a clean verdict.
- **LIVE BLOCKED / NOT RUN**: the owner reports no active Modal endpoint. Live inference requests **0**; the required new task-owned live DB and live Parent flow have not run. See `evidence/STORYRUN_LITE_MODAL_LIVE_20261103.md`. The task scanner was stopped after its check; readiness must be established again before a future live attempt. No deployment, stage, commit, push or merge occurred.
## StoryRun-lite temporary Modal serve — 2026-11-03

- A new isolated PG17 task DB and synthetic upload reached **READY**; real ClamAV returned CLEAN/EICAR INFECTED. Bootstrap stopped before attach. The temporary Modal serve endpoint's **GET /health timed out after 100 s**; direct DNS/TLS succeeded, app had 0 tasks, and no app logs were returned. Cause remains undetermined.
- The bridge now accepts valid regional Modal hostnames; bridge/A1 tests **83 passed**, Ruff and security passed. Mypy remains **2 repository/port arg-type errors**; the underlying mismatch predates live integration and its port fix is outside the approved scope.
- **LIVE BLOCKED / NOT RUN**, inference requests **0**, no confirmation or live ledger result. App and task-owned local processes were stopped. See `evidence/STORYRUN_LITE_MODAL_TEMP_SERVE_20261103.md`; no existing DB reset, persistent deployment, stage, commit, push or merge.
## StoryRun-lite one-request Modal live smoke — 2026-11-03

- New temporary app health **200**; one synthetic Parent flow via BE/A1 sent exactly **one Modal inference POST**, HTTP **200**, Vision **SUCCEEDED**. Attach **202**, GET **SUBJECT_REVIEW**, confirm **202**, subsequent GET **PREPARATION_REVIEW**; ledger **SUCCEEDED**. See `evidence/STORYRUN_LITE_MODAL_LIVE_SUCCESS_20261103.md` for timing and limits.
- Cleanup return contract corrected to `bool` after caller/implementation review. Focused **104 passed**, mypy on the two live source files and new test **passed**; no whole-repository clean claim. Real ClamAV CLEAN/EICAR INFECTED. The prior health timeout cause remains unknown.
- App and task-owned temporary processes were stopped; task DB retained. No persistent deploy, stage, commit, push or merge. This live smoke is not independent review or production approval.
## StoryRun-lite main BE integration — 2026-11-03

- Local synthetic StoryRun routes/lifecycle are opt-in in the combined main app, guarded to loopback. Lesson and StoryRun upload tables are separated with verified migration compatibility. The clean/lesson-first/story-first/unknown-shape matrix passed; StoryRun PG **12 passed**, loopback **3 passed**, Lesson **6 passed**.
- Owner-authorized empty `sketch2life` on PG17 loopback 5433 passed preflight and `upgrade heads`; main BE synthetic upload READY and one Modal inference returned **200 / SUCCEEDED**. Attach 202, SUBJECT_REVIEW, confirm 202, PREPARATION_REVIEW; ledger SUCCEEDED. Modal inference HTTP requests **1**.
- Temporary app/processes stopped, DB and synthetic run retained. UI handoff: `artifacts/storyrun-lite/MAIN_BE_UI_HANDOFF_20261103.md`; evidence: `evidence/STORYRUN_LITE_MAIN_BE_INTEGRATION_20261103.md`. Local demo only; independent review and production identity remain open. No A2 change, stage, commit, push, merge or permanent deploy.

## Milestone 1 review round 1 fixes — 2026-11-03

**FIXED — XONG-CHƯA REVIEW** for six independent-review findings. Offline: 163 passed, 1 skipped (real PG test, exercised separately). PG17 task-owned loopback: 36 passed, no skips or timeouts. Ruff/mypy and final validators are recorded in `evidence/MILESTONE1_REVIEW_FIX_REPORT_20261103.md`. Parent HTTP repeat/replay and ledger transition races were exercised with synthetic scanner/normalizer and loopback Vision. Bruno CLI, real ClamAV/worker repeat demo and Modal live after fixes are NOT RUN. No stage/commit/push/merge. M2 is not started; A2 remains preserved.

## Milestone 1 review round 2 fixes — 2026-11-03

**FIXED — CHỜ REVIEW ĐỘC LẬP; NOT ACCEPTED.** Closed the two new P2 findings (attach-replay TOCTOU and public readiness after singleton loss) and added the requested cancel/create, duplicate/stale cancel, probe-concurrency, and terminated-session coverage. Final offline regression: **170 passed, 1 PostgreSQL-dependent skip**. Isolated PostgreSQL 17.11: **46 passed, 0 failed, 0 skipped, 0 timeout**. Bruno with real ClamAV and Windows Job Object normalizer: **two synthetic runs, 11/11 requests and tests in each**, Vision loopback stub only. Ruff check/format, five production-source mypy modules, harness, security, architecture and diff-check passed. Modal/GPU/provider and full BE/A2 regression were NOT RUN. The 55 pre-existing A2 paths match their preserved bytes. Branch/HEAD unchanged, index empty; no stage/commit/push/merge. See `evidence/MILESTONE1_REVIEW_ROUND2_FIX_REPORT_20261103.md`; round-3 independent review is still required.

## Milestone 1 independent review round 3 — 2026-11-03

**ACCEPTED** for the synthetic local demo scope. The independent reviewer accepted all six round-1 findings and both round-2 P2 findings after checking source, tests, contracts, handoff and evidence; all 38 snapshot paths matched at review time. Recorded verification remains 170 offline passed/1 PostgreSQL-dependent skip, 46 PostgreSQL passed, and two Bruno runs at 11/11 requests/tests each. The reviewer did not rerun tests. Vision was a loopback stub; no post-fix Modal/provider call or production readiness is claimed. Review evidence: `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND3_20261103.md`. Mốc 2 remains unstarted.


## Full BE Bruno collection — 2026-11-03

**COLLECTION TASK COMPLETE — COVERAGE, BRUNO PARSE, AND LIMITED SAFE SMOKE PASS; DB-BACKED ROUTES NOT RUN.** Generated a separate 136-request collection for the current runtime union (122 paths) and a 147-row coverage CSV (136 mounted + 11 unmounted candidates excluded from requests). Profile counts: combined default 122, combined + StoryRun-lite 133, combined + optional local storage 125, classroom 57, demo 35. Custom one-to-one/safety validator, Ruff check/format, harness, repository security and architecture validators pass. Bruno CLI 4.3.0 parsed and documented all 136 request names. Safe loopback smoke passed `GET /health` 200, process-local synthetic `POST /v1/sessions` 201, and `GET /v1/sessions/{session_id}` 200 with AI disabled and no DB URL. Bruno reported 0 tests and assertions; status codes were checked from CLI and Uvicorn output. DB-backed BE1/Lesson Library routes and StoryRun-lite runtime were NOT RUN. The MCP request-list tool does not discover the new path. The existing StoryRun-lite collection was not edited; its six Milestone 1 closeout-manifest paths still match. Mypy returned an internal error (no verdict). No DB/Modal/provider call. The owner later authorized separate local commits for accepted M1 fixes and this collection; generator/validator scripts are excluded from the collection commit. No push or merge is part of this closeout. M1 remains ACCEPTED for synthetic local demo scope; M2 is not started. Details: evidence/BE_FULL_BRUNO_COLLECTION_REPORT_20261103.md.
