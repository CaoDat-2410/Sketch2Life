"""FEAT-018 P2-T1 D2 use case: the isolated image-admission service (D1 section 1).

Additive and isolated from FEAT-003. This layer depends only inward, on the domain policy
and the decoder port's abstract interface; it never reaches into an outer/infrastructure
or interface layer directly. Owns the single controlled byte snapshot: opens the source
path once, reads at most the byte budget, hashes the complete snapshot, and passes only
that snapshot (never the path) to the injected decoder port for metadata, frame-count, and
one-frame-decode operations. See evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md (D1) section 3
for the exact bounded data flow this implements.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from sketch2life.application.ports.image_decoder import (
    ImageDecodeProcessingError,
    ImageDecoderPort,
    ImageDecodeSourceError,
    ImageDecodeTimeoutError,
)
from sketch2life.contracts.schemas.media_validation import SourceMediaReferenceV1
from sketch2life.domain.understanding.image_admission import (
    AdmissionDecision,
    AdmissionOutcome,
    AdmissionReason,
    Feat018AdmissionLimits,
    ImageMetadataSignals,
    evaluate_cross_check,
    evaluate_frame_count,
    evaluate_metadata,
    outcome_for_reason,
)

_READ_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class Feat018AdmissionRequest:
    path: Path
    artifact_ref: str


@dataclass(frozen=True, slots=True)
class Feat018AdmissionResult:
    """`source` is populated only when `decision.outcome is AdmissionOutcome.ADMITTED`; it
    reuses the existing public `SourceMediaReferenceV1` unchanged and is never a parallel
    schema. No `MediaValidationResultV1` is produced anywhere in this service."""

    decision: AdmissionDecision
    source: SourceMediaReferenceV1 | None


class Feat018ImageAdmission:
    """Explicitly constructed with an injected decoder and limits; never a module default."""

    def __init__(
        self, decoder: ImageDecoderPort, limits: Feat018AdmissionLimits | None = None
    ) -> None:
        self._decoder = decoder
        self._limits = limits or Feat018AdmissionLimits()

    def admit(self, request: Feat018AdmissionRequest) -> Feat018AdmissionResult:
        try:
            snapshot, exceeded = self._read_bounded(request.path)
        except OSError:
            return self._result(AdmissionReason.MISSING_SOURCE, digest=None, metadata=None)

        if exceeded:
            return self._result(
                AdmissionReason.FILE_BYTES_EXCEEDED, digest=None, metadata=None
            )

        digest = sha256(snapshot).hexdigest()

        try:
            return self._admit_from_snapshot(snapshot, digest, request.artifact_ref)
        except Exception:  # noqa: BLE001 - last-resort: never leak a raw traceback as the
            # admission result; any bug in this service (not the decoder) becomes a typed,
            # honest INTERNAL_ERROR instead of an unhandled exception.
            return self._result(
                AdmissionReason.INTERNAL_ERROR, digest=digest, metadata=None
            )

    def _admit_from_snapshot(
        self, snapshot: bytes, digest: str, artifact_ref: str
    ) -> Feat018AdmissionResult:
        metadata = self._decoder.read_metadata(snapshot)
        reason = evaluate_metadata(metadata, self._limits)
        if reason is not None:
            return self._result(reason, digest=digest, metadata=metadata)
        assert metadata is not None  # evaluate_metadata returned None only if metadata exists

        try:
            frame_count = self._decoder.probe_frame_count(snapshot)
        except ImageDecodeTimeoutError:
            return self._result(
                AdmissionReason.DECODER_TIMEOUT, digest=digest, metadata=metadata
            )
        except ImageDecodeSourceError:
            return self._result(
                AdmissionReason.CORRUPT_OR_TRUNCATED, digest=digest, metadata=metadata
            )
        except ImageDecodeProcessingError:
            return self._result(
                AdmissionReason.DECODER_ERROR, digest=digest, metadata=metadata
            )

        reason = evaluate_frame_count(frame_count, self._limits)
        if reason is not None:
            return self._result(reason, digest=digest, metadata=metadata)

        try:
            decoded = self._decoder.decode_one_frame(snapshot)
        except ImageDecodeTimeoutError:
            return self._result(
                AdmissionReason.DECODER_TIMEOUT, digest=digest, metadata=metadata
            )
        except ImageDecodeSourceError:
            return self._result(
                AdmissionReason.CORRUPT_OR_TRUNCATED, digest=digest, metadata=metadata
            )
        except ImageDecodeProcessingError:
            return self._result(
                AdmissionReason.DECODER_ERROR, digest=digest, metadata=metadata
            )

        reason = evaluate_cross_check(metadata, decoded)
        if reason is not None:
            return self._result(reason, digest=digest, metadata=metadata)

        return self._result(
            None, digest=digest, metadata=metadata, artifact_ref=artifact_ref
        )

    def _read_bounded(self, path: Path) -> tuple[bytes, bool]:
        """Reads at most `limit + 1` bytes total, ever — not merely rejecting after the
        fact once a full chunk has pushed the total over budget. Each individual read is
        itself capped to `min(_READ_CHUNK_BYTES, limit + 1 - total)`, so the very last read
        can request only as many bytes as remain before the ceiling, and the running total
        can never exceed `limit + 1` regardless of how large the source actually is.
        Returns `(b"", True)` on overflow — the partial snapshot is discarded and never
        hashed, so an oversized file never gets even a prefix digest."""

        limit = self._limits.max_file_bytes
        ceiling = limit + 1
        chunks: list[bytes] = []
        total = 0
        with path.open("rb") as source:
            while total <= limit:
                request_size = min(_READ_CHUNK_BYTES, ceiling - total)
                chunk = source.read(request_size)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
        if total > limit:
            return b"", True
        return b"".join(chunks), False

    def _result(
        self,
        reason: AdmissionReason | None,
        *,
        digest: str | None,
        metadata: ImageMetadataSignals | None,
        artifact_ref: str | None = None,
    ) -> Feat018AdmissionResult:
        outcome = AdmissionOutcome.ADMITTED if reason is None else outcome_for_reason(reason)
        decision = AdmissionDecision(
            outcome=outcome, reason=reason, digest=digest, metadata=metadata
        )
        source: SourceMediaReferenceV1 | None = None
        if outcome is AdmissionOutcome.ADMITTED:
            if digest is None or artifact_ref is None:
                raise RuntimeError("ADMITTED outcome requires a complete digest and artifact_ref")
            source = SourceMediaReferenceV1(
                artifact_ref=artifact_ref, sha256=digest, source_status="AVAILABLE"
            )
        return Feat018AdmissionResult(decision=decision, source=source)
