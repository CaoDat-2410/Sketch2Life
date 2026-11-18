# M2 S2 Task Approval - Draft 11 (integrated Parent StoryRun, compatibility operations and lifecycle evidence)

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This document is a planning revision only. It grants no source implementation, database or migration action, provider or Modal call, network use, stage, commit, push, Task Approval, allowlist, command ceiling, or gate launch. No S2 or S3 approval is given.

**Revision note (2026-11-13).** Draft 11 is based on Draft 10 and the round-1 cold review. It applies owner decisions D-194 through D-198. D-198 revises only D-196 OQ-S2-1 to option A-prime: build on the integrated Parent StoryRun implementation already in the dev snapshot. Draft 10, Draft 9, the Rev67 crosswalk, S3 Draft 5, the M2 foundation plan, Round 4, and the round-1 review remain unchanged. The repository co-owner's PR 25 merge and dev tip `c87d8008b70910eb0a4d3579b9490312e7e3143f` are context only.

## 0. Authority and current owner dispositions

- The repository Rev60 FEAT-063 SRS remains the canonical working SRS under `docs/context/SRS_AUTHORITY.md`; it is unsigned. The owner-supplied Rev67 is an unsigned comparison input only. Its S2/S3 changes remain conditional under the dated crosswalk. D-198 does not adopt Rev67 or change the SRS authority.
- D-194 formally accepts the S1a-P2 close-out as **ACCEPTED WITH KNOWN GAP**, based on the existing closure record and real-PostgreSQL addendum. The failed Gate P2 approval remains CONSUMED; no second attempt is authorized; three synthetic rows remain; production BE1 role-adapter coverage remains NOT COVERED under D-190. This reconciles the earlier labels by append-only records; the older text remains unchanged.
- D-198 changes only OQ-S2-1 from D-196. D-194, D-195, D-197 and the rest of D-196 remain in force.
- S1b stays DEFERRED. Q-04 and Q-13 stay unanswered; no sharing is exposed. OI-05 through OI-08 remain OPEN and deferred. Real-child-data and provider use remain blocked; work remains synthetic-only. `OWNER_MODAL_CALL_APPROVED=NO`.
- S3 Draft 5 is unchanged. Its entry still requires accepted and committed S2 closure, actual phase baselines, and a separate S3 Task Approval. This draft does not satisfy those conditions.

## 1. Changes from Draft 10

| Round-1 finding | Draft 11 disposition |
|---|---|
| P1-1 - route collision and wrong router prefix | Corrects the Parent router prefix to `/v1/story-runs`; applies D-198 A-prime; reuses the existing Parent router/service/repository; records exact current and proposed ownership by composition profile; keeps the StoryRun-lite demo router out of S2; records the mobile `/api/parent/v1/story-runs` versus server `/v1/story-runs` mismatch as an open BQ-7/UI dependency. Existing OpenAPI projection entries are not treated as target approval. |
| P1-2 - stale migration audit | Replaces the stale migration claim with a static 31-file graph, file-derived roots and terminal revisions, and the exact `20261112_parent_story_context` effects. It states no additive Story DDL under D-196 and marks task-database rows and Alembic version state NOT VERIFIED. |
| P2-1 - Parent role boundary | Defines AT-08 using the authenticated Parent-principal dependency and `ParentRoleReader` boundary with a test principal and deterministic test role store. It preserves D-190: this does not cover the production BE1 role adapter. The current StoryRun route's direct BE1 identity query is called out as an integration item to resolve before any approval. |
| P2-2 - observable AT-09/AT-10 results | Adds current source-backed response fields, values and StoryRun-side effects for the assistance receipt lifecycle and age boundaries. Any public error-envelope or route value not fixed by existing source/contract is explicitly OPEN and tied to BQ-7 or BQ-8. |
| P3-1 - pre-existing CI risk | Records the dated run identifiers and four reported red jobs as owner-supplied context, explicitly NOT INDEPENDENTLY RE-VERIFIED. Child UI checks were reported passing. |

## 2. Scope and decision register

