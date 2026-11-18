# M2 S2 Task Approval - Draft 10 (Parent StoryRun, jobs, assistance compatibility and lifecycle)

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This planning specification grants no implementation, database, migration, launcher, provider, Modal, network, stage, commit, push, task-approval, gate-launch, or allowlist authority. Draft 10 records owner decisions through D-197 and updates Draft 9 as listed in "Changes from Draft 9." The exact S2 allowlist is absent. Draft 9's proposed offline command ceilings remain unapproved proposal text; Draft 10 creates no new ceiling or allowlist.

**Draft 10 note (2026-11-13).** This revision incorporates the owner decisions recorded as D-194 through D-197, the Rev67 conditional crosswalk, and the BE/AI handoff dependencies. Draft 9 remains unchanged and is the pinned source for this update. Older plan history below is subordinate to the current authority, owner dispositions, and changes recorded in this revision.
**K3 reading (D-188 and D-196).** K3 remains a carried NOT VERIFIED limitation. It is not by itself a stop. Stop before a later Gate A only if accepted evidence cannot establish the Story-chain target. This does not approve or launch Gate A or another S2 gate.

**S1a-P2 disposition (D-194; D-190).** The owner accepts the S1a-P2 close-out as ACCEPTED WITH KNOWN GAP using `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_CLOSURE_RECORD_20261112.md` and `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` as supporting evidence. The failed Gate P2 approval remains CONSUMED; no second Gate P2 attempt is authorized. The three synthetic rows remain. The production BE1 role adapter remains NOT COVERED. This append-only decision supersedes older draft/not-accepted labels without editing them.
## 0. Authority, sequence and entry conditions

The canonical working product requirements source remains the unsigned FEAT-063 SRS v2.7-draft Rev60, as registered in `docs/context/SRS_AUTHORITY.md`. Reconcile this plan with `DECISIONS.md` through D-197. Rev67 is a newer unsigned owner-supplied comparison input only; it does not replace Rev60 or change `SRS_AUTHORITY.md`. The dated row-by-row comparison is `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md`. Every Rev67 effect on S2/S3 remains CONDITIONAL until separate SRS adoption and contract review.

Owner decision D-194 accepts S1a-P2 as ACCEPTED WITH KNOWN GAP using existing evidence. The failed Gate P2 approval remains consumed and cannot be retried. The three synthetic rows remain, and production BE1 role-adapter coverage remains NOT COVERED under D-190. This closes that task disposition; it does not remove the known gap or approve S2.

The required phase order remains S1a-T, S1a-P, S2, S3. S1b remains DEFERRED under D-171. D-171 and D-172 do not open S2. Before any later S2 approval or implementation:

1. Revalidate accepted S1a-T and S1a-P closure records, commits, and final phase-owned evidence; do not reuse an earlier inventory as the next phase baseline.
2. Revalidate the S1a-P2 accepted-with-known-gap closure and its supporting evidence against D-194. Preserve the consumed failed Gate P2 status, three synthetic rows, and uncovered production BE1 role adapter. No second Gate P2 attempt is authorized.
3. Recompute and pin any required post-S1a-P mypy and database inventory baselines. This draft does not claim current pins or runtime states.
4. Carry K3 as NOT VERIFIED. Before a later Gate A approval, accepted evidence must establish the exact Story-chain target; stop if it cannot. No gate is launched by this draft.
5. Resolve BE/AI handoff dependencies BQ-1 and BQ-2 for dependent mobile resume/job-status acceptance or cancel/abandon wiring. See section 12.
6. Obtain separate owner approval of an exact S2 plan revision, then a separately reviewed exact allowlist and owner-gate instructions. This draft supplies none of those approvals or artifacts.

D-196 answers OQ-S2-1 through OQ-S2-6 as recorded in section 8. These are scope decisions only, not task approval. Recheck later decision-ledger additions before a future approval. Preserve duplicate-identifier lineage in the historical records. Implementation modules with legacy `v22` names do not replace the canonical Rev60 SRS.

## 1. Scope: decisions, source facts and plan inferences

| Area | S2 target or boundary | Authority / evidence | Status |
|---|---|---|---|
| StoryRun create | POST /v1/story-runs for one authenticated Parent profile. Teacher StoryRun selection is excluded from M2. | SRS v2.7-draft Rev60 §21.2; D-171 item 5 | Owner decision fixed; Parent-only |
| StoryRun cancel | POST /v1/story-runs/{id}/cancel with expected run revision and idempotency. | SRS §21.2 and §21.4; D-127; D-171 item 10 | Target contract fixed |
| Job status | GET /v1/jobs/{job_id}, scoped to the authenticated Parent/run. | SRS §21.2; D-171 item 10 | Target route fixed; adapter/wiring is implementation work |
| Assistance submit | POST /api/be1/v1/assistance-requests | D-171 item 10; existing compatibility source | Three-route N-1 acceptance surface |
| Assistance cancel | POST /api/be1/v1/assistance-requests/{assistance_id}/cancel | D-171 item 10; existing compatibility source | Three-route N-1 acceptance surface |
| Assistance status | GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status | D-171 item 10; existing compatibility source | Three-route N-1 acceptance surface |
| Teacher pending assistance | GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending | pilot_assistance.py | Existing compatibility operation; outside the three S2 target operations, but included in the mounted compatibility inventory |
| Existing StoryRun-lite adapter | Current router defines create/cancel and other demo operations. app.py mounts it only in the combined local/test app when STORYRUN_LITE_MAIN_DEMO_ENABLED=1; source marks this demo loopback-only. | app.py; story_run_lite.py; router_composition.py | Static source fact; not a target authenticated Parent API |
| Existing AI Jobs adapter | Candidate GET defaults to /api/collaboration/v1/jobs/{job_id}; the router is not imported or mounted by the reviewed app composition. | ai_jobs.py; app.py; router_composition.py | Static source fact; keep it unmounted. Do not expose it at the target route by mounting the candidate router as-is |
| Provider / Modal | No provider call, Modal work, or active workload in S2. | D-171; OWNER_MODAL_CALL_APPROVED=NO | Excluded |

