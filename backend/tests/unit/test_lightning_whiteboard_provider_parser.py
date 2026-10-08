from __future__ import annotations

import pytest
from tools.lightning_whiteboard_provider import (
    _parse_box,
    _subtitle_srt,
    story_video_assembly,
    story_video_scene,
)


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


def test_whiteboard_story_scene_renders_real_mp4(tmp_path, monkeypatch) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    imageio = pytest.importorskip("imageio.v2")
    image = Image.new("RGB", (160, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.line((15, 20, 140, 20), fill="black", width=4)
    image_path = tmp_path / "illustration.png"
    image.save(image_path)
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))

    response = story_video_scene(
        {
            "request": {
                "scene_id": "scene-1",
                "illustration_ref": str(image_path),
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
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    package_hash = "b" * 64
    scene = story_video_scene(
        {
            "request": {
                "scene_id": "scene-1",
                "illustration_ref": str(source),
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
    assembled = story_video_assembly(
        {
            "request": {
                "package_id": "pkg-test",
                "package_hash": package_hash,
                "scene_artifact_refs": [scene["silent_clip_ref"]],
                "narration_ref": str(audio_path),
                "subtitle_cues": [
                    {"text": "Một nét vẽ xuất hiện.", "start_seconds": 0, "end_seconds": 5}
                ],
            }
        }
    )
    assert assembled["status"] == "READY"
    assert 4.9 <= assembled["duration_seconds"] <= 5.1
    assert imageio.get_reader(assembled["video_ref"]).get_meta_data()["size"] == (1280, 720)
