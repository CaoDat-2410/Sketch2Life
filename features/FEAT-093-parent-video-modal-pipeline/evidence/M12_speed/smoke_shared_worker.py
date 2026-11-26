"""FEAT-093 Amendment C: call the deployed shared Qwen worker with synthetic inputs and print timings.

Run with the backend virtualenv from the repository root:
    backend/.venv/Scripts/python.exe <this file> <drawing.png|jpg>
No credentials or account data are read; Modal authentication comes from the local Modal profile.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo / "backend" / "src"))

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months  # noqa: E402
from sketch2life.application.video_pipeline.timeline_planner import (  # noqa: E402
    PlannerSubject,
    plan_timeline,
)
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    ModalDrawingFunctionClient,
    ModalStoryFunctionClient,
    canonical_json,
    prepare_drawing_input,
)
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


drawing = Path(sys.argv[1]).read_bytes()
prepared = prepare_drawing_input(
    source_bytes=drawing,
    source_media_type="image/png" if drawing[:4] == b"\x89PNG" else "image/jpeg",
    expected_source_sha256=hashlib.sha256(drawing).hexdigest(),
    job_id=str(uuid.uuid4()),
    generation_id=str(uuid.uuid4()),
    attempt_id=str(uuid.uuid4()),
)
understanding = step("drawing.analyze (cold)", lambda: ModalDrawingFunctionClient().invoke(prepared))
if understanding is not None:
    results["drawing.analyze (cold)"]["result"] = understanding.output.get("result")
    print(json.dumps(understanding.output.get("result"), ensure_ascii=False), flush=True)

activity = {
    "title": "Theo dấu chân rùa trên sân",
    "objective": "Trẻ nhận ra đặc điểm di chuyển chậm của rùa.",
    "materials_text": "Phấn màu và vài viên gạch nhỏ",
    "preparation_text": "Người lớn chuẩn bị một khoảng sân phẳng.",
    "instructions_text": "Bé vẽ dấu chân rồi đi chậm theo đường vừa vẽ.",
    "observation_notes": "Quan sát bé giữ thăng bằng.",
    "safety_notes": "Người lớn đi cùng bé.",
    "activity_kind": "outdoor",
}
story_input = {
    "schema_version": "sketch2life.story-generation-input.v3",
    "role": "PARENT",
    "language": "vi",
    "topic": "Động vật",
    "confirmed_subject": "rùa",
    "understanding_revision": 1,
    "drawing_sha256": prepared.drawing_sha256,
    "visible_features": ["vỏ xanh lá có các ô hình lục giác", "đầu tròn màu nâu nhạt", "bốn chân xanh nhạt"],
    "child_age_months": 48,
    "context_revision": 1,
    "adult_confirmed_idea": "con rùa",
    "rewrite_instruction": None,
    "lesson_subject_learning_notes": None,
    "lesson_direction": None,
    "primary_activity": activity,
    "primary_activity_sha256": hashlib.sha256(canonical_json(activity).encode("utf-8")).hexdigest(),
}
for label in ("story.generate", "story.generate (second)"):
    story = step(label, lambda: ModalStoryFunctionClient().generate({"worker_input": story_input}))
    if story is not None:
        results[label]["story"] = story[0]
        print(json.dumps({"title": story[0]["title"], **story[0]["story"]}, ensure_ascii=False), flush=True)
        for scene in story[0]["scenes"]:
            print("  -", scene["action"], "|", scene["narration"], flush=True)

source_story = results.get("story.generate", {}).get("story")
if source_story:
    timeline = step(
        "video.timeline.generate",
        lambda: plan_timeline(
            profile=profile_for_age_months(48),
            story={"title": source_story["title"], **source_story["story"]},
            subjects=(PlannerSubject("main", "rùa", "main"),),
            activity=activity,
            topic="Động vật",
            generator=ModalVideoTimelineGenerator(),
        ),
    )
    if timeline is not None:
        for scene in timeline.scenes:
            print("  scene", scene.index, scene.lines[0].text if getattr(scene, "lines", None) else "", flush=True)

Path(__file__).with_name("smoke_result.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
