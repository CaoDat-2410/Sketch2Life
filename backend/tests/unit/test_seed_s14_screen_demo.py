"""Unit checks for the service-backed S14 synthetic web-screen seed."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from tools.seed import data, s14_screen_demo_data
from tools.seed import s14_screen_demo as stage
from tools.seed.stage_common import StageError


def _session(mock: MagicMock) -> Session:
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = False
    return cast(Session, mock)


def session_factory() -> Session:
    mock = MagicMock()
    mock.scalar.return_value = None
    return _session(mock)


def test_catalog_already_submitted_is_left_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    session.scalar.return_value = stage.SUBMIT_KEY
    service = MagicMock()
    monkeypatch.setattr(stage, "AdminCatalogService", lambda _admin: service)
    stage.seed_catalog(lambda: _session(session))
    service.write.assert_not_called()


def test_catalog_uses_fixed_keys_and_submits(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MagicMock()
    service.write.return_value = {
        "state": "draft",
        "record_id": "record",
        "version": 1,
        "revision": 1,
        "content_hash": "a" * 64,
    }
    service.action.return_value = {"state": "submitted"}
    monkeypatch.setattr(stage, "AdminCatalogService", lambda _admin: service)
    stage.seed_catalog(session_factory)

    service.write.assert_called_once_with(stage.PAYLOAD, stage.CREATE_KEY)
    service.action.assert_called_once_with(
        "record",
        {
            "action": "submit",
            "version": 1,
            "content_hash": "a" * 64,
            "dimension": None,
            "decision": None,
            "reason": None,
        },
        1,
        stage.SUBMIT_KEY,
    )


def test_catalog_failure_has_safe_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MagicMock()
    service.write.side_effect = ValueError("sensitive detail")
    monkeypatch.setattr(stage, "AdminCatalogService", lambda _admin: service)
    with pytest.raises(StageError, match="^S14_CATALOG_FAILED$"):
        stage.seed_catalog(session_factory)


def test_catalog_rejects_unexpected_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MagicMock()
    service.write.return_value = {"state": "published"}
    monkeypatch.setattr(stage, "AdminCatalogService", lambda _admin: service)
    with pytest.raises(StageError, match="^S14_CATALOG_DRAFT_UNEXPECTED$"):
        stage.seed_catalog(session_factory)
    service.action.assert_not_called()


def test_manager_consent_uses_pending_route_and_replays_without_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        organization_id=s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
        class_id=s14_screen_demo_data.CONSENT_CLASS_ID,
        age_months=72,
    )
    session = MagicMock()
    session.get.return_value = profile
    session.scalars.return_value.all.return_value = []

    def factory() -> Session:
        return _session(session)

    handler = MagicMock(return_value={"state": "pending", "effective": False})
    monkeypatch.setattr(stage, "record_consent", handler)
    stage.seed_manager_consent(factory)

    call = handler.call_args.args
    assert call[0] == s14_screen_demo_data.CONSENT_ORGANIZATION_ID
    assert call[1] == s14_screen_demo_data.CONSENT_CLASS_ID
    assert call[2].child_id == stage.CONSENT_CHILD_ID
    assert call[2].purpose_ref == s14_screen_demo_data.CONSENT_PURPOSE_REF
    assert call[2].evidence_ref is None
    assert call[3].subject == s14_screen_demo_data.CONSENT_ACTOR_SUBJECT
    assert call[4] is session

    session.scalars.return_value.all.return_value = [
        SimpleNamespace(state="pending", evidence_ref=None)
    ]
    stage.seed_manager_consent(factory)
    handler.assert_called_once()


def test_manager_consent_refuses_existing_non_pending_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.get.return_value = SimpleNamespace(
        organization_id=s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
        class_id=s14_screen_demo_data.CONSENT_CLASS_ID,
        age_months=72,
    )
    session.scalars.return_value.all.return_value = [
        SimpleNamespace(state="revoked", evidence_ref=None)
    ]

    def factory() -> Session:
        return _session(session)

    handler = MagicMock()
    monkeypatch.setattr(stage, "record_consent", handler)
    with pytest.raises(StageError, match="^S14_CONSENT_EXISTING_STATE_UNEXPECTED$"):
        stage.seed_manager_consent(factory)
    handler.assert_not_called()
    session.rollback.assert_called_once()


def test_moderation_uses_normal_submit_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MagicMock()
    service.write.return_value = {
        "review_state": "DRAFT",
        "lesson_id": "lesson",
        "version_id": "version",
        "content_hash": "b" * 64,
        "revision": 1,
    }
    service.action.return_value = {"review_state": "PENDING_REVIEW"}
    monkeypatch.setattr(stage, "PlatformLessonService", lambda _admin: service)
    stage.seed_moderation(session_factory)

    service.write.assert_called_once_with(
        s14_screen_demo_data.PLATFORM_LESSON_CONTENT.model_dump(mode="json"),
        stage.LESSON_CREATE_KEY,
    )
    action = service.action.call_args.args
    assert action[0] == "lesson"
    assert action[1]["action"] == "submit"
    assert action[1]["version_id"] == "version"
    assert action[1]["content_hash"] == "b" * 64
    assert action[2:] == (1, stage.LESSON_SUBMIT_KEY)


def test_notification_uses_fixed_command_and_generic_demo_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.scalar.return_value = None
    session.get.return_value = None
    service = MagicMock()
    service.command.side_effect = lambda _op, _key, _payload, execute: execute()
    monkeypatch.setattr(stage, "PlatformAdminService", lambda _session, _principal: service)

    def factory() -> Session:
        return _session(session)

    stage.seed_notification(factory)
    service.identity.assert_called_once_with()
    service.command.assert_called_once()
    assert service.command.call_args.args[:2] == (
        s14_screen_demo_data.NOTIFICATION_OPERATION,
        s14_screen_demo_data.NOTIFICATION_KEY,
    )
    service.notify.assert_called_once_with(
        data.PLATFORM_ADMIN_SUBJECT,
        s14_screen_demo_data.NOTIFICATION_KIND,
        s14_screen_demo_data.NOTIFICATION_RESOURCE,
    )


def test_demo_content_is_vietnamese_synthetic_and_for_ages_six_to_eight() -> None:
    lesson = s14_screen_demo_data.PLATFORM_LESSON_CONTENT
    assert lesson.locale == "vi-VN"
    assert lesson.target_age_band_ref == "age-72-107-months-v1"
    assert lesson.target_age_band_version == 1
    assert "khu vườn" in lesson.title.casefold()
    assert lesson.script_following_allowed is False
    assert all(activity.safety_notes for activity in lesson.activities)
    assert s14_screen_demo_data.EXPECTED["be1_consent_records_s14"] == 0
    assert s14_screen_demo_data.EXPECTED["notification_inbox_items_s14"] == 1


def test_consent_child_is_an_existing_synthetic_profile_in_the_seeded_class() -> None:
    child = next(
        row
        for row in data.managed_profile_rows()
        if row["child_id"] == stage.CONSENT_CHILD_ID
    )
    assert child["organization_id"] == s14_screen_demo_data.CONSENT_ORGANIZATION_ID
    assert child["class_id"] == s14_screen_demo_data.CONSENT_CLASS_ID


def test_screen_failure_does_not_stop_other_screens(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock()
    monkeypatch.setattr(stage, "count_s14_rows", lambda _connection: {})
    monkeypatch.setattr(stage, "create_core_session_factory", lambda _engine: session_factory)
    called = []

    def fail(_factory):
        raise StageError("S14_MODERATION_FAILED")

    def succeed(_factory):
        called.append(True)

    monkeypatch.setattr(stage, "seed_catalog", succeed)
    monkeypatch.setattr(stage, "seed_moderation", fail)
    monkeypatch.setattr(stage, "seed_notification", succeed)
    result = stage.run_s14(engine)
    assert len(called) == 2
    assert result.after["screen_failures_s14"] == 1
    assert "S14_MODERATION_FAILED" in result.notes
    assert not result.ok

