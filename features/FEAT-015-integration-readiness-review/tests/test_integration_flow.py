from __future__ import annotations

import json

import pytest
from integration_fixture import (
    IntegrationRejected,
    confirm_gate_a,
    filter_p1,
    fixture_path,
    fuse_modalities,
    load_fixture,
    run_named_scenario,
    run_offline_flow,
)


def test_happy_offline_flow_reaches_handoff():
    result = run_offline_flow(load_fixture(fixture_path()))
    assert result["raw"].conflicts == ()
    assert result["p1"].status == "ELIGIBLE"
    assert result["art"].motion_kind == "DRAW_REVEAL"
    assert result["media"].status == "CACHE_HIT"


def test_modality_conflict_is_preserved_and_gate_a_is_required():
    fixture = load_fixture(fixture_path())
    asr = json.loads((fixture.root / "expected/asr-result.json").read_text())
    vision = json.loads((fixture.root / "expected/vision-result.json").read_text())
    vision["entities"][0]["label"] = "flower"
    raw = fuse_modalities(asr, vision)
    assert raw.conflicts and raw.conflicts[0]["reason_code"] == "MODALITY_DISAGREEMENT"
    with pytest.raises(IntegrationRejected, match="GATE_A_REQUIRED"):
        filter_p1(json.loads((fixture.root / "expected/p1-context.json").read_text()), None, fixture)


def test_no_eligible_activity_requests_context():
    fixture = load_fixture(fixture_path())
    gate = confirm_gate_a(fuse_modalities({}, {"entities": [{"label": "butterfly"}]}), actor_ref="adult", expected_session_version=1, session_version=1)
    result = filter_p1({"age_months": 4, "readiness_ids": [], "available_material_option_ids": [], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "ACTIVE_FIXTURE"}, gate, fixture)
    assert result.status == "CONTEXT_REQUIRED"


def test_p4_fallback_preserves_approved_identity():
    result = run_offline_flow(load_fixture(fixture_path()), cache_hit=False, validation_failed=True)
    assert result["media"].status == "FALLBACK"
    assert result["media"].objective_id == "OBJ_MOVEMENT_COORDINATION"
    assert result["media"].activity_id == "ACT-0004"


def test_stale_gate_is_rejected():
    with pytest.raises(IntegrationRejected, match="STALE_GATE_A_SESSION_VERSION"):
        confirm_gate_a(fuse_modalities({}, {"entities": [{"label": "butterfly"}]}), actor_ref="adult", expected_session_version=2, session_version=1)


def test_blocked_media_preserves_handoff_identity():
    result = run_offline_flow(load_fixture(fixture_path()), cache_hit=False, blocked=True)
    assert result["media"].status == "BLOCK"
    assert result["gate_b"].activity_id == "ACT-0004"
    assert result["gate_b"].objective_id == "OBJ_MOVEMENT_COORDINATION"


@pytest.mark.parametrize(
    ("name", "status", "handoff"),
    [
        ("happy_cache_hit", "READY_FOR_OFFSCREEN_ACTIVITY", True),
        ("modality_conflict_requires_gate_a", "GATE_A_REQUIRED", False),
        ("no_eligible_activity_add_context", "CONTEXT_REQUIRED", False),
        ("cache_miss_fallback", "READY_FOR_OFFSCREEN_ACTIVITY", True),
        ("asset_integrity_failure", "ASSET_REJECTED", False),
        ("stale_gate_or_completion", "STALE_VERSION_REJECTED", False),
        ("invalid_media_recap", "RECAPTURE", False),
        ("blocked_learning_media", "MEDIA_BLOCKED_HANDOFF_PRESERVED", True),
    ],
)
def test_all_eight_scenarios_execute_through_adapters(name, status, handoff):
    fixture = load_fixture(fixture_path())
    outcome = run_named_scenario(fixture, name)
    assert outcome["status"] == status
    assert outcome["handoff"] is handoff

