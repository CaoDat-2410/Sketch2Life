"""FEAT-087 M2: request/response contract and service guard for subject roles."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentDrawingCandidateV1,
    ParentSubjectConfirmationRequestV1,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))


def _request(**extra: Any) -> dict[str, Any]:
    return {"expected_understanding_revision": 1, "confirmed_subject": "con rùa", **extra}


def test_request_without_roles_is_still_valid_for_older_clients() -> None:
    assert ParentSubjectConfirmationRequestV1.model_validate(_request()).subject_roles is None


def test_request_accepts_roles_and_trims_labels() -> None:
    parsed = ParentSubjectConfirmationRequestV1.model_validate(
        _request(subject_roles=[{"entity_id": "main", "label": " con rùa ", "role": "main"}])
    )
    assert parsed.subject_roles[0].label == "con rùa"


@pytest.mark.parametrize(
    "roles",
    [
        [],
        [{"entity_id": "main", "label": "x", "role": "boss"}],
        [{"entity_id": "sec-9", "label": "x", "role": "main"}],
        [{"entity_id": "main", "label": "", "role": "main"}],
        [{"entity_id": "main", "label": "x" * 101, "role": "main"}],
        [{"entity_id": "main", "label": "x", "role": "main", "box": [1, 1, 2, 2]}],
        [{"entity_id": "main", "label": "x", "role": "main"}] * 5,
    ],
)
def test_request_rejects_malformed_roles(roles) -> None:
    with pytest.raises(ValidationError):
        ParentSubjectConfirmationRequestV1.model_validate(_request(subject_roles=roles))


def test_candidate_response_defaults_keep_v1_runs_valid() -> None:
    candidate = ParentDrawingCandidateV1.model_validate(
        {
            "candidate_subject": "con rùa",
            "visible_features": ["mai"],
            "confidence": 0.8,
            "adult_confirmation_required": True,
            "decision": "REVIEW_REQUIRED",
        }
    )
    assert candidate.entities == [] and candidate.subject_roles is None


class _Repository:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def confirm_subject(self, **kwargs: Any) -> int:
        self.calls.append(kwargs)
        return 2


def _service() -> tuple[ParentStoryRunService, _Repository]:
    repository = _Repository()
    service = ParentStoryRunService.__new__(ParentStoryRunService)
    service._repository = repository  # type: ignore[attr-defined]
    return service, repository


def _confirm(service: ParentStoryRunService, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": _PRINCIPAL,
        "run_id": "run-1",
        "expected_understanding_revision": 1,
        "confirmed_subject": "con rùa",
        "idempotency_key": "k",
    }
    values.update(overrides)
    return service.confirm_subject(**values)


def test_service_passes_roles_through_when_the_main_label_matches() -> None:
    service, repository = _service()
    roles = [{"entity_id": "main", "label": "con rùa", "role": "main"}]
    assert _confirm(service, subject_roles=roles) == 2
    assert repository.calls[0]["subject_roles"] == roles


def test_service_without_roles_passes_none() -> None:
    service, repository = _service()
    _confirm(service)
    assert repository.calls[0]["subject_roles"] is None


def test_service_rejects_roles_without_exactly_one_matching_main() -> None:
    service, repository = _service()
    for roles in (
        [{"entity_id": "main", "label": "khác", "role": "main"}],
        [{"entity_id": "main", "label": "con rùa", "role": "secondary"}],
        [
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {"entity_id": "sec-1", "label": "con rùa", "role": "main"},
        ],
    ):
        with pytest.raises(ParentStoryRunServiceError) as refused:
            _confirm(service, subject_roles=roles)
        assert (refused.value.status_code, refused.value.code) == (
            422,
            "PARENT_SUBJECT_ROLES_INVALID",
        )
    assert repository.calls == []
