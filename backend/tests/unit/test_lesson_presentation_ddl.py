"""Offline static checks for the T-SLD1 migration and SQLAlchemy table mirrors."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.lesson_occurrences.tables import (
    PRESENTATION_REVISIONS,
    PRESENTATION_SVG_DRAFTS,
    PRESENTATION_TABLES,
)

BACKEND = Path(__file__).resolve().parents[2]
VERSIONS = BACKEND / "alembic" / "versions"
MIGRATION = VERSIONS / "20261126_sl_0001_teacher_presentations.py"
PARENT = "20261125_nt_0003"
REVISION = "20261126_sl_0001"


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sl_0001_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _constants(path: Path) -> dict[str, object]:
    found: dict[str, object] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "revision", "down_revision", "branch_labels", "depends_on",
            }:
                found[target.id] = ast.literal_eval(node.value)
    return found


def _revision_refs(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    assert isinstance(value, tuple)
    return tuple(str(item) for item in value)


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in sorted(VERSIONS.glob("*.py")):
        values = _constants(path)
        down, depends = values.get("down_revision"), values.get("depends_on")
        graph[str(values["revision"])] = (_revision_refs(down), _revision_refs(depends))
    return graph


def test_revision_and_provisional_notification_parent_are_explicit() -> None:
    constants = _constants(MIGRATION)
    assert constants == {
        "revision": REVISION,
        "down_revision": PARENT,
        "branch_labels": None,
        "depends_on": None,
    }
    raw = MIGRATION.read_bytes()
    raw.decode("ascii")
    assert b"\r\n" not in raw


def test_graph_links_this_migration_into_the_expected_chain() -> None:
    graph = _graph()
    assert REVISION in graph
    assert graph[REVISION] == ((PARENT,), ())
    assert {
        revision for revision, (downs, _) in graph.items() if PARENT in downs
    } == {REVISION, "20261122_t6b_0001"}
    down_targets = {parent for downs, _ in graph.values() for parent in downs}
    dependency_targets = down_targets | {
        parent for _, parents in graph.values() for parent in parents
    }
    heads_down_only = {revision for revision in graph if revision not in down_targets}
    heads_with_dependencies = {revision for revision in graph if revision not in dependency_targets}
    assert REVISION not in heads_down_only and PARENT not in heads_down_only
    assert PARENT not in heads_with_dependencies


def test_migration_tables_columns_checks_and_indexes_match_the_orm() -> None:
    migration = _load_migration()
    assert migration.SCHEMA == "lesson"
    assert tuple(table.name for table in PRESENTATION_TABLES) == (
        "presentations", "presentation_revisions", "presentation_svg_drafts",
    )
    assert all(table.schema == "lesson" for table in PRESENTATION_TABLES)
    source = MIGRATION.read_text(encoding="ascii")
    expected_checks = {
        "presentations": {"ck_pres_head", "ck_pres_ready", "ck_pres_revision"},
        "presentation_revisions": {
            "ck_presrev_number", "ck_presrev_base", "ck_presrev_plan_hash",
            "ck_presrev_content_hash", "ck_presrev_slides", "ck_presrev_state",
            "ck_presrev_ready_fields",
        },
        "presentation_svg_drafts": {
            "ck_pres_svg_state", "ck_pres_svg_revision", "ck_pres_svg_input_hash",
            "ck_pres_svg_source_hash", "ck_pres_svg_canonical_hash",
            "ck_pres_svg_document", "ck_pres_svg_decided_fields",
        },
    }
    for table in PRESENTATION_TABLES:
        orm_checks = {
            constraint.name
            for constraint in table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        assert orm_checks == expected_checks[table.name]
        assert all(f'name="{name}"' in source for name in orm_checks)
        assert not any(
            word in column.name.lower()
            for column in table.columns
            for word in ("child", "roster", "profile", "drawing")
        )
        foreign_keys = {
            constraint.name: constraint.ondelete
            for constraint in table.constraints
            if isinstance(constraint, ForeignKeyConstraint)
        }
        assert foreign_keys and set(foreign_keys.values()) == {"RESTRICT"}
    assert "uq_presrev_one_ready" in source
    assert {index.name for index in PRESENTATION_REVISIONS.indexes} == {"uq_presrev_one_ready"}
    assert "ix_pres_svg_draft_created" in source
    assert "ix_pres_svg_draft_created" in {index.name for index in PRESENTATION_SVG_DRAFTS.indexes}
    assert "PRESENTATION_DELETE_FORBIDDEN" in source
    assert "PRESENTATION_REVISION_IMMUTABLE" in source
    assert "PRESENTATION_SVG_DRAFT_ILLEGAL_TRANSITION" in source
    assert "Refusing to downgrade teacher presentations" in source


def test_upload_purpose_check_is_mirrored_and_downgrade_guard_is_data_aware() -> None:
    migration = MIGRATION.read_text(encoding="ascii")
    purpose_checks = {
        constraint
        for constraint in UPLOAD_SESSIONS.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name == "ck_core_upload_purpose"
    }
    assert len(purpose_checks) == 1
    assert "PRESENTATION_IMAGE" in str(next(iter(purpose_checks)).sqltext)
    assert "PRESENTATION_IMAGE" in migration
    # The guard literal is split across two source lines.
    assert "FROM public.core_upload_sessions " in migration
    assert "WHERE purpose = 'PRESENTATION_IMAGE'" in migration
