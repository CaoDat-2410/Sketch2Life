# M2 S2 Draft 11 Cold Review — 2026-11-14

## Verdict

**CHANGES REQUIRED.** Draft 11 preserves the no-approval/no-launch boundary and resolves the main Draft 10 route and migration-graph findings. Before this plan can serve as a review-ready S2 approval candidate, it should correct the AT-08 concurrency setup and the stated location of `current_input_revision`. The unchanged S3 Draft 5 also contains a K3 stop condition that conflicts with D-198 and must be reconciled before any later S3 approval.

**Reviewed plan:** 39,857 bytes; SHA-256 `1FABBCE8E1820C0747868368535E5FFC6BA3FE4019FA7FCE1F1F96B96B8BD95B`.

**Review type:** Independent fresh-context review of the assigned records and cited source files. This is a read-only plan review, not approval, implementation authorization, allowlist, command ceiling, gate approval, or launch. I did not use another session's review conclusions or delegate the review.

## Findings

### P2-1 — AT-08 does not specify distinct idempotency keys for the concurrent-create conflict case

**Evidence:** Draft 11 line 68 requires two concurrent creates for one Parent to produce one run and one receipt, with the loser returning HTTP 409 `ACTIVE_RUN_EXISTS`, but does not say whether the requests use the same or different idempotency keys. The existing route requires `Idempotency-Key` and checks `replay_create_run` before calling `create_run` (`.worktrees/m2-s2/backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:116-149`). A same-key, same-payload retry can return the existing 201 replay before reaching the repository's active-run conflict mapping (`.worktrees/m2-s2/backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:156-160`).

**Impact:** A valid test setup using the same key can return 201, so the stated 409 assertion is not deterministic as written.

**Suggested fix:** Specify two distinct idempotency keys for the competing creates. If same-key replay is in scope, assert it as a separate case from the distinct-key active-run conflict.

### P2-2 — The migration summary puts `current_input_revision` on the wrong table

**Evidence:** Draft 11 line 136 says the migration adds `current_input_revision` and the other listed context columns “on Story inputs.” In `20261112_parent_story_context.py`, `current_input_revision` is added to `story.runs` (`.worktrees/m2-s2/backend/alembic/versions/20261112_parent_story_context.py:48-50`); the source-profile, typed-idea, context and confirmation fields are added to `story.run_inputs` (`:116-159`).

**Impact:** This misstates a source fact in the migration audit used to explain the no-additive-DDL boundary.

**Suggested fix:** Split the sentence by table: `current_input_revision` is on `story.runs`; the listed input metadata is on `story.run_inputs`. The migration's asset-column alterations and related size constraint are also present at `:16-26,67-113` if the paragraph is intended to enumerate all effects.

### P3-1 — The unchanged S3 Draft 5 retains a K3 gate inconsistent with D-198

**Evidence:** Draft 11 correctly records D-198's current K3 rule at line 34, but line 172 says S3 Draft 5 remains unchanged. That root-checkout draft still says to stop S2/S3 close-out whenever accepted S1a-P closure leaves K3 unresolved (`features/FEAT-063-system-architecture-rearchitecture/plan/M2_S3_TASK_APPROVAL_DRAFT5_20261110.md:102`). D-198 says K3 remains `NOT VERIFIED` and to stop only if accepted evidence cannot establish the Gate A Story-chain target (`.worktrees/m2-s2/features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:525`). Round 4 reviewed S2 Draft 5 and S3 Draft 5 before these later decisions; it is historical review evidence, not a reconciliation of the newer rule (`features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_S3_PLAN_REVIEW_ROUND4_20261110.md:4,25`).

**Impact:** The unchanged S3 plan can carry forward a stricter K3 blocker than the current owner decision.

**Suggested fix:** Keep S3 Draft 5 unchanged for this S2 task, but state that its K3 clause is stale context and must be reconciled to D-198 in any future S3 revision before separate S3 approval. The foundation plan Draft 11 is also older context; its S2/S1b sequencing at lines 571-573 does not grant authority and should not override D-197/D-198.

## Verified OK

