from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RESPONSE = (
    ROOT
    / "features/FEAT-063-system-architecture-rearchitecture/evidence/"
    / "EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/attempt_001/response.json"
)
OUT = Path(__file__).resolve().parent / "curated_source_build_check.json"
sys.path.insert(0, str(ROOT / "deployment/modal/srs_v23"))

import language_audio_app as worker  # noqa: E402


def main() -> None:
    response = json.loads(RESPONSE.read_text(encoding="utf-8"))
    doc_paths = {path["path_id"]: path for path in response["document"]["paths"]}
    source_path_by_id = {
        item["derived_path_id"]: item["source_path_ids"][0]
        for item in response["derivation"]["path_lineage"]
    }
    segments = [
        {
            "path_id": f"source_segment_{index:03d}",
            "source_path_id": source_path_by_id[f"guide_stroke_{index:02d}"],
            "d": doc_paths[f"guide_stroke_{index:02d}"]["d"],
        }
        for index in range(1, 21)
    ]
    source = response["reference_illustration"]
    candidate = {
        "asset_id": response["reference_source"]["asset_id"],
        "source_sha256": response["reference_source"]["source_sha256"],
        "parsed_svg": {"view_box": source["view_box"], "paths": source["paths"]},
    }
    pinned = ["source_segment_005", "source_segment_006"]
    plan = worker._curated_openclipart_source_plan(
        candidate, segments, first_step_segment_ids=pinned
    )
    if plan is None:
        raise RuntimeError("CURATED_PLAN_NOT_SELECTED_FOR_PINNED_SOURCE")
    guide, _ = worker._build_openclipart_segment_guide(candidate, segments, plan)
    if [stroke["d"] for stroke in guide["strokes"]] != [segment["d"] for segment in segments]:
        raise RuntimeError("CURATED_BUILD_CHANGED_SOURCE_GEOMETRY")
    result = {
        "status": "PASS",
        "request_id": response["request_id"],
        "asset_id": candidate["asset_id"],
        "source_sha256": candidate["source_sha256"],
        "source_segment_count": len(segments),
        "output_stroke_count": len(guide["strokes"]),
        "stage_count": len(guide["stages"]),
        "all_segment_ids_used_once": sum(
            len(stage["stroke_ids"]) for stage in guide["stages"]
        ) == len(segments),
        "geometry_identical_in_source_order": True,
        "stages": [
            {
                "step_index": stage["step_index"],
                "instruction_vi": stage["instruction_vi"],
                "stroke_ids": stage["stroke_ids"],
            }
            for stage in guide["stages"]
        ],
        "data_note": "Uses only the prior synthetic catalog response; no child data or model call.",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
