"""Fail-closed ClamAV daemon scanner for an exact immutable upload snapshot."""

from __future__ import annotations

import hashlib
import socket
import struct
from datetime import UTC, datetime

from sketch2life.application.ports.story_run_lite import ImageSafetyScannerPort, ScanVerdict


class ScannerUnavailable(RuntimeError):
    """ClamAV could not scan the exact requested bytes; do not parse or dispatch them."""


class ClamAvScanner(ImageSafetyScannerPort):
    def __init__(self, *, host: str | None, port: int = 3310, timeout_seconds: float = 8.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout_seconds

    def scan(self, snapshot: bytes, sha256: str) -> ScanVerdict:
        digest = hashlib.sha256(snapshot).hexdigest()
        if digest != sha256:
            raise ScannerUnavailable("quarantine digest changed before scanner admission")
        if not self._host:
            raise ScannerUnavailable("ClamAV is not configured")
        version: str | None = None
        try:
            with socket.create_connection(
                (self._host, self._port), timeout=self._timeout
            ) as connection:
                connection.settimeout(self._timeout)
                connection.sendall(b"zVERSION\0")
                version = _receive_z(connection)
            if not version or "ERROR" in version.upper():
                raise ScannerUnavailable("ClamAV version handshake failed")
            with socket.create_connection(
                (self._host, self._port), timeout=self._timeout
            ) as connection:
                connection.settimeout(self._timeout)
                connection.sendall(b"zINSTREAM\0")
                for offset in range(0, len(snapshot), 64 * 1024):
                    chunk = snapshot[offset : offset + 64 * 1024]
                    connection.sendall(struct.pack("!I", len(chunk)))
                    connection.sendall(chunk)
                connection.sendall(struct.pack("!I", 0))
                response = _receive_z(connection)
        except (OSError, TimeoutError, ScannerUnavailable):
            raise ScannerUnavailable("ClamAV did not complete the scan") from None
        if response.endswith(": OK"):
            return ScanVerdict("CLEAN", digest, version, datetime.now(UTC))
        if response.endswith("FOUND"):
            return ScanVerdict("INFECTED", digest, version, datetime.now(UTC), "CLAMAV_FOUND")
        if response.endswith("ERROR") or "ERROR" in response:
            raise ScannerUnavailable("ClamAV returned an error")
        raise ScannerUnavailable("ClamAV returned an unrecognized verdict")


def _receive_z(connection: socket.socket, *, limit: int = 2048) -> str:
    chunks = bytearray()
    while len(chunks) <= limit:
        byte = connection.recv(1)
        if not byte:
            break
        if byte == b"\0":
            return chunks.decode("utf-8", errors="replace").strip()
        chunks.extend(byte)
    if len(chunks) > limit:
        raise ScannerUnavailable("ClamAV response exceeded its limit")
    return chunks.decode("utf-8", errors="replace").strip()


__all__ = ["ClamAvScanner", "ScannerUnavailable"]
