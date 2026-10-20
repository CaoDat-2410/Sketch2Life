"""MEMORY/ASSUMED owner invalidation and rebind; not SQL or actual access revocation."""

import copy
from contextlib import contextmanager
from dataclasses import replace
from itertools import count
from types import SimpleNamespace

import pytest

from sketch2life.application.ports.video_review_lifecycle import ReviewChangeReceipt
from sketch2life.application.ports.video_review_write import ReviewWriteContext
from sketch2life.application.video_review_lifecycle import VideoReviewLifecycleService
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.domain.video_review.lifecycle import (
    ReviewChange,
    ReviewChangeAction,
    ReviewChangeRequest,
)
from sketch2life.domain.video_review.model import Applicability, Decision, Invalidation
from tests.contract.test_video_review_contract import command
from tests.unit.test_video_review_domain import NOW, approved, subject
from tests.unit.test_video_review_write import MemoryReviewStore
from tests.unit.test_video_review_write import setup as write_setup


def rebind(target=None, reason=Invalidation.CONTENT_CHANGED):
    return ReviewChangeRequest(
        ReviewChangeAction.REBIND,
        reason,
        target
        or replace(
            subject(),
            video_version=2,
            artifact=ExactRef("next.asset", 1, "d" * 64),
            pin_digest="d" * 64,
        ),
    )


def invalidate(reason=Invalidation.CONTENT_CHANGED):
    return ReviewChangeRequest(ReviewChangeAction.INVALIDATE, reason)


def change(request=None, head=None):
    head = head or approved()
    return ReviewChange.create("event", "teacher", head, request or rebind(), head.revision, NOW)


def test_rebind_archives_exact_old_entry_and_never_copies_approval():
    event = change()
    assert event.archived.entry == event.before.entry
    assert event.archived.applicability is Applicability.STALE
    assert not event.archived.permits_intent(event.archived.subject)
    assert event.after.entry is None and event.after.revision == event.before.revision + 1
    assert event.after.applicability is Applicability.EFFECTIVE
    assert not event.after.permits_intent(event.after.subject)
    assert event.before.permits_intent(event.before.subject)  # Immutable historical snapshot.


@pytest.mark.parametrize("reason", list(Invalidation))
def test_invalidation_keeps_prior_decision_no_fabricated_playback_stop(reason):
    event = change(invalidate(reason))
    assert event.after == event.archived
    assert event.after.entry == event.before.entry
    assert not event.after.permits_intent(event.after.subject)
    assert not hasattr(event, "player_stopped")


def test_revocation_strengthens_stale_head_and_cannot_downgrade_revoked():
    stale = change(invalidate()).after
    revoked = change(invalidate(Invalidation.USAGE_REVOKED), stale)
    assert revoked.after.applicability is Applicability.REVOKED
    assert revoked.after.entry == stale.entry
    assert revoked.after.revision == stale.revision + 1
    with pytest.raises(VideoError):
        change(invalidate(), revoked.after)


@pytest.mark.parametrize("reason", list(Invalidation))
def test_rebind_from_invalidated_preserves_archive_but_requires_fresh_review(reason):
    stale = change(invalidate(reason)).after
    event = change(rebind(), stale)
    assert event.archived == stale
    assert event.after.revision == stale.revision + 1 and event.after.entry is None
    assert not event.after.permits_intent(event.after.subject)


@pytest.mark.parametrize(
    "changes",
    [
        {"organization_id": "foreign"},
        {"video_id": "foreign"},
        {"audience": replace(subject().audience, session_id="foreign")},
    ],
)
def test_cross_scope_change_rejected(changes):
    with pytest.raises(VideoError, match="VIDEO_REVIEW_SCOPE_MISMATCH"):
        change(rebind(replace(subject(), **changes)))


