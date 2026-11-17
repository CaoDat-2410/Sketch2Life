from __future__ import annotations

import hashlib
import multiprocessing
import os
import socket
import struct
import time
import zlib
from io import BytesIO
from threading import Thread
from typing import cast
from unittest.mock import Mock

import pytest
from PIL import Image

from sketch2life.application.ports.story_run_lite import (
    CommandResult,
    CoreAssetAdmissionPort,
    ImageNormalizerPort,
    ImageSafetyScannerPort,
    NormalizedImage,
    ScanVerdict,
    StoryRunLiteRepositoryPort,
    StoryRunLiteVisionPort,
    StoryRunReferencePort,
    UploadReservation,
)
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.contracts.schemas.story_run_lite import CompleteUploadRequest
from sketch2life.domain.story_run_lite import MAX_IMAGE_PIXELS
from sketch2life.infrastructure.story_run_lite.clamav import ClamAvScanner
from sketch2life.infrastructure.story_run_lite.image_worker import (
    WORKER_CPU_LIMIT_PERCENT,
    WORKER_DEADLINE_SECONDS,
    WORKER_MEMORY_LIMIT_BYTES,
    ImageNormalizationError,
    WindowsJobObjectImageNormalizer,
    _WindowsJobObject,
)


def _image_bytes(image_format: str, size: tuple[int, int] = (64, 48)) -> bytes:
    stream = BytesIO()
    Image.new("RGB", size, color=(25, 80, 145)).save(stream, format=image_format)
    return stream.getvalue()


def test_clamd_version_and_instream_use_separate_connections() -> None:
    snapshot = _image_bytes("PNG")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(2)
    listener.settimeout(2)
    commands: list[bytes] = []
    scanned_bytes = bytearray()
    server_errors: list[Exception] = []

    def receive_command(connection: socket.socket) -> bytes:
        command = bytearray()
        while not command.endswith(b"\0"):
            chunk = connection.recv(1)
            if not chunk:
                break
            command.extend(chunk)
        return bytes(command)

    def receive_exact(connection: socket.socket, size: int) -> bytes:
        received = bytearray()
        while len(received) < size:
            chunk = connection.recv(size - len(received))
            if not chunk:
                raise AssertionError("ClamAV stream ended before its declared length")
            received.extend(chunk)
        return bytes(received)

    def serve() -> None:
        try:
            for _ in range(2):
                connection, _address = listener.accept()
                with connection:
                    connection.settimeout(2)
                    command = receive_command(connection)
                    commands.append(command)
                    if command == b"zVERSION\0":
                        connection.sendall(b"ClamAV 1.5.4\0")
                        continue
                    if command != b"zINSTREAM\0":
                        raise AssertionError(f"unexpected ClamAV command: {command!r}")
                    while True:
                        size = struct.unpack("!I", receive_exact(connection, 4))[0]
                        if size == 0:
                            break
                        scanned_bytes.extend(receive_exact(connection, size))
                    connection.sendall(b"stream: OK\0")
        except Exception as error:
            server_errors.append(error)

    thread = Thread(target=serve, daemon=True)
    thread.start()
    try:
        scanner = ClamAvScanner(
            host="127.0.0.1", port=int(listener.getsockname()[1]), timeout_seconds=2
        )
        result = scanner.scan(snapshot, hashlib.sha256(snapshot).hexdigest())
    finally:
        listener.close()
        thread.join(timeout=3)

    assert not thread.is_alive()
    assert not server_errors
    assert commands == [b"zVERSION\0", b"zINSTREAM\0"]
    assert bytes(scanned_bytes) == snapshot
    assert result.decision == "CLEAN"
    assert result.scanner_version == "ClamAV 1.5.4"


@pytest.mark.parametrize(
    ("image_format", "media_type"),
    [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")],
)
def test_isolated_worker_normalizes_jpeg_png_and_webp(
    tmp_path, image_format: str, media_type: str
) -> None:
    source = _image_bytes(image_format)
    digest = hashlib.sha256(source).hexdigest()
    result = WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
        source, original_media_type=media_type, sha256=digest
    )
    assert (result.width, result.height) == (64, 48)
    assert result.original_sha256 == digest
    assert result.derived_media_type == "image/jpeg"
    assert result.derived_size_bytes == len(result.derived_bytes)
    assert hashlib.sha256(result.derived_bytes).hexdigest() == result.derived_sha256
    assert result.worker_memory_limit_bytes == WORKER_MEMORY_LIMIT_BYTES
    assert result.worker_cpu_percent == WORKER_CPU_LIMIT_PERCENT
    assert result.worker_deadline_seconds == WORKER_DEADLINE_SECONDS
    assert result.worker_peak_memory_bytes <= WORKER_MEMORY_LIMIT_BYTES
    assert result.worker_cpu_hard_cap_percent == WORKER_CPU_LIMIT_PERCENT
    assert result.worker_elapsed_ms > 0


