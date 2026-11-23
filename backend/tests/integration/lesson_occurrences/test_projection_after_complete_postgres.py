"""V4-A T-1c-fix: the class projection of a sample after Teacher Complete, on PostgreSQL (owner
decision C1(a); recorded departure DEV-5 from SRS l.1672 and l.1676 for an unclaimed sample).

SRS l.396 (the playable sample claims the slot), l.552 (FR-T-13: the slot never reopens), l.777,
l.1449, l.1661-1662 (no confirmation, no projection token), l.1672 and l.1676 (Complete is valid
only at ``VIDEO_READY``; the token is for the current artifact), OD-14 (the claim is the first
projection confirmation). T-4b2 OPEN-2 asked what a sample completed before projection should do;
the owner chose option (a): the confirmation and the token are allowed on a ``COMPLETED`` run that
still holds its READY output while the slot is ``AVAILABLE``; the slot is still claimed at the first
projection confirmation. A confirmation given BEFORE Complete still ends at Complete, and a claimed
completed sample is not confirmed again. Runs only against a disposable database whose name
contains ``be1_acceptance`` and ``frc08``. The helpers and fixtures are those of
``test_projection_postgres.py``.
"""

# ruff: noqa: F401, F811  (the fixtures are imported for pytest and used as test arguments)

from __future__ import annotations

from uuid import uuid4

from tests.integration.lesson_occurrences.test_projection_postgres import (
    CLAIM_ACTION,
    CONFIRM_ACTION,
    VEnv,
    api,
    assert_untouched,
    audit_rows,
    complete,
    confirm,
    confirmed_sample,
    env,
    occurrence_row,
    playback_token,
    projection_token,
    ready_sample,
    revision_of,
    set_class_state,
    stream,
    streams,
    update_occurrence,
    v,
)


