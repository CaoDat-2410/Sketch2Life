from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.activity_preparation import (
    ActivityPreparationCatalogV1,
    ActivityPreparationProfileV1,
)
from sketch2life.infrastructure.catalog.activity_preparation import (
    load_activity_preparation_catalog,
)

ROOT = Path(__file__).resolve().parents[3]


def test_manifest_covers_all_active_activity_variants() -> None:
    catalog = load_activity_preparation_catalog(ROOT)

    assert len(catalog.profiles) == 300
    assert {profile.print_requirement for profile in catalog.profiles} == {
        "NO_PRINTABLE_ASSET",
        "PRINT_RECOMMENDED",
        "PRINT_REQUIRED",
    }
    assert catalog.profile_for("ACT-0102").print_requirement == "PRINT_REQUIRED"
    assert catalog.profile_for("ACT-0102").planned_asset_kinds == (
        "MATCHING_CARD_SET",
        "PICTURE_CARD_SET",
    )


def test_no_print_profile_cannot_carry_printable_metadata() -> None:
    with pytest.raises(ValidationError):
        ActivityPreparationProfileV1.model_validate(
            {
                "activity_ref": {"id": "ACT-0001", "version": 1},
                "catalog_revision": "catalog-2026-09-expansion-1",
                "print_requirement": "NO_PRINTABLE_ASSET",
                "guide_note_vi": "Không cần in.",
                "planned_asset_kinds": ["WORKSHEET"],
                "asset_set_status": "NOT_APPLICABLE",
                "asset_set_refs": [],
                "print_defaults": None,
                "provenance": {
                    "source": "AUTHORED_CATALOG",
                    "review_status": "PENDING_OWNER_REVIEW",
                    "classification_version": "1",
                },
            }
        )


def test_asset_reference_requires_reviewed_ready_profile() -> None:
    with pytest.raises(ValidationError):
        ActivityPreparationProfileV1.model_validate(
            {
                "activity_ref": {"id": "ACT-0002", "version": 1},
                "catalog_revision": "catalog-2026-09-expansion-1",
                "print_requirement": "PRINT_REQUIRED",
                "guide_note_vi": "Cần in phiếu hoạt động.",
                "planned_asset_kinds": ["WORKSHEET"],
                "asset_set_status": "PLANNED",
                "asset_set_refs": ["assets/activity/ACT-0002/pack.pdf"],
                "print_defaults": {"paper_size": "A4", "preferred_format": "PDF"},
                "provenance": {
                    "source": "AUTHORED_CATALOG",
                    "review_status": "PENDING_OWNER_REVIEW",
                    "classification_version": "1",
                },
            }
        )


def test_catalog_rejects_duplicate_activity_refs() -> None:
    catalog = load_activity_preparation_catalog(ROOT)
    record = catalog.profile_for("ACT-0102").model_dump(mode="json")
    with pytest.raises(ValidationError):
        ActivityPreparationCatalogV1.model_validate(
            {
                "catalog_revision": catalog.document.catalog_revision,
                "profiles": [record, record],
            }
        )
