# C3b command orchestration — approved-plan implementation details

Scope: revision 1/P1–P4, all eight learning_content DATA-33 actions, shared
DATA-24 command/record unchanged. No preset/policy implementation or HTTP route
is introduced here. Those remain C4; real owner boundary adoption remains gated.

## Authority and eligibility

Every command/replay enters the owner guard and verifies principal/org and its
current independent action capability before accessing receipts. Review/publish
also check non-author separation against the persisted exact target version.
Parent UPDATE locking precedes non-create mutation; guard remains held through
SQL commit/rollback. Typed owner consistency obligations are in
C3_BOUNDARY_CANDIDATE.md, not implemented by the labelled test fixtures.

Create/edit/submit require current policy, server-derived generic source and
usage permission. Drafting/submission do not assert moderation success: a safety
review can still find a problem. Approve/publication additionally require passed
moderation. Negative review can request remediation without requiring the unsafe
source to pass moderation first; exact body/context/audience, review capability,
review CAS and current effectiveness still apply. Recall/archive are authorized
removal operations, not content usage, and must not be blocked by a source/policy
that has since become ineligible for publication.

Edits create head+1 draft with fresh author/time and no approval carry-over.
This also applies to a retired head under approved P3: old version remains
terminal; only the new version starts in draft and needs fresh review. See
artifacts/REINTRODUCTION_RULE.md for correction of the earlier over-restriction.
Superseded unpublished versions cannot mutate except exact recall/archive.
Previously published older versions remain addressable unless removed or denied
by current eligibility. Exact target hash, record If-Match and named review CAS
are separate checks. Explicit recall can target an older published version using
the current global record revision, without changing the draft head.

## Atomicity and identifiers

State/proof linkage/event/outbox/receipt share one transaction. Version bytes
remain immutable; stored events/outbox contain safe metadata, not body/asset
bytes. Receipt result includes DATA-33 server metadata and optional unchanged
shared ExactContentReviewRecordV1, never raw authored content.

Server IDs derive from SHA256(canonical JSON [organization, principal, request
key]) with separate lc_/lcr_/lce_ namespaces. Caller chooses the request key, not
an unscoped record/review/event ID. Changed content under that same scoped key
conflicts via the separate request fingerprint. This is idempotent identity,
not a security token or claim of opaque cryptographic secrecy.

## Duplicate and stale behavior

Fingerprint binds organization, principal, full validated command and record
If-Match. Original request with identical fingerprint may replay only after
current authorization/eligibility. Changed command or precondition conflicts.
Result distinguishes recorded result metadata from current exact-version
revision/state; no replay rewrites state, creates another version or emits events.

Non-create paths recheck receipt after acquiring parent UPDATE: an identical
command committed while waiting must replay, not fail by reapplying its original
If-Match. For unique insert conflict, the entire candidate transaction rolls
back first; one fresh transaction may read/validate the winner receipt. No blind
write retry, no arbitrary integrity error interpreted as success.

Recalled/archived content cannot replay create/edit/submit/review/publish receipts
as an effective action. Superseded unpublished versions are denied. Submit
receipts from a previous review context are ineffective. Review replay requires
the same exact proof still selected in the current context/dimension, current
policy and reviewer effectiveness; a superseded/revoked review does not replay.
Publication replay runs full current publication eligibility. Retirement replay
requires current recall authority and the same terminal state, but not content
usage authorization. History is preserved; callers must not treat a cached
response as permission for new-session use, which always calls resolution.

## Proof limits

Component memory rollback/thread checks are not SQL proof. PostgreSQL tests
exercise the actual SQL adapter with assumed owner ports. Repository/connection
reconstruction in the application test is not an independent-process restart
claim (C2 separately has a child-process persistence test). Real BE1 fencing,
review-owner conformance and production composition require separate evidence.
