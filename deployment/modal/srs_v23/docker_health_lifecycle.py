"""Warm configured workers in existing Modal apps without inference, then probe health."""

from __future__ import annotations

import json
import os
import re
import signal
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contracts import WORKER_WARMUP_REQUEST, WORKER_WARMUP_SCHEMA

REGISTRY_FILE = ROOT / "workloads.json"
STATE_FILE = Path("/run/sketch2life-modal-health/status.json")
WARMUP_WAIT_SECONDS = 600
HEALTH_WAIT_SECONDS = 30
_SAFE_CODE = re.compile(r"\A[A-Z][A-Z0-9_]{2,95}\Z")
_APP_NAME = re.compile(r"\A[a-z0-9][a-z0-9-]{0,62}\Z")
_FUNCTION_NAME = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}\Z")
_ALLOWED_STARTUP_WORKLOADS = frozenset(
    {
        "drawing.analyze",
        "story.generate",
        "parent.activity.suggest",
        "teacher.sketch-deck.generate",
        "lesson.plan.suggest",
        "parent.sketch-guide.generate",
        "lesson.visual.generate",
    }
)
_stop_requested = threading.Event()


def _emit(event: str, **details: object) -> None:
    print(json.dumps({"event": event, **details}, sort_keys=True), flush=True)


def _write_state(state: str, **details: object) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"state": state, **details}
    STATE_FILE.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    _emit("modal_startup_state", **payload)


def _check() -> int:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("state")
    except (OSError, json.JSONDecodeError, AttributeError):
        return 1
    return 0 if state in {"READY", "SKIPPED"} else 1


def _load_startup_apps() -> list[dict[str, Any]]:
    try:
        registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("MODAL_WORKLOAD_REGISTRY_INVALID") from exc

    startup = registry.get("local_startup") if isinstance(registry, dict) else None
    apps = startup.get("apps") if isinstance(startup, dict) else None
    if not isinstance(apps, list) or not apps:
        raise RuntimeError("MODAL_STARTUP_APPS_NOT_CONFIGURED")

    app_names: set[str] = set()
    for app in apps:
        if not isinstance(app, dict):
            raise TypeError("MODAL_STARTUP_APP_INVALID")
        app_name = app.get("app_name")
        module = app.get("module")
        health_function = app.get("health_function")
        health_path = app.get("health_path")
        workers = app.get("workers")
        if (
            not isinstance(app_name, str)
            or _APP_NAME.fullmatch(app_name) is None
            or app_name in app_names
            or not isinstance(module, str)
            or Path(module).name != module
            or not module.endswith(".py")
            or not isinstance(health_function, str)
            or _FUNCTION_NAME.fullmatch(health_function) is None
            or not isinstance(health_path, str)
            or not health_path.startswith("/")
            or "?" in health_path
            or "#" in health_path
            or not isinstance(workers, list)
            or not workers
        ):
            raise RuntimeError("MODAL_STARTUP_APP_INVALID")
        app_names.add(app_name)

        worker_names: set[str] = set()
        for worker in workers:
            if not isinstance(worker, dict):
                raise TypeError("MODAL_STARTUP_WORKER_INVALID")
            function_name = worker.get("function_name")
            workload = worker.get("workload")
            if (
                not isinstance(function_name, str)
                or _FUNCTION_NAME.fullmatch(function_name) is None
                or function_name in worker_names
                or not isinstance(workload, str)
                or workload not in _ALLOWED_STARTUP_WORKLOADS
            ):
                raise RuntimeError("MODAL_STARTUP_WORKER_INVALID")
            worker_names.add(function_name)
    return apps


def _error_code(exc: BaseException, fallback: str) -> str:
    candidate = getattr(exc, "code", None)
    if isinstance(candidate, str) and _SAFE_CODE.fullmatch(candidate):
        return candidate
    return fallback


def _validate_warmup_result(result: Any, expected_workload: str) -> dict[str, Any]:
    if (
        not isinstance(result, dict)
        or set(result)
        != {
            "schema_version",
            "status",
            "mode",
            "workload",
            "model",
            "model_ready",
            "inference_executed",
            "product_output_created",
            "gpu_allocated",
        }
        or result.get("schema_version") != WORKER_WARMUP_SCHEMA
        or result.get("status") != "ready"
        or result.get("mode") != "warmup"
        or result.get("workload") != expected_workload
        or result.get("model_ready") is not True
        or result.get("inference_executed") is not False
        or result.get("product_output_created") is not False
        or result.get("gpu_allocated") is not True
    ):
        raise RuntimeError("MODAL_WARMUP_RESULT_INVALID")
    model = result.get("model")
    if (
        not isinstance(model, dict)
        or set(model) != {"id", "revision"}
        or not isinstance(model.get("id"), str)
        or not model["id"].strip()
        or not isinstance(model.get("revision"), str)
        or not model["revision"].strip()
    ):
        raise RuntimeError("MODAL_WARMUP_MODEL_IDENTITY_INVALID")
    return result


