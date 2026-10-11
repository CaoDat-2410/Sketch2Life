from __future__ import annotations

import io
from hashlib import sha256
from pathlib import Path
from struct import pack
from zlib import compress, crc32

import av
import pytest

from sketch2life.application.services.image_admission import (
    Feat018AdmissionRequest,
    Feat018AdmissionResult,
    Feat018ImageAdmission,
)
from sketch2life.application.services.media_validation import (
    ImageOnlyStructuralMediaValidator,
    ImageOnlyValidationRequest,
)
from sketch2life.benchmark.feat018_live_lightning_binding import runtime_config_sha256
from sketch2life.benchmark.feat018_live_preflight import (
    HostPreflightInputs,
    observe_host_preflight,
)
from sketch2life.contracts.schemas.feat018_live_wiring import LiveObservationInputError
from sketch2life.contracts.schemas.media_validation import (
    ImageOnlyValidationResultV1,
    ImageOnlyValidationStatus,
    SourceMediaReferenceV1,
    image_only_validation_artifact_sha256,
)
from sketch2life.domain.understanding.image_admission import (
    AdmissionDecision,
    AdmissionOutcome,
    AdmissionReason,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder

_PROMPT = "synthetic W1 producer prompt; never a FEAT-003 prompt"
_PROMPT_SHA256 = sha256(_PROMPT.encode("utf-8")).hexdigest()
_REFERENCE = "fixture:drawing:v1"
_VALIDATOR = "feat018-image-only-structural-validator-v1"
_VALIDATOR_POLICY = "feat018-image-only-structural-policy-v1"
_CONTENT_POLICY_VERSION = "vision-prohibited-lexicon-fixture-v1"
_POLICY_VIEW_VERSION = "vision-policy-match-view-v2"
_MAX_BYTES = 8 * 1024 * 1024


class _Policy:
    content_policy_version = _CONTENT_POLICY_VERSION
    policy_match_view_version = _POLICY_VIEW_VERSION

    def evaluate(self, *_args: object) -> None:
        return None


class _NeverCalled:
    def admit(self, request: Feat018AdmissionRequest) -> Feat018AdmissionResult:
        raise AssertionError("admission must not run")

    def validate(self, request: ImageOnlyValidationRequest) -> ImageOnlyValidationResultV1:
        raise AssertionError("validation must not run")


class _Raises:
    def admit(self, request: Feat018AdmissionRequest) -> Feat018AdmissionResult:
        raise RuntimeError("private-marker-text")

    def validate(self, request: ImageOnlyValidationRequest) -> ImageOnlyValidationResultV1:
        raise RuntimeError("private-marker-text")


class _WrongType:
    def admit(self, request: Feat018AdmissionRequest) -> object:
        return object()

    def validate(self, request: ImageOnlyValidationRequest) -> object:
        return {"status": "PASS"}


class _OtherDigestAdmission:
    """Reports an ADMITTED decision for different bytes, as if the file changed."""

    def admit(self, request: Feat018AdmissionRequest) -> Feat018AdmissionResult:
        digest = "f" * 64
        return Feat018AdmissionResult(
            decision=AdmissionDecision(
                outcome=AdmissionOutcome.ADMITTED, reason=None, digest=digest, metadata=None
            ),
            source=SourceMediaReferenceV1(
                artifact_ref=request.artifact_ref, sha256=digest, source_status="AVAILABLE"
            ),
        )


def _png_payload(width: int = 160, height: int = 160) -> bytes:
    raw = b"".join(
        b"\x00" + b"".join(bytes((20, 20 + (x + y) % 200, 200)) for x in range(width))
        for y in range(height)
    )
    header = pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", compress(raw))
        + _png_chunk(b"IEND", b"")
    )


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return pack(">I", len(data)) + kind + data + pack(">I", crc32(kind + data) & 0xFFFFFFFF)


