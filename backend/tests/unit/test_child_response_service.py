"""CMD-36 authority, accepted acknowledgement and viewer-local state semantics."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.services.child_response import ChildResponseError, ResponseCommand
from sketch2life.contracts.schemas.child_responses import ChildResponseCommandV1
from sketch2life.domain.child_response import ResponseAction
from sketch2life.domain.sketch_review import ModerationOutcome
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    LEVEL,
    ORG,
    OTHER_CLASS_TEACHER,
    TEACHER,
)
from sketch2life.infrastructure.child_response.harness import (
    ChildResponseHarness,
    build_child_response_harness,
)


@pytest.fixture
def h() -> ChildResponseHarness:
    return build_child_response_harness()


def _error(code: str) -> pytest.RaisesExc[ChildResponseError]:
    return pytest.raises(ChildResponseError, match=f"^{code}$")


def _work(h: ChildResponseHarness) -> object:
    chain = h.review.chain
    return deepcopy((chain.generator.calls, chain.generator.requests,
                     chain.h.vision_provider.requests, len(chain.h.job_store.snapshot().jobs),
                     chain.h.queue.messages))


def test_b6_c03_initial_projection_has_no_fake_response_or_storage(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    projection = h.projection(proposal_id)
    assert projection.child_response is None
    assert projection.visibility == "available" and projection.response_revision == 1
    assert projection.turn_id is not None
    assert h.store.snapshot().states == {} and h.store.commits == 0
    assert h.read(proposal_id).payload is not None
    assert h.store.commits == 0


def test_b6_p01_response_is_content_free_and_server_attributed(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    result = h.respond(proposal_id)
    entry = h.store.snapshot().history[0]
    assert result.data.applied and not result.replayed
    assert result.data.child_response.participant_id == CHILD_A
    assert result.data.child_response.turn_id == entry.turn_id
    assert result.data.child_response.responded_at == h.review.chain.h.clock.now()
    assert result.data.response_revision == 2
    value = result.data.model_dump(mode="json")
    assert not {"text_or_question", "overlay_asset_ref", "payload", "target"} & value.keys()
    assert not any(word in json.dumps(value) for word in ("https://", "provider_token"))
    state = h.store.snapshot()
    assert len(state.history) == len(state.receipts) == len(state.audit) == len(state.events) == 1
    assert state.history[0].operation_id == state.audit[0].operation_key.idempotency_key


@pytest.mark.parametrize("action", ["viewed", "hidden", "declined"])
def test_b6_i03_new_key_same_state_is_noop(h: ChildResponseHarness, action: str) -> None:
    proposal_id = h.approved()
    original = h.respond(proposal_id, action)
    before = h.store.snapshot()
    result = h.respond(proposal_id, action)
    after = h.store.snapshot()
    assert not result.data.applied and not result.replayed
    assert result.data.response_id == original.data.response_id
    assert result.data.child_response == original.data.child_response
    assert result.data.etag == original.data.etag
    assert after.states == before.states and after.history == before.history
    assert after.outbox == before.outbox and after.markers == before.markers
    assert len(after.receipts) == len(after.audit) == 2


@pytest.mark.parametrize("action", ["viewed", "hidden", "declined"])
def test_b6_i01_same_key_replay_has_no_new_writes(h: ChildResponseHarness, action: str) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id, action)
    original = h.service.record_response(command)
    before, commits = h.store.snapshot(), h.store.commits
    replay = h.service.record_response(command)
    assert replay.replayed and replay.data == original.data
    assert h.store.snapshot() == before and h.store.commits == commits


def test_b6_i04_closed_turn_and_stale_etag_replay_original_receipt(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    result = h.service.record_response(command)
    assert result.data.etag != command.if_match
    h.close_turn()
    before = h.store.snapshot()
    replay = h.service.record_response(command)
    assert replay.replayed and replay.data == result.data
    assert h.store.snapshot() == before
    with _error("SKETCH_UNAVAILABLE"):
        h.service.record_response(replace(command, idempotency_key="new_key_after_closed_turn"))
    with _error("SKETCH_UNAVAILABLE"):
        h.read(proposal_id)


def test_b6_i02_changed_payload_still_conflicts_after_turn_close(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    h.service.record_response(command)
    assert not isinstance(command.body, str | bytes)
    changed = replace(command, body=command.body.model_copy(update={"action": "hidden"}))
    h.close_turn()
    with _error("IDEMPOTENCY_PAYLOAD_MISMATCH"):
        h.service.record_response(changed)
    assert len(h.store.snapshot().history) == 1


@pytest.mark.parametrize("change", ["grant", "review", "binding"])
def test_b6_i05_replay_requires_current_disclosure(h: ChildResponseHarness, change: str) -> None:
    proposal_id = h.approved(group=True)
    command = h.command(proposal_id, principal=DEVICE_GA)
    h.service.record_response(command)
    if change == "grant":
        h.revoke_grant(DEVICE_GA)
    elif change == "review":
        h.revoke_review(proposal_id)
    else:
        h.rebind(DEVICE_GA, CHILD_B, "turn_fx_rebound_b")
    before = h.store.snapshot()
    with _error("SKETCH_UNAVAILABLE"):
        h.service.record_response(command)
    assert h.store.snapshot() == before


def test_b6_i06_old_receipt_cannot_restore_later_hidden_state(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    original = h.service.record_response(command)
    hidden = h.respond(proposal_id, "hidden")
    replay = h.service.record_response(command)
    assert replay.data == original.data
    assert h.projection(proposal_id).visibility == "hidden"
    assert h.read(proposal_id).payload is None
    assert h.projection(proposal_id).etag == hidden.data.etag
    assert len(h.store.snapshot().history) == 2


def test_b6_c06_command_whitespace_property_order_is_canonical(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    assert not isinstance(command.body, str | bytes)
    body = command.body.model_dump(mode="json")
    first = replace(command, body=json.dumps(body, indent=3))
    reverse = replace(command, body=json.dumps(dict(reversed(list(body.items())))).encode())
    expected = h.service.record_response(first)
    replay = h.service.record_response(reverse)
    assert replay.replayed and replay.data == expected.data


@pytest.mark.parametrize("field,value", [("action", "hidden"), ("turn_id", "turn_fx_other"),
                                        ("expected_proposal_version", 2),
                                        ("review_ref", "review_fx_other")])
def test_b6_i02_semantic_field_change_conflicts(
    h: ChildResponseHarness, field: str, value: object,
) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    h.service.record_response(command)
    assert not isinstance(command.body, str | bytes)
    changed = replace(command, body=command.body.model_copy(update={field: value}))
    with _error("IDEMPOTENCY_PAYLOAD_MISMATCH"):
        h.service.record_response(changed)
    assert len(h.store.snapshot().receipts) == 1


@pytest.mark.parametrize("bad_key", [None, "", "contains space", "a" * 121])
def test_invalid_operation_key_has_no_success(h: ChildResponseHarness, bad_key: str | None) -> None:
    proposal_id = h.approved()
    command = replace(h.command(proposal_id), idempotency_key=bad_key)
    with _error("FIELD_VALIDATION_FAILED"):
        h.service.record_response(command)
    assert not h.store.snapshot().receipts


def test_b6_n03_raw_unknown_identity_fields_rejected(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    assert not isinstance(command.body, str | bytes)
    body = {**command.body.model_dump(mode="json"), "participant_id": CHILD_B}
    with _error("FIELD_NOT_ALLOWED"):
        h.service.record_response(replace(command, body=json.dumps(body)))
    assert not h.store.snapshot().receipts


def test_b6_n07_missing_if_match_only_blocks_unseen_mutation(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id, etag=None)
    with _error("PRECONDITION_REQUIRED"):
        h.service.record_response(command)
    assert not h.store.snapshot().history
    accepted = replace(command, if_match=h.projection(proposal_id).etag)
    expected = h.service.record_response(accepted)
    assert h.service.record_response(command).data == expected.data


@pytest.mark.parametrize("tag", ['"wrong-family"', '"child-response:guess:1"'])
def test_b6_n08_stale_or_foreign_etag(h: ChildResponseHarness, tag: str) -> None:
    proposal_id = h.approved()
    with _error("STALE_AGGREGATE"):
        h.respond(proposal_id, etag=tag)
    assert not h.store.snapshot().history


def test_b6_n08_another_participant_etag_is_rejected(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True)
    tag = h.projection(proposal_id, DEVICE_GA).etag
    with _error("STALE_AGGREGATE"):
        h.respond(proposal_id, principal=DEVICE_GB, etag=tag)
    assert not h.store.snapshot().history


def test_b6_n09_decline_survives_new_turn_and_review(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True, participants=(CHILD_A,))
    original = h.respond(proposal_id, "declined", principal=DEVICE_GA)
    h.rebind(DEVICE_GA, CHILD_A, "turn_fx_later_a")
    h.review.review(proposal_id, participants=(CHILD_A, CHILD_B))
    for action in ("viewed", "hidden"):
        with _error("RESPONSE_TERMINAL"):
            h.respond(proposal_id, action, principal=DEVICE_GA)
    duplicate = h.respond(proposal_id, "declined", principal=DEVICE_GA)
    assert not duplicate.data.applied
    assert duplicate.data.child_response == original.data.child_response
    assert duplicate.data.review_ref != original.data.review_ref
    assert h.read(proposal_id, DEVICE_GA, explicit_reveal=True).payload is None
    assert len(h.store.snapshot().history) == 1


def test_b6_i03_noop_under_later_turn_preserves_original_attribution(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    original = h.respond(proposal_id, "hidden")
    h.rebind(DEVICE_A, CHILD_A, "turn_fx_next_a")
    result = h.respond(proposal_id, "hidden")
    assert result.data.child_response == original.data.child_response
    assert h.store.snapshot().audit[-1].turn_id == "turn_fx_next_a"
    assert h.store.snapshot().history[0].turn_id != "turn_fx_next_a"


def test_b6_p02_explicit_reveal_does_not_itself_record_view(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    h.respond(proposal_id, "hidden")
    before = h.store.snapshot()
    assert h.read(proposal_id).payload is None
    revealed = h.read(proposal_id, explicit_reveal=True)
    assert revealed.payload is not None and revealed.projection.visibility == "hidden"
    assert h.store.snapshot() == before
    h.respond(proposal_id)
    assert h.projection(proposal_id).visibility == "viewed"
    assert len(h.store.snapshot().events) == 2


def test_b6_c02_teacher_scope_and_event_replay(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id, "declined")
    h.service.record_response(command)
    h.service.record_response(command)
    event, = h.teacher_events()
    assert event.action == "declined" and event.access.participant_id == CHILD_A
    assert event.turn_id == h.store.snapshot().history[0].turn_id
    assert event.response_id == h.store.snapshot().history[0].response_id
    assert h.teacher_events(OTHER_CLASS_TEACHER) == ()
    assert h.teacher_events(DEVICE_A) == ()
    assert h.teacher_events(Principal("admin_fx", ORG, PrincipalRole.ADMIN)) == ()
    h.authority.revoked.add(TEACHER.principal_id)
    assert h.teacher_events() == ()


def test_b6_n06_inactive_owner_session_cannot_use_independently_allowed05(
    h: ChildResponseHarness, monkeypatch: pytest.MonkeyPatch,
) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    observed = h.access.authorize(DEVICE_A, proposal_id)
    read = h.access.read(DEVICE_A, proposal_id)
    assert observed is not None and read is not None
    # Model independently observed owner facts: the public access fixture still returns
    # its earlier allowed result, while the device authority now sees inactive CanvasFacts.
    monkeypatch.setattr(h.access, "authorize", lambda *args, **kwargs: observed)
    monkeypatch.setattr(h.access, "read", lambda *args, **kwargs: read)
    h.set_session_active(False)
    assert h.access.authorize(DEVICE_A, proposal_id) is not None
    with _error("SKETCH_UNAVAILABLE"):
        h.service.record_response(command)
    with _error("SKETCH_UNAVAILABLE"):
        h.read(proposal_id)
    assert not h.store.snapshot().history


def test_closed_owner_session_denies_current_review_without_erasing_receipt(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    h.service.record_response(command)
    before = h.store.snapshot()
    h.set_session_active(False)
    # The actual 05 producer adapter revalidates owner session state. The explicit
    # exact-review disclosure policy therefore denies this receipt, unlike turn-only close.
    with _error("SKETCH_UNAVAILABLE"):
        h.service.record_response(command)
    assert h.store.snapshot() == before
    assert h.store.snapshot().history[0].action is ResponseAction.VIEWED


def test_b6_i05_old_version_receipt_and_unseen_old_command_deny_after_replacement(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    old_command = h.command(proposal_id, "declined")
    h.service.record_response(old_command)
    h.new_version(proposal_id, LEVEL)
    before, work = h.store.snapshot(), _work(h)
    for command in (old_command, replace(old_command, idempotency_key="old_version_new_key")):
        with _error("SKETCH_UNAVAILABLE"):
            h.service.record_response(command)
    fresh = h.projection(proposal_id)
    assert fresh.access.proposal_version == 2 and fresh.child_response is None
    assert h.store.snapshot() == before and _work(h) == work


@pytest.mark.parametrize("reason", ["pending", "blocked", "stale", "rejected", "missing"])
def test_b6_n01_actual_ineligible_states_share_denial_without_generation(
    h: ChildResponseHarness, reason: str,
) -> None:
    proposal_id = h.pending(unsafe=reason == "blocked")
    if reason in {"blocked", "rejected"}:
        assessment = h.review.service.moderate(TEACHER, proposal_id)
        assert assessment.outcome is (
            ModerationOutcome.BLOCKED if reason == "blocked" else ModerationOutcome.PASSED)
    if reason == "rejected":
        rejected = h.review.review(proposal_id, "reject")
        assert rejected.data["decision"] == "reject"
    elif reason == "stale":
        h.review.moderate(proposal_id)
        h.review.review(proposal_id)
        assert h.read(proposal_id).payload is not None
        h.review.revoke_producer_consent()
        assert h.review.target(proposal_id).pipeline_state == "stale"
    elif reason == "missing":
        proposal_id = "sketch_fx_missing"
    work = _work(h)
    command = ResponseCommand(
        DEVICE_A, proposal_id, "denied_new_key", '"child-response:untrusted:1"',
        ChildResponseCommandV1(action="viewed", expected_proposal_version=1,
                               review_ref="review_fx_guess", turn_id="turn_fx_a1"))
    with _error("SKETCH_UNAVAILABLE"):
        h.read(proposal_id)  # no guessed review selector: exercises actual owner eligibility
    with _error("SKETCH_UNAVAILABLE"):
        h.service.record_response(command)
    assert not h.store.snapshot().history and not h.store.snapshot().events
    assert not h.store.snapshot().receipts and _work(h) == work


@pytest.mark.parametrize("change", ["review", "grant", "version"])
def test_b6_n04_unseen_key_after_real_invalidation_has_no_work(
    h: ChildResponseHarness, change: str,
) -> None:
    proposal_id = h.approved()
    command = h.command(proposal_id)
    if change == "review":
        h.revoke_review(proposal_id)
    elif change == "grant":
        h.revoke_grant()
    else:
        h.new_version(proposal_id, LEVEL)
    before, work = h.store.snapshot(), _work(h)
    with _error("SKETCH_UNAVAILABLE"):
        h.service.record_response(command)
    assert h.store.snapshot() == before and _work(h) == work


def test_b6_p02_restoring_a_does_not_change_b_viewer_state(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True)
    h.respond(proposal_id, "hidden", principal=DEVICE_GA)
    h.respond(proposal_id, principal=DEVICE_GB)
    before_b = h.projection(proposal_id, DEVICE_GB)
    h.read(proposal_id, DEVICE_GA, explicit_reveal=True)
    h.respond(proposal_id, principal=DEVICE_GA)
    assert h.projection(proposal_id, DEVICE_GB) == before_b
    assert h.projection(proposal_id, DEVICE_GA).visibility == "viewed"
