# FEAT-063 — Whole-repository architecture redesign

## Rev87.21 — constrained Parent stroke generation result (2026-11-15)

- The worker now constrains an internal fixed-key stroke map and normalizes it to the existing Parent guide contract. Focused final tests passed: Modal 30/30, backend 12/12, mobile 3/3.
- Three real synthetic `con mèo` Parent route → Modal Qwen3.5 calls were run sequentially under the approved cap. Call 1 duplicated geometry at stroke 5; call 2 produced eight unique paths then duplicated at stroke 9; call 3 failed first-path complexity at 768 characters. HTTP 502 durations were 193.140 s, 211.341 s and 446.930 s. None was a worker timeout. No valid SVG or render exists.
- The worker kept all hard gates. Modal health probes reported CPU-only/no inference; after the third call the app was stopped and verified stopped. No child data/video/Android UI was used.
- **Current state:** free-form Qwen-authored SVG path data remains unreliable. Next approach should generate bounded semantic primitives and render SVG paths deterministically. See `evidence/EV-063-117_PARENT_STROKE_CONSTRAINED_GENERATION_20261115/REPORT.md`; SRS §32.35 is as-built only, §§1–31 unchanged.

## Rev87.20 — Parent construction-guide live result (2026-11-15)

- Rev87.20 ran the corrected source-conditioned Parent guide through the real Parent route and Modal Qwen3.5 worker using only synthetic topic `con mèo`. Focused tests passed after the prompt/diagnostic correction: Modal 27/27, backend 12/12, mobile 3/3.
- The first request failed because the final stage lacked a feature stroke. The narrow prompt/diagnostic correction was deployed. The one final authorized request did not time out: Qwen emitted only two strokes for eight stages, with duplicate geometry (70 total geometry characters). The unchanged worker gate rejected it with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID` / `DUPLICATE_STROKE_GEOMETRY`; Parent route returned HTTP 502 after 189.152 s. No guide/render was produced.
- No gate was relaxed, no retry or third inference was sent. Modal `dev` deployment v2 passed CPU `/health` with no GPU allocation/inference for health; the app was stopped and verified stopped afterward.
- **Current status:** the Parent AI construction-guide generation remains unverified and unusable for this live case. Need to address constrained output structure/unique stroke generation before another inference. See `evidence/EV-063-116_PARENT_STROKE_LIVE_FIX_20261115/REPORT.md`; SRS §32.34 is as-built only, §§1–31 unchanged.

## Rev87.19 — Parent construction-guide implementation outcome (2026-11-15)

- The approved separate construction-guide contract and focused backend/Modal/mobile coverage are implemented in the current worktree. Focused tests passed: backend 12/12, Modal worker 25 passed (two asyncio deprecation warnings), mobile 3/3.
- One real Modal Qwen3.5 inference for synthetic topic `con mèo` completed model inference but failed worker geometry validation with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`; HTTP 502, 234.273 seconds. The exact subreason is unknown because the earlier combined gate did not retain raw output or separate size from duplicate-geometry failures.
- A local geometry-cap/prompt/diagnostic correction was deployed to Modal `dev` after the failure. No further inference was authorized or run; the corrected worker has no live generation proof. No SVG/image was returned or rendered, and no Android UI/Teacher presentation/video/child-data run occurred.
- SRS §32.33 records this environment-specific failure and correction; §§1–31 remain unchanged. The SRS is still unsigned. Details: `evidence/EV-063-115_PARENT_CONSTRUCTION_MODAL_TEST_20261115/REPORT.md`.

## Rev83.4 — M1/M2 implementation authorized (2026-11-13)

- Owner selected “Approve these defaults and M1/M2 (Recommended)”. The exact approved source and documentation manifest is in `plan/PLAN_REV83_4_M1_M2_APPROVED_IMPLEMENTATION_20261113.md` and `approvals/TASK_APPROVAL.md`.
- Canonical working SRS is now FEAT-063 v2.7-draft Rev69 in this checkout. Rev68 contains approved M0 defaults and the M1/M2 boundary; Rev69 adds only a source-only implementation snapshot and explicitly leaves verification open. It remains unsigned.
- M1/M2 are the only authorized source scope: deterministic SVG catalog/sanitizer/readiness/renderer, Parent and Teacher playback, and manual Teacher guide authoring using immutable lesson revisions. Core catalog/review persistence is limited to the gap recorded in `artifacts/REV68_SVG_CATALOG_PERSISTENCE_CROSSWALK.md`.
- Reusable source-bound catalog guide revisions are distinct from each lesson's immutable presentation snapshot; curator approval gates platform catalog visibility, while `grouping_allowed` is only for future automatic grouping. The migration now has immutable guide/review row guards and a downgrade guard for retained catalog/platform assets. Parent and Teacher renderers consume the same approved `animation_order`.
- The exact manifest excludes `ParentApplicationModule.ts`; Parent's `learning` boundary therefore does not type-expose `listSvgGuides`, and the controller uses a local narrow cast to the existing runtime use case. This remains an unverified type-level integration seam for a separately approved manifest update.
- No catalog item is treated as curated or educator-approved. No fixture, canned output, Modal call/deploy/warmup, AI activation, video, FLUX removal, migration execution, test/build/runtime verification, commit, or push is included.
- Source edits for M1/M2 are present in the approved manifest, including backend catalog/review contracts and migration, Parent SVG guide lookup/playback, and Teacher manual guide authoring/review/presentation. They remain unverified and uncommitted; pre-existing worktree changes remain in place. See `status/STATUS.md` and `evidence/EV-063-93_SVG_ENGINE_M1_M2_20261113/IMPLEMENTATION_REPORT.md`.

## Shared SVG engine and Parent/Teacher completion — Plan Rev83.3 (2026-11-13)

- Planning-only amendment after the third independent review. Adds structural stroke/filled-shape facts plus educator review before curator-authorized grouping; separates `BASELINE_E2E`, existing Parent AI subcases and per-task SVG `AI_E2E`; specifies Teacher editor Undo/Redo, autosave and `409` recovery; proposes renderer performance measurements; and adds independent SVG capability kill switches with `CAPABILITY_DISABLED` and no fallback.
- All metric formulas, educator-review ownership/rubric, editor-save details, performance thresholds/device and flag/error mapping remain M0 proposals. Candidate renderer thresholds are not approved SLOs.
- SRS reconciliation remains open: task-level instructions identify the FEAT-063 file and amendments through Rev64, the current worktree file/pointer says Rev60, and a Rev65 pointer was seen in a different checkout. Do not use that other checkout as product authority. The SRS remains unsigned; the 3–5/4–8 step conflict remains open.
- The 1188-line Rev83.3 plan includes three review dispositions, contracts, deterministic readiness and educator-review rules, editor recovery, playback/performance proposals, E2E evidence classes, independent AI flags, staged POCs, APIs, milestones and acceptance tests. SHA-256: `73730C4EF30B4EB1E6CF5581105824F3D3D6EFCBDC0E2EE64C7A71009A0960F4`.
- No implementation approval was recorded. No SRS, DTR, source code, Docker, Modal, database, secret, or runtime state was changed; no tests or inference were run. See `status/STATUS.md` and plan §32.
- Plan: `plan/PLAN_REV83_SVG_ENGINE_AND_PARENT_TEACHER_COMPLETION_20261112.md`. Rev82 runtime evidence remains partial; see the matching Status entry and EV-063-90 reports.

## Shared SVG engine and Parent/Teacher completion — Rev83.2 predecessor (2026-11-13)

- Rev83.2 added deterministic source readiness classes, Teacher manual guide authoring, playback policy, separate M3-A/M3-B gates and catalog/manual baselines before full Qwen quality work.
- Historical plan snapshot: 1153 lines; SHA-256 `BF637F820CF6B984F6F36D59FCEAAB0312E48C2F8449974AA71F8B3D03E4BFB5`. Its review disposition remains in plan §31; Rev83.3 refines it without authorizing implementation.

## Consolidated Parent/Teacher/Docker plan — Rev81 — 2026-11-12

- At drafting time, the owner asked to pause coding and combine the existing Parent Docker/seed/Modal-health baseline, Parent Android workflow, Teacher presentation and progressive line-sketch work into one comprehensive plan. That planning-only state was later superseded by the explicit implementation approval recorded below.
- Owner-confirmed direction: Parent may start from a system/custom topic, no topic, or an authorized lesson presentation; drawing capture is required; on subject mismatch retain lesson knowledge and let the adult switch topic or retake once; choose one primary activity before story generation and show all lesson activities after video. Plan detail also covers Parent account/profile/share/library/settings/notification/quota/history and Teacher occurrence from approved presentation through that child's drawing and script confirmation.
- Teacher lesson is intended to be an editable presentation with uploaded images, video URLs, optional Teacher-enabled AI images and a progressive drawing guide. School Manager controls school visibility; Platform Admin approves platform-wide PUBLIC publication. Media URL policy remains open. If the one allowed retake still mismatches, use the adult-confirmed AI-detected subject while retaining the lesson as knowledge.
- Rev60 SRS remains canonical, unchanged and unsigned. The plan records conflicts with Parent activity timing/topic input and the current Teacher Sketch Deck scope; see Plan Rev81 §2/§9 and `approvals/TASK_APPROVAL.md`.
- Plan Rev81 has been expanded into screen-level Parent and Teacher workflows, verified current API routes versus proposed contract gaps, data ownership/migration gates, AI quality contracts, Docker/seed setup, dependency-ordered work packages and a real-E2E acceptance matrix. Its latest approved hash is recorded in `approvals/TASK_APPROVAL.md`.
- Rev79 source/runtime work and EV-063-88 are preserved as the current local baseline. Rev80 is superseded before source implementation; its Parent real-AI verification and Teacher sketch fix are carried into Rev81.

