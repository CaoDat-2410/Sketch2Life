# H-CONTENT-PRESET consumer pack — 0.1-candidate

Producer: BE2-12 (receiver owns 08–14). Consumers: receiver's later 08/11/13
cards, sender's 01–07 integration points where applicable, and BE1/P4 gateway/
audit/notification composition. This is a proposed typed boundary and executable
conformance pack, not another owner's implementation or adoption sign-off.

## 1. Published-reference query

`PublishedContentQueryPort.resolve_reference(principal_id, organization_id, query)`
is implemented by ContentConsumerQueries over existing ContentEligibility.
Verified actor/org are separate server arguments, not caller-asserted query fields.
ContentReferenceQueryV1 contains record_id, age_months, purpose_code, optional
explicit version and expected_hash (hash requires explicit version).

```python
query = ContentReferenceQueryV1(
    record_id=selected_record_id, age_months=verified_age_months,
    purpose_code=applicable_purpose, version=pinned_version,
    expected_hash=pinned_hash,
)
reference = queries.resolve_reference(verified_actor, verified_org, query)
```

Every call rechecks current READ scope, policy/source/moderation and both exact
effective reviews under the content guard/transaction. PublishedContentReferenceV1
returns organization/id/version/revision/hash and both review IDs/policy version.
It contains no source/media/title/body, bearer token or raw child data.

The reference is immutable metadata, NOT a delivery/consent grant, reservation or
permission to skip current checks. It may be retained as historical provenance,
but each new use requires resolution. Reference return is a point-in-time content
decision; BE1's session-start commit needs its adopted consistency/revalidation
contract to avoid a cross-transaction recall/authorization race. This pack does
not manufacture that fence or extend an in-process guard across an RPC.

Default selects eligible published content, not draft head. Explicit version/hash
never substitutes. After recall/archive, old ref metadata remains historically
unchanged but new default/exact resolution is denied. New version needs fresh
reviews and only becomes selectable after actual publication.

## 2. Lifecycle notice, matching owned outbox

`notice_from_outbox(event_id, organization_id, payload_json)` validates the exact
existing SQL event/outbox payload and wraps ContentLifecycleNoticeV1. It is a pure
projection, NOT an outbox reader, delivery worker or acknowledgement operation.

Notice contains contract name/version, stable event_id, payload:
organization_id/record_id/version/revision/hash/state/kind. Kind is one of eight
`content.<action>` values; action/state combinations are validated. No extra
secrets/content fields allowed; wrong scoped organization is rejected safely.
This parser does not authenticate a producer: use only configured trusted
internal outbox delivery. Do not expose notice acceptance as a client API.

Notice is an invalidation/audit intent, not a new-session authorization. Consumers
locate impacted refs in their OWN storage via exact organization/id/version/hash;
BE2-12 neither reads nor writes their tables. No automatic active-copy deletion,
replacement, portfolio mutation or session cancellation policy is invented.

## 3. Sink and acknowledgement obligations

Candidate ContentNoticeSink.accept(notice) returns ContentNoticeAckV1 with exact
event_id, organization_id, configured consumer_id and accepted/duplicate outcome.

- Durably deduplicate scoped event_id plus exact canonical payload digest atomically
  with the consumer's own effect. Same ID/different body is a conflict, not duplicate.
- Acknowledge only after durable acceptance; lost ack/restart must tolerate replay.
- Delivery adapter must verify ack event/org/consumer before marking own outbox
  delivered. No ack means pending/retry under the adopted operational policy.
- Retirements invalidate exact versions for new use; delayed publish or duplicate
  cannot resurrect the same retired version. Do not use a global record high-water
  mark to confuse a new draft version with an old published/retired version.
- Keep historical pinned references and original provenance. Authoritative
  eligibility, not local notice cache, decides new use.

No exactly-once guarantee, worker, scheduler, transport secrets, production retry
budget or durable BE1 consumer is supplied by this candidate port. Those are
explicit remaining wiring/adoption responsibilities, not test fixtures in disguise.

## 4. Executable examples and evidence

`backend/tests/contract/test_content_consumers.py` includes an explicitly labelled
memory sink illustrating duplicate/conflict, delayed publication after recall,
exact-version invalidation and unchanged pinned history. It is NOT durable dedup.
Positive/negative query examples cover current review/source/policy/READ withdrawal,
strict metadata, wrong scope/fields and no fabricated child session/consent.

`test_consumer_contracts_from_actual_http_sql_and_outbox` in the owned PostgreSQL
suite exercises the real candidate HTTP route/SQL lifecycle, shared reviews,
reference resolution and typed notice projection from actual outbox rows. Identity/
owner guard is still ASSUMED. Rows remain delivered_at=NULL: no actual delivery
is claimed. No fake PASS from an absent sink or missing runtime.

## 5. Receiver / sender integration checklist

Receiver 08–14 supplies this branch's query/notice ports, metadata contracts and
conformance examples; future 13/14 can bind strict owner models to the fixed CMD-48
dispatcher without a second route. Sender 01–07 consumes agreed references and
review contracts without direct learning_content SQL or duplicate DATA-24 schema.
BE1/P4 binds real authority/source/review/commit consistency, session gateway and
scoped durable sink, then runs real contract conformance. Keep actual integrated
acceptance separate from this pack's component/owned SQL evidence.
