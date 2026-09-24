"""Safe filesystem paths for ephemeral whiteboard artifacts."""

from __future__ import annotations

from pathlib import Path


class WhiteboardArtifactPaths:
    """Resolve job/region artifact paths below one configured runtime root."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()

    @property
    def root(self) -> Path:
        return self._root

    def job_file(self, job_id: str, suffix: str) -> Path:
        if not job_id or Path(job_id).name != job_id:
            raise ValueError("invalid whiteboard job id")
        if not suffix.startswith(".") or "/" in suffix or "\\" in suffix:
            raise ValueError("invalid whiteboard artifact suffix")
        path = (self._root / job_id).with_suffix(suffix).resolve()
        self._assert_inside(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def region_mask(self, region_ref: str) -> Path:
        if not region_ref or Path(region_ref).name != region_ref:
            raise ValueError("invalid whiteboard region reference")
        path = (self._root / "masks" / f"{region_ref}.png").resolve()
        self._assert_inside(path)
        return path

    def _assert_inside(self, path: Path) -> None:
        try:
            path.relative_to(self._root)
        except ValueError as error:
            raise ValueError("whiteboard artifact path escapes runtime root") from error


__all__ = ["WhiteboardArtifactPaths"]
