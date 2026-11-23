"""Validated visual continuity plans and prompt compilation for silent stories."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

STORY_VISUAL_PLAN_SCHEMA = "sketch2life.modal.story-visual-plan.v2"
PROMPT_TEMPLATE_VERSION = "story-i2v-v4"
_ENTITY_ID = re.compile(r"\A[a-z][a-z0-9-]{1,47}\Z")
_CAMERA_MOTIONS = {"locked", "slow_follow", "slow_push"}
_FRAME_RATE = 24
_FRAME_QUANTUM = 8
_MIN_MODEL_FRAMES = 9


class StoryVisualPlanError(ValueError):
    """An unsafe, incomplete, or internally inconsistent visual plan."""


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def plan_scene_frames(
    duration_seconds: float, *, frame_rate: int = _FRAME_RATE
) -> dict[str, int | float]:
    """Choose the nearest LTX 1+8k frame count, then time-map to exact output frames."""

    if (
        isinstance(duration_seconds, bool)
        or not isinstance(duration_seconds, (int, float))
        or not math.isfinite(float(duration_seconds))
        or duration_seconds <= 0
        or type(frame_rate) is not int
        or frame_rate <= 0
    ):
        raise StoryVisualPlanError("VIDEO_STORY_TIMELINE_INVALID")

    target_frames = round(float(duration_seconds) * frame_rate)
    if target_frames <= 0:
        raise StoryVisualPlanError("VIDEO_STORY_TIMELINE_INVALID")
    lower = max(
        _MIN_MODEL_FRAMES,
        ((max(_MIN_MODEL_FRAMES, target_frames) - 1) // _FRAME_QUANTUM) * _FRAME_QUANTUM
        + 1,
    )
    upper = lower + _FRAME_QUANTUM
    generated_frames = min(
        (lower, upper), key=lambda frames: (abs(frames - target_frames), frames)
    )
    return {
        "target_frame_count": target_frames,
        "generated_frame_count": generated_frames,
        "temporal_scale": target_frames / generated_frames,
    }


def validate_story_visual_plan(
    visual_plan: Any,
    *,
    scenes: list[dict[str, Any]],
    story_sha256: str,
) -> dict[str, Any]:
    """Validate entity presence and scene transitions against the approved scene actions."""

    top_keys = {"schema_version", "source_story_sha256", "entities", "scenes"}
    if not isinstance(visual_plan, dict) or set(visual_plan) != top_keys:
        raise StoryVisualPlanError("VIDEO_STORY_VISUAL_PLAN_INVALID")
    if (
        visual_plan.get("schema_version") != STORY_VISUAL_PLAN_SCHEMA
        or visual_plan.get("source_story_sha256") != story_sha256
    ):
        raise StoryVisualPlanError("VIDEO_STORY_VISUAL_PLAN_HASH_MISMATCH")

    entities = visual_plan.get("entities")
    plan_scenes = visual_plan.get("scenes")
    if (
        not isinstance(entities, list)
        or not 1 <= len(entities) <= 16
        or not isinstance(plan_scenes, list)
        or len(plan_scenes) != len(scenes)
    ):
        raise StoryVisualPlanError("VIDEO_STORY_VISUAL_PLAN_INVALID")

    entity_map: dict[str, dict[str, Any]] = {}
    source_entities: set[str] = set()
    subject_ids: set[str] = set()
    for entity in entities:
        keys = {"entity_id", "kind", "source", "label", "appearance"}
        if not isinstance(entity, dict) or set(entity) != keys:
            raise StoryVisualPlanError("VIDEO_STORY_ENTITY_INVALID")
        entity_id = entity.get("entity_id")
        kind = entity.get("kind")
        source = entity.get("source")
        if (
            not isinstance(entity_id, str)
            or _ENTITY_ID.fullmatch(entity_id) is None
            or entity_id in entity_map
            or kind not in {"subject", "prop"}
            or source not in {"source_drawing", "story_directed"}
            or (kind == "subject") != (source == "source_drawing")
            or not _bounded_text(entity.get("label"), 1, 80)
            or not _bounded_text(entity.get("appearance"), 8, 240)
        ):
            raise StoryVisualPlanError("VIDEO_STORY_ENTITY_INVALID")
        entity_map[entity_id] = entity
        if source == "source_drawing":
            source_entities.add(entity_id)
        if kind == "subject":
            subject_ids.add(entity_id)

    if (
        len(source_entities) != 1
        or len(subject_ids) != 1
        or source_entities != subject_ids
    ):
        raise StoryVisualPlanError("VIDEO_STORY_SUBJECT_ANCHOR_INVALID")

    previous_visible = set(source_entities)
    seen_entities: set[str] = set()
    for expected_index, (scene, plan_scene) in enumerate(
        zip(scenes, plan_scenes, strict=True), start=1
    ):
        keys = {
            "scene_id",
            "approved_action",
            "duration_seconds",
            "visible_entity_ids",
            "introduced_entity_ids",
            "removed_entity_ids",
            "continuity_in",
            "continuity_out",
            "spatial_direction",
            "model_action_instruction",
            "camera_motion",
        }
        if not isinstance(plan_scene, dict) or set(plan_scene) != keys:
            raise StoryVisualPlanError("VIDEO_STORY_VISUAL_SCENE_INVALID")
        visible = _entity_ids(plan_scene.get("visible_entity_ids"), entity_map)
        introduced = _entity_ids(plan_scene.get("introduced_entity_ids"), entity_map)
        removed = _entity_ids(plan_scene.get("removed_entity_ids"), entity_map)
        expected_introduced = visible - previous_visible
        expected_removed = previous_visible - visible
        duration = plan_scene.get("duration_seconds")
        if (
            plan_scene.get("scene_id") != scene.get("scene_id")
            or plan_scene.get("approved_action") != scene.get("action")
            or type(duration) not in (int, float)
            or not math.isfinite(float(duration))
            or abs(float(duration) - float(scene.get("duration_seconds", -1))) > 1e-6
            or visible is None
            or introduced is None
            or removed is None
            or not subject_ids.issubset(visible)
            or introduced != expected_introduced
            or removed != expected_removed
            or not _bounded_text(plan_scene.get("continuity_in"), 1, 240)
            or not _bounded_text(plan_scene.get("continuity_out"), 1, 240)
            or not _bounded_text(plan_scene.get("spatial_direction"), 0, 160)
            or not _bounded_text(plan_scene.get("model_action_instruction"), 8, 400)
            or plan_scene.get("camera_motion") not in _CAMERA_MOTIONS
        ):
            raise StoryVisualPlanError("VIDEO_STORY_VISUAL_TRANSITION_INVALID")
        seen_entities.update(visible)
        previous_visible = visible

    if seen_entities != set(entity_map):
        raise StoryVisualPlanError("VIDEO_STORY_ENTITY_NEVER_VISIBLE")
    return visual_plan


def compile_scene_prompt(
    scene: dict[str, Any], visual_plan: dict[str, Any], *, first_scene: bool
) -> str:
    """Compile a short action-first prompt from a validated visual plan."""

    plan_scene = next(
        item for item in visual_plan["scenes"] if item["scene_id"] == scene["scene_id"]
    )
    entity_map = {entity["entity_id"]: entity for entity in visual_plan["entities"]}
    visible = [entity_map[item] for item in plan_scene["visible_entity_ids"]]
    introduced = [entity_map[item] for item in plan_scene["introduced_entity_ids"]]
    removed = [entity_map[item] for item in plan_scene["removed_entity_ids"]]

    def describe(items: list[dict[str, Any]]) -> str:
        return (
            "; ".join(f"{item['label']}: {item['appearance']}" for item in items)
            or "none"
        )

    initial_image = (
        "the exact original child drawing"
        if first_scene
        else "the last frame of the preceding scene"
    )
    camera_instruction = {
        "locked": (
            "Camera is completely fixed. Keep subject scale, screen position, and crop constant; "
            "no pan, zoom, tilt, shake, or reframing."
        ),
        "slow_follow": "Use only a subtle, smooth follow movement; keep the full subject in frame.",
        "slow_push": "Use only the explicitly approved gentle push; do not crop or resize the subject.",
    }[plan_scene["camera_motion"]]
    opening_instruction = (
        "Use the exact original child drawing as the opening frame. Preserve the whole drawn subject."
        if first_scene
        else "Use the preceding scene's final frame as the exact opening state; continue its subject and prop placement."
    )
    prompt = "\n".join(
        (
            "Image-to-video. Animate the supplied image itself; it is the only design reference. Do not create a replacement illustration.",
            f"Opening state: {initial_image}. {opening_instruction}",
            "Identity lock across every frame: keep the same subject silhouette, proportions, colors, line thickness, hand-drawn/crayon texture, screen position, and apparent size. Do not vectorize, clean up, beautify, recolor, or invent markings.",
            f"Approved story action (source wording, unchanged): {plan_scene['approved_action']}",
            (
                "Faithful motion rendering of that action; add no event or behavior: "
                f"{plan_scene['model_action_instruction']}"
            ),
            "Animate only the body parts and planned prop needed for this action; hold all other drawing details and the paper background still.",
            f"Entities that must remain visible: {describe(visible)}.",
            f"Introduce in this scene: {describe(introduced)}. Add each introduced entity exactly once, at the described size, orientation, and position; keep it secondary and do not cover or redraw the subject.",
            f"Entities that must be absent by the end: {describe(removed)}.",
            f"Spatial direction: {plan_scene['spatial_direction'] or 'preserve the current relative positions'}.",
            f"Continuity at start: {plan_scene['continuity_in']}",
            f"Resolve by the end: {plan_scene['continuity_out']}",
            "Motion timing: show one clearly readable action from start to finish, then settle during the final fifth of the clip. Use restrained movement; no pose jump or teleport.",
            camera_instruction,
            "No extra entities, duplicate props, text, narration, subtitles, music, sound, or audio. Keep the background plain and stable.",
        )
    )
    if len(prompt) > 5_000:
        raise StoryVisualPlanError("VIDEO_STORY_PROMPT_LIMIT_EXCEEDED")
    return prompt


def _entity_ids(value: Any, entities: dict[str, dict[str, Any]]) -> set[str] | None:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or item not in entities for item in value)
        or len(value) != len(set(value))
    ):
        return None
    return set(value)


def _bounded_text(value: Any, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and minimum <= len(value.strip()) <= maximum
        and not any(ord(character) < 32 for character in value)
    )
