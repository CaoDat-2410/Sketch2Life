"""FEAT-066 goal v4 T-12c: the static shape of migrations ``20261121_psn_0001`` and ``_0002``.

Two revisions (DDL-D): ``parent.profile_support_needs`` on the Parent branch (child of T-12a's
``20261121_pce_0001``) and ``public.be1_profile_support_needs`` on the Story branch (child of
T-12b's ``20261121_bpr_0001``), because the two profile tables live on separate roots. Each is one
child of one head with no ``depends_on``; the current combined graph has 83 revisions, 12 raw
heads, and one dependency-aware effective head
heads. The trigger and constraint behaviour is proven on PostgreSQL in
``tests/integration/test_support_needs_postgres.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table, UniqueConstraint

from sketch2life.infrastructure.persistence.be1_models import Be1ProfileSupportNeedsModel
from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase
from sketch2life.infrastructure.persistence.parent_models import (
    ParentPersistenceBase,
    ParentProfileSupportNeedsModel,
)

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_PARENT_FILE = _VERSIONS / "20261121_psn_0001_parent_support_needs.py"
_BE1_FILE = _VERSIONS / "20261121_psn_0002_be1_support_needs.py"
PARENT_TABLE: Table = ParentProfileSupportNeedsModel.__table__  # type: ignore[assignment]
BE1_TABLE: Table = Be1ProfileSupportNeedsModel.__table__  # type: ignore[assignment]
COLUMNS_PARENT = (
    "parent_profile_id",
    "revision",
    "ciphertext",
    "nonce",
    "key_id",
    "algorithm_version",
    "created_at",
    "updated_at",
)
COLUMNS_BE1 = ("child_id", *COLUMNS_PARENT[1:])


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
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
                "revision",
                "down_revision",
                "branch_labels",
                "depends_on",
            }:
                found[target.id] = ast.literal_eval(node.value)
    return found


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        found = _constants(path)
        down, depends = found.get("down_revision"), found.get("depends_on")
        graph[str(found["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down),  # type: ignore[arg-type]
            () if depends is None else (depends,) if isinstance(depends, str) else tuple(depends),  # type: ignore[arg-type]
        )
    return graph


def _normal(expression: str) -> str:
    return re.sub(r"\s+", " ", expression).strip()


_CASES = [
    pytest.param(
        _PARENT_FILE,
        "20261121_psn_0001",
        "20261121_pce_0001",
        PARENT_TABLE,
        COLUMNS_PARENT,
        "parent.profile_support_needs",
        "parent.child_profiles.parent_profile_id",
        "fk_parent_profile_support_needs_profile",
        "parent_profile_id",
        id="parent",
    ),
    pytest.param(
        _BE1_FILE,
        "20261121_psn_0002",
        "20261121_bpr_0001",
        BE1_TABLE,
        COLUMNS_BE1,
        "public.be1_profile_support_needs",
        "be1_managed_profiles.child_id",
        "fk_be1_profile_support_needs_profile",
        "child_id",
        id="be1",
    ),
]
_ARGS = "path, revision, parent, table, columns, qualified, target, fk_name, key_column"


@pytest.mark.parametrize(_ARGS, _CASES)
def test_each_revision_is_the_one_child_of_one_head_and_declares_no_label(
    path: Path,
    revision: str,
    parent: str,
    table: Table,
    columns: tuple[str, ...],
    qualified: str,
    target: str,
    fk_name: str,
    key_column: str,
) -> None:
    assert _constants(path) == {
        "revision": revision,
        "down_revision": parent,
        "branch_labels": None,
        "depends_on": None,
    }
    assert len(revision) <= 32
    graph = _graph()
    assert {rev for rev, (downs, _) in graph.items() if parent in downs} == {revision}
    # V4-B T-12b-fix: ``20261123_ppg_0001`` is the one child of the BE1 revision.
    assert {rev for rev, (downs, _) in graph.items() if revision in downs} == (
        {"20261123_ppg_0001"} if revision == "20261121_psn_0002" else set()
    )
    assert graph[revision] == ((parent,), ())


def test_the_graph_has_83_revisions_and_twelve_raw_and_one_effective_head() -> None:
    graph = _graph()
    # 53 before T-12c (T-12a: pce_0001; T-12b: bpr_0001); T-12c adds psn_0001 and psn_0002.
    # Phase D adds three revisions, including two new down-only leaves.
    assert len(graph) == 83
    down_targets = {target for downs, _ in graph.values() for target in downs}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (12, 1)
    assert "20261125_as_0002" not in heads_down_only
    assert "20261125_as_0002" not in heads_with_depends
    assert "20261122_t6b_0001" in heads_down_only
    assert "20261122_t6b_0001" not in heads_with_depends
    assert "20261126_as_0003" in heads_down_only and "20261126_as_0003" in heads_with_depends
    assert "20261121_psn_0001" in heads_down_only
    assert "20261121_psn_0001" not in heads_with_depends
    for old in ("20261121_pce_0001", "20261121_bpr_0001", "20261121_psn_0002"):
        assert old not in heads_down_only and old not in heads_with_depends
    # the two revisions never share a parent: a second child of one head would add a head
    assert graph["20261121_psn_0001"][0] != graph["20261121_psn_0002"][0]


def test_the_two_tables_belong_to_their_own_metadata() -> None:
    assert "parent.profile_support_needs" in ParentPersistenceBase.metadata.tables
    assert "be1_profile_support_needs" in CorePersistenceBase.metadata.tables
    assert "be1_profile_support_needs" not in ParentPersistenceBase.metadata.tables


@pytest.mark.parametrize(_ARGS, _CASES)
def test_the_column_list_is_closed_and_holds_no_plaintext_column(
    path: Path,
    revision: str,
    parent: str,
    table: Table,
    columns: tuple[str, ...],
    qualified: str,
    target: str,
    fk_name: str,
    key_column: str,
) -> None:
    assert tuple(column.name for column in table.columns) == columns
    assert not any(column.nullable for column in table.columns)
    assert [column.name for column in table.primary_key.columns] == [key_column]
    source = path.read_text(encoding="utf-8")
    for column in columns:
        assert f'"{column}"' in source, column
    assert not {"note", "category", "text", "value", "content"} & set(columns)
    assert source.count("op.create_table(") == 1
    for forbidden in ("INSERT", "UPDATE " + qualified, "backfill"):
        assert forbidden not in source.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]


@pytest.mark.parametrize(_ARGS, _CASES)
def test_the_checks_equal_the_orm_checks_and_the_names_are_pinned(
    path: Path,
    revision: str,
    parent: str,
    table: Table,
    columns: tuple[str, ...],
    qualified: str,
    target: str,
    fk_name: str,
    key_column: str,
) -> None:
    module = _load(path)
    migration_checks = {name: _normal(expression) for name, expression in module.CHECKS}
    orm_checks = {
        str(constraint.name): _normal(str(constraint.sqltext))
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert migration_checks == orm_checks
    stem = (
        "ck_parent_profile_support_needs"
        if "parent" in qualified
        else "ck_be1_profile_support_needs"
    )
    assert set(migration_checks) == {
        f"{stem}_revision",
        f"{stem}_ciphertext",
        f"{stem}_nonce",
        f"{stem}_key_id",
        f"{stem}_algorithm",
    }
    assert migration_checks[f"{stem}_revision"] == "revision >= 1"
    assert migration_checks[f"{stem}_ciphertext"] == "octet_length(ciphertext) BETWEEN 16 AND 16384"
    assert migration_checks[f"{stem}_nonce"] == "octet_length(nonce) = 12"
    assert migration_checks[f"{stem}_algorithm"] == "algorithm_version = 1"


@pytest.mark.parametrize(_ARGS, _CASES)
def test_the_foreign_key_restricts_and_the_nonce_is_unique_per_key(
    path: Path,
    revision: str,
    parent: str,
    table: Table,
    columns: tuple[str, ...],
    qualified: str,
    target: str,
    fk_name: str,
    key_column: str,
) -> None:
    foreign = [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
    assert len(foreign) == 1 and foreign[0].name == fk_name
    assert foreign[0].ondelete == "RESTRICT"
    assert [element.target_fullname for element in foreign[0].elements] == [target]
    source = path.read_text(encoding="utf-8")
    upgrade = source.split("def upgrade()", 1)[1]
    assert 'ondelete="RESTRICT"' in upgrade and "CASCADE" not in upgrade
    unique = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert len(unique) == 1 and [column.name for column in unique[0].columns] == ["key_id", "nonce"]
    assert str(unique[0].name) in source
    assert not table.indexes  # no index on encrypted bytes; the primary key is the lookup


@pytest.mark.parametrize(_ARGS, _CASES)
def test_the_update_guard_and_the_delete_refusal_are_declared(
    path: Path,
    revision: str,
    parent: str,
    table: Table,
    columns: tuple[str, ...],
    qualified: str,
    target: str,
    fk_name: str,
    key_column: str,
) -> None:
    module = _load(path)
    update_sql = _normal(module.UPDATE_FUNCTION_SQL)
    for needle in (
        "NEW." + key_column + " IS DISTINCT FROM OLD." + key_column,
        "NEW.created_at IS DISTINCT FROM OLD.created_at",
        "NEW.revision IS DISTINCT FROM OLD.revision + 1",
        "NEW.nonce IS NOT DISTINCT FROM OLD.nonce",
    ):
        assert needle in update_sql, needle
    assert "RAISE EXCEPTION" in module.DELETE_FUNCTION_SQL
    source = _normal(path.read_text(encoding="utf-8"))
    assert "BEFORE UPDATE ON" in source and "BEFORE DELETE ON" in source
    assert "UPDATE OR DELETE" not in source


@pytest.mark.parametrize(_ARGS, _CASES)
def test_the_downgrade_refuses_rows_before_it_removes_anything(
    path: Path,
    revision: str,
    parent: str,
    table: Table,
    columns: tuple[str, ...],
    qualified: str,
    target: str,
    fk_name: str,
    key_column: str,
) -> None:
    module = _load(path)
    assert f"SELECT 1 FROM {qualified}" in module.DOWNGRADE_GUARD
    assert (
        "RAISE EXCEPTION" in module.DOWNGRADE_GUARD
        and "downgrade refused" in module.DOWNGRADE_GUARD
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    downgrade = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "downgrade"
    )
    statements = [ast.unparse(statement) for statement in downgrade.body]
    assert "DOWNGRADE_GUARD" in statements[0]
    assert not any("CASCADE" in statement for statement in statements)
    assert any("drop_table" in statement for statement in statements)
