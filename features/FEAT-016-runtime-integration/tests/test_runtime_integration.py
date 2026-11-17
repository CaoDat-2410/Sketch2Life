from __future__ import annotations

import hashlib

import pytest

from runtime_integration import (
    ArtifactRef,
    CommandEnvelope,
    GateAConfirmation,
    GateBApproval,
    GateBDecision,
    LocalJobStore,
    RuntimeRejected,
    SessionAggregate,
    SessionState,
)

ACTIVITY = ("ACT-0004", 2)
OBJECTIVE = ("OBJ_OBJECT_PERMANENCE", 1)
TEMPLATE = ("TPL-BUTTERFLY-01", 1)
SPEC = ArtifactRef("experience-001", 1, "EXPERIENCE_SPEC", hashlib.sha256(b"experience").hexdigest())


def filter_candidates(session: SessionAggregate, number: int, version: int, context: dict[str, object]) -> None:
    session.filter_candidates(
        cmd("session-001", number, version),
        context,
        activity_id=ACTIVITY[0],
        activity_version=ACTIVITY[1],
        objective_id=OBJECTIVE[0],
        objective_version=OBJECTIVE[1],
        template_id=TEMPLATE[0],
        template_version=TEMPLATE[1],
    )


def cmd(session: str, number: int, version: int, actor: str = "adult") -> CommandEnvelope:
    return CommandEnvelope(f"cmd-{number}", session, version, actor)


def started_session() -> SessionAggregate:
    session = SessionAggregate("session-001")
    source = (ArtifactRef("drawing-001", 1, "DRAWING", "a" * 64), ArtifactRef("audio-001", 1, "AUDIO", "b" * 64))
    session.submit_media(cmd("session-001", 1, 0), source, validation_passed=True)
    session.record_understanding(cmd("session-001", 2, 1), {"claims": [{"claim_id": "claim-1", "label": "butterfly"}]})
    session.confirm_gate_a(cmd("session-001", 3, 2), GateAConfirmation(2, ("claim-1",)))
    return session


def test_fixture_session_reaches_feedback():
    session = started_session()
    context = {"age_months": 16, "readiness_ids": ["READY_SEARCH_PARTLY_HIDDEN"], "completed_activity_ids": [], "available_material_option_ids": ["GMAT-0004-PRIMARY"], "supervision_level": "DIRECT", "policy_flags": ["CAREGIVER_PRESENT"], "candidate_status": "ACTIVE_FIXTURE"}
    filter_candidates(session, 4, 3, context)
    assert session.snapshot.state is SessionState.CANDIDATES_READY
    session.attach_experience(cmd("session-001", 5, 4), (SPEC,))
    assert session.snapshot.state is SessionState.GATE_B_PENDING
    session.record_gate_b(
        cmd("session-001", 6, 5),
        GateBDecision(ACTIVITY[0], ACTIVITY[1], OBJECTIVE[0], OBJECTIVE[1], TEMPLATE[0], TEMPLATE[1], SPEC.artifact_id, SPEC.artifact_version),
    )
    session.complete_handoff(cmd("session-001", 7, 6))
    final = session.record_feedback(cmd("session-001", 8, 7), {"observed": "completed"})
    assert final.state is SessionState.FEEDBACK_RECORDED
    assert final.gate_b and final.gate_b.objective_id == OBJECTIVE[0]


def test_gate_a_is_mandatory_and_stale_commands_fail():
    session = SessionAggregate("session-001")
    with pytest.raises(RuntimeRejected, match="STALE_SESSION_VERSION"):
        session.submit_media(cmd("session-001", 1, 1), (ArtifactRef("d", 1, "DRAWING"),), validation_passed=True)
    session.submit_media(cmd("session-001", 1, 0), (ArtifactRef("d", 1, "DRAWING"),), validation_passed=True)
    with pytest.raises(RuntimeRejected, match="GATE_A_REQUIRED"):
        session.filter_candidates(cmd("session-001", 2, 1), {}, activity_id="A", activity_version=1, objective_id="O", objective_version=1, template_id="T", template_version=1)


