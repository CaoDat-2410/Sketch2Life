"""FEAT-066 T-3b: attach rules of an occurrence source document (SRS l.545, l.1437, l.1653, l.1692).

Offline unit tests: the domain rules (rejection mapping, text normalisation, warnings, cursors,
ETags), the bounded parser gate, the inline job record, the job-kind registry entry and its
per-class Teacher rule (T0.4-DEBT-1), and the real parser's refusals that need no document
library. Tests that need ``python-docx`` or ``python-pptx`` skip when the library is absent;
``pypdf`` is not installed in this environment, so no real PDF is parsed here (recorded in the
evidence note). Behaviour against PostgreSQL is in
``tests/integration/lesson_occurrences/test_document_attach_postgres.py``.
"""

from __future__ import annotations

import ast
import hashlib
import io
import random
import struct
import threading
import time
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.job_kinds import (
    DEFAULT_JOB_KIND_REGISTRY,
    LESSON_SOURCE_EXTRACTION_JOB_TYPE,
    ActorMembership,
    JobActor,
    JobKindRegistry,
    JobKindSpec,
    JobNotVisible,
    JobStatusReader,
    JobTargetKind,
    build_job_kind_registry,
    lesson_source_document_spec,
)
from sketch2life.application.ports.ai_jobs import PrincipalRole
from sketch2life.application.ports.inline_jobs import InlineSucceededJob
from sketch2life.application.ports.lesson_documents import (
    LessonDocumentExtraction,
    LessonDocumentRejected,
)
from sketch2life.domain.ai_jobs.model import JobState, ResultDisposition
from sketch2life.domain.lesson_occurrences import documents as rules
from sketch2life.infrastructure.ai_jobs.inline_recorder import (
    INLINE_POLICY_STATUS,
    SqlInlineJobRecorder,
)
from sketch2life.infrastructure.documents.lesson_parser import (
    MAX_EXTRACTED_TEXT_BYTES,
    DeterministicLessonDocumentParser,
    sanitize_extracted_text,
)
from sketch2life.infrastructure.lesson_occurrences.documents import (
    DocumentError,
    ParseGate,
    accepted_body,
    attach_fingerprint,
    extension_of,
)
from sketch2life.interfaces.http import error_envelope as envelope

SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
NOW = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)
HASH = "ab" * 32


# ----------------------------------------------------------------------------- rejection table
@pytest.mark.parametrize(
    ("parser_code", "expected"),
    [
        ("UNSUPPORTED_MEDIA_TYPE", (415, "UNSUPPORTED_LESSON_TYPE")),
        ("OCR_NOT_SUPPORTED", (422, "OCR_NOT_SUPPORTED")),
        ("INVALID_SOURCE_DOCUMENT", (400, "INVALID_FILE_CONTENT")),
        ("DOCUMENT_EXPANSION_LIMIT_EXCEEDED", (400, "INVALID_FILE_CONTENT")),
        ("ENCRYPTED_DOCUMENT_UNSUPPORTED", (422, "ENCRYPTED_DOCUMENT_UNSUPPORTED")),
        ("DOCUMENT_PAGE_LIMIT_EXCEEDED", (422, "DOCUMENT_PAGE_LIMIT_EXCEEDED")),
        ("DOCUMENT_TEXT_LIMIT_EXCEEDED", (422, "DOCUMENT_TEXT_LIMIT_EXCEEDED")),
        ("A_CODE_THE_PARSER_NEVER_RAISES", (400, "INVALID_FILE_CONTENT")),
    ],
)
def test_every_parser_rejection_maps_to_one_status_and_public_code(
    parser_code: str, expected: tuple[int, str]
) -> None:
    assert rules.map_parser_rejection(parser_code) == expected
    status, code = expected
    assert code in envelope.MESSAGES or code in envelope.STATUS_MESSAGE_ONLY
    assert envelope.build_error_body(status=status, code=code, request_id="r")["code"] == code


