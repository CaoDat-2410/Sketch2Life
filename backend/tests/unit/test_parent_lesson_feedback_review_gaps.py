# ruff: noqa: E501, F811, SIM117, B023
"""Missing unit tests for E6 T-FBK1 named in IMPL_REVIEW_E_E6_R1_20261125.md and E6_PROMPT.md."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.lesson_library import feedback as feedback_module
from sketch2life.infrastructure.lesson_library.feedback import ParentLessonFeedbackService
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError


def _fake_admin(db: Any, *, subject: str = "parent-1") -> SimpleNamespace:
    return SimpleNamespace(
        db=db,
        principal=SimpleNamespace(subject=subject),
        audit=lambda *_args, **_kwargs: None,
        notify=lambda *_args, **_kwargs: None,
    )


class _DummyDb:
    def __init__(self, *, dialect: str = "sqlite") -> None:
        self._dialect = dialect
        self.rolled_back = False
        self.committed = False
        self.added: list[Any] = []

    def get_bind(self) -> Any:
        return SimpleNamespace(dialect=SimpleNamespace(name=self._dialect))

    def rollback(self) -> None:
        self.rolled_back = True

    def commit(self) -> None:
        self.committed = True

    def add(self, item: Any) -> None:
        self.added.append(item)

    def execute(self, *_args: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))

    def scalar(self, *_args: Any, **_kwargs: Any) -> Any:
        return None


@pytest.mark.parametrize("bad_text", ["", "   ", "\n\t", "x" * 1201])
def test_submit_rejects_blank_or_oversized_feedback_text(bad_text: str) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §2 D-9 text length validation)"""
    service = ParentLessonFeedbackService(_fake_admin(_DummyDb()))

    with pytest.raises(LessonLibraryError) as caught:
        service.submit("lesson-1", bad_text, "valid-key-1")

    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_REQUEST"
    assert caught.value.field_errors == [{"field": "feedback_text", "code": "INVALID_LENGTH"}]


@pytest.mark.parametrize(
    "bad_key",
    ["", "k" * 129, "key with space", "key\nnewline", "key\x7fdel"],
)
def test_submit_rejects_malformed_idempotency_key_formats(bad_key: str) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §3 Idempotency-Key ASCII format)"""
    service = ParentLessonFeedbackService(_fake_admin(_DummyDb()))

    with pytest.raises(LessonLibraryError) as caught:
        service.submit("lesson-1", "Valid note", bad_key)

    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_REQUEST"
    assert caught.value.field_errors == [{"field": "Idempotency-Key", "code": "INVALID_FORMAT"}]


def test_submit_receipt_mismatch_rolls_back_before_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Finding 2 (mismatched-fingerprint receipt hit rolls back transaction)"""
    db = _DummyDb(dialect="postgresql")
    service = ParentLessonFeedbackService(
        _fake_admin(db),
        parent_lesson=lambda _lesson_id: {"version_id": "ver-1"},
    )
    monkeypatch.setattr(
        service,
        "_authorize_lesson",
        lambda _lesson_id: ({"organization_id": "org-1", "created_by": "teacher-1"}, "ver-1"),
    )
    monkeypatch.setattr(service, "_lock_parent_lesson", lambda *_args: None)
    monkeypatch.setattr(
        service,
        "_load_receipt",
        lambda *_args: SimpleNamespace(
            organization_id="org-1",
            request_fingerprint="0" * 64,
            response_json={"feedback_id": "t-1", "message_id": "m-1", "revision": 1},
        ),
    )

    with pytest.raises(LessonLibraryError) as caught:
        service.submit("lesson-1", "Changed body", "reused-key")

    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_IDEMPOTENCY_KEY"
    assert db.rolled_back is True


