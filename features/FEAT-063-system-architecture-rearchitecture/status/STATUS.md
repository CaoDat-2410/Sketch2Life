# Status
## Rev56 ten-group diagram-readiness alignment — 2026-11-08

- Lifecycle: COMPLETE for the approved documentation-only synchronization on the isolated diagram-readiness branch.
- SRS and Data Table Register remain v2.7-draft and unsigned. Rev56 adds a traceable successor input catalog and aligns UC-05, FR-T-10, FR-PL-20 and AC-56 to system random selection plus Teacher confirmation.
- Q-01 eligibility/consent/reselection/no-eligible/evidence details and the other owner/technical gates remain OPEN; no settled requirement was reopened.
- Physical ERD, final diagrams, and as-built diagram claims remain blocked by their stated approval/evidence gates.
- `git diff --check` passed; repository security validation passed before commit and push (`publishable_files_scanned=6576`). No product tests/builds or runtime/provider/database checks were performed.
- Publication: commit `09cfc5ca396016cbb7b238a5c744e004f7c7025a` was pushed to `origin/docs/feat063-diagram-readiness-20261107`; fresh `git ls-remote` confirmed the same SHA.
- Plan/approval and evidence: plan/PLAN_REV56_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md, approvals/TASK_APPROVAL.md, and evidence/EV-063-61_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md.

## Rev54 v2.6 checklist audit and diagram readiness — 2026-11-07

- Lifecycle: COMPLETE for the approved documentation review and package publication on the isolated branch.
- Current canonical pair: SRS and Data Table Register v2.7-draft, unsigned. Rev54 publishes draft TO-BE diagram inputs only.
- Disposition: M = 13 FIXED-LOGICAL, 2 PARTIAL, 1 OPEN-OWNER; D = 10 COVERED-LOGICAL, 7 PARTIAL, 3 OPEN; Q-01–Q-13 = OPEN-OWNER as complete checklist items; R-01/02/03/05 fixed in v2.7 and R-04 remains partial/open.
- The review found D-09 remains partial: the current Register still leaves the exact Parent Profile–Managed Profile–Delivery Recipient link and post-revoke history behavior open. D-08 remains partial after quota-scope/charge-order clarification because school grant allocation/purchase remains open.
- No new owner decision, product code/schema/migration/test/build/provider/runtime/source verification or final diagram was produced. See EV-063-59 and the Rev54 catalog/crosswalk.
- Plan Rev54 and exact authorization are in both approval registers. Package commit c5469153600ba8763f14715eb12f5792e8b5afe4 was pushed to origin/docs/feat063-diagram-readiness-20261107; fresh git ls-remote returned the same SHA. git diff --cached --check passed. python tools/validate_repository_security.py passed before commit and push (publishable_files_scanned=6571 each time). The SRS and Data Table Register remain unsigned; no PR, merge or dev push was performed.

## Rev53 v2.6 checklist reconciliation — 2026-11-07

- Lifecycle: COMPLETE for the approved documentation package and normal branch publication.
- Target pair: canonical SRS and Data Table Register v2.7-draft, unsigned. Owner formal sign-off is still pending.
- Product changes are limited to supported logical clarifications. Parent no-preset activity, plan supersession, role persistence, legacy ages, audit schema/retention and physical DDL/migration remain open.
- `git diff --check` passed. `python tools/validate_repository_security.py` passed immediately before commit and push (`publishable_files_scanned=6567`). Commit `359b0b92384faad789f6006c37cc5f66760ad594` was pushed to `origin/docs/feat063-srs-v26-checklist-20261107`; `git ls-remote` confirmed the same SHA at publication. No product test/build/runtime/provider/database operation was in scope.
- Plan/approval: Plan Rev53 and hash-identified approval are recorded in root and feature approval registers. Evidence: `evidence/EV-063-58_SRS_V26_CHECKLIST_REMEDIATION_20261107.md`.

## Rev52 SRS contradiction reconciliation — 2026-11-06

- Lifecycle: COMPLETE for the reviewed documentation package; publication to the isolated origin branch is verified.
- Canonical SRS and Data Table Register are v2.6-draft and remain unsigned. Product target requirements remain distinct from §32 source/runtime observations.
- Incorporated the three owner clarifications and aligned role/permission boundaries, admin media default-deny, Parent lesson pin/activity timing, profile-share acceptance, AI Job targets, video admission transitions and current target table count.
- Report items that lack owner answers remain open; no DDL, migration, code, product tests, build, provider or runtime operations were performed.
- Plan Rev52 approvals are recorded in root and FEAT-063 approval registers. Package commit `ca3c5dda695dc8d325442921ace684364d0215b1` is pushed to `origin/docs/feat063-srs-conflict-remediation-20261106`; fresh `git ls-remote` confirmed the remote SHA matches. Evidence: evidence/EV-063-57_SRS_V25_CONTRADICTION_REVIEW_20261106.md.



## Prior SRS v2.5 alignment and dev-source review — Plans Rev45/Rev51 (2026-11-06)

