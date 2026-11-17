"""Explicit MEMORY/ASSUMED authority tests, not actual Teacher/owner/SQL adoption."""

import copy
from contextlib import contextmanager
from dataclasses import replace
from itertools import count
from types import SimpleNamespace

import pytest

from sketch2life.application.ports.video_review_write import ReviewWriteContext, ReviewWriteSnapshot
from sketch2life.application.video_review_write import VideoReviewWriteService
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_review.model import Decision, Invalidation, ReviewHead
from tests.contract.test_video_review_contract import command
from tests.unit.test_video_review_domain import NOW, subject


class MemoryReviewStore:
    """Snapshot rollback fixture, NOT durable CAS/serialization/authority fences."""

    def __init__(self):
        self.heads, self.receipts, self.history, self.events = {}, {}, [], []
        self.active = False
        self.fail = None

    @contextmanager
    def transaction(self, org, session, video):
        assert not self.active
        before = copy.deepcopy((self.heads, self.receipts, self.history, self.events))
        self.active = True
        self.scope = (org, session, video)
        try:
            yield self
            if self.fail == "commit":
                raise RuntimeError("private commit failure")
        except Exception:
            self.heads, self.receipts, self.history, self.events = before
            raise
        finally:
            self.active = False

    def head(self):
        assert self.active
        return self.heads.get(self.scope)

    def receipt(self, principal, key):
        assert self.active
        return self.receipts.get((*self.scope, principal, key))

    def write(self, before, after, receipt):
        assert self.active
        assert self.head() == before
        self.heads[self.scope] = after
        if self.fail == "head":
            raise RuntimeError("private head failure")
        self.history.append(receipt.entry)
        key = (*self.scope, receipt.context.principal_id, receipt.context.client_key)
        assert key not in self.receipts
        self.receipts[key] = receipt
        if self.fail == "receipt":
            raise RuntimeError("private receipt failure")
        self.events.append((after.entry.review_id, after.revision))


class AssumedReviewBoundary:
    def __init__(self, store):
        self.store = store
        self.initial = ReviewHead(subject(), 1)
        self.held = False
        self.denied = None
        self.calls = []
        self.on_check = None
        self.override = None
        self.fail_exit = False
        self.policy_version = "fixture-review-policy-v1"

    @contextmanager
    def guard(self, ctx):
        if ctx.principal_id not in {"teacher", "teacher2"}:
            raise VideoError("VIDEO_REVIEW_FORBIDDEN")
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("private guard exit")
        finally:
            self.held = False

    def resolve(self, ctx, cmd):
        assert self.held and not self.store.active
        head = self.override or self.store.heads.get(
            (ctx.organization_id, ctx.session_id, ctx.video_id), self.initial
        )
        return ReviewWriteSnapshot(head, self.policy_version)

    def check(self, ctx, cmd, snapshot, phase):
        assert self.held
        self.calls.append((phase, self.store.active))
        if self.on_check:
            self.on_check(ctx, cmd, snapshot, phase)
        if phase == self.denied:
            raise VideoError("VIDEO_REVIEW_FORBIDDEN")


def setup():
    store = MemoryReviewStore()
    boundary = AssumedReviewBoundary(store)
    ids = count(1)
    service = VideoReviewWriteService(
        boundary, store, clock=lambda: NOW, review_ids=lambda: "review." + str(next(ids))
    )
    ctx = ReviewWriteContext("teacher", "school", "session", "video", "key", 1)
    return SimpleNamespace(store=store, boundary=boundary, service=service, context=ctx)


def execute(h, cmd=None, **context):
    return h.service.record(replace(h.context, **context), cmd or command())


