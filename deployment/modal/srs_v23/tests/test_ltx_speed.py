"""FEAT-094 phase 2 / ADR-0026: the fast LTX profile, its prompt cache and its fall-back."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import ltx_speed  # noqa: E402


class _Encoder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.marker = "real"

    def __call__(self, prompts: list[str], **_kwargs: Any) -> list[str]:
        self.calls.append(list(prompts))
        return [f"encoded:{prompt}" for prompt in prompts]


def test_all_prompts_of_a_video_are_encoded_in_one_call() -> None:
    encoder = _Encoder()
    cache = ltx_speed.PromptCache(encoder)

    cache.prepare(["a", "b", "a"])

    assert encoder.calls == [["a", "b"]]
    assert cache(["b"], enhance_first_prompt=False) == ["encoded:b"]
    assert cache(["a"]) == ["encoded:a"]
    assert encoder.calls == [["a", "b"]]


def test_an_unknown_prompt_is_encoded_when_the_pipeline_asks_for_it() -> None:
    encoder = _Encoder()
    cache = ltx_speed.PromptCache(encoder)

    assert cache(["new"]) == ["encoded:new"]
    assert encoder.calls == [["new"]]
    assert cache.marker == "real"  # other attributes come from the real block


def test_the_cache_keeps_only_the_latest_video() -> None:
    cache = ltx_speed.PromptCache(_Encoder(), limit=2)

    cache.prepare(["a", "b"])
    cache.prepare(["c"])

    assert cache.cached_prompts() == ("b", "c")


def test_prompt_enhancement_is_never_served_from_the_cache() -> None:
    cache = ltx_speed.PromptCache(_Encoder())

    with pytest.raises(ValueError, match="LTX_PROMPT_ENHANCEMENT_NOT_SUPPORTED"):
        cache(["a"], enhance_first_prompt=True)


class OutOfMemoryError(RuntimeError):
    pass


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (OutOfMemoryError("x"), True),
        (RuntimeError("CUDA out of memory. Tried to allocate 2 GiB"), True),
        (RuntimeError("something else"), False),
        (ValueError("out of range"), False),
    ],
)
def test_out_of_memory_is_recognised(error: BaseException, expected: bool) -> None:
    assert ltx_speed.is_out_of_memory(error) is expected


def test_a_fast_render_that_runs_out_of_memory_is_repeated_with_the_safe_profile() -> None:
    profiles = ltx_speed.ProfileSwitch()
    released: list[str] = []
    used: list[str] = []

    def render() -> str:
        used.append(profiles.current)
        if profiles.current == ltx_speed.FAST:
            raise OutOfMemoryError("CUDA out of memory")
        return "clip"

    assert ltx_speed.render_with_fallback(profiles, render, release=lambda: released.append("gpu")) == "clip"
    assert used == [ltx_speed.FAST, ltx_speed.SAFE]
    assert released == ["gpu"]
    # The container stays on the safe profile for the following scenes.
    assert profiles.current == ltx_speed.SAFE


def test_other_failures_and_a_safe_profile_failure_are_not_repeated() -> None:
    released: list[str] = []
    profiles = ltx_speed.ProfileSwitch()
    attempts: list[int] = []

    def broken() -> None:
        attempts.append(1)
        raise RuntimeError("broken")

    with pytest.raises(RuntimeError, match="broken"):
        ltx_speed.render_with_fallback(profiles, broken, release=lambda: released.append("gpu"))
    assert len(attempts) == 1 and not released

    def always_out_of_memory() -> None:
        attempts.append(1)
        raise OutOfMemoryError("CUDA out of memory")

    attempts.clear()
    with pytest.raises(OutOfMemoryError):
        ltx_speed.render_with_fallback(profiles, always_out_of_memory, release=lambda: None)
    assert len(attempts) == 2


@pytest.mark.parametrize(
    ("payload", "prompts"),
    [
        ({"warmup": True}, []),
        ({"warmup": True, "prompts": ["a", "b"]}, ["a", "b"]),
        ({"job_id": "x"}, None),
        ({}, None),
    ],
)
def test_the_warm_up_payload_is_recognised(payload: dict[str, Any], prompts: list[str] | None) -> None:
    assert ltx_speed.warm_up_prompts(payload) == prompts


@pytest.mark.parametrize(
    "payload",
    [
        {"warmup": True, "prompts": "a"},
        {"warmup": True, "prompts": ["a"] * 16},
        {"warmup": True, "prompts": ["x" * 1_501]},
        {"warmup": True, "prompts": ["  "]},
        {"warmup": True, "job_id": "x"},
    ],
)
def test_a_malformed_warm_up_payload_is_refused(payload: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="MODAL_INPUT_NOT_ALLOWED"):
        ltx_speed.warm_up_prompts(payload)


def _video_app_with_fake_ltx(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list[dict[str, Any]]]:
    """Import the video worker with stand-ins for torch and the pinned LTX packages."""

    built: list[dict[str, Any]] = []

    class _OffloadMode:
        CPU = "cpu"
        NONE = "none"

    class _Pipeline:
        def __init__(self, **arguments: Any) -> None:
            built.append(arguments)
            self.prompt_encoder = type("E", (), {"_offload_mode": arguments["offload_mode"]})()
            self.stage = type("S", (), {"_active_weights": None})()

    def module(name: str, **members: Any) -> None:
        fake = types.ModuleType(name)
        fake.__dict__.update(members)
        monkeypatch.setitem(sys.modules, name, fake)

    cuda = types.SimpleNamespace(is_available=lambda: True)
    module("torch", cuda=cuda)
    for name in ("ltx_core", "ltx_core.quantization", "ltx_core.model", "ltx_core.model.video_vae",
                 "ltx_pipelines", "ltx_pipelines.utils"):
        module(name)
    sys.modules["ltx_pipelines"].DistilledPipeline = _Pipeline
    module("ltx_core.quantization.fp8_cast", build_policy=lambda _path: "fp8")
    module("ltx_core.model.video_vae.transformer", DiffVAEMode=lambda value: f"mode:{value}")
    module("ltx_pipelines.utils.model_paths", ModelPaths=types.SimpleNamespace(from_split=lambda **kw: kw))
    module("ltx_pipelines.utils.types", OffloadMode=_OffloadMode)
    spec = importlib.util.spec_from_file_location("sketch2life_video_app_speed", MODAL_DIR / "video_app.py")
    assert spec is not None and spec.loader is not None
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "_read_ltx_code_commit", lambda: app.PINNED_LTX_CODE_COMMIT)
    monkeypatch.setattr(app, "_read_ltx_dependency_lock_sha256", lambda: "0" * 64)
    return app, built


def test_the_worker_builds_the_fast_pipeline_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    app, built = _video_app_with_fake_ltx(monkeypatch)

    pipeline = app._load_pipeline()

    assert built[0]["offload_mode"] == "none"
    assert built[0]["diffvae_optimization"] == "mode:combined_compile"
    assert pipeline.stage._active_weights == {}
    assert isinstance(pipeline.prompt_encoder, ltx_speed.PromptCache)
    # Only the text encoder keeps streaming through the CPU: loaded whole it did not fit.
    assert pipeline.prompt_encoder._offload_mode == "cpu"
    assert app._load_pipeline() is pipeline and len(built) == 1


def test_after_a_fall_back_the_worker_builds_the_earlier_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    app, built = _video_app_with_fake_ltx(monkeypatch)
    app._load_pipeline()

    app._PROFILES.fall_back()
    app._release_pipeline()
    pipeline = app._load_pipeline()

    assert built[1]["offload_mode"] == "cpu"
    assert "diffvae_optimization" not in built[1]
    assert pipeline.stage._active_weights is None
    assert not isinstance(pipeline.prompt_encoder, ltx_speed.PromptCache)