### Rev81 implementation state — 2026-11-12

- The owner explicitly superseded the earlier pause and approved implementation with “implement plan, make sure no fixture”. The approval is bound to Rev81 SHA-256 `6BE36B78F949177FA87DCED2EA620713BFE8A8EFE092B844AD20EC83B7CF71C6` and the path families in plan §8.1.
- No fixture/mock/hardcoded output may drive a product workflow or count as E2E evidence. Synthetic local accounts/entities and generated non-personal drawings may enter through real services only. A missing service/API must produce an explicit error/unavailable state.
- Rev60 remains the canonical unsigned SRS. Rev81 implementation follows the owner’s task-scoped clarifications while keeping SRS conflicts/open decisions explicit; it does not modify the SRS or Data Table Register.
- Video inference, production writes/publication, real-child data, consent fabrication, local `.env`/secret changes, destructive database/container operations, commit and push remain excluded. Existing Rev79 changes/runtime are preserved.

## Rev79 Parent Docker seed, Firebase config and Modal health — 2026-11-12

- Parent local Compose now builds and starts PostgreSQL, Redis, MinIO/bucket init, ClamAV, Firebase Auth Emulator, migration, insert-only seed, API and a dedicated Modal health app. The isolated Rev79 stack is currently running on loopback-only development ports; the API uses host port 58000 because another local service owns 8000.
- Alembic upgrade to all heads passed after shortening the Parent context revision to `20261110_parent_ctx`; the lesson-pin child revision now follows it. The second seed run reported existing rows and aggregate counts remained one Parent identity/profile/revision/synthetic authorization/lesson/version/public grant with three activities.
- Firebase Auth Emulator sign-in and Parent role/profile/consent/quota/public-lesson/active-run APIs passed. The local quota endpoint is display-only, not a Billing ledger. Expo CLI resolved the Firebase app ID from the one root `.env`; the worktree path lookup was fixed without adding a nested `.env`.
- The root `.env` local AI provider is now `modal_dev`; Compose startup still sent exactly one health request to the CPU-only Modal health app and no model inference. Health explicitly reports `inference_ready=false` and `gpu_allocated=false`.
- The punctuation relaxation passed bounded backend quality-gate and Qwen parser checks on synthetic Vietnamese text. No live Qwen/vision/FLUX/TTS/ASR inference, Android UI interaction or video was performed. Exact results and limits are in EV-063-88.
- Plan Rev79 and its addenda are approved in `approvals/TASK_APPROVAL.md`; current plan hash is `5B8375B7DEED983AAB33C69297C3F44C5B35B12985F17D39E7920035555C0380`. SRS Rev60 remains unchanged and unsigned.

## Rev78 Parent catalog-first activity publication — 2026-11-11

- Feature commit `34b92194867e915040aae1a1178dee0e526a60c3` was pushed to `origin/codex/feat063-parent-catalog-20261111`, fast-forward merged into `dev`, and pushed. Fresh remote verification confirmed both refs at the same SHA; the `dev` update also published the 21 pre-existing local `dev` commits. The remote reported the pull-request-only rule was bypassed for the owner-authorized push; no history was rewritten.
- The repository security validator passed before pushing `dev` (`publishable_files_scanned=7223`). Implementation/test results and live-inference limitations are recorded in `status/STATUS.md` and `evidence/EV-063-87_PARENT_FULL_API_UI_E2E_20261111/API_PARENT_E2E_REPORT.md`.
- The v2.7-draft Rev60 SRS remains unchanged and unsigned; D-172 remains task-scoped pending formal SRS reconciliation.

## Teacher Sketch Deck presentation UI — Plan Rev65 (2026-11-10)

- Implemented and verified the Teacher presentation surface in the real Teacher Web UI with live Modal output: 4-slide Qwen3.5 DRAFT and FLUX composite image on the drawing-guide slide. Activity content scrolls inside the fixed 16:9 slide so safety notes remain reachable.
- Teacher slice PASS; the broader Parent/Teacher E2E remains PARTIAL. This run did not execute Parent Android because the isolated host had no `adb`, Android SDK/platform-tools, or emulator. The Rev64 Parent 256-token output failure remains the last live result; the approved 512-token worker change was not exercised through Parent UI.
- Build and sanitized timings, worker-log limitation, screenshots and cleanup are recorded in `evidence/EV-063-75_TEACHER_PRESENTATION_UI_20261110.md`.

## Parent/Teacher Modal E2E — Plan Rev64 (2026-11-10)

- Owner requires UI-driven Parent Android and Teacher Web workflows through Firebase role resolution → backend → live Modal inference → visible UI result. Fixture and backend-only runs do not count; video remains deferred. Last approved scope SHA-256: `C6A217BB2114C7D64621E6B50E3A92F6E7E20063866EF6977667F40581BBF9A3`; execution plan SHA-256: `B791E6E552FF16A6A99D5758D7A2226FA6DD561AE852A40DF6BC2B87E32015C8`.
- Initial preflight found the Parent fixture and Teacher prototype surfaces and an empty Modal app list. The owner was correct that source/deployment definitions exist on `dev`: local `dev` and `origin/dev` both point to `1431ef81972b71303fd4a7909748fd3005769a3c`. Apps were redeployed temporarily from that source for this test.
- Execution result is PARTIAL. Real Parent signup/role resolution and optional FLUX line-sketch passed after one approved UI-render recovery. Parent Qwen drawing understanding failed strict JSON parsing after generating 256 tokens; API returned 504 `MODAL_OUTCOME_UNKNOWN` before the worker logged terminal `MODAL_MODEL_OUTPUT_INVALID`. Parent story was not called because no candidate was available for adult confirmation. Real Teacher role resolution and Qwen lesson suggestion, Qwen Sketch Deck and FLUX lesson visual passed through Teacher UI; raw lesson-file upload/parser review was not exercised.
- Cleanup completed: three task-used Modal apps STOPPED at zero tasks; synthetic Firebase users and `rev64_e2e` removed; task-started Postgres/Redis and emulator stopped; pre-existing API/ClamAV preserved. No video, commit or push. Full timings and screenshots: `evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md` and its `logs/`/`screenshots/` subfolders.

## Server-managed roles and account recovery — Plan Rev63 (2026-11-10)

- Added a single server-side product role on `be1_adult_identities`: Parent, Teacher, School Manager, or Platform Admin. Parent signup is assigned Parent by the backend; Teacher Web accepts only the Teacher role; management Web routes are split between School Manager class access and Platform Admin account management.
- Platform Admin can list/search/page accounts, create Firebase identities with a selected role, change roles, and disable/re-enable accounts. Role changes are audited and revoke incompatible active school assignments. Email/display name are read from Firebase Auth for authorized Platform Admin responses and are not persisted in PostgreSQL/audit records. Legacy identities with ambiguous roles appear unassigned and are denied protected routes until an admin assigns a role. Compose passes the root `.env` bootstrap email to the API container and no longer forwards the retired subject allowlist.
- Admin Web requests a Firebase password-reset email after account creation. Parent Android, Teacher Web and management Web include Firebase password reset and authenticated password change. The initial Platform Admin is provisioned by the explicit command `python -m sketch2life.infrastructure.identity.bootstrap_platform_admin`, configured with `SKETCH2LIFE_PLATFORM_ADMIN_BOOTSTRAP_EMAIL` in the repository-root `.env` after the additive migration.
- E2E update (2026-11-10): all Alembic heads were applied to disposable PostgreSQL; backend Parent registration, account/role lifecycle and authorization scenarios passed with synthetic identities. Real HTTP Parent registration and safe invalid-token mapping passed. Role-gated business cases used an injected test principal rather than a Firebase-signed token. The root `.env` Web API key differed from the owner-provided Web config and was corrected; a non-mutating Firebase probe and synthetic Identity Toolkit reset/sign-in/change-password lifecycle then passed. The synthetic user was deleted and no email was sent. Admin/Teacher builds and mobile typecheck passed, but interactive UI flows were not run. Full Compose startup hit a MinIO registry HTTP 401, so isolated temporary API/PostgreSQL containers were used and then removed. Existing services/volumes were preserved, synthetic identities were deleted, and no admin seed remains. UC-13 email-verification activation/delivery and production shared throttling remain open.
- Contract/evidence: `artifacts/AUTH_ROLE_API_CONTRACT_REV63_20261110.md`, `evidence/EV-063-73_ROLE_BASED_AUTH_AND_RECOVERY_20261110.md`. Plan Rev63 approval/hash and boundaries are recorded in `approvals/TASK_APPROVAL.md`.

## Backend Firebase Auth registration — Plan Rev62 historical state (extended by Rev63, 2026-11-10)

