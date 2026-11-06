# FEAT-063 — Whole-repository architecture redesign


## As-built SRS alignment — Plan Rev43 (2026-11-06)

- Lifecycle: REVIEW; SRS v2.4-draft and matching Data Table Register add a current implementation snapshot without replacing the v2.3 target requirements.
- Canonical SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.4-draft, unsigned. §32 distinguishes backend code, mounted API, local database and Modal dashboard observations from target behavior.
- Read-only snapshot: local OpenAPI 111 paths / 124 operations; local PostgreSQL Alembic `20261028_ll_0001`, 41 application tables (34 `public`, 7 `lesson`). Full table list and AI/database access boundary are in EV-063-33 / Data Table Register §§14.5–14.6.
- AI clarification: owner selected Qwen3.5-VL, FLUX.3, Whisper, optional SAM 2.1, with Modal as the inference-host direction; Q159 is resolved as Platform Admin + Teacher may initiate AI suggestions, Parent may edit authorized drafts only. Deployment and backend integration are separately qualified.
- No requirements were deleted; API and database checks were read-only; no database writes/migrations or AI-provider calls were made for this amendment. The SRS remains unsigned. Approval: Plan Rev43 hash is recorded in root and feature approval registers.
- Evidence: `evidence/EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md`.


## B3 ownership manifest and owner decision slip — 2026-10-31

B3 produced a documentation-only ownership, shared-file and migration-order manifest (`evidence/B3_OWNERSHIP_MIGRATION_MANIFEST_20261031.md` and `evidence/B3_OWNER_MATRIX_20261031.csv`): 18 source boundaries, 18 shared-file/migration rows, every co-signature `CHƯA KÝ`, and a static Alembic count of 22 revisions with 10 terminals by `down_revision` only or 9 when `depends_on` is counted. Migration options X/Y/Z, writers and signatures were left to the owner.

The owner's decision slip (`evidence/OWNER_DECISION_SLIP_20261031.md`) records the answers: BE2 = Person 2 as a FEAT-064-scoped exception to ADR-0015; migration option X with the BE1 owner owning the synthetic-origin schema; `OwnerFenceV1` needs the BE1, BE2 and integration owners' signatures; pilot before Rev36; no temporary database yet; and Q2-Q8 of the B2 Parent-activity decision are now decided (option A). The slip is not an approval for FEAT-064, Rev36 or B2A, and signs nothing. The 16 B1 rows stay `blocked_by=B2` until the source is amended under its own approval.

## B2 Parent activity ordering - 2026-10-31

- B2 reviewed 225 source passages: POST_VIDEO 26, PRE_VIDEO 9, TEACHER_PRE_VIDEO 82, NEUTRAL 81, AMBIGUOUS 27.
- Owner selected A for Q1 only; Q2-Q8 remain unconfirmed working assumptions.
- B2A amendment plan is DRAFT / AWAITING_APPROVAL; 42/45 proposed edits remain owner-gated, none applied.
- B1 rows T018-T031, T046 and T047 remain blocked_by=B2.
- No SRS or Data Table Register source was changed; B2 does not block the FEAT-064 pilot.

## B0 baseline and B1 API crosswalk — 2026-10-30

B0a is complete: offline OpenAPI snapshots of the current backend (`combined` profile, 121 operations with the storage example off and 124 with it on) match the 124 mounted rows of catalog Rev37 on method/path, parameter names and 2xx codes; the 11 candidate/fixture rows are absent. B0b stays open: the catalog's `EV-063-30` OpenAPI JSON and verification report were not found on local disk, in any Git ref, on GitHub or in agent logs, so Rev37's historical commit, profile and runtime results are unverified. See `evidence/B0_CLOSEOUT_20261030.md`.

B1 produced a 192-row crosswalk (135 catalog rows plus 57 target rows from SRS 2.3 and the FEAT-064 pilot outline) in `evidence/B1_API_CROSSWALK_20261030.md` and `.csv`. All dispositions are proposals; evidence levels E0-E3 never mean a route passed. Twelve S1 fence candidates are also needed by the pilot, 16 rows wait on B2 (Parent activity ordering) and 23 low-confidence rows need owner answers. The B1 approval entry is recorded in `approvals/TASK_APPROVAL.md` after the work was done. Documentation only; no code, database, MinIO, Modal or GPU operation. Pilot FEAT-064 remains the owner's chosen first track (D-01) but is unapproved, and backend Rev36 is still awaiting approval.

## Dev backend synchronization — 2026-10-30

Owner requested the latest dev backend in this feature branch for testing. Incoming tip `111ae547` adds existing Lesson Library/BE1 fixes and upstream evidence/UI drafts; Modal remains present. Revision numbers overlap across independent backend and UI/API work: use exact plan filenames and hashes for authority. Upstream UI Rev36 approval does not approve backend Rev36. See `evidence/notes/DEV_BACKEND_SYNC_20261030.md` for actual checks and limitations.

## Remaining AI-stage candidates — 2026-10-30

