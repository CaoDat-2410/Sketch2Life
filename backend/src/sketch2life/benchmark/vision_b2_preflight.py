"""Internal (non-CLI) executor for the approved P2-T3 Phase B B2 typed GPU preflight.

This module is imported and called directly (e.g. from a script or test), never exposed as
a CLI -- the ~20-fixture end-to-end CLI/report remains P2-T5's scope, mirroring the P2-T2
`asr_round1_runner` precedent. It executes exactly one real B2 preflight call:

- writes a small synthetic image and a synthetic tone (never real child data) into the
  already-ignored ``data/runtime/`` scratch location, refusing up front -- before writing
  anything -- if ``fixtures_dir`` is not a safe ``shutil.rmtree`` target, and refusing again,
  before either file is opened, if the paths the builder returns are not real files strictly
  inside that directory;
- earns a real P2-T1 ``PASS`` through the real ``DeterministicMediaValidator`` -- never a
  fabricated one -- before the vision adapter is ever invoked;
- calls exactly one ``VisionUnderstandingPortV2.understand`` (the real ``QwenVisionAdapter``
  for a Lightning run, or an injected fake for unit tests -- the same test/real seam already
  used by ``Round1RunnerConfig.adapter_factory`` on the ASR side);
- measures wall-clock latency and GPU memory via ``nvidia-smi``, matching the ASR Round-1
  ``_VramSampler`` pattern; the sampler's background poller, once started, is always stopped
  and joined -- even when the adapter call raises -- so no thread outlives this function;
- deletes the scratch fixtures afterward in a ``finally`` that covers fixture creation itself,
  so a builder that writes one fixture and then raises still leaves nothing behind, and never
  fabricates a measurement: an unavailable value stays ``NOT_MEASURED`` (``None`` plus a
  stated reason), never ``0`` and never silently omitted.

Approved scope only: one real model load and one synthetic inference (B2). This module
performs no B3 mapping study, B4 benchmark, or B5 recommendation, and returns only closed
typed identifiers, measured numbers, and non-sensitive model-provenance strings -- never raw
model output, a prompt, or a local path.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from math import sin
from pathlib import Path
from struct import pack
from threading import Event, Thread
from wave import open as wave_open
from zlib import compress, crc32

from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.contracts.schemas.vision import (
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionModelProvenanceV1,
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

_DEFAULT_FIXTURES_DIR = Path("data/runtime/vision-b2-preflight")


class NoRealP2T1PassAvailableError(RuntimeError):
    """The synthetic preflight fixtures did not earn a real P2-T1 ``PASS``.

    B2 must call the adapter with a real, earned ``VisionMediaValidationProvenanceV1`` --
    never a fabricated one -- so this stops before the adapter is ever invoked rather than
    silently forcing a ``PASS``.
    """


class UnsafeFixturesDirectoryError(ValueError):
    """``fixtures_dir`` is not a safe ``shutil.rmtree`` cleanup target.

    A caller-supplied ``fixtures_dir`` is later deleted wholesale at cleanup, so it must
    resolve strictly inside the current working directory -- never an absolute path, the
    working directory itself, or one of its ancestors -- before this function writes a single
    byte to it. Refusing early keeps the mandatory cleanup step from ever being asked to
    remove something outside the intended ephemeral scratch location.
    """


class UnsafeFixturePathError(ValueError):
    """A path returned by ``build_fixtures`` is not a real file inside the guarded scratch dir.

    ``build_fixtures`` is caller-supplied (including test doubles), so its returned
    image/audio paths are never trusted implicitly: each is checked, by path metadata only --
    resolution and ``is_file()``, never by opening or reading the file's contents -- against
    the already safe-guarded ``fixtures_dir`` before this module reads either one or uses it
    as a relative ``artifact_ref``. A path that is absolute, resolves outside ``fixtures_dir``,
    equals ``fixtures_dir`` itself, is a directory, or does not exist is rejected here, before
    P2-T1 validation and before the adapter is ever called.
    """


@dataclass(frozen=True, slots=True)
class VisionB2PreflightResult:
    """Typed, evidence-safe record of one real B2 preflight call.

    Every field is a closed identifier already present on ``VisionUnderstandingResultV2``, a
    measured number, or an explicit ``None`` paired with ``vram_not_measured_reason`` --
    never raw model output, a prompt, or a local path.
    """

    profile_id: str
    profile_catalog_hash: str
    status: str
    attempt_number: int
    repair_attempted: bool
    policy_execution_state: str
    error_code: str | None
    error_detail: str | None
    model_identifier: str | None
    model_revision: str | None
    wall_latency_ms: float
    baseline_vram_mb: float | None
    peak_vram_mb: float | None
    post_call_vram_mb: float | None
    vram_not_measured_reason: str | None


class _VramSampler:
    """Background ``nvidia-smi`` poller. Silently inert (never fabricates) if unavailable.

    Mirrors ``sketch2life.benchmark.asr_round1_runner._VramSampler``; duplicated rather than
    imported to keep this feature's benchmark module independent of P2-T2's, matching the
    plan's "P2-T3 must not import from or depend on P2-T2's modules" boundary.
    """

    def __init__(self, device_index: int = 0, interval_seconds: float = 0.1) -> None:
        self._device_index = device_index
        self._interval_seconds = interval_seconds
        self._stop = Event()
        self._thread: Thread | None = None
        self._peak_mb: float | None = None
        self._available = self._sample_once() is not None

    def _sample_once(self) -> float | None:
        try:
            completed = subprocess.run(
                [
                    "nvidia-smi",
                    f"--id={self._device_index}",
                    "--query-gpu=memory.used",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        try:
            return float(completed.stdout.strip().splitlines()[0])
        except (ValueError, IndexError):
            return None

    def sample_now(self) -> float | None:
        return self._sample_once() if self._available else None

    def _loop(self) -> None:
        while not self._stop.is_set():
            sample = self._sample_once()
            if sample is not None:
                self._peak_mb = sample if self._peak_mb is None else max(self._peak_mb, sample)
            self._stop.wait(self._interval_seconds)

    def start(self) -> None:
        if not self._available:
            return
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_and_get_peak_mb(self) -> float | None:
        if not self._available:
            return None
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        return self._peak_mb


def _write_synthetic_preflight_image(path: Path) -> None:
    """Write a small synthetic PNG -- shapes only, never a real drawing.

    Mirrors the companion image already proven to pass P2-T1 in
    ``sketch2life.benchmark.asr_round1_runner._write_p2t1_companion_image``.
    """

    width, height = 160, 160
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            in_interior = 30 < x < 130 and 30 < y < 130
            shade = 30 if in_interior and (x // 8) % 2 == 0 else 235
            rows.extend((shade, shade, shade))
    compressed = compress(bytes(rows), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return pack(">I", len(data)) + tag + data + pack(">I", crc32(tag + data) & 0xFFFFFFFF)

    ihdr = pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def _write_synthetic_preflight_audio(path: Path) -> None:
    """Write a one-second synthetic tone -- the same shape already proven to pass P2-T1's
    audio quality gate in ``tests/unit/test_media_validation.py``.
    """

    sample_rate = 16000
    seconds = 1.0
    amplitude = 0.3
    samples = [
        int(amplitude * 32767 * sin(2 * 3.14159265 * 220 * index / sample_rate))
        for index in range(int(sample_rate * seconds))
    ]
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(pack("<h", sample) for sample in samples))


def _require_safe_cleanup_target(fixtures_dir: Path) -> None:
    """Reject a ``fixtures_dir`` that ``shutil.rmtree`` must not be pointed at.

    Requires a relative path whose resolved location sits strictly inside the resolved
    current working directory -- never equal to it and never one of its ancestors -- so a
    misconfigured caller cannot turn the mandatory post-run cleanup into an accidental
    wide deletion.
    """

    if fixtures_dir.is_absolute():
        raise UnsafeFixturesDirectoryError(
            "fixtures_dir must be a relative path so its later cleanup stays scoped under "
            "the current working directory"
        )
    cwd = Path.cwd().resolve()
    resolved = fixtures_dir.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise UnsafeFixturesDirectoryError(
            "fixtures_dir must resolve to a location strictly nested under the current "
            "working directory, never the working directory itself or an ancestor of it"
        )


def _require_fixture_path_within_scratch(fixtures_dir: Path, path: Path, *, label: str) -> None:
    """Reject a ``build_fixtures`` path that is not a real file strictly inside ``fixtures_dir``.

    Checks only path metadata -- resolution and ``is_file()`` -- never opens or reads the
    file's contents, so a path pointing outside the scratch directory, a directory, or a
    non-existent path is never touched beyond a stat call.
    """

    if path.is_absolute():
        raise UnsafeFixturePathError(
            f"the {label} fixture path must be relative so it can be used as a request "
            "artifact_ref"
        )
    fixtures_root = fixtures_dir.resolve()
    resolved = path.resolve()
    if resolved == fixtures_root or fixtures_root not in resolved.parents:
        raise UnsafeFixturePathError(
            f"the {label} fixture path must resolve strictly inside fixtures_dir, never "
            "fixtures_dir itself or a location outside it"
        )
    if not resolved.is_file():
        raise UnsafeFixturePathError(
            f"the {label} fixture path must be an existing regular file, never a directory "
            "or a path that does not exist"
        )


def _default_fixture_builder(fixtures_dir: Path) -> tuple[Path, Path]:
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    image_path = fixtures_dir / "preflight.png"
    audio_path = fixtures_dir / "preflight.wav"
    _write_synthetic_preflight_image(image_path)
    _write_synthetic_preflight_audio(audio_path)
    return image_path, audio_path


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _real_p2t1_pass_media_validation(
    image_path: Path, audio_path: Path
) -> VisionMediaValidationProvenanceV1:
    """Run the real P2-T1 validator -- never a fabricated ``PASS``."""

    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref="vision-b2-preflight-synthetic-image",
            audio_artifact_ref="vision-b2-preflight-synthetic-audio",
        )
    )
    if result.decision is not MediaDecision.PASS:
        raise NoRealP2T1PassAvailableError(
            "the B2 preflight synthetic fixtures did not earn a real P2-T1 PASS; "
            "refusing to fabricate one"
        )
    artifact_payload = result.model_dump_json().encode("utf-8")
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref="vision-b2-preflight-p2t1-validation",
        validation_artifact_sha256=sha256(artifact_payload).hexdigest(),
        decision="PASS",
        validator_policy_version=result.validator_policy_version,
    )


def _to_preflight_result(
    result: VisionUnderstandingResultV2,
    *,
    wall_latency_ms: float,
    baseline_vram_mb: float | None,
    peak_vram_mb: float | None,
    post_call_vram_mb: float | None,
    vram_not_measured_reason: str | None,
) -> VisionB2PreflightResult:
    model_provenance: VisionModelProvenanceV1 | None
    if isinstance(result, VisionUnderstandingSuccessV2):
        error_code = None
        error_detail = None
        model_provenance = result.model_provenance
    else:
        assert isinstance(result, VisionUnderstandingFailureV2)
        error_code = result.error_code.value
        error_detail = result.error_detail.value
        model_provenance = result.model_provenance

    return VisionB2PreflightResult(
        profile_id=result.profile_id.value,
        profile_catalog_hash=result.profile_catalog_hash,
        status=result.status,
        attempt_number=result.attempt_number,
        repair_attempted=result.repair_attempted,
        policy_execution_state=result.policy_execution_state,
        error_code=error_code,
        error_detail=error_detail,
        model_identifier=model_provenance.model_identifier if model_provenance else None,
        model_revision=model_provenance.model_revision if model_provenance else None,
        wall_latency_ms=wall_latency_ms,
        baseline_vram_mb=baseline_vram_mb,
        peak_vram_mb=peak_vram_mb,
        post_call_vram_mb=post_call_vram_mb,
        vram_not_measured_reason=vram_not_measured_reason,
    )


def run_b2_preflight(
    adapter: VisionUnderstandingPortV2,
    *,
    profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    correlation_id: str = "vision-b2-preflight",
    sample_vram: bool = True,
    fixtures_dir: Path = _DEFAULT_FIXTURES_DIR,
    build_fixtures: Callable[[Path], tuple[Path, Path]] = _default_fixture_builder,
) -> VisionB2PreflightResult:
    """Execute exactly one B2 preflight call against ``adapter``.

    ``adapter`` is the real ``QwenVisionAdapter`` for an actual Lightning L4 run, or an
    injected fake for unit tests -- the same test/real seam already used by
    ``Round1RunnerConfig.adapter_factory`` on the ASR side. ``build_fixtures`` lets a test
    substitute its own tiny synthetic image/audio writers; the real default writes fixtures
    proven to pass P2-T1 in this repository's own tests, into the already-ignored
    ``data/runtime/`` scratch location, and deletes them again once the call returns.

    Raises ``UnsafeFixturesDirectoryError`` before writing anything if ``fixtures_dir`` is
    not a safe cleanup target, and ``UnsafeFixturePathError`` -- before P2-T1 validation and
    before the adapter is ever called -- if ``build_fixtures`` returns a path that is not a
    real file strictly inside ``fixtures_dir`` (see each error's docstring).

    The scratch directory is deleted in a ``finally`` block covering ``build_fixtures``
    itself, so a builder that writes one fixture and then raises still leaves nothing behind.
    A background VRAM sampler, once started, is always stopped and joined -- even when the
    adapter call raises -- so no polling thread outlives this function.
    """

    _require_safe_cleanup_target(fixtures_dir)

    sampler: _VramSampler | None = None
    try:
        image_path, audio_path = build_fixtures(fixtures_dir)
        _require_fixture_path_within_scratch(fixtures_dir, image_path, label="image")
        _require_fixture_path_within_scratch(fixtures_dir, audio_path, label="audio")

        media_validation = _real_p2t1_pass_media_validation(image_path, audio_path)

        request = VisionUnderstandingRequestV2(
            correlation_id=correlation_id,
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=image_path.as_posix(), sha256=_sha256_of(image_path)
            ),
            media_validation=media_validation,
            requested_profile_id=profile_id,
        )

        sampler = _VramSampler() if sample_vram else None
        baseline_vram_mb = sampler.sample_now() if sampler is not None else None
        if sampler is not None:
            sampler.start()

        peak_vram_mb: float | None = None
        try:
            started = time.perf_counter()
            result = adapter.understand(request)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        finally:
            if sampler is not None:
                peak_vram_mb = sampler.stop_and_get_peak_mb()

        post_call_vram_mb = sampler.sample_now() if sampler is not None else None
    finally:
        shutil.rmtree(fixtures_dir, ignore_errors=True)

    if sample_vram:
        vram_not_measured_reason = (
            None if peak_vram_mb is not None else "nvidia-smi was unavailable or returned no sample"
        )
    else:
        vram_not_measured_reason = "VRAM sampling was disabled for this call"

    return _to_preflight_result(
        result,
        wall_latency_ms=elapsed_ms,
        baseline_vram_mb=baseline_vram_mb,
        peak_vram_mb=peak_vram_mb,
        post_call_vram_mb=post_call_vram_mb,
        vram_not_measured_reason=vram_not_measured_reason,
    )


__all__ = [
    "NoRealP2T1PassAvailableError",
    "UnsafeFixturePathError",
    "UnsafeFixturesDirectoryError",
    "VisionB2PreflightResult",
    "run_b2_preflight",
]
