"""Exact intent/auth/rollback invariants with assumed authority; no provider effects."""

import importlib.util
import re
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_operations import (
    validate_operation,
    validate_operation_authorization,
)
from sketch2life.application.ports.ai_policy_copy_registry import RegisteredProviderCopy
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationAuthorization
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import (
    COPY_OPERATION,
    COPY_OPERATION_AUTHORITY,
)
from tests.ai_policy_copy_operation_fixtures import command, schedule, setup
from tests.unit.test_ai_policy_domain import NOW


@pytest.mark.parametrize("action", ["cancel", "purge"])
def test_exact_intent_original_profile_and_authority_persist_without_provider_effect(action):
    service, authority, store = setup()
    envelope = schedule(service, operation=action)
    state = store.scopes["school", "scope"]
    assert state["operations"][envelope.operation_key] == envelope
    assert len(state["operation_authority"]) == 1
    assert state["purging"] == (action == "purge")
    assert _digest(envelope.binding()) == envelope.binding_digest
    assert _digest(envelope.key_binding()) == envelope.operation_key
    assert len(authority.calls) == 3 and len(authority.profile_calls) == 1
    assert authority.calls[-1][2] is True
    assert envelope.target.original_profile_ref == command().data_request_ref
    assert not hasattr(envelope, "deleted") and not hasattr(envelope, "acknowledged")


def test_replay_renews_authority_but_preserves_original_envelope_key_and_single_event():
    service, authority, store = setup()
    original = schedule(service)
    previous_revision = store.scopes["school", "scope"]["revision"]
    authority.changes = {"authority_revision": "new-owner-revision"}
    service.clock = lambda: NOW + timedelta(seconds=10)
    assert schedule(service) == original
    state = store.scopes["school", "scope"]
    assert len(state["operations"]) == 1 and state["revision"] == previous_revision
    assert len(state["operation_authority"]) == 2
    assert state["operation_authority"][-1].authority.authority_revision == "new-owner-revision"
    assert original.initial_authority.authority_revision == "fixture-owner"


@pytest.mark.parametrize(
    "change",
    [
        {"allowed": False},
        {"allowed": 1},
        {"organization_id": "other"},
        {"principal_id": "other"},
        {"command_digest": "f" * 64},
        {"expires_at": NOW},
    ],
)
def test_denied_malformed_or_expired_authority_does_not_read_original_copy(change):
    service, authority, store = setup()
    before = store.commits
    authority.changes = change
    with pytest.raises(PolicyError):
        schedule(service)
    assert store.commits == before and not authority.profile_calls
    assert not store.scopes["school", "scope"]["operations"]


@pytest.mark.parametrize(
    "change",
    [
        {"allowed": False},
        {"authority_revision": "revoked"},
        {"expires_at": NOW},
    ],
)
def test_changed_current_authority_rolls_back_intent_fence_event_and_history(change):
    service, authority, store = setup()
    authority.final_changes = change
    with pytest.raises(PolicyError):
        schedule(service)
    state = store.scopes["school", "scope"]
    assert state["revision"] == 1 and not state["purging"]
    assert not state["operations"] and not state["operation_authority"]


@pytest.mark.parametrize(
    "field,value", [("version", 2), ("hash", "f" * 64), ("ref", "new-profile")]
)
def test_original_profile_cannot_be_silently_replaced(field, value):
    service, authority, store = setup()
    authority.profile = authority.profile.model_copy(update={field: value})
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_PROFILE_MISMATCH"):
        schedule(service)
    assert not store.scopes["school", "scope"]["operations"]


def test_same_request_copy_action_key_with_different_data_request_binding_conflicts():
    service, _, store = setup()
    original = schedule(service)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_OPERATION_CONFLICT"):
        schedule(
            service, data_request_ref=command().data_request_ref.model_copy(update={"version": 2})
        )
    state = store.scopes["school", "scope"]
    assert state["operations"][original.operation_key] == original
    assert len(state["operation_authority"]) == 1


