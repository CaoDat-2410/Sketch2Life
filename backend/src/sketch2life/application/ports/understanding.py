"""Application ports for provider-neutral multimodal understanding."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.understanding import (
    AsrRequestV1,
    AsrResultV1,
    VisionRequestV1,
    VisionUnderstandingResultV1,
)


class AsrPort(Protocol):
    def transcribe(self, request: AsrRequestV1) -> AsrResultV1: ...


class VisionUnderstandingPort(Protocol):
    def understand(self, request: VisionRequestV1) -> VisionUnderstandingResultV1: ...
