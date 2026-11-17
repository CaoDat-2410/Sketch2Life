"""Synthetic object-aware drawing mechanics, fidelity and video decode checks."""

from __future__ import annotations

import hashlib
import io

import imageio.v2 as imageio
import numpy as np
import pytest
from PIL import Image, ImageDraw
from tools.story_whiteboard_v2_pilot import render_fixture
from tools.story_world_v2_fixture import make_prototype as family_prototype
from tools.story_world_v2_ocean_fixture import fixture_inputs as ocean_inputs
from tools.story_world_v2_ocean_fixture import make_prototype as ocean_prototype

from sketch2life.application.services.story_draw_schedule_v2 import build_draw_schedule
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import build_source_asset_registry
from sketch2life.contracts.schemas.story_strokes_v2 import (
    SceneDrawScheduleV2,
    SourceObjectStrokesV2,
)
from sketch2life.contracts.schemas.story_video import stable_model_hash
from sketch2life.infrastructure.media.object_stroke_engine_v2 import (
    LocalObjectAwareStrokeEngine,
    extract_object_strokes,
)
from sketch2life.infrastructure.media.scene_state_composer import SceneStateComposer
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import render_scene_pilot


@pytest.mark.parametrize("fixture", ["family", "ocean-png", "ocean-jpeg"])
def test_object_strokes_are_source_bound_and_pen_down_paths_are_connected(fixture: str) -> None:
    result = family_prototype() if fixture == "family" else ocean_prototype(
        image_format="JPEG" if fixture == "ocean-jpeg" else "PNG",
    )
    registry = result.registry
    engine = LocalObjectAwareStrokeEngine()
    objects = tuple(engine.extract_object(registry, obj.object_id)
                    for obj in registry.world.source_objects)
    assert len(objects) == len(registry.world.source_objects)
    for obj in objects:
        spec = next(
            item for item in registry.world.source_objects if item.object_id == obj.object_id
        )
        assert obj.source_asset_sha256 == spec.asset_sha256
        assert obj.source_mask_sha256 == spec.source_mask_sha256
        assert obj.source_image_sha256 == spec.source_image_sha256
        assert obj.outline_paths and obj.color_paths
        assert all(path.pen_up_before for path in (
            *obj.outline_paths, *obj.detail_paths, *obj.color_paths,
        ))
        for path in (*obj.outline_paths, *obj.detail_paths):
            assert all(max(abs(x0 - x1), abs(y0 - y1)) <= 1 for
                       (x0, y0), (x1, y1) in zip(path.points, path.points[1:], strict=False))
    schedule = build_draw_schedule(result.scene_plan.scenes[0], objects, duration_seconds=6)
    phases = [item.phase for item in schedule.strokes]
    assert phases == sorted(phases, key={"OUTLINE": 0, "DETAIL": 1, "COLOR": 2}.get)
    assert schedule.strokes[0].start_seconds == 0
    assert schedule.strokes[-1].end_seconds < schedule.duration_seconds
    assert all(a.end_seconds <= b.start_seconds for a, b in zip(
        schedule.strokes, schedule.strokes[1:], strict=False,
    ))


@pytest.mark.parametrize("fixture", ["family", "ocean-png"])
def test_encoded_pilot_has_progress_and_decodable_last_frame(tmp_path, fixture: str) -> None:
    metrics = render_fixture(fixture, tmp_path, duration_seconds=4, fps=10)
    assert metrics["final_mae"] == 0
    assert metrics["final_changed_pixels"] == 0
    assert metrics["source_mask_coverage"] == 1
    assert (tmp_path / f"{fixture}-v2-pilot.mp4").stat().st_size > 1000
    reader = imageio.get_reader(str(tmp_path / f"{fixture}-v2-pilot.mp4"), format="ffmpeg")
    try:
        first = np.asarray(reader.get_data(0))
        middle = np.asarray(reader.get_data(20))
        last = np.asarray(reader.get_data(39))
        assert reader.get_meta_data()["fps"] == 10
        assert first.shape == middle.shape == last.shape
        assert first.mean() > middle.mean()  # white board gains source color
        assert np.abs(first.astype("int16") - last.astype("int16")).mean() > 10
        assert np.abs(middle.astype("int16") - last.astype("int16")).mean() > 1
    finally:
        reader.close()
    sheet = Image.open(tmp_path / f"{fixture}-v2-0-25-50-75-100.png")
    assert sheet.width == first.shape[1] * 5


