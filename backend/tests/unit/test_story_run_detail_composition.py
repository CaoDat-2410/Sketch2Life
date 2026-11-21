"""FEAT-066 T-1c: the video part of ``StoryRunDetailV1`` (SRS l.805, l.1811, AC-41, TD-22).

Pure composition over the records of one bounded read: what the detail shows (state, job, scenes,
playback readiness, request counts, history, timeline), what it must never show (a prompt, a
transcript, provider text, the storage key), the closed public failure-code set, the ETag input,
and the equality of the record and the response model that the seed tests rely on.
"""

from __future__ import annotations

import json
from dataclasses import fields
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from sketch2life.application.ports.parent_story_runs import ParentStoryRunRecord
from sketch2life.application.ports.story_video import DetailGeneration, DetailScene, RunVideoRows
from sketch2life.application.services.story_run_detail import (
    compose_timeline,
    compose_video,
    detail_etag,
    etag_matches,
    video_asset_handle,
)
from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunResponseV1
from sketch2life.contracts.schemas.story_run_video import (
    ParentStoryQuotaSummaryV1,
    ParentStoryRunVideoV1,
)
from sketch2life.domain.story_video.model import (
    PUBLIC_FAILURE_CODES,
    GenerationState,
    is_playable,
    public_failure_code,
)
from sketch2life.infrastructure.story_video.job_projection import build_video_job

T0 = datetime(2026, 11, 21, 8, 0, tzinfo=UTC)
RUN = str(uuid4())


def at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def job_row(state: str, **overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "video_generation_id": str(uuid4()),
        "job_ref": "vjob_synthetic",
        "accepted_at": at(1),
        "state": state,
        "revision_no": 1,
        "target_script_hash": "a" * 64,
        "started_at": at(2),
        "completed_at": at(3),
        "safe_failure_code": None,
        "generation_revision": 2,
        "updated_at": at(3),
    }
    values.update(overrides)
    return values


def generation(
    state: str = "READY",
    *,
    number: int | None = 1,
    kind: str = "INITIAL",
    validations: str = "PASSED",
    has_output: bool = True,
    failure: str | None = None,
    generation_id: str | None = None,
    with_job: bool = True,
) -> DetailGeneration:
    gid = generation_id or str(uuid4())
    row = job_row(state, video_generation_id=gid, safe_failure_code=failure)
    return DetailGeneration(
        generation_id=gid,
        generation_no=number,
        kind=kind,
        state=state,
        technical_validation_state=validations,
        consistency_validation_state=validations,
        safety_validation_state=validations,
        has_output=has_output,
        admission_started_at=at(0),
        accepted_at=at(1) if number is not None else None,
        started_at=at(2) if number is not None else None,
        completed_at=at(3)
        if state in {"READY", "REJECTED_BY_ADULT", "FAILED", "SAFETY_BLOCKED"}
        else None,
        updated_at=at(4) if state == "REJECTED_BY_ADULT" else at(3),
        job=build_video_job(row) if with_job and number is not None else None,
    )


def rows(*items: DetailGeneration, current: int = -1, scenes: int = 5) -> RunVideoRows:
    return RunVideoRows(
        current_generation_id=items[current].generation_id,
        generations=tuple(items),
        scenes=tuple(DetailScene(index, "READY") for index in range(1, scenes + 1)),
    )


# ----------------------------------------------------------------------------- video block
def test_no_rows_means_no_video_block() -> None:
    assert compose_video(RUN, "SCRIPT_REVIEW", None) is None
    ghost = RunVideoRows("missing", (generation(),), ())
    assert compose_video(RUN, "VIDEO_READY", ghost) is None


def test_a_ready_video_in_a_ready_run_is_available_with_a_handle_and_the_token_route() -> None:
    ready = generation()
    video = compose_video(RUN, "VIDEO_READY", rows(ready))
    assert video is not None
    assert video["playback"] == {
        "state": "AVAILABLE",
        "asset_ref": f"vid_{ready.generation_id}",
        "token_route": f"/v1/story-runs/{RUN}/playback-token",
    }
    assert video_asset_handle(ready.generation_id) == f"vid_{ready.generation_id}"
    assert video["video_requests_used"] == 1 and video["video_requests_remaining"] == 2
    assert video["admission_pending"] is False
    assert video["job"] == {
        "job_id": "vjob_synthetic",
        "state": "succeeded",
        "stage": None,
        "retryable": False,
        "error_code": None,
    }
    # the model accepts exactly this shape
    assert ParentStoryRunVideoV1.model_validate(video).playback.state == "AVAILABLE"


