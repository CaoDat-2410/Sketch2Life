from sketch2life.application.services.story_video_pipeline import (
    StoryVideoPipeline,
    StoryVideoProviderError,
)
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


def test_story_package_rejects_placeholder_approval_hash() -> None:
    import pytest

    with pytest.raises(ValueError, match="placeholder hash"):
        ApprovedStoryPackageV1.model_validate(
            _package().model_dump() | {"approval_sha256": "0" * 64}
        )


def test_compile_rejects_measured_audio_outside_target_instead_of_cutting_words() -> None:
    try:
        StoryVideoPlanner().compile(
            StoryboardCompileInput(_package(), _segments(), (20.0, 20.0, 20.0, 20.0))
        )
    except ValueError as error:
        assert "40-60" in str(error)
    else:
        raise AssertionError("out-of-range narration must require script revision")


def test_director_groups_short_approved_segments_into_timed_scenes() -> None:
    segments = tuple(
        StoryScriptSegmentV1(
            segment_id=f"segment-{index}",
            text=f"Đoạn kể đã duyệt số {index}.",
            approved_fact_ids=(f"fact-{index}",),
            confirmed_anchor_ids=("anchor-cat",),
            scene_purpose=("INTRO", "EXPLAIN", "DEMONSTRATE", "RECAP")[(index - 1) // 2],
        )
        for index in range(1, 9)
    )
    plan = StoryVideoPlanner().compile(
        StoryboardCompileInput(_package(), segments, (6.0,) * 8)
    )

    assert plan.duration_seconds == 48.0
    assert len(plan.scenes) == 4
    assert [scene.segment_ids for scene in plan.scenes] == [
        ("segment-1", "segment-2"),
        ("segment-3", "segment-4"),
        ("segment-5", "segment-6"),
        ("segment-7", "segment-8"),
    ]
    assert plan.scenes[0].approved_fact_ids == ("fact-1", "fact-2")
    assert all(scene.duration_seconds == 12.0 for scene in plan.scenes)


def test_director_rejects_too_few_approved_segments() -> None:
    try:
        StoryVideoPlanner().compile(
            StoryboardCompileInput(_package(), _segments()[:2], (20.0, 20.0))
        )
    except ValueError as error:
        assert "at least three" in str(error)
    else:
        raise AssertionError("two long clips are not a controlled storyboard")


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
        assert len(request.subtitle_cues) >= len(request.scene_ids)
        assert request.subtitle_cues[0].text
        assert request.subtitle_cues[-1].end_seconds == 43.0
        assert all(len(cue.text) <= 62 for cue in request.subtitle_cues)
        assert all(
            current.start_seconds >= previous.end_seconds - 0.01
            for previous, current in zip(
                request.subtitle_cues, request.subtitle_cues[1:], strict=False
            )
        )
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


def test_pipeline_reports_invalid_storyboard_before_rendering_images() -> None:
    class ShortNarration(_Narration):
        def render(self, request, texts):
            return NarrationAssetV1(
                status="READY",
                audio_ref="audio:short",
                audio_sha256="b" * 64,
                duration_seconds=40.0,
                locale=request.locale,
                voice_model_ref="tts:test",
                segment_timing_seconds=(20.0, 20.0),
            )

    class NoImages:
        def render(self, request):
            raise AssertionError("invalid storyboard must stop before image rendering")

    pipeline = StoryVideoPipeline(
        narration=ShortNarration(),
        illustrations=NoImages(),
        motion=_Motion(),
        assembler=_Assembler(),
    )
    try:
        pipeline.run(_package(), _segments()[:2])
    except StoryVideoProviderError as error:
        assert error.code == "STORYBOARD_INVALID"
        assert not error.retryable
    else:
        raise AssertionError("invalid storyboard must be a typed failure")


def test_synthetic_40_second_story_renders_and_assembles_real_mp4(tmp_path, monkeypatch) -> None:
    """Exercise all four media stages without a GPU, network call or child media."""

    import hashlib
    import wave

    import pytest

    imageio = pytest.importorskip("imageio.v2")
    imageio_ffmpeg = pytest.importorskip("imageio_ffmpeg")
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setattr(
        provider, "_require_executable", lambda _name: imageio_ffmpeg.get_ffmpeg_exe()
    )
    monkeypatch.setattr(
        provider,
        "_ffprobe_duration",
        lambda path: float(imageio.get_reader(path).get_meta_data()["duration"]),
    )
    audio_path = tmp_path / "narration.wav"
    with wave.open(str(audio_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24_000)
        output.writeframes(b"\0\0" * (24_000 * 40))

    class Narration:
        def render(self, request, texts):
            assert len(texts) == 4
            return NarrationAssetV1(
                status="READY",
                audio_ref=str(audio_path),
                audio_sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                duration_seconds=40.0,
                locale=request.locale,
                voice_model_ref="synthetic-silence:test-only",
                segment_timing_seconds=(10.0,) * 4,
            )

    class Illustrations:
        def render(self, request):
            image = Image.new("RGB", (160, 80), "white")
            draw = ImageDraw.Draw(image)
            draw.line((10, 15, 145, 15), fill="black", width=4)
            draw.line((25, 20, 25, 65), fill="black", width=4)
            path = tmp_path / f"{request.scene_id}.png"
            image.save(path)
            return IllustrationAssetV1(
                status="READY",
                scene_id=request.scene_id,
                asset_ref=str(path),
                asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                content_type="image/png",
                width=160,
                height=80,
                source_image_ref=request.source_image_ref,
                source_image_sha256=request.source_image_sha256,
                model_profile_ref="synthetic-lines:test-only",
            )

    class Motion:
        def render(self, request):
            return VideoSceneArtifactV1.model_validate(
                provider.story_video_scene({"request": request.model_dump(mode="json")})
            )

    class Assembler:
        def assemble(self, request):
            return VideoArtifactV1.model_validate(
                provider.story_video_assembly({"request": request.model_dump(mode="json")})
            )

    run = StoryVideoPipeline(
        narration=Narration(),
        illustrations=Illustrations(),
        motion=Motion(),
        assembler=Assembler(),
    ).run(_package(), _segments())

    assert run.video.status == "READY"
    assert len(run.scenes) == 4
    assert 39.5 <= run.video.duration_seconds <= 40.5
    assert imageio.get_reader(run.video.video_ref).get_meta_data()["size"] == (1280, 720)
