"""Submit a Parent run's idea: text, audio or a transcript correction (SRS l.1665; goal v3 T-2c).

Order of the use case (each step ends the request on failure):

1. a request with audio first goes through ``prepare_idea``: owner-scoped run, replay of an
   earlier receipt, purged run, stale revision and input state, before any audio byte is read;
2. the completed upload behind ``audio_ref``: purpose ``RUN_AUDIO``, this run, this Parent's scope,
   clean scan. Every miss is the same 404 (SRS l.864-865, CV-5);
3. the stored bytes are read through ``ObjectStoragePort``, verified against the upload record,
   and measured with ``media_validation.audio_duration`` (at most 120 s, l.982; no decoder);
4. the repository writes the input revision (or the transcript correction), the run state and the
   receipt in one transaction under the run row lock (``submit_idea``).

The route never receives a key, bucket or URL from the client, and none leaves the service. The
audio file is read only to measure it; the transcript is produced later behind
``SpeechTranscriberPort`` and confirmed by the adult before it can reach a story.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import IdeaOutcome, VoiceInput
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.contracts.schemas.parent_story_inputs import AddRunIdeaRequestV1
from sketch2life.infrastructure.media_validation.audio_duration import (
    SUPPORTED_AUDIO_MEDIA_TYPES,
    AudioDurationError,
    audio_duration_ms,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    idea_fingerprint,
)
from sketch2life.infrastructure.story_inputs.service import read_verified_original
from sketch2life.infrastructure.uploads.purposes import (
    MAX_AUDIO_BYTES,
    MAX_AUDIO_DURATION_MS,
    RUN_AUDIO,
)
from sketch2life.infrastructure.uploads.service import resolve_completed_upload


class ParentRunIdeaService:
    """The use case for a Parent run and, with a Teacher ``repository`` (T-4b3a), for a pinned
    Teacher run: the repository carries the actor, so every scope below comes from it."""

    def __init__(
        self,
        db: Session,
        *,
        storage: ObjectStoragePort | None,
        repository: SqlParentStoryRunRepository | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._repository = repository or SqlParentStoryRunRepository(db)

    def submit(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        payload: AddRunIdeaRequestV1,
        idempotency_key: str,
    ) -> IdeaOutcome | ParentStoryLifecycleRecord:
        correction = payload.transcript_correction
        fingerprint = idea_fingerprint(
            payload.expected_run_revision,
            payload.text,
            payload.audio_ref,
            None if correction is None else (correction.base_revision, correction.text),
        )
        voice: VoiceInput | None = None
        if payload.audio_ref is not None:
            early = self._repository.prepare_idea(
                principal=principal,
                run_id=run_id,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                expected_run_revision=payload.expected_run_revision,
            )
            if early is not None:
                return early
            voice = self._resolve_voice(principal, run_id, payload.audio_ref)
        return self._repository.submit_idea(
            principal=principal,
            run_id=run_id,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            expected_run_revision=payload.expected_run_revision,
            text=payload.text,
            voice=voice,
            correction_base_revision=None if correction is None else correction.base_revision,
            correction_text=None if correction is None else correction.text,
        )

    def _resolve_voice(
        self, principal: VerifiedPrincipal, run_id: str, audio_ref: str
    ) -> VoiceInput:
        owner = self._repository.asset_owner(principal=principal, run_id=run_id)
        upload = resolve_completed_upload(
            self._db,
            audio_ref,
            purpose=RUN_AUDIO,
            owner_scope_kind=owner.kind,
            owner_scope_ref=owner.ref,
            organization_id=owner.organization_id,
            target_ref=run_id,
        )
        self._db.rollback()
        if upload is None:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        if upload.media_type not in SUPPORTED_AUDIO_MEDIA_TYPES:
            raise ParentStoryRunError(415, "UNSUPPORTED_MEDIA_TYPE")
        if upload.size_bytes > MAX_AUDIO_BYTES:
            raise ParentStoryRunError(413, "AUDIO_TOO_LARGE")
        storage = self._storage
        if storage is None:
            raise ParentStoryRunError(503, "STORAGE_UNAVAILABLE")
        data = read_verified_original(storage, upload.asset_key, upload.size_bytes, upload.sha256)
        if len(data) > MAX_AUDIO_BYTES:
            raise ParentStoryRunError(413, "AUDIO_TOO_LARGE")
        try:
            duration_ms = audio_duration_ms(data, media_type=upload.media_type)
        except AudioDurationError as exc:
            raise ParentStoryRunError(422, exc.code) from None
        if duration_ms > MAX_AUDIO_DURATION_MS:
            raise ParentStoryRunError(413, "AUDIO_TOO_LARGE")
        return VoiceInput(
            asset_key=upload.asset_key,
            sha256=upload.sha256,
            media_type=upload.media_type,
            size_bytes=upload.size_bytes,
            duration_ms=duration_ms,
        )


__all__ = ["ParentRunIdeaService"]
