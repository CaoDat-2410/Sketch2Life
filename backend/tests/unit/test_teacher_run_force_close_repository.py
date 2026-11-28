from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.manager_story_run_scope import (
    ManagerStoryRunScopeDecision,
)
from sketch2life.application.ports.story_run_force_close import (
    ManagerStoryRunForceCloseFailure,
)
from sketch2life.domain.teacher_run_force_close import (
    build_force_close_receipt_identity,
)
from sketch2life.infrastructure.persistence.manager_story_run_scope import (
    SqlManagerStoryRunScope,
)
from sketch2life.infrastructure.story_teacher.manager_story_run_force_close_repository import (
    SqlManagerStoryRunForceCloseRepository,
    _replay_receipt,
)

RUN_ID = "4be7a402-dbab-4977-bd1a-63d4b580cf08"


class _MappingsResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _MappingsResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _SelectSession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.statement: Any = None

    def execute(self, statement: Any) -> _MappingsResult:
        self.statement = statement
        return _MappingsResult(self.rows)


class _ScalarRows:
    def __init__(self, rows: Iterable[object]) -> None:
        self._rows = tuple(rows)

    def all(self) -> list[object]:
        return list(self._rows)


class _ScopeSession:
    def __init__(
        self,
        *,
        identity: object,
        organization: object,
        assignments: Iterable[object],
    ) -> None:
        self._scalar_values = iter((identity, organization))
        self._assignments = tuple(assignments)

    def scalar(self, _statement: Any) -> object:
        return next(self._scalar_values)

    def scalars(self, _statement: Any) -> _ScalarRows:
        return _ScalarRows(self._assignments)


def _identity(*, reason: str = "manager reason"):
    return build_force_close_receipt_identity(
        principal_ref="manager-subject",
        organization_id="org-1",
        run_id=RUN_ID,
        expected_revision=1,
        reason=reason,
        idempotency_key="key-1",
    )


def _receipt(*, fingerprint: str | None = None) -> dict[str, Any]:
    return {
        "request_fingerprint_sha256": fingerprint or _identity().request_fingerprint_sha256,
        "state": "FINAL",
        "response_status": 200,
        "resource_ref": RUN_ID,
        "response_body": {
            "contract": "ManagerForceClosedStoryRunV1",
            "run_id": RUN_ID,
            "run_state": "ABANDONED",
            "revision": 2,
        },
    }


def test_active_conflict_selects_only_metadata_fields() -> None:
    session = _SelectSession(
        [{"run_id": RUN_ID, "run_state": "SCRIPT_REVIEW", "revision": 4}]
    )
    result = SqlManagerStoryRunForceCloseRepository(session).find_active_conflict(
        organization_id="org-1",
        teacher_ref="teacher-account",
    )
    assert result is not None
    assert (result.run_id, result.run_state, result.revision) == (
        RUN_ID,
        "SCRIPT_REVIEW",
        4,
    )
    assert tuple(column.name for column in session.statement.selected_columns) == (
        "run_id",
        "run_state",
        "revision",
    )


def test_matching_final_receipt_replays_only_the_minimal_projection() -> None:
    result = _replay_receipt(
        _receipt(),
        expected_fingerprint=_identity().request_fingerprint_sha256,
        run_id=RUN_ID,
    )
    assert (result.run_id, result.revision) == (RUN_ID, 2)
    assert set(_receipt()["response_body"]) == {  # type: ignore[arg-type]
        "contract",
        "run_id",
        "run_state",
        "revision",
    }


def test_changed_payload_and_corrupt_receipt_fail_without_returning_receipt_data() -> None:
    with pytest.raises(ManagerStoryRunForceCloseFailure) as changed:
        _replay_receipt(
            _receipt(),
            expected_fingerprint=_identity(reason="other reason").request_fingerprint_sha256,
            run_id=RUN_ID,
        )
    assert (changed.value.status_code, changed.value.code) == (400, "INVALID_IDEMPOTENCY_KEY")

    malformed = _receipt()
    malformed["response_body"] = {"run_id": RUN_ID, "reason": "never return"}
    with pytest.raises(ManagerStoryRunForceCloseFailure) as corrupt:
        _replay_receipt(
            malformed,
            expected_fingerprint=_identity().request_fingerprint_sha256,
            run_id=RUN_ID,
        )
    assert (corrupt.value.status_code, corrupt.value.code) == (409, "RESOURCE_CONFLICT")
    assert "never return" not in str(corrupt.value)


def test_manager_scope_requires_active_organization_and_org_wide_role() -> None:
    manager = SimpleNamespace(
        state="active", issuer="synthetic-issuer", account_role="school_manager"
    )
    school_admin = SimpleNamespace(role="school_admin", class_id=None)
    active = _ScopeSession(
        identity=manager,
        organization=SimpleNamespace(state="active"),
        assignments=[school_admin],
    )
    authorized = SqlManagerStoryRunScope(active).authorize_manager(
        principal_subject="manager-subject",
        principal_issuer="synthetic-issuer",
        organization_id="org-1",
        lock=True,
    )
    assert authorized.decision is ManagerStoryRunScopeDecision.AUTHORIZED
    assert authorized.audit_actor_ref is not None
    assert "manager-subject" not in authorized.audit_actor_ref

    inactive = _ScopeSession(
        identity=manager,
        organization=SimpleNamespace(state="inactive"),
        assignments=[school_admin],
    )
    denied = SqlManagerStoryRunScope(inactive).authorize_manager(
        principal_subject="manager-subject",
        principal_issuer="synthetic-issuer",
        organization_id="org-1",
        lock=True,
    )
    assert denied.decision is ManagerStoryRunScopeDecision.OUT_OF_SCOPE


def test_assigned_teacher_is_in_scope_but_not_authorized_as_manager() -> None:
    session = _ScopeSession(
        identity=SimpleNamespace(
            state="active", issuer="synthetic-issuer", account_role="teacher"
        ),
        organization=SimpleNamespace(state="active"),
        assignments=[SimpleNamespace(role="teacher", class_id="class-1")],
    )
    denied = SqlManagerStoryRunScope(session).authorize_manager(
        principal_subject="teacher-subject",
        principal_issuer="synthetic-issuer",
        organization_id="org-1",
        lock=False,
    )
    assert denied.decision is ManagerStoryRunScopeDecision.ROLE_DENIED
