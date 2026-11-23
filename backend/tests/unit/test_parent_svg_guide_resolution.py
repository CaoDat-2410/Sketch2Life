from __future__ import annotations

import pytest

from sketch2life.application.services.parent_svg_guide import build_parent_svg_guide
from sketch2life.infrastructure.svg.openmoji_guide import build_openmoji_guide


@pytest.mark.parametrize("subject", ["Rùa biển", "Con rùa biển", "Rua Bien"])
def test_parent_svg_guide_resolves_exact_sea_turtle_aliases(subject: str) -> None:
    result = build_parent_svg_guide(
        topic="Đại dương", intended_subject=subject, builders=(build_openmoji_guide,)
    )

    assert result is not None
    assert result["intended_subject"] == subject
    assert result["generation_source"] == "CURATED_SOURCE_DERIVATION"
    assert result["derivation"]["engine_id"] == "openmoji-source-shape-guide"
    assert 4 <= result["stage_count"] <= 8
    assert result["reference_source"]["dataset_name"] == "OpenMoji"


def test_openmoji_does_not_match_unrelated_sea_subject_to_turtle() -> None:
    assert build_openmoji_guide("Sao biển") is None
    assert build_openmoji_guide("Rùa biển") is not None
