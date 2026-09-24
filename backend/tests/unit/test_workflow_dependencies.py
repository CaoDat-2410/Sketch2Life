from __future__ import annotations

from pathlib import Path

from sketch2life.infrastructure.catalog.workflow_metadata import (
    FileWorkflowCatalogMetadata,
)
from sketch2life.interfaces.cli.workflow_demo import build_real_workflow_dependencies

ROOT = Path(__file__).resolve().parents[3]


def test_application_layer_has_no_outer_layer_imports() -> None:
    application_root = ROOT / "backend" / "src" / "sketch2life" / "application"
    forbidden = ("sketch2life.infrastructure", "sketch2life.interfaces")
    offenders = [
        path
        for path in application_root.rglob("*.py")
        if any(token in path.read_text(encoding="utf-8") for token in forbidden)
    ]
    assert offenders == []


def test_file_metadata_adapter_exposes_authored_material_and_multiday_duration() -> None:
    metadata = FileWorkflowCatalogMetadata(ROOT)

    assert metadata.primary_material_ids("ACT-0123") == (
        "MAT_PLANT_TRAY",
        "MAT_WATER_BASIN",
    )
    assert metadata.duration_spec("ACT-0123") == {
        "duration_type": "MULTI_DAY",
        "min_minutes": None,
        "max_minutes": None,
        "initial_session_minutes": 20,
        "daily_observation_minutes": 5,
        "min_days": 3,
        "max_days": 5,
    }
    preparation = metadata.preparation_profile("ACT-0102")
    assert preparation.print_requirement == "PRINT_REQUIRED"
    assert preparation.asset_set_status == "PLANNED"
    assert preparation.print_defaults is not None


def test_real_composition_builds_complete_dependency_bundle() -> None:
    dependencies = build_real_workflow_dependencies(ROOT, include_expansion=True)

    dependencies.asset_catalog.validate_all_age_bands()
    assert dependencies.template_library.templates
    assert dependencies.semantic_catalog.profile_for("ACT-0001")
    assert dependencies.semantic_catalog_v2 is not None
    assert dependencies.catalog_metadata.duration_spec("ACT-0001") is not None
