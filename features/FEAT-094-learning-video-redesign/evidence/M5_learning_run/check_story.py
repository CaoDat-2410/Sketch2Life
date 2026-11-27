"""Generate one real learning script on the deployed story worker with synthetic data (FEAT-094 phase 4).

    docker exec -i sketch2life-video-worker-1 python -u - < features/.../M5_learning_run/check_story.py

Writes no business state. Runs the same request builder and backend gates as the API and saves the result to
``/tmp/feat094-story.json`` for ``check_video.py``.
"""

from __future__ import annotations

import hashlib
import json
import time

from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.application.story_staging import split_story_staging
from sketch2life.application.video_pipeline.story_timeline import check_line_text
from sketch2life.domain.learning_script import check_learning_script
from sketch2life.infrastructure.ai.modal_function_client import ModalStoryFunctionClient
from sketch2life.infrastructure.knowledge.learning_request import build_learning_request

AGE_MONTHS = 48
SUBJECT = "con gà"
FEATURES = ["mỏ cam", "mào đỏ", "đuôi hồng"]

activity = {
    "title": "Tìm lá trong sân",
    "objective": "Quan sát hình dạng của lá.",
    "materials_text": "Vài chiếc lá rụng.",
    "preparation_text": "Chọn lá sạch.",
    "instructions_text": "Cùng nhặt lá và nói về hình dạng của lá.",
    "observation_notes": "Để trẻ tự mô tả.",
    "safety_notes": "Người lớn chọn chỗ an toàn.",
    "activity_kind": "outdoor",
}
learning = build_learning_request(
    context={"age_months": AGE_MONTHS, "interests_summary": "thích động vật và khu vườn"},
    subject=SUBJECT,
    visible_features=FEATURES,
    lesson_notes=None,
    enabled=True,
)
worker_input = {
    "schema_version": "sketch2life.story-generation-input.v3",
    "role": "PARENT",
    "language": "vi",
    "topic": "Các loài chim",
    "confirmed_subject": SUBJECT,
    "understanding_revision": 1,
    "drawing_sha256": hashlib.sha256(b"synthetic-chick").hexdigest(),
    "visible_features": FEATURES,
    "child_age_months": AGE_MONTHS,
    "context_revision": 1,
    "adult_confirmed_idea": "",
    "rewrite_instruction": None,
    "lesson_subject_learning_notes": None,
    "lesson_direction": None,
    "primary_activity": activity,
    "primary_activity_sha256": hashlib.sha256(
        json.dumps(activity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest(),
    "learning": learning,
}
print("REQUEST", json.dumps({k: learning[k] for k in ("scene_count", "max_words", "fact_source", "interest_tags")}, ensure_ascii=False))

started = time.monotonic()
raw, _call_id = ModalStoryFunctionClient().generate({"worker_input": worker_input})
print(f"STORY_SECONDS {time.monotonic() - started:.1f}")

story, _staging, _issue = split_story_staging(raw, worker_input, scene_count=len(raw["scenes"]))
answered = story.pop("_learning")
normalized, _digest = normalize_story_output(story, confirmed_subject=SUBJECT)
checked = check_learning_script(normalized, answered, request=learning, subject=SUBJECT)
for scene in normalized["scenes"]:
    check_line_text(scene["narration"])
print("TITLE", normalized["title"])
for fact in checked["facts"]:
    print("FACT", fact["kind"], "|", fact["text"])
for scene, plan in zip(normalized["scenes"], checked["scenes"], strict=True):
    print(f"SCENE {scene['scene_index']} [{plan['fact_id']}] {scene['narration']}")
    print(f"   action: {plan['action_en']}")
    print(f"   setting: {plan['setting_en']}")
with open("/tmp/feat094-story.json", "w", encoding="utf-8") as handle:
    json.dump({"story": normalized, "learning": checked}, handle, ensure_ascii=False)
print("DONE")
