from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "docker_health_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("docker_modal_startup", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
startup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(startup)
import contracts


def test_registry_selects_only_existing_non_video_worker_apps() -> None:
    apps = startup._load_startup_apps()

    assert [app["app_name"] for app in apps] == [
        "sketch2life-srs23-drawing-vlm-dev",
        "sketch2life-srs23-language-audio-dev",
        "sketch2life-srs23-flux-image-dev",
    ]
    assert sum(len(app["workers"]) for app in apps) == 7
    assert all("video" not in worker["workload"] for app in apps for worker in app["workers"])
    assert all("segment" not in worker["workload"] for app in apps for worker in app["workers"])


def test_every_configured_worker_has_a_no_inference_warmup_handler() -> None:
    for app in startup._load_startup_apps():
        module_path = MODULE_PATH.parent / app["module"]
        module_ast = ast.parse(module_path.read_text(encoding="utf-8"))
        for worker in app["workers"]:
            function = _find_modal_function(module_ast, worker["function_name"])
            assert function is not None, worker["function_name"]
            assert any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "is_worker_warmup"
                for node in ast.walk(function)
            ), worker["function_name"]


def _find_modal_function(module_ast: ast.Module, modal_name: str) -> ast.FunctionDef | None:
    for node in module_ast.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr != "function":
                continue
            if any(
                keyword.arg == "name"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == modal_name
                for keyword in decorator.keywords
            ):
                return node
    return None


def test_worker_warmup_control_envelope_is_exact_and_contains_no_product_input() -> None:
    request = dict(contracts.WORKER_WARMUP_REQUEST)

    assert contracts.is_worker_warmup(request)
    assert not contracts.is_worker_warmup({**request, "prompt": "must not be accepted"})
    assert not contracts.is_worker_warmup({"mode": "warmup"})


def test_warmup_contract_requires_real_model_ready_without_product_inference() -> None:
    result = {
        "schema_version": "sketch2life.modal.worker-warmup.v1",
        "status": "ready",
        "mode": "warmup",
        "workload": "drawing.analyze",
        "model": {"id": "Qwen/Qwen3.5-9B", "revision": "pinned-revision"},
        "model_ready": True,
        "inference_executed": False,
        "product_output_created": False,
        "gpu_allocated": True,
    }

    assert startup._validate_warmup_result(result, "drawing.analyze") is result


@pytest.mark.parametrize(
    "changes",
    [
        {"inference_executed": True},
        {"product_output_created": True},
        {"model_ready": False},
        {"gpu_allocated": False},
        {"workload": "video.scene.generate"},
        {"product_result": {"generated": "must never be returned by warmup"}},
    ],
)
def test_warmup_contract_rejects_inference_output_or_wrong_workload(
    changes: dict[str, object],
) -> None:
    result = {
        "schema_version": "sketch2life.modal.worker-warmup.v1",
        "status": "ready",
        "mode": "warmup",
        "workload": "drawing.analyze",
        "model": {"id": "Qwen/Qwen3.5-9B", "revision": "pinned-revision"},
        "model_ready": True,
        "inference_executed": False,
        "product_output_created": False,
        "gpu_allocated": True,
        **changes,
    }

    with pytest.raises(RuntimeError, match="MODAL_WARMUP_RESULT_INVALID"):
        startup._validate_warmup_result(result, "drawing.analyze")


def test_health_contract_only_reports_deployed_app_health() -> None:
    body = {
        "status": "ok",
        "app": "sketch2life-srs23-drawing-vlm-dev",
        "health_scope": "deployed-app",
        "gpu_allocated": False,
        "inference_executed": False,
    }

    result = startup._validate_health_response(
        body, 200, "sketch2life-srs23-drawing-vlm-dev"
    )
    assert result["status"] == "READY"
    assert result["gpu_allocated"] is False

    with pytest.raises(RuntimeError, match="MODAL_HEALTH_RESPONSE_INVALID"):
        startup._validate_health_response({**body, "inference_executed": True}, 200, body["app"])


def test_controller_healthcheck_distinguishes_ready_skipped_and_degraded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_file = tmp_path / "modal-status.json"
    monkeypatch.setattr(startup, "STATE_FILE", state_file)

    for state, expected in (("READY", 0), ("SKIPPED", 0), ("STARTING", 1), ("DEGRADED", 1)):
        state_file.write_text(json.dumps({"state": state}), encoding="utf-8")
        assert startup._check() == expected
