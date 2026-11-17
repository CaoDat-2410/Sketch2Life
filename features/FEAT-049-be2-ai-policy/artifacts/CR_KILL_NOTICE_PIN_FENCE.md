# CR — policy-stop delivery must fence original policy generation

2026-10-18, source0ecff26. Request to foundation BE2-01/worker owner; proposed,
NOT adopted. No foundation source/schema modified. Owner deferred real wiring to
teammates; current implementation continues other approved local BE2-14 work.

## Evidence / gap

application/ports/ai_jobs.py CancellationNotice exposes notice_id, organization_id,
reason_code, session_id/job_type/subject_ref. services/ai_jobs.py notice_matches
uses OR matching across those selectors for cancellable jobs; no exact policy
pin/epoch selector. apply_cancellation_notice records notice only after processing
all matches; above dispatch_policy.notice_atomic_max fails without mutation.

BE2-14 scope_transition stores immutable disabled epoch/pin intent. A delayed old
stop mapped blindly to job_type can cancel newly authorized jobs after reviewed
reactivation. Feature names must not be assumed to equal job_type. Tuple return
and notice_seen replay are also not actual provider-stop/purge confirmation.

## Requested owner contract / acceptance

Provide a scoped internal application cancellation operation with deterministic
org/feature/stop-event idempotency and immutable original stopped policy generation
cutoff. Owner resolves feature-to-job semantics from adopted registry and selects
only applicable original requests/attempts, never later reactivated generation.
Reject ambiguous/missing/withdrawn mapping with typed pending/unsupported/error,
not broad fallback. No caller-provided all-org boolean or direct job-table write.
Exact payload fields/types and generation matching require owner adoption before
BE2-14 creates a notice or changes published shared contract.

Required tests: delayed stop after new activation excludes new jobs; replacement
pins retain original provenance; cross-org/feature mismatches fail; duplicate and
crash-after-owner-commit replay are idempotent; terminal jobs never resume; bounded
too-large handling truthfully pending; revoke/expiry fences current decisions;
transport/provider exceptions never mean all work stopped. Receipt must distinguish
owner notice application, per-job cancellation, provider acknowledgment and purge.

Until adopted: epoch disables new policy use locally; stop event remains pending
intent, NOT delivered/all-jobs-stopped. No fabricated mapping, notice consumption
or delivered_at update. BE2-14 C5/C6 can proceed without granting runtime adoption.
