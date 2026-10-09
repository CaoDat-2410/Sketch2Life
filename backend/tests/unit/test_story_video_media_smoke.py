"""Provider-only smoke orchestration never fabricates an approved backend job."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tools.create_story_video_media_fixture import create_fixture
from tools.story_video_media_smoke import (
    _local_base_url,
    _scene_draw_beats,
    load_fixture,
    run_media_smoke,
)


def _fixture(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    source = tmp_path / "synthetic.png"
    Image.new("RGB", (24, 24), "white").save(source)
    scenes = tuple(
        {"text": f"Synthetic story beat {index}.", "visual_prompt": f"line art beat {index}"}
        for index in range(1, 5)
    )
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({"source_image": source.name, "locale": "vi-VN", "scenes": scenes}),
        encoding="utf-8",
    )
    return source, scenes, fixture


def test_media_smoke_runs_provider_stages_and_verifies_final_file(tmp_path) -> None:
    source, scenes, fixture = _fixture(tmp_path)
    scenes = ({**scenes[0], "draw_cues": [
        {"element_id": "subject", "label": "Chủ thể", "focus_box": [0.1, 0.1, 0.9, 0.9]},
    ]}, *scenes[1:])
    fixture.write_text(json.dumps({
        "source_image": source.name, "locale": "vi-VN", "scenes": scenes,
    }), encoding="utf-8")
    assert load_fixture(fixture) == (source.resolve(), "vi-VN", scenes)
    audio = tmp_path / "narration.wav"
    audio.write_bytes(b"fake-audio")
    video = tmp_path / "story.mp4"
    video.write_bytes(b"fake-video")
    calls: list[str] = []

    def post(path, payload):
        calls.append(path)
        if path.endswith("/narration"):
            assert len(payload["texts"]) == 4
            return {
                "status": "READY",
                "audio_ref": str(audio),
                "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
                "duration_seconds": 40.0,
                "segment_timing_seconds": [10.0] * 4,
            }
        if path.endswith("/illustration"):
            scene_id = payload["request"]["scene_id"]
            image = tmp_path / f"{scene_id}.png"
            image.write_bytes(scene_id.encode())
            return {
                "status": "READY",
                "asset_ref": str(image),
                "asset_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            }
        if path.endswith("/scene"):
            scene_id = payload["request"]["scene_id"]
            if scene_id == "scene-1":
                assert payload["request"]["draw_beats"][0]["end_seconds"] == 10.0
            else:
                assert "draw_beats" not in payload["request"]
            clip = tmp_path / f"{scene_id}.mp4"
            clip.write_bytes(scene_id.encode())
            assert payload["request"]["duration_seconds"] == 10.0
            return {
                "status": "READY",
                "silent_clip_ref": str(clip),
                "silent_clip_sha256": hashlib.sha256(clip.read_bytes()).hexdigest(),
                "duration_seconds": 10.0,
            }
        assert path.endswith("/assembly")
        assert len(payload["request"]["scene_artifact_sha256"]) == 4
        assert payload["request"]["subtitle_cues"][-1]["end_seconds"] == 40.0
        return {
            "status": "READY",
            "video_ref": str(video),
            "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
            "duration_seconds": 40.0,
        }

    result = run_media_smoke(
        source,
        "vi-VN",
        scenes,
        get=lambda _path: {"ready": True, "checks": {}},
        post=post,
    )
    assert result["video_ref"] == str(video)
    assert calls == [
        "/v1/story-video/narration",
        *("/v1/story-video/illustration" for _index in range(4)),
        *("/v1/story-video/scene" for _index in range(4)),
        "/v1/story-video/assembly",
    ]


def test_media_smoke_preflight_and_duration_fail_without_image_calls(tmp_path) -> None:
    source, scenes, _fixture_path = _fixture(tmp_path)
    calls: list[str] = []

    def post(path, _payload):
        calls.append(path)
        return {"status": "READY", "segment_timing_seconds": [3.0] * 4}

    with pytest.raises(RuntimeError, match="preflight failed"):
        run_media_smoke(
            source, "vi-VN", scenes,
            get=lambda _path: {"ready": False, "checks": {"cuda": {"ready": False}}},
            post=post,
        )
    assert calls == []

    result = run_media_smoke(
        source, "vi-VN", scenes,
        get=lambda _path: {"ready": True, "checks": {}},
        post=post,
        preflight_only=True,
    )
    assert result["preflight"] == "READY"
    assert calls == []

    with pytest.raises(RuntimeError, match="40-60 s"):
        run_media_smoke(
            source, "vi-VN", scenes,
            get=lambda _path: {"ready": True, "checks": {}},
            post=post,
        )
    assert calls == ["/v1/story-video/narration"]


def test_sam2_media_smoke_requires_cues_before_paid_provider_calls(tmp_path) -> None:
    source, scenes, _fixture_path = _fixture(tmp_path)
    calls = []
    with pytest.raises(ValueError, match="draw_cues in every scene"):
        run_media_smoke(
            source, "vi-VN", scenes,
            get=lambda _path: {"ready": True, "checks": {}, "story_segmenter": "sam2"},
            post=lambda path, _payload: calls.append(path),
        )
    assert calls == []


def test_image_preview_skips_tts_and_reuses_hash_after_cue_edit(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    source, scenes, _fixture_path = _fixture(tmp_path)
    seen_hashes = []
    calls = []

    def post(path, payload):
        calls.append(path)
        assert path == "/v1/story-video/illustration"
        request = payload["request"]
        seen_hashes.append(request["package_hash"])
        image = tmp_path / f"{request['scene_id']}.png"
        number = int(request["scene_id"].split("-")[-1])
        Image.new("RGB", (80, 60), (number * 40, 60, 140)).save(image)
        return {"status": "READY", "asset_ref": str(image),
                "asset_sha256": hashlib.sha256(image.read_bytes()).hexdigest()}

    kwargs = {
        "get": lambda _path: {"ready": True, "checks": {}, "story_segmenter": "sam2"},
        "post": post,
        "preview_images": True,
    }
    first = run_media_smoke(source, "vi-VN", scenes, **kwargs)
    edited = ({**scenes[0], "draw_cues": [
        {"element_id": "subject", "label": "Chủ thể", "focus_box": [0.1, 0.1, 0.9, 0.9]},
    ]}, *scenes[1:])
    second = run_media_smoke(source, "vi-VN", edited, **kwargs)

    assert first["package_hash"] == second["package_hash"]
    assert first["cue_sha256"] != second["cue_sha256"]
    assert len(first["illustrations"]) == 4
    assert set(seen_hashes) == {first["package_hash"]}
    assert first["contact_sheet_sha256"] != second["contact_sheet_sha256"]
    with Image.open(second["contact_sheet_ref"]) as sheet:
        assert sheet.size == (1260, 580)
        assert sheet.getpixel((210, 153)) == (255, 255, 255)
        assert sheet.getpixel((630, 153)) == (40, 60, 140)
    assert hashlib.sha256(Path(second["contact_sheet_ref"]).read_bytes()).hexdigest() == (
        second["contact_sheet_sha256"]
    )
    assert calls == ["/v1/story-video/illustration"] * 8


def test_media_smoke_rejects_remote_provider_and_long_caption(tmp_path) -> None:
    _source, scenes, fixture = _fixture(tmp_path)
    with pytest.raises(ValueError, match="local HTTP"):
        _local_base_url("https://example.com")
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    raw["scenes"][0]["text"] = "word " * 60
    fixture.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="caption chunks"):
        load_fixture(fixture)


def test_media_smoke_rejects_undecodable_image_before_tts(tmp_path) -> None:
    source, _scenes, fixture = _fixture(tmp_path)
    source.write_bytes(b"not-a-png")
    with pytest.raises(ValueError, match="cannot be decoded"):
        load_fixture(fixture)


def test_generated_non_child_fixture_is_valid_and_never_overwrites(tmp_path) -> None:
    directory = tmp_path / "sample"
    fixture = create_fixture(directory)
    image, locale, scenes = load_fixture(fixture)
    assert image.is_file()
    assert locale == "vi-VN"
    assert len(scenes) == 4
    assert all(len(scene["text"].split()) >= 25 for scene in scenes)
    assert all(len(scene["focus_box"]) == 4 for scene in scenes)
    assert len({tuple(scene["focus_box"]) for scene in scenes}) == 4
    with pytest.raises(FileExistsError, match="already exists"):
        create_fixture(directory)
    repository_root = Path(__file__).resolve().parents[3]
    with pytest.raises(ValueError, match="outside the Git repository"):
        create_fixture(repository_root / "forbidden-smoke-output")


def test_media_smoke_rejects_invalid_scene_focus_box(tmp_path) -> None:
    _source, _scenes, fixture = _fixture(tmp_path)
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    raw["scenes"][0]["focus_box"] = [0.2, 0.2, 0.1, 0.9]
    fixture.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="focus_box"):
        load_fixture(fixture)


def test_media_smoke_cues_bind_draw_order_to_measured_tts(tmp_path) -> None:
    _source, _scenes, fixture = _fixture(tmp_path)
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    raw["scenes"][0]["draw_cues"] = [
        {"element_id": "right", "label": "Bên phải", "focus_box": [0.55, 0.1, 0.95, 0.5]},
        {"element_id": "left", "label": "Bên trái", "focus_box": [0.05, 0.5, 0.45, 0.9]},
    ]
    fixture.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    scene = load_fixture(fixture)[2][0]

    beats = _scene_draw_beats(scene, 1, 11.0)
    assert [(beat["element_id"], beat["start_seconds"], beat["end_seconds"])
            for beat in beats] == [("right", 0.0, 5.5), ("left", 5.5, 11.0)]
    assert all(beat["segment_id"] == "segment-1" for beat in beats)

    raw["scenes"][0]["draw_cues"][1]["focus_box"] = [0.9, 0.2, 0.1, 0.8]
    fixture.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="draw cue box"):
        load_fixture(fixture)
