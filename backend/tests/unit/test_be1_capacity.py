"""Unit coverage for BE1 capacity request contracts and due-downgrade counting."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from sketch2life.contracts.schemas.be1_capacity import (
    Be1CapacityConfigureRequest,
    Be1OrganizationCapacityV1,
)
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.be1.capacity_adapter import (
    Be1CapacityAdapter,
    effective_active_class_count,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.billing_models import (
    BillingReceiptModel,
)


class _AdapterSessionStub:
    def __init__(self, scalar_results=()) -> None:
        self.scalar_results = iter(scalar_results)
        self.statements = []
        self.added = []
        self.flush_count = 0
        self.commit_count = 0
        self.execute_count = 0

    def scalar(self, statement):
        self.statements.append(statement)
        return next(self.scalar_results)

    def scalars(self, _statement):
        return []

    def execute(self, *_args, **_kwargs):
        self.execute_count += 1
        return None

    def get(self, model, key):
        if model is BillingReceiptModel:
            return next(
                (
                    receipt
                    for receipt in self.added
                    if (receipt.actor_ref, receipt.operation, receipt.key) == key
                ),
                None,
            )
        return None

    def add(self, record) -> None:
        self.added.append(record)

    def flush(self) -> None:
        self.flush_count += 1

    def commit(self) -> None:
        self.commit_count += 1


def _settings(*, env: str, billing_sandbox_enabled: bool) -> Settings:
    return Settings.model_construct(
        env=env,
        billing_sandbox_enabled=billing_sandbox_enabled,
    )


def test_manager_capacity_request_accepts_only_supported_actions_and_fields() -> None:
    assert Be1CapacityConfigureRequest(action="cancel_renewal").action == "cancel_renewal"
    assert Be1CapacityConfigureRequest(action="resume_renewal").action == "resume_renewal"
    downgrade = Be1CapacityConfigureRequest(
        action="downgrade", addon_slots=0, suspend_class_refs=["class-1"]
    )
    assert downgrade.addon_slots == 0

    with pytest.raises(ValidationError):
        Be1CapacityConfigureRequest(action="downgrade")
    with pytest.raises(ValidationError):
        Be1CapacityConfigureRequest(action="renew")
    with pytest.raises(ValidationError):
        Be1CapacityConfigureRequest(action="cancel_renewal", price_id="price-1")
    with pytest.raises(ValidationError):
        Be1CapacityConfigureRequest(action="resume_renewal", addon_slots=2)


def test_due_downgrade_counts_only_active_refs_selected_by_billing() -> None:
    assert effective_active_class_count(
        {"active-1", "active-2", "active-3"}, {"active-2", "foreign", "archived"}
    ) == 2
    assert effective_active_class_count(set(), {"scheduled-1"}) == 0


def test_capacity_response_contains_effective_values_without_price_configuration() -> None:
    view = Be1OrganizationCapacityV1(
        organization_id="org-1",
        subscription_id="sub-1",
        capacity=10,
        active_class_count=8,
        available_slots=2,
        subscription_state="ACTIVE",
        revision=4,
        period_start="2026-11-01T00:00:00+00:00",
        period_end="2026-12-01T00:00:00+00:00",
    )
    assert view.contract == "Be1OrganizationCapacityV1"
    assert "price_id" not in view.model_dump()


def test_missing_subscription_uses_included_slots_and_locks_organization_for_create() -> None:
    organization = SimpleNamespace(organization_id="org-1")
    db = _AdapterSessionStub([None, organization])
    adapter = Be1CapacityAdapter(
        db, "manager-1", _settings(env="production", billing_sandbox_enabled=False)
    )

    row, view = adapter.view_for_organization("org-1", lock=True)

    assert row is None
    assert view["capacity"] == 10
    assert view["addon_slots"] == 0
    assert view["revision"] == 0
    assert view["suspended_class_refs"] == []
    lock_sql = str(db.statements[1].compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in lock_sql


def test_existing_subscription_read_uses_billing_capacity_view_without_sandbox_gate() -> None:
    now = datetime(2026, 11, 25, tzinfo=UTC)
    row = SimpleNamespace(
        subscription_id="sub-1",
        organization_ref="org-1",
        price_id="private-price-ref",
        addon_slots=3,
        state="ACTIVE",
        revision=7,
        period_start=now,
        period_end=now + timedelta(days=30),
    )
    db = _AdapterSessionStub([row, None])
    adapter = Be1CapacityAdapter(
        db,
        "manager-1",
        _settings(env="production", billing_sandbox_enabled=False),
        clock=lambda: now,
    )

    returned_row, view = adapter.view_for_organization("org-1", lock=False)

    assert returned_row is row
    assert view["capacity"] == 13
    assert view["revision"] == 7
    assert view["period_end"] == row.period_end.isoformat()


def test_adapter_billing_command_matches_billing_receipt_contract_and_defers_commit() -> None:
    db = _AdapterSessionStub()
    adapter = Be1CapacityAdapter(
        db, "manager-1", _settings(env="test", billing_sandbox_enabled=True)
    )
    billing = adapter._command_service()
    payload = {"action": "cancel_renewal", "revision": 3}
    expected_result = {"subscription_id": "sub-1", "revision": 4}
    execute_count = 0

    def execute():
        nonlocal execute_count
        execute_count += 1
        return expected_result

    first = billing.command("subscription.configure:sub-1", "same-key", payload, execute)
    replay = billing.command("subscription.configure:sub-1", "same-key", payload, execute)
    receipt = db.added[0]
    expected_fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    assert first == expected_result
    assert replay == expected_result
    assert execute_count == 1
    assert len(db.added) == 1
    assert isinstance(receipt, BillingReceiptModel)
    assert (receipt.actor_ref, receipt.operation, receipt.key) == (
        "manager-1",
        "subscription.configure:sub-1",
        "same-key",
    )
    assert receipt.fingerprint == expected_fingerprint
    assert receipt.response_json == expected_result
    assert db.flush_count == 1
    assert db.commit_count == 0

    with pytest.raises(AdminError, match="INVALID_IDEMPOTENCY_KEY"):
        billing.command(
            "subscription.configure:sub-1",
            "same-key",
            {"action": "resume_renewal", "revision": 3},
            execute,
        )
