"""Pilot-only durable methods on the owner-provided disposable PostgreSQL database."""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine, delete, inspect
from sqlalchemy.engine import make_url

from sketch2life.application.ports.assistance import (
    AssistanceEvent,
    AssistanceRevisionConflict,
    AssistanceUniqueConflict,
    CommandReceipt,
    ReceiptKey,
    ReceiptOutcome,
)
from sketch2life.application.ports.vision_analysis import AnalysisRevisionConflict
from sketch2life.domain.assistance import AssistanceRequest
from sketch2life.infrastructure.assistance.harness import build_assistance_harness
from sketch2life.infrastructure.assistance.sql_repository import SqlAssistanceRepository
from sketch2life.infrastructure.vision_analysis import tables
from sketch2life.infrastructure.vision_analysis.harness import build_analysis_harness
from sketch2life.infrastructure.vision_analysis.ledger import InvocationLedger
from sketch2life.infrastructure.vision_analysis.repository import SqlAnalysisRepository


def _loopback(host: str | None) -> bool:
    if host == "localhost":
        return True
    try:
        return bool(host and ipaddress.ip_address(host).is_loopback)
    except ValueError:
        return False


@pytest.fixture
def database() -> Iterator[tuple[Engine, str]]:
    raw = os.environ.get("BE1_TEST_DATABASE_URL")
    if not raw:
        pytest.skip("BE1_TEST_DATABASE_URL is required for this PostgreSQL test")
    url = make_url(raw)
    assert url.database and "be1_acceptance" in url.database and _loopback(url.host)
    assert "service" not in url.query
    for key in ("host", "hostaddr"):
        values = url.query.get(key, ())
        values = values if isinstance(values, tuple) else (values,)
        assert all(_loopback(value) for value in values)
    engine = create_engine(url)
    assert inspect(engine).has_table("invocation", schema=tables.SCHEMA), "pilot migration required"
    org = "synthetic-pilot-" + uuid4().hex
    try:
        yield engine, org
    finally:
        # Provider results/observations precede heads; receipts/events precede requests.
        with engine.begin() as connection:
            for table in reversed(tables.METADATA.sorted_tables):
                connection.execute(delete(table).where(table.c.organization_id == org))
        engine.dispose()


def _request(org: str) -> AssistanceRequest:
    value = build_assistance_harness().submit().request
    return replace(
        value,
        assistance_id="synthetic-" + uuid4().hex,
        facts=replace(value.facts, organization_id=org),
    )


def test_assistance_methods_are_durable_atomic_and_scoped(database: tuple[Engine, str]) -> None:
    engine, org = database
    repo = SqlAssistanceRepository(engine, org)
    request = _request(org)
    receipt = CommandReceipt(
        ReceiptKey(org, "synthetic-actor", "create", request.assistance_id, "synthetic-key"),
        "a" * 64,
        ReceiptOutcome.CREATED,
        request,
        datetime.now(UTC),
    )
    event = AssistanceEvent(
        "synthetic-event", "pilot.requested", org, request.assistance_id, 1, None, datetime.now(UTC)
    )
    with repo.transaction() as tx:
        assert tx.decision_epoch(org) == (0, 0)
        tx.insert(request)
        tx.put_receipt(receipt)
        tx.add_event(event)
        tx.record_notice("synthetic-notice")
        tx.publish_request_fence(org)
    # A separately constructed repository must see the committed state.
    with SqlAssistanceRepository(engine, org).transaction() as tx:
        assert tx.get(request.assistance_id) == request
        assert tx.find_active_semantic(org, request.semantic_identity) == request.assistance_id
        assert tx.active_by_operation_target(org, request.operation_target) == (request,)
        assert tx.get_receipt(receipt.key) == receipt
        assert tx.notice_seen("synthetic-notice")
        assert tx.list_requests(org) == (request,)
        assert tx.latest_counted(org, request.debounce_key) == request.created_at
        assert tx.count_reserved(org, request.facts.session_id, request.facts.target.key()) == 1
        assert tx.decision_epoch(org) == (1, 0)
    with SqlAssistanceRepository(engine, "synthetic-other").transaction() as tx:
        assert tx.get(request.assistance_id) is None
        assert tx.list_requests("synthetic-other") == ()
    with pytest.raises(RuntimeError, match="rollback"), repo.transaction() as tx:
        tx.cas(
            expected_record_version=request.record_version,
            request=replace(request, record_version=request.record_version + 1),
        )
        tx.publish_request_fence(org)
        raise RuntimeError("rollback")
    with repo.transaction() as tx:
        assert tx.get(request.assistance_id) == request
        assert tx.decision_epoch(org) == (1, 0)
    with repo.transaction() as tx:
        tx.cas(
            expected_record_version=request.record_version,
            request=replace(request, record_version=request.record_version + 1),
        )
    with pytest.raises(AssistanceRevisionConflict), repo.transaction() as tx:
        tx.cas(expected_record_version=request.record_version, request=request)


