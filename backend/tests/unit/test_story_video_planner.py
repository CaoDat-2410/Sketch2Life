from sketch2life.application.services.story_video_pipeline import StoryVideoPipeline
from sketch2life.application.services.story_video_planner import (
    StoryboardCompileInput,
    StoryVideoPlanner,
)
from sketch2life.contracts.schemas.story_video import ApprovedStoryPackageV1, StoryScriptSegmentV1
from sketch2life.contracts.schemas.story_video_media import (
    IllustrationAssetV1,
    NarrationAssetV1,
    VideoArtifactV1,
    VideoSceneArtifactV1,
)


def _package() -> ApprovedStoryPackageV1:
    digest = "a" * 64
    return ApprovedStoryPackageV1(
        package_id="pkg-cat-001",
        session_id="session-001",
        session_version=3,
        source_image_ref="artifact:image-001",
        source_image_sha256=digest,
        confirmed_understanding_ref="understanding:001",
        confirmed_understanding_sha256=digest,
        experience_spec_ref="experience:001",
        experience_spec_sha256=digest,
        story_script_ref="script:001",
        story_script_revision=2,
        story_script_sha256=digest,
        audience_profile_ref="audience:early-primary",
        audience_profile_sha256=digest,
        evidence_set_ref="evidence:001",
        evidence_set_sha256=digest,
        locale="vi-VN",
        narration_profile_ref="voice:child-friendly",
        narration_profile_sha256=digest,
        approval_ref="approval:adult-001",
        approval_sha256=digest,
        content_validator_version="story-policy-1",
        content_validator_result="PASSED",
        created_at="2026-09-30T00:00:00Z",
        package_hash=digest,
    )


def _segments() -> tuple[StoryScriptSegmentV1, ...]:
    return tuple(
        StoryScriptSegmentV1(
            segment_id=f"segment-{index}",
            text="Mèo con trèo lên cây để tìm chỗ nghỉ an toàn." * 2,
            approved_fact_ids=("fact-cat-001",),
            confirmed_anchor_ids=("anchor-cat-001",),
            scene_purpose=purpose,
        )
        for index, purpose in enumerate(("INTRO", "EXPLAIN", "DEMONSTRATE", "RECAP"), 1)
    )


def test_compile_uses_measured_tts_as_scene_timing_ground_truth() -> None:
    plan = StoryVideoPlanner().compile(
        StoryboardCompileInput(_package(), _segments(), (10.0, 11.0, 12.0, 10.0))
    )
    assert plan.duration_basis == "MEASURED_TTS"
    assert plan.duration_seconds == 43.0
    assert [scene.duration_seconds for scene in plan.scenes] == [10.0, 11.0, 12.0, 10.0]


def test_compile_rejects_measured_audio_outside_target_instead_of_cutting_words() -> None:
    try:
        StoryVideoPlanner().compile(
            StoryboardCompileInput(_package(), _segments(), (20.0, 20.0, 20.0, 20.0))
        )
    except ValueError as error:
        assert "40-60" in str(error)
    else:
        raise AssertionError("out-of-range narration must require script revision")


class _Narration:
    def render(self, request, texts):
        return NarrationAssetV1(
            status="READY",
            audio_ref="audio:001",
            audio_sha256="b" * 64,
            duration_seconds=43.0,
            locale=request.locale,
            voice_model_ref="tts:test",
            segment_timing_seconds=(10.0, 11.0, 12.0, 10.0),
        )


class _Illustrations:
    def render(self, request):
        return IllustrationAssetV1(
            status="READY",
            scene_id=request.scene_id,
            asset_ref=f"image:{request.scene_id}",
            asset_sha256="c" * 64,
            content_type="image/png",
            width=1024,
            height=1024,
            source_image_ref=request.source_image_ref,
            source_image_sha256=request.source_image_sha256,
            model_profile_ref="image:test",
        )


class _Motion:
    def render(self, request):
        return VideoSceneArtifactV1(
            status="READY",
            scene_id=request.scene_id,
            silent_clip_ref=f"clip:{request.scene_id}",
            silent_clip_sha256="d" * 64,
            duration_seconds=request.duration_seconds,
            frame_count=240,
            fps=24.0,
            model_profile_ref=request.model_profile_ref,
        )


class _Assembler:
    def assemble(self, request):
        return VideoArtifactV1(
            status="READY",
            video_ref="video:001",
            video_sha256="e" * 64,
            duration_seconds=43.0,
            audio_ref=request.narration_ref,
            video_codec="h264",
            audio_codec="aac",
        )


def test_pipeline_runs_tts_before_scenes_and_returns_ready_video() -> None:
    stages: list[str] = []
    run = StoryVideoPipeline(
        narration=_Narration(),
        illustrations=_Illustrations(),
        motion=_Motion(),
        assembler=_Assembler(),
        update_stage=lambda stage, _progress: stages.append(stage),
    ).run(_package(), _segments())
    assert run.video.status == "READY"
    assert run.storyboard.duration_basis == "MEASURED_TTS"
    assert stages == [
        "NARRATION_RENDERING",
        "ILLUSTRATIONS_RENDERING",
        "SCENES_RENDERING",
        "ASSEMBLING",
        "READY",
    ]
