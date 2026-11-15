from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
SOURCE_ATTEMPT = (
    ROOT
    / "features/FEAT-063-system-architecture-rearchitecture/evidence/"
    / "EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/attempt_003"
)
SOURCE_RESPONSE = SOURCE_ATTEMPT / "response.json"
PREVIEW_RESPONSE = EVIDENCE / "response_resequenced_offline.json"
RENDERED_DIR = EVIDENCE / "rendered_symmetric_eye_stage"
RENDERER_SCRIPT = SOURCE_ATTEMPT / "render_parent_result.py"

sys.path.insert(0, str(ROOT / "deployment/modal/srs_v23"))
import language_audio_app as worker  # noqa: E402


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = json.loads(SOURCE_RESPONSE.read_text(encoding="utf-8"))
    reference = payload["reference_illustration"]
    source_path_by_derived_id = {
        item["derived_path_id"]: item["source_path_ids"][0]
        for item in payload["derivation"]["path_lineage"]
    }
    segments = [
        {
            "path_id": (
                "source_segment_"
                f"{int(path['path_id'].rsplit('_', 1)[1]):03d}"
            ),
            "source_path_id": source_path_by_derived_id[path["path_id"]],
            "d": path["d"],
        }
        for path in sorted(
            payload["document"]["paths"],
            key=lambda item: int(item["path_id"].rsplit("_", 1)[1]),
        )
    ]
    candidate = {
        "asset_id": payload["reference_source"]["asset_id"],
        "source_sha256": payload["reference_source"]["source_sha256"],
        "parsed_svg": {
            "view_box": reference["view_box"],
            "paths": [
                {
                    "path_id": path["path_id"],
                    "d": path["d"],
                    "fill": path["fill"],
                    "stroke": path["stroke"],
                    "stroke_width": path["stroke_width"],
                    "stroke_linecap": path.get("stroke_linecap", "round"),
                    "stroke_linejoin": path.get("stroke_linejoin", "round"),
                }
                for path in reference["paths"]
            ],
        },
    }
    plan = worker._curated_openclipart_source_plan(
        candidate,
        segments,
        first_step_segment_ids=["source_segment_005", "source_segment_006"],
    )
    if plan is None:
        raise RuntimeError("PINNED_SOURCE_PLAN_NOT_APPLIED")

    guide, _ = worker._build_openclipart_segment_guide(candidate, segments, plan)
    render_guide = copy.deepcopy(guide)
    for stage in render_guide["stages"]:
        stage["new_path_ids"] = list(stage["stroke_ids"])
    preview_payload = copy.deepcopy(payload)
    preview_payload["guide"] = render_guide
    preview_payload["offline_preview_metadata"] = {
        "source_response": str(SOURCE_RESPONSE.relative_to(ROOT)),
        "source_response_is_unchanged": True,
        "live_api_response": False,
        "modal_request_sent": False,
        "sequence_version": "openclipart-friendly-kitten-icon-v3",
        "eye_detail_segment_ids_in_one_step": [
            f"source_segment_{index:03d}" for index in range(10, 16)
        ],
    }
    PREVIEW_RESPONSE.write_text(
        json.dumps(preview_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    spec = importlib.util.spec_from_file_location("saved_parent_result_renderer", RENDERER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("SAVED_RESPONSE_RENDERER_UNAVAILABLE")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.RESPONSE_PATH = PREVIEW_RESPONSE
    renderer.OUT = RENDERED_DIR
    renderer.main()

    print(
        json.dumps(
            {
                "preview_only": True,
                "modal_call_made": False,
                "stage_count": len(guide["stages"]),
                "stage_path_groups": [
                    stage["stroke_ids"] for stage in guide["stages"]
                ],
                "eye_detail_step": guide["stages"][3]["instruction_vi"],
                "preview_response": str(PREVIEW_RESPONSE),
                "rendered_dir": str(RENDERED_DIR),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