- Lifecycle: REVIEW; documentation/source review and Plan Rev51 package publication are complete.
- SRS and Data Table Register are v2.5-draft and remain unsigned. §§1–31 preserve target requirements; §§32.5–32.6 label the local Rev45 and fetched `origin/dev` Rev51 source snapshots separately.
- Rev51 source base: `4749451080f49243464d40a464b8f83a03ae77bb`. Main API/AI Jobs, separate StoryRun-lite dispatch, Modal dev workers, and model pins are documented with current evidence and limits; no runtime/API/DB/provider checks were rerun.
- Open: durable AI Jobs and authenticated main-app AI APIs; parent/teacher target flows; production profile, licensing, safety, latency/cost and video validation. SRS owner sign-off remains pending.
- Plan Rev51 authorization is in root and feature `approvals/TASK_APPROVAL.md`.
- Evidence: `evidence/EV-063-55_SRS_SYSTEM_CODE_ALIGNMENT_REV45_20261106.md` and `evidence/EV-063-56_SRS_PUBLICATION_REV51_20261106.md`.
- Published: `docs/feat063-rev45-srs-code-alignment-20261106`, package commit `620386fb227e2d8b76c48e72ad22892e3b0c1c53`; fresh fetch confirmed the remote matched. Security validation passed before commit and push.

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

## Modal AI setup scaffold — 2026-11-03

- Lifecycle: COMPLETE for the exact dev-only scaffold in `plan/MODAL_AI_SETUP_SCAFFOLD_20261103.md` (SHA-256 `7FE03A68DF76877457DF5C5F652FCB705669A624B2E07F7B6F317C9FB510E391`).
- Workload registry, versioned worker envelope, L4/L40S function skeletons, placeholder environment sample, setup guide, evidence and feature records are present under the approved allowlist.
- Static Python/JSON parsing, `git diff --check`, and repository security validation passed. No product test was run.
- No model handler, backend adapter, actual environment value, Modal resource, deployment, inference, or real-child data is included. Owner-side Modal environment setup is the next dependency.

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

## Modal drawing VLM L4 POC — 2026-11-03

- Status: IN_PROGRESS under approved plan SHA-256 F2AF6433EFE812BBD8144CBCD3E4ECFDE09FCF0A9952280BCE814314A7008E72.
- Preflight complete: Modal CLI 1.6.3 authentication succeeds; dev is present; no Modal apps, Volumes, or Secrets exist in dev; current-month dev metered-cost summary is 0.00.
- Implementation/deployment/inference not yet run. Scope is one private Qwen2.5-VL-7B L4 app and exactly one synthetic drawing inference. Do not infer AI-fleet or product readiness from this task.

## Modal AI hosting wave - 2026-11-03

- **IN PROGRESS.** Approved plan SHA-256 `C8FCB03681F2145E727F89E55DDD159AA354814E30B868CD745B930A83FCA5BA`.
- Four private dev apps are deployed: drawing VLM, language/audio, FLUX image, and Wan video candidate. All seven pinned checkpoints are downloaded directly from Hugging Face into Modal Volume v2; total retained file footprint is 95,121,275,282 bytes (88.59 GiB). Current account billing after downloads has not been checked.
- Synthetic TTS and ASR calls succeeded; the Vietnamese transcript substituted one word. FLUX generated one synthetic three-panel line guide successfully (768x512, 158,296 bytes); elapsed time including queue/cold start was 1,202.53 seconds. Visual ordering, child usability, safety, and product quality remain unvalidated.
- Corrective Qwen-VL call `fc-01M6GN62XVPDBR39205WQ35K9Q` later reached terminal `success`; no further Qwen story/storyboard or Wan inference has run. The later API-triggered drawing call is documented separately below; its result was not reconciled into the API run.
- Next: collect the Qwen-VL result; run the remaining approved synthetic POCs sequentially if capacity permits; update workload/evidence records; run repository security validation. LTX-2.5 remains gated; lesson suggestion, SAM2, safety validation, and product enablement remain deferred.
- Evidence: `evidence/MODAL_AI_HOSTING_WAVE_20261103.md`. No commit or push requested/performed.

## Local API runtime availability smoke - 2026-11-03

- **COMPLETE for read-only availability checks.** `/health` and `/openapi.json` on the running local Docker API returned HTTP 200; the documented StoryRun route probe returned HTTP 404.
- The active image started 2026-10-30, has no source bind mount, exposes no StoryRun or new-Modal worker routes, and has no AI provider/StoryRun Modal configuration. No POST or provider inference was sent.
- The new Modal worker requests therefore remain direct function POCs, not backend API requests. Wiring is outside the approved hosting-wave plan. Evidence: `evidence/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`. No code or database changes, commit, or push.


## Backend API to Modal drawing VLM vertical slice - 2026-11-03

- **PARTIAL / AWAITING RECONCILIATION** under the corrected approved plan hash `855235EA0B209A8B64699074C6D861734A5AC17CBD82B1E56E42F9FA9039D0F5`.
- The private Modal SDK adapter is wired to the synthetic StoryRun API. Isolated PG17 migrations, API health/OpenAPI, CRUD, image upload, ClamAV, and Windows image normalization passed.
- The previous Qwen-VL call reached `success`; exactly one API-triggered call was sent. `fc-01M6GYB9EZHJ4TCPAKFPT20Z7G` later reached Modal terminal `success` after the API had recorded `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION` and `OPERATOR_REVIEW`. Its result/output hash was not committed to the API; no retry was sent. The drawing app is stopped per owner request; the API run still needs separate operator reconciliation.
- Focused tests: 83 passed; Ruff passed; targeted Mypy passed with imported-module diagnostics silenced; `git diff --check` and repository security validation passed.
- Evidence: `evidence/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`. No commit, push, or merge.
- The temporary Windows API/PostgreSQL processes and task-owned Docker API/PostgreSQL containers are stopped; their task data is retained. The pre-existing local API and service containers remain healthy and untouched.