def _jpeg_payload(width: int = 160, height: int = 160) -> bytes:
    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format="mjpeg") as container:
        stream = container.add_stream("mjpeg", rate=1)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuvj420p"
        frame = av.VideoFrame(width, height, "rgb24")
        plane = frame.planes[0]
        row = bytes([128, 128, 128]) * width
        plane.update((row + b"\x00" * (plane.line_size - len(row))) * height)
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return buffer.getvalue()


def _services() -> tuple[Feat018ImageAdmission, ImageOnlyStructuralMediaValidator]:
    return (
        Feat018ImageAdmission(AvImageDecoder()),
        ImageOnlyStructuralMediaValidator(AvImageDecoder()),
    )


def _inputs(path: Path, payload: bytes, tmp_path: Path, **overrides: object) -> HostPreflightInputs:
    config = QwenVisionRuntimeConfig(model_dir=tmp_path / "model-dir")
    values: dict[str, object] = {
        "fixture_path": path,
        "max_fixture_bytes": _MAX_BYTES,
        "expected_source_sha256": sha256(payload).hexdigest(),
        "validation_artifact_ref": _REFERENCE,
        "expected_validator_identity": _VALIDATOR,
        "expected_validator_policy_version": _VALIDATOR_POLICY,
        "expected_validation_artifact_sha256": None,
        "prompt": _PROMPT,
        "expected_prompt_sha256": _PROMPT_SHA256,
        "runtime_config": config,
        "expected_runtime_config_sha256": runtime_config_sha256(config),
        "content_policy": _Policy(),
        "expected_content_policy_version": _CONTENT_POLICY_VERSION,
        "expected_policy_match_view_version": _POLICY_VIEW_VERSION,
    }
    values.update(overrides)
    return HostPreflightInputs(**values)  # type: ignore[arg-type]


def _fixture(tmp_path: Path, kind: str = "png") -> tuple[Path, bytes]:
    payload = _jpeg_payload() if kind == "jpeg" else _png_payload()
    path = tmp_path / f"fixture.{kind}"
    path.write_bytes(payload)
    return path, payload


@pytest.mark.parametrize("kind", ["png", "jpeg"])
def test_real_services_accept_a_synthetic_fixture(kind: str, tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path, kind)
    admission, validator = _services()

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=admission, validator=validator
    )

    expected_result = validator.validate(
        ImageOnlyValidationRequest(path, _REFERENCE, sha256(payload).hexdigest())
    )
    assert observation.accepted is True
    assert observation.failure_codes == ()
    assert observation.live_authorized is False
    assert observation.observed_source_sha256 == sha256(payload).hexdigest()
    assert observation.source_stable is True
    assert observation.admission_outcome == "ADMITTED"
    assert observation.validation_decision == "PASS"
    assert observation.validation_artifact_sha256 == image_only_validation_artifact_sha256(
        expected_result
    )
    assert observation.validation_artifact_matches is None
    serialized = observation.model_dump_json()
    assert str(tmp_path) not in serialized
    assert _PROMPT not in serialized
    assert _PROMPT not in repr(_inputs(path, payload, tmp_path))
    assert str(tmp_path) not in repr(_inputs(path, payload, tmp_path))


def test_expected_validation_artifact_digest_is_compared(tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    admission, validator = _services()
    first = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=admission, validator=validator
    )
    assert first.validation_artifact_sha256 is not None

    matching = observe_host_preflight(
        _inputs(
            path, payload, tmp_path,
            expected_validation_artifact_sha256=first.validation_artifact_sha256,
        ),
        admission=admission,
        validator=validator,
    )
    mismatching = observe_host_preflight(
        _inputs(path, payload, tmp_path, expected_validation_artifact_sha256="0" * 64),
        admission=admission,
        validator=validator,
    )

    assert matching.accepted is True
    assert matching.validation_artifact_matches is True
    assert mismatching.accepted is False
    assert mismatching.validation_artifact_matches is False
    assert mismatching.failure_codes == ("VALIDATION_ARTIFACT_MISMATCH",)


