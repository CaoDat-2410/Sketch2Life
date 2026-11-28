"""Seed Parent StoryRuns into the Phase B states used by the owner screens."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Connection, Engine, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import LessonDocumentParser, MalwareScanner
from sketch2life.application.ports.object_storage import ObjectStoragePort, StoredObject
from sketch2life.application.ports.parent_story_inputs import (
    StoryGenerationResult,
    VoiceInput,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.application.services.parent_profiles import ParentProfileService
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.application.services.story_output import (
    StoryOutputInvalid,
    complete_generated_story,
)
from sketch2life.application.services.story_run_video import (
    StoryVideoAdmissionService,
    StoryVideoCommandService,
)
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from sketch2life.domain.parent_profiles import ParentProfileError
from sketch2life.infrastructure.lesson_library.parent_activity_catalog import (
    LessonLibraryParentActivityCatalogAdapter,
)
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS as LESSON_ACCESS_GRANTS,
)
from sketch2life.infrastructure.lesson_library.tables import (
    COMMAND_RECEIPTS as LESSON_COMMAND_RECEIPTS,
)
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS as LESSON_LIBRARY_ITEMS,
)
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_VERSIONS as LESSON_LIBRARY_VERSIONS,
)
from sketch2life.infrastructure.lesson_library.tables import (
    VERSION_ACTIVITIES as LESSON_VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentCommandReceiptModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    drawing_attach_fingerprint,
    idea_fingerprint,
)
from sketch2life.infrastructure.story_inputs.drawing import normalize_drawing
from sketch2life.infrastructure.story_inputs.fixtures import (
    FixtureDrawingAnalyzer,
    FixtureSpeechTranscriber,
    FixtureStoryGenerator,
    worker_input_sha256,
)
from sketch2life.infrastructure.story_inputs.runner import ParentInputJobRunner
from sketch2life.infrastructure.story_inputs.speech import ParentSpeechJobRunner
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRunner
from sketch2life.infrastructure.story_video.local_adapters import build_local_video_adapters
from sketch2life.infrastructure.story_video.repository import (
    SqlStoryVideoRepository,
)
from sketch2life.infrastructure.story_video.repository import (
    idempotency_key_hash as video_idempotency_key_hash,
)
from tools.seed import data
from tools.seed import s7b_story_states_data as seed_data
from tools.seed.s7a_runs import _require_parent
from tools.seed.stage_common import StageError, StageResult, run_stage_main, stage_key

_ASSET_TABLE = cast(sa.Table, CoreAssetMetadataModel.__table__)


class MemoryObjectStorage:
    """A process-local fake; no file, network, bucket or external object is created."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}

    def put_object(
        self,
        key: str,
        body: Any,
        *,
        content_type: str,
        content_length: int,
        metadata: Mapping[str, str],
    ) -> None:
        content = body.read()
        if len(content) != content_length:
            raise ValueError("synthetic object size did not match")
        self.objects[key] = (content, content_type, dict(metadata))

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type, metadata = item
        return StoredObject(io.BytesIO(content), len(content), content_type, metadata)

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


def _idempotency_key_hash(value: str) -> str:
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def _story_key(name: str) -> str:
    return stage_key("s7b", seed_data.S7B_COMMAND_CASES[name])


