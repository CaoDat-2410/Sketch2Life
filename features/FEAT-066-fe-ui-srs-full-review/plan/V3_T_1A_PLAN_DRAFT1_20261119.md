# V3 T-1a plan, Draft 1: video admission saga, `video-generations`, DDL-B1 video tables

Date 2026-11-19. Goal v3b, T-1a (WP-1, P-05 part, AUD-P#20). Facts read at HEAD `0ee27069`. T-2b..T-2d land first and are not visible: "re-verify at start" items are implementer preconditions. Sources: BE API plan Draft 5 (WP-1, DDL-B1 §1.5, OD-01, OD-03, TD-22, X-13, R3, R5), Billing Draft 9 §7.2 (`VideoQuotaPortV1`).
Owner scope rule (teammate: Platform Admin, Billing/capacity; owner: quota): NO capacity, subscription, quota, billing or payment code; no production adapter for `VIDEO_QUOTA_EXCEEDED`, `SUBSCRIPTION_RESTRICTED`, `AI_COST_LIMIT_REACHED`; no `/v1/video-quota`. Only port shapes and one local/test adapter pair (OD-03).

## 1. Verified facts

- F1 `story.runs` (Core tables in `infrastructure/story_run_lite/tables.py`) has `revision`, `version`, `job_state`, unique partial `active_owner_parent_account_id`; it lacks `adult_wait_started_at`, `last_meaningful_activity_at`, `finished_at` and a video pointer (REG l.373).
- F2 `ck_story_run_state` (replaced by `20261119_frc08_lifecycle_scope`, branch `frc08_lifecycle`) has 12 values: no `VIDEO_QUEUED`, `VIDEO_GENERATING`, `VIDEO_SAFETY_VALIDATING`, `VIDEO_READY`, `SAFETY_BLOCKED`, `ABANDONED`. `ck_story_receipt_operation` has 8 operations. The public set (20 values) is `PUBLIC_RUN_STATES` in `application/ports/story_run_lifecycle.py`.
- F3 `script-confirmation` leaves the run in `SCRIPT_REVIEW`, story revision `CONFIRMED`, one review row (`uq_story_revision_review_once`). Runs start in `INPUT_PROCESSING`; a failed drawing job already goes `FAILED` and frees the lock.
- F4 Story commands use body `expected_revision` and 409 `STALE_REVISION` with `current_version` (cancel). The family has its own handler in `interfaces/http/app.py` (safe-message map) and is not a CONV-1 prefix.
- F5 `ai_jobs.job.organization_id` is NOT NULL; FR-C-08 states "no Parent product run creates an AI job (S4)" (a Parent notice matches no job). T0.4 left `ParentJobScopePort` (HEAD `NoParentJobs`) as the seam.
- F6 AI Policy `ResourceAccountingService.reserve` is organization-scoped; no runtime adapter for a Parent scope. Billing does not exist.
- F7 Purge closure lives in `story_lifecycle_store._child_ids/_delete_children`. Settings guard precedent: T-2z (`enforce_deployment_provider_policy`). Pins: `test_synthetic_eligibility.py:454-470` (graph, heads 14/10), `test_m2_s2_g1_parent_story_postgres.py:96`.

## 2. Decisions (SRS-cited)

| ID | Decision | Basis |
|---|---|---|
| D1 | Route `POST /v1/story-runs/{id}/video-generations`: body `expected_revision` (run revision), `story_sha256`, optional `quality_reason_code`; `Idempotency-Key` required (missing 400 `INVALID_REQUEST`, other payload 400 `INVALID_IDEMPOTENCY_KEY`). 202 `ParentVideoGenerationAcceptedV1` (`request_id`, `video_generation{generation_id, state, generation_no, kind, job_id, run_state, run_revision}`). Same key replays the stored outcome (a rejected intent replays its error, a pending one its current state). | l.1670, l.1697-1699, C-D5/D6 |
| D2 | Saga, not one SQL transaction. Tx1: lock run, checks, insert intent `ADMISSION_PENDING`, run to `VIDEO_ADMISSION_PENDING` (lock kept, no adult-wait). Then, holding the run row lock (in-process calls, bounded by port timeouts): compute reservation, then quota admission, same key. Tx2: both clear gives `ACCEPTED` (number, `accepted_at`, both refs, scenes copied from the pinned revision, `job_ref`) and run `VIDEO_QUEUED`; a rejection gives `ADMISSION_REJECTED`, releases the reservation, run back to `SCRIPT_REVIEW` with a new adult-wait start. A rejected intent makes no usage, job, dispatch or cap. | l.1670, l.394-395, l.597, l.503, BR-38 l.282 |
| D3 | `UNAVAILABLE` from a port: intent stays `ADMISSION_PENDING`, 202 with that state. `reconcile_pending_admissions(now)` re-calls both ports with the same key (idempotent, Draft 9 §7.2) and decides; no timer rejects an intent (a unit may be consumed). No scheduler (periodic runner slice, D-066-73 PD-9a). | l.597, l.394 |
| D4 | Cap: accepted rows count, at most three per run (initial plus two `QUALITY_REGEN`); rejected rows do not. Next request: 409 `VIDEO_REGENERATION_LIMIT_REACHED`. `quality_reason_code` required once an accepted row exists (400 `INVALID_REQUEST` with `field_errors`); closed set `QUALITY_LOW`, `NOT_MATCHING_STORY`, `CONTENT_CONCERN`, `OTHER` (candidate: the SRS names the field only). | l.573, l.518, l.1670 |
| D5 | Script gate: latest story revision `CONFIRMED`, hash equal to the body, its review not consumed by a non-rejected generation (`story_review_id`, unique unless rejected). Run revision or hash mismatch: 409 `STALE_REVISION` + `current_version`; unconfirmed or consumed: 409 `INVALID_STATE_TRANSITION`; defensive 422 `SUBJECT_NOT_CONFIRMED`/`PROFILE_CONTEXT_NOT_CONFIRMED`. | l.1669-1670, l.395, l.871 |
| D6 | Ports (`application/ports/story_video.py`, Story-owned). `VideoComputeReservationPort`: `reserve(scope, request_ref, key, fingerprint)` returns `RESERVED(ref)`, `COST_LIMIT_REACHED` or `UNAVAILABLE`; `release(...)`; `settle(..., outcome)` (called by D9 at a terminal state). `VideoQuotaAdmissionPort.admit_video_request(scope, request_ref, key, fingerprint, contract_version)` returns `ACCEPTED(usage_ref, grant_ref)`, `QUOTA_EXCEEDED`, `SUBSCRIPTION_RESTRICTED`, `IDEMPOTENCY_MISMATCH` or `UNAVAILABLE` (Draft 9 §7.2; same key returns the same usage). `scope` is `PARENT_ACCOUNT` or `ORGANIZATION` (Teacher seam, unused). `request_ref` = generation id. No `read_balance`. | l.596-597, OD-03 |
| D7 | One local/test adapter pair (`infrastructure/story_video/local_adapters.py`): accept-all, in-memory idempotent receipts, a test-only per-scope outcome script; no counters, units, balance, grant or price logic. Refused outside `{local,test}` by its constructor and by `Settings` (flag `story_video_adapters`: `unconfigured` default, `local_test`); production starts `unconfigured` and the route answers 503 `PROVIDER_UNAVAILABLE` before writing an intent. The same flag builds the fixture runner. | OD-03, R3, T-2z |
| D8 | Job record without `ai_jobs` (default, Q2): the generation row is the durable job (`job_ref` unique). `GET /v1/jobs/{job_id}` reads it through a `ParentJobScopePort` adapter projecting the row to a read-only `AiJob`, plus a registry entry for `VIDEO_GENERATION`; keeps S4 true and needs no `ai_jobs` DDL. Scenes carry states only, no attempt counter. | l.779, l.1675, F5, REG l.381 (deviation) |
| D9 | `StoryVideoProgressService.apply(generation_id, event)` moves generation and run together by CAS (`QUEUED`/`VIDEO_QUEUED`, `GENERATING`/`VIDEO_GENERATING`, validating/`VIDEO_SAFETY_VALIDATING`, `READY`/`VIDEO_READY` with output asset and adult-wait start, `SAFETY_BLOCKED` with adult-wait, `FAILED`/`FAILED` with lock released and no refund) and calls `settle`. A result for a run no longer in the expected state is recorded stale. The fixture runner (OD-13) writes a tiny synthetic MP4 stand-in via `ObjectStoragePort` and a `PARENT_ACCOUNT` `core_asset_metadata` row (`source_refs` = run id, so purge sees it), is scripted and stepped by tests, never scheduled. Cut line: if too large, the runner moves to T-1b as a test helper. | l.394-395, l.386, l.575 |

## 3. Route, authorization, keys

| Method, path | Actor | Success | Errors |
|---|---|---|---|
| `POST /v1/story-runs/{id}/video-generations` | Parent owner | 202 | 400 `INVALID_REQUEST`/`INVALID_IDEMPOTENCY_KEY`; 404 `RESOURCE_NOT_FOUND`; 409 `STALE_REVISION`, `INVALID_STATE_TRANSITION`, `VIDEO_REGENERATION_LIMIT_REACHED`, `VIDEO_QUOTA_EXCEEDED`, `SUBSCRIPTION_RESTRICTED`; 422 as D5; 503 `AI_COST_LIMIT_REACHED`, `PROVIDER_UNAVAILABLE` |

Authorization: `_require_parent` plus the owner-scoped locked lookup (scope ref = hash of issuer and subject), as the sibling routes; the wrong-role answer is whatever T0.9 leaves (403 now, 404 after OD-18b). Foreign or missing run: 404. No body field names an owner or scope. Teacher-only codes (`SAMPLE_VIDEO_ALREADY_EXISTS`, `LESSON_PLAN_NOT_APPROVED`) wait for T-4a1/T-5a; the service takes a typed `scope`, so that path adds no signature change.
Keys: body `expected_revision`, no ETag on commands (C-D7). Receipt operation `CREATE_VIDEO_GENERATION`, scope `STORY_RUN`, fingerprint over run, revision, hash, reason. `app.py`: safe messages for the new codes and `current_version` on these routes.

## 4. DDL-B1 part 2 (named approval first, R5/OD-01)

One migration `20261120_vb_0002_video_generations` (id proposed). Chain: `down_revision` = head of branch `frc08_lifecycle` at implementation (expected T-2c's DDL-B1 part 1; else `20261119_frc08_lifecycle_scope`). It must follow frc08 because it replaces the two CHECKs frc08 created; a parallel branch off `20261112_parent_story_context` would race them. Heads stay 14/10, revisions +1 (update the pin). Deploy with `upgrade heads`.

1. `story.video_generations` (REG l.380): PK; run FK CASCADE; composite FK `(story_run_id, story_revision_id)` to `story_revisions(run_id, story_revision_id)`; `story_review_id` FK; `generation_no` (NULL until accepted, 1..3, unique per run); `generation_kind`; 12-value `state`; key hash and fingerprint with unique `(story_run_id, key_hash)`; `target_script_hash`; `quality_reason_code`, `rejection_reason_code` (T-1b); `compute_reservation_ref`, `billing_quota_usage_ref`; `job_ref` unique; output asset ref and version; profile, model, config; three validation states (`PENDING|PASSED|FAILED`), safety policy version and finding codes; `admission_started_at`, `accepted_at`, `rejected_at`, `started_at`, `completed_at`; `safe_failure_code`; `generation_revision`; timestamps; unique `(video_generation_id, story_revision_id)`. CHECKs on state shape (accepted rows carry number, `accepted_at`, both refs, `job_ref`; rejected rows no refs; `READY` carries the asset and three `PASSED`). Partial uniques per run: one pending, one in flight, one `READY`; `story_review_id` where not rejected.
2. `story.video_generation_scenes` (REG l.381): composite FKs to the generation and to `story_scenes(story_revision_id, scene_id)` (adds that trivially true unique); unique `(video_generation_id, story_scene_id)`; state `QUEUED|GENERATING|READY|FAILED`, clip refs, `source_job_ref` (NULL under D8), codes, timestamps.
3. `story.runs`: `current_video_generation_id` (FK `ON DELETE SET NULL`; run match enforced in code and tested), `adult_wait_started_at`, `last_meaningful_activity_at`, `finished_at`; backfill both timers from `updated_at` for wait-state runs (T-1d1 plan).
4. Replace `ck_story_run_state` with the 20-value set and `ck_story_receipt_operation` with the current list plus `CREATE_VIDEO_GENERATION`, `MARK_VIDEO_UNSUITABLE`, `COMPLETE_RUN` (re-read both first; T-2c/T-2d may add values).
5. Only if Q4 rules for option A: relax `uq_story_revision_review_once` to unique `(story_revision_id, confirmation_epoch)`.

Downgrade refuses while video rows or new-state runs exist; round trip verified on a fresh database.

## 5. State machine (`domain/story_video/model.py`, pure)

Generation: `ADMISSION_PENDING` to `ACCEPTED|ADMISSION_REJECTED`; `ACCEPTED` to `QUEUED` to `GENERATING` to `TECHNICAL_VALIDATING` to `SAFETY_VALIDATING` to `READY|SAFETY_BLOCKED`; in flight to `FAILED`; `READY` to `REJECTED_BY_ADULT` (T-1b) or `SUPERSEDED`. Run: `SCRIPT_REVIEW` to `VIDEO_ADMISSION_PENDING` to `VIDEO_QUEUED` (or back to `SCRIPT_REVIEW`), then D9. One constant maps generation state to run state and drives service and tests.

## 6. Tests

Unit: every legal and illegal edge; service with fake ports (both clear, quota rejected releases, cost rejected before quota, unavailable pending, reconciler outcomes, replay after each outcome, cap, reason rule, hash/revision mismatch, consumed review); adapters refused in staging/production; settings guard; job projection (mapping, scope, no result refs unless `READY`). Contract: catalog entry, error bodies, no storage key or provider text, foreign owner answer. PostgreSQL (fresh database, `alembic upgrade heads`): two concurrent requests with one key give one intent; a rejected intent leaves no usage ref, job or cap use; fourth accepted request refused; composite FKs and partial uniques reject bad rows; cancel in each in-flight state still purges video rows and assets; migration up, down, up.

## 7. File allowlist

New: `backend/alembic/versions/20261120_vb_0002_video_generations.py`; `domain/story_video/{__init__,model}.py`; `application/ports/story_video.py`; `application/services/story_run_video.py`; `infrastructure/story_video/{__init__,repository,local_adapters,fixture_runner,job_projection}.py`; `contracts/schemas/story_run_video.py`; `interfaces/http/routers/story_run_video.py`; tests `unit/test_story_video_{domain,admission_service,local_adapters,migration}.py`, `contract/test_story_run_video_routes.py`, `integration/story_video/test_video_generations_postgres.py`.
Edit: `infrastructure/story_run_lite/tables.py`, `infrastructure/persistence/story_lifecycle_store.py`, `infrastructure/config/settings.py`, `interfaces/http/{app,router_composition,openapi_contract}.py`. Existing tests affected: `unit/test_synthetic_eligibility.py`, `integration/test_m2_s2_g1_parent_story_postgres.py`, `contract/test_app_composition.py`, `contract/test_openapi_contract_catalog.py`, `unit/test_story_lifecycle_store.py`, `integration/test_frc08_lifecycle_postgres.py`.

## 8. Review rule

**2 reviews** (new migration/DDL; money-adjacent admission seam). Plan review before the migration is approved.

## 9. Risks

R1 Row lock held across two in-process calls (bounded; a timeout leaves the intent pending). R2 Cancel or purge after `ACCEPTED`: the quota unit stays consumed (no refund) and the compute reservation is not settled by purge (AI Policy side, debt). R3 D8 deviates from REG l.381; the first real worker migrates it. R4 No Parent activity gate before the story (R-5, X-05). R5 Backfilled timers may make old synthetic runs eligible at the first sweep.

## 10. BLOCKED_OPEN and ownership

- **Q1 (before the migration):** may DDL-B1 cover the extra Story columns (section 4 items 1 and 3: REG has no `rejection_reason_code`, `quality_reason_code`, `story_review_id`, `job_ref`)? Default yes; if no, T-1d1 falls back to `updated_at` and those columns go.
- **Q2:** is a Story-owned job record (D8) acceptable until the first real worker, instead of Parent-owned `ai_jobs` rows (owner-scope DDL on `ai_jobs.job` and a change to S4)? Default D8.
- **Q3:** who builds the production compute-reservation adapter for a Parent scope (AI Policy budget)? Parked OWNED_BY_TEAMMATE (Platform Admin lane) unless the owner says otherwise. Quota admission and balance reads: OWNED_BY_OWNER (Billing B-3). Neither is built here.
- **Q4 (BLOCKED_OPEN, regeneration path only):** after `video-unsuitable` the SRS requires the adult to confirm the script again (l.395, FR-P-09), but `script-confirmation` accepts a revision once. May a confirmed revision be confirmed again (option A, DDL item 5, a change to an approved M2 route, carried by T-1b), or must the adult rewrite first (option B, which traps an adult who used all three rewrites)? T-1a works with both.
