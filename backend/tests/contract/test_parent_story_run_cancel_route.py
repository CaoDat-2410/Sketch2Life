"""FR-C-08 cancel and delete routes: lifecycle envelope and the 1-128 key (Contract Draft 11)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryLifecycleRecord
from sketch2life.application.ports.story_run_lifecycle import lifecycle_request_id
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryRunCancelRequestV1,
    ParentStoryRunLifecycleEnvelopeV1,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = UUID("22222222-2222-4222-8222-222222222222")


def _record(state: str = "DELETE_PENDING") -> ParentStoryLifecycleRecord:
    return ParentStoryLifecycleRecord(
        run_id=str(_RUN_ID),
        run_state=state,
        revision=8,
        version=10,
        lifecycle_request_ref=lifecycle_request_id(str(_RUN_ID)),
        purge_state="COMPLETED" if state == "DELETED" else "PENDING",
    )


class _Db:
    def get(self, *_args: Any) -> Any:
        from types import SimpleNamespace

        return SimpleNamespace(
            account_id="parent-account-1",
            issuer=_PRINCIPAL.issuer,
            account_role="parent",
            state="active",
        )


def _request(*keys: str) -> Request:
    headers = [(b"idempotency-key", key.encode("latin-1")) for key in keys]
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": f"/v1/story-runs/{_RUN_ID}/cancel",
            "headers": headers,
            "query_string": b"",
        }
    )


def test_cancel_request_requires_only_a_positive_expected_revision() -> None:
    assert ParentStoryRunCancelRequestV1(expected_revision=1).expected_revision == 1
    with pytest.raises(ValidationError):
        ParentStoryRunCancelRequestV1.model_validate({})
    with pytest.raises(ValidationError):
        ParentStoryRunCancelRequestV1(expected_revision=0)
    with pytest.raises(ValidationError):
        ParentStoryRunCancelRequestV1(expected_revision=1, extra="forbidden")  # type: ignore[call-arg]


def test_cancel_route_returns_the_lifecycle_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class _Service:
        def cancel_run(self, **kwargs: Any) -> ParentStoryLifecycleRecord:
            captured.update(kwargs)
            return _record()

    monkeypatch.setattr(story_routes, "_service", lambda _db: _Service())
    response = story_routes.cancel_parent_story_run(
        run_id=_RUN_ID,
        payload=ParentStoryRunCancelRequestV1(expected_revision=7),
        request=_request("k" * 128),
        principal=_PRINCIPAL,
        db=_Db(),  # type: ignore[arg-type]
    )
    body = response.model_dump(mode="json")
    assert set(body) == {"request_id", "lifecycle"}
    assert body["lifecycle"] == _record().as_body()
    assert captured == {
        "principal": _PRINCIPAL,
        "run_id": str(_RUN_ID),
        "expected_revision": 7,
        "idempotency_key": "k" * 128,
    }


def test_delete_route_returns_the_lifecycle_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class _Service:
        def delete_run(self, **kwargs: Any) -> ParentStoryLifecycleRecord:
            captured.update(kwargs)
            return _record()

    monkeypatch.setattr(story_routes, "_service", lambda _db: _Service())
    response = story_routes.delete_parent_story_run(
        run_id=_RUN_ID,
        request=_request("delete-key"),
        principal=_PRINCIPAL,
        db=_Db(),  # type: ignore[arg-type]
    )
    assert isinstance(response, ParentStoryRunLifecycleEnvelopeV1)
    assert response.lifecycle.run_state == "DELETE_PENDING"
    assert captured == {
        "principal": _PRINCIPAL,
        "run_id": str(_RUN_ID),
        "idempotency_key": "delete-key",
    }
    assert "expected_revision" not in captured


@pytest.mark.parametrize("keys", ((), ("",), ("k" * 129,), ("a", "b"), ("é",)))
def test_routes_read_the_key_with_the_conv1_parser(
    monkeypatch: pytest.MonkeyPatch, keys: tuple[str, ...]
) -> None:
    monkeypatch.setattr(
        story_routes, "_service", lambda _db: pytest.fail("service must not be reached")
    )
    with pytest.raises(HTTPException) as refused:
        story_routes.delete_parent_story_run(
            run_id=_RUN_ID,
            request=_request(*keys),
            principal=_PRINCIPAL,
            db=_Db(),  # type: ignore[arg-type]
        )
    assert refused.value.status_code == 400
    assert isinstance(refused.value.detail, dict)
    assert refused.value.detail["code"] == "INVALID_REQUEST"


def test_the_projection_never_carries_run_content() -> None:
    fields = set(ParentStoryRunLifecycleEnvelopeV1.model_fields["lifecycle"].annotation.model_fields)  # type: ignore[union-attr]
    assert fields == {
        "run_id",
        "run_state",
        "revision",
        "version",
        "lifecycle_request_ref",
        "purge_state",
    }
    with pytest.raises(ValidationError):
        ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {
                "request_id": str(_RUN_ID),
                "lifecycle": {**_record().as_body(), "subject_label": "private"},
            }
        )
