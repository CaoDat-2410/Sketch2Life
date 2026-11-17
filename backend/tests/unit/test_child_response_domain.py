"""Participant/version state, immutable attribution and exact viewer preconditions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

from sketch2life.domain.child_response import (
    ChildResponseRuleViolation,
    ResponseAction,
    ResponseEntry,
    ResponseTerminal,
    ViewerKey,
    ViewerState,
    transition,
    viewer_etag,
)

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
KEY = ViewerKey("org_fx", "child_a", "proposal_fx", 1)
DIGEST = "a" * 64


def _entry(action: ResponseAction = ResponseAction.VIEWED) -> ResponseEntry:
    return ResponseEntry(
        response_id="response_fx", operation_id="operation_fx", key=KEY, response_revision=2,
        class_id="class_fx", session_id="session_fx", canvas_id="canvas_fx",
        content_sha256=DIGEST, review_ref="review_fx", turn_id="turn_fx", turn_revision=1,
        action=action, responded_at=NOW,
    )


@pytest.mark.parametrize("action", list(ResponseAction))
def test_first_real_choice_advances_virtual_state(action: ResponseAction) -> None:
    initial = ViewerState(KEY)
    entry = _entry(action)
    updated = initial.with_entry(entry)
    assert initial.latest is None and initial.revision == 1
    assert updated.latest is entry and updated.revision == 2


@pytest.mark.parametrize("prior", list(ResponseAction))
@pytest.mark.parametrize("requested", list(ResponseAction))
def test_transition_table(prior: ResponseAction, requested: ResponseAction) -> None:
    state = ViewerState(KEY, 2, _entry(prior))
    if prior is ResponseAction.DECLINED and requested is not prior:
        with pytest.raises(ResponseTerminal):
            transition(state, requested)
    else:
        assert transition(state, requested) is (prior is not requested)


def test_repeat_state_cannot_create_semantic_history() -> None:
    state = ViewerState(KEY, 2, _entry())
    duplicate = replace(_entry(), response_id="another", response_revision=3,
                        operation_id="another_operation", turn_id="later_turn", turn_revision=2)
    with pytest.raises(ChildResponseRuleViolation, match="no-op"):
        state.with_entry(duplicate)


def test_decline_survives_changed_turn_and_review_but_new_version_is_independent() -> None:
    declined = ViewerState(KEY, 2, _entry(ResponseAction.DECLINED))
    later_view = replace(_entry(), response_revision=3, turn_id="later_turn",
                         turn_revision=2, review_ref="later_review")
    with pytest.raises(ResponseTerminal):
        declined.with_entry(later_view)
    new_version = ViewerState(replace(KEY, proposal_version=2))
    assert transition(new_version, ResponseAction.VIEWED)
    assert declined.latest is not None and declined.latest.turn_id == "turn_fx"


def test_viewer_isolation_and_monotonic_revision() -> None:
    initial = ViewerState(KEY)
    with pytest.raises(ChildResponseRuleViolation):
        initial.with_entry(replace(_entry(), key=replace(KEY, participant_id="child_b")))
    with pytest.raises(ChildResponseRuleViolation):
        initial.with_entry(replace(_entry(), response_revision=3))
    with pytest.raises(ChildResponseRuleViolation):
        ViewerState(KEY, 3, _entry())


def test_entries_are_immutable_and_require_real_aware_attribution() -> None:
    entry = _entry()
    with pytest.raises(FrozenInstanceError):
        entry.turn_id = "replacement"  # type: ignore[misc]
    with pytest.raises(ChildResponseRuleViolation):
        replace(entry, responded_at=NOW.replace(tzinfo=None))
    with pytest.raises(ChildResponseRuleViolation):
        replace(entry, response_revision=1)


@pytest.mark.parametrize("change", [
    {"participant_id": "other"}, {"organization_id": "other"},
    {"proposal_id": "other"}, {"proposal_version": 2},
])
def test_etag_binds_viewer_target_identity(change: dict[str, str | int]) -> None:
    other = replace(KEY, **change)  # type: ignore[arg-type]
    assert viewer_etag(other, DIGEST, "review_fx", 1) != viewer_etag(KEY, DIGEST, "review_fx", 1)


def test_etag_binds_content_review_and_local_revision_without_exposing_identity() -> None:
    tag = viewer_etag(KEY, DIGEST, "review_fx", 1)
    assert tag.startswith('"child-response:') and tag.endswith(':1"')
    assert "child_a" not in tag
    assert tag == viewer_etag(KEY, DIGEST, "review_fx", 1)
    assert tag != viewer_etag(KEY, "b" * 64, "review_fx", 1)
    assert tag != viewer_etag(KEY, DIGEST, "other_review", 1)
    assert tag != viewer_etag(KEY, DIGEST, "review_fx", 2)


@pytest.mark.parametrize("revision", [0, -1, True])
def test_invalid_revisions_are_rejected(revision: int) -> None:
    with pytest.raises(ChildResponseRuleViolation):
        replace(KEY, proposal_version=revision)


@pytest.mark.parametrize("invalid", ["", "bad reference", "id\n", "a" * 121])
def test_opaque_references_are_preserved_and_validated(invalid: str) -> None:
    with pytest.raises(ChildResponseRuleViolation):
        replace(KEY, participant_id=invalid)