@pytest.mark.parametrize(
    "changes",
    [
        {"video_version": 1},
        {"source_context_revision": 0},
        {"audience": replace(subject().audience, audience_revision=0)},
    ],
)
def test_version_context_audience_cannot_go_backward(changes):
    old = replace(
        subject(),
        video_version=2,
        source_context_revision=2,
        audience=replace(subject().audience, audience_revision=2),
    )
    head = replace(approved(), subject=old, entry=replace(approved().entry, subject=old))
    with pytest.raises(VideoError, match="VIDEO_REVIEW_BACKWARD_CHANGE"):
        change(rebind(replace(old, **changes)), head)


@pytest.mark.parametrize(
    "changes",
    [
        {"artifact": ExactRef("edited", 1, "d" * 64)},
        {"pin_digest": "d" * 64},
    ],
)
def test_editing_media_or_script_without_new_content_version_rejected(changes):
    with pytest.raises(VideoError, match="VIDEO_REVIEW_NEW_CONTENT_VERSION_REQUIRED"):
        change(rebind(replace(subject(), **changes)))


def test_context_or_audience_change_same_bytes_still_requires_new_review():
    target = replace(subject(), source_context_revision=1)
    event = change(rebind(target, Invalidation.CONTEXT_CHANGED))
    assert event.after.subject.artifact == event.before.subject.artifact
    assert event.after.entry is None
    audience = replace(subject().audience, participant_ids=("newchild",), audience_revision=1)
    event = change(rebind(replace(subject(), audience=audience), Invalidation.AUDIENCE_CHANGED))
    assert event.after.entry is None


@pytest.mark.parametrize("reason", [Invalidation.CONTEXT_CHANGED, Invalidation.AUDIENCE_CHANGED])
def test_reason_must_match_actual_changed_context_or_audience(reason):
    with pytest.raises(VideoError, match="VIDEO_REVIEW_CHANGE_REASON_MISMATCH"):
        change(rebind(replace(subject(), video_version=2), reason))


def test_unchanged_subject_cannot_be_rebound_to_clear_approval_or_revocation():
    with pytest.raises(VideoError, match="VIDEO_REVIEW_CHANGE_REQUIRED"):
        change(rebind(subject()))


@pytest.mark.parametrize(
    "action,reason,target",
    [
        ("rebind", Invalidation.CONTENT_CHANGED, subject()),
        (ReviewChangeAction.REBIND, "content_changed", subject()),
        (ReviewChangeAction.INVALIDATE, Invalidation.CONTENT_CHANGED, subject()),
        (ReviewChangeAction.REBIND, Invalidation.CONTENT_CHANGED, None),
    ],
)
def test_native_change_shape_invalidity(action, reason, target):
    with pytest.raises(VideoError):
        ReviewChangeRequest(action, reason, target)


class LifecycleMemoryStore(MemoryReviewStore):
    def __init__(self):
        super().__init__()
        self.changes, self.archives = {}, []
        self.fail_change = None

    @contextmanager
    def transaction(self, org, session, video):
        before = copy.deepcopy((self.changes, self.archives))
        try:
            with super().transaction(org, session, video) as tx:
                yield tx
        except Exception:
            self.changes, self.archives = before
            raise

    def receipt(self, principal, key):
        if (*self.scope, principal, key) in self.changes:
            raise VideoError("VIDEO_REVIEW_IDEMPOTENCY_CONFLICT")
        return super().receipt(principal, key)

    def change_receipt(self, principal, key):
        assert self.active
        if (*self.scope, principal, key) in self.receipts:
            raise VideoError("VIDEO_REVIEW_IDEMPOTENCY_CONFLICT")
        return self.changes.get((*self.scope, principal, key))

    def change(self, receipt):
        assert self.active and self.head() == receipt.change.before
        key = (*self.scope, receipt.context.principal_id, receipt.context.client_key)
        assert key not in self.changes and key not in self.receipts
        self.archives.append(receipt.change)
        self.heads[self.scope] = receipt.change.after
        if self.fail_change == "head":
            raise RuntimeError("private head fault")
        self.changes[key] = receipt
        if self.fail_change == "receipt":
            raise RuntimeError("private receipt fault")
        self.events.append((receipt.change.event_id, receipt.change.after.revision))


