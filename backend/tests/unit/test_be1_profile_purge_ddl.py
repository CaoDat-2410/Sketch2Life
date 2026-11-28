"""Text and graph pins of migration 20261123_ppg_0001 (V4-B T-12b-fix, owner decision Q5).

The behaviour (the purge removes revisions, receipts and support needs; an ordinary UPDATE and
DELETE stay refused; the guard names one child) is proved on PostgreSQL in
``tests/integration/test_be1_profile_revisions_postgres.py`` and the round trip in
``tests/integration/test_support_needs_postgres.py`` (the round-trip test).
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
VERSIONS = BACKEND / "alembic" / "versions"
MIGRATION = VERSIONS / "20261123_ppg_0001_be1_profile_purge.py"
REVISION = "20261123_ppg_0001"
PARENT = "20261121_psn_0002"


def _constants() -> dict[str, object]:
    """The module's constants, imported (SQL constants are f-strings; no database is touched)."""
    spec = importlib.util.spec_from_file_location("ppg_0001_under_test", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {name: getattr(module, name) for name in dir(module) if not name.startswith("__")}


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in VERSIONS.glob("*.py"):
        values: dict[str, object] = {}
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name in {"revision", "down_revision", "depends_on"}:
                    values[name] = ast.literal_eval(node.value)

        def _tuple(value: object) -> tuple[str, ...]:
            if value is None:
                return ()
            return (value,) if isinstance(value, str) else tuple(value)  # type: ignore[arg-type]

        graph[str(values["revision"])] = (
            _tuple(values.get("down_revision")),
            _tuple(values.get("depends_on")),
        )
    return graph


def test_the_revision_is_the_one_child_of_the_be1_head_with_no_label_or_dependency() -> None:
    constants = _constants()
    assert constants["revision"] == REVISION and len(REVISION) <= 32
    assert constants["down_revision"] == PARENT
    assert constants["branch_labels"] is None
    assert constants["depends_on"] is None
    graph = _graph()
    assert {rev for rev, (downs, _) in graph.items() if PARENT in downs} == {REVISION}
    assert {rev for rev, (downs, _) in graph.items() if REVISION in downs} == {
        "20261125_as_0002"
    }


def test_the_head_counts_are_twelve_and_one_with_83_revisions() -> None:
    graph = _graph()
    assert len(graph) == 83
    down_targets = {target for downs, _ in graph.values() for target in downs}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (12, 1)
    assert "20261125_as_0002" not in heads_down_only and "20261125_as_0002" not in heads_with_depends
    assert "20261122_t6b_0001" in heads_down_only
    assert "20261122_t6b_0001" not in heads_with_depends
    assert "20261126_as_0003" in heads_down_only and "20261126_as_0003" in heads_with_depends
    assert REVISION not in heads_down_only and REVISION not in heads_with_depends
    assert {rev for rev, (downs, _) in graph.items() if REVISION in downs} == {
        "20261125_as_0002"
    }
    assert PARENT not in heads_down_only


def _sql(name: str) -> str:
    value = _constants()[name]
    assert isinstance(value, str)
    return value


def test_the_guard_allows_a_delete_of_the_named_child_only() -> None:
    revisions = _sql("REVISION_FUNCTION_PURGE_SQL")
    support = _sql("SUPPORT_FUNCTION_PURGE_SQL")
    # a DELETE of the very row the purge names; an UPDATE and any other DELETE still raise
    assert "TG_OP = 'DELETE'" in revisions
    assert (
        "current_setting('sketch2life.profile_purge', true) IS NOT DISTINCT FROM OLD.child_id"
        in revisions
    )
    assert "RAISE EXCEPTION 'BE1_PROFILE_REVISION_IS_APPEND_ONLY'" in revisions
    assert "IS NOT DISTINCT FROM OLD.child_id" in support
    assert "RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_DELETE_FORBIDDEN'" in support
    assert _constants()["SETTING"] == "sketch2life.profile_purge"


def test_the_original_function_bodies_are_restored_by_the_downgrade() -> None:
    for name in ("REVISION_FUNCTION_ORIGINAL_SQL", "SUPPORT_FUNCTION_ORIGINAL_SQL"):
        body = _sql(name)
        assert "current_setting" not in body and "RETURN OLD" not in body
        assert "RAISE EXCEPTION" in body
    text = MIGRATION.read_text(encoding="utf-8")
    downgrade = text[text.index("def downgrade()") :]
    assert downgrade.index("DROP FUNCTION") < downgrade.index("SUPPORT_FUNCTION_ORIGINAL_SQL")
    assert "REVISION_FUNCTION_ORIGINAL_SQL" in downgrade
    # the downgrade touches no row, so it needs no data guard
    assert "DELETE FROM" not in downgrade and "DROP TABLE" not in downgrade


def test_the_purge_function_deletes_in_a_safe_order_and_returns_counts_only() -> None:
    body = _sql("PURGE_FUNCTION_SQL")
    order = [
        "DELETE FROM public.be1_profile_support_needs",
        "DELETE FROM public.be1_synthetic_eligibility_proofs",
        "DELETE FROM public.be1_command_receipts",
        "DELETE FROM public.be1_profile_revisions",
        "DELETE FROM public.be1_managed_profiles",
    ]
    positions = [body.index(statement) for statement in order]
    assert positions == sorted(positions)
    assert "FOR UPDATE" in body  # the profile row is locked first
    assert "set_config('sketch2life.profile_purge', p_child_id, true)" in body  # transaction local
    assert "set_config('sketch2life.profile_purge', '', true)" in body
    assert "COMMIT" not in body.upper()  # the caller owns the transaction
    returned = re.findall(r"RETURN jsonb_build_object\((.*?)\);", body, re.S)
    assert len(returned) == 2  # nothing found, and the counts after the purge
    assert set(re.findall(r"'(\w+)'", returned[-1])) == {
        "profiles",
        "revisions",
        "support_needs",
        "proofs",
        "receipts",
    }
    assert "display_name" not in body  # no value of a child is read or returned


@pytest.mark.parametrize(
    "shape",
    [
        "'PATCH /organizations/' || p_organization_id || '/classes/'",
        "'/profiles/' || p_child_id || '/move'",
        "'/profiles/' || p_child_id || '/support-needs'",
        "r.response_json ->> 'child_id' = p_child_id",
        "r.response_json ->> 'profile_revision_id' IN",
    ],
)
def test_the_receipt_shapes_of_the_profile_commands_are_covered(shape: str) -> None:
    assert shape in _sql("PURGE_FUNCTION_SQL")


def test_the_purge_function_pins_search_path_and_is_revoked_from_public() -> None:
    body = _sql("PURGE_FUNCTION_SQL")
    assert "SET search_path = pg_catalog, public" in body
    revoke = _sql("REVOKE_SQL")
    assert revoke == (
        "REVOKE ALL ON FUNCTION public.be1_purge_profile(varchar, varchar) FROM PUBLIC"
    )
    text = MIGRATION.read_text(encoding="utf-8")
    upgrade = text[text.index("def upgrade()") : text.index("def downgrade()")]
    assert upgrade.index("PURGE_FUNCTION_SQL") < upgrade.index("REVOKE_SQL")


def test_the_scope_of_the_purge_is_stated_and_the_open_items_are_named() -> None:
    doc = MIGRATION.read_text(encoding="utf-8")
    purge_py = (
        BACKEND / "src" / "sketch2life" / "infrastructure" / "persistence" / "be1_profile_purge.py"
    ).read_text(encoding="utf-8")
    for text in (doc, purge_py):
        assert "does not" in text.lower() or "does NOT" in text
        for table in ("enrollments", "observations"):
            assert table in text
    assert "role split" in doc and "EXECUTE" in doc
    assert "everything that blocks or follows" not in purge_py