def test_worker_handles_a_synthetic_forty_megapixel_image(tmp_path) -> None:
    source = _image_bytes("JPEG", size=(8_000, 5_000))
    result = WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
        source,
        original_media_type="image/jpeg",
        sha256=hashlib.sha256(source).hexdigest(),
    )
    assert result.width * result.height == MAX_IMAGE_PIXELS
    assert result.derived_size_bytes <= 5_000_000
    cpu_ms = (result.worker_cpu_user_time_100ns + result.worker_cpu_kernel_time_100ns) / 10_000
    assert result.worker_peak_memory_bytes <= WORKER_MEMORY_LIMIT_BYTES
    assert result.worker_cpu_hard_cap_percent == WORKER_CPU_LIMIT_PERCENT
    assert result.worker_elapsed_ms > 0
    processor_count = os.cpu_count() or 1
    assert cpu_ms / (result.worker_elapsed_ms * processor_count) <= 0.35


def test_worker_rejects_malformed_bytes_as_an_image(tmp_path) -> None:
    source = b"synthetic-but-not-an-image"
    with pytest.raises(ImageNormalizationError) as error:
        WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
            source,
            original_media_type="image/jpeg",
            sha256=hashlib.sha256(source).hexdigest(),
        )
    assert error.value.code == "IMAGE_INVALID"


def test_worker_rejects_declared_media_type_mismatch(tmp_path) -> None:
    source = _image_bytes("JPEG")
    with pytest.raises(ImageNormalizationError) as error:
        WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
            source,
            original_media_type="image/png",
            sha256=hashlib.sha256(source).hexdigest(),
        )
    assert error.value.code == "UNSUPPORTED_MEDIA_TYPE"


def test_worker_rejects_animated_webp(tmp_path) -> None:
    stream = BytesIO()
    Image.new("RGB", (32, 24), color=(20, 40, 60)).save(
        stream,
        format="WEBP",
        save_all=True,
        append_images=[Image.new("RGB", (32, 24), color=(60, 40, 20))],
        duration=100,
        loop=0,
    )
    source = stream.getvalue()
    with pytest.raises(ImageNormalizationError) as error:
        WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
            source,
            original_media_type="image/webp",
            sha256=hashlib.sha256(source).hexdigest(),
        )
    assert error.value.code == "IMAGE_INVALID"


def test_worker_rejects_a_synthetic_image_above_the_pixel_limit(tmp_path) -> None:
    width, height = 10_000, 5_000
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = (
        struct.pack("!I", len(ihdr))
        + b"IHDR"
        + ihdr
        + struct.pack("!I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    )
    source = b"\x89PNG\r\n\x1a\n" + ihdr_chunk
    with pytest.raises(ImageNormalizationError) as error:
        WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
            source,
            original_media_type="image/png",
            sha256=hashlib.sha256(source).hexdigest(),
        )
    assert error.value.code in {"IMAGE_TOO_LARGE", "IMAGE_INVALID"}


def test_worker_rejects_digest_mismatch_before_spawning(tmp_path) -> None:
    with pytest.raises(ImageNormalizationError) as error:
        WindowsJobObjectImageNormalizer(temporary_root=tmp_path).normalize(
            _image_bytes("JPEG"), original_media_type="image/jpeg", sha256="0" * 64
        )
    assert error.value.code == "IMAGE_HASH_MISMATCH"


def _run_until_job_closes(connection) -> None:
    if connection.recv() != "RUN":
        return
    while True:
        time.sleep(0.05)


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object verification")
def test_job_object_kill_on_close_terminates_its_worker() -> None:
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=True)
    process = context.Process(target=_run_until_job_closes, args=(child,), daemon=False)
    job: _WindowsJobObject | None = None
    try:
        process.start()
        child.close()
        job = _WindowsJobObject(
            memory_bytes=WORKER_MEMORY_LIMIT_BYTES,
            cpu_percent=WORKER_CPU_LIMIT_PERCENT,
            cpu_seconds=WORKER_DEADLINE_SECONDS // 2,
        )
        job.assign(process.pid or 0)
        parent.send("RUN")
        time.sleep(0.2)
        job.close()
        process.join(timeout=2)
        assert not process.is_alive()
    finally:
        if job is not None:
            job.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
        parent.close()
        child.close()
        if process.pid is not None:
            process.close()