@pytest.mark.parametrize("decision", ["approve", "reject", "request_changes"])
def test_exact_shared_record_head_history_receipt_event_committed_together(decision):
    h = setup()
    result = execute(h, command(decision=decision, reason="fixture reason"))
    assert result.record.review_revision == result.current_review_revision == 2
    assert result.record.state == "effective" and not result.replayed
    assert len(h.store.receipts) == len(h.store.history) == len(h.store.events) == 1
    assert next(iter(h.store.heads.values())).entry.decision is Decision(decision)
    assert h.boundary.calls == [("prepare", False), ("commit", True), ("commit", True)]
    assert not h.boundary.held and not h.store.active
    assert not hasattr(result, "url") and not hasattr(result, "playing")


def test_replay_rechecks_current_authority_no_second_review_or_revision_bump():
    h = setup()
    first = execute(h)
    replay = execute(h)
    assert replay.replayed and replay.record == first.record
    assert replay.current_review_revision == 2
    assert len(h.store.history) == len(h.store.events) == 1
    assert h.boundary.calls[-3:] == [("prepare", False), ("replay", True), ("replay", True)]


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_old_approval_replay_after_later_decision_returns_stale_not_effective(decision):
    h = setup()
    first = execute(h)
    execute(
        h,
        command(decision=decision, reason="changes"),
        client_key="new",
        expected_review_revision=2,
    )
    replay = execute(h)
    assert replay.record.review_id == first.record.review_id
    assert replay.record.state == "stale" and replay.current_review_revision == 3
    assert len(h.store.history) == 2
    # Receipt is immutable original fact, not current authorization.
    stored = next(iter(h.store.receipts.values()))
    assert stored.record.state == "effective"


@pytest.mark.parametrize(
    "reason,state",
    [
        (Invalidation.CONTENT_CHANGED, "stale"),
        (Invalidation.USAGE_REVOKED, "revoked"),
    ],
)
def test_historical_receipt_projection_respects_current_head_invalidation(reason, state):
    h = setup()
    execute(h)
    key, head = next(iter(h.store.heads.items()))
    h.store.heads[key] = head.invalidate(head.revision, reason)
    result = execute(h)
    assert result.record.state == state and result.current_review_revision == 3
    with pytest.raises(VideoError, match="VIDEO_REVIEW_TARGET_NOT_CURRENT"):
        execute(h, client_key="new", expected_review_revision=3)


@pytest.mark.parametrize(
    "changes",
    [
        dict(decision="reject", reason="no"),
        dict(reason="another exact text"),
    ],
)
def test_same_key_different_body_conflict_does_not_write(changes):
    h = setup()
    execute(h)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_IDEMPOTENCY_CONFLICT"):
        execute(h, command(**changes))
    assert len(h.store.history) == 1


def test_changed_original_if_match_is_conflict_on_same_key_not_new_review():
    h = setup()
    execute(h)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_IDEMPOTENCY_CONFLICT"):
        execute(h, expected_review_revision=2)
    assert len(h.store.history) == 1


@pytest.mark.parametrize("revision", [2, 7, 99])
def test_stale_job_run_session_revision_cannot_substitute_review_cas(revision):
    h = setup()
    with pytest.raises(VideoError, match="VIDEO_REVIEW_STALE_REVISION"):
        execute(h, expected_review_revision=revision)
    assert not h.store.heads and not h.store.receipts


@pytest.mark.parametrize("actor", ["child", "operator", "unknown"])
def test_only_current_action_authority_not_generic_role_can_review(actor):
    h = setup()
    with pytest.raises(VideoError, match="VIDEO_REVIEW_FORBIDDEN"):
        execute(h, principal_id=actor)
    assert not h.store.receipts


@pytest.mark.parametrize("phase", ["prepare", "commit", "replay"])
def test_current_moderation_consent_grant_denial_before_write_or_on_replay(phase):
    h = setup()
    if phase == "replay":
        execute(h)
    h.boundary.denied = phase
    with pytest.raises(VideoError, match="VIDEO_REVIEW_FORBIDDEN"):
        execute(h)
    assert len(h.store.history) == (1 if phase == "replay" else 0)


