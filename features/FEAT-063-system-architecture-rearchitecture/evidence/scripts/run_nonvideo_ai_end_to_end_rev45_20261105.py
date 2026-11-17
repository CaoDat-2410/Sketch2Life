from __future__ import annotations

import json
import re
import sys
import time
import wave
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
SCRIPT_DIR = SCRIPT.parent
OUTPUT_DIR = FEATURE / "evidence" / "assets" / "ai_nonvideo_ai_end_to_end_20261105"
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
import run_speech_nonvideo_retest_20261104 as speech
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1

MAX_CALL_WAIT_SECONDS = 600
EXPECTED_TRANSCRIPT = "Con bướm bay qua khu vườn đầy nắng."


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _save_json(name: str, payload: object) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _normalize_words(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ỹ]+", text.casefold())


def _word_error_rate(reference: str, hypothesis: str) -> float:
    expected = _normalize_words(reference)
    actual = _normalize_words(hypothesis)
    previous = list(range(len(actual) + 1))
    for row, expected_word in enumerate(expected, start=1):
        current = [row]
        for column, actual_word in enumerate(actual, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (expected_word != actual_word),
                )
            )
        previous = current
    return previous[-1] / max(1, len(expected))


def _run(label: str, function: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = function()
    except Exception as exc:  # noqa: BLE001 - only the safe exception type is recorded.
        result = {"outcome": "FAILED_RUNNER", "error_type": type(exc).__name__}
    result["runner_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    result["label"] = label
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


def _lesson_request() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": "bướm",
        "target_age_band_ref": "age-band-3-6",
        "target_age_band_version": 1,
        "target_age_months": 60,
        "objectives": ["Quan sát hình dáng và vòng đời của bướm"],
        "drawing_subject": "bướm",
        "activity_count": 1,
        "activity_kind": "outdoor",
        "script_following_allowed": False,
        "script_direction": None,
    }


def main() -> int:
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise SystemExit("Rev45 evidence exists; refusing a duplicate inference dispatch.")
    if not IMAGE_PATH.is_file():
        raise SystemExit("The synthetic drawing fixture is missing.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    qwen.OUT_DIR = OUTPUT_DIR
    qwen.IMAGE_PATH = IMAGE_PATH
    qwen.WAIT_SECONDS = MAX_CALL_WAIT_SECONDS
    speech.OUTPUT_DIR = OUTPUT_DIR

    metadata = {
        "plan": "PLAN_REV45_NONVIDEO_AI_END_TO_END_20261105.md",
        "started_at": _now(),
        "synthetic_only": True,
        "image_fixture": IMAGE_PATH.name,
        "qwen_model": {
            "id": "Qwen/Qwen3.5-9B",
            "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        },
        "max_wait_seconds_per_call": MAX_CALL_WAIT_SECONDS,
        "video_called": False,
        "image_generation_called": False,
        "sam2_called": False,
    }
    _save_json("run_metadata.json", metadata)
    results: list[dict[str, Any]] = []

    drawing = _run("drawing.analyze", qwen.invoke_drawing)
    results.append(drawing)

    story = _run("story.generate_storyboard", qwen.invoke_story)
    results.append(story)

    plan_module = qwen.flow
    approved_plan = plan_module.synthetic_approved_plan()
    deck = _run(
        "teacher.sketch_deck.generate",
        lambda: qwen.invoke_generic(
            workload="teacher.sketch-deck.generate",
            app="sketch2life-srs23-language-audio-dev",
            function="generate-teacher-sketch-deck",
            request_data=approved_plan,
        ),
    )
    results.append(deck)

    lesson = _run(
        "lesson.plan.suggest",
        lambda: qwen.invoke_generic(
            workload="lesson.plan.suggest",
            app="sketch2life-srs23-language-audio-dev",
            function="suggest-lesson-plan",
            request_data=_lesson_request(),
        ),
    )
    if lesson.get("outcome") == "SUCCEEDED":
        envelope = (lesson.get("result") or {}).get("result")
        if not isinstance(envelope, dict) or envelope.get("draft_only") is not True:
            lesson.update(
                {"outcome": "CONTRACT_FAILED", "contract_error": "DRAFT_ONLY_REQUIRED"}
            )
        else:
            validated = LessonContentInputV1.model_validate(envelope.get("content"))
            lesson["validated_draft"] = {
                "status": "DRAFT_ONLY",
                "activity_count": len(validated.activities),
                "activity_kinds": [item.activity_kind for item in validated.activities],
                "age_band_ref": validated.target_age_band_ref,
                "locale": validated.locale,
            }
    results.append(lesson)

    request = {"text": EXPECTED_TRANSCRIPT, "voice": "Hải Đăng"}
    wav_path = OUTPUT_DIR / "synthetic_vietnamese_narration.wav"
    tts = _run(
        "tts.narration.generate",
        lambda: speech._invoke(
            workload="tts.narration.generate",
            function_name="synthesize-vietnamese-narration",
            asset_path="input/request.json",
            content_type="application/json",
            asset_bytes=plan_module.canonical_json(request),
            output_path=wav_path,
        ),
    )
    results.append(tts)

    if tts.get("outcome") == "SUCCEEDED" and wav_path.is_file():
        with wave.open(str(wav_path), "rb") as audio:
            audio_facts = {
                "channels": audio.getnchannels(),
                "sample_rate_hz": audio.getframerate(),
                "duration_seconds": round(audio.getnframes() / audio.getframerate(), 3),
                "size_bytes": wav_path.stat().st_size,
            }
        asr = _run(
            "asr.transcribe",
            lambda: speech._invoke(
                workload="asr.transcribe",
                function_name="transcribe-vietnamese-audio",
                asset_path="input/audio.wav",
                content_type="audio/wav",
                asset_bytes=wav_path.read_bytes(),
                output_path=None,
            ),
        )
        result = (asr.get("result") or {}).get("result") or {}
        transcript = result.get("text", "")
        asr["quality_check"] = {
            "reference": EXPECTED_TRANSCRIPT,
            "transcript": transcript,
            "word_error_rate": round(_word_error_rate(EXPECTED_TRANSCRIPT, transcript), 4),
            "exact_match": _normalize_words(EXPECTED_TRANSCRIPT)
            == _normalize_words(transcript),
            "adult_confirmation_required": True,
        }
        results.append(asr)
    else:
        audio_facts = None
        results.append({"label": "asr.transcribe", "outcome": "NOT_RUN_TTS_FAILED"})

    final = {
        **metadata,
        "ended_at": _now(),
        "results": results,
        "speech_audio": audio_facts,
        "summary": {
            item.get("label", "unknown"): item.get(
                "outcome", item.get("status", "UNKNOWN")
            )
            for item in results
        },
    }
    _save_json("summary.json", final)
    print(
        json.dumps(
            {
                "complete": True,
                "workload_count": len(results),
                "video_called": False,
                "summary": final["summary"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
