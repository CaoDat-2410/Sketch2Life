# CMD-45 / DATA-29 candidate and CMD-59 source handoff

Approved revision1,2026-10-19. All shapes0.1-candidate; FR042/043 details remain
product refinements, no numeric age/material/prerequisite/ranking policy selected.
No default app mounting/production identity/provider. Actual owner CRs remain OPEN.

## Command boundary

Inject build_activity_execution_router(service, resolve_identity, max_body_bytes=...).
Service=None ->closed503. Existing verified VideoIdentity supplies principal/org/
authorized session, not body/X-Session/X-Organization values. Child/device/admin
not implicit Teacher. Actual action-specific current authority held by application
Boundary through commit, not transport constructor/type/role flag alone.

POST /api/collaboration/v1/activity-assignments, one Idempotency-Key opaque1–120.
Create select has no If-Match; existing assignment uses assignment_id +one strong
quoted assignment revision If-Match, e.g. `"2"`. Missing428, malformed400, stale409.
No mixing source/session/review/job revisions. Same key/body reauthorizes and returns
CURRENT assignment projection plus historical applied_revision/replayed=true; never
reapply old adaptation or return old ready as current. Changed body conflicts409.

Strict JSON/unknown fields/scalars/duplicates (nested too)/UTF8/nonfinite/object body,
content-type and duplicate auth/precondition checks. Explicit actual streamed size
limit, no encoded body, no trusting Content-Length. Existing09 transport-only
helpers reused with ACTIVITY_ code translation; no09 business/authority coupling.
Errors fixed text/server correlation/no-store/Vary:Authorization; no request notes,
private child/profile/source/provider diagnostic echo.

Synthetic select example:

```json
{
  "action": "select",
  "activity_ref": {"activity_id": "activity", "version": 1, "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "audience_scope": {"session_id": "session", "group_ids": ["group"]},
  "teacher_adaptations": {"instructions": "Instructions adapted for this group"}
}
```

Group list empty means whole class ONLY if actual owner explicitly resolves that
scope; client cannot declare child membership/ages. Existing pre-start select adds
assignment_id +If-Match and same required source/audience assertions, replaces local
adaptations, clears readiness/proof/invalidation. This is candidate reselection,
NOT an invented upstream `adapt` action. Exact source current publication required.

| Action | Allowed state / fields | Result |
|---|---|---|
|select create|Exact activity_ref +audience_scope, optional teacher_adaptations; no assignment/ETag|teacher_selected, revision1|
|select existing|Pre-start only; assignment_id/ETag +exact new source/scope/edits|preparation_required, revision+1, old confirmation/proof cleared|
|confirm_ready|Pre-start, nonnull feasibility_confirmation, fresh per-child/adaptation policy proof|ready|
|start|ready, nonnull feasibility_confirmation AGAIN, current policy/proof/ages rechecked|in_progress, started_at|
|finish|in_progress; optional reason/evidence_refs|completed, finished_at, pending BE1 result handoff|
|skip|Pre-start only, required nonblank reason, optional evidence_refs|skipped, no invented start/completion|
|interrupt|in_progress only, required nonblank reason, optional evidence_refs|interrupted, not successful completion|

Pre-start=proposed/teacher_selected/preparation_required/ready. Public create chooses
teacher_selected, not proposed recommendation acceptance. Terminal states cannot
resurrect; no start from selected without preparation. No automatic activity/session
start or shared stage transition. All successful changes monotonic own revision.

feasibility_confirmation={materials_available:bool,safety_checked:bool,note:null|string}.
True checkboxes NOT safety authority. Definition/adaptation review +exact bound
policy/child IDs and current owner checks required. Any denied/unknown child prevents
start/confirm. Materials/instructions/duration_note/safety_note edits are bounded
local snapshot fields, not master edits or self-reviewed hazard override.

## Projection and privacy

200 ActivityAssignmentView: assignment_id/assignment_revision/applied_revision/
replayed, organization_id, audience_scope(session/group refs), learning_objective_refs,
source_activity_ref, effective_activity_snapshot, state, selected_by, created_at/
started_at/finished_at, invalidation_reason and outcome_delivery.

Effective snapshot includes exact reviewed definition_ref, title/instructions/
materials/safety/duration/form/observation prompts plus current local edits. No child
IDs/ages, readiness profile, group-achievement judgement, reflection record or raw
URL. Private internal child context is bounded and only authenticated owning ports
receive scoped events. Master source hash stays original; edited effective snapshot
is a different bound assignment, not an assertion original authored bytes changed.