- Implemented local-only `POST /api/auth/v1/registrations`. Parent signup now calls the backend first, then Firebase Auth REST sign-in. The backend creates an unverified Firebase Auth identity and does not accept a role or expose UID/password.
- Verification: focused backend tests 18/18 passed; Parent auth Jest 6/6 passed; TypeScript, Ruff, and `docker compose config -q` passed. A live backend request returned 201 and Firebase Admin found `synthetic Firebase identity (identifier redacted)` in `sketch2life-dev`, `email_verified=false`.
- Live REST sign-in is still blocked: Firebase returns `API key not valid` for the owner-supplied Web API key, even after aligning the root `.env` value to the provided string. The synthetic account is retained but its random password was discarded; no second account was created.
- Under Rev62, registration was local-only and did not persist role. Rev63 makes the route public with a bounded process-local limiter and adds backend Parent role persistence. Email-verification action delivery/activation and production shared throttling remain unimplemented.
- Evidence: `evidence/EV-063-72_BACKEND_FIREBASE_ACCOUNT_REGISTRATION_20261110.md`; contract: `artifacts/AUTH_REGISTRATION_API_CONTRACT_REV62.md`. Plan Rev62 lifecycle is REVIEW; approval and hashes are in `approvals/TASK_APPROVAL.md`.
- The live request used FastAPI `TestClient`, not a running Docker container. No Docker service lifecycle, DB/migration, commit, or push occurred.

## Single-root Firebase Auth configuration — Plan Rev61 (2026-11-10)

- Work was confined to `the repository root`; no sibling checkout/worktree was edited, created or removed during this slice.
- Local Firebase configuration is now read from one ignored repository-root `.env`. Compose forwards Admin verification settings only to the API; Teacher Vite and Parent Android read only public `VITE_FIREBASE_*` values from that same file.
- At Rev61, Parent Android's AuthSessionPort used Firebase REST for email/password signup, sign-in, refresh, and sign-out. Plan Rev62 supersedes only the signup-creation step with backend-first registration; REST sign-in/refresh/sign-out remain. Parent role/profile provisioning and the full Parent workflow remain separate backend work.
- The owner supplied the Firebase Admin service-account JSON from Downloads; its Base64 value is now in the ignored root `.env`, and `SKETCH2LIFE_AUTH_PROVIDER=firebase`. The local Admin SDK accepted the credential and its project ID matches `sketch2life-dev`; no live token verification was performed.
- Evidence and limits: `evidence/EV-063-71_SINGLE_ROOT_ENV_FIREBASE_AUTH_20261110.md`. No live Firebase request, account creation, Docker service lifecycle operation, database change, commit or push was performed.

## SRS baseline correction and Rev57 note reconciliation — Plan Rev60 (2026-11-09)

- Owner correction selects the latest FEAT-063 SRS source, v2.7-draft Rev57 at commit `f21c6f34af1ee045caf9a0621e38376a2bfde390`; local working SRS now carries amendments through Rev60 and remains unsigned.
- Rev57 §§32.6–32.7 are preserved; Rev58 CI snapshot is §32.8. §25.5 separates existing GitHub Actions CI from a target CD/release flow; §28.2 retains the acceptance scenarios and labels no-eligible as a temporary test assumption.
- Counts distinguish 86 pre-Rev31 mappings, 89 current source mappings, historical v2.3 89/137, current target 92/140, and local runtime snapshot 41. Seventeen owner decisions remain `OPEN-OWNER`; Q183 and Q192 point to §31.10 items 3 and 10.
- The supplied six-group note is reflected only where supported inside SRS; physical schema evidence, diagram artifacts and owner answers remain open. DTR is unchanged and still locally labeled v2.5-draft.
- Evidence: `evidence/EV-063-65_SRS_REBASE_V27_REV60_20261109.md`; Plan Rev60 and approval hashes are in root and feature registers.

## Rev56 ten-group diagram-readiness alignment — 2026-11-08

- Lifecycle: COMPLETE for the bounded documentation-only synchronization; SRS/Data Table Register remain v2.7-draft and unsigned.
- Aligned system random selection and Teacher confirmation across UC-05, FR-T-10, FR-PL-20, AC-56, the Teacher responsibility/screen/error traces and §5.2; retained Q185 as source wording with a current-flow note. Q-01 keeps eligibility, consent, exclusion, reselection, no-eligible handling and selection evidence/snapshot placement OPEN.
- Mapped all ten remaining groups to existing SRS/Register and M/D/Q/R/OI references in the Rev56 catalog. Settled sub-decisions remain unchanged.
- Physical ERD and final diagram approval remain gated; every final artifact must trace to requirement/decision IDs on one approved SRS/Register baseline. No new product policy, schema, state, permission, API, implementation, or as-built claim was produced.
- Evidence: evidence/EV-063-61_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md; catalog: artifacts/DIAGRAM_INPUT_CATALOG_V27_REV56_20261108.md.

## Rev54 v2.6 checklist audit and diagram readiness — 2026-11-07

- Lifecycle: approved documentation review complete; publication checks and push closeout are recorded in status/STATUS.md.
- Current authority remains the canonical SRS and Data Table Register v2.7-draft. Both are unsigned; this task creates no final diagram and claims no fresh as-built verification.
- Read the owner-supplied v2.6 checklist sources together at Rev55 commit a711e78cf6586dd5b639d811e610a741efd7433d, then reconciled every M/D/Q/R code against the current 98cc34a baseline.
- Added a TO-BE diagram input catalog and a full crosswalk. M-12 is logically resolved for school-only Teacher quota and current-month-included then top-up FIFO; M-04 and M-15 retain open role/grant details. D-08 and D-09 remain partial because allocation and identity-link details are not settled.
- All Q-01–Q-13 remain OPEN-OWNER as complete checklist items. Existing direct owner clarifications are only scoped sub-decisions; no new product decision was made.
- Parent no-preset activity behavior, plan supersession effects, role persistence/resolver, legacy age handling, audit schema/retention, physical DDL/migration, final screen/API detail and package verification remain open/evidence-gated.
- See artifacts/DIAGRAM_INPUT_CATALOG_V27_REV54_20261107.md, artifacts/DIAGRAM_READINESS_CROSSWALK_REV54_20261107.md and evidence/EV-063-59_DIAGRAM_CHECKLIST_REVIEW_20261107.md.

## Rev53 v2.6 checklist reconciliation — 2026-11-07

- Lifecycle: COMPLETE for the approved documentation reconciliation and normal publication.
- Working pair target: SRS and Data Table Register v2.7-draft; both remain unsigned. The supplied checklist is analysis evidence only.
- Reconcile exact optional LessonVersion ref/version/hash lineage through occurrence, plan revision and Teacher run; state video admission as separate owner transactions coordinated by an idempotent saga; normalize organization-admin labels to School Manager where current product role is established.
- Keep Parent activity behavior without a lesson preset, plan supersession, role persistence/resolver, legacy age 121–155 handling, physical audit/retention, and DDL/migration details OPEN. Do not infer new owner decisions from the checklist.
- Plan Rev53 and owner authorization are recorded in the root and feature approval registers. Package commit `359b0b92384faad789f6006c37cc5f66760ad594` was pushed to `origin/docs/feat063-srs-v26-checklist-20261107` and confirmed by `git ls-remote`. Completion evidence: `evidence/EV-063-58_SRS_V26_CHECKLIST_REMEDIATION_20261107.md`.

## Rev52 SRS contradiction reconciliation — historical publication record — 2026-11-06

- Lifecycle: REVIEW; approved documentation-only SRS/Data Table Register reconciliation is complete; final diff reviewed and git diff --check passed.
- Canonical working pair: SRS and Data Table Register v2.6-draft; both remain unsigned and do not have owner content sign-off.
- Incorporated the report review and owner clarifications: Content Admin is a Platform Admin permission; child-media access for Platform Admin remains deny-by-default until a separate workflow is approved; Teacher video uses only the school organization quota.
- Corrected Parent optional lesson-version pin and post-video activity ordering, invitation acceptance, all eight AI Job targets, video admission transitions, and the 92 active + 48 legacy = 140 current target count. The 89/137 count remains the historical v2.3 baseline.
- Unresolved details remain open, including field-scope/expiry, school-wide invitation acceptor, personal-copy ownership/retention, admin media workflow, random sample eligibility/consent, publication approval, quota amounts/pricing/allocation, DDL, migration mapping and final diagrams.
- Plan Rev52 and approval are recorded; evidence: evidence/EV-063-57_SRS_V25_CONTRADICTION_REVIEW_20261106.md. Owner-authorized package commit `ca3c5dda695dc8d325442921ace684364d0215b1` is pushed to `origin/docs/feat063-srs-conflict-remediation-20261106`; `git ls-remote` confirmed the same SHA. SRS remains unsigned.



## Prior SRS v2.5 alignment and dev-source review — Plans Rev45/Rev51 (2026-11-06)

- Lifecycle: REVIEW; SRS/code review and initial publication are complete under Plan Rev51.
- Canonical working SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.5-draft with matching Data Table Register v2.5-draft; neither has owner content sign-off.
- Rev45 reconciles existing product directions and records the earlier local working-tree source snapshot. Rev51 adds §32.6 for fetched `origin/dev` `4749451080f49243464d40a464b8f83a03ae77bb`, preserving the distinction between main API, separate StoryRun-lite fixture integration, Modal dev workers, and product target requirements.
- Current source review confirms code/configuration presence only. Main-app AI dispatch and durable AI Jobs remain gaps; separate StoryRun-lite background tasks do not satisfy the durable target. Existing Rev44–46 worker evidence is attributed but was not rerun for Rev51.
- Evidence: `evidence/EV-063-55_SRS_SYSTEM_CODE_ALIGNMENT_REV45_20261106.md` and `evidence/EV-063-56_SRS_PUBLICATION_REV51_20261106.md`.
- Published branch: `docs/feat063-rev45-srs-code-alignment-20261106`; SRS package commit `620386fb227e2d8b76c48e72ad22892e3b0c1c53`. Fresh fetch matched the remote branch at that SHA.