class AssumedChangeBoundary:
    def __init__(self, store):
        self.store, self.calls = store, []
        self.held = False
        self.denied = None
        self.on_check = None
        self.fail_exit = False
        self.override = None

    @contextmanager
    def guard(self, ctx):
        if ctx.principal_id != "teacher":
            raise VideoError("VIDEO_REVIEW_FORBIDDEN")
        self.held = True
        try:
            yield self
            if self.fail_exit:
                raise RuntimeError("private exit fault")
        finally:
            self.held = False

    def resolve(self, ctx, request):
        assert self.held and not self.store.active
        return (
            self.override or self.store.heads[(ctx.organization_id, ctx.session_id, ctx.video_id)]
        )

    def check(self, receipt, phase):
        assert self.held
        self.calls.append((phase, self.store.active))
        if self.on_check:
            self.on_check(receipt, phase)
        if phase == self.denied:
            raise VideoError("VIDEO_REVIEW_FORBIDDEN")


def setup():
    store = LifecycleMemoryStore()
    store.heads["school", "session", "video"] = approved()
    boundary = AssumedChangeBoundary(store)
    ids = count(1)
    service = VideoReviewLifecycleService(
        boundary, store, clock=lambda: NOW, event_ids=lambda: "change." + str(next(ids))
    )
    ctx = ReviewWriteContext("teacher", "school", "session", "video", "change-key", 2)
    return SimpleNamespace(store=store, boundary=boundary, service=service, context=ctx)


def execute(h, request=None, **context):
    return h.service.apply(replace(h.context, **context), request or rebind())


def test_guarded_change_atomic_history_current_head_receipt_and_event_fixture():
    h = setup()
    result = execute(h)
    assert result.applied_review_revision == 3 and not result.replayed
    assert len(h.store.changes) == len(h.store.archives) == len(h.store.events) == 1
    assert h.store.heads["school", "session", "video"].entry is None
    assert h.boundary.calls == [("prepare", False), ("commit", True), ("commit", True)]
    assert not hasattr(result, "playback_url") and not hasattr(result, "approved")


def test_replay_original_change_after_newer_review_does_not_clear_or_repeat_it():
    h = setup()
    result = execute(h)
    current = h.store.heads["school", "session", "video"]
    h.store.heads["school", "session", "video"] = current.record(
        3, "new-review", "teacher", Decision.APPROVE, None, NOW
    )
    replay = execute(h)
    assert replay.replayed and replay.event_id == result.event_id
    assert replay.applied_review_revision == 3  # Historical receipt, NOT current revision4.
    assert h.store.heads["school", "session", "video"].revision == 4
    assert len(h.store.events) == 1


@pytest.mark.parametrize(
    "changed_request", [invalidate(), rebind(replace(subject(), video_version=3))]
)
def test_same_key_changed_action_or_target_conflict_no_new_event(changed_request):
    h = setup()
    execute(h)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_IDEMPOTENCY_CONFLICT"):
        execute(h, changed_request)
    assert len(h.store.events) == 1


@pytest.mark.parametrize("phase", ["prepare", "commit", "replay"])
def test_current_owner_denial_no_change_or_replay_disclosure(phase):
    h = setup()
    if phase == "replay":
        execute(h)
    h.boundary.denied = phase
    with pytest.raises(VideoError, match="VIDEO_REVIEW_FORBIDDEN"):
        execute(h)
    assert len(h.store.events) == (1 if phase == "replay" else 0)


def test_revoked_source_requires_current_new_target_authority_not_old_approval():
    h = setup()
    h.store.heads["school", "session", "video"] = change(
        invalidate(Invalidation.USAGE_REVOKED)
    ).after
    h.boundary.denied = "prepare"
    with pytest.raises(VideoError, match="VIDEO_REVIEW_FORBIDDEN"):
        execute(h, expected_review_revision=3)
    assert h.store.heads["school", "session", "video"].applicability is Applicability.REVOKED


@pytest.mark.parametrize("failure", ["head", "receipt", "commit"])
def test_change_partial_write_rolls_back_entire_head_history_receipt_event(failure):
    h = setup()
    if failure == "commit":
        h.store.fail = failure
    else:
        h.store.fail_change = failure
    with pytest.raises(VideoError, match="VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE"):
        execute(h)
    assert h.store.heads["school", "session", "video"] == approved()
    assert not h.store.changes and not h.store.archives and not h.store.events