The mapping of the three existing assistance operations into S2 is a compatibility-test decision under D-171. It does not make those legacy routes new versioned target contracts. D-171 OI-20 classifies currently mounted BE1/classroom/demo routes as frozen compatibility surfaces to be deprecated later; only new target routes receive versioned contracts.

### 1.1 Draft 1 known-fact reconciliation

| Draft 1 item | Current status | Source-grounded consequence |
|---|---|---|
| 1. Draft 9 records an older Rev57 G09 audit claim that the AI Jobs router was not mounted | CONFIRMED by current static imports/composition. Runtime route exposure was not inspected. | Keep the router unmounted; implement the target GET /v1/jobs/{job_id} through an explicitly wired target adapter. |
| 2. StoryRun-lite, repository, router, tests and Modal client changed across the merges | The files are present in the current checkout. story_run_lite routes remain conditional loopback demo routes; modal_function_client.py distinguishes unknown and terminal outcomes. | Treat current files as implementation evidence, not proof of target authenticated behavior. Do not call Modal or a provider. |
| 3. DTR omits two StoryRun-lite receipt rows | CONFIRMED: source maps logical core.upload_command_receipts to physical core.core_upload_command_receipts and maps story.command_receipts; repository uses both. | D-171 keeps these as DTR amendments. Record the crosswalk; do not edit the SRS or DTR here and do not infer DDL approval. |
| 4. Alembic has multiple branches and depends_on edges; K3 was reported FAIL | Static revision metadata confirms multiple roots/branches; 20261104_story_revisions is the latest node in the Story chain, not a repository-wide head. No Alembic CLI or database was inspected. D-196 carries K3 as NOT VERIFIED; the target must be established from accepted evidence before a later Gate A. | Carry K3 as NOT VERIFIED for the S2 entry. Read the accepted S1a-P closure and current committed graph before pinning a migration command. Never use upgrade heads by default. |
| 5. Profile age rule for 121-155 months was open in Draft 1 | RESOLVED by D-171 item 6. Existing values remain readable; new StoryRun creation is refused for 121-155 months; no clamp, delete or rewrite. New ages are 36-120. | Remove the owner question. Test the StoryRun service using trusted persisted age and assert no run write on refusal. |
| 6. N-1 request-to-job-to-status/cancel route evidence was missing | Draft 11 says it had not been exercised. Existing T9 route tests use monkeypatches and are not the required real PostgreSQL route acceptance. | Keep M2-AT-09 open until a real composed/authenticated route test passes without monkeypatching _build_child_binding or overriding the dependency under test. |
| 7. B1 orphan invalidation/reconciliation/read-exposure was open | D-171 item 10 fixes S2 acceptance: an orphan is accepted only with a result reference and authoritative receipt; status cannot report success without that receipt. Runtime evidence remains NOT RUN. | Implement and test the disposition in S2. Do not call an orphan accepted from job state alone. |

### 1.2 Decision/inference split

| Decision-fixed behavior | Plan inference and technical proposal |
|---|---|
| Parent-only StoryRun path; no Teacher random selection in S2 (D-171 item 5). | Use the real Parent identity and profile ownership port in the target classroom composition. Do not reuse the unauthenticated loopback demo composition. |
| Concurrency loser is 409 ACTIVE_RUN_EXISTS; idempotency behavior follows SRS §21.4 (D-171 item 10). | Use the durable Story owner lock/unique constraint and transaction; compare the stable error code and message, not a body containing a request_id. |
| Assistance timeout is non-terminal AWAITING_RECONCILIATION; success requires an authoritative receipt; orphan acceptance requires a result ref and authoritative receipt (D-171 item 10). | Persist the request/job/reconciliation projection so a fresh process can read it. Keep provider execution outside this phase. |
| Keep both receipt mappings as amendments; AI Jobs router stays unmounted; S2 route set is fixed; age 121-155 is refused (D-171 item 10). | Add the logical-to-physical receipt crosswalk and implement a target GET adapter; do not edit historical migrations or mount the candidate AI Jobs router. |
| Sequential phase use of sketch2life_m2_s1a, with inventory and mypy baselines recomputed between phases (D-171 item 2; D-172). | Extend the two-inventory owner-gate pattern from D-175 to S2 using the accepted S1a-P post-run inventory, never the S1a-T inventory. |

D-196 resolves OQ-S2-1 through OQ-S2-6 as scope decisions. BQ-1 and BQ-2, other owner fields not answered by D-194 through D-197, S2 task approval, exact allowlist approval, and owner-run gate approvals remain open or separate authorization steps.

### 1.3 Target route composition for AT-08 and AT-09