## Parent image-to-script API/AI retest - 2026-11-03

- Test execution complete with external AI scheduling blockers. Isolated DB migrations and Parent run/upload APIs passed through upload readiness.
- Vision attachment returned 202 after 904.056 seconds; final run state is `AWAITING_RECONCILIATION` with `VISION_OUTCOME_UNKNOWN`. Do not retry.
- The detached story worker produced no result during a 436-second wait. Subject confirmation was not reached; no Parent script API exists in the standalone router. Video calls: 0.
- Verified all four Modal dev apps stopped. Task API port 8002 and test PostgreSQL port 5433 are stopped. Shared model Volumes remain.
- Full details: `evidence/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md`.

## Parent generated-image, story, and activity-selection retest - 2026-11-04

- **COMPLETE** under the approved synthetic-only plan; no video inference.
- The first run was correctly blocked before provider dispatch because its run ID did not match the runtime pin. It was preserved. A replacement run with a matching pin completed image admission, one Modal drawing VLM call, adult confirmation, and one Modal story worker call.
- VLM: `bướm`, call `fc-01M6H51D7MD2P4XS68S2DQEN53`, Modal execution 29.295 s after 595.263 s queue wait. Story: five scenes, call `fc-01M6H5P6TFKW6Q7ZKRX28JCTDD`, Modal execution 90.741 s after 202.845 s queue wait.
- Activity API: one catalog card (`ACT-0102`) returned and selected successfully in its separate legacy fixture session; it is not integrated with StoryRun and is not the SRS post-video outdoor step.
- Review finding: the story output incorrectly depicts a butterfly hatching and seeking a nest. Treat it as an unreviewed draft.
- Shutdown verified: Modal drawing and language/audio apps stopped at 00:09:03 and 00:09:06 Asia/Saigon; all Modal dev app records report stopped. Task API 8002 and PostgreSQL 5433 are closed; pre-existing API 8000 remains available. Shared model Volumes were retained.
- Evidence: `evidence/PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md` and its task-scoped scripts/assets.

## AI flow SRS alignment and Teacher deck POC - 2026-11-04

**Status: PARTIAL / IMPLEMENTATION AND TEST EVIDENCE RECORDED.**

- Implemented Parent story schema, revision APIs/persistence, age/subject/role/business-rule guards, and terminal Modal story-error classification. Live story call failed before model load because the prior client sent the drawing manifest schema; local adapter is corrected but has not been redeployed or live-retested.
- Teacher Deck text POC succeeded (5-slide, 16:9 DRAFT); FLUX visual did not complete due unavailable L4 capacity. No generated visual is claimed.
- All 13 mounted StoryRun-lite operations were exercised; the story-generation worker path is the live failure. Parent positive script confirmation was not reached. The activity list was not requested before video; Teacher Deck HTTP/session endpoint is not mounted in this API slice.
- Verification: 92 passed, 3 PostgreSQL-URL cases skipped; Ruff, compileall, and diff check passed.
- All Modal dev apps stopped and verified at zero tasks. Shared Volumes and shared Docker services retained. No commit/push.
- See `evidence/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md`.
## Full non-video AI workload retest - 2026-11-04

**Status: PARTIAL / RETEST COMPLETE.** Owner-authorized fresh non-video attempts and API checks are complete. TTS/ASR succeeded; the fresh GPU-backed VLM, story, sketch-guide, Teacher Deck, lesson-visual, and SAM2 inferences timed out while waiting for Modal L4 capacity. Parent image analysis remains `AWAITING_RECONCILIATION`; do not retry. All 13 mounted StoryRun-lite operations passed 14 isolated contract checks, and 46 focused tests passed with two legacy-fixture cases deselected. Targeted Ruff, compileall, and diff checks passed. All Modal apps stopped with zero tasks; task DB/cache cleaned; shared services/Volumes preserved. No video call, product enablement, commit, or push. Evidence: `evidence/AI_NONVIDEO_WORKLOAD_FULL_RETEST_RESULTS_20261104.md`.

## Owner-directed publication - 2026-11-04

The owner authorized committing the reviewed pending FEAT-063 worktree and pushing the current branch `codex/feat063-modal-backend-completion-20261103` to a same-named remote branch. The required repository security validator will run before commit; this publication does not include a push to `dev` or changes to the canonical SRS.

## 30-minute non-video AI queue retest - 2026-11-04

