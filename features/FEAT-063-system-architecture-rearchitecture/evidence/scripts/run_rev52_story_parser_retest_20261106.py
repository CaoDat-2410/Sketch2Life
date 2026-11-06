from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
SCRIPT_DIR = SCRIPT.parent
OUTPUT = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "story_parser_srs_aligned_text_contract_retest_20261106"
)
IMAGE = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
WAIT_SECONDS = 600

for item in (
    str(REPO / "backend" / "src"),
    str(SCRIPT_DIR),
    str(REPO / "deployment" / "modal" / "srs_v23"),
):
    if item not in sys.path:
        sys.path.insert(0, item)

import modal  # noqa: E402
import run_ai_nonvideo_30min_queue_retest_20261104 as qwen  # noqa: E402
from sketch2life.contracts.schemas.ai_story import (  # noqa: E402
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.infrastructure.ai.modal_function_client import (  # noqa: E402
    MODEL_REVISION,
    STORY_MODEL_ID,
    summarize_worker_call_logs,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summarize_call(call_id: Any) -> dict[str, Any] | None:
    if not isinstance(call_id, str) or not call_id.startswith("fc-"):
        return None
    try:
        return summarize_worker_call_logs(
            modal.FunctionCall.from_id(call_id), max_log_wait_seconds=20
        )
    except Exception as exc:  # noqa: BLE001 - retain only safe exception class.
        return {
            "worker_logs_available": False,
            "worker_failure_boundary": "worker_log_fetch_exception",
            "error_type": type(exc).__name__,
        }


def main() -> int:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise SystemExit(
            "Story parser retest evidence exists; refusing another Modal call"
        )
    if not IMAGE.is_file():
        raise SystemExit("The synthetic drawing fixture is missing")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    qwen.OUT_DIR = OUTPUT
    qwen.IMAGE_PATH = IMAGE
    qwen.WAIT_SECONDS = WAIT_SECONDS
    started = datetime.now().astimezone().isoformat(timespec="seconds")
    started_perf = time.perf_counter()
    write_json(
        OUTPUT / "dispatch_guard.json",
        {
            "state": "DISPATCH_INTENT_RECORDED",
            "created_at": started,
            "workload": "story.generate",
            "alias": "storyboard.generate",
            "model_id": STORY_MODEL_ID,
            "model_revision": MODEL_REVISION,
            "synthetic_only": True,
            "max_attempts": 1,
            "video_called": False,
            "purpose": "Verify compact complete scene fields and butterfly lifecycle",
        },
    )
    record: dict[str, Any]
    try:
        record = qwen.invoke_story(
            confirmed_subject="bướm",
            visible_features=["hai đôi cánh rộng", "thân hình thon", "râu cong"],
        )
    except Exception as exc:  # noqa: BLE001 - do not persist raw provider text.
        record = {"workload": "story.generate", "outcome": "FAILED_RUNNER"}
        record["runner_error_type"] = type(exc).__name__

    call_id = record.get("call_id")
    worker_logs = summarize_call(call_id)
    summary: dict[str, Any] = {
        "started_at": started,
        "ended_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.perf_counter() - started_perf, 3),
        "workload": "story.generate",
        "aliases": ["storyboard.generate"],
        "model_id": STORY_MODEL_ID,
        "model_revision": MODEL_REVISION,
        "call_id": call_id,
        "runner_outcome": record.get("outcome"),
        "runner_error_type": record.get("error_type")
        or record.get("runner_error_type"),
        "worker_log_summary": worker_logs,
        "video_calls": 0,
        "synthetic_only": True,
    }
    if (worker_logs or {}).get("worker_terminal_event") == "worker_failed":
        summary["outcome"] = "FAILED_TERMINAL"
    elif record.get("outcome") == "SUCCEEDED":
        draft = StoryRevisionDraftV1.model_validate(record.get("result"))
        validate_butterfly_lifecycle_v1(draft, confirmed_subject="bướm")
        sections = draft.story
        story_sections_nonempty = all(value.strip() for value in sections.values())
        scene_action_nonempty = all(scene.action.strip() for scene in draft.scenes)
        scene_visual_prompt_nonempty = all(
            scene.visual_prompt.strip() for scene in draft.scenes
        )
        scene_narration_nonempty = all(
            scene.narration.strip() for scene in draft.scenes
        )
        summary["outcome"] = (
            "SUCCEEDED"
            if all(
                (
                    story_sections_nonempty,
                    scene_action_nonempty,
                    scene_visual_prompt_nonempty,
                    scene_narration_nonempty,
                )
            )
            else "OUTPUT_TEXT_FIELDS_INVALID"
        )
        canonical = json.dumps(
            draft.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        summary.update(
            {
                "schema_valid": True,
                "butterfly_lifecycle_valid": True,
                "story_sections_nonempty": story_sections_nonempty,
                "scene_action_nonempty": scene_action_nonempty,
                "scene_visual_prompt_nonempty": scene_visual_prompt_nonempty,
                "scene_narration_nonempty": scene_narration_nonempty,
                "scene_count": len(draft.scenes),
                "duration_ms": draft.duration_ms,
                "result_sha256": hashlib.sha256(canonical).hexdigest(),
                "result_artifact": "story_generate_result.json",
            }
        )
    else:
        summary["outcome"] = record.get("outcome", "UNKNOWN")

    record["worker_log_summary"] = worker_logs
    write_json(OUTPUT / "story_generate_result.json", record)
    write_json(OUTPUT / "summary.json", summary)
    guard = {
        "state": "COMPLETED"
        if summary["outcome"] == "SUCCEEDED"
        else "COMPLETED_WITH_FAILURES",
        "ended_at": summary["ended_at"],
        "workload": "story.generate",
        "call_id": call_id,
        "video_called": False,
    }
    write_json(OUTPUT / "dispatch_guard.json", guard)
    print(
        json.dumps(
            {
                "outcome": summary["outcome"],
                "call_id": call_id,
                "worker_stage": (worker_logs or {}).get("worker_last_stage"),
                "worker_error_code": (worker_logs or {}).get("worker_error_code"),
                "scene_count": summary.get("scene_count"),
                "video_called": False,
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    return 0 if summary["outcome"] == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
