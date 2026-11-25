"""FEAT-093: the SQL source reader assembles a VideoSource from stored rows (canned rows, no database)."""

from __future__ import annotations

import hashlib
import io

from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.story_video import VideoRenderRequest
from sketch2life.infrastructure.story_video.local_boxes import grid_box
from sketch2life.infrastructure.story_video.sql_source_reader import SqlVideoSourceReader

DRAWING = b"\x89PNG-drawing"
SHA = hashlib.sha256(DRAWING).hexdigest()
REQUEST = VideoRenderRequest("gen-1", "run-1", "rev-1", "s" * 64, 0, "job-1")


class _Result:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row


class _Session:
    def __init__(self, rows):
        self.rows = list(rows)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, _statement):
        return _Result(self.rows.pop(0))


class _Body:
    def __init__(self, data):
        self._io = io.BytesIO(data)

    def read(self, size=-1):
        return self._io.read(size)

    def close(self):
        pass


class _Storage:
    def __init__(self, data=DRAWING):
        self.data = data

    def get_object(self, key):
        return None if self.data is None else StoredObject(_Body(self.data), len(self.data), "image/png", {})


def _rows(**override):
    revision = {
        "story_sha256": "s" * 64, "story_content": {"opening": "Rùa ra khỏi hang.", "middle": "Rùa ăn lá.", "ending": "Rùa cười."},
        "title": "Rùa con", "context_revision": 1, "source_asset_sha256": SHA, "understanding_revision": 2,
    }
    candidate = {
        "candidate_subject": "con rùa",
        "main_subject": {"entity_id": "main", "label": "con rùa", "box": [2, 6, 11, 17]},
        "secondary_subjects": [
            {"entity_id": "sec-1", "label": "chiếc lá", "box": [13, 9, 19, 15]},
            {"entity_id": "sec-2", "label": "đám mây", "box": [1, 0, 6, 3]},
        ],
        "approved_roles": [{"entity_id": "main", "role": "main"}, {"entity_id": "sec-1", "role": "secondary"}],
    }
    rows = [
        revision,
        {"subject_label": "con rùa"},
        {"original_asset_ref": "parent/run-1/original.png", "original_sha256": SHA, "context_snapshot": {"topic": "Động vật", "age_months": 48}},
        {"result_snapshot": {"result": candidate}},
        {"activity_snapshot": {"title": "Tìm lá", "objective": "Quan sát lá", "activity_kind": "OUTDOOR"}},
    ]
    for index, value in override.items():
        rows[int(index)] = value
    return rows


def _read(rows, storage=None):
    return SqlVideoSourceReader(lambda: _Session(rows), storage or _Storage()).read(REQUEST)


def test_a_confirmed_story_becomes_a_video_source() -> None:
    source = _read(_rows())

    assert source is not None
    assert source.story_sha256 == "s" * 64 and source.age_months == 48 and source.topic == "Động vật"
    assert [(s.entity_id, s.role) for s in source.subjects] == [("main", "main"), ("sec-1", "secondary")]
    assert source.subject_boxes == {"main": (2, 6, 11, 17), "sec-1": (13, 9, 19, 15)}  # sec-2 was not approved
    assert source.story["middle"] == "Rùa ăn lá." and source.activity["title"] == "Tìm lá"
    assert source.drawing_png == DRAWING and source.drawing_sha256 == SHA


def test_missing_or_inconsistent_data_answers_none() -> None:
    assert _read(_rows(**{"0": None})) is None
    assert _read(_rows(), _Storage(None)) is None
    assert _read(_rows(), _Storage(b"tampered")) is None
    wrong_hash = VideoRenderRequest("gen-1", "run-1", "rev-1", "x" * 64, 0, "job-1")
    assert SqlVideoSourceReader(lambda: _Session(_rows()), _Storage()).read(wrong_hash) is None


def test_grid_boxes_are_validated() -> None:
    assert grid_box([2, 6, 11, 17]) == (2, 6, 11, 17)
    for bad in (None, [1, 2, 3], [5, 5, 5, 9], [0, 0, 21, 5], [True, 0, 3, 3], "box"):
        assert grid_box(bad) is None
