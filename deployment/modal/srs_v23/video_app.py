"""Dev-only L40S video-scene Modal function scaffold; LTX is not wired yet."""

from __future__ import annotations

from typing import Any

import modal

from contracts import not_configured, parse_worker_input


APP_NAME = "sketch2life-srs23-dev-video"
app = modal.App(APP_NAME)


@app.function(
    name="generate-video-scene",
    gpu="L40S",
    cpu=8.0,
    memory=32_768,
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    timeout=1_800,
    retries=0,
)
def generate_video_scene(payload: dict[str, Any]) -> None:
    """Validate a dev envelope, then fail closed until LTX is pinned and wired."""

    request = parse_worker_input(payload, execution_group="l40s-video")
    not_configured(request)


@app.function(
    name="health",
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    timeout=15,
)
def health() -> dict[str, str]:
    """CPU-only deployment check; this does not verify GPU or LTX readiness."""

    return {"status": "ok", "app": APP_NAME, "inference_ready": "false"}
