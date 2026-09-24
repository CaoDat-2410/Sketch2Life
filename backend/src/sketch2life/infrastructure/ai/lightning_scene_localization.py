"""Backend-only Qwen/Lightning adapter for bounded drawing localization."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Callable, Mapping

from sketch2life.application.ports.scene_localization import SceneLocalizationRequest
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)


class LightningSceneLocalizationAdapter:
    """Return only regions for the already-confirmed candidate ids.

    Provider output is deliberately kept smaller than the public renderer contract. The
    application layer remains the single validator through ``build_scene_focus_plan``.
    """

    def __init__(
        self,
        *,
        transport: JsonTransport,
        artifact_loader: Callable[[str], bytes],
        endpoint_path: str = "/v2/localize",
        max_input_bytes: int = 5_000_000,
    ) -> None:
        self._transport = transport
        self._artifact_loader = artifact_loader
        self._endpoint_path = endpoint_path
        self._max_input_bytes = max_input_bytes

    def localize(
        self, request: SceneLocalizationRequest
    ) -> Mapping[str, Mapping[str, float]] | None:
        try:
            image = self._artifact_loader(request.source_artifact_ref)
            if not image or len(image) > self._max_input_bytes:
                return None
            digest = hashlib.sha256(image).hexdigest()
            if digest != request.source_artifact_sha256:
                return None
            raw = self._transport.post_json(
                self._endpoint_path,
                {
                    "contract_name": "SceneLocalizationRequestV1",
                    "contract_version": "1.0",
                    "session_id": request.session_id,
                    "experience_spec_ref": (
                        request.experience_spec_ref.model_dump(mode="json")
                        if request.experience_spec_ref is not None
                        else None
                    ),
                    "source_image": {
                        "artifact_ref": request.source_artifact_ref,
                        "sha256": digest,
                        "content_base64": base64.b64encode(image).decode("ascii"),
                    },
                    "targets": list(request.target_refs),
                    "target_labels": {
                        ref: request.target_labels[ref]
                        for ref in request.target_refs
                        if ref in request.target_labels
                    },
                },
            )
            values = raw.get("regions")
            if not isinstance(values, list):
                return None
            allowed = set(request.target_refs)
            result: dict[str, Mapping[str, float]] = {}
            for item in values:
                if not isinstance(item, dict):
                    return None
                target_ref = item.get("target_ref")
                region = item.get("region")
                if not isinstance(target_ref, str) or target_ref not in allowed:
                    return None
                if not isinstance(region, dict) or target_ref in result:
                    return None
                values_only = {
                    key: region.get(key)
                    for key in ("x", "y", "width", "height")
                }
                if not all(isinstance(value, (int, float)) for value in values_only.values()):
                    return None
                result[target_ref] = {key: float(value) for key, value in values_only.items()}
            return result or None
        except (KeyError, LightningProviderError, TimeoutError, TypeError, ValueError, OSError):
            return None


__all__ = ["LightningSceneLocalizationAdapter"]