Owner asked for line-sketch, consistency and safety model proposals compatible with the discussed dev model set. Research and limits are in `evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md`; no canonical SRS, approved plan or runtime model changed. Existing NO_GO and synthetic evaluation gates remain.

## Video comparison; task allocation deferred to backend team — 2026-10-30

Owner requested the backend team handle allocation, steering this session to a read-only comparison. `evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md` distinguishes source legacy video paths from the SRS target and SRS 2.2 → 2.3 continuity. No S1 implementation approval, provider execution or new task assignment is inferred.

## Current-machine S1 preparation — 2026-10-30

Owner resumed work on this machine. Rev36's three P3 corrections received a bounded independent DELTA_REVIEW_PASS. `plan/S1_DECISION_CARD_20261030.md` proposes 24 blocked and five preserved operations during a preparatory fence, with explicit read-only cutover and ownership gates. It is not approved; no product code or existing approval changed. See `evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md`.

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

## Swagger review and local commit — Plan Rev42 (2026-10-30)

- Lifecycle: review and verification complete for the approved local commit scope. No push is authorized.
- Plan Rev42 SHA-256: `E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8`.
- The full pending Swagger/OpenAPI diff was reviewed. Local and served OpenAPI match at 124 operations, 111 paths, 18 tags and 11 unmounted candidates. A request-ID reflection issue in typed 413 middleware was fixed and regression-checked.
- Five focused tests, Ruff, compile, exporter, live snapshot parity, plan hash checks, whitespace check and required repository security validation passed. Evidence: `evidence/EV-063-34_SWAGGER_REVIEW_AND_COMMIT_20261030.md`.

## Rev41 Swagger overview presentation — 2026-10-30

- Lifecycle: COMPLETE for the approved Swagger overview-copy scope. Plan Rev41 SHA-256: `8693C3B4165F9413775306260CCC9023404F2AB7F58C967632236951B1FC2BDB`.
- The info block now uses a short intro and labeled coverage, Try it out/authentication, and unmounted-candidate notes instead of one long paragraph.
- The API surface is unchanged. The served local OpenAPI matches the regenerated snapshot: 124 operations, 111 paths, 18 tags, 11 unmounted candidates. `/docs` and `/openapi.json` returned 200.
- Snapshot SHA-256: `C1F2B453E5D893AF5328C9091A51B183CB2D67FED2587411C0D45598F47A9466`. Evidence: `evidence/EV-063-33_SWAGGER_INFO_PRESENTATION_20261030.md`.

## Rev40 local Swagger QA kit — 2026-10-30

- Lifecycle: COMPLETE for the approved synthetic local QA and upload 413 parity scope. Plan Rev40 SHA-256: `701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9`.
- The local Swagger page now provides a runnable in-memory create-session/image-upload example and a deterministic synthetic PNG. TestClient returned session HTTP 201/version 0, then image HTTP 200/`ADMITTED`/version 1 with external AI disabled.
- Oversized image/audio responses now match the Rev37 `MobileWorkflowResultV1` schema. Focused tests: 4 passed; exporter, Ruff, compile and whitespace checks passed.
- Current snapshot: `artifacts/OPENAPI_FEAT063_REV37_20261030.json`, SHA-256 `70BDA49D2E122C4CE0370211DCEF8EA03BEC477CFDE2C60673501EB2CCDF8208`. Live loopback `/docs` and `/openapi.json` return 200 with 124 operations, 111 paths and 18 tags.
- The local Demo flow is ready for interactive Swagger testing. Protected Lesson Library/BE1 operations are not yet interactive-test-ready because this setup has no configured Firebase Auth Emulator/test token or disposable BE1 database URL. No fake credential path was added. See `artifacts/LOCAL_SWAGGER_QA_QUICKSTART_20261030.md` and `evidence/EV-063-32_LOCAL_SWAGGER_QA_KIT_20261030.md`.

## Rev39 professional Swagger navigation — 2026-10-30

- Current Swagger groups 124 mounted Rev37 operations into 18 descriptive tags. Lesson Library tags follow explicit Teacher, School Manager, Parent, Platform Admin, shared-staff, and upload-owner guards; remaining APIs use BE1/Demo domain groups.
- All 11 candidate routes remain unmounted; request/authentication/response parity and the Rev38 413 discrepancy record are preserved. Tags are navigational and do not change authorization.
- Approved Plan Rev39 SHA-256: `1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F`.
- Current snapshot: `artifacts/OPENAPI_FEAT063_REV37_20261030.json`, SHA-256 `27BB19AC8A5938D239A300DB4BFC5028AA205A675AE9B09EE00CCD35CB3D3453`.
- Focused Swagger parity: 2 passed; snapshot exporter passed; the local `/docs` server was restarted. Evidence: `evidence/EV-063-31_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`.

## Rev37 contract-aligned Swagger/OpenAPI — Plan Rev38 (2026-10-30)

