# BE2-09 CMD-41/42 candidate HTTP handoff

Owned09 revision1 implementation; candidate0.1, not shared-owner adoption. Existing
shared DATA-24 schema is reused unchanged. Routes are NOT mounted in the production
app. This document does not authorize production mounting or permissive adapters.

## Composition and common boundary

`build_video_review_router(review_service, playback_service, resolve_identity,
resolve_playback_subject, max_body_bytes=...)` returns an APIRouter. Default prefix
`/api/collaboration/v1` is configurable. Services/resolvers are injected; None service
or missing playback resolver returns closed503, never fake success/access. Positive
explicit byte limit required, no production policy default. Sync adapters/services
run in threadpool, request body streamed with actual byte bound.

Identity resolver returns verified VideoIdentity(principal_id, organization_id,
session_id) from trusted BE1/server context. It must verify credentials, authorized
target session and action, not just trust body/X-Session/X-Organization headers.
Application guards independently hold/recheck current action-specific authority.
Child/device/admin roles receive no implicit Teacher permission. Duplicate auth
headers rejected; absent identity401 before parsing body.

One valid Idempotency-Key required (opaque ID1–120). application/json only; no
encoded bodies. Duplicate JSON keys (including nested), nonfinite tokens, invalid
UTF8, non-object bodies and unknown fields rejected. Strict scalars reject bools
as revisions. Client-supplied correlation ID is not reflected; server generates it.
All owned responses/errors use Cache-Control:no-store and Vary:Authorization.
No request body, source/script/child list, provider exception or storage URL echoed
in errors. Neither endpoint serves media. No lifecycle invalidation public route.

## CMD-41 — POST /knowledge-videos/{video_id}/reviews

If-Match is required and means **canonical09 video review head revision**. Exactly
one strong quoted positive decimal, e.g. `"1"`; weak/list/wildcard/zero/leading-zero/
out-of-64-bit-range values rejected. Missing428; malformed400; stale409. It is NOT
run/job/session revision. A new review advances expected review revision by1.
Replay resends ORIGINAL key/body/If-Match, not today's precondition.

Body is ExactContentReviewCommandV1, not a new copy of shared DATA-24:

```json
{
  "target_kind": "knowledge_video",
  "target_id": "video",
  "target_version": 1,
  "target_hash": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
  "source_context_revision": 0,
  "decision": "approve",
  "review_context": {
    "kind": "session_content",
    "session_id": "session",
    "audience_context_revision": 0,
    "consent_revision_refs": [{"subject_ref": "child", "revision": 1}],
    "review_purpose": "teaching_delivery"
  },
  "audience_scope": {
    "session_id": "session",
    "group_ids": ["group"],
    "participant_ids": ["child"]
  }
}
```

Synthetic fixture IDs/hash above are examples, NOT actual consent/media evidence.
Audience/context in shared DTO are assertions matched to resolved scope, not
authority. Use final artifact BYTE hash, not pin/catalog hash. target_id must match
path. Owner resolves ready artifact/current lineage and exact authorized audience.
Generic library publication review cannot replace session Teacher review.
Non-null review_dimension/body expected_review_revision rejected by09 refinement.
reject/request_changes require nonblank reason. Edits go through07/08 new version,
not mutation of approved bytes by this route.

200 data: contract_version, video_id, target_version, target_hash, canonical shared
record, current_review_revision, replayed. Shared record identifies the historical
review; its state is refreshed against current head on replay. Superseded approval
becomes stale, not perpetually effective. Effective rejection is not approval.
Approval never automatically starts playback. Invalid dependency projections503.

## CMD-42 — POST /knowledge-videos/{video_id}/playback

Body is owned StartVideoPlayback0.1-candidate. All fields required:

