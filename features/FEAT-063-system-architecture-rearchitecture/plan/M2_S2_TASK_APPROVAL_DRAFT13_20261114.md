# M2 S2 Task Approval - Draft 13 (cancel idempotency reconciliation and status evidence)

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This document is a planning revision only. It grants no source implementation, database or migration action, provider or Modal call, network use, stage, commit, push, Task Approval, allowlist, command ceiling, or gate launch. No S2 or S3 approval is given.

**Revision note (2026-11-14).** Draft 13 is based on Draft 12 and the independent round-3 cold review. It records D-200, the owner's option A decision: cancel idempotency-key reuse with a different request returns HTTP 400 and detail.code INVALID_IDEMPOTENCY_KEY. D-200 supersedes D-199 only for that mismatch response; a same-key, same-run, same-request retry still replays the stored HTTP 202 receipt, and every other D-199 decision remains in force. Draft 13 adds the context-confirmation row to the BQ-1 code-reading table and explicitly marks the crosswalk's GET /v1/jobs/{job_id} entry as superseded by D-199. Rev60 remains the formally canonical working SRS under docs/context/SRS_AUTHORITY.md and D-195. The owner-selected unsigned Rev67 is used as a requirements input for this refinement only; it is not formally adopted. Draft 12, Draft 11, Draft 10, Draft 9, the Rev67 crosswalk, S3 Draft 5, the foundation plan, Round 4, and the prior cold reviews remain unchanged. PR 25 was merged by the repository co-owner; dev tip c87d8008b70910eb0a4d3579b9490312e7e3143f is context only.


## 0. Authority and current owner dispositions

