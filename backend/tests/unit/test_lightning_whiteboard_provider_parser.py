from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from tools.lightning_whiteboard_provider import (
    _assembled_streams_ready,
    _parse_box,
    _subtitle_srt,
    story_video_assembly,
    story_video_scene,
)

from sketch2life.contracts.schemas.story_video_media import NarrationAssetV1


def test_parse_box_scales_1024_coordinates_to_image_size() -> None:
    assert _parse_box("[100, 200, 900, 1000]", 600, 600) == [
        pytest.approx(58.59375),
        pytest.approx(117.1875),
        pytest.approx(527.34375),
        pytest.approx(585.9375),
    ]


def test_parse_box_rejects_missing_box() -> None:
    with pytest.raises(ValueError, match="bounding box"):
        _parse_box("no coordinates", 600, 600)


def test_preflight_detects_unusable_whiteboard_encoder_before_paid_work(monkeypatch) -> None:
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setenv("SKETCH2LIFE_STORY_MOTION_PROVIDER", "whiteboard-stroke-v1")

    def missing_encoder() -> None:
        raise RuntimeError("libx264 unavailable")

    monkeypatch.setattr(provider, "_probe_whiteboard_encoder", missing_encoder)
    result = provider.story_video_preflight()

    assert result["checks"]["whiteboard_renderer"]["ready"] is True
    assert result["checks"]["h264_encoder"]["ready"] is False
    assert result["ready"] is False


def test_preflight_blocks_opt_in_sam2_when_runtime_is_missing(monkeypatch) -> None:
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setenv("SKETCH2LIFE_STORY_MOTION_PROVIDER", "whiteboard-stroke-v1")
    monkeypatch.setenv("SKETCH2LIFE_STORY_SEGMENTER", "sam2")
    actual_import = provider.importlib.import_module

    def import_with_missing_sam(name, *args, **kwargs):
        if name == "sam2.sam2_image_predictor":
            raise ImportError("sam2 unavailable")
        return actual_import(name, *args, **kwargs)

    monkeypatch.setattr(provider.importlib, "import_module", import_with_missing_sam)
    report = provider.story_video_preflight()
    assert report["checks"]["story_segmenter"]["ready"] is False
    assert report["ready"] is False


def test_preflight_rejects_missing_optional_hand_before_paid_work(tmp_path, monkeypatch) -> None:
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setenv("SKETCH2LIFE_STORY_MOTION_PROVIDER", "whiteboard-stroke-v1")
    monkeypatch.setenv("SKETCH2LIFE_WHITEBOARD_HAND_ASSET", str(tmp_path / "missing.png"))
    report = provider.story_video_preflight()
    assert report["checks"]["whiteboard_hand"]["ready"] is False
    assert report["ready"] is False


def test_preflight_h264_probe_encodes_synthetic_frame() -> None:
    pytest.importorskip("imageio.v2")
    pytest.importorskip("imageio_ffmpeg")
    import tools.lightning_whiteboard_provider as provider

    provider._probe_whiteboard_encoder()


@pytest.mark.parametrize(
    ("filter_output", "available"),
    [
        (" T.C subtitles V->V Render text subtitles using libass", True),
        (" T.C ass V->V Burn ASS subtitles using libass", False),
        (" T.C scale V->V Scale the input video", False),
    ],
)
def test_preflight_checks_ffmpeg_subtitle_filter(
    monkeypatch, filter_output: str, available: bool
) -> None:
    import tools.lightning_whiteboard_provider as provider

    def fake_run(args, **kwargs):
        assert args[-1] == "-filters"
        assert kwargs["timeout"] == 15
        return subprocess.CompletedProcess(args, 0, stdout=filter_output, stderr="")

    monkeypatch.setattr(provider.subprocess, "run", fake_run)
    assert provider._ffmpeg_subtitles_available("ffmpeg") is available


