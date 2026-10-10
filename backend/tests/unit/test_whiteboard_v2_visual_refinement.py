"""Milestone 2.1 source-canvas, fallback and decoded-video evidence tests."""

from __future__ import annotations

import hashlib
import io
from dataclasses import replace

import imageio.v2 as imageio
import numpy as np
import pytest
from PIL import Image, ImageDraw
from tools.story_whiteboard_v2_pilot import render_fixture
from tools.story_world_v2_fixture import fixture_inputs as family_inputs
from tools.story_world_v2_fixture import make_prototype as family_prototype
from tools.story_world_v2_ocean_fixture import fixture_inputs as ocean_inputs
from tools.story_world_v2_ocean_fixture import make_prototype as ocean_prototype

from sketch2life.application.services.story_draw_schedule_v2 import build_draw_schedule
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import build_source_asset_registry
from sketch2life.contracts.schemas.story_video import stable_model_hash
from sketch2life.infrastructure.media.object_stroke_engine_v2 import extract_object_strokes
from sketch2life.infrastructure.media.scene_state_composer import (
    SceneStateComposer,
    source_canvas_layers,
)
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import render_scene_pilot


@pytest.mark.parametrize("kind", ["family", "ocean-png", "ocean-jpeg"])
def test_static_scene_matches_every_decoded_source_pixel(kind: str) -> None:
    result = family_prototype() if kind == "family" else ocean_prototype(
        image_format="JPEG" if kind == "ocean-jpeg" else "PNG"
    )
    source = Image.open(io.BytesIO(result.registry.source_image_bytes)).convert("RGBA")
    white = Image.new("RGBA", source.size, "white")
    expected = Image.alpha_composite(white, source).convert("RGB")
    actual = SceneStateComposer().render_scene(result.registry, result.scene_plan.scenes[0])
    assert actual.tobytes() == expected.tobytes()


def test_moving_scene_preserves_known_background_and_marks_occlusion_limit() -> None:
    result = ocean_prototype()
    original, background = source_canvas_layers(result.registry)
    scene = result.scene_plan.scenes[1]
    target = SceneStateComposer().render_scene(result.registry, scene)
    assert target.getpixel((0, 0)) == original.convert("RGB").getpixel((0, 0))
    assert target.getpixel((475, 310)) == original.convert("RGB").getpixel((475, 310))
    # Previously occluded pixels cannot be recovered from one source image.
    assert background.getpixel((90, 110)) != original.getpixel((90, 110))
    assert background.getpixel((90, 110))[:3] != (255, 255, 255)


def test_transparent_png_edges_match_white_composited_source() -> None:
    package, segments, body, specs, additions, events = family_inputs()
    source = Image.open(io.BytesIO(body)).convert("RGBA")
    source.putpixel((60, 180), (235, 98, 108, 128))  # inside reviewed mother mask
    source.putpixel((5, 5), (23, 45, 67, 64))  # outside all object masks
    buffer = io.BytesIO()
    source.save(buffer, format="PNG")
    changed = buffer.getvalue()
    package = package.model_copy(update={
        "source_image_sha256": hashlib.sha256(changed).hexdigest(),
        "package_hash": "0" * 64,
    })
    package = package.model_copy(update={
        "package_hash": stable_model_hash(package, exclude={"package_hash"}),
    })
    registry = build_source_asset_registry(
        package=package, segments=segments, source_image_bytes=changed,
        source_objects=specs, narration_objects=additions, events=events,
    )
    scene = family_prototype().scene_plan.scenes[0]
    actual = SceneStateComposer().render_scene(registry, scene)
    expected = Image.alpha_composite(Image.new("RGBA", source.size, "white"), source)
    for point in ((60, 180), (5, 5)):
        assert actual.getpixel(point) == expected.convert("RGB").getpixel(point)


def test_missing_source_bytes_fail_instead_of_white_background_fallback() -> None:
    result = family_prototype()
    registry = result.registry.__class__(
        world=result.registry.world,
        asset_png_by_id=result.registry.asset_png_by_id,
        mask_png_by_id=result.registry.mask_png_by_id,
    )
    with pytest.raises(StoryWorldError, match="SOURCE_ASSET_MISMATCH"):
        SceneStateComposer().render_scene(registry, result.scene_plan.scenes[0])


