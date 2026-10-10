"""Experimental local source-part rig primitives, never a production motion provider.

No segmentation, new art, approval, HTTP, TTS or inference happens here. Callers
must supply source-bound candidate part PNGs and explicit joint positions. Foot
plant locks constrain the foot endpoint; they do not prove pleasing animation.
"""

from __future__ import annotations

import hashlib
import io
import math
from collections.abc import Mapping
from dataclasses import dataclass

from PIL import Image, ImageFilter

from sketch2life.application.services.story_world_errors import StoryWorldError

Point = tuple[float, float]


@dataclass(frozen=True)
class DerivedStyleProfile:
    """Source-derived smoothing candidate; original pixels remain an immutable input."""

    source_sha256: str
    name: str = "ENHANCED_HAND_DRAWN_SOURCE_DERIVED_CANDIDATE"
    blur_radius: float = 0.4
    blend: float = 0.12
    review_status: str = "NEEDS_VISUAL_REVIEW"

    def apply(self, image: Image.Image) -> Image.Image:
        if not 0 <= self.blur_radius <= 0.8 or not 0 <= self.blend <= 0.2:
            raise StoryWorldError("STYLE_PROFILE_INVALID", "bounded light smoothing only")
        rgba = image.convert("RGBA")
        # Do not blur masks or silhouette alpha, recolor, denoise away texture, or
        # silently redefine enhanced pixels as exact source RGB.
        rgb = rgba.convert("RGB")
        result = Image.blend(rgb, rgb.filter(ImageFilter.GaussianBlur(self.blur_radius)),
                             self.blend).convert("RGBA")
        result.putalpha(rgba.getchannel("A"))
        return result


@dataclass(frozen=True)
class SourceRigPart:
    part_id: str
    object_id: str
    source_image_sha256: str
    asset_sha256: str
    start_joint: str
    end_joint: str
    bind_start: Point
    bind_end: Point
    z_index: int = 0
    provenance: str = "SOURCE_MASKED_PIXELS"


def ease(value: float) -> float:
    value = min(1., max(0., value))
    return value * value * (3. - 2. * value)


def lerp(left: Point, right: Point, fraction: float) -> Point:
    return left[0] + (right[0] - left[0]) * fraction, left[1] + (right[1] - left[1]) * fraction


def two_bone_ik(
    root: Point, endpoint: Point, upper_length: float, lower_length: float, *, bend: int = 1,
) -> Point:
    """Solve a reviewed two-bone plane chain without scaling either bone."""
    dx, dy = endpoint[0] - root[0], endpoint[1] - root[1]
    distance = math.hypot(dx, dy)
    if (not all(math.isfinite(v) for v in (*root, *endpoint, upper_length, lower_length))
        or min(upper_length, lower_length) <= 0 or bend not in {-1, 1}
        or distance < abs(upper_length - lower_length) + 1e-6
        or distance > upper_length + lower_length - 1e-6):
        raise StoryWorldError("NEEDS_POSE_REVIEW", "foot/hand target outside fixed bone reach")
    cosine = (upper_length ** 2 + distance ** 2 - lower_length ** 2) / (
        2 * upper_length * distance)
    angle = math.atan2(dy, dx) + bend * math.acos(min(1., max(-1., cosine)))
    return root[0] + upper_length * math.cos(angle), root[1] + upper_length * math.sin(angle)


def planted_step(
    elapsed: float, *, start_seconds: float, end_seconds: float,
    start: Point, target: Point, lift_pixels: float,
) -> tuple[Point, bool]:
    """Foot remains fixed outside swing; height and travel have zero endpoint velocity."""
    if (not all(math.isfinite(v) for v in (elapsed, start_seconds, end_seconds,
                                          *start, *target, lift_pixels))
        or end_seconds <= start_seconds or not 0 <= lift_pixels <= 20):
        raise StoryWorldError("MOTION_TIMING_INVALID", "invalid bounded foot swing")
    if elapsed <= start_seconds:
        return start, True
    if elapsed >= end_seconds:
        return target, True
    u = (elapsed - start_seconds) / (end_seconds - start_seconds)
    x, y = lerp(start, target, ease(u))
    return (x, y - lift_pixels * math.sin(math.pi * u) ** 2), False


