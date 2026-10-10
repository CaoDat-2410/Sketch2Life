"""Lightning adapter for the first whiteboard stage: source localization."""

from __future__ import annotations

import base64
import hashlib
import logging
from collections.abc import Callable, Mapping
from typing import Any

from sketch2life.application.services.whiteboard_video_pipeline import (
    LocalizedRegionBatch,
    WhiteboardVideoStageError,
)
from sketch2life.application.services.whiteboard_video_job import WhiteboardVideoPipelineError
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)

_LOGGER = logging.getLogger("sketch2life.lightning_whiteboard")


class LightningWhiteboardLocalizationAdapter:
    """Call a backend-owned Lightning localization endpoint with strict output checks.

    The provider endpoint is intentionally configurable. Lightning receives the source image
    only through this backend adapter; the mobile client never receives the provider token.
    """

    def __init__(
        self,
        *,
        transport: JsonTransport,
        artifact_loader: Callable[[str], bytes],
        endpoint_path: str = "/v1/whiteboard/localize",
        max_input_bytes: int = 5_000_000,
        minimum_confidence: float = 0.75,
    ) -> None:
        if not endpoint_path.startswith("/"):
            raise ValueError("Lightning whiteboard endpoint path must be absolute")
        if not 1 <= max_input_bytes <= 5_000_000:
            raise ValueError("whiteboard localization input limit must be between 1 and 5 MB")
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum localization confidence must be between 0 and 1")
        self._transport = transport
        self._artifact_loader = artifact_loader
        self._endpoint_path = endpoint_path
        self._max_input_bytes = max_input_bytes
        self._minimum_confidence = minimum_confidence

    def localize(self, job: WhiteboardVideoJobV1) -> LocalizedRegionBatch:
        try:
            image = self._artifact_loader(job.source_artifact_id)
            if not image or len(image) > self._max_input_bytes:
                raise WhiteboardVideoStageError("SOURCE_IMAGE_INVALID", retryable=False)
            digest = hashlib.sha256(image).hexdigest()
            if digest != job.source_hash:
                raise WhiteboardVideoStageError("SOURCE_HASH_MISMATCH", retryable=False)
            content_type = _image_content_type(image)
            if content_type is None:
                raise WhiteboardVideoStageError("SOURCE_IMAGE_INVALID", retryable=False)

            raw = self._transport.post_json(
                self._endpoint_path,
                {
                    "contract_name": "WhiteboardLocalizationRequestV1",
                    "contract_version": "1.0",
                    "job_id": job.job_id,
                    "experience_spec_id": job.experience_spec_id,
                    "source_artifact_id": job.source_artifact_id,
                    "source_hash": job.source_hash,
                    "source_image": {
                        "artifact_ref": job.source_artifact_id,
                        "sha256": job.source_hash,
                        "content_type": content_type,
                        "content_base64": base64.b64encode(image).decode("ascii"),
                    },
                },
            )
            return _parse_localization(raw, job.source_hash, self._minimum_confidence)
        except WhiteboardVideoStageError as error:
            raise WhiteboardVideoPipelineError(error.args[0], retryable=False) from error
        except TimeoutError as error:
            raise WhiteboardVideoPipelineError("LOCALIZATION_TIMEOUT", retryable=True) from error
        except LightningProviderError as error:
            raise WhiteboardVideoPipelineError(error.code, retryable=error.retryable) from error
        except (KeyError, TypeError, ValueError) as error:
            _LOGGER.error(
                "whiteboard_localization_adapter_rejected error_type=%s reason=%s",
                type(error).__name__,
                str(error),
            )
            raise WhiteboardVideoPipelineError("LOCALIZATION_SCHEMA_INVALID", retryable=False) from error


def _parse_localization(
    raw: Mapping[str, Any], source_hash: str, minimum_confidence: float
) -> LocalizedRegionBatch:
    if raw.get("source_hash") != source_hash:
        raise WhiteboardVideoStageError("SOURCE_HASH_MISMATCH", retryable=False)
    regions = raw.get("regions")
    if not isinstance(regions, list) or not regions:
        raise ValueError("localization response must contain at least one region")
    refs: list[str] = []
    for region in regions:
        if not isinstance(region, dict):
            raise TypeError("localization region must be an object")
        ref = region.get("region_ref")
        confidence = region.get("confidence")
        if not isinstance(ref, str) or not ref or not isinstance(confidence, (int, float)):
            raise ValueError("localization region shape is invalid")
        if confidence < minimum_confidence:
            raise ValueError("localization confidence is below the acceptance threshold")
        refs.append(ref)
    return LocalizedRegionBatch(source_hash=source_hash, region_refs=tuple(refs))


def _image_content_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


__all__ = ["LightningWhiteboardLocalizationAdapter"]
