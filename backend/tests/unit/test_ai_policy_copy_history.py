"""Historical verification/rollback/DDL checks; MEMORY and offline, not real SQL proof."""

import importlib.util
import re
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.contracts.schemas.ai_policy_copy_history import CopyInventoryEvidence
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
    decode_inventory_evidence,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import COPY_EVIDENCE
from tests.ai_policy_copy_inventory_fixtures import (
    COVERAGE,
    SOURCE,
    context,
    read_request,
    registration,
    setup,
)
from tests.unit.test_ai_policy_domain import NOW


def evidence():
    service, _, store = setup()
    service.register("operator", "school", context(), registration(), SOURCE)
    return store.scopes["school", "scope"]["evidence"][0]


def row(value):
    return dict(
        evidence_id="proof",
        organization_id=value.organization_id,
        scope_ref=value.context.scope_ref,
        principal_id=value.principal_id,
        inventory_revision=1,
        observed_at=value.observed_at,
        record=value.model_dump(mode="json"),
    )


def test_history_exact_command_and_source_survive_json_roundtrip():
    value = evidence()
    assert _digest(value.command_binding()) == value.command_digest
    assert value.authority.command_digest == value.source.binding_digest == value.command_digest
    assert value.source.reference == SOURCE
    assert value.registration.original_profile_ref == registration().original_profile_ref
    assert decode_inventory_evidence(row(value)) == value
    assert not hasattr(value, "actual_deletion_proven")


def test_replay_keeps_fresh_authority_history_without_duplicate_mutation():
    service, boundary, store = setup()
    for _ in range(2):
        service.register("operator", "school", context(), registration(), SOURCE)
    state = store.scopes["school", "scope"]
    assert state["revision"] == 1 and len(state["events"]) == 1
    assert len(state["evidence"]) == 2
    boundary.allowed.remove("register")
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.register("operator", "school", context(), registration(), SOURCE)
    assert len(state["evidence"]) == 2


def test_fence_and_coverage_keep_separate_bindings_without_invalidating_coverage():
    service, _, store = setup()
    service.fence("operator", "school", context())
    service.fence("operator", "school", context())
    service.coverage("operator", "school", context(), expected_revision=1, reference=COVERAGE)
    state = store.scopes["school", "scope"]
    assert len(state["evidence"]) == 3 and state["revision"] == 2
    assert state["evidence"][0].source is None
    assert state["evidence"][2].coverage.attestation_ref == COVERAGE
    assert all(_digest(v.command_binding()) == v.command_digest for v in state["evidence"])
    assert service.page("operator", "school", read_request()).coverage_status == "reported_complete"
    assert len(state["evidence"]) == 3  # Authorized reads are not durable grants.


@pytest.mark.parametrize("failure", ["commit", "authority", "history"])
def test_history_and_inventory_are_rolled_back_together(failure):
    service, boundary, store = setup()
    if failure == "commit":
        store.fail_commit = True
    elif failure == "authority":
        boundary.confirm_changes = {"allowed": False}
    else:
        original = store.record_evidence

        def fail(value):
            original(value)
            raise PolicyError("SYNTHETIC_EVIDENCE_FAILURE")

        store.record_evidence = fail
    with pytest.raises(PolicyError):
        service.register("operator", "school", context(), registration(), SOURCE)
    assert not store.scopes


@pytest.mark.parametrize(
    "change",
    [
        {"action": "read"},
        {"principal_id": "other"},
        {"organization_id": "other"},
        {"command_digest": "f" * 64},
        {"source": None},
        {"registration": None},
        {"action": "fence"},
        {"observed_at": NOW + timedelta(hours=2)},
        {"observed_at": NOW.replace(tzinfo=None)},
        {"actual_deletion_proven": True},
    ],
)
def test_history_rejects_incomplete_cross_scope_expired_or_asserted_proof(change):
    value = evidence().model_dump(mode="python") | change
    with pytest.raises(ValidationError):
        CopyInventoryEvidence.model_validate(value, strict=True)


@pytest.mark.parametrize(
    "change",
    [
        {"principal_id": "other"},
        {"scope_ref": "other"},
        {"organization_id": "other"},
        {"observed_at": NOW + timedelta(seconds=1)},
        {"inventory_revision": True},
        {"inventory_revision": -1},
        {"evidence_id": "https://not-an-opaque-reference"},
        {"record": {}},
    ],
)
def test_decoder_rejects_column_payload_substitution(change):
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_EVIDENCE_STORAGE"):
        decode_inventory_evidence(row(evidence()) | change)


def test_sql_write_strictly_revalidates_constructed_history_and_binds_transaction():
    class NoWrites:
        def execute(self, statement):
            raise AssertionError("invalid history must not execute SQL")

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection = NoWrites()
    tx.writable = True
    tx.organization_id, tx.scope_ref, tx.principal_id = "school", "scope", "operator"
    value = evidence()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
        tx.principal_id = "different"
        tx.record_evidence(value)
    tx.principal_id = "operator"
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_EVIDENCE"):
        tx.record_evidence(value.model_copy(update={"command_digest": "f" * 64}))
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_EVIDENCE"):
        tx.record_evidence(
            value.model_copy(update={"source": value.source.model_copy(update={"verified": 1})})
        )
    # Internally consistent echoed digest still cannot hide a different exact body.
    forged = value.model_copy(
        update={
            "command_digest": "f" * 64,
            "authority": value.authority.model_copy(update={"command_digest": "f" * 64}),
            "source": value.source.model_copy(update={"binding_digest": "f" * 64}),
        }
    )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_EVIDENCE"):
        tx.record_evidence(forged)
    tx.writable = False
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.record_evidence(value)


def test_forward_migration_matches_metadata_and_history_trigger(monkeypatch):
    path = (
        Path(__file__).resolve().parents[2] / "alembic/versions/20261017_ap_0005_copy_evidence.py"
    )
    spec = importlib.util.spec_from_file_location("copy_evidence_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def normalize(text):
        return re.sub(r"\s+", "", text)

    assert normalize(str(CreateTable(COPY_EVIDENCE).compile(dialect=dialect())) + ";") == normalize(
        module.DDL
    )
    assert module.down_revision == "20261017_ap_0004" and module.branch_labels is None
    statements = []

    class Capture:
        def execute(self, sql):
            statements.append(sql)

        def drop_table(self, name, schema):
            statements.append((schema, name))

    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert "BEFORE UPDATE OR DELETE" in statements[1]
    assert "ai_policy.protect_history()" in statements[1]
    module.downgrade()
    assert statements[-1] == ("ai_policy", "copy_inventory_evidence")


def test_sql_evidence_insert_binds_original_record_and_inventory_revision():
    captured = []

    class Capture:
        def execute(self, statement):
            captured.append(statement.compile(dialect=dialect()).params)

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.writable, tx.revision = Capture(), True, 4
    tx.organization_id, tx.scope_ref, tx.principal_id = "school", "scope", "operator"
    value = evidence()
    tx.record_evidence(value)
    assert len(captured) == 1
    assert captured[0]["inventory_revision"] == 4
    assert decode_inventory_evidence(captured[0]) == value


def test_storage_decode_recomputes_command_not_just_echoed_hashes():
    value = evidence().model_dump(mode="json")
    value["command_digest"] = "f" * 64
    value["authority"]["command_digest"] = "f" * 64
    value["source"]["binding_digest"] = "f" * 64
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_EVIDENCE_STORAGE"):
        decode_inventory_evidence(row(evidence()) | {"record": value})
