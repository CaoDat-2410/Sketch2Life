"""Dev-only L4 Modal function scaffold; inference handlers are intentionally absent."""

from __future__ import annotations

from typing import Any

import modal

from contracts import not_configured, parse_worker_input


APP_NAME = "sketch2life-srs23-dev-l4"
app = modal.App(APP_NAME)


@app.function(
    name="run-l4-stage",
    gpu="L4",
    cpu=4.0,
    memory=16_384,
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=300,
    retries=0,
)
def run_l4_stage(payload: dict[str, Any]) -> None:
    """Validate a dev envelope, then fail closed until its handler is approved."""

    request = parse_worker_input(payload, execution_group="l4")
    not_configured(request)


@app.function(
    name="health",
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=15,
)
def health() -> dict[str, str]:
    """CPU-only deployment check; this does not verify GPU or model readiness."""

    return {"status": "ok", "app": APP_NAME, "inference_ready": "false"}
