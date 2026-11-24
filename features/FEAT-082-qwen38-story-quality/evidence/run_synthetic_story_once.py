from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from sketch2life.contracts.schemas.ai_story import StoryRevisionDraftV1
from sketch2life.infrastructure.ai.modal_function_client import ModalStoryFunctionClient


EVIDENCE_DIR = Path(__file__).resolve().parent
RESULT_PATH = EVIDENCE_DIR / "SYNTHETIC_STORY_RESULT_20261122.json"
GUARD_PATH = EVIDENCE_DIR / "SYNTHETIC_STORY_REQUEST_USED_20261122.txt"

with GUARD_PATH.open("x", encoding="utf-8") as guard:
    guard.write(datetime.now(UTC).isoformat())

synthetic_label = b"FEAT-082 synthetic metadata-only story request"
worker_input = {
    "schema_version": "sketch2life.story-generation-input.v2",
    "role": "PARENT",
    "language": "vi",
    "confirmed_subject": "rùa",
    "understanding_revision": 1,
    "drawing_sha256": hashlib.sha256(synthetic_label).hexdigest(),
    "visible_features": [
        "mai xanh có các mảng hình lục giác",
        "đầu nhỏ hướng sang phải",
        "bốn chân ngắn",
        "chiếc lá vàng nằm bên phải",
    ],
    "child_age_months": 60,
    "context_revision": 1,
    "adult_confirmed_idea": "Rùa muốn đến gần chiếc lá vàng để khám phá.",
    "rewrite_instruction": None,
    "lesson_direction": None,
    "topic": "Động vật",
    "lesson_subject_learning_notes": "Mai rùa là lớp vỏ cứng giúp bảo vệ cơ thể.",
}

started_at = datetime.now(UTC)
started_clock = perf_counter()
report: dict[str, object] = {
    "schema_version": "sketch2life.feat082.synthetic-story-evidence.v1",
    "status": "RUNNING",
    "started_at_utc": started_at.isoformat(),
    "input_mode": "synthetic metadata only; no drawing bytes, child account, or profile",
    "model_id": "Qwen/Qwen3.8-27B-FP8",
    "model_revision": "c3a462cc3d38cf351f3b26cbd763469eeb74ef81",
    "worker_input": worker_input,
}
RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

try:
    raw_story, modal_call_id = ModalStoryFunctionClient(timeout_seconds=1_800).generate(
        {"worker_input": worker_input}
    )
    story = StoryRevisionDraftV1.model_validate(raw_story)
    report.update(
        {
            "status": "SUCCEEDED",
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(perf_counter() - started_clock, 3),
            "modal_call_id": modal_call_id,
            "backend_schema_validation": "PASS",
            "story": story.model_dump(mode="json"),
        }
    )
except Exception as exc:
    report.update(
        {
            "status": "FAILED",
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(perf_counter() - started_clock, 3),
            "error_type": type(exc).__name__,
            "error_code": getattr(exc, "code", None),
            "modal_call_id": getattr(exc, "call_id", None),
        }
    )
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    raise

RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
