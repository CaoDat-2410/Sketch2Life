# V3 T-1c plan, Draft 1: `playback-token`, stream route, `StoryRunDetailV1` aggregate

Date 2026-11-19. Goal v3b, T-1c (WP-1, P-05, AUD-P#10 and #24; TD-07, TD-22). Facts read at HEAD `0ee27069`; builds on T-1a (tables, generation rows, job projection) and T-1b. No DDL, no capacity, quota, billing or payment code.

## 1. Verified facts

- F1 `GET /v1/story-runs/{id}` returns `ParentStoryRunEnvelopeV1{request_id, story_run: ParentStoryRunResponseV1}` or, from `DELETE_PENDING` on, the content-free lifecycle envelope (D-208). `ParentStoryRunResponseV1` has no `extra="forbid"`; it is built by `_response(record)` in `routers/parent_story_runs.py` from `ParentStoryRunRecord` (`application/ports/parent_story_runs.py`) filled by `SqlParentStoryRunRepository.get_run`. The family sets no `ETag` today.
- F2 `ObjectStoragePort` offers `get_object(key)` returning a readable body; it has no range read. Core asset rows (`core_asset_metadata`, Parent scope, `source_refs` = run id) are what T-2a and T-1a write.
- F3 No playback grant table exists and DDL-B1 names none. The BE2 pilot playback code (`application/video_playback.py`) is organization-scoped and unrelated.
- F4 T-1a leaves the generation row with output asset, three validation states, `job_ref`, scenes and a read-only job projection.

## 2. Decisions (SRS-cited)

| ID | Decision | Basis |
|---|---|---|
| D1 | `POST /v1/story-runs/{id}/playback-token`, no body, no idempotency key (a grant, no state change, no write; it does not reset the idle timer). Preconditions: Parent owner (current ownership re-read), run `VIDEO_READY`, current generation `READY` with technical, consistency and safety states `PASSED` and an output asset. Else 404 (not owner) or 409 `INVALID_STATE_TRANSITION`. 200 `{request_id, playback{token, expires_at, stream_path, media_type "video/mp4", asset_ref (opaque handle)}}`, `Cache-Control: no-store`. | l.1676, l.575, l.1691 |
| D2 | Token format (TD-07 candidate, deviation recorded): opaque signed token `ptk1.<payload>.<mac>` (HMAC-SHA256), payload = run id, generation id, asset handle digest, actor scope ref digest, expiry, nonce. TD-07 recommended "stored hashed"; that needs a grant table outside DDL-B1, so the stateless form is used and **every stream request re-checks** current ownership, run state, generation identity and visibility, which gives the same revocation effect. Lifetime 300 s (settings value, hard maximum 900 s; "short-lived" has no number in the SRS). Signing secret comes from settings: required in staging and production (startup refuses without it); local and test may use an ephemeral per-process key. The token is never logged, stored or put in an error body. | l.1691, l.1693, TD-07 |
| D3 | Stream route `GET /v1/story-runs/{id}/playback`; the token travels in header `X-Playback-Token` (not in the URL, so access logs, history and referrers never hold it, l.1693; a media player that cannot set headers is Q2). No Firebase bearer is required (players cannot always send one); the token is the grant. Order: parse and verify token (bad shape or MAC 401 `INVALID_TOKEN`; expired 401 `TOKEN_EXPIRED`), run id in path equals token run, owner-scoped lookup with the token's actor digest (404), run `VIDEO_READY`, current generation equals the token's and is `READY` and not hidden or superseded (404), asset resolves server side (404/503 `STORAGE_UNAVAILABLE`). The wrong-owner and revoked cases answer the uniform 404, not an auth hint. | l.1691, l.863-865, l.875 |
| D4 | Response: `Accept-Ranges: bytes`, `Content-Type: video/mp4`, `Content-Disposition: inline` with no file name, `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`; one `Range` gives 206 with `Content-Range`, malformed or multiple ranges 416; no `Content-Length` leak beyond the object size; no bucket, key, URL, list or download route anywhere (l.1692). Bytes stream in 64 KiB chunks from `ObjectStoragePort.get_object`, skipping to the range start (no range read in the port: debt for the real adapter), with a size ceiling (settings, default 100 MiB, over it 503). | l.1692, l.575, TD-07 |
| D5 | `StoryRunDetailV1` is realised by extending `ParentStoryRunResponseV1` in place with optional fields only (no rename, no removal; l.1635 allows additive fields; the Android and web DTO decoding of unknown fields is a precondition check, as for OD-18). New fields: `video` (null until a generation exists): `current_generation_id`, `generation_no`, `kind`, `state`, `job{job_id, state, stage, retryable, error_code}` (safe code set only), `scenes[{scene_index, state}]`, `playback{state AVAILABLE or HIDDEN or UNAVAILABLE, asset_ref, token_route}`, `requests_used`, `requests_remaining`, `admission_pending`, `history[{generation_id, generation_no, kind, state}]` (accepted rows); `quota{state "UNAVAILABLE", granted/used/available null}` (TD-22: never zero; the owner's quota reader later fills it without a contract break); `timeline[{event, at}]` derived from existing timestamps only. The playback "ref" is the readiness descriptor and the route name; a token exists only after the explicit POST (no mint on read). | l.780, l.805, l.1811, AC-41 l.1164, TD-22 |
| D6 | Composition rule (AC-41, l.1811): one Story-owned read in `infrastructure/story_video/repository.py` called by `get_run`; job data comes from the same projection `GET /v1/jobs/{id}` uses; no read of `ai_jobs`, Billing, Lesson or `core_asset_metadata` tables (asset readiness comes from the generation row), no fan-out, no new table. Excluded: prompts (`visual_prompt`), raw transcript, hidden story revisions, `safe_failure_code` values outside a public set, rejected-video content, foreign scope. | l.780, l.1164, l.875 |
| D7 | ETag (SRS l.1811 "ETag"): strong `"d1-<first 32 hex of sha256 of the canonical detail body without request_id>"`; `Cache-Control: private, no-cache`; `If-None-Match` match gives 304 **after** authorization. Content-hash rather than the run revision because generation and scene states change without a run revision bump. Applies to the detail (non-lifecycle) response only; commands keep body `expected_revision`. | l.1811, T0.4 pattern |
| D8 | Responses of T-1a and T-1b commands and `script-confirmation` use the same extended model through the shared `_response` builder, so a client sees one shape. Lifecycle envelope after `DELETE_PENDING` is unchanged. | D-208 (FEAT-063) |

## 3. Routes and contract

| Method, path | Actor | Success | Errors |
|---|---|---|---|
| `POST /v1/story-runs/{id}/playback-token` | Parent owner | 200 token | 404; 409 `INVALID_STATE_TRANSITION` |
| `GET /v1/story-runs/{id}/playback` | token holder (the owner at issue and now) | 200 or 206 bytes | 401 `INVALID_TOKEN`, `TOKEN_EXPIRED`; 404; 416; 503 `STORAGE_UNAVAILABLE` |
| `GET /v1/story-runs/{id}` | Parent owner | 200 extended envelope with `ETag`, or 304 | 404 |

Authorization (2 reviews): issuing re-reads current ownership; streaming re-reads it on every request, so cancel, delete, completion, hide-by-unsuitable, reassignment (T-4a1 later) and a foreign actor all end playback at the next request. The existing sibling answer (403 now, 404 after OD-18b) applies to the role guard of the token route. Teacher assignment recheck ("assignment version") is a seam only: the token carries a scope digest, and T-4a1 adds the assignment check.

## 4. DDL

None. The stateless token (D2) avoids a grant table. If Q1 answers "stored", a `story.playback_grants` table needs its own DDL approval and this task moves to a later slice.

## 5. Tests

Unit: token round trip, tamper, expiry (injected clock), wrong run, wrong actor, bad shape; the token string is absent from log output and error bodies; range parser (valid, open ended, suffix, malformed, multiple); composer privacy (no prompt, transcript or provider text; `quota` marker; counts after one, two and three requests); ETag stability (`request_id` excluded) and change on a state change. Contract: three routes in the catalog; response schema additive (old fields unchanged); 304 path; header set; no storage key, bucket or URL in any body or header. PostgreSQL (fresh database): Parent run to `READY` through the T-1a fixture runner, then token, `200`, `206`, `416`; after `video-unsuitable` a new token is 409 and the old token 404; after cancel the stream is 404; another Parent's token for the same run id is 404; tampered 401; expired 401; after `complete` a token is 409; detail ETag changes when the generation moves and `If-None-Match` returns 304; detail JSON never holds the object key.

## 6. File allowlist

New: `infrastructure/story_video/playback_tokens.py`, `application/services/story_run_playback.py`, tests `unit/test_story_playback_tokens.py`, `unit/test_story_run_detail_composition.py`, `contract/test_story_run_playback_routes.py`, `integration/story_video/test_playback_and_detail_postgres.py`.
Edit: `application/ports/story_video.py`, `application/ports/parent_story_runs.py` (record fields), `infrastructure/story_video/repository.py` (read), `infrastructure/persistence/parent_story_repository.py` (`get_run` calls the read), `contracts/schemas/parent_story_runs.py` (additive fields), `contracts/schemas/story_run_video.py`, `interfaces/http/routers/story_run_video.py`, `interfaces/http/routers/parent_story_runs.py` (`_response`, GET ETag and 304), `interfaces/http/app.py` (safe messages `INVALID_TOKEN`, `TOKEN_EXPIRED`, `STORAGE_UNAVAILABLE`), `interfaces/http/openapi_contract.py`, `infrastructure/config/settings.py` (ttl, ceiling, secret). Existing tests affected: `contract/test_parent_story_run_request_contract.py`, `unit/test_parent_story_run_create_service.py` and `unit/test_parent_story_run_cancel_repository.py` (record construction), `contract/test_openapi_contract_catalog.py`, `integration/test_m2_s2_g1_parent_story_postgres.py` and `integration/test_parent_story_run_history_postgres.py` where they compare the whole response body, `unit/test_http_error_envelope.py` if codes are added to the shared map.

## 7. Review rule

**2 reviews**: new authorization and playback guard (scope and role guards) and a change to a response Android and web already use.

## 8. Risks

R1 Stateless tokens cannot be revoked before expiry; mitigated by the per-request recheck and 300 s lifetime. R2 Header transport does not suit a plain web `<video src>` (Q2). R3 Whole-object read through the port with no range support (memory and latency; ceiling plus debt). R4 Additive fields can break a strict client decoder; precondition check on `.worktrees/mobile` and `.worktrees/ui` DTOs. R5 The secret must exist in production or the app refuses to start; recorded for the deployment owner.

## 9. BLOCKED_OPEN and ownership

- **Q1:** is the stateless signed token acceptable instead of TD-07's "stored hashed" token (which needs a new table outside DDL-B1)? Default yes.
- **Q2 (client, OPEN-WITH-DEFAULT):** may the playback token travel in a header, given that a web `<video>` element cannot set headers (the web client would fetch into a blob or use Media Source)? If the web player needs a URL-borne token, ask for a one-time exchange route; not built.
- **Q3:** the SRS asks for a "timeline" (AC-41, l.805) but no state-history store exists and "no read-model table" is a rule. Default: a derived list from existing timestamps; a true history needs an owner decision.
- **Q4:** token lifetime (300 s default; the SRS says only "short-lived").
- Quota summary content: OWNED_BY_OWNER (the quota reader); the marker is delivered here.