def _is_timeout(exc: BaseException) -> bool:
    return isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower()


def _cancel_warmup_call(call: Any, app_name: str, function_name: str, reason: str) -> None:
    try:
        call.cancel()
    except Exception as exc:  # noqa: BLE001 - cancellation errors must not hide startup status
        _emit(
            "modal_worker_warmup_cancel_failed",
            app_name=app_name,
            function_name=function_name,
            reason=reason,
            error_type=type(exc).__name__,
        )


def _wait_for_warmup_call(call: Any, app_name: str, function_name: str) -> Any:
    deadline = time.monotonic() + WARMUP_WAIT_SECONDS
    while True:
        if _stop_requested.is_set():
            _cancel_warmup_call(call, app_name, function_name, "shutdown")
            raise RuntimeError("MODAL_WARMUP_CANCELLED_ON_SHUTDOWN")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _cancel_warmup_call(call, app_name, function_name, "timeout")
            raise TimeoutError("MODAL_WARMUP_TIMEOUT")
        try:
            return call.get(timeout=min(5, remaining))
        except Exception as exc:
            if type(exc).__name__ == "TimeoutError" and time.monotonic() < deadline:
                continue
            raise


def _warm_deployed_workers(
    modal_module: Any,
    deployed_apps: list[dict[str, Any]],
    environment: str,
) -> list[dict[str, Any]]:
    pending: list[tuple[str, dict[str, Any], Any, float]] = []
    results: list[dict[str, Any]] = []

    # Submit every approved warmup before waiting so that the first worker does not
    # scale down while later model pools are still cold-starting.
    for app_spec in deployed_apps:
        app_name = app_spec["app_name"]
        for worker in app_spec["workers"]:
            function_name = worker["function_name"]
            workload = worker["workload"]
            started_at = time.monotonic()
            try:
                function = modal_module.Function.from_name(
                    app_name, function_name, environment_name=environment
                )
                call = function.spawn(dict(WORKER_WARMUP_REQUEST))
            except Exception as exc:  # noqa: BLE001 - any Modal submission failure degrades this optional sidecar
                result = {
                    "app_name": app_name,
                    "function_name": function_name,
                    "workload": workload,
                    "status": "FAILED",
                    "error_type": type(exc).__name__,
                    "error_code": _error_code(exc, "MODAL_WARMUP_SUBMIT_FAILED"),
                }
                results.append(result)
                _emit("modal_worker_warmup_failed", **result)
                continue
            pending.append((app_name, worker, call, started_at))
            _emit(
                "modal_worker_warmup_submitted",
                app_name=app_name,
                function_name=function_name,
                workload=workload,
                inference_executed=False,
            )

    if not pending:
        return results

    with ThreadPoolExecutor(max_workers=len(pending)) as executor:
        futures = {
            executor.submit(
                _wait_for_warmup_call, call, app_name, worker["function_name"]
            ): (app_name, worker, call, started_at)
            for app_name, worker, call, started_at in pending
        }
        for future in as_completed(futures):
            app_name, worker, call, started_at = futures[future]
            function_name = worker["function_name"]
            workload = worker["workload"]
            elapsed_ms = round((time.monotonic() - started_at) * 1000)
            try:
                result = _validate_warmup_result(future.result(), workload)
            except Exception as exc:  # noqa: BLE001 - remote worker failures are reported per workload
                timed_out = _is_timeout(exc)
                if timed_out:
                    _cancel_warmup_call(call, app_name, function_name, "timeout")
                outcome = {
                    "app_name": app_name,
                    "function_name": function_name,
                    "workload": workload,
                    "status": "FAILED",
                    "elapsed_ms": elapsed_ms,
                    "error_type": type(exc).__name__,
                    "error_code": _error_code(
                        exc,
                        "MODAL_WARMUP_TIMEOUT" if timed_out else "MODAL_WARMUP_FAILED",
                    ),
                }
                results.append(outcome)
                _emit("modal_worker_warmup_failed", **outcome)
                continue

            outcome = {
                "app_name": app_name,
                "function_name": function_name,
                "workload": workload,
                "status": "READY",
                "elapsed_ms": elapsed_ms,
                "model_id": result["model"]["id"],
                "model_revision": result["model"]["revision"],
                "gpu_allocated": result["gpu_allocated"],
                "inference_executed": result["inference_executed"],
                "product_output_created": result["product_output_created"],
            }
            results.append(outcome)
            _emit("modal_worker_warmup_ready", **outcome)
    return results


