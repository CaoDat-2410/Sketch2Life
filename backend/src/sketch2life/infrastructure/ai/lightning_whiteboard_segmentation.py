"""Lightning adapter that transfers validated SAM2 masks into backend storage."""

from __future__ import annotations

import base64
import binascii
import hashlib
from collections.abc import Callable, Mapping
from typing import Any

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.application.services.whiteboard_video_pipeline import (
    LocalizedRegionBatch,
    MaskBatch,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)


class LightningWhiteboardSegmentationAdapter:
    """Call SAM2 remotely and persist returned masks through an injected sink."""

    def __init__(
        self,
        *,
        transport: JsonTransport,
        artifact_loader: Callable[[str], bytes],
        artifact_sink: Callable[[str, bytes], str],
        endpoint_path: str = "/v1/whiteboard/segment",
        max_input_bytes: int = 5_000_000,
        max_mask_bytes: int = 5_000_000,
    ) -> None:
        if not endpoint_path.startswith("/"):
            raise ValueError("segmentation endpoint path must be absolute")
        self._transport = transport
        self._artifact_loader = artifact_loader
        self._artifact_sink = artifact_sink
        self._endpoint_path = endpoint_path
        self._max_input_bytes = max_input_bytes
        self._max_mask_bytes = max_mask_bytes

    def segment(
        self,
        job: WhiteboardVideoJobV1,
        regions: LocalizedRegionBatch,
    ) -> MaskBatch:
        try:
            image = self._artifact_loader(job.source_artifact_id)
            if not image or len(image) > self._max_input_bytes:
                raise ValueError("source image is invalid")
            if hashlib.sha256(image).hexdigest() != job.source_hash:
                raise ValueError("source hash mismatch")
            raw = self._transport.post_json(
                self._endpoint_path,
                {
                    "contract_name": "WhiteboardSegmentationRequestV1",
                    "contract_version": "1.0",
                    "job_id": job.job_id,
                    "source_hash": job.source_hash,
                    "region_refs": list(regions.region_refs),
                    "source_image": {
                        "artifact_ref": job.source_artifact_id,
                        "sha256": job.source_hash,
                        "content_base64": base64.b64encode(image).decode("ascii"),
                    },
                },
            )
            return self._parse_response(raw, job, regions)
        except TimeoutError as error:
            raise WhiteboardVideoPipelineError("SEGMENTATION_TIMEOUT", retryable=True) from error
        except LightningProviderError as error:
            raise WhiteboardVideoPipelineError(error.code, retryable=error.retryable) from error
        except (KeyError, TypeError, ValueError) as error:
            code = "SOURCE_HASH_MISMATCH" if "hash" in str(error) else "SEGMENTATION_SCHEMA_INVALID"
            raise WhiteboardVideoPipelineError(code, retryable=False) from error

    def _parse_response(
        self,
        raw: Mapping[str, Any],
        job: WhiteboardVideoJobV1,
        regions: LocalizedRegionBatch,
    ) -> MaskBatch:
        if raw.get("source_hash") != job.source_hash:
            raise ValueError("source hash mismatch")
        masks = raw.get("masks")
        if not isinstance(masks, list) or len(masks) != len(regions.region_refs):
            raise ValueError("segmentation response must contain one mask per region")
        refs: list[str] = []
        for item in masks:
            if not isinstance(item, dict):
                raise TypeError("mask item must be an object")
            ref = item.get("mask_ref")
            encoded = item.get("content_base64")
            if not isinstance(ref, str) or not ref or not isinstance(encoded, str):
                raise ValueError("mask item shape is invalid")
            try:
                content = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as error:
                raise ValueError("mask content is not valid base64") from error
            if not content or len(content) > self._max_mask_bytes:
                raise ValueError("mask artifact exceeds the size limit")
            if not content.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("mask artifact must be PNG")
            refs.append(self._artifact_sink(ref, content))
        return MaskBatch(source_hash=job.source_hash, mask_refs=tuple(refs))


__all__ = ["LightningWhiteboardSegmentationAdapter"]
