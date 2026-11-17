"""Atomic, opaque-reference artifact storage for local BE1 development."""

from __future__ import annotations

import hashlib
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from uuid import UUID, uuid4


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self._root = root.expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def put(self, content: bytes) -> tuple[str, str]:
        if not content:
            raise ValueError("artifact cannot be empty")
        ref = f"local-artifact:{uuid4()}"
        digest = hashlib.sha256(content).hexdigest()
        target = self._path_for(ref)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except Exception:
            with suppress(OSError):
                os.unlink(temporary)
            raise
        return ref, digest

    def get(self, ref: str) -> bytes | None:
        target = self._path_for(ref)
        try:
            return target.read_bytes()
        except FileNotFoundError:
            return None

    def delete(self, ref: str) -> bool:
        target = self._path_for(ref)
        try:
            target.unlink()
            return True
        except FileNotFoundError:
            return False

    def _path_for(self, ref: str) -> Path:
        prefix, separator, token = ref.partition(":")
        if prefix != "local-artifact" or not separator or len(token) != 36:
            raise ValueError("artifact reference is invalid")
        try:
            # UUID parsing rejects separators and path syntax before filesystem access.
            token = str(UUID(token))
        except ValueError:
            raise ValueError("artifact reference is invalid") from None
        path = (self._root / token[:2] / token).resolve()
        if self._root not in path.parents:
            raise ValueError("artifact reference is invalid")
        return path


__all__ = ["LocalArtifactStore"]
