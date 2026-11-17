from __future__ import annotations

import hashlib
import io
import json
import time
import uuid
from pathlib import Path
from typing import Any

import modal

APP_NAME = "sketch2life-rev52-scratch-visibility-probe"
VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
MOUNT_PATH = "/scratch"
PROBE_CONTENT = b"sketch2life-rev52-scratch-volume-probe"

app = modal.App(APP_NAME)
scratch_volume = modal.Volume.from_name(
    VOLUME_NAME, environment_name="dev", version=2
)


@app.function(
    name="read-scratch-after-reload",
    image=modal.Image.debian_slim(),
    volumes={MOUNT_PATH: scratch_volume.with_mount_options(read_only=True)},
    cpu=1.0,
    memory=1024,
    timeout=120,
    retries=0,
)
def read_scratch_after_reload(
    probe_prefix: str, expected_size: int, expected_sha256: str
) -> dict[str, Any]:
    scratch_volume.reload()
    marker_path = (Path(MOUNT_PATH) / probe_prefix / "marker.bin").resolve()
    scratch_root = Path(MOUNT_PATH).resolve()
    if not marker_path.is_relative_to(scratch_root):
        return {"outcome": "PATH_SCOPE_INVALID"}
    if not marker_path.is_file():
        return {"outcome": "FILE_MISSING_AFTER_RELOAD"}
    content = marker_path.read_bytes()
    return {
        "outcome": "SUCCEEDED",
        "size_matches": len(content) == expected_size,
        "sha256_matches": hashlib.sha256(content).hexdigest() == expected_sha256,
        "observed_size_bytes": len(content),
    }


@app.local_entrypoint()
def main() -> None:
    probe_prefix = f"diagnostics/rev52/{uuid.uuid4().hex}"
    expected_sha256 = hashlib.sha256(PROBE_CONTENT).hexdigest()
    started = time.perf_counter()
    call_id: str | None = None
    terminal = False
    try:
        with scratch_volume.batch_upload() as batch:
            batch.put_file(
                io.BytesIO(PROBE_CONTENT),
                f"/{probe_prefix}/marker.bin",
            )
        call = read_scratch_after_reload.spawn(
            probe_prefix, len(PROBE_CONTENT), expected_sha256
        )
        call_id = getattr(call, "object_id", None)
        output = call.get(timeout=120)
        terminal = True
        result = output if isinstance(output, dict) else {"outcome": "INVALID_OUTPUT"}
    except Exception as exc:  # noqa: BLE001 - persist only exception class.
        result = {"outcome": "FAILED", "error_type": type(exc).__name__}
    finally:
        if terminal:
            scratch_volume.remove_file(probe_prefix, recursive=True)
    print(
        json.dumps(
            {
                "app": APP_NAME,
                "call_id": call_id,
                "probe_duration_ms": round((time.perf_counter() - started) * 1000, 2),
                **result,
            },
            ensure_ascii=True,
            sort_keys=True,
        ),
        flush=True,
    )