| Question | Owner decision in force | Effect in this draft |
|---|---|---|
| OQ-S2-1, D-196 as revised by D-198 | Option A-prime. Use the integrated Parent StoryRun router, service and repository already in dev. No parallel StoryRun-lite target adapter. S2 adds the Parent cancel operation, job-status read, three assistance compatibility-test operations, and AT-08 through AT-10 evidence and hardening of the existing create path: trusted age lookup, concurrency, idempotency and receipts. The StoryRun-lite demo adapter remains unmounted and outside S2. | Keep the existing create/read/confirmation handlers and persistence as the baseline. Add no duplicate create implementation. Exact job-status route ownership remains OPEN under BQ-7. |
| OQ-S2-2 | S2 does not add dev `/api/parent/v1/*` story routes. The existing dev composition is the baseline; S2 does not remove existing routes or add routes beyond the operations above. A separate UI task moves apps to approved routes. | Existing `/v1/story-runs` in the combined profile remains. The mobile client prefix mismatch is visible and unresolved; this draft does not change UI routes. |
| OQ-S2-3 | No additive Story DDL. Cancel and job-status must use existing columns and states. If they cannot, stop and ask the owner. | No migration or schema extension is proposed or authorized by this draft. |
| OQ-S2-4 | Defer the FR-P-06 adult-confirmed context snapshot. | No new confirmation flow or DDL. The already-present dev columns and existing create behavior are baseline facts, not approval to extend them. |
| OQ-S2-5 | Defer lesson pin. | No new lesson-pin behavior or DDL. Existing columns are not extended. |
| OQ-S2-6 | Carry K3 as NOT VERIFIED under D-188. Stop only if accepted evidence cannot establish the Gate A Story-chain target. | K3 remains a limitation, not a pass or a gate launch. No task-database state is inferred from source files. |

The dated crosswalk remains valid for Rev61 through Rev67 requirement comparisons. Its “Current M2 disposition” still says basis B; D-198 supersedes that statement only for OQ-S2-1. This dated Draft 11 records the A-prime correction without editing the crosswalk. All Rev67 requirement markers remain conditional as described in section 6.

## 3. Route ownership and composition profiles

### 3.1 Existing source composition

`parent_story_runs.py` declares `APIRouter(prefix="/v1/story-runs")` at line 43. Its current create handler is `create_parent_story_run` (`POST /v1/story-runs`, lines 116-197); active/current, read-by-id, context confirmation, subject confirmation and script confirmation remain the existing handlers at lines 200-322. The current file has no cancel or job-status handler. Do not describe this router as `/api/parent/v1/story-runs`.

`mount_classroom_routers` currently mounts Parent Profiles and Pilot Assistance but not `parent_story_runs_router` (`router_composition.py:35-45`). `mount_all_routers` composes the classroom and demo groups and mounts `parent_story_runs_router` when `include_parent_story_runs` is true (`:60-77`). `create_app` defaults to the combined profile and defaults `STORYRUN_LITE_MAIN_DEMO_ENABLED` to `0`; the combined profile then mounts the existing Parent router. Only combined local/test mode with the flag set to `1` omits that router and mounts the StoryRun-lite demo router (`app.py:256-267,1003-1010`). S2 does not use the demo setting.

### 3.2 Planned ownership by operation and profile

This table distinguishes source behavior today from the proposed S2 wiring. Proposed wiring is not approval to implement or launch it.

