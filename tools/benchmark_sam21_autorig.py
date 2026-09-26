"""Run the approved SAM 2.1 smoke benchmark on synthetic/demo fixtures only.

The command is intentionally opt-in and never downloads a checkpoint. It measures the
process-scoped worker, serialized one image at a time, so the report can be compared with the
existing Qwen-only L4 measurements before enabling concurrency or the live adapter.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from statistics import mean

from sketch2life.infrastructure.ai.lightning_sam21 import (
    propose_colored_component_region,
)
from sketch2life.infrastructure.ai.sam21_runtime import (
    Sam21ImageSegmenter,
    Sam21RuntimeConfig,
    Sam21RuntimeError,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=1)
    args = parser.parse_args()
    if args.runs < 1 or args.warmup < 0:
        parser.error("--runs must be positive and --warmup cannot be negative")
    images = tuple(
        path
        for path in sorted(args.input_dir.rglob("*"))
        if path.suffix.casefold() in {".png", ".jpg", ".jpeg"}
    )
    if not images:
        parser.error("input directory contains no PNG/JPEG fixtures")
    segmenter = Sam21ImageSegmenter(Sam21RuntimeConfig.from_env(dict(os.environ)))
    durations: list[float] = []
    accepted = 0
    rejected = 0
    failures: dict[str, int] = {}
    for path in images:
        image = path.read_bytes()
        prompt = propose_colored_component_region(image)
        if prompt is None:
            failures["PROMPT_UNAVAILABLE"] = failures.get("PROMPT_UNAVAILABLE", 0) + 1
            continue
        for iteration in range(args.warmup + args.runs):
            _synchronize_cuda()
            started = time.perf_counter()
            try:
                result = segmenter.segment(
                    image,
                    prompt_region=prompt,
                    positive_points=(),
                    negative_points=(),
                )
            except Sam21RuntimeError as exc:
                code = type(exc).__name__.replace("Sam21", "").upper()
                failures[code] = failures.get(code, 0) + 1
                break
            finally:
                _synchronize_cuda()
            elapsed = time.perf_counter() - started
            if iteration >= args.warmup:
                durations.append(elapsed)
            if iteration == args.warmup:
                accepted += 1
                if result is not None and result.confidence < 0.5:
                    rejected += 1
    report = {
        "contractName": "Sam21SmokeBenchmarkReportV1",
        "contractVersion": "1.0",
        "model": "facebook/sam2.1-hiera-small",
        "device": os.getenv("SKETCH2LIFE_SAM21_DEVICE", "cuda"),
        "fixtureCount": len(images),
        "acceptedCount": accepted,
        "lowConfidenceCount": rejected,
        "warmP95Seconds": _percentile95(durations),
        "meanSeconds": mean(durations) if durations else None,
        "failures": failures,
        "cudaPeakAllocatedGiB": _cuda_peak_gib(),
        "serialized": True,
        "checkpointDownloaded": False,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def _synchronize_cuda() -> None:
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def _cuda_peak_gib() -> float | None:
    try:
        import torch
    except ImportError:
        return None
    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.max_memory_allocated() / (1024**3), 3)


def _percentile95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
    return round(ordered[index], 4)


if __name__ == "__main__":
    raise SystemExit(main())
