from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryRunCancelRequestV1,
)
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = UUID("22222222-2222-4222-8222-222222222222")


def _record() -> SimpleNamespace:
    return SimpleNamespace(
        run_id=str(_RUN_ID),
        run_revision=8,
        run_state="DELETE_PENDING",
        parent_profile_id=UUID("11111111-1111-4111-8111-111111111111"),
        profile_revision_ref=UUID("33333333-3333-4333-8333-333333333333"),
        context_revision=1,
        context_confirmed=False,
        context_snapshot={
            "schema_version": "sketch2life.parent-context.v1",
            "profile_revision_ref": "33333333-3333-4333-8333-333333333333",
            "age_months": 72,
            "interests_summary": "",
            "topic": "",
            "adult_confirmed_idea": "",
        },
        context_snapshot_sha256="a" * 64,
        lesson_pin_snapshot=None,
        current_input_revision=1,
        understanding_revision=None,
        subject_label=None,
        candidate=None,
        story_revision_id=None,
        story_revision_no=None,
        story_status=None,
        story_sha256=None,
        story_content=None,
        job_state=None,
        retryable=False,
        error_code=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class _Db:
    def get(self, *_args: Any) -> SimpleNamespace:
        return SimpleNamespace(
            account_id="parent-account-1",
            issuer=_PRINCIPAL.issuer,
            account_role="parent",
            state="active",
        )


def test_cancel_request_requires_only_a_positive_expected_revision() -> None:
    assert ParentStoryRunCancelRequestV1(expected_revision=1).expected_revision == 1
    with pytest.raises(ValidationError):
        ParentStoryRunCancelRequestV1.model_validate({})
    with pytest.raises(ValidationError):
        ParentStoryRunCancelRequestV1(expected_revision=0)
    with pytest.raises(ValidationError):
        ParentStoryRunCancelRequestV1(expected_revision=1, extra="forbidden")


def test_cancel_route_returns_exact_persisted_success_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class _Service:
        def cancel_run(self, **kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return kwargs["response_builder"](_record(), kwargs["request_id"])

    monkeypatch.setattr(story_routes, "SqlParentStoryRunRepository", lambda _db: _Service())
    response = story_routes.cancel_parent_story_run(
        run_id=_RUN_ID,
        payload=ParentStoryRunCancelRequestV1(expected_revision=7),
        idempotency_key="cancel-key",
        principal=_PRINCIPAL,
        db=_Db(),  # type: ignore[arg-type]
    )

    body = response.model_dump(mode="json")
    assert set(body) == {"request_id", "story_run", "purge_state"}
    assert body["story_run"]["run_state"] == "DELETE_PENDING"
    assert body["story_run"]["run_revision"] == 8
    assert body["purge_state"] == "PENDING"
    assert captured["run_id"] == str(_RUN_ID)
    assert captured["expected_revision"] == 7
    assert captured["idempotency_key"] == "cancel-key"
