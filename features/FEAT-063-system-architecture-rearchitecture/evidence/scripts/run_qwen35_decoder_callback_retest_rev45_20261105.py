from __future__ import annotations

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
OUTPUT_DIR = (
    FEATURE
    / "evidence"
    / "assets"
    / "ai_nonvideo_ai_end_to_end_20261105"
    / "parser_state_replay_retest_11"
)
IMAGE_PATH = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
BACKEND_SRC = REPO / "backend" / "src"
for import_path in (str(BACKEND_SRC), str(SCRIPT_DIR)):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import run_ai_nonvideo_30min_queue_retest_20261104 as qwen

MAX_WAIT_SECONDS = 600


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _save_json(name: str, payload: object) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _run(label: str, operation: Any) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = operation()
    except Exception as exc:  # noqa: BLE001 - store type only; Modal logs hold safe diagnostics.
        result = {"label": label, "outcome": "FAILED_RUNNER", "error_type": type(exc).__name__}
    result["label"] = label
    result["runner_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    _save_json(f"{label.replace('.', '_')}_result.json", result)
    print(
        json.dumps(
            {
                "label": label,
                "outcome": result.get("outcome", result.get("status", "UNKNOWN")),
                "call_id": result.get("call_id"),
                "elapsed_ms": result.get("elapsed_ms", result["runner_elapsed_ms"]),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return result


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Retest evidence exists; refusing a duplicate dispatch.")
    if not IMAGE_PATH.is_file():
        raise SystemExit("Synthetic drawing fixture is missing.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    qwen.OUT_DIR = OUTPUT_DIR
    qwen.IMAGE_PATH = IMAGE_PATH
    qwen.WAIT_SECONDS = MAX_WAIT_SECONDS
    metadata = {
        "started_at": _now(),
        "synthetic_only": True,
        "image_fixture": IMAGE_PATH.name,
        "qwen_model": {
            "id": "Qwen/Qwen3.5-9B",
            "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        },
        "max_wait_seconds_per_call": MAX_WAIT_SECONDS,
        "video_called": False,
        "purpose": "Compare the incremental TokenEnforcer parser state with a fresh JsonSchemaParser replay over the exact generated token-decoder text.",
    }
    _save_json("run_metadata.json", metadata)

    story = _run(
        "story.generate_storyboard",
        lambda: qwen.invoke_story(
            confirmed_subject="bướm",
            visible_features=[
                "cánh màu hồng và tím",
                "thân màu vàng có vạch ngang",
                "mặt cười đơn giản",
                "anten cong ở đầu",
            ],
        ),
    )
    deck = _run(
        "teacher.sketch_deck.generate",
        lambda: qwen.invoke_generic(
            workload="teacher.sketch-deck.generate",
            app="sketch2life-srs23-language-audio-dev",
            function="generate-teacher-sketch-deck",
            request_data=qwen.flow.synthetic_approved_plan(),
        ),
    )
    final = {
        **metadata,
        "ended_at": _now(),
        "results": [story, deck],
        "summary": {
            story["label"]: story["outcome"],
            deck["label"]: deck["outcome"],
        },
    }
    _save_json("summary.json", final)
    print(json.dumps({"complete": True, "summary": final["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
