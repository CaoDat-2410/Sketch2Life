"""Bounded complex-detail tracing, masked source reveal and no silent detail loss."""

from __future__ import annotations

import hashlib
import io

import numpy as np
import pytest
from PIL import Image, ImageDraw
from tools.story_world_v2_fixture import fixture_inputs, make_prototype

from sketch2life.application.services.story_draw_schedule_v2 import build_draw_schedule
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import build_source_asset_registry
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.contracts.schemas.story_video import stable_model_hash
from sketch2life.infrastructure.media.object_stroke_engine_v2 import (
    _natural_color_paths,
    _paths_clustered,
    _structural_details,
    extract_object_strokes,
)
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _draw_path, render_scene_pilot


def flower_registry(image_format: str = "PNG"):
    package, segments, source_bytes, specs, additions, events = fixture_inputs()
    source = Image.open(io.BytesIO(source_bytes)).convert("RGB")
    painter = ImageDraw.Draw(source)
    painter.rectangle((306, 56, 484, 229), fill=(186, 224, 156))
    for y in range(63, 220, 17):
        for x in range(313, 477, 17):
            painter.line((x, y + 4, x, y + 12), fill=(20, 65, 25), width=1)
            painter.line((x - 4, y + 7, x, y + 10, x + 4, y + 7),
                         fill=(25, 95, 30), width=1)
            painter.ellipse((x - 5, y - 4, x + 5, y + 4),
                            fill=(215, 25, 75), outline=(65, 15, 30), width=1)
    # Pencil grain: source texture, not a fabricated renderer fill pattern.
    pixels = np.asarray(source).copy()
    rng = np.random.default_rng(104)
    grain = rng.integers(-9, 10, size=(174, 179, 1))
    region = pixels[56:230, 306:485].astype(np.int16)
    pixels[56:230, 306:485] = np.clip(region + grain, 0, 255).astype(np.uint8)
    source = Image.fromarray(pixels)
    stream = io.BytesIO()
    source.save(stream, format=image_format, quality=92)
    body = stream.getvalue()
    package = package.model_copy(update={
        "source_image_sha256": hashlib.sha256(body).hexdigest(), "package_hash": "0" * 64,
    })
    package = package.model_copy(update={
        "package_hash": stable_model_hash(package, exclude={"package_hash"}),
    })
    return build_source_asset_registry(
        package=package, segments=segments, source_image_bytes=body, source_objects=specs,
        narration_objects=additions, events=events,
    )


def test_clustered_trace_keeps_all_dense_pixels_and_original_coordinates() -> None:
    binary = np.zeros((125, 130), dtype=bool)
    binary[13:93, 17:97] = True  # 6,400 points, not one >2,000-point graph.
    binary[124, 129] = True  # isolated thin dot must not disappear.
    paths, _clusters, maximum = _paths_clustered(binary)
    selected = {(int(x), int(y)) for y, x in zip(*np.nonzero(binary), strict=True)}
    assert {point for path in paths for point in path} == selected
    assert maximum <= 1024
    assert all(max(abs(x - a), abs(y - b)) <= 1 for path in paths
               for (x, y), (a, b) in zip(path, path[1:], strict=False))


def test_structural_budget_fails_explicitly_instead_of_pruning_pixels() -> None:
    with pytest.raises(StoryWorldError, match="structural pixels exceed bounded"):
        _paths_clustered(np.ones((200, 200), dtype=bool))


def test_thin_stems_and_colored_petals_are_not_classified_as_pencil_grain() -> None:
    rgb = np.full((64, 64, 3), 210, dtype=np.uint8)
    rgb[15:48, 32] = (20, 70, 25)  # one-pixel stem.
    rgb[10:16, 28:37] = (220, 25, 60)
    image = Image.fromarray(rgb)
    deep = np.zeros((64, 64), dtype=bool)
    deep[4:-4, 4:-4] = True
    strength = np.full((64, 64), 100, dtype=np.uint8)
    structural, texture = _structural_details(image, deep, strength, 70)
    assert structural[25, 32]
    assert structural[12, 31]
    assert texture[40, 10]  # flat high-frequency candidate is color, not ink.


@pytest.mark.parametrize("image_format", ["PNG", "JPEG"])
@pytest.mark.parametrize("strategy", ["refined", "visual", "pencil"])
def test_dense_flower_source_has_bounded_traces_and_exact_color_coverage(
    image_format, strategy,
) -> None:
    registry = flower_registry(image_format)
    with pytest.raises(StoryWorldError, match="too many candidate ink pixels"):
        extract_object_strokes(registry, "house", strategy="legacy")
    data = extract_object_strokes(registry, "house", strategy=strategy)
    diagnostics = data.processing_diagnostics
    assert diagnostics is not None
    assert diagnostics.raw_detail_candidates > 2000
    assert diagnostics.retained_structural_fraction == 1
    assert diagnostics.max_cluster_pixels <= 1024
    source = Image.open(io.BytesIO(registry.asset_png_by_id["house"])).convert("RGBA")
    alpha = np.asarray(source.getchannel("A")) > 0
    reveal = Image.new("L", source.size, 0)
    brush = ImageDraw.Draw(reveal)
    for path in (*data.outline_paths, *data.detail_paths, *data.color_paths):
        assert all(alpha[y, x] for x, y in path.points)
        _draw_path(brush, path, 1.)
    assert np.all((np.asarray(reveal) > 0)[alpha])


@pytest.mark.parametrize("descending", [True, False])
def test_color_tracks_lift_at_mask_holes_and_do_not_cross_unapproved_pixels(descending) -> None:
    alpha = np.zeros((40, 40), dtype=bool)
    alpha[2:37, 2:37] = True
    alpha[10:26, 11:27] = False  # source mask hole, never an allowed pen-down region.

    def factory(phase, index, points, width):
        return ObjectStrokeV2(stroke_id=f"color-{index}", phase=phase, points=points,
                              brush_width=width, color_rgb=(20, 70, 40))

    paths = _natural_color_paths(alpha, factory, descending=descending)
    reveal = Image.new("L", (40, 40), 0)
    brush = ImageDraw.Draw(reveal)
    for path in paths:
        _draw_path(brush, path, 1.)
        for (x0, y0), (x1, y1) in zip(path.points, path.points[1:], strict=False):
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for step in range(steps + 1):
                x = round(x0 + (x1 - x0) * step / steps)
                y = round(y0 + (y1 - y0) * step / steps)
                assert alpha[y, x]
    assert np.all((np.asarray(reveal) > 0)[alpha])


def test_renderer_frame_rate_and_deadline_fail_closed(tmp_path) -> None:
    result = make_prototype()
    scene = result.scene_plan.scenes[0]
    objects = tuple(extract_object_strokes(result.registry, obj.object_id)
                    for obj in result.registry.world.source_objects)
    schedule = build_draw_schedule(scene, objects, duration_seconds=4)
    with pytest.raises(StoryWorldError, match="DRAW_TIMING_INFEASIBLE"):
        render_scene_pilot(result.registry, scene, objects, schedule,
                           video_path=tmp_path / "bad.mp4", contact_sheet_path=tmp_path / "bad.png",
                           fps=100)
    with pytest.raises(StoryWorldError, match="deadline exceeded"):
        render_scene_pilot(result.registry, scene, objects, schedule,
                           video_path=tmp_path / "late.mp4",
                           contact_sheet_path=tmp_path / "late.png",
                           max_render_seconds=1e-9)
    assert not (tmp_path / "late.mp4").exists()
