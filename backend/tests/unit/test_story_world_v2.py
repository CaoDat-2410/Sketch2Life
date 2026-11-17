"""Level-1 tests: no child media, paid API, GPU or finished-video claim."""

from __future__ import annotations

import hashlib
import io
from dataclasses import replace

import pytest
from PIL import Image
from tools.story_world_v2_fixture import _NoProvider, fixture_inputs, make_prototype

from sketch2life.application.services.story_video_pipeline import StoryVideoPipeline
from sketch2life.application.services.story_world_model import (
    StoryWorldError,
    build_source_asset_registry,
)
from sketch2life.contracts.schemas.story_world_v2 import NarrationObjectV2
from sketch2life.infrastructure.media.scene_state_composer import SceneStateComposer


def _world(**overrides):
    package, segments, source, specs, additions, events = fixture_inputs()
    data = dict(package=package, segments=segments, source_image_bytes=source,
                source_objects=specs, narration_objects=additions, events=events)
    data.update(overrides)
    return build_source_asset_registry(**data)


def test_v2_preserves_ids_provenance_pixels_and_continuous_state() -> None:
    result = make_prototype()
    world, plan = result.registry.world, result.scene_plan
    assert world.contract == "StoryWorldModelV2" and plan.contract == "StoryScenePlanV2"
    assert len(plan.scenes) == 4 and plan.duration_seconds == 40
    assert {obj.object_id for obj in world.source_objects} == {
        "mother", "father", "child", "house", "tree", "flowers"
    }
    assert world.narration_objects[0].object_id == "butterfly"
    assert world.narration_objects[0].provenance == "APPROVED_NARRATION"
    assert world.narration_objects[0].asset_status == "PENDING"
    assert all(obj.provenance == "SOURCE_DRAWING" for obj in world.source_objects)
    assert [scene.event_ids for scene in plan.scenes] == [
        ("event-family-start",), ("event-walk",),
        ("event-butterfly",), ("event-return",),
    ]
    assert all(left.target_states == right.starting_states for left, right in zip(
        plan.scenes, plan.scenes[1:], strict=False
    ))
    assert plan.scenes[2].new_object_ids == ("butterfly",)
    assert plan.scenes[1].action == "TRANSLATE"
    assert plan.scenes[1].camera.center_x != .5
    package, _segments, source_bytes, *_ = fixture_inputs()
    source = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    assert world.source_image_sha256 == package.source_image_sha256
    for obj in world.source_objects:
        encoded = result.registry.asset_png_by_id[obj.object_id]
        assert hashlib.sha256(encoded).hexdigest() == obj.asset_sha256
        asset = Image.open(io.BytesIO(encoded)).convert("RGBA")
        mask = Image.open(io.BytesIO(result.registry.mask_png_by_id[obj.object_id])).convert("L")
        box = mask.getbbox()
        assert box is not None
        original = source.crop(box)
        local_mask = mask.crop(box)
        original_rgb = original.tobytes()
        asset_rgba = asset.tobytes()
        for index, alpha in enumerate(local_mask.tobytes()):
            if alpha:
                assert asset_rgba[4 * index:4 * index + 4] == (
                    original_rgb[3 * index:3 * index + 3] + b"\xff"
                )
    composer = SceneStateComposer()
    first = composer.render_scene(result.registry, plan.scenes[0])
    second = composer.render_scene(result.registry, plan.scenes[1])
    assert first.size == second.size == (600, 360)
    assert first.tobytes() != second.tobytes()


def test_v2_feature_flag_off_does_not_call_any_provider() -> None:
    package, segments, source, specs, additions, events = fixture_inputs()
    pipeline = StoryVideoPipeline(
        narration=_NoProvider(), illustrations=_NoProvider(),
        motion=_NoProvider(), assembler=_NoProvider(),
    )
    with pytest.raises(StoryWorldError, match="V2_DISABLED"):
        pipeline.run_v2_prototype(
            package, segments, source_image_bytes=source, source_objects=specs,
            narration_objects=additions, events=events,
            measured_segment_durations=(10.0,) * 4,
        )


def test_flag_on_does_not_silently_replace_v1_run() -> None:
    package, segments, *_ = fixture_inputs()
    pipeline = StoryVideoPipeline(
        narration=_NoProvider(), illustrations=_NoProvider(),
        motion=_NoProvider(), assembler=_NoProvider(), story_render_v2_enabled=True,
    )
    with pytest.raises(AssertionError, match="must not call a paid provider"):
        pipeline.run(package, segments)


