from __future__ import annotations

import importlib.util
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
OUTPUT_DIR = FEATURE / "evidence" / "assets" / "ai_api_qwen35_modal_validation_20261105"
IMAGE_PATH = (
    FEATURE
    / "evidence"
    / "assets"
    / "parent_generated_image_activity_retest_20261103"
    / "synthetic_childlike_butterfly.png"
)
SCRIPT_DIR = SCRIPT.parent
BACKEND_SRC = REPO / "backend" / "src"
for item in (str(BACKEND_SRC), str(SCRIPT_DIR)):
    if item not in sys.path:
        sys.path.insert(0, item)

import run_ai_nonvideo_30min_queue_retest_20261104 as qwen
import run_speech_nonvideo_retest_20261104 as speech
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1

MAX_QWEN_WAIT_SECONDS = 1_800


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_retest_helper() -> Any:
    path = SCRIPT_DIR / "run_ai_nonvideo_full_retest_20261104.py"
    spec = importlib.util.spec_from_file_location("rev44_qwen35_flow_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the approved synthetic request helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _record_json(name: str, payload: object) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _lesson_suggestion_request() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": "bướm",
        "target_age_band_ref": "age-band-3-6",
        "target_age_band_version": 1,
        "target_age_months": 60,
        "objectives": ["Quan sát hình dạng và vòng đời của bướm"],
        "drawing_subject": "bướm",
        "activity_count": 1,
        "activity_kind": "outdoor",
        "script_following_allowed": False,
        "script_direction": None,
    }


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit(
            "Existing Rev44 evidence found; refusing duplicate worker dispatch."
        )
    if not IMAGE_PATH.is_file():
        raise SystemExit("The pre-generated synthetic drawing fixture is missing.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    flow = _load_retest_helper()
    qwen.OUT_DIR = OUTPUT_DIR
    qwen.IMAGE_PATH = IMAGE_PATH
    qwen.WAIT_SECONDS = MAX_QWEN_WAIT_SECONDS
    speech.OUTPUT_DIR = OUTPUT_DIR

    metadata = {
        "plan": "PLAN_REV44_AI_API_COVERAGE_QWEN35_MODAL_20261105.md",
        "started_at": _now(),
        "synthetic_only": True,
        "qwen_model": {
            "id": "Qwen/Qwen3.5-9B",
            "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        },
        "max_attempts_per_workload": 1,
        "qwen_wait_limit_seconds": MAX_QWEN_WAIT_SECONDS,
        "video_called": False,
        "blocked_without_dispatch": {
            "parent.sketch-guide.generate": "FLUX.3 checkpoint returned HTTP 401; no Modal HF Secret exists",
            "lesson.visual.generate": "FLUX.3 checkpoint returned HTTP 401; no Modal HF Secret exists",
            "drawing.segment": "prior 1,800-second GPU_L4 scheduling timeout; no retry",
            "video.scene.generate": "deferred by owner",
            "video.scene.validate": "deferred with video pipeline",
            "video.final-safety.validate": "no policy/model selected; fail closed",
        },
    }
    _record_json("run_metadata.json", metadata)
    results: list[dict[str, Any]] = []

    def save_result(label: str, result: dict[str, Any]) -> None:
        results.append({"label": label, **result})
        _record_json(
            "summary.json", {**metadata, "updated_at": _now(), "results": results}
        )
        print(
            json.dumps(
                {
                    "label": label,
                    "outcome": result.get("outcome", result.get("status", "UNKNOWN")),
                    "call_id": result.get("call_id"),
                    "elapsed_ms": result.get("elapsed_ms"),
                },
                ensure_ascii=True,
            ),
            flush=True,
        )

    started = time.perf_counter()
    save_result("drawing.analyze", qwen.invoke_drawing())

    started = time.perf_counter()
    story = qwen.invoke_story()
    story["client_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    save_result("story.generate+storyboard.generate", story)

    plan = flow.synthetic_approved_plan()
    started = time.perf_counter()
    deck = qwen.invoke_generic(
        workload="teacher.sketch-deck.generate",
        app="sketch2life-srs23-language-audio-dev",
        function="generate-teacher-sketch-deck",
        request_data=plan,
    )
    deck["client_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    save_result("teacher.sketch-deck.generate", deck)

    started = time.perf_counter()
    lesson = qwen.invoke_generic(
        workload="lesson.plan.suggest",
        app="sketch2life-srs23-language-audio-dev",
        function="suggest-lesson-plan",
        request_data=_lesson_suggestion_request(),
    )
    lesson["client_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    if lesson.get("outcome") == "SUCCEEDED":
        envelope = (lesson.get("result") or {}).get("result")
        if not isinstance(envelope, dict) or envelope.get("draft_only") is not True:
            lesson.update(
                {
                    "outcome": "CONTRACT_FAILED",
                    "contract_error": "suggestion result was not marked draft_only",
                }
            )
        else:
            parsed = LessonContentInputV1.model_validate(envelope.get("content"))
            lesson["validated_output"] = {
                "status": "DRAFT_ONLY",
                "activity_count": len(parsed.activities),
                "activity_kinds": [item.activity_kind for item in parsed.activities],
                "age_band_ref": parsed.target_age_band_ref,
                "locale": parsed.locale,
            }
    save_result("lesson.plan.suggest", lesson)

    speech_started = time.perf_counter()
    request = {"text": "Con bướm bay qua khu vườn đầy nắng.", "voice": "Hải Đăng"}
    tts = speech._invoke(
        workload="tts.narration.generate",
        function_name="synthesize-vietnamese-narration",
        asset_path="input/request.json",
        content_type="application/json",
        asset_bytes=flow.canonical_json(request),
        output_path=OUTPUT_DIR / "synthetic_vietnamese_narration.wav",
    )
    save_result("tts.narration.generate", tts)
    wav_path = OUTPUT_DIR / "synthetic_vietnamese_narration.wav"
    asr = speech._invoke(
        workload="asr.transcribe",
        function_name="transcribe-vietnamese-audio",
        asset_path="input/audio.wav",
        content_type="audio/wav",
        asset_bytes=wav_path.read_bytes(),
        output_path=None,
    )
    asr["roundtrip_elapsed_ms"] = round(
        (time.perf_counter() - speech_started) * 1000, 2
    )
    save_result("asr.transcribe", asr)

    final = {
        **metadata,
        "ended_at": _now(),
        "results": results,
        "speech_roundtrip": {
            "tts_status": tts.get("outcome"),
            "asr_status": asr.get("outcome"),
            "transcript": ((asr.get("result") or {}).get("result") or {}).get("text"),
        },
    }
    _record_json("summary.json", final)
    print(
        json.dumps(
            {"complete": True, "result_count": len(results), "video_called": False}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