def test_story_scene_rejects_unbounded_draw_beats_before_render(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image = tmp_path / "synthetic.png"
    Image.new("RGB", (40, 40), "white").save(image)
    result = story_video_scene({"request": {
        "package_id": "synthetic-test",
        "package_hash": "a" * 64,
        "scene_id": "scene-1",
        "illustration_ref": str(image),
        "illustration_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "duration_seconds": 10.0,
        "model_profile_ref": "whiteboard-stroke-v1",
        "draw_beats": [{
            "element_id": "cat", "segment_id": "segment-1", "label": "Mèo",
            "focus_box": [0.8, 0.2, 0.2, 0.8],
            "start_seconds": 0.0, "end_seconds": 10.0,
        }],
    }})
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "DRAW_BEATS_INVALID"


def test_story_scene_forwards_opt_in_sam_masks_to_renderer(tmp_path, monkeypatch) -> None:
    import json

    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    np = pytest.importorskip("numpy")
    import tools.lightning_whiteboard_provider as provider

    import sketch2life.infrastructure.media.whiteboard_mvp_renderer as renderer

    illustration = tmp_path / "scene.png"
    image = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 60, 35, 85), outline="black", width=3)
    draw.rectangle((65, 15, 90, 40), outline="black", width=3)
    image.save(illustration)
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("SKETCH2LIFE_STORY_SEGMENTER", "sam2")
    received = {}

    def fake_masks(_image_path, stroke_path, beats):
        payload = json.loads(stroke_path.read_text(encoding="utf-8"))
        assert [beat.element_id for beat in beats] == ["right", "left"]
        return tuple(np.ones((payload["height"], payload["width"]), dtype=bool) for _ in beats)

    def fake_render(_stroke_path, output_path, *, spec, draw_beats, beat_masks):
        received["beats"] = draw_beats
        received["masks"] = beat_masks
        assert spec.duration_seconds == 5.0
        output_path.write_bytes(b"synthetic-test-video")
        return SimpleNamespace(fps=30)

    monkeypatch.setattr(provider, "_story_scene_sam_masks", fake_masks)
    monkeypatch.setattr(renderer, "render_stroke_animation", fake_render)
    result = story_video_scene({"request": {
        "package_id": "synthetic-test", "package_hash": "b" * 64,
        "scene_id": "scene-1", "illustration_ref": str(illustration),
        "illustration_sha256": hashlib.sha256(illustration.read_bytes()).hexdigest(),
        "duration_seconds": 5.0, "model_profile_ref": "whiteboard-stroke-v1",
        "draw_beats": [
            {"element_id": "right", "segment_id": "segment-1", "label": "Bên phải",
             "focus_box": [0.6, 0.1, 0.95, 0.5], "start_seconds": 0, "end_seconds": 2.5},
            {"element_id": "left", "segment_id": "segment-1", "label": "Bên trái",
             "focus_box": [0.05, 0.5, 0.4, 0.95], "start_seconds": 2.5, "end_seconds": 5},
        ],
    }})
    assert result["status"] == "READY"
    assert len(received["masks"]) == 2
    assert [beat.element_id for beat in received["beats"]] == ["right", "left"]


def test_sam_story_scene_requires_visual_cues(tmp_path, monkeypatch) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    illustration = tmp_path / "scene.png"
    image = Image.new("RGB", (100, 100), "white")
    ImageDraw.Draw(image).rectangle((20, 20, 80, 80), outline="black", width=4)
    image.save(illustration)
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("SKETCH2LIFE_STORY_SEGMENTER", "sam2")

    result = story_video_scene({"request": {
        "package_id": "synthetic-test", "package_hash": "c" * 64,
        "scene_id": "scene-1", "illustration_ref": str(illustration),
        "illustration_sha256": hashlib.sha256(illustration.read_bytes()).hexdigest(),
        "duration_seconds": 5.0, "model_profile_ref": "whiteboard-stroke-v1",
    }})
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "DRAW_BEATS_REQUIRED_FOR_SAM"


