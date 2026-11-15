"""One-shot synthetic Parent route runner for the approved Rev87.26/27 checks."""

from __future__ import annotations

import contextlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_DIR = Path(__file__).resolve().parent
ATTEMPT_NAME = os.environ.get("REV87_26_ATTEMPT", "attempt_001")
if ATTEMPT_NAME not in {"attempt_001", "attempt_002", "attempt_003"}:
    raise RuntimeError("REV87_26_27_ATTEMPT_OUT_OF_BOUNDS")
ATTEMPT_DIR = EVIDENCE_DIR / ATTEMPT_NAME
ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
WORKTREE_ROOT = EVIDENCE_DIR.parents[3]
sys.path.insert(0, str(WORKTREE_ROOT / "backend" / "src"))
sys.path.append(r"<repo-root>\.venv-modal\Lib\site-packages")

os.environ["SKETCH2LIFE_ENV"] = "local"
os.environ["SKETCH2LIFE_AI_PROVIDER"] = "modal_dev"
os.environ["SKETCH2LIFE_SVG_TOPIC_STROKE_GUIDE_GENERATION_ENABLED"] = "true"

from fastapi import HTTPException  # noqa: E402

from sketch2life.application.ports.identity import VerifiedPrincipal  # noqa: E402
from sketch2life.contracts.schemas.svg_engine import SvgTopicStrokeGuideRequestV1  # noqa: E402
from sketch2life.interfaces.http.routers import parent_ai  # noqa: E402


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    request = SvgTopicStrokeGuideRequestV1(topic="con mèo", difficulty="beginner")
    write_json(
        ATTEMPT_DIR / "request.json",
        {
            "contract": "SvgTopicStrokeGuideRequestV1",
            "topic": request.topic,
            "difficulty": request.difficulty,
            "data_class": "synthetic_topic_only_no_child_profile_or_photo",
            "video_requested": False,
        },
    )
    principal = VerifiedPrincipal(
        subject=f"rev87-26-spatial-grounding-{ATTEMPT_NAME}",
        issuer="rev87-26-local-test-harness",
        roles=frozenset({"parent"}),
    )
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).astimezone().isoformat()
    status_code = 200
    response_body: dict[str, Any]
    with (ATTEMPT_DIR / "modal_route_call.log").open("w", encoding="utf-8") as log_file:
        with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
            try:
                from unittest.mock import patch

                with patch.object(parent_ai, "_require_parent", return_value=None):
                    result = parent_ai.generate_sketch_guide(
                        request,
                        principal=principal,
                        db=None,
                    )
                response_body = result.model_dump(mode="json")
            except HTTPException as exc:
                status_code = exc.status_code
                response_body = {"detail": exc.detail}
            except Exception as exc:  # safe type only; do not write model text to logs
                status_code = 500
                response_body = {
                    "detail": {
                        "code": "LOCAL_ROUTE_HARNESS_ERROR",
                        "exception_type": type(exc).__name__,
                    }
                }

    elapsed = round(time.perf_counter() - started, 3)
    write_json(ATTEMPT_DIR / "response.json", response_body)
    guide = response_body.get("guide")
    document = response_body.get("document")
    summary = {
        "status": "HANDLER_HTTP_200" if status_code == 200 else f"HANDLER_HTTP_{status_code}",
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "elapsed_seconds": elapsed,
        "http_status": status_code,
        "topic": request.topic,
        "data_class": "synthetic_topic_only_no_child_profile_or_photo",
        "response_contract": response_body.get("contract"),
        "generation_source": response_body.get("generation_source"),
        "request_id": response_body.get("request_id"),
        "modal_call_id": response_body.get("modal_call_id"),
        "path_count": len(document.get("paths", [])) if isinstance(document, dict) else None,
        "stage_count": len(guide.get("stages", [])) if isinstance(guide, dict) else None,
        "error_detail": response_body.get("detail"),
        "svg_returned": isinstance(document, dict),
        "retry_performed": False,
        "video_requested": False,
        "child_data_used": False,
    }
    write_json(ATTEMPT_DIR / "request_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