def _validate_health_response(body: Any, status: int, app_name: str) -> dict[str, Any]:
    if (
        status != 200
        or not isinstance(body, dict)
        or body.get("status") != "ok"
        or body.get("app") != app_name
        or body.get("health_scope") != "deployed-app"
        or body.get("gpu_allocated") is not False
        or body.get("inference_executed") is not False
    ):
        raise RuntimeError("MODAL_HEALTH_RESPONSE_INVALID")
    return {
        "app_name": app_name,
        "status": "READY",
        "health_scope": body["health_scope"],
        "gpu_allocated": body["gpu_allocated"],
        "inference_executed": body["inference_executed"],
    }


def _probe_app_health(
    modal_module: Any, app_spec: dict[str, Any], environment: str
) -> dict[str, Any]:
    app_name = app_spec["app_name"]
    function = modal_module.Function.from_name(
        app_name, app_spec["health_function"], environment_name=environment
    )
    base_url = function.get_web_url()
    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        raise RuntimeError("MODAL_HEALTH_URL_UNAVAILABLE")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{app_spec['health_path']}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=HEALTH_WAIT_SECONDS) as response:
        body = json.loads(response.read().decode("utf-8"))
        status = response.status
    return {
        **_validate_health_response(body, status, app_name),
        "health_path": app_spec["health_path"],
    }


def _stop_handler(_signal: int, _frame: object) -> None:
    _stop_requested.set()


def _wait_for_shutdown() -> None:
    while not _stop_requested.wait(timeout=1):
        pass


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        return _check()

    signal.signal(signal.SIGTERM, _stop_handler)
    signal.signal(signal.SIGINT, _stop_handler)
    token_id = os.getenv("MODAL_TOKEN_ID", "").strip()
    token_secret = os.getenv("MODAL_TOKEN_SECRET", "").strip()
    if not token_id or not token_secret:
        _write_state("SKIPPED", reason="modal_credentials_not_configured")
        _wait_for_shutdown()
        return 0

    environment = os.getenv("SKETCH2LIFE_MODAL_ENVIRONMENT", "dev").strip() or "dev"
    os.environ["MODAL_ENVIRONMENT"] = environment
    warmup_results: list[dict[str, Any]] = []
    app_results: list[dict[str, Any]] = []
    try:
        apps = _load_startup_apps()
        _write_state(
            "STARTING",
            environment=environment,
            app_count=len(apps),
            worker_count=sum(len(app["workers"]) for app in apps),
            inference_executed=False,
        )
        import modal

        _emit(
            "modal_existing_apps_selected",
            app_names=[app["app_name"] for app in apps],
            deployment_action="none",
            stop_action="none",
        )
        warmup_results = _warm_deployed_workers(modal, apps, environment)
        for app_spec in apps:
            app_name = app_spec["app_name"]
            try:
                health = _probe_app_health(modal, app_spec, environment)
                _emit("modal_app_health_ready", **health)
            except Exception as exc:  # noqa: BLE001 - health endpoint/provider failures degrade only this app
                health = {
                    "app_name": app_name,
                    "status": "FAILED",
                    "error_type": type(exc).__name__,
                    "error_code": _error_code(exc, "MODAL_HEALTH_PROBE_FAILED"),
                }
                _emit("modal_app_health_failed", **health)
            app_results.append({"app_name": app_name, **health})
    except Exception as exc:  # noqa: BLE001 - Modal is an optional external dependency for local startup
        _emit(
            "modal_startup_failed",
            error_type=type(exc).__name__,
            error_code=_error_code(exc, "MODAL_STARTUP_FAILED"),
        )
        app_results.append({"status": "FAILED", "error_type": type(exc).__name__})

    failures = any(
        app.get("status") != "READY" for app in app_results
    ) or any(result.get("status") != "READY" for result in warmup_results)
    final_state = "DEGRADED" if failures or len(app_results) == 0 else "READY"
    _write_state(
        final_state,
        environment=environment,
        apps=app_results,
        workers=warmup_results,
        inference_executed=False,
        product_output_created=False,
        deployment_action="none_existing_apps_only",
        min_gpu_containers=0,
        shutdown_action="none_shared_apps_preserved",
    )
    _wait_for_shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
