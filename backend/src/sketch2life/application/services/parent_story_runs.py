"""Provider-independent Parent StoryRun use cases and bounded input validation."""

from __future__ import annotations

import re
import uuid

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
    def __init__(self, repository: ParentStoryRunRepositoryPort) -> None:
        self._repository = repository

    def create_run(
        self,
        *,
        owner_subject: str,
        account_id: str,
        parent_profile_id: str,
        expected_profile_revision_ref: str,
        accepted_policy_version: str,
        policy_version: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_pin_snapshot: dict[str, object] | None = None,
    ) -> ParentStoryRunRecord:
        if not accepted_policy_version.strip():
            raise ParentStoryRunServiceError(422, "PARENT_CONSENT_VERSION_REQUIRED")
        if accepted_policy_version.strip() != policy_version.strip():
            raise ParentStoryRunServiceError(409, "PARENT_CONSENT_POLICY_CHANGED")
        normalized_topic = topic.strip()
        normalized_idea = adult_confirmed_idea.strip()
        if (normalized_topic and not _SAFE_TOPIC.search(normalized_topic)) or len(
            normalized_topic
        ) > 120:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_TOPIC_INVALID")
        if len(normalized_idea) > 500:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_IDEA_TOO_LONG")
        return self._repository.create_run(
            owner_subject=owner_subject,
            account_id=account_id,
            parent_profile_id=parent_profile_id,
            expected_profile_revision_ref=expected_profile_revision_ref,
            policy_version=policy_version,
            run_id=str(uuid.uuid4()),
            topic=normalized_topic,
            adult_confirmed_idea=normalized_idea,
            lesson_pin_snapshot=lesson_pin_snapshot,
        )

    def get_run(
        self, *, owner_subject: str, policy_version: str, run_id: str
    ) -> ParentStoryRunRecord:
        return self._repository.get_run(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
        )

    def get_active_run(
        self, *, owner_subject: str, account_id: str, policy_version: str
    ) -> ParentStoryRunRecord | None:
        return self._repository.get_active_run(
            owner_subject=owner_subject,
            account_id=account_id,
            policy_version=policy_version,
        )

    def confirm_subject(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
    ) -> int:
        subject = confirmed_subject.strip()
        if not subject or len(subject) > 160:
            raise ParentStoryRunServiceError(422, "PARENT_CONFIRMED_SUBJECT_INVALID")
        return self._repository.confirm_subject(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            confirmed_subject=subject,
        )

    def reserve_story_revision(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation:
        instruction = rewrite_instruction.strip() if rewrite_instruction else None
        if instruction is not None and (not instruction or len(instruction) > 400):
            raise ParentStoryRunServiceError(422, "PARENT_REWRITE_INSTRUCTION_INVALID")
        return self._repository.reserve_story_revision(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            rewrite_instruction=instruction,
            story_revision_id=str(uuid.uuid4()),
            model_id=model_id,
            model_revision=model_revision,
            prompt_version=prompt_version,
        )

    def confirm_story_revision(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
    ) -> ParentStoryRunRecord:
        return self._repository.confirm_story_revision(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
            expected_revision=expected_revision,
            expected_story_sha256=expected_story_sha256,
        )


__all__ = ["ParentStoryRunService", "ParentStoryRunServiceError"]
