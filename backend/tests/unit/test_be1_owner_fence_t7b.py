"""T7b: canonical scoped fences and caller-owned PostgreSQL lock behavior."""

from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import pytest
from sketch2life.application.ports.ai_jobs import OwnerFence
from sketch2life.domain.assistance import (
    MemberFact,
    ResolvedFacts,
    SourcePin,
    TargetKind,
    TargetScope,
)
from sketch2life.domain.eligibility import BASIS_VERSION, EligibilityBasis, EligibilityScope
from sketch2life.infrastructure.assistance import owner_fence as module
from sketch2life.infrastructure.assistance.owner_fence import (
    PostgresBE1OwnerFence,
    build_owner_fence,
    decode_owner_fence_scope,
    owner_fence_factory,
    resolved_facts_epoch,
)
from sqlalchemy import Connection
from sqlalchemy.dialects import postgresql


def facts() -> ResolvedFacts:
    return ResolvedFacts(
        organization_id="org",
        class_id="class",
        session_id="session",
        canvas_id="canvas",
        group_id="group",
        roster_revision=1,
        target=TargetScope(TargetKind.INDIVIDUAL, "child"),
        region_id=None,
        region_policy_revision=1,
        contributor_participant_id="child",
        audience=("child",),
        members=(
            MemberFact(
                "child",
                60,
                "age",
                1,
                None,
                None,
                False,
                False,
                str(EligibilityBasis.SYNTHETIC_DEV),
                BASIS_VERSION,
                "proof",
                EligibilityScope("org", "class", "child", "purpose"),
            ),
        ),
        purpose_code="purpose",
        age_policy_ref="age-policy",
        policy_id="policy",
        policy_version="1",
        context_revision=3,
        source=SourcePin("snapshot", "checkpoint", 1, 40, "a" * 64, "render", "b" * 64, "c" * 64),
    )


class Result:
    def __init__(self, values: list[str]) -> None:
        self.values = values

    def scalars(self) -> Result:
        return self

    def all(self) -> list[str]:
        return self.values

    def scalar_one_or_none(self) -> str | None:
        assert len(self.values) <= 1
        return self.values[0] if self.values else None


class ConnectionFake:
    dialect = SimpleNamespace(name="postgresql")

    def __init__(self) -> None:
        self.statements: list[str] = []
        self.parameters: list[object] = []
        self.transaction_active = True
        self.missing_table: str | None = None
        self.raise_on_execute = False

    def in_transaction(self) -> bool:
        return self.transaction_active

    def execute(self, statement: Any, parameters: object = None) -> Result:
        if self.raise_on_execute:
            raise RuntimeError("synthetic database unavailable")
        compiled = statement.compile(dialect=postgresql.dialect())
        sql = str(compiled)
        self.statements.append(sql)
        self.parameters.append(parameters)
        if "FOR SHARE" not in sql:
            return Result(["membership"] if "be1_session_memberships" in sql else [])
        if self.missing_table is not None and self.missing_table in sql:
            return Result([])
        return Result([next(iter(compiled.params.values()))])


def test_canonical_fence_roundtrip_and_existing_epoch_function() -> None:
    pinned = build_owner_fence(facts())
    scope = decode_owner_fence_scope(pinned.fence_scope)
    assert scope is not None
    assert scope.canonical() == pinned.fence_scope
    assert pinned.epoch == resolved_facts_epoch(facts().digest())
    assert 1 <= pinned.epoch <= 0x7FFFFFFF


@pytest.mark.parametrize("change", ["version", "unknown", "duplicate", "missing", "noncanonical"])
def test_scope_rejects_malformed_or_ambiguous_values(change: str) -> None:
    encoded = build_owner_fence(facts()).fence_scope
    payload = json.loads(encoded)
    if change == "version":
        payload["version"] = "unrecognized"
    elif change == "unknown":
        payload["unrecognized"] = True
    elif change == "duplicate":
        payload["audience"] = ["child", "child"]
        payload["proof_ids"] = ["proof", "proof"]
    elif change == "missing":
        del payload["class_id"]
    else:
        assert decode_owner_fence_scope(json.dumps(payload)) is None
        return
    candidate = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    assert decode_owner_fence_scope(candidate) is None


