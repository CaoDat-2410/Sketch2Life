"""Safe metadata query with MEMORY/ASSUMED guards and read-only SQL shape."""

from contextlib import contextmanager
from dataclasses import asdict, replace

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.sql.selectable import Select

from sketch2life.application.ai_policy_operations import AiPolicyOperations
from sketch2life.contracts.schemas.ai_policy_operations import (
    BudgetWindowRef,
    LedgerOperationsSnapshot,
    PolicyOperationsRequest,
    PolicyOperationsView,
    PolicyScopeMetadata,
)
from sketch2life.domain.ai_policy.accounting import BudgetKey, DefinitionKey
from sketch2life.domain.ai_policy.model import Capability, PolicyError
from sketch2life.infrastructure.ai_policy.operations_sql import SqlResourceOperationsReader
from tests.ai_policy_fixtures import execute, harness, published

REQUEST = PolicyOperationsRequest(feature_scope="fixture.feature")
WINDOW = BudgetWindowRef.model_validate(
    dict(
        definition=dict(ref="fixture-budget", version=1, hash="a" * 64),
        unit="fixture-unit",
        window_id="fixture-window",
    )
)
WITH_WINDOW = REQUEST.model_copy(update={"budget_window": WINDOW})
KEY = BudgetKey(
    "school",
    "fixture.feature",
    DefinitionKey("fixture-budget", 1, "a" * 64),
    "fixture-unit",
    "fixture-window",
)


def operations(ledger=None):
    commands, boundary, store = harness()
    boundary.rights["monitor"] = {Capability.OPERATIONS_READ}
    return AiPolicyOperations(store, boundary, ledger), commands, boundary, store


def test_empty_projection_unknown_is_not_zero_and_never_creates_scope():
    service, _, _, store = operations()
    view = service.read("monitor", "school", WITH_WINDOW)
    assert view.scope is None and view.actual_cost is None
    assert view.ledger.occupied_slots is None and not view.ledger.bucket_available
    assert view.ledger.recorded_held_units is view.ledger.recorded_spent_units is None
    assert not store.scopes and not store.events and not store.receipts


def test_exact_pin_and_stopped_metadata_redacted_even_if_registry_withdrawn():
    service, commands, boundary, store = operations()
    record = published(commands, store).record
    view = service.read("monitor", "school", REQUEST)
    assert view.scope.policy_ref.ref == record.record_id and not view.scope.disabled
    assert view.scope.policy_state == "published" and view.scope.epoch == 1
    execute(commands, "operator", "recall", "retire", record, reason="synthetic-private-reason")
    boundary.feature = False
    result = service.read("monitor", "school", REQUEST)
    assert result.scope.disabled and result.scope.policy_state == "recalled"
    assert result.scope.epoch == 2 and boundary.feature_calls >= 1
    payload = result.model_dump(mode="json")
    assert set(payload) == {
        "contract_version",
        "organization_id",
        "request",
        "scope",
        "ledger",
        "accounting_semantics",
        "actual_cost",
    }
    encoded = result.model_dump_json()
    for private in (
        "authored_by",
        "created_at",
        "title",
        "reason",
        "review",
        "model_profile",
        "prompt",
        "media",
        "token",
        "synthetic-private-reason",
    ):
        assert private not in encoded


@pytest.mark.parametrize(
    "principal,org", [("author", "school"), ("unknown", "school"), ("monitor", "other")]
)
def test_denial_before_storage(principal, org, monkeypatch):
    service, _, _, store = operations()

    def forbidden_read(*args, **kwargs):
        pytest.fail("unauthorized storage access")

    monkeypatch.setattr(store, "transaction", forbidden_read)
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.read(principal, org, REQUEST)


class Ledger:
    def __init__(self, value):
        self.value = value

    def snapshot(self, org, request):
        return self.value


def test_actual_zero_remains_available_recorded_zero_not_actual_cost():
    result = LedgerOperationsSnapshot(
        organization_id="school",
        request=WITH_WINDOW,
        occupied_slots=0,
        bucket_available=True,
        recorded_held_units=0,
        recorded_spent_units=0,
    )
    service, _, _, _ = operations(Ledger(result))
    view = service.read("monitor", "school", WITH_WINDOW)
    assert view.ledger == result and view.actual_cost is None
    assert view.accounting_semantics == "recorded_ledger_not_actual_cost"


@pytest.mark.parametrize(
    "change",
    [
        {"organization_id": "other"},
        {"request": REQUEST},
        {"occupied_slots": True},
        {"bucket_available": 1},
        {"recorded_spent_units": -1},
    ],
)
def test_wrong_or_native_malformed_ledger_fails_closed(change):
    result = LedgerOperationsSnapshot(
        organization_id="school",
        request=WITH_WINDOW,
        occupied_slots=1,
        bucket_available=True,
        recorded_held_units=2,
        recorded_spent_units=3,
    )
    service, _, _, _ = operations(Ledger(result.model_copy(update=change)))
    with pytest.raises(PolicyError, match="AI_POLICY_OPERATIONS_UNAVAILABLE"):
        service.read("monitor", "school", WITH_WINDOW)