def test_scanner_precedes_image_decoder_and_receives_exact_snapshot() -> None:
    snapshot = _image_bytes("PNG")
    digest = hashlib.sha256(snapshot).hexdigest()
    derived = b"synthetic-derived-model-image"
    events: list[str] = []
    repository = Mock()
    accepted = CommandResult(202, {"state": "PROCESSING"}, 2)
    reservation = UploadReservation(
        command_result=CommandResult(202, {"state": "PENDING"}, 1),
        upload_id="synthetic-upload-1",
        claim_version=2,
        snapshot=snapshot,
        expected_sha256=digest,
        original_media_type="image/png",
        actor_scope_ref="synthetic-parent-local-v1",
    )
    repository.reserve_complete_upload.return_value = reservation
    repository.finalize_complete_upload.return_value = accepted
    repository.open_upload_gate.return_value = True
    repository.finish_upload_admission.return_value = True

    class Scanner:
        def scan(self, scanned_snapshot: bytes, sha256: str) -> ScanVerdict:
            events.append("scan")
            assert scanned_snapshot == snapshot
            assert sha256 == digest
            return ScanVerdict("CLEAN", digest, "test-stub-not-clamav", None)

    class Normalizer:
        def normalize(
            self, normalized_snapshot: bytes, *, original_media_type: str, sha256: str
        ) -> NormalizedImage:
            events.append("decode")
            assert events == ["scan", "decode"]
            assert normalized_snapshot == snapshot
            assert original_media_type == "image/png"
            assert sha256 == digest
            return NormalizedImage(
                original_media_type="image/png",
                original_sha256=digest,
                original_size_bytes=len(snapshot),
                width=64,
                height=48,
                derived_media_type="image/jpeg",
                derived_sha256=hashlib.sha256(derived).hexdigest(),
                derived_size_bytes=len(derived),
                derived_bytes=derived,
                worker_memory_limit_bytes=WORKER_MEMORY_LIMIT_BYTES,
                worker_cpu_percent=WORKER_CPU_LIMIT_PERCENT,
                worker_deadline_seconds=WORKER_DEADLINE_SECONDS,
                worker_peak_memory_bytes=20_000_000,
                worker_cpu_user_time_100ns=100,
                worker_cpu_kernel_time_100ns=100,
                worker_cpu_hard_cap_percent=WORKER_CPU_LIMIT_PERCENT,
                worker_elapsed_ms=1,
            )

    class NotInvokedVision:
        def analyze(self, **_values: object):  # pragma: no cover - not used in upload flow
            raise AssertionError("Vision must not run during upload admission")

    service = StoryRunLiteService(
        repository=cast(StoryRunLiteRepositoryPort, repository),
        scanner=cast(ImageSafetyScannerPort, Scanner()),
        normalizer=cast(ImageNormalizerPort, Normalizer()),
        vision=cast(StoryRunLiteVisionPort, NotInvokedVision()),
        story_references=cast(StoryRunReferencePort, repository),
        asset_admission=cast(CoreAssetAdmissionPort, repository),
    )
    result = service.complete_upload(
        upload_id="synthetic-upload-1",
        request=CompleteUploadRequest(expected_size_bytes=len(snapshot), expected_sha256=digest),
        if_match='"v1"',
        idempotency_key="synthetic-complete-1",
    )
    assert result is accepted
    assert events == ["scan", "decode"]
    repository.store_asset.assert_called()
    repository.finish_upload_admission.assert_called_once()
    repository.remove_upload_quarantine.assert_called_once_with("synthetic-upload-1")