## As-built SRS alignment — Plan Rev43 (2026-11-06)

- Lifecycle: REVIEW; SRS v2.4-draft and matching Data Table Register add a current implementation snapshot without replacing the v2.3 target requirements.
- Canonical SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.4-draft, unsigned. §32 distinguishes backend code, mounted API, local database and Modal dashboard observations from target behavior.
- Read-only snapshot: local OpenAPI 111 paths / 124 operations; local PostgreSQL Alembic `20261028_ll_0001`, 41 application tables (34 `public`, 7 `lesson`). Full table list and AI/database access boundary are in EV-063-33 / Data Table Register §§14.5–14.6.
- AI clarification: owner selected Qwen3.5-VL, FLUX.3, Whisper, optional SAM 2.1, with Modal as the inference-host direction; Q159 is resolved as Platform Admin + Teacher may initiate AI suggestions, Parent may edit authorized drafts only. Deployment and backend integration are separately qualified.
- No requirements were deleted; API and database checks were read-only; no database writes/migrations or AI-provider calls were made for this amendment. The SRS remains unsigned. Approval: Plan Rev43 hash is recorded in root and feature approval registers.
- Evidence: `evidence/EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md`.

## Six-milestone roadmap review — independent round 3 ACCEPTED — 2026-11-03

The owner accepted the six-milestone Parent/Teacher roadmap as a planning baseline using the existing SRS v2.3-draft unchanged; the SRS remains unsigned. Independent read-only round 3 accepted the preceding roadmap bytes with no remaining finding in scope. The roadmap now records the owner's planning-baseline decision and follows SRS §8.1's Parent-before-Teacher ordering. No M2–M6 implementation is approved. Rev49 handled the initial review; Rev50 adds the round-2 quota/lesson/lifecycle/model/A2/B-ID gates and corrects the D-130 and DTR explanations; Rev50A synchronizes the historical backlog pointer and B4b/B10/B13 summaries. See `plan/ROADMAP_REVIEW_FIX_PLAN_REV50_20261103.md`, `plan/ROADMAP_REVIEW_FIX_PLAN_REV50A_BACKLOG_POINTER_20261103.md`, the roadmap, and `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`.

M1 review round 3 is ACCEPTED for synthetic local demo scope. The local A2 closeout records ACCEPTED/COMPLETE within scope, while disclosing 58 retained synthetic rows in shared `sketch2life`, unreconciled physical schema/Alembic history, and one baseline mypy issue. These residuals remain M2 entry gates; no cleanup is authorized here. The A2→B1→B2 sequence is a separate FEAT-064 coordination chain and may temporarily take execution priority over M2–M6. The current phase must be checked in its active implementation thread; do not infer it from a draft goal or old closeout.

The cloud reviewer was correct about the D-130 collision, D-114 summary duplication, B0–B13 plan provenance mismatch, and DTR line-ending explanation. Rev49's D-130 reassignment and DTR uncertainty were mistakes in our prior disposition, not cloud-review errors. The source-register and current-phase comments remain visibility limits when the cloud review has only remote refs; they do not establish the local state.

Independent review round 3 was performed in thread `01a1a205-1441-73e0-9170-6fdc4d591472` (`gpt-6-luna`, effort `max`); all 12 pinned hashes matched and the verdict was **ACCEPTED** for the reviewed roadmap hash. The owner subsequently adopted the current SRS as the unchanged planning baseline and recorded D-132; this is not an implementation approval. See `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md` for the verdict and remaining owner gates.

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

## Milestone 1 independent review fixes — 2026-11-03

The owner approved all six findings and the approval entry. Runtime and handoff fixes are implemented; offline regression: 163 passed, 1 PostgreSQL-dependent skipped; isolated PG17/loopback/singleton regression: 36 passed. No Modal rerun. Status: FIXED — XONG-CHƯA REVIEW; not ACCEPTED. See `evidence/MILESTONE1_REVIEW_FIX_REPORT_20261103.md`.

## Milestone 1 review round 2 — 2026-11-03

The follow-up review identified an attach-replay race and missing public StoryRun readiness. The replay path now rechecks the immutable receipt under the repository identity lock when mutable attach validation fails. A dedicated GET `/v1/story-runs/readiness` probes the latched runtime singleton state; `/health` remains liveness. PostgreSQL tests cover the HTTP overlap, PENDING recovery, confirmed-run cancel/create races, probe concurrency and terminated lock-owner session. Offline regression is 170 passed/1 PostgreSQL-dependent skip; isolated PostgreSQL is 46/46. Bruno completed two different synthetic Parent runs on the same task DB with real ClamAV and the Windows Job Object normalizer, while Vision used a local loopback stub. No post-fix Modal call occurred. See `evidence/MILESTONE1_REVIEW_ROUND2_FIX_REPORT_20261103.md`; status remains FIXED — waiting for independent review.

## Milestone 1 review acceptance — 2026-11-03

Independent review round 3 returned ACCEPTED for all six round-1 findings and both round-2 P2 findings. The review checked the current working tree and verified all 38 closeout-snapshot paths at review time. PostgreSQL/Bruno results remain implementation-run evidence; no tests or services were rerun by the reviewer. This accepts the synthetic local demo scope only. No post-fix Modal inference or production readiness is claimed. See `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND3_20261103.md`.


## Full BE Bruno API collection — 2026-11-03

After Milestone 1 was independently accepted, the owner requested a separate Bruno collection for the full BE. Approved plan SHA-256: 4488A7B739FDCC80246AFB590DDFC229B6DCB37FEB9600C5B9501B160E5E80ED. The collection and runtime OpenAPI inventory live in artifacts/be-full/; the existing StoryRun-lite guided collection is preserved. Current schema union: 136 mounted operations / 122 paths, with 11 historical unmounted candidates excluded from runnable requests. Profile counts and the one-route difference from the Rev31 static inventory are documented in artifacts/be-full/README.md. The structural validator, Ruff, harness, security and architecture validators pass. Bruno CLI 4.3.0 parsed all 136 requests, and its local docs generator listed all 136 request names. A limited safe loopback smoke passed health 200, process-local synthetic session create 201, and session read 200 with AI disabled and no DB URL. DB-backed BE1/Lesson Library routes and StoryRun-lite runtime flow were not run. The MCP request listing does not discover the new path. See evidence/BE_FULL_BRUNO_COLLECTION_REPORT_20261103.md.

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

## Rev52 completion - non-video Modal AI reliability

- Status: COMPLETE WITH FINDINGS on `feature/feat063-modal-ai-reliability-20261106`; implementation and evidence are local to the isolated worktree.
- Eight enabled non-video workers passed after the logging and story-contract fixes. Optional `drawing.segment` is still disabled and stops at its workload gate without inference. Video was not called.
- Parent API verification covered 33 expected request outcomes and a separate four-request story confirmation/resume. Parent drawing used a live HTTP-to-Modal call; story HTTP used a validated fixture while its Modal worker was verified separately.
- API readiness is not implied for worker-only workloads. Parent guide, Teacher deck, lesson suggestion/visual and speech product endpoints remain NOT_IMPLEMENTED; see the consolidated result report.
- Worker/caller phase logs retain only allowlisted diagnostics; no prompts, generated text, child/media payloads or raw Modal logs are persisted. Modal apps are stopped, the disposable PostgreSQL container is exited, and registry switches remain disabled.
- Verification: 97 Modal tests and 59 focused backend tests passed; Ruff, Python compilation and `git diff --check` passed.
- Full matrix, timings, root causes, API boundary, output hashes and cleanup evidence: `evidence/nonvideo_modal_ai_reliability_20261106/API_AND_AI_MODAL_RESULTS_20261106.md`.

## Rev53 SAM 2.1 gate retest - 2026-11-06

- Status: COMPLETE WITH FINDINGS under the approved one-shot synthetic scope. The L4 worker envelope now accepts `drawing.segment`; the product workload registry remains `enabled: false`.
- Root cause of the previous pre-inference rejection: `drawing.segment` was missing from `contracts.py::L4_WORKLOADS`, while the dedicated worker used the L4 envelope. This was a parser allowlist mismatch, not a Modal GPU scheduling or checkpoint failure.
- Live result: pinned SAM 2.1 Hiera-Small checkpoint preflight passed; one synthetic GPU inference passed at the worker/output-contract level. Model revision `2b90b9f5ceec907a1c18123530e92e794ad901a4`; checkpoint SHA-256 `6d1aa6f30de5c92224f8172114de081d104bbd23dd9dc5c58996f0cad5dc4d38`.
- Quality limit: visual inspection shows the mask selects the central body only and misses the butterfly wings, head and antennae. This is a partial mask, not acceptable whole-object segmentation; SAM 2.1 remains an optional development candidate, and OpenCV/Pillow remains the baseline.
- Timing: checkpoint call elapsed 27.051 s (worker 0.734 s; checkpoint already present); inference caller wait 31.896 s (worker 7.924 s); total run 61 s. No video call was made.
- Cleanup: dedicated Modal app stopped and verified at 0 tasks; shared volumes/checkpoints retained. Full results and visual review: `evidence/sam2_gate_retest_20261106/RESULTS.md` and `visual_review.md`.

