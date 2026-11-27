"""Hidden per-scene staging of a Parent story (FEAT-087).

For each scene the story model says where the main subject ends up and what happens to every
object an adult approved. The video worker builds its start/end keyframes from this. The data is
technical, never shown to the adult, and a violation never fails the story: callers drop the
staging and the video falls back to the plain (single-frame) path.
"""

from __future__ import annotations

from typing import Any

STAGING_SCHEMA = "sketch2life.story-staging.v1"
POSITIONS = tuple(
    f"{column}-{row}"
    for row in ("top", "middle", "bottom")
    for column in ("left", "center", "right")
)
MAIN_FACING = ("left", "right")
MAIN_SCALE = ("same", "slightly_bigger", "slightly_smaller")
SECONDARY_STATES = ("unchanged", "moved", "partly_gone", "gone")
_NEXT_STATES = {
    "unchanged": set(SECONDARY_STATES),
    "moved": set(SECONDARY_STATES),
    "partly_gone": {"partly_gone", "gone"},
    "gone": {"gone"},
}


class StagingError(ValueError):
    """Content-free staging violation."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _exact(value: Any, keys: set[str], code: str = "STAGING_SHAPE_INVALID") -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise StagingError(code)
    return value


def validate_staging(
    staging: Any, *, scene_count: int, approved_ids: tuple[str, ...]
) -> dict[str, Any]:
    """Return ``staging`` unchanged when valid, else raise :class:`StagingError`."""

    root = _exact(staging, {"schema_version", "scenes"})
    if root["schema_version"] != STAGING_SCHEMA or not isinstance(root["scenes"], list):
        raise StagingError("STAGING_SHAPE_INVALID")
    scenes = root["scenes"]
    if len(scenes) != scene_count:
        raise StagingError("STAGING_SCENE_COUNT_INVALID")
    last_state: dict[str, str] = {entity_id: "unchanged" for entity_id in approved_ids}
    for expected_index, scene in enumerate(scenes, start=1):
        scene = _exact(scene, {"scene_index", "main_end", "secondary_end"})
        if type(scene["scene_index"]) is not int or scene["scene_index"] != expected_index:
            raise StagingError("STAGING_SCENE_COUNT_INVALID")
        main = _exact(scene["main_end"], {"position", "facing", "scale"})
        if (
            main["position"] not in POSITIONS
            or main["facing"] not in MAIN_FACING
            or main["scale"] not in MAIN_SCALE
        ):
            raise StagingError("STAGING_FIELD_INVALID")
        entries = scene["secondary_end"]
        if not isinstance(entries, list):
            raise StagingError("STAGING_SHAPE_INVALID")
        seen: list[str] = []
        taken_cells: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict) or not {"entity_id", "state"} <= set(entry) <= {
                "entity_id",
                "state",
                "position",
            }:
                raise StagingError("STAGING_SHAPE_INVALID")
            entity_id, state = entry["entity_id"], entry["state"]
            if entity_id not in approved_ids or entity_id in seen:
                raise StagingError("STAGING_ENTITY_SET_INVALID")
            seen.append(entity_id)
            if state not in SECONDARY_STATES:
                raise StagingError("STAGING_FIELD_INVALID")
            has_position = "position" in entry
            if (state == "moved") != has_position or (
                has_position and entry["position"] not in POSITIONS
            ):
                raise StagingError("STAGING_FIELD_INVALID")
            if state not in _NEXT_STATES[last_state[entity_id]]:
                raise StagingError("STAGING_STATE_ORDER_INVALID")
            last_state[entity_id] = state
            if state == "moved":
                if entry["position"] == main["position"] or entry["position"] in taken_cells:
                    raise StagingError("STAGING_POSITION_CONFLICT")
                taken_cells.append(entry["position"])
        if set(seen) != set(approved_ids):
            raise StagingError("STAGING_ENTITY_SET_INVALID")
    return staging


def normalize_staging(
    staging: Any, *, scene_count: int, approved_ids: tuple[str, ...]
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate without raising: ``(staging, None)`` or ``(None, reason_code)``."""

    if staging is None:
        return None, "STAGING_ABSENT"
    try:
        return validate_staging(staging, scene_count=scene_count, approved_ids=approved_ids), None
    except StagingError as exc:
        return None, exc.code


_SECTION_KEYS = ("opening", "middle", "ending")


def pack_story_content(
    sections: dict[str, Any],
    staging: dict[str, Any] | None,
    issue: str | None,
    learning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Story JSONB: the visible sections, hidden staging (or why it was dropped) and the learning script."""

    packed = {key: sections[key] for key in _SECTION_KEYS}
    if staging is not None:
        packed["staging"] = staging
    elif issue is not None:
        packed["staging_issue"] = issue
    if learning is not None:
        packed["learning"] = learning  # FEAT-094
    return packed


def unpack_sections(story_content: dict[str, Any]) -> dict[str, Any]:
    """The visible sections only; staging never reaches the adult-facing story."""

    return {key: story_content[key] for key in _SECTION_KEYS}


def unpack_staging(story_content: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    staging = story_content.get("staging")
    if isinstance(staging, dict):
        return staging, None
    issue = story_content.get("staging_issue")
    return None, issue if isinstance(issue, str) else "STAGING_ABSENT"


def secondary_subjects_are_valid(value: Any) -> bool:
    """Shape of ``worker_input["secondary_subjects"]``: adult-approved extras, ids ``sec-1..3``."""

    if not isinstance(value, list) or not 1 <= len(value) <= 3:
        return False
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {"entity_id", "label", "visible_features"}:
            return False
        entity_id, label, features = item["entity_id"], item["label"], item["visible_features"]
        if entity_id not in {"sec-1", "sec-2", "sec-3"} or entity_id in seen:
            return False
        seen.add(entity_id)
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 80:
            return False
        if (
            not isinstance(features, list)
            or len(features) > 2
            or any(not isinstance(f, str) or not f.strip() or len(f) > 160 for f in features)
        ):
            return False
    return True


def split_story_staging(
    raw_story: dict[str, Any], worker_input: dict[str, Any], *, scene_count: int
) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Separate the worker's reserved staging keys from the story and re-validate them.

    The backend never trusts the worker's verdict: staging is checked against the objects the
    adult approved (``worker_input["secondary_subjects"]``). A bad staging is dropped, never fatal.
    """

    story = {k: v for k, v in raw_story.items() if k not in ("_staging", "_staging_issue")}
    staging = raw_story.get("_staging")
    worker_issue = raw_story.get("_staging_issue")
    if staging is None:
        return story, None, worker_issue if isinstance(worker_issue, str) else "STAGING_ABSENT"
    approved = tuple(item["entity_id"] for item in worker_input.get("secondary_subjects") or [])
    valid, issue = normalize_staging(staging, scene_count=scene_count, approved_ids=approved)
    return story, valid, issue
