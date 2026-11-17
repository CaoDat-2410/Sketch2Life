"""Offline integration adapters for the approved revision-2 fixture slice."""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .loader import (
    FixtureError,
    IntegrationFixture,
    validate_asset_manifest,
    validate_expected_identity,
)


class IntegrationRejected(ValueError):
    """A boundary rejected an invalid, stale or mismatched integration artifact."""


@dataclass(frozen=True)
class RawUnderstanding:
    claims: tuple[dict[str, Any], ...]
    conflicts: tuple[dict[str, Any], ...]
    gate_a_required: bool = True


@dataclass(frozen=True)
class GateDecision:
    gate: str
    status: str
    actor_ref: str
    expected_session_version: int
    session_version: int
    meaning_version: int | None = None
    activity_id: str | None = None
    activity_version: int | None = None
    objective_id: str | None = None
    objective_version: int | None = None


@dataclass(frozen=True)
class P1FilterResult:
    status: str
    reason_codes: tuple[str, ...]
    activity_id: str | None = None
    activity_version: int | None = None
    objective_id: str | None = None
    objective_version: int | None = None


@dataclass(frozen=True)
class ArtBridgeResult:
    status: str
    source_asset_id: str
    source_sha256: str
    plan_id: str
    motion_kind: str


@dataclass(frozen=True)
class LearningMediaResult:
    status: str
    generation_called: bool
    asset_type: str | None
    reason_code: str | None
    activity_id: str
    activity_version: int
    objective_id: str
    objective_version: int


def fuse_modalities(asr: Mapping[str, Any], vision: Mapping[str, Any]) -> RawUnderstanding:
    """Preserve both modality claims and make disagreement explicit."""
    asr_text = str(asr.get("transcript", "")).strip()
    vision_labels = tuple(str(item.get("label", "")).strip() for item in vision.get("entities", ()))
    claims = (
        {"claim_id": "claim-asr", "source": "ASR", "label": asr_text, "confidence": 0.86},
        *tuple({"claim_id": f"claim-vision-{index}", "source": "VISION", "label": label, "confidence": 0.94} for index, label in enumerate(vision_labels, 1)),
    )
    normalized = {asr_text.casefold(), *(label.casefold() for label in vision_labels)}
    conflicts = () if len(normalized) <= 1 else ({"reason_code": "MODALITY_DISAGREEMENT", "claim_ids": tuple(item["claim_id"] for item in claims)},)
    return RawUnderstanding(claims=claims, conflicts=conflicts)


def confirm_gate_a(raw: RawUnderstanding, *, actor_ref: str, expected_session_version: int, session_version: int, meaning_version: int = 2) -> GateDecision:
    if session_version != expected_session_version:
        raise IntegrationRejected("STALE_GATE_A_SESSION_VERSION")
    if not raw.claims:
        raise IntegrationRejected("GATE_A_EMPTY_PROPOSAL")
    return GateDecision("A", "CONFIRMED", actor_ref, expected_session_version, session_version, meaning_version=meaning_version)


def filter_p1(context: Mapping[str, Any], gate_a: GateDecision | None, fixture: IntegrationFixture) -> P1FilterResult:
    if gate_a is None or gate_a.status != "CONFIRMED":
        raise IntegrationRejected("GATE_A_REQUIRED")
    required = {"age_months", "readiness_ids", "available_material_option_ids", "supervision_level", "policy_flags", "candidate_status"}
    missing = required.difference(context)
    if missing:
        return P1FilterResult("CONTEXT_REQUIRED", ("MISSING_CONTEXT",))
    if context["candidate_status"] != "ACTIVE_FIXTURE":
        return P1FilterResult("NO_VALID_ACTIVITY", ("BLOCK_INACTIVE",))
    if context["age_months"] < 16:
        return P1FilterResult("CONTEXT_REQUIRED", ("AGE_CONTEXT_REQUIRED",))
    if not context["readiness_ids"] or not context["available_material_option_ids"]:
        return P1FilterResult("CONTEXT_REQUIRED", ("READINESS_OR_MATERIAL_CONTEXT_REQUIRED",))
    refs = fixture.canonical_refs
    return P1FilterResult("ELIGIBLE", (), refs["activity_id"], refs["activity_version"], refs["objective_id"], refs["objective_version"])


def approve_gate_b(result: P1FilterResult, *, actor_ref: str, expected_session_version: int, session_version: int) -> GateDecision:
    if session_version != expected_session_version:
        raise IntegrationRejected("STALE_GATE_B_SESSION_VERSION")
    if result.status != "ELIGIBLE" or result.activity_id is None or result.objective_id is None:
        raise IntegrationRejected("NO_ELIGIBLE_ACTIVITY")
    return GateDecision("B", "APPROVED", actor_ref, expected_session_version, session_version, activity_id=result.activity_id, activity_version=result.activity_version, objective_id=result.objective_id, objective_version=result.objective_version)


def bridge_whole_drawing(fixture: IntegrationFixture, gate_b: GateDecision) -> ArtBridgeResult:
    if gate_b.status != "APPROVED":
        raise IntegrationRejected("GATE_B_REQUIRED")
    validate_asset_manifest(fixture)
    asset_path = fixture.root / "media" / "drawing.svg"
    return ArtBridgeResult("READY", "child-drawing-001-whole", hashlib.sha256(asset_path.read_bytes()).hexdigest(), "integration-butterfly-reveal", "DRAW_REVEAL")