| Operation | Durable classroom profile | Combined application profile |
|---|---|---|
| Existing Parent create, active/current, read, context, subject and script confirmation | Not mounted by the current classroom composition, and S2 does not add a classroom mount. No Parent StoryRun route is available in this profile under the current scope. | Already owned by `parent_story_runs_router` when the default `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`; preserve these handlers and routes. The demo-flag profile is outside S2. |
| Parent cancel | No Parent StoryRun route is mounted here. The cancel handler is planned in the shared Parent StoryRun router used by the combined profile; S2 does not add a separate classroom mount. Rev60 lists `POST /v1/story-runs/{id}/cancel` at §21.2 line 1646. BQ-2 and BQ-7 must settle exact request, response, auth and idempotency details before approval. | No current handler. Add the cancel operation to the existing Parent StoryRun router/service/repository boundary; do not create a second adapter. Keep the existing combined composition. |
| Parent job-status read | No Parent StoryRun route is mounted here. No classroom job-status route is added by S2. | No current S2 handler. Rev60 lists `GET /v1/jobs/{job_id}` at §21.2 line 1648. Exact target router/handler, Parent scoping, denial and response are OPEN under BQ-7. Do not mount the candidate AI Jobs router as-is; it has a `/api/collaboration/v1` prefix and is not imported or mounted by `router_composition.py`. |
| Assistance submit and cancel | `pilot_assistance_router` is mounted by default; it includes `assistance_requests` at `/api/be1/v1`. Existing handlers are `submit` (`POST /api/be1/v1/assistance-requests`) and `cancel` (`POST /api/be1/v1/assistance-requests/{assistance_id}/cancel`). S2 tests these compatibility operations; it does not create new target routes. | Same existing handlers when Pilot Assistance is enabled by the combined profile's environment predicate. |
| Assistance status | Existing `child_status` handler in `pilot_assistance_router`: `GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status`. S2 tests this compatibility operation. | Same existing handler when Pilot Assistance is enabled. |
| Teacher-pending assistance | Existing compatibility handler, outside the three S2 assistance operations. | Existing compatibility handler when Pilot Assistance is enabled; not an S2 target. |

For AT-08/AT-10, use the combined profile with the default StoryRun demo flag off; the durable classroom profile remains unchanged and has no Parent StoryRun routes. The intended durable Parent identity boundary is `get_parent_principal` plus `ParentRoleReader` (`parent_runtime.py:46-83,120-131`; `parent_profiles.py:73-90`; `application/ports/parent_roles.py:14-15`). The test uses a synthetic test principal and deterministic role store, then a distinct non-owner principal for the denial case. This is not production-adapter evidence. The current StoryRun router instead uses `get_verified_adult` and `_require_parent` with a direct `AdultIdentityModel` query (`parent_story_runs.py:40,69-78`). S2 must resolve that boundary before approval; it must not relabel this direct query as the ParentRoleReader path. D-190 keeps production `Be1ParentRoleAdapter` PostgreSQL coverage NOT COVERED until separate BE1 alignment. If Parent StoryRun route acceptance is later required in the classroom profile, stop for a new owner decision because that requires a composition change beyond D-198's listed operations.

`ParentApi.ts:89-110` currently forms mobile paths under `/api/parent/v1/story-runs`, while the existing dev server router is `/v1/story-runs`. This mismatch is an explicit BQ-7 and separate UI-task dependency. D-198 does not authorize a mobile edit, `/api/parent/v1/*` route, or route removal.

## 4. Acceptance criteria (future evidence only; NOT RUN)

### M2-AT-08 - Parent create concurrency, cancel, and durable status

- Use the combined profile with the default StoryRun demo flag off, and a real route stack, persistence and authentication boundary in a future separately approved gate. Exercise the existing create handler and its existing repository; do not substitute a StoryRun-lite target adapter. Use a test principal and role store for Parent role testing. A result on that test store does not cover the production BE1 adapter under D-190. The classroom profile does not mount Parent StoryRun routes under the current scope.
- Two concurrent create requests for the same synthetic Parent must result in one run and one create receipt. The loser is HTTP 409 with stable code `ACTIVE_RUN_EXISTS` (SRS §21.4 lines 1670-1671; current repository maps the active-owner unique conflict at `parent_story_repository.py:156-160`). The `ACTIVE_RUN_EXISTS` public error body fields are OPEN under BQ-8; do not assume run ID/state fields.
- Cancel of a non-completed run uses the current expected revision and an idempotency key and yields `DELETE_PENDING` with active-owner lock release in the same transaction, as Rev60 §21.2 line 1646 and §22.3 line 1770 specify. The exact response envelope and route details remain subject to BQ-2/BQ-7. Existing state/receipt columns must suffice; otherwise stop for an owner decision under D-198.
- A distinct non-owner test principal must not read the job or learn its existence. The exact HTTP status and error shape are OPEN under BQ-7. Owner job-status success must be durable and versioned; exact handler, state fields and route contract are OPEN under BQ-7. The current AI Jobs candidate is not mounted.
- If an approved acceptance requires process recovery, create a durable pending state, record and stop the original OS process, confirm it exited, then use a fresh OS process and composition against the same task database. A same-process recreation is not restart evidence. No such test or database access occurred here.
- The current create method writes a run, run-input row and Story command receipt (`backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:105-155`); it does not itself create an AI job or outbox row. Do not claim create dispatches a job. The job trigger and the relationship to `INPUT_PROCESSING` remain a BQ-1/BQ-7 integration question.

