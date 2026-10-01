from __future__ import annotations

import base64
from dataclasses import replace
from hashlib import sha256
from io import BytesIO

import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from sketch2life.application.ports.pixi_show_planner import (
    PixiShowAssetCandidate,
    PixiShowPlannerUnavailable,
    PixiShowPlanningRequest,
)
from sketch2life.application.services.auto_rig.part_masks import derive_part_masks_from_subject_mask
from sketch2life.application.services.pixi_show_compiler import compile_pixi_show_plan
from sketch2life.contracts.schemas.auto_rig import RigArchetype
from sketch2life.contracts.schemas.pixi_show import (
    PixiShowIntentV1,
)
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.lightning_pixi_show_planner import (
    LightningPixiShowPlanner,
)

_PNG = b"\x89PNG\r\n\x1a\nsynthetic-test-crop"


def _planning_request(
    *, rig_tier: str = "FULL_AUTO_RIG", part_roles: tuple[str, ...] = ("left-wing", "right-wing")
) -> PixiShowPlanningRequest:
    return PixiShowPlanningRequest(
        request_id="internal-test-request",
        session_id="internal-session-id",
        source_artifact_ref="internal-artifact-ref",
        source_sha256="a" * 64,
        package_id="rig-package-test",
        subject_region=SourceRegionV1(x=0.35, y=0.3, width=0.3, height=0.35),
        confirmed_subject_id="anchor-bird",
        confirmed_subject_label="con chim",
        subject_tags=("bird", "animal"),
        experience_spec_id="spec-bird",
        experience_spec_version=1,
        renderer_duration_seconds=20,
        activity_id="ACT-0001",
        activity_label="Khám phá đôi cánh",
        objective_ids=("OBJ-0001",),
        objective_labels=("Quan sát hình dạng",),
        rig_tier=rig_tier,
        part_roles=part_roles,
        candidate_assets=(
            PixiShowAssetCandidate(
                asset_id="asset-flower-1",
                label="Bông hoa",
                role="PROP",
                visual_description="Một bông hoa nhỏ màu vàng.",
                topic_tags=("hoa", "vườn"),
            ),
        ),
        source_crop_content_type="image/png",
        source_crop_bytes=_PNG,
    )


def _intent(**overrides: object) -> PixiShowIntentV1:
    value: dict[str, object] = {
        "visualSubjectHintId": "BIRD",
        "behaviorClass": "FLYER",
        "confidence": 0.82,
        "selectedAssetIds": ["asset-flower-1"],
        "durationSeconds": 20,
        "beats": [
            {
                "beatId": "notice",
                "startSeconds": 0,
                "endSeconds": 4,
                "action": "NOTICE",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "interact",
                "startSeconds": 5,
                "endSeconds": 10,
                "action": "INTERACT",
                "targetRole": "SUPPLEMENTAL_ASSET",
                "assetId": "asset-flower-1",
                "x": 0.18,
                "y": 0.8,
            },
            {
                "beatId": "settle",
                "startSeconds": 12,
                "endSeconds": 17,
                "action": "SETTLE",
                "targetRole": "SOURCE_SUBJECT",
            },
        ],
        "endingStill": True,
    }
    value.update(overrides)
    return PixiShowIntentV1.model_validate(value)


def test_compiler_emits_versioned_plan_bound_to_gate_a_gate_b_and_rig() -> None:
    plan = compile_pixi_show_plan(
        request=_planning_request(), intent=_intent(), plan_id="show-synthetic-1"
    )

    assert plan.contract_name == "PixiShowPlanV1"
    assert plan.plan_id == "show-synthetic-1"
    assert plan.session_id == "internal-session-id"
    assert plan.package_id == "rig-package-test"
    assert plan.confirmed_subject_id == "anchor-bird"
    assert plan.experience_spec_ref.id == "spec-bird"
    assert plan.selected_asset_ids == ("asset-flower-1",)
    assert plan.duration_seconds == 20


def test_compiler_rejects_model_subject_disagreement_for_caregiver_reconfirmation() -> None:
    with pytest.raises(PixiShowPlannerUnavailable, match="SUBJECT_RECONFIRMATION_REQUIRED"):
        compile_pixi_show_plan(
            request=_planning_request(),
            intent=_intent(visualSubjectHintId="QUADRUPED"),
        )


def test_compiler_requires_plan_duration_to_match_renderer_timeline() -> None:
    with pytest.raises(PixiShowPlannerUnavailable, match="PLANNER_INVALID_RESULT"):
        compile_pixi_show_plan(
            request=replace(_planning_request(), renderer_duration_seconds=15),
            intent=_intent(),
        )


