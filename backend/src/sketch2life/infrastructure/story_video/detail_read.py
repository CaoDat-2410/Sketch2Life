"""Story-owned read behind the video part of ``GET /v1/story-runs/{id}`` (FEAT-066 T-1c).

SRS l.1811 and AC-41 ask the run detail to show the video state, the job state, the scenes and a
playback readiness without cross-schema SQL and without a read-model table. Story owns the
generation rows, their scenes and (T-1a D8/D9) the job record, so one bounded read is enough: the
accepted rows and the pending intent of one run (at most four rows), the scenes of the current
generation, and the job of each row mapped by the single mapper that ``GET /v1/jobs/{id}`` uses.
No ``ai_jobs``, Billing, Lesson or Core table is read, and no prompt, key or provider text is
selected: the output reference is read only as "present or not".

It lives apart from ``repository.py`` because ``parent_story_repository`` calls it and
``repository.py`` (through ``uploads.resolvers``) imports ``parent_story_repository``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.story_video import (
    DetailGeneration,
    DetailProgress,
    DetailScene,
    RunVideoRows,
)
from sketch2life.domain.story_video.model import MAX_ACCEPTED_REQUESTS, GenerationState
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.job_projection import build_video_job

_VG = story_tables.video_generations
_VGS = story_tables.video_generation_scenes
_PROGRESS = story_tables.video_generation_progress
_SCENES = story_tables.story_scenes
_REVISIONS = story_tables.story_revisions
# Three accepted requests at most (l.573) plus the one intent that may still wait for admission.
_ROW_LIMIT = MAX_ACCEPTED_REQUESTS + 1


def read_run_video(
    session: Session, run_id: str, current_generation_id: str | None
) -> RunVideoRows | None:
    """The video rows of a run, or ``None`` when the run has no current generation (nothing to
    show: no request was ever accepted or is waiting)."""

    if current_generation_id is None:
        return None
    rows = (
        session.execute(
            select(
                _VG.c.video_generation_id,
                _VG.c.generation_no,
                _VG.c.generation_kind,
                _VG.c.state,
                _VG.c.technical_validation_state,
                _VG.c.consistency_validation_state,
                _VG.c.safety_validation_state,
                # presence only: the physical key is never selected (it is Story-internal)
                _VG.c.output_asset_ref.is_not(None).label("has_output"),
                _VG.c.admission_started_at,
                _VG.c.accepted_at,
                _VG.c.started_at,
                _VG.c.completed_at,
                _VG.c.updated_at,
                _VG.c.job_ref,
                _VG.c.target_script_hash,
                _VG.c.safe_failure_code,
                _VG.c.generation_revision,
                _REVISIONS.c.revision_no,
            )
            .join(_REVISIONS, _REVISIONS.c.story_revision_id == _VG.c.story_revision_id)
            .where(
                _VG.c.story_run_id == run_id,
                or_(
                    _VG.c.generation_no.is_not(None),
                    _VG.c.state == str(GenerationState.ADMISSION_PENDING),
                ),
            )
            .order_by(_VG.c.admission_started_at, _VG.c.video_generation_id)
            .limit(_ROW_LIMIT)
        )
        .mappings()
        .all()
    )
    if not rows:
        return None
    scenes = (
        session.execute(
            select(_SCENES.c.scene_index, _VGS.c.state)
            .join(
                _VGS,
                (_VGS.c.story_revision_id == _SCENES.c.story_revision_id)
                & (_VGS.c.story_scene_id == _SCENES.c.scene_id),
            )
            .where(_VGS.c.video_generation_id == current_generation_id)
            .order_by(_SCENES.c.scene_index)
            .limit(15)
        )
        .mappings()
        .all()
    )
    progress_row = (
        session.execute(
            select(_PROGRESS).where(_PROGRESS.c.video_generation_id == current_generation_id)
        )
        .mappings()
        .one_or_none()
    )
    return RunVideoRows(
        current_generation_id=current_generation_id,
        generations=tuple(
            _generation(row, progress_row if str(row["video_generation_id"]) == current_generation_id else None)
            for row in rows
        ),
        scenes=tuple(
            DetailScene(int(scene["scene_index"]), str(scene["state"])) for scene in scenes
        ),
    )


def _progress(row: Any) -> DetailProgress | None:
    if row is None:
        return None
    cues = row["cues"] if isinstance(row["cues"], list) else []
    return DetailProgress(
        stage=str(row["stage"]),
        scene_index=None if row["scene_index"] is None else int(row["scene_index"]),
        scene_count=int(row["scene_count"]),
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        cues=tuple(cue for cue in cues if isinstance(cue, dict)),
    )


def _generation(row: Any, progress_row: Any = None) -> DetailGeneration:
    return DetailGeneration(
        generation_id=str(row["video_generation_id"]),
        generation_no=None if row["generation_no"] is None else int(row["generation_no"]),
        kind=str(row["generation_kind"]),
        state=str(row["state"]),
        technical_validation_state=str(row["technical_validation_state"]),
        consistency_validation_state=str(row["consistency_validation_state"]),
        safety_validation_state=str(row["safety_validation_state"]),
        has_output=bool(row["has_output"]),
        admission_started_at=row["admission_started_at"],
        accepted_at=row["accepted_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        updated_at=row["updated_at"],
        job=build_video_job(row),
        progress=_progress(progress_row),
    )


__all__ = ["read_run_video"]