def test_late_revocation_rolls_back_no_published_partial_rebind():
    h = setup()

    def revoke(receipt, phase):
        if phase == "commit" and h.store.events:
            raise VideoError("VIDEO_REVIEW_FORBIDDEN")

    h.boundary.on_check = revoke
    with pytest.raises(VideoError):
        execute(h)
    assert not h.store.changes and h.store.heads["school", "session", "video"] == approved()


def test_stale_current_head_snapshot_rejected_by_cas_not_overwritten():
    h = setup()
    h.boundary.override = approved()
    h.store.heads["school", "session", "video"] = change(invalidate()).after
    with pytest.raises(VideoError, match="VIDEO_REVIEW_HEAD_NOT_CURRENT"):
        execute(h)
    assert not h.store.events


def test_lost_commit_ack_recovers_original_event_without_resetting_new_review():
    h = setup()
    transaction = h.store.transaction
    lost = []

    @contextmanager
    def lose_ack(org, session, video):
        with transaction(org, session, video) as tx:
            yield tx
        if h.store.changes and not lost:
            lost.append(True)
            raise RuntimeError("private lost ACK")

    h.store.transaction = lose_ack
    with pytest.raises(VideoError, match="VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE"):
        execute(h)
    assert execute(h).replayed and len(h.store.events) == 1


def test_guard_exit_error_preserves_committed_event_for_recovery():
    h = setup()
    h.boundary.fail_exit = True
    with pytest.raises(VideoError, match="VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE"):
        execute(h)
    h.boundary.fail_exit = False
    assert execute(h).replayed and len(h.store.events) == 1


def test_rebind_new_version_then_review_via_existing_write_component_no_approval_copy():
    h = setup()
    execute(h)
    head = h.store.heads["school", "session", "video"]
    assert not head.permits_intent(head.subject)
    write = write_setup()
    write.store = h.store
    write.boundary.store = h.store
    write.service._store = h.store
    cmd = command(target_version=head.subject.video_version, target_hash=head.subject.artifact.hash)
    result = write.service.record(replace(write.context, expected_review_revision=3), cmd)
    assert result.record.review_revision == 4 and result.record.state == "effective"
    assert h.store.heads["school", "session", "video"].permits_intent(head.subject)
    assert h.store.archives[0].archived.entry.review_id == "review"


def test_review_and_change_key_namespace_cannot_execute_two_kinds_of_write():
    h = setup()
    execute(h)
    write = write_setup()
    write.service._store = h.store
    write.boundary.store = h.store
    head = h.store.heads["school", "session", "video"]
    with pytest.raises(VideoError, match="VIDEO_REVIEW_IDEMPOTENCY_CONFLICT"):
        write.service.record(
            replace(write.context, client_key="change-key", expected_review_revision=3),
            command(target_version=2, target_hash=head.subject.artifact.hash),
        )


@pytest.mark.parametrize("field,value", [("revision", True), ("applicability", "effective")])
def test_native_change_head_forgery_not_saved(field, value):
    h = setup()
    forged = copy.deepcopy(h.store.heads["school", "session", "video"])
    object.__setattr__(forged, field, value)
    h.boundary.override = forged
    with pytest.raises(VideoError):
        execute(h)
    assert not h.store.events


def test_forged_event_after_head_cannot_copy_historical_approval():
    original = change()
    bad = replace(
        original.after,
        entry=replace(
            original.before.entry, subject=original.after.subject, revision=original.after.revision
        ),
    )
    with pytest.raises(VideoError, match="VIDEO_REVIEW_INVALID_CHANGE"):
        replace(original, after=bad)


def test_receipt_scope_and_expected_revision_match_original_change():
    event = change()
    ctx = setup().context
    assert ReviewChangeReceipt(ctx, event.request, event)
    with pytest.raises(VideoError):
        ReviewChangeReceipt(replace(ctx, expected_review_revision=3), event.request, event)