@pytest.mark.parametrize(
    ("run_state", "state", "validations", "has_output", "expected"),
    [
        ("VIDEO_READY", "READY", "PASSED", True, "AVAILABLE"),
        ("COMPLETED", "READY", "PASSED", True, "UNAVAILABLE"),  # Q5: l.1676 "active until complete"
        ("SCRIPT_REVIEW", "REJECTED_BY_ADULT", "PASSED", True, "HIDDEN"),
        ("VIDEO_READY", "READY", "PENDING", True, "UNAVAILABLE"),
        ("VIDEO_READY", "READY", "FAILED", True, "UNAVAILABLE"),
        ("VIDEO_READY", "READY", "PASSED", False, "UNAVAILABLE"),
        ("VIDEO_GENERATING", "GENERATING", "PENDING", False, "UNAVAILABLE"),
        ("SAFETY_BLOCKED", "SAFETY_BLOCKED", "FAILED", False, "UNAVAILABLE"),
        ("FAILED", "FAILED", "PENDING", False, "UNAVAILABLE"),
        ("VIDEO_READY", "SUPERSEDED", "PASSED", True, "UNAVAILABLE"),
        ("VIDEO_ADMISSION_PENDING", "ADMISSION_PENDING", "PENDING", False, "UNAVAILABLE"),
    ],
)
def test_the_playback_state_needs_the_run_state_and_the_generation_state_together(
    run_state: str, state: str, validations: str, has_output: bool, expected: str
) -> None:
    number = None if state == "ADMISSION_PENDING" else 1
    current = generation(state, number=number, validations=validations, has_output=has_output)
    video = compose_video(RUN, run_state, rows(current))
    assert video is not None
    assert video["playback"]["state"] == expected
    assert (video["playback"]["asset_ref"] is not None) == (expected == "AVAILABLE")
    assert (video["playback"]["token_route"] is not None) == (expected == "AVAILABLE")
    assert is_playable(
        run_state=run_state,
        generation_state=state,
        technical=validations,
        consistency=validations,
        safety=validations,
        has_output=has_output,
    ) == (expected == "AVAILABLE")


def test_counts_history_and_the_pending_intent_follow_the_accepted_rows() -> None:
    first = generation("REJECTED_BY_ADULT", number=1)
    second = generation("REJECTED_BY_ADULT", number=2, kind="QUALITY_REGEN")
    third = generation("READY", number=3, kind="QUALITY_REGEN")
    video = compose_video(RUN, "VIDEO_READY", rows(first, second, third))
    assert video is not None
    assert video["video_requests_used"] == 3 and video["video_requests_remaining"] == 0
    assert [item["generation_no"] for item in video["history"]] == [1, 2, 3]
    assert video["generation_no"] == 3 and video["kind"] == "QUALITY_REGEN"
    intent = generation("ADMISSION_PENDING", number=None, kind="QUALITY_REGEN", has_output=False)
    pending = compose_video(RUN, "VIDEO_ADMISSION_PENDING", rows(first, intent))
    assert pending is not None
    assert pending["admission_pending"] is True and pending["generation_no"] is None
    assert pending["video_requests_used"] == 1 and pending["video_requests_remaining"] == 2
    assert [item["generation_no"] for item in pending["history"]] == [1]  # the intent is no history
    assert pending["job"] is None
    first_request = compose_video(
        RUN,
        "VIDEO_ADMISSION_PENDING",
        rows(generation("ADMISSION_PENDING", number=None, has_output=False)),
    )
    assert first_request is not None
    assert (
        first_request["video_requests_used"] == 0 and first_request["video_requests_remaining"] == 3
    )
    # an impossible fourth accepted row can never show a negative figure or a long history
    many = rows(*(generation("FAILED", number=n % 3 + 1) for n in range(4)))
    capped = compose_video(RUN, "FAILED", many)
    assert capped is not None
    assert capped["video_requests_remaining"] == 0 and len(capped["history"]) == 3


