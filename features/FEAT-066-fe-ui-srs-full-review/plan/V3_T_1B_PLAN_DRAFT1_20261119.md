# V3 T-1b plan, Draft 1: `video-unsuitable` and `complete`

Date 2026-11-19. Goal v3b, T-1b (WP-1, AUD-P#22 and #23). Facts read at HEAD `0ee27069`; T-1a (tables, state machine, progress service, ports) lands first and this plan builds on its names. Sources: BE API plan Draft 5 WP-1, UC-16. No DDL, no capacity, quota, billing or payment code.

## 1. Verified facts

- F1 HEAD has neither route. `run_summary_capabilities` already treats `VIDEO_READY` as cancel-eligible and `COMPLETED` as delete-eligible (`CANCEL_ELIGIBLE_STATES`, `DELETE_ELIGIBLE_STATES`), so `DELETE` works for a completed run once T-1b can produce one (plan note S-10 #26).
- F2 The one-run lock is `story.runs.active_owner_parent_account_id` (unique partial index); cancel and failure set it to NULL. `COMPLETED` is in `ck_story_run_state` at HEAD; T-1a widens the set and adds the receipt operations `MARK_VIDEO_UNSUITABLE` and `COMPLETE_RUN`.
- F3 `story_revision_reviews` allows one review per revision (`uq_story_revision_review_once`); `confirm_story_revision` refuses a revision that is not `DRAFT`.
- F4 The family error handler maps `STALE_REVISION` and adds `current_version` only on the cancel path (T-1a extends it to the video routes).

## 2. Decisions (SRS-cited)

| ID | Decision | Basis |
|---|---|---|
| D1 | `POST /v1/story-runs/{id}/video-unsuitable`: body `expected_revision`, `generation_id` (the current generation), `reason_code`; `Idempotency-Key` required. Check order: role, key syntax, owner-scoped locked lookup (404), replay (same key and fingerprint returns the stored 200; another payload 400 `INVALID_IDEMPOTENCY_KEY`), purge states (as the sibling routes), run revision (409 `STALE_REVISION` + `current_version`), run state must be `VIDEO_READY` (409 `INVALID_STATE_TRANSITION`), `generation_id` must equal `current_video_generation_id` and the generation be `READY` (409 `STALE_REVISION`), then the cap. | l.1671, l.1697-1699 |
| D2 | Cap: if three accepted generations already exist (T-1a D4), answer 409 `VIDEO_REGENERATION_LIMIT_REACHED` and change nothing (the video stays visible; the adult can still complete or cancel). Otherwise: generation `READY` to `REJECTED_BY_ADULT` (`rejection_reason_code` stored, output kept internally until the run is deleted), run to `SCRIPT_REVIEW`, `revision` and `version` +1, `adult_wait_started_at` and `last_meaningful_activity_at` = now, owner lock kept. 200 with the existing run envelope (`ParentStoryRunEnvelopeV1`; T-1c adds the video fields to it). | l.1671, l.518 (FR-P-09), l.573, l.395 |
| D3 | Hide timing: the SRS says the rejected video is hidden when the regeneration is accepted (FR-P-09 l.518, l.382, FR-AI-09 l.575) and also when it is marked (UC-16 l.1580, l.1581: it stays hidden even if no regeneration follows; l.395: `REJECTED_BY_ADULT` "immediately"). Decision: hide at the mark. No behaviour differs for a playing client because a token needs `VIDEO_READY` (l.1676), which the run leaves at the mark. Recorded as a resolved SRS inconsistency. | l.395, l.1580-1581, l.1676 |
| D4 | `reason_code` is the closed set shared with T-1a (`QUALITY_LOW`, `NOT_MATCHING_STORY`, `CONTENT_CONCERN`, `OTHER`; candidate, the SRS says "safe reason code"). The text is never free. No quality feedback reaches an operator (UC-16 l.1582). | l.1671, l.1582 |
| D5 | `POST /v1/story-runs/{id}/complete`: body `expected_revision`; `Idempotency-Key` required; only `VIDEO_READY`. Effect: run `COMPLETED`, `active_owner_parent_account_id` NULL (lock released in the same transaction), `finished_at` and `last_meaningful_activity_at` = now, `adult_wait_started_at` cleared, `revision` and `version` +1; the generation stays `READY` (internal; no review row, "not a video approval"); content is kept until the user deletes the run. 200 with the run envelope. After `COMPLETED` no playback token is issued (the token route needs `VIDEO_READY`, l.1676); the SRS gives no replay after completion, recorded as a note. | l.1672, l.517, l.503, l.1676 |
| D6 | Both commands write a receipt (`MARK_VIDEO_UNSUITABLE`, `COMPLETE_RUN`, scope `STORY_RUN`) in the run transaction with the same locking and replay code as `confirm_story_revision` (advisory lock on the key, receipt row, `FOR UPDATE` on the run). No outbox event and no audit row (the sibling confirm routes have none; lifecycle events stay with cancel and delete). | pattern of `parent_story_repository.py` |
| D7 | Teacher actor and `SAMPLE_VIDEO_ALREADY_EXISTS` handling are out (T-4a1, T-5a). The service takes the typed scope of T-1a, so that path adds no signature change. | WP-4a, WP-5 |

## 3. Routes and contract

| Method, path | Body | Success | Errors |
|---|---|---|---|
| `POST /v1/story-runs/{id}/video-unsuitable` | `expected_revision`, `generation_id`, `reason_code` | 200 run envelope, state `SCRIPT_REVIEW` | 400 `INVALID_REQUEST`, `INVALID_IDEMPOTENCY_KEY`; 404; 409 `STALE_REVISION`, `INVALID_STATE_TRANSITION`, `VIDEO_REGENERATION_LIMIT_REACHED` |
| `POST /v1/story-runs/{id}/complete` | `expected_revision` | 200 run envelope, state `COMPLETED` | 400 as above; 404; 409 `STALE_REVISION`, `INVALID_STATE_TRANSITION` |

Authorization: `_require_parent` and the owner-scoped locked lookup, identical to T-1a; foreign or missing run is 404; the wrong-role answer is whatever T0.9 leaves. No ETag (C-D7, story family). The response model and the 409 body already carry `current_version`.

## 4. State machine

Run: `VIDEO_READY` to `SCRIPT_REVIEW` (unsuitable) or `COMPLETED` (complete). Generation: `READY` to `REJECTED_BY_ADULT`. Both are legal pairs in the T-1a constant; the tests assert the full legal and illegal edge list for these two commands (every other run state refuses both).

## 5. Tests

Unit: service with a fake store for each refusal and the replay rules; reason code set. Contract: both routes in the catalog; error bodies; foreign owner 404; no provider text. PostgreSQL (fresh database, `alembic upgrade heads`): from a `READY` generation (T-1a fixture runner) `video-unsuitable` returns the run to `SCRIPT_REVIEW` and a later `video-generations` is admitted as `QUALITY_REGEN`; with three accepted generations the next unsuitable answers 409 and leaves the video visible; stale revision and a non-current generation id answer 409; `complete` releases the lock (a new run can then be created) and a second request with the same key replays; two concurrent requests with one key give one transition; `DELETE` of the completed run works; cancel from `SCRIPT_REVIEW` after an unsuitable still purges the rejected generation and its asset.

## 6. File allowlist

Edit: `application/services/story_run_video.py`, `infrastructure/story_video/repository.py`, `contracts/schemas/story_run_video.py`, `interfaces/http/routers/story_run_video.py`, `interfaces/http/openapi_contract.py`; only if Q1 rules for option A: `infrastructure/persistence/parent_story_repository.py` (`confirm_story_revision`) and its tests. New tests: `unit/test_story_video_unsuitable_complete.py`, `contract/test_story_run_video_commands_routes.py`, `integration/story_video/test_video_commands_postgres.py`. Existing tests affected: `contract/test_openapi_contract_catalog.py`; under option A also `integration/test_m2_s2_g1_parent_story_postgres.py` and `contract/test_parent_story_run_request_contract.py` (the `PARENT_STORY_REVISION_STALE` assertions).

## 7. Review rule

**1 combined review** (no DDL, guards reused unchanged, new routes no client uses yet). If Q1 resolves to option A the task changes an approved M2 route that Android and web use and the rule becomes **2 reviews**.

## 8. Risks

R1 After `video-unsuitable` the adult cannot regenerate the same script unless Q1 is resolved (a rewrite is the only way back to a fresh confirmation); this is the main product risk of the task. R2 `SAFETY_BLOCKED` exits are not specified (Q2), so no route leaves it. R3 The hidden-at-mark choice (D3) is a reading of an inconsistent SRS and is recorded for the owner check.

## 9. BLOCKED_OPEN and ownership

- **Q1 (BLOCKED_OPEN, regeneration only; same question as T-1a Q4):** after `video-unsuitable` must the adult confirm the script again (l.395, FR-P-09), and may the same `CONFIRMED` revision be confirmed again (option A: new review row with an epoch, one approved M2 route changes, T-1a DDL item 5), or only a new rewrite revision (option B: no change, but an adult who used all three rewrites cannot regenerate)? Default if unanswered: B, with T-1b delivering the two routes and the doc note.
- **Q2:** what may the adult do from `SAFETY_BLOCKED` (back to `SCRIPT_REVIEW` as a new request, or only cancel and idle closeout)? The SRS lists it as an adult-wait state (l.394) but names no command. Default: cancel and idle closeout only (T-1d1); no new route.
- **Q3 (OPEN-WITH-DEFAULT):** the `reason_code` set; owner may replace it before Android adopts it.
- Quota and capacity effects of regeneration: none built here (OWNED_BY_OWNER); T-1a ports carry them.
