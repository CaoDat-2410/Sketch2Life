from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
ASSET_DIR = FEATURE / "evidence" / "assets" / "ai_flow_srs_alignment_20261104"
RUNNER_PATH = SCRIPT.with_name("run_ai_flow_srs_alignment_20261104.py")
CONTINUATION_GUARD = ASSET_DIR / "CONTINUATION_DISPATCH_GUARD.json"
STORY_DISPATCH_GUARD = ASSET_DIR / "parent_story_dispatch_intent.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("feat063_ai_flow_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the approved synthetic flow runner.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_resume_preconditions(runner, trace: dict[str, Any]) -> None:
    parent = trace.get("parent_flow") or {}
    if parent.get("state") != "FAILED" or parent.get("error_type") != "KeyError":
        raise RuntimeError("Trace is not the expected interrupted Parent run.")
    if parent.get("error") != "'ETag'":
        raise RuntimeError("The previous Parent stop was not the known header-key casing issue.")
    if not parent.get("run_ref") or not parent.get("flow_id"):
        raise RuntimeError("The interrupted Parent run identity is missing.")
    records = trace.get("api_records", [])
    completed_names = {record.get("name") for record in records}
    if "read_run_after_vlm" not in completed_names:
        raise RuntimeError("No completed drawing analysis is recorded for this run.")
    if completed_names.intersection(
        {"adult_confirms_drawing_subject", "generate_parent_story_once", "read_story_revision"}
    ):
        raise RuntimeError("A later Parent action already exists; refusing a duplicate continuation.")
    if any(
        record.get("workload") in {"story.generate", "teacher.sketch-deck.generate", "lesson.visual.generate"}
        for record in trace.get("modal_workers", [])
    ):
        raise RuntimeError("A continuation AI workload already has a provider record.")
    if CONTINUATION_GUARD.exists() or STORY_DISPATCH_GUARD.exists():
        raise RuntimeError("A continuation/story dispatch guard already exists; refusing a second attempt.")
    old_deck_intent = ASSET_DIR / "teacher_sketch-deck_generate_dispatch_intent.json"
    if not old_deck_intent.exists():
        raise RuntimeError("Expected first Teacher deck intent is missing.")