def test_failure_codes_shown_to_a_client_are_the_closed_set() -> None:
    assert {
        "VIDEO_SAFETY_BLOCKED",
        "VIDEO_DEADLINE_EXCEEDED",
        "VIDEO_TECHNICAL_FAILURE",
        "PROVIDER_UNAVAILABLE",
    } == PUBLIC_FAILURE_CODES
    expected = {
        "SAFETY_BLOCKED": "VIDEO_SAFETY_BLOCKED",
        "VIDEO_SAFETY_BLOCKED": "VIDEO_SAFETY_BLOCKED",
        "VIDEO_DEADLINE_EXCEEDED": "VIDEO_DEADLINE_EXCEEDED",
        "PROVIDER_UNAVAILABLE": "PROVIDER_UNAVAILABLE",
        "VIDEO_TECHNICAL_FAILURE": "VIDEO_TECHNICAL_FAILURE",
        "RUN_CANCELLED": "VIDEO_TECHNICAL_FAILURE",
        "STORAGE_UNAVAILABLE": "VIDEO_TECHNICAL_FAILURE",
        "VIDEO_VALIDATION_FAILED": "VIDEO_TECHNICAL_FAILURE",
        "Traceback (most recent call last)": "VIDEO_TECHNICAL_FAILURE",
        "": "VIDEO_TECHNICAL_FAILURE",
    }
    for stored, public in expected.items():
        assert public_failure_code(stored) == public
    assert public_failure_code(None) == "VIDEO_TECHNICAL_FAILURE"
    for state, stored, public in (
        ("FAILED", "provider said: secret detail", "VIDEO_TECHNICAL_FAILURE"),
        ("SAFETY_BLOCKED", "SAFETY_BLOCKED", "VIDEO_SAFETY_BLOCKED"),
        ("FAILED", "VIDEO_DEADLINE_EXCEEDED", "VIDEO_DEADLINE_EXCEEDED"),
    ):
        video = compose_video(
            RUN,
            state,
            rows(generation(state, validations="FAILED", has_output=False, failure=stored)),
        )
        assert video is not None
        assert video["job"]["error_code"] == public and video["job"]["retryable"] is False
        assert "secret" not in json.dumps(video, default=str)


def test_a_running_job_shows_its_stage_and_no_figure() -> None:
    running = generation("TECHNICAL_VALIDATING", validations="PENDING", has_output=False)
    video = compose_video(RUN, "VIDEO_SAFETY_VALIDATING", rows(running))
    assert video is not None
    assert video["job"]["state"] == "running" and video["job"]["stage"] == "technical_validating"
    assert video["playback"]["state"] == "UNAVAILABLE"


def test_nothing_private_can_appear_in_the_block() -> None:
    video = compose_video(RUN, "VIDEO_READY", rows(generation()))
    text = json.dumps(video, default=str).lower()
    for word in (
        "output_asset_ref",
        "storage",
        "bucket",
        "key",
        "url",
        "prompt",
        "transcript",
        "provider",
        "billing",
        "quota",
        "reservation",
        "idempotency",
        "hash",
    ):
        assert word not in text, word
    assert set(ParentStoryRunVideoV1.model_fields) == set(video)  # type: ignore[arg-type]


# ----------------------------------------------------------------------------- timeline
def test_the_timeline_is_derived_ordered_and_bounded() -> None:
    first = generation("REJECTED_BY_ADULT", number=1)
    second = generation("READY", number=2, kind="QUALITY_REGEN")
    timeline = compose_timeline(
        run_state="COMPLETED",
        run_created_at=at(-10),
        run_finished_at=at(30),
        rows=rows(first, second),
    )
    names = [item["event"] for item in timeline]
    assert names[0] == "RUN_CREATED" and names[-1] == "RUN_COMPLETED"
    assert names.count("VIDEO_REQUESTED") == 2 and names.count("VIDEO_READY") == 2
    assert names.count("VIDEO_REJECTED_BY_ADULT") == 1
    stamps = [item["at"] for item in timeline]
    assert stamps == sorted(stamps)
    assert len(timeline) <= 20
    assert all(set(item) == {"event", "at"} for item in timeline)
    bare = compose_timeline(
        run_state="SCRIPT_REVIEW", run_created_at=at(0), run_finished_at=None, rows=None
    )
    assert [item["event"] for item in bare] == ["RUN_CREATED"]
    failed = compose_timeline(
        run_state="FAILED",
        run_created_at=at(0),
        run_finished_at=at(9),
        rows=rows(generation("FAILED", validations="FAILED", has_output=False)),
    )
    assert "VIDEO_FAILED" in [item["event"] for item in failed]
    assert "RUN_COMPLETED" not in [item["event"] for item in failed]
    blocked = compose_timeline(
        run_state="SAFETY_BLOCKED",
        run_created_at=at(0),
        run_finished_at=None,
        rows=rows(generation("SAFETY_BLOCKED", validations="FAILED", has_output=False)),
    )
    assert "VIDEO_SAFETY_BLOCKED" in [item["event"] for item in blocked]


# ----------------------------------------------------------------------------- etag
def test_the_etag_is_a_stable_content_hash_without_per_call_values() -> None:
    body = {"b": 1, "a": {"z": [1, 2], "y": None}}
    twin = {"a": {"y": None, "z": [1, 2]}, "b": 1}
    first = detail_etag(body)
    assert first == detail_etag(twin)  # canonical: key order does not matter
    assert first.startswith('"d1-') and first.endswith('"') and len(first) == 37
    assert detail_etag({**body, "b": 2}) != first
    assert detail_etag({**body, "a": {"z": [1, 2], "y": ""}}) != first
    envelope = {"request_id": str(uuid4()), "story_run": body}
    assert detail_etag(envelope["story_run"]) == first  # request_id is not part of the input


