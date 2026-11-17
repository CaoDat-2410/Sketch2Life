"""MEMORY/ASSUMED port conformance, not actual durable cross-owner effects."""

from contextlib import contextmanager
from dataclasses import replace

import pytest

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_failure.model import Action
from tests.video_failure_fixtures import choice, context, harness, receipt


@pytest.mark.parametrize("action", list(Action))
def test_three_explicit_actions_intent_before_bridge_one_effect_and_replay(action):
    h = harness()
    first = h.service.decide(context(), choice(action))
    assert first.receipt is not None and len(h.store.history) == len(h.store.events) == 2
    assert h.service.decide(context(), choice(action)) == first
    assert h.bridge.execute.call_count == 1 and not h.store.active and not h.boundary.held
    assert h.boundary.calls[:5] == [
        ("prepare", False),
        ("commit_intent", True),
        ("commit_intent", True),
        ("dispatch", False),
        ("record_receipt", False),
    ]
    assert first.target.state is JobState.FAILED_EXHAUSTED


@pytest.mark.parametrize("action", list(Action))
@pytest.mark.parametrize("phase", ["prepare", "commit_intent", "dispatch"])
def test_current_denial_stops_effect_with_transaction_rollback(action, phase):
    h = harness()
    h.boundary.denied = phase
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.decide(context(), choice(action))
    assert len(h.store.rows) == (1 if phase == "dispatch" else 0)
    h.bridge.execute.assert_not_called()


@pytest.mark.parametrize("principal", ["child", "device", "admin"])
def test_no_implicit_teacher_role(principal):
    h = harness()
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.decide(context(principal_id=principal), choice())
    assert not h.store.rows


@pytest.mark.parametrize("field", ["organization_id", "session_id", "video_id"])
def test_foreign_scope_no_effect(field):
    h = harness()
    with pytest.raises(VideoError, match="FORBIDDEN|SCOPE_MISMATCH"):
        h.service.decide(context(**{field: "foreign"}), choice())
    assert not h.store.rows


@pytest.mark.parametrize(
    "field",
    [
        "expected_video_version",
        "expected_job_revision",
        "expected_run_revision",
        "expected_session_revision",
    ],
)
def test_independent_stale_preconditions(field):
    h = harness()
    with pytest.raises(VideoError, match="STALE_TARGET|STALE_SESSION"):
        h.service.decide(context(), choice(**{field: 99}))
    assert not h.store.rows


def test_budget_note_no_grant_and_concurrent_policy_stop_blocks_dispatch():
    h = harness()
    h.boundary.retry_allowed = False
    with pytest.raises(VideoError, match="RETRY_NOT_AUTHORIZED"):
        h.service.decide(context(), choice(Action.RETRY, retry_authorization_note="please"))
    h.boundary.retry_allowed = True

    def kill(i, phase):
        if phase == "dispatch":
            h.boundary.retry_allowed = False

    h.boundary.on_check = kill
    with pytest.raises(VideoError, match="RETRY_NOT_AUTHORIZED"):
        h.service.decide(context(), choice(Action.RETRY))
    assert len(h.store.rows) == 1
    h.bridge.execute.assert_not_called()


@pytest.mark.parametrize("action", list(Action))
def test_timeout_replay_original_lookup_never_auto_redispatch(action):
    h = harness()
    h.bridge.execute.side_effect = TimeoutError("synthetic_sensitive")
    pending = h.service.decide(context(), choice(action))
    assert pending.receipt is None
    assert h.service.decide(context(), choice(action)) == pending
    assert h.bridge.execute.call_count == h.bridge.lookup.call_count == 1
    h.bridge.lookup.return_value = receipt(pending)
    result = h.service.decide(context(), choice(action))
    assert result.receipt is not None and h.bridge.execute.call_count == 1
    assert len(h.store.history) == 2


@pytest.mark.parametrize("action", list(Action))
@pytest.mark.parametrize(
    "field,value",
    [
        ("operation_key", "f" * 64),
        ("request_digest", "f" * 64),
        ("target_digest", "f" * 64),
        ("principal_id", "foreign"),
    ],
)
def test_foreign_receipts_do_not_confirm(action, field, value):
    h = harness()
    h.bridge.execute.side_effect = lambda i: receipt(i, **{field: value})
    result = h.service.decide(context(), choice(action))
    assert result.receipt is None and len(h.store.history) == 1


def test_end_partial_checkpoint_is_pending_no_guessed_success_or_compensation():
    h = harness()
    h.bridge.execute.side_effect = lambda i: receipt(i, checkpoint_ref=None)
    result = h.service.decide(context(), choice(Action.END))
    assert result.receipt is None
    assert h.bridge.method_calls[0][0] == "execute" and len(h.bridge.method_calls) == 1


@pytest.mark.parametrize("action", list(Action))
def test_one_failure_winner_across_actors_actions_and_keys(action):
    h = harness()
    h.service.decide(context(), choice())
    with pytest.raises(VideoError, match="CONFLICT"):
        h.service.decide(context(principal_id="teacher2", client_key="different"), choice(action))
    assert len(h.store.claims) == len(h.store.rows) == h.bridge.execute.call_count == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason", "different"),
        ("action", Action.END),
        ("expected_session_revision", 5),
        ("expected_run_revision", 8),
    ],
)
def test_same_key_changed_body_or_etag_conflict_not_new_effect(field, value):
    h = harness()
    h.service.decide(context(), choice())
    with pytest.raises(VideoError, match="IDEMPOTENCY_CONFLICT"):
        h.service.decide(context(), choice(**{field: value}))
    assert h.bridge.execute.call_count == 1


