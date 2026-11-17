from __future__ import annotations

import hashlib
import json

import pytest
from integration_fixture import (
    FixtureError,
    fixture_path,
    load_fixture,
    run_scenario,
    validate_expected_identity,
)


@pytest.fixture()
def fixture():
    return load_fixture(fixture_path())


def test_fixture_is_synthetic_and_uses_p1_canonical_identity(fixture):
    assert fixture.manifest["synthetic_data"] is True
    assert fixture.canonical_refs == {
        "activity_id": "ACT-0004",
        "activity_version": 2,
        "objective_id": "OBJ_MOVEMENT_COORDINATION",
        "objective_version": 1,
    }
    validate_expected_identity(fixture)


def test_source_hashes_are_present_and_stable(fixture):
    for source in fixture.manifest["source_media"]:
        actual = hashlib.sha256((fixture.root / source["path"]).read_bytes()).hexdigest()
        assert actual == source["sha256"]


def test_all_required_scenarios_have_typed_outcomes(fixture):
    names = fixture.manifest["scenarios"]
    assert len(names) == 8
    results = {name: run_scenario(fixture, name) for name in names}
    assert results["happy_cache_hit"]["status"] == "READY_FOR_OFFSCREEN_ACTIVITY"
    assert results["modality_conflict_requires_gate_a"]["status"] == "GATE_A_REQUIRED"
    assert results["no_eligible_activity_add_context"]["status"] == "CONTEXT_REQUIRED"
    assert results["invalid_media_recap"]["status"] == "RECAPTURE"
    assert results["stale_gate_or_completion"]["status"] == "STALE_VERSION_REJECTED"


def test_conflict_and_context_scenarios_do_not_handoff(fixture):
    assert run_scenario(fixture, "modality_conflict_requires_gate_a")["handoff"] is False
    assert run_scenario(fixture, "no_eligible_activity_add_context")["handoff"] is False


def test_hash_tampering_fails_closed(tmp_path, fixture):
    copied = tmp_path / "fixture"
    import shutil
    shutil.copytree(fixture.root, copied)
    drawing = copied / "media" / "drawing.svg"
    drawing.write_text(drawing.read_text(encoding="utf-8") + "tampered", encoding="utf-8")
    with pytest.raises(FixtureError, match="source hash mismatch"):
        load_fixture(copied)


def test_paths_cannot_escape_fixture(tmp_path):
    manifest = {"fixture_id": "x", "fixture_version": "1.0", "synthetic_data": True, "source_media": [{"artifact_id": "x", "path": "../outside", "sha256": "x"}], "canonical_refs": {"activity_id": "A", "activity_version": 1, "objective_id": "O", "objective_version": 1}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(FixtureError, match="escapes"):
        load_fixture(tmp_path)


def test_asset_manifest_is_bound_to_whole_drawing_hash(fixture):
    from integration_fixture import validate_asset_manifest
    validate_asset_manifest(fixture)


def test_every_scenario_has_explicit_terminal_contract(fixture):
    expected = {
        "happy_cache_hit": ("READY_FOR_OFFSCREEN_ACTIVITY", True),
        "modality_conflict_requires_gate_a": ("GATE_A_REQUIRED", False),
        "no_eligible_activity_add_context": ("CONTEXT_REQUIRED", False),
        "cache_miss_fallback": ("READY_FOR_OFFSCREEN_ACTIVITY", True),
        "asset_integrity_failure": ("ASSET_REJECTED", False),
        "stale_gate_or_completion": ("STALE_VERSION_REJECTED", False),
        "invalid_media_recap": ("RECAPTURE", False),
        "blocked_learning_media": ("MEDIA_BLOCKED_HANDOFF_PRESERVED", True),
    }
    assert {name: (run_scenario(fixture, name)["status"], run_scenario(fixture, name)["handoff"]) for name in expected} == expected


def test_expected_artifacts_have_declared_contracts(fixture):
    contracts = set(fixture.manifest["contracts"].values())
    for path in (fixture.root / "expected").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["contract_name"] in contracts
        assert payload["contract_version"] in {"1.0", "2.0"}
