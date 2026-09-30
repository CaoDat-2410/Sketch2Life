"""Lightning adapters for the story-video provider boundary.

The Lightning service owns model weights and private provider jobs. This module
only sends versioned references and validates the typed result returned by that
service; it never turns a missing artifact into a success.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from sketch2life.application.services.story_video_pipeline import StoryVideoProviderError
from sketch2life.contracts.schemas.story_video_media import (
    IllustrationAssetV1,
    IllustrationImageRequestV1,
    NarrationAssetV1,
    NarrationRenderRequestV1,
    VideoArtifactV1,
    VideoAssemblyRequestV1,
    VideoSceneArtifactV1,
    VideoSceneRenderRequestV1,
)
from sketch2life.infrastructure.ai.lightning_client import JsonTransport


def _post(transport: JsonTransport, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = transport.post_json(path, payload)
    except Exception as error:  # transport normalizes provider failures at this boundary
        raise StoryVideoProviderError("PROVIDER_ERROR", retryable=True) from error
    return dict(raw)


def _validated(model: type[Any], raw: dict[str, Any]) -> Any:
    try:
        return model.model_validate(raw)
    except (TypeError, ValueError, ValidationError) as error:
        raise StoryVideoProviderError("MALFORMED_OUTPUT", retryable=False) from error


@dataclass(frozen=True, slots=True)
class LightningStoryVideoAdapter:
    transport: JsonTransport
    narration_path: str = "/v1/story-video/narration"
    illustration_path: str = "/v1/story-video/illustration"
    motion_path: str = "/v1/story-video/scene"
    assembly_path: str = "/v1/story-video/assembly"

    def render_narration(
        self, request: NarrationRenderRequestV1, texts: tuple[str, ...]
    ) -> NarrationAssetV1:
        raw = _post(
            self.transport,
            self.narration_path,
            {"request": request.model_dump(mode="json"), "texts": texts},
        )
        return _validated(NarrationAssetV1, raw)

    def render_illustration(self, request: IllustrationImageRequestV1) -> IllustrationAssetV1:
        raw = _post(
            self.transport,
            self.illustration_path,
            {"request": request.model_dump(mode="json")},
        )
        return _validated(IllustrationAssetV1, raw)

    def render_scene(self, request: VideoSceneRenderRequestV1) -> VideoSceneArtifactV1:
        raw = _post(
            self.transport,
            self.motion_path,
            {"request": request.model_dump(mode="json")},
        )
        return _validated(VideoSceneArtifactV1, raw)

    def assemble(self, request: VideoAssemblyRequestV1) -> VideoArtifactV1:
        raw = _post(
            self.transport,
            self.assembly_path,
            {"request": request.model_dump(mode="json")},
        )
        return _validated(VideoArtifactV1, raw)


@dataclass(frozen=True, slots=True)
class LightningNarrationProvider:
    adapter: LightningStoryVideoAdapter

    def render(self, request: NarrationRenderRequestV1, texts: tuple[str, ...]) -> NarrationAssetV1:
        return self.adapter.render_narration(request, texts)


@dataclass(frozen=True, slots=True)
class LightningIllustrationProvider:
    adapter: LightningStoryVideoAdapter

    def render(self, request: IllustrationImageRequestV1) -> IllustrationAssetV1:
        return self.adapter.render_illustration(request)


@dataclass(frozen=True, slots=True)
class LightningMotionProvider:
    adapter: LightningStoryVideoAdapter

    def render(self, request: VideoSceneRenderRequestV1) -> VideoSceneArtifactV1:
        return self.adapter.render_scene(request)


@dataclass(frozen=True, slots=True)
class LightningVideoAssembler:
    adapter: LightningStoryVideoAdapter

    def assemble(self, request: VideoAssemblyRequestV1) -> VideoArtifactV1:
        return self.adapter.assemble(request)


__all__ = [
    "LightningIllustrationProvider",
    "LightningMotionProvider",
    "LightningNarrationProvider",
    "LightningStoryVideoAdapter",
    "LightningVideoAssembler",
]
