"""Pure rule evidence only, not actual failed source or retry/session authority."""

from dataclasses import replace

import pytest

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_failure.model import Action
from tests.video_failure_fixtures import (
    NOW,
    authorization,
    choice,
    context,
    intent,
    receipt,
    ref,
    target,
)


@pytest.mark.parametrize("action", list(Action))
def test_exact_original_intent_settlement_and_immutable_failure(action):
    i = intent(action)
    result = i.settle(receipt(i))
    assert result.revision == 2 and result.receipt.action is action
    assert result.target == i.target and i.receipt is None and i.revision == 1
    assert result.settle(result.receipt) == result
    if action is Action.RETRY:
        assert result.receipt.new_lifecycle.video_id != i.target.video_id
        assert result.receipt.new_lifecycle.job_id != i.target.job_id
        assert result.receipt.new_lifecycle.review_state == "pending_media"
    else:
        assert result.receipt.new_lifecycle is None
    assert not hasattr(result, "approved") and not hasattr(result, "playback_url")


@pytest.mark.parametrize("state", [s for s in JobState if s is not JobState.FAILED_EXHAUSTED])
def test_no_other_state_is_exhaustion(state):
    with pytest.raises(VideoError, match="VIDEO_NOT_EXHAUSTED"):
        target(state=state)


@pytest.mark.parametrize(
    "field,value",
    [
        ("video_version", True),
        ("run_revision", 0),
        ("job_revision", "9"),
        ("pin_digest", "url"),
        ("history_digest", "wrong"),
        ("attempt_id", "private/url"),
        ("failure_ref", None),
        ("exhausted_at", NOW.replace(tzinfo=None)),
    ],
)
def test_invalid_failure_target(field, value):
    with pytest.raises(VideoError):
        target(**{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason", " "),
        ("reason", "x" * 201),
        ("action", "skip"),
        ("expected_video_version", True),
        ("expected_job_revision", 0),
        ("expected_run_revision", True),
        ("expected_session_revision", -1),
        ("retry_authorization_note", "override grant"),
    ],
)
def test_strict_choice_and_note_not_a_nonretry_grant(field, value):
    with pytest.raises(VideoError):
        choice(**{field: value})


@pytest.mark.parametrize(
    "field", ["expected_video_version", "expected_run_revision", "expected_job_revision"]
)
def test_independent_expected_revisions_not_interchangeable(field):
    with pytest.raises(VideoError, match="STALE_TARGET"):
        intent(choice=choice(**{field: 55}))


@pytest.mark.parametrize("field", ["organization_id", "session_id", "video_id"])
def test_scope_from_exact_owner_target(field):
    with pytest.raises(VideoError, match="SCOPE_MISMATCH"):
        intent(context=context(**{field: "foreign"}))


@pytest.mark.parametrize(
    "changes",
    [
        {"authorization": None},
        {"authorization": authorization(expires_at=NOW)},
        {"authorization": authorization(principal_id="foreign")},
        {"authorization": authorization(target_digest="f" * 64)},
        {"authorization": authorization(policy=ref("foreign"))},
    ],
)
def test_retry_requires_exact_current_authorization(changes):
    with pytest.raises(VideoError, match="RETRY_NOT_AUTHORIZED"):
        intent(Action.RETRY, **changes)


@pytest.mark.parametrize(
    "field,value",
    [
        ("disposition_id", "foreign"),
        ("operation_key", "f" * 64),
        ("request_digest", "f" * 64),
        ("target_digest", "f" * 64),
        ("principal_id", "foreign"),
        ("session_revision_before", 3),
        ("video_run_revision", 99),
        ("recorded_at", NOW.replace(year=2025)),
    ],
)
def test_receipt_exact_binding(field, value):
    i = intent()
    with pytest.raises(VideoError, match="RECEIPT_MISMATCH"):
        i.settle(receipt(i, **{field: value}))


def test_end_requires_checkpoint_not_partial_early_success():
    with pytest.raises(VideoError, match="INVALID_RECEIPT"):
        receipt(intent(Action.END), checkpoint_ref=None)
    with pytest.raises(VideoError):
        receipt(intent(Action.SKIP), checkpoint_ref=ref("not.end"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("authorization_ref", None),
        ("budget_consumption_ref", None),
        ("new_lifecycle", None),
        ("checkpoint_ref", ref("forbidden")),
    ],
)
def test_retry_receipt_requires_consumption_and_new_lifecycle(field, value):
    with pytest.raises(VideoError):
        receipt(intent(Action.RETRY), **{field: value})


@pytest.mark.parametrize(
    "field,value", [("video_id", "video"), ("job_id", "old.job"), ("video_version", 99)]
)
def test_retry_cannot_reset_old_lifecycle_or_change_content(field, value):
    i = intent(Action.RETRY)
    r = receipt(i)
    with pytest.raises(VideoError, match="RECEIPT_MISMATCH"):
        i.settle(replace(r, new_lifecycle=replace(r.new_lifecycle, **{field: value})))


def test_key_claim_request_material_have_different_purposes():
    i = intent()
    other = intent(Action.END)
    assert i.context.operation_key() == other.context.operation_key()
    assert i.digest() != other.digest()
    assert i.target.claim_key() == replace(i.target, job_revision=99).claim_key()
    assert i.target.digest() != replace(i.target, job_revision=99).digest()
    assert replace(i.context, video_id="foreign").operation_key() == i.context.operation_key()
    assert replace(i.context, principal_id="other").operation_key() != i.context.operation_key()


def test_no_terminal_receipt_overwrite_or_explicit_note_grant():
    i = intent()
    settled = i.settle(receipt(i))
    with pytest.raises(VideoError, match="RECEIPT_CONFLICT"):
        settled.settle(receipt(i, receipt_id="other"))
    with pytest.raises(VideoError, match="RETRY_NOT_AUTHORIZED"):
        intent(
            Action.RETRY,
            choice=choice(Action.RETRY, retry_authorization_note="approved"),
            authorization=None,
        )