def test_cancel_and_purge_and_different_request_keys_do_not_alias():
    service, _, _ = setup()
    a = schedule(service, operation="cancel")
    b = schedule(service)
    c = schedule(service, client_request_id="another")
    assert len({a.operation_key, b.operation_key, c.operation_key}) == 3


def test_revoked_retry_cannot_reuse_stored_authority():
    service, authority, store = setup()
    schedule(service)
    authority.changes = {"allowed": False}
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        schedule(service)
    assert len(store.scopes["school", "scope"]["operation_authority"]) == 1


def test_profile_error_is_redacted_and_does_not_queue_intent():
    service, authority, store = setup()
    authority.fail_profile = True
    with pytest.raises(PolicyError, match="^AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE$"):
        schedule(service)
    assert not store.scopes["school", "scope"]["operations"]


def test_missing_copy_is_denied_after_current_authority_without_profile_lookup():
    service, authority, _ = setup()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_NOT_FOUND"):
        service.schedule("operator", "school", command(), "missing")
    assert len(authority.calls) == 1 and not authority.profile_calls


@pytest.mark.parametrize("field,value", [("operation", "delete"), ("client_request_id", True)])
def test_malformed_native_command_is_rejected_before_guard(field, value):
    service, authority, _ = setup()
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION"):
        service.schedule("operator", "school", command().model_copy(update={field: value}), "copy")
    assert not authority.calls


def test_commit_failure_rolls_back_new_intent_fence_and_observation():
    service, _, store = setup()
    # The first read succeeds; fail only the subsequent write transaction.
    original = store.enqueue_operation

    def failing(envelope, authorization):
        result = original(envelope, authorization)
        store.fail_commit = True
        return result

    store.enqueue_operation = failing
    with pytest.raises(PolicyError, match="SYNTHETIC_INVENTORY_COMMIT_FAILURE"):
        schedule(service)
    state = store.scopes["school", "scope"]
    assert state["revision"] == 1 and not state["purging"]
    assert not state["operations"] and not state["operation_authority"]


def test_original_registration_is_rechecked_after_external_profile_resolution():
    from sketch2life.application.ports.ai_policy_copy_registry import RegisteredProviderCopy

    service, authority, store = setup()
    original = authority.resolve_profile

    def changed(copy):
        result = original(copy)
        state = store.scopes["school", "scope"]
        item = state["rows"]["copy"]
        state["rows"]["copy"] = RegisteredProviderCopy(
            item.registration.model_copy(update={"kind": "output"}), False
        )
        return result

    authority.resolve_profile = changed
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRATION_CONFLICT"):
        schedule(service)
    assert not store.scopes["school", "scope"]["operations"]


def test_guard_exit_uncertainty_does_not_invent_rollback_or_new_operation_key():
    service, authority, store = setup()
    authority.fail_exit = True
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE"):
        schedule(service)
    state = store.scopes["school", "scope"]
    assert len(state["operations"]) == 1
    revision = state["revision"]
    authority.fail_exit = False
    schedule(service)
    assert store.scopes["school", "scope"]["revision"] == revision


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation_key", "f" * 64),
        ("binding_digest", "f" * 64),
        ("principal_id", "other"),
        ("created_at", NOW.replace(tzinfo=None)),
    ],
)
def test_native_envelope_tampering_fails_closed(field, value):
    service, _, _ = setup()
    original = schedule(service)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION"):
        validate_operation(original.model_copy(update={field: value}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("allowed", 1),
        ("principal_id", "other"),
        ("command_digest", "f" * 64),
        ("organization_id", "other"),
        ("expires_at", NOW),
    ],
)
def test_observation_rechecks_native_authority_and_exact_binding(field, value):
    service, _, _ = setup()
    envelope = schedule(service)
    observation = CopyOperationAuthorization.model_construct(
        operation_key=envelope.operation_key,
        observed_at=NOW,
        authority=envelope.initial_authority.model_copy(update={field: value}),
    )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION_AUTHORITY"):
        validate_operation_authorization(envelope, observation)


