"""Provider-neutral FEAT-018 semantic handoff boundary."""

from __future__ import annotations

from typing import Protocol

from sketch2life.contracts.schemas.asr import AsrResultV1
from sketch2life.contracts.schemas.raw_understanding import RawUnderstandingResultV1
from sketch2life.contracts.schemas.vision_v2 import VisionUnderstandingResultV2


class RawUnderstandingMapperPort(Protocol):
    """Map typed upstream observations without owning model execution."""

    def map(
        self,
        result: VisionUnderstandingResultV2,
        *,
        session_id: str,
        expected_source_sha256: str,
        expected_correlation_id: str,
        asr_result: AsrResultV1 | None = None,
    ) -> RawUnderstandingResultV1: ...
