"""FEAT-087 M4: worker-side staging contract (schema, prompt, parsing). No model or GPU."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
BACKEND_SRC = MODAL_DIR.parents[2] / "backend" / "src"
for p in (str(MODAL_DIR), str(BACKEND_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from sketch2life.application import story_staging as backend

import story_staging_worker as w

SECONDARIES = [
    {"entity_id": "sec-1", "label": "chiếc lá", "visible_features": ["màu xanh"]}
]
STORY = {
    "title": "Rùa và chiếc lá",
    "story": {"opening": "a", "middle": "b", "ending": "c"},
    "scenes": [
        {
            "title": f"Cảnh {i}",
            "action": f"hành động {i}",
            "visual_prompt": "x",
            "narration": "n",
            "character_anchors": ["mai"],
        }
        for i in range(1, 6)
    ],
}


def _valid(
    state_by_scene=("unchanged", "unchanged", "partly_gone", "gone", "gone"),
) -> dict:
    scenes = []
    for i, st in enumerate(state_by_scene, start=1):
        sec = {"entity_id": "sec-1", "state": st}
        scenes.append(
            {
                "scene_index": i,
                "main_end": {
                    "position": "center-middle",
                    "facing": "right",
                    "scale": "same",
                },
                "secondary_end": [sec],
            }
        )
    return {"schema_version": w.STAGING_SCHEMA, "scenes": scenes}


def test_schema_is_closed_enums_with_exact_scene_count() -> None:
    schema = w.staging_json_schema(scene_count=5, entity_ids=("sec-1",))
    text = json.dumps(schema)
    assert (
        "minimum" not in text and "maximum" not in text
    )  # LMFE ignores numeric ranges
    scene = schema["properties"]["scenes"]
    assert scene["minItems"] == scene["maxItems"] == 5
    item = scene["items"]["properties"]
    assert item["main_end"]["properties"]["position"]["enum"] == list(w.POSITIONS)
    assert item["main_end"]["properties"]["facing"]["enum"] == ["left", "right"]
    sec = item["secondary_end"]
    assert sec["minItems"] == sec["maxItems"] == 1
    assert sec["items"]["properties"]["entity_id"]["enum"] == ["sec-1"]
    assert sec["items"]["properties"]["state"]["enum"] == list(w.SECONDARY_STATES)


def test_schema_without_secondaries_has_empty_secondary_list() -> None:
    schema = w.staging_json_schema(scene_count=5, entity_ids=())
    sec = schema["properties"]["scenes"]["items"]["properties"]["secondary_end"]
    assert sec["maxItems"] == 0


def test_prompt_lists_story_actions_and_only_approved_objects() -> None:
    prompt = w.staging_prompt(STORY, subject="con rùa", secondaries=SECONDARIES)
    assert "con rùa" in prompt and "chiếc lá" in prompt and "sec-1" in prompt
    for i in range(1, 6):
        assert f"hành động {i}" in prompt
    assert "visual_prompt" not in prompt
    none = w.staging_prompt(STORY, subject="con rùa", secondaries=[])
    assert "sec-" not in none


def _model_output(staging: dict) -> dict:
    """What the model emits: no schema_version / scene_index (the worker adds them)."""
    raw = deepcopy(staging)
    del raw["schema_version"]
    for scene in raw["scenes"]:
        del scene["scene_index"]
    return raw


def test_parse_adds_scene_index_and_schema_version() -> None:
    raw = _model_output(_valid())
    out = w.parse_staging_output(
        json.dumps(raw), scene_count=5, approved_ids=("sec-1",)
    )
    assert out == (_valid(), None)


@pytest.mark.parametrize("text", ["", "not json", "[]", '{"scenes": 3}'])
def test_unparseable_output_gives_a_reason_not_an_exception(text: str) -> None:
    staging, issue = w.parse_staging_output(
        text, scene_count=5, approved_ids=("sec-1",)
    )
    assert staging is None and issue == "STAGING_SHAPE_INVALID"


def test_order_violation_is_reported_by_code() -> None:
    bad = _model_output(
        _valid(("gone", "unchanged", "unchanged", "unchanged", "unchanged"))
    )
    staging, issue = w.parse_staging_output(
        json.dumps(bad), scene_count=5, approved_ids=("sec-1",)
    )
    assert staging is None and issue == "STAGING_STATE_ORDER_INVALID"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: None,
        lambda s: s["scenes"][1]["secondary_end"][0].update(
            state="moved", position="left-top"
        ),
        lambda s: s["scenes"][1]["secondary_end"][0].update(
            state="moved", position="center-middle"
        ),
        lambda s: s["scenes"][0]["main_end"].update(facing="front"),
        lambda s: s["scenes"][2]["secondary_end"][0].update(state="gone"),
        lambda s: s["scenes"].pop(),
        lambda s: s["scenes"][0]["secondary_end"].clear(),
    ],
)
def test_worker_and_backend_validators_agree(mutate) -> None:
    staging = _valid()
    mutate(staging)

    def verdict(fn) -> str | None:
        try:
            fn(staging, scene_count=5, approved_ids=("sec-1",))
            return None
        except Exception as exc:  # noqa: BLE001
            return getattr(exc, "code", type(exc).__name__)

    assert verdict(w.validate_staging) == verdict(backend.validate_staging)