| Field | Why / source |
|---|---|
| target_version | Exact final content version assertion, not render/job revision |
| target_hash | Final artifact byte hash assertion |
| subject_digest | Exact owned subject digest covering pin/context/audience/consent/policy; from adopted09 projection, not arbitrary client audience grant |
| review_id | Exact prior Teacher session review reference |
| review_revision | Review that authorizes this new start; independent of session CAS |
| expected_session_revision | Explicit BE1 session CAS, nonnegative integer |

Revision integers bounded to signed64-bit for this candidate transport. Path video
and verified org/session/actor are NOT body fields. CMD-42 does not consume If-Match;
present header400 rather than silently confusing review/run/job/session preconditions.
No duplicated shared review DTO and no public script, approval bool or raw URL.

Playback resolver signature: `(VideoIdentity, video_id, StartVideoPlayback) ->
ReviewSubject`. It must resolve/authenticate original-scope exact immutable subject
for replay, including historical versions, not substitute today's artifact. Router
revalidates native subject and compares org/session/video/version/byte hash/digest
before application call. A digest assertion is not a permission check. Current
eligibility/effective review/session revision still verified under actual held
application/BE1 fences at dispatch; no network under own DB transaction.

Application persists original scoped intent before external bridge call. Scope is
org/session/actor/key (NOT per video); changed body conflicts409. Duplicate pending
does lookup only, never automatically start again. Lost ACK/malformed/foreign receipt
stays pending. Unknown effect is not cancellation, rollback or permission to resend.
Missing actual current guards/bridge must not be replaced with fixture adapters.

202 pending data has status=pending, stable operation_key, reason_code=
VIDEO_PLAYBACK_PENDING and receipt_id=null. 200 confirmed/rejected has exact receipt
reference and corresponding reason_code. Projection checks exact scoped operation
key and consistent status/reason/receipt. **confirmed is historical**, not current
playing, current authorization or a bearer grant. No access_ref/URL/token/TTL.
Actual BE1 mediated gateway supplies/rechecks any authorized reference on EVERY
fetch/range/resume; that adoption remains CR09-02, not this HTTP endpoint.

## Closed error envelope / recovery

Envelope: correlation_id + error {code, fixed message, retryable}. retryable=true
only for503; retry/recovery must keep original key/body/precondition. No automatic
new key after ambiguous failure. Error samples are synthetic public codes only:

| Status | Codes / meaning |
|---|---|
|401|UNAUTHENTICATED|
|400|VIDEO_REVIEW_INVALID_IDEMPOTENCY_KEY, VIDEO_REVIEW_INVALID_PRECONDITION, VIDEO_REVIEW_INVALID_TARGET, VIDEO_PLAYBACK_UNSUPPORTED_PRECONDITION|
|403|VIDEO_REVIEW_FORBIDDEN, VIDEO_PLAYBACK_FORBIDDEN, VIDEO_REVIEW_SCOPE_MISMATCH|
|409|VIDEO_REVIEW_STALE_REVISION/HEAD_NOT_CURRENT/TARGET_NOT_CURRENT/TARGET_MISMATCH/IDEMPOTENCY_CONFLICT/WRITE_CONFLICT; VIDEO_PLAYBACK_IDEMPOTENCY_CONFLICT/REVIEW_NOT_EFFECTIVE/STALE_SESSION|
|413|VIDEO_REVIEW_BODY_TOO_LARGE|
|415|UNSUPPORTED_MEDIA_TYPE|
|422|VIDEO_REVIEW_INVALID_COMMAND/INVALID_CONTEXT/REASON_REQUIRED|
|428|VIDEO_REVIEW_PRECONDITION_REQUIRED|
|503|VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE or VIDEO_PLAYBACK_DEPENDENCY_UNAVAILABLE; unknown exceptions/codes and malformed adapter outputs redacted|

Public start pending is a separate202 recovery result, not falsely promoted to503
failure/rollback or200 confirmed. Foreign scope403 reveals no original metadata.
Owner-specific errors must adopt this closed mapping (or coordinate a new version),
not leak arbitrary diagnostics. Root framework unmatched routes are not09 responses.