Use `create_classroom_app()` (`create_app(_composition_profile="classroom")`) for the S2 route acceptance in AT-08 and AT-09. The planned test environment is `SKETCH2LIFE_ENV=test`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true`, `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=false`, `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`, with dotenv disabled. Static source shows this profile mounts the classroom/Parent route group and Pilot Assistance, and does not mount the combined local/demo router group. These settings and route behavior are a source-based plan, not runtime verification.

S2 must add and wire new authenticated Parent target adapters in both the durable classroom profile and the combined application profile for `POST /v1/story-runs`, `POST /v1/story-runs/{id}/cancel`, and `GET /v1/jobs/{job_id}`. The adapters must resolve the verified Parent principal and owner-scoped profile through the accepted S1a-P contract. Keep all three routes out of the local/demo profile. The current `story_run_lite` router is an unauthenticated loopback demo and remains unmounted; the existing candidate `ai_jobs` router also remains unmounted. The job-status target is a new Parent-scoped adapter, not a path-prefix or mount of the candidate router. AT-09 uses the three existing Pilot Assistance compatibility operations in the §1.3 classroom composition. Do not substitute the Teacher-pending compatibility GET.

S2's OpenAPI work must register these three approved target operations in the full runtime route/schema inventory and in the client-facing SRS projection produced by `project_srs_v22_openapi`. Add only the D-171-approved S2 paths to the current projection; do not add additional compatibility operations or infer target status from existing projection membership. Preserve the pre-existing projection members and classify them by exact path and authority; any proposal to remove or reclassify one is a scope change that returns to the owner. The current source projection omits the S2 StoryRun/Jobs targets; the approved S2 implementation must add the D-171 route set and its exact schemas/tags, then verify the complete runtime schema/catalog and published projection as separate outputs. No runtime OpenAPI was generated during this planning review.

## 2. Invariants and data ownership

| Invariant | Requirement source | S2 acceptance |
|---|---|---|
| Commands use principal/operation/resource-scoped idempotency. Same key and payload replays; same key with a different payload returns INVALID_IDEMPOTENCY_KEY. | SRS §21.4 | AT-08 replay and no-duplicate assertions |
| One adult cannot create two active runs concurrently. The durable loser response is 409 ACTIVE_RUN_EXISTS. | SRS §21.4; D-171 item 10 | AT-08 uses separate requests/connections and observes one durable run |
| Cancel of an incomplete run returns 202 DELETE_PENDING, checks the expected revision, releases the active-owner lock in the same transaction, and retains result/assets/receipts. DELETE_PENDING is not deletion. | SRS §21.2; D-127 | AT-08 checks state, lock, retained evidence and idempotent replay |
| Job state is durable in PostgreSQL; queue delivery does not become the source of truth. Completion is fenced by target kind/ref/revision/hash. | SRS §§22.1-22.2 | AT-08 restart/recovery and stale-result checks |
| ai_jobs.attempt is the attempt/retry ledger. No provider retry or Modal call is authorized in S2. | SRS §22.3; D-171 | No provider invocation; test stored transitions only |
| Assistance status never reports success without an authoritative receipt. Timeout stays non-terminal AWAITING_RECONCILIATION. | D-171 item 10 | AT-09 checks status before and after process restart |
| An orphan result is accepted only if it has a result reference and authoritative receipt; otherwise it is not exposed as accepted. | D-171 item 10; SRS §22 | AT-08/09 assert stale, missing-ref and missing-receipt cases fail closed |
| Existing profiles aged 121-155 months stay readable and unchanged but cannot start a new StoryRun. New ages are 36-120. | D-171 item 6 | AT-10 reads trusted stored age, refuses before run persistence, and asserts no clamp/write |
| No cross-owner database joins or foreign keys. Story, AI Jobs, Core and BE1 communicate through typed opaque refs/ports. | SRS §§9.7, 9.9 and 22 | Static boundary review and route tests |

| Logical owner | Relevant logical/physical records | Boundary |
|---|---|---|
| Story | story.runs; run inputs; story revisions/scenes/reviews; story.command_receipts | Owns run lifecycle and Story receipts |
| AI Jobs | ai_jobs.job, attempt, command/completion receipts, outbox and job events | Owns durable job state and dispatch/recovery |
| Core | upload sessions/parts, asset lineage, logical core.upload_command_receipts / physical core.core_upload_command_receipts | Owns upload receipts and asset provenance |
| BE1 compatibility | Assistance request and job state accessed through existing BE1/Pilot Assistance adapters | Existing compatibility surface; no cross-module table writes from Story |
| Parent | S1a-P-owned profiles and revisions | S2 resolves a typed profile ref and trusts the persisted age; S2 adds no Parent schema owner |

Draft 9 records a Rev57 Physical Data Dictionary observation about two StoryRun-lite receipt rows. Treat that observation as historical until a later static reconciliation against canonical Rev60. D-171 preserves the logical receipt names as amendments. This plan records only the logical-to-physical crosswalk; it does not authorize DDL or change the SRS/Data Table Register.

## 3. Acceptance criteria (NOT RUN)

| ID | Required evidence |
|---|---|
| M2-AT-08 - Parent StoryRun concurrency, cancel and restart | Through the new authenticated Parent target adapters in the §1.3 `create_classroom_app()` profile and real application/repository wiring, submit two concurrent create commands for the same Parent. Exactly one active run/job/receipt/effect is created; the loser is 409 ACTIVE_RUN_EXISTS. Cancel a non-completed run using the current expected revision and idempotency key; receive 202 DELETE_PENDING, release the active lock in the same transaction, and retain result/assets/receipts. Replay must not duplicate effects. Create a durable pending/recoverable state; record the old process PID, stop that OS process, confirm that PID has exited, and only then start a fresh OS process and new composition against the same task DB. Through the restarted `create_classroom_app()` composition and real route/auth dependency wiring, make an authenticated owner request to `GET /v1/jobs/{job_id}` and assert the durable, owner-scoped job status/version. Also request that job as a distinct non-owner Parent and assert the contract-defined denial without exposing job data. The fresh process must create no duplicate run/job/outbox effect and reject stale or orphan output without the D-171 receipt conditions. Same-process object recreation, a lifespan restart, or a TestClient restart does not count. If termination cannot be confirmed within the approved timeout, stop and record NOT RUN. |
| M2-AT-09 - N-1 assistance route lifecycle | Exercise the three exact operations through the §1.3 `create_classroom_app()` profile, real authentication and real dependency wiring against PostgreSQL: submit, status, cancel. Do not monkeypatch _build_child_binding, replace the route dependency under test, or call the service/repository directly as a substitute. Cover success only after a durable SUCCEEDED state and authoritative receipt; timeout as non-terminal AWAITING_RECONCILIATION with no success; orphan with no result ref or no authoritative receipt as not accepted. Repeat status after a real OS process stop and fresh-process start against the same DB. The extra Teacher-pending compatibility GET is inventoried by S3 and is not substituted for one of these three operations. |
| M2-AT-10 - S2 age eligibility | Exercise the new trusted profile-lookup boundary used by StoryRunLiteService.create_run; ignore any client-supplied age. New ages 36 and 120 may proceed under the approved profile contract. For the legacy refusal case, the owner-selected test-only fixture at this typed lookup seam returns ages 121 and 155 with a synthetic legacy profile ref. Use the real application service and StoryRun repository against the task DB, and assert refusal occurs before any run/job/receipt/outbox write. The fixture is not inserted into `parent.*`, does not bypass the 36–120 database CHECK, and does not read a BE1 row or widen Parent-only scope. This evidence tests the refusal decision and absence of StoryRun persistence; it does not claim that a Parent database row can store a 121–155 age. Preserve any actual legacy source value; do not clamp, rewrite or delete it. This S2 criterion does not close broader Q-11 lifecycle policy. |

AT-08 and AT-09 require route, authentication, composition and persistence evidence. Unit, repository, mocked route, static, or OpenAPI tests cannot substitute for the owner-run PostgreSQL route gate. For denied requests, capture response code/message/request_id presence and prove the denied action created no run/job/receipt/outbox row. Redact secrets and URI-like output. Keep correlation IDs and synthetic marker IDs traceable without logging child content.

## 4. Static assumption audit and marker plan

D-171 item 11 requires this audit before each review. The following are test/runner design constraints, not results from a live database:

| Assumption | Static result / required control |
|---|---|
| Server address identity | PostgreSQL inet text may include a prefix such as 127.0.0.1/32. Use host(inet_server_addr()) before loopback comparison; do not compare inet_server_addr()::text directly. |
| Database text forms | Before an owner gate, statically identify output form for inet, UUID, timestamp/timestamptz, bigint, boolean and NULL. Treat NULL as a typed absence, not the string "None" or "NULL" unless the runner explicitly emits that representation. No live query was run here. |
| Row markers | Every table written by an acceptance or denied path must have a deterministic marker strategy. A uuid4 primary key is not a marker. Use a synthetic authenticated Parent subject/run ID as an explicit marker where the schema already stores it; correlate child rows by an FK/reference to that marked root row. For generated IDs, include their parent relationship in the marker query. Before S2 approval, statically trace every INSERT/UPDATE from each approved test and publish exact table, marker column, join path, marker value and cleanup status. If a table cannot be proven to belong to this run, stop; do not widen the test or cleanup scope. |
| LIKE patterns | Do not use an unescaped marker in SQL LIKE. Underscore and percent are wildcards. Prefer exact equality or an explicitly escaped literal pattern, and prove the matcher against adversarial values. |
| Error body comparison | BE1 error envelopes contain request_id. Compare stable code and message, and assert request_id exists/is safe; do not compare the entire body to a fixed request ID. |
| Redirected output | Windows redirected pytest output is CRLF. Official-summary matching must accept CRLF, for example a $-anchored expression ending in \r?$. Do not add a second -q because pyproject.toml already configures -q. |
| Writable temp/cache | The Codex sandbox cannot write under tmp/M2_* and pytest will not create a missing parent for --basetemp. Future commands must use a known-writable approved log root whose parent already exists, create a unique child before execution, and put basetemp/cache there. Ruff uses --no-cache or the same approved log root. |
| One-run feasibility | Each future runner and command is NOT YET DRAFTED and NOT VERIFIED for passability. Before approval, statically simulate all guards and prove command order, exact run count, inventory baseline, target revision, loopback predicate, log/result paths, and stop behavior. If any precondition cannot be true under the approved owner environment, return to planning; never retry to obtain PASS. |

### 4.1 Provisional marker coverage

This matrix is a planning requirement. It is not the final marker manifest and grants no table writes.

| Write family | Marker approach to prove before approval |
|---|---|
| story.runs | Unique synthetic Parent issuer/subject carries the run ID; verify the stored active-owner/principal field is the exact marked identity |
| story.run_inputs, revisions, scenes, review records | Correlate to the marked StoryRun ID with same-owner joins; verify each relation is constrained to the one marked run |
| story.command_receipts | Exact idempotency/actor scope marker and resource_ref to the marked run |
| ai_jobs.job | Exact owner_scope_ref marker and target ref to the marked StoryRun |
| ai_jobs.attempt, command/completion receipts, outbox, job events | Correlate by the marked job ID; verify no rows are created for the denied/stale case |
| Core upload/asset rows, if the test writes them | Exact marked actor scope and upload/session lineage to the marked run; otherwise seed an existing approved synthetic asset and assert it is retained |
| BE1 assistance request/job records | Exact synthetic device/child/session principal marker and request/job reference; determine the physical tables and every write path from the post-S1a-P source before approval |
| AT-10 legacy-age fixture | A unique synthetic profile ref returned only by the trusted profile-lookup test seam; do not insert a 121–155 value into Parent tables or use a BE1 row. Query exact StoryRun-side marker paths before/after to prove no run-side writes. |

Any additional write table discovered during the static trace must be added to the reviewed marker manifest before S2 approval. A failed or missing marker check is a stop, not permission to broaden the scan or delete rows.

## 5. Database, migration and command framework

### 5.1 Database and migration proposal

Use only sketch2life_m2_s1a after S1a-P ACCEPTED and committed. Never use shared sketch2life, create another DB, clean the task DB, delete the 29 S1a-T rows, or reset inventory.

Current static migration source identifies 20261104_story_revisions as the latest node in the Story chain. The proposal for Gate A is an explicit upgrade to that Story-chain target, after confirming the accepted S1a-P graph and current target state. It is not a repository-wide head. Never use upgrade heads or stamp an inferred state. The Story root declares a depends_on edge to pilot vision; inspect the exact post-S1a-P revision graph and version rows before approval. The Parent migration remains its own owner branch; no cross-owner FK or dependency is proposed because Story reads the Parent profile through a typed port/ref.

Owner decision D-196 sets OQ-S2-3 to no additive Story DDL for M2. No Story migration is included or authorized. If a later verified requirement appears to need schema change, stop and return with a new reviewed plan and owner decision before changing scope. Do not alter historical migrations or the canonical Rev60 SRS/Data Table Register. Current live DB state, Alembic version rows, target applicability, and rollback feasibility remain NOT VERIFIED.

S2 uses two owner-run gates following the sequential inventory pattern clarified in D-175 and phase order in D-171:

1. **Gate A - owner-run migration, NOT LAUNCHED.** Compare a read-only pre-run inventory to the accepted S1a-P final post-run inventory/hash. If different, stop. Run one exact, approved target revision once; capture a read-only post-migration inventory and pin it by hash for Gate B. The owner runs it and handles any hidden password prompt.
2. **Gate B - owner-run PostgreSQL acceptance, NOT LAUNCHED.** Compare a read-only pre-run inventory to the pinned Gate A post-migration inventory. If different, stop. Run the exact approved PostgreSQL acceptance once. AT-08 and AT-09 must use the real §1.3 composition, authentication and dependency wiring. AT-10 uses the owner-selected lookup-seam fixture with the real application service and StoryRun repository against the same task DB; it must prove refusal and zero run-side writes without inserting a legacy-age Parent row or replacing AT-08/09 route dependencies. Capture the post-run inventory and marker counts. Preserve all prior-phase rows and record the runner. No cleanup/reset.

S2 scripts do not exist in this planning task. Their static passability cannot be claimed. Each script must have its own exact path/hash, launch instruction, read-only inventory implementation, hidden password prompt, one-run ceiling, official-summary rule, output-safety scan and stop-gate review before owner execution. Codex stops before either owner gate.

### 5.2 Offline command ceilings proposed for a later S2 Task Approval

These are ceilings for review, not authorization to execute now. Exact command strings, paths and logs belong in a later approved allowlist.

| Command class | Maximum | Rule |
|---|---:|---|
| Focused offline pytest, including route/catalog/composition tests that provably open no DB and no network | 2 total | One first run and at most one fix-driven rerun of affected tests. Official summary required; no retry after missing summary or environment block |
| Strict mypy | 2 total | One baseline before S2 source edits, one after. Compare normalized diagnostics; no new S2 diagnostics. Exit 1 is never PASS |
| Ruff | 2 total | Use exact edited/new paths and --no-cache. D-176: only the six baseline I001 diagnostics in unchanged regions may be recorded as exit 1 / NO PASS / zero new diagnostics; any other/new diagnostic blocks. |
| validate_harness.py, validate_repository_security.py, validate_architecture.py, validate_skeleton.py when structure changes, and git diff --check | 2 each | One initial result and at most one fix-driven rerun; a missing verdict is NOT RUN and stops the sequence |
| Offline Alembic SQL preview | 1 | Artifact-only; no connection and never apply its SQL |
| Gate A owner-run migration | 1 | Owner only; exact target and inventory checks |
| Gate B owner-run PostgreSQL acceptance | 1 | Owner only; after Gate A evidence is accepted |
| Modal/provider/network | 0 | Prohibited |

Every future command uses cmd.exe /d /c, direct stdout/stderr redirection, a separate exit record, a new unique log directory, exact working directory, and approved output scan. The official pytest-summary matcher is CRLF-aware. No command is repeated to obtain PASS. If command execution lacks a verdict, record NOT RUN and stop.

### 5.3 Allowlist method and deferred pin step

There is no S2 allowlist in this draft. Do not infer one from Draft 1 or hash the current S1a-P working tree. Build it only after S1a-P is ACCEPTED and committed and after the owner later approves the exact S2 draft and requests allowlist preparation:

1. Recheck branch, HEAD, clean index, clean worktree, S1a-P acceptance/commit, closure record, final inventory, current D-number and canonical SRS hash.
2. Enumerate every needed input/change from the final S2 requirements-to-code-to-test map. Use exact repository-relative paths only, no globs. Assign R (read-only current input), E (edit existing), N (new), or H (historical read-only record; never edit or replace) per path. Exclude all S1a-P files outside explicit S2 need; flag the shared app/composition/OpenAPI/catalog/migration files for cross-phase review.
3. Capture byte count and SHA-256 with Python for every existing R/E/H path at the clean post-S1a-P commit. N paths have no pre-existing content hash; pin their exact planned names and verify their output hashes before review/approval.
4. Reject duplicate paths, absolute paths, wildcards, changed pins, and files still being edited by another phase. Any scope change or new shared path requires a new draft revision and cold review.
5. Attach the exact allowlist and pin manifest to a new S2 draft revision. Do not append a Task Approval entry or start implementation in this task.

## 6. Stop gates and NOT RUN

Stop before any S2 approval or implementation if S1a-P lacks ACCEPTED/commit/closure, its actual final inventory or mypy baseline is missing, accepted evidence cannot establish the Story-chain target for Gate A, the target Alembic graph changes, a route or table requires owner product/permission/scope authority, the AT-10 fixture cannot be supplied through the trusted lookup seam without bypassing the Parent constraint or crossing into BE1 scope, a marker cannot be proven, a shared file is still changing, a path/hash differs, a test needs DB/network/provider access before its owner gate, or a reviewer proposes scope/allowlist expansion.

Current NOT RUN / NOT VERIFIED:

- Runtime application construction, OpenAPI generation, tests, validators, mypy, Ruff and diff checks.
- Database connection, PostgreSQL inventory, live Alembic state/graph, migration, launcher, Docker, Modal, provider and network.
- Actual route exposure under a live environment; this plan records static composition only.
- S1a-P acceptance, commit, owner-run Gate A/Gate B closure and final post-run inventory.
- S2 Gate A, Gate B, process stop/restart acceptance, recovery and orphan acceptance.
- Exact S2 allowlist, exact future command strings and scripts, row-write set, final marker manifest, and runner passability.

No source, decision, approval, S1a-P file or file outside an explicitly permitted new draft/review report was changed.

## 7. Dev story-flow adoption audit (static reading on 2026-11-12, nothing executed)

### 7.1 What `origin/dev` provides (files and signatures read; behavior not run)

- `routers/parent_story_runs.py` (251 lines) under `/api/parent/v1/story-runs`: create (201), read by id, read the active run, subject confirmation, story-revision confirmation. `routers/parent_ai.py` (668 lines) under `/api/parent/v1/ai` carries the Modal-facing AI routes, which S2 must not exercise (OWNER_MODAL_CALL_APPROVED=NO). The dev routers are mounted only in `mount_all_routers`, not in the classroom profile.
- `application/services/parent_story_runs.py` (148 lines): `ParentStoryRunService` with create, read, read-active, confirm-subject, reserve and confirm story revision. Create takes `parent_profile_id` and `expected_profile_revision_ref`.
- `infrastructure/persistence/parent_story_repository.py` (1,095 lines) over the existing StoryRun-lite tables. One active run per account: the stored key is the BE1 `account_id` taken from `AdultIdentityModel` (router lines 47-56, repository line 78). The loser error is `PARENT_ACTIVE_STORY_RUN_EXISTS` (409, repository lines 82 and 138), not the SRS code `ACTIVE_RUN_EXISTS`. Idempotency fields appear only on child records scoped `STORY_RUN` (lines 530-531 and 922-923). Create (lines 37-141) reads the dev Parent models, holds a row lock on the profile and requires a data authorization.
- Migration `20261110_parent_profile_story_context`: creates `parent.child_profiles`, `parent.profile_revisions`, `parent.data_authorizations`; alters `story.runs` and `story.run_inputs`. Its `down_revision` is a tuple that merges twelve heads (including `20261104_story_revisions` and `20261110_ar_0001`) and does not include the S1a-P revision (`down_revision=None`, a separate root). Migration `20261110_parent_lesson_pin` adds columns to `story.run_inputs` and chains onto the first.
- The author's contract document (`PARENT_API_CONTRACT_REV67_20261110.md`, lines 79-80) lists as not implemented: a general idempotency-key contract, cancel and delete lifecycle, durable job polling and reconciliation.
- What the existing StoryRun-lite code already has (HEAD, `infrastructure/story_run_lite/repository.py` lines 356-470): create with a command receipt, `ACTIVE_RUN_EXISTS`, and the active-owner lock, keyed on `actor_scope_ref` (lines 402 and 445).

### 7.2 Known DDL and structural consequences of the dev migration

The dev migration is not applied as it stands. If any part of it is carried into S2 (either path), these facts apply:

1. Its foreign keys from `story.run_inputs` to `parent.profile_revisions` and `parent.data_authorizations` (migration lines 197-216) cross an owner boundary and break the Draft 5 invariant of no cross-owner foreign keys (section 2); the S2 migration must not create them and keeps typed opaque references.
2. The CHECK `ck_story_run_input_parent_context` (lines 217-230) requires `data_authorization_id IS NOT NULL whenever a context snapshot exists. A synthetic profile has no authorization (S1b is DEFERRED), and a CHECK on `run_inputs` cannot read `parent.child_profiles.data_origin`, so excluding or refusing non-synthetic profiles needs a marker column or snapshot field, which is more DDL.
3. It rewrites `ck_story_run_state` (adds `COMPLETED`) and the versions, hashes and sizes CHECKs, and relaxes asset-column nullability on `story.run_inputs` only; each rewrite needs line-level review against the Draft 5 invariants.
4. Its 12-head merge `down_revision` conflicts with the Draft 5 section 5.1 rule (explicit Story-chain target, never `upgrade heads`); an S2 migration must be one additive revision on the accepted Story chain.
5. The parent-table creation is removed because the S1a-P tables exist.
6. Its downgrade raises when data exists; the S2 migration must state the rollback disposition required by section 5.1.
7. If the lesson pin is kept, its migration needs a new parent revision because its current parent is the dev story-context migration.
8. Draft 9 listed these potential FR-P-06 snapshot and lesson-pin columns: `context_revision`, `context_snapshot`, `context_snapshot_sha256`, `context_confirmed_by`, `context_confirmed_at`, `source_profile_revision_ref`, `data_authorization_id`, `current_input_revision` (on `story.runs`), and lesson-pin columns. D-196 defers both features, so this hypothetical DDL is not current M2 scope and creates no migration. A future scope change requires a new owner decision and reviewed plan.

