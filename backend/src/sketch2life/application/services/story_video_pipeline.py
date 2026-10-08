"""Orchestration boundary for an approved illustrated story video."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from sketch2life.application.services.story_video_planner import (
    StoryboardCompileInput,
    StoryVideoPlanner,
)
from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryboardPlanV1,
    StoryScriptSegmentV1,
    stable_model_hash,
    story_script_segments_hash,
)
from sketch2life.contracts.schemas.story_video_media import (
    IllustrationAssetV1,
    IllustrationImageRequestV1,
    NarrationAssetV1,
    NarrationRenderRequestV1,
    SubtitleCueV1,
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
        motion_model_profile_ref: str = "whiteboard-stroke-v1",
        update_stage: Callable[[str, int], None] | None = None,
    ) -> None:
        self._narration = narration
        self._illustrations = illustrations
        self._motion = motion
        self._assembler = assembler
        self._planner = planner or StoryVideoPlanner()
        if motion_model_profile_ref not in {"whiteboard-stroke-v1", "wan2.2-ti2v-5b"}:
            raise ValueError("unsupported story motion profile")
        self._motion_model_profile_ref = motion_model_profile_ref
        self._update_stage = update_stage or (lambda _stage, _progress: None)

    def run(
        self,
        package: ApprovedStoryPackageV1,
        segments: tuple[StoryScriptSegmentV1, ...],
        *,
        update_stage: Callable[[str, int], None] | None = None,
    ) -> StoryVideoRun:
        update = update_stage or self._update_stage
        update("NARRATION_RENDERING", 10)
        texts = tuple(segment.text for segment in segments)
        narration_request = NarrationRenderRequestV1(
            request_id=f"narration-{package.package_id}",
            idempotency_key=f"narration-{package.package_hash}",
            package_id=package.package_id,
            package_hash=package.package_hash,
            locale=package.locale,
            narration_profile_ref=package.narration_profile_ref,
            segment_ids=tuple(segment.segment_id for segment in segments),
            approved_text_hash=story_script_segments_hash(segments),
        )
        narration = self._narration.render(narration_request, texts)
        self._require_ready(narration.status, "NARRATION_NOT_READY", narration.error_code)
        if (
            not narration.audio_ref
            or not narration.audio_sha256
            or narration.duration_seconds is None
        ):
            raise StoryVideoProviderError("NARRATION_ARTIFACT_INVALID", retryable=False)
        if len(narration.segment_timing_seconds) != len(segments):
            raise StoryVideoProviderError("NARRATION_TIMING_MISMATCH", retryable=False)
        if abs(sum(narration.segment_timing_seconds) - narration.duration_seconds) > 0.25:
            raise StoryVideoProviderError("NARRATION_TIMING_MISMATCH", retryable=False)

        try:
            storyboard = self._planner.compile(
                StoryboardCompileInput(package, segments, narration.segment_timing_seconds)
            )
        except ValueError as error:
            raise StoryVideoProviderError("STORYBOARD_INVALID", retryable=False) from error
        if self._motion_model_profile_ref == "whiteboard-stroke-v1" and any(
            scene.duration_seconds < 5.0 for scene in storyboard.scenes
        ):
            raise StoryVideoProviderError("WHITEBOARD_SCENE_TOO_SHORT", retryable=False)
        update("ILLUSTRATIONS_RENDERING", 30)
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
        if tuple(asset.scene_id for asset in illustrations) != tuple(
            scene.scene_id for scene in storyboard.scenes
        ):
            raise StoryVideoProviderError("ILLUSTRATION_SCENE_MISMATCH", retryable=False)
        if any(
            not asset.asset_ref
            or not asset.asset_sha256
            or asset.source_image_ref != package.source_image_ref
            or asset.source_image_sha256 != package.source_image_sha256
            for asset in illustrations
        ):
            raise StoryVideoProviderError("ILLUSTRATION_ARTIFACT_INVALID", retryable=False)

        update("SCENES_RENDERING", 55)
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
                    model_profile_ref=self._motion_model_profile_ref,
                    duration_seconds=scene.duration_seconds,
                    resource_preflight="PASSED",
                )
            )
            for scene, illustration in zip(storyboard.scenes, illustrations, strict=True)
        )
        if any(scene.status != "READY" for scene in scenes):
            raise StoryVideoProviderError("SCENE_RENDER_NOT_READY", retryable=True)
        if tuple(scene.scene_id for scene in scenes) != tuple(
            scene.scene_id for scene in storyboard.scenes
        ):
            raise StoryVideoProviderError("VIDEO_SCENE_MISMATCH", retryable=False)
        if any(
            not scene.silent_clip_ref
            or not scene.silent_clip_sha256
            or scene.model_profile_ref != self._motion_model_profile_ref
            for scene in scenes
        ):
            raise StoryVideoProviderError("VIDEO_SCENE_ARTIFACT_INVALID", retryable=False)
        if any(
            rendered.duration_seconds is None
            or abs(rendered.duration_seconds - planned.duration_seconds) > 0.5
            for rendered, planned in zip(scenes, storyboard.scenes, strict=True)
        ):
            raise StoryVideoProviderError("VIDEO_SCENE_DURATION_MISMATCH", retryable=True)

        update("ASSEMBLING", 80)
        subtitle_cues = _subtitle_cues(storyboard)
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
                subtitle_cues=subtitle_cues,
                target_duration_min_seconds=package.target_duration_min_seconds,
                target_duration_max_seconds=package.target_duration_max_seconds,
            )
        )
        self._require_ready(video.status, "VIDEO_NOT_READY", video.error_code)
        if (
            not video.video_ref
            or not video.video_sha256
            or video.audio_ref != narration.audio_ref
        ):
            raise StoryVideoProviderError("VIDEO_ARTIFACT_INVALID", retryable=False)
        if video.duration_seconds is None or not (
            package.target_duration_min_seconds
            <= video.duration_seconds
            <= package.target_duration_max_seconds
        ):
            raise StoryVideoProviderError("VIDEO_DURATION_OUT_OF_RANGE", retryable=False)
        update("READY", 100)
        return StoryVideoRun(package, storyboard, narration, illustrations, scenes, video)

    @staticmethod
    def _require_ready(status: str, code: str, provider_code: str | None) -> None:
        if status != "READY":
            raise StoryVideoProviderError(
                provider_code or code, retryable=status == "RETRYABLE_FAILURE"
            )


def _subtitle_cues(storyboard: StoryboardPlanV1) -> tuple[SubtitleCueV1, ...]:
    """Build short, ordered cues from approved narration and measured scene timing."""

    cursor = 0.0
    cues: list[SubtitleCueV1] = []
    for scene in storyboard.scenes:
        chunks = _caption_chunks(scene.narration_text)
        if len(chunks) > 4:
            raise StoryVideoProviderError("SUBTITLE_TEXT_TOO_LONG", retryable=False)
        weights = [len(chunk.split()) for chunk in chunks]
        total_weight = sum(weights)
        elapsed = 0.0
        for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
            start = round(cursor + elapsed, 3)
            elapsed += scene.duration_seconds * weight / total_weight
            end = (
                round(cursor + scene.duration_seconds, 3)
                if index == len(chunks) - 1
                else round(cursor + elapsed, 3)
            )
            cues.append(SubtitleCueV1(text=chunk, start_seconds=start, end_seconds=end))
        cursor += scene.duration_seconds
    return tuple(cues)


def _caption_chunks(text: str, max_chars: int = 62) -> tuple[str, ...]:
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        if len(word) > max_chars:
            raise StoryVideoProviderError("SUBTITLE_WORD_TOO_LONG", retryable=False)
        if current and len(" ".join((*current, word))) > max_chars:
            chunks.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        chunks.append(" ".join(current))
    return tuple(chunks)


__all__ = ["StoryVideoPipeline", "StoryVideoProviderError", "StoryVideoRun"]
