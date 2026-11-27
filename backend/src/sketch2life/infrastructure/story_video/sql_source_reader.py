"""SQL reader of everything the Parent video pipeline needs about a confirmed story (FEAT-093); read-only.

Implements ``VideoSourceReaderPort``: the story revision (title, sections, hash), the child's age and topic from the run
context, the adult's chosen activity, the approved main and secondary subjects with their boxes, and the original
drawing bytes from object storage. Anything missing or inconsistent answers ``None`` (the job then fails with a safe code).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.parent_subject_roles import approved_subjects
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.story_video import VideoRenderRequest
from sketch2life.application.story_staging import unpack_sections
from sketch2life.application.video_pipeline.ports import VideoSource
from sketch2life.application.video_pipeline.timeline_planner import PlannerSubject
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.local_boxes import grid_box

MAX_DRAWING_BYTES = 20 * 1024 * 1024
_ACTIVITY_FIELDS = ("title", "objective", "materials_text", "instructions_text", "activity_kind")


class SqlVideoSourceReader:
    def __init__(
        self, session_factory: Callable[[], Session] | sessionmaker[Session], storage: ObjectStoragePort
    ) -> None:
        self._sessions = session_factory
        self._storage = storage

    def read(self, request: VideoRenderRequest) -> VideoSource | None:
        try:
            with self._sessions() as session:
                return self._read(session, request)
        except (SQLAlchemyError, ObjectStorageFailure, KeyError, ValueError, TypeError):
            return None

    def _read(self, session: Session, request: VideoRenderRequest) -> VideoSource | None:
        revisions = story_tables.story_revisions
        revision = (
            session.execute(
                select(revisions).where(
                    revisions.c.story_revision_id == request.story_revision_id,
                    revisions.c.run_id == request.run_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if revision is None or not revision["story_sha256"] or revision["story_content"] is None:
            return None
        if request.script_hash and revision["story_sha256"] != request.script_hash:
            return None
        run = (
            session.execute(select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == request.run_id))
            .mappings()
            .one_or_none()
        )
        if run is None:
            return None
        input_row = (
            session.execute(
                select(story_tables.run_inputs).where(
                    story_tables.run_inputs.c.run_id == request.run_id,
                    story_tables.run_inputs.c.context_revision == revision["context_revision"],
                    story_tables.run_inputs.c.original_sha256 == revision["source_asset_sha256"],
                )
                .order_by(story_tables.run_inputs.c.input_revision.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        understanding = (
            session.execute(
                select(story_tables.understanding_revisions).where(
                    story_tables.understanding_revisions.c.run_id == request.run_id,
                    story_tables.understanding_revisions.c.revision_no == revision["understanding_revision"],
                )
            )
            .mappings()
            .one_or_none()
        )
        selection = (
            session.execute(
                select(story_tables.activity_selections)
                .where(
                    story_tables.activity_selections.c.run_id == request.run_id,
                    story_tables.activity_selections.c.target_understanding_revision
                    == revision["understanding_revision"],
                )
                .order_by(story_tables.activity_selections.c.selection_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        if input_row is None or understanding is None or selection is None or not input_row["original_asset_ref"]:
            return None
        candidate = (understanding["result_snapshot"] or {}).get("result")
        if not isinstance(candidate, dict):
            return None
        main, secondaries = approved_subjects(candidate)
        subjects, boxes = [], {}
        for entity, role in [(main, "main"), *[(item, "secondary") for item in secondaries]]:
            box = grid_box(entity.get("box"))
            label = str(entity.get("label") or run["subject_label"] or "").strip()
            if box is None or not label:
                return None
            subjects.append(PlannerSubject(str(entity["entity_id"]), label, role))
            boxes[str(entity["entity_id"])] = box
        drawing = self._drawing(str(input_row["original_asset_ref"]), str(input_row["original_sha256"]))
        if drawing is None:
            return None
        context = input_row["context_snapshot"] or {}
        sections = unpack_sections(revision["story_content"])
        activity_snapshot = selection["activity_snapshot"] or {}
        learning = self._learning(session, revision, request.story_revision_id)
        return VideoSource(
            learning=learning,
            run_id=request.run_id,
            story_sha256=str(revision["story_sha256"]),
            story={"title": revision["title"] or "", **sections},
            topic=str(context.get("topic", ""))[:120],
            age_months=int(context["age_months"]),
            subjects=tuple(subjects),
            activity={name: str(activity_snapshot.get(name, ""))[:400] for name in _ACTIVITY_FIELDS},
            drawing_png=drawing,
            drawing_sha256=str(input_row["original_sha256"]),
            subject_boxes=boxes,
        )

    def _learning(self, session: Session, revision: Any, revision_id: str) -> dict[str, Any] | None:
        """The stored learning script with the confirmed spoken text of every scene (FEAT-094)."""

        stored = revision["story_content"].get("learning")
        if not stored:
            return None
        scenes = story_tables.story_scenes
        rows = (
            session.execute(
                select(scenes)
                .where(scenes.c.story_revision_id == revision_id)
                .order_by(scenes.c.scene_index)
            )
            .mappings()
            .all()
        )
        planned = {entry["scene_index"]: entry for entry in stored["scenes"]}
        return {
            "title": revision["title"] or "",
            "scenes": [
                {**planned[row["scene_index"]], "title": row["title"], "narration": row["narration"]} for row in rows
            ],
        }

    def _drawing(self, key: str, expected_sha256: str) -> bytes | None:
        stored = self._storage.get_object(key)
        if stored is None or stored.content_length > MAX_DRAWING_BYTES:
            return None
        try:
            data = stored.body.read()
        finally:
            stored.body.close()
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            return None
        return data


__all__ = ["SqlVideoSourceReader"]
