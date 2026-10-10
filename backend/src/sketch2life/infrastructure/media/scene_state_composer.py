"""Lossless-source-asset scene stills for the explicit V2 prototype, not video."""

from __future__ import annotations

import hashlib
import io

from PIL import Image, ImageChops, ImageStat

from sketch2life.application.services.story_world_model import SourceAssetRegistry, StoryWorldError
from sketch2life.contracts.schemas.story_world_v2 import ScenePlanV2


def source_canvas_layers(registry: SourceAssetRegistry) -> tuple[Image.Image, Image.Image]:
    """Return white-composited source and its object-cleared static background.

    Pixels hidden behind source objects are unknown. White in those regions is a
    placeholder, not inpainting or a claim that the original background is recovered.
    """
    body = registry.source_image_bytes
    if body is None or hashlib.sha256(body).hexdigest() != registry.world.source_image_sha256:
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "original source bytes missing or changed")
    try:
        original = Image.open(io.BytesIO(body)).convert("RGBA")
    except (OSError, ValueError) as error:
        raise StoryWorldError(
            "SOURCE_ASSET_MISMATCH", "original image cannot be decoded"
        ) from error
    if original.size != (registry.world.source_width, registry.world.source_height):
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "original image size changed")
    white = Image.new("RGBA", original.size, "white")
    original = Image.alpha_composite(white, original)
    union = Image.new("L", original.size, 0)
    masks: list[Image.Image] = []
    for spec in registry.world.source_objects:
        encoded = registry.mask_png_by_id.get(spec.object_id)
        if encoded is None or hashlib.sha256(encoded).hexdigest() != spec.source_mask_sha256:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "source mask missing or changed")
        mask = Image.open(io.BytesIO(encoded)).convert("L")
        if mask.size != original.size:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "source mask dimensions changed")
        union = ImageChops.lighter(union, mask)
        masks.append(mask)
    background = original.copy()
    for mask in masks:
        bounds = mask.getbbox()
        if bounds is None:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "source mask is empty")
        left, top, right, bottom = bounds
        region = (max(0, left - 8), max(0, top - 8),
                  min(original.width, right + 8), min(original.height, bottom + 8))
        outside = ImageChops.invert(union.crop(region))
        if outside.getbbox() is None:
            placeholder = (255, 255, 255, 255)
        else:
            rgb = ImageStat.Stat(original.crop(region), outside).median[:3]
            placeholder = (int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)
        background.paste(placeholder, (0, 0), mask)
    return original, background


class SceneStateComposer:
    def render_scene(
        self, registry: SourceAssetRegistry, scene: ScenePlanV2,
        *, width: int | None = None, height: int | None = None,
    ) -> Image.Image:
        """Render one target-state still. Walking, running and new assets block explicitly."""
        if scene.action not in {"STATIC", "TRANSLATE", "SCALE", "ROTATE"}:
            raise StoryWorldError("UNSUPPORTED_ACTION", f"{scene.action} needs a motion renderer")
        if scene.new_object_ids:
            raise StoryWorldError("UNSUPPORTED_ACTION", "approved new object has no reviewed asset")
        world = registry.world
        width = width or world.source_width
        height = height or world.source_height
        if width <= 0 or height <= 0:
            raise StoryWorldError("COMPOSER_SIZE_INVALID", "positive canvas size required")
        if {state.object_id for state in scene.target_states} != {
            obj.object_id for obj in world.source_objects
        }:
            raise StoryWorldError("SCENE_STATE_INVALID", "state must cover source IDs exactly")
        if scene.order == 1 and scene.starting_states != world.initial_states:
            raise StoryWorldError("SCENE_STATE_INVALID", "first scene starts from wrong world")
        _original, background = source_canvas_layers(registry)
        board = background.resize((width, height), Image.Resampling.LANCZOS)
        specs = {obj.object_id: obj for obj in world.source_objects}
        for state in sorted(scene.target_states, key=lambda item: item.z_index):
            if not state.visible:
                continue
            spec = specs[state.object_id]
            encoded = registry.asset_png_by_id.get(state.object_id)
            if encoded is None or hashlib.sha256(encoded).hexdigest() != spec.asset_sha256:
                raise StoryWorldError("SOURCE_ASSET_MISMATCH", "source cutout missing or changed")
            source_asset = Image.open(io.BytesIO(encoded)).convert("RGBA")
            base_scale = min(width / world.source_width, height / world.source_height)
            size = (max(1, round(source_asset.width * base_scale * state.scale)),
                    max(1, round(source_asset.height * base_scale * state.scale)))
            asset = source_asset.resize(size, Image.Resampling.LANCZOS)
            if state.rotation_degrees:
                asset = asset.rotate(-state.rotation_degrees, resample=Image.Resampling.BICUBIC,
                                     expand=True)
            left = round(state.x * width - asset.width / 2)
            top = round(state.y * height - asset.height / 2)
            board.alpha_composite(asset, (left, top))
        if scene.camera.zoom > 1 or (scene.camera.center_x, scene.camera.center_y) != (0.5, 0.5):
            crop_width = width / scene.camera.zoom
            crop_height = height / scene.camera.zoom
            camera_left = min(max(scene.camera.center_x * width - crop_width / 2, 0),
                              width - crop_width)
            camera_top = min(max(scene.camera.center_y * height - crop_height / 2, 0),
                             height - crop_height)
            board = board.crop((round(camera_left), round(camera_top),
                                round(camera_left + crop_width),
                                round(camera_top + crop_height))).resize(
                                    (width, height), Image.Resampling.LANCZOS
                                )
        return board.convert("RGB")
