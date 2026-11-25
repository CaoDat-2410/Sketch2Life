"""FEAT-093: the progress store writes an upsert and reads a row back (statements captured, no database)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.dialects import postgresql

from sketch2life.application.video_pipeline.caption_plan import Cue
from sketch2life.infrastructure.story_video.progress_store import SqlVideoProgressStore, cues_to_json

NOW = datetime(2026, 11, 25, 9, 0, tzinfo=UTC)


class _Session:
    def __init__(self, row=None):
        self.statements, self.committed, self.row = [], 0, row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, statement):
        self.statements.append(statement)
        return self

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row

    def commit(self):
        self.committed += 1


def _sql(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


def test_record_is_an_upsert_on_the_generation_id() -> None:
    session = _Session()

    SqlVideoProgressStore(lambda: session, clock=lambda: NOW).record("gen-1", "RENDERING", 2, 5)

    sql = _sql(session.statements[0])
    assert "INSERT INTO story.video_generation_progress" in sql and "ON CONFLICT (video_generation_id) DO UPDATE" in sql
    assert session.committed == 1


def test_captions_update_and_read_back() -> None:
    session = _Session()
    store = SqlVideoProgressStore(lambda: session, clock=lambda: NOW)

    store.record_captions("gen-1", "WEBVTT", [Cue(0, 900, "Rùa đi.", "narration")])

    assert "UPDATE story.video_generation_progress" in _sql(session.statements[0])
    assert cues_to_json([Cue(0, 900, "Rùa đi.", "narration")])[0]["text"] == "Rùa đi."
    row = {"stage": "RENDERING", "scene_index": 2, "scene_count": 5, "started_at": NOW, "updated_at": NOW}
    progress = SqlVideoProgressStore(lambda: _Session(row)).read("gen-1")
    assert progress is not None and (progress.stage, progress.scene_index, progress.scene_count) == ("RENDERING", 2, 5)
    assert SqlVideoProgressStore(lambda: _Session(None)).read("gen-1") is None
