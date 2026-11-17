#!/usr/bin/env python3
"""Run one sanitized real-provider localization smoke test."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from sketch2life.application.services.whiteboard_video_pipeline import (  # noqa: E402
    WhiteboardVideoPipelineError,
)
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1  # noqa: E402
from sketch2life.infrastructure.ai.lightning_client import (  # noqa: E402
    UrllibJsonTransport,
    read_secret_file,
)
from sketch2life.infrastructure.ai.lightning_whiteboard import (  # noqa: E402
    LightningWhiteboardLocalizationAdapter,
)
from sketch2life.infrastructure.config.settings import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="Sanitized PNG/JPEG fixture")
    parser.add_argument("--source-artifact-id", default="fixture-source-001")
    args = parser.parse_args()

    settings = get_settings()
    if settings.ai_provider != "lightning_dev":
        raise SystemExit("Set SKETCH2LIFE_AI_PROVIDER=lightning_dev for a real smoke test.")
    if not settings.lightning_ai_base_url or settings.lightning_ai_token_file is None:
        raise SystemExit("Configure the Lightning base URL and token file locally.")

    image = args.image.read_bytes()
    source_hash = hashlib.sha256(image).hexdigest()
    now = datetime.now(UTC)
    job = WhiteboardVideoJobV1(
        job_id="smoke-localization-001",
        session_id="smoke-session-001",
        experience_spec_id="smoke-spec-001",
        source_artifact_id=args.source_artifact_id,
        source_hash=source_hash,
        learning_thread_ref="smoke-thread-001",
        status="RUNNING",
        progress=1,
        current_stage="LOCALIZING",
        attempt=1,
        idempotency_key="smoke-idempotency-001",
        created_at=now,
        started_at=now,
        expires_at=now + timedelta(minutes=3),
    )
    token = read_secret_file(settings.lightning_ai_token_file)
    transport = UrllibJsonTransport(
        base_url=settings.lightning_ai_base_url,
        token=token,
        request_timeout_seconds=settings.ai_request_timeout_seconds,
    )

    def load_artifact(artifact_ref: str) -> bytes:
        if artifact_ref != args.source_artifact_id:
            raise KeyError(artifact_ref)
        return image

    adapter = LightningWhiteboardLocalizationAdapter(
        transport=transport,
        artifact_loader=load_artifact,
        endpoint_path=settings.lightning_whiteboard_localization_path,
    )
    try:
        result = adapter.localize(job)
    except WhiteboardVideoPipelineError as error:
        print(
            json.dumps(
                {
                    "smoke_test": "whiteboard_localization",
                    "status": "FAILED",
                    "error_code": error.code,
                    "retryable": error.retryable,
                    "source_hash": source_hash,
                },
                sort_keys=True,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "smoke_test": "whiteboard_localization",
                "status": "PASSED",
                "region_count": len(result.region_refs),
                "source_hash": source_hash,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
