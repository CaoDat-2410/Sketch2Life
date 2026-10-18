"""ASSUMED owner/bridge, transactional MEMORY only, not actual BE1 playback proof."""

import copy
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sketch2life.application.video_playback import VideoPlaybackService
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.domain.video_review.model import Decision, Invalidation, ReviewHead
from sketch2life.domain.video_review.playback import (
    PlaybackIntent,
    PlaybackReceipt,
    PlaybackRequest,
    PlaybackState,
)
from tests.unit.test_video_review_domain import NOW, approved


class MemoryStore:
    """Test transaction rollback; NOT durable storage/locking/owner fences."""

    def __init__(self):
        self.rows = {}
        self.active = False
        self.fail_insert = self.fail_save = self.fail_commit = False

    @contextmanager
    def transaction(self, org, session):
        assert not self.active
        self.active = True
        before = copy.deepcopy(self.rows)
        self.scope = (org, session)
        try:
            yield self
            if self.fail_commit:
                raise RuntimeError("synthetic private commit")
        except Exception:
            self.rows = before
            raise
        finally:
            self.active = False

    def get(self, principal, key):
        assert self.active
        return self.rows.get((*self.scope, principal, key))

    def insert(self, intent):
        assert self.active
        if self.fail_insert:
            raise RuntimeError("private insert failure")
        subject = intent.request.subject
        assert self.scope == (subject.organization_id, subject.audience.session_id)
        key = (*self.scope, intent.principal_id, intent.client_key)
        assert key not in self.rows
        self.rows[key] = intent

    def save(self, intent, *, expected_revision):
        assert self.active
        if self.fail_save:
            raise RuntimeError("private save failure")
        key = (*self.scope, intent.principal_id, intent.client_key)
        assert self.rows[key].revision == expected_revision
        self.rows[key] = intent


class AssumedBoundary:
    def __init__(self, head):
        self.head = head
        self.checks = []
        self.denied = None
        self.held = False
        self.on_check = None
        self.fail_exit = False

    @contextmanager
    def guard(self, principal, org, session):
        assert (principal, org, session) == ("teacher", "school", "session")
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("private guard exit")
        finally:
            self.held = False

    def review_head(self, request):
        assert self.held
        return self.head

    def check(self, intent, phase):
        assert self.held
        self.checks.append(phase)
        if self.on_check:
            self.on_check(intent, phase)
        if phase == self.denied:
            raise VideoError("VIDEO_PLAYBACK_FORBIDDEN")


def receipt(intent, **changes):
    return PlaybackReceipt(
        **dict(
            receipt_id="receipt",
            operation_key=intent.operation_key(),
            request_digest=intent.request.digest(),
            principal_id="teacher",
            session_revision_before=4,
            session_revision_after=5,
            accepted=True,
            recorded_at=NOW,
            authoritative=True,
        )
        | changes
    )


def setup():
    head = approved()
    request = PlaybackRequest(head.subject, head.entry.review_id, head.revision, 4)
    store, boundary, bridge = MemoryStore(), AssumedBoundary(head), Mock()

    def start(intent):
        assert boundary.held and not store.active
        assert len(store.rows) == 1 and next(iter(store.rows.values())) == intent
        return receipt(intent)

    bridge.start.side_effect = start
    bridge.lookup.return_value = None
    service = VideoPlaybackService(boundary, store, bridge, clock=lambda: NOW)
    return SimpleNamespace(
        request=request, store=store, boundary=boundary, bridge=bridge, service=service
    )


def execute(h, request=None, key="key"):
    return h.service.start("teacher", key, request or h.request)


def test_intent_commits_before_bridge_outside_db_and_exact_receipt_not_url():
    h = setup()
    result = execute(h)
    assert result.status == "confirmed" and result.receipt_id == "receipt"
    assert not hasattr(result, "url") and not hasattr(result, "playing")
    assert next(iter(h.store.rows.values())).state is PlaybackState.PLAYING
    assert h.boundary.checks == [
        "prepare",
        "commit_intent",
        "commit_intent",
        "dispatch",
        "record_receipt",
        "record_receipt",
    ]


def test_duplicate_confirmed_no_second_effect_even_with_changed_clock():
    h = setup()
    first = execute(h)
    h.service._clock = lambda: NOW.replace(year=2027)
    assert execute(h) == first
    assert h.bridge.start.call_count == 1
    h.bridge.lookup.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"review_id": "different"},
        {"review_revision": 3},
        {"expected_session_revision": 5},
    ],
)
def test_same_key_different_body_conflict_not_new_effect(changes):
    h = setup()
    execute(h)
    with pytest.raises(VideoError, match="VIDEO_PLAYBACK_IDEMPOTENCY_CONFLICT"):
        execute(h, replace(h.request, **changes))
    assert h.bridge.start.call_count == 1


