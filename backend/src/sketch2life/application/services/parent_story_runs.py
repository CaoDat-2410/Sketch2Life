"""Provider-independent Parent StoryRun use cases and bounded input validation."""

from __future__ import annotations

import re
import uuid
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupPort,
    ParentStoryProfileLookupUnavailable,
    ParentStoryProfileReference,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunRecord,
    ParentStoryRunRepositoryPort,
)

_SAFE_TOPIC = re.compile(r"\S")


class ParentStoryRunServiceError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


class ParentStoryRunService:
    def __init__(
        self,
        repository: ParentStoryRunRepositoryPort,
        profile_lookup: ParentStoryProfileLookupPort,
    ) -> None:
        self._repository = repository
        self._profile_lookup = profile_lookup

    def create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        parent_profile_id: UUID,
        idempotency_key: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_version_ref: dict[str, str] | None = None,
        lesson_pin_snapshot: dict[str, object] | None = None,
    ) -> ParentStoryRunRecord:
        normalized_topic, normalized_idea = self._normalize_create_values(
            topic=topic, adult_confirmed_idea=adult_confirmed_idea
        )
        profile = self._profile_for_run(principal=principal, profile_id=parent_profile_id)
        return self._repository.create_run(
            principal=principal,
            account_id=account_id,
            profile=profile,
            idempotency_key=idempotency_key,
            run_id=str(uuid.uuid4()),
            topic=normalized_topic,
            adult_confirmed_idea=normalized_idea,
            lesson_version_ref=lesson_version_ref,
            lesson_pin_snapshot=lesson_pin_snapshot,
        )

    def replay_create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        parent_profile_id: UUID,
        idempotency_key: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_version_ref: dict[str, str] | None = None,
    ) -> ParentStoryRunRecord | None:
        normalized_topic, normalized_idea = self._normalize_create_values(
            topic=topic, adult_confirmed_idea=adult_confirmed_idea
        )
        return self._repository.replay_create_run(
            principal=principal,
            account_id=account_id,
            parent_profile_id=parent_profile_id,
            idempotency_key=idempotency_key,
            topic=normalized_topic,
            adult_confirmed_idea=normalized_idea,
            lesson_version_ref=lesson_version_ref,
        )

    @staticmethod
    def _normalize_create_values(*, topic: str, adult_confirmed_idea: str) -> tuple[str, str]:
        normalized_topic = topic.strip()
        normalized_idea = adult_confirmed_idea.strip()
        if (normalized_topic and not _SAFE_TOPIC.search(normalized_topic)) or len(
            normalized_topic
        ) > 120:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_TOPIC_INVALID")
        if len(normalized_idea) > 500:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_IDEA_TOO_LONG")
        return normalized_topic, normalized_idea

    def get_run(self, *, principal: VerifiedPrincipal, run_id: str) -> ParentStoryRunRecord:
        return self._repository.get_run(principal=principal, run_id=run_id)

    def get_active_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunRecord | None:
        return self._repository.get_active_run(principal=principal, account_id=account_id)

    def confirm_context(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_context_revision: int,
        expected_context_snapshot_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunRecord:
        return self._repository.confirm_context(
            principal=principal,
            run_id=run_id,
            expected_context_revision=expected_context_revision,
            expected_context_snapshot_sha256=expected_context_snapshot_sha256,
            idempotency_key=idempotency_key,
        )

    def confirm_subject(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
        idempotency_key: str,
    ) -> int:
        subject = confirmed_subject.strip()
        if not subject or len(subject) > 160:
            raise ParentStoryRunServiceError(422, "PARENT_CONFIRMED_SUBJECT_INVALID")
        return self._repository.confirm_subject(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            confirmed_subject=subject,
            idempotency_key=idempotency_key,
        )

    def reserve_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        idempotency_key: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation:
        instruction = rewrite_instruction.strip() if rewrite_instruction else None
        if instruction is not None and (not instruction or len(instruction) > 400):
            raise ParentStoryRunServiceError(422, "PARENT_REWRITE_INSTRUCTION_INVALID")
        return self._repository.reserve_story_revision(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            rewrite_instruction=instruction,
            idempotency_key=idempotency_key,
            story_revision_id=str(uuid.uuid4()),
            model_id=model_id,
            model_revision=model_revision,
            prompt_version=prompt_version,
        )

    def confirm_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunRecord:
        return self._repository.confirm_story_revision(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            expected_story_sha256=expected_story_sha256,
            idempotency_key=idempotency_key,
        )

    def _profile_for_run(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> ParentStoryProfileReference:
        try:
            profile = self._profile_lookup.get_owned_profile_current_revision(
                principal=principal,
                profile_id=profile_id,
            )
        except ParentStoryProfileLookupUnavailable:
            raise ParentStoryRunServiceError(503, "PARENT_PROFILE_REVISION_UNAVAILABLE") from None
        if profile is None or profile.state != "ACTIVE" or profile.data_origin != "SYNTHETIC_DEV":
            raise ParentStoryRunServiceError(404, "RESOURCE_NOT_FOUND")
        if not 36 <= profile.age_months <= 120:
            raise ParentStoryRunServiceError(422, "INVALID_REQUEST")
        return profile


__all__ = ["ParentStoryRunService", "ParentStoryRunServiceError"]