def _principal(parent_key: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(
        subject=data.PARENT_SUBJECTS[parent_key], issuer=data.SEED_ISSUER, roles=frozenset()
    )


def _build_story_service(session: Session) -> ParentStoryRunService:
    return ParentStoryRunService(
        SqlParentStoryRunRepository(session), SqlParentStoryProfileLookup(session)
    )


def _build_lesson_library_service(session: Session) -> LessonLibraryService:
    """Build the catalog service without enabling lesson upload I/O."""

    return LessonLibraryService(
        session,
        storage=cast(ObjectStoragePort, None),
        parser=cast(LessonDocumentParser, None),
        scanner=cast(MalwareScanner, None),
    )


def _build_activity_selection_service(session: Session) -> ParentActivitySelectionService:
    return ParentActivitySelectionService(
        SqlParentStoryRunRepository(session),
        LessonLibraryParentActivityCatalogAdapter(_build_lesson_library_service(session)),
    )


def _raise_command_error(exc: Exception) -> StageError:
    code = getattr(exc, "code", "COMMAND_FAILED")
    return StageError(f"S7B_COMMAND_FAILED_{code}")


def _create_k6_profile(factory: Any) -> UUID:
    principal = _principal("p3")
    with factory() as session:
        _require_parent(session, principal)
        session.rollback()  # the profile repository opens its own transaction
        service = ParentProfileService(SqlParentProfileRepository(session), synthetic_enabled=True)
        try:
            result = service.create_profile(
                principal=principal,
                snapshot=seed_data.PROFILE_SNAPSHOT,
                idempotency_key=_story_key("profile_create"),
                request_id=stage_key("s7b", "p3-profile-create-request-1"),
            )
        except ParentProfileError as exc:
            raise _raise_command_error(exc) from None
    try:
        return UUID(str(result.body["profile_id"]))
    except (KeyError, TypeError, ValueError):
        raise StageError("S7B_PROFILE_RECEIPT_INVALID") from None


def _is_seed_run(
    record: ParentStoryRunRecord,
    profile_id: UUID,
    topic: str,
    idea: str,
) -> bool:
    snapshot = record.context_snapshot
    return (
        str(record.parent_profile_id) == str(profile_id)
        and snapshot.get("topic") == topic
        and snapshot.get("adult_confirmed_idea") == idea
        and data.sha256_json(snapshot) == record.context_snapshot_sha256
    )


def _ensure_new_parent_run(
    factory: Any,
    *,
    profile_id: UUID,
    topic: str,
    idea: str,
    create_case: str,
    confirm_case: str,
) -> ParentStoryRunRecord:
    principal = _principal("p3")
    account_id = data.parent_account_id("p3")
    with factory() as session:
        _require_parent(session, principal)
        service = _build_story_service(session)
        key = _story_key(create_case)
        try:
            record = service.replay_create_run(
                principal=principal,
                account_id=account_id,
                parent_profile_id=profile_id,
                idempotency_key=key,
                topic=topic,
                adult_confirmed_idea=idea,
            )
            if record is None:
                active = service.get_active_run(principal=principal, account_id=account_id)
                if active is not None:
                    raise StageError("S7B_FOREIGN_ACTIVE_RUN")
                record = service.create_run(
                    principal=principal,
                    account_id=account_id,
                    parent_profile_id=profile_id,
                    idempotency_key=key,
                    topic=topic,
                    adult_confirmed_idea=idea,
                )
            if not isinstance(record, ParentStoryRunRecord) or not _is_seed_run(
                record, profile_id, topic, idea
            ):
                raise StageError("S7B_SEED_RUN_MISMATCH")
            if not record.context_confirmed:
                if record.run_state != "INPUT_PROCESSING":
                    raise StageError("S7B_CONTEXT_NOT_CONFIRMABLE")
                record = service.confirm_context(
                    principal=principal,
                    run_id=record.run_id,
                    expected_context_revision=record.context_revision,
                    expected_context_snapshot_sha256=record.context_snapshot_sha256,
                    idempotency_key=_story_key(confirm_case),
                )
            if not isinstance(record, ParentStoryRunRecord) or not record.context_confirmed:
                raise StageError("S7B_CONTEXT_NOT_CONFIRMED")
            return record
        except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
            raise _raise_command_error(exc) from None


def _get_run(factory: Any, principal: VerifiedPrincipal, run_id: str) -> ParentStoryRunRecord:
    with factory() as session:
        try:
            record = SqlParentStoryRunRepository(session).get_run(
                principal=principal, run_id=run_id
            )
        except ParentStoryRunError as exc:
            raise _raise_command_error(exc) from None
    if not isinstance(record, ParentStoryRunRecord):
        raise StageError("S7B_RUN_RECORD_UNAVAILABLE")
    return record


def _ensure_voice_metadata(
    factory: Any,
    storage: ObjectStoragePort,
    principal: VerifiedPrincipal,
    run_id: str,
) -> VoiceInput:
    asset_ref = f"parent/{run_id}/s7b/voice/original.wav"
    storage.put_object(
        asset_ref,
        io.BytesIO(seed_data.AUDIO_BYTES),
        content_type="audio/wav",
        content_length=len(seed_data.AUDIO_BYTES),
        metadata={"sha256": seed_data.AUDIO_SHA256},
    )
    with factory.begin() as session:
        session.execute(
            pg_insert(_ASSET_TABLE)
            .values(
                asset_ref=asset_ref,
                asset_version=1,
                organization_id=None,
                owner_scope_kind="PARENT_ACCOUNT",
                owner_scope_ref=data.principal_scope_ref(data.SEED_ISSUER, principal.subject),
                content_sha256=seed_data.AUDIO_SHA256,
                media_type="audio/wav",
                source_refs=[run_id],
                derived_from_ref=None,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    CoreAssetMetadataModel.__table__.c.asset_ref,
                    CoreAssetMetadataModel.__table__.c.asset_version,
                ]
            )
        )
    return VoiceInput(
        asset_key=asset_ref,
        sha256=seed_data.AUDIO_SHA256,
        media_type="audio/wav",
        size_bytes=len(seed_data.AUDIO_BYTES),
        duration_ms=1_000,
    )


def _has_story_receipt(factory: Any, run_id: str, key: str) -> bool:
    receipts = story_tables.story_command_receipts
    with factory() as session:
        count = session.scalar(
            select(func.count())
            .select_from(receipts)
            .where(
                receipts.c.resource_ref == run_id,
                receipts.c.idempotency_key_sha256 == _idempotency_key_hash(key),
            )
        )
    return bool(count)


def _story_catalog_key(case: str) -> str:
    return stage_key("s7b", f"story-catalog-{case}")


def _ensure_p3_story_catalog_access(factory: Any) -> None:
    """Share an age-fit outdoor plant lesson that matches p3's drawing context."""

    with factory() as session:
        try:
            grant = _build_lesson_library_service(session).create_access_grant(
                organization_id=data.org_id("a"),
                lesson_id=data.lesson_id(seed_data.P3_ACTIVITY_LESSON_KEY),
                actor=data.ORG_A_TEACHERS[0],
                version_id=data.version_id(
                    seed_data.P3_ACTIVITY_LESSON_KEY,
                    seed_data.P3_ACTIVITY_LESSON_VERSION_NO,
                ),
                audience_kind="PARENT_GROUP",
                audience_ref=data.PARENT_GROUP_IDS[1],
                capability="VIEW",
                expires_at=None,
                idempotency_key=_story_catalog_key("p3-outdoor-lesson-grant"),
            )
        except LessonLibraryError as exc:
            raise StageError("S7B_P3_ACTIVITY_CATALOG_GRANT_FAILED") from exc
    if grant.get("state") != "ACTIVE":
        raise StageError("S7B_P3_ACTIVITY_CATALOG_GRANT_INVALID")