## Plan Rev54 - SRS v2.5 and Modal AI integration to dev

- The approved SRS and Modal AI branches are merged locally on `codex/feat063-srs-ai-dev-integration-20261106`; merge commits are `634e0e20f56cbfa6101ece6e67f3e4267a30ae92` and `6bbb375a359fb78f06585963b8ee9f7bfc2246ff`.
- FEAT-063 v2.5-draft is the canonical working SRS, still unsigned. Its SRS authority pointer and companion Data Table Register match the selected source branch byte-for-byte.
- All four D-144/D-145 records are retained; SRS decisions were renumbered D-148/D-149 to keep the integrated decision register unique.
- Rev52/Rev53 AI code and existing verification evidence are preserved. SAM2 remains product-disabled due to partial visual mask coverage. No AI/video runtime calls or test suites were rerun during this merge.
- Detailed hashes, evidence limits and results: `evidence/EV-063-57_SRS_V25_AND_MODAL_AI_DEV_INTEGRATION_20261106.md`.
- Current execution status: complete; normal push to `origin/dev` succeeded and the remote tip was verified. Integration commit: `47e5308a5c547df8dab5f3c560f949ee925f441e`; final closeout push is verified in the repository state.

## Rev55 — independent diagram readiness assessment

The owner requested publication of the immediately preceding two-agent assessment. Two agents independently reviewed the same canonical v2.7-draft SRS/Register commit 98cc34a39af279560b5f8d39f18939a376535834. Most diagram inputs are draftable with explicit open questions; Screen Flow is not sufficiently specified for an approved navigation flow and ERD physical is blocked on DDL/schema reconciliation. The assessment changes no product decision and does not sign off the SRS. See evidence/EV-063-60_TWO_AGENT_DIAGRAM_READINESS_ASSESSMENT_20261107.md and Plan Rev55.

## Plan Rev57 — substantive diagram-input remediation

The owner authorized substantive documentation updates for G01–G10 and explicitly requested commit/push. Work is scoped by Plan Rev57 and its approval record, based on fetched Rev56 SHA ae5707ca188d01d9719ed959b62d768ae927912d. SRS and Data Table Register remain v2.7-draft and unsigned. Owner decisions are not resolved by this package. Source review is limited to the selected commit; no product code, database or migration was changed.

## Plan Rev67 — Parent Android profile, consent, and story flow — 2026-11-10

- Implemented the approved Parent slice: Parent-owned profile revisions and versioned consent, authenticated StoryRun context snapshots/resume, physical drawing camera/gallery upload, adult subject confirmation, structured story generation/rewrite/review, and optional topic-only line-sketch dispatch.
- Added an additive PostgreSQL migration and the versioned API contract in `artifacts/PARENT_API_CONTRACT_REV67_20261110.md`. Product SRS remains the unsigned v2.7-draft with local amendments through Rev60; this implementation note does not change requirements.
- Consent text/version are read from the single root `.env` through blank placeholders in `.env.example`; empty configuration fails closed. The owner approved proceeding but did not provide copy/version in this thread, so no legal text was invented and no real-child data was used.
- Static review: mobile TypeScript passed; changed Python files compiled; migration graph AST review found no missing parent revisions and the new migration joins all 12 pre-existing heads into one. Repository security validator passed (7,157 publishable files); `git diff --check` passed.
- Limits: no product tests, database migration application, Docker, Firebase, or live Modal request was run under this plan. Ruff and Alembic CLI were unavailable in the local Python environment; ESLint was blocked by the repository's unresolved `jest/globals` plugin configuration.
- Remaining Parent SRS gaps include second VLM reinterpretation after adult subject correction, voice/Whisper, video generation/playback and subsequent activities, history/cancel/delete, durable AI-job reconciliation, and temporary sketch-guide cleanup/safety validation. See the API contract and `evidence/EV-063-76_PARENT_ANDROID_PROFILE_CONSENT_STORY_FLOW_20261110.md`.

## Parent catalog-first activity suggestions and publication — Plans Rev78/78A/78B (2026-11-11)

- The owner-directed flow uses activities from published/shared lesson versions that the Parent may access. AI receives bounded candidates and minimized profile, drawing, topic and adult-confirmed narration context; it selects catalog activities or returns exactly three temporary drafts when none fit. Backend quality/safety rules remain hard gates.
- The Expo Parent activity/story screens call the existing Parent-owned API boundary. The ACT demo catalog is not used as a production candidate source.
- Exact lesson pin data now persists on StoryRun input revisions, including version/hash, age-band reference/version and activity content. Migration 20261110_parent_lesson_pin follows 20261110_parent_profile_story_context. The migration has not been applied to PostgreSQL.
- Focused Parent service/worker tests previously passed 28/28; one post-refinement Modal inference was cancelled after 976.326 seconds before output, so the live quality-gate result remains unknown. Dev catalog had zero eligible published/shared activities. Video was not called.
- The canonical SRS remains v2.7-draft Rev60 and unsigned. The user's catalog-first clarification is recorded as D-172; SRS reconciliation remains open.
- Plan, approval and synthetic evidence: plan/PLAN_REV78_PARENT_CATALOG_FIRST_ACTIVITY_SUGGESTIONS_20261111.md, plan/PLAN_REV78A_PARENT_ACTIVITY_GATE_REFINEMENT_20261111.md, plan/PLAN_REV78B_PARENT_CATALOG_PIN_AND_PUBLICATION_20261111.md, and evidence/EV-063-87_PARENT_FULL_API_UI_E2E_20261111/.

## Rev81 current owner direction and execution baseline — 2026-11-12

- Current plan: `plan/PLAN_REV81_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112.md`, approved SHA-256 `494F55A33D56CD0E90D6217A29A6719E08DE2C3ED4CB8D251DF2EC2AFA75960F`; implementation status and evidence are in `evidence/EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/`.
- Owner clarified adaptive 4–8-stage progressive drawing guides, on-demand guide generation for an authorized lesson missing one, and HTTPS YouTube/Vimeo embeds only. The guide range conflicts with Rev60's 3–5 text; Rev60 and the DTR remain unchanged and unsigned.
- Docker must reuse the existing deployed non-video Modal Apps, invoke selected actual workers once with an internal warmup-only control envelope (no product request or output), then call each app's `/health`. It does not redeploy/update Apps each Compose start. Warmup/model-load and idle scaledown time incur compute charges; no permanent minimum GPU container is retained, and shared Apps are not stopped on Compose shutdown. Video and disabled SAM2 are excluded.
- Modal's Dashboard Containers surface is for inspecting and controlling runtime containers; it is not a separate app/deployment mode. Use the existing App/Function architecture and the bounded warmup lifecycle for this system. Deployed Apps may remain listed while their Functions have zero live containers and no compute use after scale-to-zero.

### Rev81 Android/Modal E2E result — 2026-11-12

- Parent was exercised on Android emulator with the live Docker API/Auth Emulator and a generated synthetic deer drawing. Auth/profile/StoryRun/photo flow was reached; local synthetic authorization is not legal consent.
- FLUX Parent guide failed its cumulative-stroke quality gate. Qwen3.5 drawing inference completed but JSON parsing failed (`MODAL_MODEL_OUTPUT_INVALID`); the API first returned 504 `MODAL_OUTCOME_UNKNOWN`, and the run remains `AWAITING_RECONCILIATION`. No retry, activity/story request, or video request was made.
- Parent history collection GET returned 405. Teacher presentation was blocked by absent local Teacher/org/class or Teacher-authored reviewed lesson data (one Parent library seed exists) and unresolved Modal language/audio functions. Modal health sidecar remains DEGRADED.
- No AI artifact passed its gate; no AI result screenshot was created. Detailed evidence: `evidence/EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/parent_teacher_e2e_20261112/REPORT_PARENT_TEACHER_ANDROID_MODAL_E2E_20261112.md`.


## Rev82 AI gate and Docker/Modal follow-up — 2026-11-12

- The approved activity JSON/schema moderation and Qwen decoder fixes remain in place. Existing Teacher Qwen lesson-plan and Sketch Deck API calls passed (240.981 s and 90.303 s respectively); the deck is a five-slide draft requiring Teacher review.
- The approved FLUX progression-gate adjustment and 10 focused mask tests passed. One real post-fix Teacher lesson-visual request still failed: transition Step 4 → Step 5 retained 9.46%, below the approved 12% hard floor. FLUX inference itself succeeded; the API returned terminal 502 `MODAL_WORKER_FAILED_TERMINAL` after 398.967 s. No retry or further paid call was made.
- Parent fresh AI E2E remains incomplete. The existing synthetic Parent run is still `DRAWING_OUTCOME_UNKNOWN` and non-retryable; no retry was made. Parent guide output from an earlier successful run was reused without another inference.
- Rev82 plan §21 explicitly stops further Modal calls/deployments after the one post-fix visual failure. A possible next gate change (single 8-step transition floor from 12% to 8%) is only a proposal, not implemented or deployed.
- Docker services were healthy; FLUX CPU `/health` passed without GPU/inference; `modal container list` returned empty after completion. No shared Modal App was stopped.
- Detailed result and numeric logs: `evidence/EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/parent_teacher_e2e_20261112/REPORT_REV82_POSTFIX_DOCKER_MODAL_20261112.md`.