def test_complete_then_confirm_claims_the_slot_and_the_class_can_watch(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    assert before["sample_slot_state"] == "AVAILABLE"
    assert complete(e, "t1", run_id).status_code == 200
    assert_untouched(before, e, occurrence_id)  # Complete never touches the slot (FR-T-13)
    # no confirmation yet: no projection token
    assert projection_token(e, "t1", occurrence_id).status_code == 409
    response = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["run_id"] == run_id and body["generation_id"] == generation_id
    after = occurrence_row(e.d, occurrence_id)
    assert (after["sample_slot_state"], after["state"]) == ("CLAIMED", "SAMPLE_USED")
    assert after["successful_sample_run_ref"] == run_id
    assert after["class_projection_confirmed_at"] is not None
    rows = [(row.action, row.actor_ref) for row in audit_rows(e, occurrence_id)]
    assert rows.count((CONFIRM_ACTION, e.d.accounts["t1"])) == 1
    assert rows.count((CLAIM_ACTION, e.d.accounts["t1"])) == 1
    issued = projection_token(e, "t1", occurrence_id)
    assert issued.status_code == 200, issued.text
    token = str(issued.json()["token"])
    assert streams(stream(e, "t1", run_id, token))
    ranged = stream(e, "t1", run_id, token, byte_range="bytes=0-9")
    assert ranged.status_code == 206 and len(ranged.content) == 10
    # the Teacher's own preview of the completed run follows the same rule as a Parent's replay
    own = playback_token(e, "t1", run_id)
    assert own.status_code == 200
    assert streams(stream(e, "t1", run_id, own.json()["playback"]["token"]))
    # a retry with a new key (a lost answer) behaves as on a VIDEO_READY run: 200, nothing written
    again = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert again.status_code == 200, again.text
    assert occurrence_row(e.d, occurrence_id) == after
    assert len(audit_rows(e, occurrence_id)) == 2  # one confirm and one claim, no new row
    assert streams(stream(e, "t1", run_id, token))  # the token it did not end


def test_a_confirmation_before_complete_ends_at_complete_and_cannot_be_given_again(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, token = confirmed_sample(v)
    claimed = occurrence_row(e.d, occurrence_id)
    assert streams(stream(e, "t1", run_id, token))
    assert complete(e, "t1", run_id).status_code == 200
    # the projection grant ended at Complete (today's rule, kept)
    assert stream(e, "t1", run_id, token).status_code == 404
    refused = projection_token(e, "t1", occurrence_id)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    # ... and a second confirmation is refused: the owner decision covers an AVAILABLE slot only
    again = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert again.status_code == 409 and again.json()["code"] == "INVALID_STATE_TRANSITION"
    after = occurrence_row(e.d, occurrence_id)
    assert after["sample_slot_state"] == "CLAIMED" and after["state"] == "SAMPLE_USED"
    assert after["successful_sample_run_ref"] == run_id
    assert after["sample_claimed_at"] == claimed["sample_claimed_at"]
    assert after["class_projection_confirmed_at"] == claimed["class_projection_confirmed_at"]
    # the Teacher's own view of the completed run still plays (not a class projection)
    own = playback_token(e, "t1", run_id)
    assert own.status_code == 200
    assert streams(stream(e, "t1", run_id, own.json()["playback"]["token"]))
    rows = [(row.action, row.actor_ref) for row in audit_rows(e, occurrence_id)]
    assert rows.count((CLAIM_ACTION, e.d.accounts["t1"])) == 1  # never claimed twice


def test_a_completed_sample_of_a_claimed_slot_is_refused_with_the_slot_error(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, _token = confirmed_sample(v)
    assert complete(e, "t1", run_id).status_code == 200
    # the claim was kept by a run that has since been deleted: the pointer is emptied (l.396), or
    # another run holds it; the completed sample is never confirmed for a claimed slot
    for pointer in (None, str(uuid4())):
        update_occurrence(e, occurrence_id, successful_sample_run_ref=pointer)
        before = occurrence_row(e.d, occurrence_id)
        response = confirm(e, "t1", occurrence_id, run_id, generation_id)
        assert response.status_code == 409
        assert response.json()["code"] == "SAMPLE_VIDEO_ALREADY_EXISTS"
        assert_untouched(before, e, occurrence_id)
        assert before["sample_slot_state"] == "CLAIMED"
        assert projection_token(e, "t1", occurrence_id).status_code == 409


def test_a_stale_pair_and_a_suspended_class_refuse_the_projection_of_a_completed_sample(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    assert complete(e, "t1", run_id).status_code == 200
    before = occurrence_row(e.d, occurrence_id)
    wrong = confirm(e, "t1", occurrence_id, run_id, "00000000-0000-4000-8000-000000000000")
    assert wrong.status_code == 409 and wrong.json()["code"] == "STALE_REVISION"
    set_class_state(e, "suspended")
    try:
        refused = confirm(e, "t1", occurrence_id, run_id, generation_id)
        assert refused.status_code == 409
        assert refused.json()["code"] == "INVALID_STATE_TRANSITION"
    finally:
        set_class_state(e, "active")
    assert_untouched(before, e, occurrence_id)
    assert not audit_rows(e, occurrence_id)
    # the class is active again: the same confirmation now claims the slot
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 200


def test_only_the_responsible_teacher_can_project_a_completed_sample(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    assert complete(e, "t1", run_id).status_code == 200
    before = occurrence_row(e.d, occurrence_id)
    for who in ("parent", "t2", "stranger", "manager"):
        assert confirm(e, who, occurrence_id, run_id, generation_id).status_code == 404, who
        assert projection_token(e, who, occurrence_id).status_code == 404, who
    assert_untouched(before, e, occurrence_id)
    assert not audit_rows(e, occurrence_id)
    # a covered colleague who is not the responsible Teacher is refused, not found
    assert confirm(e, "t4", occurrence_id, run_id, generation_id).status_code == 403
    assert_untouched(before, e, occurrence_id)


def test_after_a_post_complete_claim_a_new_responsible_teacher_can_take_over(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    assert complete(e, "t1", run_id).status_code == 200
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 200
    old = str(projection_token(e, "t1", occurrence_id).json()["token"])
    first = occurrence_row(e.d, occurrence_id)
    update_occurrence(e, occurrence_id, responsible_teacher_ref=e.d.accounts["t4"])
    assert stream(e, "t1", run_id, old).status_code == 404  # the old Teacher is out at once
    # the new Teacher has no confirmation of their own yet
    assert projection_token(e, "t4", occurrence_id).status_code == 409
    response = confirm(e, "t4", occurrence_id, run_id, generation_id)
    assert response.status_code == 200, response.text
    after = occurrence_row(e.d, occurrence_id)
    assert after["class_projection_confirmed_by_ref"] == e.d.accounts["t4"]
    assert after["sample_claimed_at"] == first["sample_claimed_at"]  # never claimed twice
    token = str(projection_token(e, "t4", occurrence_id).json()["token"])
    assert streams(stream(e, "t4", run_id, token))


def test_a_new_teacher_cannot_revive_a_confirmation_given_before_complete(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, _token = confirmed_sample(v)
    assert complete(e, "t1", run_id).status_code == 200
    update_occurrence(e, occurrence_id, responsible_teacher_ref=e.d.accounts["t4"])
    before = occurrence_row(e.d, occurrence_id)
    refused = confirm(e, "t4", occurrence_id, run_id, generation_id)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert_untouched(before, e, occurrence_id)
    assert projection_token(e, "t4", occurrence_id).status_code == 409
