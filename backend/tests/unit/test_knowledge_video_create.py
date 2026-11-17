"""Guarded create + process-local transaction fixture, not actual foundation SQL."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from sketch2life.application.knowledge_video_create import VideoCreateService
from sketch2life.application.ports.knowledge_video import VideoRequestContext
from sketch2life.contracts.schemas.knowledge_video import CreateKnowledgeVideo, VideoExactRef
from sketch2life.domain.knowledge_video.model import ExactRef, Strategy, VideoError, VideoPin
from sketch2life.infrastructure.knowledge_video.fakes import (
    FixtureAtomicVideoSubmission,
    FixtureVideoOwner,
)

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def ref(name):
    return ExactRef(name, 1, "a" * 64)


def setup(strategy=Strategy.GENERATE):
    p = VideoPin(
        "school", "session", ref("bundle"), 0, 0, 0, (ref("source"),), strategy,
        ref("profile"), ref("encoding"), ref("rights"), ref("retry"), ref("policy"), 1,
        ref("model") if strategy is Strategy.GENERATE else None,
        ref("library") if strategy is not Strategy.GENERATE else None
    )
    owner = FixtureVideoOwner(p)
    store = FixtureAtomicVideoSubmission(NOW)
    context = VideoRequestContext("teacher", "school", "session", "key", "correlation")
    body = CreateKnowledgeVideo(bundle_id="bundle", bundle_version=1,
                                bundle_hash="a" * 64, audience_context_revision=0,
                                strategy=strategy.value)
    return VideoCreateService(owner, store), owner, store, context, body


@pytest.mark.parametrize("strategy", list(Strategy))
def test_all_strategies_only_submit_intents_not_generated_media(strategy):
    service, owner, store, context, body = setup(strategy)
    result = service.create(context, body)
    assert result.outcome == "created"
    assert result.run.artifact is None
    assert result.run.generation_state == "queued"
    assert len(store.runs) == len(store.job_intents) == len(store.dispatch_intents) == 1
    assert len(store.audit_intents) == 1
    assert "FIXTURE_ONLY" in store.marker
    assert not owner.active


def test_replay_rechecks_rights_and_does_not_dispatch_twice():
    service, owner, store, context, body = setup()
    first = service.create(context, body)
    second = service.create(context, body)
    assert second.outcome == "replayed"
    assert second.run == first.run
    assert len(store.receipts) == len(store.dispatch_intents) == 1
    owner.allowed_principals.clear()
    with pytest.raises(VideoError, match="VIDEO_FORBIDDEN"):
        service.create(context, body)
    assert not owner.active


def test_semantic_dedup_for_other_key_and_authorized_teacher():
    service, owner, store, context, body = setup()
    first = service.create(context, body)
    owner.allowed_principals.add("teacher2")
    other = replace(context, principal_id="teacher2", idempotency_key="key2")
    second = service.create(other, body)
    assert second.outcome == "deduplicated"
    assert second.run == first.run
    assert len(store.receipts) == 2
    assert len(store.runs) == len(store.dispatch_intents) == 1


def test_same_key_different_body_conflicts_even_if_same_resolved_profile():
    service, _, store, context, body = setup()
    service.create(context, body)
    changed = body.model_copy(update={"requested_profile_ref": VideoExactRef(
        ref="profile", version=1, hash="a" * 64
    )})
    with pytest.raises(VideoError, match="VIDEO_IDEMPOTENCY_CONFLICT"):
        service.create(context, changed)
    assert len(store.runs) == len(store.receipts) == 1


def test_old_key_cannot_rewrite_original_policy_pin():
    service, owner, store, context, body = setup()
    first = service.create(context, body)
    owner.pin = replace(owner.pin, policy_epoch=2)
    with pytest.raises(VideoError, match="VIDEO_STALE_CONTEXT"):
        service.create(context, body)
    assert store.runs[first.run.video_id].pin.policy_epoch == 1
    assert len(store.dispatch_intents) == 1


@pytest.mark.parametrize("field,value", [
    ("organization_id", "other"), ("session_id", "other"),
    ("bundle", ExactRef("bundle", 2, "a" * 64)),
    ("bundle", ExactRef("bundle", 1, "b" * 64)),
    ("audience_revision", 1),
])
def test_resolver_cannot_substitute_scope_source_or_audience(field, value):
    service, owner, store, context, body = setup()
    owner.pin = replace(owner.pin, **{field: value})
    with pytest.raises(VideoError, match="VIDEO_RESOLUTION_MISMATCH"):
        service.create(context, body)
    assert not store.runs


@pytest.mark.parametrize("field", ["requested_profile_ref", "candidate_library_asset_ref"])
def test_explicit_candidate_ref_cannot_be_silently_replaced(field):
    service, _, store, context, body = setup(Strategy.REVIEWED_LIBRARY)
    changed = body.model_copy(update={field: VideoExactRef(
        ref="other", version=1, hash="a" * 64
    )})
    with pytest.raises(VideoError, match="VIDEO_RESOLUTION_MISMATCH"):
        service.create(context, changed)
    assert not store.runs


def test_fault_before_commit_has_no_partial_fixture_intent():
    service, _, store, context, body = setup()

    def fail():
        raise RuntimeError("synthetic storage failure")

    store.before_commit = fail
    with pytest.raises(RuntimeError):
        service.create(context, body)
    assert not any((store.runs, store.semantic, store.receipts, store.job_intents,
                    store.dispatch_intents, store.audit_intents))
    store.before_commit = None
    assert service.create(context, body).outcome == "created"


def test_lease_change_before_commit_rolls_back_fixture_effects():
    service, owner, store, context, body = setup()
    store.before_commit = lambda: store.revoke_for_test(owner)
    with pytest.raises(VideoError, match="VIDEO_STALE_CONTEXT"):
        service.create(context, body)
    assert not any((store.runs, store.receipts, store.job_intents, store.dispatch_intents))


def test_parallel_same_key_one_intent_process_local_only():
    service, _, store, context, body = setup()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: service.create(context, body), range(24)))
    assert len({result.run.video_id for result in results}) == 1
    assert sum(result.outcome == "created" for result in results) == 1
    assert len(store.receipts) == len(store.dispatch_intents) == 1


def test_parallel_distinct_keys_semantic_dedup_process_local_only():
    service, _, store, context, body = setup()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda i: service.create(
            replace(context, idempotency_key=f"key{i}"), body
        ), range(24)))
    assert len({result.run.video_id for result in results}) == 1
    assert sum(result.outcome == "created" for result in results) == 1
    assert len(store.receipts) == 24
    assert len(store.dispatch_intents) == 1


def test_source_set_order_dedup_does_not_fail_after_receipt_commit():
    service, owner, store, context, body = setup()
    owner.pin = replace(owner.pin, sources=(ref("source"), ref("source2")))
    first = service.create(context, body)
    owner.pin = replace(owner.pin, sources=tuple(reversed(owner.pin.sources)))
    assert service.create(context, body).run == first.run
    assert service.create(replace(context, idempotency_key="other"), body).run == first.run
    assert len(store.runs) == 1


def test_closed_lease_is_not_a_reusable_authority_token():
    _, owner, _, context, body = setup()
    with owner.hold(context, body) as lease:
        lease.assert_current()
    with pytest.raises(VideoError, match="VIDEO_LEASE_CLOSED"):
        lease.assert_current()
    with owner.hold(context, body) as new_lease:
        new_lease.assert_current()
        with pytest.raises(VideoError, match="VIDEO_LEASE_CLOSED"):
            lease.assert_current()


def test_valid_lease_cannot_submit_for_another_context():
    _, owner, store, context, body = setup()
    with (owner.hold(context, body) as lease,
          pytest.raises(VideoError, match="VIDEO_RESOLUTION_MISMATCH")):
        store.submit(context=replace(context, principal_id="someone.else"),
                     command_hash="a" * 64, lease=lease)
    assert not store.runs
