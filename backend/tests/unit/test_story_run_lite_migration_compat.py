from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sketch2life.infrastructure.story_run_lite import migration_compat as compat


def _connection() -> Mock:
    conn = Mock()
    conn.dialect = SimpleNamespace(name="postgresql")
    conn.execute.return_value.scalars.return_value = ["20261102_story_run_lite"]
    return conn


def test_relocates_only_verified_legacy_and_verifies_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = _connection()
    monkeypatch.setattr(compat, "_present", lambda _c, name: name in compat._OLD_NAMES)
    monkeypatch.setattr(compat, "_schema_snapshot", lambda _c, *, legacy: {"old": [[legacy]]})
    monkeypatch.setattr(compat, "_LEGACY_SIGNATURE", compat._signature({"old": [[True]]}))
    monkeypatch.setattr(compat, "_CURRENT_SIGNATURE", compat._signature({"old": [[False]]}))
    compat.relocate_story_upload_tables(conn, required=True)
    statements = [str(call.args[0]) for call in conn.execute.call_args_list]
    assert len(statements) == 8  # relation lock, version lookup and six transactional renames
    assert "ACCESS EXCLUSIVE MODE NOWAIT" in statements[0]
    assert "RENAME TO storyrun_upload_sessions" in statements[2]
    assert "RENAME CONSTRAINT core_upload_parts_pkey" in statements[5]
    assert "RENAME TO ix_storyrun_upload_owner_state" in statements[6]


def test_unknown_legacy_layout_fails_before_rename(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = _connection()
    monkeypatch.setattr(compat, "_present", lambda _c, name: name in compat._OLD_NAMES)
    monkeypatch.setattr(compat, "_schema_snapshot", lambda _c, *, legacy: {"unknown": []})
    with pytest.raises(RuntimeError, match="schema or dependencies"):
        compat.relocate_story_upload_tables(conn, required=True)
    assert conn.execute.call_count == 2  # only relation lock and revision lookup


def test_extra_dependency_changes_signature() -> None:
    verified = {"dependencies": [["core_upload_sessions", 0, "n", "known FK"]]}
    altered = {
        "dependencies": [*verified["dependencies"], ["core_upload_sessions", 0, "n", "view"]]
    }
    assert compat._signature(verified) != compat._signature(altered)


def test_legacy_table_without_applied_revision_is_not_relocated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = _connection()
    conn.execute.return_value.scalars.return_value = ["20261028_ll_0001"]
    monkeypatch.setattr(compat, "_present", lambda _c, name: name in compat._OLD_NAMES)
    with pytest.raises(RuntimeError, match="not an applied legacy"):
        compat.relocate_story_upload_tables(conn, required=True)
    assert conn.execute.call_count == 2


def test_unknown_destination_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = _connection()
    monkeypatch.setattr(compat, "_present", lambda _c, name: name in compat._NEW_NAMES)
    monkeypatch.setattr(compat, "_schema_snapshot", lambda _c, *, legacy: {"unexpected": []})
    with pytest.raises(RuntimeError, match="destination schema or dependencies"):
        compat.relocate_story_upload_tables(conn, required=True)
    assert conn.execute.call_count == 1  # only the lock


def test_failed_post_rename_verification_raises_for_transaction_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = _connection()
    monkeypatch.setattr(compat, "_present", lambda _c, name: name in compat._OLD_NAMES)
    monkeypatch.setattr(compat, "_schema_snapshot", lambda _c, *, legacy: {"old": [[legacy]]})
    monkeypatch.setattr(compat, "_LEGACY_SIGNATURE", compat._signature({"old": [[True]]}))
    monkeypatch.setattr(compat, "_CURRENT_SIGNATURE", "different")
    with pytest.raises(RuntimeError, match="failed verification"):
        compat.relocate_story_upload_tables(conn, required=True)
    assert conn.execute.call_count == 8


@pytest.mark.parametrize("name", [compat._OLD_NAMES[0], compat._NEW_NAMES[0]])
def test_incomplete_layout_is_rejected_before_sql(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    conn = _connection()
    monkeypatch.setattr(compat, "_present", lambda _c, candidate: candidate == name)
    with pytest.raises(RuntimeError, match="incomplete"):
        compat.relocate_story_upload_tables(conn, required=True)
    conn.execute.assert_not_called()


def test_fresh_lesson_database_permits_creation_but_story_requires_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = _connection()
    monkeypatch.setattr(compat, "_present", lambda _c, _name: False)
    compat.prepare_lesson_upload_tables(conn)
    with pytest.raises(RuntimeError, match="missing"):
        compat.relocate_story_upload_tables(conn, required=True)
    conn.execute.assert_not_called()
