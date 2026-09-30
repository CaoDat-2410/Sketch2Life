"""Age-specific adult supervision requirements for activity candidates."""

from __future__ import annotations

from typing import Literal

SupervisionLevel = Literal["NONE", "NEARBY", "DIRECT"]

_SUPERVISION_LABELS_VI: dict[SupervisionLevel, str] = {
    "NONE": "Không cần giám sát trực tiếp",
    "NEARBY": "Người lớn ở gần",
    "DIRECT": "Người lớn hướng dẫn trực tiếp",
}


def supervision_requirement_for_age(
    age_months: int,
    catalog_minimum: SupervisionLevel,
) -> tuple[SupervisionLevel, str]:
    """Apply SRS BR-013 without allowing weaker catalog metadata to lower safety."""
    if age_months < 36:
        return "DIRECT", "Người chăm sóc ở bên và giám sát trực tiếp"
    return catalog_minimum, _SUPERVISION_LABELS_VI[catalog_minimum]