def test_revocation_at_last_commit_confirmation_rolls_back_entire_write():
    h = setup()

    def revoke(ctx, cmd, snapshot, phase):
        if phase == "commit" and h.store.history:
            raise VideoError("VIDEO_REVIEW_FORBIDDEN")

    h.boundary.on_check = revoke
    with pytest.raises(VideoError):
        execute(h)
    assert not any((h.store.heads, h.store.receipts, h.store.history, h.store.events))


@pytest.mark.parametrize("failure", ["head", "receipt", "commit"])
def test_partial_write_fault_rolls_back_head_history_receipt_and_outbox(failure):
    h = setup()
    h.store.fail = failure
    with pytest.raises(VideoError, match="^VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE$"):
        execute(h)
    assert not any((h.store.heads, h.store.receipts, h.store.history, h.store.events))


def test_lost_commit_ack_replay_original_receipt_no_second_write():
    h = setup()
    transaction = h.store.transaction
    once = []

    @contextmanager
    def lost_ack(org, session, video):
        with transaction(org, session, video) as tx:
            yield tx
        if not once:
            once.append(True)
            raise RuntimeError("private commit ACK lost")

    h.store.transaction = lost_ack
    with pytest.raises(VideoError, match="VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE"):
        execute(h)
    assert len(h.store.history) == 1
    result = execute(h)
    assert result.replayed and len(h.store.history) == len(h.store.events) == 1


def test_guard_exit_fault_does_not_claim_rollback_or_insert_again():
    h = setup()
    h.boundary.fail_exit = True
    with pytest.raises(VideoError, match="VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE"):
        execute(h)
    assert len(h.store.history) == 1
    h.boundary.fail_exit = False
    assert execute(h).replayed
    assert len(h.store.history) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"organization_id": "foreign"},
        {"session_id": "foreign"},
        {"video_id": "foreign"},
    ],
)
def test_foreign_resolved_scope_cannot_write(changes):
    h = setup()
    with pytest.raises(VideoError, match="VIDEO_REVIEW_SCOPE_MISMATCH"):
        execute(h, **changes)
    assert not h.store.history


@pytest.mark.parametrize(
    "changes",
    [
        {"target_hash": "d" * 64},
        {"target_version": 2},
        {"target_id": "foreign"},
        {"source_context_revision": 3},
    ],
)
def test_exact_target_mismatch_denied_before_transaction_write(changes):
    h = setup()
    with pytest.raises(VideoError, match="VIDEO_REVIEW_TARGET_MISMATCH"):
        execute(h, command(**changes))
    assert not h.store.history


def test_resolved_head_cannot_silently_replace_different_local_canonical_head():
    h = setup()
    execute(h)
    h.boundary.override = h.boundary.initial
    with pytest.raises(VideoError, match="VIDEO_REVIEW_HEAD_NOT_CURRENT"):
        execute(h)
    assert len(h.store.history) == 1


def test_external_head_with_entry_cannot_be_imported_without_own_receipt_history():
    h = setup()
    h.boundary.override = h.boundary.initial.record(
        1, "external", "teacher", Decision.APPROVE, None, NOW
    )
    with pytest.raises(VideoError, match="VIDEO_REVIEW_HEAD_NOT_CURRENT"):
        execute(h)
    assert not h.store.history


