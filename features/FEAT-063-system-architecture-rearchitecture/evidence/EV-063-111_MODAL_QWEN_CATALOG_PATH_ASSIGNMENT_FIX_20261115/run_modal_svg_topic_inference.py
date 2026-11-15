"""Run one synthetic, non-video SVG topic-guide inference against deployed Modal."""
from __future__ import annotations

import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent
ENVIRONMENT = "dev"
WORKLOAD = "svg.topic-stroke-guide.generate"
APP = "sketch2life-srs23-language-audio-dev"
FUNCTION = "generate-topic-svg-stroke-guide-draft"
SCRATCH_VOLUME = "sketch2life-dev-job-scratch-v2"
TOPIC_REQUEST = {
    "schema_version": "sketch2life.svg-topic-stroke-guide-input.v1",
    "topic": "con mèo",
    "difficulty": "beginner",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
    attempt_prefix = f"sketch2life/{ENVIRONMENT}/{job_id}/{generation_id}/{attempt_id}/"
    request_bytes = canonical_bytes(TOPIC_REQUEST)
    manifest_bytes = canonical_bytes(
        {
            "schema_version": "sketch2life.modal.ai-request.v1",
            "asset": {
                "path": "input/request.json",
                "content_type": "application/json",
                "size_bytes": len(request_bytes),
                "sha256": hashlib.sha256(request_bytes).hexdigest(),
            },
        }
    )
    payload = {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": ENVIRONMENT,
        "workload": WORKLOAD,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "input_bytes": len(request_bytes) + len(manifest_bytes),
    }
    call = None
    output_returned = False
    started = datetime.now(timezone.utc)
    try:
        volume = modal.Volume.from_name(
            SCRATCH_VOLUME, environment_name=ENVIRONMENT, version=2
        )
        function = modal.Function.from_name(
            APP, FUNCTION, environment_name=ENVIRONMENT
        )
        with volume.batch_upload() as batch:
            batch.put_file(
                io.BytesIO(request_bytes),
                f"/{attempt_prefix}input/request.json",
            )
            batch.put_file(
                io.BytesIO(manifest_bytes),
                f"/{attempt_prefix}input/manifest.json",
            )
        call = function.spawn(payload)
        output = call.get(timeout=1800)
        output_returned = True
        if (
            not isinstance(output, dict)
            or output.get("schema_version") != "sketch2life.modal.worker-output.v1"
            or output.get("workload") != WORKLOAD
            or output.get("job_id") != job_id
            or output.get("generation_id") != generation_id
            or output.get("attempt_id") != attempt_id
        ):
            raise ValueError("MODAL_OUTPUT_CONTRACT_INVALID")

        result = output.get("result")
        source = output.get("reference_source")
        paths = result.get("document", {}).get("paths", []) if isinstance(result, dict) else []
        stages = result.get("stages", []) if isinstance(result, dict) else []
        source_path_ids = output.get("source_path_ids", [])
        flattened_stage_paths = [
            path_id
            for stage in stages
            if isinstance(stage, dict)
            for path_id in stage.get("new_path_ids", [])
        ]
        guide_path_ids = [path.get("path_id") for path in paths if isinstance(path, dict)]
        reference_paths = output.get("reference_illustration", {}).get("paths", [])
        reference_path_ids = [
            path.get("path_id") for path in reference_paths if isinstance(path, dict)
        ]
        quality_checks = {
            "output_under_backend_limit": len(canonical_bytes(output)) <= 256 * 1024,
            "stage_count_4_to_8": 4 <= len(stages) <= 8,
            "source_paths_unique": isinstance(source_path_ids, list)
            and len(source_path_ids) > 0
            and len(source_path_ids) == len(set(source_path_ids)),
            "guide_geometry_matches_source": set(guide_path_ids) == set(source_path_ids)
            and len(guide_path_ids) == len(source_path_ids),
            "color_reference_matches_source": set(reference_path_ids) == set(source_path_ids)
            and len(reference_path_ids) == len(source_path_ids),
            "stages_cover_each_source_path_once": sorted(flattened_stage_paths)
            == sorted(source_path_ids)
            and len(flattened_stage_paths) == len(source_path_ids),
            "cc0_source_provenance": isinstance(source, dict)
            and source.get("license_id") == "CC0-1.0"
            and source.get("dataset_name") == "Openclipart",
            "model_revision_pinned": output.get("model", {}).get("revision")
            == "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        }
        summary = {
            "evidence_id": "EV-063-111",
            "status": "PASS",
            "started_at_utc": started.isoformat(),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
            "environment": ENVIRONMENT,
            "topic": TOPIC_REQUEST["topic"],
            "workload": WORKLOAD,
            "modal_call_id": getattr(call, "object_id", None),
            "model": output.get("model"),
            "source": source,
            "path_count": len(paths),
            "stage_count": len(stages),
            "quality_checks": quality_checks,
            "quality_passed": all(quality_checks.values()),
            "stages": [
                {
                    "step_index": stage.get("step_index"),
                    "instruction_vi": stage.get("instruction_vi"),
                    "new_path_ids": stage.get("new_path_ids"),
                }
                for stage in stages
                if isinstance(stage, dict)
            ],
            "output_sha256": hashlib.sha256(canonical_bytes(output)).hexdigest(),
            "output_contract_valid": True,
            "no_video_requested": True,
            "no_child_data_used": True,
        }
        write_json(ROOT / "modal-worker-output.json", output)
        if not all(quality_checks.values()):
            summary["status"] = "OUTPUT_REJECTED"
            summary["failed_quality_checks"] = [
                key for key, passed in quality_checks.items() if not passed
            ]
            write_json(ROOT / "modal-worker-summary.json", summary)
            try:
                volume.remove_file(f"{attempt_prefix}input", recursive=True)
                summary["scratch_cleanup"] = "completed"
            except Exception as cleanup_error:
                summary["scratch_cleanup"] = f"failed:{type(cleanup_error).__name__}"
            write_json(ROOT / "modal-worker-summary.json", summary)
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
            return 3
        write_json(ROOT / "modal-worker-summary.json", summary)
        try:
            volume.remove_file(f"{attempt_prefix}input", recursive=True)
            summary["scratch_cleanup"] = "completed"
        except Exception as cleanup_error:  # preserve successful inference evidence
            summary["scratch_cleanup"] = f"failed:{type(cleanup_error).__name__}"
        write_json(ROOT / "modal-worker-summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    except BaseException as error:
        failure = {
            "evidence_id": "EV-063-111",
            "status": "OUTPUT_REJECTED" if output_returned else "FAILED_OR_UNKNOWN",
            "started_at_utc": started.isoformat(),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "environment": ENVIRONMENT,
            "topic": TOPIC_REQUEST["topic"],
            "workload": WORKLOAD,
            "modal_call_id": getattr(call, "object_id", None),
            "exception_type": type(error).__name__,
            "safe_error_code": str(error) if str(error).isupper() and len(str(error)) < 100 else None,
            "dispatched": call is not None,
            "retry_performed": False,
            "scratch_cleanup": "not_attempted_to_preserve_failure_evidence",
            "no_video_requested": True,
            "no_child_data_used": True,
        }
        write_json(ROOT / "modal-worker-summary.json", failure)
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