@pytest.mark.parametrize("mode", ["empty", "rejected", "stale", "wrong-review", "wrong-head"])
def test_no_effect_without_current_exact_approved_review(mode):
    h = setup()
    head = h.boundary.head
    if mode == "empty":
        h.boundary.head = ReviewHead(head.subject, 2)
    elif mode == "rejected":
        h.boundary.head = head.record(2, "reject", "teacher", Decision.REJECT, "reason", NOW)
    elif mode == "stale":
        h.boundary.head = head.invalidate(2, Invalidation.CONTENT_CHANGED)
    elif mode == "wrong-review":
        h.request = replace(h.request, review_id="foreign")
    else:
        h.request = replace(h.request, review_revision=9)
    with pytest.raises(VideoError, match="VIDEO_PLAYBACK_REVIEW_NOT_EFFECTIVE"):
        execute(h)
    assert not h.store.rows
    h.bridge.start.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"video_version": 2},
        {"pin_digest": "f" * 64},
        {"source_context_revision": 1},
        {"artifact": ExactRef("asset", 2, "f" * 64)},
    ],
)
def test_changed_content_context_hash_not_authorized_by_old_approval(changes):
    h = setup()
    h.request = replace(h.request, subject=replace(h.request.subject, **changes))
    with pytest.raises(VideoError):
        execute(h)
    h.bridge.start.assert_not_called()


@pytest.mark.parametrize("phase", ["prepare", "commit_intent", "dispatch"])
def test_current_teacher_or_consent_denial_blocks_effect(phase):
    h = setup()
    h.boundary.denied = phase
    with pytest.raises(VideoError, match="VIDEO_PLAYBACK_FORBIDDEN"):
        execute(h)
    h.bridge.start.assert_not_called()
    assert len(h.store.rows) == (1 if phase == "dispatch" else 0)


def test_revocation_at_last_intent_confirmation_rolls_back_no_dispatch():
    h = setup()

    def revoke(intent, phase):
        if phase == "commit_intent" and h.store.rows:
            raise VideoError("VIDEO_PLAYBACK_FORBIDDEN")

    h.boundary.on_check = revoke
    with pytest.raises(VideoError):
        execute(h)
    assert not h.store.rows
    h.bridge.start.assert_not_called()


@pytest.mark.parametrize("failure", ["fail_insert", "fail_commit"])
def test_persistence_fault_before_dispatch_no_effect_or_fake_success(failure):
    h = setup()
    setattr(h.store, failure, True)
    assert execute(h).status == "pending"
    h.bridge.start.assert_not_called()


def test_lost_ack_recover_original_receipt_without_second_start_or_review_resurrection():
    h = setup()
    committed = []

    def lost_ack(intent):
        committed.append(receipt(intent))
        raise TimeoutError("private provider path")

    h.bridge.start.side_effect = lost_ack
    pending = execute(h)
    assert pending.status == "pending" and "private" not in repr(pending)
    h.boundary.head = h.boundary.head.invalidate(2, Invalidation.USAGE_REVOKED)
    h.bridge.lookup.return_value = committed[0]
    result = execute(h)
    assert result.status == "confirmed" and result.operation_key == pending.operation_key
    assert h.bridge.start.call_count == 1
    assert not hasattr(result, "access_ref")  # Historical result, no live permission.


@pytest.mark.parametrize("unavailable", [False, True])
def test_missing_or_unavailable_receipt_never_guesses_resend(unavailable):
    h = setup()
    h.bridge.start.side_effect = TimeoutError("lost")
    assert execute(h).status == "pending"
    if unavailable:
        h.bridge.lookup.side_effect = TimeoutError("outage")
    assert execute(h).status == "pending"
    assert h.bridge.start.call_count == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"operation_key": "f" * 64},
        {"request_digest": "f" * 64},
        {"principal_id": "foreign"},
        {"session_revision_before": 3},
        {"authoritative": 1},
        {"accepted": 1},
        {"session_revision_after": True},
        {"recorded_at": NOW.replace(year=2025)},
        {"receipt_id": "private/url"},
    ],
)
def test_forged_receipt_never_confirmed_or_automatically_retried(changes):
    h = setup()
    h.bridge.start.side_effect = lambda intent: replace_unsafe(receipt(intent), changes)
    result = execute(h)
    assert result.status == "pending" and result.receipt_id is None
    assert next(iter(h.store.rows.values())).receipt is None
    assert h.bridge.start.call_count == 1


def replace_unsafe(value, changes):
    value = copy.deepcopy(value)
    for field, field_value in changes.items():
        object.__setattr__(value, field, field_value)
    return value


def test_explicit_rejection_receipt_never_playing_or_auto_retry():
    h = setup()
    h.bridge.start.side_effect = lambda intent: receipt(
        intent, accepted=False, session_revision_after=4
    )
    assert execute(h).status == "rejected"
    assert execute(h).status == "rejected"
    assert h.bridge.start.call_count == 1
    assert next(iter(h.store.rows.values())).state is PlaybackState.REJECTED