def test_command_replay_is_idempotent():
    session = SessionAggregate("session-001")
    envelope = cmd("session-001", 1, 0)
    artifacts = (ArtifactRef("d", 1, "DRAWING"),)
    first = session.submit_media(envelope, artifacts, validation_passed=True)
    replay = session.submit_media(envelope, artifacts, validation_passed=True)
    assert replay == first
    assert session.snapshot.version == 1


def test_gate_b_identity_mismatch_is_rejected():
    session = started_session()
    context = {"age_months": 16, "readiness_ids": ["r"], "completed_activity_ids": [], "available_material_option_ids": ["m"], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "ACTIVE_FIXTURE"}
    filter_candidates(session, 4, 3, context)
    session.attach_experience(cmd("session-001", 5, 4), (SPEC,))
    with pytest.raises(RuntimeRejected, match="GATE_B_IDENTITY_MISMATCH"):
        session.record_gate_b(cmd("session-001", 6, 5), GateBDecision("ACT-999", 2, OBJECTIVE[0], OBJECTIVE[1], TEMPLATE[0], TEMPLATE[1], SPEC.artifact_id, SPEC.artifact_version))
    assert session.snapshot.state is SessionState.GATE_B_PENDING


def test_gate_b_blocked_result_stays_pending_and_does_not_enable_handoff():
    session = started_session()
    context = {"age_months": 16, "readiness_ids": ["r"], "completed_activity_ids": [], "available_material_option_ids": ["m"], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "ACTIVE_FIXTURE"}
    filter_candidates(session, 4, 3, context)
    session.attach_experience(cmd("session-001", 5, 4), (SPEC,))
    blocked = GateBDecision(
        ACTIVITY[0], ACTIVITY[1], OBJECTIVE[0], OBJECTIVE[1], TEMPLATE[0], TEMPLATE[1],
        SPEC.artifact_id, SPEC.artifact_version, status="BLOCKED", reason_codes=("ADULT_NOT_READY",),
    )
    state = session.record_gate_b(cmd("session-001", 6, 5), blocked)
    assert state.state is SessionState.GATE_B_PENDING
    assert state.gate_b is not None and state.gate_b.status == "BLOCKED"
    with pytest.raises(RuntimeRejected, match="HANDOFF_NOT_READY"):
        session.complete_handoff(cmd("session-001", 7, 6))


def test_context_required_can_be_retried():
    session = started_session()
    missing = {"age_months": 16, "readiness_ids": [], "available_material_option_ids": [], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "ACTIVE_FIXTURE"}
    state = session.filter_candidates(cmd("session-001", 4, 3), missing, activity_id=ACTIVITY[0], activity_version=ACTIVITY[1], objective_id=OBJECTIVE[0], objective_version=OBJECTIVE[1], template_id=TEMPLATE[0], template_version=TEMPLATE[1])
    assert state.state is SessionState.CONTEXT_REQUIRED
    complete = dict(missing, readiness_ids=["r"], completed_activity_ids=[], available_material_option_ids=["m"])
    state = session.filter_candidates(cmd("session-001", 5, 4), complete, activity_id=ACTIVITY[0], activity_version=ACTIVITY[1], objective_id=OBJECTIVE[0], objective_version=OBJECTIVE[1], template_id=TEMPLATE[0], template_version=TEMPLATE[1])
    assert state.state is SessionState.CANDIDATES_READY
    state = session.attach_experience(cmd("session-001", 6, 5), (SPEC,))
    assert state.state is SessionState.GATE_B_PENDING


def test_missing_completed_activity_list_is_context_required():
    session = started_session()
    context = {"age_months": 16, "readiness_ids": ["r"], "available_material_option_ids": ["m"], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "ACTIVE_FIXTURE"}
    state = session.filter_candidates(cmd("session-001", 4, 3), context, activity_id=ACTIVITY[0], activity_version=ACTIVITY[1], objective_id=OBJECTIVE[0], objective_version=OBJECTIVE[1], template_id=TEMPLATE[0], template_version=TEMPLATE[1])
    assert state.state is SessionState.CONTEXT_REQUIRED