### 7.3 Fit against S2 (static audit; basis-B planning evidence)

This retained Draft 9 comparison is static planning evidence. D-196 selects basis B, so option-A adaptations below are not current M2 commitments. Its OQ-S2-4 and OQ-S2-5 entries describe features now deferred by D-196.

| S2 requirement | Dev status (static) | HEAD StoryRun-lite status (static) | Adaptation only if option A is reopened |
|---|---|---|---|
| `POST /v1/story-runs`, `POST /v1/story-runs/{id}/cancel`, `GET /v1/jobs/{job_id}` on the SRS paths | Different paths, no cancel, no jobs route | Create and cancel exist as demo routes; no authenticated Parent target adapters | New target adapters over the chosen service; dev paths stay out of the classroom profile |
| Principal, operation and resource scoped idempotency; `INVALID_IDEMPOTENCY_KEY` | Not general (child records only) | Create has a command receipt | Add through `story.command_receipts` |
| Concurrent create: loser is 409 `ACTIVE_RUN_EXISTS` | Active-owner key on BE1 `account_id`; code `PARENT_ACTIVE_STORY_RUN_EXISTS` | `ACTIVE_RUN_EXISTS` and the lock exist, keyed on `actor_scope_ref` | Dev path: map the code and choose the key supplier; S1a-P2's role port answers only yes or no, so `account_id` has no supplier and S2 would use the principal-derived scope |
| Cancel returns 202 `DELETE_PENDING`, expected revision, releases the lock in one transaction | Missing | Cancel exists as a demo route; target contract not verified | Add or adapt |
| Durable, owner-scoped job status; non-owner denial; no success without a receipt; orphan rule (D-171 item 10) | Missing | AI Jobs router unmounted | Add over `ai_jobs`; keep the candidate router unmounted |
| Trusted age lookup; refuse stored ages 121-155 without clamp or write (AT-10) | Dev profile range is 36-120 only | Client-supplied age today (Draft 8 of S1a-P, section 2.2) | S2 adds its own read-only typed profile-lookup port over the accepted repository; test fixture at that seam |
| Ownership by issuer plus subject; refuse `DELETE_PENDING` | Router compares the BE1 identity issuer with the principal (lines 47-56) but stores key only on `owner_subject`; profile row lock | Not profile-bound | Use the S1a-P models through the lookup port; a cross-owner read cannot take a row lock, so the race between a profile deletion and a run creation is recorded as a known limit unless the allowlist places the check in one transaction |
| Profile revision pinned at run creation | Present (`expected_profile_revision_ref`) | Absent | Keep; the reference becomes the S1a-P `profile_revision_id` |
| FR-P-06 adult-confirmed minimal context snapshot | Create requires `sketch2life.parent-context.v1` | Absent | OQ-S2-4 |
| Lesson pin | Create takes a pin through the lesson-library service | Absent | OQ-S2-5 |
| Consent or data authorization before a run; `consent_policy_version` request field and its settings gate | Required by the dev flow | None | Not adopted for `SYNTHETIC_DEV` profiles (D-155 F-7, D-171 item 9; the SRS name is `SYNTHETIC_TEST`, an owner-accepted naming mapping); non-synthetic fails closed (S1b DEFERRED); the field and its gate are removed |
| Error envelope | `HTTPException(detail={"code": ...})` | Story envelope | Adapt to the SRS section 9.8 envelope |
| Three Pilot Assistance routes (AT-09) and the `core.upload_command_receipts` crosswalk | Not touched by the dev flow | Existing | Unaffected |
| OpenAPI and catalog | Dev routes are not in the SRS catalog | Demo routes only | Register exactly the three target operations (section 1.3) |