### Rev82 §22 bounded real AI continuation — 2026-11-12

- The approved 8% single-transition floor was deployed and the real Teacher lesson-visual API returned a review-required eight-step FLUX candidate. Its mechanical gate passed; visual review still found sparse/repeated middle construction stages, so it remains a draft.
- A fresh Parent account was created through the local registration API/Auth Emulator. Synthetic child profile, local test consent, StoryRun, generated deer drawing, Qwen3.5 drawing analysis (`con hươu`, confidence 0.90, topic match) and adult subject confirmation all passed.
- Catalog-first activity inference returned valid JSON with `NO_MATCH` and three fallback drafts. Backend returned 502 `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` because one activity had a positive unsafe-action match and two did not name an outdoor setting. This was a policy gate rejection, not a parser or Modal worker failure. Story generation was correctly skipped.
- The fallback prompt now explicitly requires each activity to name its own outdoor location and use safe adult-prepared materials. The hard safety/outdoor gates were retained. Focused tests: 30 passed. The prompt change was not deployed or live-tested; Rev82 §22 forbids retrying the already-used activity workload. The owner stopped the three Modal apps after the run; they were not restarted.
- No video inference, credentials, Firebase tokens, production Auth or real-child data were used. Full timings, structured worker phases and actual synthetic AI outputs: `evidence/EV-063-90_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112/parent_teacher_e2e_20261112/REPORT_REV82_LIMITED_PARENT_TEACHER_20261112.md`.

## Rev84 — real Teacher SVG Modal UI verification (2026-11-13)

- One authenticated synthetic Teacher Web session submitted the actual SVG illustration form and received a real Qwen3.5 Modal result. No fixture or dataset was used. API returned HTTP 200 and a non-persisted, review-required DRAFT with 18 rendered paths.
- The sample rendered as a geometric young deer. It proves the bounded UI/API/Modal/render path only; Teacher review remains required, and broad illustration quality is not verified.
- The Modal app was absent in the configured dev environment and was deployed once. CPU /health verified the pinned checkpoint; after the one inference there were no live Modal containers. Local SVG capability was disabled again; isolated Docker/UI/browser processes were stopped.
- OpenAPI generation still returns HTTP 500 for the existing missing Rev37 SVG catalog contract schema. The direct authenticated SVG route worked. The API immediate worker log summary missed the terminal event due Modal log indexing delay; a later read-only query found worker_succeeded.
- Detailed result, actual response/vector and rendered screenshot: evidence/EV-063-94_TEACHER_SVG_MODAL_UI_20261113/REPORT.md.
## Rev85 Teacher SVG dataset-conditioned attempt — 2026-11-13

- A pinned three-example animal SVG reference pack and deterministic local topic lookup were deployed to the existing Teacher Qwen3.5 Modal function for one approved real authenticated UI comparison.
- The one UI request for non-personal con hươu sao / 60 months / warm_storybook returned HTTP 502 MODAL_WORKER_FAILED_TERMINAL, request ID 37bdb1ee-24a1-4de2-866b-8051acf77143.
- Failure occurred during dataset reference validation before model loading/inference. The loader rejected prompet-sample-cat/path-026 because its stroke_width=20 exceeds the unchanged parser/schema maximum of 12; the loader validates the entire pack even when the request would select the quadruped dog exemplar.
- No SVG or render was produced, so there is no Rev84 visual comparison and no verified quality gain. Do not describe the dataset-conditioned generation as working.
- The single-call allowance is exhausted. No retry/deploy is authorized by Rev85. Local flag is false; shared Modal app remains deployed. The post-run container-list CLI timed out, so scale-to-zero is unverified. See evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/REPORT.md.


## Rev86 Teacher SVG dataset-pack correction and real comparison — 2026-11-13

- Approved plan/hash: `plan/PLAN_REV86_TEACHER_SVG_DATASET_PACK_FIX_20261113.md`, SHA-256 `144EA85E3314A9CC86659D749DDFDD9D317C306C5C134BFE6035F975C395696D`.
- Preserved the raw pinned dataset snapshot; excluded only the invalid cat from the active pack; dog/quadruped and rabbit references passed the exact strict worker parser. Active pack SHA-256: `319d25932c8d4bc8c362b6af19ecded75cb1015d7f8cc19387c9685a74349af0`.
- One real synthetic Teacher UI → API → Modal request succeeded technically (HTTP 200, Qwen3.5, 19-path non-persisted review draft). Visual objective did **not** pass: the deer reads rabbit-like because it lacks branched antlers. Limbs/grounding and detached-object criteria improved; overall comparison is mixed and single-sample.
- API worker summary omitted the terminal event despite successful phases. The local API container has its feature flag false but could not bind occupied port 8000 and remains `Created`; the separate healthy API was left untouched. Modal scale-to-zero was not verified. No retry, tests, migration, or video occurred.
- Full timings, exact IDs, hashes, visual rubric, artifact links and cleanup limitations: `evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/REPORT.md`.

## Rev87.4 curated SVG source + stroke-authoring skill — 2026-11-13

- Owner direction: prefer one curated, professionally authored SVG source plus an authoring skill for ordered stroke construction; do not require a dataset that already contains stroke order.
- Added one CC0 Arcadia Science `Gallus gallus` tricolor-stroke SVG as visual reference only (Zenodo DOI `10.5281/zenodo.17203578`; archive MD5 `a845bf16730238334f39c7cfbc1d4703`; selected SVG SHA-256 `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`) and upstream MIT `whiteboard-animation` skill v0.1.0 as authoring guidance. The skill is not a runtime service.
- Code now packages/verifies the source, rasterizes it in memory only for allowlisted chicken topics, includes source provenance in an adult-review draft, and applies the ordered-open-stroke guidance to Qwen3.5 plus the strict topology gate. Other topics do not receive this reference.
- Static source/JSON checks and Teacher UI build passed. Parent typecheck remains blocked by pre-existing Expo environment type declarations. The single approved Modal deploy attempt failed before updating the app due to a Windows-to-POSIX remote path; the local path fix was made, but the plan's one-attempt stop condition prohibits redeploy/inference. No live guide or generated image is verified. See EV-063-101.
## Rev87.5 bounded deployment retry — 2026-11-13

- Owner authorized one additional Modal deployment attempt after Rev87.4 failed before app update. Final approved plan hash: `94547CEC22E0638788358EEEE8DAFBD304D3BF49837DC9CA246CE0DB7D3BF155`.
- The temporary API built from the current worktree passed local Docker health and mounted the Parent guide route (unauthenticated GET: 405). `/openapi.json` returned 500 because `SVG catalog contract` is missing from runtime OpenAPI components.
- Modal deploy exited 1 after image-build logs with a Windows `charmap` output-encoding error. Deployment state is unknown; no post-failure Modal status/health request was made. No Parent UI login, authenticated AI request, GPU inference, generated SVG, or screenshot occurred.
- The default Postgres/Firebase startup attempt hit the existing Rev79 Postgres host-port allocation. Rev79 services and the original API were left untouched; the temporary API was stopped/removed. The task-created Firebase container was removed without its volume; default Postgres container remains Created/inactive with its volume preserved. No migration, seed, account creation, or `.env` edit.
- Rev87.5's single attempt is consumed; no further deploy/inference without a new approved amendment. Evidence: EV-063-101 `runtime-attempt-2.json` and `REPORT.md`.

## Rev87.6 Android Parent UI attempt — 2026-11-13

- API health/OpenAPI and the mounted Parent guide route passed after the SVG projection fix. Expo Android bundle, emulator launch, synthetic sign-in, profile load and current-consent preflight passed.
- The existing open Parent run could not be resumed because required run data is incomplete. UI blocks new sessions while that run is open; no run/profile/consent mutation or Modal request was made.
- No Modal deploy/health/GPU inference occurred. Temporary API, Metro and emulator were stopped; shared Postgres/Firebase Auth were left untouched. See EV-063-101 `runtime-attempt-3.json` and `REPORT.md`.


## Rev87.9 — Android Parent flow runtime evidence — 2026-11-13

- **Status: PARTIAL; flow stopped before story inference.** Real Android signup/Firebase Auth Emulator, synthetic profile, context confirmation, generated chicken drawing upload and adult subject confirmation passed. Two real Qwen3.5 Modal inferences passed technically: drawing analysis (HTTP 200, 38.191 s) and activity suggestions (HTTP 200, 121.894 s). No fixture was used.
- The optional SVG guide lookup failed twice with `DATABASE_UNAVAILABLE`: the shared dev DB is at `20261110_parent_lesson_pin` and lacks three SVG catalog/review tables. No migration was run; guide was skipped.
- The catalog returned two butterfly candidates for chicken; Qwen produced three chicken fallback drafts. The UI has no main-activity selector; continuing reached a story HTTP 422 because `ParentStoryRequestV1` requires a selected activity request/ref pair while the UI API sends only the understanding revision. No activity was injected, and no story Modal call or video occurred.
- One fallback draft uses small grains/beans with an adult-supervision warning; current technical gate passed it. API worker telemetry also logged `worker_started_without_terminal_event` for successful results. These are open product-safety/observability defects, not approved content.
- The temporary API, Metro and emulator were stopped; shared Postgres/Firebase/Redis/MinIO/ClamAV, Modal apps and model volume were preserved. `.env` and source were not changed. See EV-063-101 `runtime-attempt-4.json` and `REPORT.md`.