def test_source_digest_mismatch_stops_before_any_service(tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    never = _NeverCalled()

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path, expected_source_sha256="0" * 64),
        admission=never,
        validator=never,
    )

    assert observation.accepted is False
    assert observation.failure_codes == ("SOURCE_DIGEST_MISMATCH",)
    assert observation.source_matches is False
    assert observation.source_stable is None
    assert observation.admission_outcome == "NOT_RUN"
    assert observation.validation_decision == "NOT_RUN"


def test_missing_unreadable_and_oversized_fixtures_fail_closed(tmp_path: Path) -> None:
    _, payload = _fixture(tmp_path)
    never = _NeverCalled()
    directory = tmp_path / "directory"
    directory.mkdir()
    oversized = tmp_path / "oversized.png"
    oversized.write_bytes(payload)

    missing = observe_host_preflight(
        _inputs(tmp_path / "absent.png", payload, tmp_path), admission=never, validator=never
    )
    unreadable = observe_host_preflight(
        _inputs(directory, payload, tmp_path), admission=never, validator=never
    )
    too_large = observe_host_preflight(
        _inputs(oversized, payload, tmp_path, max_fixture_bytes=len(payload) - 1),
        admission=never,
        validator=never,
    )

    assert missing.failure_codes == ("FIXTURE_MISSING",)
    assert unreadable.failure_codes == ("FIXTURE_UNREADABLE",)
    assert too_large.failure_codes == ("FIXTURE_TOO_LARGE",)
    for observation in (missing, unreadable, too_large):
        assert observation.accepted is False
        assert observation.observed_source_sha256 is None
        assert observation.source_stable is None


def test_a_non_image_is_rejected_by_admission_and_validation(tmp_path: Path) -> None:
    payload = b"synthetic bytes that are not an image " * 8
    path = tmp_path / "not-an-image.png"
    path.write_bytes(payload)
    admission, validator = _services()

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=admission, validator=validator
    )

    assert observation.accepted is False
    assert observation.admission_outcome != "ADMITTED"
    assert observation.admission_reason is not None
    assert observation.validation_decision == "FAIL"
    assert observation.validation_failure_code is not None
    assert "ADMISSION_NOT_ADMITTED" in observation.failure_codes
    assert "VALIDATION_NOT_PASS" in observation.failure_codes
    assert observation.source_stable is True


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"prompt": ""}, "PROMPT_INVALID"),
        ({"prompt": 7}, "PROMPT_INVALID"),
        ({"prompt": "\ud800"}, "PROMPT_INVALID"),
        ({"prompt": _PROMPT + " changed"}, "PROMPT_HASH_MISMATCH"),
        ({"expected_runtime_config_sha256": "0" * 64}, "RUNTIME_CONFIG_IDENTITY_MISMATCH"),
        ({"expected_content_policy_version": "other-policy-v1"}, "POLICY_IDENTITY_MISMATCH"),
        ({"expected_policy_match_view_version": "other-view-v1"}, "POLICY_IDENTITY_MISMATCH"),
        ({"content_policy": object()}, "POLICY_IDENTITY_MISMATCH"),
        ({"expected_validator_identity": "other-validator-v1"}, "VALIDATION_IDENTITY_MISMATCH"),
        ({"expected_validator_policy_version": "other-policy-v1"}, "VALIDATION_IDENTITY_MISMATCH"),
    ],
)
def test_identity_mismatches_have_closed_codes(
    overrides: dict[str, object], code: str, tmp_path: Path
) -> None:
    path, payload = _fixture(tmp_path)
    admission, validator = _services()

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path, **overrides), admission=admission, validator=validator
    )

    assert observation.accepted is False
    assert observation.failure_codes == (code,)
    assert observation.admission_outcome == "ADMITTED"
    assert observation.validation_decision == "PASS"
    assert "private" not in observation.model_dump_json()


def test_non_callable_policy_evaluate_is_a_mismatch(tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    admission, validator = _services()
    policy = _Policy()
    policy.evaluate = "not callable"  # type: ignore[assignment,method-assign]

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path, content_policy=policy),
        admission=admission,
        validator=validator,
    )

    assert observation.failure_codes == ("POLICY_IDENTITY_MISMATCH",)


