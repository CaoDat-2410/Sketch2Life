"""FEAT-094 phase 2, option A: one L40S container prepares every scene frame and then renders with LTX-2.5."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))
SOURCE = (MODAL_DIR / "video_app.py").read_text(encoding="utf-8")


def _video_app() -> Any:
    spec = importlib.util.spec_from_file_location("sketch2life_video_app_prepare", MODAL_DIR / "video_app.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Child:
    def __init__(self, events: list[str], keyframe: bytes = b"\x89PNG-keyframe") -> None:
        self.events = events
        self.keyframe = keyframe
        self.running = False
        self.bodies: list[tuple[str, dict[str, Any]]] = []

    def request(self, op: str, body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        self.events.append(f"child:{op}")
        self.running = True
        self.bodies.append((op, body))
        if op == "warmup":
            return {"loaded": ["plate", "mask"]}
        directory = Path(body["directory"])
        assert (directory / "drawing.png").read_bytes() == b"png-bytes"
        (directory / "keyframe.png").write_bytes(self.keyframe)
        return {"background": "AI", "reason": None}

    def stop(self) -> None:
        if self.running:
            self.events.append("child:stop")
        self.running = False


def _wired(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _Child, list[str]]:
    app = _video_app()
    events: list[str] = []
    child = _Child(events)
    monkeypatch.setattr(app, "_PREPARATION", child)
    monkeypatch.setattr(app, "_require_model_ready", lambda: events.append("model_ready"))
    monkeypatch.setattr(app, "_unload_pipeline", lambda: events.append("unload"))
    monkeypatch.setattr(app, "_start_checkpoint_prefetch", lambda: events.append("prefetch"))
    return app, child, events


def test_the_preparation_warm_up_checks_the_checkpoint_before_the_child_holds_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _child, events = _wired(monkeypatch)

    result = app.generate_video_scene.local({"prepare_warmup": True})

    assert result == {"warmed": True, "loaded": ["plate", "mask"]}
    assert events == ["model_ready", "unload", "child:warmup", "prefetch"]


def test_a_running_child_is_not_set_up_again(monkeypatch: pytest.MonkeyPatch) -> None:
    app, child, events = _wired(monkeypatch)
    child.running = True

    app.generate_video_scene.local({"prepare_warmup": True})

    assert events == ["child:warmup", "prefetch"]


def test_a_failed_warm_up_never_fails_the_call(monkeypatch: pytest.MonkeyPatch) -> None:
    app, child, _events = _wired(monkeypatch)

    def broken(_op: str, _body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        raise app.PrepWorkerError("SCENE_PREPARE_PROCESS_UNAVAILABLE")

    monkeypatch.setattr(child, "request", broken)

    assert app.generate_video_scene.local({"prepare_warmup": True}) == {"warmed": False, "loaded": []}


def _job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, app: Any) -> dict[str, Any]:
    from test_scene_prepare_host import _data, _stage

    ids = {"job_id": "job1", "generation_id": "gen1", "attempt_id": "att1"}
    prefix = "sketch2life/dev/job1/gen1/att1/"
    digest, size = _stage(tmp_path / prefix, _data())
    monkeypatch.setattr(app, "SCRATCH_MOUNT", str(tmp_path))
    monkeypatch.setattr(app, "scratch_volume", types.SimpleNamespace(reload=lambda: None))
    return {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": "video.scene.prepare",
        **ids,
        "attempt_prefix": prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": digest,
        "input_bytes": size,
    }


def test_a_preparation_job_answers_with_the_keyframe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app, child, events = _wired(monkeypatch)
    payload = _job(tmp_path, monkeypatch, app)

    result = app.generate_video_scene.local(payload)

    keyframe = b"\x89PNG-keyframe"
    assert result["schema_version"] == "sketch2life.modal.worker-output.v1"
    assert result["workload"] == "video.scene.prepare"
    assert (result["job_id"], result["attempt_id"]) == ("job1", "att1")
    assert result["prepare"] == {"background": "AI", "reason": None}
    assert result["asset"] == {
        "content_type": "image/png",
        "size_bytes": len(keyframe),
        "sha256": hashlib.sha256(keyframe).hexdigest(),
        "bytes": keyframe,
    }
    assert events == ["model_ready", "unload", "child:prepare"]
    assert child.bodies[0][1]["request"]["scene_index"] == 2


def test_a_child_failure_is_a_job_error_with_its_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app, child, _events = _wired(monkeypatch)
    payload = _job(tmp_path, monkeypatch, app)

    def broken(_op: str, _body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        raise app.PrepWorkerError("SCENE_PREPARE_TIMEOUT")

    monkeypatch.setattr(child, "request", broken)

    with pytest.raises(RuntimeError, match="SCENE_PREPARE_TIMEOUT"):
        app.generate_video_scene.local(payload)


def test_a_missing_checkpoint_does_not_stop_preparation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app, _child, events = _wired(monkeypatch)
    payload = _job(tmp_path, monkeypatch, app)

    def missing() -> None:
        raise RuntimeError("LTX_MODEL_NOT_STAGED")

    monkeypatch.setattr(app, "_require_model_ready", missing)

    assert app.generate_video_scene.local(payload)["prepare"]["background"] == "AI"
    assert events == ["unload", "child:prepare"]


def test_loading_the_renderer_ends_the_preparation_child_first(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _video_app()
    events: list[str] = []
    child = _Child(events)
    child.running = True
    monkeypatch.setattr(app, "_PREPARATION", child)
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: False)))
    for name in (
        "ltx_core",
        "ltx_core.quantization",
        "ltx_core.quantization.fp8_cast",
        "ltx_pipelines",
        "ltx_pipelines.utils",
        "ltx_pipelines.utils.model_paths",
        "ltx_pipelines.utils.types",
    ):
        module = types.ModuleType(name)
        module.__dict__.update(build_policy=None, DistilledPipeline=None, ModelPaths=None, OffloadMode=None)
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(app, "_read_ltx_code_commit", lambda: app.PINNED_LTX_CODE_COMMIT)
    monkeypatch.setattr(app, "_read_ltx_dependency_lock_sha256", lambda: "a" * 64)

    with pytest.raises(RuntimeError, match="LTX_GPU_UNAVAILABLE"):
        app._load_pipeline()

    assert events == ["child:stop"]


def test_memory_from_a_pipeline_that_failed_half_loaded_is_given_back(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _video_app()
    emptied: list[int] = []
    monkeypatch.setitem(
        sys.modules, "torch", types.SimpleNamespace(cuda=types.SimpleNamespace(empty_cache=lambda: emptied.append(1)))
    )
    assert app._PIPELINE is None  # loading raised before the pipeline was stored

    app._release_pipeline()

    assert emptied == [1]


def test_render_calls_still_reach_the_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _video_app()
    monkeypatch.setattr(app, "_warm_up_scene_renderer", lambda prompts: {"warmed": True, "prompts": prompts})

    assert app.generate_video_scene.local({"warmup": True}) == {"warmed": True, "prompts": []}


def test_checkpoints_read_ahead_are_not_read_a_second_time(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app = _video_app()
    for name in app.MODEL_FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(b"w")
    monkeypatch.setattr(app, "MODEL_ROOT", str(tmp_path))
    reads: list[int] = []
    original = app._read_checkpoints
    monkeypatch.setattr(app, "_read_checkpoints", lambda: reads.append(1) or original())

    app._start_checkpoint_prefetch()
    app._ensure_checkpoints_read()
    app._start_checkpoint_prefetch()
    app._ensure_checkpoints_read()

    assert reads == [1]


def test_a_failed_read_ahead_is_repeated_when_the_renderer_needs_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _video_app()
    monkeypatch.setattr(app, "MODEL_ROOT", str(tmp_path))  # no files yet

    app._start_checkpoint_prefetch()
    with pytest.raises(OSError):
        app._ensure_checkpoints_read()
    for name in app.MODEL_FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(b"w")

    app._ensure_checkpoints_read()


def test_no_other_app_still_prepares_scenes_on_a_gpu_of_its_own() -> None:
    other = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")

    assert "prepare-video-scene" not in other and "_load_scene_flux" not in other


# ------------------------------------------------------------------- the image
def test_the_image_installs_both_environments_from_committed_locks() -> None:
    assert "uv lock" not in SOURCE
    assert "uv sync --frozen --package ltx-pipelines" in SOURCE
    assert "ltx-2.5-v1.6.2.uv.lock" in SOURCE and "scene-prepare.txt" in SOURCE
    assert (MODAL_DIR / "locks" / "ltx-2.5-v1.6.2.uv.lock").stat().st_size > 100_000
    pinned = [
        line
        for line in (MODAL_DIR / "locks" / "scene-prepare.txt").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith((" ", "#"))
    ]
    assert pinned and all("==" in line for line in pinned)


def test_the_preparation_modules_are_mounted_after_the_dependency_layers() -> None:
    base = SOURCE[SOURCE.index("_worker_base_image = (") : SOURCE.index("def _with_runtime_modules")]
    assert "scene_prepare" not in base
    mounted = ast.literal_eval(
        next(
            node.value
            for node in ast.parse(SOURCE).body
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "_RUNTIME_MODULES"
        )
    )
    assert set(mounted) == {"ltx_speed.py", "scene_prepare.py", "scene_prepare_host.py", "scene_prepare_server.py"}
    assert SOURCE.count("image=_with_runtime_modules(") == SOURCE.count("    image=")
