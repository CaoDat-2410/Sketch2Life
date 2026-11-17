"""Private, bounded local quarantine and immutable synthetic asset snapshots."""

from __future__ import annotations

import hashlib
import os
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import cast
from uuid import UUID

from sketch2life.domain.story_run_lite import MAX_PART_BYTES, MAX_PARTS, MAX_UPLOAD_BYTES


class QuarantineError(Exception):
    """A local staging object is missing, inconsistent, or outside its bound."""


class QuarantineStore:
    """Store opaque keys below one configured root; callers never supply a filesystem path."""

    def __init__(self, root: Path) -> None:
        self._root = root.expanduser().resolve()
        self._parts = self._root / "parts"
        self._snapshots = self._root / "snapshots"
        self._assets = self._root / "assets"
        for directory in (self._parts, self._snapshots, self._assets):
            directory.mkdir(parents=True, exist_ok=True)

    def write_part(self, upload_id: str, part_number: int, payload: bytes) -> tuple[str, int]:
        self._uuid(upload_id)
        if not 1 <= part_number <= MAX_PARTS or not 1 <= len(payload) <= MAX_PART_BYTES:
            raise QuarantineError("part is outside the advertised bounds")
        directory = self._parts / upload_id
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"part-{part_number:02d}.bin"
        self._atomic_write(target, payload)
        return hashlib.sha256(payload).hexdigest(), len(payload)

    def read_part(
        self, upload_id: str, part_number: int, expected_digest: str, expected_size: int
    ) -> bytes:
        self._uuid(upload_id)
        path = self._parts / upload_id / f"part-{part_number:02d}.bin"
        try:
            data = path.read_bytes()
        except OSError:
            raise QuarantineError("an upload part is unavailable") from None
        if len(data) != expected_size or hashlib.sha256(data).hexdigest() != expected_digest:
            raise QuarantineError("an immutable upload part no longer matches its receipt")
        return data

    def assemble_snapshot(
        self,
        upload_id: str,
        part_rows: list[dict[str, object]],
        *,
        expected_size: int,
        expected_sha256: str,
    ) -> tuple[Path, bytes]:
        self._uuid(upload_id)
        if not 1 <= len(part_rows) <= MAX_PARTS or expected_size > MAX_UPLOAD_BYTES:
            raise QuarantineError("aggregate upload is outside its advertised bounds")
        ordered = sorted(
            part_rows, key=lambda row: int(cast(int, row["part_number"]))
        )
        if [int(cast(int, row["part_number"])) for row in ordered] != list(
            range(1, len(ordered) + 1)
        ):
            raise QuarantineError("upload parts must be contiguous from part one")
        digest = hashlib.sha256()
        target = self._snapshots / f"{upload_id}.bin"
        fd, temporary_name = tempfile.mkstemp(
            prefix=f"{upload_id}-", suffix=".tmp", dir=self._snapshots
        )
        total = 0
        try:
            with os.fdopen(fd, "wb") as output:
                for row in ordered:
                    part_no = int(cast(int, row["part_number"]))
                    payload = self.read_part(
                        upload_id,
                        part_no,
                        str(row["sha256"]),
                        int(cast(int, row["byte_size"])),
                    )
                    total += len(payload)
                    if total > MAX_UPLOAD_BYTES:
                        raise QuarantineError("aggregate upload exceeds the advertised maximum")
                    output.write(payload)
                    digest.update(payload)
                output.flush()
                os.fsync(output.fileno())
            if total != expected_size or digest.hexdigest() != expected_sha256:
                raise QuarantineError("aggregate size or SHA-256 does not match the request")
            os.replace(temporary_name, target)
        except BaseException:
            with suppress(OSError):
                os.unlink(temporary_name)
            raise
        # The scanner and decoder receive these exact bytes; the path is not reopened by an
        # untrusted caller. The worker re-hashes before parsing as a second snapshot check.
        try:
            snapshot = target.read_bytes()
        except OSError:
            raise QuarantineError("the completed quarantine snapshot is unavailable") from None
        if len(snapshot) != total or hashlib.sha256(snapshot).hexdigest() != expected_sha256:
            raise QuarantineError("the quarantine snapshot changed after assembly")
        return target, snapshot

    def snapshot_path(self, upload_id: str) -> Path:
        self._uuid(upload_id)
        path = self._snapshots / f"{upload_id}.bin"
        if not path.is_file():
            raise QuarantineError("the completed quarantine snapshot is unavailable")
        return path

    def store_asset(self, asset_ref: str, payload: bytes) -> str:
        self._uuid(asset_ref)
        key = f"{asset_ref}.bin"
        target = self._assets / key
        self._atomic_write(target, payload)
        return key

    def read_asset(self, asset_ref: str, *, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
        self._uuid(asset_ref)
        path = self._assets / f"{asset_ref}.bin"
        try:
            size = path.stat().st_size
            if size < 1 or size > max_bytes:
                raise QuarantineError("stored asset is outside its byte limit")
            data = path.read_bytes()
        except OSError:
            raise QuarantineError("stored asset is unavailable") from None
        if len(data) != size:
            raise QuarantineError("stored asset changed while reading")
        return data

    def delete_asset(self, asset_ref: str) -> None:
        self._uuid(asset_ref)
        try:
            (self._assets / f"{asset_ref}.bin").unlink(missing_ok=True)
        except OSError:
            raise QuarantineError("stored asset could not be removed") from None

    def remove_upload(self, upload_id: str) -> None:
        self._uuid(upload_id)
        for path in (
            self._parts / upload_id,
            self._snapshots / f"{upload_id}.bin",
        ):
            if path.is_dir():
                for child in path.iterdir():
                    if child.is_file():
                        child.unlink(missing_ok=True)
                path.rmdir()
            else:
                path.unlink(missing_ok=True)

    def _atomic_write(self, target: Path, payload: bytes) -> None:
        fd, temporary_name = tempfile.mkstemp(
            prefix=target.stem + "-", suffix=".tmp", dir=target.parent
        )
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary_name, target)
        except BaseException:
            with suppress(OSError):
                os.unlink(temporary_name)
            raise

    @staticmethod
    def _uuid(value: str) -> None:
        try:
            UUID(value)
        except (ValueError, TypeError, AttributeError):
            raise QuarantineError("resource reference is invalid") from None


__all__ = ["QuarantineError", "QuarantineStore"]
