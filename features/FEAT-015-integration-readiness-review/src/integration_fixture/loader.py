"""Read-only loader and offline scenario harness for integration-fixture-v1."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCENARIOS = {
    "happy_cache_hit": ("READY_FOR_OFFSCREEN_ACTIVITY", True),
    "modality_conflict_requires_gate_a": ("GATE_A_REQUIRED", False),
    "no_eligible_activity_add_context": ("CONTEXT_REQUIRED", False),
    "cache_miss_fallback": ("READY_FOR_OFFSCREEN_ACTIVITY", True),
    "asset_integrity_failure": ("ASSET_REJECTED", False),
    "stale_gate_or_completion": ("STALE_VERSION_REJECTED", False),
    "invalid_media_recap": ("RECAPTURE", False),
    "blocked_learning_media": ("MEDIA_BLOCKED_HANDOFF_PRESERVED", True),
}


class FixtureError(ValueError):
    pass


@dataclass(frozen=True)
class IntegrationFixture:
    root: Path
    manifest: dict[str, Any]

    @property
    def fixture_id(self) -> str:
        return str(self.manifest["fixture_id"])

    @property
    def canonical_refs(self) -> dict[str, Any]:
        return dict(self.manifest["canonical_refs"])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_safe(root: Path, value: str) -> Path:
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise FixtureError(f"fixture path escapes package: {value}") from exc
    return candidate


def load_fixture(root: Path) -> IntegrationFixture:
    root = root.resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FixtureError("manifest.json is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("synthetic_data") is not True:
        raise FixtureError("fixture must declare synthetic_data=true")
    if manifest.get("fixture_version") != "1.0":
        raise FixtureError("unsupported fixture version")
    refs = manifest.get("canonical_refs", {})
    required_refs = {"activity_id", "activity_version", "objective_id", "objective_version"}
    if set(refs) != required_refs:
        raise FixtureError("canonical_refs must contain exactly the P1 identity fields")
    for source in manifest.get("source_media", []):
        path = _relative_safe(root, source["path"])
        if not path.is_file():
            raise FixtureError(f"source media is missing: {source['path']}")
        actual = _sha256(path)
        if source["sha256"] != actual:
            raise FixtureError(f"source hash mismatch: {source['artifact_id']}")
    return IntegrationFixture(root=root, manifest=manifest)


def validate_expected_identity(fixture: IntegrationFixture) -> None:
    refs = fixture.canonical_refs
    for path in sorted((fixture.root / "expected").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("activity_id", "objective_id"):
            if key in data and data[key] != refs[key]:
                raise FixtureError(f"{path.name}: {key} does not use P1 canonical identity")
        for key in ("activity_version", "objective_version"):
            if key in data and data[key] != refs[key]:
                raise FixtureError(f"{path.name}: {key} does not use P1 canonical version")


def run_scenario(fixture: IntegrationFixture, name: str) -> dict[str, Any]:
    if name not in SCENARIOS:
        raise FixtureError(f"unknown scenario: {name}")
    validate_expected_identity(fixture)
    status, handoff = SCENARIOS[name]
    transitions = ["MEDIA_VALIDATED"]
    if name == "invalid_media_recap":
        transitions.append("RECAPTURE")
    elif name == "modality_conflict_requires_gate_a":
        transitions.extend(["RAW_PROPOSAL", "GATE_A_REQUIRED"])
    elif name == "no_eligible_activity_add_context":
        transitions.extend(["GATE_A_CONFIRMED", "CONTEXT_REQUIRED", "RE_EVALUATION"])
    elif name == "asset_integrity_failure":
        transitions.extend(["GATE_A_CONFIRMED", "GATE_B_APPROVED", "ASSET_REJECTED"])
    elif name == "stale_gate_or_completion":
        transitions.append("STALE_VERSION_REJECTED")
    elif name == "blocked_learning_media":
        transitions.extend(["GATE_A_CONFIRMED", "GATE_B_APPROVED", "MEDIA_BLOCKED", "HANDOFF_PRESERVED"])
    else:
        transitions.extend(["GATE_A_CONFIRMED", "P1_FILTERED", "GATE_B_APPROVED"])
        if name == "cache_miss_fallback":
            transitions.extend(["CACHE_MISS", "FALLBACK"])
        else:
            transitions.extend(["P3_DRAW_REVEAL", "CACHE_HIT"])
        transitions.extend(["ACTIVITY_HANDOFF", "FEEDBACK_RECORDED"])
    return {"scenario": name, "status": status, "handoff": handoff, "transitions": transitions}


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / "integration-fixture-v1"


def validate_asset_manifest(fixture: IntegrationFixture) -> None:
    """Validate the P3 whole-drawing manifest against the immutable source bytes."""
    path = fixture.root / "expected" / "art-asset-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("asset_kind") != "WHOLE_DRAWING":
        raise FixtureError("v1 asset must use WHOLE_DRAWING")
    if data.get("source_artifact_id") != "child-drawing-001":
        raise FixtureError("asset source artifact is not the fixture drawing")
    source = next(item for item in fixture.manifest["source_media"] if item["artifact_id"] == "child-drawing-001")
    if data.get("source_sha256") != source["sha256"]:
        raise FixtureError("asset source hash does not match manifest")
    _relative_safe(fixture.root, data["source_path"])
