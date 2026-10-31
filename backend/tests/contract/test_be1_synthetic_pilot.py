"""Source-level boundaries, guard probes and typed-decision seams; never an HTTP/DB flow test.

Guard cases execute only the actual consent-denial clause extracted from the named function,
with the typed-eligibility seam replaced by a spy. The seam itself (`eligibility_ready`) is
covered separately with replaced lookups. Authority, SQL, transactions, and the complete flow
are NOT tested here; the chain create profile -> ... -> append stroke is NOT_RUN until T12.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from sketch2life.domain.eligibility import (
    BASIS_VERSION,
    EligibilityBasis,
    EligibilityDecision,
    EligibilityReason,
    EligibilityScope,
    SyntheticEligibilityProof,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import ClassroomSessionModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.routers import be1_common
from sqlalchemy.orm import Session

_SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
_MODULES = {
    "sketch2life.interfaces.http.be1_runtime": _SRC / "interfaces/http/be1_runtime.py",
    **{
        f"sketch2life.interfaces.http.routers.{name}": _SRC
        / "interfaces/http/routers"
        / f"{name}.py"
        for name in (
            "be1_sessions",
            "be1_canvas",
            "be1_common",
            "be1_registry",
            "be1_records",
            "be1_artifacts",
        )
    },
}
_SESSIONS = "sketch2life.interfaces.http.routers.be1_sessions"
_CANVAS = "sketch2life.interfaces.http.routers.be1_canvas"
_COMMON = "sketch2life.interfaces.http.routers.be1_common"
_RUNTIME = "sketch2life.interfaces.http.be1_runtime"
_SITES = (
    (_SESSIONS, "_transition"),
    (_SESSIONS, "admit_device"),
    (_SESSIONS, "assign_member_to_group"),
    (_SESSIONS, "start_child_turn"),
    (_RUNTIME, "get_verified_device"),
    (_CANVAS, "append_canvas_operation"),
)
_LEGAL_CANVAS = (
    "sync_canvas_operations",
    "save_checkpoint",
    "read_latest_checkpoint",
    "restore_checkpoint",
    "reconnect_canvas",
)
_Function = ast.FunctionDef | ast.AsyncFunctionDef


@lru_cache
def _tree(module: str) -> ast.Module:
    return ast.parse(_MODULES[module].read_text(encoding="utf-8"))


def _function(module: str, name: str) -> _Function:
    matches = [
        node
        for node in _tree(module).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(matches) != 1:
        raise LookupError(f"Expected exactly one function: {module}.{name}")
    return matches[0]


def _calls(node: ast.AST) -> set[str]:
    return {
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }


def _reaches_evaluator(
    module: str, name: str, visited: frozenset[tuple[str, str]] = frozenset()
) -> bool:
    """Follow function calls and from-import aliases without importing an app."""
    key = (module, name)
    if key in visited:
        return False
    visited = visited | {key}
    imports = {
        alias.asname or alias.name: (node.module, alias.name)
        for node in _tree(module).body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    local = {
        node.name
        for node in _tree(module).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for called in _calls(_function(module, name)):
        if called in imports:
            target, target_name = imports[called]
            if target == "sketch2life.domain.eligibility" and target_name == "evaluate_eligibility":
                return True
            if target in _MODULES and _reaches_evaluator(target, target_name, visited):
                return True
        elif called in local and _reaches_evaluator(module, called, visited):
            return True
    return False


def _has_effective_sql(function: _Function) -> bool:
    return any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Attribute)
        and isinstance(node.left.value, ast.Name)
        and node.left.value.id == "ConsentRecordModel"
        and node.left.attr == "state"
        and any(
            isinstance(value, ast.Constant) and value.value == "effective"
            for value in node.comparators
        )
        for node in ast.walk(function)
    )


@pytest.mark.parametrize("module,name", _SITES)
def test_selected_guard_reaches_typed_evaluator(module: str, name: str) -> None:
    assert _reaches_evaluator(module, name), (module, name)
    if name == "append_canvas_operation":
        assert "_require_group_consent" not in _calls(_function(module, name))


def _keyword_names(node: ast.AST, callee: str) -> list[set[str | None]]:
    return [
        {keyword.arg for keyword in call.keywords}
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == callee
    ]


def _keyword_values(node: ast.AST, callee: str) -> list[dict[str, str]]:
    return [
        {keyword.arg: ast.unparse(keyword.value) for keyword in call.keywords if keyword.arg}
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == callee
    ]


@pytest.mark.parametrize(
    "module,name,callee,settings_value",
    [
        (_SESSIONS, "_transition", "eligibility_all_ready", "settings"),
        (_SESSIONS, "admit_device", "eligibility_ready", "runtime.settings"),
        (_SESSIONS, "assign_member_to_group", "eligibility_ready", "runtime.settings"),
        (_SESSIONS, "start_child_turn", "eligibility_ready", "runtime.settings"),
    ],
)
def test_state_changing_sites_audit_accepted_synthetic_eligibility(
    module: str, name: str, callee: str, settings_value: str
) -> None:
    calls = _keyword_values(_function(module, name), callee)
    assert len(calls) == 1
    assert calls[0]["legal_effective"] == "consent_is_effective"
    assert calls[0]["settings"] == settings_value
    assert calls[0]["audit_action"].endswith(".synthetic_eligibility'")


@pytest.mark.parametrize(
    "module,name,settings_value",
    [
        (_RUNTIME, "get_verified_device", "runtime.settings"),
        (_CANVAS, "_require_group_eligibility", "settings"),
    ],
)
def test_per_request_sites_do_not_write_a_success_audit(
    module: str, name: str, settings_value: str
) -> None:
    calls = _keyword_values(_function(module, name), "eligibility_ready")
    assert len(calls) == 1
    assert "audit_action" not in calls[0]
    assert calls[0]["legal_effective"] == "consent_is_effective"
    assert calls[0]["settings"] == settings_value


def test_settings_reach_the_typed_gate_through_every_caller() -> None:
    append = _keyword_values(
        _function(_CANVAS, "append_canvas_operation"), "_require_group_eligibility"
    )
    assert len(append) == 1 and append[0]["settings"] == "runtime.settings"
    start = _keyword_values(_function(_SESSIONS, "start_session"), "_do_transition")
    assert len(start) == 1 and start[0]["settings"] == "runtime.settings"
    forwarded = _keyword_values(_function(_SESSIONS, "_do_transition"), "_transition")
    assert len(forwarded) == 1 and forwarded[0]["settings"] == "settings"


def test_the_legal_lookup_passed_to_the_gate_is_the_shared_function() -> None:
    from sketch2life.interfaces.http import be1_runtime
    from sketch2life.interfaces.http.routers import be1_canvas, be1_sessions

    # The monkeypatch at test_be1_postgres_api.py:316 replaces this name in be1_sessions only.
    for module in (be1_sessions, be1_canvas, be1_runtime):
        assert module.__dict__["consent_is_effective"] is be1_common.consent_is_effective


@pytest.mark.parametrize("name", _LEGAL_CANVAS)
def test_five_other_canvas_sites_keep_the_legal_helper(name: str) -> None:
    function = _function(_CANVAS, name)
    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_require_group_consent"
    ]
    assert len(calls) == 1
    assert {keyword.arg for keyword in calls[0].keywords} == {
        "organization_id",
        "session_id",
        "group_id",
        "actor",
        "action",
    }
    assert not _reaches_evaluator(_CANVAS, name)


def test_legal_canvas_helper_is_not_widened_for_append() -> None:
    assert _has_effective_sql(_function(_CANVAS, "_require_group_consent"))
    assert not _reaches_evaluator(_CANVAS, "_require_group_consent")


@pytest.mark.parametrize("name", ("update_progress", "request_help"))
def test_progress_and_help_keep_legal_only_consent(name: str) -> None:
    assert "consent_is_effective" in _calls(_function(_SESSIONS, name))
    assert not _reaches_evaluator(_SESSIONS, name)


def test_registry_and_records_do_not_gain_a_synthetic_path() -> None:
    for suffix in ("be1_registry", "be1_records"):
        module = f"sketch2life.interfaces.http.routers.{suffix}"
        for node in _tree(module).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert not _reaches_evaluator(module, node.name)
    records = "sketch2life.interfaces.http.routers.be1_records"
    assert "consent_is_effective" in _calls(_function(records, "_require_contributors_consent"))
    assert _has_effective_sql(
        _function("sketch2life.interfaces.http.routers.be1_registry", "create_profile")
    )


@pytest.mark.parametrize("name", ("upload_session_artifact", "download_session_artifact"))
def test_artifacts_keep_legal_only_sql(name: str) -> None:
    module = "sketch2life.interfaces.http.routers.be1_artifacts"
    assert _has_effective_sql(_function(module, name))
    assert not _reaches_evaluator(module, name)


class _Denied(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _AuditSink:
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    def add(self, entry: dict[str, object]) -> None:
        self.entries.append(entry)

    def commit(self) -> None:
        """The extracted audit clause has no persistence in this probe."""


def _denial_clause(module: str, name: str) -> tuple[list[ast.stmt], str]:
    """Select the narrowest actual consent denial; do not execute SQL or routes."""
    if name == "append_canvas_operation":
        name = "_require_group_eligibility"
    function = _function(module, name)
    clauses = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.If)
        and (
            "deny_pending_consent" in _calls(node)
            or (name == "get_verified_device" and "CONSENT_NOT_EFFECTIVE" in ast.unparse(node))
        )
    ]
    if not clauses:
        raise LookupError(f"Review the new guard seam for {module}.{name}")
    clause = min(clauses, key=lambda node: len(list(ast.walk(node))))
    statements: list[ast.stmt] = []
    if name == "_transition":
        statements.extend(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assign) and "eligibility_all_ready" in _calls(node)
        )
    statements.append(clause)
    return statements, name


def _probe_guard(module: str, name: str, *, synthetic_allowed: bool) -> tuple[_Denied | None, int]:
    """Run source clauses with fetched facts and evaluator/audit seams only."""
    statements, actual_name = _denial_clause(module, name)
    sink = _AuditSink()
    evaluator_calls = 0

    def eligibility_ready(*args: object, **kwargs: object) -> bool:
        """Typed-eligibility seam: the decision itself is covered by dedicated tests below."""
        nonlocal evaluator_calls
        evaluator_calls += 1
        return synthetic_allowed

    def audit(db: object, **kwargs: object) -> None:
        sink.entries.append(kwargs)

    def failure(status_code: int, code: str, message: str) -> _Denied:
        return _Denied(status_code, {"code": code, "message": message})

    def legal_lookup(*args: object, **kwargs: object) -> bool:
        return False

    record = SimpleNamespace(
        organization_id="synthetic-org",
        class_id="synthetic-class",
        session_id="synthetic-session",
        configuration={
            "purpose_ref": "synthetic-purpose",
            "pilot_run_ref": "synthetic-run",
        },
    )
    namespace: dict[str, object] = {
        "db": sink,
        "audit": audit,
        "commit": lambda db: None,
        "failure": failure,
        "HTTPException": _Denied,
        "CoreAuditEntryModel": lambda **kwargs: kwargs,
        "uuid4": lambda: "synthetic-audit",
        "consent_is_effective": legal_lookup,
        "eligibility_ready": eligibility_ready,
        "eligibility_all_ready": eligibility_ready,
        "settings": SimpleNamespace(env="test", synthetic_pilot_enabled=True),
        "runtime": SimpleNamespace(
            settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True)
        ),
        "record": record,
        "session": record,
        "organization_id": "synthetic-org",
        "session_id": "synthetic-session",
        "group_id": "synthetic-group",
        "grant_id": "synthetic-grant",
        "child_id": "synthetic-child",
        "purpose_ref": "synthetic-purpose",
        "actor": "synthetic-operator",
        "action": "synthetic-guard-probe",
        "principal": SimpleNamespace(subject="synthetic-operator"),
        "grant": SimpleNamespace(
            grant_id="synthetic-grant",
            organization_id="synthetic-org",
            session_id="synthetic-session",
            admitted_child_id="synthetic-child",
        ),
        "payload": SimpleNamespace(child_id="synthetic-child"),
        "membership": SimpleNamespace(membership_id="synthetic-member"),
        "members": [SimpleNamespace(child_id="synthetic-child")],
        "consent_id": None,
        "consent": None,
    }
    denial = deepcopy(_function(_COMMON, "deny_pending_consent"))
    assert isinstance(denial, ast.FunctionDef)
    denial.returns = None
    for argument in (*denial.args.args, *denial.args.kwonlyargs):
        argument.annotation = None
    ast_module = ast.fix_missing_locations(ast.Module(body=[denial], type_ignores=[]))
    exec(compile(ast_module, "<BE1 denial audit clause>", "exec"), namespace)
    probe = ast.fix_missing_locations(ast.Module(body=deepcopy(statements), type_ignores=[]))
    rejection = None
    try:
        exec(compile(probe, f"<BE1 {actual_name} consent clause>", "exec"), namespace)
    except _Denied as exc:
        rejection = exc
    if not synthetic_allowed:
        assert rejection is not None
        assert rejection.status_code == 409
        assert rejection.detail["code"] == "CONSENT_NOT_EFFECTIVE"
        assert any(entry.get("decision") == "denied_consent_pending" for entry in sink.entries)
    return rejection, evaluator_calls


@pytest.mark.parametrize("module,name", _SITES)
def test_valid_synthetic_basis_is_consulted_and_allowed_by_actual_guard(
    module: str,
    name: str,
) -> None:
    rejection, calls = _probe_guard(module, name, synthetic_allowed=True)
    assert rejection is None
    assert calls == 1


@pytest.mark.parametrize("module,name", _SITES)
def test_denied_typed_basis_is_consulted_and_keeps_409_audit(module: str, name: str) -> None:
    _, calls = _probe_guard(module, name, synthetic_allowed=False)
    assert calls == 1


_NOW = datetime(2026, 10, 31, 5, 0, tzinfo=UTC)
_SCOPE = EligibilityScope(
    "synthetic-org", "synthetic-class", "synthetic-child", "synthetic-purpose"
)


class _Db:
    """Collects added rows; any commit means the eligibility seam overstepped."""

    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, row: object) -> None:
        self.added.append(row)

    def commit(self) -> None:
        raise AssertionError("the eligibility seam must not commit")


def _proof(**changes: object) -> SyntheticEligibilityProof:
    base = SyntheticEligibilityProof(
        evidence_id="synthetic-evidence-v1",
        scope=_SCOPE,
        run_ref="synthetic-run",
        issued_at=_NOW - timedelta(minutes=1),
        expires_at=_NOW + timedelta(minutes=10),
        session_id="synthetic-session",
    )
    return replace(base, **changes)  # type: ignore[arg-type]


def _session(**configuration: object) -> ClassroomSessionModel:
    values: dict[str, object] = {
        "purpose_ref": "synthetic-purpose",
        "pilot_run_ref": "synthetic-run",
    }
    values.update(configuration)
    return cast(
        ClassroomSessionModel,
        SimpleNamespace(
            organization_id="synthetic-org",
            class_id="synthetic-class",
            session_id="synthetic-session",
            configuration=values,
        ),
    )


def _settings(env: str = "test", enabled: bool = True) -> Settings:
    return cast(Settings, SimpleNamespace(env=env, synthetic_pilot_enabled=enabled))


def _legal(result: bool) -> Callable[..., bool]:
    def lookup(db: object, **kwargs: object) -> bool:
        return result

    return lookup


def _wire(
    monkeypatch: pytest.MonkeyPatch,
    origin: str | None,
    proof: SyntheticEligibilityProof | None,
) -> list[dict[str, object]]:
    seen: list[dict[str, object]] = []

    def load_origin(db: object, **kwargs: object) -> str | None:
        seen.append(dict(kwargs))
        return origin

    def load_proof(db: object, **kwargs: object) -> SyntheticEligibilityProof | None:
        seen.append(dict(kwargs))
        return proof

    monkeypatch.setattr(be1_common, "load_profile_origin", load_origin)
    monkeypatch.setattr(be1_common, "load_synthetic_proof", load_proof)
    return seen


def _decide(
    *,
    session: ClassroomSessionModel | None = None,
    legal: bool = False,
    settings: Settings | None = None,
) -> EligibilityDecision:
    return be1_common.eligibility_decision(
        cast(Session, _Db()),
        session=session or _session(),
        child_id="synthetic-child",
        legal_effective=_legal(legal),
        settings=settings,
        now=_NOW,
    )


def test_valid_synthetic_facts_are_fetched_with_the_exact_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _wire(monkeypatch, "SYNTHETIC_DEV", _proof())
    decision = _decide(settings=_settings())
    assert decision.basis is EligibilityBasis.SYNTHETIC_DEV
    assert decision.evidence_id == "synthetic-evidence-v1"
    assert decision.basis_version == BASIS_VERSION
    assert seen[0] == {
        "organization_id": "synthetic-org",
        "class_id": "synthetic-class",
        "child_id": "synthetic-child",
    }
    assert seen[1] == {**seen[0], "purpose_ref": "synthetic-purpose"}


@pytest.mark.parametrize(
    "settings,session,proof,reason",
    [
        (None, _session(), _proof(), EligibilityReason.ENVIRONMENT_DENIED),
        (_settings(enabled=False), _session(), _proof(), EligibilityReason.PILOT_DISABLED),
        (_settings(env="production"), _session(), _proof(), EligibilityReason.ENVIRONMENT_DENIED),
        (_settings(env="staging"), _session(), _proof(), EligibilityReason.ENVIRONMENT_DENIED),
        (_settings(), _session(pilot_run_ref=None), _proof(), EligibilityReason.RUN_REQUIRED),
        (_settings(), _session(pilot_run_ref=123), _proof(), EligibilityReason.RUN_REQUIRED),
        (_settings(), _session(pilot_run_ref="other"), _proof(), EligibilityReason.RUN_MISMATCH),
        (_settings(), _session(), None, EligibilityReason.PROOF_REQUIRED),
        (
            _settings(),
            _session(),
            _proof(revoked_at=_NOW - timedelta(seconds=1)),
            EligibilityReason.PROOF_REVOKED,
        ),
        (_settings(), _session(), _proof(expires_at=_NOW), EligibilityReason.PROOF_EXPIRED),
    ],
)
def test_synthetic_profile_is_denied_unless_every_current_fact_holds(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings | None,
    session: ClassroomSessionModel,
    proof: SyntheticEligibilityProof | None,
    reason: EligibilityReason,
) -> None:
    _wire(monkeypatch, "SYNTHETIC_DEV", proof)
    decision = _decide(session=session, settings=settings)
    assert decision.basis is EligibilityBasis.DENIED
    assert decision.reason is reason


def test_pilot_run_comes_only_from_the_server_session_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _wire(monkeypatch, "SYNTHETIC_DEV", _proof(run_ref="synthetic-client-run"))
    decision = _decide(settings=_settings())
    assert decision.reason is EligibilityReason.RUN_MISMATCH


@pytest.mark.parametrize("origin", ["REAL", "LEGACY_UNCLASSIFIED"])
def test_legal_profiles_keep_the_effective_consent_lookup(
    monkeypatch: pytest.MonkeyPatch, origin: str
) -> None:
    _wire(monkeypatch, origin, None)
    granted = _decide(legal=True)
    assert granted.basis is EligibilityBasis.LEGAL_CONSENT
    assert granted.evidence_id is None
    denied = _decide(legal=False)
    assert denied.basis is EligibilityBasis.DENIED
    assert denied.reason is EligibilityReason.LEGAL_CONSENT_NOT_EFFECTIVE


@pytest.mark.parametrize("origin", ["REAL", "LEGACY_UNCLASSIFIED", None])
def test_the_proof_table_is_not_consulted_for_legal_or_missing_profiles(
    monkeypatch: pytest.MonkeyPatch, origin: str | None
) -> None:
    # The legal path must not depend on the proof table: a read failure there cannot turn a
    # legitimate request into an error. (The pure evaluator still denies a stray proof on a
    # legal profile; that is covered by the domain unit tests.)
    def forbidden(db: object, **kwargs: object) -> SyntheticEligibilityProof | None:
        raise AssertionError("the proof table must not be read for a legal profile")

    _wire(monkeypatch, origin, None)
    monkeypatch.setattr(be1_common, "load_synthetic_proof", forbidden)
    assert _decide(legal=True, settings=_settings()).basis is EligibilityBasis.LEGAL_CONSENT
    assert _decide(legal=False, settings=_settings()).basis is EligibilityBasis.DENIED


def test_a_legal_effective_result_never_mixes_with_a_synthetic_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _wire(monkeypatch, "SYNTHETIC_DEV", _proof())
    decision = _decide(legal=True, settings=_settings())
    assert decision.reason is EligibilityReason.CONFLICTING_BASIS


def test_a_missing_profile_keeps_the_pre_existing_legal_only_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No active profile row (for example archived after admission): the old gate only looked at
    # the effective consent record, and this still holds. It can never become synthetic.
    _wire(monkeypatch, None, None)
    granted = _decide(legal=True, settings=_settings())
    assert granted.basis is EligibilityBasis.LEGAL_CONSENT
    denied = _decide(legal=False, settings=_settings())
    assert denied.basis is EligibilityBasis.DENIED
    assert denied.reason is EligibilityReason.LEGAL_CONSENT_NOT_EFFECTIVE


def test_a_synthetic_proof_must_name_the_session_it_is_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _wire(monkeypatch, "SYNTHETIC_DEV", _proof(session_id=None))
    decision = _decide(settings=_settings())
    assert decision.basis is EligibilityBasis.DENIED
    assert decision.reason is EligibilityReason.PROOF_REQUIRED


def test_a_proof_for_another_session_does_not_count(monkeypatch: pytest.MonkeyPatch) -> None:
    _wire(monkeypatch, "SYNTHETIC_DEV", _proof(session_id="synthetic-other-session"))
    decision = _decide(settings=_settings())
    assert decision.reason is EligibilityReason.SESSION_MISMATCH


def test_the_shared_legal_lookup_treats_a_missing_purpose_as_not_effective() -> None:
    # No query is issued: the stand-in session would fail on any attribute access.
    assert (
        be1_common.consent_is_effective(
            cast(Session, object()),
            organization_id="synthetic-org",
            class_id="synthetic-class",
            child_id="synthetic-child",
            purpose_ref=None,
        )
        is False
    )


def _ready(
    db: _Db, audit_action: str | None, settings: Settings | None = None, legal: bool = False
) -> bool:
    return be1_common.eligibility_ready(
        cast(Session, db),
        session=_session(),
        child_id="synthetic-child",
        legal_effective=_legal(legal),
        settings=settings,
        actor="synthetic-operator",
        audit_action=audit_action,
    )


def test_accepted_synthetic_decision_is_audited_only_when_the_caller_names_an_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    proof = _proof(issued_at=now - timedelta(minutes=1), expires_at=now + timedelta(minutes=5))
    _wire(monkeypatch, "SYNTHETIC_DEV", proof)
    quiet = _Db()
    assert _ready(quiet, None, _settings()) is True
    assert quiet.added == []
    audited = _Db()
    assert _ready(audited, "turn.start.synthetic_eligibility", _settings()) is True
    (entry,) = audited.added
    assert isinstance(entry, CoreAuditEntryModel)
    assert entry.action == "turn.start.synthetic_eligibility"
    assert entry.resource_type == "synthetic_eligibility_proof"
    assert entry.resource_id == "synthetic-evidence-v1"
    assert entry.decision == f"allowed_synthetic_dev:{BASIS_VERSION}"
    assert entry.actor_ref == "synthetic-operator"


def test_denied_and_legal_decisions_write_no_synthetic_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _wire(monkeypatch, "SYNTHETIC_DEV", None)
    denied = _Db()
    assert _ready(denied, "turn.start.synthetic_eligibility", _settings()) is False
    assert denied.added == []
    _wire(monkeypatch, "REAL", None)
    legal = _Db()
    assert _ready(legal, "turn.start.synthetic_eligibility", _settings(), legal=True) is True
    assert legal.added == []


def _wire_by_child(
    monkeypatch: pytest.MonkeyPatch, proofs: dict[str, SyntheticEligibilityProof | None]
) -> None:
    def load_origin(db: object, **kwargs: object) -> str | None:
        return "SYNTHETIC_DEV" if kwargs["child_id"] in proofs else None

    def load_proof(db: object, **kwargs: object) -> SyntheticEligibilityProof | None:
        return proofs.get(str(kwargs["child_id"]))

    monkeypatch.setattr(be1_common, "load_profile_origin", load_origin)
    monkeypatch.setattr(be1_common, "load_synthetic_proof", load_proof)


def _all_ready(db: _Db, child_ids: list[str]) -> bool:
    return be1_common.eligibility_all_ready(
        cast(Session, db),
        session=_session(),
        child_ids=child_ids,
        legal_effective=_legal(False),
        settings=_settings(),
        actor="synthetic-operator",
        audit_action="session.start.synthetic_eligibility",
    )


def _live_proof(child_id: str) -> SyntheticEligibilityProof:
    now = datetime.now(UTC)
    scope = EligibilityScope("synthetic-org", "synthetic-class", child_id, "synthetic-purpose")
    return SyntheticEligibilityProof(
        evidence_id=f"evidence-{child_id}",
        scope=scope,
        run_ref="synthetic-run",
        issued_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=5),
        session_id="synthetic-session",
    )


def test_start_audits_every_accepted_child_only_when_all_children_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _wire_by_child(
        monkeypatch, {"child-a": _live_proof("child-a"), "child-b": _live_proof("child-b")}
    )
    accepted = _Db()
    assert _all_ready(accepted, ["child-a", "child-b"]) is True
    rows = [cast(CoreAuditEntryModel, row) for row in accepted.added]
    assert sorted(row.resource_id for row in rows) == ["evidence-child-a", "evidence-child-b"]


def test_a_denied_child_leaves_no_allowed_audit_for_the_others(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # child-b has no profile at all, so the whole Start must be refused without any success audit.
    _wire_by_child(monkeypatch, {"child-a": _live_proof("child-a")})
    refused = _Db()
    assert _all_ready(refused, ["child-a", "child-b"]) is False
    assert refused.added == []
    reversed_order = _Db()
    assert _all_ready(reversed_order, ["child-b", "child-a"]) is False
    assert reversed_order.added == []
