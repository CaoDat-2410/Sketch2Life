"""FEAT-066 goal v4 T-12b: the static shape of migration ``20261121_bpr_0001`` (DDL-D, offline).

The package (immutable Teacher profile revisions and the head of each managed profile) is approved
by the owner's Phase B launch. The test pins the revision graph (one child of the Story head, 53
revisions, heads stay 15 and 10), the table and its named checks against the ORM mirror, the order
of the upgrade (backfill, reconciliation, NOT NULL, deferred head foreign key, triggers) and the
guarded downgrade. Behaviour and the round trip on real data are in
``tests/integration/test_be1_profile_revisions_postgres.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

from sketch2life.infrastructure.persistence.be1_models import (
    ManagedProfileModel,
    ProfileRevisionModel,
)

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261121_bpr_0001_be1_profile_revisions.py"
_REVISION = "20261121_bpr_0001"
_PARENT = "20261123_rv_0001"
_SOURCE = _MIGRATION.read_text(encoding="utf-8")


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bpr_ddl_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _constants(path: Path) -> dict[str, object]:
    found: dict[str, object] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target, node.value
        if isinstance(target, ast.Name) and target.id in {
            "revision",
            "down_revision",
            "depends_on",
            "branch_labels",
        }:
            assert value is not None
            found[target.id] = ast.literal_eval(value)
    return found


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in _VERSIONS.glob("*.py"):
        found = _constants(path)
        if "revision" not in found:
            continue
        down, depends = found.get("down_revision"), found.get("depends_on")
        graph[str(found["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down),  # type: ignore[arg-type]
            () if depends is None else (depends,) if isinstance(depends, str) else tuple(depends),  # type: ignore[arg-type]
        )
    return graph


# ----------------------------------------------------------------------------- the graph
def test_the_revision_is_the_one_child_of_the_story_head_with_no_label() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == _REVISION and len(_REVISION) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None  # the frc08_lifecycle label is inherited
    assert constants["depends_on"] is None
    graph = _graph()
    # The Phase B squash keeps two parallel children of 20261123_rv_0001: this revision and the
    # AIPORT1 20261113_svg_catalog_review (both are heads; ``alembic upgrade heads`` applies both).
    assert {rev for rev, (downs, _) in graph.items() if _PARENT in downs} == {
        _REVISION,
        "20261113_svg_catalog_review",
    }
    assert {rev for rev, (downs, _) in graph.items() if _REVISION in downs} == {
        "20261121_psn_0002"
    }


def test_one_more_revision_and_the_head_counts_are_sixteen_and_eleven() -> None:
    graph = _graph()
    # T-12a: pce_0001 (Parent root); T-12b: this revision; T-12c: psn_0001, psn_0002
    # 62 after T-10b/T-10c; T-8b and T-NTF1 extend the notification chain.
    assert len(graph) == 64
    down_targets = {target for downs, _ in graph.values() for target in downs}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (16, 11)
    assert _REVISION not in heads_down_only and _REVISION not in heads_with_depends
    assert "20261123_ppg_0001" in heads_down_only and "20261123_ppg_0001" in heads_with_depends
    assert "20261121_psn_0002" not in heads_down_only
    assert _PARENT not in heads_down_only and _PARENT not in heads_with_depends


def test_the_ancestry_holds_the_be1_profile_table_and_the_age_columns() -> None:
    graph = _graph()
    seen: set[str] = set()
    stack = [_REVISION]
    while stack:
        revision = stack.pop()
        if revision in seen:
            continue
        seen.add(revision)
        downs, depends = graph[revision]
        stack.extend((*downs, *depends))
    assert {"20261101_be1_age_0001", "20261014_0002"} <= seen


# ----------------------------------------------------------------------------- the table
def _names(source: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, source))


def test_the_named_constraints_of_the_migration_equal_the_orm_mirror() -> None:
    table = ProfileRevisionModel.__table__
    orm_names = {c.name for c in table.constraints if c.name} | {
        i.name for i in table.indexes if i.name
    }
    migration_names = _names(_SOURCE, r'name="((?:ck|uq|fk)_[a-z0-9_]+)"')
    migration_names -= {"fk_be1_profile_head_revision", "ck_be1_profile_revision_no"}
    assert migration_names == orm_names


def test_the_columns_of_the_migration_equal_the_orm_mirror() -> None:
    columns = [c.name for c in ProfileRevisionModel.__table__.columns]
    assert columns == [
        "profile_revision_id",
        "child_id",
        "revision_no",
        "display_name",
        "age_months",
        "age_band_version",
        "age_band_code",
        "structured_interests",
        "authored_by",
        "created_at",
        "revision_hash_version",
        "revision_hash",
    ]
    for name in columns:
        assert f'"{name}"' in _SOURCE


def test_the_profile_foreign_key_is_restrict_and_the_head_foreign_key_is_deferred() -> None:
    fk = next(
        c
        for c in ProfileRevisionModel.__table__.constraints
        if c.name == "fk_be1_profile_revision_profile"
    )
    assert fk.ondelete == "RESTRICT"  # type: ignore[attr-defined]
    assert 'ondelete="RESTRICT"' in _SOURCE
    head = next(
        c
        for c in ManagedProfileModel.__table__.constraints
        if c.name == "fk_be1_profile_head_revision"
    )
    assert head.deferrable and head.initially == "DEFERRED"  # type: ignore[attr-defined]
    assert 'deferrable=True,\n        initially="DEFERRED"' in _SOURCE
    assert [c.name for c in head.columns] == ["child_id", "current_profile_revision_id"]  # type: ignore[attr-defined]


def test_the_head_columns_are_not_null_in_the_orm_mirror() -> None:
    columns = ManagedProfileModel.__table__.columns
    assert not columns["current_profile_revision_id"].nullable
    assert not columns["profile_revision_no"].nullable


# ----------------------------------------------------------------------------- the upgrade order
def test_the_upgrade_backfills_reconciles_then_sets_not_null_and_the_foreign_key() -> None:
    upgrade = _SOURCE[_SOURCE.index("def upgrade()") : _SOURCE.index("def downgrade()")]
    order = [
        "_create_revision_table()",
        "op.add_column(PROFILES, sa.Column(HEAD_ID",
        "_backfill_baseline()",
        "_reconcile_baseline()",
        "op.alter_column(PROFILES, HEAD_ID",
        "op.create_check_constraint(HEAD_CHECK",
        "op.create_foreign_key(",
        "APPEND_ONLY_FUNCTION_SQL",
        "HEAD_FUNCTION_SQL",
    ]
    positions = [upgrade.index(marker) for marker in order]
    assert positions == sorted(positions)
    assert "nullable=True" in upgrade  # the head columns start nullable
    assert upgrade.count("CREATE CONSTRAINT TRIGGER") == 2
    assert "DEFERRABLE INITIALLY DEFERRED" in upgrade


def test_the_reconciliation_aborts_instead_of_leaving_the_columns_nullable() -> None:
    reconcile = _SOURCE[_SOURCE.index("def _reconcile_baseline()") : _SOURCE.index("def upgrade()")]
    assert "raise RuntimeError" in reconcile
    for marker in ("profile_count != revision_count", "unheaded", "drift", "bad_hash"):
        assert marker in reconcile
    # the message carries counts only, never a name
    assert "display_name" not in reconcile.split("raise RuntimeError")[1]


def test_the_triggers_make_the_revisions_append_only_and_the_head_consistent() -> None:
    module = _load()
    assert "BEFORE UPDATE OR DELETE" in _SOURCE
    assert module.APPEND_ONLY_TRIGGER == "trg_be1_profile_revisions_append_only"
    assert "BE1_PROFILE_REVISION_IS_APPEND_ONLY" in module.APPEND_ONLY_FUNCTION_SQL
    sql = module.HEAD_FUNCTION_SQL
    assert "BE1_PROFILE_HEAD_MISMATCH" in sql and "BE1_PROFILE_HEAD_NOT_LATEST" in sql
    assert "r.revision_no > head_no" in sql
    assert "AFTER INSERT OR UPDATE OF" in _SOURCE and "AFTER INSERT ON public" in _SOURCE


def test_the_baseline_provenance_is_explicit_and_holds_no_interest() -> None:
    module = _load()
    assert module.LEGACY_AUTHOR == "LEGACY_UNCLASSIFIED"
    assert "CAST('[]' AS jsonb)" in _SOURCE


# ----------------------------------------------------------------------------- the downgrade
def test_the_downgrade_guard_runs_first_and_refuses_anything_beyond_the_baseline() -> None:
    module = _load()
    downgrade = _SOURCE[_SOURCE.index("def downgrade()") :]
    assert downgrade.index("DOWNGRADE_GUARD") < downgrade.index("DROP TRIGGER")
    assert "downgrade refused" in module.DOWNGRADE_GUARD
    assert "r.revision_no <> 1" in module.DOWNGRADE_GUARD
    assert "structured_interests <> '[]'::jsonb" in module.DOWNGRADE_GUARD
    # a profile created through the API has a real author: its revision blocks the downgrade
    assert "r.authored_by <> 'LEGACY_UNCLASSIFIED'" in module.DOWNGRADE_GUARD
    drops = [
        "DROP TRIGGER {HEAD_TRIGGER_REVISION}",
        "DROP TRIGGER {HEAD_TRIGGER_PROFILE}",
        "DROP FUNCTION public.{HEAD_FUNCTION}",
        "DROP TRIGGER {APPEND_ONLY_TRIGGER}",
        "DROP FUNCTION public.{APPEND_ONLY_FUNCTION}",
        "op.drop_constraint(HEAD_FK",
        "op.drop_constraint(HEAD_CHECK",
        "op.drop_column(PROFILES, HEAD_NO)",
        "op.drop_column(PROFILES, HEAD_ID)",
        "op.drop_table(TABLE)",
    ]
    positions = [downgrade.index(marker) for marker in drops]
    assert positions == sorted(positions)


# ----------------------------------------------------------------------------- the reconciliation
class _Rows:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one(self) -> object:
        return self._value

    def __iter__(self) -> object:
        return iter(self._value)  # type: ignore[call-overload,no-any-return]


class _Bind:
    """A stub connection that answers the reconciliation queries by their text."""

    def __init__(self, **answers: object) -> None:
        self.answers = answers

    def execute(self, statement: object) -> _Rows:
        sql = str(statement)
        if "IS NULL" in sql:
            return _Rows(self.answers["unheaded"])
        if "JOIN" in sql:
            return _Rows(self.answers["drift"])
        if "revision_hash FROM" in sql:
            return _Rows(self.answers["hashes"])
        if "be1_profile_revisions" in sql:
            return _Rows(self.answers["revisions"])
        return _Rows(self.answers["profiles"])


def _reconcile(monkeypatch: object, **answers: object) -> None:
    module = _load()
    base: dict[str, object] = {
        "profiles": 1,
        "revisions": 1,
        "unheaded": 0,
        "drift": 0,
        "hashes": [],
    }
    base.update(answers)
    monkeypatch.setattr(module.op, "get_bind", lambda: _Bind(**base))  # type: ignore[attr-defined]
    module._reconcile_baseline()


def test_the_reconciliation_passes_and_aborts_on_each_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load()
    good = module._hash("c1", 1, "Synthetic A", 60, [])
    row = type(
        "Row",
        (),
        {
            "child_id": "c1",
            "revision_no": 1,
            "display_name": "Synthetic A",
            "age_months": 60,
            "structured_interests": [],
            "revision_hash": good,
        },
    )
    _reconcile(monkeypatch, hashes=[row])
    for answers in (
        {"revisions": 0},
        {"profiles": 2},
        {"unheaded": 1},
        {"drift": 1},
        {"hashes": [type("Bad", (row,), {"revision_hash": "0" * 64})]},
    ):
        with pytest.raises(RuntimeError, match="does not reconcile") as raised:
            _reconcile(monkeypatch, **{"hashes": [row], **answers})
        assert "Synthetic" not in str(raised.value)
