from __future__ import annotations

from typing import Any, cast
from uuid import UUID

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupPort,
    ParentStoryProfileReference,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRunRecord,
    ParentStoryRunRepositoryPort,
)
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)


class _ReplayRepository:
    def __init__(self, result: ParentStoryRunRecord) -> None:
        self.result = result
        self.arguments: dict[str, Any] = {}

    def replay_create_run(self, **kwargs: Any) -> ParentStoryRunRecord:
        self.arguments = kwargs
        return self.result


class _ForbiddenProfileLookup:
    def get_owned_profile_current_revision(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> None:
        raise AssertionError("an idempotent replay must not read the mutable profile")


class _AgeProfileLookup:
    def __init__(self, age_months: int) -> None:
        self.age_months = age_months

    def get_owned_profile_current_revision(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> ParentStoryProfileReference:
        del principal
        return ParentStoryProfileReference(
            profile_id=profile_id,
            profile_revision_id=UUID("11111111-1111-4111-8111-111111111111"),
            state="ACTIVE",
            data_origin="SYNTHETIC_DEV",
            age_months=self.age_months,
            interests_summary=None,
        )


class _CreateRepository:
    def __init__(self) -> None:
        self.calls = 0

    def create_run(self, **_kwargs: Any) -> ParentStoryRunRecord:
        self.calls += 1
        return cast(ParentStoryRunRecord, object())


def test_create_replay_short_circuits_profile_lookup_and_normalizes_payload() -> None:
    record = cast(ParentStoryRunRecord, object())
    repository = _ReplayRepository(record)
    service = ParentStoryRunService(
        cast(ParentStoryRunRepositoryPort, repository),
        cast(ParentStoryProfileLookupPort, _ForbiddenProfileLookup()),
    )
    lesson_version_ref = {
        "lesson_id": "lesson-1",
        "version_id": "version-1",
        "content_sha256": "a" * 64,
    }

    result = service.replay_create_run(
        principal=cast(VerifiedPrincipal, object()),
        account_id="account-1",
        parent_profile_id=UUID("01234567-89ab-cdef-0123-456789abcdef"),
        idempotency_key="create-key",
        topic="  Butterflies  ",
        adult_confirmed_idea="  Visit a garden  ",
        lesson_version_ref=lesson_version_ref,
    )

    assert result is record
    assert repository.arguments["topic"] == "Butterflies"
    assert repository.arguments["adult_confirmed_idea"] == "Visit a garden"
    assert repository.arguments["lesson_version_ref"] == lesson_version_ref


@pytest.mark.parametrize("age_months", (36, 120))
def test_create_accepts_boundary_ages_before_repository_admission(age_months: int) -> None:
    repository = _CreateRepository()
    service = ParentStoryRunService(
        cast(ParentStoryRunRepositoryPort, repository),
        cast(ParentStoryProfileLookupPort, _AgeProfileLookup(age_months)),
    )
    service.create_run(
        principal=cast(VerifiedPrincipal, object()),
        account_id="account-1",
        parent_profile_id=UUID("22222222-2222-4222-8222-222222222222"),
        idempotency_key="create-key",
        topic="A garden",
        adult_confirmed_idea="A butterfly",
    )
    assert repository.calls == 1


@pytest.mark.parametrize("age_months", (121, 155))
def test_create_refuses_out_of_range_ages_before_repository_admission(age_months: int) -> None:
    repository = _CreateRepository()
    service = ParentStoryRunService(
        cast(ParentStoryRunRepositoryPort, repository),
        cast(ParentStoryProfileLookupPort, _AgeProfileLookup(age_months)),
    )
    with pytest.raises(ParentStoryRunServiceError) as refused:
        service.create_run(
            principal=cast(VerifiedPrincipal, object()),
            account_id="account-1",
            parent_profile_id=UUID("22222222-2222-4222-8222-222222222222"),
            idempotency_key="create-key",
            topic="A garden",
            adult_confirmed_idea="A butterfly",
        )
    assert refused.value.status_code == 422
    assert refused.value.code == "INVALID_REQUEST"
    assert repository.calls == 0