def test_cue_edit_keeps_prior_scene_mp4_artifact(tmp_path, monkeypatch) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    import sketch2life.infrastructure.media.whiteboard_mvp_renderer as renderer

    illustration = tmp_path / "scene.png"
    image = Image.new("RGB", (100, 100), "white")
    ImageDraw.Draw(image).rectangle((20, 20, 80, 80), outline="black", width=4)
    image.save(illustration)
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("SKETCH2LIFE_STORY_SEGMENTER", "bbox")

    def fake_render(_stroke_path, output_path, *, spec, draw_beats, beat_masks):
        assert spec.duration_seconds == 5.0 and beat_masks is None
        output_path.write_bytes(draw_beats[0].element_id.encode())
        return SimpleNamespace(fps=30)

    monkeypatch.setattr(renderer, "render_stroke_animation", fake_render)
    request = {
        "package_hash": "d" * 64, "scene_id": "scene-1",
        "illustration_ref": str(illustration),
        "illustration_sha256": hashlib.sha256(illustration.read_bytes()).hexdigest(),
        "duration_seconds": 5.0, "model_profile_ref": "whiteboard-stroke-v1",
        "draw_beats": [{
            "element_id": "house", "segment_id": "segment-1", "label": "Ngôi nhà",
            "focus_box": [0.1, 0.1, 0.9, 0.9], "start_seconds": 0, "end_seconds": 5,
        }],
    }
    first = story_video_scene({"request": request})
    request["draw_beats"][0] = {**request["draw_beats"][0], "element_id": "roof"}
    second = story_video_scene({"request": request})

    assert first["status"] == second["status"] == "READY"
    assert first["silent_clip_ref"] != second["silent_clip_ref"]
    assert first["silent_clip_sha256"] != second["silent_clip_sha256"]
    assert Path(first["silent_clip_ref"]).read_bytes() == b"house"
    assert Path(second["silent_clip_ref"]).read_bytes() == b"roof"


def test_hand_asset_change_keeps_prior_scene_mp4_artifact(tmp_path, monkeypatch) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    import sketch2life.infrastructure.media.whiteboard_mvp_renderer as renderer

    illustration = tmp_path / "scene.png"
    image = Image.new("RGB", (100, 100), "white")
    ImageDraw.Draw(image).line((10, 20, 90, 80), fill="black", width=4)
    image.save(illustration)
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("SKETCH2LIFE_STORY_SEGMENTER", "bbox")
    hand = tmp_path / "hand.png"

    def fake_render(_stroke_path, output_path, *, spec, draw_beats, beat_masks, hand_asset_path):
        assert spec.duration_seconds == 5 and not draw_beats and beat_masks is None
        output_path.write_bytes(hand_asset_path.read_bytes())
        return SimpleNamespace(fps=30)

    monkeypatch.setattr(renderer, "render_stroke_animation", fake_render)
    request = {
        "package_hash": "f" * 64, "scene_id": "scene-1",
        "illustration_ref": str(illustration),
        "illustration_sha256": hashlib.sha256(illustration.read_bytes()).hexdigest(),
        "duration_seconds": 5.0, "model_profile_ref": "whiteboard-stroke-v1",
    }
    monkeypatch.setenv("SKETCH2LIFE_WHITEBOARD_HAND_ASSET", str(hand))
    Image.new("RGBA", (30, 30), (255, 0, 0, 255)).save(hand)
    first = story_video_scene({"request": request})
    Image.new("RGBA", (30, 30), (0, 0, 255, 255)).save(hand)
    second = story_video_scene({"request": request})
    assert first["status"] == second["status"] == "READY"
    assert first["silent_clip_ref"] != second["silent_clip_ref"]
    assert first["silent_clip_sha256"] != second["silent_clip_sha256"]
    assert Path(first["silent_clip_ref"]).is_file()


def test_subtitle_srt_serializes_utf8_scene_cues() -> None:
    assert _subtitle_srt(
        [
            {
                "text": "Ria mèo giúp mèo cảm nhận vật ở gần.",
                "start_seconds": 0,
                "end_seconds": 3.5,
            },
            {
                "text": "Không nên cắt ria của mèo.",
                "start_seconds": 3.5,
                "end_seconds": 6,
            },
        ]
    ) == (
        "1\n00:00:00,000 --> 00:00:03,500\nRia mèo giúp mèo cảm nhận vật ở gần.\n\n"
        "2\n00:00:03,500 --> 00:00:06,000\nKhông nên cắt ria của mèo.\n"
    )


