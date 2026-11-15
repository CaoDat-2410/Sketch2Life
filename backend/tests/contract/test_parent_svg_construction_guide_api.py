from __future__ import annotations

from types import SimpleNamespace

from sketch2life.contracts.schemas.svg_engine import SvgTopicStrokeGuideRequestV1
from sketch2life.infrastructure.ai.modal_function_client import MODEL_ID, MODEL_REVISION
from sketch2life.interfaces.http.routers import parent_ai


def _modal_output() -> dict[str, object]:
    source_ids = [f"oc_path_{index:03d}" for index in range(1, 9)]
    strokes = [
        {
            "path_id": f"guide_stroke_{index:02d}",
            "d": f"M {40 + index * 5} 80 L {60 + index * 5} 100",
            "role": "construction" if index <= 2 else "outline" if index <= 6 else "feature",
            "feature_vi": f"nét số {index}",
            "source_path_ids": [source_ids[index - 1]],
        }
        for index in range(1, 9)
    ]
    stages = [
        {
            "step_index": 1,
            "label_vi": "Khối đầu và thân",
            "instruction_vi": "Vẽ hai hình bầu dục lớn.",
            "stroke_ids": ["guide_stroke_01", "guide_stroke_02"],
        },
        {
            "step_index": 2,
            "label_vi": "Nối các phần",
            "instruction_vi": "Nối đầu với thân bằng nét cong.",
            "stroke_ids": ["guide_stroke_03", "guide_stroke_04"],
        },
        {
            "step_index": 3,
            "label_vi": "Thêm chân và đuôi",
            "instruction_vi": "Thêm chân ở dưới và đuôi phía sau.",
            "stroke_ids": ["guide_stroke_05", "guide_stroke_06"],
        },
        {
            "step_index": 4,
            "label_vi": "Thêm nét nhận dạng",
            "instruction_vi": "Vẽ mắt và vài nét ria mép.",
            "stroke_ids": ["guide_stroke_07", "guide_stroke_08"],
        },
    ]
    source_paths = [
        {
            "path_id": source_id,
            "d": f"M {80 + index * 2} 120 L {120 + index * 2} 120 L {120 + index * 2} 150 Z",
            "fill": "#d8aa64",
            "stroke": "#202938",
            "stroke_width": 2,
            "stroke_linecap": "round",
            "stroke_linejoin": "round",
            "stroke_miterlimit": 4,
        }
        for index, source_id in enumerate(source_ids)
    ]
    return {
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "reference_source": {
            "asset_id": "openclipart-cat-synthetic-test",
            "dataset_name": "Openclipart",
            "dataset_revision": "a" * 40,
            "dataset_doi": None,
            "dataset_uri": "https://openclipart.org/detail/12345/cat",
            "source_sha256": "b" * 64,
            "license_id": "CC0-1.0",
            "license_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        },
        "reference_illustration": {
            "schema_version": "SvgReferenceIllustrationV1",
            "view_box": "0 0 512 512",
            "paths": source_paths,
        },
        "source_path_ids": source_ids,
        "result": {
            "schema_version": "SvgTopicStrokeGuideConstructionContentV1",
            "title_vi": "Cùng vẽ con mèo",
            "strokes": strokes,
            "stages": stages,
        },
    }


def test_parent_sketch_guide_returns_construction_contract_and_separate_reference(
    monkeypatch,
) -> None:
    monkeypatch.setattr(parent_ai, "_require_parent", lambda *_args: None)
    monkeypatch.setattr(parent_ai, "_require_modal_dev", lambda: None)
    monkeypatch.setattr(
        parent_ai,
        "get_settings",
        lambda: SimpleNamespace(svg_topic_stroke_guide_generation_enabled=True),
    )
    monkeypatch.setattr(parent_ai, "build_openclipart_guide", lambda _topic: None)
    monkeypatch.setattr(parent_ai, "build_openmoji_guide", lambda _topic: None)
    monkeypatch.setattr(parent_ai, "arcadia_source_pack_installed", lambda: False)

    class FakeModalJsonFunctionClient:
        def invoke(self, _workload, _payload):
            return SimpleNamespace(
                output=_modal_output(),
                call_id="fc-construction-contract-test",
                elapsed_seconds=3.25,
            )

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", FakeModalJsonFunctionClient)

    response = parent_ai.generate_sketch_guide(
        SvgTopicStrokeGuideRequestV1(topic="con cá heo"),
        principal=object(),
        db=None,
    )
    payload = response.model_dump(mode="json")

    assert payload["contract"] == "SvgTopicStrokeGuideConstructionDraftV1"
    assert payload["generation_source"] == "QWEN_REFERENCE_CONDITIONED_CONSTRUCTION"
    assert payload["derivation"]["method"] == "QWEN_REFERENCE_CONDITIONED_CONSTRUCTION_V1"
    assert payload["path_count"] == 8
    assert payload["stage_count"] == 4
    assert payload["guide"]["stages"][0]["new_path_ids"] == [
        "guide_stroke_01",
        "guide_stroke_02",
    ]
    assert payload["document"]["paths"][0]["d"] != payload[
        "reference_illustration"
    ]["paths"][0]["d"]
    assert payload["review_required"] is True
    assert payload["persisted"] is False
