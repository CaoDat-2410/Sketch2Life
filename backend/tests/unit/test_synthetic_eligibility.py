"""Pure eligibility facts, static migration checks and the operator tool with fakes.

No database, Alembic run, real settings loader or provider is used.
"""

from __future__ import annotations

import ast
import importlib.util
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest
from sketch2life.domain.eligibility import (
    BASIS_VERSION,
    PROOF_VERSION,
    EligibilityBasis,
    EligibilityDecision,
    EligibilityFacts,
    EligibilityReason,
    EligibilityScope,
    ProvisionalDataOrigin,
    SyntheticEligibilityProof,
    evaluate_eligibility,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import (
    ManagedProfileModel,
    SyntheticEligibilityProofModel,
)
from sqlalchemy import CheckConstraint, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

NOW = datetime(2026, 10, 31, 5, 0, tzinfo=UTC)
SCOPE = EligibilityScope("synthetic-org", "synthetic-class", "synthetic-child", "vision-pilot")


def valid_proof() -> SyntheticEligibilityProof:
    return SyntheticEligibilityProof(
        evidence_id="synthetic-evidence-v1",
        scope=SCOPE,
        run_ref="synthetic-run-v1",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
    )


def valid_facts() -> EligibilityFacts:
    return EligibilityFacts(
        profile_origin=ProvisionalDataOrigin.SYNTHETIC_DEV,
        scope=SCOPE,
        legal_consent_effective=False,
        proof=valid_proof(),
        session_run_ref="synthetic-run-v1",
        session_id="synthetic-session",
        environment="test",
        pilot_enabled=True,
        evaluated_at=NOW,
    )


def assert_denied(facts: EligibilityFacts, reason: EligibilityReason) -> None:
    result = evaluate_eligibility(facts)
    assert result.basis is EligibilityBasis.DENIED
    assert result.reason is reason
    assert result.basis_version == BASIS_VERSION
    assert result.evidence_id is None


@pytest.mark.parametrize("environment", ["local", "test"])
def test_valid_synthetic_decision_has_separate_versioned_basis(environment: str) -> None:
    facts = replace(valid_facts(), environment=environment)
    result = evaluate_eligibility(facts)
    assert result == EligibilityDecision(
        basis=EligibilityBasis.SYNTHETIC_DEV,
        reason=EligibilityReason.SYNTHETIC_PROOF_VALID,
        basis_version=BASIS_VERSION,
        evidence_id="synthetic-evidence-v1",
    )
    assert evaluate_eligibility(facts) == result
    assert facts.legal_consent_effective is False
    assert {field.name for field in fields(result)} == {
        "basis",
        "reason",
        "basis_version",
        "evidence_id",
    }


@pytest.mark.parametrize(
    "origin", [ProvisionalDataOrigin.REAL, ProvisionalDataOrigin.LEGACY_UNCLASSIFIED]
)
@pytest.mark.parametrize("environment", ["local", "production", ""])
def test_legal_branch_keeps_existing_effective_lookup_semantics(
    origin: ProvisionalDataOrigin,
    environment: str,
) -> None:
    facts = replace(
        valid_facts(),
        profile_origin=origin,
        proof=None,
        legal_consent_effective=True,
        pilot_enabled=False,
        environment=environment,
        session_run_ref=None,
    )
    result = evaluate_eligibility(facts)
    assert result.basis is EligibilityBasis.LEGAL_CONSENT
    assert result.reason is EligibilityReason.LEGAL_CONSENT_EFFECTIVE
    assert result.evidence_id is None


@pytest.mark.parametrize(
    "origin", [ProvisionalDataOrigin.REAL, ProvisionalDataOrigin.LEGACY_UNCLASSIFIED]
)
@pytest.mark.parametrize("effective", [False, None])
def test_pending_revoked_or_missing_legal_consent_denies(
    origin: ProvisionalDataOrigin,
    effective: bool | None,
) -> None:
    assert_denied(
        replace(
            valid_facts(), profile_origin=origin, proof=None, legal_consent_effective=effective
        ),
        EligibilityReason.LEGAL_CONSENT_NOT_EFFECTIVE,
    )


@pytest.mark.parametrize(
    "origin", [ProvisionalDataOrigin.REAL, ProvisionalDataOrigin.LEGACY_UNCLASSIFIED]
)
@pytest.mark.parametrize("effective", [True, False, None])
def test_proof_attached_to_real_or_legacy_is_always_denied(
    origin: ProvisionalDataOrigin,
    effective: bool | None,
) -> None:
    assert_denied(
        replace(valid_facts(), profile_origin=origin, legal_consent_effective=effective),
        EligibilityReason.PROOF_ON_LEGAL_PROFILE,
    )


@pytest.mark.parametrize("origin", [None, "", "SYNTHETIC_TEST", "synthetic_dev", "FUTURE_ORIGIN"])
@pytest.mark.parametrize("effective", [True, False])
def test_unknown_or_missing_origin_fails_closed(origin: str | None, effective: bool) -> None:
    assert_denied(
        replace(valid_facts(), profile_origin=origin, legal_consent_effective=effective),
        EligibilityReason.ORIGIN_NOT_ALLOWED,
    )


@pytest.mark.parametrize("field", ["organization_id", "class_id", "child_id", "purpose_ref"])
@pytest.mark.parametrize("missing", ["", "   ", None])
def test_missing_scope_is_denied(field: str, missing: str | None) -> None:
    # Simulate malformed pre-fetched facts at the future adapter boundary.
    scope = replace(SCOPE, **{field: cast(str, missing)})
    assert_denied(replace(valid_facts(), scope=scope), EligibilityReason.INVALID_FACTS)


@pytest.mark.parametrize("field", ["organization_id", "class_id", "child_id", "purpose_ref"])
def test_proof_must_match_each_scope_field(field: str) -> None:
    proof = replace(valid_proof(), scope=replace(SCOPE, **{field: "synthetic-foreign"}))
    assert_denied(replace(valid_facts(), proof=proof), EligibilityReason.SCOPE_MISMATCH)


@pytest.mark.parametrize("run_ref", [None, "", "   "])
def test_session_pilot_run_ref_must_exist(run_ref: str | None) -> None:
    assert_denied(replace(valid_facts(), session_run_ref=run_ref), EligibilityReason.RUN_REQUIRED)


def test_proof_run_must_match_server_session_configuration_run() -> None:
    proof = replace(valid_proof(), run_ref="synthetic-other-run")
    assert_denied(replace(valid_facts(), proof=proof), EligibilityReason.RUN_MISMATCH)


def test_optional_proof_session_binding_is_enforced() -> None:
    proof = replace(valid_proof(), session_id="synthetic-session")
    assert (
        evaluate_eligibility(replace(valid_facts(), proof=proof)).basis
        is EligibilityBasis.SYNTHETIC_DEV
    )
    for session_id in ("synthetic-other-session", None, ""):
        assert_denied(
            replace(valid_facts(), proof=proof, session_id=session_id),
            EligibilityReason.SESSION_MISMATCH,
        )


@pytest.mark.parametrize("environment", ["production", "dev", "staging", "TEST", "", None])
def test_synthetic_requires_local_or_test_at_evaluation_time(environment: str | None) -> None:
    assert_denied(
        replace(valid_facts(), environment=environment),
        EligibilityReason.ENVIRONMENT_DENIED,
    )


@pytest.mark.parametrize("enabled", [False, None, "true", 1])
def test_pilot_requires_exact_true(enabled: object) -> None:
    assert_denied(
        replace(valid_facts(), pilot_enabled=cast(bool, enabled)),
        EligibilityReason.PILOT_DISABLED,
    )


@pytest.mark.parametrize("proof", [None, "client-asserted-synthetic"])
def test_absent_or_wrong_type_proof_cannot_grant_synthetic(proof: object) -> None:
    assert_denied(
        replace(valid_facts(), proof=cast(SyntheticEligibilityProof | None, proof)),
        EligibilityReason.PROOF_REQUIRED if proof is None else EligibilityReason.INVALID_PROOF,
    )


@pytest.mark.parametrize("effective", [True, "true", 1])
def test_synthetic_cannot_carry_effective_legal_consent(effective: object) -> None:
    assert_denied(
        replace(valid_facts(), legal_consent_effective=cast(bool, effective)),
        EligibilityReason.CONFLICTING_BASIS,
    )


@pytest.mark.parametrize("effective", ["true", "false", 1, 0])
def test_legal_lookup_result_requires_boolean_true(effective: object) -> None:
    assert_denied(
        replace(
            valid_facts(),
            profile_origin=ProvisionalDataOrigin.REAL,
            proof=None,
            legal_consent_effective=cast(bool, effective),
        ),
        EligibilityReason.LEGAL_CONSENT_NOT_EFFECTIVE,
    )


@pytest.mark.parametrize("expires_at", [NOW, NOW - timedelta(seconds=1)])
def test_proof_expiry_boundary_is_exclusive(expires_at: datetime) -> None:
    assert_denied(
        replace(valid_facts(), proof=replace(valid_proof(), expires_at=expires_at)),
        EligibilityReason.PROOF_EXPIRED,
    )


def test_previously_valid_proof_is_rechecked_on_every_evaluation() -> None:
    facts = valid_facts()
    assert evaluate_eligibility(facts).basis is EligibilityBasis.SYNTHETIC_DEV
    assert_denied(
        replace(facts, evaluated_at=NOW + timedelta(hours=1)), EligibilityReason.PROOF_EXPIRED
    )
    assert_denied(replace(facts, pilot_enabled=False), EligibilityReason.PILOT_DISABLED)
    revoked = replace(valid_proof(), revoked_at=NOW)
    assert_denied(replace(facts, proof=revoked), EligibilityReason.PROOF_REVOKED)


@pytest.mark.parametrize("revoked_at", [NOW - timedelta(seconds=1), NOW, NOW + timedelta(days=1)])
def test_any_revocation_closes_proof(revoked_at: datetime) -> None:
    assert_denied(
        replace(valid_facts(), proof=replace(valid_proof(), revoked_at=revoked_at)),
        EligibilityReason.PROOF_REVOKED,
    )


def test_issued_at_must_not_be_in_the_future() -> None:
    assert_denied(
        replace(valid_facts(), proof=replace(valid_proof(), issued_at=NOW + timedelta(seconds=1))),
        EligibilityReason.PROOF_NOT_YET_VALID,
    )


@pytest.mark.parametrize("field", ["evidence_id", "run_ref", "schema_version", "session_id"])
@pytest.mark.parametrize("value", ["", "   "])
def test_empty_proof_identity_or_version_is_invalid(field: str, value: str) -> None:
    proof = valid_proof()
    if field == "evidence_id":
        proof = replace(proof, evidence_id=value)
    elif field == "run_ref":
        proof = replace(proof, run_ref=value)
    elif field == "schema_version":
        proof = replace(proof, schema_version=value)
    else:
        proof = replace(proof, session_id=value)
    assert_denied(
        replace(valid_facts(), proof=proof),
        EligibilityReason.INVALID_PROOF,
    )


def test_unsupported_proof_version_is_denied() -> None:
    assert valid_proof().schema_version == PROOF_VERSION
    assert_denied(
        replace(valid_facts(), proof=replace(valid_proof(), schema_version="future-proof-v2")),
        EligibilityReason.INVALID_PROOF,
    )


@pytest.mark.parametrize("field", ["issued_at", "expires_at"])
def test_naive_proof_time_is_denied(field: str) -> None:
    naive = NOW.replace(tzinfo=None)
    proof = (
        replace(valid_proof(), issued_at=naive)
        if field == "issued_at"
        else replace(valid_proof(), expires_at=naive)
    )
    assert_denied(
        replace(valid_facts(), proof=proof),
        EligibilityReason.INVALID_PROOF,
    )


def test_invalid_proof_interval_is_denied() -> None:
    proof = replace(valid_proof(), expires_at=valid_proof().issued_at)
    assert_denied(replace(valid_facts(), proof=proof), EligibilityReason.INVALID_PROOF)


def test_naive_or_missing_evaluation_clock_is_denied() -> None:
    for now in (NOW.replace(tzinfo=None), None):
        assert_denied(
            replace(valid_facts(), evaluated_at=cast(datetime, now)),
            EligibilityReason.INVALID_FACTS,
        )


def test_aware_non_utc_clock_uses_same_instant() -> None:
    facts = replace(valid_facts(), evaluated_at=NOW.astimezone(timezone(timedelta(hours=7))))
    assert evaluate_eligibility(facts) == evaluate_eligibility(valid_facts())


class _RepeatedHourTimezone(tzinfo):
    """Deterministic rollback-hour fixture without platform timezone data."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=-5 if dt is not None and dt.fold else -4)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, dt: datetime | None) -> str:
        return "synthetic-fold-timezone"


@pytest.mark.parametrize("case", ["expiry", "issued", "interval"])
def test_repeated_hour_compares_instants_instead_of_wall_clock(case: str) -> None:
    zone = _RepeatedHourTimezone()
    now = datetime(2026, 11, 1, 1, 20, tzinfo=zone, fold=1)
    issued = datetime(2026, 11, 1, 1, 0, tzinfo=zone, fold=0)
    expires = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
    if case == "issued":
        issued = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
        expires = datetime(2026, 11, 1, 2, 0, tzinfo=zone, fold=1)
    elif case == "interval":
        issued = datetime(2026, 11, 1, 1, 50, tzinfo=zone, fold=0)
        expires = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=1)
    facts = replace(
        valid_facts(),
        evaluated_at=now,
        proof=replace(valid_proof(), issued_at=issued, expires_at=expires),
    )
    if case == "expiry":
        assert_denied(facts, EligibilityReason.PROOF_EXPIRED)
    else:
        assert evaluate_eligibility(facts).basis is EligibilityBasis.SYNTHETIC_DEV


def test_domain_has_only_standard_library_dependencies_and_no_io_calls() -> None:
    path = Path(__file__).resolve().parents[2] / "src/sketch2life/domain/eligibility.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imports <= {"__future__", "dataclasses", "datetime", "enum"}
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    forbidden = {
        "open",
        "getenv",
        "now",
        "utcnow",
        "connect",
        "execute",
        "requests",
        "get_settings",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (
                node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            )
            assert name not in forbidden


# --- P4 static checks: no Alembic run, no database connection ---------------------------------

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_NEW_REVISION = "20261031_be1_se_0001"
_PARENT_REVISION = "20261024_0005"
_NEW_MIGRATION = _VERSIONS / "20261031_be1_synthetic_eligibility.py"


def _as_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    assert isinstance(value, (tuple, list))
    return tuple(str(item) for item in value)


def _module_constants(path: Path) -> dict[str, object]:
    constants: dict[str, object] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target: ast.expr = node.targets[0]
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target = node.target
        else:
            continue
        if isinstance(target, ast.Name) and target.id in {
            "revision",
            "down_revision",
            "depends_on",
            "branch_labels",
        }:
            value = node.value
            assert value is not None
            constants[target.id] = ast.literal_eval(value)
    return constants


def _revision_graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        constants = _module_constants(path)
        revision = constants["revision"]
        assert isinstance(revision, str)
        assert revision not in graph, revision
        graph[revision] = (
            _as_tuple(constants.get("down_revision")),
            _as_tuple(constants.get("depends_on")),
        )
    return graph


def test_new_revision_is_a_single_short_child_of_the_confirmed_parent() -> None:
    constants = _module_constants(_NEW_MIGRATION)
    assert constants["revision"] == _NEW_REVISION
    assert len(_NEW_REVISION) <= 32
    assert constants["down_revision"] == _PARENT_REVISION
    assert constants["branch_labels"] is None
    assert constants["depends_on"] is None
    graph = _revision_graph()
    children = {rev for rev, (down, _) in graph.items() if _PARENT_REVISION in down}
    assert children == {_NEW_REVISION}


def test_head_counts_by_both_methods_match_the_derived_expectation() -> None:
    graph = _revision_graph()
    assert len(graph) == 23  # 22 existing scripts plus the new one
    down_targets = {target for down, _ in graph.values() for target in down}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    # Before this revision the counts were 10 and 9; the new leaf replaces its parent as a
    # down_revision leaf and adds one dependency-aware leaf.
    assert (len(heads_down_only), len(heads_with_depends)) == (10, 10)
    assert _NEW_REVISION in heads_down_only
    assert _NEW_REVISION in heads_with_depends


def _migration_check_texts() -> dict[str, str]:
    texts: dict[str, str] = {}
    for node in ast.walk(ast.parse(_NEW_MIGRATION.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        callee = ast.unparse(node.func)
        if callee == "op.create_check_constraint":
            name, _, text = (ast.literal_eval(arg) for arg in node.args[:3])
            texts[name] = text
        elif callee == "sa.CheckConstraint":
            keywords = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords if kw.arg}
            texts[keywords["name"]] = ast.literal_eval(node.args[0])
    return texts


def _normalized(text: object) -> str:
    return " ".join(str(text).split())


def test_orm_check_constraints_match_the_migration_text_exactly() -> None:
    migration = _migration_check_texts()
    orm: dict[str, str] = {}
    for model in (ManagedProfileModel, SyntheticEligibilityProofModel):
        table = cast(Table, model.__table__)
        for constraint in table.constraints:
            if isinstance(constraint, CheckConstraint) and constraint.name in {
                "ck_be1_profile_data_origin",
                "ck_be1_profile_origin_consent_refs",
                "ck_be1_synth_proof_origin",
                "ck_be1_synth_proof_interval",
                "ck_be1_synth_proof_revocation",
            }:
                orm[str(constraint.name)] = str(constraint.sqltext)
    assert set(orm) == set(migration) and len(orm) == 5
    for name, text in orm.items():
        assert _normalized(migration[name]) == _normalized(text), name


def _migration_call(name: str, table: str) -> ast.Call:
    for node in ast.walk(ast.parse(_NEW_MIGRATION.read_text(encoding="utf-8"))):
        if (
            isinstance(node, ast.Call)
            and ast.unparse(node.func) == name
            and node.args
            and ast.literal_eval(node.args[0]) == table
        ):
            return node
    raise AssertionError(f"{name}({table!r}) not found in the migration")


def _literal_keyword(call: ast.Call, key: str, default: object) -> object:
    for keyword in call.keywords:
        if keyword.arg == key:
            return ast.literal_eval(keyword.value)
    return default


def test_orm_columns_foreign_keys_and_index_match_the_migration() -> None:
    proofs = cast(Table, SyntheticEligibilityProofModel.__table__)
    create = _migration_call("op.create_table", "be1_synthetic_eligibility_proofs")
    migrated: dict[str, bool] = {}
    foreign_keys: dict[str, tuple[str, str | None]] = {}
    for arg in create.args[1:]:
        assert isinstance(arg, ast.Call)
        callee = ast.unparse(arg.func)
        if callee == "sa.Column":
            primary_key = _literal_keyword(arg, "primary_key", False) is True
            nullable = _literal_keyword(arg, "nullable", not primary_key)
            migrated[ast.literal_eval(arg.args[0])] = bool(nullable) and not primary_key
        elif callee == "sa.ForeignKeyConstraint":
            foreign_keys[str(_literal_keyword(arg, "name", None))] = (
                ast.literal_eval(arg.args[1])[0],
                cast("str | None", _literal_keyword(arg, "ondelete", None)),
            )
    assert migrated == {column.name: column.nullable for column in proofs.columns}
    orm_foreign_keys = {
        str(fk.name): (fk.target_fullname, fk.ondelete)
        for fk in (list(column.foreign_keys)[0] for column in proofs.columns if column.foreign_keys)
    }
    assert foreign_keys == orm_foreign_keys
    index = _migration_call("op.create_index", "ix_be1_synth_proof_scope")
    assert ast.literal_eval(index.args[2]) == [
        column.name for column in next(iter(proofs.indexes)).columns
    ]
    profile = cast(Table, ManagedProfileModel.__table__)
    assert profile.c.data_origin.nullable is False
    assert profile.c.consent_id.nullable is True and profile.c.consent_purpose_ref.nullable is True
    upgrade = next(
        node
        for node in ast.parse(_NEW_MIGRATION.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade"
    )
    relaxed = {
        ast.literal_eval(call.args[1])
        for call in ast.walk(upgrade)
        if isinstance(call, ast.Call)
        and ast.unparse(call.func) == "op.alter_column"
        and _literal_keyword(call, "nullable", None) is True
    }
    assert relaxed == {"consent_id", "consent_purpose_ref"}


def test_new_tables_compile_for_postgresql_without_a_connection() -> None:
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    proof = str(
        CreateTable(cast(Table, SyntheticEligibilityProofModel.__table__)).compile(dialect=dialect)
    )
    for expected in (
        "ck_be1_synth_proof_origin",
        "ck_be1_synth_proof_interval",
        "ck_be1_synth_proof_revocation",
        "REFERENCES be1_managed_profiles (child_id)",
        "REFERENCES be1_organizations (organization_id)",
        "issued_at TIMESTAMP WITH TIME ZONE NOT NULL",
        "expires_at TIMESTAMP WITH TIME ZONE NOT NULL",
        "revoked_at TIMESTAMP WITH TIME ZONE,",
    ):
        assert expected in proof, expected
    profile = str(CreateTable(cast(Table, ManagedProfileModel.__table__)).compile(dialect=dialect))
    assert "data_origin VARCHAR(24) NOT NULL" in profile
    assert "ck_be1_profile_data_origin" in profile
    assert "ck_be1_profile_origin_consent_refs" in profile
    assert "consent_id VARCHAR(36)," in profile and "consent_purpose_ref VARCHAR(128)," in profile


def test_check_constraints_never_read_another_table() -> None:
    for text in _migration_check_texts().values():
        assert "SELECT" not in text.upper()
        assert "be1_synthetic_eligibility_proofs" not in text


def test_registry_default_stays_real_and_the_migration_backfills_legacy() -> None:
    column = cast(Table, ManagedProfileModel.__table__).c.data_origin
    assert getattr(column.default, "arg", None) == "REAL"
    source = _NEW_MIGRATION.read_text(encoding="utf-8")
    assert 'server_default="LEGACY_UNCLASSIFIED"' in source
    assert source.index("server_default=None") > source.index(
        'server_default="LEGACY_UNCLASSIFIED"'
    )


def test_downgrade_refuses_before_it_drops_anything() -> None:
    tree = ast.parse(_NEW_MIGRATION.read_text(encoding="utf-8"))
    downgrade = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "downgrade"
    )
    raises = [node for node in ast.walk(downgrade) if isinstance(node, ast.Raise)]
    drops = [
        node
        for node in ast.walk(downgrade)
        if isinstance(node, ast.Call)
        and ast.unparse(node.func) in {"op.drop_table", "op.drop_column", "op.drop_constraint"}
    ]
    assert len(raises) == 1 and drops
    assert all(raises[0].lineno < drop.lineno for drop in drops)
    guard = ast.unparse(downgrade)
    for needle in (
        "be1_synthetic_eligibility_proofs",
        "data_origin = 'SYNTHETIC_DEV'",
        "consent_id IS NULL",
    ):
        assert needle in guard, needle


def test_synthetic_pilot_setting_is_off_by_default() -> None:
    assert Settings.model_fields["synthetic_pilot_enabled"].default is False


# --- P6 operator tool: fakes only, no database, no real settings -------------------------------

_TOOL_PATH = Path(__file__).resolve().parents[3] / "tools" / "synthetic_eligibility.py"
_PROBE = "redaction-probe-value"
_LOCAL_URL = f"postgresql+psycopg://operator:{_PROBE}@localhost:5432/anything"


def _load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("synthetic_eligibility_tool", _TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


class _FakeStore:
    def __init__(self, result: bool = True, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._result = result
        self._error = error

    def _record(self, name: str, kwargs: dict[str, Any]) -> bool:
        self.calls.append((name, kwargs))
        if self._error is not None:
            raise self._error
        return self._result

    def create_synthetic_profile(self, **kwargs: Any) -> bool:
        return self._record("create_synthetic_profile", kwargs)

    def issue_synthetic_proof(self, **kwargs: Any) -> bool:
        return self._record("issue_synthetic_proof", kwargs)

    def revoke_synthetic_proof(self, **kwargs: Any) -> bool:
        return self._record("revoke_synthetic_proof", kwargs)


def _run(
    argv: list[str],
    *,
    env: str = "test",
    enabled: bool = True,
    url: str | None = _LOCAL_URL,
    store: _FakeStore | None = None,
) -> tuple[int, list[str], list[str]]:
    output: list[str] = []
    factory_urls: list[str] = []
    fake = store or _FakeStore()

    def factory(database_url: str) -> _FakeStore:
        factory_urls.append(database_url)
        return fake

    code = tool.run(
        argv,
        settings_loader=lambda: SimpleNamespace(env=env, synthetic_pilot_enabled=enabled),
        database_url_loader=lambda: url,
        store_factory=factory,
        clock=lambda: NOW,
        emit=output.append,
    )
    assert isinstance(code, int)
    return code, output, factory_urls


_ISSUE = [
    "issue",
    "--pilot",
    "--organization-id",
    "synthetic-org",
    "--class-id",
    "synthetic-class",
    "--child-id",
    "synthetic-child",
    "--purpose-ref",
    "vision-pilot",
    "--run-ref",
    "synthetic-run-v1",
    "--evidence-id",
    "synthetic-evidence-v1",
    "--session-id",
    "synthetic-session",
]


@pytest.mark.parametrize(
    "url",
    [
        f"postgresql://u:{_PROBE}@localhost/db",
        f"postgresql://u:{_PROBE}@127.0.0.1:5432/db",
        f"postgresql://u:{_PROBE}@[::1]/db",
        f"postgresql://u:{_PROBE}@db.example.com/s2l_be1_acceptance",
        f"postgresql://u:{_PROBE}@localhost/db?hostaddr=127.0.0.1",
    ],
)
def test_database_url_checks_accept_loopback_or_disposable_databases(url: str) -> None:
    tool.check_database_url(url)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "not a url",
        f"postgresql://u:{_PROBE}@db.example.com/production",
        f"postgresql://u:{_PROBE}@10.0.0.5/production",
        f"postgresql://u:{_PROBE}@localhost/production?host=db.example.com",
        f"postgresql://u:{_PROBE}@localhost/production?hostaddr=10.0.0.5",
        f"postgresql://u:{_PROBE}@/production?host=/var/run/postgresql",
    ],
)
def test_database_url_checks_refuse_everything_else_without_echoing_secrets(
    url: str | None,
) -> None:
    with pytest.raises(tool.SafetyError) as caught:
        tool.check_database_url(url)
    assert _PROBE not in str(caught.value)
    assert "example.com" not in str(caught.value)


@pytest.mark.parametrize(
    "env,enabled,flag",
    [
        ("production", True, True),
        ("staging", True, True),
        ("test", False, True),
        ("test", True, False),
    ],
)
def test_tool_refuses_outside_local_test_pilot_and_without_the_pilot_flag(
    env: str, enabled: bool, flag: bool
) -> None:
    argv = [arg for arg in _ISSUE if flag or arg != "--pilot"]
    store = _FakeStore()
    code, output, factory_urls = _run(argv + ["--apply"], env=env, enabled=enabled, store=store)
    assert code == 2 and factory_urls == [] and store.calls == []
    assert _PROBE not in " ".join(output)


def test_tool_refuses_a_non_loopback_database_before_connecting() -> None:
    store = _FakeStore()
    url = f"postgresql://u:{_PROBE}@db.example.com/production"
    code, output, factory_urls = _run(_ISSUE + ["--apply"], url=url, store=store)
    assert code == 2 and factory_urls == [] and store.calls == []
    assert _PROBE not in " ".join(output)


def test_tool_defaults_to_a_dry_run_that_opens_no_connection() -> None:
    store = _FakeStore()
    code, output, factory_urls = _run(_ISSUE, store=store)
    assert code == 0 and factory_urls == [] and store.calls == []
    assert output and output[0].startswith("DRY-RUN")
    assert _PROBE not in " ".join(output)


def test_apply_issues_only_the_scoped_proof_with_a_bounded_lifetime() -> None:
    store = _FakeStore()
    code, output, factory_urls = _run(
        _ISSUE + ["--ttl-minutes", "30", "--apply"],
        store=store,
    )
    assert code == 0 and factory_urls == [_LOCAL_URL]
    ((name, kwargs),) = store.calls
    assert name == "issue_synthetic_proof"
    assert kwargs == {
        "evidence_id": "synthetic-evidence-v1",
        "organization_id": "synthetic-org",
        "class_id": "synthetic-class",
        "child_id": "synthetic-child",
        "purpose_ref": "vision-pilot",
        "run_ref": "synthetic-run-v1",
        "session_id": "synthetic-session",
        "issued_by": "local-operator",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=30),
        "policy_version": tool.POLICY_VERSION,
    }
    assert output[0].startswith("APPLIED")
    assert _PROBE not in " ".join(output) and _LOCAL_URL not in " ".join(output)


def test_issue_requires_a_session_id_because_the_run_is_teacher_writable() -> None:
    argv = _ISSUE[: _ISSUE.index("--session-id")] + ["--apply"]
    store = _FakeStore()
    with pytest.raises(SystemExit) as raised:
        _run(argv, store=store)
    assert raised.value.code == 2
    assert store.calls == []


@pytest.mark.parametrize("ttl", ["0", "-5", "1441"])
def test_ttl_outside_the_bound_is_refused(ttl: str) -> None:
    store = _FakeStore()
    code, _, _ = _run(_ISSUE + ["--ttl-minutes", ttl, "--apply"], store=store)
    assert code == 2 and store.calls == []


def test_create_profile_and_revoke_use_only_their_narrow_store_methods() -> None:
    store = _FakeStore()
    code, _, _ = _run(
        [
            "create-profile",
            "--pilot",
            "--organization-id",
            "synthetic-org",
            "--class-id",
            "synthetic-class",
            "--child-id",
            "synthetic-child",
            "--age-months",
            "60",
            "--apply",
        ],
        store=store,
    )
    assert code == 0
    assert store.calls[0][1]["display_name"] == "Synthetic synthetic-child"
    code, _, _ = _run(
        [
            "revoke",
            "--pilot",
            "--organization-id",
            "synthetic-org",
            "--evidence-id",
            "e1",
            "--apply",
        ],
        store=store,
    )
    assert code == 0
    assert [name for name, _ in store.calls] == [
        "create_synthetic_profile",
        "revoke_synthetic_proof",
    ]
    assert store.calls[1][1] == {
        "evidence_id": "e1",
        "organization_id": "synthetic-org",
        "revoked_at": NOW,
    }


def test_age_outside_the_profile_bound_is_refused() -> None:
    store = _FakeStore()
    code, _, _ = _run(
        [
            "create-profile",
            "--pilot",
            "--organization-id",
            "o",
            "--class-id",
            "c",
            "--child-id",
            "synthetic-k",
            "--age-months",
            "12",
            "--apply",
        ],
        store=store,
    )
    assert code == 2 and store.calls == []


@pytest.mark.parametrize(
    "child_id",
    ["real-child", "Nguyen Van A", "synthetic-", "synthetic-UPPER", "synthetic-a b", "x" * 120],
)
def test_only_artificial_child_ids_are_accepted_so_no_real_identity_is_stored(
    child_id: str,
) -> None:
    profile = ["create-profile", "--pilot", "--organization-id", "o", "--class-id", "c"]
    store = _FakeStore()
    code, _, _ = _run(
        profile + ["--child-id", child_id, "--age-months", "60", "--apply"], store=store
    )
    assert code == 2 and store.calls == []
    issued = [child_id if arg == "synthetic-child" else arg for arg in _ISSUE]
    code, _, _ = _run(issued + ["--apply"], store=store)
    assert code == 2 and store.calls == []


def test_the_profile_has_no_free_text_name_option() -> None:
    store = _FakeStore()
    with pytest.raises(SystemExit) as raised:
        _run(
            ["create-profile", "--pilot", "--organization-id", "o", "--class-id", "c"]
            + ["--child-id", "synthetic-k", "--display-name", "Real Name", "--age-months", "60"],
            store=store,
        )
    assert raised.value.code == 2 and store.calls == []


def test_the_store_refuses_a_profile_that_does_not_look_synthetic_before_any_session() -> None:
    from sketch2life.infrastructure.persistence.core_store import PostgresCoreStore

    store = PostgresCoreStore(cast(Any, None))
    for child_id, name in (("real-child", "Synthetic x"), ("synthetic-k", "Real Name")):
        with pytest.raises(ValueError):
            store.create_synthetic_profile(
                organization_id="o",
                class_id="c",
                child_id=child_id,
                display_name=name,
                age_months=60,
                created_by="local-operator",
            )


def test_store_refusal_or_conflict_is_reported_and_not_a_success() -> None:
    code, output, _ = _run(
        _ISSUE + ["--apply"], store=_FakeStore(error=ValueError("not a SYNTHETIC_DEV profile"))
    )
    assert code == 1 and output[0].startswith("refused")
    code, output, _ = _run(_ISSUE + ["--apply"], store=_FakeStore(result=False))
    assert code == 1 and output[0].startswith("NOT APPLIED")


def test_tool_exposes_no_http_surface() -> None:
    tree = ast.parse(_TOOL_PATH.read_text(encoding="utf-8"))
    imported = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any(
        name.split(".")[0] in {"fastapi", "starlette", "httpx", "requests"} for name in imported
    )