@pytest.mark.parametrize(
    ("header", "matches"),
    [
        (None, False),
        ("", False),
        ('"d1-x"', True),
        ('W/"d1-x"', True),
        ('"a", "d1-x" ,"b"', True),
        ("*", True),
        ('"d1-y"', False),
        ("d1-x", False),
    ],
)
def test_if_none_match_accepts_the_current_tag_a_weak_form_a_list_and_a_star(
    header: str | None, matches: bool
) -> None:
    assert etag_matches(header, '"d1-x"') is matches


# ----------------------------------------------------------------------------- models
def test_the_quota_marker_is_a_constant_unavailable_never_zero() -> None:
    marker = ParentStoryQuotaSummaryV1()
    assert marker.model_dump() == {
        "state": "UNAVAILABLE",
        "granted": None,
        "used": None,
        "available": None,
        "month": None,
    }
    with pytest.raises(ValueError):
        ParentStoryQuotaSummaryV1(state="AVAILABLE")  # type: ignore[arg-type]


def test_the_record_and_the_response_model_share_the_new_field_names() -> None:
    record_names = {item.name for item in fields(ParentStoryRunRecord)}
    model_names = set(ParentStoryRunResponseV1.model_fields)
    assert {"video", "timeline"} <= record_names
    assert {"video", "quota", "timeline"} <= model_names
    # every record field except the renamed story content is a model field (the seed tests rebuild
    # the model from every dataclass field, so a record-only name would be silently dropped)
    assert record_names - {"story_content"} <= model_names


def test_the_detail_model_is_additive_the_older_fields_keep_their_names() -> None:
    older = {
        "run_id",
        "run_revision",
        "run_state",
        "parent_profile_id",
        "profile_revision_ref",
        "context_revision",
        "context_confirmed",
        "context_snapshot",
        "context_snapshot_sha256",
        "lesson_pin_snapshot",
        "current_input_revision",
        "understanding_revision",
        "subject_label",
        "candidate",
        "story_revision_id",
        "story_revision_no",
        "story_status",
        "story_sha256",
        "story",
        "job_state",
        "retryable",
        "error_code",
        "created_at",
        "updated_at",
    }
    assert older <= set(ParentStoryRunResponseV1.model_fields)
    required = {
        name for name, field in ParentStoryRunResponseV1.model_fields.items() if field.is_required()
    }
    assert {"video", "quota", "timeline"}.isdisjoint(required)  # an old payload still validates


def test_every_video_state_the_machine_has_maps_to_a_schema_state() -> None:
    from sketch2life.contracts.schemas.story_run_video import VideoGenerationState

    assert set(VideoGenerationState.__args__) == {state.value for state in GenerationState}  # type: ignore[attr-defined]


def test_the_two_builders_are_one_function() -> None:
    from sketch2life.interfaces.http.routers import parent_ai, parent_story_runs

    assert parent_ai._story_response is parent_story_runs.story_run_response
    assert parent_story_runs._response is parent_story_runs.story_run_response


def test_the_run_level_error_code_is_the_closed_public_code_while_the_video_failed() -> None:
    from sketch2life.infrastructure.persistence.parent_story_repository import (
        _public_run_error_code,
    )

    failed = generation("FAILED", failure="PROVIDER_STACK_TRACE_RAW", has_output=False)
    blocked = generation("SAFETY_BLOCKED", failure="VIDEO_SAFETY_BLOCKED", has_output=False)
    ready = generation("READY")
    # no stored code, or no video rows: nothing to map, the value is returned unchanged
    assert _public_run_error_code(None, rows(failed)) is None
    assert _public_run_error_code("PROVIDER_STACK_TRACE_RAW", None) == "PROVIDER_STACK_TRACE_RAW"
    # the current video failed or was blocked: only a code of the closed public set is shown
    assert _public_run_error_code("PROVIDER_STACK_TRACE_RAW", rows(failed)) == (
        "VIDEO_TECHNICAL_FAILURE"
    )
    assert _public_run_error_code("PROVIDER_STACK_TRACE_RAW", rows(blocked)) == (
        "VIDEO_TECHNICAL_FAILURE"
    )
    assert _public_run_error_code("VIDEO_SAFETY_BLOCKED", rows(blocked)) == "VIDEO_SAFETY_BLOCKED"
    # a run whose current video did not fail keeps the code of its own family unchanged
    assert _public_run_error_code("RUN_CANCELLED", rows(ready)) == "RUN_CANCELLED"
    # only the CURRENT generation decides: an older failed row does not map the code
    assert _public_run_error_code("RUN_CANCELLED", rows(failed, ready)) == "RUN_CANCELLED"