def test_forward_operation_migration_matches_exact_metadata_and_has_immutable_triggers(monkeypatch):
    path = (
        Path(__file__).resolve().parents[2] / "alembic/versions/20261018_ap_0006_copy_operations.py"
    )
    spec = importlib.util.spec_from_file_location("copy_operation_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def normalized(value):
        return re.sub(r"\s+", "", value)

    expected = (
        ";".join(
            str(CreateTable(t).compile(dialect=dialect())).strip()
            for t in (COPY_OPERATION, COPY_OPERATION_AUTHORITY)
        )
        + ";"
    )
    assert normalized(expected) == normalized(module.DDL)
    assert module.down_revision == "20261017_ap_0005"
    statements = []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, name, schema):
            statements.append((schema, name))

    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert sum("CREATE TRIGGER" in s and "BEFORE UPDATE OR DELETE" in s for s in statements) == 2
    module.downgrade()
    assert statements[-2:] == [
        ("ai_policy", "copy_operation_authority"),
        ("ai_policy", "copy_operation"),
    ]


@pytest.mark.parametrize("replay", [False, True])
def test_sql_enqueue_has_one_immutable_intent_but_fresh_authority_on_replay(replay):
    service, _, _ = setup()
    value = schedule(service)
    statements, events = [], []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.writable = Capture(), True
    tx.organization_id, tx.scope_ref, tx.principal_id = "school", "scope", "operator"
    tx.get = lambda copy_id: RegisteredProviderCopy(value.target, False)
    tx.get_operation = lambda key: value if replay else None
    tx.mark_purging = lambda: events.append("fence")
    tx._advance = lambda kind, detail: events.append(kind)
    proof = CopyOperationAuthorization(
        operation_key=value.operation_key, authority=value.initial_authority, observed_at=NOW
    )
    assert tx.enqueue_operation(value, proof) == value
    assert [s.table.name for s in statements] == (
        ["copy_operation_authority"] if replay else ["copy_operation", "copy_operation_authority"]
    )
    assert len(events) == (0 if replay else 2)


@pytest.mark.parametrize(
    "column,value",
    [
        ("organization_id", "other"),
        ("scope_ref", "other"),
        ("copy_id", "other"),
        ("operation_key", "f" * 64),
        ("envelope", {}),
    ],
)
def test_sql_recovery_rejects_stored_binding_substitution(column, value):
    service, _, _ = setup()
    envelope = schedule(service)
    row = dict(
        organization_id="school",
        scope_ref="scope",
        copy_id="copy",
        operation_key=envelope.operation_key,
        envelope=envelope.model_dump(mode="json"),
    )

    class Rows:
        def mappings(self):
            return self

        def one_or_none(self):
            return row | {column: value}

    class Connection:
        def execute(self, statement):
            return Rows()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.exists = Connection(), True
    tx.organization_id, tx.scope_ref = "school", "scope"
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION_STORAGE"):
        tx.get_operation(envelope.operation_key)


def test_sql_recovery_roundtrips_original_envelope_after_authority_deadline():
    service, _, _ = setup()
    envelope = schedule(service)

    class Rows:
        def mappings(self):
            return self

        def one_or_none(self):
            return dict(
                organization_id="school",
                scope_ref="scope",
                copy_id="copy",
                operation_key=envelope.operation_key,
                envelope=envelope.model_dump(mode="json"),
            )

    class Connection:
        def execute(self, statement):
            return Rows()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.exists = Connection(), True
    tx.organization_id, tx.scope_ref = "school", "scope"
    tx.clock = lambda: NOW + timedelta(days=1)
    assert (
        tx.get_operation(envelope.operation_key) == envelope
    )  # History, not current authorization.


def test_sql_enqueue_rejects_read_only_and_wrong_actor_without_writes():
    service, _, _ = setup()
    envelope = schedule(service)
    proof = CopyOperationAuthorization(
        operation_key=envelope.operation_key, authority=envelope.initial_authority, observed_at=NOW
    )
    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.writable = False
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.enqueue_operation(envelope, proof)
    tx.writable = True
    tx.organization_id, tx.scope_ref, tx.principal_id = "school", "scope", "other"
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
        tx.enqueue_operation(envelope, proof)
