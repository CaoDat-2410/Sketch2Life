"""Occurrence source documents: attach a completed upload and read it (FEAT-066 goal v3, T-3b).

SRS l.545-546, l.1437, l.1653 (``POST /v1/lesson-occurrences/{id}/documents``: attach the asset of a
completed upload session; PDF, DOCX or PPTX, 25 MB, 100 pages or slides; the source hash is verified
by the server; 202 extraction job and source ref), l.1692 (no bucket, key or URL leaves the API),
l.1696-1699 (idempotency, revisions and hashes), l.1708 (review of the text).

Order of work (plan review R1 F-03): authorise and take a snapshot with no row lock, release the
database connection, read the object, verify size and SHA-256, parse under a deadline and a
concurrency cap, and only then open the write transaction: lock the occurrence and the upload
session, re-check everything the snapshot read, insert the document, revision 1 and the finished
job, write the audit entry and the receipt, commit. Locks are therefore held for milliseconds and
never during storage or parser work. Every refusal of the file (type, encryption, size, pages, text,
checksum) is answered before any row is written, so a bad file leaves no document and no job and the
Teacher can upload a replacement.

TD-15 and the deviation from SRS l.1940-1941 are recorded in T-3b-DEC-2: the parser runs in a
bounded thread of the API process, not in a separate resource-limited worker.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import UTC, datetime
from tempfile import SpooledTemporaryFile
from typing import Any, BinaryIO, cast
from uuid import uuid4

from sqlalchemy import func, literal, select, tuple_
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.job_kinds import LESSON_SOURCE_EXTRACTION_JOB_TYPE
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.inline_jobs import InlineJobRecorder, InlineSucceededJob
from sketch2life.application.ports.lesson_documents import (
    LessonDocumentExtraction,
    LessonDocumentParser,
    LessonDocumentRejected,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.upload_sessions import ORGANIZATION_SCOPE
from sketch2life.contracts.schemas.lesson_occurrences import (
    AttachOccurrenceDocumentRequestV1,
    EditDocumentRevisionRequestV1,
)
from sketch2life.domain.lesson_occurrences.documents import (
    JOB_POLICY_ID,
    JOB_PURPOSE_CODE,
    MAX_DOCUMENT_BYTES,
    MAX_REVISIONS_PER_DOCUMENT,
    decode_document_cursor,
    decode_revision_cursor,
    derive_warnings,
    edit_fingerprint,
    edit_text_problem,
    encode_document_cursor,
    encode_revision_cursor,
    map_parser_rejection,
    revision_ref,
    storable_text_problem,
    text_sha256,
    upload_id_from_handle,
)
from sketch2life.infrastructure.ai_jobs.inline_recorder import SqlInlineJobRecorder
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    authorize_occurrence,
    not_found,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    SOURCE_DOCUMENTS,
)
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.infrastructure.persistence.core_models import (
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
)
from sketch2life.infrastructure.uploads.purposes import (
    DOCUMENT_EXTENSIONS,
    OCCURRENCE_DOCUMENT,
    document_media_type_for,
)
from sketch2life.infrastructure.uploads.service import resolve_asset_key

ATTACH_RECEIPT_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/documents"
AUDIT_ATTACH_ACTION = "lesson.source_document.create"
EDIT_RECEIPT_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions"
AUDIT_EDIT_ACTION = "lesson.document_revision.create"
READ_CHUNK_BYTES = 64 * 1024
SPOOL_MEMORY_BYTES = 5 * 1024 * 1024
MAX_PAGE_SIZE = 100

PARSE_MAX_CONCURRENCY = 2
PARSE_QUEUE_WAIT_SECONDS = 5.0
PARSE_DEADLINE_SECONDS = 30.0
RETRY_AFTER_SECONDS = 5


class DocumentError(LessonOccurrenceError):
    """A refusal with status and public code; ``retry_after`` is set for a busy parser."""

    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        field_errors: list[dict[str, str]] | None = None,
        retry_after: int | None = None,
        current_version: int | None = None,
        etag: str | None = None,
    ) -> None:
        super().__init__(
            status_code, code, field_errors=field_errors, current_version=current_version
        )
        self.retry_after = retry_after
        self.etag = etag


# --------------------------------------------------------------------------- parse gate
class ParseGate:
    """Bounded, time-limited parser execution inside the API process (T-3b-DEC-2).

    At most ``max_concurrent`` parses run at once; a request that cannot get a slot within
    ``queue_wait_seconds`` is answered 503 so parallel uploads cannot starve the API. A parse that
    exceeds ``deadline_seconds`` is refused as unreadable content. A Python thread cannot be killed:
    the slot is released only when the worker really returns, so the cap bounds the real number of
    runaway parses; the caller closes the file on a timeout, which ends any parser that is still
    reading it.
    """

    def __init__(
        self,
        *,
        max_concurrent: int = PARSE_MAX_CONCURRENCY,
        queue_wait_seconds: float = PARSE_QUEUE_WAIT_SECONDS,
        deadline_seconds: float = PARSE_DEADLINE_SECONDS,
    ) -> None:
        if max_concurrent < 1 or queue_wait_seconds < 0 or deadline_seconds <= 0:
            raise ValueError("parse gate bounds are invalid")
        self.deadline_seconds = deadline_seconds
        self._queue_wait = queue_wait_seconds
        self._slots = threading.BoundedSemaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(
            max_workers=max_concurrent, thread_name_prefix="lesson-document-parse"
        )

    def run(
        self, parser: LessonDocumentParser, file_obj: BinaryIO, *, file_extension: str
    ) -> LessonDocumentExtraction:
        if not self._slots.acquire(timeout=self._queue_wait):
            raise DocumentError(503, "PROVIDER_UNAVAILABLE", retry_after=RETRY_AFTER_SECONDS)
        try:
            future: Future[LessonDocumentExtraction] = self._executor.submit(
                parser.extract, file_obj, file_extension=file_extension
            )
        except BaseException:
            self._slots.release()
            raise
        future.add_done_callback(lambda _done: self._slots.release())
        try:
            return future.result(timeout=self.deadline_seconds)
        except FutureTimeout:
            future.cancel()
            raise DocumentError(400, "INVALID_FILE_CONTENT") from None
        except LessonDocumentRejected as rejected:
            status, code = map_parser_rejection(rejected.code)
            raise DocumentError(status, code) from None
        except Exception:
            # Any other parser fault is unreadable content, never a 500 (and never echoed).
            raise DocumentError(400, "INVALID_FILE_CONTENT") from None


_DEFAULT_GATE: ParseGate | None = None
_DEFAULT_GATE_LOCK = threading.Lock()


def default_parse_gate() -> ParseGate:
    global _DEFAULT_GATE
    with _DEFAULT_GATE_LOCK:
        if _DEFAULT_GATE is None:
            _DEFAULT_GATE = ParseGate()
        return _DEFAULT_GATE


# --------------------------------------------------------------------------- value objects
@dataclass(frozen=True, slots=True)
class AttachResult:
    body: dict[str, Any]
    replayed: bool


@dataclass(frozen=True, slots=True)
class _Candidate:
    """What the snapshot established about the asset (no row lock held)."""

    upload_id: str
    asset_key: str
    organization_id: str
    file_name: str
    file_extension: str
    media_type: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class _Extracted:
    extraction: LessonDocumentExtraction
    text: str
    warnings: list[str]


def attach_fingerprint(occurrence_id: str, asset_ref: str) -> str:
    canonical = json.dumps(
        {"occurrence_id": occurrence_id, "asset_ref": asset_ref},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def extension_of(file_name: str) -> str | None:
    """Lower-case extension (with the dot) when it is one of the three document types."""
    suffix = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return suffix if suffix in DOCUMENT_EXTENSIONS else None


@dataclass(frozen=True, slots=True)
class EditResult:
    """A revision edit: the body, 201 (new revision) or 200 (no change), and replay flag."""

    body: dict[str, Any]
    status_code: int
    replayed: bool


def accepted_body(source_document_id: str, job_id: str) -> dict[str, Any]:
    return {
        "contract": "LessonSourceDocumentAcceptedV1",
        "source_document_id": source_document_id,
        "document_revision_no": 1,
        "job": {"job_id": job_id, "target_kind": "LESSON_SOURCE_DOCUMENT", "state": "succeeded"},
    }


class OccurrenceDocumentService:
    def __init__(
        self,
        db: Session,
        *,
        storage: ObjectStoragePort | None,
        parser: LessonDocumentParser | None,
        gate: ParseGate | None = None,
        recorder_factory: Callable[[Session], InlineJobRecorder] | None = None,
    ) -> None:
        self.db = db
        self._storage = storage
        self._parser = parser
        self._gate = gate or default_parse_gate()
        self._recorder_factory = recorder_factory or _sql_recorder

    # ------------------------------------------------------------------ attach
    def attach(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        payload: AttachOccurrenceDocumentRequestV1,
        idempotency_key: str,
    ) -> AttachResult:
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        fingerprint = attach_fingerprint(occurrence_id, payload.asset_ref)
        access = authorize_occurrence(self.db, principal, occurrence_id, write=True)
        receipt = self._receipt(principal, occurrence_id, idempotency_key)
        if receipt is not None:
            replay = self._replay(receipt, fingerprint)
            self.db.rollback()
            return AttachResult(replay, True)
        self._require_writable(access.occurrence)
        candidate = self._candidate(principal, access.occurrence, payload.asset_ref)
        # No row lock and no connection is held while the object is read and parsed.
        self.db.rollback()
        extracted = self._read_and_parse(candidate)
        return self._persist(
            principal=principal,
            occurrence_id=occurrence_id,
            payload=payload,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            candidate=candidate,
            extracted=extracted,
        )

    @staticmethod
    def _require_writable(occurrence: RowMapping) -> None:
        # ARCHIVED is the only non-writable state in v3 (the document and plan states of the
        # occurrence are never moved by a v3 route; T-3a-DEC-9 uses the same rule for uploads).
        if occurrence["state"] == "ARCHIVED":
            raise DocumentError(409, "INVALID_STATE_TRANSITION")

    def _session_row(
        self, principal: VerifiedPrincipal, occurrence: RowMapping, upload_id: str, *, lock: bool
    ) -> RowMapping:
        statement = select(UPLOAD_SESSIONS).where(
            UPLOAD_SESSIONS.c.upload_session_id == upload_id,
            UPLOAD_SESSIONS.c.purpose == OCCURRENCE_DOCUMENT,
            UPLOAD_SESSIONS.c.target_ref == occurrence["occurrence_id"],
            UPLOAD_SESSIONS.c.owner_principal_ref == principal.subject,
            UPLOAD_SESSIONS.c.owner_scope_kind == ORGANIZATION_SCOPE,
            UPLOAD_SESSIONS.c.organization_id == occurrence["organization_ref"],
            UPLOAD_SESSIONS.c.state == "COMPLETED",
            UPLOAD_SESSIONS.c.scan_verdict == "CLEAN",
        )
        if lock:
            statement = statement.with_for_update()
        row = self.db.execute(statement).mappings().one_or_none()
        if row is None or row["final_asset_ref"] is None:
            # Another actor's asset, another occurrence's, an unfinished, failed, unscanned or
            # non-CLEAN session and an unknown handle all answer the same 404.
            raise not_found()
        return row

    def _candidate(
        self, principal: VerifiedPrincipal, occurrence: RowMapping, asset_ref: str
    ) -> _Candidate:
        upload_id = upload_id_from_handle(asset_ref)
        if upload_id is None:
            raise not_found()
        session = self._session_row(principal, occurrence, upload_id, lock=False)
        organization_id = str(occurrence["organization_ref"])
        key = resolve_asset_key(
            self.db,
            asset_ref,
            owner_scope_kind=ORGANIZATION_SCOPE,
            owner_scope_ref=None,
            organization_id=organization_id,
        )
        if key is None or key != session["final_asset_ref"]:
            raise not_found()
        asset = self.db.get(CoreAssetMetadataModel, (key, 1))
        if (
            asset is None
            or asset.organization_id != organization_id
            or asset.owner_scope_kind != ORGANIZATION_SCOPE
        ):
            raise not_found()
        file_name = str(session["safe_file_name"])
        extension = extension_of(file_name)
        if extension is None or document_media_type_for(file_name) != asset.media_type:
            raise DocumentError(415, "UNSUPPORTED_LESSON_TYPE")
        if self._already_attached(upload_id, key):
            raise DocumentError(409, "RESOURCE_CONFLICT")
        return _Candidate(
            upload_id=upload_id,
            asset_key=key,
            organization_id=organization_id,
            file_name=file_name,
            file_extension=extension,
            media_type=asset.media_type,
            size_bytes=int(session["expected_size_bytes"]),
            sha256=asset.content_sha256,
        )

    def _already_attached(self, upload_id: str, key: str) -> bool:
        found = self.db.scalar(
            select(SOURCE_DOCUMENTS.c.source_document_id)
            .where(
                (SOURCE_DOCUMENTS.c.upload_session_ref == upload_id)
                | ((SOURCE_DOCUMENTS.c.asset_ref == key) & (SOURCE_DOCUMENTS.c.asset_version == 1))
            )
            .limit(1)
        )
        return found is not None

    # ------------------------------------------------------------------ verify and parse
    def _read_and_parse(self, candidate: _Candidate) -> _Extracted:
        if self._storage is None:
            raise DocumentError(503, "STORAGE_UNAVAILABLE")
        if self._parser is None:
            raise DocumentError(503, "PROVIDER_UNAVAILABLE")
        spool = SpooledTemporaryFile(  # noqa: SIM115 - closed in the finally below
            max_size=SPOOL_MEMORY_BYTES, mode="w+b"
        )
        try:
            self._fetch_verified(self._storage, candidate, spool)
            spool.seek(0)
            extraction = self._gate.run(
                self._parser, cast(BinaryIO, spool), file_extension=candidate.file_extension
            )
        finally:
            spool.close()
        if extraction.detected_media_type != candidate.media_type:
            raise DocumentError(415, "UNSUPPORTED_LESSON_TYPE")
        text = extraction.extracted_text
        if storable_text_problem(text) is not None:
            # The parser normalises its text; this is the guard that keeps a NUL, a lone
            # surrogate, an empty or an oversized text from ever reaching a 500 or a partial row.
            raise DocumentError(400, "INVALID_FILE_CONTENT")
        warnings = derive_warnings(
            extraction.warnings, extraction.page_or_slide_count, extraction.page_coverage
        )
        return _Extracted(extraction, text, warnings)

    def _fetch_verified(
        self, storage: ObjectStoragePort, candidate: _Candidate, spool: Any
    ) -> None:
        try:
            stored = storage.get_object(candidate.asset_key)
        except ObjectStorageFailure:
            raise DocumentError(503, "STORAGE_UNAVAILABLE") from None
        if stored is None:
            raise DocumentError(422, "UPLOAD_INCOMPLETE")
        digest = hashlib.sha256()
        total = 0
        try:
            while chunk := stored.body.read(READ_CHUNK_BYTES):
                total += len(chunk)
                if total > MAX_DOCUMENT_BYTES:
                    raise DocumentError(413, "LESSON_FILE_TOO_LARGE")
                digest.update(chunk)
                spool.write(chunk)
        except DocumentError:
            raise
        except Exception:
            # The stream of a real client raises its own (botocore, urllib3) errors mid-read, not
            # only ObjectStorageFailure: every fault of the read is a retryable storage fault.
            raise DocumentError(503, "STORAGE_UNAVAILABLE") from None
        finally:
            with contextlib.suppress(Exception):
                stored.body.close()
        if total != candidate.size_bytes or digest.hexdigest() != candidate.sha256:
            raise DocumentError(422, "UPLOAD_CHECKSUM_MISMATCH")

    # ------------------------------------------------------------------ write transaction
    def _persist(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        payload: AttachOccurrenceDocumentRequestV1,
        idempotency_key: str,
        fingerprint: str,
        candidate: _Candidate,
        extracted: _Extracted,
    ) -> AttachResult:
        try:
            # Lock order: occurrence, then upload session. Everything the snapshot read is
            # re-checked under the locks (the occurrence may have been archived, the Teacher
            # changed, the asset attached by a concurrent request, the same key replayed).
            access = authorize_occurrence(
                self.db, principal, occurrence_id, write=True, lock="update"
            )
            receipt = self._receipt(principal, occurrence_id, idempotency_key)
            if receipt is not None:
                replay = self._replay(receipt, fingerprint)
                self.db.rollback()
                return AttachResult(replay, True)
            self._require_writable(access.occurrence)
            self._session_row(principal, access.occurrence, candidate.upload_id, lock=True)
            if self._already_attached(candidate.upload_id, candidate.asset_key):
                raise DocumentError(409, "RESOURCE_CONFLICT")
            body = self._write_rows(
                principal=principal,
                access_account=access.account_ref,
                occurrence_id=occurrence_id,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                candidate=candidate,
                extracted=extracted,
            )
            self.db.commit()
            return AttachResult(body, False)
        except IntegrityError:
            # A concurrent request committed the same asset or key first: its rows stand and this
            # transaction (document, revision, job, audit, receipt) is rolled back whole.
            self.db.rollback()
            winner = self._receipt(principal, occurrence_id, idempotency_key)
            if winner is None:
                raise DocumentError(409, "RESOURCE_CONFLICT") from None
            replay = self._replay(winner, fingerprint)
            self.db.rollback()
            return AttachResult(replay, True)
        except SQLAlchemyError:
            self.db.rollback()
            raise DocumentError(503, "PROVIDER_UNAVAILABLE") from None
        except BaseException:
            self.db.rollback()
            raise

    def _write_rows(
        self,
        *,
        principal: VerifiedPrincipal,
        access_account: str,
        occurrence_id: str,
        idempotency_key: str,
        fingerprint: str,
        candidate: _Candidate,
        extracted: _Extracted,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        source_document_id = str(uuid4())
        revision_id = str(uuid4())
        job_id = f"lsd-{uuid4().hex}"
        extraction = extracted.extraction
        text_hash = text_sha256(extracted.text)
        self.db.execute(
            SOURCE_DOCUMENTS.insert().values(
                source_document_id=source_document_id,
                occurrence_id=occurrence_id,
                asset_ref=candidate.asset_key,
                asset_version=1,
                upload_session_ref=candidate.upload_id,
                extraction_job_ref=job_id,
                safe_file_name=candidate.file_name,
                file_extension=candidate.file_extension,
                page_or_slide_count=extraction.page_or_slide_count,
                uploaded_by=access_account,
                uploaded_at=now,
            )
        )
        self.db.execute(
            DOCUMENT_REVISIONS.insert().values(
                document_revision_id=revision_id,
                source_document_id=source_document_id,
                revision_no=1,
                origin="EXTRACTION",
                extracted_text=extracted.text,
                extracted_text_hash=text_hash,
                parser_name=extraction.parser_name,
                parser_version=extraction.parser_version,
                extraction_warnings=extracted.warnings,
                page_coverage=list(extraction.page_coverage),
                created_by=access_account,
                created_at=now,
            )
        )
        # TD-15: one job row, already terminal, in this transaction; no outbox row, no queue
        # message, no semantic request, no receipt in ``ai_jobs`` (nothing can pick it up).
        self._recorder_factory(self.db).record_succeeded(
            InlineSucceededJob(
                job_id=job_id,
                attempt_id=f"{job_id}-a1",
                correlation_id=source_document_id,
                job_type=LESSON_SOURCE_EXTRACTION_JOB_TYPE,
                organization_id=candidate.organization_id,
                purpose_code=JOB_PURPOSE_CODE,
                target_id=source_document_id,
                request_id=source_document_id,
                request_revision=1,
                input_hash=candidate.sha256,
                result_artifact_ref=revision_ref(revision_id),
                result_sha256=text_hash,
                result_provenance=f"parser:{extraction.parser_name}@{extraction.parser_version}",
                policy_id=JOB_POLICY_ID,
                attempt_timeout_ms=int(self._gate.deadline_seconds * 1000),
                at=now,
            )
        )
        body = accepted_body(source_document_id, job_id)
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=candidate.organization_id,
                actor_ref=access_account,
                action=AUDIT_ATTACH_ACTION,
                resource_type="lesson_source_document",
                resource_id=source_document_id,
                decision="allowed",
            )
        )
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=ATTACH_RECEIPT_SCOPE.format(occurrence_id=occurrence_id),
                idempotency_key=idempotency_key,
                organization_id=candidate.organization_id,
                request_fingerprint=fingerprint,
                response_json=body,
            )
        )
        self.db.flush()
        return body

    def _receipt(
        self, principal: VerifiedPrincipal, occurrence_id: str, key: str
    ) -> Be1CommandReceiptModel | None:
        return self.db.get(
            Be1CommandReceiptModel,
            (principal.subject, ATTACH_RECEIPT_SCOPE.format(occurrence_id=occurrence_id), key),
        )

    @staticmethod
    def _replay(receipt: Be1CommandReceiptModel, fingerprint: str) -> dict[str, Any]:
        if receipt.request_fingerprint != fingerprint:
            raise DocumentError(400, "INVALID_IDEMPOTENCY_KEY")
        return dict(receipt.response_json)

    # ------------------------------------------------------------------ revision edit (T-3c)
    def edit_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        document_id: str,
        payload: EditDocumentRevisionRequestV1,
        idempotency_key: str,
    ) -> EditResult:
        """Write the Teacher's text as a new immutable revision, or answer the head unchanged.

        One transaction, no storage and no parser: authorise (responsible Teacher), lock the
        occurrence ``FOR SHARE`` and the document ``FOR UPDATE`` (the order T-3d uses), replay a
        stored receipt, check states, compare the fence with the head, then insert head + 1.
        """
        problem = edit_text_problem(payload.extracted_text)
        if problem is not None:
            raise DocumentError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "extracted_text", "code": problem}],
            )
        if not 0 < len(occurrence_id) <= 36 or not 0 < len(document_id) <= 36:
            raise not_found()
        text_hash = text_sha256(payload.extracted_text)
        fingerprint = edit_fingerprint(payload.expected_head_revision_no, text_hash)
        try:
            access = authorize_occurrence(
                self.db, principal, occurrence_id, write=True, lock="share"
            )
            document = self._document_row(occurrence_id, document_id, lock=True)
            receipt = self._edit_receipt(principal, occurrence_id, document_id, idempotency_key)
            if receipt is not None:
                replayed = self._edit_replay(receipt, fingerprint, document_id)
                self.db.rollback()
                return replayed
            self._require_writable(access.occurrence)
            if document["document_state"] == "DELETED":
                raise DocumentError(409, "INVALID_STATE_TRANSITION")
            head = self._head_revision(document_id)
            head_no = int(head["revision_no"])
            if payload.expected_head_revision_no != head_no:
                # The edit never overwrites or forks the head: the client reloads the head.
                raise DocumentError(
                    409, "STALE_REVISION", current_version=head_no, etag=str(head_no)
                )
            organization = str(access.occurrence["organization_ref"])
            if head["extracted_text_hash"] == text_hash:
                # Same bytes as the head (no normalisation: another line ending is a real edit):
                # nothing is written except the receipt, so a replay answers 200 with this head.
                self._store_edit_receipt(
                    principal,
                    occurrence_id,
                    document_id,
                    idempotency_key,
                    organization,
                    fingerprint,
                    status_code=200,
                    revision_id=str(head["document_revision_id"]),
                    revision_no=head_no,
                    review_state=str(head["review_state"]),
                )
                self.db.flush()
                body = revision_body(self._revision_row(document_id, head_no), document_id)
                self.db.commit()
                return EditResult(body, 200, False)
            if head_no >= MAX_REVISIONS_PER_DOCUMENT:
                raise DocumentError(409, "RESOURCE_CONFLICT")
            revision_id = str(uuid4())
            self.db.execute(
                DOCUMENT_REVISIONS.insert().values(
                    document_revision_id=revision_id,
                    source_document_id=document_id,
                    revision_no=head_no + 1,
                    origin="TEACHER_EDIT",
                    base_revision_no=head_no,
                    extracted_text=payload.extracted_text,
                    extracted_text_hash=text_hash,
                    parser_name=None,
                    parser_version=None,
                    extraction_warnings=[],
                    page_coverage=[],
                    created_by=access.account_ref,
                    created_at=datetime.now(UTC),
                )
            )
            self.db.add(
                CoreAuditEntryModel(
                    audit_id=str(uuid4()),
                    organization_id=organization,
                    actor_ref=access.account_ref,
                    action=AUDIT_EDIT_ACTION,
                    resource_type="lesson_document_revision",
                    resource_id=revision_id,
                    decision="allowed",
                )
            )
            self._store_edit_receipt(
                principal,
                occurrence_id,
                document_id,
                idempotency_key,
                organization,
                fingerprint,
                status_code=201,
                revision_id=revision_id,
                revision_no=head_no + 1,
                review_state="NEEDS_REVIEW",
            )
            self.db.flush()
            body = revision_body(self._revision_row(document_id, head_no + 1), document_id)
            self.db.commit()
            return EditResult(body, 201, False)
        except IntegrityError as error:
            # A concurrent request committed first (the same key, or head + 1): its rows stand and
            # this transaction is rolled back whole. The lock makes this unreachable in practice.
            # Only a unique violation (SQLSTATE 23505) means "someone else won"; any other integrity
            # failure is a fault, not a stale head, so the client is never told to reload forever.
            self.db.rollback()
            if getattr(error.orig, "sqlstate", None) != "23505":
                raise DocumentError(503, "PROVIDER_UNAVAILABLE") from None
            winner = self._edit_receipt(principal, occurrence_id, document_id, idempotency_key)
            if winner is not None:
                replayed = self._edit_replay(winner, fingerprint, document_id)
                self.db.rollback()
                return replayed
            current = self._head_revision(document_id)
            self.db.rollback()
            number = int(current["revision_no"])
            raise DocumentError(
                409, "STALE_REVISION", current_version=number, etag=str(number)
            ) from None
        except SQLAlchemyError:
            self.db.rollback()
            raise DocumentError(503, "PROVIDER_UNAVAILABLE") from None
        except BaseException:
            self.db.rollback()
            raise

    def _head_revision(self, document_id: str) -> RowMapping:
        """The head revision without its text (the text can be 2 MiB)."""
        return (
            self.db.execute(
                select(
                    DOCUMENT_REVISIONS.c.document_revision_id,
                    DOCUMENT_REVISIONS.c.revision_no,
                    DOCUMENT_REVISIONS.c.extracted_text_hash,
                    DOCUMENT_REVISIONS.c.review_state,
                )
                .where(DOCUMENT_REVISIONS.c.source_document_id == document_id)
                .order_by(DOCUMENT_REVISIONS.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one()
        )

    def _revision_row(self, document_id: str, revision_no: int) -> RowMapping:
        return (
            self.db.execute(
                select(DOCUMENT_REVISIONS).where(
                    DOCUMENT_REVISIONS.c.source_document_id == document_id,
                    DOCUMENT_REVISIONS.c.revision_no == revision_no,
                )
            )
            .mappings()
            .one()
        )

    def _edit_receipt(
        self, principal: VerifiedPrincipal, occurrence_id: str, document_id: str, key: str
    ) -> Be1CommandReceiptModel | None:
        scope = EDIT_RECEIPT_SCOPE.format(occurrence_id=occurrence_id, document_id=document_id)
        return self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))

    def _store_edit_receipt(
        self,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        document_id: str,
        key: str,
        organization: str,
        fingerprint: str,
        *,
        status_code: int,
        revision_id: str,
        revision_no: int,
        review_state: str,
    ) -> None:
        """References only, never the text (it can be 2 MiB and the revision row is immutable)."""
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=EDIT_RECEIPT_SCOPE.format(
                    occurrence_id=occurrence_id, document_id=document_id
                ),
                idempotency_key=key,
                organization_id=organization,
                request_fingerprint=fingerprint,
                response_json={
                    "status_code": status_code,
                    "document_revision_id": revision_id,
                    "revision_no": revision_no,
                    "review_state": review_state,
                },
            )
        )

    def _edit_replay(
        self, receipt: Be1CommandReceiptModel, fingerprint: str, document_id: str
    ) -> EditResult:
        """The first answer again: the immutable row, with the review state it had at creation."""
        if receipt.request_fingerprint != fingerprint:
            raise DocumentError(400, "INVALID_IDEMPOTENCY_KEY")
        stored = receipt.response_json
        row = self._revision_row(document_id, int(str(stored["revision_no"])))
        body = revision_body(row, document_id, review_state=str(stored["review_state"]))
        return EditResult(body, int(str(stored["status_code"])), True)

    # ------------------------------------------------------------------ reads
    def _read_access(self, principal: VerifiedPrincipal, occurrence_id: str) -> RowMapping:
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        return authorize_occurrence(self.db, principal, occurrence_id).occurrence

    def _document_row(
        self, occurrence_id: str, document_id: str, *, lock: bool = False
    ) -> RowMapping:
        if not 0 < len(document_id) <= 36:
            raise not_found()
        statement = select(SOURCE_DOCUMENTS).where(
            SOURCE_DOCUMENTS.c.source_document_id == document_id,
            SOURCE_DOCUMENTS.c.occurrence_id == occurrence_id,
        )
        if lock:
            statement = statement.with_for_update()
        row = self.db.execute(statement).mappings().one_or_none()
        if row is None:
            raise not_found()
        return row

    def _document_views(self, rows: list[RowMapping]) -> list[dict[str, Any]]:
        if not rows:
            return []
        ids = [row["source_document_id"] for row in rows]
        heads = dict(
            self.db.execute(
                select(
                    DOCUMENT_REVISIONS.c.source_document_id,
                    func.max(DOCUMENT_REVISIONS.c.revision_no),
                )
                .where(DOCUMENT_REVISIONS.c.source_document_id.in_(ids))
                .group_by(DOCUMENT_REVISIONS.c.source_document_id)
            )
            .tuples()
            .all()
        )
        extraction = {
            row["source_document_id"]: row
            for row in self.db.execute(
                select(
                    DOCUMENT_REVISIONS.c.source_document_id,
                    DOCUMENT_REVISIONS.c.extraction_warnings,
                    DOCUMENT_REVISIONS.c.page_coverage,
                ).where(
                    DOCUMENT_REVISIONS.c.source_document_id.in_(ids),
                    DOCUMENT_REVISIONS.c.revision_no == 1,
                )
            )
            .mappings()
            .all()
        }
        views: list[dict[str, Any]] = []
        for row in rows:
            first = extraction.get(row["source_document_id"])
            views.append(
                {
                    "contract": "LessonSourceDocumentV1",
                    "source_document_id": row["source_document_id"],
                    "occurrence_id": row["occurrence_id"],
                    "file_name": row["safe_file_name"],
                    "file_extension": row["file_extension"],
                    "page_or_slide_count": row["page_or_slide_count"],
                    "document_state": row["document_state"],
                    "head_revision_no": int(heads.get(row["source_document_id"], 1)),
                    "job_ref": row["extraction_job_ref"],
                    "warnings": list(first["extraction_warnings"]) if first else [],
                    "page_coverage": list(first["page_coverage"]) if first else [],
                    "uploaded_at": row["uploaded_at"],
                }
            )
        return views

    def get_document(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, document_id: str
    ) -> dict[str, Any]:
        self._read_access(principal, occurrence_id)
        view = self._document_views([self._document_row(occurrence_id, document_id)])[0]
        self.db.rollback()
        return view

    def list_documents(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, limit: int, cursor: str | None
    ) -> dict[str, Any]:
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise DocumentError(
                400, "INVALID_REQUEST", field_errors=[{"field": "limit", "code": "OUT_OF_RANGE"}]
            )
        after = decode_document_cursor(cursor) if cursor is not None else None
        self._read_access(principal, occurrence_id)
        statement = select(SOURCE_DOCUMENTS).where(
            SOURCE_DOCUMENTS.c.occurrence_id == occurrence_id
        )
        if after is not None:
            statement = statement.where(
                tuple_(SOURCE_DOCUMENTS.c.uploaded_at, SOURCE_DOCUMENTS.c.source_document_id)
                < tuple_(literal(after[0]), literal(after[1]))
            )
        rows = list(
            self.db.execute(
                statement.order_by(
                    SOURCE_DOCUMENTS.c.uploaded_at.desc(),
                    SOURCE_DOCUMENTS.c.source_document_id.desc(),
                ).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        page = rows[:limit]
        next_cursor = (
            encode_document_cursor(page[-1]["uploaded_at"], page[-1]["source_document_id"])
            if len(rows) > limit
            else None
        )
        items = self._document_views(page)
        self.db.rollback()
        return {
            "contract": "LessonSourceDocumentPageV1",
            "items": items,
            "next_cursor": next_cursor,
        }

    def list_revisions(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        document_id: str,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise DocumentError(
                400, "INVALID_REQUEST", field_errors=[{"field": "limit", "code": "OUT_OF_RANGE"}]
            )
        before = decode_revision_cursor(cursor) if cursor is not None else None
        self._read_access(principal, occurrence_id)
        self._document_row(occurrence_id, document_id)
        statement = select(
            DOCUMENT_REVISIONS.c.revision_no,
            DOCUMENT_REVISIONS.c.origin,
            DOCUMENT_REVISIONS.c.review_state,
            DOCUMENT_REVISIONS.c.extracted_text_hash,
            func.char_length(DOCUMENT_REVISIONS.c.extracted_text).label("text_length"),
            DOCUMENT_REVISIONS.c.created_at,
        ).where(DOCUMENT_REVISIONS.c.source_document_id == document_id)
        if before is not None:
            statement = statement.where(DOCUMENT_REVISIONS.c.revision_no < before)
        rows = list(
            self.db.execute(
                statement.order_by(DOCUMENT_REVISIONS.c.revision_no.desc()).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        page = rows[:limit]
        next_cursor = encode_revision_cursor(page[-1]["revision_no"]) if len(rows) > limit else None
        items = [
            {
                "revision_no": row["revision_no"],
                "origin": row["origin"],
                "review_state": row["review_state"],
                "text_hash": row["extracted_text_hash"],
                "text_length": int(row["text_length"]),
                "created_at": row["created_at"],
            }
            for row in page
        ]
        self.db.rollback()
        return {
            "contract": "LessonDocumentRevisionPageV1",
            "items": items,
            "next_cursor": next_cursor,
        }

    def get_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        document_id: str,
        revision_no: int,
    ) -> dict[str, Any]:
        self._read_access(principal, occurrence_id)
        self._document_row(occurrence_id, document_id)
        row = (
            self.db.execute(
                select(DOCUMENT_REVISIONS).where(
                    DOCUMENT_REVISIONS.c.source_document_id == document_id,
                    DOCUMENT_REVISIONS.c.revision_no == revision_no,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise not_found()
        body = revision_body(row, document_id)
        self.db.rollback()
        return body


def revision_body(
    row: RowMapping, document_id: str, *, review_state: str | None = None
) -> dict[str, Any]:
    """The ``LessonDocumentRevisionV2`` body of a stored revision row.

    ``review_state`` overrides the row's current stamp: a replayed edit answers with the state the
    revision had when it was created (T-3c-DEC-7).
    """
    parser = (
        {"name": row["parser_name"], "version": row["parser_version"]}
        if row["parser_name"] is not None
        else None
    )
    return {
        "contract": "LessonDocumentRevisionV2",
        "source_document_id": document_id,
        "revision_no": row["revision_no"],
        "origin": row["origin"],
        "review_state": review_state if review_state is not None else row["review_state"],
        "base_revision_no": row["base_revision_no"],
        "extracted_text": row["extracted_text"],
        "text_hash": row["extracted_text_hash"],
        "text_length": len(row["extracted_text"]),
        "parser": parser,
        "warnings": list(row["extraction_warnings"]),
        "page_coverage": list(row["page_coverage"]),
        "created_at": row["created_at"],
    }


def _sql_recorder(db: Session) -> InlineJobRecorder:
    return SqlInlineJobRecorder(db.connection())


__all__ = [
    "ATTACH_RECEIPT_SCOPE",
    "AUDIT_ATTACH_ACTION",
    "AttachResult",
    "EDIT_RECEIPT_SCOPE",
    "DocumentError",
    "EditResult",
    "OccurrenceDocumentService",
    "ParseGate",
    "accepted_body",
    "attach_fingerprint",
    "default_parse_gate",
    "extension_of",
    "revision_body",
]
