"""ClamD INSTREAM adapter; failures are fail-closed for lesson uploads."""

from __future__ import annotations

import socket
import struct
from typing import BinaryIO

from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScanResult,
    MalwareScannerUnavailable,
)


class ClamAvScanner:
    def __init__(self, *, host: str | None, port: int = 3310, timeout_seconds: float = 30.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout_seconds

    def scan(self, file_obj: BinaryIO) -> MalwareScanResult:
        if not self._host:
            raise MalwareScannerUnavailable("malware scanner is not configured")
        try:
            with socket.create_connection((self._host, self._port), timeout=self._timeout) as client:
                client.settimeout(self._timeout)
                client.sendall(b"zINSTREAM\0")
                file_obj.seek(0)
                while chunk := file_obj.read(64 * 1024):
                    client.sendall(struct.pack("!I", len(chunk)))
                    client.sendall(chunk)
                client.sendall(b"\0\0\0\0")
                response = bytearray()
                while len(response) < 4096:
                    data = client.recv(512)
                    if not data:
                        break
                    response.extend(data)
                    if b"\0" in data or b"\n" in data:
                        break
        except (OSError, TimeoutError):
            raise MalwareScannerUnavailable("malware scanner is unavailable") from None
        finally:
            file_obj.seek(0)
        result = bytes(response).strip(b"\0\r\n").decode("ascii", errors="ignore")
        if result.endswith(": OK"):
            version = self._version()
            return MalwareScanResult(
                scanner_name="clamav-clamd-instream", scanner_version=version, verdict="CLEAN"
            )
        if result.endswith(" FOUND"):
            raise MalwareDetected("MALWARE_DETECTED")
        raise MalwareScannerUnavailable("malware scanner did not return a clean verdict")

    def _version(self) -> str:
        if not self._host:
            raise MalwareScannerUnavailable("malware scanner is not configured")
        try:
            with socket.create_connection((self._host, self._port), timeout=self._timeout) as client:
                client.settimeout(self._timeout)
                client.sendall(b"zVERSION\0")
                response = client.recv(512).strip(b"\0\r\n").decode("ascii", errors="ignore")
        except (OSError, TimeoutError):
            raise MalwareScannerUnavailable("malware scanner is unavailable") from None
        if not response or len(response) > 128:
            raise MalwareScannerUnavailable("malware scanner did not report its version")
        return response


__all__ = ["ClamAvScanner"]
