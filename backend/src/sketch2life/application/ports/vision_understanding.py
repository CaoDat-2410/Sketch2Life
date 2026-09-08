"""Provider-neutral vision-understanding boundary for the standalone component."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.vision import (
    VisionUnderstandingRequestV1,
    VisionUnderstandingResultV1,
)


class VisionUnderstandingPort(Protocol):
    """Interface only: no file, byte-reading, or hashing operation crosses this boundary."""

    def understand(self, request: VisionUnderstandingRequestV1) -> VisionUnderstandingResultV1: ...
