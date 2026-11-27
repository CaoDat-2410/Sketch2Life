"""FEAT-098 B2: the speed options of the scene renderer are off unless named, and keep the delivered clip profile."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import render_options  # noqa: E402
from test_ltx_speed import _video_app_with_fake_ltx  # noqa: E402
from test_video_keyframe_conditioning import fake_ltx  # noqa: E402,F401  (a fixture)


def test_nothing_is_switched_on_by_default() -> None:
    options = render_options.parse_options("")

    assert options == render_options.RenderOptions()
    assert (options.width, options.height, options.fps) == (1280, 768, 24)
    assert options.names == ()


def test_options_are_named_in_one_setting() -> None:
    options = render_options.parse_options(" small, fps16 ,conv_vae")

    assert options.names == ("conv_vae", "small", "fps16")
    # Two-stage LTX needs multiples of 64, so the smaller size is 960x576 (not 960x544).
    assert (options.width, options.height, options.fps) == (960, 576, 16)
    assert options.width % 64 == 0 and options.height % 64 == 0


def test_the_accepted_options_are_the_ones_the_owner_chose() -> None:
    assert render_options.parse_options(render_options.ACCEPTED).names == ("conv_vae", "small")


def test_a_deploy_can_switch_every_option_off() -> None:
    assert render_options.parse_options("none") == render_options.RenderOptions()


def test_an_unknown_option_is_refused() -> None:
    with pytest.raises(ValueError, match="VIDEO_RENDER_OPTION_UNKNOWN"):
        render_options.parse_options("smal")


def test_the_default_filter_is_the_one_used_before() -> None:
    filters = render_options.parse_options("").video_filter(target_frame_count=240, generated_frame_count=241)

    assert filters == (
        "setpts=PTS*0.995850622407,crop=1280:720:0:24,fps=24,trim=end_frame=240,setpts=N/(24*TB)"
    )


def test_a_small_render_is_cropped_to_widescreen_and_scaled_up() -> None:
    filters = render_options.parse_options("small").video_filter(target_frame_count=240, generated_frame_count=241)

    assert "crop=960:540:0:18,scale=1280:720:flags=lanczos," in filters


def test_sixteen_frames_a_second_are_interpolated_to_twenty_four() -> None:
    filters = render_options.parse_options("fps16").video_filter(target_frame_count=240, generated_frame_count=161)

    # 161 frames at 16 fps cover the 10 s target.
    assert filters.startswith(f"setpts=PTS*{(240 / 24) / (161 / 16):.12f},")
    assert "minterpolate=fps=24" in filters and "tpad=stop_mode=clone" in filters
    assert filters.index("tpad") < filters.index("trim=end_frame=240")


def _ltx_call(app: Any, fake: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    pipeline, seen, tmp = fake
    plan = app._run_ltx(
        pipeline=pipeline,
        image_path=tmp / "k0.png",
        output_path=tmp / "o.mp4",
        visual_prompt="p",
        seed=1,
        target_duration=10.0,
        prompt_is_compiled=True,
    )
    return plan, seen


def _video_app() -> Any:
    spec = importlib.util.spec_from_file_location("sketch2life_video_app_options", MODAL_DIR / "video_app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("text", "size", "rate", "frames"),
    [("", (1280, 768), 24, 241), ("small", (960, 576), 24, 241), ("fps16", (1280, 768), 16, 161)],
)
def test_the_renderer_asks_ltx_for_the_chosen_size_and_rate(
    monkeypatch: pytest.MonkeyPatch,
    fake_ltx: Any,  # noqa: F811
    text: str,
    size: tuple[int, int],
    rate: int,
    frames: int,
) -> None:
    app = _video_app()
    monkeypatch.setattr(app, "_OPTIONS", render_options.parse_options(text))

    plan, seen = _ltx_call(app, fake_ltx)

    assert (seen["width"], seen["height"], seen["frame_rate"], seen["num_frames"]) == (*size, rate, frames)
    assert plan["generated_frame_count"] == frames and plan["target_frame_count"] == 240


def test_the_clip_is_normalised_with_the_chosen_filter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app = _video_app()
    options = render_options.parse_options("small,fps16")
    monkeypatch.setattr(app, "_OPTIONS", options)
    commands: list[list[str]] = []
    destination = tmp_path / "clip.mp4"

    def run(command: list[str], **_options: Any) -> Any:
        commands.append(command)
        destination.write_bytes(b"x")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", run)

    app._normalize_silent_clip(tmp_path / "raw.mp4", destination, target_duration=10.0, generated_frame_count=161)

    command = commands[0]
    assert command[command.index("-vf") + 1] == options.video_filter(
        target_frame_count=240, generated_frame_count=161
    )


@pytest.mark.parametrize("text", ["", "small,fps16"])
def test_a_real_ffmpeg_run_keeps_the_clip_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str
) -> None:
    imageio_ffmpeg = pytest.importorskip("imageio_ffmpeg")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    app = _video_app()
    options = render_options.parse_options(text)
    monkeypatch.setattr(app, "_OPTIONS", options)
    raw, clip = tmp_path / "raw.mp4", tmp_path / "clip.mp4"
    frames = 49 if options.fps == 24 else 33  # about two seconds
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         f"testsrc2=size={options.width}x{options.height}:rate={options.fps}",
         "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(raw)],
        check=True,
    )
    real_run = subprocess.run
    monkeypatch.setattr(app.subprocess, "run", lambda command, **kw: real_run([ffmpeg, *command[1:]], **kw))

    app._normalize_silent_clip(raw, clip, target_duration=2.0, generated_frame_count=frames)

    listing = real_run(
        [ffmpeg, "-loglevel", "error", "-i", str(clip), "-f", "framemd5", "-"],
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert "#tb 0: 1/24" in listing and "#dimensions 0: 1280x720" in listing
    assert len([line for line in listing if not line.startswith("#")]) == 48


def test_the_convolution_vae_replaces_the_diffusion_vae(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app, built = _video_app_with_fake_ltx(monkeypatch)
    monkeypatch.setattr(app, "_OPTIONS", render_options.parse_options("conv_vae"))
    monkeypatch.setattr(app, "MODEL_ROOT", str(tmp_path))
    vae = tmp_path / app.CONV_VAE_FILE
    vae.parent.mkdir(parents=True)
    vae.write_bytes(b"w")

    app._load_pipeline()

    assert Path(built[0]["model_paths"]["video_vae_path"]) == vae
    assert "diffvae_optimization" not in built[0]
    assert app.CONV_VAE_FILE not in app.MODEL_FILES  # the verified checkpoint pack is unchanged


def test_a_missing_convolution_vae_is_named(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app, _built = _video_app_with_fake_ltx(monkeypatch)
    monkeypatch.setattr(app, "_OPTIONS", render_options.parse_options("conv_vae"))
    monkeypatch.setattr(app, "MODEL_ROOT", str(tmp_path))

    with pytest.raises(RuntimeError, match="LTX_CONV_VAE_NOT_STAGED"):
        app._load_pipeline()


def test_the_prefetch_reads_the_vae_that_will_be_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _video_app()
    assert app._checkpoint_names() == list(app.MODEL_FILES)

    monkeypatch.setattr(app, "_OPTIONS", render_options.parse_options("conv_vae"))

    names = app._checkpoint_names()
    assert app.CONV_VAE_FILE in names and "vae/ltx-2.5-video-vae-bf16.safetensors" not in names


def test_the_image_carries_the_setting_given_at_deploy_time() -> None:
    source = (MODAL_DIR / "video_app.py").read_text(encoding="utf-8")

    # A deploy that names nothing gets the options the owner accepted from the measured clips.
    assert "render_options.OPTIONS_ENV: os.environ.get(render_options.OPTIONS_ENV, render_options.ACCEPTED)" in source
    assert 'name="download-ltx25-conv-vae"' in source