outcome_delivery=not_required before terminal; pending after terminal transaction;
acknowledged only when exact authenticated BE1 ACK is stored. COMPLETED means Teacher
ended actual assignment execution, NOT all children achieved objective or portfolio/
observation/reflection saved. Missing reflection remains absent; no mic/camera capture.

## Current source / age / preparation

Definition source_ref is12 content record exact version/hash; definition_ref points
to a separately reviewed immutable typed definition asset. map_published_definition
requires asset ref listed in published ContentWrite.asset_refs, activity kind and
matching title/exact age interval/source IDs. Actual resolver must verify asset BYTES
and current12 publication/reviews/rights under fences. Helper/legacy ID alone does
not authenticate source. Editorial note is never interpreted as trusted safety data.

ExecutionBinding digest covers org, full definition, edits, exact server audience/
child ages and policy. Every resolved child checked individually via current policy,
then exact adaptation_review proof. No group-average/legacy age buckets, imported
readiness numeric rules or user-supplied birthday/safe boolean as authority.
Start rechecks; a prior ready snapshot is not a permanent grant.

Internal authenticated owner invalidate notice (no public endpoint) preserves
history. Pre-start ->preparation_required with no proof; running remains running
with invalidation_reason, not a claimed physical stop. Actual policy/owner chooses
permitted intervention/finish/interrupt. Fresh source reselection still requires
current eligible publication; cannot revive recalled content from cached approval.

## Discovery / recommendation for BE1 CMD-59

ActivityDiscovery.discover(Actor,DiscoveryQuery, recommend=...) is a scoped source
provider, NOT another primary CMD-59 route. Query topic_ids/full-topic intersection,
exact age_months, confirmed preferences, explicit limit<=100; owner validates current
query context. Current authorized reviewed source enumeration bounded<=100. No
readiness/history/material fields used to remove rows. Warnings separate from results.
Exact source metadata age eligibility is not additional invented readiness filtering.

Recommendation optional: not_requested/available/unavailable, no fake score/hidden
provider fallback. Candidate exact refs/reasons must be unique subset of eligible
rows; missing/error/malformed ranker preserves catalog and reports unavailable.
LegacyRankingAdapter maps explicit version/hash refs to ActivityRankingCandidateV1
ACT-* aliases and current title, calls existing bounded ranker only when injected,
checks original request and candidate IDs. Reasons from reviewed mapping, not invented
AI explanation. Existing ranker max3/age bounds stay candidate adapter limits, not
new product policies or hard catalog filters. No provider instance/config selected.

## Delivery / closed errors

OutcomeEvent binds event ID, exact terminal assignment, created_at and recorded_by
(authenticated finishing/skipping/interrupting Teacher, independent of selected_by).
Its fingerprint/ACK includes that actor; SQL requires it match command receipt.
It is not a Teacher observation or per-child assessment. Actor-key receipts/history/event
commit atomically. ActivityOutcomeDelivery.deliver sends ONE explicitly selected
event outside DB UoW; no scheduler/default retry budget/lease. Concurrent calls may
redeliver same event and REQUIRE actual authenticated durable BE1 consumer dedup on
ID+exact payload before use. At-least-once transport, no exactly-once external claim.
OutcomeAck event_id/event_digest/exact receipt_ref must match, immutable after first
ACK. Timeout/wrong ACK/lost ACK/store failure remains pending; same event redelivery,
never changed payload/new outcome/reflection. Own ACK is not an independently proven
BE1 portfolio save; consumer semantics need CR11-03 adoption.

401 UNAUTHENTICATED;400 ACTIVITY_INVALID_IDEMPOTENCY_KEY/INVALID_PRECONDITION/
CREATE_PRECONDITION_FORBIDDEN;428 ACTIVITY_PRECONDITION_REQUIRED;413
ACTIVITY_BODY_TOO_LARGE;415 UNSUPPORTED_MEDIA_TYPE;422 ACTIVITY_INVALID_COMMAND.
403 ACTIVITY_FORBIDDEN/SCOPE_MISMATCH;404 ACTIVITY_NOT_FOUND;409
ACTIVITY_STALE_REVISION/SOURCE_MISMATCH/SOURCE_INELIGIBLE/POLICY_DENIED/
INVALID_TRANSITION/NOT_READY/PREPARATION_STALE/IDEMPOTENCY_CONFLICT/WRITE_CONFLICT.
503 ACTIVITY_DEPENDENCY_UNAVAILABLE for unbound/unknown/malformed adapters.
retryable=true only503; original key/body/precondition recovers after ambiguous
commit. Internal corruption is never echoed as raw source/provider diagnostic.