def test_compiler_rejects_motion_without_validated_matching_parts() -> None:
    intent = _intent(
        beats=[
            {
                "beatId": "flap",
                "startSeconds": 0,
                "endSeconds": 4,
                "action": "FLAP",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "interact",
                "startSeconds": 5,
                "endSeconds": 10,
                "action": "INTERACT",
                "targetRole": "SUPPLEMENTAL_ASSET",
                "assetId": "asset-flower-1",
                "x": 0.18,
                "y": 0.8,
            },
            {
                "beatId": "settle",
                "startSeconds": 12,
                "endSeconds": 17,
                "action": "SETTLE",
                "targetRole": "SOURCE_SUBJECT",
            },
        ],
    )
    with pytest.raises(PixiShowPlannerUnavailable, match="BEHAVIOR_CAPABILITY_UNSUPPORTED"):
        compile_pixi_show_plan(
            request=_planning_request(rig_tier="CUTOUT_MICRO_MOTION", part_roles=()),
            intent=intent,
        )


def test_intent_schema_rejects_non_still_ending_or_missing_rest_window() -> None:
    with pytest.raises(ValidationError):
        _intent(
            beats=[
                {
                    "beatId": "notice",
                    "startSeconds": 0,
                    "endSeconds": 4,
                    "action": "NOTICE",
                    "targetRole": "SOURCE_SUBJECT",
                },
                {
                    "beatId": "interact",
                    "startSeconds": 5,
                    "endSeconds": 10,
                    "action": "INTERACT",
                    "targetRole": "SUPPLEMENTAL_ASSET",
                    "assetId": "asset-flower-1",
                },
                {
                    "beatId": "finish",
                    "startSeconds": 12,
                    "endSeconds": 19,
                    "action": "APPROACH",
                    "targetRole": "SOURCE_SUBJECT",
                },
            ]
        )


class _RecordingTransport:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.paths: list[str] = []
        self.payloads: list[dict[str, object]] = []

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.paths.append(path)
        self.payloads.append(payload)
        return self.response


def test_lightning_adapter_sends_only_minimized_crop_and_allowlisted_context_once() -> None:
    response = _intent().model_dump(mode="json", by_alias=True)
    transport = _RecordingTransport(response)
    planner = LightningPixiShowPlanner(transport=transport)

    result = planner.plan(_planning_request())

    assert result.visual_subject_hint_id == "BIRD"
    assert transport.paths == ["/v2/pixi/show-plan"]
    payload = transport.payloads[0]
    assert "session_id" not in payload and "source_artifact_ref" not in payload
    crop = payload["sourceCrop"]
    assert isinstance(crop, dict)
    assert crop["sha256"] == sha256(_PNG).hexdigest()
    assert base64.b64decode(crop["contentBase64"]) == _PNG
    assert payload["candidateAssets"][0]["assetId"] == "asset-flower-1"
    assert payload["rendererDurationSeconds"] == 20
    assert payload["sourceSubjectRegion"] == {
        "x": 0.35,
        "y": 0.3,
        "width": 0.3,
        "height": 0.35,
    }


def test_lightning_adapter_makes_no_call_without_runtime_eligible_candidates() -> None:
    transport = _RecordingTransport(_intent().model_dump(mode="json", by_alias=True))
    planner = LightningPixiShowPlanner(transport=transport)
    request = _planning_request()
    request = replace(request, candidate_assets=())

    with pytest.raises(PixiShowPlannerUnavailable, match="NO_ELIGIBLE_ASSETS"):
        planner.plan(request)
    assert transport.paths == []


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_part_proposals_follow_visible_color_components_and_parent_mask() -> None:
    source = Image.new("RGB", (180, 120), "white")
    draw = ImageDraw.Draw(source)
    draw.ellipse((18, 15, 78, 68), fill=(235, 120, 30))
    draw.ellipse((102, 15, 162, 68), fill=(235, 120, 30))
    draw.rectangle((78, 36, 102, 105), fill=(20, 130, 240))
    mask = Image.new("L", source.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((18, 15, 78, 68), fill=255)
    mask_draw.ellipse((102, 15, 162, 68), fill=255)
    mask_draw.rectangle((78, 36, 102, 105), fill=255)

    parts = derive_part_masks_from_subject_mask(_png(source), _png(mask), RigArchetype.BUTTERFLY)

    assert {part.part_id for part in parts} == {"left-wing", "body", "right-wing"}
    assert len({part.confidence for part in parts}) > 1
    parent = mask.load()
    for part in parts:
        with Image.open(BytesIO(part.mask_png)) as part_image:
            part_pixels = part_image.convert("L").load()
            assert part_pixels is not None and parent is not None
            assert all(
                part_pixels[x, y] == 0 or parent[x, y] != 0
                for y in range(source.height)
                for x in range(source.width)
            )


def test_part_proposals_refuse_uniform_subject_without_internal_boundary_evidence() -> None:
    source = Image.new("RGB", (96, 96), "white")
    ImageDraw.Draw(source).ellipse((16, 12, 80, 84), fill=(190, 85, 45))
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).ellipse((16, 12, 80, 84), fill=255)

    assert (
        derive_part_masks_from_subject_mask(_png(source), _png(mask), RigArchetype.BUTTERFLY) == ()
    )
