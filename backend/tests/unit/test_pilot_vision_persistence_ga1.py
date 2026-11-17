"""Offline codec/schema and explicit fail-closed pilot method contracts."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import Mock

import pytest
from sqlalchemy import Connection

from sketch2life.application.ports.assistance import (
    AssistanceEvent,
    CommandReceipt,
    ReceiptKey,
    ReceiptOutcome,
)
from sketch2life.infrastructure.assistance.harness import build_assistance_harness
from sketch2life.infrastructure.assistance.sql_repository import SqlAssistanceUnitOfWork
from sketch2life.infrastructure.vision_analysis import tables
from sketch2life.infrastructure.vision_analysis.codec import from_payload, to_payload
from sketch2life.infrastructure.vision_analysis.repository import SqlAnalysisUnitOfWork


def test_fixed_codec_roundtrips_domain_records_and_nested_collections() -> None:
    event = AssistanceEvent(
        "event", "pilot.requested", "org", "request", 1, None, datetime(2026, 11, 1, tzinfo=UTC)
    )
    assert from_payload(to_payload(event), AssistanceEvent) == event
    assert from_payload(to_payload({"items": (frozenset({"a", "b"}),)}), dict) == {
        "items": (frozenset({"a", "b"}),)
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"$type": "untrusted.import.Class", "fields": {}},
        {"$type": "datetime", "value": "2026-01-01T00:00:00"},
        {"$type": "tuple", "items": [], "extra": True},
    ],
)
def test_codec_rejects_unknown_or_malformed_tags(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        from_payload(payload, dict)


def test_codec_refuses_nonfinite_values_and_unregistered_objects() -> None:
    for value in (float("nan"), float("inf"), object()):
        with pytest.raises(ValueError):
            to_payload(value)


def test_persistence_shape_has_full_ledger_and_semantic_uniqueness() -> None:
    assert len(tables.METADATA.tables) >= 9
    assert tables.SCHEMA == "pilot_vision"
    assert {
        "run_id",
        "job_id",
        "attempt_id",
        "state",
        "claimed_at",
        "sent_at",
        "finished_at",
        "result_sha256",
    } <= set(tables.invocations.c.keys())
    assert any(
        set(column.name for column in item.columns) == {"run_id"}
        for item in tables.invocations.constraints
        if hasattr(item, "columns")
    )
    assert any(
        set(column.name for column in item.columns) == {"job_id", "attempt_id"}
        for item in tables.invocations.constraints
        if hasattr(item, "columns")
    )
    assert any(index.unique for index in tables.requests.indexes)


def test_put_receipt_rejects_foreign_organization_snapshot_before_storage() -> None:
    request = build_assistance_harness().submit().request
    foreign_snapshot = replace(
        request,
        facts=replace(request.facts, organization_id="foreign-org"),
    )
    receipt = CommandReceipt(
        ReceiptKey("org", "synthetic-actor", "create", request.assistance_id, "synthetic-key"),
        "a" * 64,
        ReceiptOutcome.CREATED,
        foreign_snapshot,
        datetime.now(UTC),
    )
    connection = Mock(spec=Connection)
    connection.execute.side_effect = AssertionError("storage must not be called")
    unit = SqlAssistanceUnitOfWork(connection, "org")

    with pytest.raises(ValueError, match="organization scope mismatch"):
        unit.put_receipt(receipt)

    connection.execute.assert_not_called()


@pytest.mark.parametrize(
    ("kind", "method", "args"),
    [
        ("assistance", "find_cache", ("org", "identity")),
        ("assistance", "put_cache", ("org", "identity", None)),
        ("assistance", "add_sketch_intent", (None,)),
        ("analysis", "append_correction", (None,)),
        ("analysis", "get_correction", ("correction",)),
        ("analysis", "list_corrections", ("analysis",)),
        ("analysis", "get_receipt", (None,)),
        ("analysis", "put_receipt", (None,)),
        ("analysis", "add_invalidation", (None,)),
        ("analysis", "notice_seen", ("notice",)),
        ("analysis", "record_notice", ("notice",)),
    ],
)
def test_unselected_methods_raise_without_any_storage_call(
    kind: str, method: str, args: tuple[object, ...]
) -> None:
    connection = cast(Connection, object())
    unit: Any = (
        SqlAssistanceUnitOfWork(connection, "org")
        if kind == "assistance"
        else SqlAnalysisUnitOfWork(connection, "org")
    )
    with pytest.raises(NotImplementedError, match="outside.*pilot"):
        getattr(unit, method)(*args)