## Rev87.10-A — Parent SVG attempt — 2026-11-13

- Owner authorized one optional Parent SVG guide attempt. The actual Android UI exposed the AI fallback after catalog lookup failed; the focused fallback test passed (4/4).
- The catalog GET returned 401 before DB access because the temporary API used project `sketch2life-local`. After setting only the task container to the existing app/Auth Emulator project `sketch2life-dev`, the one AI-draft POST still returned 401 `INVALID_IDENTITY_TOKEN`; the Modal worker was not dispatched, so there is no SVG output/render. Exact verifier cause is unresolved.
- No catalog retry, Modal inference/deploy, story, video, migration, seed, `.env` edit or shared-service stop. Task API/Metro/emulator stopped; shared services preserved. See EV-063-101 `runtime-attempt-5.json` and `REPORT.md`.


## Rev87.10-B/C Parent Auth and SVG runtime result — 2026-11-13

The prior 401 was caused by a stale API container missing `FIREBASE_AUTH_EMULATOR_HOST`, not by the Parent token or Firebase project ID. Current `compose.yaml` already injects `firebase-auth:9099`. A current-worktree task API with the root `.env` authenticated a fresh local emulator token and `/api/auth/v1/me` returned 200, role `parent`, state `active`; signature/issuer/revocation checks stayed enabled. The task API is available on the configured host port 58000. The old API on port 18000 was left untouched and remains misconfigured.

The catalog still returns 503 `DATABASE_UNAVAILABLE` because its tables have not been migrated. The single permitted Parent SVG request reached Qwen3.5 Modal and failed after 820.282 s with worker error `SVG_TOPIC_GUIDE_PATH_INVALID` during output parse/contract validation; no valid SVG exists. API-side log summarization missed the worker's terminal failure, but a posthoc read-only call-log query found it. Android UI was not tested because SDK/adb/emulator were unavailable. One inference allowance is exhausted; another SVG attempt needs a separate approval. Full safe trace: `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-6.json` and `REPORT.md`.


## Rev87.10-D Parent SVG catalog database repair — 2026-11-13

The shared local development Postgres was at `20261110_parent_lesson_pin` and lacked the three SVG catalog tables. Read-only preflight confirmed all 14 existing Core asset rows satisfy the expanded owner-scope check. Applied only `20261113_svg_catalog_review` transactionally; other Alembic heads were not upgraded. All three tables, the validated check and two immutable triggers now exist; the Core asset count remains 14. Authenticated Parent catalog GET is HTTP 200 with zero items; no fixtures or AI were used. Database blocker resolved; catalog remains empty. See EV-063-101 `runtime-attempt-7.json` and `REPORT.md`.
## Rev87.10-E Parent SVG runtime result — 2026-11-13

After the catalog migration, the real authenticated Parent catalog request returned HTTP 200 with zero items. One generic topic request reached the deployed Qwen3.5 Modal worker and failed after 223 seconds at `output_parse_and_contract_validation` with `SVG_TOPIC_GUIDE_PATH_INVALID`. The API/auth/database paths passed; no valid SVG was returned and no retry was made. The worker's strict path parser rejected an SVG path field, but raw model output was not logged, so the specific invalid field is unknown. See EV-063-101 `runtime-attempt-8.json` and `REPORT.md`.

## Rev87.10-F/G/H Parent SVG worker correction and final attempt — 2026-11-13

The worker's constrained-decoder crash was corrected by removing redundant length keywords from regex-constrained `path_id` and `d`; parser-side bounds and all SVG safety/quality gates remain. Focused tests passed 4/4, compile passed, and one deployment completed. A single real authenticated Parent request passed auth/catalog preflight; Qwen3.5 inference completed but the output parser returned `SVG_TOPIC_GUIDE_JSON_INVALID` after 364.985 seconds of inference (388.003 seconds total worker time). API logged HTTP 502; no valid SVG was returned. The client surfaced a `TypeError` after 307.345 seconds, with exact transport cause not captured. Source order parses JSON before checking EOS/max-token truncation, so malformed vs truncated output is unresolved. The Rev87.10-H inference limit is consumed; no retry or video was run. Details: `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-10.json` and `REPORT.md`.

## Rev87.10-I Parent SVG truncation diagnosis — 2026-11-13

The worker now checks EOS/token cap before parsing and emits safe token/EOS diagnostics. Focused worker tests passed 6/6, worker compile and the backend safe-log-summary test passed; one language/audio app deployment completed. The task API alone was rebuilt and is healthy (HTTP 200); shared services were not restarted. The single authenticated Parent API request passed health, Auth Emulator sign-in, Parent `/me`, and empty `con-ga` catalog checks, then returned HTTP 502 after 395.670 seconds. Qwen3.5 reached the 6,144-token ceiling without EOS (`MODAL_SVG_TOPIC_GUIDE_OUTPUT_TRUNCATED`); no validated SVG was returned. The failure is now isolated to output-budget truncation, not cold start, decoder setup, auth or catalog. No retry is authorized by Rev87.10-I. Safe details: EV-063-101 `runtime-attempt-11.json` and `REPORT.md`.
## Rev87.10-M/N/O/P Parent chicken SVG diagnosis — 2026-11-14

- Worker/parser, auth, catalog, and request timing now pass. Focused worker tests passed **10/10**, compile passed, backend topology tests passed **2/2**, and scoped diff checks passed. The language/audio Modal app was deployed once.
- Final real Parent request reached Qwen3.5 and completed in about **253 s** under the 1,800-second deadline. API returned HTTP 502 `SVG_CHICKEN_ANATOMY_ENDPOINT_DISCONNECTED`; this is a hard geometry rejection, not a timeout.
- Safe in-memory checks: neck endpoint misses the head; beak remains shorter than 12 units; both legs fail the >40-unit descent rule. Body shape, overlaps, wing/tail/comb endpoints, beak start, ground baseline, and foot alignment pass. No validated SVG was returned.
- Rev87.10-P's single inference allowance is consumed. No retry, output repair, gate bypass, video, or further deployment/inference occurred. See EV-063-101 `runtime-attempt-20.json` and `REPORT.md`. SRS §§1–31 unchanged; §32.23 contains as-built evidence only.

## Rev87.11 Parent source-derived SVG guide — 2026-11-14

The pinned Arcadia CC0 Gallus gallus anatomy reference now has a separate, versioned 19-path / six-stage child drawing derivation. A final Docker-image route request for con gà returned HTTP 200 (SvgTopicStrokeGuideSourceDraftV1) in 0.027 s, passed existing sanitization and chicken anatomy gates, and did not dispatch Modal. SVG and raster artifacts plus the request record are in EV-063-102. Focused backend tests passed 7/7; focused mobile tests passed 6/6. This is a source-specific private draft and focused route verification, not a Firebase or Android end-to-end test; other topics still use the existing Qwen/Modal fallback. SRS §32.24 records this as-built result; target §§1–31 remain unchanged.

### Rev87.11-C — progressive strokes separated from finished illustration

Visual review found the first color-underlay rendering mixed the finished chicken pose with the separately authored drawing and made the stroke sequence hard to follow. The Parent screen now defaults to progressive strokes on white; a separate toggle shows the pinned full-color SVG and returns to the same step. The guide is a new 20-path/six-stage revision that faces the same direction as the reference and passes existing hard topology checks. The real source-derived route returned HTTP 200 in 0.045 s without Modal. Focused backend checks passed 9/9 and mobile checks passed 5/5. Eight actual SVG artifacts were rendered and inspected. This is not Android E2E or educator approval. See EV-063-102 `REPORT.md` and `runtime-attempt.json`.

### Rev87.11-F — Parent hen drawing sequence checked against supplied HTML — 2026-11-14

The supplied HTML was run and its seven part-by-part stages inspected before the guide was revised. V5 now follows that teaching rhythm in eight stages and depicts a simplified left-facing hen with a feathered wing and raised tail. The pinned Arcadia color illustration is a separate view, never an underlay. V4 is preserved with its hash; no topology gate was relaxed. The local Parent source-derived route returned HTTP 200 with 16 paths/eight stages in 0.082 s without Modal dispatch. Backend focused tests passed 12/12; mobile guide contract tests passed 3/3. Eight staged route SVGs, final strokes and separate reference were rendered at 1024×1024. This is not Firebase/Android E2E or educator approval. See EV-063-105 `REPORT.md`; SRS §32.26 records the as-built result only.

### Rev87.11-H — exact-source-path Parent chicken guide — 2026-11-14