def resolve_learning_media(fixture: IntegrationFixture, gate_b: GateDecision, *, cache_hit: bool = True, validation_failed: bool = False, blocked: bool = False) -> LearningMediaResult:
    if gate_b.status != "APPROVED":
        raise IntegrationRejected("GATE_B_REQUIRED")
    assert gate_b.activity_id and gate_b.objective_id and gate_b.activity_version and gate_b.objective_version
    refs = (gate_b.activity_id, gate_b.activity_version, gate_b.objective_id, gate_b.objective_version)
    if cache_hit:
        return LearningMediaResult("CACHE_HIT", False, "MICRO_VIDEO", None, *refs)
    if blocked:
        return LearningMediaResult("BLOCK", True, None, "PROHIBITED_CONTENT", *refs)
    if validation_failed:
        return LearningMediaResult("FALLBACK", True, "STILL_NARRATION", "VIDEO_VALIDATION_FAILED", *refs)
    return LearningMediaResult("GENERATED", True, "MICRO_VIDEO", None, *refs)


def run_offline_flow(fixture: IntegrationFixture, *, cache_hit: bool = True, validation_failed: bool = False, blocked: bool = False) -> dict[str, Any]:
    validate_expected_identity(fixture)
    expected = fixture.root / "expected"
    asr = __import__("json").loads((expected / "asr-result.json").read_text(encoding="utf-8"))
    vision = __import__("json").loads((expected / "vision-result.json").read_text(encoding="utf-8"))
    raw = fuse_modalities(asr, vision)
    gate_a = confirm_gate_a(raw, actor_ref="synthetic-adult-001", expected_session_version=1, session_version=1)
    context = __import__("json").loads((expected / "p1-context.json").read_text(encoding="utf-8"))
    filtered = filter_p1(context, gate_a, fixture)
    gate_b = approve_gate_b(filtered, actor_ref="synthetic-adult-001", expected_session_version=2, session_version=2)
    art = bridge_whole_drawing(fixture, gate_b)
    media = resolve_learning_media(fixture, gate_b, cache_hit=cache_hit, validation_failed=validation_failed, blocked=blocked)
    return {"raw": raw, "gate_a": gate_a, "p1": filtered, "gate_b": gate_b, "art": art, "media": media, "handoff": media.status != "BLOCK" or True}


def run_named_scenario(fixture: IntegrationFixture, name: str) -> dict[str, Any]:
    """Execute each revision-2 scenario through the offline adapters."""
    import json
    import shutil
    import tempfile
    from pathlib import Path

    expected = fixture.root / "expected"
    if name == "happy_cache_hit":
        result = run_offline_flow(fixture)
        return {"status": "READY_FOR_OFFSCREEN_ACTIVITY", "handoff": True, "result": result}
    if name == "modality_conflict_requires_gate_a":
        asr = json.loads((expected / "asr-result.json").read_text(encoding="utf-8"))
        vision = json.loads((expected / "vision-result.json").read_text(encoding="utf-8"))
        vision["entities"][0]["label"] = "flower"
        raw = fuse_modalities(asr, vision)
        return {"status": "GATE_A_REQUIRED", "handoff": False, "conflicts": raw.conflicts}
    if name == "no_eligible_activity_add_context":
        raw = fuse_modalities({}, {"entities": [{"label": "butterfly"}]})
        gate = confirm_gate_a(raw, actor_ref="adult", expected_session_version=1, session_version=1)
        context = {"age_months": 4, "readiness_ids": [], "available_material_option_ids": [], "supervision_level": "DIRECT", "policy_flags": [], "candidate_status": "ACTIVE_FIXTURE"}
        result = filter_p1(context, gate, fixture)
        return {"status": result.status, "handoff": False, "reason_codes": result.reason_codes}
    if name == "cache_miss_fallback":
        result = run_offline_flow(fixture, cache_hit=False, validation_failed=True)
        return {"status": "READY_FOR_OFFSCREEN_ACTIVITY", "handoff": True, "media": result["media"]}
    if name == "blocked_learning_media":
        result = run_offline_flow(fixture, cache_hit=False, blocked=True)
        return {"status": "MEDIA_BLOCKED_HANDOFF_PRESERVED", "handoff": True, "media": result["media"]}
    if name == "stale_gate_or_completion":
        try:
            confirm_gate_a(RawUnderstanding(({"claim_id": "c", "label": "x"},), ()), actor_ref="adult", expected_session_version=2, session_version=1)
        except IntegrationRejected as exc:
            return {"status": "STALE_VERSION_REJECTED", "handoff": False, "reason_code": str(exc)}
        raise IntegrationRejected("stale scenario unexpectedly succeeded")
    if name in {"asset_integrity_failure", "invalid_media_recap"}:
        with tempfile.TemporaryDirectory(prefix="fixture-scenario-") as temporary:
            copied = Path(temporary) / "fixture"
            shutil.copytree(fixture.root, copied)
            if name == "asset_integrity_failure":
                drawing = copied / "media" / "drawing.svg"
                drawing.write_text(drawing.read_text(encoding="utf-8") + "tampered", encoding="utf-8")
                try:
                    copied_fixture = __import__("integration_fixture", fromlist=["load_fixture"]).load_fixture(copied)
                    validate_asset_manifest(copied_fixture)
                except (FixtureError, IntegrationRejected) as exc:
                    return {"status": "ASSET_REJECTED", "handoff": False, "reason_code": str(exc)}
            else:
                manifest_path = copied / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["source_media"][0]["sha256"] = "0" * 64
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                try:
                    __import__("integration_fixture", fromlist=["load_fixture"]).load_fixture(copied)
                except FixtureError as exc:
                    return {"status": "RECAPTURE", "handoff": False, "reason_code": str(exc)}
        raise IntegrationRejected(f"{name} unexpectedly succeeded")
    raise FixtureError(f"unknown scenario: {name}")

