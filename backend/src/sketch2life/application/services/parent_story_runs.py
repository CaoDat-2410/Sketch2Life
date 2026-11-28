"""Provider-independent Parent StoryRun use cases and bounded input validation."""

from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import SubjectConfirmOutcome
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileLookupPort,
    ParentStoryProfileLookupUnavailable,
    ParentStoryProfileReference,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRepositoryPort,
    ParentStoryRunSummary,
    ParentStoryRunView,
    StoryStartedCallback,
)
from sketch2life.domain.parent_profile_context import SelectedContextEntry

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
        intended_drawing_subject: str | None = None,
        lesson_version_ref: dict[str, str] | None = None,
        lesson_pin_snapshot: dict[str, object] | None = None,
    ) -> ParentStoryRunView:
        normalized_topic, normalized_idea, normalized_subject = self._normalize_create_values(
            topic=topic,
            adult_confirmed_idea=adult_confirmed_idea,
            intended_drawing_subject=intended_drawing_subject,
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
            intended_drawing_subject=normalized_subject,
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
        intended_drawing_subject: str | None = None,
        lesson_version_ref: dict[str, str] | None = None,
    ) -> ParentStoryRunView | None:
        normalized_topic, normalized_idea, normalized_subject = self._normalize_create_values(
            topic=topic,
            adult_confirmed_idea=adult_confirmed_idea,
            intended_drawing_subject=intended_drawing_subject,
        )
        return self._repository.replay_create_run(
            principal=principal,
            account_id=account_id,
            parent_profile_id=parent_profile_id,
            idempotency_key=idempotency_key,
            topic=normalized_topic,
            adult_confirmed_idea=normalized_idea,
            intended_drawing_subject=normalized_subject,
            lesson_version_ref=lesson_version_ref,
        )

    @staticmethod
    def _normalize_create_values(
        *, topic: str, adult_confirmed_idea: str, intended_drawing_subject: str | None
    ) -> tuple[str, str, str | None]:
        normalized_topic = topic.strip()
        normalized_idea = adult_confirmed_idea.strip()
        if (normalized_topic and not _SAFE_TOPIC.search(normalized_topic)) or len(
            normalized_topic
        ) > 120:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_TOPIC_INVALID")
        if len(normalized_idea) > 500:
            raise ParentStoryRunServiceError(422, "PARENT_STORY_IDEA_TOO_LONG")
        normalized_subject = " ".join((intended_drawing_subject or "").split()) or None
        if normalized_subject is not None and len(normalized_subject) > 160:
            raise ParentStoryRunServiceError(422, "PARENT_DRAWING_SUBJECT_TOO_LONG")
        return normalized_topic, normalized_idea, normalized_subject

    def get_run(self, *, principal: VerifiedPrincipal, run_id: str) -> ParentStoryRunView:
        return self._repository.get_run(principal=principal, run_id=run_id)

    def get_active_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunView | None:
        return self._repository.get_active_run(principal=principal, account_id=account_id)

    def cancel_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> ParentStoryLifecycleRecord:
        """FR-C-08 cancel: the run becomes DELETE_PENDING and the purge is requested."""
        return self._repository.cancel_run(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
        )

    def delete_run(
        self, *, principal: VerifiedPrincipal, run_id: str, idempotency_key: str
    ) -> ParentStoryLifecycleRecord:
        """FR-C-08 delete of a COMPLETED, FAILED or ABANDONED run (D-214 item 1)."""
        return self._repository.delete_run(
            principal=principal, run_id=run_id, idempotency_key=idempotency_key
        )

    def confirm_context(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_context_revision: int,
        expected_context_snapshot_sha256: str,
        idempotency_key: str,
        on_story_started: StoryStartedCallback | None = None,
        generator_supports_role: bool = True,
        selected_context_entry_ids: Sequence[UUID] | None = None,
    ) -> ParentStoryRunView:
        selected: tuple[UUID, ...] | None = None
        resolve = None
        if selected_context_entry_ids is not None:
            # T-12a: the service builds the resolver (as the activity selection does), so the Story
            # repository never imports the Parent context persistence.
            selected = tuple(selected_context_entry_ids)

            def resolve(profile_id: UUID, wanted: tuple[UUID, ...]) -> list[SelectedContextEntry]:
                try:
                    entries = self._profile_lookup.resolve_selected_context_entries(
                        principal=principal, profile_id=profile_id, entry_ids=wanted
                    )
                except ParentStoryProfileLookupUnavailable:
                    raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None
                if entries is None:
                    raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
                return entries

        return self._repository.confirm_context(
            principal=principal,
            run_id=run_id,
            expected_context_revision=expected_context_revision,
            expected_context_snapshot_sha256=expected_context_snapshot_sha256,
            idempotency_key=idempotency_key,
            on_story_started=on_story_started,
            generator_supports_role=generator_supports_role,
            selected_context_entry_ids=selected,
            resolve_context_entries=resolve,
        )

    def confirm_subject(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
        idempotency_key: str,
        subject_roles: list[dict[str, str]] | None = None,
        rerun_on_edit: bool = False,
        on_story_started: StoryStartedCallback | None = None,
        generator_supports_role: bool = True,
    ) -> SubjectConfirmOutcome | ParentStoryLifecycleRecord:
        subject = confirmed_subject.strip()
        if not subject or len(subject) > 160:
            raise ParentStoryRunServiceError(422, "PARENT_CONFIRMED_SUBJECT_INVALID")
        if subject_roles is not None:
            mains = [item for item in subject_roles if item.get("role") == "main"]
            if len(mains) != 1 or str(mains[0].get("label", "")).strip() != subject:
                raise ParentStoryRunServiceError(422, "PARENT_SUBJECT_ROLES_INVALID")
        return self._repository.confirm_subject(
            principal=principal,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            confirmed_subject=subject,
            idempotency_key=idempotency_key,
            subject_roles=subject_roles,
            rerun_on_edit=rerun_on_edit,
            on_story_started=on_story_started,
            generator_supports_role=generator_supports_role,
        )

    def reserve_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        idempotency_key: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
        require_activity_selection: bool = False,
    ) -> ParentStoryRevisionReservation:
        instruction = rewrite_instruction.strip() if rewrite_instruction else None
        if instruction is not None and (not instruction or len(instruction) > 400):
            raise ParentStoryRunServiceError(422, "PARENT_REWRITE_INSTRUCTION_INVALID")
        return self._repository.reserve_story_revision(
            principal=principal,
            account_id=account_id,
            run_id=run_id,
            expected_understanding_revision=expected_understanding_revision,
            rewrite_instruction=instruction,
            idempotency_key=idempotency_key,
            story_revision_id=str(uuid.uuid4()),
            model_id=model_id,
            model_revision=model_revision,
            prompt_version=prompt_version,
            require_activity_selection=require_activity_selection,
        )

    def confirm_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunView:
        return self._repository.confirm_story_revision(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            expected_story_sha256=expected_story_sha256,
            idempotency_key=idempotency_key,
        )

    def list_runs(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID | None,
        limit: int,
        after: tuple[datetime, str] | None,
    ) -> list[ParentStoryRunSummary]:
        """FEAT-081 C3b: the caller's run history (SRS §21.5 line 1707, FR-C-06 line 498)."""
        if profile_id is not None:
            try:
                owned = self._profile_lookup.is_owned_profile(
                    principal=principal, profile_id=profile_id
                )
            except ParentStoryProfileLookupUnavailable:
                raise ParentStoryRunServiceError(
                    503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
                ) from None
            if not owned:
                raise ParentStoryRunServiceError(404, "RESOURCE_NOT_FOUND")
        return self._repository.list_runs(
            principal=principal, profile_id=profile_id, limit=limit, after=after
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
