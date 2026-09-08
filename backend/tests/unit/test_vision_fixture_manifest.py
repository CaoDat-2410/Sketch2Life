from __future__ import annotations

import json
from pathlib import Path

from sketch2life.contracts.schemas.vision import VisionFixtureManifestEntryV1


def test_manifest_is_synthetic_and_declares_every_scenario_family() -> None:
    manifest_path = _project_root() / "data/fixtures/manifests/vision-phase-a-v1.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = tuple(
        VisionFixtureManifestEntryV1.model_validate(item) for item in payload["fixtures"]
    )

    assert payload["data_policy"] == "synthetic-only"
    assert all(entry.synthetic_data for entry in entries)
    assert {entry.fixture_id for entry in entries} == {
        item["fixture_id"] for item in payload["fixtures"]
    }

    policy_blocked = {
        entry.fixture_id
        for entry in entries
        if entry.expected_error_code == "PROHIBITED_CLAIM_DETECTED"
    }
    assert len(policy_blocked) == 6


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]