- Rev60 remains the formally canonical working SRS under docs/context/SRS_AUTHORITY.md and D-195; it is unsigned. For this refinement only, the owner selected the unsigned Rev67 file as a product-requirements input. Rev60 §21.4 and owner-selected Rev67 §21.4 both require INVALID_IDEMPOTENCY_KEY for a mismatched reused key and neither specifies the HTTP status. D-200 records the owner's HTTP 400 choice based on the current Parent helper. This use does not formally adopt Rev67, alter D-195, or edit docs/context/SRS_AUTHORITY.md.
- D-194 formally accepts the S1a-P2 close-out as ACCEPTED WITH KNOWN GAP, based on the existing closure record and real-PostgreSQL addendum. The failed Gate P2 approval remains CONSUMED; no second attempt is authorized; three synthetic rows remain; production BE1 role-adapter coverage remains NOT COVERED under D-190. The older conflicting draft/not-accepted text remains unchanged.
- D-198 changes only OQ-S2-1 from D-196 to option A-prime. D-199 refines Parent cancellation and job-status evidence. D-200 supersedes D-199 only for cancel idempotency-key reuse with a mismatched request: HTTP 400 with detail.code INVALID_IDEMPOTENCY_KEY. D-200 changes no other part of D-194 through D-199.
- OQ-S2-2 remains no S2-added /api/parent/v1/* story routes; OQ-S2-3 remains no additive Story DDL; OQ-S2-4 adult-confirmed context snapshot and OQ-S2-5 lesson pin remain deferred; OQ-S2-6 carries K3 as NOT VERIFIED under D-188, with a hard stop only if accepted evidence cannot establish the Gate A Story-chain target.
- S1b stays DEFERRED. Q-04 and Q-13 stay unanswered; no sharing is exposed. OI-05 through OI-08 remain OPEN and deferred. Real-child-data and provider use remain blocked; work remains synthetic-only. OWNER_MODAL_CALL_APPROVED=NO.
- S3 Draft 5 remains unchanged. Its K3 clause is stale context and must be reconciled to D-198 in any future S3 revision. S3 still requires accepted S2 closure and a separate S3 Task Approval; this draft meets neither condition.

## 1. Changes from Draft 12

| Round-3 finding or owner decision | Draft 13 disposition |
|---|---|
| P2-1 - cancel idempotency mismatch response | D-200 records the owner's option A choice: HTTP 400 with detail.code INVALID_IDEMPOTENCY_KEY. Rev60 and owner-selected Rev67 §21.4 require the code but leave HTTP status unspecified; the current Parent helper uses HTTP 400. D-200 supersedes D-199 only for this mismatch response. AT-08 separates same-request replay, same-run/different-payload mismatch, and cross-run reuse. |
| P3-1 - BQ-1 omitted context confirmation | Added a repository-reading row: context confirmation leaves run_state and job_state unchanged, sets context_confirmed, and the existing owner GET exposes context_confirmed, run_state, job_state, retryable, and error_code. Follow-on request/dispatch/provider behavior remains open or not verified where source does not establish it. |
| P3-2 - crosswalk lists a stale /jobs route | The unchanged crosswalk's GET /v1/jobs/{job_id} entry is explicitly marked superseded by D-199; S2 uses only the existing Parent active/current and by-ID reads for job-status evidence. |
| Scope and prior decisions | All other D-194 through D-199 decisions, Draft 12 boundaries, and prior finding dispositions are preserved. D-200 changes no S2/S3 approval, route scope beyond D-199, DDL, allowlist, command ceiling, gate, or launch status. |

## 2. Scope and decision register

| Question | Owner decision in force | Effect in this draft |
|---|---|---|
| OQ-S2-1, D-196 as revised by D-198 and refined by D-199 | Option A-prime. Use the integrated Parent StoryRun router, service and repository already in dev; no parallel StoryRun-lite target adapter. S2 hardens the existing create path, adds Parent cancel, adds the three assistance compatibility-test operations, and adds AT-08 through AT-10 evidence. Job-status evidence uses the existing owner-scoped active/current and by-ID Parent reads; no separate job route is mounted. | Preserve all existing create/read/confirmation handlers. Add no duplicate create implementation and do not mount the StoryRun-lite demo adapter. |
| OQ-S2-2 | S2 does not add dev /api/parent/v1/* story routes. Existing dev composition is the baseline; S2 neither removes routes nor adds routes other than Parent cancel. A separate UI task moves apps to approved routes. | The current /v1/story-runs router remains in the combined profile. The mobile prefix mismatch remains a separate UI task. |
| OQ-S2-3 | No additive Story DDL. Cancel must use existing columns, states and receipts. If it cannot, stop and ask the owner. | No migration or schema extension is proposed or authorized. |
| OQ-S2-4 | Defer the FR-P-06 adult-confirmed context snapshot. | No new confirmation flow or DDL. Existing dev columns and existing create behavior are source facts, not approval to extend them. |
| OQ-S2-5 | Defer lesson pin. | No new lesson-pin behavior or DDL. Existing columns are not extended. |
| OQ-S2-6 | Carry K3 as NOT VERIFIED under D-188. Stop only if accepted evidence cannot establish the Gate A Story-chain target. | K3 remains a limitation, not a pass or a gate launch. No task-database state is inferred from source files. |

The dated Rev67 crosswalk remains unchanged. Its historical current-disposition row still says basis B; D-198 supersedes that statement only for OQ-S2-1. The crosswalk's line 28 entry GET /v1/jobs/{job_id} is superseded by D-199 and is not an S2 route: use only the existing Parent GET /v1/story-runs/active/current and GET /v1/story-runs/{run_id} reads for job-status evidence; the AI Jobs candidate router remains unmounted. D-200 changes only cancel mismatch status/code as described above. Rev61 through Rev67 retain their crosswalk dispositions; Rev67 is an owner-selected requirements input for this refinement, not a formal SRS adoption.

## 3. Route ownership and composition profiles

### 3.1 Existing source composition

The Parent StoryRun router prefix is /v1/story-runs (backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:43). Its existing create handler is POST /v1/story-runs (lines 116-197); existing active/current and read-by-ID handlers are GET /v1/story-runs/active/current (lines 200-219) and GET /v1/story-runs/{run_id} (lines 222-240). Context, subject and script confirmation handlers remain on this router. There is no Parent cancel handler today. The existing GET responses already expose run_state, job_state, retryable and error_code (backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113; backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-138).

mount_classroom_routers mounts authentication, admin, health, BE1 runtime and Parent Profiles routers, plus Pilot Assistance when enabled; it does not mount parent_story_runs_router (backend/src/sketch2life/interfaces/http/router_composition.py:35-45). mount_all_routers composes those routers with the demo, lesson-library, Parent AI and Teacher AI groups, and mounts parent_story_runs_router when include_parent_story_runs is true (backend/src/sketch2life/interfaces/http/router_composition.py:60-77). create_app defaults to the combined profile and STORYRUN_LITE_MAIN_DEMO_ENABLED=0; the normal combined profile therefore includes the existing Parent router. Only the combined local/test demo-flag profile omits it and mounts StoryRun-lite instead (backend/src/sketch2life/interfaces/http/app.py:256-267,1003-1010). S2 does not use the demo profile.

The AI Jobs candidate defines GET /api/collaboration/v1/jobs/{job_id} (backend/src/sketch2life/interfaces/http/routers/ai_jobs.py:29,36-45) but is not imported or mounted by backend/src/sketch2life/interfaces/http/router_composition.py. S2 does not mount it.

### 3.2 Planned ownership by operation and profile

This table distinguishes current source behavior from the D-199 plan. A planned route or evidence item is not approval to implement or launch it.

| Operation | Durable classroom profile | Combined application profile |
|---|---|---|
| Existing Parent create, active/current, by-ID read and context/subject/script confirmation | Not mounted by mount_classroom_routers; S2 adds no classroom mount. | Already owned by parent_story_runs_router with the normal combined profile; preserve handlers and routes. The StoryRun-lite demo-flag profile is outside S2. |
| Parent cancel | No Parent StoryRun router is mounted. S2 adds no separate classroom mount. | No current cancel handler. Add POST /v1/story-runs/{run_id}/cancel to the existing Parent router/service/repository path. |
| Parent job-status evidence | No Parent StoryRun reads or job-status route are mounted. S2 adds neither the AI Jobs candidate nor another classroom route. | Use only the existing owner-scoped GET /v1/story-runs/active/current and GET /v1/story-runs/{run_id} responses. They expose run_state, job_state, retryable and error_code. This is evidence on the existing run resource, not a separate /jobs route. A separate /jobs read is deferred to the video phase. |
| Assistance submit and cancel compatibility operations | Existing pilot_assistance_router and assistance_requests handlers are available when Pilot Assistance is enabled: POST /api/be1/v1/assistance-requests and POST /api/be1/v1/assistance-requests/{assistance_id}/cancel. S2 tests them and creates no target route. | Same existing handlers when the combined profile's Pilot Assistance predicate enables them. |
| Assistance status compatibility operation | Existing child_status handler: GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status. S2 tests this compatibility operation. | Same existing handler when Pilot Assistance is enabled. |
| Teacher-pending assistance | Existing compatibility handler, outside the three S2 assistance operations. | Existing when Pilot Assistance is enabled; not an S2 target. |

For AT-08 and AT-10, use the combined profile with the default StoryRun demo flag off. The intended Parent identity boundary remains the authenticated Parent principal and role-reader path with a synthetic test principal and deterministic test role store (backend/src/sketch2life/interfaces/http/parent_runtime.py:46-83,120-131; backend/src/sketch2life/interfaces/http/routers/parent_profiles.py:73-90; backend/src/sketch2life/application/ports/parent_roles.py:14-15). That test-store evidence does not cover the production BE1 role adapter. The existing StoryRun router currently uses get_verified_adult and _require_parent with a direct AdultIdentityModel query (backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:40,69-78); do not describe that as the ParentRoleReader path. D-190 keeps production Be1ParentRoleAdapter PostgreSQL coverage NOT COVERED pending separate BE1 alignment. If future acceptance requires Parent StoryRun routes in the classroom profile, stop for a new owner decision because D-198 did not authorize a composition change.

apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts:89-110 currently forms mobile paths under /api/parent/v1/story-runs, while the server router is /v1/story-runs. This mismatch is a separate UI-task dependency. D-199 authorizes no mobile edit, /api/parent/v1/* route, or route removal.

## 4. Acceptance criteria (future evidence only; NOT RUN)

### M2-AT-08 - Parent create concurrency, cancellation, and durable status

All acceptance evidence in this section is future work and NOT RUN. Use the combined profile with STORYRUN_LITE_MAIN_DEMO_ENABLED=0, synthetic-only identities and a future separately approved route/persistence gate. Use a test principal and role store for Parent-role testing; this does not cover the production BE1 adapter under D-190. The durable classroom profile has no Parent StoryRun routes.

| Case | Test setup and expected result | Source or decision |
|---|---|---|
| Competing creates | Send two concurrent creates for the same synthetic Parent and same payload with two DISTINCT Idempotency-Key values. Expect one HTTP 201 create, one run and one CREATE_RUN receipt; the losing request returns HTTP 409 with detail.code ACTIVE_RUN_EXISTS. The distinct keys prevent the route's replay check from short-circuiting the repository conflict. | D-199; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:116-149; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:51-90,156-160; backend/alembic/versions/20261102_story_run_lite.py:388-395. |
| Same-key create replay | As a separate case, repeat the same create payload with the same key. Expect the saved HTTP 201 replay for the existing run/receipt; do not treat it as the competing-create loser. | backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:126-149; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:169-215. |
| Parent cancel success | POST /v1/story-runs/{run_id}/cancel with required Idempotency-Key and an owned unfinished run. Expect HTTP 202, run_state DELETE_PENDING, active_owner_parent_account_id cleared in the same transaction, and a saved receipt whose purge_state is PENDING. Only purge_state and the 202 status are fixed publicly by D-199; other receipt fields/envelope and exact precondition header encoding remain OPEN. Rev60 §21.2 line 1646 requires the current run revision; do not invent an If-Match wire contract. | D-199; Rev60 §21.2 line 1646; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:43; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1290-1301,1327-1391; backend/alembic/versions/20261112_parent_story_context.py:195-203. |
| Same-key cancel replay | The same key with the same run and same request returns the recorded HTTP 202 receipt. | D-199; D-200; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1303-1391. |
| Same run, different cancel payload | Reusing the same key for the same run with a different request fingerprint returns HTTP 400 with detail.code INVALID_IDEMPOTENCY_KEY. Rev60 §21.4 and owner-selected Rev67 §21.4 require the error code but do not specify HTTP status; D-200 selects 400, consistent with the current helper and router mapping. | D-200; Rev60 §21.4; owner-selected Rev67 §21.4; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1327-1352; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:81-85. |
| Cross-run cancel key reuse | Reuse of the same Parent-scoped key against a different run/request returns HTTP 400 with detail.code INVALID_IDEMPOTENCY_KEY. The planned CANCEL_RUN path must use a Parent-wide collection receipt scope to detect cross-run reuse; if existing receipt columns/helpers cannot support this without DDL, stop under D-196 OQ-S2-3. | D-199; D-200; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:51-79,1303-1391; backend/alembic/versions/20261102_story_run_lite.py:484-527. |
| Wrong-state cancellation | COMPLETED, FAILED and DELETE_PENDING each return HTTP 409. The StoryRun-lite analogue rejects FAILED and DELETE_PENDING (backend/src/sketch2life/infrastructure/story_run_lite/repository.py:2629-2649) but does not itself reject COMPLETED; the new Parent route must enforce D-199's explicit COMPLETED guard. No public error code/body beyond the status is assumed. | D-199; backend/src/sketch2life/infrastructure/story_run_lite/repository.py:2629-2649. |
| Ownership and active lock | A non-owner cancelling or reading another Parent's run gets the existing HTTP 404 not-found result. After cancellation, active/current does not return that DELETE_PENDING run; clearing the active-owner field releases the partial unique lock so a subsequent create by the same Parent can succeed. | D-199; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:206-240; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:308-323,1290-1301; backend/alembic/versions/20261102_story_run_lite.py:355-395. |
| Job-status evidence | The owner reads run_state, job_state, retryable and error_code through active/current or by-ID. A non-owner's by-ID read returns RESOURCE_NOT_FOUND/HTTP 404. No job-ID route is added; a separate /jobs read remains deferred to the video phase. | D-199; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113,200-240; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:217-323,1290-1301; backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-138. |

The Parent cancellation reference is StoryRun-lite cancel_run at backend/src/sketch2life/infrastructure/story_run_lite/repository.py:2575-2685. It shows an atomic DELETE_PENDING transition, saved command receipt and active-owner lock release in its database transaction. It is a semantic reference only; the StoryRun-lite demo router/adapter stays outside S2. S2 adds no purge worker, provider cancellation, AI-job cancellation or deletion-complete claim. PENDING means the purge lifecycle has not completed.

The current Parent receipt check already allows operation CANCEL_RUN (backend/alembic/versions/20261112_parent_story_context.py:195-203). Parent repository helpers lock and find/store command receipts. The existing active-owner column and partial unique index are in backend/alembic/versions/20261102_story_run_lite.py:355,388-395; Parent create maps that unique conflict to ACTIVE_RUN_EXISTS (backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:156-160). These static code facts support the no-additive-DDL plan, but do not prove task-database contents or runtime behavior.

#### BQ-1 code-reading transition table

This table records assignments in the Parent repository; it is not runtime, worker-dispatch or provider evidence.

| Event | run_state | job_state | Source lines |
|---|---|---|---|
| Create | INPUT_PROCESSING | null; create does not assign job_state and the column is nullable | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:105-122; backend/alembic/versions/20261102_story_run_lite.py:338-381 |
| Artwork accepted and analysis starts | INPUT_PROCESSING | RUNNING | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:530-544 |
| Artwork analysis succeeds | SUBJECT_REVIEW | SUCCEEDED | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:603-618 |
| Artwork analysis has a known failure | FAILED | FAILED | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1154-1173 |
| Artwork analysis outcome is unknown | INPUT_PROCESSING | AWAITING_RECONCILIATION | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1154-1173 |
| Parent confirms the subject | PREPARATION_REVIEW | no job_state assignment in this transition | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:730-742 |
| Parent confirms context; owner read shows context_confirmed=true and status fields | Unchanged from the prior allowed state (INPUT_PROCESSING, SUBJECT_REVIEW or PREPARATION_REVIEW) | Unchanged; confirm_context makes no job_state assignment | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:269-271,345-378,382-400,422; backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113,228-240; backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-133 |
| Story generation starts | SCRIPT_GENERATING | RUNNING | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:934-947 |
| Story generation succeeds | SCRIPT_REVIEW | SUCCEEDED | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1021-1034 |
| Story generation outcome is unknown | SCRIPT_GENERATION_UNKNOWN | AWAITING_RECONCILIATION | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:1080-1114 |

After context confirmation, the existing owner-scoped by-ID GET returns the response fields context_confirmed=true, run_state, job_state, retryable and error_code. The repository code leaves both state fields unchanged in confirm_context; this is persistence-code evidence only. Which request or dispatch follows context confirmation and any later worker/provider result remain OPEN or NOT VERIFIED. This does not claim runtime or job execution evidence.

### M2-AT-09 - three assistance compatibility operations and receipt handling

Exercise the three existing compatibility operations through the composed route and dependency path, using synthetic-only identities/data. Do not substitute the Teacher-pending GET or call the service/repository directly instead of the routes. Do not monkeypatch `_build_child_binding` or replace the route dependency under test. No provider or Modal call is authorized.

| Operation | Source-defined public result to assert |
|---|---|
| First accepted submit | HTTP 202. `AssistanceReceipt` envelope with `contract_version="0.1-candidate"`, `correlation_id`; device `data` with `contract_name="AssistanceRequestDeviceView"`, matching `contract_version`, `assistance_id`, `request_revision`, `status="pending"`, `job_id` (which may be null), and `poll_after_ms` while pending. `meta.outcome="created"`, `replayed=false`, `resource_revision` equal to the request revision, `projection="device"`. The response has ETag, `Cache-Control: no-store`, and `Vary: Authorization`; a replay also has `Idempotency-Replayed: true`. Sources: `assistance_requests.py:62-96,143-159`; `assistance.py:1310-1320`; `contracts/schemas/assistance_requests.py:154-176`. |
| Status after an accepted authoritative receipt | HTTP 200 fields `assistance_id`, `request_revision`, `status`, `processing_state`, `poll_after_ms`. For a still-pending request with a SUCCEEDED/ACCEPTED job, result reference, and matching authoritative completion receipt, `processing_state="submitted_to_teacher"`, `status="pending"`, and `poll_after_ms=2000`. Without the authoritative receipt, status must not claim `submitted_to_teacher`; in the SUCCEEDED-but-unaccepted/orphan case the source maps processing state to `unknown`. Sources: `pilot_assistance.py:95-103,382-440,458-505`. |
| Accepted cancel | HTTP 200 receipt envelope; for the first accepted cancel, `meta.outcome="cancelled"`, `replayed=false`, `projection="device"`, and the device data reports `status="cancelled"` with `poll_after_ms=null`. Resource revision is the resulting request revision. Headers include ETag, `Cache-Control: no-store`, and `Vary: Authorization`. Sources: `assistance_requests.py:98-117,143-159`; `assistance.py:1310-1320`; schema `assistance_requests.py:154-176`. |

The success receipt asserts accepted receipt handling only; HTTP 202 on submit is not proof that a provider completed. Timeout remains non-terminal and does not report success. A missing result reference or authoritative receipt cannot be accepted as success under D-171. Any change beyond the existing assistance compatibility contract is OPEN and requires a separate contract decision; D-199 adds no assistance target route.

### M2-AT-10 - trusted stored-age eligibility

Use the existing trusted profile lookup path, not a client age field. New ages 36 and 120 are eligible; ages 121 and 155 are refused. A 36/120 create success is HTTP 201 with `{request_id, story_run}`. Source-defined response values include `story_run.run_state="INPUT_PROCESSING"`, the profile and profile-revision refs, and `story_run.context_snapshot.age_months` equal to the trusted stored value; the route response also carries `context_confirmed=false` on this existing create path. The corresponding Story-side writes are one `story.runs` row with that `child_age_months`, state `INPUT_PROCESSING`, revision/version 1 and current input revision 1; one `story.run_inputs` row; and one `CREATE_RUN` command receipt. The current create method does not create an AI job or outbox row. Sources: `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113,116-197`; response schema `backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-138`; service `backend/src/sketch2life/application/services/parent_story_runs.py:52-66,193-207`; repository `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:91-155`.

For trusted lookup values 121 and 155, expect HTTP 422 and stable code `INVALID_REQUEST`; the current route maps service errors to detail.code; any additional envelope fields absent from source remain OPEN and are not invented. The trusted service check runs before `repository.create_run`, so there must be no Story run, run-input or create-receipt write for the refusal. Use a test-only typed profile-lookup fixture for those legacy values; do not insert an out-of-range age into Parent tables, bypass the constraint, or read a BE1 row. Existing code: `backend/src/sketch2life/application/services/parent_story_runs.py:55-66,193-207`; `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:105-155`.

The age range 36-120 also appears in the current Parent API contract Rev67 (lines 33, 48), profile domain rules (`domain/parent_profiles.py:10-11,69-100`), and mobile rule helper (`profileRules.ts:1-6`). Rev67 remains conditional under D-195; it is a comparison input, not this draft's authority. Whether the full Rev67 create request and context-confirmation contract is adopted remains OPEN and is not implied by AT-10.

## 5. Static migration graph, DDL boundary and database status

The following graph is a static reading of the 31 revision files in the worktree at the PR 25 dev snapshot. The table records each file's `revision`, `down_revision` and `depends_on`; it is not output from Alembic CLI and is not evidence of the task database's version table.

Static roots (`down_revision=None`, 13): `20261014_0001`, `20261015_ai_0001`, `20261017_ap_0001`, `20261017_lc_0001`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261028_ll_0001`, `20261102_pv_0001`, `20261102_story_run_lite`, `20261109_m2_parent_profiles`.

Static terminal revisions when following both `down_revision` and `depends_on` edges (10): `20261017_lc_0001`, `20261018_ap_0009`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261109_m2_parent_profiles`, `20261110_ar_0001`, `20261112_parent_story_context`. The Story chain is `20261102_story_run_lite` -> `20261103_story_upload_compat` -> `20261104_story_revisions` -> `20261112_parent_story_context`; the StoryRun-lite revision also declares a dependency on `20261102_pv_0001`. These are file-derived relationships only. K3 remains NOT VERIFIED.

| Migration file | revision | down_revision | depends_on | bytes | SHA-256 |
|---|---|---|---|---:|---|
| `backend/alembic/versions/20261014_0001_core_persistence.py` | `20261014_0001` | `?` | `?` | 11186 | `55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C` |
| `backend/alembic/versions/20261014_0002_be1_runtime.py` | `20261014_0002` | `20261014_0001` | `?` | 10959 | `08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520` |
| `backend/alembic/versions/20261014_0003_canvas_payload.py` | `20261014_0003` | `20261014_0002` | `?` | 520 | `194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5` |
| `backend/alembic/versions/20261014_0004_be1_constraint_names.py` | `20261014_0004` | `20261014_0003` | `?` | 3759 | `AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD` |
| `backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py` | `20261015_ai_0001` | `?` | `?` | 13321 | `D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714` |
| `backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py` | `20261017_ap_0001` | `?` | `?` | 5976 | `81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A` |
| `backend/alembic/versions/20261017_ap_0002_effective_scope.py` | `20261017_ap_0002` | `20261017_ap_0001` | `?` | 2549 | `35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7` |
| `backend/alembic/versions/20261017_ap_0003_resource_ledger.py` | `20261017_ap_0003` | `20261017_ap_0002` | `?` | 7510 | `FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924` |
| `backend/alembic/versions/20261017_ap_0004_copy_inventory.py` | `20261017_ap_0004` | `20261017_ap_0003` | `?` | 4303 | `3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7` |
| `backend/alembic/versions/20261017_ap_0005_copy_evidence.py` | `20261017_ap_0005` | `20261017_ap_0004` | `?` | 1107 | `9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12` |
| `backend/alembic/versions/20261017_lc_0001_content_publication.py` | `20261017_lc_0001` | `?` | `?` | 5171 | `DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498` |
| `backend/alembic/versions/20261018_ap_0006_copy_operations.py` | `20261018_ap_0006` | `20261017_ap_0005` | `?` | 1577 | `B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7` |
| `backend/alembic/versions/20261018_ap_0007_copy_delivery.py` | `20261018_ap_0007` | `20261018_ap_0006` | `?` | 2600 | `3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52` |
| `backend/alembic/versions/20261018_ap_0008_delivery_authority.py` | `20261018_ap_0008` | `20261018_ap_0007` | `?` | 966 | `9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05` |
| `backend/alembic/versions/20261018_ap_0009_copy_resolution.py` | `20261018_ap_0009` | `20261018_ap_0008` | `?` | 3444 | `465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44` |
| `backend/alembic/versions/20261018_kv_0001_knowledge_video.py` | `20261018_kv_0001` | `?` | `?` | 2284 | `E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87` |
| `backend/alembic/versions/20261018_vr_0001_video_review.py` | `20261018_vr_0001` | `?` | `?` | 5968 | `3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7` |
| `backend/alembic/versions/20261019_ae_0001_activity_execution.py` | `20261019_ae_0001` | `?` | `?` | 3108 | `56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30` |
| `backend/alembic/versions/20261019_pa_0001_preset_automation.py` | `20261019_pa_0001` | `?` | `?` | 2459 | `D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8` |
| `backend/alembic/versions/20261019_vf_0001_video_failure.py` | `20261019_vf_0001` | `?` | `?` | 3751 | `0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178` |
| `backend/alembic/versions/20261024_0005_classroom_srs_contracts.py` | `20261024_0005` | `20261014_0004` | `?` | 6254 | `E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C` |
| `backend/alembic/versions/20261028_ll_0001_lesson_library.py` | `20261028_ll_0001` | `?` | `20261024_0005` | 19803 | `733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83` |
| `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` | `20261031_be1_se_0001` | `20261024_0005` | `?` | 5037 | `421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC` |
| `backend/alembic/versions/20261101_be1_age_provenance.py` | `20261101_be1_age_0001` | `20261031_be1_se_0001` | `?` | 1646 | `2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E` |
| `backend/alembic/versions/20261102_pilot_vision.py` | `20261102_pv_0001` | `?` | `20261101_be1_age_0001, 20261015_ai_0001` | 8573 | `6335AD224708AEC8251447A296458854B663FC7DD763EFB184E4AFF156E86BD9` |
| `backend/alembic/versions/20261102_story_run_lite.py` | `20261102_story_run_lite` | `?` | `20261102_pv_0001` | 28335 | `D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143` |
| `backend/alembic/versions/20261103_story_upload_compat.py` | `20261103_story_upload_compat` | `20261102_story_run_lite` | `?` | 821 | `F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166` |
| `backend/alembic/versions/20261104_story_revisions.py` | `20261104_story_revisions` | `20261103_story_upload_compat` | `?` | 8529 | `3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8` |
| `backend/alembic/versions/20261109_m2_parent_profiles.py` | `20261109_m2_parent_profiles` | `?` | `?` | 7545 | `73B907E3782A324EF23F51C30A8F53F2145DDA0E90FE31B5CC686C18BC2922FB` |
| `backend/alembic/versions/20261110_ar_0001_account_roles.py` | `20261110_ar_0001` | `20261028_ll_0001` | `?` | 3413 | `B21E212BC75FE4F23156ABEEC5367C495FC7E1B2F78438AF20BA4406B34A82CA` |
| `backend/alembic/versions/20261112_parent_story_context.py` | `20261112_parent_story_context` | `20261104_story_revisions` | `?` | 8251 | `CFC7A92436066191134E27F1579B54109057CBAC43ABEB72B84C0F2D6CBFD9DF` |

The source backend/alembic/versions/20261112_parent_story_context.py declares revision 20261112_parent_story_context, down_revision 20261104_story_revisions and no depends_on (lines 10-13). Its upgrade fails unless story.runs is empty (lines 30-47). It changes the story.runs run_state check to allow INPUT_PROCESSING, SUBJECT_REVIEW, PREPARATION_REVIEW, SCRIPT_GENERATING, SCRIPT_GENERATION_UNKNOWN, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, DELETE_PENDING, FAILED and COMPLETED (lines 57-65). It adds current_input_revision to story.runs (lines 48-50). It adds source-profile reference, typed idea, idea source, context revision/snapshot/hash, lesson-pin snapshot/hash and context-confirmation fields to story.run_inputs (lines 116-159). Separately, it makes the original and derived asset columns nullable (lines 16-26,67-76) and adds asset size bounds (lines 106-113). Its story.command_receipts operation check already allows CANCEL_RUN (lines 195-203). These are existing migration-source facts. Under D-196/D-199, S2 adds no Story DDL and does not extend the migration. The task database is not inspected.

**Task database: NOT VERIFIED.** No database connection or command was used. The task database's row counts, whether `story.runs` is empty, its stamped Alembic revision(s), migration applicability, and rollback behavior are all NOT VERIFIED. The empty-run condition above describes the migration source only; it does not establish that the condition holds in any database. No migration, inventory, or Gate A/B action is authorized here.

## 6. Rev67 conditional markers

Rev60 remains formally canonical under docs/context/SRS_AUTHORITY.md and D-195. For this refinement, the owner selected unsigned Rev67 as a requirements input; its §21.4 key-mismatch code is identical to Rev60 §21.4. The crosswalk's document-control rows apply as follows; no Rev67-only route or flow behavior is adopted by this draft.

| Rev67 row | Marker | S2/S3 effect recorded by the crosswalk |
|---|---|---|
| Rev61 | CONDITIONAL | Legacy-age lifecycle clarification; the new-run 121/155 refusal is compatible, but grandfathered completion/read/delete behavior is not accepted by AT-10. |
| Rev62 | CONDITIONAL | Photo-first prerequisite and create-input sequence would require create-flow reconciliation if adopted. |
| Rev63 | CONDITIONAL | Catalog-first activity candidate and no-match behavior remain conditional; no activity-selection implementation is added here. |
| Rev64 | NOT AFFECTED | Diagram readiness does not change routes, request contracts or runtime evidence. |
| Rev65 | CONDITIONAL | Lesson-version access recheck matters only if lesson pin enters scope; D-196 defers it. |
| Rev66 | CONDITIONAL | Parent create sequence and required activity selection would change if adopted; API V2/persistence alignment remains open. |
| Rev67 | CONDITIONAL | Required main activity and recovery requirements remain conditional; no new route, pin, snapshot or activity contract is adopted. |

D-198 and D-199 define the current S2 operation set and the Parent cancel/job-status disposition; D-200 supersedes D-199 only for the mismatched cancel idempotency response. Rev60 remains formally canonical. The unchanged crosswalk line 28 entry GET /v1/jobs/{job_id} is superseded by D-199: it is not mounted or added by S2; the existing Parent active/current and by-ID reads provide the planned status evidence. Rev67 is an owner-selected requirements input for this refinement only and is not formally adopted. The crosswalk does not approve routes. Its S3 Draft 5 refresh note remains historical context and waits for accepted S2 plus a separate S3 review and approval.



## 7. Open dependencies, risk context and owner fields

### BE/AI dependencies and open contract questions

- BQ-1's persisted state assignments, including context confirmation, are answered by code reading in the transition table above. The row records the existing owner-read fields; the next request, job dispatch, worker execution and provider behavior remain OPEN or NOT VERIFIED and were not run or verified.
- BQ-2 and BQ-7 are replaced as S2 scope dependencies by D-199. The route, method, required Idempotency-Key, status semantics, and use of existing owner-scoped reads are recorded above.
- BQ-8 is answered by code reading for the current conflict body: _invoke maps the exception to detail.code (backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:81-85), and ACTIVE_RUN_EXISTS is the code (backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:81-90,156-160). A safe current-run reference in that body, as discussed in Rev60 §21.6, remains OPEN for a separate BE/owner decision.
- D-199 fixes HTTP 202 and purge_state=PENDING for cancel success and HTTP 409 for the specified wrong-state conflict cases. D-200 fixes mismatched cancel-key reuse at HTTP 400 with detail.code INVALID_IDEMPOTENCY_KEY; Rev60 and owner-selected Rev67 §21.4 require the code but leave status open, and the owner selected 400 consistently with the existing Parent helper. Same-key/same-request replay remains HTTP 202. Other success-envelope keys, failure-body fields/codes, and the exact revision-precondition header remain OPEN until the Parent contract is reconciled. If existing receipt columns/helpers cannot detect cross-run reuse without DDL, stop under OQ-S2-3.
- BQ-16 red CI is owned by the co-owner and is not an S2 dependency. The repository is not deployed. The four job statuses remain owner-supplied context and are not independently re-verified.

### Owner and phase boundaries

- D-190 production BE1 role-adapter coverage remains NOT COVERED; production acceptance on that adapter waits for separate BE1 alignment. AT-08 test-principal evidence does not close that production gap.
- S1b remains DEFERRED; Q-04/Q-13 unanswered; no sharing; OI-05 to OI-08 OPEN/deferred; synthetic-only; no real-child-data or provider use; OWNER_MODAL_CALL_APPROVED=NO.
- Exact S2 Task Approval, allowlist, command ceiling and owner-run gate approvals remain absent and separate. This draft creates none.
- S3 Draft 5 line 102 says unresolved K3 blocks S2/S3 close-out. That clause is stale context relative to D-188/D-198 and must be reconciled to the accepted-limitation rule in any future S3 revision before separate S3 approval. Do not edit S3 Draft 5 here.
- The foundation plan Draft 11 lines 571-573 predates D-194 through D-199. Its sequencing is historical planning and does not override D-197's S1b deferral or D-198/D-199's current S2 scope. Do not edit the foundation plan here.

### Owner-supplied CI context (not independently re-verified)

The owner reports GitHub Actions run `43059473029` on `dev` at commit `1f5bb0b5`, dated 2026-11-11, plus PR 25 runs `43380946045` and `43401368611`. Four jobs were red: Repository policy checks (Python 3.12.14 absent from runner cache); Backend unit and contract tests (`uv.lock` needs an update while `--locked` was supplied); Teacher UI checks (two failures in `src/__tests__/app.test.tsx`); Admin UI checks (two failures in the same path). Child UI checks pass. These run results were supplied as context only and were not independently re-verified; no network was used.

## 8. Stop conditions and NOT RUN

Before any future approval, stop if the required role/auth boundary or route owner remains unresolved; an existing column/state is insufficient for cancel or job status; accepted evidence cannot establish the Gate A Story-chain target; the migration graph or approved target changes; a route/schema or permission choice needs an owner decision; an AT-10 fixture would bypass the lookup boundary or write a legacy age to Parent tables; a write cannot be marked exactly; the shared app/composition is still changing; a pin differs; or an acceptance needs database, provider, Modal or network work outside its separate approval.

NOT RUN / NOT VERIFIED in this record-and-draft task: backend execution, database access, migration or inventory, Docker, Modal, pytest, mypy, install, validators, OpenAPI generation, runtime route exposure, authentication/authorization execution, concurrency, cancel, receipt handling, age-boundary tests, process restart/recovery, task-database contents, Gate A, Gate B, and CI re-verification. No source code changed. No S2/S3 approval, gate or allowlist was created.

## 9. Input pins

The 44 input-pin rows below and all 31 migration pins in the static graph above were rehashed during this refinement. The owner-selected Rev67 file was separately verified at 634291 bytes and the full SHA-256 shown below matches the repository copy. Root-checkout inputs remain read-only and are not copied into this worktree. The historical pre-D-199 decision pin is verified against the unchanged prefix; the pre-D-200 and post-D-200 DECISIONS pins identify the exact append boundary.

| Location | Input path | Bytes | SHA-256 |
|---|---|---:|---|
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT9_20261112.md` | 49154 | `6B6821710E3A5716DFA5AB6FB827A980F96717109BA8F0640BB93CBAEBF58C9C` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S3_TASK_APPROVAL_DRAFT5_20261110.md` | 23308 | `BC2518817202C6275CED9543200CC17DAAADA36759FF4B53C4FF3D16928A2B9D` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_S3_PLAN_REVIEW_ROUND4_20261110.md` | 9553 | `D2A4BB19B513F9B69A2D0AE51FFDB30D2631F96CAC82C3A6C84A38B00495CE26` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1B_DECISION_BRIEF_20261109.md` | 2368 | `CBD93FA70F45B82C22F42E6D956AE0E5E956A2BB067E1D0EF7B5ADE70E8E637D` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md` | 133204 | `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/plan/BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md` | 9206 | `F746A7B3D425A2C6EF0541C28A8584CC8CEF0D6D0F140CD09A68F14F9FA091EA` |
| root checkout | `tmp/be-ai-questions/BE_AI_QUESTIONS_20261113.md` | 11736 | `EBDBAD3AB823447D5A72298290AD95822F20768CB8C39C89DC299B9AEE097C5F` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT10_20261113.md` | 53129 | `A1A680FE6DC94F6AE3A9ED9FAA766B957269A26E33BE69A64FDA58702098BC1D` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT10_COLD_REVIEW_20261113.md` | 14825 | `E46A0E0A0E10177D00AE66BC52F60F484E47FF93A5E1055A3FB584F6CF370A38` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md` | 9184 | `98C3E656B2CDA391C103C21D10E780DF3BB102286E2053360C1690D03FC11891` |
| S2 worktree, DECISIONS before D-199 | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 192584 | `2BF5C0A08BE168E7F02F41A115109EC07A1532C3E167B2D5688659AEA876EBC9` |
| S2 worktree, DECISIONS after D-199 and before D-200 | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 195904 | `EBDD23B35D797224CE6C2249A152E83002E90AA89144AFD4D908A1756CA0B07B` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 404042 | `0D4E434C2D932C5FBF09D7BAE75DBA46CD29835AA41884FBFEBFC2A36C5DA73A` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_CLOSURE_RECORD_20261112.md` | 3503 | `0C1801119F17D98FBD4ADA2C7D884530DFAB4A068AF88DE7C74525ADA61F40E4` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` | 5547 | `6BB4A6EA6F477B44486A4E518766099CC2DA9A97246DE7ADAD08E4C00C891485` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/artifacts/PARENT_API_CONTRACT_REV67_20261110.md` | 9573 | `0BB99DAFDC6592118B367EBEB60BC0D15FBE80DCD697499EB68EC135C302C47D` |
| root checkout | `docs/context/SRS_AUTHORITY.md` | 4054 | `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 553948 | `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` |
| owner-selected Rev67 content, matching repository copy | `.worktrees/mobile/tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md` | 634291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/router_composition.py` | 3743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/app.py` | 73534 | `262CB4583ED545F92DF784B69D426C834D5D7BD23179A61C5C818E6C50F4C298` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 12698 | `32C707515032FC7BEF08A12D0B1D8E6DD4271FF1B9C55891072BA76E150D6B60` |
| S2 worktree | `backend/src/sketch2life/application/services/parent_story_runs.py` | 7630 | `FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14` |
| S2 worktree | `backend/src/sketch2life/infrastructure/persistence/parent_story_profile_lookup.py` | 2333 | `F994AF975C44A65FC8550F7C2F7E5B4068B78020E9E72DEE5D4BB94203C6A767` |
| S2 worktree | `backend/src/sketch2life/domain/parent_profiles.py` | 4035 | `D632E28F16DCB0CF89517E524C12CBF2AB79315EC9CFF383BF77410BAD27D148` |
| S2 worktree | `apps/ui-mobile/src/parent/domain/profileRules.ts` | 356 | `25EA93AD268DC49704D64F87A2D1252983F745A530CB43D8D67AEFD3EE16C3EE` |
| S2 worktree | `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` | 16805 | `B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918` |
| S2 worktree | `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 64452 | `407D2843A93C31BD54202A1E504DE938FB085E67730C199FD4E9B9505E72B832` |
| S2 worktree | `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7309 | `C026A1566500EE7B7C2705DFCE6C4E0D0EC7B397E9FE93F11A237A416F768B19` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py` | 14276 | `3E2FC42DBB2329CF711D91B085E72AD8E462E55511BE899D13C5CE85E461357C` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/parent_runtime.py` | 5203 | `4329F4E775B2954C53268A836D4A7A30C2923F77E6EDD9B3AACFA7D05E47FA49` |
| S2 worktree | `backend/src/sketch2life/application/ports/parent_roles.py` | 462 | `A9E97AA2D0C09ED4BB271B52F07C42CF5BA652D3F0DC69A1EFF8902659ADDFB3` |
| S2 worktree | `backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py` | 1507 | `1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/routers/pilot_assistance.py` | 20678 | `D2AB3BE3DA9201BB0D76DC82689C4361793FDCB7B63E9F4EB7402A1E23E2670B` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/routers/assistance_requests.py` | 9323 | `2BC20104A480155BDCCBCB200E9B71CD49D2D1E44394B14928AD643E8E2C958E` |
| S2 worktree | `backend/src/sketch2life/application/services/assistance.py` | 60581 | `81C3765BDCDC15C7731B4D05F870542AD7AD6A9D5CCC6F47C05423A7DF57C549` |
| S2 worktree | `backend/src/sketch2life/contracts/schemas/assistance_requests.py` | 7267 | `3C6D16420ECE19B3530B9B04BA86303EC733BD0A24D38DFAD6B1584300BA78EA` |
| S2 worktree | `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py` | 3872 | `8F90789FE6BC5ABBD5B1F2D489C201DD99DEF252AD2182D591A2BECBBC7641B6` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT11_20261113.md` | 39857 | `1FABBCE8E1820C0747868368535E5FFC6BA3FE4019FA7FCE1F1F96B96B8BD95B` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT11_COLD_REVIEW_20261113.md` | 9378 | `2CAEA0611DC1F7C723375F9F08BBBF3CC5D56C82B2B76EFF7260FED590801C54` |
| S2 worktree | `backend/src/sketch2life/infrastructure/story_run_lite/repository.py` | 132748 | `58952C2A210785DBC6459C6FAC6203C5F5460DFEDD7852CD1375E12821E709D5` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT12_20261114.md` | 46385 | `AAC71A6E258585A6CF9B063E75A8FF1E4693C9E23E92065884B4C493B67E0917` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT12_COLD_REVIEW_20261114.md` | 12619 | `DA29C72DC9B9AC8F225E975AC3A2CACEC373088E72CD39936FCE7935980457F4` |
| S2 worktree, DECISIONS after D-200 | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 198453 | `2A13CE8D79BCC34F2DD3E09119BA20BB80B8AE23A71B105D29EE25CCDEC471B7` |
