from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import run_ai_nonvideo_full_retest_20261104 as flow  # noqa: E402
from sketch2life.contracts.schemas.ai_story import (  # noqa: E402
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)

OUTPUT_DIR = flow.ASSET_DIR
GUARD_PATH = OUTPUT_DIR / "parent_story_worker_dispatch_guard.json"
RESULT_PATH = OUTPUT_DIR / "parent_story_worker_result.json"


def main() -> int:
    if GUARD_PATH.exists() or RESULT_PATH.exists():
        raise SystemExit("Parent story worker already dispatched; refusing retry.")
    image_sha = hashlib.sha256(flow.IMAGE_PATH.read_bytes()).hexdigest()
    request = {
        "schema_version": "sketch2life.story-generation-input.v1",
        "role": "PARENT",
        "language": "vi",
        "confirmed_subject": "con bướm",
        "understanding_revision": 1,
        "drawing_sha256": image_sha,
        "visible_features": [
            "thân nhỏ ở giữa",
            "hai cặp cánh ở hai bên",
            "hai râu cong trên đầu",
        ],
        "child_age_months": 60,
        "context_revision": 1,
        "adult_confirmed_idea": "Kể hành trình của bướm từ trứng, sâu bướm, nhộng đến bướm trưởng thành; kết thúc khi bướm bay tới một bông hoa.",
        "rewrite_instruction": None,
        "lesson_direction": None,
    }
    flow.dump_json(
        GUARD_PATH,
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "workload": "story.generate",
            "created_at": flow.now_local(),
            "input_sha256": hashlib.sha256(flow.canonical_json(request)).hexdigest(),
            "source_drawing_sha256": image_sha,
            "adult_confirmed_subject_fixture": True,
            "adult_confirmation_gate_in_product_api": "not reached in Parent run because drawing VLM timed out",
            "max_attempts": 1,
        },
    )
    trace = json.loads(flow.TRACE_PATH.read_text(encoding="utf-8"))
    try:
        record = flow.invoke_modal_worker(
            trace,
            workload="story.generate",
            app_name=flow.LANGUAGE_APP,
            function_name="generate-story-and-storyboard",
            request_data=request,
            timeout=600,
        )
        output = record["result"]
        draft_data = output.get("result")
        if output.get("workload") != "story.generate" or not isinstance(draft_data, dict):
            raise RuntimeError("Story worker output envelope did not match the request.")
        draft = StoryRevisionDraftV1.model_validate(draft_data)
        validate_butterfly_lifecycle_v1(draft, confirmed_subject="con bướm")
        flow.dump_json(
            RESULT_PATH,
            {
                "outcome": "SUCCEEDED",
                "call_id": record["call_id"],
                "elapsed_ms": record["elapsed_ms"],
                "worker_model": output.get("model"),
                "draft_status": "DRAFT",
                "adult_confirmation_required": True,
                "api_revision_persisted": False,
                "video_called": False,
                "story": draft.model_dump(mode="json"),
            },
        )
        print(json.dumps({"outcome": "SUCCEEDED", "call_id": record["call_id"], "elapsed_ms": record["elapsed_ms"], "scenes": len(draft.scenes), "duration_ms": draft.duration_ms}, ensure_ascii=True))
        return 0
    except Exception as exc:
        flow.dump_json(
            RESULT_PATH,
            {"outcome": "FAILED_OR_UNKNOWN", "error_type": type(exc).__name__, "ended_at": flow.now_local(), "video_called": False},
        )
        print(json.dumps({"outcome": "FAILED_OR_UNKNOWN", "error_type": type(exc).__name__}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
