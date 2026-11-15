from __future__ import annotations

from types import SimpleNamespace

import pytest

from sketch2life.contracts.schemas.svg_engine import SvgTopicStrokeGuideRequestV1
from sketch2life.domain.svg_engine import (
    SvgRuleError,
    validate_source_bound_topic_stroke_guide_v1,
)
from sketch2life.infrastructure.svg import (
    arcadia_gallus_guide,
    openclipart_guide,
    openmoji_guide,
)
from sketch2life.interfaces.http.routers import parent_ai


def test_source_bound_validator_uses_worker_content_schema_version() -> None:
    with pytest.raises(SvgRuleError) as content_error:
        validate_source_bound_topic_stroke_guide_v1(
            {"schema_version": "SvgTopicStrokeGuideContentV1"}, topic="con mèo"
        )
    assert content_error.value.code == "SVG_SOURCE_GUIDE_SHAPE_INVALID"

    with pytest.raises(SvgRuleError) as response_error:
        validate_source_bound_topic_stroke_guide_v1(
            {"schema_version": "SvgTopicStrokeGuideV1"}, topic="con mèo"
        )
    assert response_error.value.code == "SVG_SOURCE_GUIDE_SCHEMA_UNSUPPORTED"


def test_supported_chicken_parent_request_returns_source_contract_without_modal(monkeypatch) -> None:
    monkeypatch.setattr(parent_ai, "_require_parent", lambda *_args: None)
    monkeypatch.setattr(
        parent_ai,
        "get_settings",
        lambda: SimpleNamespace(svg_topic_stroke_guide_generation_enabled=True),
    )

    def reject_modal_call():
        pytest.fail("Pinned Arcadia chicken guide must not dispatch to Modal")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", reject_modal_call)
    response = parent_ai.generate_sketch_guide(
        SvgTopicStrokeGuideRequestV1(topic="con gà"),
        principal=object(),
        db=None,
    )

    payload = response.model_dump(mode="json")
    assert payload["contract"] == "SvgTopicStrokeGuideSourceDraftV1"
    assert payload["generation_source"] == "CURATED_SOURCE_DERIVATION"
    assert payload["reference_source"]["source_sha256"] == (
        "4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed"
    )
    assert payload["path_count"] == 77
    assert payload["stage_count"] == 8
    assert response.derivation.engine_revision == "7.0.0"
    assert response.derivation.method == "EXACT_SOURCE_PATH_SEQUENCE_V7"
    assert payload["reference_illustration"]["schema_version"] == "SvgReferenceIllustrationV1"
    assert len(payload["reference_illustration"]["paths"]) == 77
    assert any(path["fill"] != "none" for path in payload["reference_illustration"]["paths"])
    assert len(payload["derivation"]["path_lineage"]) == 77
    assert {gate for gate in payload["quality_gates_passed"]} >= {
        "EXACT_SOURCE_PATH_GEOMETRY",
        "SOURCE_PATH_COVERAGE_EXACTLY_ONCE",
        "PINNED_SEQUENCE_MANIFEST_HASH",
    }
    assert "REFERENCE_ILLUSTRATION_SANITIZER" in payload["quality_gates_passed"]
    assert payload["review_required"] is True
    assert payload["persisted"] is False
    assert payload.get("modal_call_id") is None
    assert payload.get("model") is None
    assert len(payload["document"]["paths"]) == payload["path_count"]
    assert all(path["fill"] == "none" for path in payload["document"]["paths"])
    source_by_id = {
        path["path_id"]: path for path in payload["reference_illustration"]["paths"]
    }
    for path in payload["document"]["paths"]:
        assert path["d"] == source_by_id[path["path_id"]]["d"]


def test_gallus_hen_alias_uses_registered_source_guide(monkeypatch) -> None:
    monkeypatch.setattr(parent_ai, "_require_parent", lambda *_args: None)
    monkeypatch.setattr(
        parent_ai,
        "get_settings",
        lambda: SimpleNamespace(svg_topic_stroke_guide_generation_enabled=True),
    )

    def reject_modal_call():
        pytest.fail("Pinned Arcadia hen guide must not dispatch to Modal")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", reject_modal_call)
    response = parent_ai.generate_sketch_guide(
        SvgTopicStrokeGuideRequestV1(topic="gà mái"),
        principal=object(),
        db=None,
    )

    assert response.contract == "SvgTopicStrokeGuideSourceDraftV1"
    assert response.derivation.engine_revision == "7.0.0"
    assert response.derivation.method == "EXACT_SOURCE_PATH_SEQUENCE_V7"


def test_unsupported_topic_keeps_existing_modal_gate(monkeypatch) -> None:
    class ExistingModalGateReached(RuntimeError):
        pass

    monkeypatch.setattr(parent_ai, "_require_parent", lambda *_args: None)
    monkeypatch.setattr(
        parent_ai,
        "get_settings",
        lambda: SimpleNamespace(svg_topic_stroke_guide_generation_enabled=True),
    )
    monkeypatch.setattr(parent_ai, "build_openclipart_guide", lambda _topic: None)
    monkeypatch.setattr(parent_ai, "build_openmoji_guide", lambda _topic: None)
    monkeypatch.setattr(parent_ai, "arcadia_source_pack_installed", lambda: False)
    monkeypatch.setattr(
        parent_ai,
        "_require_modal_dev",
        lambda: (_ for _ in ()).throw(ExistingModalGateReached()),
    )

    with pytest.raises(ExistingModalGateReached):
        parent_ai.generate_sketch_guide(
            SvgTopicStrokeGuideRequestV1(topic="con bướm"),
            principal=object(),
            db=None,
        )


def test_missing_optional_source_packs_are_skipped(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        openclipart_guide, "_data_directory", lambda: tmp_path / "missing-openclipart"
    )
    monkeypatch.setattr(
        openmoji_guide, "_source_directory", lambda: tmp_path / "missing-openmoji"
    )
    monkeypatch.setattr(
        arcadia_gallus_guide, "_source_directory", lambda: tmp_path / "missing-arcadia"
    )

    assert openclipart_guide.build_openclipart_guide("con mèo") is None
    assert openmoji_guide.build_openmoji_guide("con mèo") is None
    assert arcadia_gallus_guide.build_arcadia_gallus_guide("con gà") is None


def test_parent_guide_skips_absent_local_packs_before_modal(monkeypatch, tmp_path) -> None:
    class ExistingModalGateReached(RuntimeError):
        pass

    monkeypatch.setattr(parent_ai, "_require_parent", lambda *_args: None)
    monkeypatch.setattr(
        parent_ai,
        "get_settings",
        lambda: SimpleNamespace(svg_topic_stroke_guide_generation_enabled=True),
    )
    monkeypatch.setattr(
        openclipart_guide,
        "_data_directory",
        lambda: tmp_path / "missing-openclipart",
    )
    monkeypatch.setattr(
        openmoji_guide, "_source_directory", lambda: tmp_path / "missing-openmoji"
    )
    monkeypatch.setattr(
        parent_ai, "arcadia_source_pack_installed", lambda: False
    )
    monkeypatch.setattr(
        parent_ai,
        "_require_modal_dev",
        lambda: (_ for _ in ()).throw(ExistingModalGateReached()),
    )

    with pytest.raises(ExistingModalGateReached):
        parent_ai.generate_sketch_guide(
            SvgTopicStrokeGuideRequestV1(topic="con gà"),
            principal=object(),
            db=None,
        )
