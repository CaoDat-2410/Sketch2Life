from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupPort,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRunRecord,
    ParentStoryRunRepositoryPort,
)
from sketch2life.application.services.parent_story_runs import ParentStoryRunService


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
