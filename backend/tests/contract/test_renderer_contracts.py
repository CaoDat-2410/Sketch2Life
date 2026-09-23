from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.renderer import (
    ArtAnimationPlanPayloadV1,
    ArtAnimationPlanV1,
    PixiArtAssetManifestV1,
    RendererBootstrapV1,
    RendererEventAdapterV1,
)
from sketch2life.contracts.schemas.scene_exploration import (
    SceneFocusPlanV1,
    SourceRegionV1,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RENDERER_FIXTURE = (
    REPOSITORY_ROOT
    / "packages"
    / "art-renderer"
    / "fixtures"
    / "butterfly"
    / "art_animation_plan.json"
)
SOURCE_HASH = "0" * 64


def test_renderer_v1_payload_matches_camel_case_protocol_and_fixture() -> None:
    plan_data = json.loads(RENDERER_FIXTURE.read_text(encoding="utf-8"))
    plan = ArtAnimationPlanPayloadV1.model_validate(plan_data)
    schema = ArtAnimationPlanPayloadV1.model_json_schema(by_alias=True)

    assert plan.plan_id == "fixture-butterfly-art-animation"
    assert "contractVersion" in schema["properties"]
    assert schema["properties"]["contractVersion"]["const"] == "1"
    assert schema["additionalProperties"] is False


def test_art_animation_envelope_locks_renderer_to_source_and_experience() -> None:
    plan_data = json.loads(RENDERER_FIXTURE.read_text(encoding="utf-8"))
    envelope = ArtAnimationPlanV1.model_validate(
        {
            "contractName": "ArtAnimationPlanV1",
            "contractVersion": "1.0",
            "sessionId": "session-1",
            "experienceSpecRef": {"id": "spec-1", "version": 2},
            "sourceArtifactRef": "artifact:source-1",
            "sourceArtifactSha256": SOURCE_HASH,
            "plan": plan_data,
            "originalArtPreserved": True,
            "videoExecuted": False,
        }
    )
    assert envelope.plan.objects[0].asset.source_sha256 == SOURCE_HASH

    plan_data["objects"][0]["asset"]["sourceSha256"] = "1" * 64
    with pytest.raises(ValidationError, match="source hash"):
        ArtAnimationPlanV1.model_validate(
            {
                "contractName": "ArtAnimationPlanV1",
                "contractVersion": "1.0",
                "sessionId": "session-1",
                "experienceSpecRef": {"id": "spec-1", "version": 2},
                "sourceArtifactRef": "artifact:source-1",
                "sourceArtifactSha256": SOURCE_HASH,
                "plan": plan_data,
            }
        )


def test_pixi_manifest_requires_original_and_approved_rights_cleared_overlays() -> None:
    manifest = {
        "contractName": "PixiArtAssetManifestV1",
        "contractVersion": "1.0",
        "sessionId": "session-1",
        "experienceSpecRef": {"id": "spec-1", "version": 2},
        "sourceArtifactRef": "artifact:source-1",
        "sourceArtifactSha256": SOURCE_HASH,
        "assets": [
            {
                "assetId": "source-1",
                "assetVersion": "1",
                "assetRef": "artifact:source-1",
                "sha256": SOURCE_HASH,
                "role": "ORIGINAL_ART",
                "reviewStatus": "SOURCE_ORIGINAL",
                "rightsStatus": "NOT_APPLICABLE",
            }
        ],
        "originalArtPreserved": True,
        "providerGenerationCalled": False,
    }
    parsed = PixiArtAssetManifestV1.model_validate(manifest)
    assert len(parsed.assets) == 1
    assert parsed.assets[0].role == "ORIGINAL_ART"

    pending_overlay = {
        "assetId": "pending-butterfly",
        "assetVersion": "1",
        "assetRef": "asset:pending-butterfly",
        "sha256": "2" * 64,
        "role": "SUPPLEMENTAL",
        "reviewStatus": "SOURCE_ORIGINAL",
        "rightsStatus": "NOT_APPLICABLE",
    }
    with pytest.raises(ValidationError, match="visual and rights approval"):
        PixiArtAssetManifestV1.model_validate(
            {**manifest, "assets": [manifest["assets"][0], pending_overlay]}
        )


def test_renderer_bootstrap_and_event_protocol_are_typed_and_bounded() -> None:
    bootstrap = RendererBootstrapV1(
        protocolVersion="1",
        rendererInstanceId="renderer-1",
    )
    assert bootstrap.protocol_version == "1"
    assert (
        RendererEventAdapterV1.validate_python(
            {"type": "PLAYBACK_STARTED", "planId": "plan-1"}
        ).type
        == "PLAYBACK_STARTED"
    )
    assert (
        RendererEventAdapterV1.validate_python(
            {
                "type": "FALLBACK_APPLIED",
                "planId": "plan-1",
                "reason": "MASK_INVALID",
            }
        ).reason
        == "MASK_INVALID"
    )
    with pytest.raises(ValidationError):
        RendererEventAdapterV1.validate_python(
            {"type": "FALLBACK_APPLIED", "planId": "plan-1", "reason": "unknown"}
        )
    with pytest.raises(ValidationError):
        RendererEventAdapterV1.validate_python(
            {"type": "PLAYBACK_FAILED", "planId": "plan-1", "reason": "x" * 161}
        )


def test_scene_focus_requires_explicit_bounded_source_regions() -> None:
    region = SourceRegionV1(x=0.1, y=0.2, width=0.25, height=0.3)
    assert region.x + region.width <= 1
    ready = SceneFocusPlanV1.model_validate(
        {
            "contractName": "SceneFocusPlanV1",
            "contractVersion": "1.0",
            "sessionId": "session-1",
            "experienceSpecRef": {"id": "spec-1", "version": 2},
            "sourceArtifactRef": "artifact:source-1",
            "sourceArtifactSha256": SOURCE_HASH,
            "extractionStatus": "READY",
            "targets": [
                {
                    "targetRef": "bird-1",
                    "labelVi": "con chim",
                    "sourceRegion": region.model_dump(mode="json"),
                    "regionConfidence": 0.91,
                    "depthLayer": 1,
                    "hitSlop": 0.06,
                    "assetKind": "CROP",
                    "extractionVersion": "1",
                }
            ],
        }
    )
    assert ready.extraction_status == "READY"
    with pytest.raises(ValidationError, match="inside"):
        SourceRegionV1(x=0.9, y=0.1, width=0.2, height=0.2)
    with pytest.raises(ValidationError, match="fallback"):
        SceneFocusPlanV1.model_validate(
            {
                "contractName": "SceneFocusPlanV1",
                "contractVersion": "1.0",
                "sessionId": "session-1",
                "experienceSpecRef": {"id": "spec-1", "version": 2},
                "sourceArtifactRef": "artifact:source-1",
                "sourceArtifactSha256": SOURCE_HASH,
                "extractionStatus": "FALLBACK_REQUIRED",
                "targets": [
                    {
                        "targetRef": "bird-1",
                        "labelVi": "con chim",
                        "sourceRegion": region.model_dump(mode="json"),
                        "regionConfidence": 0.91,
                        "depthLayer": 1,
                        "hitSlop": 0.06,
                        "assetKind": "CROP",
                        "extractionVersion": "1",
                    }
                ],
                "fallbackReason": "NO_LOCALIZER",
            }
        )