def test_final_authority_rechecked_after_ledger_read():
    service, _, boundary, _ = operations()

    class Revoke:
        def snapshot(self, org, request):
            boundary.authority = replace(boundary.authority, capabilities=frozenset())
            return LedgerOperationsSnapshot(organization_id=org, request=request)

    service.ledger = Revoke()
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.read("monitor", "school", REQUEST)


@pytest.mark.parametrize("error_type", [PolicyError, RuntimeError])
def test_private_reader_errors_do_not_escape_projection(error_type):
    class Broken:
        def snapshot(self, org, request):
            raise error_type("synthetic-private-provider-token")

    service, _, _, _ = operations(Broken())
    with pytest.raises(PolicyError, match="^AI_POLICY_OPERATIONS_UNAVAILABLE$"):
        service.read("monitor", "school", REQUEST)


@pytest.mark.parametrize(
    "change",
    [
        {"organization_id": "other"},
        {"feature_scope": "other"},
        {"epoch": True},
        {"disabled": 1},
        {"hash": "b" * 64},
        {"version": True},
    ],
)
def test_malformed_or_mismatched_scope_and_pin_fail_closed(change):
    service, commands, _, store = operations()
    published(commands, store)
    key = "school", "fixture.feature"
    store.scopes[key] = replace(store.scopes[key], **change)
    with pytest.raises(PolicyError):
        service.read("monitor", "school", REQUEST)


@pytest.mark.parametrize(
    "change",
    [
        {"bucket_available": True},
        {"recorded_spent_units": 0},
        {"occupied_slots": True},
    ],
)
def test_unknown_cannot_be_encoded_as_zero_or_partial_bucket(change):
    with pytest.raises(ValidationError):
        LedgerOperationsSnapshot(organization_id="school", request=REQUEST, **change)


@pytest.mark.parametrize(
    "change",
    [
        {"epoch": 0, "disabled": True},
        {"epoch": 1, "disabled": False},
        {"epoch": True, "disabled": False},
    ],
)
def test_scope_projection_invariants(change):
    with pytest.raises(ValidationError):
        PolicyScopeMetadata(**change)


def test_projection_cannot_encode_money_or_extra_private_fields():
    ledger = LedgerOperationsSnapshot(organization_id="school", request=REQUEST)
    for extra in ({"actual_cost": 0}, {"provider_url": "https://invalid.example/private"}):
        with pytest.raises(ValidationError):
            PolicyOperationsView(
                organization_id="school", request=REQUEST, scope=None, ledger=ledger, **extra
            )


class SqlFixture:
    def __init__(self, rows):
        self.rows, self.statements = list(rows), []

    @contextmanager
    def begin(self):
        yield self

    def execute(self, statement):
        assert isinstance(statement, Select), "operational read must not mutate"
        self.statements.append(statement)
        return self

    def mappings(self):
        return self

    def one_or_none(self):
        return self.rows.pop(0)


def test_sql_missing_scope_no_write_or_followup_phantom_bucket():
    fixture = SqlFixture([None])
    snapshot = SqlResourceOperationsReader(fixture).snapshot("school", WITH_WINDOW)
    assert snapshot.occupied_slots is None and len(fixture.statements) == 1
    assert "FOR SHARE" in str(fixture.statements[0].compile(dialect=dialect()))


def test_sql_exact_bucket_binding_read_only_and_stored_counters():
    fixture = SqlFixture(
        [
            dict(organization_id="school", feature_scope="fixture.feature", occupied_slots=2),
            dict(key=asdict(KEY), held_units=7, spent_units=3),
        ]
    )
    snapshot = SqlResourceOperationsReader(fixture).snapshot("school", WITH_WINDOW)
    assert (
        snapshot.occupied_slots,
        snapshot.recorded_held_units,
        snapshot.recorded_spent_units,
    ) == (2, 7, 3)
    assert snapshot.bucket_available
    for query in fixture.statements:
        encoded = str(query.compile(dialect=dialect()))
        assert (
            "organization_id =" in encoded
            and "feature_scope =" in encoded
            and "FOR SHARE" in encoded
        )


@pytest.mark.parametrize(
    "change",
    [
        {"key": asdict(replace(KEY, window_id="other"))},
        {"held_units": True},
        {"spent_units": -1},
        {
            "key": asdict(KEY)
            | {"definition": {"ref": "fixture-budget", "version": True, "hash": "a" * 64}}
        },
    ],
)
def test_sql_wrong_key_or_malformed_counter_fails_closed(change):
    fixture = SqlFixture(
        [
            dict(organization_id="school", feature_scope="fixture.feature", occupied_slots=2),
            dict(key=asdict(KEY), held_units=7, spent_units=3) | change,
        ]
    )
    with pytest.raises(PolicyError):
        SqlResourceOperationsReader(fixture).snapshot("school", WITH_WINDOW)


def test_sql_private_failure_is_sanitized():
    class Broken:
        def begin(self):
            raise RuntimeError("synthetic-private-provider-token")

    with pytest.raises(PolicyError, match="^AI_POLICY_OPERATIONS_UNAVAILABLE$"):
        SqlResourceOperationsReader(Broken()).snapshot("school", REQUEST)
