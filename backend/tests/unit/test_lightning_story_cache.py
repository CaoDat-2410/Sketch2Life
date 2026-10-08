"""Expensive story stages may reuse only intact outputs for identical inputs."""

from __future__ import annotations

import base64
import hashlib
import io
import sys
import types
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from tools import lightning_whiteboard_provider as provider


def test_narration_cache_skips_identical_tts_and_rejects_tampering(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("SKETCH2LIFE_TTS_PROVIDER", "edge_tts")
    calls: list[str] = []

    def tts(text: str, *, voice: str) -> bytes:
        calls.append(text)
        return b"fake-mp3"

    def write_wav(_mp3: bytes, output: Path) -> None:
        with wave.open(str(output), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24_000)
            audio.writeframes(b"\0\0" * 24_000)

    monkeypatch.setattr(provider, "_edge_tts", tts)
    monkeypatch.setattr(provider, "_mp3_to_wav", write_wav)
    payload = {
        "request": {"package_id": "pkg", "package_hash": "a" * 64, "locale": "vi-VN"},
        "texts": ["Câu một.", "Câu hai."],
    }

    first = provider.story_video_narration(payload)
    second = provider.story_video_narration(payload)
    assert first == second
    assert first["status"] == "READY"
    assert calls == payload["texts"]

    Path(first["audio_ref"]).write_bytes(b"corrupt")
    restored = provider.story_video_narration(payload)
    assert restored["status"] == "READY"
    assert len(calls) == 2, "an intact segment should not be synthesized twice"
    assert restored["audio_sha256"] == hashlib.sha256(
        Path(restored["audio_ref"]).read_bytes()
    ).hexdigest()

    segment_one = tmp_path / ("a" * 64) / "pkg.segment-1.wav"
    segment_one.write_bytes(b"corrupt")
    Path(restored["audio_ref"]).write_bytes(b"corrupt")
    repaired = provider.story_video_narration(payload)
    assert repaired["status"] == "READY"
    assert calls == ["Câu một.", "Câu hai.", "Câu một."]

    changed = {**payload, "texts": ["Câu khác.", "Câu hai."]}
    assert provider.story_video_narration(changed)["status"] == "READY"
    assert len(calls) == 5
    monkeypatch.setenv("EDGE_TTS_VOICE", "vi-VN-NamMinhNeural")
    assert provider.story_video_narration(changed)["status"] == "READY"
    assert len(calls) == 7


def test_narration_retry_reuses_completed_segment_after_network_timeout(
    tmp_path, monkeypatch
) -> None:
    import subprocess

    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("SKETCH2LIFE_TTS_PROVIDER", "edge_tts")
    calls: list[str] = []
    fail_second = True

    def tts(text: str, *, voice: str) -> bytes:
        nonlocal fail_second
        calls.append(text)
        if text == "Câu hai." and fail_second:
            fail_second = False
            raise subprocess.TimeoutExpired(cmd="edge_tts", timeout=120)
        return b"fake-mp3"

    def write_wav(_mp3: bytes, output: Path) -> None:
        with wave.open(str(output), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24_000)
            audio.writeframes(b"\0\0" * 24_000)

    monkeypatch.setattr(provider, "_edge_tts", tts)
    monkeypatch.setattr(provider, "_mp3_to_wav", write_wav)
    payload = {
        "request": {"package_id": "pkg", "package_hash": "a" * 64, "locale": "vi-VN"},
        "texts": ["Câu một.", "Câu hai."],
    }

    first = provider.story_video_narration(payload)
    assert first["status"] == "RETRYABLE_FAILURE"
    assert first["error_code"] == "TTS_TIMEOUT"
    second = provider.story_video_narration(payload)
    assert second["status"] == "READY"
    assert calls == ["Câu một.", "Câu hai.", "Câu hai."]


def test_illustration_cache_skips_identical_model_and_rejects_tampering(
    tmp_path, monkeypatch
) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setenv("SKETCH2LIFE_IMAGE_MODEL", "synthetic-model")
    source = Image.new("RGB", (80, 50), "white")
    ImageDraw.Draw(source).line((5, 5, 75, 45), fill="black", width=3)
    buffer = io.BytesIO()
    source.save(buffer, format="PNG")
    raw = buffer.getvalue()
    source_hash = hashlib.sha256(raw).hexdigest()
    payload = {
        "request": {
            "package_hash": "b" * 64,
            "scene_id": "scene-1",
            "source_image_ref": "artifact:test",
            "source_image_sha256": source_hash,
            "visual_prompt": "black line art",
        },
        "source_image": {
            "sha256": source_hash,
            "content_base64": base64.b64encode(raw).decode("ascii"),
        },
    }
    model_calls: list[str] = []
    inference_seeds: list[int] = []

    class FakeGenerator:
        def __init__(self, *, device: str):
            assert device == "cpu"

        def manual_seed(self, seed: int):
            self.seed = seed
            return self

    class FakePipeline:
        @classmethod
        def from_pretrained(cls, model_id, **_kwargs):
            model_calls.append(model_id)
            return cls()

        def enable_model_cpu_offload(self):
            pass

        def __call__(self, **kwargs):
            inference_seeds.append(kwargs["generator"].seed)
            return SimpleNamespace(images=[source.copy()])

    fake_torch = types.ModuleType("torch")
    fake_torch.float16 = object()
    fake_torch.Generator = FakeGenerator
    fake_diffusers = types.ModuleType("diffusers")
    fake_diffusers.AutoPipelineForImage2Image = FakePipeline
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "diffusers", fake_diffusers)
    monkeypatch.setattr(provider, "_story_image_pipeline", None)
    monkeypatch.setattr(provider, "_story_image_pipeline_key", None)

    first = provider.story_video_illustration(payload)
    second = provider.story_video_illustration(payload)
    assert first == second
    assert first["status"] == "READY"
    assert model_calls == ["synthetic-model"]
    assert len(inference_seeds) == 1

    Path(first["asset_ref"]).write_bytes(b"corrupt")
    restored = provider.story_video_illustration(payload)
    assert restored["status"] == "READY"
    assert model_calls == ["synthetic-model"]
    assert len(inference_seeds) == 2
    assert inference_seeds[0] == inference_seeds[1]

    changed = {
        **payload,
        "request": {**payload["request"], "visual_prompt": "different approved drawing"},
    }
    assert provider.story_video_illustration(changed)["status"] == "READY"
    assert model_calls == ["synthetic-model"]
    assert len(inference_seeds) == 3
    assert inference_seeds[2] == inference_seeds[1]
    monkeypatch.setenv("SKETCH2LIFE_IMAGE_STRENGTH", "0.5")
    assert provider.story_video_illustration(changed)["status"] == "READY"
    assert model_calls == ["synthetic-model"]
    assert len(inference_seeds) == 4
    assert inference_seeds[3] == inference_seeds[2]

    monkeypatch.setenv("SKETCH2LIFE_IMAGE_VARIANT", "alternate")
    assert provider.story_video_illustration(changed)["status"] == "READY"
    assert model_calls == ["synthetic-model", "synthetic-model"]
    assert inference_seeds[-1] == inference_seeds[0]

    next_scene = {
        **changed,
        "request": {**changed["request"], "scene_id": "scene-2"},
    }
    assert provider.story_video_illustration(next_scene)["status"] == "READY"
    assert inference_seeds[-1] == inference_seeds[0]
    assert model_calls == ["synthetic-model", "synthetic-model"]
