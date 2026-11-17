"""Modal development endpoint for Sketch2Life Qwen3-VL Vision V2 only.

The Modal ASGI app deliberately registers the existing authenticated Vision V2
handler and no other provider routes. The original Lightning app remains intact.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path, PurePosixPath

import modal


APP_NAME = "sketch2life-qwen3-vl-vision-v2"
MODEL_VOLUME_NAME = "sketch2life-qwen3-vl-8b-v1"
AUTH_CONFIG_NAME = "sketch2life-modal-qwen-auth"
MODEL_VOLUME_MOUNT = "/models"
MODEL_PATH = f"{MODEL_VOLUME_MOUNT}/qwen3-vl-8b-instruct"

if modal.is_local():
    REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
    BACKEND_ROOT = REPOSITORY_ROOT / "backend"
    BACKEND_SOURCE = BACKEND_ROOT / "src"
    VISION_SERVER_SOURCE = REPOSITORY_ROOT / "tools" / "lightning_vision_v2_server.py"

REMOTE_ROOT = PurePosixPath("/opt/sketch2life")
REMOTE_BACKEND = REMOTE_ROOT / "backend"
REMOTE_VISION_SERVER = (
    REMOTE_ROOT / "sketch2life_modal" / "lightning_vision_v2_server.py"
)

model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME)
auth_secret = modal.Secret.from_name(AUTH_CONFIG_NAME)

if modal.is_local():
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .add_local_dir(
            str(BACKEND_SOURCE),
            remote_path=str(REMOTE_BACKEND / "src"),
            copy=True,
        )
        .add_local_file(
            str(BACKEND_ROOT / "pyproject.toml"),
            remote_path=str(REMOTE_BACKEND / "pyproject.toml"),
            copy=True,
        )
        .add_local_file(
            str(BACKEND_ROOT / "README.md"),
            remote_path=str(REMOTE_BACKEND / "README.md"),
            copy=True,
        )
        .add_local_file(
            str(VISION_SERVER_SOURCE),
            remote_path=str(REMOTE_VISION_SERVER),
            copy=True,
        )
        .uv_pip_install(f"{REMOTE_BACKEND}[vision-qwen]", extra_options="-e")
        .uv_pip_install("torch==2.8.0", "torchvision==0.23.0")
        .env(
            {
                "PYTHONPATH": f"{REMOTE_ROOT}:{REMOTE_BACKEND / 'src'}",
                "SKETCH2LIFE_VISION_MODEL_DIR": MODEL_PATH,
                "SKETCH2LIFE_VISION_DEVICE": "cuda",
                "SKETCH2LIFE_VISION_DEVICE_INDEX": "0",
                "SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD": "false",
            }
        )
    )
else:
    image = None

app = modal.App(APP_NAME, image=image)


@app.function(
    name="qwen-vision-v2",
    image=image,
    gpu="L40S",
    cpu=8.0,
    memory=32_768,
    volumes={
        MODEL_VOLUME_MOUNT: model_volume.with_mount_options(read_only=True),
    },
    secrets=[auth_secret],
    min_containers=0,
    max_containers=1,
    scaledown_window=30,
    startup_timeout=300,
    timeout=150,
)
@modal.asgi_app()
def qwen_vision_v2():
    """Expose only the legacy service's Qwen Vision V2 route on Modal."""

    from fastapi import FastAPI

    from sketch2life_modal import lightning_vision_v2_server as vision_server

    @asynccontextmanager
    async def lifespan(_api):
        try:
            yield
        finally:
            vision_server._QWEN_GENERATION_RUNNER.close()

    api = FastAPI(
        title="Sketch2Life Qwen3-VL Vision V2",
        version="2.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "modal-qwen3-vl-vision-v2"}

    # Reuse the original handler so authentication, admission, Qwen invocation,
    # timeouts, logging redaction and versioned response contracts stay identical.
    api.add_api_route(
        "/v2/vision",
        vision_server.vision_v2,
        methods=["POST"],
    )
    return api
