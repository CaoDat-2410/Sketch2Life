"""Provider-only smoke orchestration never fabricates an approved backend job."""

from __future__ import annotations

import hashlib
import json

import pytest
from tools.story_video_media_smoke import _local_base_url, load_fixture, run_media_smoke


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
        *(
            stage
            for _index in range(4)
            for stage in ("/v1/story-video/illustration", "/v1/story-video/scene")
        ),
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