- Lifecycle: COMPLETE for the Swagger/OpenAPI documentation scope; the upload body-limit payload mismatch is recorded as an outstanding API/test defect, not concealed or behavior-fixed here.
- Approved Plan Rev38 SHA-256: `C1E8C74AD57E7F053E0D1E093BAF7F97BE6F12E8EF8887A2C098632B9B863BCF`; source contract SHA-256: `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- `/docs` and `/openapi.json` expose 124 mounted Rev37 operations across 111 local-profile paths; 11 candidate/fixture operations remain unmounted and are recorded with exact metadata. Request inputs, security, response codes/media/schemas, descriptions, handlers and verification status are reconciled against the contract.
- Snapshot: `artifacts/OPENAPI_FEAT063_REV37_20261030.json`, SHA-256 `A45748B8715F1934BED86F89795F71C3559CD0E2122140EC3D346194E9B2F9F5`. Focused Swagger test: 2 passed; exporter parity validation passed.
- Known mismatch: oversized audio/image upload transport responses use the middleware's generic `REQUEST_TOO_LARGE` payload, while the contract declares `MobileWorkflowResultV1`; the existing image-cap regression expects a third payload shape and fails. Swagger documents both observed/declared shapes. No API behavior changed. See EV-063-30.
## Swagger commit consolidation — Plan Rev46 (2026-11-01)

- The owner authorized replacing the two tip Swagger commits with one consolidated commit and updating `origin/dev` by force-with-lease. Exact old tip `6d77d2ad` and parent Swagger commit `f68ed2b5` are replaced on `dev`; merge parent `111ae547` is retained.
- Remote `origin/dev` was verified at `6d77d2ad` before history work. Plan Rev46 SHA-256: `4EE5DEF1E5AD7C544BBCF79921E8A7495EDE79C7765AE523D38BFFA1D9938B27`.
- The new commit retains the current SRS v2.2 FE Swagger tree and records the exact deletion/replacement scope. Other refs are excluded.
- Plans Rev47–48 remove superseded snapshots, local-demo artifacts, and standalone Swagger revision notes before the current-only commit is amended; the Rev45 SRS v2.2 snapshot and evidence remain.

## FE Swagger SRS v2.2 scope — Plan Rev45 (2026-11-01)

- The owner selected SRS v2.2 as the baseline for this Swagger update. The source SRS remains a draft; this task does not sign it off.
- Swagger now publishes an explicit FE projection of 24 currently mounted operations across 17 paths and four navigation tags. The full 124-operation mounted schema remains available in app state for internal contract parity; backend routes and behavior are unchanged.
- The FE view includes organization/class/profile/consent and Teacher lesson preparation/upload. It omits classroom collaboration, gallery, local/demo/storage, sharing, moderation, and health operations. It states that Parent StoryRun, activity catalog, occurrence/Sketch Deck/sample-video, playback/job, billing/quota, and notification APIs are not available here.
- SRS §9.6 is a logical route proposal, not the final API contract. Plan Rev45 SHA-256: `5D1DBABE161F92F08DE7FE8C1B81B1E5D57CFA3C2B8D57CBA6BE76ACADB0FD06`; approval is recorded in `approvals/TASK_APPROVAL.md`.
- The FE view labels the shared error envelope `ApiError`; its fields and payload remain unchanged. The overview is 50 words and each tag description is at most seven words. Snapshot `artifacts/OPENAPI_FEAT063_REV45_20261101.json`, SHA-256 `C61D3ADD7FF906AC9E5B018A9CE428AF7B162D67510FEEE7B202B53DA05D74A2`. Live parity is recorded in evidence. No test suite was run. Evidence: `evidence/EV-063-37_SWAGGER_SRS_V22_SCOPE_20261101.md`.

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

## StoryRun-lite S1→S2 implementation context — 2026-11-02

- The approved synthetic Parent demo is an isolated local API with a Core/Story persistence slice, 10-operation OpenAPI/Bruno handoff, bounded upload/quarantine and image normalization, and S1 fake Vision. S2’s photo bridge is limited to the existing A1 ledger/guard/HTTP JSON transport and literal HTTP loopback.
- S1 offline tests pass, including one/two/five contiguous upload parts, exact size bounds, scanner-before-decoder fail-closed branches, JPEG/PNG/WebP validation, multi-frame rejection, 40MP normalization, and Windows Job Object kill/limit measurements. Evidence is in `evidence/STORYRUN_LITE_S1_CHECKPOINT_20261102.md`.
- Overall S1 and S2 readiness are not complete: compatible ClamAV is unavailable and PostgreSQL could not be reached with a goal-specific URL/owner. The runtime remains fail-closed if ClamAV or Vision loopback is unconfigured. Do not report production readiness or a real scanner CLEAN result.
- A2 and FEAT-061 local changes remain protected by the initial change baseline. No Modal, GPU, remote provider, external inference, real child data, or pre-existing database was used.

## StoryRun-lite S2 readiness — 2026-11-02

- S2 route and bridge wiring are statically validated: the 10 OpenAPI operations, runtime router and Bruno request paths match; V2 bridge traffic can target only literal HTTP loopback and goes through the existing A1 guard, ledger, transport and adapter.
- Story result persistence precedes ledger terminalization. Raw response and canonical result hashes are separate. Tests cover loopback success, refusal, race, HTTP status failures, reset, timeout, invalid response, recovery and cancel/late CAS, but those five PostgreSQL-backed cases were skipped because no goal-owned database could be established.
- 118 focused StoryRun-lite/A1 regression tests passed; 5 database-dependent cases skipped. Ruff, mypy, harness, architecture and repository-security validators passed. Bruno CLI was unavailable; static operation matching passed.
- Overall readiness remains NOT VERIFIED until local ClamAV and the approved disposable PostgreSQL setup are available. The FEAT-061/FEAT-064 protected baseline hashes remain unchanged; one unrelated FEAT-063 roadmap hash changed during the session and was retained untouched. See the S2 readiness evidence for exact hashes and resume steps.

## Final StoryRun-lite handoff — 2026-11-02

- The approved S1→S2 implementation and handoff are recorded in `evidence/STORYRUN_LITE_S1_S2_FINAL_20261102.md`; overall acceptance is NOT VERIFIED because ClamAV and the goal-owned PostgreSQL run were unavailable. The worker/CPU/memory gate, offline contracts, A1 regression tests, harness, architecture and security checks passed.
- A2 and the three FEAT-061 local documents remain unchanged. One unrelated FEAT-063 roadmap baseline hash discrepancy was detected and preserved as found; inspect it before claiming the full original workspace baseline is unchanged.

## StoryRun-lite final continuation — 2026-11-02

- The earlier pending ClamAV/PostgreSQL/Bruno gates were resolved with temporary goal-owned loopback resources. Final focused S1/S2 and A1 regression result: 125 passed, 0 skipped; real ClamAV, PostgreSQL migration/transactions, loopback bridge/recovery and all ten Bruno request files were exercised. See the final S1 checkpoint, S2 readiness, environment and handoff addenda.
- S1 and S2 technical/runtime gates are VERIFIED. Strict end-to-end acceptance remains NOT VERIFIED only because the initial 83-path hash audit has one unrelated FEAT-063 roadmap mismatch outside the edit allowlist; that current file was preserved untouched. The other three hash changes are approved append-only FEAT-063 records. All 35 protected FEAT-061/FEAT-064 paths, including A2 and the three FEAT-061 documents, are byte-identical.
- Goal-owned databases and local processes were cleaned up after verification. No A2 work, Modal/GPU/provider inference, real child data, or deployment occurred.

## Modal AI setup scaffold — approved, awaiting owner environment setup (2026-11-03)

- Owner approved exact scaffold plan `plan/MODAL_AI_SETUP_SCAFFOLD_20261103.md`, SHA-256 `7FE03A68DF76877457DF5C5F652FCB705669A624B2E07F7B6F317C9FB510E391`; approval is recorded in `approvals/TASK_APPROVAL.md`.
- Canonical workflow source is FEAT-063 SRS v2.3-draft. The new `deployment/modal/srs_v23/` registry and two dev-only app skeletons do not lock model candidates or change backend provider selection.
- All Modal stage handlers are intentionally unconfigured. Current dev settings are L4 for smaller candidate stages and L40S for the LTX video candidate; both are scaffolding values only. Parent/Teacher sketches remain opt-in; lesson/activity suggestion stays disabled while Q157/Q159 roles are unresolved.
- Owner will provision Modal environment/secrets later. No Modal command, account resource, model call, GPU, actual `.env`, deployment, product test, or child data is used by this task.


## StoryRun-lite final baseline disposition — 2026-11-02

- Owner selected B — Rebaseline 875. The exact current roadmap bytes are accepted as the baseline for that one path under an explicit SL-0/SL-8 exception; the initial B881 hash remains historical evidence and is not claimed to have been preserved.
- The original baseline manifest and initial snapshot remain unchanged. The new owner-approved rebaseline record and post-decision snapshot are linked from `evidence/STORYRUN_LITE_SL0_SL8_REBASELINE_20261102.md`.
- S1/S2 technical gates remain verified; the approved rebaseline closes the remaining baseline gate. A2 and all 35 protected FEAT-061/FEAT-064 paths remain byte-identical.

## Modal drawing VLM L4 POC — 2026-11-03

- Owner authorized the next Modal AI hosting work after creating the environment. Exact scope is approved in plan/MODAL_DRAWING_VLM_L4_POC_20261103.md (SHA-256 F2AF6433EFE812BBD8144CBCD3E4ECFDE09FCF0A9952280BCE814314A7008E72).
- Canonical workflow source remains the SRS v2.3-draft. Qwen2.5-VL-7B is a bounded experimental candidate for the first drawing.analyze stage only; it is not a production default and does not enable any product flow.
- Modal auth works and environment dev exists. Preflight inventory on 2026-11-03 found no apps, Volumes, or Secrets in dev; this month's dev metered-cost summary was 0.00. No POC app, model weights, or synthetic inference has yet been deployed/run at this context update.
- Use only a generated synthetic butterfly drawing, two named Volume v2 resources, one private L4 function call, and no secret/public endpoint. Other AI workloads remain separate and are not claimed complete.

## Modal AI hosting wave — 2026-11-03

- Approved scope: `plan/MODAL_AI_HOSTING_WAVE_20261103.md`, SHA-256 `C8FCB03681F2145E727F89E55DDD159AA354814E30B868CD745B930A83FCA5BA`; owner explicitly authorized continuing Modal AI hosting after the dev environment was ready.
- Four private dev apps now exist for drawing VLM, language/audio, FLUX image generation, and Wan video feasibility. Model weights are fetched directly from pinned Hugging Face revisions into Modal Volume v2; no user workstation upload is needed.
- Qwen2.5-VL, Qwen2.5-7B-Instruct, faster-whisper large-v3, VieNeu-TTS v3 Turbo, MOSS Audio Tokenizer Nano ONNX, FLUX.2 Klein 4B, and Wan2.2 TI2V-5B checkpoints have completed download and verification. Their combined retained file footprint is 88.59 GiB; current Modal billing after download has not been checked.
- Synthetic speech POC: VieNeu produced valid WAV; Whisper returned Vietnamese text with one lexical error (butterfly transcribed as a different word). FLUX produced a synthetic line-guide image in 1,202.53 seconds including queue/cold start. The corrective Qwen-VL inference later reached terminal success; this did not verify API result delivery. No duplicate calls or GPU fallback.
- This work remains development-only. All `workloads.json` entries stay disabled; lesson suggestions, SAM2, video safety, and production model choice remain unresolved/deferred. LTX-2.5 remains gated; no terms or credentials were accepted/created.

## Local API runtime availability smoke - 2026-11-03

- Owner requested running the APIs. The live local Docker API returned HTTP 200 for `/health` and `/openapi.json`, but the active image started 2026-10-30 and has no source bind mount.
- Its OpenAPI does not expose `/v1/story-runs` or HTTP routes to the new Modal apps; `GET /v1/story-runs/synthetic-smoke` returned 404. AI provider and StoryRun Modal configuration are unset.
- No POST or model request was sent because the running API cannot dispatch to the new workers. See `evidence/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`. Backend-to-worker integration remains a separate task outside the approved hosting-wave plan.


## Backend API to Modal drawing VLM vertical slice - 2026-11-03

- Owner approved the isolated FEAT-063 adapter/test plan; current cumulative plan SHA-256 is `855235EA0B209A8B64699074C6D861734A5AC17CBD82B1E56E42F9FA9039D0F5`.
- The existing synthetic StoryRun API is wired to the private `drawing.analyze` Modal function through the SDK and scratch Volume v2. The worker receives a versioned path/hash/size envelope; no public Modal HTTP endpoint or new credential is used.
- A separate PostgreSQL 17.11 process under OS temp met the Windows-host loopback guard; migrations and the API upload/image-admission path passed. Existing API and database containers remain untouched.
- Exactly one API-triggered call `fc-01M6GYB9EZHJ4TCPAKFPT20Z7G` later reached Modal terminal `success` after the API timed out. The result/output hash was not returned to the API; the StoryRun remains `AWAITING_RECONCILIATION` with `VISION_OUTCOME_UNKNOWN` / `OPERATOR_REVIEW`. Do not retry. At the owner's request, only `sketch2life-srs23-drawing-vlm-dev` was stopped and verified `State: stopped`; redeploy is required for future use.
- The Qwen worker has no calibrated confidence; its mapped `0.0` is a legacy local DTO placeholder only and must not be treated as a confidence/safety score. Product workload entries remain disabled.
- The bounded API wait returned `VISION_OUTCOME_UNKNOWN`; task-owned local API and PostgreSQL processes are stopped and their temp database/files are retained. Existing stack health is unchanged.
- Evidence: `evidence/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`.

## Parent image-to-script API/AI retest - 2026-11-03

- Ran the standalone StoryRun-lite Parent API against a fresh migrated task database and the generated synthetic butterfly image. Create-run, upload, ClamAV, normalization, and upload-ready operations passed.
- The single API-triggered drawing analysis stayed queued for Modal L4 capacity; the API ended at `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION`. Preserve the run; do not retry.
- A single detached story worker request also returned no result during its bounded wait. The Parent subject-confirmation route was not reached, and the StoryRun-lite API has no script-generation route. No video was requested.
- All four deployed Modal dev apps, the task API, and task PostgreSQL were stopped. Shared model Volumes were retained. Evidence: `evidence/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md`.

## Parent generated-image, story, and activity retest - 2026-11-03/04

- A new synthetic butterfly image completed the isolated StoryRun-lite upload, ClamAV/image-normalization admission, one Modal Qwen2.5-VL inference, and adult subject confirmation. The VLM returned `bướm`; API state reached `PREPARATION_REVIEW` / `SUCCEEDED`.
- A separate direct Modal Qwen2.5-7B story worker returned five Vietnamese scenes. Its input was the confirmed topic, not the image pixels. The draft has factual butterfly-lifecycle errors and needs educator review.
- The legacy activity-list HTTP route returned one curated catalog option and accepted selection. It uses a deterministic VLM fixture in a separate session and remains before-video, so it is not the SRS post-video outdoor activity flow.
- Video calls: zero. All active Modal dev apps and the task API/PostgreSQL were stopped; ports 8002/5433 are closed. Existing API port 8000 and shared model Volumes were retained.
- Full timing, API statuses, limitations, and evidence: `evidence/PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md`.

## AI flow SRS alignment and Teacher deck POC - 2026-11-04

- StoryRun-lite now has a versioned Parent story revision contract/API, exact-age and adult-subject gates, bounded scene/time validation, immutable draft/rewrite rules, and a narrow butterfly lifecycle guard. Parent activity preselection is rejected by design; SRS activities remain after playable video.
- Live synthetic image upload/admission and one Qwen2.5-VL call reached adult subject review. The story API's single Qwen call failed before model load with `MODAL_SCHEMA_UNSUPPORTED`; its old adapter reported `STORY_OUTCOME_UNKNOWN`. The local adapter now uses `sketch2life.modal.ai-request.v1` and maps terminal worker failures, but no live retry was sent.
- Direct Teacher Deck Qwen call produced a 5-slide 16:9 DRAFT from the approved synthetic plan, with four drawing steps and exactly two approved activities. The FLUX visual call waited 468.339s without L4 capacity and produced no image. The HTML preview is text-only.
- API surface: all 13 mounted StoryRun-lite operations were exercised. Story generation is the one live end-to-end API failure; the confirmation success path was not reached. Teacher Deck HTTP/session and integrated post-video Parent activity endpoints are not present in this isolated router.
- Tests: 92 passed, 3 PostgreSQL-URL cases skipped; Ruff, compileall, and diff check passed. All Modal dev apps are stopped with zero tasks; both shared Volumes and shared Docker services are preserved.
- Updated `deployment/modal/srs_v23/workloads.json` with observed POC outcomes; all workloads remain disabled. Parent Sketch Guide, SAM2, ASR/TTS, video, and lesson-plan suggestion were not called in this slice.
- Evidence: `evidence/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md` and `evidence/assets/ai_flow_srs_alignment_20261104/`.
## Full non-video AI retest - 2026-11-04

- Owner explicitly authorized fresh Modal inference and testing all non-video AI workloads after the prior partial POC. Approved plan: `plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md`; approval SHA-256 is recorded in `approvals/TASK_APPROVAL.md`.
- Scope includes corrected Parent story/storyboard, drawing VLM, Parent Sketch Guide, Teacher deck, lesson visual, synthetic TTS-to-ASR, and one isolated SAM2.1 image-segmentation feasibility call. Video generation/composition are excluded; video-specific validators remain contract-only.
- `lesson.plan.suggest` remains no-dispatch because the current SRS leaves requesting roles/model unresolved. All workloads remain disabled for product dispatch; only synthetic assets are used.
- Retest complete. TTS and Whisper round-trip succeeded; fresh VLM, story, Parent Guide, Teacher Deck, lesson visual, and SAM2 inference attempts ended at the bounded queue timeout, with Modal explicitly reporting GPU_L4 capacity acquisition for Qwen workloads. No video calls occurred.
- All 13 mounted StoryRun-lite operations passed 14 isolated contract checks; focused backend tests passed 46 with two legacy-fixture cases deselected. Targeted Ruff, compileall, and diff checks passed.
- All deployed Modal dev apps are stopped with zero tasks. The task PostgreSQL container and pip-cache volume are removed; shared Docker services and Modal Volumes remain. Full result matrix: `evidence/AI_NONVIDEO_WORKLOAD_FULL_RETEST_RESULTS_20261104.md`.

## 30-minute non-video AI queue retest - 2026-11-04

- Owner-authorized fresh direct Modal worker calls used a 1,800-second client-side wait; worker timeouts, model pins, GPU class, and product enablement were unchanged.
- Parent Sketch Guide succeeded in 36 seconds. Teacher Sketch Deck succeeded after 17m22 following a pre-dispatch NotFound from the already-stopped deployment; output validated as a 5-slide DRAFT with four drawing steps and two approved activities.
- Drawing VLM, story/storyboard, lesson visual, and SAM2 each waited the full 30-minute bound without inference output. Modal logs confirmed GPU_L4 scheduling waits; no unknown call was retried.
- TTS/ASR were not repeated; video inference remained zero. All Modal dev apps were stopped with zero tasks at 22:00:30. Full evidence: evidence/AI_NONVIDEO_30MIN_QUEUE_RETEST_RESULTS_20261104.md.

## Modal Qwen story readiness diagnostic - 2026-11-04

- A temporary L4 readiness probe loaded the pinned Qwen2.5-7B checkpoint and generated smoke tokens: model load 15.989 s, inference 1.297 s, total 26.194 s. This confirms the checkpoint and basic GPU runtime were ready in the probe container; the smoke prompt was not a semantic quality test.
- The deployed story function did not start: Modal logged that it was waiting for a `GPU_L4` worker while acquiring capacity. The two observed calls had no `started_at` or `container_id`; therefore the 600-second worker execution timeout and story inference were never reached. Longer client waits do not fix this scheduling blocker.
- The approved diagnostic allowed one new story call; two were accidentally enqueued after the first runner failed to surface its call ID. This scope deviation is disclosed in the execution report. Both were synthetic, neither ran inference, cancellation was requested, and the task-owned Modal apps were stopped with zero active containers.
- Current FEAT-063 SRS v2.3-draft and the deployed POC both specify Qwen2.5-7B for story generation; this result does not justify a Qwen3 model change. No source, SRS, API, or persistent scaling change was made. Evidence: `evidence/MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md`.


## Serverless story latency experiment - 2026-11-05

Owner-authorized FEAT-063 dev-only test added ordered L4/L40S/A10 GPU options, story-only Transformers parallel shard loading, safe phase timing logs, and a 120-second scaledown window while retaining scale-to-zero. One synthetic Parent call received an A10, loaded the pinned Qwen model, and generated 722 tokens; strict worker parsing rejected the output as `MODAL_MODEL_OUTPUT_INVALID`. No retry or video call was made. The task-owned Modal app is stopped with zero tasks. This does not promote a production profile; the output-format issue remains separate. See `evidence/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`.

## Modal Parent story parser follow-up — 2026-11-05

- The first parser-alignment call ended with safe reason `SCENE_FIELDS_INVALID`; the exact malformed field was not retained because raw model output is not persisted.
- Follow-up keeps the public SRS/backend story contract unchanged. Qwen emits content only; the server validates it, assigns fixed five-scene timing metadata, then runs the original strict parser and backend contract checks.
- One synthetic butterfly request passed worker parsing, `StoryRevisionDraftV1`, and the lifecycle fact check: five scenes, 30 seconds, 56.073 seconds dispatch-to-terminal, 608 generated tokens on NVIDIA L40S.
- Focused tests: 46 passed; Ruff and Python compilation passed. The Modal app is stopped with zero tasks and shared Volumes are retained. No video/other AI workload, SRS/API change, or product enablement.
- Evidence and limitations: `evidence/MODAL_STORY_CONTENT_BOUNDARY_20261105.md`.

## Parent StoryRun-lite API and AI retest - 2026-11-05

- The 22-request no-AI matrix covered all 13 mounted operations and passed its expected contract/status checks. Focused backend tests: 154 passed; Modal story/parser checks: 45 passed, 1 skipped.
- The real drawing-analysis API accepted the request only after 304.333 seconds; its Modal outcome remained unknown after 303.762 seconds. Persisted state was `INPUT_PROCESSING` / `AWAITING_RECONCILIATION` with `VISION_OUTCOME_UNKNOWN`; no candidate was committed and no retry was sent. This is a latency/unknown-outcome API issue, not a confirmed model result.
- A separate fixture-backed story API request returned 502 `STORY_OUTPUT_INVALID` after 59.266 seconds. The worker parsed structured output, then rejected butterfly lifecycle facts as `EDUCATIONAL_FACT_INVALID`; the parser-contract suite passed. Do not describe this as parser drift or weaken the semantic guard based on this run.
- The mounted slice does not expose the broader SRS capabilities for Parent activities, line-sketch guide, lesson visuals, ASR/TTS, SAM2, Teacher Deck, or video. Video was explicitly excluded; these unmounted capabilities were not invoked through this API retest.
- Both task Modal apps and the disposable PostgreSQL container were stopped and verified. Shared Docker services and Modal Volumes were preserved. Full results: `evidence/PARENT_STORY_API_RETEST_20261105.md`.

## Rev44 AI API coverage and Qwen3.5 validation - 2026-11-05

- Q159 is resolved: Platform Admin and Teacher may initiate lesson/activity/plan suggestions; Parent may edit only an already-authorized draft or personal copy. Generated lesson content stays private pending human review.
- The current Modal profile pins Qwen3.5-9B at `c202236235762e1c871ad0ccb60c8ee5ba337b9a` with Transformers 5.22.1. One bounded Teacher Deck call passed; drawing VLM returned unusable text; story and lesson suggestion failed before generation on an outdated LMFE/Transformers import. The LMFE adapter was corrected and passed local constrained-token tests plus a Modal CPU import check. The post-fix story/lesson inference remains unverified; no retry was made.
- VieNeu TTS produced a synthetic WAV, while paired Whisper changed one word. FLUX.3 is blocked by HTTP 401/no Modal HF Secret; SAM2 previously timed out waiting for GPU_L4; video was deferred. All workload flags remain off.
- Main OpenAPI has 24 operations/17 path templates and no AI dispatch. StoryRun-lite has 13 fixture operations; its two Modal calls use non-durable in-process background tasks. The catalog records missing authenticated durable APIs for Parent ASR/guide/story gates, Teacher deck, Admin/Teacher lesson suggestions, visuals, and shared job polling.
- Focused validation: 59 Modal/parser tests passed; 79 backend API/contract tests passed, 6 skipped. Detailed per-call timings, output state, current blockers, and shutdown are in `evidence/AI_API_QWEN35_MODAL_VALIDATION_20261105.md` and `artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`.

## Rev45 non-video AI execution - 2026-11-05

- Root cause for premature Qwen EOS was LMFE's 92-character ASCII alphabet dropping parser state on Vietnamese Unicode inside nested JSON strings. Runtime alphabet extension now preserves parser state; strict schema, semantic, and adult-review checks remain unchanged.
- Fresh synthetic worker inference passed for drawing analysis, Parent story/storyboard, Teacher Sketch Deck, lesson-plan suggestion, TTS, and exact-text ASR. Results and Modal call IDs: `evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md`.
- Modal Secret list is still empty, so FLUX.3 Parent Guide and lesson visual remain blocked pending owner-managed HF access. SAM2 remains optional and unverified; its last attempt waited 1,800 seconds for GPU capacity, and current availability was not rechecked.
- Focused tests: 76 Modal tests passed; 61 backend API/OpenAPI tests passed and 6 were skipped. Both task-used Modal apps were stopped at zero tasks; Volumes remain. No video calls and no product workload switch was enabled.


## Rev46/46A ? Qwen3.5-only profile and FLUX component repair ? 2026-11-05

- Owner directed that Qwen2 be removed from active use and Qwen3.5 used instead. Canonical SRS, D-142, and active Modal workload registry now use only pinned Qwen3.5-9B for Qwen workloads. Historical Qwen2.5 evidence and shared Volume contents were preserved. Active backend/deployment source and configuration search found no Qwen2 selection.
- Rev46 image calls exposed an incomplete FLUX checkpoint: downloader allowlist omitted Diffusers `transformer/` and `vae/`; the marker verifier did not require them. The allowlist/verifier now include those components, and a stale marker cannot skip staging an incomplete checkpoint.
- Rev46A staging passed in 61.472s. Synthetic Parent Sketch Guide passed in 65.772s and synthetic lesson visual passed in 47.206s. Both returned 3-panel PNG DRAFT candidates with review required; lesson revision/content hash matched. Output visual review noted the lesson image's first panel is minimal and requires educator review for pedagogical clarity.
- Modal app `ap-n5KrAmUnWNrKLYfDoQC5Ef` was stopped; final list showed zero tasks. Shared volumes retained. No Qwen, TTS/ASR, SAM2, video, or authenticated product API was invoked in Rev46A; every workload remains disabled.
- Validation: 27 focused tests passed; Ruff, compileall, repository security validator, and diff check results are recorded in the completion report.


## Plan Rev50 ? dev duplicate repair and Modal/SRS integration (2026-11-06)

- The six local-only `dev` commits were patch-equivalent to commits already in `origin/dev`; the old checkout and its staged, unstaged, and untracked work are preserved on a backup branch.
- The selected Modal branch and its pending AI changes are integrated with the published FEAT-063 SRS v2.4-draft. The SRS remains unsigned and is the current canonical working source.
- The six local commit copies were not rewritten or renamed. Local merge `370cb26d6e8c99c126f4a5a16df132eaa70c8e70` completed and was fast-forward pushed; `origin/dev` now equals `0d15b1a0ae6e5373354d7ac35cc163e41b55c42e`. Detailed refs, checksums, conflict decisions, and verification limits are recorded in `evidence/EV-063-54_DEV_HISTORY_AND_SRS_MERGE_20261106.md`.

## Rev51 Modal AI and legacy API audit - 2026-11-06

- Current FEAT-063 SRS v2.4-draft remains canonical. Rev51 reused already-passed synthetic worker outputs and did not repeat GPU inference.
- Live API returned 200 for `/health`, `/docs`, and `/openapi.json`; OpenAPI lists 124 operations / 111 paths. The API/contract suite collected 1,460 cases (1,454 pass, 6 fail); exact failures are in `evidence/modal_ai_and_legacy_api_retest_20261106/API_TONG_HOP_VA_SAN_PHAM_AI_MODAL_20261106.md`.
- Modal worker contracts: 79 pass, 2 skip. Qwen3.5, FLUX.3, TTS and Whisper artifacts were copied with SHA-256/provenance into the Rev51 result folder. Product API dispatch/persistence remains incomplete for several AI workloads.
- SAM2's last attempt spent 1,800 seconds waiting for GPU capacity and returned no mask. No execution-time timeout was reproduced; Modal `dev` app inventory was empty, so no task app was deployed or needed shutdown.
- No code change was justified by current evidence; keep the six API regression failures and Parent StoryRun-lite historical AI failures open for focused follow-up.


## Plan Rev52 - non-video Modal AI reliability and observability

- Status: APPROVED; implementation is proceeding on `feature/feat063-modal-ai-reliability-20261106`, based on `dev` commit `0fc773fa`.
- Scope: all 9 non-video workload IDs in the current Modal registry, structured privacy-safe worker/caller logs, current mounted Parent AI routes, bounded synthetic calls, and task-app shutdown. Video remains excluded.
- Baseline: prior worker successes are historical evidence; backend durable product APIs remain absent for several workloads. A worker pass will not be described as product API readiness.
- Approved plan and SHA-256: `plan/PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md`, `6B3B1C25CD2A9974860A93551CDAD0FB3363DB38CB00D293ABB4818C9F0782D2`.
- No source implementation or Modal deployment has started before this approval record.
