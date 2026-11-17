"""Candidate versioned ports; BE1/P4 own effects, real authority and adoption."""

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol

from sketch2life.contracts.schemas.content_consumers import (
    ContentLifecycleNoticeV1,
    ContentNoticeAckV1,
    ContentReferenceQueryV1,
    PublishedContentReferenceV1,
)


class PublishedContentQueryPort(Protocol):
    def resolve_reference(self, principal_id: str, organization_id: str,
                          query: ContentReferenceQueryV1) -> PublishedContentReferenceV1: ...


class ContentNoticeSink(Protocol):
    """Only configured trusted delivery may invoke; not a public command API.

    Receiver durably deduplicates organization/event_id and exact payload digest
    atomically with its own effect; changed payload under same key is an error,
    never an accepted duplicate. Ack only after durable acceptance. At-least-once
    replay must be safe, including lost ack. Real adapter must scope/authenticate
    producer and preserve historical refs without inventing active-copy deletion.
    """

    def accept(self, notice: ContentLifecycleNoticeV1) -> ContentNoticeAckV1: ...


class ContentDeliveryTransaction(Protocol):
    """Exact row locked through acknowledgement/commit; None means delivered."""

    notice: ContentLifecycleNoticeV1 | None

    def mark_delivered(self, at: datetime) -> None: ...


class ContentDeliveryStore(Protocol):
    def delivery(self, organization_id: str,
                 event_id: str) -> AbstractContextManager[ContentDeliveryTransaction]: ...
