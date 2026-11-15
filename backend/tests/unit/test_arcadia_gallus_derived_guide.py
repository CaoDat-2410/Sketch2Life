from __future__ import annotations

import hashlib
import json
import shutil

import pytest

from sketch2life.infrastructure.svg import arcadia_gallus_guide


def test_v7_guide_uses_every_exact_pinned_source_path_once() -> None:
    derived = arcadia_gallus_guide.build_arcadia_gallus_guide("con gà")

    assert derived is not None
    assert derived.reference_source.source_sha256 == (
        "4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed"
    )
    assert derived.source_path_count == 77
    assert derived.engine_id == "arcadia-source-svg-path-sequence"
    assert derived.engine_revision == "7.0.0"
    assert derived.derivation_method == "EXACT_SOURCE_PATH_SEQUENCE_V7"
    assert len(derived.generated.document.paths) == 77
    assert len(derived.generated.stages) == 8

    reference_by_id = {
        path.path_id: path for path in derived.reference_illustration.paths
    }
    guide_path_ids = [path.path_id for path in derived.generated.document.paths]
    staged_path_ids = [
        path_id
        for stage in derived.generated.stages
        for path_id in stage.new_path_ids
    ]
    assert len(guide_path_ids) == len(set(guide_path_ids)) == 77
    assert staged_path_ids == guide_path_ids
    assert set(guide_path_ids) == set(reference_by_id)
    for guide_path in derived.generated.document.paths:
        source_path = reference_by_id[guide_path.path_id]
        assert guide_path.d == source_path.d
        assert guide_path.fill == "none"
        assert guide_path.stroke == "#221f1f"
        assert guide_path.stroke_width == source_path.stroke_width

    assert len(derived.path_lineage) == 77
    assert all(
        item["derived_path_id"] == item["source_path_ids"][0]
        and item["operation"] == "EXACT_SOURCE_PATH_SEQUENCE_V7"
        for item in derived.path_lineage
    )
    assert [stage.step_index for stage in derived.generated.stages] == list(range(1, 9))
    assert [stage.instruction_vi for stage in derived.generated.stages] == [
        "Bắt đầu bằng đường bao lớn của thân và cổ gà.",
        "Thêm mào, mỏ, yếm và các nét trên mặt.",
        "Vẽ hai chân cùng dáng bàn chân đứng vững.",
        "Thêm phần cánh và chiếc đuôi vươn lên phía sau.",
        "Vẽ các nét lông cong ở phần thân dưới.",
        "Hoàn thiện các nét lông trên cổ và ngực.",
        "Thêm các nét cong tạo thành nhiều lớp lông đuôi.",
        "Cuối cùng, thêm các nét lông trên cánh và lưng.",
    ]


def test_v7_manifest_hash_and_source_hash_are_pinned() -> None:
    source_dir = arcadia_gallus_guide._source_directory()
    manifest_hash = hashlib.sha256(
        (source_dir / arcadia_gallus_guide._SOURCE_PATH_SEQUENCE_FILENAME).read_bytes()
    ).hexdigest()
    source_hash = hashlib.sha256(
        (source_dir / arcadia_gallus_guide._SOURCE_FILENAME).read_bytes()
    ).hexdigest()
    assert manifest_hash == arcadia_gallus_guide._SOURCE_PATH_SEQUENCE_SHA256
    assert source_hash == "4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed"


def test_non_chicken_topic_does_not_select_arcadia_derivation() -> None:
    assert arcadia_gallus_guide.build_arcadia_gallus_guide("con bướm") is None


def test_source_hash_mismatch_fails_closed(tmp_path, monkeypatch) -> None:
    source_dir = arcadia_gallus_guide._source_directory()
    shutil.copytree(source_dir, tmp_path, dirs_exist_ok=True)
    source_path = tmp_path / arcadia_gallus_guide._SOURCE_FILENAME
    source_path.write_bytes(source_path.read_bytes() + b"\n")
    monkeypatch.setattr(arcadia_gallus_guide, "_source_directory", lambda: tmp_path)

    with pytest.raises(
        arcadia_gallus_guide.ArcadiaDerivedGuideUnavailable,
        match="SVG_ARCADIA_SOURCE_HASH_MISMATCH",
    ):
        arcadia_gallus_guide.build_arcadia_gallus_guide("gà trống")


def test_modified_stage_manifest_fails_closed(tmp_path, monkeypatch) -> None:
    source_dir = arcadia_gallus_guide._source_directory()
    shutil.copytree(source_dir, tmp_path, dirs_exist_ok=True)
    manifest_path = tmp_path / arcadia_gallus_guide._SOURCE_PATH_SEQUENCE_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["stages"][0]["instruction_vi"] = "Một câu hướng dẫn khác."
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(arcadia_gallus_guide, "_source_directory", lambda: tmp_path)

    with pytest.raises(
        arcadia_gallus_guide.ArcadiaDerivedGuideUnavailable,
        match="SVG_ARCADIA_GUIDE_MANIFEST_HASH_MISMATCH",
    ):
        arcadia_gallus_guide.build_arcadia_gallus_guide("rooster")


def test_stage_partition_rejects_missing_or_repeated_source_path() -> None:
    source_dir = arcadia_gallus_guide._source_directory()
    manifest = json.loads(
        (source_dir / arcadia_gallus_guide._SOURCE_PATH_SEQUENCE_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    expected = [f"source-path-{index:03d}" for index in range(1, 78)]
    stages = manifest["stages"]
    stages[-1]["path_ids"].pop()

    with pytest.raises(
        arcadia_gallus_guide.ArcadiaDerivedGuideUnavailable,
        match="SVG_ARCADIA_SOURCE_PATH_COVERAGE_INVALID",
    ):
        arcadia_gallus_guide._build_v7_guide_structure(stages, expected)