**Status: PARTIAL / RETEST COMPLETE.** Fresh direct Modal worker calls used a 1,800-second client-side wait, preserving worker timeouts and model pins. Parent Sketch Guide succeeded in 36 seconds. Teacher Sketch Deck succeeded after 17m22 with a validated 5-slide DRAFT, four drawing steps, and two approved activities; its earlier NotFound was pre-dispatch on a stopped deployment. Drawing VLM, story/storyboard, lesson visual, and SAM2 reached the full queue wait without inference output; Modal logs confirmed GPU_L4 scheduling waits. Unknown calls were not retried. TTS/ASR were not repeated; video inference was zero. All Modal dev apps stopped with zero tasks at 22:00:30. Product workloads remain disabled; no commit or push. Evidence: evidence/AI_NONVIDEO_30MIN_QUEUE_RETEST_RESULTS_20261104.md.

## Modal Qwen story readiness diagnostic - 2026-11-04

**Status: COMPLETE / ROOT CAUSE IDENTIFIED; STORY OUTPUT NOT PRODUCED.** The temporary L4 probe loaded the pinned Qwen2.5-7B checkpoint and completed a technical token-generation smoke check in 26.194 s. The story calls stayed queued with no start time/container; Modal logs explicitly reported GPU_L4 capacity acquisition. This is a scheduling-capacity blocker before worker/model execution, not the 600-second worker timeout or a demonstrated model failure. Two calls were accidentally dispatched instead of the approved one; the first also remained queued for 63 seconds beyond the approved 30-minute cap after its runner was interrupted. Both were synthetic and neither reached inference. The scope and timing deviations and local result-wrapper error are documented in the report. Task-owned Modal apps are stopped, no active containers remain, and no product source/config/SRS was changed. See `evidence/MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md`.


## Modal serverless story latency experiment - 2026-11-05

**Status: COMPLETE; scheduling/model startup improved, story output invalid.** The approved one-shot synthetic Parent story call was assigned an NVIDIA A10 from the ordered fallback configuration. Client dispatch-to-terminal elapsed time was 46.803 seconds; model loading took 12.634 seconds, prompt encoding 0.015 seconds, and generation 27.407 seconds for 722 tokens. The worker rejected its output with `MODAL_MODEL_OUTPUT_INVALID`; no second request was sent. Ruff and Python compile checks passed. The language/audio app was stopped with zero active tasks and shared Volumes retained. No video inference or production enablement. Details: `evidence/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`.

## Modal Parent story parser/content boundary follow-up - 2026-11-05

**Status: COMPLETE; synthetic story accepted by the existing contract.** The worker now asks Qwen for narrative content only and assigns scene indices/timing deterministically before the unchanged strict parser. One fresh synthetic request succeeded: five scenes, 30 seconds, backend `StoryRevisionDraftV1` and butterfly lifecycle checks passed. Dispatch-to-terminal was 56.073 seconds on NVIDIA L40S; generation took 26.137 seconds for 608 tokens. Focused tests: 46 passed; Ruff and Python compilation passed. The Modal app is stopped with zero tasks, scratch input removed, shared Volumes retained. No video/other AI call, SRS/API change, production enablement, commit, or push. Evidence: `evidence/MODAL_STORY_CONTENT_BOUNDARY_20261105.md`.

## Parent StoryRun-lite API and AI retest - 2026-11-05

**Status: COMPLETE WITH PARTIAL AI RESULTS.** The no-AI API matrix covered all 13 mounted operations in 22 checks; focused backend tests passed (154), and Modal story/parser tests passed (45, 1 skipped). The VLM API call remained unknown after 303.762 s and its endpoint took 304.333 s to return 202. The separate story API call returned 502 after 59.266 s because generated butterfly lifecycle facts failed semantic validation; no story draft was created. No video call. Task Modal apps and disposable PostgreSQL were stopped; shared services and Volumes were preserved. Evidence: `evidence/PARENT_STORY_API_RETEST_20261105.md`. No product source, API, or SRS contract was changed.

## Rev44 AI API coverage and Qwen3.5 validation - 2026-11-05

**Status: PARTIAL / IMPLEMENTATION AND TEST PASS, AI RESULTS MIXED.** The latest SRS copy and Q159 role rule are recorded. Qwen3.5-9B is pinned at the approved revision and loaded with Transformers 5.22.1. One Teacher Sketch Deck worker call passed its DRAFT/slide/activity contract. Drawing analysis returned unusable output. Story and lesson suggestion each failed before generation because LMFE's old Transformers adapter imported a removed Transformers 4 module; the adapter now uses LMFE 0.11.3 TokenEnforcer directly, with 59 focused Modal tests passing and a Modal CPU runtime-import check passing. No post-fix story/lesson inference was dispatched.

VieNeu TTS produced audio; paired Whisper changed one word. FLUX.3 image generation is blocked by HTTP 401/no Modal HF Secret; SAM2 remains a prior 1,800-second GPU scheduling UNKNOWN; video was not run. Main backend OpenAPI has 24 operations/17 paths and no AI dispatch; StoryRun-lite's 13 operations are synthetic, and its two AI routes use non-durable in-process tasks. Backend API/contract tests: 79 passed, 6 skipped. All workload flags remain disabled.

The task-owned drawing and language/audio apps were stopped with zero tasks; shared Volumes were retained. Repository security scan passed across 6,388 publishable files. Evidence: `evidence/AI_API_QWEN35_MODAL_VALIDATION_20261105.md`; API/workload crosswalk: `artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`.

