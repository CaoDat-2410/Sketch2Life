"""Deterministic, synthetic consumer examples generated through the actual 04/05 chain."""

from __future__ import annotations

from sketch2life.infrastructure.assistance.harness import DEVICE_A
from sketch2life.infrastructure.child_response.harness import build_child_response_harness

EXAMPLES_FIXTURE_ID = "FEAT-055-BE206-H-AI-REVIEW"


def build_child_response_examples() -> dict[str, object]:
    h = build_child_response_harness()
    proposal_id = h.approved()
    initial = h.read(proposal_id)
    viewed = h.respond(proposal_id)
    hidden = h.respond(proposal_id, "hidden")
    passive_hidden = h.read(proposal_id)
    explicit_reveal = h.read(proposal_id, explicit_reveal=True)
    restored = h.respond(proposal_id)
    decline_command = h.command(proposal_id, "declined")
    declined = h.service.record_response(decline_command)
    suppressed = h.read(proposal_id, explicit_reveal=True)
    h.close_turn(DEVICE_A)
    replay = h.service.record_response(decline_command)
    return {
        "fixture_id": EXAMPLES_FIXTURE_ID,
        "synthetic_only": True,
        "contract_version": "0.1-candidate",
        "examples": {
            "initial_read": initial.model_dump(mode="json"),
            "viewed_receipt": viewed.data.model_dump(mode="json"),
            "hidden_receipt": hidden.data.model_dump(mode="json"),
            "hidden_passive_read": passive_hidden.model_dump(mode="json"),
            "hidden_explicit_reveal": explicit_reveal.model_dump(mode="json"),
            "restored_receipt": restored.data.model_dump(mode="json"),
            "declined_receipt": declined.data.model_dump(mode="json"),
            "declined_read": suppressed.model_dump(mode="json"),
            "closed_turn_replay": {
                "replayed": replay.replayed, "data": replay.data.model_dump(mode="json")},
            "teacher_events": [e.model_dump(mode="json") for e in h.teacher_events()],
        },
        "runtime_status": "NOT_RUN",
    }
