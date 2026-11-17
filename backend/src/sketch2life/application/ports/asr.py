"""Provider-neutral ASR boundary for the standalone understanding component."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.asr import AsrRequestV1, AsrResultV1


class AsrPort(Protocol):
    """Returns only validated local contracts; provider SDK types never cross this port."""

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1: ...
