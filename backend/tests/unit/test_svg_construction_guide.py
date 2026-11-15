from __future__ import annotations

import pytest

from sketch2life.contracts.schemas.svg_engine import (
    SvgTopicStrokeGuideConstructionModelResultV1,
)
from sketch2life.domain.svg_engine import (
    SvgRuleError,
    validate_construction_topic_stroke_guide_v1,
)


def _construction_result() -> dict[str, object]:
    source_path_ids = [f"oc_path_{index:03d}" for index in range(1, 9)]
    return {
        "schema_version": "SvgTopicStrokeGuideConstructionContentV1",
        "title_vi": "Con mèo",
        "strokes": [
            {
                "path_id": f"guide_stroke_{index:02d}",
                "d": f"M {40 + index * 5} 80 L {60 + index * 5} 100",
                "role": "construction" if index <= 2 else "outline" if index <= 6 else "feature",
                "feature_vi": f"nét số {index}",
                "source_path_ids": [source_path_ids[index - 1]],
            }
            for index in range(1, 9)
        ],
        "stages": [
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
        ],
    }


def test_construction_guide_contract_builds_its_own_progressive_svg() -> None:
    raw = _construction_result()
    source_ids = [f"oc_path_{index:03d}" for index in range(1, 12)]

    model_result = SvgTopicStrokeGuideConstructionModelResultV1.model_validate(raw)
    validated = validate_construction_topic_stroke_guide_v1(
        model_result.model_dump(mode="json"),
        topic="con mèo",
        source_path_ids=source_ids,
        source_path_geometries={
            source_id: f"M {index} 10 L {index + 2} 12"
            for index, source_id in enumerate(source_ids, start=1)
        },
    )

    assert validated["document"]["schema_version"] == "SvgDocumentV1"
    assert len(validated["document"]["paths"]) == 8
    assert len(validated["stages"]) == 4
    assert validated["stages"][0]["new_path_ids"] == [
        "guide_stroke_01",
        "guide_stroke_02",
    ]
    assert validated["path_lineage"][0]["source_path_ids"] == ["oc_path_001"]
    assert "oc_path_011" not in {
        source_id
        for item in validated["path_lineage"]
        for source_id in item["source_path_ids"]
    }


def test_construction_guide_domain_accepts_full_contract_geometry_budget() -> None:
    source_path_ids = [f"oc_path_{index:03d}" for index in range(1, 12)]
    strokes = []
    for index in range(1, 21):
        path_data = (
            f"M {40 + index} 80 L {60 + index} 100"
            if index <= 3
            else (
                f"M {30 + index}.1234567890 {40 + index}.1234567890 "
                + " ".join(
                    f"L {31 + index}.{point:011d} {41 + index}.{point + 1:011d}"
                    for point in range(23)
                )
            )
        )
        strokes.append(
            {
                "path_id": f"guide_stroke_{index:02d}",
                "d": path_data,
                "role": (
                    "construction"
                    if index <= 3
                    else "feature"
                    if index == 20
                    else "outline"
                ),
                "feature_vi": f"nét số {index}",
                "source_path_ids": [source_path_ids[(index - 1) % len(source_path_ids)]],
            }
        )
    raw = {
        "schema_version": "SvgTopicStrokeGuideConstructionContentV1",
        "title_vi": "Con mèo",
        "strokes": strokes,
        "stages": [
            {
                "step_index": 1,
                "label_vi": "Khung lớn",
                "instruction_vi": "Vẽ hình lớn cho đầu và thân.",
                "stroke_ids": ["guide_stroke_01", "guide_stroke_02", "guide_stroke_03"],
            },
            {
                "step_index": 2,
                "label_vi": "Nối hình",
                "instruction_vi": "Nối các hình lớn lại với nhau.",
                "stroke_ids": [f"guide_stroke_{index:02d}" for index in range(4, 9)],
            },
            {
                "step_index": 3,
                "label_vi": "Thêm bộ phận",
                "instruction_vi": "Vẽ thêm chân và đuôi.",
                "stroke_ids": [f"guide_stroke_{index:02d}" for index in range(9, 15)],
            },
            {
                "step_index": 4,
                "label_vi": "Nhận ra con mèo",
                "instruction_vi": "Thêm tai và mắt cho mèo.",
                "stroke_ids": [f"guide_stroke_{index:02d}" for index in range(15, 21)],
            },
        ],
    }
    assert sum(len(stroke["d"]) for stroke in strokes) > 12_288
    assert max(len(stroke["d"]) for stroke in strokes) <= 768

    validated = validate_construction_topic_stroke_guide_v1(
        raw,
        topic="con mèo",
        source_path_ids=source_path_ids,
        source_path_geometries={
            source_id: f"M {index} 10 L {index + 2} 12"
            for index, source_id in enumerate(source_path_ids, start=1)
        },
    )

    assert len(validated["document"]["paths"]) == 20
    assert len(validated["stages"]) == 4


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda value: value["strokes"][0].update(role="outline"),
            "SVG_CONSTRUCTION_GUIDE_FIRST_STEP_NOT_CONSTRUCTION",
        ),
        (
            lambda value: value["strokes"][0].update(source_path_ids=["unknown_source"]),
            "SVG_CONSTRUCTION_GUIDE_STROKE_INVALID",
        ),
        (
            lambda value: value["stages"][0].update(stroke_ids=["guide_stroke_01"]),
            "SVG_CONSTRUCTION_GUIDE_PATH_COVERAGE_INVALID",
        ),
    ],
)
def test_construction_guide_rejects_invalid_anchors_or_step_order(mutate, expected_code) -> None:
    raw = _construction_result()
    mutate(raw)

    with pytest.raises(SvgRuleError) as raised:
        validate_construction_topic_stroke_guide_v1(
            raw,
            topic="con mèo",
            source_path_ids=[f"oc_path_{index:03d}" for index in range(1, 12)],
            source_path_geometries={},
        )

    assert raised.value.code == expected_code