@pytest.mark.parametrize(
    ("decision", "digest_matches", "failure_type", "expected_code"),
    [
        ("INFECTED", True, None, "IMAGE_INFECTED"),
        ("ERROR", True, None, "SCANNER_UNAVAILABLE"),
        ("CLEAN", False, None, "SCANNER_UNAVAILABLE"),
        ("CLEAN", True, OSError, "SCANNER_UNAVAILABLE"),
        ("CLEAN", True, TimeoutError, "SCANNER_UNAVAILABLE"),
    ],
)
def test_nonclean_or_unavailable_scanner_never_reaches_decoder(
    decision: str,
    digest_matches: bool,
    failure_type: type[Exception] | None,
    expected_code: str,
) -> None:
    snapshot = _image_bytes("JPEG")
    digest = hashlib.sha256(snapshot).hexdigest()
    events: list[str] = []
    repository = Mock()
    accepted = CommandResult(202, {"state": "PROCESSING"}, 2)
    repository.reserve_complete_upload.return_value = UploadReservation(
        command_result=CommandResult(202, {"state": "PENDING"}, 1),
        upload_id="synthetic-upload-failure",
        claim_version=2,
        snapshot=snapshot,
        expected_sha256=digest,
        original_media_type="image/jpeg",
        actor_scope_ref="synthetic-parent-local-v1",
    )
    repository.finalize_complete_upload.return_value = accepted
    repository.open_upload_gate.return_value = True

    class Scanner:
        def scan(self, scanned_snapshot: bytes, sha256: str) -> ScanVerdict:
            events.append("scan")
            assert scanned_snapshot == snapshot and sha256 == digest
            if failure_type is not None:
                raise failure_type("synthetic scanner unavailable")
            return ScanVerdict(
                decision,
                digest if digest_matches else "0" * 64,
                "test-stub-not-clamav",
                None,
            )

    class NeverNormalize:
        def normalize(self, *_args: object, **_kwargs: object) -> NormalizedImage:
            events.append("decode")
            raise AssertionError("unsafe input reached the image decoder")

    service = StoryRunLiteService(
        repository=cast(StoryRunLiteRepositoryPort, repository),
        scanner=cast(ImageSafetyScannerPort, Scanner()),
        normalizer=cast(ImageNormalizerPort, NeverNormalize()),
        vision=cast(StoryRunLiteVisionPort, Mock()),
        story_references=cast(StoryRunReferencePort, repository),
        asset_admission=cast(CoreAssetAdmissionPort, repository),
    )
    result = service.complete_upload(
        upload_id="synthetic-upload-failure",
        request=CompleteUploadRequest(expected_size_bytes=len(snapshot), expected_sha256=digest),
        if_match='"v1"',
        idempotency_key="synthetic-complete-failure-1",
    )
    assert result is accepted
    assert events == ["scan"]
    repository.fail_upload_admission.assert_called_once()
    assert repository.fail_upload_admission.call_args.kwargs["error_code"] == expected_code
    repository.store_asset.assert_not_called()
    repository.remove_upload_quarantine.assert_called_once_with("synthetic-upload-failure")


def test_decoder_failure_fails_closed_without_staging_or_vision_dispatch() -> None:
    snapshot = _image_bytes("PNG")
    digest = hashlib.sha256(snapshot).hexdigest()
    repository = Mock()
    accepted = CommandResult(202, {"state": "PROCESSING"}, 2)
    repository.reserve_complete_upload.return_value = UploadReservation(
        command_result=CommandResult(202, {"state": "PENDING"}, 1),
        upload_id="synthetic-upload-invalid-image",
        claim_version=2,
        snapshot=snapshot,
        expected_sha256=digest,
        original_media_type="image/png",
        actor_scope_ref="synthetic-parent-local-v1",
    )
    repository.finalize_complete_upload.return_value = accepted
    repository.open_upload_gate.return_value = True
    vision = Mock()

    class CleanTestScanner:
        def scan(self, scanned_snapshot: bytes, sha256: str) -> ScanVerdict:
            assert scanned_snapshot == snapshot and sha256 == digest
            return ScanVerdict("CLEAN", digest, "test-stub-not-clamav", None)

    class InvalidImageNormalizer:
        def normalize(self, *_args: object, **_kwargs: object) -> NormalizedImage:
            raise ImageNormalizationError("IMAGE_INVALID", "synthetic malformed fixture")

    service = StoryRunLiteService(
        repository=cast(StoryRunLiteRepositoryPort, repository),
        scanner=cast(ImageSafetyScannerPort, CleanTestScanner()),
        normalizer=cast(ImageNormalizerPort, InvalidImageNormalizer()),
        vision=cast(StoryRunLiteVisionPort, vision),
        story_references=cast(StoryRunReferencePort, repository),
        asset_admission=cast(CoreAssetAdmissionPort, repository),
    )
    result = service.complete_upload(
        upload_id="synthetic-upload-invalid-image",
        request=CompleteUploadRequest(expected_size_bytes=len(snapshot), expected_sha256=digest),
        if_match='"v1"',
        idempotency_key="synthetic-complete-invalid-image-1",
    )
    assert result is accepted
    repository.fail_upload_admission.assert_called_once()
    assert repository.fail_upload_admission.call_args.kwargs["error_code"] == "IMAGE_INVALID"
    repository.store_asset.assert_not_called()
    vision.analyze.assert_not_called()
