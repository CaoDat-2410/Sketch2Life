from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
BACKEND_SRC = REPO / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import modal
import run_ai_nonvideo_full_retest_20261104 as flow

from sketch2life.contracts.schemas.ai_story import (
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    APP_NAME as DRAWING_APP,
    DRAWING_INPUT_SCHEMA,
    ENVIRONMENT_NAME,
    MODEL_ID as DRAWING_MODEL_ID,
    MODEL_REVISION as DRAWING_MODEL_REVISION,
    SCRATCH_VOLUME_NAME,
    STORY_INPUT_SCHEMA,
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    WORKER_INPUT_SCHEMA,
    WORKER_OUTPUT_SCHEMA,
    prepare_drawing_input,
)

OUT_DIR = FEATURE / "evidence" / "assets" / "ai_nonvideo_30min_queue_retest_20261104"
IMAGE_PATH = FEATURE / "evidence" / "assets" / "parent_generated_image_activity_retest_20261103" / "synthetic_childlike_butterfly.png"
WAIT_SECONDS = 1_800
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
MODAL_ENV = "dev"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def identity() -> tuple[str, str, str]:
    return tuple(str(uuid.uuid4()) for _ in range(3))  # type: ignore[return-value]


def cancel_and_check(call: Any) -> tuple[bool, str]:
    try:
        call.cancel(terminate_containers=True)
    except Exception as exc:
        return False, f"cancel_{type(exc).__name__}"
    try:
        call.get(timeout=1)
        return True, "result_arrived_during_cancel"
    except TimeoutError:
        return False, "still_pending_after_cancel"
    except Exception as exc:
        return True, f"terminal_{type(exc).__name__}"


def invoke_drawing() -> dict[str, Any]:
    source = IMAGE_PATH.read_bytes()
    source_sha = digest(source)
    job_id, generation_id, attempt_id = identity()
    prepared = prepare_drawing_input(
        source_bytes=source,
        source_media_type="image/png",
        expected_source_sha256=source_sha,
        job_id=job_id,
        generation_id=generation_id,
        attempt_id=attempt_id,
    )
    record: dict[str, Any] = {
        "workload": "drawing.analyze",
        "app": DRAWING_APP,
        "function": "analyze-drawing",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "source_sha256": source_sha,
        "drawing_sha256": prepared.drawing_sha256,
        "wait_limit_seconds": WAIT_SECONDS,
        "started_at": now(),
        "outcome": "DISPATCH_FAILED_NO_CALL",
    }
    save_json(OUT_DIR / "drawing_analyze_dispatch_intent.json", {**record, "state": "DISPATCH_INTENT_RECORDED", "attempt_prefix": prepared.attempt_prefix, "max_attempts": 1})
    call = None
    terminal = False
    try:
        volume = modal.Volume.from_name(SCRATCH_VOLUME_NAME, environment_name=ENVIRONMENT_NAME, version=2)
        function = modal.Function.from_name(DRAWING_APP, "analyze-drawing", environment_name=ENVIRONMENT_NAME)
        with volume.batch_upload() as batch:
            batch.put_file(BytesIO(prepared.drawing_png), f"/{prepared.attempt_prefix}input/drawing.png")
            batch.put_file(BytesIO(prepared.manifest), f"/{prepared.attempt_prefix}input/manifest.json")
        call = function.spawn(prepared.payload)
        record["call_id"] = getattr(call, "object_id", None)
        if not isinstance(record["call_id"], str) or not record["call_id"].startswith("fc-"):
            record["outcome"] = "UNKNOWN_NO_CALL_ID"
            return record
        record["dispatch_at"] = now()
        output = call.get(timeout=WAIT_SECONDS)
        terminal = True
        expected = {
            "schema_version": WORKER_OUTPUT_SCHEMA,
            "workload": "drawing.analyze",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "input_sha256": prepared.drawing_sha256,
            "model": {"id": DRAWING_MODEL_ID, "revision": DRAWING_MODEL_REVISION},
        }
        if not isinstance(output, dict) or any(output.get(key) != value for key, value in expected.items()):
            raise ValueError("drawing output envelope or source lineage did not match")
        candidate = output.get("result")
        if (
            not isinstance(candidate, dict)
            or candidate.get("decision") != "NEEDS_ADULT_CONFIRMATION"
            or candidate.get("adult_confirmation_required") is not True
            or not isinstance(candidate.get("candidate_subject"), str)
            or not isinstance(candidate.get("visible_features"), list)
        ):
            raise ValueError("drawing output did not satisfy the adult-confirmation contract")
        record.update({
            "outcome": "SUCCEEDED",
            "model": output.get("model"),
            "candidate_subject": candidate["candidate_subject"],
            "visible_features": candidate["visible_features"],
            "adult_confirmation_required": True,
            "output_sha256": digest(flow.canonical_json(output)),
        })
    except TimeoutError:
        record["outcome"] = "UNKNOWN_NO_RETRY"
        record["cancel"] = cancel_and_check(call) if call is not None else (False, "no_call")
        terminal = bool(record["cancel"][0])
    except Exception as exc:
        terminal = call is not None
        record.update({"outcome": "FAILED_TERMINAL" if terminal else "DISPATCH_FAILED_NO_CALL", "error_type": type(exc).__name__})
    finally:
        record["ended_at"] = now()
        if terminal:
            volume.remove_file(f"{prepared.attempt_prefix}input", recursive=True)
        save_json(OUT_DIR / "drawing_analyze_result.json", record)
        print(json.dumps({"workload": record["workload"], "outcome": record["outcome"], "call_id": record.get("call_id"), "wait_limit_seconds": WAIT_SECONDS}, ensure_ascii=True), flush=True)
    return record


