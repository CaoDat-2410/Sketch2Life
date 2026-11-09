from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve()
FEATURE = SCRIPT.parents[2]
REPO = FEATURE.parents[1]
BACKEND_SRC = REPO / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import modal  # noqa: E402

OUTPUT = (
    FEATURE
    / "evidence"
    / "nonvideo_modal_ai_reliability_20261106"
    / "runtime"
    / "qwen35_decoder_preflight_after_deploy.json"
)


def main() -> int:
    if OUTPUT.exists():
        raise SystemExit("Readiness evidence exists; refusing duplicate call")
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    started = time.perf_counter()
    call = None
    try:
        function = modal.Function.from_name(
            "sketch2life-srs23-language-audio-dev",
            "check-qwen35-decoder-readiness",
            environment_name="dev",
        )
        call = function.spawn()
        result = call.get(timeout=120)
        safe_result = {
            key: value
            for key, value in result.items()
            if key
            in {
                "status",
                "transformers_version",
                "lm_format_enforcer_version",
                "model_loader",
                "processor_loader",
                "schema_parser",
                "token_enforcer",
                "tokenizer_data",
            }
            and isinstance(value, str)
        }
        outcome = "SUCCEEDED" if safe_result.get("status") == "ready" else "INVALID_RESULT"
        error_type = None
    except Exception as exc:  # noqa: BLE001 - store only safe exception class.
        outcome = "FAILED_TERMINAL" if call is not None else "DISPATCH_FAILED_NO_CALL"
        safe_result = None
        error_type = type(exc).__name__
    record = {
        "started_at": started_at,
        "ended_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "call_id": getattr(call, "object_id", None),
        "outcome": outcome,
        "error_type": error_type,
        "result": safe_result,
        "gpu_inference_called": False,
        "video_called": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: record[key] for key in ("call_id", "outcome", "elapsed_seconds", "error_type")}))
    return 0 if outcome == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