Draft 9's static comparison identified the FR-P-06 snapshot and lesson pin (plus subject and story-revision flows that Draft 5 excludes) as dev-only values. D-196 defers the snapshot and pin. The remaining S2 route requirements still need the Draft 5 basis implementation or a later reviewed integration.

### 7.4 Not adopted by S2

S1b consent/data-authorization tables, routes, or sharing; dev `/api/parent/v1/*` story routes; mobile/UI route changes; the FR-P-06 adult-confirmed context snapshot; lesson pin; subject-confirmation and story-revision flows beyond create, cancel, and job status; API V2 adoption; and real-child-data or provider-backed work are outside this S2 scope. A separate UI task moves the apps to separately approved routes. M2 work remains synthetic-only; `OWNER_MODAL_CALL_APPROVED=NO`.

### 7.5 Rev60 authority and Rev67 conditional crosswalk

Rev60 remains the canonical working SRS. Owner-supplied Rev67 is an unsigned newer draft and a comparison input only. The crosswalk at `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md` marks each document-control row Rev61 through Rev67 as CONDITIONAL or NOT AFFECTED, with section and line references in both versions. S2 create-input and activity-selection changes, including the photo-first flow and API V2 gate, remain conditional on separate Rev67 adoption. The target create/cancel/job-status operation set and cancel/job-status semantics are not expanded by the crosswalk. No Rev67-only requirement is silently adopted.