def inverse_bone_affine(
    bind_start: Point, bind_end: Point, start: Point, end: Point,
) -> tuple[float, float, float, float, float, float]:
    """Pillow destination->source similarity; no shear or negative/mirror scale."""
    sx, sy = bind_end[0] - bind_start[0], bind_end[1] - bind_start[1]
    tx, ty = end[0] - start[0], end[1] - start[1]
    source_length, target_length = math.hypot(sx, sy), math.hypot(tx, ty)
    if min(source_length, target_length) < 1 or not all(
        math.isfinite(v) for v in (*bind_start, *bind_end, *start, *end)
    ):
        raise StoryWorldError("NEEDS_POSE_REVIEW", "invalid or degenerate source bone")
    scale = target_length / source_length
    if not .85 <= scale <= 1.15:
        raise StoryWorldError("NEEDS_POSE_REVIEW", "bone length changed beyond review limits")
    angle = math.atan2(ty, tx) - math.atan2(sy, sx)
    cosine, sine = math.cos(angle) / scale, math.sin(angle) / scale
    return (cosine, sine, bind_start[0] - cosine * start[0] - sine * start[1],
            -sine, cosine, bind_start[1] + sine * start[0] - cosine * start[1])


def render_rig_pose(
    *, canvas_size: tuple[int, int], object_id: str, source_sha256: str,
    parts: tuple[SourceRigPart, ...], assets: Mapping[str, Image.Image],
    asset_png_by_id: Mapping[str, bytes], joints: Mapping[str, Point],
) -> tuple[Image.Image, list[dict[str, object]]]:
    """Render explicit candidate joints; no whole-cutout motion or approval fallback."""
    width, height = canvas_size
    if min(canvas_size) <= 0 or max(canvas_size) > 2048 or width * height > 1920 * 1080:
        raise StoryWorldError("MOTION_RESOURCE_LIMIT", "canvas exceeds offline limits")
    if not 1 <= len(parts) <= 32 or len({p.part_id for p in parts}) != len(parts):
        raise StoryWorldError("NEEDS_POSE_REVIEW", "part count/identities invalid")
    output = Image.new("RGBA", canvas_size)
    trace: list[dict[str, object]] = []
    for part in sorted(parts, key=lambda p: p.z_index):
        if part.object_id != object_id or part.source_image_sha256 != source_sha256:
            raise StoryWorldError("SOURCE_ASSET_MISMATCH", "part identity/source mismatch")
        if part.part_id not in assets or part.part_id not in asset_png_by_id:
            raise StoryWorldError("SOURCE_ASSET_MISMATCH", "rig asset missing")
        if hashlib.sha256(asset_png_by_id[part.part_id]).hexdigest() != part.asset_sha256:
            raise StoryWorldError("SOURCE_ASSET_MISMATCH", "rig PNG changed")
        if part.start_joint not in joints or part.end_joint not in joints:
            raise StoryWorldError("NEEDS_POSE_REVIEW", "missing joint target")
        image = assets[part.part_id]
        if image.size != canvas_size or image.mode != "RGBA":
            raise StoryWorldError("NEEDS_MASK_REVIEW", "part must use source canvas coordinates")
        # Verify both supplied representations, not merely an unrelated PNG digest.
        verified = Image.open(io.BytesIO(asset_png_by_id[part.part_id])).convert("RGBA")
        if verified.size != image.size or verified.tobytes() != image.tobytes():
            raise StoryWorldError("SOURCE_ASSET_MISMATCH", "decoded part does not match PNG")
        matrix = inverse_bone_affine(part.bind_start, part.bind_end,
                                     joints[part.start_joint], joints[part.end_joint])
        warped = image.convert("RGBa").transform(
            canvas_size, Image.Transform.AFFINE, matrix, Image.Resampling.BICUBIC,
        ).convert("RGBA")
        output = Image.alpha_composite(output, warped)
        trace.append({"part_id": part.part_id, "object_id": object_id,
                      "inverse_affine": list(matrix),
                      "start": list(joints[part.start_joint]),
                      "end": list(joints[part.end_joint]), "provenance": part.provenance})
    return output, trace


def eased_camera_frame(
    board: Image.Image, *, elapsed: float, duration: float,
    start_zoom: float = 1., end_zoom: float = 1.08, center: Point = (.5, .5),
) -> Image.Image:
    if (not math.isfinite(elapsed) or not math.isfinite(duration) or duration <= 0
        or not 1 <= start_zoom <= 1.2 or not 1 <= end_zoom <= 1.2
        or not all(math.isfinite(v) and 0 <= v <= 1 for v in center)):
        raise StoryWorldError("MOTION_TIMING_INVALID", "bounded camera inputs invalid")
    zoom = start_zoom + (end_zoom - start_zoom) * ease(elapsed / duration)
    width, height = board.size
    left = min(max(center[0] * width - width / zoom / 2, 0), width - width / zoom)
    top = min(max(center[1] * height - height / zoom / 2, 0), height - height / zoom)
    return board.transform(board.size, Image.Transform.AFFINE,
                           (1 / zoom, 0, left, 0, 1 / zoom, top), Image.Resampling.BICUBIC)