## Rev45 non-video AI end-to-end verification - 2026-11-05

**Status: PARTIAL; callable Qwen and speech workers verified, external blockers remain.** Fixed the LMFE parser's ASCII-only alphabet issue that allowed premature EOS inside Vietnamese strings. Synthetic Modal calls passed for drawing analysis (44.014s), Parent story/storyboard (113.381s), Teacher Deck (43.464s), lesson suggestion (61.636s), TTS (19.161s), and exact-text ASR (23.900s). Focused Modal/parser tests: 76 passed; backend API/OpenAPI tests: 61 passed, 6 skipped. Targeted Ruff, `py_compile`, repository security validation (6,556 files), and `git diff --check` passed.

Parent Sketch Guide and lesson visuals were not dispatched because Modal `dev` still has no HF Secret; the prior FLUX.3 checkpoint request returned HTTP 401. Optional SAM2 was not re-dispatched; its last attempt waited 1,800 seconds for GPU scheduling without producing a mask. Current SAM2 GPU availability was not rechecked. No video was called; product workload switches remain disabled. Both task-used Modal apps were stopped and verified at zero tasks; shared Volumes were retained. See `evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md` and `evidence/assets/ai_nonvideo_ai_end_to_end_20261105/`.


## Rev46/46A ? Qwen3.5-only and FLUX images ? 2026-11-05

**Status: COMPLETE.** Qwen2.5 is retired from active FEAT-063 configuration; all active Qwen candidates are pinned Qwen3.5-9B. Fixed FLUX3 checkpoint staging to include required Diffusers transformer and VAE files. One download and one inference each for Parent Sketch Guide and lesson visual passed with synthetic input; both outputs are DRAFT/review-required. Focused tests: 27 passed; Ruff and compileall passed. Modal FLUX app stopped with zero tasks; shared Volumes retained. No product API, SAM2, or video was called; workloads remain disabled. Evidence: `evidence/AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md`.

## SRS v2.4 publication — Plan Rev44 (2026-11-06)

- Lifecycle: COMPLETE. Commit `fa61c41bead365fe49f84d38abc5557e765ff6bf` was pushed to `origin/codex/feat063-srs-v24-asbuilt-20261106`, based on `origin/dev` at `c98701b1e500906f396e773c79ec3bba55db2542`.
- Published the exact 16 documentation paths listed in Plan Rev44. No application/runtime changes or unrelated local work were included; the original checkout's pre-existing staged and unstaged changes remain untouched.
- Repository security validation passed before commit and again before push (`publishable_files_scanned=5807`). No test suite was run for this documentation-only publication.


## As-built SRS alignment — Plan Rev43 (2026-11-06)

- Lifecycle: REVIEW; canonical SRS and Data Table Register updated to v2.4-draft, unsigned.
- SRS §§1–31 retain product target requirements; new §32 separates current local implementation observations from those targets.
- Verified locally: OpenAPI 111 paths / 124 operations; database Alembic `20261028_ll_0001`; 41 application tables (34 `public`, 7 `lesson`). Full names and AI/database access boundary are in EV-063-33 and Data Table Register §§14.5–14.6.
- AI direction updated per owner: Qwen3.5-VL, FLUX.3, Whisper, optional SAM 2.1, Modal inference. Q159 roles clarified. Modal dashboard presence is not claimed as backend end-to-end success; LTX-2.5 video remains unverified.
- Verification: documentation cross-check and path-scoped diff review; no tests, database writes/migrations, provider/GPU invocation, deployment change, commit or push.
- Plan/approval: Plan Rev43 authorization hash `000A4D0C22BB92666C60C4597BB5B8AEB126E0D4C1F654B610909CC7BBDED945`; current reviewed plan hash `1F10B3F447F7AFB59FAD847E6BE05F0C898B4CE4F6F51B0536258BBD1806F185`; approvals in root and feature `TASK_APPROVAL.md`.
- Evidence: `evidence/EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md`.


## Plan Rev50 ? local dev duplicate repair and Modal/SRS merge

**Status: COMPLETE ? fast-forward pushed to `origin/dev`.** The six local duplicate patches were removed from `dev` ancestry after preserving the old dirty checkout on a backup branch. The Modal AI branch and pending changes are integrated; the SRS v2.4 branch was merged with its approved SRS/Data Table Register preserved byte-for-byte. Final merge commit is `370cb26d6e8c99c126f4a5a16df132eaa70c8e70`; `git cherry` confirms zero duplicate patches relative to `origin/dev`. No tests or AI/provider calls were run. `origin/dev` now equals `0d15b1a0ae6e5373354d7ac35cc163e41b55c42e`. See `evidence/EV-063-54_DEV_HISTORY_AND_SRS_MERGE_20261106.md`.

## Rev51 Modal AI and legacy API audit - 2026-11-06

- Status: COMPLETE WITH FINDINGS; evidence-only closeout, no product code change.
- Results: live OpenAPI 124 operations / 111 paths; 1,454/1,460 backend contract tests passed; 79 Modal worker contract tests passed and 2 skipped.
- Six failing API/contract tests, their classifications, worker/API readiness gaps, timeout diagnosis, and full synthetic artifacts are recorded in `evidence/modal_ai_and_legacy_api_retest_20261106/API_TONG_HOP_VA_SAN_PHAM_AI_MODAL_20261106.md`.
- No GPU inference was repeated. SAM2 remains blocked by documented GPU scheduling capacity; the current Modal `dev` app inventory was empty and no task app was deployed.
- Open follow-ups: review legacy composition/BE1 test failures and implement durable product AI dispatch routes in a separately approved task.


