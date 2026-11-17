# Derived review history — F03 candidate 0.1

Application port: ContentReviewHistory.read. No new HTTP delivery/history route,
no shared DATA-24 command/record changes, no migration or original-proof rewrite.
The projection is owned by BE2-12 and is not a separate review authority.

## Scope and permissions

Caller supplies verified principal/org/record, an explicit content version,
page_size (1–100), optional after_revision and snapshot_revision. Server owner
guard and current scoped READ capability are required through transaction exit.
The 100-row cap is technical query admission, not a chosen business policy.

No authored body, source/asset bytes or raw child artifacts are returned. Entries
contain immutable original ReviewProof metadata plus separate derived state/reason.
The proof's original decision/reason/effective-at-recording state remains intact.
This does not grant raw-source access or permission for new-session usage.
History remains readable with READ authority after recall or source usage denial;
publication eligibility and historical audit permission are different operations.

## Snapshot and pagination

Store acquires the same parent SHARE boundary as resolution; writers use UPDATE.
Query reads ALL contexts for the requested exact version, ordered by monotonic
review_revision, limited to page_size+1. Projection rejects wrong target/hash,
invalid ordering/duplicates/revision ranges instead of disclosing corrupt scope.

Use returned next_after_revision with returned record_revision as snapshot_revision
for the next page. A changed global record revision raises CONTENT_STALE_REVISION;
restart pagination rather than mixing statuses computed at different revisions.
No continuation cursor for a missing/empty final page. Even reading an old
published version binds current global record revision for consistent context.

## Derived reasons, in evaluation order

| Condition | Derived state / reason |
|---|---|
| Exact target recalled or archived | stale / content_recalled or content_archived |
| Proof from prior review context | stale / context_changed |
| Dimension's proof superseded in same context | stale / dimension_replaced |
| Older version was never published and a newer head exists | stale / superseded_unpublished_version |
| Current owner policy version differs | stale / policy_changed |
| Exact library audience hash differs | stale / audience_changed |
| Original proof recorded stale/revoked | original state / recorded_ineffective |
| Current owner reports proof ineffective | stale / owner_ineffective |
| None of the above | effective / no derived stale reason |

Original state/reason is always preserved separately; a lifecycle stale reason
does not overwrite an original revocation. Older published v1 is not invalidated
merely by draft v2. New draft has no inherited reviews. The current owner's
boolean review_effective port cannot say whether false means revoked vs stale,
or provide the external cause. The view explicitly reports owner_ineffective,
not an invented revocation cause or real owner integration proof.

An effective history entry means the review remains selected/current, not that
the entire content is eligible: age/purpose/source/moderation/publication checks
still run through ContentEligibility for new usage. Negative review may itself
be effective feedback and still forbid publication.

## Evidence/remaining integration

Component fixtures and SQL runtime tests explicitly label owner ports ASSUMED.
Real BE1 READ/review authority/fencing and shared owner cause/adoption remain F02.
This closes the local projection omission only after its own tests; it does not
close full AC04, dispatcher, consumer or production composition gates.
