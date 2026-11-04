"""Generate a deterministic synthetic drawing and run the approved Modal smoke."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import sys
import time
import uuid
import zlib
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
FEATURE_DIR = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]
FIXTURE_PATH = FEATURE_DIR / "evidence" / "assets" / "drawing_vlm_synthetic_butterfly.png"
APP_NAME = "sketch2life-srs23-drawing-vlm-dev"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
INPUT_SCHEMA = "sketch2life.modal.drawing-input.v1"
WORKER_INPUT_SCHEMA = "sketch2life.modal.worker-input.v1"
MAX_STAGED_INPUT_BYTES = 48 * 1024 * 1024
CANVAS_SIZE = 512


def _set_pixel(pixels: bytearray, x: int, y: int, *, width: int = 512) -> None:
    if 0 <= x < width and 0 <= y < width:
        offset = (y * width + x) * 3
        pixels[offset : offset + 3] = b"\x18\x18\x18"


def _draw_line(
    pixels: bytearray,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    thickness: int = 5,
) -> None:
    x0, y0 = start
    x1, y1 = end
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    error = dx - dy
    radius = thickness // 2
    while True:
        for oy in range(-radius, radius + 1):
            for ox in range(-radius, radius + 1):
                if ox * ox + oy * oy <= radius * radius + 1:
                    _set_pixel(pixels, x0 + ox, y0 + oy)
        if x0 == x1 and y0 == y1:
            break
        twice_error = error * 2
        if twice_error > -dy:
            error -= dy
            x0 += sx
        if twice_error < dx:
            error += dx
            y0 += sy


def _draw_path(pixels: bytearray, points: list[tuple[int, int]], *, close: bool = False) -> None:
    pairs = list(zip(points, points[1:]))
    if close and len(points) > 1:
        pairs.append((points[-1], points[0]))
    for start, end in pairs:
        _draw_line(pixels, start, end)


def _circle_points(cx: int, cy: int, radius: int, steps: int = 40) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for i in range(steps):
        # Integer-only approximation to a small circular head.
        x = round(cx + radius * ((steps - 2 * i) / steps))
        y_square = max(radius * radius - (x - cx) * (x - cx), 0)
        y = round(cy + (1 if i < steps // 2 else -1) * (y_square**0.5))
        points.append((x, y))
    return points


def generate_fixture(path: Path = FIXTURE_PATH) -> tuple[str, int]:
    """Write a plain RGB PNG with a deterministic butterfly outline."""

    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = bytearray(b"\xff" * (CANVAS_SIZE * CANVAS_SIZE * 3))

    upper_left = [
        (256, 224),
        (231, 183),
        (199, 145),
        (160, 124),
        (125, 130),
        (108, 158),
        (117, 190),
        (151, 214),
        (198, 226),
        (238, 231),
    ]
    lower_left = [
        (256, 235),
        (226, 248),
        (196, 271),
        (184, 304),
        (195, 332),
        (220, 333),
        (241, 304),
        (254, 266),
    ]
    mirror = lambda points: [(CANVAS_SIZE - x, y) for x, y in points]
    for outline in (upper_left, mirror(upper_left), lower_left, mirror(lower_left)):
        _draw_path(pixels, outline, close=True)

    _draw_path(pixels, [(256, 205), (256, 320)])
    _draw_path(pixels, _circle_points(256, 198, 11), close=True,)
    _draw_path(pixels, [(251, 195), (238, 175), (222, 164)])
    _draw_path(pixels, [(261, 195), (274, 175), (290, 164)])
    for endpoint in ((124, 164), (157, 193), (198, 211), (224, 268), (206, 309)):
        _draw_line(pixels, (254, 235), endpoint, thickness=3)
        _draw_line(pixels, (258, 235), (CANVAS_SIZE - endpoint[0], endpoint[1]), thickness=3)

    raw = b"".join(
        b"\x00" + pixels[y * CANVAS_SIZE * 3 : (y + 1) * CANVAS_SIZE * 3]
        for y in range(CANVAS_SIZE)
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", CANVAS_SIZE, CANVAS_SIZE, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    return hashlib.sha256(png).hexdigest(), len(png)


def _download_model() -> None:
    import modal

    function = modal.Function.from_name(
        APP_NAME,
        "download-pinned-model",
        environment_name="dev",
    )
    print(json.dumps(function.remote(), ensure_ascii=False, sort_keys=True))


def _validate_payload(payload: dict[str, Any]) -> None:
    contract_dir = REPO_ROOT / "deployment" / "modal" / "srs_v23"
    sys.path.insert(0, str(contract_dir))
    from contracts import parse_worker_input

    request = parse_worker_input(payload, execution_group="l4")
    if request.workload != "drawing.analyze":
        raise ValueError("POC payload must use drawing.analyze")


def _run_one_inference() -> None:
    import modal

    fixture_sha256, fixture_size = generate_fixture()
    fixture_bytes = FIXTURE_PATH.read_bytes()
    job_id = "modal-vlm-poc-20261103"
    generation_id = "synthetic-butterfly-v1"
    attempt_id = f"attempt-{uuid.uuid4().hex[:12]}"
    attempt_prefix = f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/"

    manifest = {
        "schema_version": INPUT_SCHEMA,
        "asset": {
            "path": "input/drawing.png",
            "content_type": "image/png",
            "size_bytes": fixture_size,
            "sha256": fixture_sha256,
        },
    }
    manifest_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    input_bytes = len(fixture_bytes) + len(manifest_bytes)
    if input_bytes > MAX_STAGED_INPUT_BYTES:
        raise ValueError("Synthetic input exceeds the SRS Modal staging cap")

    payload: dict[str, Any] = {
        "schema_version": WORKER_INPUT_SCHEMA,
        "environment": "dev",
        "workload": "drawing.analyze",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "input_bytes": input_bytes,
    }
    _validate_payload(payload)

    volume = modal.Volume.from_name(
        SCRATCH_VOLUME_NAME,
        environment_name="dev",
        version=2,
    )
    try:
        with volume.batch_upload() as batch:
            batch.put_file(FIXTURE_PATH, f"/{attempt_prefix}input/drawing.png")
            batch.put_file(
                io.BytesIO(manifest_bytes),
                f"/{attempt_prefix}input/manifest.json",
            )

        function = modal.Function.from_name(
            APP_NAME,
            "analyze-drawing",
            environment_name="dev",
        )
        started = time.perf_counter()
        result = function.remote(payload)
        elapsed_seconds = round(time.perf_counter() - started, 3)
        if (
            not isinstance(result, dict)
            or result.get("schema_version") != "sketch2life.modal.worker-output.v1"
            or result.get("input_sha256") != fixture_sha256
            or result.get("result", {}).get("adult_confirmation_required") is not True
        ):
            raise RuntimeError("Modal smoke returned an invalid output envelope")
        print(
            json.dumps(
                {
                    "fixture_path": str(FIXTURE_PATH),
                    "fixture_sha256": fixture_sha256,
                    "fixture_bytes": fixture_size,
                    "inference_requests": 1,
                    "elapsed_seconds_including_cold_start": elapsed_seconds,
                    "result": result,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    finally:
        volume.remove_file(f"{attempt_prefix}input", recursive=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--download-model", action="store_true")
    group.add_argument("--invoke", action="store_true")
    args = parser.parse_args()
    if args.download_model:
        _download_model()
    else:
        _run_one_inference()


if __name__ == "__main__":
    main()
