"""Orchestration boundary for an approved illustrated story video."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from sketch2life.application.services.story_video_planner import (
    StoryboardCompileInput,
    StoryVideoPlanner,
)
from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryboardPlanV1,
    StoryScriptSegmentV1,
    stable_model_hash,
)
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


class StoryVideoProviderError(RuntimeError):
    """Sanitized provider failure that is safe for job orchestration."""

    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class NarrationProvider(Protocol):
    def render(
        self, request: NarrationRenderRequestV1, texts: tuple[str, ...]
    ) -> NarrationAssetV1: ...


class IllustrationProvider(Protocol):
    def render(self, request: IllustrationImageRequestV1) -> IllustrationAssetV1: ...


class MotionProvider(Protocol):
    def render(self, request: VideoSceneRenderRequestV1) -> VideoSceneArtifactV1: ...


class VideoAssembler(Protocol):
    def assemble(self, request: VideoAssemblyRequestV1) -> VideoArtifactV1: ...


@dataclass(frozen=True)
class StoryVideoRun:
    package: ApprovedStoryPackageV1
    storyboard: StoryboardPlanV1
    narration: NarrationAssetV1
    illustrations: tuple[IllustrationAssetV1, ...]
    scenes: tuple[VideoSceneArtifactV1, ...]
    video: VideoArtifactV1


class StoryVideoPipeline:
    """Run the new flow in dependency order, with no provider SDK imports."""

    def __init__(
        self,
        *,
        narration: NarrationProvider,
        illustrations: IllustrationProvider,
        motion: MotionProvider,
        assembler: VideoAssembler,
        planner: StoryVideoPlanner | None = None,
        update_stage: Callable[[str, int], None] | None = None,
    ) -> None:
        self._narration = narration
        self._illustrations = illustrations
        self._motion = motion
        self._assembler = assembler
        self._planner = planner or StoryVideoPlanner()
        self._update_stage = update_stage or (lambda _stage, _progress: None)

    def run(
        self,
        package: ApprovedStoryPackageV1,
        segments: tuple[StoryScriptSegmentV1, ...],
    ) -> StoryVideoRun:
        self._update_stage("NARRATION_RENDERING", 10)
        texts = tuple(segment.text for segment in segments)
        narration_request = NarrationRenderRequestV1(
            request_id=f"narration-{package.package_id}",
            idempotency_key=f"narration-{package.package_hash}",
            package_id=package.package_id,
            package_hash=package.package_hash,
            locale=package.locale,
            narration_profile_ref=package.narration_profile_ref,
            segment_ids=tuple(segment.segment_id for segment in segments),
            approved_text_hash=stable_model_hash_wrapper(segments),
        )
        narration = self._narration.render(narration_request, texts)
        self._require_ready(narration.status, "NARRATION_NOT_READY", narration.error_code)
        if len(narration.segment_timing_seconds) != len(segments):
            raise StoryVideoProviderError("NARRATION_TIMING_MISMATCH", retryable=False)

        storyboard = self._planner.compile(
            StoryboardCompileInput(package, segments, narration.segment_timing_seconds)
        )
        self._update_stage("ILLUSTRATIONS_RENDERING", 30)
        illustrations = tuple(
            self._illustrations.render(
                IllustrationImageRequestV1(
                    request_id=f"illustration-{package.package_id}-{scene.scene_id}",
                    idempotency_key=f"illustration-{package.package_hash}-{scene.scene_id}",
                    package_id=package.package_id,
                    package_hash=package.package_hash,
                    scene_id=scene.scene_id,
                    source_image_ref=package.source_image_ref,
                    source_image_sha256=package.source_image_sha256,
                    visual_prompt=scene.visual_prompt,
                    style_profile_ref=package.audience_profile_ref,
                    safety_policy_version=package.content_validator_version,
                )
            )
            for scene in storyboard.scenes
        )
        if any(asset.status != "READY" for asset in illustrations):
            raise StoryVideoProviderError("ILLUSTRATION_NOT_READY", retryable=True)

        self._update_stage("SCENES_RENDERING", 55)
        scenes = tuple(
            self._motion.render(
                VideoSceneRenderRequestV1(
                    request_id=f"motion-{package.package_id}-{scene.scene_id}",
                    idempotency_key=f"motion-{package.package_hash}-{scene.scene_id}",
                    package_id=package.package_id,
                    package_hash=package.package_hash,
                    storyboard_id=storyboard.storyboard_id,
                    storyboard_hash=stable_model_hash(storyboard),
                    scene_id=scene.scene_id,
                    illustration_ref=illustration.asset_ref or "",
                    illustration_sha256=illustration.asset_sha256 or "0" * 64,
                    approved_fact_ids=scene.approved_fact_ids,
                    confirmed_anchor_ids=scene.confirmed_anchor_ids,
                    duration_seconds=scene.duration_seconds,
                    resource_preflight="PASSED",
                )
            )
            for scene, illustration in zip(storyboard.scenes, illustrations, strict=True)
        )
        if any(scene.status != "READY" for scene in scenes):
            raise StoryVideoProviderError("SCENE_RENDER_NOT_READY", retryable=True)

        self._update_stage("ASSEMBLING", 80)
        video = self._assembler.assemble(
            VideoAssemblyRequestV1(
                request_id=f"assembly-{package.package_id}",
                idempotency_key=f"assembly-{package.package_hash}",
                package_id=package.package_id,
                package_hash=package.package_hash,
                storyboard_id=storyboard.storyboard_id,
                scene_ids=tuple(scene.scene_id for scene in storyboard.scenes),
                scene_artifact_refs=tuple(scene.silent_clip_ref or "" for scene in scenes),
                narration_ref=narration.audio_ref or "",
                narration_sha256=narration.audio_sha256 or "0" * 64,
                target_duration_min_seconds=package.target_duration_min_seconds,
                target_duration_max_seconds=package.target_duration_max_seconds,
            )
        )
        self._require_ready(video.status, "VIDEO_NOT_READY", video.error_code)
        if video.duration_seconds is None or not (
            package.target_duration_min_seconds
            <= video.duration_seconds
            <= package.target_duration_max_seconds
        ):
            raise StoryVideoProviderError("VIDEO_DURATION_OUT_OF_RANGE", retryable=False)
        self._update_stage("READY", 100)
        return StoryVideoRun(package, storyboard, narration, illustrations, scenes, video)

    @staticmethod
    def _require_ready(status: str, code: str, provider_code: str | None) -> None:
        if status != "READY":
            raise StoryVideoProviderError(
                provider_code or code, retryable=status == "RETRYABLE_FAILURE"
            )


def stable_model_hash_wrapper(segments: tuple[StoryScriptSegmentV1, ...]) -> str:
    """Hash approved text inputs without exposing their content in provider IDs."""

    return stable_model_hash(_SegmentHashPayload(segments=segments))


class _SegmentHashPayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    segments: tuple[StoryScriptSegmentV1, ...]


__all__ = ["StoryVideoPipeline", "StoryVideoProviderError", "StoryVideoRun"]