@pytest.mark.parametrize("reason", ["missing", "wrong_size", "soft", "unreviewed"])
def test_invalid_mask_or_identity_blocks_instead_of_using_bbox(reason: str) -> None:
    package, segments, source, specs, additions, events = fixture_inputs()
    if reason == "missing":
        item = replace(specs[0], mask_png=None)
    elif reason == "unreviewed":
        item = replace(specs[0], identity_review_ref=None)
    else:
        mask = Image.new("L", (1, 1) if reason == "wrong_size" else (600, 360), 128)
        output = io.BytesIO()
        mask.save(output, format="PNG")
        item = replace(specs[0], mask_png=output.getvalue())
    with pytest.raises(StoryWorldError) as error:
        _world(source_objects=(item, *specs[1:]))
    assert error.value.code == "NEEDS_MASK_REVIEW"


def test_overlap_and_duplicate_identity_block() -> None:
    _, _, _, specs, _, _ = fixture_inputs()
    with pytest.raises(StoryWorldError) as error:
        _world(source_objects=(specs[0], replace(specs[1], mask_png=specs[0].mask_png),
                               *specs[2:]))
    assert error.value.code == "NEEDS_MASK_REVIEW"
    with pytest.raises(StoryWorldError) as error:
        _world(source_objects=(specs[0], replace(specs[1], object_id="mother"), *specs[2:]))
    assert error.value.code == "NEEDS_MASK_REVIEW"


def test_event_quote_fact_and_review_must_match_approved_segment() -> None:
    package, segments, source, specs, additions, events = fixture_inputs()
    for altered in (
        events[0].model_copy(update={"source_quote": "Gia đình bay lên mặt trăng."}),
        events[0].model_copy(update={"approved_fact_ids": ("fact-unknown",)}),
        events[0].model_copy(update={"approval_status": "NEEDS_APPROVAL"}),
    ):
        with pytest.raises(StoryWorldError) as error:
            _world(events=(altered, *events[1:]))
        assert error.value.code == "NEEDS_APPROVAL"
    # Changing approved text invalidates the immutable package/script binding.
    bad_segments = (segments[0].model_copy(update={"text": "Thêm sự kiện mới."}), *segments[1:])
    pipeline = StoryVideoPipeline(
        narration=_NoProvider(), illustrations=_NoProvider(),
        motion=_NoProvider(), assembler=_NoProvider(), story_render_v2_enabled=True,
    )
    with pytest.raises(StoryWorldError, match="NEEDS_APPROVAL"):
        pipeline.run_v2_prototype(
            package, bad_segments, source_image_bytes=source, source_objects=specs,
            narration_objects=additions, events=events,
            measured_segment_durations=(10.0,) * 4,
        )


def test_new_object_requires_matching_fact_and_remains_pending() -> None:
    _package, _segments, _source, _specs, additions, _events = fixture_inputs()
    unauthorized = NarrationObjectV2(
        object_id="dragon", object_type="dragon", segment_id="segment-3",
        approved_fact_ids=("fact-not-approved",), requested_appearance="purple",
        requested_action="appears", asset_status="PENDING",
    )
    with pytest.raises(StoryWorldError) as error:
        _world(narration_objects=(unauthorized,))
    assert error.value.code == "NEEDS_APPROVAL"
    with pytest.raises(StoryWorldError) as error:
        _world(narration_objects=(additions[0].model_copy(update={"asset_status": "GENERATED"}),))
    assert error.value.code == "NEEDS_APPROVAL"


def test_unsupported_new_object_and_running_do_not_fake_success() -> None:
    result = make_prototype()
    with pytest.raises(StoryWorldError) as error:
        SceneStateComposer().render_scene(result.registry, result.scene_plan.scenes[2])
    assert error.value.code == "UNSUPPORTED_ACTION"
    running = result.scene_plan.scenes[1].model_copy(update={"action": "RUN"})
    with pytest.raises(StoryWorldError) as error:
        SceneStateComposer().render_scene(result.registry, running)
    assert error.value.code == "UNSUPPORTED_ACTION"


def test_duration_and_event_partition_fail_with_structured_reason() -> None:
    package, segments, source, specs, additions, events = fixture_inputs()
    pipeline = StoryVideoPipeline(
        narration=_NoProvider(), illustrations=_NoProvider(),
        motion=_NoProvider(), assembler=_NoProvider(), story_render_v2_enabled=True,
    )
    for durations, expected in (
        ((8.0,) * 4, "DURATION_OUT_OF_RANGE"),
        ((20.0, 4.0, 10.0, 16.0), "SCENE_PARTITION_IMPOSSIBLE"),
    ):
        with pytest.raises(StoryWorldError) as error:
            pipeline.run_v2_prototype(
                package, segments, source_image_bytes=source, source_objects=specs,
                narration_objects=additions, events=events,
                measured_segment_durations=durations,
            )
        assert error.value.code == expected