def test_actor_keys_are_scoped_no_cross_actor_receipt_disclosure():
    h = setup()
    first = execute(h)
    result = execute(h, principal_id="teacher2", expected_review_revision=2)
    assert not result.replayed and result.record.reviewer_principal_id == "teacher2"
    assert result.record.review_id != first.record.review_id
    assert len(h.store.receipts) == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_review_revision", True),
        ("client_key", "raw/private"),
    ],
)
def test_forged_context_revalidated_before_authority(field, value):
    h = setup()
    forged = copy.deepcopy(h.context)
    object.__setattr__(forged, field, value)
    with pytest.raises(VideoError):
        h.service.record(forged, command())
    assert not h.boundary.calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_version", True),
        ("decision", "play"),
        ("target_hash", "private/url"),
    ],
)
def test_forged_shared_command_revalidated_before_authority(field, value):
    h = setup()
    with pytest.raises(VideoError):
        execute(h, command().model_copy(update={field: value}))
    assert not h.boundary.calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("fingerprint", "f" * 64),
        ("entry", None),
    ],
)
def test_forged_stored_receipt_not_replayed(field, value):
    h = setup()
    execute(h)
    key, receipt = next(iter(h.store.receipts.items()))
    forged = copy.deepcopy(receipt)
    object.__setattr__(forged, field, value)
    h.store.receipts[key] = forged
    with pytest.raises(VideoError):
        execute(h)
    assert len(h.store.history) == 1


def test_set_order_does_not_change_semantic_fingerprint_or_approval_scope():
    h = setup()
    audience = replace(subject().audience, group_ids=("b", "a"))
    h.boundary.initial = ReviewHead(replace(subject(), audience=audience), 1)
    first = command(
        audience_scope={
            "session_id": "session",
            "group_ids": ("b", "a"),
            "participant_ids": ("child",),
        }
    )
    execute(h, first)
    second = first.model_copy(
        update={"audience_scope": first.audience_scope.model_copy(update={"group_ids": ("a", "b")})}
    )
    assert execute(h, second).replayed
    assert len(h.store.history) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"review_revision": True},
        {"review_id": "foreign"},
        {"reviewer_principal_id": "foreign"},
        {"state": "revoked"},
        {"reviewed_at": NOW.replace(tzinfo=None)},
    ],
)
def test_native_shared_receipt_record_must_match_original_entry(changes):
    h = setup()
    execute(h)
    key, receipt = next(iter(h.store.receipts.items()))
    forged = copy.deepcopy(receipt)
    object.__setattr__(forged, "record", receipt.record.model_copy(update=changes))
    h.store.receipts[key] = forged
    with pytest.raises(VideoError):
        execute(h)
    assert len(h.store.history) == 1


def test_current_head_same_revision_with_different_receipt_entry_not_valid_history():
    h = setup()
    execute(h)
    key, receipt = next(iter(h.store.receipts.items()))
    other_entry = replace(receipt.entry, review_id="forged")
    other_record = receipt.record.model_copy(update={"review_id": "forged"})
    h.store.receipts[key] = replace(receipt, entry=other_entry, record=other_record)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_INVALID_RECEIPT"):
        execute(h)


def test_review_write_then_explicit_playback_fixture_only_no_autoplay():
    from tests.unit.test_video_playback import execute as start_playback
    from tests.unit.test_video_playback import setup as playback_setup

    h = setup()
    reviewed = execute(h)
    p = playback_setup()
    assert not p.bridge.start.called
    head = next(iter(h.store.heads.values()))
    p.boundary.head = head
    p.request = replace(
        p.request,
        subject=head.subject,
        review_id=reviewed.record.review_id,
        review_revision=head.revision,
    )
    result = start_playback(p)
    assert result.status == "confirmed"
    assert p.bridge.start.call_count == 1


def test_replay_after_new_exact_subject_cannot_hide_context_change():
    h = setup()
    execute(h)
    original = next(iter(h.store.heads.values()))
    changed = replace(original.subject, pin_digest="f" * 64)
    h.boundary.override = replace(
        original, subject=changed, entry=replace(original.entry, subject=changed)
    )
    with pytest.raises(VideoError, match="VIDEO_REVIEW_HEAD_NOT_CURRENT"):
        execute(h)
    assert len(h.store.history) == 1


def test_explicit_initial_review_revision_from_owner_not_guessed_as_one():
    h = setup()
    h.boundary.initial = ReviewHead(subject(), 8)
    result = execute(h, expected_review_revision=8)
    assert result.current_review_revision == result.record.review_revision == 9
