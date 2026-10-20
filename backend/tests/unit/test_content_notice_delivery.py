"""Producer component checks; memory transactions/sink are not real BE1 adoption."""

from contextlib import contextmanager
from datetime import datetime

import pytest

from sketch2life.application.content_consumer_queries import notice_from_outbox
from sketch2life.application.content_notice_delivery import ContentNoticeDelivery
from sketch2life.contracts.schemas.content_consumers import ContentNoticeAckV1
from sketch2life.domain.learning_content.model import ContentError
from tests.learning_content_fixtures import NOW


def notice():
    return notice_from_outbox("event", "school", '''{
        "organization_id":"school","record_id":"record","version":1,
        "revision":6,"hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "state":"recalled","kind":"content.recall"}''')


class MemoryDelivery:
    def __init__(self):
        self.notice = notice()
        self.delivered = False
        self.marked_at = None
        self.fail_commit = False
        self.fail_mark = False

    @contextmanager
    def delivery(self, organization_id, event_id):
        self.notice = None if self.delivered else self.notice
        self.marked_at = None
        yield self
        if self.fail_commit:
            raise ContentError("SYNTHETIC_COMMIT_FAILURE")
        if self.marked_at is not None:
            self.delivered = True

    def mark_delivered(self, at):
        if self.fail_mark:
            raise ContentError("SYNTHETIC_MARK_FAILURE")
        self.marked_at = at


class SyntheticSink:
    def __init__(self, **changes):
        self.changes = changes
        self.calls = []
        self.fail = False

    def accept(self, item):
        self.calls.append(item)
        if self.fail:
            raise RuntimeError("private-token-must-not-escape")
        values = dict(event_id=item.event_id, organization_id=item.payload.organization_id,
                      consumer_id="gateway", outcome="accepted")
        values.update(self.changes)
        return ContentNoticeAckV1.model_construct(**values)


def worker(store, sink, **kwargs):
    return ContentNoticeDelivery(store, sink, consumer_id="gateway", clock=lambda: NOW, **kwargs)


@pytest.mark.parametrize("outcome", ["accepted", "duplicate"])
def test_matching_durable_ack_commits_once(outcome):
    store, sink = MemoryDelivery(), SyntheticSink(outcome=outcome)
    pump = worker(store, sink)
    assert pump.deliver("school", "event") == "delivered"
    assert store.delivered and store.marked_at == NOW
    assert pump.deliver("school", "event") == "already_delivered"
    assert len(sink.calls) == 1


def test_already_delivered_does_not_invoke_sink():
    store, sink = MemoryDelivery(), SyntheticSink()
    store.delivered = True
    assert worker(store, sink).deliver("school", "event") == "already_delivered"
    assert not sink.calls


@pytest.mark.parametrize("field,value", [
    ("event_id", "other-event"), ("organization_id", "other-school"),
    ("consumer_id", "other-gateway"), ("outcome", "pending"),
    ("event_id", ""), ("consumer_id", None),
])
def test_invalid_or_wrong_ack_never_marks_delivered(field, value):
    store, sink = MemoryDelivery(), SyntheticSink(**{field: value})
    with pytest.raises(ContentError, match="CONTENT_DELIVERY_INVALID_ACK"):
        worker(store, sink).deliver("school", "event")
    assert not store.delivered and store.marked_at is None


@pytest.mark.parametrize("raw", [None, {}, "secret"])
def test_untyped_ack_is_not_accepted(raw):
    class UntypedSink:
        def accept(self, item):
            return raw

    store = MemoryDelivery()
    with pytest.raises(ContentError, match="CONTENT_DELIVERY_INVALID_ACK"):
        worker(store, UntypedSink()).deliver("school", "event")
    assert not store.delivered


def test_sink_exception_is_safe_and_pending():
    store, sink = MemoryDelivery(), SyntheticSink()
    sink.fail = True
    with pytest.raises(ContentError, match="^CONTENT_DELIVERY_UNAVAILABLE$"):
        worker(store, sink).deliver("school", "event")
    assert not store.delivered and store.marked_at is None


@pytest.mark.parametrize("field,value", [("event_id", "other"), ("organization_id", "other")])
def test_misscoped_storage_notice_cannot_be_sent(field, value):
    store, sink = MemoryDelivery(), SyntheticSink()
    if field == "event_id":
        store.notice = store.notice.model_copy(update={field: value})
    else:
        store.notice = store.notice.model_copy(update={
            "payload": store.notice.payload.model_copy(update={field: value})})
    with pytest.raises(ContentError, match="CONTENT_NOTICE_SCOPE_MISMATCH"):
        worker(store, sink).deliver("school", "event")
    assert not sink.calls and not store.delivered


@pytest.mark.parametrize("field", ["organization_id", "event_id", "consumer_id"])
def test_invalid_target_rejected_before_effect(field):
    store, sink = MemoryDelivery(), SyntheticSink()
    with pytest.raises(ContentError, match="CONTENT_INVALID_DELIVERY_TARGET"):
        if field == "consumer_id":
            ContentNoticeDelivery(store, sink, consumer_id="")
        else:
            worker(store, sink).deliver(**({"organization_id": "school", "event_id": "event"}
                                          | {field: ""}))
    assert not sink.calls


def test_invalid_clock_rejected_before_effect():
    store, sink = MemoryDelivery(), SyntheticSink()
    pump = ContentNoticeDelivery(store, sink, consumer_id="gateway", clock=datetime.now)
    with pytest.raises(ContentError, match="CONTENT_INVALID_DELIVERY_CLOCK"):
        pump.deliver("school", "event")
    assert not sink.calls


def test_clock_failure_after_ack_keeps_pending():
    store, sink = MemoryDelivery(), SyntheticSink()
    times = iter([NOW, datetime(2026, 10, 17)])
    pump = ContentNoticeDelivery(store, sink, consumer_id="gateway", clock=lambda: next(times))
    with pytest.raises(ContentError, match="CONTENT_INVALID_DELIVERY_CLOCK"):
        pump.deliver("school", "event")
    assert len(sink.calls) == 1 and not store.delivered


@pytest.mark.parametrize("failure", ["fail_commit", "fail_mark"])
def test_storage_failure_never_reports_success(failure):
    store, sink = MemoryDelivery(), SyntheticSink()
    setattr(store, failure, True)
    with pytest.raises(ContentError, match="SYNTHETIC_"):
        worker(store, sink).deliver("school", "event")
    assert not store.delivered


def test_lost_ack_replays_same_event_without_fake_producer_completion():
    store, sink = MemoryDelivery(), SyntheticSink()
    sink.fail = True
    with pytest.raises(ContentError):
        worker(store, sink).deliver("school", "event")
    sink.fail = False
    sink.changes["outcome"] = "duplicate"
    assert worker(store, sink).deliver("school", "event") == "delivered"
    assert sink.calls[0] == sink.calls[1] and store.delivered