## 8. Owner decisions for OQ-S2-1 through OQ-S2-6

D-196 records the owner's answers. These answers define the proposed M2 scope but do not approve Draft 10, any allowlist, or any gate.

| ID | Owner decision | Current M2 effect |
|---|---|---|
| OQ-S2-1 | Option B: keep Draft 5's StoryRun-lite service basis and merge dev later. Switch to option A only if OQ-S2-4 or OQ-S2-5 becomes yes. Option C is infeasible. | Draft 5 basis remains the M2 proposal. The dev implementation is not adopted as-is. |
| OQ-S2-2 | Do not mount dev `/api/parent/v1/*` story routes in M2. A separate UI task moves apps to approved routes. | No dev Parent story route is added to either M2 composition. The UI migration is separate. |
| OQ-S2-3 | No additive Story DDL. | No Story migration or schema extension is in M2. |
| OQ-S2-4 | Defer the FR-P-06 adult-confirmed context snapshot. | No snapshot contract or persistence change is part of M2. |
| OQ-S2-5 | Defer the lesson pin. | No lesson-pin request field, persistence, or access recheck is added by M2. |
| OQ-S2-6 | Carry K3 as NOT VERIFIED, as accepted in D-188. Hard stop only if accepted evidence cannot establish the Gate A Story-chain target. | K3 remains an explicit limitation; it does not by itself block the phase. No gate is approved or launched. |