def invoke_story(
    *,
    confirmed_subject: str = "butterfly",
    visible_features: list[str] | None = None,
) -> dict[str, Any]:
    image_sha = digest(IMAGE_PATH.read_bytes())
    job_id, generation_id, attempt_id = identity()
    prefix = f"sketch2life/{ENVIRONMENT_NAME}/{job_id}/{generation_id}/{attempt_id}/"
    features = visible_features or ["two pairs of broad wings", "slender body", "curved antennae"]
    worker_input = {
        "schema_version": "sketch2life.story-generation-input.v1",
        "role": "PARENT",
        "language": "vi",
        "confirmed_subject": confirmed_subject,
        "understanding_revision": 1,
        "drawing_sha256": image_sha,
        "visible_features": features,
        "child_age_months": 60,
        "context_revision": 1,
        "adult_confirmed_idea": "Kể vòng đời thật của bướm từ trứng, sâu bướm, nhộng đến bướm trưởng thành; không gán việc nở trứng cho bướm trưởng thành.",
        "rewrite_instruction": None,
        "lesson_direction": None,
    }
    request_bytes = flow.canonical_json(worker_input)
    manifest = {
        "schema_version": STORY_INPUT_SCHEMA,
        "asset": {
            "path": "input/request.json",
            "content_type": "application/json",
            "size_bytes": len(request_bytes),
            "sha256": digest(request_bytes),
        },
    }
    manifest_bytes = flow.canonical_json(manifest)
    payload = {
        "schema_version": WORKER_INPUT_SCHEMA,
        "environment": ENVIRONMENT_NAME,
        "workload": "story.generate",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": digest(manifest_bytes),
        "input_bytes": len(manifest_bytes) + len(request_bytes),
    }
    dispatch = {
        "state": "DISPATCH_INTENT_RECORDED",
        "workload": "story.generate",
        "app": "sketch2life-srs23-language-audio-dev",
        "function": "generate-story-and-storyboard",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "input_sha256": digest(request_bytes),
        "manifest_sha256": digest(manifest_bytes),
        "wait_limit_seconds": WAIT_SECONDS,
        "synthetic_adult_confirmed_fixture": True,
        "created_at": now(),
        "max_attempts": 1,
    }
    save_json(OUT_DIR / "story_generate_dispatch_intent.json", dispatch)
    record: dict[str, Any] = {**dispatch, "outcome": "DISPATCH_FAILED_NO_CALL"}
    call = None
    terminal = False
    try:
        volume = modal.Volume.from_name(SCRATCH_VOLUME_NAME, environment_name=ENVIRONMENT_NAME, version=2)
        function = modal.Function.from_name("sketch2life-srs23-language-audio-dev", "generate-story-and-storyboard", environment_name=ENVIRONMENT_NAME)
        with volume.batch_upload() as batch:
            batch.put_file(BytesIO(request_bytes), f"/{prefix}input/request.json")
            batch.put_file(BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
        call = function.spawn(payload)
        call_id = getattr(call, "object_id", None)
        record["call_id"] = call_id
        if not isinstance(call_id, str) or not call_id.startswith("fc-"):
            record["outcome"] = "UNKNOWN_NO_CALL_ID"
            return record
        record["dispatch_at"] = now()
        output = call.get(timeout=WAIT_SECONDS)
        terminal = True
        if not isinstance(output, dict) or any(output.get(key) != value for key, value in {
            "schema_version": WORKER_OUTPUT_SCHEMA,
            "workload": "story.generate",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "model": {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION},
        }.items()):
            raise ValueError("story worker output envelope or model pin did not match")
        draft = StoryRevisionDraftV1.model_validate(output.get("result"))
        validate_butterfly_lifecycle_v1(
            draft, confirmed_subject=confirmed_subject
        )
        record.update({
            "outcome": "SUCCEEDED",
            "title": draft.title,
            "scene_count": len(draft.scenes),
            "duration_ms": draft.duration_ms,
            "story_sha256": digest(flow.canonical_json(draft.model_dump(mode="json"))),
            "result": draft.model_dump(mode="json"),
        })
    except TimeoutError:
        record["outcome"] = "UNKNOWN_NO_RETRY"
        record["cancel"] = cancel_and_check(call) if call is not None else (False, "no_call")
        terminal = bool(record["cancel"][0])
    except Exception as exc:
        terminal = call is not None
        record.update({"outcome": "FAILED_TERMINAL" if terminal else "DISPATCH_FAILED_NO_CALL", "error_type": type(exc).__name__})
    finally:
        record["ended_at"] = now()
        if terminal:
            volume.remove_file(f"{prefix}input", recursive=True)
        save_json(OUT_DIR / "story_generate_result.json", record)
        print(json.dumps({"workload": "story.generate/storyboard.generate", "outcome": record["outcome"], "call_id": record.get("call_id"), "wait_limit_seconds": WAIT_SECONDS}, ensure_ascii=True), flush=True)
    return record


def invoke_generic(
    *, workload: str, app: str, function: str, request_data: dict[str, Any], output_name: str | None = None
) -> dict[str, Any]:
    identity_data, payload, request_bytes, manifest_bytes = flow.modal_payload(workload, request_data)
    prefix = identity_data["prefix"]
    record: dict[str, Any] = {
        "workload": workload,
        "app": app,
        "function": function,
        "job_id": identity_data["job_id"],
        "generation_id": identity_data["generation_id"],
        "attempt_id": identity_data["attempt_id"],
        "input_sha256": digest(request_bytes),
        "manifest_sha256": digest(manifest_bytes),
        "wait_limit_seconds": WAIT_SECONDS,
        "started_at": now(),
        "outcome": "DISPATCH_FAILED_NO_CALL",
    }
    dispatch_path = OUT_DIR / f"{workload.replace('.', '_')}_dispatch_intent.json"
    save_json(dispatch_path, {**record, "state": "DISPATCH_INTENT_RECORDED", "max_attempts": 1})
    call = None
    terminal = False
    try:
        volume = modal.Volume.from_name(SCRATCH_VOLUME, environment_name=MODAL_ENV, version=2)
        with volume.batch_upload() as batch:
            batch.put_file(BytesIO(request_bytes), f"/{prefix}input/request.json")
            batch.put_file(BytesIO(manifest_bytes), f"/{prefix}input/manifest.json")
        remote = modal.Function.from_name(app, function, environment_name=MODAL_ENV)
        call = remote.spawn(payload)
        call_id = getattr(call, "object_id", None)
        record["call_id"] = call_id
        if not isinstance(call_id, str) or not call_id.startswith("fc-"):
            record["outcome"] = "UNKNOWN_NO_CALL_ID"
            return record
        record["dispatch_at"] = now()
        result = call.get(timeout=WAIT_SECONDS)
        terminal = True
        if not isinstance(result, dict) or any(result.get(key) != value for key, value in {
            "schema_version": WORKER_OUTPUT_SCHEMA,
            "workload": workload,
            "job_id": identity_data["job_id"],
            "generation_id": identity_data["generation_id"],
            "attempt_id": identity_data["attempt_id"],
        }.items()):
            raise ValueError("worker output envelope or lineage did not match")
        safe = dict(result)
        asset = safe.get("asset")
        if isinstance(asset, dict):
            asset = dict(asset)
            asset_bytes = asset.pop("bytes", None)
            safe["asset"] = asset
            if asset_bytes is not None:
                if not isinstance(asset_bytes, bytes) or digest(asset_bytes) != asset.get("sha256") or len(asset_bytes) != asset.get("size_bytes"):
                    raise ValueError("derived image asset failed its size/hash check")
                if output_name is not None:
                    (OUT_DIR / output_name).write_bytes(asset_bytes)
                    record["asset_file"] = output_name
        if workload == "parent.sketch-guide.generate":
            a = safe.get("asset") or {}
            if (a.get("width"), a.get("height")) != (768, 512):
                raise ValueError("line-sketch guide dimensions did not match the contract")
        elif workload == "teacher.sketch-deck.generate":
            deck = safe.get("result") or {}
            expected_refs = [item["activity_ref"] for item in request_data["activities"]]
            slides = deck.get("slides", [])
            guides = [slide for slide in slides if slide.get("kind") == "drawing_guide"] if isinstance(slides, list) else []
            guide_steps = guides[0].get("steps", []) if len(guides) == 1 else []
            if (
                deck.get("status") != "DRAFT"
                or deck.get("aspect_ratio") != "16:9"
                or len(slides) != 5
                or deck.get("approved_activity_refs") != expected_refs
                or not 3 <= len(guide_steps) <= 5
            ):
                raise ValueError("Teacher Deck draft contract did not match")
            record["slide_count"] = len(slides)
            record["drawing_step_count"] = len(guide_steps)
            record["approved_activity_refs"] = deck.get("approved_activity_refs")
        elif workload == "lesson.visual.generate":
            if safe.get("status") != "DRAFT" or safe.get("review_required") is not True:
                raise ValueError("lesson visual was not returned as a private DRAFT")
            a = safe.get("asset") or {}
            if (a.get("width"), a.get("height")) != (768, 432):
                raise ValueError("lesson visual dimensions did not match the contract")
        record.update({"outcome": "SUCCEEDED", "result": safe, "output_sha256": digest(flow.canonical_json(safe))})
    except TimeoutError:
        record["outcome"] = "UNKNOWN_NO_RETRY"
        record["cancel"] = cancel_and_check(call) if call is not None else (False, "no_call")
        terminal = bool(record["cancel"][0])
    except Exception as exc:
        terminal = call is not None
        record.update({"outcome": "FAILED_TERMINAL" if terminal else "DISPATCH_FAILED_NO_CALL", "error_type": type(exc).__name__})
    finally:
        record["ended_at"] = now()
        if terminal:
            volume.remove_file(f"{prefix}input", recursive=True)
        save_json(OUT_DIR / f"{workload.replace('.', '_')}_result.json", record)
        print(json.dumps({"workload": workload, "outcome": record["outcome"], "call_id": record.get("call_id"), "wait_limit_seconds": WAIT_SECONDS}, ensure_ascii=True), flush=True)
    return record


def main() -> int:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing retest evidence: {OUT_DIR.name}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trace: dict[str, Any] = {
        "started_at": now(),
        "plan": "AI_NONVIDEO_30MIN_QUEUE_RETEST_20261104.md",
        "wait_limit_seconds": WAIT_SECONDS,
        "synthetic_only": True,
        "video_called": False,
        "workloads": [],
    }
    save_json(OUT_DIR / "dispatch_guard.json", {
        "state": "RUN_STARTED",
        "started_at": trace["started_at"],
        "max_attempts_per_workload": 1,
        "wait_limit_seconds": WAIT_SECONDS,
        "video_enabled": False,
    })
    save_json(OUT_DIR / "run_metadata.json", trace)

    results: list[dict[str, Any]] = []
    def safe_run(workload: str, operation: Any) -> dict[str, Any]:
        try:
            return operation()
        except Exception as exc:
            record = {"workload": workload, "outcome": "DISPATCH_FAILED_NO_CALL", "error_type": type(exc).__name__, "ended_at": now()}
            save_json(OUT_DIR / f"{workload.replace('.', '_')}_result.json", record)
            print(json.dumps({"workload": workload, "outcome": record["outcome"], "error_type": record["error_type"]}, ensure_ascii=True), flush=True)
            return record

    drawing = safe_run("drawing.analyze", invoke_drawing)
    results.append(drawing)
    story = safe_run("story.generate", invoke_story)
    results.append(story)

    results.append(safe_run("parent.sketch-guide.generate", lambda: invoke_generic(
        workload="parent.sketch-guide.generate",
        app="sketch2life-srs23-flux-image-dev",
        function="generate-line-sketch-guide-candidate",
        request_data={"topic": "butterfly", "difficulty": "beginner", "step_count": 3},
        output_name="parent_sketch_guide.png",
    )))

    plan = flow.synthetic_approved_plan()
    results.append(safe_run("teacher.sketch-deck.generate", lambda: invoke_generic(
        workload="teacher.sketch-deck.generate",
        app="sketch2life-srs23-language-audio-dev",
        function="generate-teacher-sketch-deck",
        request_data=plan,
    )))

    visual_request = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": plan["plan_revision_ref"],
        "content_hash": plan["content_hash"],
        "topic": plan["topic"],
        "steps": [
            {"step_index": step["step_index"], "instruction": step["action"], "placement": step["placement"]}
            for step in plan["drawing_steps"]
        ],
    }
    results.append(safe_run("lesson.visual.generate", lambda: invoke_generic(
        workload="lesson.visual.generate",
        app="sketch2life-srs23-flux-image-dev",
        function="generate-approved-lesson-visual-candidate",
        request_data=visual_request,
        output_name="lesson_visual.png",
    )))

    sam2_spec = __import__("importlib.util", fromlist=["spec_from_file_location"])
    sam2_path = FEATURE / "evidence" / "scripts" / "run_sam2_nonvideo_retest_20261104.py"
    spec = sam2_spec.spec_from_file_location("sam2_retry_module", sam2_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the existing SAM2 feasibility runner")
    sam2 = sam2_spec.module_from_spec(spec)
    sys.modules[spec.name] = sam2
    spec.loader.exec_module(sam2)
    sam2.OUTPUT_DIR = OUT_DIR
    sam2.MAX_WAIT_SECONDS = WAIT_SECONDS
    try:
        sam2_result = sam2.main()
        sam2_path = OUT_DIR / "sam2_segment_result.json"
        if sam2_path.is_file():
            results.append(json.loads(sam2_path.read_text(encoding="utf-8")))
        else:
            results.append({"workload": "drawing.segment", "outcome": "FAILED_BEFORE_SEGMENT", "sam2_runner_exit_code": sam2_result})
    except Exception as exc:
        sam2_result = 1
        results.append({"workload": "drawing.segment", "outcome": "DISPATCH_FAILED_NO_CALL", "error_type": type(exc).__name__})

    summary = {
        "started_at": trace["started_at"],
        "ended_at": now(),
        "wait_limit_seconds": WAIT_SECONDS,
        "video_called": False,
        "results": results,
        "outcome_counts": {
            outcome: sum(1 for item in results if item.get("outcome") == outcome)
            for outcome in sorted({item.get("outcome", "UNRECORDED") for item in results})
        },
        "sam2_runner_exit_code": sam2_result,
    }
    save_json(OUT_DIR / "summary.json", summary)
    print(json.dumps({"summary": "summary.json", "outcome_counts": summary["outcome_counts"], "video_called": False}, ensure_ascii=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
