"""Deterministic S1 Vision double. It never calls an adapter or provider."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable

from sketch2life.application.ports.story_run_lite import (
    AssetBinding,
    StoryRunLiteVisionPort,
    ValidatedVisionResult,
    VisionAttemptResult,
)


class FakeStoryRunLiteVision(StoryRunLiteVisionPort):
    """Return a visibly synthetic result for S1 contract and workflow verification."""

    def analyze(
        self,
        *,
        run_id: str,
        binding: AssetBinding,
        persist_success: Callable[[ValidatedVisionResult], bool],
    ) -> VisionAttemptResult:
        snapshot: dict[str, object] = {
            "contract_name": "FakeStoryRunLiteResultV1",
            "status": "SUCCEEDED",
            "run_ref": run_id,
            "derived_asset_sha256": binding.sha256,
            "subject_label": "Synthetic artwork",
            "confidence": 0.0,
            "is_fake": True,
        }
        document = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        result = ValidatedVisionResult(
            result_snapshot=snapshot,
            subject_label="Synthetic artwork",
            confidence=0.0,
            canonical_result_sha256=hashlib.sha256(document).hexdigest(),
            raw_body_sha256=None,
        )
        committed = persist_success(result)
        return VisionAttemptResult(
            state="SUCCEEDED" if committed else "FAILED",
            error_code=None if committed else "VISION_ATTEMPT_HOLD",
            provider_invoked=False,
            result_committed=committed,
        )


__all__ = ["FakeStoryRunLiteVision"]