def request_story_and_exercise_apis(runner, trace: dict[str, Any]) -> None:
    parent = trace["parent_flow"]
    flow_id = parent["flow_id"]
    run_ref = parent["run_ref"]
    base_port = runner.get_free_port()
    base_url = f"http://127.0.0.1:{base_port}"
    session = requests.Session()
    harness = runner.start_api_server(
        port=base_port,
        run_id=run_ref,
        trace=trace,
    )
    try:
        runner.wait_for_api(base_url, harness)
        current, current_body = runner.api_call(
            trace,
            session,
            name="resume_read_run_after_vlm",
            method="GET",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}",
        )
        runner.require_status(current, current_body, {200}, "resume read run")
        if current_body.get("run_state") != "SUBJECT_REVIEW":
            raise RuntimeError(f"Expected SUBJECT_REVIEW, received {current_body.get('run_state')}.")
        subject = current_body.get("result") or {}
        label = str(subject.get("subject_label", ""))
        folded = "".join(
            ch
            for ch in runner.unicodedata.normalize("NFKD", label.casefold())
            if not runner.unicodedata.combining(ch)
        )
        if "buom" not in folded and "butterfly" not in folded:
            raise RuntimeError("Synthetic drawing result is not the expected butterfly subject.")
        current_etag = current.headers.get("ETag")
        if not current_etag:
            raise RuntimeError("StoryRun API omitted ETag on the subject-review response.")

        confirmed_subject, confirm_body = runner.api_call(
            trace,
            session,
            name="adult_confirms_drawing_subject",
            method="POST",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}/subject-confirmation",
            headers={
                "Idempotency-Key": f"{flow_id}:confirm-subject",
                "If-Match": current_etag,
            },
            json={
                "decision": "CONFIRM",
                "expected_understanding_revision": subject["understanding_revision"],
            },
        )
        runner.require_status(confirmed_subject, confirm_body, {202}, "adult subject confirmation")
        parent["adult_subject_decision"] = {"decision": "CONFIRM", "candidate": label}

        prepared, prepared_body = runner.api_call(
            trace,
            session,
            name="read_run_before_story",
            method="GET",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}",
        )
        runner.require_status(prepared, prepared_body, {200}, "read run before story")
        prepared_etag = prepared.headers.get("ETag")
        if not prepared_etag:
            raise RuntimeError("StoryRun API omitted ETag before story generation.")

        dispatch = {
            "state": "STORY_GENERATION_DISPATCH_INTENT_RECORDED",
            "flow_id": flow_id,
            "run_ref": run_ref,
            "idempotency_key_ref": f"{flow_id}:initial-story",
            "created_at": runner.now_local(),
            "max_attempts": 1,
            "video_enabled": False,
        }
        runner.dump_json(STORY_DISPATCH_GUARD, dispatch)
        started = time.perf_counter()
        story, story_body = runner.api_call(
            trace,
            session,
            name="generate_parent_story_once",
            method="POST",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}/story-revisions",
            headers={
                "Idempotency-Key": f"{flow_id}:initial-story",
                "If-Match": prepared_etag,
            },
            json={
                "expected_understanding_revision": subject["understanding_revision"],
                "adult_confirmed_idea": runner.PARENT_ADULT_IDEA,
            },
            timeout=(20, 1_250),
        )
        parent["story_generation_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        if story.status_code == 202:
            runner.dump_json(
                STORY_DISPATCH_GUARD,
                {**dispatch, "state": "STORY_OUTCOME_UNKNOWN_NO_RETRY", "response": story_body},
            )
            parent["state"] = "STORY_OUTCOME_UNKNOWN_NO_RETRY"
            parent["story_generation_error"] = story_body
            raise RuntimeError("Story call returned an asynchronous/unknown outcome; no retry allowed.")
        if story.status_code != 201:
            runner.dump_json(
                STORY_DISPATCH_GUARD,
                {**dispatch, "state": "STORY_FAILED_TERMINAL", "response": story_body},
            )
            parent["story_generation_error"] = story_body
            raise RuntimeError(f"Story generation returned HTTP {story.status_code}.")
        revision_ref = str(story_body["story_revision_ref"])
        runner.dump_json(
            STORY_DISPATCH_GUARD,
            {
                **dispatch,
                "state": "STORY_HTTP_RESULT_RECEIVED",
                "story_revision_ref": revision_ref,
                "story_sha256": story_body.get("story_sha256"),
                "http_status": story.status_code,
                "elapsed_ms": parent["story_generation_elapsed_ms"],
            },
        )
        parent["story_revision_ref"] = revision_ref

        fetched, fetched_body = runner.api_call(
            trace,
            session,
            name="read_story_revision",
            method="GET",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}",
        )
        runner.require_status(fetched, fetched_body, {200}, "read story revision")
        if fetched_body.get("status") != "DRAFT" or not fetched_body.get("story_sha256"):
            raise RuntimeError(f"Story revision is not a reviewable DRAFT: {fetched_body.get('status')}.")
        parent["story_revision_ref"] = revision_ref
        parent["story_scene_count"] = len(fetched_body.get("scenes", []))
        parent["story_duration_ms"] = fetched_body.get("duration_ms")
        parent["story_title"] = fetched_body.get("title")
        parent["final_story_revision"] = fetched_body

        story_etag = story.headers.get("ETag")
        if not story_etag:
            raise RuntimeError("Story generation response omitted its ETag.")
        confirmed_story, confirmed_story_body = runner.api_call(
            trace,
            session,
            name="adult_confirms_story_revision",
            method="POST",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}/story-revisions/{revision_ref}/confirmation",
            headers={
                "Idempotency-Key": f"{flow_id}:confirm-story",
                "If-Match": story_etag,
            },
            json={
                "expected_revision": fetched_body["revision_no"],
                "story_sha256": fetched_body["story_sha256"],
            },
        )
        runner.require_status(confirmed_story, confirmed_story_body, {200}, "adult confirms story")
        parent["story_confirmation"] = confirmed_story_body
        final, final_body = runner.api_call(
            trace,
            session,
            name="read_run_after_script_confirmation",
            method="GET",
            base_url=base_url,
            path=f"/v1/story-runs/{run_ref}",
        )
        runner.require_status(final, final_body, {200}, "read run after script confirmation")
        parent.update(
            {
                "state": "SUCCEEDED",
                "ended_at": runner.now_local(),
                "final_run": final_body,
                "video_calls": 0,
                "activities_selected": False,
            }
        )
        runner.dump_json(
            runner.RESULT_PATH,
            {"parent_flow": parent, "story_revision": fetched_body},
        )

        cancelled, cancel_body = runner.api_call(
            trace,
            session,
            name="create_run_for_cancel_test",
            method="POST",
            base_url=base_url,
            path="/v1/story-runs",
            headers={"Idempotency-Key": f"{flow_id}:cancel-run-create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 48},
        )
        runner.require_status(cancelled, cancel_body, {201}, "create run for cancel")
        cancelled_run, cancelled_body = runner.api_call(
            trace,
            session,
            name="cancel_story_run",
            method="POST",
            base_url=base_url,
            path=f"/v1/story-runs/{cancel_body['run_ref']}/cancel",
            headers={
                "Idempotency-Key": f"{flow_id}:cancel-run",
                "If-Match": cancelled.headers.get("ETag", ""),
            },
            json={"expected_revision": cancel_body["revision"]},
        )
        runner.require_status(cancelled_run, cancelled_body, {202}, "cancel story run")

        disposable, disposable_body = runner.api_call(
            trace,
            session,
            name="create_run_for_upload_abort_test",
            method="POST",
            base_url=base_url,
            path="/v1/story-runs",
            headers={"Idempotency-Key": f"{flow_id}:abort-run-create"},
            json={"profile_ref": "synthetic-parent-demo", "child_age_months": 72},
        )
        runner.require_status(disposable, disposable_body, {201}, "create run for upload abort")
        upload, upload_body = runner.api_call(
            trace,
            session,
            name="create_upload_for_abort_test",
            method="POST",
            base_url=base_url,
            path="/v1/upload-sessions",
            headers={"Idempotency-Key": f"{flow_id}:abort-upload-create"},
            json={
                "target_ref": disposable_body["run_ref"],
                "purpose": "RUN_ARTWORK",
                "media_type": "image/png",
                "expected_size_bytes": parent["image"]["size_bytes"],
                "expected_sha256": parent["image"]["sha256"],
            },
        )
        runner.require_status(upload, upload_body, {201}, "create upload for abort")
        aborted, aborted_body = runner.api_call(
            trace,
            session,
            name="abort_upload_session",
            method="DELETE",
            base_url=base_url,
            path=f"/v1/upload-sessions/{upload_body['upload_ref']}",
            headers={
                "Idempotency-Key": f"{flow_id}:abort-upload",
                "If-Match": upload.headers.get("ETag", ""),
            },
        )
        runner.require_status(aborted, aborted_body, {202}, "abort upload")

        for name, path in (("unmounted_health_route", "/health"), ("unmounted_openapi_route", "/openapi.json")):
            response, body = runner.api_call(
                trace, session, name=name, method="GET", base_url=base_url, path=path
            )
            runner.require_status(response, body, {404}, name)
    finally:
        runner.stop_api_server(harness)


def main() -> int:
    runner = load_runner()
    if not runner.TRACE_PATH.is_file():
        raise SystemExit("The original POC trace is missing; refusing to create a new run.")
    trace = json.loads(runner.TRACE_PATH.read_text(encoding="utf-8"))
    validate_resume_preconditions(runner, trace)
    runner.dump_json(
        CONTINUATION_GUARD,
        {
            "state": "CONTINUATION_STARTED",
            "run_ref": trace["parent_flow"]["run_ref"],
            "created_at": runner.now_local(),
            "story_attempts": 1,
            "deck_attempts": 1,
            "visual_attempts": 1,
            "video_enabled": False,
        },
    )
    failures: list[dict[str, str]] = []
    try:
        request_story_and_exercise_apis(runner, trace)
    except Exception as exc:
        failures.append(
            {"stage": "parent_story_and_api_continuation", "error_type": type(exc).__name__, "message": str(exc)[:300]}
        )
        trace["parent_flow"].update(
            {
                "state": trace["parent_flow"].get("state", "FAILED"),
                "ended_at": runner.now_local(),
                "continuation_error_type": type(exc).__name__,
                "continuation_error": str(exc)[:300],
            }
        )
        runner.dump_json(runner.RESULT_PATH, {"parent_flow": trace["parent_flow"]})
    try:
        runner.teacher_deck_flow(trace)
    except Exception as exc:
        failures.append(
            {"stage": "teacher_deck_flow", "error_type": type(exc).__name__, "message": str(exc)[:300]}
        )
        trace["teacher_deck"] = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)[:300]}
        runner.dump_json(runner.TRACE_PATH, trace)
    trace.update({"ended_at": runner.now_local(), "failures": failures, "video_called": False})
    runner.dump_json(runner.TRACE_PATH, trace)
    runner.dump_json(
        CONTINUATION_GUARD,
        {
            "state": "CONTINUATION_FINISHED",
            "run_ref": trace["parent_flow"].get("run_ref"),
            "ended_at": trace["ended_at"],
            "failures": failures,
            "video_enabled": False,
        },
    )
    print(
        json.dumps(
            {
                "parent_state": trace.get("parent_flow", {}).get("state"),
                "teacher_deck_state": trace.get("teacher_deck", {}).get("status"),
                "api_operations": len(trace.get("api_records", [])),
                "modal_workers": [
                    {"workload": item["workload"], "outcome": item["outcome"], "call_id": item.get("call_id")}
                    for item in trace.get("modal_workers", [])
                ],
                "failures": failures,
                "video_called": False,
            },
            ensure_ascii=True,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