def test_transformed_scene_final_matches_canonical_composer(tmp_path) -> None:
    result = ocean_prototype()
    scene = result.scene_plan.scenes[1]  # approved TRANSLATE; target includes camera state
    objects = tuple(extract_object_strokes(result.registry, obj.object_id)
                    for obj in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=4, fps=10)
    pilot = render_scene_pilot(
        result.registry, scene, objects, schedule, video_path=tmp_path / "move.mp4",
        contact_sheet_path=tmp_path / "move.png", fps=10,
    )
    assert pilot.final_changed_pixels == 0
    sheet = Image.open(tmp_path / "move.png").convert("RGB")
    canonical = SceneStateComposer().render_scene(result.registry, scene)
    assert sheet.crop((canonical.width * 4, 25, canonical.width * 5,
                       canonical.height + 25)).tobytes() == canonical.tobytes()


def test_missing_or_tampered_asset_and_unsupported_action_fail_closed() -> None:
    result = family_prototype()
    first = result.registry.world.source_objects[0]
    del result.registry.asset_png_by_id[first.object_id]
    with pytest.raises(StoryWorldError, match="SOURCE_ASSET_MISMATCH"):
        extract_object_strokes(result.registry, first.object_id)
    other = ocean_prototype()
    scene = other.scene_plan.scenes[0].model_copy(update={"action": "WALK"})
    objects = tuple(extract_object_strokes(other.registry, obj.object_id)
                    for obj in other.registry.world.source_objects)
    with pytest.raises(StoryWorldError, match="UNSUPPORTED_ACTION"):
        build_draw_schedule(scene, objects, duration_seconds=4)
    with pytest.raises(StoryWorldError, match="DRAW_TIMING_INFEASIBLE"):
        build_draw_schedule(other.scene_plan.scenes[0], objects, duration_seconds=.5)


def test_multicolor_thin_curved_detail_source_is_not_repainted() -> None:
    package, segments, source_bytes, specs, additions, events = ocean_inputs()
    source = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    painter = ImageDraw.Draw(source)
    # Extra source texture is drawn *inside* an existing reviewed fish mask.
    painter.arc((70, 94, 105, 130), 25, 270, fill="#793de0", width=2)
    painter.line(((78, 111), (88, 116), (98, 108)), fill="#d2397c", width=1)
    stream = io.BytesIO()
    source.save(stream, format="PNG")
    body = stream.getvalue()
    package = package.model_copy(update={
        "source_image_sha256": hashlib.sha256(body).hexdigest(), "package_hash": "0" * 64,
    })
    package = package.model_copy(update={
        "package_hash": stable_model_hash(package, exclude={"package_hash"}),
    })
    registry = build_source_asset_registry(
        package=package, segments=segments, source_image_bytes=body,
        source_objects=specs, narration_objects=additions, events=events,
    )
    fish = extract_object_strokes(registry, "fish-blue")
    assert fish.detail_paths
    cutout = Image.open(io.BytesIO(registry.asset_png_by_id["fish-blue"])).convert("RGBA")
    assert any(pixel[:3] == (121, 61, 224) for pixel in cutout.get_flattened_data())


def test_versioned_stroke_and_schedule_contract_round_trip() -> None:
    result = ocean_prototype()
    objects = tuple(extract_object_strokes(result.registry, obj.object_id)
                    for obj in result.registry.world.source_objects)
    stroke = SourceObjectStrokesV2.model_validate_json(objects[0].model_dump_json())
    assert stroke == objects[0]
    schedule = build_draw_schedule(result.scene_plan.scenes[0], objects, duration_seconds=6)
    assert SceneDrawScheduleV2.model_validate_json(schedule.model_dump_json()) == schedule