The three target Story operations remain `POST /v1/story-runs`, `POST /v1/story-runs/{id}/cancel`, and `GET /v1/jobs/{job_id}`. The three assistance compatibility operations remain as described in Draft 9 and D-171. No dev `/api/parent/v1/*` route is mounted. The Rev67 crosswalk describes conditional future contract differences; it does not authorize new routes, DDL, or semantics.

## 9. NOT RUN and NOT APPROVED

No S2 or S3 approval, launch, implementation, or owner-run gate occurred under this draft. The exact S2 allowlist and future command strings are absent. No backend, database, Docker, Modal, pytest, mypy, Ruff, validator, install, or provider command was run for this record-and-draft task. Runtime application construction, route exposure, OpenAPI generation, database inventory/state, migration applicability, Gate A, Gate B, stop/restart acceptance, and marker verification remain NOT RUN or NOT VERIFIED.

S1a-P2 is ACCEPTED WITH KNOWN GAP by D-194 based on the existing closure record and real-PostgreSQL evidence addendum. Gate P2 remains FAILED/CONSUMED; no second attempt is authorized. The three synthetic rows remain, and production BE1 role-adapter coverage remains NOT COVERED. These are recorded limitations, not pending retries.

BQ-1 and BQ-2 remain unanswered. No Modal/provider call or real-child-data use is authorized. No source code was changed in this task; only append-only owner records and new planning documents were written in the designated worktree.

## 10. Change record

Draft 6 over Draft 5 added the note, entry conditions 5 and 6, and sections 7 to 9. Draft 7 over Draft 6 stated the DDL consequences, corrected facts and restated OQ-S2-1 to OQ-S2-3. Draft 8 over Draft 7 (round-2 review: NEEDS_REVISION, 0 P1, 4 P2): P2-1 reuse claims corrected and the HEAD StoryRun-lite column added (7.1, 7.3, OQ-S2-1 with the dev-only value named, the `account_id` supplier gap stated); P2-2 FR-P-06 and the lesson pin become OQ-S2-4 and OQ-S2-5, and section 7.2 lists the DDL and states it applies to both paths if either is kept; P2-3 OQ-S2-2 restated (cannot be kept unchanged, D-171 item 10 noted); P2-4 K3 reading added to the status note and OQ-S2-6. P3: "must not create" for the FKs; marker-column DDL; state CHECK `COMPLETED` and the other rewritten CHECKs; rollback and lesson-pin chain; the audit then answer then allowlist sequence; the decision citation corrected to D-155 F-7 and D-171 item 9 (it was wrongly D-156 O5); the DELETE_PENDING race and lookup-port ownership; the error envelope and `consent_policy_version` rows; the commit hash source. No scope row, invariant, acceptance criterion or command ceiling of Draft 5 changed.

