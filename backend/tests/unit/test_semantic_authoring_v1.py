import hashlib
import json

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from sketch2life.contracts.schemas.semantic_authoring_v1 import SemanticAuthoringPackV1
from sketch2life.infrastructure.media.semantic_authoring_v1 import compile_pack, route_authoring
from sketch2life.infrastructure.media.semantic_drawing_engine_v2 import SemanticProgress


@pytest.fixture
def pack(tmp_path):
    Image.new("RGBA", (16, 10), (190, 120, 60, 255)).save(tmp_path / "asset.png")
    Image.new("L", (16, 10), 255).save(tmp_path / "mask.png")

    def digest(name):
        return hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()

    data = {
        "object_id": "arbitrary-object",
        "asset_ref": "asset.png",
        "asset_sha256": digest("asset.png"),
        "source_image_sha256": "a" * 64,
        "provenance": "SOURCE_DRAWING",
        "authoring_method": "TEST_ONLY",
        "approval": "TECHNICAL_PROOF_ONLY",
        "target_seconds": 0.01,
        "regions": [
            {
                "region_id": "region",
                "semantic_label": "arbitrary",
                "mask_ref": "mask.png",
                "mask_sha256": digest("mask.png"),
                "provenance": "MANUAL_TEST",
            }
        ],
        "strokes": [
            {
                "path": {
                    "stroke_id": "outline",
                    "phase": "OUTLINE",
                    "points": [[0, 0], [15, 0]],
                    "brush_width": 1,
                    "color_rgb": [0, 0, 0],
                },
                "role": "PRIMARY_CONTOUR",
                "region_id": "region",
            },
            {
                "path": {
                    "stroke_id": "color",
                    "phase": "COLOR",
                    "points": [[0, 5], [15, 5]],
                    "brush_width": 12,
                    "color_rgb": [0, 0, 0],
                },
                "role": "COLOR_REGION",
                "region_id": "region",
            },
        ],
        "stroke_order": ["outline", "color"],
    }
    return tmp_path / "pack.json", data


def save_pack(pack):
    path, data = pack
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("provenance", ["SOURCE_DRAWING", "NEW_LOCAL_AUTHORED"])
def test_source_and_new_assets_share_contract_and_exact_final(pack, provenance):
    pack[1]["provenance"] = provenance
    asset, plan, stats = compile_pack(save_pack(pack))
    before = asset.source.tobytes()
    progress = SemanticProgress(asset, plan)
    _, _, masks = progress.at(plan["rows"][0]["pen_down_end"])
    assert not masks["color"].any()
    final, _, masks = progress.at(plan["seconds"])
    assert final.tobytes() == before == asset.source.tobytes()
    assert masks["color"].all()
    assert stats["timing"] == "TIMING_INFEASIBLE"
    assert [r["stroke_id"] for r in plan["rows"]] == ["outline", "color"]


@pytest.mark.parametrize("change", ["version", "order", "duplicate", "role", "optional"])
def test_contract_rejects_invalid_authoring(pack, change):
    data = pack[1]
    if change == "version":
        data["version"] = "99"
    elif change == "order":
        data["stroke_order"].reverse()
    elif change == "duplicate":
        data["strokes"][1]["path"]["stroke_id"] = "outline"
    elif change == "role":
        data["strokes"][0]["role"] = "COLOR_REGION"
    else:
        data["strokes"][0]["essential"] = False
    with pytest.raises(ValidationError):
        SemanticAuthoringPackV1.model_validate(data)


def test_hash_mismatch_fails(pack):
    pack[1]["asset_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SOURCE_ASSET_MISMATCH"):
        compile_pack(save_pack(pack))


def test_missing_coverage_exports_review_not_cleanup(pack):
    pack[1]["strokes"][1]["path"]["brush_width"] = 1
    review = pack[0].parent / "review"
    with pytest.raises(ValueError, match="NEEDS_AUTHORING_REVIEW"):
        compile_pack(save_pack(pack), review)
    assert (review / "missing-region-0.png").is_file()
    assert json.loads((review / "coverage-review.json").read_text())["region"] > 0


def test_color_dot_is_not_accepted_as_coverage(pack):
    pack[1]["strokes"][1]["path"]["points"] = [[5, 5], [5, 5]]
    with pytest.raises(ValueError, match="color dot cleanup"):
        compile_pack(save_pack(pack))


def test_wrong_mask_coordinates_require_review(pack):
    path, data = pack
    Image.new("L", (5, 5), 255).save(path.parent / "mask.png")
    data["regions"][0]["mask_sha256"] = hashlib.sha256(
        (path.parent / "mask.png").read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="mask coordinate mismatch"):
        compile_pack(save_pack(pack))


def test_explicit_minimum_only_lengthens_timing(pack):
    _, before, _ = compile_pack(save_pack(pack))
    pack[1]["strokes"][0]["minimum_down_seconds"] = 10
    _, after, _ = compile_pack(save_pack(pack))
    assert after["seconds"] > before["seconds"]
    assert after["rows"][0]["pen_down_seconds"] == 10


def test_pen_up_does_not_reveal_color(pack):
    asset, plan, _ = compile_pack(save_pack(pack))
    progress = SemanticProgress(asset, plan)
    row = plan["rows"][1]
    _, trace, masks = progress.at((row["pen_up_start"] + row["pen_down_start"]) / 2)
    assert trace["state"] == "UP"
    assert not np.any(masks["color"])


@pytest.mark.parametrize(
    "trusted,candidate,approved,route",
    [
        (True, False, False, "AUTO"),
        (False, True, False, "REVIEW"),
        (False, False, True, "FALLBACK"),
        (False, False, False, "REVIEW"),
    ],
)
def test_routing_is_explicit_not_silent_v1(trusted, candidate, approved, route):
    result = route_authoring(
        automatic_trusted=trusted, candidate_available=candidate, approved_pack_available=approved
    )
    assert result["route"] == route
    if route == "FALLBACK":
        assert "NOT_V1" in result["condition"]
