from __future__ import annotations

import pytest

from sketch2life.infrastructure.media.whiteboard_artifact_paths import (
    WhiteboardArtifactPaths,
)


def test_artifact_paths_stay_under_runtime_root(tmp_path) -> None:
    paths = WhiteboardArtifactPaths(tmp_path)

    artifact = paths.job_file("job-1", ".mp4")
    region = paths.region_mask("region-1")

    assert artifact.parent == tmp_path.resolve()
    assert region.parent == (tmp_path / "masks").resolve()


@pytest.mark.parametrize("value", ["../escape", "a/b", "a\\b", ""])
def test_artifact_paths_reject_traversal(value, tmp_path) -> None:
    paths = WhiteboardArtifactPaths(tmp_path)

    with pytest.raises(ValueError):
        paths.job_file(value, ".mp4")