def test_submit_maps_pk_receipt_race_other_integrity_and_sqlalchemy_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §2 D-6 PK race replay, 409, 503)"""
    now = datetime.now(UTC)

    class _RaceDb(_DummyDb):
        def __init__(self, exc: Exception) -> None:
            super().__init__()
            self._exc = exc

        def commit(self) -> None:
            raise self._exc

    def _prepare_service(db: _DummyDb) -> ParentLessonFeedbackService:
        service = ParentLessonFeedbackService(
            _fake_admin(db),
            parent_lesson=lambda _lesson_id: {"version_id": "ver-1"},
        )
        monkeypatch.setattr(
            service,
            "_authorize_lesson",
            lambda _lesson_id: ({"organization_id": None, "created_by": "teacher-1"}, "ver-1"),
        )
        monkeypatch.setattr(service, "_lock_parent_lesson", lambda *_args: None)
        monkeypatch.setattr(service, "_load_receipt", lambda *_args: None)
        monkeypatch.setattr(service, "_latest_thread", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(
            service,
            "_thread_by_id",
            lambda tid: {
                "thread_id": tid,
                "lesson_id": "lesson-1",
                "version_id": "ver-1",
                "revision": 1,
                "created_by": "parent-1",
                "created_at": now,
            },
        )
        monkeypatch.setattr(
            service,
            "_message_by_id",
            lambda _mid, _tid, _subj: {"body": "Note", "created_at": now},
        )
        monkeypatch.setattr(service, "_reply_count", lambda *_args: 0)
        return service

    pk_conflict = IntegrityError(
        "insert",
        {},
        SimpleNamespace(
            sqlstate="23505",
            diag=SimpleNamespace(constraint_name="pk_be1_command_receipts"),
        ),
    )
    race_db = _RaceDb(pk_conflict)
    race_service = _prepare_service(race_db)
    expected_replay = {"contract": "ParentLessonFeedbackV1", "feedback_id": "winner-thread"}
    monkeypatch.setattr(race_service, "_replay_after_receipt_race", lambda **_kw: expected_replay)
    assert race_service.submit("lesson-1", "Note", "race-key") == expected_replay
    assert race_db.rolled_back is True

    other_db = _RaceDb(
        IntegrityError(
            "insert",
            {},
            SimpleNamespace(sqlstate="23505", diag=SimpleNamespace(constraint_name="uq_other")),
        )
    )
    other_service = _prepare_service(other_db)
    with pytest.raises(LessonLibraryError) as conflict_err:
        other_service.submit("lesson-1", "Note", "other-key")
    assert conflict_err.value.status_code == 409
    assert conflict_err.value.code == "RESOURCE_CONFLICT"
    assert other_db.rolled_back is True

    sa_db = _RaceDb(SQLAlchemyError("db outage"))
    sa_service = _prepare_service(sa_db)
    with pytest.raises(LessonLibraryError) as sa_err:
        sa_service.submit("lesson-1", "Note", "sa-key")
    assert sa_err.value.status_code == 503
    assert sa_err.value.code == "DEPENDENCY_UNAVAILABLE"
    assert sa_db.rolled_back is True


def test_rebuild_receipt_and_state_reject_corrupt_or_missing_rows_with_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Conformance (E6_PROMPT §2 D-6 corrupt receipt & missing message 503)"""
    db = _DummyDb()
    service = ParentLessonFeedbackService(_fake_admin(db))
    fingerprint = service.command_fingerprint("lesson-1", "Note")

    bad_receipt = SimpleNamespace(
        organization_id="platform",
        request_fingerprint=fingerprint,
        response_json={"feedback_id": "t-1"},
    )
    with pytest.raises(LessonLibraryError) as bad_json_err:
        service._rebuild_receipt(
            bad_receipt,  # type: ignore[arg-type]
            subject="parent-1",
            lesson_id="lesson-1",
            organization_id="platform",
            fingerprint=fingerprint,
        )
    assert bad_json_err.value.status_code == 503
    assert bad_json_err.value.code == "DEPENDENCY_UNAVAILABLE"

    monkeypatch.setattr(
        service,
        "_authorize_lesson",
        lambda _lesson_id: ({"organization_id": "platform"}, "ver-1"),
    )
    monkeypatch.setattr(service, "_latest_thread", lambda *_args: {"thread_id": "t-1"})
    with pytest.raises(LessonLibraryError) as missing_msg_err:
        service.state("lesson-1")
    assert missing_msg_err.value.status_code == 503
    assert missing_msg_err.value.code == "DEPENDENCY_UNAVAILABLE"


def test_replies_maps_invalid_cursor_to_400_and_sqlalchemy_error_to_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E6_R1_20261125.md Finding 3 (replies INVALID_CURSOR -> 400 INVALID_REQUEST & SQLAlchemyError -> 503)"""
    db = _DummyDb()
    service = ParentLessonFeedbackService(_fake_admin(db))
    monkeypatch.setattr(
        service,
        "_authorize_lesson",
        lambda _lesson_id: ({"organization_id": "platform"}, "ver-1"),
    )

    monkeypatch.setattr(
        feedback_module,
        "apply_datetime_cursor",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AdminError("INVALID_CURSOR", 400)),
    )
    with pytest.raises(LessonLibraryError) as cursor_err:
        service.replies("lesson-1", limit=10, cursor="tampered")
    assert cursor_err.value.status_code == 400
    assert cursor_err.value.code == "INVALID_REQUEST"
    assert cursor_err.value.field_errors == [{"field": "cursor", "code": "INVALID_FORMAT"}]

    monkeypatch.setattr(
        feedback_module,
        "apply_datetime_cursor",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(SQLAlchemyError("db lost")),
    )
    with pytest.raises(LessonLibraryError) as db_err:
        service.replies("lesson-1", limit=10, cursor=None)
    assert db_err.value.status_code == 503
    assert db_err.value.code == "DEPENDENCY_UNAVAILABLE"
    assert db.rolled_back is True
