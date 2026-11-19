"""FEAT-066 C4: derived upload-session revision and the stale-revision mapping."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryService,
    LessonLibraryStaleRevision,
    upload_session_revision,
)
from sketch2life.interfaces.http.routers.lesson_library import _call


@pytest.mark.parametrize(
    ("state", "parts", "expected"),
    [
        ("OPEN", 0, 1),
        ("OPEN", 3, 4),
        ("COMPLETED", 3, 5),
        ("ABORTED", 0, 2),
        ("EXPIRED", 2, 4),
        ("FAILED", 1, 3),
    ],
)
def test_upload_session_revision_is_one_plus_parts_open_and_two_plus_parts_after(
    state: str, parts: int, expected: int
) -> None:
    assert upload_session_revision(state, parts) == expected


def test_every_terminal_state_is_above_the_open_value_for_the_same_parts() -> None:
    for parts in range(8):
        open_value = upload_session_revision("OPEN", parts)
        for state in ("COMPLETED", "ABORTED", "EXPIRED", "FAILED"):
            assert upload_session_revision(state, parts) == open_value + 1


def test_require_revision_carries_the_current_revision() -> None:
    with pytest.raises(LessonLibraryStaleRevision) as caught:
        LessonLibraryService._require_revision(4, 3)
    assert caught.value.current_revision == 4
    assert caught.value.status_code == 409
    assert caught.value.code == "STALE_REVISION"
    LessonLibraryService._require_revision(4, 4)


def test_router_maps_stale_revision_to_current_version_and_strong_etag() -> None:
    def stale() -> None:
        raise LessonLibraryStaleRevision(7)

    with pytest.raises(HTTPException) as caught:
        _call(stale)
    assert caught.value.status_code == 409
    assert caught.value.detail == {"code": "STALE_REVISION", "current_version": 7}
    assert caught.value.headers == {"ETag": '"7"'}
