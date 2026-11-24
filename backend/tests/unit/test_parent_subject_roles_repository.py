"""FEAT-087 M2: the adult's subject roles are stored with the subject confirmation.

Statement-recording session, no database. The final roles live in the understanding
``result_snapshot`` (existing JSONB), so no migration is needed.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.parent_subject_roles import normalize_worker_candidate
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"


class _Session:
    def __init__(self) -> None:
        self.statements: list[Any] = []
        self.commits = 0

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        return None

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:  # pragma: no cover - only on failure paths
        raise AssertionError("unexpected rollback")

    def writes_to(self, table: str) -> list[Any]:
        return [
            s for s in self.statements if getattr(getattr(s, "table", None), "name", "") == table
        ]


def _candidate_v2() -> dict[str, Any]:
    return normalize_worker_candidate(
        {
            "understanding_schema": "sketch2life.drawing-understanding.v2",
            "main_subject": {
                "label": "con rùa",
                "visible_features": ["mai ba ô tròn"],
                "facing": "right",
                "box": [2, 6, 12, 16],
            },
            "secondary_subjects": [
                {"label": "chiếc lá", "visible_features": [], "box": [14, 9, 19, 15]}
            ],
            "confidence": 0.8,
            "candidate_subject": "con rùa",
            "visible_features": ["mai ba ô tròn"],
        }
    )


def _repository(monkeypatch: pytest.MonkeyPatch, candidate: dict[str, Any]):
    session = _Session()
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    stored: dict[str, Any] = {}
    run = {"run_id": _RUN_ID, "run_state": "SUBJECT_REVIEW", "version": 3}
    monkeypatch.setattr(repository, "_owned_run", lambda *_a, **_k: dict(run))
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_k: None)
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **_k: None)
    monkeypatch.setattr(repository, "_refuse_purged", lambda *_a, **_k: None)
    monkeypatch.setattr(
        repository, "_store_idempotency_receipt", lambda **kwargs: stored.update(kwargs) or "rc-1"
    )
    monkeypatch.setattr(
        repository,
        "_latest_understanding",
        lambda _run_id: {
            "revision_no": 1,
            "run_input_id": "input-1",
            "confidence": 0.8,
            "raw_body_sha256": "a" * 64,
            "result_snapshot": {"result": candidate},
        },
    )
    return repository, session, stored


def _params(statement: Any) -> dict[str, Any]:
    dialect: Any = postgresql.dialect
    return dict(statement.compile(dialect=dialect()).params)


def _confirm(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": _PRINCIPAL,
        "run_id": _RUN_ID,
        "expected_understanding_revision": 1,
        "confirmed_subject": "con rùa",
        "idempotency_key": "subject-1",
    }
    values.update(overrides)
    return repository.confirm_subject(**values)


_ROLES = [
    {"entity_id": "main", "label": "con rùa", "role": "main"},
    {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
]


def test_roles_create_a_new_understanding_revision_with_approved_roles(monkeypatch) -> None:
    repository, session, stored = _repository(monkeypatch, _candidate_v2())
    revision = _confirm(repository, subject_roles=_ROLES)
    assert revision == 2
    (insert,) = session.writes_to("understanding_revisions")
    snapshot = _params(insert)["result_snapshot"]["result"]
    assert snapshot["approved_roles"] == _ROLES
    assert snapshot["main_subject"]["box"] == [2, 6, 12, 16]
    assert stored["response_body"] == {"decision": "CONFIRMED", "understanding_revision": 2}
    assert "subject_roles" in str(stored["fingerprint"]) or stored["fingerprint"]
    assert session.commits == 1


def test_without_roles_nothing_is_approved_and_no_new_revision(monkeypatch) -> None:
    repository, session, stored = _repository(monkeypatch, _candidate_v2())
    assert _confirm(repository) == 1
    assert session.writes_to("understanding_revisions") == []
    assert stored["response_body"]["understanding_revision"] == 1


def test_a_rename_without_roles_keeps_the_v2_main_subject_coherent(monkeypatch) -> None:
    repository, session, _ = _repository(monkeypatch, _candidate_v2())
    assert _confirm(repository, confirmed_subject="rùa nhỏ") == 2
    (insert,) = session.writes_to("understanding_revisions")
    result = _params(insert)["result_snapshot"]["result"]
    assert result["main_subject"]["label"] == "rùa nhỏ"
    assert "approved_roles" not in result  # no roles were approved


def test_invalid_roles_are_refused_before_any_write(monkeypatch) -> None:
    repository, session, _ = _repository(monkeypatch, _candidate_v2())
    bad = [{"entity_id": "main", "label": "con rùa", "role": "main"}]  # misses sec-1
    with pytest.raises(ParentStoryRunError) as refused:
        _confirm(repository, subject_roles=bad)
    assert (refused.value.status_code, refused.value.code) == (422, "PARENT_SUBJECT_ROLES_INVALID")
    assert session.writes_to("understanding_revisions") == []


def test_roles_whose_main_label_differs_from_the_confirmed_subject_are_refused(
    monkeypatch,
) -> None:
    repository, _, _ = _repository(monkeypatch, _candidate_v2())
    with pytest.raises(ParentStoryRunError) as refused:
        _confirm(repository, confirmed_subject="khác", subject_roles=_ROLES)
    assert refused.value.code == "PARENT_SUBJECT_ROLES_INVALID"


def test_roles_cannot_be_sent_for_a_v1_understanding(monkeypatch) -> None:
    legacy = {
        "candidate_subject": "con rùa",
        "visible_features": ["mai"],
        "confidence": 0.8,
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }
    repository, _, _ = _repository(monkeypatch, legacy)
    with pytest.raises(ParentStoryRunError) as refused:
        _confirm(repository, subject_roles=_ROLES)
    assert refused.value.code == "PARENT_SUBJECT_ROLES_INVALID"


def test_the_fingerprint_changes_when_roles_change(monkeypatch) -> None:
    repository, _, stored_a = _repository(monkeypatch, _candidate_v2())
    _confirm(repository, subject_roles=_ROLES)
    repository, _, stored_b = _repository(monkeypatch, _candidate_v2())
    other = [dict(_ROLES[0]), {**_ROLES[1], "role": "excluded"}]
    _confirm(repository, subject_roles=other)
    repository, _, stored_c = _repository(monkeypatch, _candidate_v2())
    _confirm(repository)
    assert len({stored_a["fingerprint"], stored_b["fingerprint"], stored_c["fingerprint"]}) == 3
