# CMD-43 / DATA-28 candidate HTTP and effect receipt handoff

Revision1 approved2026-10-19. Owned0.1-candidate, not shared-owner adoption or
production composition. Endpoint not mounted in default app; no Child route.

## Transport and identity

Inject build_video_failure_router(service, resolve_identity, max_body_bytes=...).
Service=None returns closed503. Resolver must authenticate BE1 adult principal and
authorized target session, not trust client identity/session/org headers. Application
held guards independently check exact action/current scope. Actual BE1/P4 adapters
remain deferred; fixture identities/booleans are not production authorization.

POST /api/collaboration/v1/knowledge-videos/{video_id}/failure-dispositions.
Idempotency-Key is one opaque1–120 ID. If-Match exactly one strong quoted positive
run revision (signed64-bit), e.g. `"7"`; NOT video version2/job revision9/session4
or09 review revision. Missing428, malformed/duplicate400, stale409. Replay uses
ORIGINAL key/body/If-Match, never a new key after unknown effect.

application/json only, unencoded body, explicit positive streamed size bound,
actual bytes checked regardless of Content-Length. Strict JSON scalars/unknown
fields/duplicate keys (nested too)/nonfinite/nonobject/UTF8 checks. Borrow existing
09 transport-only admission/error primitives, translating VIDEO_REVIEW_ transport
codes to VIDEO_DISPOSITION_; no09 authority/domain/service reuse. Source pins and
regression cover this dependency. Duplicate Authorization401 before parsing.

Synthetic example (no actual consent/failure/budget authority implied):

```json
{
  "action": "retry",
  "reason": "Teacher requests another bounded attempt",
  "expected_video_version": 2,
  "expected_job_revision": 9,
  "expected_session_revision": 4,
  "retry_authorization_note": "For owner review only; not an authorization grant"
}
```

action=retry/skip/end_session; reason required nonblank <=200 chars. Optional note
only on retry, same bounds; its contents NEVER authorize budget. No body run revision,
org/actor/session/grant/checkpoint/budget/endpoint/media URL fields. Path video and
verified server scope plus run If-Match form Context/Choice. Own DTO, not a change
to upstream DATA-28 enum. All responses no-store/Vary:Authorization, generated
correlation ID, fixed safe error message. Authorized adult records include reason;
errors/events never echo raw reasons/notes/provider diagnostics/child data.

## Confirmed and pending outputs

200 data is strict ConfirmedDisposition: contract_version, disposition_id,
recorded_by, recorded_at, action, reason, prior_failure_ref (exact ref/version/hash),
session_revision, video_run_revision, outcome and nullable new_job_id.

| Action | Confirmed outcome | Required authenticated effect proof / returned revisions |
|---|---|---|
|retry|retry_pending|New video/job lifecycle, same content version, queued/pending_media, exact authorization+budget consumption references. video_run_revision=new lifecycle run revision; new_job_id required. Session after >= before, no auto stage inferred|
|skip|skipped_by_teacher|Explicit owner-permitted session transition receipt; after > before; video_run_revision=immutable prior failed run revision; new_job_id null. Not generated/succeeded|
|end_session|session_ended_early|Early outcome AND exact checkpoint/evidence ref; after > before; prior failed video run revision unchanged; new_job_id null. Partial/no checkpoint never confirms|

All confirmations historical receipt facts, not a live session grant/current stage
or playback capability. Exact output source Intent revalidated, foreign/forged
service projection503. No arbitrary object dumping or raw artifact/provider URL.

202 data is SEPARATE candidate PendingDisposition: contract_version, status=pending,
disposition_id, operation_key, reason_code=VIDEO_DISPOSITION_PENDING. No invented
recorded_by/at, after revision, new_job_id or outcome until verified exact receipt.
This does not add `pending` to confirmed upstream DATA-28 outcome enum.

## Owner protocol and provenance

FailureTarget authenticates exact org/session/video/content+run revision/job+job
revision/attempt, state failed_exhausted, pin/history digests, context/audience
revisions, exact failure/policy refs and exhausted time. Construction/type validity
does not authenticate any fact. Current01/08 adapter must prove final policy-exhausted
outcome/history and consistent current metadata. Generating/retryable/blocked_unsafe/
cancelled/success cannot be mislabeled exhausted. failure_ref is not media hash.

Context key scope org/session/actor/key EXCLUDES video/action/body, so changed body
conflicts. Stable unique failure claim org+target.claim_key(video/job lifecycle)
EXCLUDES actor/action/revisions; different keys/actors/actions cannot both win.
First pending intent, claim, immutable history and minimal event persist atomically
before effect. Durable store lock serializes own session, not cross-owner fences.
Unique loser rolls back wholly; later original-key request can recover, no hidden
automatic resend. A pending claim remains reserved even when dispatch is denied/
ACK is lost. Release/cancel/new action requires an explicit adopted reconciliation
protocol proving outcome/absence, not local guessing; no release method invented.

Bridge.execute runs outside10 DB tx with original key/body/target under current
owner fences. Exact EffectReceipt must match disposition_id, operation_key,
request_digest,target_digest,principal,action,session_before and timestamps. Retry
also binds original authorization_ref and budget consumption proof; new video/job
IDs differ from old. Current candidate same-content retry uses new08 video row,
not changed bytes/version or terminal-row resurrection. Content editing stays07/08.
Before/after session revisions are actual owner outputs, not incremented locally.
End checkpoint ref mandatory; authentication and completeness owed by BE1 bridge.

No boolean 'authoritative' shortcut. Actual bridge authenticates real receipts and
transaction semantics. One-owner transaction or explicit recoverable coordination
must consume retry budget/create lifecycle or commit skip/end/checkpoint; sequential
independent commits are not sold as atomic. Original key globally dedups that effect.

After timeout/malformed/foreign/late partial receipt/store uncertainty, return
pending or closed503 (if commit/guard exit ambiguous); preserve intent/history. Replay
reauthorizes ORIGINAL historical recovery, reads before resolving today's target,
and lookup only. None known absent or lookup outage never causes execute again.
Confirmed receipt replay does not revive current eligibility. No cancel/purge/
session reversal/reset/late result playback compensation is guessed.

## Closed errors

401 UNAUTHENTICATED.400 VIDEO_DISPOSITION_INVALID_IDEMPOTENCY_KEY/
INVALID_PRECONDITION/INVALID_TARGET.428 VIDEO_DISPOSITION_PRECONDITION_REQUIRED.
413 VIDEO_DISPOSITION_BODY_TOO_LARGE;415 UNSUPPORTED_MEDIA_TYPE;
422 VIDEO_DISPOSITION_INVALID_COMMAND.

403 VIDEO_DISPOSITION_FORBIDDEN/SCOPE_MISMATCH.409 VIDEO_NOT_EXHAUSTED,
VIDEO_DISPOSITION_STALE_TARGET/STALE_SESSION/IDEMPOTENCY_CONFLICT/CONFLICT,
VIDEO_RETRY_NOT_AUTHORIZED.503 VIDEO_DISPOSITION_DEPENDENCY_UNAVAILABLE for missing
or malformed adapters/unknown diagnostics; fixed message, retryable true only503.
Recovery uses ORIGINAL key/body, no automatic new action/authorization/resend.