### M2-AT-09 - three assistance compatibility operations and receipt handling

Exercise the three existing compatibility operations through the composed route and dependency path, using synthetic-only identities/data. Do not substitute the Teacher-pending GET or call the service/repository directly instead of the routes. Do not monkeypatch `_build_child_binding` or replace the route dependency under test. No provider or Modal call is authorized.

| Operation | Source-defined public result to assert |
|---|---|
| First accepted submit | HTTP 202. `AssistanceReceipt` envelope with `contract_version="0.1-candidate"`, `correlation_id`; device `data` with `contract_name="AssistanceRequestDeviceView"`, matching `contract_version`, `assistance_id`, `request_revision`, `status="pending"`, `job_id` (which may be null), and `poll_after_ms` while pending. `meta.outcome="created"`, `replayed=false`, `resource_revision` equal to the request revision, `projection="device"`. The response has ETag, `Cache-Control: no-store`, and `Vary: Authorization`; a replay also has `Idempotency-Replayed: true`. Sources: `assistance_requests.py:62-96,143-159`; `assistance.py:1310-1320`; `contracts/schemas/assistance_requests.py:154-176`. |
| Status after an accepted authoritative receipt | HTTP 200 fields `assistance_id`, `request_revision`, `status`, `processing_state`, `poll_after_ms`. For a still-pending request with a SUCCEEDED/ACCEPTED job, result reference, and matching authoritative completion receipt, `processing_state="submitted_to_teacher"`, `status="pending"`, and `poll_after_ms=2000`. Without the authoritative receipt, status must not claim `submitted_to_teacher`; in the SUCCEEDED-but-unaccepted/orphan case the source maps processing state to `unknown`. Sources: `pilot_assistance.py:95-103,382-440,458-505`. |
| Accepted cancel | HTTP 200 receipt envelope; for the first accepted cancel, `meta.outcome="cancelled"`, `replayed=false`, `projection="device"`, and the device data reports `status="cancelled"` with `poll_after_ms=null`. Resource revision is the resulting request revision. Headers include ETag, `Cache-Control: no-store`, and `Vary: Authorization`. Sources: `assistance_requests.py:98-117,143-159`; `assistance.py:1310-1320`; schema `assistance_requests.py:154-176`. |

The success receipt asserts accepted receipt handling only; HTTP 202 on submit is not proof that a provider completed. Timeout remains non-terminal and does not report success. A missing result reference or authoritative receipt cannot be accepted as success under D-171. Any target-contract changes beyond the current compatibility source are OPEN under BQ-7.

### M2-AT-10 - trusted stored-age eligibility

Use the existing trusted profile lookup path, not a client age field. New ages 36 and 120 are eligible; ages 121 and 155 are refused. A 36/120 create success is HTTP 201 with `{request_id, story_run}`. Source-defined response values include `story_run.run_state="INPUT_PROCESSING"`, the profile and profile-revision refs, and `story_run.context_snapshot.age_months` equal to the trusted stored value; the route response also carries `context_confirmed=false` on this existing create path. The corresponding Story-side writes are one `story.runs` row with that `child_age_months`, state `INPUT_PROCESSING`, revision/version 1 and current input revision 1; one `story.run_inputs` row; and one `CREATE_RUN` command receipt. The current create method does not create an AI job or outbox row. Sources: `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:88-113,116-197`; response schema `backend/src/sketch2life/contracts/schemas/parent_story_runs.py:104-138`; service `backend/src/sketch2life/application/services/parent_story_runs.py:52-66,193-207`; repository `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:91-155`.