def test_refined_contours_reduce_fragments_but_flat_color_keeps_legacy_fill() -> None:
    result = family_prototype()
    legacy = extract_object_strokes(result.registry, "house", strategy="legacy")
    refined = extract_object_strokes(result.registry, "house", strategy="refined")
    assert len(refined.outline_paths) < len(legacy.outline_paths)
    assert refined.color_paths == legacy.color_paths
    assert legacy.extraction_method == "MASK_BOUNDARY_AND_LOCAL_CONTRAST_V1"
    assert refined.extraction_method == "MASK_BOUNDARY_AND_STRUCTURAL_TEXTURE_V3"


def test_textured_source_uses_source_pixel_brush_instead_of_flat_fallback() -> None:
    package, segments, body, specs, additions, events = ocean_inputs()
    source = Image.open(io.BytesIO(body)).convert("RGB")
    checker = Image.new("RGB", source.size, "white")
    painter = ImageDraw.Draw(checker)
    for x in range(35, 126, 6):
        painter.rectangle((x, 75, x + 5, 145),
                          fill="#2055dd" if x // 6 % 2 else "#ed3850")
    source.paste(checker, mask=Image.open(io.BytesIO(specs[0].mask_png)).convert("L"))
    stream = io.BytesIO()
    source.save(stream, format="PNG")
    changed = stream.getvalue()
    package = package.model_copy(update={
        "source_image_sha256": hashlib.sha256(changed).hexdigest(),
        "package_hash": "0" * 64,
    })
    package = package.model_copy(update={
        "package_hash": stable_model_hash(package, exclude={"package_hash"}),
    })
    registry = build_source_asset_registry(
        package=package, segments=segments, source_image_bytes=changed,
        source_objects=specs, narration_objects=additions, events=events,
    )
    legacy = extract_object_strokes(registry, "fish-blue", strategy="legacy")
    refined = extract_object_strokes(registry, "fish-blue", strategy="refined")
    assert refined.color_paths != legacy.color_paths
    assert any(path.points[0][0] != path.points[-1][0] and
               path.points[0][1] != path.points[-1][1]
               for path in refined.color_paths)


def test_pilot_evidence_uses_decoded_frames_and_has_no_final_snap(tmp_path) -> None:
    metrics = render_fixture("ocean-png", tmp_path, duration_seconds=4, fps=10)
    assert metrics["original_to_canonical_mae"] == 0
    assert metrics["final_mae"] == 0
    assert metrics["decoded_final_mae"] > 0  # H.264 is lossy
    assert len(metrics["difference_map_paths"]) == 3
    assert all(Image.open(path).size == (480, 320)
               for path in metrics["difference_map_paths"])
    decoded_sheet = Image.open(metrics["decoded_contact_sheet_path"]).convert("RGB")
    reader = imageio.get_reader(metrics["video_path"], format="ffmpeg")
    try:
        first = Image.fromarray(np.asarray(reader.get_data(0))).convert("RGB")
        penultimate = np.asarray(reader.get_data(38), dtype=np.int16)
        final = np.asarray(reader.get_data(39), dtype=np.int16)
    finally:
        reader.close()
    assert first.getpixel((0, 0)) == (255, 255, 255)
    assert decoded_sheet.crop((0, 25, 480, 345)).tobytes() == first.tobytes()
    assert np.abs(penultimate - final).mean() < 2


def test_oversized_canvas_blocks_before_encoding(tmp_path) -> None:
    result = family_prototype()
    scene = result.scene_plan.scenes[0]
    objects = tuple(extract_object_strokes(result.registry, item.object_id)
                    for item in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=4, fps=10)
    oversized_world = result.registry.world.model_copy(update={
        "source_width": 3000, "source_height": 3000,
    })
    oversized = replace(result.registry, world=oversized_world)
    with pytest.raises(StoryWorldError, match="DRAW_TIMING_INFEASIBLE"):
        render_scene_pilot(
            oversized, scene, objects, schedule,
            video_path=tmp_path / "unsupported.mp4",
            contact_sheet_path=tmp_path / "unsupported.png", fps=10,
        )
    assert not (tmp_path / "unsupported.mp4").exists()
