from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.interfaces.http.routers import parent_ai


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
OUTPUT_DIR = Path(__file__).resolve().parent


def _svg_document(view_box: str, label: str, paths: list[dict]) -> str:
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "viewBox": view_box,
            "width": "1024",
            "height": "1024",
            "role": "img",
            "aria-label": label,
        },
    )
    _, _, width, height = (float(value) for value in view_box.split())
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {"width": str(width), "height": str(height), "fill": "#FFFFFF"},
    )
    for path in paths:
        ET.SubElement(root, f"{{{SVG_NS}}}path", path)
    return ET.tostring(root, encoding="unicode")


def _render_stage(payload: dict, stage_index: int) -> str:
    guide = payload["guide"]
    visible_ids = {
        path_id
        for stage in guide["stages"][: stage_index + 1]
        for path_id in stage["animation_order"]
    }
    current_ids = set(guide["stages"][stage_index]["new_path_ids"])
    source_by_id = {
        path["path_id"]: path
        for path in payload["reference_illustration"]["paths"]
    }
    rendered = []
    for path in payload["document"]["paths"]:
        if path["path_id"] not in visible_ids:
            continue
        source = source_by_id[path["path_id"]]
        current = path["path_id"] in current_ids
        rendered.append(
            {
                "d": path["d"],
                "fill": "none",
                "stroke": "#3867F6" if current else "#221f1f",
                "stroke-width": str(path["stroke_width"] + (0.25 if current else 0)),
                "stroke-linecap": source["stroke_linecap"],
                "stroke-linejoin": source["stroke_linejoin"],
                "stroke-miterlimit": str(source["stroke_miterlimit"]),
            }
        )
    return _svg_document(
        payload["document"]["view_box"],
        f"Gợi ý nét vẽ con gà, bước {stage_index + 1}",
        rendered,
    )


def _render_final_guide(payload: dict) -> str:
    source_by_id = {
        path["path_id"]: path
        for path in payload["reference_illustration"]["paths"]
    }
    rendered = [
        {
            "d": path["d"],
            "fill": "none",
            "stroke": "#221f1f",
            "stroke-width": str(path["stroke_width"]),
            "stroke-linecap": source_by_id[path["path_id"]]["stroke_linecap"],
            "stroke-linejoin": source_by_id[path["path_id"]]["stroke_linejoin"],
            "stroke-miterlimit": str(source_by_id[path["path_id"]]["stroke_miterlimit"]),
        }
        for path in payload["document"]["paths"]
    ]
    return _svg_document(
        payload["document"]["view_box"], "Con gà hoàn chỉnh được tạo từ các nét SVG nguồn", rendered
    )


def _render_reference(payload: dict) -> str:
    reference = payload["reference_illustration"]
    rendered = [
        {
            "d": path["d"],
            "fill": path["fill"],
            "stroke": path["stroke"],
            "stroke-width": str(path["stroke_width"]),
            "stroke-linecap": path["stroke_linecap"],
            "stroke-linejoin": path["stroke_linejoin"],
            "stroke-miterlimit": str(path["stroke_miterlimit"]),
        }
        for path in reference["paths"]
    ]
    return _svg_document(reference["view_box"], "Hình gà màu nguồn, xem riêng", rendered)


def main() -> None:
    parent_ai._require_parent = lambda *_args: None
    parent_ai.get_settings = lambda: SimpleNamespace(
        svg_topic_stroke_guide_generation_enabled=True
    )

    def reject_modal_call():
        raise AssertionError("Pinned Arcadia chicken request unexpectedly dispatched to Modal")

    parent_ai.ModalJsonFunctionClient = reject_modal_call
    app = FastAPI()
    app.include_router(parent_ai.router)
    app.dependency_overrides[parent_ai.get_verified_adult] = lambda: object()
    app.dependency_overrides[parent_ai.get_db] = lambda: None

    started = perf_counter()
    with TestClient(app) as client:
        response = client.post(
            "/api/parent/v1/ai/sketch-guides",
            json={
                "contract": "SvgTopicStrokeGuideRequestV1",
                "topic": "gà mái",
                "difficulty": "beginner",
            },
        )
    elapsed = round(perf_counter() - started, 3)
    if response.status_code != 200:
        raise SystemExit(f"Parent route returned HTTP {response.status_code}: {response.text}")

    payload = response.json()
    if (
        payload.get("contract") != "SvgTopicStrokeGuideSourceDraftV1"
        or payload.get("generation_source") != "CURATED_SOURCE_DERIVATION"
        or payload.get("derivation", {}).get("method") != "EXACT_SOURCE_PATH_SEQUENCE_V7"
        or payload.get("path_count") != 77
        or payload.get("stage_count") != 8
        or payload.get("modal_call_id") is not None
        or payload.get("model") is not None
    ):
        raise SystemExit("Parent route did not return the expected exact-source V7 guide")

    reference_by_id = {
        path["path_id"]: path for path in payload["reference_illustration"]["paths"]
    }
    guide_by_id = {path["path_id"]: path for path in payload["document"]["paths"]}
    if len(guide_by_id) != 77 or set(guide_by_id) != set(reference_by_id):
        raise SystemExit("Guide path inventory differs from the pinned source")
    if any(
        guide_by_id[path_id]["d"] != reference_by_id[path_id]["d"]
        for path_id in reference_by_id
    ):
        raise SystemExit("Guide changed source path geometry")
    stage_ids = [
        path_id
        for stage in payload["guide"]["stages"]
        for path_id in stage["new_path_ids"]
    ]
    if len(stage_ids) != 77 or len(set(stage_ids)) != 77 or set(stage_ids) != set(guide_by_id):
        raise SystemExit("Stages do not cover each source path exactly once")

    for index in range(payload["stage_count"]):
        (OUTPUT_DIR / f"parent-chicken-v7-step-{index + 1}.svg").write_text(
            _render_stage(payload, index), encoding="utf-8"
        )
    (OUTPUT_DIR / "parent-chicken-v7-final-line-guide.svg").write_text(
        _render_final_guide(payload), encoding="utf-8"
    )
    (OUTPUT_DIR / "parent-chicken-v7-reference.svg").write_text(
        _render_reference(payload), encoding="utf-8"
    )
    (OUTPUT_DIR / "parent-svg-guide-response.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    reference_digest = hashlib.sha256(
        json.dumps(
            payload["reference_illustration"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    attempt = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "request": {"topic": "gà mái", "difficulty": "beginner"},
        "http_status": response.status_code,
        "elapsed_seconds": elapsed,
        "contract": payload["contract"],
        "generation_source": payload["generation_source"],
        "engine_revision": payload["derivation"]["engine_revision"],
        "derivation_method": payload["derivation"]["method"],
        "source_sha256": payload["reference_source"]["source_sha256"],
        "source_path_count": payload["derivation"]["source_path_count"],
        "guide_path_count": payload["path_count"],
        "stage_count": payload["stage_count"],
        "reference_path_count": len(payload["reference_illustration"]["paths"]),
        "reference_document_sha256": reference_digest,
        "document_sha256": payload["document_sha256"],
        "exact_path_data_match": True,
        "all_paths_staged_once": True,
        "reference_rendered_under_strokes": False,
        "modal_dispatched": False,
        "auth_scope": "focused local TestClient; identity and database dependencies overridden only",
    }
    (OUTPUT_DIR / "runtime-attempt.json").write_text(
        json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(attempt, ensure_ascii=False))


if __name__ == "__main__":
    main()