def _ensure_p5_story_catalog_access(factory: Any) -> tuple[str, str]:
    """Create and publish an age-appropriate lesson for p5 through the Lesson Library service."""

    teacher = data.ORG_A_TEACHERS[0]
    organization_id = data.org_id("a")
    content = LessonContentInputV1.model_validate(seed_data.P5_ACTIVITY_LESSON_CONTENT)
    with factory() as session:
        try:
            lesson = _build_lesson_library_service(session).create_lesson(
                organization_id=organization_id,
                actor=teacher,
                content=content,
                visibility="PRIVATE",
                idempotency_key=_story_catalog_key("p5-lesson"),
            )
        except LessonLibraryError as exc:
            raise StageError("S7B_P5_ACTIVITY_LESSON_CREATE_FAILED") from exc
    lesson_id = lesson.get("lesson_id")
    current_version = lesson.get("current_version")
    version_id = (
        current_version.get("version_id") if isinstance(current_version, dict) else None
    )
    if not isinstance(lesson_id, str) or not isinstance(version_id, str):
        raise StageError("S7B_P5_ACTIVITY_LESSON_INVALID")

    with factory() as session:
        try:
            grant = _build_lesson_library_service(session).create_access_grant(
                organization_id=organization_id,
                lesson_id=lesson_id,
                actor=teacher,
                version_id=version_id,
                audience_kind="PUBLIC",
                audience_ref=None,
                capability="VIEW",
                expires_at=None,
                idempotency_key=_story_catalog_key("p5-grant"),
            )
        except LessonLibraryError as exc:
            raise StageError("S7B_P5_ACTIVITY_CATALOG_GRANT_FAILED") from exc
    grant_id = grant.get("access_grant_id")
    if not isinstance(grant_id, str) or not grant_id:
        raise StageError("S7B_P5_ACTIVITY_CATALOG_GRANT_INVALID")

    with factory() as session:
        try:
            decision = _build_lesson_library_service(session).decide_access_grant(
                organization_id=organization_id,
                grant_id=grant_id,
                actor=data.manager_subject("a"),
                expected_revision=1,
                decision="APPROVE",
                reason=None,
                idempotency_key=_story_catalog_key("p5-approve"),
            )
        except LessonLibraryError as exc:
            raise StageError("S7B_P5_ACTIVITY_CATALOG_APPROVAL_FAILED") from exc
    if decision.get("state") != "ACTIVE":
        raise StageError("S7B_P5_ACTIVITY_CATALOG_APPROVAL_INVALID")
    return lesson_id, version_id


def _ensure_parent_activity_selection(
    factory: Any,
    principal: VerifiedPrincipal,
    record: ParentStoryRunRecord,
    selection_case: str,
) -> ParentStoryRevisionReservation | None:
    key = _story_key(selection_case)
    if _has_story_receipt(factory, record.run_id, key):
        return None

    if selection_case == "p3a_select_activity":
        _ensure_p3_story_catalog_access(factory)
        lesson_id = data.lesson_id(seed_data.P3_ACTIVITY_LESSON_KEY)
        version_id = data.version_id(
            seed_data.P3_ACTIVITY_LESSON_KEY,
            seed_data.P3_ACTIVITY_LESSON_VERSION_NO,
        )
    elif selection_case == "p5_select_activity":
        lesson_id, version_id = _ensure_p5_story_catalog_access(factory)
    else:
        raise StageError("S7B_ACTIVITY_SELECTION_CASE_UNKNOWN")
    started: list[ParentStoryRevisionReservation] = []
    with factory() as session:
        service = _build_activity_selection_service(session)
        try:
            listing = service.list_activities(principal=principal, run_id=record.run_id)
            candidates = [
                item
                for item in listing["items"]
                if item["activity_ref"]["lesson_id"] == lesson_id
                and item["activity_ref"]["version_id"] == version_id
                and item["activity_ref"]["activity_index"] == 0
            ]
            if not candidates:
                raise StageError("S7B_ACTIVITY_CATALOG_EMPTY")
            service.select_activity(
                principal=principal,
                run_id=record.run_id,
                expected_revision=record.run_revision,
                activity_ref=candidates[0]["activity_ref"],
                idempotency_key=key,
                on_story_started=started.append,
            )
        except (ParentStoryRunError, LessonLibraryError) as exc:
            raise _raise_command_error(exc) from None

    if len(started) > 1:
        raise StageError("S7B_MULTIPLE_FIRST_STORY_RESERVATIONS")
    return started[0] if started else None


def _submit_voice_idea(
    factory: Any,
    storage: ObjectStoragePort,
    principal: VerifiedPrincipal,
    run_id: str,
) -> None:
    key = _story_key("p3a_submit_idea")
    if _has_story_receipt(factory, run_id, key):
        return
    record = _get_run(factory, principal, run_id)
    voice = _ensure_voice_metadata(factory, storage, principal, run_id)
    fingerprint = idea_fingerprint(
        expected_run_revision=record.run_revision,
        text=None,
        audio_ref=voice.asset_key,
        correction=None,
    )
    with factory() as session:
        try:
            SqlParentStoryRunRepository(session).submit_idea(
                principal=principal,
                run_id=run_id,
                idempotency_key=key,
                fingerprint=fingerprint,
                expected_run_revision=record.run_revision,
                voice=voice,
            )
        except ParentStoryRunError as exc:
            raise _raise_command_error(exc) from None


def _ensure_drawing_attached(
    factory: Any,
    storage: ObjectStoragePort,
    principal: VerifiedPrincipal,
    run_id: str,
    case: str,
) -> None:
    key_case = {
        "p3-a": "p3a_attach",
        "p3-b": "p3b_attach",
        "p4": "p4_attach",
        "p5": "p5_attach",
    }[case]
    key = _story_key(key_case)
    if _has_story_receipt(factory, run_id, key):
        return
    record = _get_run(factory, principal, run_id)
    original = seed_data.DRAWING_BYTES[case]
    normalized = normalize_drawing(original, declared_media_type="image/png")
    original_ref = f"parent/{run_id}/s7b/{case}/original.png"
    fingerprint = drawing_attach_fingerprint(original_ref, record.run_revision)
    with factory() as session:
        try:
            prepared = SqlParentStoryRunRepository(session).prepare_drawing_attach(
                principal=principal,
                run_id=run_id,
                idempotency_key=key,
                fingerprint=fingerprint,
                expected_run_revision=record.run_revision,
            )
        except ParentStoryRunError as exc:
            raise _raise_command_error(exc) from None
    if prepared is not None:
        return
    original_sha256 = hashlib.sha256(original).hexdigest()
    storage.put_object(
        original_ref,
        io.BytesIO(original),
        content_type="image/png",
        content_length=len(original),
        metadata={"sha256": original_sha256},
    )
    with factory.begin() as session:
        session.execute(
            pg_insert(_ASSET_TABLE)
            .values(
                asset_ref=original_ref,
                asset_version=1,
                organization_id=None,
                owner_scope_kind="PARENT_ACCOUNT",
                owner_scope_ref=data.principal_scope_ref(data.SEED_ISSUER, principal.subject),
                content_sha256=original_sha256,
                media_type="image/png",
                source_refs=[run_id],
                derived_from_ref=None,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    CoreAssetMetadataModel.__table__.c.asset_ref,
                    CoreAssetMetadataModel.__table__.c.asset_version,
                ]
            )
        )
    with factory() as session:
        try:
            SqlParentStoryRunRepository(session).attach_uploaded_drawing(
                principal=principal,
                run_id=run_id,
                idempotency_key=key,
                fingerprint=fingerprint,
                expected_run_revision=record.run_revision,
                original_asset_ref=original_ref,
                original_sha256=original_sha256,
                original_media_type="image/png",
                original_size_bytes=len(original),
                scanner_name="seed-fixture-scanner",
                scanner_version="1",
                derived_png=normalized.png_bytes,
                derived_sha256=normalized.sha256,
                storage=storage,
            )
        except ParentStoryRunError as exc:
            raise _raise_command_error(exc) from None


