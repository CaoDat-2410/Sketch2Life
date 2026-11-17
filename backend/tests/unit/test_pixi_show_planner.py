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
from sketch2life.application.services.pixi_show_compiler import (
    _confirmed_subject_hint,
    compile_adaptive_pixi_show_plan,
    compile_pixi_show_plan,
)
from sketch2life.contracts.schemas.auto_rig import RigArchetype, RigDeliveryTier
from sketch2life.contracts.schemas.pixi_motion_cycle import (
    PixiRendererShowEnvelopeV2,
    PixiRendererShowEnvelopeV3,
    PixiRendererShowEnvelopeV4,
)
from sketch2life.contracts.schemas.pixi_show import (
    PixiShowIntentV2,
)
from sketch2life.contracts.schemas.renderer_v2 import (
    PixiRendererLaunchV2,
    VisualAnimationPlanV2,
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
                preview_bytes=_png(Image.new("RGBA", (8, 8), (240, 180, 40, 255))),
            ),
        ),
        source_crop_content_type="image/png",
        source_crop_bytes=_PNG,
        chosen_topic_labels=("Cùng khám phá chim",),
    )


def _intent(**overrides: object) -> PixiShowIntentV2:
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
        "renderStrategy": "FULL_AUTO_RIG",
        "sceneThemeAssetId": None,
    }
    value.update(overrides)
    return PixiShowIntentV2.model_validate(value)


def test_compiler_emits_versioned_plan_bound_to_gate_a_gate_b_and_rig() -> None:
    plan = compile_pixi_show_plan(
        request=_planning_request(), intent=_intent(), plan_id="show-synthetic-1"
    )

    assert plan.contract_name == "PixiShowPlanV2"
    assert plan.plan_id == "show-synthetic-1"
    assert plan.session_id == "internal-session-id"
    assert plan.package_id == "rig-package-test"
    assert plan.confirmed_subject_id == "anchor-bird"
    assert plan.experience_spec_ref.id == "spec-bird"
    assert plan.selected_asset_ids == ("asset-flower-1",)
    assert plan.duration_seconds == 20


@pytest.mark.parametrize(
    ("label", "expected"),
    (
        ("cà rốt", "PLANT"),
        ("hóa thạch", "OBJECT"),
        ("con gà", "BIRD"),
        ("ô tô", "VEHICLE"),
        ("chim", "BIRD"),
        ("bướm", "INSECT"),
    ),
)
def test_vietnamese_subject_hints_use_longest_whole_phrase(label: str, expected: str) -> None:
    assert _confirmed_subject_hint(label, ()).value == expected


def test_conflicting_equal_specificity_subject_hints_remain_unknown() -> None:
    assert _confirmed_subject_hint("chim xe", ()).value == "UNKNOWN"


def test_compiler_rejects_model_subject_disagreement_for_caregiver_reconfirmation() -> None:
    with pytest.raises(PixiShowPlannerUnavailable, match="SUBJECT_RECONFIRMATION_REQUIRED"):
        compile_pixi_show_plan(
            request=_planning_request(),
            intent=_intent(visualSubjectHintId="QUADRUPED"),
        )


