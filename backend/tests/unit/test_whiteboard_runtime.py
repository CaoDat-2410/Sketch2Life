from __future__ import annotations

import json

import pytest

from sketch2life.infrastructure.media.whiteboard_runtime import (
    WhiteboardLearningThreadScripts,
)


def test_learning_thread_scripts_resolve_fixture_ref(tmp_path) -> None:
    fixture = tmp_path / "threads.json"
    fixture.write_text(json.dumps({"thread-1": "  Nội dung bài học.  "}), encoding="utf-8")

    scripts = WhiteboardLearningThreadScripts(fixture)

    assert scripts.script_for("thread-1") == "Nội dung bài học."


def test_learning_thread_scripts_fail_closed_for_unknown_ref(tmp_path) -> None:
    fixture = tmp_path / "threads.json"
    fixture.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="script is unavailable"):
        WhiteboardLearningThreadScripts(fixture).script_for("missing")
