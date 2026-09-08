"""Local transport contract used by fixture-only HTTP/job tests."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from .contracts import RuntimeRejected


@dataclass(frozen=True)
class TransportEnvelope:
    contract_name: str
    contract_version: str
    command_id: str
    session_id: str
    expected_session_version: int
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_name": self.contract_name,
            "contract_version": self.contract_version,
            "command_id": self.command_id,
            "session_id": self.session_id,
            "expected_session_version": self.expected_session_version,
            "payload": dict(self.payload),
        }


class LocalTransport:
    supported_versions: ClassVar[dict[str, str]] = {"RuntimeCommandV1": "1.0", "RuntimeResultV1": "1.0"}

    def accept(self, envelope: TransportEnvelope) -> dict[str, Any]:
        expected = self.supported_versions.get(envelope.contract_name)
        if expected is None or expected != envelope.contract_version:
            raise RuntimeRejected("UNSUPPORTED_CONTRACT_VERSION")
        if not envelope.command_id or not envelope.session_id:
            raise RuntimeRejected("TRANSPORT_ID_REQUIRED")
        return {
            "contract_name": "RuntimeResultV1",
            "contract_version": "1.0",
            "command_id": envelope.command_id,
            "session_id": envelope.session_id,
            "expected_session_version": envelope.expected_session_version,
            "status": "ACCEPTED",
            "payload": dict(envelope.payload),
        }

