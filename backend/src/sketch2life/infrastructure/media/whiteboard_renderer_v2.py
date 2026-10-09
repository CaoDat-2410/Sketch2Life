"""Offline V2 source-pixel brush reveal; independent of V1 and HTTP jobs."""

from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageChops, ImageDraw

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import SourceAssetRegistry
from sketch2life.contracts.schemas.story_strokes_v2 import (
    ObjectStrokeV2,
    SceneDrawScheduleV2,
    SourceObjectStrokesV2,
)
from sketch2life.contracts.schemas.story_world_v2 import ScenePlanV2
from sketch2life.infrastructure.media.scene_state_composer import SceneStateComposer


@dataclass(frozen=True)
class V2DrawingPilotResult:
    video_path: str
    contact_sheet_path: str
    duration_seconds: float
    fps: int
    frame_count: int
    final_mae: float
    final_changed_pixels: int
    source_mask_coverage: float
    contact_frames: tuple[str, ...]


def _partial_points(path: ObjectStrokeV2, fraction: float) -> list[tuple[float, float]]:
    points = path.points
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:], strict=False)]
    remaining = sum(lengths) * max(0., min(1., fraction))
    output: list[tuple[float, float]] = [(float(points[0][0]), float(points[0][1]))]
    for (x0, y0), (x1, y1), length in zip(points, points[1:], lengths, strict=False):
        if length == 0:
            continue
        if remaining >= length:
            output.append((float(x1), float(y1)))
            remaining -= length
        else:
            ratio = remaining / length
            output.append((x0 + (x1 - x0) * ratio, y0 + (y1 - y0) * ratio))
            break
    return output


def _draw_path(draw: ImageDraw.ImageDraw, path: ObjectStrokeV2, fraction: float) -> None:
    if fraction <= 0:
        return
    points = _partial_points(path, fraction)
    radius = max(1, path.brush_width // 2)
    if len(points) >= 2:
        draw.line(points, fill=255, width=path.brush_width, joint="curve")
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)


def _camera(board: Image.Image, scene: ScenePlanV2) -> Image.Image:
    width, height = board.size
    if scene.camera.zoom == 1 and (scene.camera.center_x, scene.camera.center_y) == (.5, .5):
        return board
    crop_width = width / scene.camera.zoom
    crop_height = height / scene.camera.zoom
    left = min(max(scene.camera.center_x * width - crop_width / 2, 0), width - crop_width)
    top = min(max(scene.camera.center_y * height - crop_height / 2, 0), height - crop_height)
    return board.crop((round(left), round(top), round(left + crop_width),
                       round(top + crop_height))).resize((width, height), Image.Resampling.LANCZOS)


def _frame(
    registry: SourceAssetRegistry, scene: ScenePlanV2,
    objects: tuple[SourceObjectStrokesV2, ...], schedule: SceneDrawScheduleV2,
    elapsed: float,
) -> Image.Image:
    width, height = registry.world.source_width, registry.world.source_height
    board = Image.new("RGBA", (width, height), "white")
    by_id = {item.object_id: item for item in objects}
    states = sorted(scene.target_states, key=lambda item: item.z_index)
    for state in states:
        if not state.visible:
            continue
        data = by_id[state.object_id]
        encoded = registry.asset_png_by_id.get(state.object_id)
        if encoded is None or hashlib.sha256(encoded).hexdigest() != data.source_asset_sha256:
            raise StoryWorldError("SOURCE_ASSET_MISMATCH", "cutout bytes changed after extraction")
        source = Image.open(io.BytesIO(encoded)).convert("RGBA")
        reveal = Image.new("L", source.size, 0)
        brush = ImageDraw.Draw(reveal)
        paths = {path.stroke_id: path for group in (
            data.outline_paths, data.detail_paths, data.color_paths,
        ) for path in group}
        for item in schedule.strokes:
            if item.object_id != state.object_id or elapsed < item.start_seconds:
                continue
            fraction = min(1., (elapsed - item.start_seconds) /
                           (item.end_seconds - item.start_seconds))
            _draw_path(brush, paths[item.stroke_id], fraction)
        source.putalpha(ImageChops.multiply(source.getchannel("A"), reveal))
        base_scale = min(width / registry.world.source_width, height / registry.world.source_height)
        size = (max(1, round(source.width * base_scale * state.scale)),
                max(1, round(source.height * base_scale * state.scale)))
        layer = source.resize(size, Image.Resampling.LANCZOS)
        if state.rotation_degrees:
            layer = layer.rotate(-state.rotation_degrees, resample=Image.Resampling.BICUBIC,
                                 expand=True)
        left = round(state.x * width - layer.width / 2)
        top = round(state.y * height - layer.height / 2)
        board.alpha_composite(layer, (left, top))
    return _camera(board, scene).convert("RGB")


