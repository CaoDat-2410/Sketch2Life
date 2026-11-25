"""FEAT-093: the run detail shows the real stage, an estimate and, when ready, the captions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sketch2life.application.ports.story_video import DetailGeneration, DetailProgress, RunVideoRows
from sketch2life.application.services.story_run_detail import compose_video, estimate_eta_seconds
from sketch2life.contracts.schemas.story_run_video import ParentStoryRunVideoV1

NOW = datetime(2026, 11, 25, 9, 0, tzinfo=UTC)
RUN = str(uuid4())


def _rows(state: str, progress: DetailProgress | None):
    generation_id = str(uuid4())
    generation = DetailGeneration(
        generation_id=generation_id, generation_no=1, kind="INITIAL", state=state,
        technical_validation_state="PASSED" if state == "READY" else "PENDING",
        consistency_validation_state="PASSED" if state == "READY" else "PENDING",
        safety_validation_state="PASSED" if state == "READY" else "PENDING",
        has_output=state == "READY", admission_started_at=NOW, accepted_at=NOW, started_at=NOW, completed_at=None,
        updated_at=NOW, job=None, progress=progress,
    )
    return RunVideoRows(current_generation_id=generation_id, generations=(generation,), scenes=())


def test_a_running_generation_shows_stage_scene_and_an_estimate() -> None:
    rows = _rows("GENERATING", DetailProgress("RENDERING", 2, 5, NOW, NOW))

    video = compose_video(RUN, "VIDEO_GENERATING", rows)

    assert video is not None and video["progress"]["stage"] == "RENDERING"
    assert video["progress"]["scene_index"] == 2 and video["progress"]["eta_seconds"] == 4 * 100 + 120
    assert video["captions"] is None
    ParentStoryRunVideoV1.model_validate(video)


def test_a_ready_video_has_captions_and_no_progress() -> None:
    cues = ({"start_ms": 0, "end_ms": 900, "text": "Rùa đi.", "lane": "narration", "speaker_ref": None},)
    video = compose_video(RUN, "VIDEO_READY", _rows("READY", DetailProgress("CHECKING", None, 5, NOW, NOW, cues)))

    assert video is not None and video["progress"] is None
    assert video["captions"] == [{"start_ms": 0, "end_ms": 900, "text": "Rùa đi.", "lane": "narration"}]
    ParentStoryRunVideoV1.model_validate(video)


def test_without_progress_nothing_is_invented() -> None:
    video = compose_video(RUN, "VIDEO_GENERATING", _rows("QUEUED", None))

    assert video is not None and video["progress"] is None and video["captions"] is None


def test_estimates_shrink_as_the_worker_advances() -> None:
    first = estimate_eta_seconds("PLANNING", None, 5)
    middle = estimate_eta_seconds("RENDERING", 3, 5)
    end = estimate_eta_seconds("CHECKING", None, 5)
    assert first > middle > end > 0
