"""Provider-independent Parent StoryRun use cases and bounded input validation."""

from __future__ import annotations

import base64
import binascii
import json
import re
import uuid
from collections.abc import Mapping
from datetime import datetime

from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunRecord,
    ParentStoryRunRepositoryPort,
)

_SAFE_TOPIC = re.compile(r"\S")
_PRIMARY_ACTIVITY_KEYS = {
    "activity_ref",
    "title",
    "objective",
    "materials_text",
    "preparation_text",
    "instructions_text",
    "observation_notes",
    "safety_notes",
    "activity_kind",
    "source",
    "source_lesson_id",
    "source_lesson_title",
    "source_lesson_version_id",
    "source_content_sha256",
    "source_activity_index",
    "match_reason",
}


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

    def list_runs(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        limit: int,
        profile_id: str | None = None,
        cursor: str | None = None,
    ) -> tuple[list[ParentStoryRunRecord], str | None]:
        if not 1 <= limit <= 50:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_HISTORY_LIMIT_INVALID")

        before_created_at = None
        before_run_id = None
        if cursor:
            before_created_at, before_run_id = self._decode_history_cursor(cursor)

        rows = self._repository.list_runs(
            owner_subject=owner_subject,
            policy_version=policy_version,
            limit=limit + 1,
            profile_id=profile_id,
            before_created_at=before_created_at,
            before_run_id=before_run_id,
        )
        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = self._encode_history_cursor(page[-1]) if has_more and page else None
        return page, next_cursor

    @staticmethod
    def _encode_history_cursor(record: ParentStoryRunRecord) -> str:
        payload = json.dumps(
            {"created_at": record.created_at.isoformat(), "run_id": record.run_id},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_history_cursor(cursor: str) -> tuple[datetime, str]:
        if len(cursor) > 512:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_HISTORY_CURSOR_INVALID")
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
            if not isinstance(payload, dict) or set(payload) != {"created_at", "run_id"}:
                raise ValueError
            created_at = datetime.fromisoformat(payload["created_at"])
            if created_at.tzinfo is None or created_at.utcoffset() is None:
                raise ValueError
            run_id = str(uuid.UUID(payload["run_id"]))
        except (
            ValueError,
            TypeError,
            KeyError,
            UnicodeEncodeError,
            binascii.Error,
            json.JSONDecodeError,
        ):
            raise ParentStoryRunServiceError(
                422, "PARENT_STORY_HISTORY_CURSOR_INVALID"
            ) from None
        return created_at, run_id

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
        primary_activity: Mapping[str, object],
        rewrite_instruction: str | None,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation:
        instruction = rewrite_instruction.strip() if rewrite_instruction else None
        if instruction is not None and (not instruction or len(instruction) > 400):
            raise ParentStoryRunServiceError(422, "PARENT_REWRITE_INSTRUCTION_INVALID")
        activity = dict(primary_activity)
        if set(activity) != _PRIMARY_ACTIVITY_KEYS:
            raise ParentStoryRunServiceError(409, "PARENT_PRIMARY_ACTIVITY_SNAPSHOT_INVALID")
        if (
            activity.get("activity_kind") != "outdoor"
            or activity.get("source")
            not in {"PINNED_LESSON", "PUBLISHED_SHARED_LESSON", "AI_GENERATED_DRAFT"}
            or not isinstance(activity.get("activity_ref"), str)
            or not activity["activity_ref"].strip()
            or any(
                not isinstance(activity.get(field), str) or not str(activity[field]).strip()
                for field in (
                    "title",
                    "objective",
                    "materials_text",
                    "preparation_text",
                    "instructions_text",
                    "observation_notes",
                    "safety_notes",
                )
            )
            or len(str(activity["instructions_text"])) < 16
            or len(str(activity["safety_notes"])) < 8
        ):
            raise ParentStoryRunServiceError(409, "PARENT_PRIMARY_ACTIVITY_SNAPSHOT_INVALID")
        return self._repository.reserve_story_revision(
            owner_subject=owner_subject,
            policy_version=policy_version,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            primary_activity=activity,
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