Draft 9 over Draft 8: section 7.5 added and the note line; no other change.


## 11. Changes from Draft 9

- Updated the title and status to Draft 10 / DRAFT / NOT APPROVED / NOT LAUNCHED. Draft 9 remains unchanged and is pinned below.
- Replaced Rev57-as-current authority with canonical Rev60 per `docs/context/SRS_AUTHORITY.md`; linked the Rev67 conditional crosswalk and kept all Rev67 deltas conditional.
- Recorded D-194 S1a-P2 acceptance with known gap, the consumed failed Gate P2 attempt, no retry, three retained synthetic rows, and production BE1 role adapter NOT COVERED under D-190. Older records and labels remain unedited.
- Replaced OQ-S2-1 through OQ-S2-6 recommendations with D-196: basis B; no dev Parent routes; no additive Story DDL; snapshot and lesson pin deferred; K3 carried NOT VERIFIED under the target-evidence stop condition.
- Added D-197 S1b/OI and provider/data boundaries, and explicit BQ-1/BQ-2 dependencies from the BE/AI handoff.
- Recorded PR 25's merge into `dev` by the repository co-owner and dev tip `c87d8008` as context only, not a decision or approval.
- Preserved Draft 9's proposed command ceilings as unapproved historical proposal text. Draft 10 creates no allowlist, new ceiling, approval, or gate instruction.
- S3 Draft 5 remains unchanged; its refresh waits for an accepted S2 and a separate review/approval.

## 12. Open dependencies and owner fields

### BE/AI handoff dependencies

- **BQ-1 INPUT_PROCESSING:** Legal state/job transitions after context confirmation, the triggering request, and sufficiency of `GET /v1/story-runs/active/current` remain unverified. This blocks dependent mobile resume and job-status acceptance until answered with evidence.
- **BQ-2 Parent cancel/abandon route:** The verified route, method, request/response, authorization, idempotency behavior, and state transition remain unverified. This blocks mobile cancel/abandon wiring and acceptance until answered. Do not infer that mobile `/api/parent/v1/*` paths are approved for M2.

### Owner decisions and boundaries still open

S1b remains DEFERRED under D-171. Q-04 and Q-13 remain unanswered. No sharing is exposed. OI-05, OI-06, OI-07, and OI-08 remain OPEN and deferred. Real-child-data and provider use remain blocked; work remains synthetic-only. `OWNER_MODAL_CALL_APPROVED=NO`. Owner fields outside decisions expressly recorded in D-194 through D-197 remain open. Exact S2 plan approval, exact allowlist approval, and each owner-run gate approval remain separate and ungranted.

### Integration context

The repository co-owner merged M2 branch PR 25 into `dev`; the observed dev tip for this planning snapshot is `c87d8008`. This is context only. It does not change the basis-B decision, approve mounting dev routes, or authorize implementation or gates.

## 13. Source pins

Every cited planning input used for this revision is pinned below. SHA-256 values are full 64-character digests; byte counts refer to the exact files read at drafting time.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT9_20261112.md` | 49154 | `6B6821710E3A5716DFA5AB6FB827A980F96717109BA8F0640BB93CBAEBF58C9C` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S3_TASK_APPROVAL_DRAFT5_20261110.md` | 23308 | `BC2518817202C6275CED9543200CC17DAAADA36759FF4B53C4FF3D16928A2B9D` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_S3_PLAN_REVIEW_ROUND4_20261110.md` | 9553 | `D2A4BB19B513F9B69A2D0AE51FFDB30D2631F96CAC82C3A6C84A38B00495CE26` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1B_DECISION_BRIEF_20261109.md` | 2368 | `CBD93FA70F45B82C22F42E6D956AE0E5E956A2BB067E1D0EF7B5ADE70E8E637D` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md` | 133204 | `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md` | 9206 | `F746A7B3D425A2C6EF0541C28A8584CC8CEF0D6D0F140CD09A68F14F9FA091EA` |
| `tmp/m2-s2-s3-review/M2_S2_S3_OPEN_QUESTIONS.md` | 8274 | `2E74E680B6074BDFCA2DD91EA7C18BB85587B2F94F1674F6EB01B31C36952A9D` |
| `tmp/m2-s2-s3-review/M2_S2_S3_STATUS_REPORT.md` | 19418 | `5E926225AE94ECC703B572735A325A8FFA5D4438B1E03F4803BF2F86141932D1` |
| `docs/context/SRS_AUTHORITY.md` | 4054 | `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` |
| `docs/context/SOURCE_REGISTER.md` | 113526 | `D09F5849F4A3829EC4241FF1A840319225909E0EECA93A9BF6964625C4E987A0` |
| `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | 66896 | `08A0AE379D87CD237A923F921E2FC7F1385BAAE63C74F264FEBD24721FC1EED1` |
| `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | 113670 | `7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF` |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 553948 | `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` |
| `.worktrees/mobile/tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md` | 634291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_CLOSURE_RECORD_20261112.md` | 3503 | `0C1801119F17D98FBD4ADA2C7D884530DFAB4A068AF88DE7C74525ADA61F40E4` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` | 5547 | `6BB4A6EA6F477B44486A4E518766099CC2DA9A97246DE7ADAD08E4C00C891485` |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 190063 | `BDC6FB0A5F5B350F1C3DDD21175277FB169B618BFFE8075567FBF485B02F813C` |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 404042 | `0D4E434C2D932C5FBF09D7BAE75DBA46CD29835AA41884FBFEBFC2A36C5DA73A` |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/PARENT_API_CONTRACT_REV67_20261110.md` | 9573 | `0BB99DAFDC6592118B367EBEB60BC0D15FBE80DCD697499EB68EC135C302C47D` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md` | 9184 | `98C3E656B2CDA391C103C21D10E780DF3BB102286E2053360C1690D03FC11891` |
