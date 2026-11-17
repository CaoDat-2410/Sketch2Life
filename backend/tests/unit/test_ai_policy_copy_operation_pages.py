"""Offline SQL query/validation shape; not actual database/owner authorization proof."""

import pytest
from sqlalchemy.dialects.postgresql import dialect

from sketch2life.application.ports.ai_policy_copy_registry import CopyOperationPage
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
)


def transaction(keys=(), *, exists=True):
    queries = []

    class Result:
        def scalars(self):
            return iter(keys)

    class Connection:
        def execute(self, statement):
            queries.append(statement)
            return Result()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.exists, tx.revision = Connection(), exists, 7 if exists else 0
    tx.organization_id, tx.scope_ref = "school", "scope"
    return tx, queries


def test_scoped_ordered_page_has_extra_row_and_revision_bound_continuation():
    tx, queries = transaction(("b" * 64, "c" * 64, "d" * 64))
    assert tx.operation_page(limit=2, after="a" * 64, expected_revision=7) == CopyOperationPage(
        7, ("b" * 64, "c" * 64), "c" * 64
    )
    query = queries[0].compile(dialect=dialect())
    assert "organization_id" in str(query) and "scope_ref" in str(query)
    assert "ORDER BY" in str(query) and "LIMIT" in str(query)
    assert set(query.params.values()) == {"school", "scope", "a" * 64, 3}


def test_missing_scope_does_not_query_after_absence_observation():
    tx, queries = transaction(("b" * 64,), exists=False)
    assert tx.operation_page(limit=2) == CopyOperationPage(0, (), None)
    assert not queries


@pytest.mark.parametrize("keys", [(), ("b" * 64,), ("b" * 64, "c" * 64)])
def test_final_page_has_no_continuation(keys):
    tx, _ = transaction(keys)
    assert tx.operation_page(limit=2) == CopyOperationPage(7, keys, None)


@pytest.mark.parametrize(
    "options",
    [
        {"limit": True},
        {"limit": 0},
        {"limit": 257},
        {"after": "a" * 64},
        {"after": "not-a-digest", "expected_revision": 7},
        {"after": "A" * 64, "expected_revision": 7},
        {"expected_revision": True},
        {"expected_revision": -1},
        {"expected_revision": 6},
    ],
)
def test_invalid_or_stale_pages_fail_before_database(options):
    tx, queries = transaction()
    with pytest.raises(PolicyError):
        tx.operation_page(**(dict(limit=2) | options))
    assert not queries


@pytest.mark.parametrize(
    "keys",
    [
        ("bad",),
        (True,),
        ("c" * 64, "b" * 64),
        ("b" * 64, "b" * 64),
        ("a" * 64,),
    ],
)
def test_malformed_duplicate_or_out_of_order_storage_keys_fail_closed(keys):
    tx, _ = transaction(keys)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION_STORAGE"):
        tx.operation_page(limit=2, after="a" * 64, expected_revision=7)