def test_service_exceptions_and_malformed_results_fail_closed(tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    admission, validator = _services()

    raised = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=_Raises(), validator=_Raises()
    )
    malformed = observe_host_preflight(
        _inputs(path, payload, tmp_path),
        admission=_WrongType(),  # type: ignore[arg-type]
        validator=_WrongType(),  # type: ignore[arg-type]
    )
    unstable = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=_OtherDigestAdmission(), validator=validator
    )

    for observation in (raised, malformed):
        assert observation.accepted is False
        assert observation.failure_codes == ("ADMISSION_EXCEPTION", "VALIDATION_EXCEPTION")
        assert observation.admission_outcome == "NOT_RUN"
        assert observation.validation_decision == "NOT_RUN"
        # No service returned a digest, so no stability comparison happened.
        assert observation.source_stable is None
        assert "private-marker-text" not in observation.model_dump_json()
    assert unstable.accepted is False
    assert unstable.failure_codes == ("SOURCE_UNSTABLE",)
    assert unstable.source_stable is False


class _InconsistentAdmission:
    """Returns one inconsistent admission result shape chosen by the test."""

    def __init__(self, kind: str, observed: str) -> None:
        self._kind = kind
        self._observed = observed

    def admit(self, request: Feat018AdmissionRequest) -> Feat018AdmissionResult:
        digest: str | None = self._observed
        outcome = AdmissionOutcome.ADMITTED
        reason: AdmissionReason | None = None
        source: SourceMediaReferenceV1 | None = SourceMediaReferenceV1(
            artifact_ref=request.artifact_ref, sha256=digest, source_status="AVAILABLE"
        )
        if self._kind == "admitted_with_reason":
            reason = AdmissionReason.NOT_AN_IMAGE
        elif self._kind == "malformed_digest":
            digest = "NOT-A-DIGEST"
            source = None
        elif self._kind == "rejected_with_malformed_digest":
            # Only the digest-format guard rejects this shape.
            outcome = AdmissionOutcome.REJECTED
            reason = AdmissionReason.NOT_AN_IMAGE
            digest = "NOT-A-DIGEST"
            source = None
        elif self._kind == "admitted_without_digest":
            # Only the "digest is None" guard rejects this shape.
            digest = None
            source = SourceMediaReferenceV1(
                artifact_ref=request.artifact_ref, sha256=None, source_status="MISSING"
            )
        elif self._kind == "other_reference":
            source = SourceMediaReferenceV1(
                artifact_ref="fixture:drawing:v2", sha256=digest, source_status="AVAILABLE"
            )
        elif self._kind == "source_digest_differs":
            source = SourceMediaReferenceV1(
                artifact_ref=request.artifact_ref, sha256="e" * 64, source_status="AVAILABLE"
            )
        elif self._kind == "admitted_without_source":
            source = None
        elif self._kind == "rejected_without_reason":
            outcome = AdmissionOutcome.REJECTED
            source = None
        return Feat018AdmissionResult(
            decision=AdmissionDecision(
                outcome=outcome, reason=reason, digest=digest, metadata=None
            ),
            source=source,
        )


@pytest.mark.parametrize(
    "kind",
    [
        "admitted_with_reason",
        "malformed_digest",
        "rejected_with_malformed_digest",
        "admitted_without_digest",
        "other_reference",
        "source_digest_differs",
        "admitted_without_source",
        "rejected_without_reason",
    ],
)
def test_inconsistent_admission_results_fail_closed(kind: str, tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    _, validator = _services()

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path),
        admission=_InconsistentAdmission(kind, sha256(payload).hexdigest()),
        validator=validator,
    )

    assert observation.accepted is False
    assert observation.failure_codes == ("ADMISSION_EXCEPTION",)
    assert observation.admission_outcome == "NOT_RUN"
    assert observation.admission_reason is None
    assert observation.validation_decision == "PASS"
    # The validator digest was compared and agrees with the producer's own read.
    assert observation.source_stable is True