def test_the_table_covers_every_code_the_parser_raises() -> None:
    tree = ast.parse((SRC / "infrastructure/documents/lesson_parser.py").read_text("utf-8"))
    raised = {
        str(node.args[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "LessonDocumentRejected"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    }
    assert raised == set(rules.PARSER_REJECTIONS)


def test_every_new_code_has_a_vietnamese_message_and_the_three_parser_codes_are_marked() -> None:
    for code in (
        "INVALID_FILE_CONTENT",
        "OCR_NOT_SUPPORTED",
        "ENCRYPTED_DOCUMENT_UNSUPPORTED",
        "DOCUMENT_PAGE_LIMIT_EXCEEDED",
        "DOCUMENT_TEXT_LIMIT_EXCEEDED",
        "UNSUPPORTED_LESSON_TYPE",
        "UPLOAD_CHECKSUM_MISMATCH",
        "LESSON_FILE_TOO_LARGE",
        "UPLOAD_INCOMPLETE",
        "STORAGE_UNAVAILABLE",
    ):
        assert envelope.MESSAGES[code].strip()
    # Not named by §9.8 (T-3b-DEC-5): kept as the parser's own stable codes.
    assert "ENCRYPTED_DOCUMENT_UNSUPPORTED" in envelope.MESSAGES
    assert envelope.build_error_body(status=422, code="OCR_NOT_SUPPORTED", request_id="r")[
        "message"
    ].startswith("Tệp")


def test_every_code_the_attach_code_raises_has_a_message_or_status_message() -> None:
    codes: set[str] = set()
    for relative in (
        "infrastructure/lesson_occurrences/documents.py",
        "interfaces/http/routers/lesson_occurrences.py",
    ):
        tree = ast.parse((SRC / relative).read_text("utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"DocumentError", "LessonOccurrenceError"}
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
            ):
                codes.add(str(node.args[1].value))
    codes |= {code for _status, code in rules.PARSER_REJECTIONS.values()}
    assert {
        "RESOURCE_CONFLICT",
        "INVALID_STATE_TRANSITION",
        "LESSON_FILE_TOO_LARGE",
        "UNSUPPORTED_LESSON_TYPE",
        "UPLOAD_INCOMPLETE",
        "UPLOAD_CHECKSUM_MISMATCH",
        "STORAGE_UNAVAILABLE",
        "PROVIDER_UNAVAILABLE",
        "INVALID_FILE_CONTENT",
        "INVALID_IDEMPOTENCY_KEY",
    } <= codes
    for code in codes:
        assert code in envelope.MESSAGES or code in envelope.STATUS_MESSAGE_ONLY, code


# ----------------------------------------------------------------------------- text rules
def test_the_text_normaliser_drops_nul_and_controls_and_replaces_lone_surrogates() -> None:
    assert sanitize_extracted_text("a\x00b\x01c\x7fd\x85e") == "abcde"
    assert sanitize_extracted_text("keep\ttabs\nnew\r\nlines") == "keep\ttabs\nnew\r\nlines"
    assert sanitize_extracted_text("lone \ud800 here") == "lone � here"
    assert sanitize_extracted_text("pair 😀 ok") == "pair \U0001f600 ok"
    assert sanitize_extracted_text("Vẽ con mèo xinh đẹp") == "Vẽ con mèo xinh đẹp"
    # The result is always encodable and has no NUL, the two causes of a 500 (review F-02).
    dirty = "x\x00\ud800y\udfffz"
    clean = sanitize_extracted_text(dirty)
    assert "\x00" not in clean
    clean.encode("utf-8")


def test_text_problems_are_named_and_a_clean_text_has_none() -> None:
    assert rules.storable_text_problem("Bài học vẽ con mèo") is None
    assert rules.storable_text_problem("a\x00b") == "NUL"
    assert rules.storable_text_problem("a\ud800b") == "SURROGATE"
    assert rules.storable_text_problem("") == "EMPTY"
    assert rules.storable_text_problem("   \n") == "EMPTY"
    assert rules.storable_text_problem("ê" * (rules.MAX_TEXT_BYTES // 2)) is None
    assert rules.storable_text_problem("ê" * (rules.MAX_TEXT_BYTES // 2 + 1)) == "TOO_LARGE"
    assert rules.MAX_TEXT_BYTES == MAX_EXTRACTED_TEXT_BYTES == 2 * 1024 * 1024


def test_the_text_hash_is_the_sha256_of_the_utf8_bytes() -> None:
    text = "Vẽ con mèo\nBước 1"
    assert rules.text_sha256(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_scan_pages_are_derived_from_the_page_count_and_the_coverage() -> None:
    assert rules.derive_warnings(["MISSING_FIELD_TOPIC"], 3, [1, 2, 3]) == ["MISSING_FIELD_TOPIC"]
    mixed = rules.derive_warnings(["MISSING_FIELD_TOPIC"], 4, [1, 3])
    assert mixed == ["MISSING_FIELD_TOPIC", "OCR_NOT_SUPPORTED_PAGES"]
    # a DOCX has no page count: never the scan-page warning
    assert rules.derive_warnings([], None, [1]) == []
    # duplicates collapse and the warning is added once
    assert rules.derive_warnings(["A", "A", "OCR_NOT_SUPPORTED_PAGES"], 2, [1]) == [
        "A",
        "OCR_NOT_SUPPORTED_PAGES",
    ]


def test_asset_handles_are_opaque_and_only_the_upl_prefix_resolves() -> None:
    assert rules.upload_id_from_handle("upl_1234") == "1234"
    assert rules.upload_id_from_handle("upl_") is None
    assert rules.upload_id_from_handle("occurrences/org/occ/abc/original") is None
    assert rules.upload_id_from_handle("lesson-source:abc") is None
    assert rules.upload_id_from_handle("upl_" + "x" * 65) is None


def test_extensions_are_the_three_document_types_only() -> None:
    assert extension_of("Bai hoc.PDF") == ".pdf"
    assert extension_of("a.docx") == ".docx"
    assert extension_of("a.pptx") == ".pptx"
    assert extension_of("a.exe") is None
    assert extension_of("noextension") is None
    assert extension_of("archive.pdf.zip") is None


def test_the_fingerprint_binds_the_occurrence_and_the_asset() -> None:
    base = attach_fingerprint("occ-1", "upl_a")
    assert base == attach_fingerprint("occ-1", "upl_a")
    assert base != attach_fingerprint("occ-2", "upl_a")
    assert base != attach_fingerprint("occ-1", "upl_b")
    assert len(base) == 64


def test_the_accepted_body_has_one_job_and_no_storage_words() -> None:
    body = accepted_body("doc-1", "lsd-1")
    assert body == {
        "contract": "LessonSourceDocumentAcceptedV1",
        "source_document_id": "doc-1",
        "document_revision_no": 1,
        "job": {"job_id": "lsd-1", "target_kind": "LESSON_SOURCE_DOCUMENT", "state": "succeeded"},
    }


def test_cursors_round_trip_and_reject_every_defect() -> None:
    cursor = rules.encode_document_cursor(NOW, "doc-1")
    assert rules.decode_document_cursor(cursor) == (NOW, "doc-1")
    assert rules.decode_revision_cursor(rules.encode_revision_cursor(7)) == 7
    for bad in ("", "!!!", "e30", rules.encode_revision_cursor(3), "x" * 600):
        with pytest.raises(rules.DocumentRuleError) as error:
            rules.decode_document_cursor(bad)
        assert (error.value.field, error.value.code) == ("cursor", "INVALID_FORMAT")
    with pytest.raises(rules.DocumentRuleError):
        rules.decode_revision_cursor(cursor)
    with pytest.raises(rules.DocumentRuleError):
        rules.decode_revision_cursor(rules.encode_revision_cursor(0))


def test_etags_are_strong_and_the_revision_tag_moves_with_the_review_state() -> None:
    assert rules.document_etag(3) == '"3"'
    pending = rules.revision_etag("a" * 64, "NEEDS_REVIEW")
    confirmed = rules.revision_etag("a" * 64, "CONFIRMED")
    assert pending != confirmed
    assert rules.etag_matches(f'W/"x", {pending}', pending)
    assert rules.etag_matches("*", pending)
    assert not rules.etag_matches(None, pending)
    assert not rules.etag_matches(confirmed, pending)
    assert rules.revision_ref("rev-1") == "lesson-document-revision:rev-1"
    assert "/" not in rules.revision_ref("rev-1")


# ----------------------------------------------------------------------------- parser gate
def _extraction(text: str = "Tiêu đề: Bài học") -> LessonDocumentExtraction:
    return LessonDocumentExtraction(
        detected_media_type="application/pdf",
        parser_name="p",
        parser_version="1",
        page_or_slide_count=1,
        page_coverage=(1,),
        extracted_fields={},
        warnings=(),
        extracted_text=text,
    )


class _Parser:
    def __init__(self, behaviour: Any) -> None:
        self.behaviour = behaviour
        self.calls = 0

    def extract(self, file_obj: Any, *, file_extension: str) -> LessonDocumentExtraction:
        self.calls += 1
        result = self.behaviour(file_obj, file_extension)
        assert isinstance(result, LessonDocumentExtraction)
        return result


def test_the_gate_returns_the_extraction_and_passes_the_extension() -> None:
    seen: list[str] = []

    def behave(_file: Any, extension: str) -> LessonDocumentExtraction:
        seen.append(extension)
        return _extraction()

    gate = ParseGate(max_concurrent=1, queue_wait_seconds=0.2, deadline_seconds=2)
    assert gate.run(_Parser(behave), io.BytesIO(b"x"), file_extension=".pdf").extracted_text
    assert seen == [".pdf"]


@pytest.mark.parametrize("parser_code", sorted(rules.PARSER_REJECTIONS))
def test_a_parser_rejection_becomes_the_mapped_refusal(parser_code: str) -> None:
    def behave(_file: Any, _extension: str) -> LessonDocumentExtraction:
        raise LessonDocumentRejected(parser_code)

    gate = ParseGate(max_concurrent=1, queue_wait_seconds=0.2, deadline_seconds=2)
    with pytest.raises(DocumentError) as error:
        gate.run(_Parser(behave), io.BytesIO(b"x"), file_extension=".pdf")
    assert (error.value.status_code, error.value.code) == rules.PARSER_REJECTIONS[parser_code]


def test_an_unexpected_parser_fault_is_unreadable_content_never_a_500_and_never_echoed() -> None:
    def behave(_file: Any, _extension: str) -> LessonDocumentExtraction:
        raise UnicodeEncodeError("utf-8", "\ud800 secret text", 0, 1, "surrogates not allowed")

    gate = ParseGate(max_concurrent=1, queue_wait_seconds=0.2, deadline_seconds=2)
    with pytest.raises(DocumentError) as error:
        gate.run(_Parser(behave), io.BytesIO(b"x"), file_extension=".docx")
    assert (error.value.status_code, error.value.code) == (400, "INVALID_FILE_CONTENT")
    assert "secret" not in str(error.value)


def test_a_parse_over_the_deadline_is_refused_and_the_slot_stays_taken_until_it_returns() -> None:
    release = threading.Event()
    started = threading.Event()

    def slow(_file: Any, _extension: str) -> LessonDocumentExtraction:
        started.set()
        assert release.wait(timeout=10)
        return _extraction()

    gate = ParseGate(max_concurrent=1, queue_wait_seconds=0.05, deadline_seconds=0.1)
    with pytest.raises(DocumentError) as timeout:
        gate.run(_Parser(slow), io.BytesIO(b"x"), file_extension=".pdf")
    assert (timeout.value.status_code, timeout.value.code) == (400, "INVALID_FILE_CONTENT")
    assert started.is_set()
    # The runaway parse still holds the only slot: the next request is told to retry.
    with pytest.raises(DocumentError) as busy:
        gate.run(_Parser(lambda _f, _e: _extraction()), io.BytesIO(b"x"), file_extension=".pdf")
    assert (busy.value.status_code, busy.value.code) == (503, "PROVIDER_UNAVAILABLE")
    assert busy.value.retry_after == 5
    release.set()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            result = gate.run(
                _Parser(lambda _f, _e: _extraction("ok")), io.BytesIO(b"x"), file_extension=".pdf"
            )
            break
        except DocumentError:
            time.sleep(0.02)
    else:  # pragma: no cover - failure path
        pytest.fail("the slot was never released")
    assert result.extracted_text == "ok"


def test_the_gate_caps_real_concurrency() -> None:
    running = 0
    peak = 0
    lock = threading.Lock()
    barrier_release = threading.Event()

    def behave(_file: Any, _extension: str) -> LessonDocumentExtraction:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        barrier_release.wait(timeout=0.3)
        with lock:
            running -= 1
        return _extraction()

    gate = ParseGate(max_concurrent=2, queue_wait_seconds=0.05, deadline_seconds=5)
    outcomes: list[str] = []

    def call() -> None:
        try:
            gate.run(_Parser(behave), io.BytesIO(b"x"), file_extension=".pdf")
            outcomes.append("ok")
        except DocumentError as error:
            outcomes.append(str(error.status_code))

    threads = [threading.Thread(target=call) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert peak <= 2
    assert outcomes.count("ok") >= 2
    assert set(outcomes) <= {"ok", "503"}


def test_gate_bounds_are_validated() -> None:
    for bounds in (
        {"max_concurrent": 0},
        {"queue_wait_seconds": -1},
        {"deadline_seconds": 0},
    ):
        with pytest.raises(ValueError):
            ParseGate(**bounds)  # type: ignore[arg-type]


# ----------------------------------------------------------------------------- inline job record
class _Connection:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> None:
        self.statements.append(statement)


def _inline(**overrides: Any) -> InlineSucceededJob:
    values: dict[str, Any] = {
        "job_id": "lsd-1",
        "attempt_id": "lsd-1-a1",
        "correlation_id": "doc-1",
        "job_type": LESSON_SOURCE_EXTRACTION_JOB_TYPE,
        "organization_id": "org-1",
        "purpose_code": rules.JOB_PURPOSE_CODE,
        "target_id": "doc-1",
        "request_id": "doc-1",
        "request_revision": 1,
        "input_hash": HASH,
        "result_artifact_ref": rules.revision_ref("rev-1"),
        "result_sha256": "cd" * 32,
        "result_provenance": "parser:p@1",
        "policy_id": rules.JOB_POLICY_ID,
        "attempt_timeout_ms": 30000,
        "at": NOW,
    }
    values.update(overrides)
    return InlineSucceededJob(**values)


def test_the_inline_job_is_born_terminal_with_one_attempt_and_one_result_ref() -> None:
    connection = _Connection()
    SqlInlineJobRecorder(connection).record_succeeded(_inline())  # type: ignore[arg-type]
    # Exactly the job row and its one attempt: no outbox row, no semantic request, no receipt.
    assert [statement.table.fullname for statement in connection.statements] == [
        "ai_jobs.job",
        "ai_jobs.attempt",
    ]
    job = connection.statements[0].compile().params
    assert job["state"] == "succeeded"
    assert job["result_disposition"] == "accepted"
    assert job["job_revision"] == 3
    assert job["history"] == ["created", "started", "succeeded:accepted"]
    assert job["session_id"] is None and job["subject_refs"] == []
    assert job["target_id"] == "doc-1" and job["organization_id"] == "org-1"
    assert job["result_refs"] == [
        {
            "artifact_ref": "lesson-document-revision:rev-1",
            "sha256": "cd" * 32,
            "provenance": "parser:p@1",
        }
    ]
    assert job["request_ref"] == {
        "request_id": "doc-1",
        "request_revision": 1,
        "input_hash": HASH,
        "context_revision": 0,
    }
    assert job["completed_at"] == NOW and job["created_at"] == NOW and job["updated_at"] == NOW
    assert job["policy_snapshot_id"] == "lesson.inline.v1"
    assert job["policy_snapshot"]["max_attempts"] == 1
    assert job["policy_snapshot"]["status"] == INLINE_POLICY_STATUS != "PROPOSED"
    assert job["accepted_fences"] == {}
    attempt = connection.statements[1].compile().params
    assert attempt["attempt_number"] == 1
    assert attempt["started_at"] == attempt["finished_at"] == NOW
    assert attempt["outcome"] == "succeeded:accepted"


def test_the_inline_job_can_never_be_retried_or_swept() -> None:
    from sketch2life.domain.ai_jobs import model as jobs
    from sketch2life.infrastructure.ai_jobs.inline_recorder import inline_retry_policy

    policy = inline_retry_policy(rules.JOB_POLICY_ID, 30000)
    assert policy.max_attempts == 1 and policy.attempts_remaining(1) == 0
    job = jobs.create_job(
        job_id="j",
        attempt_id="a",
        job_type="t",
        scope=jobs.JobScope("o", None, (), "p", "x"),
        request_ref=jobs.RequestRef("x", 1, HASH, 0),
        correlation_id="c",
        retry_policy=policy,
        now=NOW,
    )
    job = jobs.start_attempt(job, "a", NOW)
    job = jobs.succeed(
        job,
        "a",
        result_refs=(jobs.ResultRef("r", HASH, "p"),),
        disposition=ResultDisposition.ACCEPTED,
        now=NOW,
    )
    assert job.state is JobState.SUCCEEDED and job.is_terminal
    assert job.retry_not_before is None
    assert jobs.poll_after_ms(job, SimpleNamespace(), NOW) is None  # type: ignore[arg-type]
    with pytest.raises(jobs.InvalidJobTransition):
        jobs.requeue_for_retry(job, new_attempt_id="b", now=NOW)


# ----------------------------------------------------------------------------- job kind rule
CLASS_A, CLASS_B, ORG = "class-a", "class-b", "org-1"


class _Classes:
    def __init__(self, mapping: dict[tuple[str, str], str]) -> None:
        self.mapping = mapping
        self.calls: list[tuple[str, str]] = []

    def class_for(self, organization_id: str, source_document_id: str) -> str | None:
        self.calls.append((organization_id, source_document_id))
        return self.mapping.get((organization_id, source_document_id))


def _finished_job(recorder_job: InlineSucceededJob) -> Any:
    from sketch2life.domain.ai_jobs import model as jobs
    from sketch2life.infrastructure.ai_jobs.inline_recorder import inline_retry_policy

    created = jobs.create_job(
        job_id=recorder_job.job_id,
        attempt_id=recorder_job.attempt_id,
        job_type=recorder_job.job_type,
        scope=jobs.JobScope(
            recorder_job.organization_id,
            None,
            (),
            recorder_job.purpose_code,
            recorder_job.target_id,
        ),
        request_ref=jobs.RequestRef(recorder_job.request_id, 1, recorder_job.input_hash, 0),
        correlation_id=recorder_job.correlation_id,
        retry_policy=inline_retry_policy(recorder_job.policy_id, 30000),
        now=NOW,
    )
    started = jobs.start_attempt(created, recorder_job.attempt_id, NOW)
    return jobs.succeed(
        started,
        recorder_job.attempt_id,
        result_refs=(
            jobs.ResultRef(
                recorder_job.result_artifact_ref,
                recorder_job.result_sha256,
                recorder_job.result_provenance,
            ),
        ),
        disposition=ResultDisposition.ACCEPTED,
        now=NOW,
    )


class _Repository:
    def __init__(self, job: Any) -> None:
        self.job = job

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        yield SimpleNamespace(
            get_job=lambda job_id: self.job if job_id == self.job.job_id else None
        )


class _Clock:
    def now(self) -> datetime:
        return NOW


def _reader(classes: _Classes, job: Any | None = None) -> tuple[JobStatusReader, Any]:
    job = job or _finished_job(_inline())
    registry = build_job_kind_registry(classes)
    return JobStatusReader(_Repository(job), registry, _Clock()), job  # type: ignore[arg-type]


def _actor(
    class_roles: dict[str, set[str]],
    *,
    roles: set[str],
    organization: str = ORG,
    account_role: str = "teacher",
) -> JobActor:
    membership = ActorMembership(
        organization_id=organization,
        roles=frozenset(roles),
        class_ids=frozenset(class_roles),
        class_roles={key: frozenset(value) for key, value in class_roles.items()},
    )
    return JobActor("acct-1", account_role, lambda _org: membership)


def test_the_registry_maps_the_extraction_job_type_to_the_source_document_kind() -> None:
    registry = build_job_kind_registry(_Classes({}))
    spec = registry.for_job_type(LESSON_SOURCE_EXTRACTION_JOB_TYPE)
    assert spec is not None and spec.target_kind is JobTargetKind.LESSON_SOURCE_DOCUMENT
    assert spec.rule_grants_teacher_role
    assert registry.for_job_type("vision_analysis") is None
    assert len(registry.specs) == 8
    # the module default stays empty: the production registry is built per application
    assert all(not item.job_types for item in DEFAULT_JOB_KIND_REGISTRY.specs)
    # the constructor still refuses a registration without its own rule and eligibility
    with pytest.raises(ValueError):
        JobKindSpec(JobTargetKind.PARENT_SKETCH_GUIDE, ("a",))
    assert lesson_source_document_spec(_Classes({})).eligibility is not None
    assert isinstance(registry, JobKindRegistry)


def test_the_teacher_of_the_class_reads_the_job_with_result_refs() -> None:
    classes = _Classes({(ORG, "doc-1"): CLASS_A})
    reader, job = _reader(classes)
    read = reader.read(_actor({CLASS_A: {"teacher"}}, roles={"teacher"}), job.job_id)
    assert read.status.role is PrincipalRole.TEACHER
    assert read.target_kind is JobTargetKind.LESSON_SOURCE_DOCUMENT
    assert read.target_ref == "doc-1"
    view = read.status.view
    assert view is not None
    assert view["state"] == "succeeded" and view["poll_after_ms"] is None
    assert [item["artifact_ref"] for item in view["result_refs"]] == [
        "lesson-document-revision:rev-1"
    ]
    assert classes.calls == [(ORG, "doc-1")]


@pytest.mark.parametrize(
    ("label", "class_roles", "roles"),
    [
        ("guide of the class only", {CLASS_A: {"guide"}}, {"guide"}),
        ("observer of the class only", {CLASS_A: {"observer"}}, {"observer"}),
        ("teacher of another class", {CLASS_B: {"teacher"}}, {"teacher"}),
        # T0.4-DEBT-1: the union of organization roles must not grant the class-A projection
        (
            "observer of A and teacher of B",
            {CLASS_A: {"observer"}, CLASS_B: {"teacher"}},
            {"observer", "teacher"},
        ),
        ("School Manager who teaches B", {CLASS_B: {"teacher"}}, {"school_admin", "teacher"}),
        ("School Manager organization-wide", {}, {"school_admin"}),
        ("no class at all", {}, {"teacher"}),
    ],
)
def test_nobody_but_the_teacher_of_that_class_reads_the_job(
    label: str, class_roles: dict[str, set[str]], roles: set[str]
) -> None:
    reader, job = _reader(_Classes({(ORG, "doc-1"): CLASS_A}))
    with pytest.raises(JobNotVisible):
        reader.read(_actor(class_roles, roles=roles), job.job_id)


def test_a_school_manager_account_that_teaches_the_class_does_not_read_the_job() -> None:
    """Consistent with the document routes, which refuse that account too (F-02)."""
    reader, job = _reader(_Classes({(ORG, "doc-1"): CLASS_A}))
    manager = _actor(
        {CLASS_A: {"teacher"}},
        roles={"school_admin", "teacher"},
        account_role="school_manager",
    )
    with pytest.raises(JobNotVisible):
        reader.read(manager, job.job_id)
    teacher = _actor({CLASS_A: {"teacher"}}, roles={"school_admin", "teacher"})
    assert reader.read(teacher, job.job_id).status.role is PrincipalRole.TEACHER


def test_an_unknown_document_or_a_document_of_another_organization_is_not_visible() -> None:
    reader, job = _reader(_Classes({("other-org", "doc-1"): CLASS_A}))
    with pytest.raises(JobNotVisible):
        reader.read(_actor({CLASS_A: {"teacher"}}, roles={"teacher"}), job.job_id)


def test_a_revoked_assignment_gives_no_membership_and_no_read() -> None:
    reader, job = _reader(_Classes({(ORG, "doc-1"): CLASS_A}))
    actor = JobActor("acct-1", "teacher", lambda _org: None)
    with pytest.raises(JobNotVisible):
        reader.read(actor, job.job_id)


def test_a_parent_and_a_missing_id_stay_not_visible() -> None:
    reader, job = _reader(_Classes({(ORG, "doc-1"): CLASS_A}))
    parent = JobActor("acct-p", "parent", lambda _org: None)
    with pytest.raises(JobNotVisible):
        reader.read(parent, job.job_id)
    with pytest.raises(JobNotVisible):
        reader.read(_actor({CLASS_A: {"teacher"}}, roles={"teacher"}), "no-such-job")


def test_a_conditional_read_is_answered_only_after_the_class_rule() -> None:
    reader, job = _reader(_Classes({(ORG, "doc-1"): CLASS_A}))
    teacher = _actor({CLASS_A: {"teacher"}}, roles={"teacher"})
    first = reader.read(teacher, job.job_id)
    again = reader.read(teacher, job.job_id, first.status.etag)
    assert again.status.not_modified
    with pytest.raises(JobNotVisible):
        reader.read(
            _actor({CLASS_A: {"observer"}}, roles={"observer"}), job.job_id, first.status.etag
        )


# ----------------------------------------------------------------------------- real parser
def _zip(entries: dict[str, bytes], *, flag_bits: int = 0) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    raw = bytearray(buffer.getvalue())
    if flag_bits:
        # set the "encrypted" bit in every local and central header (general purpose bit flag)
        for signature, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            start = 0
            while (index := raw.find(signature, start)) != -1:
                flags = struct.unpack_from("<H", raw, index + offset)[0] | flag_bits
                struct.pack_into("<H", raw, index + offset, flags)
                start = index + 4
    return bytes(raw)


DOCX_PARTS = {"[Content_Types].xml": b"<Types/>", "word/document.xml": b"<w:document/>"}
PPTX_PARTS = {"[Content_Types].xml": b"<Types/>", "ppt/presentation.xml": b"<p:presentation/>"}


def _extract(data: bytes, extension: str) -> LessonDocumentExtraction:
    return DeterministicLessonDocumentParser().extract(io.BytesIO(data), file_extension=extension)


@pytest.mark.parametrize(
    ("data", "extension", "code"),
    [
        (b"%PDF-1.4 fine", ".exe", "UNSUPPORTED_MEDIA_TYPE"),
        (b"not a pdf at all", ".pdf", "INVALID_SOURCE_DOCUMENT"),
        (b"PK\x03\x04 not really a zip", ".docx", "INVALID_SOURCE_DOCUMENT"),
        (_zip({"[Content_Types].xml": b"<Types/>"}), ".docx", "INVALID_SOURCE_DOCUMENT"),
        (_zip(PPTX_PARTS), ".docx", "INVALID_SOURCE_DOCUMENT"),
        (
            _zip({**DOCX_PARTS, "../evil.xml": b"x"}),
            ".docx",
            "INVALID_SOURCE_DOCUMENT",
        ),
        (
            _zip({**DOCX_PARTS, "word/bomb.bin": b"\x00" * (3 * 1024 * 1024)}),
            ".docx",
            "DOCUMENT_EXPANSION_LIMIT_EXCEEDED",
        ),
        (_zip(DOCX_PARTS, flag_bits=1), ".docx", "ENCRYPTED_DOCUMENT_UNSUPPORTED"),
        (_zip(PPTX_PARTS, flag_bits=1), ".pptx", "ENCRYPTED_DOCUMENT_UNSUPPORTED"),
    ],
)
def test_the_real_parser_refuses_bad_files_before_any_document_library_runs(
    data: bytes, extension: str, code: str
) -> None:
    with pytest.raises(LessonDocumentRejected) as error:
        _extract(data, extension)
    assert error.value.code == code


def test_a_document_parser_fault_is_never_a_500() -> None:
    """A well-formed container that the library cannot read (or is missing) is unreadable."""
    with pytest.raises(LessonDocumentRejected) as error:
        _extract(_zip(DOCX_PARTS), ".docx")
    assert error.value.code == "INVALID_SOURCE_DOCUMENT"


def test_a_docx_text_is_extracted_normalised_and_hashed() -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("Tiêu đề: Vẽ con mèo")
    document.add_paragraph("Mục tiêu: Nhận biết hình dạng")
    buffer = io.BytesIO()
    document.save(buffer)
    extraction = _extract(buffer.getvalue(), ".docx")
    assert "Vẽ con mèo" in extraction.extracted_text
    assert extraction.page_or_slide_count is None and extraction.page_coverage == (1,)
    assert storable(extraction.extracted_text)
    assert extraction.detected_media_type.endswith("wordprocessingml.document")


def test_a_docx_over_two_mebibytes_of_vietnamese_text_is_refused_by_bytes() -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    alphabet = "ăâêôơưđáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ"
    generator = random.Random(3)  # varied text: repeated text would trip the ratio guard instead
    for _ in range(1100):  # 1.1 million characters = at least 2.2 MiB of UTF-8
        document.add_paragraph("".join(generator.choices(alphabet, k=1000)))
    buffer = io.BytesIO()
    document.save(buffer)
    with pytest.raises(LessonDocumentRejected) as error:
        _extract(buffer.getvalue(), ".docx")
    assert error.value.code == "DOCUMENT_TEXT_LIMIT_EXCEEDED"


def test_a_pptx_marks_the_slides_without_text() -> None:
    pptx = pytest.importorskip("pptx")
    presentation = pptx.Presentation()
    layout = presentation.slide_layouts[5]
    with_text = presentation.slides.add_slide(layout)
    with_text.shapes.title.text = "Tiêu đề: Vẽ con mèo"
    presentation.slides.add_slide(presentation.slide_layouts[6])  # blank slide
    buffer = io.BytesIO()
    presentation.save(buffer)
    extraction = _extract(buffer.getvalue(), ".pptx")
    assert extraction.page_or_slide_count == 2 and extraction.page_coverage == (1,)
    warnings = rules.derive_warnings(
        extraction.warnings, extraction.page_or_slide_count, extraction.page_coverage
    )
    assert "OCR_NOT_SUPPORTED_PAGES" in warnings


def test_a_pptx_with_no_text_at_all_is_a_scan_only_document() -> None:
    pptx = pytest.importorskip("pptx")
    presentation = pptx.Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    buffer = io.BytesIO()
    presentation.save(buffer)
    with pytest.raises(LessonDocumentRejected) as error:
        _extract(buffer.getvalue(), ".pptx")
    assert error.value.code == "OCR_NOT_SUPPORTED"


def test_the_extraction_port_keeps_its_old_shape_with_an_empty_text_default() -> None:
    legacy = LessonDocumentExtraction(
        detected_media_type="application/pdf",
        parser_name="p",
        parser_version="1",
        page_or_slide_count=None,
        page_coverage=(),
        extracted_fields={},
        warnings=(),
    )
    assert legacy.extracted_text == ""


def storable(text: str) -> bool:
    return rules.storable_text_problem(text) is None