def test_ineligible_context_does_not_advance_to_candidates_or_gate_b():
    session = started_session()
    context = {"age_months": 16, "readiness_ids": ["r"], "completed_activity_ids": [], "available_material_option_ids": ["m"], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "INACTIVE"}
    with pytest.raises(RuntimeRejected, match="P1_NO_ELIGIBLE_ACTIVITY"):
        filter_candidates(session, 4, 3, context)
    assert session.snapshot.state is SessionState.UNDERSTANDING_PROPOSED
    assert session.snapshot.version == 3


def test_gate_a_retake_invalidates_downstream_data_before_replacement():
    session = SessionAggregate("session-001")
    original = (ArtifactRef("drawing-001", 1, "DRAWING", "a" * 64),)
    session.submit_media(cmd("session-001", 1, 0), original, validation_passed=True)
    session.record_understanding(cmd("session-001", 2, 1), {"claims": [{"claim_id": "claim-1", "label": "butterfly"}]})
    state = session.request_retake(cmd("session-001", 3, 2))
    assert state.state is SessionState.MEDIA_RECAPTURE
    assert state.raw_understanding is None and state.gate_a is None and state.gate_b is None
    replacement = (ArtifactRef("drawing-002", 1, "DRAWING", "c" * 64),)
    state = session.submit_media(cmd("session-001", 4, 3), replacement, validation_passed=True)
    assert state.state is SessionState.CREATED
    assert state.source_artifacts == replacement
    assert state.raw_understanding is None and state.experience_artifacts == ()


def test_job_completion_is_stale_safe_and_idempotent():
    jobs = LocalJobStore()
    jobs.create("job-1", "session-001", 4)
    with pytest.raises(RuntimeRejected, match="STALE_JOB_COMPLETION"):
        jobs.complete("job-1", session_version=3, result_artifact=ArtifactRef("x", 1, "MEDIA"))
    done = jobs.complete("job-1", session_version=4, result_artifact=ArtifactRef("x", 1, "MEDIA"))
    assert done.status == "SUCCEEDED"
    assert jobs.complete("job-1", session_version=999).status == "SUCCEEDED"


def test_local_transport_round_trip_and_version_rejection():
    from runtime_integration import LocalTransport, TransportEnvelope
    transport = LocalTransport()
    result = transport.accept(TransportEnvelope("RuntimeCommandV1", "1.0", "cmd-1", "session-001", 0, {"type": "CREATE_SESSION"}))
    assert result["contract_name"] == "RuntimeResultV1"
    assert result["status"] == "ACCEPTED"
    with pytest.raises(RuntimeRejected, match="UNSUPPORTED_CONTRACT_VERSION"):
        transport.accept(TransportEnvelope("RuntimeCommandV1", "9.0", "cmd-2", "session-001", 0, {}))


def test_replay_remains_idempotent_after_state_changes():
    session = started_session()
    original = session.snapshot
    replay = session.record_understanding(cmd("session-001", 2, 1), {"claims": [{"claim_id": "ignored", "label": "changed"}]})
    assert replay.state is SessionState.GATE_A_PENDING
    assert session.snapshot == original




def test_contract_rejects_invalid_artifact_and_gate_values():
    with pytest.raises(RuntimeRejected, match="ARTIFACT_HASH_INVALID"):
        ArtifactRef("x", 1, "MEDIA", "bad")
    with pytest.raises(RuntimeRejected, match="GATE_A_CONFIRMATION_INVALID"):
        GateAConfirmation(0, ())
    with pytest.raises(RuntimeRejected, match="GATE_B_APPROVAL_INVALID"):
        GateBApproval("", -1, "", -1, "", -1, "", -1)
