"""Lossless-source-asset scene stills for the explicit V2 prototype, not video."""

from __future__ import annotations

import hashlib
import io

from PIL import Image

from sketch2life.application.services.story_world_model import SourceAssetRegistry, StoryWorldError
from sketch2life.contracts.schemas.story_world_v2 import ScenePlanV2


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
        board = Image.new("RGBA", (width, height), (255, 255, 255, 255))
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
