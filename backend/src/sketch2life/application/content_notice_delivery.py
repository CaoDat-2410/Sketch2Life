"""One-event at-least-once producer; no scheduler or foreign consumer effects."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.content_consumers import (
    ContentDeliveryStore,
    ContentNoticeSink,
)
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.content_consumers import ContentNoticeAckV1
from sketch2life.domain.learning_content.model import ContentError

_IDENTIFIER = TypeAdapter(OpaqueId)


class ContentNoticeDelivery:
    """Trusted internal composition only, with ONE fixed logical sink per outbox.

    The sink must durably deduplicate, authenticate transport and bound its call.
    Changing destination or using independent per-consumer pumps is NOT supported
    by the single delivered_at marker. Real binding/adoption remains mandatory.
    """

    def __init__(self, store: ContentDeliveryStore, sink: ContentNoticeSink, *,
                 consumer_id: str, clock: Callable[[], datetime] | None = None) -> None:
        try:
            self.consumer_id = _IDENTIFIER.validate_python(consumer_id, strict=True)
        except ValidationError:
            raise ContentError("CONTENT_INVALID_DELIVERY_TARGET") from None
        self.store = store
        self.sink = sink
        self.clock = clock or (lambda: datetime.now(UTC))

    def _now(self) -> datetime:
        now = self.clock()
        if not isinstance(now, datetime) or now.utcoffset() is None:
            raise ContentError("CONTENT_INVALID_DELIVERY_CLOCK")
        return now.astimezone(UTC)

    def deliver(self, organization_id: str,
                event_id: str) -> Literal["delivered", "already_delivered"]:
        try:
            _IDENTIFIER.validate_python(organization_id, strict=True)
            _IDENTIFIER.validate_python(event_id, strict=True)
        except ValidationError:
            raise ContentError("CONTENT_INVALID_DELIVERY_TARGET") from None
        self._now()  # Reject invalid clock before any external effect.
        with self.store.delivery(organization_id, event_id) as tx:
            notice = tx.notice
            if notice is None:
                return "already_delivered"
            if (notice.event_id != event_id
                    or notice.payload.organization_id != organization_id):
                raise ContentError("CONTENT_NOTICE_SCOPE_MISMATCH")
            try:
                raw_ack = self.sink.accept(notice)
            except Exception:
                # Never expose network/provider/receiver exception messages.
                raise ContentError("CONTENT_DELIVERY_UNAVAILABLE") from None
            try:
                # Revalidate even an instance built with model_construct/copy.
                if not isinstance(raw_ack, ContentNoticeAckV1):
                    raise ValueError("invalid acknowledgement type")
                ack = ContentNoticeAckV1.model_validate_json(raw_ack.model_dump_json())
            except (ValidationError, ValueError, TypeError):
                raise ContentError("CONTENT_DELIVERY_INVALID_ACK") from None
            if (ack.event_id != event_id or ack.organization_id != organization_id
                    or ack.consumer_id != self.consumer_id):
                raise ContentError("CONTENT_DELIVERY_INVALID_ACK")
            tx.mark_delivered(self._now())
        # Do not report success before the storage context's actual commit.
        return "delivered"
