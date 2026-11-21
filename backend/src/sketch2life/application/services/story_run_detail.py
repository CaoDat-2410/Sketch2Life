"""Compose the video part of ``StoryRunDetailV1`` (FEAT-066 T-1c; SRS l.805, l.1811, AC-41, TD-22).

Pure functions over the records of one bounded Story-owned read (``RunVideoRows``). The output is
plain dictionaries the HTTP model validates. Nothing here reads a store, a clock or a port, and
nothing here can show a prompt, a raw transcript, a hidden story revision, provider text, a foreign
scope or the physical storage key: those never reach a ``DetailGeneration``.

* ``video_requests_used`` and ``video_requests_remaining`` are the three-request run cap of FR-AI-07
  (l.573). They are not the monthly quota, which is a separate marker (TD-22: a quota that cannot be
  read is "UNAVAILABLE", never zero).
* The ``playback`` block is a readiness descriptor and the route name; a token exists only after
  the explicit ``POST .../playback-token``. A ``COMPLETED`` run shows ``UNAVAILABLE`` (T-1c Q5).
* ``timeline`` is derived from timestamps that already exist (no history store, no read-model
  table: l.845).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sketch2life.application.ports.story_video import DetailGeneration, RunVideoRows
from sketch2life.domain.story_video.model import (
    MAX_ACCEPTED_REQUESTS,
    GenerationState,
    is_playable,
    public_failure_code,
)

PLAYBACK_GRANT_ROUTE = "/v1/story-runs/{run_id}/playback-token"


def video_asset_handle(generation_id: str) -> str:
    """The opaque handle a client sees for a video (never the key): ``vid_`` plus the id."""

    return f"vid_{generation_id}"


def compose_video(run_id: str, run_state: str, rows: RunVideoRows | None) -> dict[str, Any] | None:
    """The ``video`` block, or ``None`` until a request was accepted or is waiting."""

    if rows is None:
        return None
    current = next(
        (row for row in rows.generations if row.generation_id == rows.current_generation_id), None
    )
    if current is None:
        return None
    accepted = [row for row in rows.generations if row.generation_no is not None]
    used = len(accepted)
    return {
        "current_generation_id": current.generation_id,
        "generation_no": current.generation_no,
        "kind": current.kind,
        "state": current.state,
        "job": _job(current),
        "scenes": [
            {"scene_index": scene.scene_index, "state": scene.state} for scene in rows.scenes
        ],
        "playback": _playback(run_id, run_state, current),
        "video_requests_used": used,
        "video_requests_remaining": max(0, MAX_ACCEPTED_REQUESTS - used),
        "admission_pending": any(
            row.state == str(GenerationState.ADMISSION_PENDING) for row in rows.generations
        ),
        "history": [
            {
                "generation_id": row.generation_id,
                "generation_no": row.generation_no,
                "kind": row.kind,
                "state": row.state,
            }
            for row in accepted[:MAX_ACCEPTED_REQUESTS]
        ],
    }


def _job(row: DetailGeneration) -> dict[str, Any] | None:
    job = row.job
    if job is None:
        return None
    failure = job.failure
    return {
        "job_id": job.job_id,
        "state": job.state.value,
        "stage": job.progress.stage_label,
        "retryable": failure.retryable if failure is not None else False,
        "error_code": public_failure_code(failure.code) if failure is not None else None,
    }


def _playback(run_id: str, run_state: str, current: DetailGeneration) -> dict[str, Any]:
    if is_playable(
        run_state=run_state,
        generation_state=current.state,
        technical=current.technical_validation_state,
        consistency=current.consistency_validation_state,
        safety=current.safety_validation_state,
        has_output=current.has_output,
    ):
        return {
            "state": "AVAILABLE",
            "asset_ref": video_asset_handle(current.generation_id),
            "token_route": PLAYBACK_GRANT_ROUTE.format(run_id=run_id),
        }
    if current.state == str(GenerationState.REJECTED_BY_ADULT):
        return {"state": "HIDDEN", "asset_ref": None, "token_route": None}
    return {"state": "UNAVAILABLE", "asset_ref": None, "token_route": None}


def compose_timeline(
    *,
    run_state: str,
    run_created_at: datetime,
    run_finished_at: datetime | None,
    rows: RunVideoRows | None,
) -> list[dict[str, Any]]:
    """Safe, derived events in time order; at most about twenty entries (three requests)."""

    events: list[tuple[datetime, int, str]] = [(run_created_at, 0, "RUN_CREATED")]
    for row in rows.generations if rows is not None else ():
        events.append((row.admission_started_at, 1, "VIDEO_REQUESTED"))
        if row.accepted_at is not None:
            events.append((row.accepted_at, 2, "VIDEO_ACCEPTED"))
        if row.started_at is not None:
            events.append((row.started_at, 3, "VIDEO_STARTED"))
        state = row.state
        if row.completed_at is not None:
            if state in {
                str(GenerationState.READY),
                str(GenerationState.REJECTED_BY_ADULT),
                str(GenerationState.SUPERSEDED),
            }:
                events.append((row.completed_at, 4, "VIDEO_READY"))
            elif state == str(GenerationState.SAFETY_BLOCKED):
                events.append((row.completed_at, 4, "VIDEO_SAFETY_BLOCKED"))
            elif state == str(GenerationState.FAILED):
                events.append((row.completed_at, 4, "VIDEO_FAILED"))
        if state == str(GenerationState.REJECTED_BY_ADULT):
            # A rejected row is terminal: its last update is the adult's mark.
            events.append((row.updated_at, 5, "VIDEO_REJECTED_BY_ADULT"))
    if run_state == "COMPLETED" and run_finished_at is not None:
        events.append((run_finished_at, 6, "RUN_COMPLETED"))
    events.sort(key=lambda item: (item[0], item[1]))
    return [{"event": name, "at": at} for at, _order, name in events]


def detail_etag(story_run: dict[str, Any]) -> str:
    """Strong ETag of a run detail (SRS l.1811): a content hash of the canonical, sorted-key body
    of the ``story_run`` object (JSON mode), so it holds no per-call value (``request_id`` is not
    part of it) and changes whenever any field of the body changes: generation and scene states
    move without a run revision bump, which is why the run revision is not the tag."""

    canonical = json.dumps(story_run, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f'"d1-{hashlib.sha256(canonical.encode("ascii")).hexdigest()[:32]}"'


def etag_matches(header: str | None, etag: str) -> bool:
    """``If-None-Match``: the list names the current tag (weak form accepted) or ``*``."""

    if header is None:
        return False
    for item in header.split(","):
        token = item.strip().removeprefix("W/")
        if token in {etag, "*"}:
            return True
    return False


__all__ = [
    "PLAYBACK_GRANT_ROUTE",
    "compose_timeline",
    "compose_video",
    "detail_etag",
    "etag_matches",
    "video_asset_handle",
]
