"""FEAT-093 Amendment D: warm-up, activity suggestions, topic subjects and the video timeline on the deployed worker.

Run with the backend virtualenv from the repository root. Synthetic input only.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo / "backend" / "src"))

import modal  # noqa: E402

from sketch2life.application.services.parent_activity_suggestions import (  # noqa: E402
    ParentActivitySuggestionService,
    generate_activity_suggestions,
)
from sketch2life.application.video_pipeline.age_profile import profile_for_age_months  # noqa: E402
from sketch2life.application.video_pipeline.timeline_planner import PlannerSubject, plan_timeline  # noqa: E402
from sketch2life.infrastructure.ai.modal_function_client import ModalJsonFunctionClient  # noqa: E402
from sketch2life.infrastructure.story_video.modal_timeline import ModalVideoTimelineGenerator  # noqa: E402

results: dict[str, Any] = {}


def step(name: str, call: Any) -> Any:
    started = time.perf_counter()
    try:
        value = call()
    except Exception as error:  # noqa: BLE001
        results[name] = {"seconds": round(time.perf_counter() - started, 1), "error": f"{type(error).__name__}:{error}"}
        print(name, json.dumps(results[name], ensure_ascii=False), flush=True)
        return None
    results[name] = {"seconds": round(time.perf_counter() - started, 1)}
    print(name, results[name], flush=True)
    return value


class _NoLessons:
    def list_accessible_lessons(self, **_kwargs: Any) -> list[Any]:
        return []

    def __getattr__(self, _name: str) -> Any:
        return lambda **_kwargs: []


worker = modal.Function.from_name("sketch2life-srs23-language-audio-dev", "qwen-worker", environment_name="dev")
step("warm-up", lambda: worker.remote({"warmup": True}))

service = ParentActivitySuggestionService(_NoLessons())
for label, subject, features in (
    ("activity: turtle", "rùa", ["vỏ xanh lá có các ô hình lục giác", "bốn chân nhỏ"]),
    ("activity: chick", "con gà con", ["thân màu vàng", "mỏ màu cam", "cỏ xanh dưới chân"]),
    ("activity: bicycle", "xe đạp", ["khung màu đỏ", "hai bánh tròn màu đen"]),
):
    prepared = service.prepare(
        parent_principal_ref="synthetic-smoke",
        context_snapshot={"age_months": 48, "topic": "Khám phá", "adult_confirmed_idea": subject},
        subject_label=subject,
        visible_features=features,
        pinned_lesson_snapshot=None,
    )
    calls: list[int] = []

    def invoke() -> Any:
        calls.append(1)
        return ModalJsonFunctionClient().invoke("parent.activity.suggest", prepared.worker_input)

    outcome = step(
        label,
        lambda: generate_activity_suggestions(
            invoke,
            lambda answer: service.resolve(
                prepared=prepared,
                raw_result=answer.output["result"],
                request_id=str(uuid.uuid4()),
                story_run_id=str(uuid.uuid4()),
                understanding_revision=1,
                modal_call_id=answer.call_id,
            ),
        ),
    )
    results[label]["model_calls"] = len(calls)
    if outcome is not None:
        for item in outcome[1]["activities"]:
            print("  -", item["title"], "|", item["objective"], flush=True)

subjects = step(
    "topic-subjects.suggest",
    lambda: ModalJsonFunctionClient().invoke(
        "parent.topic-subjects.suggest",
        {"schema_version": "sketch2life.parent-topic-subject-input.v1", "topic": "Khu vườn", "excluded_subjects": []},
    ),
)
if subjects is not None:
    print("  ", json.dumps(subjects.output.get("result"), ensure_ascii=False)[:400], flush=True)
checked = step(
    "topic-subjects.validate",
    lambda: ModalJsonFunctionClient().invoke(
        "parent.topic-subjects.validate",
        {"schema_version": "sketch2life.parent-topic-subject-validation-input.v1", "topic": "Khu vườn", "subject": "con ốc sên"},
    ),
)
if checked is not None:
    print("  ", json.dumps(checked.output.get("result"), ensure_ascii=False)[:300], flush=True)

story = {
    "title": "Gà Con tìm giọt sương",
    "opening": "Gà Con thức dậy và thấy một giọt sương trên lá cỏ.",
    "middle": "Gà Con bước chậm lại gần để nhìn giọt sương lung linh.",
    "ending": "Giọt sương rơi xuống đất và Gà Con vui vẻ đi tìm giọt khác.",
}
for age, label in ((48, "timeline 36-71"), (84, "timeline 72-107"), (114, "timeline 108-120")):
    timeline = step(
        label,
        lambda age=age: plan_timeline(
            profile=profile_for_age_months(age),
            story=story,
            subjects=(PlannerSubject("main", "con gà con", "main"), PlannerSubject("sec-1", "cỏ", "secondary")),
            activity={"title": "Tìm giọt sương", "objective": "Quan sát nước trên lá."},
            topic="Nông trại",
            generator=ModalVideoTimelineGenerator(),
        ),
    )
    if timeline is not None:
        results[label]["scenes"] = len(timeline.scenes)

Path(__file__).with_name("smoke_other_result.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
