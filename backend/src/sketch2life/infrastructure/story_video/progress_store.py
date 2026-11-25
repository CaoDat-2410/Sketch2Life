"""Progress and captions of a video generation in PostgreSQL (FEAT-093); written by the worker, read by the API."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.video_pipeline.caption_plan import Cue
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_PROGRESS = story_tables.video_generation_progress


@dataclass(frozen=True, slots=True)
class VideoProgress:
    stage: str
    scene_index: int | None
    scene_count: int
    started_at: datetime
    updated_at: datetime


def cues_to_json(cues: Sequence[Cue]) -> list[dict[str, Any]]:
    return [
        {"start_ms": cue.start_ms, "end_ms": cue.end_ms, "text": cue.text, "lane": cue.lane, "speaker_ref": cue.speaker_ref}
        for cue in cues
    ]


class SqlVideoProgressStore:
    def __init__(
        self,
        session_factory: Callable[[], Session] | sessionmaker[Session],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sessions = session_factory
        self._clock = clock

    def record(self, generation_id: str, stage: str, scene_index: int | None, scene_count: int) -> None:
        now = self._clock()
        statement = insert(_PROGRESS).values(
            video_generation_id=generation_id, stage=stage, scene_index=scene_index, scene_count=scene_count,
            started_at=now, updated_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[_PROGRESS.c.video_generation_id],
            set_={"stage": stage, "scene_index": scene_index, "scene_count": scene_count, "updated_at": now},
        )
        with self._sessions() as session:
            session.execute(statement)
            session.commit()

    def record_captions(self, generation_id: str, vtt: str, cues: Sequence[Cue]) -> None:
        with self._sessions() as session:
            session.execute(
                _PROGRESS.update()
                .where(_PROGRESS.c.video_generation_id == generation_id)
                .values(captions_vtt=vtt, cues=cues_to_json(cues), updated_at=self._clock())
            )
            session.commit()

    def read(self, generation_id: str) -> VideoProgress | None:
        with self._sessions() as session:
            row = (
                session.execute(select(_PROGRESS).where(_PROGRESS.c.video_generation_id == generation_id))
                .mappings()
                .one_or_none()
            )
        if row is None:
            return None
        return VideoProgress(
            row["stage"], row["scene_index"], int(row["scene_count"]), row["started_at"], row["updated_at"]
        )


__all__ = ["SqlVideoProgressStore", "VideoProgress", "cues_to_json"]
