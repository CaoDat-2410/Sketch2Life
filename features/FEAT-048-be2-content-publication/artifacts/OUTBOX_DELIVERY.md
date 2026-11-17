# BE2-12 C4d — owned outbox delivery

Scope: implement the already-approved P4 at-least-once producer delivery, not
another card's consumer, authorization, retry policy or active-copy effects.
One explicit internal call processes one exact organization/event. No scheduler,
automatic retries, credentials or public endpoint are added.

## Acceptance before implementation

- Lock the exact owned outbox row, scoped by organization; a missing row is an
  error, an already delivered row is a no-op. Concurrent busy row is distinguishable
  from missing and must not call the sink. Never read/write another owner's tables.
- Parse the persisted payload, validate organization, and send the existing typed
  notice. Only a strictly validated ACK matching event, organization and configured
  consumer permits setting delivered_at, in the same transaction as row selection.
- Missing/malformed/mismatched ACK, sink exception or storage failure leaves the
  producer pending. Errors exposed by the service are safe codes, not sink text.
- A crash/lost ACK after receiver acceptance may cause redelivery. The bound sink
  must implement durable dedup. Producer delivery is not an exactly-once guarantee.
- Validate aware completion clock before invoking the sink; record time after ACK.
- The existing single delivered_at column represents ONE fixed logical delivery
  destination, not per-consumer fanout. Trusted composition must adopt that binding;
  multiple independent consumers must NOT each run against this marker. A real
  fanout adapter must durably accept all its configured obligations before ACK.
  Destination changes/draining need a separate adopted transition; this component
  does not select a destination, retry budget, schedule or delivery timeout.
- The injected sink must bound its transport call. Row lock is held through that
  call; process/connection termination releases it. Operational timeout configuration
  remains a real adapter adoption gate, not a made-up production default.

Unit checks use a labelled transactional memory store. PostgreSQL checks must
exercise actual rows, transaction rollback, concurrent row locks, restart and lost
ACK replay. Synthetic receiver acceptance is not BE1/P4 consumer integration.

Real identity/source/review adapters, final owner delegate models, trusted durable
consumer adoption and full integrated closure remain separate mandatory gates.

## Implemented composition seam

```python
# Internal composition only: verified configuration and a real adopted sink.
delivery = ContentNoticeDelivery(
    SqlContentDeliveryStore(engine), sink, consumer_id=configured_logical_consumer_id)
result = delivery.deliver(organization_id, exact_event_id)
```

Return is delivered only after producer commit, or already_delivered without a
second sink invocation. Missing scope/event -> CONTENT_NOTICE_NOT_FOUND;
concurrent locked row -> CONTENT_DELIVERY_BUSY; sink failure ->
CONTENT_DELIVERY_UNAVAILABLE; invalid/mismatched ACK -> CONTENT_DELIVERY_INVALID_ACK;
database failure -> CONTENT_DELIVERY_STORAGE_UNAVAILABLE. All are internal safe
codes; none is automatically classified as a retryable production policy.
Caller must use the existing event enumeration/worker composition with adopted
operations policy; no public API, daemon or autonomous retry loop is introduced.

Actual evidence: evidence/notes/C4D_OUTBOX_DELIVERY_20261017.md. No DB schema or
migration change. The lifecycle/event/outbox payload and shared DATA-24 stay unchanged.