def test_factory_locks_sorted_rows_and_rechecks_on_exact_connection() -> None:
    connection = ConnectionFake()
    supplied: list[Connection] = []

    def resolver(bound: Connection, scope: module.BE1OwnerFenceScope) -> ResolvedFacts:
        supplied.append(bound)
        assert scope.organization_id == "org"
        assert any("FOR SHARE" in sql for sql in connection.statements)
        return facts()

    adapter = owner_fence_factory(resolver)(cast(Connection, connection))
    result = adapter.hold((build_owner_fence(facts()),))
    assert result.current and not result.stale
    assert supplied == [connection]
    assert connection.parameters[0] == {"timeout": "1000ms"}
    locks = [sql for sql in connection.statements if "FOR SHARE" in sql]
    table_names = [sql.split("FROM ")[1].split()[0] for sql in locks]
    assert table_names == sorted(table_names)
    assert len(locks) == 7  # profile, membership, group, session, proof, 2 aggregate revisions
    assert "set_config('lock_timeout'" in connection.statements[0]
    assert not any("COMMIT" in sql or "UPDATE" in sql for sql in connection.statements)


@pytest.mark.parametrize(
    "missing",
    [
        "be1_managed_profiles",
        "be1_session_memberships",
        "be1_session_groups",
        "be1_sessions",
        "be1_synthetic_eligibility_proofs",
        "core_aggregate_revisions",
    ],
)
def test_missing_required_row_refuses_before_resolver(missing: str) -> None:
    connection = ConnectionFake()
    connection.missing_table = missing
    called = []
    pinned = build_owner_fence(facts())
    result = PostgresBE1OwnerFence(
        cast(Connection, connection),
        lambda *_: called.append(True),  # type: ignore[arg-type,return-value]
    ).hold((pinned,))
    assert not result.current and result.stale == (pinned,) and not called


def test_changed_full_digest_is_stale_even_if_integer_epoch_collides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "resolved_facts_epoch", lambda _: 11)
    original = facts()
    pinned = build_owner_fence(original)
    changed = replace(original, roster_revision=2)
    adapter = PostgresBE1OwnerFence(cast(Connection, ConnectionFake()), lambda *_: changed)
    result = adapter.hold((pinned,))
    assert not result.current and result.stale == (pinned,)


def test_cross_organization_or_duplicate_fences_refuse_without_database_work() -> None:
    connection = ConnectionFake()
    pinned = build_owner_fence(facts())
    another = build_owner_fence(
        replace(
            facts(),
            organization_id="other",
            members=(
                replace(
                    facts().members[0],
                    eligibility_scope=EligibilityScope("other", "class", "child", "purpose"),
                ),
            ),
        )
    )
    adapter = PostgresBE1OwnerFence(cast(Connection, connection), lambda *_: facts())
    assert not adapter.hold((pinned, another)).current
    assert not adapter.hold((pinned, pinned)).current
    assert connection.statements == []


def test_synthetic_member_scope_must_match_the_pinned_owner_scope() -> None:
    with pytest.raises(ValueError):
        build_owner_fence(replace(facts(), organization_id="other"))


@pytest.mark.parametrize("mode", ["transaction", "epoch", "database", "resolver"])
def test_unknown_transaction_or_read_failure_never_returns_current(mode: str) -> None:
    connection = ConnectionFake()
    pinned = build_owner_fence(facts())
    if mode == "transaction":
        connection.transaction_active = False
    elif mode == "epoch":
        pinned = replace(pinned, epoch=pinned.epoch + 1)
    elif mode == "database":
        connection.raise_on_execute = True

    def resolver(*_: object) -> ResolvedFacts:
        if mode == "resolver":
            raise RuntimeError("synthetic owner source unavailable")
        return facts()

    assert not PostgresBE1OwnerFence(cast(Connection, connection), resolver).hold((pinned,)).current


def test_unknown_fence_is_stale_and_lock_timeout_is_bounded() -> None:
    connection = cast(Connection, ConnectionFake())
    adapter = PostgresBE1OwnerFence(connection, lambda *_: facts())
    assert not adapter.hold((OwnerFence("unknown", 1),)).current
    with pytest.raises(ValueError):
        PostgresBE1OwnerFence(connection, lambda *_: facts(), lock_timeout_ms=5001)
