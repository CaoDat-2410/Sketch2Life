"""The managed-profile age is written only by two named creation paths.

The detector below is a static source scan, not a runtime guard. It reports every write shape
that can set or change ``be1_managed_profiles.age_months``: constructor calls, attribute and
``setattr`` writes, ORM/Core ``update``/``insert`` statements, bulk mapping helpers, and raw
SQL strings. The meta tests feed the detector pseudo-source for each shape, so a regression in
the detector itself fails here instead of silently letting a new write path through.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from sketch2life.infrastructure.persistence.be1_models import ManagedProfileModel
from sqlalchemy import update
from sqlalchemy.dialects import postgresql

PROFILE_MODEL = "ManagedProfileModel"
PROFILE_TABLE = "be1_managed_profiles"
AGE_COLUMN = "age_months"
AGE_PROVENANCE_COLUMNS = frozenset({"age_months", "age_revision", "age_source"})

# (source file relative to src/, function name, write kind). Adding a new write path means
# adding an entry here in the same change, with a reviewer who agrees it is a creation path.
ALLOWED_CREATION_PATHS: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("sketch2life/interfaces/http/routers/be1_registry.py", "create_profile", "constructor"),
        (
            "sketch2life/infrastructure/persistence/core_store.py",
            "create_synthetic_profile",
            "constructor",
        ),
    }
)

Finding = tuple[str, str, str]

_SQL_WRITE = re.compile(r"\b(update|insert)\b", re.IGNORECASE)
_MUTATING_CALLS = {"update", "insert", "delete"}
_BULK_CALLS = {"bulk_insert_mappings", "bulk_update_mappings", "bulk_save_objects"}


def _mentions_profile(node: ast.AST, tainted: set[str]) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and (child.id == PROFILE_MODEL or child.id in tainted):
            return True
        if isinstance(child, ast.Attribute) and child.attr == PROFILE_MODEL:
            return True
        if isinstance(child, ast.Constant) and child.value == PROFILE_TABLE:
            return True
    return False


def _tainted_names(tree: ast.AST) -> set[str]:
    """Names (module-wide, flow-insensitive) bound to the profile model or its table."""

    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name == PROFILE_MODEL and alias.asname and alias.asname not in tainted:
                        tainted.add(alias.asname)
                        changed = True
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if _mentions_profile(node.value, tainted):
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id not in tainted:
                            tainted.add(target.id)
                            changed = True
    return tainted


def _attribute_targets(target: ast.AST) -> Iterator[ast.Attribute]:
    if isinstance(target, ast.Attribute):
        yield target
    elif isinstance(target, (ast.Tuple, ast.List)):
        for item in target.elts:
            yield from _attribute_targets(item)
    elif isinstance(target, ast.Starred):
        yield from _attribute_targets(target.value)


def _dict_has_age_key(node: ast.AST) -> bool:
    return isinstance(node, ast.Dict) and any(
        isinstance(key, ast.Constant) and key.value in AGE_PROVENANCE_COLUMNS for key in node.keys
    )


def _values_for_key(call: ast.Call, key: str) -> list[ast.AST]:
    values: list[ast.AST] = [keyword.value for keyword in call.keywords if keyword.arg == key]
    for argument in call.args:
        if isinstance(argument, ast.Dict):
            values.extend(
                value
                for item_key, value in zip(argument.keys, argument.values, strict=True)
                if isinstance(item_key, ast.Constant) and item_key.value == key
            )
    return values


def _is_revision_increment(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Add)
        and isinstance(node.right, ast.Constant)
        and node.right.value == 1
        and isinstance(node.left, ast.Attribute)
        and node.left.attr == "age_revision"
    )


def find_unpaired_age_updates(source: str, relative: str) -> set[tuple[str, int]]:
    """Find profile UPDATE values that change age without incrementing age_revision in-place."""

    tree = ast.parse(source, filename=relative)
    parents: dict[ast.AST, ast.AST] = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    tainted = _tainted_names(tree)
    unpaired: set[tuple[str, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not (
            isinstance(node.func, ast.Attribute) and node.func.attr == "values"
        ):
            continue
        if not _mentions_profile(node.func, tainted) or not _values_for_key(node, AGE_COLUMN):
            continue
        if any(_is_revision_increment(value) for value in _values_for_key(node, "age_revision")):
            continue

        parent: ast.AST | None = node
        function_name = "<module>"
        while parent is not None:
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_name = parent.name
                break
            parent = parents.get(parent)
        unpaired.add((function_name, node.lineno))
    return unpaired


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def find_age_write_paths(source: str, relative: str) -> set[Finding]:
    """Return ``(file, function, kind)`` for every managed-profile age write shape found."""

    tree = ast.parse(source, filename=relative)
    parents: dict[ast.AST, ast.AST] = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    tainted = _tainted_names(tree)
    docstrings = _docstring_ids(tree)
    found: set[Finding] = set()

    def record(node: ast.AST, kind: str) -> None:
        parent: ast.AST | None = node
        function_name = "<module>"
        while parent is not None:
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_name = parent.name
                break
            parent = parents.get(parent)
        found.add((relative, function_name, kind))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            callee = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else None
            )

            # (a) ManagedProfileModel age/provenance fields, also via module/alias or **kwargs.
            is_model_ctor = (
                isinstance(func, ast.Name) and (func.id == PROFILE_MODEL or func.id in tainted)
            ) or (isinstance(func, ast.Attribute) and func.attr == PROFILE_MODEL)
            if is_model_ctor and any(
                k.arg in AGE_PROVENANCE_COLUMNS or k.arg is None for k in node.keywords
            ):
                record(node, "constructor")

            # (d) .values(age/provenance=...) / .values({...}) on any statement.
            if callee == "values":
                age_keyword = any(
                    keyword.arg in AGE_PROVENANCE_COLUMNS for keyword in node.keywords
                )
                age_dict = any(_dict_has_age_key(arg) for arg in node.args)
                kwargs_on_profile = any(k.arg is None for k in node.keywords) and (
                    _mentions_profile(func, tainted)
                )
                if age_keyword or age_dict or kwargs_on_profile:
                    record(node, "values")

            # (d)/(g) update()/insert()/delete() whose target is the profile model or table:
            # update(Model), insert(Model), Model.__table__.update(), query(Model).update(...).
            if callee in _MUTATING_CALLS and _mentions_profile(node, tainted):
                record(node, "statement")

            # bulk ORM helpers that take the profile model as the mapper.
            if callee in _BULK_CALLS and any(_mentions_profile(arg, tainted) for arg in node.args):
                record(node, "bulk")

            # (e) setattr(obj, age/provenance field, ...)
            if (
                isinstance(func, ast.Name)
                and func.id == "setattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in AGE_PROVENANCE_COLUMNS
            ):
                record(node, "setattr")

        # (c) profile age/provenance fields via assignment, augassign or tuple targets.
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                attribute.attr in AGE_PROVENANCE_COLUMNS
                for target in targets
                for attribute in _attribute_targets(target)
            ):
                record(node, "attribute")

        # (f) raw SQL text with a write verb and the column or table (docstrings excluded).
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and _SQL_WRITE.search(node.value)
            and (
                any(column in node.value for column in AGE_PROVENANCE_COLUMNS)
                or PROFILE_TABLE in node.value
            )
        ):
            record(node, "raw_sql")

    return found


def check_against_allowlist(findings: set[Finding], allowed: frozenset[Finding]) -> None:
    """Fail with a message that names the new write path and the file to change."""

    unexpected = sorted(findings - allowed)
    if unexpected:
        lines = "; ".join(f"{path}::{function} ({kind})" for path, function, kind in unexpected)
        raise AssertionError(
            "New managed-profile age write path(s) found: "
            f"{lines}. Managed-profile age/provenance fields may only be set by the allowed "
            "creation paths "
            "(see ALLOWED_CREATION_PATHS in test_profile_age_invariant.py); "
            "review and extend that list only for a genuine creation path."
        )
    missing = sorted(allowed - findings)
    if missing:
        lines = "; ".join(f"{path}::{function} ({kind})" for path, function, kind in missing)
        raise AssertionError(
            f"Allowed creation path(s) no longer found: {lines}. "
            "Update ALLOWED_CREATION_PATHS if the creation path moved."
        )


def test_managed_profile_age_is_written_only_by_the_two_creation_paths() -> None:
    source_root = Path(__file__).parents[2] / "src"
    found: set[Finding] = set()
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root).as_posix()
        source = path.read_text(encoding="utf-8")
        found |= find_age_write_paths(source, relative)
        unpaired = find_unpaired_age_updates(source, relative)
        assert not unpaired, (
            "Every managed-profile age UPDATE must increment age_revision in the same statement: "
            f"{relative}::{sorted(unpaired)}"
        )

    check_against_allowlist(found, ALLOWED_CREATION_PATHS)


def test_a_future_age_change_updates_age_revision_in_the_same_statement() -> None:
    update_statement = cast(Any, update)
    statement = update_statement(ManagedProfileModel).values(
        age_months=61,
        age_revision=ManagedProfileModel.age_revision + 1,
    )
    compile_statement = cast(Callable[..., object], statement.compile)
    dialect_factory = cast(Callable[[], object], postgresql.dialect)
    compiled = str(
        compile_statement(dialect=dialect_factory(), compile_kwargs={"literal_binds": True})
    )

    assert "age_months=61" in compiled
    assert "age_revision=(be1_managed_profiles.age_revision + 1)" in compiled
    assert "age_source" not in compiled


def test_age_update_detector_rejects_missing_or_nonincrementing_revision() -> None:
    assert not find_unpaired_age_updates(
        "def f():\n"
        "    stmt = update(ManagedProfileModel).values("
        "age_months=61, age_revision=ManagedProfileModel.age_revision + 1)\n",
        "fixture.py",
    )
    missing = find_unpaired_age_updates(
        "def f():\n    stmt = update(ManagedProfileModel).values(age_months=61)\n",
        "fixture.py",
    )
    constant = find_unpaired_age_updates(
        "def f():\n    stmt = update(ManagedProfileModel).values(age_months=61, age_revision=2)\n",
        "fixture.py",
    )
    assert missing == {("f", 2)}
    assert constant == {("f", 2)}


# --------------------------------------------------------------------------- meta tests
_WRITE_SHAPES: tuple[tuple[str, str, str], ...] = (
    (
        "a1_constructor_keyword",
        "def f():\n    return ManagedProfileModel(child_id='c', age_months=60)\n",
        "constructor",
    ),
    (
        "a2_constructor_via_module",
        "def f(models):\n    return models.ManagedProfileModel(age_months=60)\n",
        "constructor",
    ),
    (
        "a3_constructor_via_import_alias",
        "from x import ManagedProfileModel as P\n\ndef f():\n    return P(age_months=60)\n",
        "constructor",
    ),
    (
        "b_constructor_kwargs",
        "def f(kwargs):\n    return ManagedProfileModel(**kwargs)\n",
        "constructor",
    ),
    ("c1_attribute_assign", "def f(p):\n    p.age_months = 61\n", "attribute"),
    ("c2_attribute_augassign", "def f(p):\n    p.age_months += 1\n", "attribute"),
    ("c3_attribute_annotated", "def f(p):\n    p.age_months: int = 61\n", "attribute"),
    ("c4_attribute_tuple_target", "def f(p, q):\n    p.age_months, q = 1, 2\n", "attribute"),
    ("c5_age_revision_assign", "def f(p):\n    p.age_revision = 2\n", "attribute"),
    ("c6_age_source_assign", "def f(p):\n    p.age_source = 'SYNTHETIC_FIXTURE'\n", "attribute"),
    (
        "d1_update_values_keyword",
        "def f(db):\n    db.execute(update(ManagedProfileModel).values(age_months=61))\n",
        "values",
    ),
    (
        "d2_update_values_dict",
        "def f(db):\n    db.execute(update(Other).values({'age_months': 61}))\n",
        "values",
    ),
    (
        "d3_update_statement_target_only",
        "def f(db, data):\n    db.execute(update(ManagedProfileModel).values(**data))\n",
        "statement",
    ),
    (
        "d4_query_update",
        "def f(db):\n    db.query(ManagedProfileModel).update({'x': 1})\n",
        "statement",
    ),
    ("e_setattr", "def f(p):\n    setattr(p, 'age_months', 61)\n", "setattr"),
    (
        "e_setattr_age_source",
        "def f(p):\n    setattr(p, 'age_source', 'ADULT_DECLARED')\n",
        "setattr",
    ),
    (
        "f1_raw_sql_update",
        "def f(db):\n    db.execute(text('UPDATE be1_managed_profiles SET x = 1'))\n",
        "raw_sql",
    ),
    (
        "f2_raw_sql_insert_age",
        "def f(db):\n    db.execute(text('insert into t (age_months) values (1)'))\n",
        "raw_sql",
    ),
    (
        "f3_raw_sql_update_age",
        "SQL = 'UPDATE people SET age_months = 5'\n",
        "raw_sql",
    ),
    (
        "g1_table_update",
        "def f(db):\n    db.execute(ManagedProfileModel.__table__.update().values(x=1))\n",
        "statement",
    ),
    (
        "g2_table_insert_via_alias",
        "def f(db):\n    t = ManagedProfileModel.__table__\n    db.execute(t.insert())\n",
        "statement",
    ),
    (
        "g3_metadata_table_update",
        "def f(db, meta):\n    db.execute(meta.tables['be1_managed_profiles'].update())\n",
        "statement",
    ),
    (
        "bulk_insert_mappings",
        "def f(db):\n    db.bulk_insert_mappings(ManagedProfileModel, [])\n",
        "bulk",
    ),
)


@pytest.mark.parametrize(
    ("shape", "source", "kind"), _WRITE_SHAPES, ids=[item[0] for item in _WRITE_SHAPES]
)
def test_detector_reports_every_age_write_shape(shape: str, source: str, kind: str) -> None:
    del shape
    found = find_age_write_paths(source, "sketch2life/probe.py")

    assert any(item[0] == "sketch2life/probe.py" and item[2] == kind for item in found), found


_SAFE_SHAPES: tuple[tuple[str, str], ...] = (
    ("select_by_model", "def f(db):\n    return db.scalar(select(ManagedProfileModel))\n"),
    ("read_age_attribute", "def f(p):\n    return p.age_months\n"),
    (
        "constructor_without_age",
        "def f():\n    return ManagedProfileModel(child_id='c', display_name='n')\n",
    ),
    ("response_dict", "def f(row):\n    return {'age_months': row.age_months}\n"),
    ("other_table_update", "def f(db):\n    db.execute(update(Other).values(state='x'))\n"),
    (
        "select_sql_text",
        "def f(db):\n    db.execute(text('SELECT age_months FROM be1_managed_profiles'))\n",
    ),
    ("docstring_only", 'def f():\n    """Never UPDATE age_months here."""\n'),
)


@pytest.mark.parametrize(("name", "source"), _SAFE_SHAPES, ids=[item[0] for item in _SAFE_SHAPES])
def test_detector_ignores_reads_and_unrelated_statements(name: str, source: str) -> None:
    del name
    assert find_age_write_paths(source, "sketch2life/probe.py") == set()


def test_detector_attributes_a_write_to_its_enclosing_function() -> None:
    source = "def outer():\n    def inner(p):\n        p.age_months = 1\n"

    assert find_age_write_paths(source, "sketch2life/probe.py") == {
        ("sketch2life/probe.py", "inner", "attribute")
    }


def test_allowlist_check_fails_with_a_clear_message_for_a_new_write_path() -> None:
    allowed = frozenset({("sketch2life/a.py", "create", "constructor")})
    findings = {
        ("sketch2life/a.py", "create", "constructor"),
        ("sketch2life/b.py", "rename_profile", "values"),
    }

    with pytest.raises(AssertionError, match=r"b\.py::rename_profile \(values\)") as caught:
        check_against_allowlist(findings, allowed)

    assert "ALLOWED_CREATION_PATHS" in str(caught.value)


def test_allowlist_check_fails_when_an_allowed_function_gains_another_write_kind() -> None:
    allowed = frozenset({("sketch2life/a.py", "create", "constructor")})
    findings = {
        ("sketch2life/a.py", "create", "constructor"),
        ("sketch2life/a.py", "create", "attribute"),
    }

    with pytest.raises(AssertionError, match=r"create \(attribute\)"):
        check_against_allowlist(findings, allowed)


def test_allowlist_check_fails_when_an_allowed_creation_path_disappears() -> None:
    allowed = frozenset({("sketch2life/a.py", "create", "constructor")})

    with pytest.raises(AssertionError, match="no longer found"):
        check_against_allowlist(set(), allowed)


def test_allowlist_names_exactly_the_two_creation_functions() -> None:
    assert {(path, function) for path, function, _ in ALLOWED_CREATION_PATHS} == {
        ("sketch2life/interfaces/http/routers/be1_registry.py", "create_profile"),
        ("sketch2life/infrastructure/persistence/core_store.py", "create_synthetic_profile"),
    }
    assert {kind for _, _, kind in ALLOWED_CREATION_PATHS} == {"constructor"}
