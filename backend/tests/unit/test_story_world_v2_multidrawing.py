"""Second drawing, codecs and fail-closed paths without GPU or inference."""

from __future__ import annotations

import hashlib
import io
from dataclasses import replace

import pytest
from PIL import Image
from tools.story_world_v2_fixture import fixture_inputs as family_inputs
from tools.story_world_v2_fixture import make_prototype as family_prototype
from tools.story_world_v2_ocean_fixture import fixture_inputs as ocean_inputs
from tools.story_world_v2_ocean_fixture import make_prototype as ocean_prototype

from sketch2life.application.services.story_video_pipeline import StoryVideoPipeline
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import (
    SourceAssetRegistry,
    build_source_asset_registry,
)
from sketch2life.infrastructure.media.scene_state_composer import SceneStateComposer


@pytest.mark.parametrize("kind,codec", [("family", "PNG"), ("ocean", "PNG"), ("ocean", "JPEG")])
def test_distinct_drawings_share_world_registry_composer_with_exact_source_pixels(
    kind: str, codec: str,
) -> None:
    inputs = family_inputs() if kind == "family" else ocean_inputs(image_format=codec)
    result = family_prototype() if kind == "family" else ocean_prototype(image_format=codec)
    package, segments, source_bytes, specs, _additions, events = inputs
    world, plan = result.registry.world, result.scene_plan
    assert result.approval_verification == "UNVERIFIED_PROTOTYPE"
    assert world.package_hash == package.package_hash
    assert len(plan.scenes) == 4 and plan.duration_seconds == 40
    assert len(world.source_objects) == len(specs)
    assert {item.object_id for item in world.source_objects} == {item.object_id for item in specs}
    assert {event.segment_id for event in events} == {segment.segment_id for segment in segments}
    assert all(event.approved_fact_ids and event.confirmed_anchor_ids for event in events)
    assert all(a.target_states == b.starting_states for a, b in zip(
        plan.scenes, plan.scenes[1:], strict=False,
    ))
    assert set(plan.scenes[0].source_object_ids) == set(plan.scenes[1].source_object_ids)
    decoded = Image.open(io.BytesIO(source_bytes)).convert("RGBA")
    for obj in world.source_objects:
        assert obj.source_image_sha256 == hashlib.sha256(source_bytes).hexdigest()
        cutout_bytes = result.registry.asset_png_by_id[obj.object_id]
        assert obj.asset_sha256 == hashlib.sha256(cutout_bytes).hexdigest()
        cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")
        mask = Image.open(io.BytesIO(result.registry.mask_png_by_id[obj.object_id])).convert("L")
        assert obj.source_mask_sha256 == hashlib.sha256(
            result.registry.mask_png_by_id[obj.object_id],
        ).hexdigest()
        box = mask.getbbox()
        assert box is not None
        original = decoded.crop(box)
        local_mask = mask.crop(box)
        assert cutout.size == original.size
        for pixel, source_pixel, alpha in zip(
            cutout.get_flattened_data(), original.get_flattened_data(),
            local_mask.get_flattened_data(), strict=True,
        ):
            if alpha:
                assert pixel == source_pixel
        assert obj.appearance_colors[0].startswith("#")
    composer = SceneStateComposer()
    stills = [composer.render_scene(result.registry, scene) for scene in plan.scenes[:2]]
    assert stills[0].tobytes() != stills[1].tobytes()


@pytest.mark.parametrize("codec", ["PNG", "JPEG"])
@pytest.mark.parametrize(
    "failure",
    ["missing", "no_digest", "wrong_size", "non_binary", "overlap", "duplicate", "swapped"],
)
def test_ocean_masks_fail_closed(codec: str, failure: str) -> None:
    package, segments, source, specs, additions, events = ocean_inputs(image_format=codec)
    if failure == "missing":
        item = replace(specs[0], mask_png=None)
    elif failure == "no_digest":
        item = replace(specs[0], reviewed_mask_sha256=None)
    elif failure == "duplicate":
        item = replace(specs[0], object_id=specs[1].object_id)
    elif failure in {"overlap", "swapped"}:
        item = replace(specs[0], mask_png=specs[1].mask_png)
    else:
        size = (1, 1) if failure == "wrong_size" else (480, 320)
        mask = Image.new("L", size, 128 if failure == "non_binary" else 255)
        stream = io.BytesIO()
        mask.save(stream, format="PNG")
        item = replace(specs[0], mask_png=stream.getvalue())
    objects = (
        (item, replace(specs[1], mask_png=specs[0].mask_png), *specs[2:])
        if failure == "swapped" else (item, *specs[1:])
    )
    with pytest.raises(StoryWorldError) as error:
        build_source_asset_registry(
            package=package, segments=segments, source_image_bytes=source,
            source_objects=objects, narration_objects=additions, events=events,
        )
    assert error.value.code == "NEEDS_MASK_REVIEW"


def test_ocean_unapproved_event_cannot_plan_or_render() -> None:
    package, segments, source, specs, additions, events = ocean_inputs()
    unreviewed = events[1].model_copy(update={"approval_status": "NEEDS_APPROVAL"})
    with pytest.raises(StoryWorldError) as error:
        build_source_asset_registry(
            package=package, segments=segments, source_image_bytes=source,
            source_objects=specs, narration_objects=additions,
            events=(events[0], unreviewed, *events[2:]),
        )
    assert error.value.code == "NEEDS_APPROVAL"


def test_ocean_missing_or_changed_asset_is_not_silent_success() -> None:
    result = ocean_prototype()
    first_id = result.registry.world.source_objects[0].object_id
    for replacement in (None, b"tampered"):
        assets = dict(result.registry.asset_png_by_id)
        if replacement is None:
            del assets[first_id]
        else:
            assets[first_id] = replacement
        registry = SourceAssetRegistry(
            world=result.registry.world, asset_png_by_id=assets,
            mask_png_by_id=result.registry.mask_png_by_id,
        )
        with pytest.raises(StoryWorldError) as error:
            SceneStateComposer().render_scene(registry, result.scene_plan.scenes[0])
        assert error.value.code == "SOURCE_ASSET_MISMATCH"


def test_ocean_unsupported_action_and_flag_off_do_not_use_v1() -> None:
    result = ocean_prototype()
    scene = result.scene_plan.scenes[1].model_copy(update={"action": "SWIM"})
    with pytest.raises(StoryWorldError) as error:
        SceneStateComposer().render_scene(result.registry, scene)
    assert error.value.code == "UNSUPPORTED_ACTION"
    package, segments, source, specs, additions, events = ocean_inputs()
    pipeline = StoryVideoPipeline(
        narration=None, illustrations=None, motion=None, assembler=None,
    )  # type: ignore[arg-type]
    with pytest.raises(StoryWorldError) as error:
        pipeline.run_v2_prototype(
            package, segments, source_image_bytes=source, source_objects=specs,
            narration_objects=additions, events=events,
            measured_segment_durations=(10.0,) * 4,
        )
    assert error.value.code == "V2_DISABLED"