def test_semantic_uniqueness_blocks_racing_requests(database: tuple[Engine, str]) -> None:
    engine, org = database
    original = _request(org)

    def insert_once(index: int) -> bool:
        value = replace(original, assistance_id=f"synthetic-race-{index}")
        try:
            with SqlAssistanceRepository(engine, org).transaction() as tx:
                tx.insert(value)
            return True
        except AssistanceUniqueConflict:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(insert_once, range(2))) == 1


def test_analysis_methods_commit_and_rollback_together(database: tuple[Engine, str]) -> None:
    engine, org = database
    harness = build_analysis_harness()
    identifier = harness.accepted_analysis()
    state = harness.store.snapshot()
    original = state.heads[identifier]
    head = replace(
        original,
        scope=replace(original.scope, organization_id=org),
        lineage=replace(
            original.lineage,
            job_id="synthetic-" + uuid4().hex,
            job_attempt_id="synthetic-" + uuid4().hex,
        ),
    )
    observation = replace(state.observations[identifier], organization_id=org)
    result = replace(next(iter(state.provider_results.values())), organization_id=org)
    repo = SqlAnalysisRepository(engine, org)
    with pytest.raises(RuntimeError, match="rollback"), repo.transaction() as tx:
        tx.insert_head(head)
        tx.insert_observation(observation)
        tx.insert_provider_result(result)
        raise RuntimeError("rollback")
    with repo.transaction() as tx:
        assert tx.get_head(identifier) is None
    with repo.transaction() as tx:
        tx.insert_head(head)
        tx.insert_observation(observation)
        tx.insert_provider_result(result)
    with SqlAnalysisRepository(engine, org).transaction() as tx:
        assert tx.get_head(identifier) == head
        assert tx.find_by_attempt(head.lineage.job_id, head.lineage.job_attempt_id) == identifier
        assert tx.get_observation(identifier) == observation
        assert tx.get_provider_result(result.result_ref) == result
        tx.cas_head(expected_revision=1, head=replace(head, analysis_revision=2))
    with pytest.raises(AnalysisRevisionConflict), repo.transaction() as tx:
        tx.cas_head(expected_revision=1, head=replace(head, analysis_revision=2))
    with SqlAnalysisRepository(engine, "synthetic-other").transaction() as tx:
        assert tx.get_head(identifier) is None
        assert tx.get_observation(identifier) is None
        assert tx.get_provider_result(result.result_ref) is None
    with SqlAssistanceRepository(engine, org).transaction() as tx:
        assert tx.decision_epoch(org) == (0, 2)


def test_ledger_is_single_use_across_restart_and_identity_mismatch(
    database: tuple[Engine, str],
) -> None:
    engine, org = database
    identity = dict(
        run_id="synthetic-" + uuid4().hex,
        job_id="synthetic-" + uuid4().hex,
        attempt_id="synthetic-" + uuid4().hex,
        organization_id=org,
    )
    ledger = InvocationLedger(engine)
    assert ledger.claim(**identity)
    assert not InvocationLedger(engine).claim(**identity)
    assert not ledger.claim(**{**identity, "run_id": "synthetic-" + uuid4().hex})
    assert not ledger.mark_sent(**{**identity, "organization_id": "synthetic-other"})
    assert ledger.mark_sent(**identity)
    assert not InvocationLedger(engine).mark_sent(**identity)
    assert ledger.complete(**identity, state="UNKNOWN")
    assert not ledger.complete(**identity, state="SUCCEEDED", result_sha256="a" * 64)
    row = InvocationLedger(engine).get(identity["run_id"])
    assert row is not None and row.state == "UNKNOWN" and row.finished_at is not None


def test_ledger_claim_race_has_one_winner(database: tuple[Engine, str]) -> None:
    engine, org = database
    identity = dict(
        run_id="synthetic-" + uuid4().hex,
        job_id="synthetic-" + uuid4().hex,
        attempt_id="synthetic-" + uuid4().hex,
        organization_id=org,
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _: InvocationLedger(engine).claim(**identity), range(2))) == 1