## Rev52 non-video Modal AI reliability - 2026-11-06

- Status: COMPLETE WITH FINDINGS under the approved Plan Rev52.
- Approved plan SHA-256: `6B3B1C25CD2A9974860A93551CDAD0FB3363DB38CB00D293ABB4818C9F0782D2`.
- Work branch: `feature/feat063-modal-ai-reliability-20261106` from `dev` at `0fc773fa`.
- Changes: structured phase observability is in place for non-video Modal workers/caller log summaries. Story parsing now follows the SRS fields/business rules without the unsupported terminal-punctuation constraint; required schema, lifecycle, fact, timing, and scene-count checks remain.
- Live worker result: all eight enabled non-video worker paths passed once after applicable fixes. Optional `drawing.segment` was attempted once and rejected by its disabled workload gate before inference (`MODAL_WORKLOAD_NOT_ALLOWED`). No video call was made.
- Parent API: 33/33 expected request outcomes on 13 routes; one live Parent drawing HTTP-to-Modal dispatch passed. Story HTTP used a verified fixture; a separate live story worker call passed. Confirmation/resume reached `VIDEO_ADMISSION_PENDING`, with zero video calls.
- Tests/quality: 97 Modal tests and 59 focused backend tests passed; targeted Ruff, `py_compile`, and `git diff --check` passed.
- Limits: Parent sketch guide, Teacher sketch deck, lesson suggestion/visual, and speech are worker-verified but do not yet have durable authenticated product API dispatch; recorded as NOT_IMPLEMENTED. Registry flags remain disabled.
- Cleanup: task Modal app list empty after stop; disposable PostgreSQL container exited; shared volumes/checkpoints retained; no secret values read or changed.
- Full results and evidence index: `evidence/nonvideo_modal_ai_reliability_20261106/API_AND_AI_MODAL_RESULTS_20261106.md`.

## Rev53 SAM 2.1 gate retest - 2026-11-06

- Status: COMPLETE WITH FINDINGS under the approved Plan Rev53; no push.
- Root cause fixed: `drawing.segment` was omitted from the L4 worker envelope allowlist. The dedicated worker now passes parsing; the video execution group still rejects it.
- Verification: pinned checkpoint preflight passed; one synthetic SAM 2.1 inference passed worker/output validation. Focused gate tests, Modal test suite, Ruff, compilation, repository security validation and diff checks are recorded in `evidence/sam2_gate_retest_20261106/RESULTS.md`.
- Quality: mask output is valid and lineage-preserving, but visual review shows only the central butterfly body, missing both wings, head and antennae. SAM 2.1 is not product-ready based on this sample; `workloads.json` remains disabled and OpenCV/Pillow remains the baseline.
- Runtime: checkpoint preflight caller elapsed 27.051 s; GPU inference caller wait 31.896 s; total run 61 s. No video was called.
- Cleanup: `sketch2life-srs23-drawing-segment-dev` is stopped with 0 tasks; shared volumes/checkpoints were retained.

## Plan Rev54 - SRS v2.5 and Modal AI integration to dev

- Status: COMPLETE WITH FINDINGS; the normal push succeeded and `origin/dev` was verified at `47e5308a5c547df8dab5f3c560f949ee925f441e`. Closeout documentation was then committed and published normally.
- Source branches: SRS `fae180dcf3ea2771b41546aa6925b94636821df1`; Modal AI `c6818490d0d889ab17dc9f8de3830987eb2a230d`.
- Merge commits: AI `634e0e20f56cbfa6101ece6e67f3e4267a30ae92`; SRS `6bbb375a359fb78f06585963b8ee9f7bfc2246ff`.
- SRS v2.5-draft is now the canonical working source and remains unsigned. SAM2 remains disabled in the product registry; all recorded quality limitations are preserved.
- No new AI calls, video inference, database changes, runtime tests or product test suites were run during integration. Existing Rev52/Rev53 evidence is linked from EV-063-57.

## Rev55 — two-agent diagram readiness assessment

- **Status:** COMPLETE — assessment published to origin/docs/feat063-diagram-readiness-20261107 at 33c40d17ff77f31b1d128ce35c1f641a2fe6de8a.
- **Baseline:** SRS/Data Table Register v2.7-draft at 98cc34a39af279560b5f8d39f18939a376535834; unsigned.
- **Outcome:** Most diagrams can be drafted with open questions annotated. Screen Flow needs screen-to-screen navigation decisions; physical ERD needs approved DDL and environment reconciliation. No final diagrams or product decisions were produced.
- **Evidence:** evidence/EV-063-60_TWO_AGENT_DIAGRAM_READINESS_ASSESSMENT_20261107.md.

## Plan Rev57 — substantive diagram-input remediation — PUBLISHED / PARTIAL