def _ensure_drawing_analysis(
    factory: Any,
    principal: VerifiedPrincipal,
    run_id: str,
    case: str,
    analyzer: FixtureDrawingAnalyzer,
    session_factory: Any,
) -> ParentStoryRunRecord:
    record = _get_run(factory, principal, run_id)
    expected_original_ref = f"parent/{run_id}/s7b/{case}/original.png"
    with factory() as session:
        try:
            input_record = SqlParentStoryRunRepository(session).read_current_input(
                principal=principal, run_id=run_id
            )
        except ParentStoryRunError as exc:
            raise _raise_command_error(exc) from None
    if input_record.original_asset_ref != expected_original_ref:
        # A Parent may have replaced the seed drawing since the previous stage pass.
        return record
    if record.run_state == "INPUT_PROCESSING" and record.job_state == "QUEUED":
        if record.current_input_revision is None:
            raise StageError("S7B_CURRENT_INPUT_MISSING")
        if input_record.derived_sha256 is None:
            raise StageError("S7B_DERIVED_DRAWING_MISSING")
        analyzer.register(input_record.derived_sha256, seed_data.DRAWING_RESULTS[case])
        ParentInputJobRunner(session_factory, analyzer).run(
            principal, run_id, record.current_input_revision
        )
        record = _get_run(factory, principal, run_id)
    if case == "p3-b":
        if record.run_state == "INPUT_REVIEW":
            if record.error_code != "MULTI_CHILD_NOT_SUPPORTED":
                raise StageError("S7B_DRAWING_FAILURE_UNEXPECTED")
        elif record.run_state == "INPUT_PROCESSING":
            raise StageError("S7B_DRAWING_ANALYSIS_STATE_UNEXPECTED")
        return record
    if case == "p3-a":
        if record.run_state == "INPUT_PROCESSING":
            if record.job_state != "SUCCEEDED" or record.understanding_revision is None:
                raise StageError("S7B_DRAWING_ANALYSIS_STATE_UNEXPECTED")
            return record
        if record.run_state == "INPUT_REVIEW":
            return record
    if record.run_state in {
        "SUBJECT_REVIEW",
        "PREPARATION_REVIEW",
        "SCRIPT_GENERATING",
        "SCRIPT_GENERATION_UNKNOWN",
        "SCRIPT_REVIEW",
        "VIDEO_ADMISSION_PENDING",
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "COMPLETED",
    }:
        return record
    raise StageError("S7B_DRAWING_ANALYSIS_STATE_UNEXPECTED")