@pytest.mark.parametrize("stage", ["insert", "commit"])
def test_intent_failure_no_dispatch_and_whole_uow_rollback(stage):
    h = harness()
    if stage == "commit":
        # Avoid failing the preceding read transaction.
        h.boundary.on_check = lambda i, p: (
            setattr(h.store, "fail", "commit") if (p == "commit_intent") else None
        )
    else:
        h.store.fail = stage
    with pytest.raises(VideoError, match="DEPENDENCY_UNAVAILABLE"):
        h.service.decide(context(), choice())
    assert not h.store.rows and not h.store.claims and not h.store.history
    h.bridge.execute.assert_not_called()


def test_committed_insert_ack_lost_recover_never_guesses_absence_safe_to_send():
    h = harness()
    original = h.store.transaction
    lost = []

    @contextmanager
    def transaction(org, session):
        had_rows = bool(h.store.rows)
        with original(org, session) as tx:
            yield tx
        if not had_rows and h.store.rows and not lost:
            lost.append(True)
            raise RuntimeError("synthetic_sensitive")

    h.store.transaction = transaction
    with pytest.raises(VideoError, match="DEPENDENCY_UNAVAILABLE"):
        h.service.decide(context(), choice())
    assert len(h.store.rows) == 1
    assert h.service.decide(context(), choice()).receipt is None
    h.bridge.execute.assert_not_called()


def test_confirmed_recovery_uses_original_failure_not_current_replacement():
    h = harness()
    first = h.service.decide(context(), choice())
    h.boundary.target = replace(h.boundary.target, job_id="different.job")
    assert h.service.decide(context(), choice()) == first
    h.boundary.denied = "recover"
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.decide(context(), choice())
    assert h.bridge.execute.call_count == 1


def test_receipt_save_failure_retains_original_pending_then_reconciles():
    h = harness()
    h.store.fail = "save"
    pending = h.service.decide(context(), choice())
    assert pending.receipt is None and len(h.store.history) == 1
    h.store.fail = None
    h.bridge.lookup.return_value = receipt(pending)
    assert h.service.decide(context(), choice()).receipt is not None
    assert h.bridge.execute.call_count == 1


def test_guard_exit_lost_after_effect_reports_unavailable_not_rollback():
    h = harness()
    h.boundary.fail_exit = True
    with pytest.raises(VideoError, match="DEPENDENCY_UNAVAILABLE"):
        h.service.decide(context(), choice())
    assert next(iter(h.store.rows.values())).receipt is not None
    h.boundary.fail_exit = False
    assert h.service.decide(context(), choice()).receipt is not None
    assert h.bridge.execute.call_count == 1


def test_source_changes_before_dispatch_blocks_old_effect():
    h = harness()
    h.boundary.on_check = lambda i, phase: (
        setattr(h.boundary, "target", replace(h.boundary.target, audience_revision=99))
        if phase == "dispatch"
        else None
    )
    with pytest.raises(VideoError, match="STALE_TARGET"):
        h.service.decide(context(), choice())
    h.bridge.execute.assert_not_called()


def test_lookup_outage_stays_pending_and_malformed_native_not_trusted():
    h = harness()
    h.bridge.execute.side_effect = TimeoutError()
    pending = h.service.decide(context(), choice())
    h.bridge.lookup.side_effect = RuntimeError("synthetic_sensitive")
    assert h.service.decide(context(), choice()) == pending
    key, value = next(iter(h.store.rows.items()))
    object.__setattr__(value, "revision", True)
    h.store.rows[key] = value
    with pytest.raises(VideoError):
        h.service.decide(context(), choice())


@pytest.mark.parametrize("action", list(Action))
def test_synthetic08_exhausted_projection_preserves_failed_row_and_late_result_rejected(action):
    from sketch2life.domain.knowledge_video.model import VideoRun
    from tests.unit.test_knowledge_video_worker import harness as render_fixture

    ready = render_fixture().finalized.video_run
    # Constructor fixture only; actual08/01 failure owner adapter remains CR10-01.
    failed = VideoRun(
        "video",
        2,
        7,
        1,
        "old.job",
        ready.pin,
        ready.created_at,
        generation_state=JobState.FAILED_EXHAUSTED,
        attempt_id="attempt",
    )
    h = harness()
    h.boundary.target = replace(
        h.boundary.target, pin_digest=failed.pin.digest(), policy=failed.pin.policy
    )
    result = h.service.decide(context(), choice(action))
    assert result.receipt is not None
    assert failed.generation_state is JobState.FAILED_EXHAUSTED and failed.run_revision == 7
    assert failed.artifact is None and failed.review_revision == 1
    with pytest.raises(VideoError):
        failed.finalize(7, "attempt", ready.artifact)
    assert [call[0] for call in h.bridge.method_calls] == ["execute"]