def test_storage_lost_ack_remains_pending_then_authenticated_lookup_recovers():
    h = setup()
    h.store.fail_save = True
    assert execute(h).status == "pending"
    h.store.fail_save = False
    intent = next(iter(h.store.rows.values()))
    h.bridge.lookup.return_value = receipt(intent)
    assert execute(h).status == "confirmed"
    assert h.bridge.start.call_count == 1


def test_record_authority_failure_does_not_fake_rollback_of_external_effect():
    h = setup()
    h.boundary.denied = "record_receipt"
    assert execute(h).status == "pending"
    assert h.bridge.start.call_count == 1
    assert next(iter(h.store.rows.values())).receipt is None


def test_no_recovery_permission_no_receipt_disclosure():
    h = setup()
    execute(h)
    h.boundary.denied = "recover"
    with pytest.raises(VideoError, match="VIDEO_PLAYBACK_FORBIDDEN"):
        execute(h)
    assert h.bridge.start.call_count == 1


def test_guard_exit_failure_after_effect_does_not_claim_current_playing_or_retry():
    h = setup()
    h.boundary.fail_exit = True
    assert execute(h).status == "pending"
    h.boundary.fail_exit = False
    assert execute(h).status == "confirmed"
    assert h.bridge.start.call_count == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("review_revision", True),
        ("expected_session_revision", True),
        ("review_id", "private/url"),
    ],
)
def test_native_request_revision_or_ref_invalidity_rejected_before_work(field, value):
    h = setup()
    with pytest.raises(VideoError):
        execute(h, replace_unsafe(h.request, {field: value}))
    h.bridge.start.assert_not_called()


def test_domain_receipt_idempotent_terminal_immutable_original_key_scope():
    h = setup()
    intent = PlaybackIntent("teacher", "key", h.request, NOW)
    proof = receipt(intent)
    settled = intent.settle(proof)
    assert settled.settle(proof) is settled
    assert (
        replace(intent, created_at=NOW.replace(year=2027)).operation_key() == intent.operation_key()
    )
    assert replace(intent, client_key="other").operation_key() != intent.operation_key()
    assert replace(intent, principal_id="other").operation_key() != intent.operation_key()
    with pytest.raises(VideoError, match="VIDEO_PLAYBACK_RECEIPT_CONFLICT"):
        settled.settle(replace(proof, receipt_id="other"))


def test_lookup_foreign_receipt_does_not_trigger_second_effect_or_persist_foreign_result():
    h = setup()
    h.bridge.start.side_effect = TimeoutError("lost")
    execute(h)
    intent = next(iter(h.store.rows.values()))
    h.bridge.lookup.return_value = replace(receipt(intent), operation_key="f" * 64)
    assert execute(h).status == "pending"
    assert h.bridge.start.call_count == 1
    assert next(iter(h.store.rows.values())).receipt is None


def test_same_key_changed_artifact_conflicts_instead_of_new_external_request():
    h = setup()
    execute(h)
    subject = replace(h.request.subject, artifact=ExactRef("other", 1, "f" * 64))
    with pytest.raises(VideoError, match="VIDEO_PLAYBACK_IDEMPOTENCY_CONFLICT"):
        execute(h, replace(h.request, subject=subject))
    assert h.bridge.start.call_count == 1


def test_insert_ack_lost_after_commit_replay_never_guesses_safe_to_dispatch():
    h = setup()
    original_transaction = h.store.transaction
    inserts = []

    @contextmanager
    def lost_commit(org, session):
        before = len(h.store.rows)
        with original_transaction(org, session) as tx:
            yield tx
        if not before and h.store.rows and not inserts:
            inserts.append(True)
            raise RuntimeError("private lost insert commit ACK")

    h.store.transaction = lost_commit
    pending = execute(h)
    assert pending.status == "pending" and len(h.store.rows) == 1
    assert execute(h).status == "pending"
    h.bridge.start.assert_not_called()
    assert h.bridge.lookup.call_count == 1


@pytest.mark.parametrize("phase", ["recover", "record_receipt"])
def test_no_current_access_from_historical_confirmation(phase):
    h = setup()
    if phase == "recover":
        result = execute(h)
        result = execute(h)
    else:
        result = execute(h)
    assert result.status == "confirmed"
    assert not {"access_ref", "capability", "url", "playback_url", "current_state"} & set(
        result.__dataclass_fields__
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"session_revision_after": 4},
        {"session_revision_before": True},
        {"accepted": False, "session_revision_after": 5},
        {"recorded_at": NOW.replace(tzinfo=None)},
        {"authoritative": False},
    ],
)
def test_invalid_receipt_state_or_revision_constructor_rejected(changes):
    h = setup()
    intent = PlaybackIntent("teacher", "key", h.request, NOW)
    with pytest.raises(VideoError):
        receipt(intent, **changes)


def test_native_terminal_state_or_revision_cannot_fake_confirmation():
    h = setup()
    execute(h)
    key, settled = next(iter(h.store.rows.items()))
    h.store.rows[key] = replace_unsafe(settled, {"state": "playing"})
    with pytest.raises(VideoError):
        execute(h)
    assert h.bridge.start.call_count == 1