def test_assembly_requires_real_h264_video_and_aac_audio_streams() -> None:
    valid = [
        {"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720},
        {"codec_type": "audio", "codec_name": "aac"},
    ]
    assert _assembled_streams_ready(valid)
    assert not _assembled_streams_ready(valid[:1])
    assert not _assembled_streams_ready(valid[1:])
    assert not _assembled_streams_ready([{**valid[0], "codec_name": "vp9"}, valid[1]])
    assert not _assembled_streams_ready([{**valid[0], "width": None}, valid[1]])


def test_whiteboard_story_scene_renders_real_mp4(tmp_path, monkeypatch) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    imageio = pytest.importorskip("imageio.v2")
    image = Image.new("RGB", (160, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.line((15, 20, 140, 20), fill="black", width=4)
    image_path = tmp_path / "illustration.png"
    image.save(image_path)
    image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))

    response = story_video_scene(
        {
            "request": {
                "scene_id": "scene-1",
                "illustration_ref": str(image_path),
                "illustration_sha256": image_hash,
                "duration_seconds": 5.0,
                "model_profile_ref": "whiteboard-stroke-v1",
                "package_hash": "a" * 64,
            }
        }
    )

    assert response["status"] == "READY"
    reader = imageio.get_reader(response["silent_clip_ref"])
    assert reader.get_meta_data()["size"] == (1280, 720)
    first = reader.get_data(0)
    last = reader.get_data(149)
    assert first.mean() > last.mean()


def test_story_video_assembly_muxes_audio_and_burns_subtitles(tmp_path, monkeypatch) -> None:
    import wave

    imageio = pytest.importorskip("imageio.v2")
    imageio_ffmpeg = pytest.importorskip("imageio_ffmpeg")
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (160, 80), "white")
    ImageDraw.Draw(image).line((10, 15, 145, 60), fill="black", width=4)
    source = tmp_path / "illustration.png"
    image.save(source)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    package_hash = "b" * 64
    scene = story_video_scene(
        {
            "request": {
                "scene_id": "scene-1",
                "illustration_ref": str(source),
                "illustration_sha256": source_hash,
                "duration_seconds": 5.0,
                "model_profile_ref": "whiteboard-stroke-v1",
                "package_hash": package_hash,
            }
        }
    )
    assert scene["status"] == "READY"
    audio_path = tmp_path / "narration.wav"
    with wave.open(str(audio_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24_000)
        output.writeframes(b"\0\0" * (24_000 * 5))

    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setattr(
        provider, "_require_executable", lambda _name: imageio_ffmpeg.get_ffmpeg_exe()
    )
    monkeypatch.setattr(
        provider,
        "_ffprobe_duration",
        lambda path: float(imageio.get_reader(path).get_meta_data()["duration"]),
    )
    monkeypatch.setattr(
        provider,
        "_ffprobe_streams",
        lambda _path: [
            {"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
    )
    assembled = story_video_assembly(
        {
            "request": {
                "package_id": "pkg-test",
                "package_hash": package_hash,
                "scene_artifact_refs": [scene["silent_clip_ref"]],
                "scene_artifact_sha256": [scene["silent_clip_sha256"]],
                "narration_ref": str(audio_path),
                "narration_sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                "subtitle_cues": [
                    {"text": "Một nét vẽ xuất hiện.", "start_seconds": 0, "end_seconds": 5}
                ],
            }
        }
    )
    assert assembled["status"] == "READY"
    assert 4.9 <= assembled["duration_seconds"] <= 5.1
    assert imageio.get_reader(assembled["video_ref"]).get_meta_data()["size"] == (1280, 720)


def test_story_scene_rejects_changed_illustration_before_render(tmp_path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"changed-art")
    result = story_video_scene(
        {"request": {
            "package_hash": "a" * 64,
            "scene_id": "scene-1",
            "illustration_ref": str(image),
            "illustration_sha256": hashlib.sha256(b"original-art").hexdigest(),
            "model_profile_ref": "whiteboard-stroke-v1",
        }}
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "ILLUSTRATION_HASH_MISMATCH"


def test_assembly_rejects_changed_audio_or_scene_before_mux(tmp_path, monkeypatch) -> None:
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setattr(provider, "_require_executable", lambda _name: "ffmpeg")
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    audio = tmp_path / "audio.wav"
    clip = tmp_path / "scene.mp4"
    audio.write_bytes(b"changed-audio")
    clip.write_bytes(b"changed-scene")
    request = {
        "package_hash": "b" * 64,
        "scene_artifact_refs": [str(clip)],
        "scene_artifact_sha256": [hashlib.sha256(b"original-scene").hexdigest()],
        "narration_ref": str(audio),
        "narration_sha256": hashlib.sha256(b"original-audio").hexdigest(),
    }
    audio_result = story_video_assembly({"request": request})
    assert audio_result["error_code"] == "NARRATION_HASH_MISMATCH"

    audio.write_bytes(b"original-audio")
    scene_result = story_video_assembly({"request": request})
    assert scene_result["error_code"] == "SCENE_HASH_MISMATCH"


def test_edge_tts_subprocess_has_a_bounded_timeout(monkeypatch) -> None:
    import tools.lightning_whiteboard_provider as provider

    def time_out(*args, **kwargs):
        assert kwargs["timeout"] == 120
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=120)

    monkeypatch.setattr(provider.subprocess, "run", time_out)
    with pytest.raises(subprocess.TimeoutExpired):
        provider._edge_tts("Một câu thử.", voice="vi-VN-HoaiMyNeural")


@pytest.mark.parametrize(
    ("provider_name", "failure", "expected_status", "expected_code"),
    [
        (
            "edge_tts", subprocess.TimeoutExpired(cmd="edge_tts", timeout=120),
            "RETRYABLE_FAILURE", "TTS_TIMEOUT",
        ),
        (
            "elevenlabs", RuntimeError("ELEVENLABS_TTS_UNAVAILABLE"),
            "RETRYABLE_FAILURE", "ELEVENLABS_TTS_UNAVAILABLE",
        ),
        (
            "elevenlabs", RuntimeError("ELEVENLABS_TTS_REJECTED"),
            "BLOCKED", "ELEVENLABS_TTS_REJECTED",
        ),
    ],
)
def test_story_narration_classifies_network_failures_without_continuing(
    tmp_path, monkeypatch, provider_name, failure, expected_status, expected_code
) -> None:
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("SKETCH2LIFE_TTS_PROVIDER", provider_name)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-only-placeholder")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "test-voice")

    def fail_tts(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(
        provider, "_edge_tts" if provider_name == "edge_tts" else "_elevenlabs_tts", fail_tts
    )
    response = provider.story_video_narration(
        {
            "request": {
                "package_id": "test-network-failure",
                "package_hash": "a" * 64,
                "locale": "vi-VN",
            },
            "texts": ["Một câu thử."],
        }
    )

    parsed = NarrationAssetV1.model_validate(response)
    assert parsed.status == expected_status
    assert parsed.error_code == expected_code


def test_story_narration_returns_typed_failure_for_undecodable_audio(
    tmp_path, monkeypatch
) -> None:
    import tools.lightning_whiteboard_provider as provider

    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("SKETCH2LIFE_TTS_PROVIDER", "edge_tts")
    monkeypatch.setattr(provider, "_edge_tts", lambda *_args, **_kwargs: b"fake-mp3")
    monkeypatch.setattr(provider, "_mp3_to_wav", lambda _audio, path: path.write_bytes(b"bad"))

    response = provider.story_video_narration(
        {
            "request": {"package_id": "bad-audio", "package_hash": "a" * 64},
            "texts": ["Một câu thử."],
        }
    )

    parsed = NarrationAssetV1.model_validate(response)
    assert parsed.status == "BLOCKED"
    assert parsed.error_code == "TTS_RENDER_FAILED"