- **Baseline:** fetched target branch at ae5707ca188d01d9719ed959b62d768ae927912d.
- **Status:** documentation package published at db7f7e4df6e95e9549e17664ea8ef9be1c338d68 by normal fast-forward; remote ref verified.
- **Outcome:** SRS/DTR Rev57 detail and companion contract artifacts published; 13 diagram inputs are explicitly DRAFT/BLOCKED as applicable. SRS/DTR remain unsigned and Q decisions remain open.
- **Technical finding:** static source import scan found one cycle under infrastructure.canvas_render; ai_jobs router file is not included by the inspected main router composition.
- **Evidence:** EV-063-62. No product tests/runtime/database/migration were run.

## Teacher Sketch Deck presentation UI — Plan Rev65 (2026-11-10)

- Lifecycle: **PASS for the approved Teacher presentation slice**; overall Parent/Teacher E2E remains **PARTIAL**.
- Real Teacher Web login and live backend/Modal flow produced a Qwen3.5 lesson draft, a four-slide Qwen3.5 DRAFT deck, and a FLUX composite line-sketch visual. The presentation displayed the actual image on the drawing slide; slide navigation, arrow keys, drawing-step skip and activity-column scrolling were verified.
- `npm run build` passed. Existing bundle-size advisory remains (~695 kB JS chunk vs 500 kB warning threshold).
- Parent Android was not run in this follow-up: `adb`, Android SDK/platform-tools and an emulator are unavailable. The approved 512-token drawing-worker change therefore remains unverified through Parent UI; the prior 256-token failure remains the last live Parent analysis outcome. Teacher upload/parser is also untested.
- Worker logs exposed model and phase data, but the successful suggestion and visual summaries lacked `worker_terminal_event`, terminal duration and output hash. See EV-063-75 for IDs, times, screenshots, limits and cleanup.
- Modal apps were stopped at zero tasks; synthetic Firebase identity and disposable DB were removed; task-started services were stopped while pre-existing API/ClamAV remained healthy.

## Parent/Teacher Modal UI E2E — Plan Rev64 (2026-11-10)

- Lifecycle: **PARTIAL — real UI-to-backend-to-Modal flows ran; Parent drawing analysis failed output validation and Parent story is blocked.** Execution plan SHA-256: `B791E6E552FF16A6A99D5758D7A2226FA6DD561AE852A40DF6BC2B87E32015C8`.
- Acceptance requires real Parent Android and Teacher Web UI actions through Firebase role resolution, backend and live Modal inference, with the result displayed in the UI. Fixture or backend-only results do not count. Video is deferred.
- Parent registration/role and optional FLUX line-sketch passed in Android after the approved accessibility recovery. Qwen drawing analysis failed strict JSON parsing after 256 generated tokens; API surfaced 504 `MODAL_OUTCOME_UNKNOWN`, then worker logged `MODAL_MODEL_OUTPUT_INVALID`. No retry; Parent story was not called because the adult-confirmation candidate was absent.
- Teacher role gate, Qwen lesson/activity suggestion, Qwen Sketch Deck and FLUX lesson visual passed through Teacher Web. The teacher reviewed and edited the lesson draft. The tested screen uses structured fields; lesson-file upload/parser review remains untested. Parent profile selection/snapshot is also absent from the tested screen.
- Source confirmation: local `dev` and `origin/dev` both point to `1431ef81972b71303fd4a7909748fd3005769a3c`, containing the Modal worker/deployment source. The three task-used Modal apps were stopped and verified at zero tasks. Synthetic Firebase identities and `rev64_e2e` were deleted; task-started Postgres/Redis and emulator were stopped; existing API/ClamAV were preserved. Evidence: `evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md`.

## Role-based authentication and account recovery — Plan Rev63 (2026-11-10)

- Lifecycle: **REVIEW — backend/database role-flow acceptance passed in an isolated E2E run; Firebase client auth and interactive UI acceptance remain blocked/pending**.
- Implemented in source: server-assigned Parent role on registration; `/api/auth/v1/me` role resolver; Teacher-only Teacher Web gate; School Manager and Platform Admin management gates; Platform Admin account list/search/pagination/create/role/state APIs; Firebase identity creation and password-reset email request; additive role migration; explicit first Platform Admin bootstrap command; Firebase reset/change password surfaces on Parent, Teacher and management Web.
- Authorization: legacy identities that cannot be unambiguously assigned during migration are visible to Platform Admin as `role: null`; protected routes deny them until a role is set. Admin API responses resolve email/display name from Firebase Auth and never save those fields to the app database or audit.
- One-root Docker setup: `.env.example` has the blank bootstrap-email placeholder and Compose forwards it to the API container. Rebuild/recreate is still required before a running container sees a changed value.
- E2E results: all Alembic heads, including the new role migration, applied to disposable PostgreSQL; backend registration and role/account lifecycle checks passed with synthetic Firebase identities; real HTTP registration and invalid-token error mapping passed. Role-gated business cases used an explicit test principal override, not a Firebase signed token. Main backend flow took about 16.26 seconds.
- Firebase Auth update: the root `.env` had a different `VITE_FIREBASE_API_KEY` from the Web app config supplied by the owner; the local value was corrected. A non-mutating Identity Toolkit probe returned HTTP 200. A synthetic Firebase identity completed reset, sign-in, password change and sign-in again; it was deleted and no email was sent.
- UI checks: Admin and Teacher Web production builds and Parent mobile typecheck passed. No browser UI flow ran, and the Firebase JS SDK screens were not exercised interactively. Full Compose startup could not pull MinIO (registry HTTP 401), so API/PostgreSQL ran in disposable isolated containers.
- Cleanup: synthetic Firebase identities were deleted; the two temporary E2E containers were stopped/removed. Pre-existing API/ClamAV services and persistent volumes were preserved. No admin seed remains and no commit/push was made.
- Remaining SRS/runtime gates: UC-13 email verification and activation, production email/invitation delivery policy, shared public-registration rate limiting, interactive Web/Android auth screens using the corrected `.env`, normal Compose startup after MinIO pull is available, first configured Platform Admin seed, and live signed-token role-gate acceptance. SRS §31.10(14) remains open.
- Contract/evidence: `artifacts/AUTH_ROLE_API_CONTRACT_REV63_20261110.md`; `evidence/EV-063-73_ROLE_BASED_AUTH_AND_RECOVERY_20261110.md`.

