"""FEAT-094: a script the worker accepts must also pass the backend and the video's own text rules.

A rule that only the video applies would fail the run after the adult had already confirmed the story.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.application.video_pipeline.learning_timeline import timeline_from_learning
from sketch2life.application.video_pipeline.story_timeline import TimelineError, check_line_text
from sketch2life.domain.learning_script import check_learning_script

from test_learning_script import FACTS, NARRATIONS
from test_learning_story_wiring import _complete, _draft, _learning_reservation
from test_video_pipeline_orchestrator import _source

WORKER = Path(__file__).resolve().parents[3] / "deployment" / "modal" / "srs_v23" / "learning_story.py"


def _worker() -> Any:
    spec = importlib.util.spec_from_file_location("sketch2life_learning_story_parity", WORKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _script(narrations: list[str]) -> dict[str, Any]:
    return {
        "title": "Gà Vàng trong vườn",
        "scenes": [
            {"title": f"Cảnh vườn {index}", "narration": text, "key_term": "gà",
             "action_en": "The chick pecks the ground gently.", "setting_en": "A sunny farm yard with green grass."}
            for index, text in enumerate(narrations, start=1)
        ],
    }


def test_what_the_worker_assembles_passes_every_later_check() -> None:
    worker = _worker()
    assigned = worker.assign_facts(5, FACTS)
    assert worker.check_script(_script(NARRATIONS), assigned, subject="con gà", max_words=18) is None

    story, learning = worker.assemble(
        _script(NARRATIONS), assigned, FACTS, source="AI_DRAFT", seconds=10, features=["mỏ cam"]
    )
    normalized, _digest = normalize_story_output(story, confirmed_subject="con gà")
    stored = check_learning_script(
        normalized, learning,
        request={"scene_count": 5, "scene_seconds": 10, "max_words": 18, "fact_count": 3, "facts": []},
        subject="con gà",
    )
    scenes = [
        {**entry, "title": scene["title"], "narration": scene["narration"]}
        for entry, scene in zip(stored["scenes"], normalized["scenes"], strict=True)
    ]
    video = timeline_from_learning(replace(_source(), learning={"title": normalized["title"], "scenes": scenes}))

    assert [item.narration.text for item in video.scenes] == NARRATIONS
    json.dumps(stored, ensure_ascii=False)


UNSPEAKABLE = [
    "Buổi trưa, Gà Vàng thấy khẩu súng đồ chơi dưới cây.",  # FEAT-098: "sung sướng" is allowed now
    "Buổi trưa, Gà Vàng nằm im như đã chết dưới cây.",
    "Buổi trưa, Gà Vàng đi tìm bóng mát mà.",
    "Buổi trưa, Gà Vàng đi tìm bóng mát ở.",
    "Buổi trưa, Gà Vàng đi tìm nơi nó đang.",
    "Buổi trưa, Gà Vàng chạy thật nhanh đến. Trời mát.",
    "Buổi trưa, Gà Vàng nhặt hạt thóc rơi từ.",
]


@pytest.mark.parametrize("narration", UNSPEAKABLE)
def test_the_worker_rewrites_what_the_video_or_the_contract_would_refuse(narration: str) -> None:
    worker = _worker()
    narrations = list(NARRATIONS)
    narrations[2] = narration

    assert worker.check_script(_script(narrations), worker.assign_facts(5, FACTS), subject="con gà", max_words=18)


def test_the_backend_refuses_a_confirmed_text_the_video_cannot_speak() -> None:
    from sketch2life.application.services.story_output import StoryOutputInvalid

    raw = _draft()
    raw["scenes"][2]["narration"] = raw["scenes"][2]["action"] = UNSPEAKABLE[0]
    raw["story"]["middle"] = " ".join(scene["narration"] for scene in raw["scenes"][1:-1])
    with pytest.raises(TimelineError):
        check_line_text(UNSPEAKABLE[0])

    with pytest.raises(StoryOutputInvalid):
        _complete(raw, _learning_reservation())