def render_scene_pilot(
    registry: SourceAssetRegistry, scene: ScenePlanV2,
    objects: tuple[SourceObjectStrokesV2, ...], schedule: SceneDrawScheduleV2,
    *, video_path: Path, contact_sheet_path: Path, fps: int = 12,
) -> V2DrawingPilotResult:
    """Encode a silent pilot; last frame must match the canonical still exactly."""
    if scene.new_object_ids or scene.action not in {"STATIC", "TRANSLATE", "SCALE", "ROTATE"}:
        raise StoryWorldError("UNSUPPORTED_ACTION", "source-only drawing pilot")
    if fps < 8 or scene.scene_id != schedule.scene_id:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "invalid frame rate or schedule")
    specs = {obj.object_id: obj for obj in registry.world.source_objects}
    if {item.object_id for item in objects} != set(scene.source_object_ids):
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "incomplete stroke manifest")
    for item in objects:
        spec = specs[item.object_id]
        if (item.source_image_sha256 != spec.source_image_sha256
            or item.source_asset_sha256 != spec.asset_sha256
            or item.source_mask_sha256 != spec.source_mask_sha256):
            raise StoryWorldError("SOURCE_ASSET_MISMATCH", "stroke manifest hash mismatch")
        mask_body = registry.mask_png_by_id.get(item.object_id)
        if mask_body is None or hashlib.sha256(mask_body).hexdigest() != spec.source_mask_sha256:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "source mask changed after extraction")
    if len(schedule.strokes) > fps * schedule.duration_seconds * 18:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "too many strokes for clip")

    # Verify that the brush itinerary covers every original nontransparent pixel
    # before encoding. No sudden final-frame replacement is allowed.
    total_active = total_covered = 0
    for item in objects:
        source = Image.open(io.BytesIO(registry.asset_png_by_id[item.object_id])).convert("RGBA")
        mask = Image.new("L", source.size, 0)
        pen = ImageDraw.Draw(mask)
        for path in (*item.outline_paths, *item.detail_paths, *item.color_paths):
            _draw_path(pen, path, 1.)
        active = np.asarray(source.getchannel("A")) > 0
        covered = np.asarray(mask) > 0
        total_active += int(active.sum())
        total_covered += int((active & covered).sum())
    coverage = total_covered / max(1, total_active)
    if coverage < 1.:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", f"brush covers only {coverage:.5f} of source")

    canonical = SceneStateComposer().render_scene(registry, scene)
    count = max(2, round(schedule.duration_seconds * fps))
    milestones = (0, 25, 50, 75, 100)
    milestone_indices = {round((count - 1) * p / 100): p for p in milestones}
    video_path.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (canonical.width * 5, canonical.height + 25), "white")
    captions = ImageDraw.Draw(sheet)
    saved: list[str] = []
    last = None
    writer = imageio.get_writer(
        str(video_path), fps=fps, codec="libx264", pixelformat="yuv420p", quality=8,
        macro_block_size=1,
    )
    try:
        for frame_index in range(count):
            elapsed = schedule.duration_seconds * frame_index / (count - 1)
            frame = _frame(registry, scene, objects, schedule, elapsed)
            writer.append_data(np.asarray(frame))
            if frame_index in milestone_indices:
                percent = milestone_indices[frame_index]
                position = milestones.index(percent) * canonical.width
                sheet.paste(frame, (position, 25))
                captions.text((position + 4, 4), f"{percent}%", fill="black")
                saved.append(f"{percent}%")
            last = frame
    finally:
        writer.close()
    assert last is not None
    if last.size != canonical.size:
        raise StoryWorldError("SOURCE_FIDELITY_FAILED", "final dimensions differ")
    difference = np.abs(np.asarray(last, dtype=np.int16) - np.asarray(canonical, dtype=np.int16))
    changed = int(np.count_nonzero(np.any(difference > 0, axis=2)))
    mae = float(difference.mean())
    if changed:
        raise StoryWorldError("SOURCE_FIDELITY_FAILED", f"{changed} final pixels differ")
    sheet.save(contact_sheet_path, format="PNG")
    return V2DrawingPilotResult(
        video_path=str(video_path), contact_sheet_path=str(contact_sheet_path),
        duration_seconds=schedule.duration_seconds, fps=fps, frame_count=count,
        final_mae=mae, final_changed_pixels=changed, source_mask_coverage=coverage,
        contact_frames=tuple(saved),
    )