## Backend Firebase Auth registration — Plan Rev62 historical state (extended by Rev63, 2026-11-10)

- Lifecycle: **REVIEW**. Local backend account creation and identity visibility are verified; live Parent REST sign-in remains blocked by an invalid Web API key.
- Rev62 contract: `POST /api/auth/v1/registrations` was local-only and did not persist role; Rev63 extends it to public registration with server-assigned Parent role in the database. It still accepts no client role and returns no UID/password. The process-local limiter allows five attempts per client IP per 15 minutes; full email-verification activation remains open.
- Automated checks: backend focused tests 18/18 passed; Parent auth Jest 6/6 passed; mobile TypeScript check, backend Ruff check, and `docker compose config -q` passed.
- Live result: backend HTTP 201; Firebase Admin lookup found `synthetic Firebase identity (identifier redacted)` in `sketch2life-dev`, `email_verified=false`. Account is retained; generated password and tokens were discarded.
- Blocker: Firebase REST sign-in returned `API key not valid` for the Web API key previously supplied by the owner, even after aligning the root `.env` value. Need a fresh key from the Firebase `sketch2life-dev` Web app config; then rerun REST sign-in.
- Runtime boundary: exercised through FastAPI `TestClient` with real Firebase Admin, not Docker. No Docker service lifecycle, database/migration, commit, or push occurred.
- Contract/evidence: `artifacts/AUTH_REGISTRATION_API_CONTRACT_REV62.md`; `evidence/EV-063-72_BACKEND_FIREBASE_ACCOUNT_REGISTRATION_20261110.md`. Plan Rev62 final hash and approval records are in `approvals/TASK_APPROVAL.md`.

## Initial single-root Firebase Auth setup — Plan Rev61 (historical; signup creation superseded by Rev62)

- Lifecycle: implementation/configuration complete for the approved local setup; live Firebase credential and account verification remain owner-gated.
- One ignored root `.env` now holds the existing local Compose values, provided public Firebase web config, and the owner-supplied Admin service-account JSON as Base64. Provider mode is `firebase`; `firebase-admin` 7.7.0 is installed in `backend/.venv`.
- At Rev61, Parent Android sign-up and sign-in both used Firebase Auth REST. Rev62 replaces only account creation with the backend route; REST sign-in, local sign-out and in-process token refresh remain. Backend Admin verifier accepts project-checked Base64 JSON. Teacher Web and Parent Android source public config from the same root `.env`.
- Verification: local Firebase Admin SDK accepted the supplied credential and its project ID matches; backend focused tests 12/12 passed; mobile TypeScript typecheck passed; Teacher Web production build passed with the existing >500 kB chunk warning; `docker compose config -q` passed; Babel root-env allow-list check and synthetic Parent Auth flow passed.
- Limits: Jest auth tests could not start because Node/Jest `realpath` returned `EPERM` for the workspace path. No live Firebase token/account operation, Docker service start/stop, DB operation, commit or push. `git diff --check` is blocked by a pre-existing trailing blank line in FEAT-058 `evidence/README.md`; that unrelated file was not changed.
- Evidence: `evidence/EV-063-71_SINGLE_ROOT_ENV_FIREBASE_AUTH_20261110.md`. The canonical v2.7-draft SRS remains unchanged and unsigned.

## SRS baseline correction — Plan Rev60 (2026-11-09)

- Lifecycle: REVIEW; SRS-only rebase and static consistency checks are complete. Latest FEAT-063 source is v2.7-draft Rev57 at `f21c6f34af1ee045caf9a0621e38376a2bfde390`; local SRS now includes Rev58–Rev60 amendments and remains unsigned.
- Rev57 §§32.6–32.7 retained; Rev58 source snapshot at §32.8. Seventeen `OPEN-OWNER` decisions remain; DTR remains a separate local v2.5-draft and was not edited.
- Output SHA-256: `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`. Evidence: `evidence/EV-063-65_SRS_REBASE_V27_REV60_20261109.md`.
- No product tests/build/CI run, database/provider/secret operation, deployment, commit or push was performed. Diagram readiness, physical schema and formal SRS sign-off remain open.