def test_old_review_cannot_start_playback_after_new_version_or_revocation():
    from tests.unit.test_video_playback import execute as start_playback
    from tests.unit.test_video_playback import setup as playback_setup

    for notice in (rebind(), invalidate(Invalidation.USAGE_REVOKED)):
        h = setup()
        execute(h, notice)
        p = playback_setup()
        p.boundary.head = h.store.heads["school", "session", "video"]
        with pytest.raises(VideoError, match="VIDEO_PLAYBACK_REVIEW_NOT_EFFECTIVE"):
            start_playback(p)
        p.bridge.start.assert_not_called()


def test_content_reason_cannot_describe_audience_only_change():
    audience = replace(subject().audience, audience_revision=1)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_CHANGE_REASON_MISMATCH"):
        change(rebind(replace(subject(), audience=audience)))


def test_existing_review_key_cannot_be_reused_for_lifecycle_operation():
    h = setup()
    write = write_setup()
    write.boundary.store = h.store
    write.service._store = h.store
    write.service.record(replace(write.context, expected_review_revision=2), command())
    with pytest.raises(VideoError, match="VIDEO_REVIEW_IDEMPOTENCY_CONFLICT"):
        execute(h, client_key="key", expected_review_revision=3)
    assert not h.store.changes


@pytest.mark.parametrize(
    "changes",
    [
        {"expected_review_revision": True},
        {"client_key": "private/url"},
    ],
)
def test_invalid_native_context_rejected_without_owner_or_storage_side_effect(changes):
    h = setup()
    forged = copy.deepcopy(h.context)
    for field, value in changes.items():
        object.__setattr__(forged, field, value)
    with pytest.raises(VideoError):
        h.service.apply(forged, rebind())
    assert not h.boundary.calls and not h.store.events


def test_corrupted_stored_change_receipt_cannot_be_replayed_as_completed():
    h = setup()
    execute(h)
    key, receipt = next(iter(h.store.changes.items()))
    forged = copy.deepcopy(receipt)
    object.__setattr__(forged.change.after, "revision", True)
    h.store.changes[key] = forged
    with pytest.raises(VideoError):
        execute(h)
    assert len(h.store.events) == 1


def test_missing_local_head_is_not_bootstrapped_by_importing_external_history():
    h = setup()
    h.boundary.override = approved()
    h.store.heads.clear()
    with pytest.raises(VideoError, match="VIDEO_REVIEW_HEAD_NOT_CURRENT"):
        execute(h)
    assert not h.store.events


@pytest.mark.parametrize("reason", list(Invalidation))
def test_owner_authorized_same_content_restore_requires_new_empty_head_and_review(reason):
    prior = change(invalidate(reason)).after
    reopened = change(rebind(prior.subject, reason), prior)
    assert reopened.archived == prior and reopened.after.entry is None
    assert reopened.after.revision == prior.revision + 1
    assert not reopened.after.permits_intent(prior.subject)
    fresh = reopened.after.record(
        reopened.after.revision, "fresh", "teacher", Decision.APPROVE, None, NOW
    )
    assert fresh.entry.review_id != prior.entry.review_id
    assert fresh.permits_intent(prior.subject)


def test_policy_epoch_pin_change_not_guessed_as_media_edit_needing_new_video_version():
    target = replace(subject(), pin_digest="f" * 64)
    event = change(rebind(target, Invalidation.CONTEXT_CHANGED))
    assert event.after.subject.video_version == event.before.subject.video_version
    assert event.after.entry is None


def test_actual_new_target_guard_denial_still_blocks_same_content_reopen():
    h = setup()
    prior = change(invalidate(Invalidation.USAGE_REVOKED)).after
    h.store.heads["school", "session", "video"] = prior
    h.boundary.denied = "prepare"
    with pytest.raises(VideoError, match="VIDEO_REVIEW_FORBIDDEN"):
        execute(h, rebind(prior.subject, Invalidation.USAGE_REVOKED), expected_review_revision=3)
    assert h.store.heads["school", "session", "video"] == prior