- **D-194 through D-198 and S1a-P2 close-out:** Decisions lines 521-525 match Draft 11's dispositions. The accepted addendum records `ACCEPTED WITH KNOWN GAP`, preserves the failed/consumed Gate P2 approval, prohibits a retry and cleanup, and preserves production BE1 role-adapter coverage as `NOT COVERED` (`approvals/TASK_APPROVAL.md:2848-2862`; closure record lines 3-10,21-23; real-PostgreSQL addendum lines 9-12,62-65). Draft 11 does not treat the scratch-PostgreSQL addendum as a Gate P2 pass.
- **Draft 10 findings:** P1-1 is addressed with the actual `/v1/story-runs` prefix and per-profile composition. P1-2 is largely addressed: a static read of the 31 migration files finds 13 roots, 10 terminals, no missing revision references, and the stated Story chain through `20261112_parent_story_context`. K3 and database state remain explicitly unverified. P2-1 distinguishes the intended `ParentRoleReader` boundary from the current StoryRun route's direct BE1 identity query and keeps that integration unresolved before approval. P2-2 adds source-backed assistance and age outcomes. P3-1 is labeled owner-supplied and not independently re-verified.
- **Router and profile facts:** `parent_story_runs.py` uses `/v1/story-runs` (`:43`); classroom composition does not mount it, while combined composition mounts it by default (`router_composition.py:35-45,60-77`; `app.py:256-267,1003-1010`). The StoryRun-lite demo branch is flag-gated. `ParentApi.ts:89-110` uses `/api/parent/v1/story-runs`, leaving the documented client/server prefix mismatch open. The AI Jobs candidate uses `/api/collaboration/v1` (`routers/ai_jobs.py:29,36-45`) and is not imported or mounted by `router_composition.py`.
- **Age and StoryRun effects:** The trusted lookup reads the current owned profile revision; the service allows 36–120 inclusive and rejects out-of-range values with 422 `INVALID_REQUEST` before repository create, so refusal does not write a Story run, run input, or `CREATE_RUN` receipt (`parent_story_profile_lookup.py:26-60`; `application/services/parent_story_runs.py:55-66,193-207`). The create path returns the stated 201 envelope and persists the trusted age, `INPUT_PROCESSING` run, run input, and `CREATE_RUN` receipt (`routers/parent_story_runs.py:116-197`; repository `:92-155`; response schema `:104-138`). This create method does not create an AI job or outbox row.
- **Assistance receipts:** The submit/cancel compatibility paths, status fields, receipt envelope, response values, and cache headers described in AT-09 match their sources (`routers/assistance_requests.py:48,62-117,143-159`; `routers/pilot_assistance.py:89,95-103,382-440,458-505`; `application/services/assistance.py:1310-1320`; `contracts/schemas/assistance_requests.py:154-176`).
- **Authority and dependencies:** Rev60 remains canonical under D-195; the Rev67 crosswalk keeps Rev61–Rev67 conditional or not affected and says the old basis-B statement is superseded only for OQ-S2-1 (`M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md:14-30`). BQ-1/BQ-2 remain open in the BE/AI handoff (`:44-52`), and BQ-7/BQ-8 remain open in the question record (`tmp/be-ai-questions/BE_AI_QUESTIONS_20261113.md:53-58`); Draft 11 keeps their route and error details unapproved.
- **Approval boundary:** Draft 11 says DRAFT / NOT APPROVED / NOT LAUNCHED, with no implementation, database/migration action, allowlist, command ceiling, gate launch, or S2/S3 approval (`:3,171-182`). D-194 and D-198 likewise authorize no later phase or gate. No new approval or launch boundary is implied.
- **Other plan context:** S3 Draft 5 requires accepted/committed S2 closure and a separate S3 Task Approval (`:9`); Round 4 is explicitly limited to Draft 5 plans (`:4`). The foundation plan's older sequencing is treated as read-only context in Draft 11 (`:172`). These older plans do not authorize S2 work.
- **Input pins:** I rehashed all **68** cited file rows: 37 inputs in Draft 11 section 9 and 31 migration files in section 5. All recorded byte counts and SHA-256 values match at the specified root-checkout, S2-worktree, or mobile-worktree paths.

## Could not be verified

- Task-database row counts, Alembic version rows, migration applicability, empty-`story.runs` precondition, or rollback behavior. No database connection or command was used.
- Runtime route exposure, generated OpenAPI, authentication/authorization, concurrent create, cancel, job-status ownership denial, receipt handling, age-boundary behavior, or process restart. No application or test command was run.
- The owner-supplied CI job statuses and any live GitHub/remote state. Draft 11 clearly labels the CI section “Owner-supplied CI context (not independently re-verified)” at lines 174-178; I did not use network access.
- Production BE1 role-adapter behavior remains `NOT COVERED` under D-190. This review does not change that status.

No database, network, backend, Docker, Modal, pytest, mypy, install, validator, staging, commit, or push command was used. Only this report was created.
