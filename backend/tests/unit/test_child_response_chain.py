"""Actual producer -> exact Teacher review -> independent Child response fixtures."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from sketch2life.application.services.child_response import ChildResponseError
from sketch2life.infrastructure.assistance.harness import (
    ADMIN,
    CHILD_A,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    LEVEL,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    TEACHER,
)
from sketch2life.infrastructure.child_response.examples import build_child_response_examples
from sketch2life.infrastructure.child_response.harness import (
    ChildResponseHarness,
    build_child_response_harness,
)


@pytest.fixture
def h() -> ChildResponseHarness:
    return build_child_response_harness()


def test_real_chain_choice_preserves_source_producer_review_and_job_counters(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    chain = h.review.chain
    before = deepcopy((
        chain.h.owner.canvases, chain.h.source_p, chain.h.source_g,
        chain.h.sources.sources, chain.service.get_record(TEACHER, proposal_id),
        h.review.store.snapshot(), chain.generator.calls, chain.generator.requests,
        chain.h.vision_provider.requests, chain.h.job_store.snapshot().jobs,
        chain.h.queue.messages, chain.h.queue.delivered,
    ))
    initial = h.read(proposal_id)
    assert initial.payload is not None
    assert initial.projection.child_response is None
    assert initial.projection.response_revision == 1
    viewed = h.respond(proposal_id)
    h.respond(proposal_id, "hidden")
    assert h.read(proposal_id).payload is None
    assert h.read(proposal_id, explicit_reveal=True).payload is not None
    h.respond(proposal_id, "viewed")
    declined = h.respond(proposal_id, "declined")
    assert viewed.data.child_response.action == "viewed"
    assert declined.data.child_response.action == "declined"
    assert h.read(proposal_id, explicit_reveal=True).payload is None
    after = (
        chain.h.owner.canvases, chain.h.source_p, chain.h.source_g,
        chain.h.sources.sources, chain.service.get_record(TEACHER, proposal_id),
        h.review.store.snapshot(), chain.generator.calls, chain.generator.requests,
        chain.h.vision_provider.requests, chain.h.job_store.snapshot().jobs,
        chain.h.queue.messages, chain.h.queue.delivered,
    )
    assert after == before
    assert chain.service.get_record(TEACHER, proposal_id)["child_response"] is None
    assert len(h.store.snapshot().history) == len(h.teacher_events()) == 4


def test_two_reviewed_children_keep_independent_choices_and_turns(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True)
    hidden_a = h.respond(proposal_id, "hidden", principal=DEVICE_GA)
    viewed_b = h.respond(proposal_id, "viewed", principal=DEVICE_GB)
    assert hidden_a.data.participant_id != viewed_b.data.participant_id
    assert hidden_a.data.child_response.turn_id == "turn_fx_ga"
    assert viewed_b.data.child_response.turn_id == "turn_fx_gb"
    assert h.read(proposal_id, DEVICE_GA).payload is None
    assert h.read(proposal_id, DEVICE_GB).payload is not None
    h.respond(proposal_id, "declined", principal=DEVICE_GA)
    assert h.projection(proposal_id, DEVICE_GB).visibility == "viewed"


def test_subset_review_does_not_publish_group_content_to_unreviewed_child(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved(group=True, participants=(CHILD_A,))
    assert h.read(proposal_id, DEVICE_GA).payload is not None
    with pytest.raises(ChildResponseError, match="SKETCH_UNAVAILABLE"):
        h.read(proposal_id, DEVICE_GB)
    assert not h.store.snapshot().history


def test_hide_reveal_is_explicit_and_does_not_record_rendering_proof(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    hidden = h.respond(proposal_id, "hidden")
    before = h.store.snapshot()
    reveal = h.read(proposal_id, explicit_reveal=True)
    assert reveal.payload is not None and reveal.projection.visibility == "hidden"
    assert h.store.snapshot() == before
    acknowledged = h.respond(proposal_id)
    assert acknowledged.data.child_response.action == "viewed"
    assert acknowledged.data.response_revision == hidden.data.response_revision + 1
    assert "rendered" not in acknowledged.data.model_dump_json()


def test_decline_stays_terminal_after_rebinding_same_participant(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    declined = h.respond(proposal_id, "declined")
    h.rebind(DEVICE_A, CHILD_A, "turn_fx_a2")
    assert h.projection(proposal_id).visibility == "declined"
    assert h.read(proposal_id, explicit_reveal=True).payload is None
    with pytest.raises(ChildResponseError, match="RESPONSE_TERMINAL"):
        h.respond(proposal_id, "viewed")
    duplicate = h.respond(proposal_id, "declined")
    assert not duplicate.data.applied
    assert duplicate.data.response_id == declined.data.response_id
    assert duplicate.data.child_response.turn_id == "turn_fx_a1"
    assert len(h.teacher_events()) == 1


def test_new_approved_version_is_independent_of_old_decline(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    declined = h.respond(proposal_id, "declined")
    h.new_version(proposal_id, LEVEL)
    fresh = h.read(proposal_id)
    assert fresh.payload is not None
    assert fresh.projection.access.proposal_version == 2
    assert fresh.projection.child_response is None
    assert fresh.projection.response_revision == 1
    assert h.store.snapshot().history[0].response_id == declined.data.response_id
    assert len(h.store.snapshot().markers) == 1


def test_closed_turn_replay_preserves_receipt_but_new_content_or_response_is_denied(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    accepted = h.service.record_response(command)
    before = h.store.snapshot()
    h.close_turn()
    replay = h.service.record_response(replace(command, if_match='"child-response:stale"'))
    assert replay.replayed and replay.data == accepted.data
    assert h.store.snapshot() == before
    with pytest.raises(ChildResponseError, match="SKETCH_UNAVAILABLE"):
        h.read(proposal_id)
    with pytest.raises(ChildResponseError, match="SKETCH_UNAVAILABLE"):
        h.service.record_response(replace(command, idempotency_key=h.key()))


@pytest.mark.parametrize("revoke", ["review", "grant"])
def test_revoke_blocks_original_receipt_and_all_future_reads(
    h: ChildResponseHarness, revoke: str,
) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    h.service.record_response(command)
    if revoke == "review":
        h.revoke_review(proposal_id)
    else:
        h.revoke_grant()
    before = h.store.snapshot()
    with pytest.raises(ChildResponseError, match="SKETCH_UNAVAILABLE"):
        h.service.record_response(command)
    with pytest.raises(ChildResponseError, match="SKETCH_UNAVAILABLE"):
        h.read(proposal_id)
    assert h.store.snapshot() == before


def test_teacher_event_consumer_is_currently_scoped_and_content_free(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    acknowledged = h.respond(proposal_id)
    events = h.teacher_events()
    assert len(events) == 1 and events[0].response_id == acknowledged.data.response_id
    target = h.review.target(proposal_id)
    serialized = events[0].model_dump_json()
    for forbidden in ("text_or_question", "overlay_asset_ref", "producer", "job_id",
                      "assessment", "deficit", "http"):
        assert forbidden not in serialized
    assert target.text is None or target.text not in serialized
    for principal in (ADMIN, OTHER_CLASS_TEACHER, OUTSIDER, DEVICE_A):
        assert h.teacher_events(principal) == ()
    h.authority.teachers.pop(TEACHER.principal_id)
    assert h.teacher_events() == ()


def test_fixture_examples_are_deterministic_and_preserve_receipt_identity() -> None:
    first = build_child_response_examples()
    assert first == build_child_response_examples()
    examples = first["examples"]
    assert isinstance(examples, dict)
    assert examples["initial_read"]["projection"]["child_response"] is None
    assert examples["hidden_passive_read"]["payload"] is None
    assert examples["declined_read"]["payload"] is None
    assert examples["closed_turn_replay"]["replayed"] is True
    assert examples["closed_turn_replay"]["data"] == examples["declined_receipt"]


def test_published_synthetic_examples_match_actual_producer_values() -> None:
    fixture = (Path(__file__).resolve().parents[3] / "features" / "FEAT-055-be2-child-response"
               / "artifacts" / "CHILD_RESPONSE_EXAMPLES.json")
    assert json.loads(fixture.read_text(encoding="utf-8")) == build_child_response_examples()
