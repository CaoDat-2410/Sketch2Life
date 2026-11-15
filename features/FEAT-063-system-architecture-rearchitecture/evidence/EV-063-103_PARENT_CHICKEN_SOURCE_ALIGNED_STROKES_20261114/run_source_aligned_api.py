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


def _append_reference(parent: ET.Element, illustration: dict, *, opacity: float) -> None:
    layer = ET.SubElement(
        parent,
        f"{{{SVG_NS}}}svg",
        {
            "x": "0",
            "y": "0",
            "width": "512",
            "height": "512",
            "viewBox": illustration["view_box"],
            "preserveAspectRatio": "xMidYMid meet",
            "opacity": str(opacity),
        },
    )
    for path in illustration["paths"]:
        ET.SubElement(
            layer,
            f"{{{SVG_NS}}}path",
            {
                "d": path["d"],
                "fill": path["fill"],
                "stroke": path["stroke"],
                "stroke-width": str(path["stroke_width"]),
                "stroke-linecap": path["stroke_linecap"],
                "stroke-linejoin": path["stroke_linejoin"],
                "stroke-miterlimit": str(path["stroke_miterlimit"]),
            },
        )


def _render_stage(payload: dict, stage_index: int) -> str:
    guide_document = payload["document"]
    guide = payload["guide"]
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "viewBox": "0 0 512 512",
            "width": "1024",
            "height": "1024",
            "role": "img",
            "aria-label": f"Gà mái, bước {stage_index + 1}",
        },
    )
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {"width": "512", "height": "512", "fill": "#FFFFFF"},
    )
    _append_reference(root, payload["reference_illustration"], opacity=0.18)
    stage_layer = ET.SubElement(
        root,
        f"{{{SVG_NS}}}svg",
        {
            "x": "0",
            "y": "0",
            "width": "512",
            "height": "512",
            "viewBox": guide_document["view_box"],
            "preserveAspectRatio": "xMidYMid meet",
        },
    )
    visible = {
        path_id
        for stage in guide["stages"][: stage_index + 1]
        for path_id in stage["animation_order"]
    }
    current = set(guide["stages"][stage_index]["new_path_ids"])
    for path in guide_document["paths"]:
        if path["path_id"] not in visible:
            continue
        ET.SubElement(
            stage_layer,
            f"{{{SVG_NS}}}path",
            {
                "d": path["d"],
                "fill": "none",
                "stroke": "#3867F6" if path["path_id"] in current else "#17243E",
                "stroke-width": str(path["stroke_width"] + (0.5 if path["path_id"] in current else 0)),
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        )
    return ET.tostring(root, encoding="unicode")


def _render_final_overlay(payload: dict) -> str:
    guide_document = payload["document"]
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "viewBox": "0 0 512 512",
            "width": "1024",
            "height": "1024",
            "role": "img",
            "aria-label": "Gà mái hoàn chỉnh với nét guide phủ đúng hình mẫu",
        },
    )
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {"width": "512", "height": "512", "fill": "#FFFFFF"},
    )
    _append_reference(root, payload["reference_illustration"], opacity=0.18)
    for path in guide_document["paths"]:
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}path",
            {
                "d": path["d"],
                "fill": "none",
                "stroke": "#17243E",
                "stroke-width": str(path["stroke_width"]),
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        )
    return ET.tostring(root, encoding="unicode")


def _render_reference(payload: dict) -> str:
    reference = payload["reference_illustration"]
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "viewBox": reference["view_box"],
            "width": "1024",
            "height": "1024",
            "role": "img",
            "aria-label": "Gà mái minh họa màu nguồn",
        },
    )
    ET.SubElement(
        root,
        f"{{{SVG_NS}}}rect",
        {"width": "252", "height": "252", "fill": "#FFFFFF"},
    )
    for path in reference["paths"]:
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}path",
            {
                "d": path["d"],
                "fill": path["fill"],
                "stroke": path["stroke"],
                "stroke-width": str(path["stroke_width"]),
                "stroke-linecap": path["stroke_linecap"],
                "stroke-linejoin": path["stroke_linejoin"],
                "stroke-miterlimit": str(path["stroke_miterlimit"]),
            },
        )
    return ET.tostring(root, encoding="unicode")


def main() -> None:
    parent_ai._require_parent = lambda *_args: None
    parent_ai.get_settings = lambda: SimpleNamespace(
        svg_topic_stroke_guide_generation_enabled=True
    )

    def reject_modal_call():
        raise AssertionError("Pinned Arcadia hen request unexpectedly dispatched to Modal")

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
    if payload.get("contract") != "SvgTopicStrokeGuideSourceDraftV1":
        raise SystemExit("Parent route returned the wrong source contract")
    if payload.get("generation_source") != "CURATED_SOURCE_DERIVATION":
        raise SystemExit("Parent route did not identify the source-derived engine")
    if payload.get("modal_call_id") is not None or payload.get("model") is not None:
        raise SystemExit("Source-derived response contains false provider provenance")

    for index in range(payload["stage_count"]):
        (OUTPUT_DIR / f"parent-chicken-v3-step-{index + 1}.svg").write_text(
            _render_stage(payload, index), encoding="utf-8"
        )
    (OUTPUT_DIR / "parent-chicken-v3-final-overlay.svg").write_text(
        _render_final_overlay(payload), encoding="utf-8"
    )
    (OUTPUT_DIR / "parent-chicken-v3-reference.svg").write_text(
        _render_reference(payload),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "parent-svg-guide-response.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
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
        "derived_path_count": payload["path_count"],
        "stage_count": payload["stage_count"],
        "reference_path_count": len(payload["reference_illustration"]["paths"]),
        "reference_view_box": payload["reference_illustration"]["view_box"],
        "guide_view_box": payload["document"]["view_box"],
        "reference_underlay_opacity": 0.18,
        "reference_document_sha256": reference_digest,
        "document_sha256": payload["document_sha256"],
        "modal_dispatched": False,
        "auth_scope": "focused local TestClient; identity and database dependencies overridden only",
    }
    (OUTPUT_DIR / "runtime-attempt.json").write_text(
        json.dumps(attempt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(attempt, ensure_ascii=False))


if __name__ == "__main__":
    main()