The owner clarified that guide strokes must form the same pictured animal, not newly authored childlike geometry. V6 is preserved as history; the active pinned-chicken guide is V7, which uses the exact 77 sanitized path geometries from the pinned Arcadia CC0 `Gallus gallus` SVG, assigned once across eight progressive stages. Its separate full-color reference is not drawn beneath the guide. The local Parent route returned HTTP 200 in 0.090 s with all 77 exact path matches and no Modal dispatch. Backend checks passed 9/9; mobile guide checks passed 8/8; all eight cumulative stages were rendered and visually inspected. This is a focused TestClient route check with identity/database overrides, not Firebase or Android E2E. The chicken guide remains a private draft requiring adult/educator review; unsupported topics retain Qwen/Modal. See EV-063-107 `REPORT.md`; SRS §32.27 is as-built evidence only.

### Rev87.13 — Parent guide dataset expansion and final color illustration — 2026-11-14

Added a pinned OpenMoji 17.0.0 source pack for turtle, butterfly and dog beside the existing Arcadia chicken guide. The Parent API source resolver and mobile progressive guide now carry the selected source's original color illustration, shown beside the completed line drawing on the last step with source/license links. Noto candidates were rejected after visual curation and are absent from runtime. Manual source previews were inspected; implementation code was not exercised through an app/API/Android run, and no automated tests were run for this change. See `evidence/EV-063-108_PARENT_MULTI_DATASET_SVG_GUIDES_20261114/REPORT.md` and SRS §32.28.

### Rev87.14 — moderately detailed Parent Openclipart guide sources — 2026-11-14

Added selected Openclipart butterfly and turtle color/line pairs as a more detailed option than the prior emoji-style guides. Each guide uses the source line-art paths across six progressive stages and carries a matching original-color reference; the existing OpenMoji and Arcadia sources remain. The dog pair was rejected for dense fur contours and an alternate turtle outline for pose mismatch. Manual preview review found moderate child-friendly detail, but no educator/child evaluation. No automated test, build, API, app, Android, or Modal run was performed. See `evidence/EV-063-109_PARENT_RICHER_OPENCLIPART_GUIDES_20261114/REPORT.md` and SRS §32.29.

### Rev87.15 — broad Openclipart catalog on Modal Volume — 2026-11-14

Added an explicit CPU-only Modal importer for the public `kawwaaa/openclipart` corpus. The intended durable store is the dedicated Volume v2 `sketch2life-openclipart-catalog-dev` in `dev`; it retains original compressed shards, extracted CC0 SVGs, SQLite/FTS search index, SHA-256 values, and a revision manifest. The existing Qwen3.5 worker now has a read-only mount and plans 4–8 stages over exact source path IDs; it does not generate replacement geometry. Backend validation checks that those IDs and path data match the paired color source. The feature remains disabled by default.

Runtime is now verified on Modal `dev`: the full 18-shard corpus and SQLite/FTS catalog are `READY` on `sketch2life-openclipart-catalog-dev` Volume v2 (178,561 source rows; 1,923 guide-eligible; 110,284,614,262 total bytes). No dataset copy went to Docker or the repository. The deployed Qwen app `/health` reported the pinned checkpoint and catalog ready. One real synthetic `con mèo` inference reached generation but failed strict exact-path coverage validation (`SVG_CATALOG_STROKE_PLAN_PATH_COVERAGE_INVALID`); no retry, video, Parent API/UI, Android, or Teacher runtime was used. The raw output is intentionally not logged, so missing-versus-duplicate path counts remain unknown. Detailed result and worker/import logs: `evidence/EV-063-110_OPENCLIPART_MODAL_VOLUME_CATALOG_20261114/REPORT.md`. SRS §32.30 records environment-specific evidence only.

### Rev87.16 — Qwen catalog path-assignment fix — 2026-11-15

The Rev87.15 worker failure came from asking Qwen to cover all source path IDs across multiple arrays; the schema restricted each ID but could not enforce exact union coverage. The worker now requests a `SvgOpenclipartSourceStrokePlanV2` with every source path ID as a required object key mapped to one stage. Unknown keys and duplicate JSON keys are rejected; the parser checks stage bounds/nonempty stages and derives stage path lists in source order. Qwen still cannot generate or alter source geometry. Focused tests: 16 passed, 2 skipped because local Python lacks LMFE; the deployed worker's constrained decoder setup and parse path were exercised successfully. The language/audio app was deployed to Modal `dev`; CPU `/health` reported Qwen3.5-9B and the existing catalog ready. One real synthetic `con mèo` request returned a CC0 Openclipart kitten guide with 11/11 source paths across six stages, matching color-reference path identities, and all eight output checks passing in 86.088 seconds. No retry, child data or video. Parent API/UI/Android and Teacher presentation remain untested. Feature flag remains off by default. Detailed logs/output/preview: `evidence/EV-063-111_MODAL_QWEN_CATALOG_PATH_ASSIGNMENT_FIX_20261115/REPORT.md`; SRS §32.31 is environment-specific evidence only.

### Rev87.17–87.18 — Parent Modal API guide integration — 2026-11-15

Rev87.17 removed the full SVG corpora from the Docker API build and let absent optional local packs fall through to the Modal catalog. Its one real authenticated synthetic Parent request reached Qwen successfully but the API rejected the worker content because it checked the API entity schema instead of the worker content schema; this was a schema boundary bug, not an inference timeout. Rev87.18 separated those schema versions and one fresh API → Modal → API request passed: HTTP 200 in 102.946 seconds, Qwen3.5-9B, 11 exact Openclipart source paths in six stages, matching separate color reference, and all eight quality gates passed. The draft was not persisted and remains review-only. The temporary emulator identity and backend row were removed. All seven emitted SVGs parsed as XML. Focused pytest collection is blocked on the host because sqlalchemy is missing; no Android UI/video test is claimed. The feature flag remains false by default and was enabled only in the ignored local dev .env. See EV-063-112/113 reports; SRS §32.32 is as-built evidence only.

### Rev87.19 — Parent stroke-guide pedagogy review — 2026-11-15

Review of the real Rev87.18 kitten result found a structural teaching issue: the active Modal worker only assigns every existing source SVG path to a step, and the backend reveals those unchanged paths. The first step is the full source outline; later steps add face details and fur. That cannot teach construction from simple marks because source paths cannot be split, simplified, or omitted. The recommended fix is a separate, versioned construction-guide geometry contract conditioned on the dataset source, with the original color SVG retained as a distinct reference and the draft kept behind adult review. Review report: evidence/EV-063-114_PARENT_STROKE_CONSTRUCTION_REVIEW_20261115/REPORT.md. Implementation plan Rev87.19 awaits explicit approval.

### Rev87.22 — Parent guide API success did not pass visual review — 2026-11-15

Qwen's free-form path output was replaced by bounded geometry primitives rendered deterministically. Three real synthetic Parent API → Modal calls produced two validation failures and one HTTP 200. The successful response still showed incomplete, disconnected kitten geometry, and its Vietnamese step descriptions did not match the rendered marks. Treat this as a visual failure, not a working guide. Focused checks passed (Modal 34/34, backend 12/12, mobile 3/3); the language/audio Modal app is stopped. Rev87.23 will test source-derived drawable segments so the model selects order and copy without inventing geometry. See EV-063-118 and SRS §32.36; §§1–31 remain unchanged.

### Rev87.26/27 — Parent pinned Openclipart source sequence — 2026-11-15

The genuine `con mèo` response from Rev87.26 first returned HTTP 200 but failed visual review because the Qwen captions disagreed with the new marks; a second request returned HTTP 502 because the visual-review assignment contained one empty stage. Logs confirm both inferences completed, so the latter was not a timeout. After inspecting the spatial segment atlas and cumulative renders, the exact CC0 kitten source was mapped into seven stages using all 20 exact SVG-derived paths once. Rev87.27 uses that reviewed sequence only when both the asset ID and raw source hash match; Qwen remains responsible for catalog-query expansion/source selection, while other sources keep the existing Qwen draft/review flow.

The one Rev87.27 synthetic Parent route request returned HTTP 200 in 73.116 seconds with a private, non-persisted seven-stage draft and 20 exact source paths. Manual cumulative review found the cat recognizable by stage 3 and each caption aligned with its new marks. Focused tests passed (Modal 49/49; backend 12/12), compile passed and the app was stopped/verified with zero tasks. The source asset is monochrome; color-reference quality, Firebase/Android E2E, educator approval and child comprehension are not established. See EV-063-121 and SRS §32.37; §§1–31 remain unchanged.

### Rev87.28 — Parent paired-eye detail step — 2026-11-15

Review confirmed the live Rev87.27 guide split eye details across stages 4 and 5. The exact pinned kitten source now groups segments 10–15 into one step, so both eyes are detailed together. Focused worker tests pass 50/50; the saved genuine response was re-rendered locally as six steps and stage 4 visually shows both eye details at once. No Modal call or deploy was made: the original live response remains seven steps. See Plan Rev87.28, EV-063-122 and SRS §32.38.


### Rev87.29 — Parent non-kitten catalog results — 2026-11-15

One butterfly request failed before Modal because its 39-path bundled guide exceeds the API's 32-path cap (turtle sibling is 35 paths and was not attempted). One real elephant and one real fish Parent route → Modal/Qwen3.5 call each returned HTTP 200, but manual stage/render review rejected both: elephant instructions append irrelevant leg-ridge marks and begin with disconnected strokes; fish used a kitchen-scale SVG and repeated/truncated instructions containing Chinese characters. Do not treat generic catalog guides as reliable based on API 200. App stopped; no retries or child data. See Plan Rev87.29, EV-063-123 and SRS §32.39.
