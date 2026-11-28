"""FEAT-066 T-4b1: the static shape of migration ``20261120_sel_0001`` (offline).

The table is metadata only (owner conditions 1 and 2, SRS l.354, BR-34): the column list is closed
and no column can hold a name, an age, a seed or a drawn index. The ORM mirror equals the migration,
the constraint, index and trigger names are pinned, and the revision graph keeps one linear
``lesson_library`` chain that now ends here. The behaviour of the trigger and the purge flag is
proven on PostgreSQL in ``tests/integration/lesson_occurrences/test_child_selection_postgres.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import sqlalchemy as sa

from sketch2life.infrastructure.lesson_occurrences.tables import CHILD_SELECTIONS, DDL_A_TABLES

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_sel_0001_child_selection.py"
_PARENT = "20261120_nt_0001"
_LIBRARY_ROOT = "20261028_ll_0001"

EXPECTED_COLUMNS = (
    "seq",
    "selection_id",
    "occurrence_id",
    "plan_revision_id",
    "organization_ref",
    "class_ref",
    "teacher_ref",
    "kind",
    "draw_no",
    "policy_version",
    "eligibility_basis",
    "candidate_count",
    "candidate_set_hash",
    "selected_child_ref",
    "class_revision",
    "occurrence_revision",
    "state",
    "revision",
    "issued_at",
    "expires_at",
    "confirmed_at",
    "confirmed_by",
    "confirmation_expires_at",
    "consumed_at",
    "consumed_run_ref",
    "created_at",
)
# Whatever a re-identifying or draw-reproducing value could be called.
FORBIDDEN_WORDS = ("name", "age", "seed", "index", "random", "rand", "draw_index", "salt", "title")


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sel_0001_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _migration_columns() -> dict[str, bool]:
    """Column name -> nullable, read from the ``_columns`` function of the migration."""
    module = ast.parse(_MIGRATION.read_text(encoding="utf-8"))
    function = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef) and node.name == "_columns"
    )
    result: dict[str, bool] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "sa.Column":
            name = node.args[0]
            assert isinstance(name, ast.Constant)
            flags = {kw.arg: kw.value for kw in node.keywords}
            primary = "primary_key" in flags
            not_null = (
                isinstance(flags.get("nullable"), ast.Constant) and flags["nullable"].value is False  # type: ignore[attr-defined]
            )
            result[str(name.value)] = not (primary or not_null)
    return result


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


def _graph() -> dict[str, tuple[str, ...]]:
    graph: dict[str, tuple[str, ...]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        found = _constants(path)
        down = found.get("down_revision")
        graph[str(found["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down)  # type: ignore[arg-type]
        )
    return graph


# ----------------------------------------------------------------------------- the revision graph
def test_revision_is_the_only_child_of_nt_0001_before_the_remix_lineage_head() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == "20261120_sel_0001" and len(str(constants["revision"])) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None and constants["depends_on"] is None
    graph = _graph()
    children: dict[str, set[str]] = {}
    for revision, downs in graph.items():
        for down in downs:
            children.setdefault(down, set()).add(revision)
    assert children[_PARENT] == {"20261120_sel_0001"}
    assert children["20261120_sel_0001"] == {"20261121_ll_0001"}
    assert children["20261121_ll_0001"] == {"20261121_pg_0001"}
    assert children["20261121_pg_0001"] == {"20261121_nt_0002"}
    assert children["20261121_nt_0002"] == {"20261125_nt_0003"}
    assert children["20261125_nt_0003"] == {
        "20261122_t6b_0001",
        "20261126_sl_0001",
    }
    assert children["20261126_sl_0001"] == {"20261126_sh_0001"}
    assert children["20261126_sh_0001"] == {"20261126_dc_0001"}
    assert "20261126_dc_0001" not in children
    node, chain = _LIBRARY_ROOT, [_LIBRARY_ROOT]
    while children.get(node):
        # FEAT-072: the Platform Admin chain (20261119_admin_foundation onward) branches from
        # 20261110_ar_0001 as its own branch; it is not part of the lesson_library chain.
        # T-6b starts a transfer branch from 20261125_nt_0003; it is parallel to the
        # lesson-library continuation and does not change this chain.
        next_nodes = {
            child
            for child in children[node]
                if "_admin_" not in child
                and child not in {"20261122_t6b_0001", "20261110_parent_profiles"}
        }
        if not next_nodes:
            break
        assert len(next_nodes) == 1, node
        (node,) = next_nodes
        chain.append(node)
    assert chain[-9:] == [
        _PARENT,
        "20261120_sel_0001",
        "20261121_ll_0001",
        "20261121_pg_0001",
        "20261121_nt_0002",
        "20261125_nt_0003",
        "20261126_sl_0001",
        "20261126_sh_0001",
        "20261126_dc_0001",
    ]


def test_the_graph_has_83_revisions_and_twelve_raw_heads() -> None:
    graph = _graph()
    # T-4b2 follows the video branch; final as_0003 dependencies order all independent leaves.
    # The final receipt repair depends on all branch heads, leaving one effective head.
    # FEAT-066 goal v4 T-2e-a adds 20261123_as_0001 (DDL-B3) on the Story branch (heads unchanged).
    # FEAT-066 goal v4 T-1b-fix adds 20261123_rv_0001 (DDL-B1c) on the same branch (heads same).
    # FEAT-066 goal v4 T-12a adds 20261121_pce_0001 (DDL-D) on the Parent root (one new head).
    # FEAT-066 goal v4 T-12b adds 20261121_bpr_0001 (DDL-D) as a second child of 20261123_rv_0001,
    # parallel to the AIPORT1 20261113_svg_catalog_review (the Phase B squash keeps both heads).
    # FEAT-066 goal v4 T-12c adds 20261121_psn_0001 (Parent root) and 20261121_psn_0002 (bpr).
    # FEAT-066 goal v4 T-12b-fix adds 20261123_ppg_0001 on the BE1 branch (squash: 55 + 5).
    # Phase D adds three revisions and the t6b_0001/t6c_0001 down-only leaves.
    assert len(graph) == 83
    down_targets = {target for downs in graph.values() for target in downs}
    down_heads = {revision for revision in graph if revision not in down_targets}
    assert len(down_heads) == 12
    assert {"20261122_t6b_0001", "20261126_as_0003"} <= down_heads


# ------------------------------------------------------------------- the closed column list
def test_the_column_list_is_closed_and_equals_the_orm_mirror() -> None:
    migration = _migration_columns()
    assert tuple(migration) == EXPECTED_COLUMNS
    assert tuple(column.name for column in CHILD_SELECTIONS.columns) == EXPECTED_COLUMNS
    assert {column.name: column.nullable for column in CHILD_SELECTIONS.columns} == migration
    assert (
        CHILD_SELECTIONS.schema == "lesson"
        and CHILD_SELECTIONS.name == "occurrence_child_selections"
    )
    assert CHILD_SELECTIONS not in DDL_A_TABLES  # DDL-A is the five original tables


def test_no_column_can_hold_a_name_an_age_a_seed_or_a_drawn_index() -> None:
    for name in EXPECTED_COLUMNS:
        lowered = name.lower()
        assert not any(word in lowered for word in FORBIDDEN_WORDS), name
    for column in CHILD_SELECTIONS.columns:
        # No free text and no JSON: only bounded refs, hashes, counts and timestamps.
        assert not isinstance(column.type, (sa.Text, sa.JSON)), column.name
        if isinstance(column.type, sa.String):
            assert column.type.length is not None and column.type.length <= 128, column.name


def test_the_seq_column_is_an_always_identity_used_for_ordering_only() -> None:
    column = CHILD_SELECTIONS.c.seq
    assert isinstance(column.identity, sa.Identity) and column.identity.always is True
    text = _MIGRATION.read_text(encoding="utf-8")
    assert 'sa.UniqueConstraint("seq", name="uq_sel_seq")' in text


def test_orm_columns_and_the_trigger_freeze_agree() -> None:
    module = _load()
    mutable = {
        "state",
        "revision",
        "confirmed_at",
        "confirmed_by",
        "confirmation_expires_at",
        "consumed_at",
        "consumed_run_ref",
    }
    assert set(EXPECTED_COLUMNS) - set(module.FROZEN_COLUMNS) == mutable
    assert set(module.FROZEN_COLUMNS) <= set(EXPECTED_COLUMNS)


# ----------------------------------------------------------------------------- names
def test_constraint_index_and_trigger_names_are_pinned() -> None:
    module = _load()
    assert module.SCHEMA == "lesson" and module.TABLE == "occurrence_child_selections"
    assert [name for name, _text in module.CHECKS] == [
        "ck_sel_id_uuid",
        "ck_sel_kind",
        "ck_sel_state",
        "ck_sel_basis",
        "ck_sel_policy",
        "ck_sel_hash",
        "ck_sel_revision",
        "ck_sel_class_revision",
        "ck_sel_kind_draw",
        "ck_sel_empty_shape",
        "ck_sel_confirm_cols",
        "ck_sel_consume_cols",
    ]
    text = _MIGRATION.read_text(encoding="utf-8")
    for name in (
        "fk_sel_occurrence",
        "fk_sel_plan",
        "uq_sel_seq",
        "uq_sel_live",
        "uq_sel_draw",
        "uq_sel_consumed_run",
        "ix_sel_occurrence",
        "ix_sel_child",
    ):
        assert f'"{name}"' in text, name
    assert module.TRIGGER == module.FUNCTION == "protect_child_selection"
    assert module.PURGE_FLAG == "sketch2life.child_selection_purge"


def test_partial_unique_indexes_have_their_predicates() -> None:
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "postgresql_where=sa.text(\"state IN ('OPEN', 'CONFIRMED')\")" in text
    assert "postgresql_where=sa.text(\"kind IN ('DRAW', 'RESELECT')\")" in text
    assert 'postgresql_where=sa.text("consumed_run_ref IS NOT NULL")' in text
    assert 'postgresql_where=sa.text("selected_child_ref IS NOT NULL")' in text
    uq_draw = text[text.index('"uq_sel_draw"') : text.index('"uq_sel_consumed_run"')]
    assert '["occurrence_id", "draw_no"]' in uq_draw and "unique=True" in uq_draw


def test_checks_pin_the_basis_the_shapes_and_the_id_format() -> None:
    module = _load()
    checks = dict(module.CHECKS)
    assert checks["ck_sel_basis"] == "eligibility_basis = 'SYNTHETIC_DEV'"
    assert "'REAL'" not in " ".join(checks.values())
    assert (
        "kind = 'EMPTY' AND state = 'EMPTY' AND candidate_count = 0" in checks["ck_sel_empty_shape"]
    )
    assert "draw_no IS NULL" in checks["ck_sel_kind_draw"]
    assert "draw_no = 2" in checks["ck_sel_kind_draw"]
    pattern = re.search(r"'(\^.*\$)'", checks["ck_sel_id_uuid"])
    assert pattern is not None
    for _ in range(50):
        assert re.fullmatch(pattern.group(1), str(uuid4()))  # R2 N-9: a canonical uuid4 string
    assert not re.fullmatch(pattern.group(1), "sel-1")
    assert not re.fullmatch(pattern.group(1), str(uuid4()).upper())


# ------------------------------------------------------------------- trigger and downgrade
def test_trigger_function_text() -> None:
    module = _load()
    function = module.FUNCTION_SQL
    for code in (
        "CHILD_SELECTION_DELETE_FORBIDDEN",
        "CHILD_SELECTION_INSERT_NOT_FRESH",
        "CHILD_SELECTION_INSERT_STATE",
        "CHILD_SELECTION_SCOPE_MISMATCH",
        "CHILD_SELECTION_IMMUTABLE",
        "CHILD_SELECTION_REVISION",
        "CHILD_SELECTION_STATE_EDGE",
        "CHILD_SELECTION_CONFIRM_COLUMNS",
        "CHILD_SELECTION_CONSUME_COLUMNS",
    ):
        assert code in function, code
    assert "current_setting('sketch2life.child_selection_purge', true)" in function
    assert "= 'on'" in function
    # the legal edges of the state machine, as in the domain table
    assert (
        "OLD.state = 'OPEN' AND NEW.state IN ('CONFIRMED', 'EXPIRED', 'STALE', 'VOID')" in function
    )
    assert (
        "OLD.state = 'CONFIRMED' AND NEW.state IN ('CONSUMED', 'EXPIRED', 'STALE', 'VOID')"
        in function
    )
    from sketch2life.domain.lesson_occurrences.child_selection import STATE_EDGES

    assert {
        "OPEN": frozenset({"CONFIRMED", "EXPIRED", "STALE", "VOID"}),
        "CONFIRMED": frozenset({"CONSUMED", "EXPIRED", "STALE", "VOID"}),
    } == STATE_EDGES


def test_downgrade_refuses_while_rows_exist_and_drops_only_its_own_objects() -> None:
    module = _load()
    assert "IF EXISTS (SELECT 1 FROM lesson.occurrence_child_selections)" in module.DOWNGRADE_GUARD
    assert "RAISE EXCEPTION" in module.DOWNGRADE_GUARD
    text = _MIGRATION.read_text(encoding="utf-8")
    body = text[text.index("def downgrade()") :]
    assert body.index("DOWNGRADE_GUARD") < body.index("DROP TRIGGER") < body.index("drop_table")
    assert "DELETE" not in body.replace("DELETE_FORBIDDEN", "")
    # one table, no change to an existing table
    upgrade = text[text.index("def upgrade()") : text.index("def downgrade()")]
    assert "ALTER TABLE" not in upgrade and "op.alter_column" not in upgrade
    assert upgrade.count("op.create_table") == 1
    assert "alembic downgrade 20261120_nt_0001" in text and "never ``-1``" in text