For trusted lookup values 121 and 155, expect HTTP 422 and stable code `INVALID_REQUEST`; the serialized envelope wrapper/message/correlation fields not determined by this route/service contract are OPEN under BQ-7. The trusted service check runs before `repository.create_run`, so there must be no Story run, run-input or create-receipt write for the refusal. Use a test-only typed profile-lookup fixture for those legacy values; do not insert an out-of-range age into Parent tables, bypass the constraint, or read a BE1 row. Existing code: `backend/src/sketch2life/application/services/parent_story_runs.py:55-66,193-207`; `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:105-155`.

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

`20261112_parent_story_context` declares `revision="20261112_parent_story_context"`, `down_revision="20261104_story_revisions"`, and no `depends_on` (`:10-13`). Its `upgrade()` explicitly fails unless `story.runs` is empty (`:30-47`). It changes the run-state check to allow `INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`, `SCRIPT_REVIEW`, `VIDEO_ADMISSION_PENDING`, `DELETE_PENDING`, `FAILED`, and `COMPLETED` (`:57-65`). It adds `current_input_revision` and the source-profile, typed-idea, context-revision, context-snapshot/hash, lesson-pin-snapshot/hash, and context-confirmation columns on Story inputs (`:48-50,116-159`). These columns are already present in the dev migration source; under D-196 and D-198 S2 adds no Story DDL and does not extend this migration. If cancel or job status cannot use existing columns/states, stop for an owner decision.

**Task database: NOT VERIFIED.** No database connection or command was used. The task database's row counts, whether `story.runs` is empty, its stamped Alembic revision(s), migration applicability, and rollback behavior are all NOT VERIFIED. The empty-run condition above describes the migration source only; it does not establish that the condition holds in any database. No migration, inventory, or Gate A/B action is authorized here.

## 6. Rev67 conditional markers

Rev60 remains canonical. The crosswalk's document-control rows apply as follows; no Rev67-only input or route behavior is promoted by this draft.

| Rev67 row | Marker | S2/S3 effect recorded by the crosswalk |
|---|---|---|
| Rev61 | CONDITIONAL | Legacy-age lifecycle clarification; the new-run 121/155 refusal is compatible, but grandfathered completion/read/delete behavior is not accepted by AT-10. |
| Rev62 | CONDITIONAL | Photo-first prerequisite and create-input sequence would require create-flow reconciliation if adopted. |
| Rev63 | CONDITIONAL | Catalog-first activity candidate and no-match behavior remain conditional; no activity-selection implementation is added here. |
| Rev64 | NOT AFFECTED | Diagram readiness does not change routes, request contracts or runtime evidence. |
| Rev65 | CONDITIONAL | Lesson-version access recheck matters only if lesson pin enters scope; D-196 defers it. |
| Rev66 | CONDITIONAL | Parent create sequence and required activity selection would change if adopted; API V2/persistence alignment remains open. |
| Rev67 | CONDITIONAL | Required main activity and recovery requirements remain conditional; no new route, pin, snapshot or activity contract is adopted. |

The target operation set and cancel/job-status semantics remain the Rev60/D-171 basis. Rev67 may be adopted only by a separate owner task followed by contract reconciliation. The crosswalk states S3 Draft 5 is unchanged and waits for an accepted S2; Round 4 is historical review evidence, not an approval of Draft 11.

## 7. Open dependencies, risk context and owner fields

### BE/AI dependencies

- **BQ-1 INPUT_PROCESSING:** the legal state/job transitions, trigger after the current create/context path, and sufficiency of active/current for resume remain open. In particular, current `create_run` creates a Story run, run input and receipt but no AI job/outbox. Do not infer a dispatch point or claim job creation from `INPUT_PROCESSING` alone.
- **BQ-2 Parent cancel/abandon:** exact verified route, method, request/response, authorization, idempotency and state transition remain open. Rev60's candidate path/semantics do not close this BE/AI question.
- **BQ-7 S2 route set and job-status access:** the BE lane must provide one route table for Parent create/cancel/job-status and the three assistance compatibility operations, with method, path, auth, idempotency, success/error bodies and persistence. Resolve the owner-only job-status handler and non-owner denial; the AI Jobs candidate is unmounted. Resolve the mobile/server route-prefix mismatch in the separate UI lane.
- **BQ-8 ACTIVE_RUN_EXISTS body:** the error body fields needed for continue/cancel recovery, including whether it carries run ID/state, remain open. Do not invent those fields.

