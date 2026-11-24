"""FEAT-087 M4: hidden per-scene staging (where the main subject ends, what happens to objects)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from sketch2life.application.story_staging import (
    STAGING_SCHEMA,
    StagingError,
    normalize_staging,
    validate_staging,
)

APPROVED = ("sec-1",)


def _scene(
    index: int, state: str = "unchanged", sec_position: str | None = None, **main: str
) -> dict:
    entry: dict[str, Any] = {"entity_id": "sec-1", "state": state}
    if sec_position is not None:
        entry["position"] = sec_position
    return {
        "scene_index": index,
        "main_end": {
            "position": main.get("position", "center-middle"),
            "facing": main.get("facing", "right"),
            "scale": main.get("scale", "same"),
        },
        "secondary_end": [entry],
    }


def _staging(*scenes: dict) -> dict:
    return {"schema_version": STAGING_SCHEMA, "scenes": list(scenes)}


def test_a_valid_turtle_eats_leaf_staging_passes() -> None:
    staging = _staging(
        _scene(1, position="left-middle"),
        _scene(2, position="center-middle"),
        _scene(3, position="right-middle", scale="slightly_bigger"),
        _scene(4, "partly_gone", position="right-middle"),
        _scene(5, "gone", position="right-middle"),
    )
    # (main_end position is the `position` keyword; secondaries only carry one when `moved`)
    assert validate_staging(staging, scene_count=5, approved_ids=APPROVED) == staging


def test_no_approved_secondaries_means_empty_secondary_lists() -> None:
    scenes = [
        {
            "scene_index": i,
            "main_end": {"position": "center-middle", "facing": "left", "scale": "same"},
            "secondary_end": [],
        }
        for i in range(1, 6)
    ]
    staging = _staging(*scenes)
    assert validate_staging(staging, scene_count=5, approved_ids=()) == staging


def test_moved_needs_a_position_and_other_states_must_not_have_one() -> None:
    bad = _staging(*(_scene(i) for i in range(1, 6)))
    bad["scenes"][1]["secondary_end"][0] = {"entity_id": "sec-1", "state": "moved"}
    with pytest.raises(StagingError) as e:
        validate_staging(bad, scene_count=5, approved_ids=APPROVED)
    assert e.value.code == "STAGING_FIELD_INVALID"
    bad = _staging(*(_scene(i) for i in range(1, 6)))
    bad["scenes"][1]["secondary_end"][0] = {
        "entity_id": "sec-1",
        "state": "unchanged",
        "position": "left-top",
    }
    with pytest.raises(StagingError):
        validate_staging(bad, scene_count=5, approved_ids=APPROVED)


def test_a_gone_object_cannot_come_back() -> None:
    staging = _staging(_scene(1), _scene(2, "gone"), _scene(3, "unchanged"), _scene(4), _scene(5))
    with pytest.raises(StagingError) as e:
        validate_staging(staging, scene_count=5, approved_ids=APPROVED)
    assert e.value.code == "STAGING_STATE_ORDER_INVALID"


def test_a_partly_gone_object_cannot_become_whole_again_or_move() -> None:
    for later in ("unchanged", "moved"):
        scenes = [_scene(1), _scene(2, "partly_gone"), _scene(3), _scene(4), _scene(5)]
        scenes[2] = _scene(3, later, sec_position="left-top" if later == "moved" else None)
        with pytest.raises(StagingError) as e:
            validate_staging(_staging(*scenes), scene_count=5, approved_ids=APPROVED)
        assert e.value.code == "STAGING_STATE_ORDER_INVALID"


def test_partly_gone_may_continue_then_disappear() -> None:
    staging = _staging(
        _scene(1),
        _scene(2, "partly_gone"),
        _scene(3, "partly_gone"),
        _scene(4, "gone"),
        _scene(5, "gone"),
    )
    assert validate_staging(staging, scene_count=5, approved_ids=APPROVED)


def test_a_secondary_cannot_move_into_the_main_subjects_cell() -> None:
    staging = _staging(
        _scene(1),
        _scene(2, "moved", sec_position="center-middle"),
        _scene(3),
        _scene(4),
        _scene(5),
    )
    with pytest.raises(StagingError) as e:
        validate_staging(staging, scene_count=5, approved_ids=APPROVED)
    assert e.value.code == "STAGING_POSITION_CONFLICT"


def test_two_secondaries_cannot_move_into_the_same_cell() -> None:
    staging = _staging(*(_scene(i) for i in range(1, 6)))
    for scene in staging["scenes"]:
        scene["secondary_end"].append({"entity_id": "sec-2", "state": "unchanged"})
    staging["scenes"][1]["secondary_end"][0] = {
        "entity_id": "sec-1",
        "state": "moved",
        "position": "left-top",
    }
    staging["scenes"][1]["secondary_end"][1] = {
        "entity_id": "sec-2",
        "state": "moved",
        "position": "left-top",
    }
    with pytest.raises(StagingError) as e:
        validate_staging(staging, scene_count=5, approved_ids=("sec-1", "sec-2"))
    assert e.value.code == "STAGING_POSITION_CONFLICT"


@pytest.mark.parametrize(
    "mutate, code",
    [
        (lambda s: s.__setitem__("schema_version", "x"), "STAGING_SHAPE_INVALID"),
        (lambda s: s.__setitem__("extra", 1), "STAGING_SHAPE_INVALID"),
        (lambda s: s["scenes"].pop(), "STAGING_SCENE_COUNT_INVALID"),
        (lambda s: s["scenes"][0].__setitem__("scene_index", 2), "STAGING_SCENE_COUNT_INVALID"),
        (
            lambda s: s["scenes"][0]["main_end"].__setitem__("position", "middle"),
            "STAGING_FIELD_INVALID",
        ),
        (
            lambda s: s["scenes"][0]["main_end"].__setitem__("facing", "front"),
            "STAGING_FIELD_INVALID",
        ),
        (
            lambda s: s["scenes"][0]["main_end"].__setitem__("scale", "huge"),
            "STAGING_FIELD_INVALID",
        ),
        (
            lambda s: s["scenes"][0]["secondary_end"][0].__setitem__("state", "eaten"),
            "STAGING_FIELD_INVALID",
        ),
        (
            lambda s: s["scenes"][0]["secondary_end"][0].__setitem__("entity_id", "sec-2"),
            "STAGING_ENTITY_SET_INVALID",
        ),
        (lambda s: s["scenes"][0]["secondary_end"].clear(), "STAGING_ENTITY_SET_INVALID"),
        (lambda s: s["scenes"][0]["main_end"].__setitem__("note", "x"), "STAGING_SHAPE_INVALID"),
    ],
)
def test_malformed_staging_is_rejected_with_a_content_free_code(mutate, code) -> None:
    staging = _staging(*(_scene(i) for i in range(1, 6)))
    mutate(staging)
    with pytest.raises(StagingError) as e:
        validate_staging(staging, scene_count=5, approved_ids=APPROVED)
    assert e.value.code == code


def test_an_object_the_adult_did_not_approve_cannot_appear() -> None:
    staging = _staging(*(_scene(i) for i in range(1, 6)))
    with pytest.raises(StagingError) as e:
        validate_staging(staging, scene_count=5, approved_ids=())
    assert e.value.code == "STAGING_ENTITY_SET_INVALID"


def test_normalize_never_raises_and_reports_the_reason() -> None:
    good = _staging(*(_scene(i) for i in range(1, 6)))
    assert normalize_staging(good, scene_count=5, approved_ids=APPROVED) == (good, None)
    assert normalize_staging(None, scene_count=5, approved_ids=APPROVED) == (None, "STAGING_ABSENT")
    broken = deepcopy(good)
    broken["scenes"][0]["main_end"]["position"] = "nowhere"
    staging, issue = normalize_staging(broken, scene_count=5, approved_ids=APPROVED)
    assert staging is None and issue == "STAGING_FIELD_INVALID"
    assert normalize_staging("text", scene_count=5, approved_ids=APPROVED) == (
        None,
        "STAGING_SHAPE_INVALID",
    )


def test_story_content_packing_keeps_display_sections_clean() -> None:
    from sketch2life.application.story_staging import (
        pack_story_content,
        unpack_sections,
        unpack_staging,
    )

    sections = {"opening": "a", "middle": "b", "ending": "c"}
    staging = _staging(*(_scene(i) for i in range(1, 6)))
    packed = pack_story_content(sections, staging, None)
    assert unpack_sections(packed) == sections
    assert unpack_staging(packed) == (staging, None)
    assert unpack_sections(sections) == sections  # a record written before FEAT-087
    assert unpack_staging(sections) == (None, "STAGING_ABSENT")
    dropped = pack_story_content(sections, None, "STAGING_FIELD_INVALID")
    assert unpack_sections(dropped) == sections
    assert unpack_staging(dropped) == (None, "STAGING_FIELD_INVALID")
    assert pack_story_content(sections, None, None) == sections


def test_split_story_staging_removes_reserved_keys_and_validates_against_approved_ids() -> None:
    from sketch2life.application.story_staging import split_story_staging

    good = _staging(*(_scene(i) for i in range(1, 6)))
    raw = {"title": "t", "_staging": good, "_staging_issue": None}
    worker_input = {
        "secondary_subjects": [{"entity_id": "sec-1", "label": "lá", "visible_features": []}]
    }
    story, staging, issue = split_story_staging(raw, worker_input, scene_count=5)
    assert story == {"title": "t"} and staging == good and issue is None
    assert "_staging" in raw  # the caller's dict is not mutated

    # staging that names an object the adult did not approve is dropped, the story is kept
    story, staging, issue = split_story_staging(raw, {}, scene_count=5)
    assert story == {"title": "t"} and staging is None and issue == "STAGING_ENTITY_SET_INVALID"

    # a worker that sent no staging (older worker) is just "absent"
    story, staging, issue = split_story_staging({"title": "t"}, {}, scene_count=5)
    assert (staging, issue) == (None, "STAGING_ABSENT")

    # the worker's own reason code is preserved when it dropped staging itself
    story, staging, issue = split_story_staging(
        {"title": "t", "_staging": None, "_staging_issue": "STAGING_PASS_FAILED"}, {}, scene_count=5
    )
    assert (staging, issue) == (None, "STAGING_PASS_FAILED")
