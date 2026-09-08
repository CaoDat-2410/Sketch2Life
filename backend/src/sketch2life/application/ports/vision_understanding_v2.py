"""Provider-neutral V2 vision-understanding boundary for the Qwen study."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
)


class VisionUnderstandingPortV2(Protocol):
    """Interface only: filesystem and model-provider work stays in infrastructure."""

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingResultV2: ...