def _latest_transcript(factory: Any, run_id: str) -> Mapping[str, Any] | None:
    table = story_tables.transcript_revisions
    with factory() as session:
        row = (
            session.execute(
                select(table)
                .where(table.c.run_id == run_id)
                .order_by(table.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
    return cast(Mapping[str, Any] | None, row)


def _ensure_voice_transcript(
    factory: Any,
    principal: VerifiedPrincipal,
    run_id: str,
    transcriber: FixtureSpeechTranscriber,
    session_factory: Any,
) -> None:
    row = _latest_transcript(factory, run_id)
    if row is None:
        raise StageError("S7B_TRANSCRIPT_MISSING")
    if row["state"] == "PENDING":
        transcriber.register(seed_data.AUDIO_SHA256, seed_data.P3A_TRANSCRIPT)
        ParentSpeechJobRunner(session_factory, transcriber).run(
            principal, run_id, str(row["transcript_revision_id"])
        )
        row = _latest_transcript(factory, run_id)
    if row is None or row["state"] not in {"NEEDS_CONFIRMATION", "CONFIRMED"}:
        raise StageError("S7B_TRANSCRIPT_NOT_READY")
    key = _story_key("p3a_confirm_transcript")
    if row["state"] == "NEEDS_CONFIRMATION" and not _has_story_receipt(factory, run_id, key):
        with factory() as session:
            try:
                SqlParentStoryRunRepository(session).confirm_transcript(
                    principal=principal,
                    run_id=run_id,
                    idempotency_key=key,
                    expected_transcript_revision=int(row["revision_no"]),
                    transcript_sha256=str(row["transcript_sha256"]),
                )
            except ParentStoryRunError as exc:
                raise _raise_command_error(exc) from None


def _confirm_subject(
    factory: Any,
    principal: VerifiedPrincipal,
    run_id: str,
    subject: str,
    key_case: str,
) -> ParentStoryRunRecord:
    record = _get_run(factory, principal, run_id)
    key = _story_key(key_case)
    if not _has_story_receipt(factory, run_id, key):
        if record.run_state == "SUBJECT_REVIEW":
            if record.understanding_revision is None:
                raise StageError("S7B_UNDERSTANDING_MISSING")
            with factory() as session:
                try:
                    service = _build_story_service(session)
                    service.confirm_subject(
                        principal=principal,
                        run_id=run_id,
                        expected_understanding_revision=record.understanding_revision,
                        confirmed_subject=subject,
                        idempotency_key=key,
                    )
                except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
                    raise _raise_command_error(exc) from None
            record = _get_run(factory, principal, run_id)
        elif record.run_state not in {
            "PREPARATION_REVIEW",
            "SCRIPT_GENERATING",
            "SCRIPT_GENERATION_UNKNOWN",
            "SCRIPT_REVIEW",
            "VIDEO_ADMISSION_PENDING",
            "VIDEO_QUEUED",
            "VIDEO_GENERATING",
            "VIDEO_SAFETY_VALIDATING",
            "VIDEO_READY",
            "COMPLETED",
        }:
            raise StageError("S7B_SUBJECT_CONFIRMATION_STATE_UNEXPECTED")
    if record.run_state not in {
        "PREPARATION_REVIEW",
        "SCRIPT_GENERATING",
        "SCRIPT_GENERATION_UNKNOWN",
        "SCRIPT_REVIEW",
        "VIDEO_ADMISSION_PENDING",
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "COMPLETED",
    }:
        raise StageError("S7B_SUBJECT_CONFIRMATION_STATE_UNEXPECTED")
    return record


def _ensure_story_revision(
    factory: Any,
    principal: VerifiedPrincipal,
    run_id: str,
    story_case: str,
    result: StoryGenerationResult,
    reserve_key_case: str,
    confirm_key_case: str,
    session_factory: Any,
) -> ParentStoryRunRecord:
    record = _get_run(factory, principal, run_id)
    if record.understanding_revision is None:
        raise StageError("S7B_UNDERSTANDING_MISSING")
    reservation: ParentStoryRevisionReservation | None = None
    if record.story_revision_id is None:
        selection_cases = {"p3-a": "p3a_select_activity", "p5": "p5_select_activity"}
        selection_case = selection_cases.get(story_case)
        if selection_case is None:
            raise StageError("S7B_ACTIVITY_SELECTION_CASE_MISSING")
        reservation = _ensure_parent_activity_selection(
            factory, principal, record, selection_case
        )
        if reservation is None:
            with factory() as session:
                try:
                    identity = _require_parent(session, principal)
                    reservation = _build_story_service(session).reserve_story_revision(
                        principal=principal,
                        account_id=identity.account_id,
                        run_id=run_id,
                        expected_understanding_revision=record.understanding_revision,
                        rewrite_instruction=None,
                        idempotency_key=_story_key(reserve_key_case),
                        model_id="sketch2life-story-v1",
                        model_revision="1",
                        prompt_version="seed-story.v1",
                    )
                except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
                    raise _raise_command_error(exc) from None
    if reservation is not None and not reservation.replayed:
        generator = FixtureStoryGenerator()
        generator.register(worker_input_sha256(reservation.worker_input), result)
        # The first story is generated synchronously by the route (parent_ai.py): generate, then
        # store through the shared service. The rewrite runner is only for rewrites.
        generated = generator.generate(reservation.worker_input)
        with factory() as session:
            try:
                complete_generated_story(
                    SqlParentStoryRunRepository(session),
                    principal=principal,
                    reservation=reservation,
                    raw_story=generated.story,
                    provider_call_id=generated.call_id,
                    model_id="sketch2life-story-v1",
                    model_revision="1",
                )
            except (ParentStoryRunError, ParentStoryRunServiceError, StoryOutputInvalid) as exc:
                raise _raise_command_error(exc) from None
    record = _get_run(factory, principal, run_id)
    if record.story_sha256 is None or record.story_revision_id is None:
        raise StageError("S7B_STORY_REVISION_MISSING")
    confirm_key = _story_key(confirm_key_case)
    if not _has_story_receipt(factory, run_id, confirm_key):
        if record.run_state != "SCRIPT_REVIEW":
            raise StageError("S7B_STORY_CONFIRMATION_STATE_UNEXPECTED")
        with factory() as session:
            try:
                _build_story_service(session).confirm_story_revision(
                    principal=principal,
                    run_id=run_id,
                    expected_revision=record.story_revision_no or 0,
                    expected_story_sha256=record.story_sha256,
                    idempotency_key=confirm_key,
                )
            except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
                raise _raise_command_error(exc) from None
    record = _get_run(factory, principal, run_id)
    if record.story_status != "CONFIRMED":
        raise StageError("S7B_STORY_NOT_CONFIRMED")
    return record


def _existing_video_generation(factory: Any, run_id: str, key: str) -> str | None:
    table = story_tables.video_generations
    with factory() as session:
        found = session.scalar(
            select(table.c.video_generation_id).where(
                table.c.story_run_id == run_id,
                table.c.request_idempotency_key_hash == video_idempotency_key_hash(key),
            )
        )
    return None if found is None else str(found)


def _ensure_video_ready(
    factory: Any,
    principal: VerifiedPrincipal,
    run_id: str,
    key_case: str,
    storage: ObjectStoragePort,
    adapters: Any,
    *,
    allow_completed: bool = False,
) -> ParentStoryRunRecord:
    key = _story_key(key_case)
    generation_id = _existing_video_generation(factory, run_id, key)
    record = _get_run(factory, principal, run_id)
    if generation_id is None:
        if record.run_state != "SCRIPT_REVIEW" or record.story_sha256 is None:
            raise StageError("S7B_VIDEO_REQUEST_STATE_UNEXPECTED")
        with factory() as session:
            repository = SqlStoryVideoRepository(session)
            try:
                outcome = StoryVideoAdmissionService(repository, adapters).request(
                    principal=principal,
                    run_id=run_id,
                    expected_revision=record.run_revision,
                    story_sha256=record.story_sha256,
                    quality_reason_code=None,
                    idempotency_key=key,
                )
            except ParentStoryRunError as exc:
                raise _raise_command_error(exc) from None
        if outcome.record is None:
            raise StageError("S7B_VIDEO_ADMISSION_NOT_ACCEPTED")
        generation_id = outcome.record.generation_id
    runner = FixtureVideoRunner(factory, storage, adapters)
    runner.run_to_end(generation_id)
    record = _get_run(factory, principal, run_id)
    allowed = {"VIDEO_READY", "COMPLETED"} if allow_completed else {"VIDEO_READY"}
    if record.run_state not in allowed:
        raise StageError("S7B_VIDEO_GENERATION_NOT_READY")
    return record


def _complete_run(
    factory: Any,
    principal: VerifiedPrincipal,
    run_id: str,
    key_case: str,
) -> ParentStoryRunRecord:
    record = _get_run(factory, principal, run_id)
    if record.run_state != "COMPLETED":
        if record.run_state != "VIDEO_READY":
            raise StageError("S7B_COMPLETION_STATE_UNEXPECTED")
        with factory() as session:
            try:
                StoryVideoCommandService(SqlStoryVideoRepository(session)).complete(
                    principal=principal,
                    run_id=run_id,
                    expected_revision=record.run_revision,
                    idempotency_key=_story_key(key_case),
                )
            except ParentStoryRunError as exc:
                raise _raise_command_error(exc) from None
        record = _get_run(factory, principal, run_id)
    if record.run_state != "COMPLETED":
        raise StageError("S7B_RUN_NOT_COMPLETED")
    return record


def _seed_abandoned_history(factory: Any) -> None:
    run, input_row = seed_data.abandoned_rows(data.SEED_ISSUER)
    with factory.begin() as session:
        session.execute(
            pg_insert(story_tables.story_runs)
            .values(**run)
            .on_conflict_do_nothing(index_elements=[story_tables.story_runs.c.run_id])
        )
        session.execute(
            pg_insert(story_tables.run_inputs)
            .values(**input_row)
            .on_conflict_do_nothing(index_elements=[story_tables.run_inputs.c.run_input_id])
        )


def _prepare_parent_runs(
    factory: Any,
    storage: ObjectStoragePort,
    analyzer: FixtureDrawingAnalyzer,
    transcriber: FixtureSpeechTranscriber,
    adapters: Any,
) -> None:
    profile_id = _create_k6_profile(factory)
    principal_p3 = _principal("p3")
    session_factory = factory

    p3a = _ensure_new_parent_run(
        factory,
        profile_id=profile_id,
        topic=seed_data.P3_RUN_A[0],
        idea=seed_data.P3_RUN_A[1],
        create_case="p3a_create",
        confirm_case="p3a_confirm_context",
    )
    _submit_voice_idea(factory, storage, principal_p3, p3a.run_id)
    _ensure_drawing_attached(factory, storage, principal_p3, p3a.run_id, "p3-a")
    _ensure_drawing_analysis(factory, principal_p3, p3a.run_id, "p3-a", analyzer, session_factory)
    _ensure_voice_transcript(factory, principal_p3, p3a.run_id, transcriber, session_factory)
    p3a = _confirm_subject(
        factory,
        principal_p3,
        p3a.run_id,
        seed_data.DRAWING_RESULTS["p3-a"].subject,
        "p3a_confirm_subject",
    )
    p3a = _ensure_story_revision(
        factory,
        principal_p3,
        p3a.run_id,
        "p3-a",
        seed_data.STORY_RESULTS["p3-a"],
        "p3a_reserve_story",
        "p3a_confirm_story",
        session_factory,
    )
    p3a = _ensure_video_ready(
        factory,
        principal_p3,
        p3a.run_id,
        "p3a_request_video",
        storage,
        adapters,
        allow_completed=True,
    )
    _complete_run(factory, principal_p3, p3a.run_id, "p3a_complete")

    p3b = _ensure_new_parent_run(
        factory,
        profile_id=profile_id,
        topic=seed_data.P3_RUN_B[0],
        idea=seed_data.P3_RUN_B[1],
        create_case="p3b_create",
        confirm_case="p3b_confirm_context",
    )
    _ensure_drawing_attached(factory, storage, principal_p3, p3b.run_id, "p3-b")
    _ensure_drawing_analysis(factory, principal_p3, p3b.run_id, "p3-b", analyzer, session_factory)

    for parent_key, drawing_case, subject, reserve_case, confirm_case, video_case, story_key in (
        ("p4", "p4", seed_data.P4_SUBJECT, None, None, None, None),
        (
            "p5",
            "p5",
            seed_data.P5_SUBJECT,
            "p5_reserve_story",
            "p5_confirm_story",
            "p5_request_video",
            "p5",
        ),
    ):
        spec = next(
            (item for item in data.S7A_RUN_SPECS if item[0] == parent_key),
            None,
        )
        if spec is None:
            raise StageError("S7B_S7A_RUN_SPEC_MISSING")
        _, profile_key, topic, idea = spec
        principal = _principal(parent_key)
        with factory() as session:
            _require_parent(session, principal)
            try:
                record = _build_story_service(session).replay_create_run(
                    principal=principal,
                    account_id=data.parent_account_id(parent_key),
                    parent_profile_id=data.parent_profile_id(profile_key),
                    idempotency_key=data.s7a_create_key(parent_key),
                    topic=topic,
                    adult_confirmed_idea=idea,
                )
            except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
                raise _raise_command_error(exc) from None
        if not isinstance(record, ParentStoryRunRecord) or not _is_seed_run(
            record, data.parent_profile_id(profile_key), topic, idea
        ):
            raise StageError("S7B_S7A_RUN_MISMATCH")
        if not record.context_confirmed:
            raise StageError("S7B_S7A_CONTEXT_NOT_CONFIRMED")
        _ensure_drawing_attached(factory, storage, principal, record.run_id, drawing_case)
        record = _ensure_drawing_analysis(
            factory, principal, record.run_id, drawing_case, analyzer, session_factory
        )
        if parent_key == "p4":
            if record.run_state not in {
                "SUBJECT_REVIEW",
                "PREPARATION_REVIEW",
                "SCRIPT_GENERATING",
                "SCRIPT_GENERATION_UNKNOWN",
                "SCRIPT_REVIEW",
                "VIDEO_ADMISSION_PENDING",
                "VIDEO_QUEUED",
                "VIDEO_GENERATING",
                "VIDEO_SAFETY_VALIDATING",
                "VIDEO_READY",
                "COMPLETED",
            }:
                raise StageError("S7B_P4_SUBJECT_REVIEW_MISSING")
            continue
        record = _confirm_subject(
            factory,
            principal,
            record.run_id,
            subject,
            "p5_confirm_subject",
        )
        if reserve_case is None or confirm_case is None or video_case is None or story_key is None:
            raise StageError("S7B_P5_SCRIPT_CONFIGURATION_MISSING")
        record = _ensure_story_revision(
            factory,
            principal,
            record.run_id,
            story_key,
            seed_data.STORY_RESULTS[story_key],
            reserve_case,
            confirm_case,
            session_factory,
        )
        _ensure_video_ready(
            factory,
            principal,
            record.run_id,
            video_case,
            storage,
            adapters,
            allow_completed=True,
        )


def _owned_run_ids(connection: Connection) -> tuple[str, ...]:
    receipts = story_tables.story_command_receipts
    create_keys = [
        _story_key("p3a_create"),
        _story_key("p3b_create"),
        *(data.s7a_create_key(parent_key) for parent_key in ("p4", "p5")),
    ]
    scope_refs = [
        data.principal_scope_ref(data.SEED_ISSUER, data.PARENT_SUBJECTS[parent_key])
        for parent_key in ("p3", "p4", "p5")
    ]
    rows = connection.execute(
        select(receipts.c.resource_ref).where(
            receipts.c.operation == "CREATE_RUN",
            receipts.c.idempotency_scope_kind == "COLLECTION",
            receipts.c.actor_scope_kind == "PARENT_ACCOUNT",
            receipts.c.actor_scope_ref.in_(scope_refs),
            receipts.c.idempotency_key_sha256.in_(
                [_idempotency_key_hash(key) for key in create_keys]
            ),
        )
    ).scalars()
    return tuple(sorted({seed_data.ABANDONED_RUN_ID, *(str(run_id) for run_id in rows)}))


def _count(connection: Connection, table: Any, *conditions: Any) -> int:
    count = connection.execute(
        select(func.count()).select_from(table).where(*conditions)
    ).scalar_one()
    return int(count)


def _lesson_catalog_receipt_response(
    connection: Connection, case: str, actor: str
) -> Mapping[str, Any] | None:
    response = connection.execute(
        select(LESSON_COMMAND_RECEIPTS.c.response_json).where(
            LESSON_COMMAND_RECEIPTS.c.organization_id == data.org_id("a"),
            LESSON_COMMAND_RECEIPTS.c.principal_ref == actor,
            LESSON_COMMAND_RECEIPTS.c.idempotency_key == _story_catalog_key(case),
        )
    ).scalar_one_or_none()
    return response if isinstance(response, Mapping) else None


def count_s7b_rows(connection: Connection) -> dict[str, int]:
    """Count S7b data through its five deterministic or receipt-owned Parent run ids."""

    runs = story_tables.story_runs
    run_inputs = story_tables.run_inputs
    run_ids = _owned_run_ids(connection)
    run_filter = runs.c.run_id.in_(run_ids)
    input_filter = run_inputs.c.run_id.in_(run_ids)
    revision_ids = select(story_tables.story_revisions.c.story_revision_id).where(
        story_tables.story_revisions.c.run_id.in_(run_ids)
    )
    video_ids = select(story_tables.video_generations.c.video_generation_id).where(
        story_tables.video_generations.c.story_run_id.in_(run_ids)
    )
    parent_key_hash = hashlib.sha256(_story_key("profile_create").encode("ascii")).digest()
    profile_receipt_table = ParentCommandReceiptModel.__table__
    profile_receipt = connection.execute(
        select(profile_receipt_table.c.response_body).where(
            profile_receipt_table.c.principal_issuer == data.SEED_ISSUER,
            profile_receipt_table.c.principal_subject == data.PARENT_SUBJECTS["p3"],
            profile_receipt_table.c.operation_scope == "create_profile",
            profile_receipt_table.c.resource_scope == "collection",
            profile_receipt_table.c.key_hash == parent_key_hash,
        )
    ).scalar_one_or_none()
    profile_id = None if profile_receipt is None else UUID(str(profile_receipt["profile_id"]))
    if profile_id is None:
        profile_count = revision_count = 0
    else:
        profile_count = _count(
            connection,
            ParentChildProfileModel.__table__,
            ParentChildProfileModel.__table__.c.parent_profile_id == profile_id,
        )
        revision_count = _count(
            connection,
            ParentProfileRevisionModel.__table__,
            ParentProfileRevisionModel.__table__.c.parent_profile_id == profile_id,
        )
    story_receipt_hashes = [
        _idempotency_key_hash(_story_key(case)) for case in seed_data.STORY_RECEIPT_CASES
    ]
    teacher = data.ORG_A_TEACHERS[0]
    p3_group_grant = _lesson_catalog_receipt_response(
        connection, "p3-outdoor-lesson-grant", teacher
    )
    p5_lesson = _lesson_catalog_receipt_response(connection, "p5-lesson", teacher)
    p5_grant = _lesson_catalog_receipt_response(connection, "p5-grant", teacher)
    p5_current_version = p5_lesson.get("current_version") if p5_lesson is not None else None
    p5_version_id = (
        p5_current_version.get("version_id")
        if isinstance(p5_current_version, Mapping)
        else None
    )
    p3_group_grant_id = (
        p3_group_grant.get("access_grant_id") if p3_group_grant is not None else None
    )
    p5_grant_id = p5_grant.get("access_grant_id") if p5_grant is not None else None
    lesson_catalog_keys = tuple(
        _story_catalog_key(case) for case in seed_data.STORY_CATALOG_RECEIPT_CASES
    )
    scope_refs = [
        data.principal_scope_ref(data.SEED_ISSUER, data.PARENT_SUBJECTS[parent_key])
        for parent_key in ("p3", "p4", "p5")
    ]
    metadata = CoreAssetMetadataModel.__table__
    metadata_sources = or_(*(metadata.c.source_refs.contains([run_id]) for run_id in run_ids))
    story_scenes = story_tables.story_scenes
    video_scenes = story_tables.video_generation_scenes
    asset_lineage = story_tables.asset_lineage
    return {
        "story_runs_s7b": _count(connection, runs, run_filter),
        "story_run_inputs_s7b": _count(connection, run_inputs, input_filter),
        "story_story_revisions_s7b": _count(
            connection,
            story_tables.story_revisions,
            story_tables.story_revisions.c.run_id.in_(run_ids),
        ),
        "story_video_generations_s7b": _count(
            connection,
            story_tables.video_generations,
            story_tables.video_generations.c.story_run_id.in_(run_ids),
        ),
        "story_transcript_revisions_s7b": _count(
            connection,
            story_tables.transcript_revisions,
            story_tables.transcript_revisions.c.run_id.in_(run_ids),
        ),
        "story_activity_selections_s7b": _count(
            connection,
            story_tables.activity_selections,
            story_tables.activity_selections.c.run_id.in_(run_ids),
        ),
        "parent_child_profiles_s7b": profile_count,
        "parent_profile_revisions_s7b": revision_count,
        "story_understanding_revisions_s7b": _count(
            connection,
            story_tables.understanding_revisions,
            story_tables.understanding_revisions.c.run_id.in_(run_ids),
        ),
        "story_review_decisions_s7b": _count(
            connection,
            story_tables.review_decisions,
            story_tables.review_decisions.c.run_id.in_(run_ids),
        ),
        "story_story_revision_reviews_s7b": _count(
            connection,
            story_tables.story_revision_reviews,
            story_tables.story_revision_reviews.c.run_id.in_(run_ids),
        ),
        "story_story_scenes_s7b": _count(
            connection, story_scenes, story_scenes.c.story_revision_id.in_(revision_ids)
        ),
        "story_video_generation_scenes_s7b": _count(
            connection, video_scenes, video_scenes.c.video_generation_id.in_(video_ids)
        ),
        "story_asset_lineage_s7b": _count(
            connection,
            asset_lineage,
            asset_lineage.c.source_asset_ref.in_(
                select(run_inputs.c.original_asset_ref).where(
                    input_filter, run_inputs.c.original_asset_ref.is_not(None)
                )
            ),
        ),
        "story_command_receipts_s7b": _count(
            connection,
            story_tables.story_command_receipts,
            story_tables.story_command_receipts.c.resource_ref.in_(run_ids),
            story_tables.story_command_receipts.c.actor_scope_ref.in_(scope_refs),
            story_tables.story_command_receipts.c.idempotency_key_sha256.in_(story_receipt_hashes),
        ),
        "parent_command_receipts_s7b": _count(
            connection,
            profile_receipt_table,
            profile_receipt_table.c.principal_issuer == data.SEED_ISSUER,
            profile_receipt_table.c.principal_subject == data.PARENT_SUBJECTS["p3"],
            profile_receipt_table.c.operation_scope == "create_profile",
            profile_receipt_table.c.resource_scope == "collection",
            profile_receipt_table.c.key_hash == parent_key_hash,
        ),
        "core_asset_metadata_s7b": _count(
            connection,
            metadata,
            metadata.c.owner_scope_kind == "PARENT_ACCOUNT",
            metadata.c.owner_scope_ref.in_(scope_refs),
            metadata_sources,
        ),
        "lesson_library_items_s7b": (
            _count(
                connection,
                LESSON_LIBRARY_ITEMS,
                LESSON_LIBRARY_ITEMS.c.lesson_id == p5_lesson.get("lesson_id"),
            )
            if p5_lesson is not None and isinstance(p5_lesson.get("lesson_id"), str)
            else 0
        ),
        "lesson_library_versions_s7b": (
            _count(
                connection,
                LESSON_LIBRARY_VERSIONS,
                LESSON_LIBRARY_VERSIONS.c.version_id == p5_version_id,
            )
            if isinstance(p5_version_id, str)
            else 0
        ),
        "lesson_version_activities_s7b": (
            _count(
                connection,
                LESSON_VERSION_ACTIVITIES,
                LESSON_VERSION_ACTIVITIES.c.version_id == p5_version_id,
            )
            if isinstance(p5_version_id, str)
            else 0
        ),
        "lesson_access_grants_s7b": (
            _count(
                connection,
                LESSON_ACCESS_GRANTS,
                LESSON_ACCESS_GRANTS.c.access_grant_id.in_(
                    [
                        grant_id
                        for grant_id in (p3_group_grant_id, p5_grant_id)
                        if isinstance(grant_id, str)
                    ]
                ),
            )
            if isinstance(p3_group_grant_id, str) and isinstance(p5_grant_id, str)
            else 0
        ),
        "lesson_command_receipts_s7b": _count(
            connection,
            LESSON_COMMAND_RECEIPTS,
            LESSON_COMMAND_RECEIPTS.c.organization_id == data.org_id("a"),
            LESSON_COMMAND_RECEIPTS.c.idempotency_key.in_(lesson_catalog_keys),
        ),
    }


def run_s7b(engine: Engine) -> StageResult:
    factory = create_core_session_factory(engine)
    try:
        with engine.connect() as connection:
            before = count_s7b_rows(connection)
        storage = MemoryObjectStorage()
        analyzer = FixtureDrawingAnalyzer()
        transcriber = FixtureSpeechTranscriber()
        adapters = build_local_video_adapters(env="test")
        _seed_abandoned_history(factory)
        _prepare_parent_runs(factory, storage, analyzer, transcriber, adapters)
        with engine.connect() as connection:
            after = count_s7b_rows(connection)
        return StageResult(
            name="s7b_story_states",
            before=before,
            after=after,
            expected=seed_data.EXPECTED,
        )
    except StageError:
        raise
    except (ParentStoryRunError, ParentStoryRunServiceError, ParentProfileError) as exc:
        raise _raise_command_error(exc) from None
    except SQLAlchemyError:
        raise
    except Exception:
        raise StageError("S7B_STAGE_FAILED") from None


def main() -> int:
    return run_stage_main(run_s7b, stage="s7b")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["MemoryObjectStorage", "count_s7b_rows", "main", "run_s7b"]
