from __future__ import annotations

import logging
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy import Engine

from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineError, QuarantineStore
from sketch2life.infrastructure.story_run_lite.repository import SqlStoryRunLiteRepository


def test_cleanup_removes_only_target_and_is_idempotent(tmp_path: Path) -> None:
    quarantine = QuarantineStore(tmp_path)
    repository = SqlStoryRunLiteRepository(engine=cast(Engine, object()), quarantine=quarantine)
    target, other = str(uuid4()), str(uuid4())
    quarantine.write_part(target, 1, b"target")
    quarantine.write_part(other, 1, b"other")

    assert repository.remove_upload_quarantine(target) is True
    assert not (quarantine._parts / target).exists()
    assert (quarantine._parts / other / "part-01.bin").read_bytes() == b"other"
    assert repository.remove_upload_quarantine(target) is True


@pytest.mark.parametrize("error", [OSError("synthetic failure"), QuarantineError("invalid")])
def test_cleanup_reports_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
) -> None:
    quarantine = QuarantineStore(tmp_path)
    repository = SqlStoryRunLiteRepository(engine=cast(Engine, object()), quarantine=quarantine)
    target = str(uuid4())
    quarantine.write_part(target, 1, b"target")
    calls: list[str] = []

    def fail(upload_id: str) -> None:
        calls.append(upload_id)
        raise error

    monkeypatch.setattr(quarantine, "remove_upload", fail)
    with caplog.at_level(logging.WARNING):
        assert repository.remove_upload_quarantine(target) is False
    assert calls == [target]
    assert (quarantine._parts / target / "part-01.bin").read_bytes() == b"target"
    assert "StoryRun-lite upload staging cleanup failed" in caplog.text