These are explicit dependencies, not implicit approvals. Until BQ-1/BQ-2/BQ-7/BQ-8 are answered and reconciled, the dependent route contract and future acceptance assertions remain unapproved.

### Owner and phase boundaries

- D-190 production BE1 role-adapter coverage remains NOT COVERED; production acceptance on that adapter waits for separate BE1 alignment. AT-08's deterministic test role store demonstrates the ParentRoleReader boundary only.
- S1b remains DEFERRED; Q-04/Q-13 unanswered; no sharing; OI-05 to OI-08 OPEN/deferred; synthetic-only; no real-child-data or provider use; `OWNER_MODAL_CALL_APPROVED=NO`.
- Exact S2 Task Approval, exact allowlist, command ceiling and owner-run gate approvals remain absent and separate. Draft 10's historical proposed ceilings are not carried forward as a Draft 11 authorization.
- The M2 foundation plan Draft 11 predates D-194 through D-198 and is read-only context. S3 Draft 5 likewise remains unchanged and cannot start until accepted S2 closure and a separate S3 approval.

### Owner-supplied CI context (not independently re-verified)

The owner reports GitHub Actions run `43059473029` on `dev` at commit `1f5bb0b5`, dated 2026-11-11, plus PR 25 runs `43380946045` and `43401368611`. Four jobs were red: Repository policy checks (Python 3.12.14 absent from runner cache); Backend unit and contract tests (`uv.lock` needs an update while `--locked` was supplied); Teacher UI checks (two failures in `src/__tests__/app.test.tsx`); Admin UI checks (two failures in the same path). Child UI checks pass. These run results were supplied as context only and were not independently re-verified; no network was used.

## 8. Stop conditions and NOT RUN

Before any future approval, stop if the required role/auth boundary or route owner remains unresolved; an existing column/state is insufficient for cancel or job status; accepted evidence cannot establish the Gate A Story-chain target; the migration graph or approved target changes; a route/schema or permission choice needs an owner decision; an AT-10 fixture would bypass the lookup boundary or write a legacy age to Parent tables; a write cannot be marked exactly; the shared app/composition is still changing; a pin differs; or an acceptance needs database, provider, Modal or network work outside its separate approval.

NOT RUN / NOT VERIFIED in this record-and-draft task: backend execution, database access, migration or inventory, Docker, Modal, pytest, mypy, install, validators, OpenAPI generation, runtime route exposure, authentication/authorization execution, concurrency, cancel, receipt handling, age-boundary tests, process restart/recovery, task-database contents, Gate A, Gate B, and CI re-verification. No source code changed. No S2/S3 approval, gate or allowlist was created.

## 9. Input pins

Every cited repository input below was rehashed while preparing this draft. Root-checkout inputs remain read-only and are not copied into this worktree. Migration pins are listed with the static graph above.

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
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 192584 | `2BF5C0A08BE168E7F02F41A115109EC07A1532C3E167B2D5688659AEA876EBC9` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 404042 | `0D4E434C2D932C5FBF09D7BAE75DBA46CD29835AA41884FBFEBFC2A36C5DA73A` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_CLOSURE_RECORD_20261112.md` | 3503 | `0C1801119F17D98FBD4ADA2C7D884530DFAB4A068AF88DE7C74525ADA61F40E4` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` | 5547 | `6BB4A6EA6F477B44486A4E518766099CC2DA9A97246DE7ADAD08E4C00C891485` |
| S2 worktree | `features/FEAT-063-system-architecture-rearchitecture/artifacts/PARENT_API_CONTRACT_REV67_20261110.md` | 9573 | `0BB99DAFDC6592118B367EBEB60BC0D15FBE80DCD697499EB68EC135C302C47D` |
| root checkout | `docs/context/SRS_AUTHORITY.md` | 4054 | `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` |
| root checkout | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 553948 | `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` |
| mobile worktree | `.worktrees/mobile/tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md` | 634291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
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
