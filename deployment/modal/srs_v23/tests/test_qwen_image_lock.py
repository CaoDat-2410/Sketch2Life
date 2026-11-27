"""FEAT-094: the serving Qwen image and the video image's ffmpeg do not drift on a rebuild."""

from __future__ import annotations

from pathlib import Path

MODAL_DIR = Path(__file__).resolve().parents[1]
QWEN = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
VIDEO = (MODAL_DIR / "video_app.py").read_text(encoding="utf-8")


def test_the_serving_qwen_image_installs_a_complete_lock() -> None:
    lines = (MODAL_DIR / "locks" / "qwen-vllm.txt").read_text(encoding="utf-8").splitlines()
    pinned = [line for line in lines if line and not line.startswith("#")]

    assert len(pinned) > 150 and all("==" in line for line in pinned)
    assert {"vllm==0.34.0", "torch==2.14.0", "transformers==5.22.2"} <= set(pinned)
    image = QWEN[QWEN.index("_qwen_vllm_image = (") : QWEN.index("_tts_image")]
    assert "qwen-vllm.txt" in image and "uv pip install --system -r /opt/locks/qwen-vllm.txt" in image
    assert 'uv_pip_install("vllm' not in image


def test_the_video_image_refuses_another_ffmpeg_series() -> None:
    assert "grep -q 'ffmpeg version 7[.]1[.]'" in VIDEO