def test_validator_reporting_another_source_digest_is_unstable(tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    other_path = tmp_path / "other.png"
    other_payload = _png_payload(96, 96)
    other_path.write_bytes(other_payload)
    admission, validator = _services()
    other_result = validator.validate(
        ImageOnlyValidationRequest(other_path, _REFERENCE, sha256(other_payload).hexdigest())
    )

    class _OtherFileValidator:
        def validate(self, request: ImageOnlyValidationRequest) -> ImageOnlyValidationResultV1:
            return other_result

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=admission, validator=_OtherFileValidator()
    )

    assert observation.accepted is False
    assert observation.failure_codes == ("SOURCE_UNSTABLE",)
    assert observation.source_stable is False
    assert observation.admission_outcome == "ADMITTED"
    assert observation.validation_decision == "PASS"


@pytest.mark.parametrize("error", [RuntimeError, ValueError])
def test_unexpected_read_errors_map_to_a_closed_code(
    error: type[Exception], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, payload = _fixture(tmp_path)
    never = _NeverCalled()
    original_open = Path.open

    def failing_open(self: Path, *args: object, **kwargs: object) -> object:
        if self == path:
            raise error(f"private-marker-text {path}")
        return original_open(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "open", failing_open)
    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=never, validator=never
    )

    assert observation.failure_codes == ("FIXTURE_UNREADABLE",)
    serialized = observation.model_dump_json()
    assert "private-marker-text" not in serialized
    assert str(tmp_path) not in serialized


def test_unchecked_validator_result_is_reparsed_and_rejected(tmp_path: Path) -> None:
    path, payload = _fixture(tmp_path)
    admission, validator = _services()
    genuine = validator.validate(
        ImageOnlyValidationRequest(path, _REFERENCE, sha256(payload).hexdigest())
    )
    # FAIL without a failure code or failed check violates the contract invariants.
    forged = ImageOnlyValidationResultV1.model_construct(
        **{**genuine.__dict__, "status": ImageOnlyValidationStatus.FAIL}
    )

    class _ForgedValidator:
        def validate(self, request: ImageOnlyValidationRequest) -> ImageOnlyValidationResultV1:
            return forged

    observation = observe_host_preflight(
        _inputs(path, payload, tmp_path), admission=admission, validator=_ForgedValidator()
    )

    assert observation.failure_codes == ("VALIDATION_EXCEPTION",)
    assert observation.validation_decision == "NOT_RUN"


@pytest.mark.parametrize(
    "overrides",
    [
        {"expected_source_sha256": "A" * 64},
        {"expected_prompt_sha256": "short"},
        {"expected_runtime_config_sha256": None},
        {"expected_validation_artifact_sha256": "g" * 64},
        {"validation_artifact_ref": "fixture:unknown:v1"},
        {"validation_artifact_ref": "bad reference private-marker-text"},
        {"expected_validator_identity": "has space"},
        {"expected_content_policy_version": ""},
        {"max_fixture_bytes": 0},
        {"max_fixture_bytes": True},
        {"max_fixture_bytes": 65 * 1024 * 1024},
        {"fixture_path": "not-a-path"},
        {"fixture_path": Path("fixture\x00private-marker-text.png")},
        {"runtime_config": object()},
    ],
)
def test_structural_inputs_raise_a_fixed_closed_error(
    overrides: dict[str, object], tmp_path: Path
) -> None:
    path, payload = _fixture(tmp_path)
    never = _NeverCalled()

    with pytest.raises(LiveObservationInputError) as caught:
        observe_host_preflight(
            _inputs(path, payload, tmp_path, **overrides), admission=never, validator=never
        )

    assert caught.value.code == "INPUT_INVALID"
    assert str(caught.value) == "live observation producer input is invalid"
    assert "private-marker-text" not in str(caught.value)


def test_inputs_type_is_required() -> None:
    never = _NeverCalled()

    with pytest.raises(LiveObservationInputError):
        observe_host_preflight(
            object(),  # type: ignore[arg-type]
            admission=never,
            validator=never,
        )