def test_compiler_accepts_source_only_show_when_catalog_has_no_eligible_assets() -> None:
    intent = _intent(
        selectedAssetIds=[],
        beats=[
            {
                "beatId": "notice",
                "startSeconds": 0,
                "endSeconds": 4,
                "action": "NOTICE",
                "targetRole": "SOURCE_SUBJECT",
            },
            {
                "beatId": "flap",
                "startSeconds": 5,
                "endSeconds": 10,
                "action": "FLAP",
                "targetRole": "SOURCE_SUBJECT",
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
    request = replace(_planning_request(), candidate_assets=())

    plan = compile_pixi_show_plan(request=request, intent=intent)

    assert plan.contract_name == "PixiShowPlanV2"
    assert plan.selected_asset_ids == ()
    assert all(beat.target_role == "SOURCE_SUBJECT" for beat in plan.beats)


def test_v3_envelope_accepts_empty_companion_reads_without_relaxing_v2() -> None:
    intent = _intent(
        selectedAssetIds=[],
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
                "targetRole": "SOURCE_SUBJECT",
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
    plan = compile_pixi_show_plan(
        request=replace(_planning_request(), candidate_assets=()),
        intent=intent,
    )
    spec_ref = {"id": "spec-bird", "version": 1}
    animation = VisualAnimationPlanV2(
        contractName="VisualAnimationPlanV2",
        contractVersion="2.0",
        planId="visual-plan-test",
        sessionId="internal-session-id",
        experienceSpecRef=spec_ref,
        packageId="rig-package-test",
        archetype=RigArchetype.BIRD,
        tier=RigDeliveryTier.FULL_AUTO_RIG,
        durationSeconds=20,
        tracks=(),
        learningBridgeVi="Cùng khám phá chuyển động.",
    )
    launch = PixiRendererLaunchV2(
        contractName="PixiRendererLaunchV2",
        contractVersion="2.0",
        sessionId="internal-session-id",
        expectedSessionVersion=3,
        experienceSpecRef=spec_ref,
        sourceReadEndpoint="/v1/renderer/source",
        sourceReadCapability="s" * 48,
        sourceSha256="a" * 64,
        packageReadEndpoint="/v1/renderer/rig-package",
        packageReadCapability="p" * 48,
        packageSha256="b" * 64,
        packageReadExpiresAt="2026-10-03T00:00:00Z",
        partMaskReads=(),
        rigParts=(),
        animationPlan=animation,
        fallbackLaunch={},
    )

    envelope = PixiRendererShowEnvelopeV3(
        contractName="PixiRendererShowEnvelopeV3",
        contractVersion="3.0",
        rendererLaunchV2=launch,
        showPlan=plan,
        assetReads=(),
        spriteCycleStatus="NOT_APPLICABLE",
    )

    assert envelope.show_plan.selected_asset_ids == ()
    with pytest.raises(ValidationError):
        PixiRendererShowEnvelopeV2.model_validate(
            {
                "contractName": "PixiRendererShowEnvelopeV2",
                "contractVersion": "2.0",
                "rendererLaunchV2": launch,
                "showPlan": plan,
                "assetReads": [],
                "spriteCycleStatus": "NOT_APPLICABLE",
            }
        )


def test_adaptive_compiler_binds_topic_scene_to_verified_cutout_and_environment_read() -> None:
    environment = PixiShowAssetCandidate(
        asset_id="asset-meadow-bg",
        label="Đồng cỏ",
        role="ENVIRONMENT",
        visual_description="Một đồng cỏ xanh dịu, phong cách nét vẽ trẻ em.",
        topic_tags=("chim", "đồng cỏ"),
        preview_bytes=_png(Image.new("RGBA", (12, 8), (90, 180, 90, 255))),
    )
    request = replace(
        _planning_request(rig_tier="CUTOUT_MICRO_MOTION", part_roles=()),
        candidate_assets=(*_planning_request().candidate_assets, environment),
    )
    intent = _intent(
        renderStrategy="CUTOUT_TOPIC_SCENE",
        sceneThemeAssetId="asset-meadow-bg",
    )
    plan = compile_adaptive_pixi_show_plan(request=request, intent=intent)
    spec_ref = {"id": "spec-bird", "version": 1}
    animation = VisualAnimationPlanV2(
        contractName="VisualAnimationPlanV2",
        contractVersion="2.0",
        planId="visual-plan-scene",
        sessionId="internal-session-id",
        experienceSpecRef=spec_ref,
        packageId="rig-package-test",
        archetype=RigArchetype.BIRD,
        tier=RigDeliveryTier.CUTOUT_MICRO_MOTION,
        durationSeconds=20,
        tracks=(),
        learningBridgeVi="Cùng khám phá chuyển động.",
    )
    launch = PixiRendererLaunchV2(
        contractName="PixiRendererLaunchV2",
        contractVersion="2.0",
        sessionId="internal-session-id",
        expectedSessionVersion=3,
        experienceSpecRef=spec_ref,
        sourceReadEndpoint="/v1/renderer/source",
        sourceReadCapability="s" * 48,
        sourceSha256="a" * 64,
        packageReadEndpoint="/v1/renderer/rig-package",
        packageReadCapability="p" * 48,
        packageSha256="b" * 64,
        packageReadExpiresAt="2026-10-03T00:00:00Z",
        partMaskReads=(),
        rigParts=(),
        animationPlan=animation,
        fallbackLaunch={},
    )
    envelope = PixiRendererShowEnvelopeV4(
        contractName="PixiRendererShowEnvelopeV4",
        contractVersion="4.0",
        rendererLaunchV2=launch,
        showPlan=plan,
        assetReads=(
            {
                "assetId": "asset-flower-1",
                "readEndpoint": "/v1/renderer/pixi-asset",
                "readCapability": "f" * 48,
                "sha256": "c" * 64,
                "byteLength": 100,
            },
            {
                "assetId": "asset-meadow-bg",
                "readEndpoint": "/v1/renderer/pixi-asset",
                "readCapability": "m" * 48,
                "sha256": "d" * 64,
                "byteLength": 100,
            },
        ),
        spriteCycleStatus="NOT_APPLICABLE",
    )

    assert envelope.show_plan.render_strategy == "CUTOUT_TOPIC_SCENE"
    assert envelope.show_plan.chosen_topic_label == "Cùng khám phá chim"
    assert envelope.show_plan.scene_theme_asset_id == "asset-meadow-bg"


def test_adaptive_compiler_rejects_environment_as_companion_and_unverified_full_rig() -> None:
    request = replace(
        _planning_request(rig_tier="CUTOUT_MICRO_MOTION", part_roles=()),
        candidate_assets=(
            replace(_planning_request().candidate_assets[0], role="ENVIRONMENT"),
        ),
    )
    with pytest.raises(PixiShowPlannerUnavailable, match="PLANNER_INVALID_RESULT"):
        compile_adaptive_pixi_show_plan(
            request=request,
            intent=_intent(
                renderStrategy="CUTOUT_MICRO_MOTION",
            ),
        )
    with pytest.raises(PixiShowPlannerUnavailable, match="BEHAVIOR_CAPABILITY_UNSUPPORTED"):
        compile_adaptive_pixi_show_plan(
            request=request,
            intent=_intent(renderStrategy="FULL_AUTO_RIG"),
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
    assert transport.paths == ["/v4/pixi/show-plan"]
    payload = transport.payloads[0]
    assert "session_id" not in payload and "source_artifact_ref" not in payload
    crop = payload["sourceCrop"]
    assert isinstance(crop, dict)
    assert crop["sha256"] == sha256(_PNG).hexdigest()
    assert base64.b64decode(crop["contentBase64"]) == _PNG
    assert payload["candidateAssets"][0]["assetId"] == "asset-flower-1"
    assert payload["candidateAssets"][0]["previewSha256"] == sha256(
        _png(Image.new("RGBA", (8, 8), (240, 180, 40, 255)))
    ).hexdigest()
    assert payload["chosenTopicLabels"] == ["Cùng khám phá chim"]
    assert payload["rendererDurationSeconds"] == 20
    assert payload["sourceSubjectRegion"] == {
        "x": 0.35,
        "y": 0.3,
        "width": 0.3,
        "height": 0.35,
    }


def test_lightning_adapter_rejects_hallucinated_scene_theme_id() -> None:
    response = _intent(
        renderStrategy="CUTOUT_TOPIC_SCENE",
        sceneThemeAssetId="invented-meadow",
    ).model_dump(mode="json", by_alias=True)
    transport = _RecordingTransport(response)
    planner = LightningPixiShowPlanner(transport=transport)

    with pytest.raises(PixiShowPlannerUnavailable, match="PLANNER_INVALID_RESULT"):
        planner.plan(_planning_request())

    assert transport.paths == ["/v4/pixi/show-plan"]


def test_lightning_adapter_surfaces_planner_timeout_without_retry() -> None:
    class TimeoutTransport:
        paths: list[str] = []

        def post_json(self, path: str, _payload: dict[str, object]) -> dict[str, object]:
            self.paths.append(path)
            raise TimeoutError

    transport = TimeoutTransport()
    planner = LightningPixiShowPlanner(transport=transport)

    with pytest.raises(PixiShowPlannerUnavailable, match="PLANNER_TIMEOUT"):
        planner.plan(_planning_request())

    assert transport.paths == ["/v4/pixi/show-plan"]


def test_lightning_adapter_sends_empty_shortlist_for_subject_only_planning() -> None:
    subject_only_intent = _intent(
        selectedAssetIds=[],
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
                "targetRole": "SOURCE_SUBJECT",
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
    transport = _RecordingTransport(subject_only_intent.model_dump(mode="json", by_alias=True))
    planner = LightningPixiShowPlanner(transport=transport)
    request = _planning_request()
    request = replace(request, candidate_assets=())

    result = planner.plan(request)

    assert result.selected_asset_ids == ()
    assert transport.paths == ["/v4/pixi/show-plan"]
    assert transport.payloads[0]["candidateAssets"] == []


def test_lightning_adapter_rejects_missing_subject_region_before_provider_call() -> None:
    transport = _RecordingTransport(_intent().model_dump(mode="json", by_alias=True))
    planner = LightningPixiShowPlanner(transport=transport)
    request = replace(_planning_request(), subject_region=None)

    with pytest.raises(PixiShowPlannerUnavailable) as error:
        planner.plan(request)

    assert error.value.code == "SUBJECT_RECONFIRMATION_REQUIRED"
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
