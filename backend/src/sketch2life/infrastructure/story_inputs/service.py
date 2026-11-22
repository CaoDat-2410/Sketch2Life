"""Attach a completed upload to a Parent run as its drawing (SRS l.1664; goal v3 T-2b).

Order of the use case (each step ends the request on failure):

1. owner-scoped run, replay of an earlier receipt, purged run, stale revision, state and retake
   budget (``prepare_drawing_attach``; nothing read from storage yet);
2. the completed upload behind the opaque ``asset_ref``: purpose ``RUN_ARTWORK``, this run, this
   Parent's scope, clean scan. Every miss is the same 404 (SRS l.864-865, CV-5). The caller's own
   completed ``RUN_AUDIO`` session of this run answers 415, which leaks nothing (T2B-D2);
3. the stored original is read through ``ObjectStoragePort``, its size and SHA-256 are recomputed
   and compared with the upload record, then normalized (``drawing.normalize_drawing``);
4. the repository attaches the derived asset, input revision, run update and receipt in one
   transaction under the run row lock (``attach_uploaded_drawing``).

The route never receives a key, bucket or URL from the client, and none leaves the service.
"""

from __future__ import annotations

import hashlib
from typing import Final

from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import DrawingAttachOutcome
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    drawing_attach_fingerprint,
)
from sketch2life.infrastructure.story_inputs.drawing import (
    DrawingNormalizationError,
    normalize_drawing,
)
from sketch2life.infrastructure.uploads.purposes import MAX_IMAGE_BYTES, RUN_ARTWORK, RUN_AUDIO
from sketch2life.infrastructure.uploads.service import resolve_completed_upload

_READ_CHUNK: Final = 64 * 1024
_IMAGE_MEDIA_TYPES: Final = frozenset({"image/jpeg", "image/png", "image/webp"})


def read_verified_original(
    storage: ObjectStoragePort, key: str, expected_size: int, expected_sha256: str
) -> bytes:
    """The stored bytes, bounded and verified against the upload record (T2B-D5, T2C-D2).

    A missing object is 422 ``UPLOAD_INCOMPLETE``, a size or SHA-256 that differs from the upload
    record is 422 ``UPLOAD_CHECKSUM_MISMATCH``, a storage fault is 503 ``STORAGE_UNAVAILABLE``.
    """
    try:
        stored = storage.get_object(key)
    except ObjectStorageFailure:
        raise ParentStoryRunError(503, "STORAGE_UNAVAILABLE") from None
    if stored is None:
        raise ParentStoryRunError(422, "UPLOAD_INCOMPLETE")
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    total = 0
    try:
        while chunk := stored.body.read(_READ_CHUNK):
            total += len(chunk)
            if total > expected_size:
                break
            digest.update(chunk)
            chunks.append(chunk)
    except ObjectStorageFailure:
        raise ParentStoryRunError(503, "STORAGE_UNAVAILABLE") from None
    finally:
        stored.body.close()
    if total != expected_size or digest.hexdigest() != expected_sha256:
        raise ParentStoryRunError(422, "UPLOAD_CHECKSUM_MISMATCH")
    return b"".join(chunks)


class ParentRunAssetService:
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

    def attach_drawing(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        asset_ref: str,
        expected_run_revision: int | None,
        idempotency_key: str,
    ) -> DrawingAttachOutcome | ParentStoryLifecycleRecord:
        fingerprint = drawing_attach_fingerprint(asset_ref, expected_run_revision)
        early = self._repository.prepare_drawing_attach(
            principal=principal,
            run_id=run_id,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            expected_run_revision=expected_run_revision,
        )
        if early is not None:
            return early

        owner = self._repository.asset_owner(principal=principal, run_id=run_id)
        upload = resolve_completed_upload(
            self._db,
            asset_ref,
            purpose=RUN_ARTWORK,
            owner_scope_kind=owner.kind,
            owner_scope_ref=owner.ref,
            organization_id=owner.organization_id,
            target_ref=run_id,
        )
        if upload is None:
            audio = resolve_completed_upload(
                self._db,
                asset_ref,
                purpose=RUN_AUDIO,
                owner_scope_kind=owner.kind,
                owner_scope_ref=owner.ref,
                organization_id=owner.organization_id,
                target_ref=run_id,
            )
            self._db.rollback()
            if audio is not None:
                raise ParentStoryRunError(415, "UNSUPPORTED_MEDIA_TYPE")
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
        self._db.rollback()
        if upload.media_type not in _IMAGE_MEDIA_TYPES:
            raise ParentStoryRunError(415, "UNSUPPORTED_MEDIA_TYPE")
        if upload.size_bytes > MAX_IMAGE_BYTES:
            raise ParentStoryRunError(413, "MEDIA_TOO_LARGE")
        storage = self._storage
        if storage is None:
            raise ParentStoryRunError(503, "STORAGE_UNAVAILABLE")

        source = read_verified_original(storage, upload.asset_key, upload.size_bytes, upload.sha256)
        try:
            derived = normalize_drawing(source, declared_media_type=upload.media_type)
        except DrawingNormalizationError as exc:
            raise ParentStoryRunError(exc.status_code, exc.code) from None
        return self._repository.attach_uploaded_drawing(
            principal=principal,
            run_id=run_id,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            expected_run_revision=expected_run_revision,
            original_asset_ref=upload.asset_key,
            original_sha256=upload.sha256,
            original_media_type=upload.media_type,
            original_size_bytes=upload.size_bytes,
            scanner_name=upload.scanner_name,
            scanner_version=upload.scanner_version,
            derived_png=derived.png_bytes,
            derived_sha256=derived.sha256,
            storage=storage,
        )


__all__ = ["ParentRunAssetService", "read_verified_original"]
