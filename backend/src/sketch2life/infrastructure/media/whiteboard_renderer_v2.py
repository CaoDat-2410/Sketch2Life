"""Offline V2 source-pixel brush reveal; independent of V1 and HTTP jobs."""

from __future__ import annotations

import hashlib
import io
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageChops, ImageDraw

from sketch2life.application.services.story_draw_schedule_v2 import validate_draw_schedule
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import SourceAssetRegistry
from sketch2life.contracts.schemas.story_strokes_v2 import (
    ObjectStrokeV2,
    SceneDrawScheduleV2,
    ScheduledStrokeV2,
    SourceObjectStrokesV2,
)
from sketch2life.contracts.schemas.story_world_v2 import ScenePlanV2
from sketch2life.infrastructure.media.scene_state_composer import (
    SceneStateComposer,
    source_canvas_layers,
)


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
    original_to_canonical_mae: float = 0.0
    decoded_final_mae: float = 0.0
    decoded_contact_sheet_path: str = ""
    difference_map_paths: tuple[str, ...] = ()


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


@lru_cache(maxsize=16)
def _background_paths(width: int, height: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Wide diagonal paper strokes reveal static source pixels before object ink."""
    result = []
    for offset in range(-width - 16, height + 17, 8):
        start = max(0, -offset)
        stop = min(width - 1, height - 1 - offset)
        if stop >= start:
            result.append(((start, start + offset), (stop, stop + offset)))
    return tuple(result)


def _background_frame(background: Image.Image, fraction: float) -> Image.Image:
    width, height = background.size
    board = Image.new("RGBA", (width, height), "white")
    if fraction <= 0:
        return board
    mask = Image.new("L", (width, height), 0)
    brush = ImageDraw.Draw(mask)
    paths = _background_paths(width, height)
    progress = min(1., fraction) * len(paths)
    for index, path in enumerate(paths):
        if index >= progress:
            break
        if index + 1 <= progress:
            brush.line(path, fill=255, width=20)
            for x, y in path:
                brush.ellipse((x - 10, y - 10, x + 10, y + 10), fill=255)
        else:
            _draw_path(brush, ObjectStrokeV2(
                stroke_id="background", phase="COLOR", points=path,
                brush_width=20, color_rgb=(255, 255, 255),
            ), progress - index)
    board.paste(background, (0, 0), mask)
    return board


def _stroke_fraction(item: ScheduledStrokeV2, elapsed: float) -> float:
    """One authoritative timing sample shared by pixel reveal and pen tip."""
    return min(1., max(0., (elapsed - item.start_seconds) /
                       (item.end_seconds - item.start_seconds)))


def _frame(
    registry: SourceAssetRegistry, scene: ScenePlanV2,
    objects: tuple[SourceObjectStrokesV2, ...], schedule: SceneDrawScheduleV2,
    elapsed: float, background: Image.Image, *, show_pen: bool = False,
    background_preview_ids: tuple[str, ...] = (),
    debug_schedule: bool = False,
    frame_audit: list[dict[str, object]] | None = None,
) -> Image.Image:
    if background_preview_ids:
        raise StoryWorldError("UNSCHEDULED_STROKE", "background preview bypasses draw schedule")
    width, height = registry.world.source_width, registry.world.source_height
    # Full-partition static fixtures have an entirely white cleared background.
    # Do not reserve 18% of the clip for painting invisible white-on-white strokes.
    has_background_marks = bool(np.any(np.asarray(background.convert("RGB")) < 255))
    background_seconds = schedule.duration_seconds * .18 if has_background_marks else 0.
    board = _background_frame(
        background, elapsed / background_seconds if background_seconds else 1.,
    )
    offset_seconds = background_seconds
    object_elapsed = max(
        0., (elapsed - offset_seconds) * schedule.duration_seconds /
        (schedule.duration_seconds - offset_seconds),
    )
    by_id = {item.object_id: item for item in objects}
    states = sorted(scene.target_states, key=lambda item: item.z_index)
    tip = None
    debug_item = None
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
            if item.object_id != state.object_id or object_elapsed < item.start_seconds:
                continue
            fraction = _stroke_fraction(item, object_elapsed)
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
    if show_pen or debug_schedule:
        pen_paths = {(obj.object_id, path.stroke_id): path for obj in objects
                 for group in (obj.outline_paths, obj.detail_paths, obj.color_paths)
                 for path in group}
        state_by_id = {s.object_id: s for s in states}

        def world_point(item, point):
            state = state_by_id[item.object_id]
            data = by_id[item.object_id]
            return (round(state.x * width - data.width / 2) + point[0],
                    round(state.y * height - data.height / 2) + point[1])

        previous = None
        if elapsed >= offset_seconds:
            for item in schedule.strokes:
                path = pen_paths[(item.object_id, item.stroke_id)]
                if item.start_seconds <= object_elapsed < item.end_seconds:
                    fraction = _stroke_fraction(item, object_elapsed)
                    tip = (*world_point(item, _partial_points(path, fraction)[-1]), True)
                    debug_item = item
                    break
                if object_elapsed < item.start_seconds:
                    target = world_point(item, path.points[0])
                    if previous is not None:
                        prior = pen_paths[(previous.object_id, previous.stroke_id)]
                        origin = world_point(previous, prior.points[-1])
                        fraction = (object_elapsed - previous.end_seconds) / (
                            item.start_seconds - previous.end_seconds)
                        target = tuple(a + (b - a) * fraction
                                       for a, b in zip(origin, target, strict=True))
                    tip = (*target, False)
                    debug_item = item
                    break
                previous = item
        if tip is not None:
            x, y, down = tip
            pen = ImageDraw.Draw(board)
            # Small UI pencil tip, not an unapproved hand or replacement artwork.
            if down:
                pen.line((x, y, x + 7, y - 10), fill=(55, 55, 55, 255), width=3)
                pen.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(20, 20, 20, 255))
            else:
                pen.ellipse((x - 3, y - 3, x + 3, y + 3), outline=(170, 110, 30, 255), width=1)
            if debug_schedule and debug_item is not None:
                label = (f"{elapsed:.3f}s {'DOWN' if down else 'UP'} "
                         f"{debug_item.object_id.split('-')[-1]} "
                         f"{debug_item.phase} {debug_item.stroke_id}")
                pen.rectangle((0, 0, min(width, 430), 16), fill=(255, 255, 255, 255))
                pen.text((3, 2), label, fill=(180, 30, 30, 255))
    if frame_audit is not None:
        frame_audit.append({
            "elapsed": elapsed, "schedule_elapsed": object_elapsed,
            "tip": list(tip) if tip is not None else None,
            "object_id": debug_item.object_id if debug_item is not None else None,
            "stroke_id": debug_item.stroke_id if debug_item is not None else None,
            "phase": debug_item.phase if debug_item is not None else None,
        })
    return _camera(board, scene).convert("RGB")


def render_scene_pilot(
    registry: SourceAssetRegistry, scene: ScenePlanV2,
    objects: tuple[SourceObjectStrokesV2, ...], schedule: SceneDrawScheduleV2,
    *, video_path: Path, contact_sheet_path: Path, fps: int = 12,
    max_render_seconds: float = 120.,
    show_pen: bool = False, background_preview_ids: tuple[str, ...] = (),
    debug_schedule: bool = False, interleave_reason: str | None = None,
) -> V2DrawingPilotResult:
    """Encode a silent pilot; last frame must match the canonical still exactly."""
    if scene.new_object_ids or scene.action not in {"STATIC", "TRANSLATE", "SCALE", "ROTATE"}:
        raise StoryWorldError("UNSUPPORTED_ACTION", "source-only drawing pilot")
    started = time.monotonic()
    if background_preview_ids:
        raise StoryWorldError("UNSCHEDULED_STROKE", "background preview bypasses draw schedule")
    validate_draw_schedule(objects, schedule, require_interleave_reason=debug_schedule,
                           interleave_reason=interleave_reason)
    if not 8 <= fps <= 30 or scene.scene_id != schedule.scene_id or max_render_seconds <= 0:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "invalid frame rate or schedule")
    width, height = registry.world.source_width, registry.world.source_height
    if (show_pen or debug_schedule) and (scene.action != "STATIC" or any(
        s.scale != 1 or s.rotation_degrees != 0 for s in scene.target_states
    )):
        raise StoryWorldError("UNSUPPORTED_ACTION", "pencil overlay supports static identity pose")
    if not set(background_preview_ids).issubset(scene.source_object_ids):
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "unknown background preview identity")
    if max(width, height) > 2048 or width * height > 1920 * 1080:
        raise StoryWorldError(
            "DRAW_TIMING_INFEASIBLE", "offline pilot is limited to 2048px edges and 2.07MP"
        )
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

    original, background = source_canvas_layers(registry)
    if debug_schedule and np.any(np.asarray(background.convert("RGB")) < 255):
        raise StoryWorldError(
            "UNSCHEDULED_STROKE", "background needs explicit scheduled source asset",
        )
    canonical = SceneStateComposer().render_scene(registry, scene)
    count = max(2, round(schedule.duration_seconds * fps))
    if count > 600:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "offline frame budget exceeds 600")
    if time.monotonic() - started > max_render_seconds:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "render deadline exceeded in preflight")
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
            if time.monotonic() - started > max_render_seconds:
                raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "render deadline exceeded")
            elapsed = schedule.duration_seconds * frame_index / (count - 1)
            frame = _frame(registry, scene, objects, schedule, elapsed, background,
                           show_pen=show_pen, debug_schedule=debug_schedule)
            if time.monotonic() - started > max_render_seconds:
                raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "render deadline exceeded in frame")
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
    if time.monotonic() - started > max_render_seconds:
        raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "render deadline exceeded during encoding")
    assert last is not None
    if last.size != canonical.size:
        raise StoryWorldError("SOURCE_FIDELITY_FAILED", "final dimensions differ")
    difference = np.abs(np.asarray(last, dtype=np.int16) - np.asarray(canonical, dtype=np.int16))
    changed = int(np.count_nonzero(np.any(difference > 0, axis=2)))
    mae = float(difference.mean())
    if changed:
        raise StoryWorldError("SOURCE_FIDELITY_FAILED", f"{changed} final pixels differ")
    sheet.save(contact_sheet_path, format="PNG")
    # Compare the actual H.264 stream separately from the lossless raw frames.
    decoded_sheet = Image.new("RGB", sheet.size, "white")
    decoded_captions = ImageDraw.Draw(decoded_sheet)
    reader = imageio.get_reader(str(video_path), format="ffmpeg")
    try:
        for frame_index, percent in sorted(milestone_indices.items()):
            decoded = Image.fromarray(np.asarray(reader.get_data(frame_index))).convert("RGB")
            position = milestones.index(percent) * canonical.width
            decoded_sheet.paste(decoded, (position, 25))
            decoded_captions.text((position + 4, 4), f"{percent}%", fill="black")
        decoded_final = Image.fromarray(np.asarray(reader.get_data(count - 1))).convert("RGB")
    finally:
        reader.close()
    decoded_path = contact_sheet_path.with_name(contact_sheet_path.stem + "-decoded.png")
    decoded_sheet.save(decoded_path, format="PNG")
    original_rgb = original.convert("RGB")
    comparisons = (
        ("original-canonical", original_rgb, canonical),
        ("canonical-raw", canonical, last),
        ("canonical-decoded", canonical, decoded_final),
    )
    diff_paths = []
    for label, left, right in comparisons:
        output = contact_sheet_path.with_name(contact_sheet_path.stem + f"-diff-{label}.png")
        ImageChops.difference(left, right).point(lambda value: min(255, value * 4)).save(output)
        diff_paths.append(str(output))
    original_mae = float(np.abs(np.asarray(original_rgb, dtype=np.int16) -
                                np.asarray(canonical, dtype=np.int16)).mean())
    decoded_mae = float(np.abs(np.asarray(decoded_final, dtype=np.int16) -
                               np.asarray(canonical, dtype=np.int16)).mean())
    return V2DrawingPilotResult(
        video_path=str(video_path), contact_sheet_path=str(contact_sheet_path),
        duration_seconds=schedule.duration_seconds, fps=fps, frame_count=count,
        final_mae=mae, final_changed_pixels=changed, source_mask_coverage=coverage,
        contact_frames=tuple(saved),
        original_to_canonical_mae=original_mae, decoded_final_mae=decoded_mae,
        decoded_contact_sheet_path=str(decoded_path), difference_map_paths=tuple(diff_paths),
    )
