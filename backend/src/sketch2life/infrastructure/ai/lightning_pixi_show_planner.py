"""Single-attempt Lightning adapter for the bounded post-Gate-B show planner."""

from __future__ import annotations

import base64
from hashlib import sha256
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from sketch2life.application.ports.pixi_show_planner import (
    PixiShowPlannerPort,
    PixiShowPlannerUnavailable,
    PixiShowPlanningRequest,
)
from sketch2life.contracts.schemas.pixi_show import (
    PixiShowIntentV1,
    PixiShowPlannerAssetCandidateV1,
    PixiShowPlannerRequestV1,
)
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)

_MAX_CROP_BYTES = 1_000_000
_RESULT_ADAPTER: TypeAdapter[PixiShowIntentV1] = TypeAdapter(PixiShowIntentV1)


class LightningPixiShowPlanner(PixiShowPlannerPort):
    """Transmit one minimized crop and a bounded candidate set; never sends child/session IDs."""

    def __init__(
        self,
        *,
        transport: JsonTransport,
        endpoint_path: str = "/v2/pixi/show-plan",
    ) -> None:
        if not endpoint_path.startswith("/"):
            raise ValueError("Pixi show planner path must be absolute")
        self._transport = transport
        self._endpoint_path = endpoint_path

    def plan(self, request: PixiShowPlanningRequest) -> PixiShowIntentV1:
        crop = request.source_crop_bytes
        if not crop or len(crop) > _MAX_CROP_BYTES:
            raise PixiShowPlannerUnavailable("SUBJECT_CROP_UNAVAILABLE")
        if not _has_matching_signature(crop, request.source_crop_content_type):
            raise PixiShowPlannerUnavailable("SUBJECT_CROP_UNAVAILABLE")

        candidates = tuple(
            PixiShowPlannerAssetCandidateV1(
                assetId=item.asset_id,
                label=item.label,
                role=item.role,
                visualDescription=item.visual_description,
                topicTags=item.topic_tags[:12],
            )
            for item in request.candidate_assets[:6]
        )
        if not candidates:
            raise PixiShowPlannerUnavailable("NO_ELIGIBLE_ASSETS")
        if len({item.asset_id for item in candidates}) != len(candidates):
            raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")

        body = PixiShowPlannerRequestV1(
            contractName="PixiShowPlannerRequestV1",
            contractVersion="1.0",
            requestId=str(uuid4()),
            sourceCrop={
                "contentType": request.source_crop_content_type,
                "sha256": sha256(crop).hexdigest(),
                "contentBase64": base64.b64encode(crop).decode("ascii"),
            },
            sourceSubjectRegion=request.subject_region,
            rendererDurationSeconds=request.renderer_duration_seconds,
            confirmedSubjectLabel=request.confirmed_subject_label[:160],
            subjectTags=request.subject_tags[:20],
            activityId=request.activity_id[:120],
            activityLabel=request.activity_label[:160],
            objectiveIds=request.objective_ids[:3],
            objectiveLabels=request.objective_labels[:3],
            rigTier=request.rig_tier,
            partRoles=request.part_roles[:8],
            candidateAssets=candidates,
        )
        try:
            raw = self._transport.post_json(
                self._endpoint_path,
                body.model_dump(mode="json", by_alias=True),
            )
        except TimeoutError:
            raise PixiShowPlannerUnavailable("PLANNER_TIMEOUT") from None
        except LightningProviderError as error:
            if error.code == "ENDPOINT_NOT_FOUND":
                raise PixiShowPlannerUnavailable("PLANNER_UNAVAILABLE") from None
            raise PixiShowPlannerUnavailable("PLANNER_UNAVAILABLE") from None
        except OSError:
            raise PixiShowPlannerUnavailable("PLANNER_UNAVAILABLE") from None

        try:
            intent = _RESULT_ADAPTER.validate_python(raw)
        except ValidationError:
            raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT") from None
        allowed_ids = {item.asset_id for item in candidates}
        if not set(intent.selected_asset_ids) <= allowed_ids:
            raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
        return intent


def _has_matching_signature(image: bytes, content_type: str) -> bool:
    if content_type == "image/png":
        return image.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return image.startswith(b"\xff\xd8\xff")
    return False


__all__ = ["LightningPixiShowPlanner"]
