"""Internal (non-CLI) P2-T3 Phase B B4 Direction A prompt-v3 mapping-validation runner.

This is the dedicated runner named by
``evidence/notes/P2_T3_PHASE_B_B4_DIRECTION_A_V3_MAPPING_VALIDATION_PLAN.md`` phase 6 and by
``evidence/notes/P2_T3_PHASE_B_B4_DIRECTION_A_V3_REAUTHORIZATION.md``. It produces
``V3_PASS_1``/``V3_REPEAT_1`` mapping-validation reports over the eight owner-approved
``vision-v3-map-manifest-v1`` synthetic fixtures, using exactly the reviewed
``vision-v2-structured-output-prompt-v3`` protocol.

**Never reuses ``run_c1_pass``/``evaluate_c1_readiness`` and never labels a result as C1.** C1
(`vision_c1_prompt_mapping_study.py`) deliberately rejects the v3 prompt identity with
``C1PromptOutOfExperimentScopeError`` at both its entry points, precisely so a v3 run can never
mint a C1-labelled ``MAPPING_READY`` verdict over B3's fixtures. This module is v3's own,
separate experiment: its own run labels (``V3_PASS_1``/``V3_REPEAT_1``), its own readiness gate
(:func:`evaluate_v3_readiness`), and its own fixture set (the v3 mapping-validation manifest, not
B3's or B4's).

It does reuse lower-level safe primitives that carry no C1/B3-specific labeling semantics:
``run_b3_mapping_study`` (the shared one-call-per-fixture-no-retry loop, VRAM/latency
measurement, real per-fixture P2-T1 gate, and scratch cleanup), ``B3RawOutputCollector`` (the
``CLASSIFY_ONLY``-default raw-output handling), and the already-reviewed v3 prompt identity
constant ``C1_PROMPT_V3`` (registered in the C1 module for exactly this purpose: "Its live
execution awaits its own separately approved runner... none of which exists in this module").
**``run_b3_mapping_study`` itself is never modified** -- its own report shape (and the
``b3-fixture-NN`` label it stamps on each internal run) stays exactly as approved. This module's
own :class:`V3PassReport`/:class:`V3FixtureRunResult` never expose that reused primitive's report
directly: every per-fixture result is re-bound, by verified position, to its approved
``v3-map-fixture-NN`` identity and manifest-verified SHA-256 before it ever leaves this module.

**Fixture handling and P2-T1 ordering.** The eight v3 mapping fixtures are pre-authored,
persistent, gitignored PNGs under
``features/FEAT-003-multimodal-understanding/fixtures/vision-v3-map/images/``, described by the
tracked ``manifest-v1.json``. :func:`load_and_verify_v3_fixtures` re-verifies the manifest's
identity, prompt binding, fixture count/order, and each image's on-disk SHA-256/dimensions before
any adapter/provider action -- closed on any mismatch. :func:`run_v3_pass` then copies the
verified images into a scratch directory and runs a **real** P2-T1 media-quality validation
against all eight copied fixtures -- closed with :class:`NoRealV3P2T1PassAvailableError` on any
failure -- entirely **before** ``adapter_factory`` is ever called (not merely before each
fixture's own ``adapter.understand()`` call, which is as far as the reused
``run_b3_mapping_study`` loop checks on its own). The persistent images directory itself is never
written to or deleted by this module.

**Timing is call-boundary only.** ``V3PassReport.started_at``/``completed_at`` are timestamps this
runner captures around its own adapter-call work, using an injectable clock for deterministic
tests. They are **not** the Lightning Studio session's billed start/stop time, and this module
makes no claim to measure the reauthorized 20-minute Studio budget -- recording actual session
start/stop remains the operator's own responsibility, per the reauthorization note. The
comparability rule is exactly: ``V3_REPEAT_1.started_at - V3_PASS_1.completed_at <= 15 minutes``,
with no session reset and no configuration or fixture-manifest-identity drift between the two
passes -- see :func:`evaluate_v3_readiness`.

This module never runs a GPU/model/provider call by itself, installs a dependency, touches
``.vision.env``, changes a V1/V2 public contract, changes decoding/timeout/retry/repair/parsing,
or reads/writes B3's or B4's fixtures/ground truth/matching rule.
"""

from __future__ import annotations

import json
import math
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from re import compile as re_compile
from struct import pack, unpack
from typing import Any, Literal
from wave import open as wave_open

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.benchmark.vision_b3_mapping_study import (
    B3FixtureRunResult,
    B3MappingStudyReport,
    B3RawOutputCollector,
    run_b3_mapping_study,
)
from sketch2life.benchmark.vision_c1_prompt_mapping_study import (
    C1_PROMPT_V3,
    c1_prompt_schema_target,
)
from sketch2life.benchmark.vision_v3_mapping_fixtures import TAXONOMY
from sketch2life.contracts.schemas.vision import VisionErrorCode
from sketch2life.contracts.schemas.vision_v2 import (
    VisionNonPolicyErrorDetailV2,
    VisionProfileIdV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.ai.qwen_vision import (
    QwenGenerationRunner,
    QwenVisionAdapter,
    RawOutputHook,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

V3RunLabel = Literal["V3_PASS_1", "V3_REPEAT_1"]

V3AdapterFactory = Callable[[str, RawOutputHook], VisionUnderstandingPortV2]
"""Builds the adapter for one v3 pass from the verified v3 prompt text and a raw-output hook.

``run_v3_pass`` is the only caller of a ``V3AdapterFactory`` and always supplies exactly the
verified ``vision-v2-structured-output-prompt-v3`` text (see :func:`_verified_v3_prompt_text`)
and ``collector.hook`` -- there is no parameter through which a caller can substitute an
already-built adapter, a v1/v2 prompt, or an empty default. It is also never called until every
copied fixture has already earned a real P2-T1 pass (see :func:`_require_real_p2t1_pass_for_all`).
"""

_V3_FIXTURE_COUNT = 8
_V3_EXPECTED_DIMENSION = 192
_V3_MANIFEST_VERSION = "vision-v3-map-manifest-v1"
_V3_CONTRACT_NAME = "VisionV3MapFixtureManifestV1"
_V3_APPROVED_STATUS = "OWNER_IMAGE_REVIEW_APPROVED"
_V3_PURPOSE = "MAPPING_VALIDATION_ONLY"

_DEFAULT_V3_MANIFEST_PATH = Path(
    "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-map/manifest-v1.json"
)
_DEFAULT_V3_IMAGES_ROOT = Path("features/FEAT-003-multimodal-understanding/fixtures/vision-v3-map")

_DEFAULT_V3_FIXTURES_DIR: dict[V3RunLabel, Path] = {
    "V3_PASS_1": Path("data/runtime/vision-v3-pass-1"),
    "V3_REPEAT_1": Path("data/runtime/vision-v3-repeat-1"),
}

_SHA256_PATTERN = re_compile(r"^[a-f0-9]{64}$")

_MIN_MAPPING_VALID_COUNT = 7
_SYSTEMIC_TRUNCATION_THRESHOLD = 2
_EXPECTED_ATTEMPTED_RUNS = 8
_COMPARABILITY_WINDOW = timedelta(minutes=15)

_RUNTIME_OR_DEVICE_ERROR_CODES = frozenset(
    {
        VisionErrorCode.VISION_MODEL_UNAVAILABLE.value,
        VisionErrorCode.VISION_TIMEOUT.value,
        VisionErrorCode.VISION_PROVIDER_FAILURE.value,
    }
)
_INPUT_INTEGRITY_ERROR_DETAILS = frozenset(
    {
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_UNREADABLE.value,
        VisionNonPolicyErrorDetailV2.SOURCE_IMAGE_HASH_MISMATCH.value,
    }
)


class V3ManifestIntegrityError(ValueError):
    """The v3 mapping-fixture manifest or one of its declared fixtures fails a closed check.

    Raised by :func:`load_and_verify_v3_fixtures`, before any prompt dispatch, adapter
    construction, scratch creation, or provider action, for: a missing/unreadable/malformed
    manifest, a manifest identity field (contract name, version, purpose, status,
    ``has_ground_truth``, ``data_policy``) that does not match the approved v3 manifest exactly,
    a ``prompt_protocol`` block that does not match the reviewed v3 identity
    (:data:`~sketch2life.benchmark.vision_c1_prompt_mapping_study.C1_PROMPT_V3`), a fixture
    count/order that does not match the approved eight-fixture taxonomy, a missing image file, or
    an on-disk image whose SHA-256/dimensions do not match the manifest's declared values. Never
    carries file content -- only closed identifiers, hashes, and dimensions already safe to log.
    """


class V3PromptBindingError(Exception):
    """The frozen v3 prompt identity failed self-verification before any fixture/provider action.

    This should never fire against the unmodified
    :data:`~sketch2life.benchmark.vision_c1_prompt_mapping_study.C1_PROMPT_V3` constant; it exists
    as a fail-closed guard, mirroring
    :class:`~sketch2life.benchmark.vision_c1_prompt_mapping_study.C1PromptBindingError`, in case
    that shared constant is ever corrupted at runtime. No caller of this module can select a
    different prompt: :func:`run_v3_pass` always uses exactly the verified v3 text.
    """


class V3UnsafeScratchDirectoryError(ValueError):
    """``fixtures_dir`` is not a safe ``shutil.rmtree`` cleanup target.

    Mirrors ``vision_b3_mapping_study.UnsafeScratchDirectoryError``. Checked by
    :func:`run_v3_pass` itself, before this module creates or copies anything into the scratch
    directory, because the real per-fixture P2-T1 pre-check (and the copy it requires) now runs
    before ``run_b3_mapping_study`` would otherwise perform its own equivalent path-safety check.
    """


class NoRealV3P2T1PassAvailableError(RuntimeError):
    """A copied v3 fixture did not earn a real P2-T1 PASS before any adapter/provider action.

    Raised by :func:`run_v3_pass` -- for any of the eight copied v3 fixtures that fails a fresh,
    real (never fabricated) P2-T1 media-quality validation -- strictly before ``adapter_factory``
    is ever called, so a failure here guarantees zero adapter/provider calls occurred. The scratch
    fixtures directory is removed before this error propagates.
    """


@dataclass(frozen=True, slots=True)
class V3VerifiedFixture:
    """One v3 mapping fixture whose manifest-declared identity matched its on-disk image."""

    fixture_id: str
    image_path: Path
    sha256: str


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    """Reads width/height from a PNG's leading IHDR chunk (always the first chunk, per spec)."""

    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise V3ManifestIntegrityError(
            f"{path.name} is not a valid PNG with a leading IHDR chunk"
        )
    width, height = unpack(">II", data[16:24])
    return int(width), int(height)


def _require_relative_within(root: Path, path: Path, *, label: str) -> None:
    root_resolved = root.resolve()
    resolved = path.resolve()
    if resolved == root_resolved or root_resolved not in resolved.parents:
        raise V3ManifestIntegrityError(f"the {label} path must resolve strictly inside {root}")


def load_and_verify_v3_fixtures(
    *,
    manifest_path: Path = _DEFAULT_V3_MANIFEST_PATH,
    images_root: Path = _DEFAULT_V3_IMAGES_ROOT,
) -> tuple[V3VerifiedFixture, ...]:
    """Load ``manifest_path`` and verify it, and every fixture it declares, against closed rules.

    Fails closed with :class:`V3ManifestIntegrityError` -- before any prompt dispatch, adapter
    construction, scratch creation, or provider action -- on any manifest-identity, prompt-
    identity, fixture-count/order, missing-file, or on-disk hash/dimension mismatch. A real,
    fresh P2-T1 pass is **not** checked here (that happens later, over the scratch-copied images,
    in :func:`_require_real_p2t1_pass_for_all`); this function only re-verifies what a static
    manifest and its referenced files can prove without a media-validation call. The returned
    tuple's order always matches the approved taxonomy order (``v3-map-fixture-01..08``).
    """

    if not manifest_path.is_file():
        raise V3ManifestIntegrityError(f"manifest not found at {manifest_path}")
    try:
        manifest: Mapping[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise V3ManifestIntegrityError("manifest is not valid JSON") from exc

    if manifest.get("contract_name") != _V3_CONTRACT_NAME:
        raise V3ManifestIntegrityError("unexpected manifest contract_name")
    if manifest.get("manifest_version") != _V3_MANIFEST_VERSION:
        raise V3ManifestIntegrityError("unexpected manifest_version")
    if manifest.get("status") != _V3_APPROVED_STATUS:
        raise V3ManifestIntegrityError("manifest is not in the owner-approved review status")
    if manifest.get("purpose") != _V3_PURPOSE:
        raise V3ManifestIntegrityError("unexpected manifest purpose")
    if manifest.get("has_ground_truth") is not False:
        raise V3ManifestIntegrityError("v3 mapping manifest must declare has_ground_truth=false")
    if manifest.get("data_policy") != "synthetic-only":
        raise V3ManifestIntegrityError("unexpected manifest data_policy")

    prompt_protocol = manifest.get("prompt_protocol")
    if not isinstance(prompt_protocol, Mapping):
        raise V3ManifestIntegrityError("manifest is missing a prompt_protocol block")
    if (
        prompt_protocol.get("protocol_id") != C1_PROMPT_V3.protocol_id
        or prompt_protocol.get("sha256") != C1_PROMPT_V3.prompt_sha256
        or prompt_protocol.get("schema_target") != c1_prompt_schema_target()
    ):
        raise V3ManifestIntegrityError(
            "manifest prompt_protocol does not match the approved v3 identity"
        )

    authoring = manifest.get("local_authoring_validation")
    if not isinstance(authoring, Mapping):
        raise V3ManifestIntegrityError("manifest is missing local_authoring_validation")
    if authoring.get("model_or_gpu_called") is not False:
        raise V3ManifestIntegrityError(
            "manifest must declare no model/GPU action occurred during authoring"
        )
    if authoring.get("p2t1_result") != "PASS_FOR_ALL_8_FIXTURES":
        raise V3ManifestIntegrityError(
            "manifest does not declare a full authoring-time P2-T1 pass"
        )

    disjointness = manifest.get("disjointness")
    if not isinstance(disjointness, Mapping) or (
        disjointness.get("b3_regenerated_hash_comparison_status") != "VERIFIED_NO_OVERLAP"
        or disjointness.get("b4_manifest_hash_comparison_status") != "VERIFIED_NO_OVERLAP"
    ):
        raise V3ManifestIntegrityError("manifest does not confirm B3/B4 hash disjointness")

    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != _V3_FIXTURE_COUNT:
        raise V3ManifestIntegrityError(
            f"manifest must declare exactly {_V3_FIXTURE_COUNT} fixtures"
        )

    expected_ids = tuple(spec.fixture_id for spec in TAXONOMY)
    expected_tokens = {spec.fixture_id: spec.taxonomy_token for spec in TAXONOMY}
    declared_ids = tuple(entry.get("fixture_id") for entry in fixtures)
    if declared_ids != expected_ids:
        raise V3ManifestIntegrityError(
            "manifest fixture order/IDs do not match the approved taxonomy"
        )

    verified: list[V3VerifiedFixture] = []
    seen_hashes: set[str] = set()
    for entry, fixture_id in zip(fixtures, expected_ids, strict=True):
        if not isinstance(entry, Mapping):
            raise V3ManifestIntegrityError(f"{fixture_id}: fixture entry is not an object")

        declared_hash = entry.get("image_sha256")
        declared_ref = entry.get("image_ref")
        dimensions = entry.get("dimensions")
        declared_width = dimensions.get("width") if isinstance(dimensions, Mapping) else None
        declared_height = dimensions.get("height") if isinstance(dimensions, Mapping) else None
        declared_token = entry.get("taxonomy_token")
        declared_p2t1 = entry.get("p2t1_pass")

        if (
            not isinstance(declared_hash, str)
            or _SHA256_PATTERN.fullmatch(declared_hash) is None
            or declared_hash in seen_hashes
        ):
            raise V3ManifestIntegrityError(
                f"{fixture_id}: invalid or duplicate declared image_sha256"
            )
        seen_hashes.add(declared_hash)

        if declared_ref != f"images/{fixture_id}.png":
            raise V3ManifestIntegrityError(f"{fixture_id}: unexpected image_ref")
        if declared_width != _V3_EXPECTED_DIMENSION or declared_height != _V3_EXPECTED_DIMENSION:
            raise V3ManifestIntegrityError(f"{fixture_id}: unexpected declared dimensions")
        if declared_token != expected_tokens[fixture_id]:
            raise V3ManifestIntegrityError(f"{fixture_id}: unexpected taxonomy_token")
        if declared_p2t1 is not True:
            raise V3ManifestIntegrityError(f"{fixture_id}: manifest does not declare a P2-T1 pass")

        image_path = images_root / declared_ref
        _require_relative_within(images_root, image_path, label="image")
        if not image_path.is_file():
            raise V3ManifestIntegrityError(f"{fixture_id}: image file not found on disk")

        actual_hash = _sha256_of(image_path)
        if actual_hash != declared_hash:
            raise V3ManifestIntegrityError(
                f"{fixture_id}: on-disk image hash does not match the manifest"
            )

        actual_width, actual_height = _read_png_dimensions(image_path)
        if actual_width != _V3_EXPECTED_DIMENSION or actual_height != _V3_EXPECTED_DIMENSION:
            raise V3ManifestIntegrityError(
                f"{fixture_id}: on-disk image dimensions do not match the manifest"
            )

        verified.append(
            V3VerifiedFixture(fixture_id=fixture_id, image_path=image_path, sha256=actual_hash)
        )

    return tuple(verified)


def _verified_v3_prompt_text() -> str:
    """Resolve the frozen v3 prompt text, self-checked against its own declared identity.

    Fails closed with :class:`V3PromptBindingError` before any fixture/adapter/provider action if
    :data:`C1_PROMPT_V3`'s declared identity or text/hash pairing has been corrupted. Under normal
    operation this always returns exactly
    :func:`~sketch2life.benchmark.vision_c1_prompt_mapping_study.c1_prompt_text_v3`'s text -- there
    is no parameter anywhere in this module through which a caller can substitute a different
    prompt.
    """

    if C1_PROMPT_V3.protocol_id != "vision-v2-structured-output-prompt-v3":
        raise V3PromptBindingError(
            f"unexpected v3 protocol_id: {C1_PROMPT_V3.protocol_id!r}"
        )
    text = C1_PROMPT_V3.prompt_text_provider()
    if sha256(text.encode("utf-8")).hexdigest() != C1_PROMPT_V3.prompt_sha256:
        raise V3PromptBindingError("v3 prompt text/hash self-check failed")
    return text


def qwen_v3_adapter_factory(
    runtime_config: QwenVisionRuntimeConfig,
    content_policy: ObservableContentPolicyV1,
    *,
    generation_runner: QwenGenerationRunner | None = None,
) -> V3AdapterFactory:
    """The real production :data:`V3AdapterFactory` for a Lightning v3 pass.

    Returns a closure matching ``V3AdapterFactory``: called by ``run_v3_pass`` with the verified
    v3 prompt text and ``collector.hook``, it constructs a fresh ``QwenVisionAdapter`` with
    ``prompt``/``on_raw_output`` set to exactly those two values. The adapter's own default
    (empty) ``_default_prompt_builder`` is never reached through this factory.
    ``generation_runner`` exists only so tests can inject a fake generation seam without a GPU; a
    real Lightning run omits it and gets the adapter's own default killable-subprocess runner.
    """

    def factory(prompt: str, on_raw_output: RawOutputHook) -> VisionUnderstandingPortV2:
        return QwenVisionAdapter(
            runtime_config,
            content_policy=content_policy,
            prompt=prompt,
            generation_runner=generation_runner,
            on_raw_output=on_raw_output,
        )

    return factory


def _write_v3_pass_companion_audio(path: Path) -> None:
    """Same deterministic tone shape already proven to pass P2-T1's audio quality gate.

    Duplicated from ``vision_v3_mapping_fixtures.py``/``vision_b3_mapping_study.py`` rather than
    imported, matching this project's own precedent of keeping each benchmark module
    self-contained (see ``_VramSampler`` in ``vision_b3_mapping_study.py``).
    """

    sample_rate = 16000
    seconds = 1.0
    amplitude = 0.3
    samples = [
        int(amplitude * 32767 * math.sin(2 * math.pi * 220 * index / sample_rate))
        for index in range(int(sample_rate * seconds))
    ]
    with wave_open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"".join(pack("<h", sample) for sample in samples))


def _require_safe_scratch_target(scratch_dir: Path) -> None:
    """Mirrors ``vision_b3_mapping_study._require_safe_cleanup_target`` (duplicated, not
    imported, matching this project's per-module self-containment precedent). Checked before this
    module creates or writes into ``scratch_dir`` itself.
    """

    if scratch_dir.is_absolute():
        raise V3UnsafeScratchDirectoryError(
            "scratch directory must be a relative path so its later cleanup stays scoped under "
            "the current working directory"
        )
    cwd = Path.cwd().resolve()
    resolved = scratch_dir.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise V3UnsafeScratchDirectoryError(
            "scratch directory must resolve to a location strictly nested under the current "
            "working directory, never the working directory itself or an ancestor of it"
        )


def _copy_v3_fixtures_into_scratch(
    verified_fixtures: tuple[V3VerifiedFixture, ...], fixtures_dir: Path
) -> tuple[tuple[Path, ...], Path]:
    """Copies each already-verified, persistent v3 image into ``fixtures_dir`` and writes an
    ephemeral companion audio file alongside them. The persistent images directory itself is
    never written to or deleted by this function.
    """

    fixtures_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[Path] = []
    for fixture in verified_fixtures:
        destination = fixtures_dir / fixture.image_path.name
        shutil.copy2(fixture.image_path, destination)
        image_paths.append(destination)
    audio_path = fixtures_dir / "vision-v3-pass-companion.wav"
    _write_v3_pass_companion_audio(audio_path)
    return tuple(image_paths), audio_path


def _real_p2t1_pass(fixture_id: str, image_path: Path, audio_path: Path) -> bool:
    """Real (never fabricated) P2-T1 pass check over one already-copied scratch image.

    Uses the same real validator ``vision_v3_mapping_fixtures.py`` and
    ``vision_b3_mapping_study.py`` already use, duplicated rather than imported, matching this
    project's per-module self-containment precedent.
    """

    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref=f"vision-v3-pass-{fixture_id}-synthetic-image",
            audio_artifact_ref="vision-v3-pass-synthetic-audio",
        )
    )
    return result.decision is MediaDecision.PASS


def _require_real_p2t1_pass_for_all(
    verified_fixtures: tuple[V3VerifiedFixture, ...],
    image_paths: tuple[Path, ...],
    audio_path: Path,
) -> None:
    """Fails closed with :class:`NoRealV3P2T1PassAvailableError` on the first copied fixture that
    does not earn a real P2-T1 PASS. Called by :func:`run_v3_pass` before ``adapter_factory``.
    """

    for fixture, image_path in zip(verified_fixtures, image_paths, strict=True):
        if not _real_p2t1_pass(fixture.fixture_id, image_path, audio_path):
            raise NoRealV3P2T1PassAvailableError(
                f"{fixture.fixture_id} did not earn a real P2-T1 PASS; refusing to proceed to "
                "any adapter/provider action"
            )


@dataclass(frozen=True, slots=True)
class V3FixtureRunResult:
    """One v3 fixture's typed outcome, safely re-bound to its approved v3 identity/hash.

    ``fixture_id`` is always one of the eight approved ``v3-map-fixture-01..08`` taxonomy IDs --
    never the reused ``run_b3_mapping_study`` primitive's internal ``b3-fixture-*`` label.
    ``fixture_sha256`` is the same manifest-verified on-disk hash
    :func:`load_and_verify_v3_fixtures` already established for this fixture. Every other field
    mirrors :class:`~sketch2life.benchmark.vision_b3_mapping_study.B3FixtureRunResult` exactly and
    carries the same safety guarantee: never a path, raw output, prompt body, prediction, or
    ground-truth text.
    """

    fixture_id: str
    fixture_sha256: str
    status: str
    error_code: str | None
    error_detail: str | None
    attempt_number: int
    repair_attempted: bool
    wall_latency_ms: float
    peak_vram_mb: float | None
    vram_not_measured_reason: str | None
    fenced: bool | None
    truncated: bool | None
    extra_key: bool | None
    invalid_enum: bool | None


@dataclass(frozen=True, slots=True)
class V3MappingSummary:
    """Aggregate-only counts from the reused B3 mapping loop; never carries a per-fixture ID."""

    profile_id: str
    profile_catalog_hash: str
    raw_output_mode: str
    attempted_runs: int
    schema_valid_count: int
    typed_failure_counts: Mapping[str, int]
    lossless_unwrap_recovered_count: int
    fenced_count: int
    truncated_count: int
    extra_key_count: int
    invalid_enum_count: int
    known_policy_trigger_rate: Literal["NOT_APPLICABLE"] = "NOT_APPLICABLE"


def _build_v3_runs(
    b3_runs: tuple[B3FixtureRunResult, ...], verified_fixtures: tuple[V3VerifiedFixture, ...]
) -> tuple[V3FixtureRunResult, ...]:
    """Re-binds each reused-primitive run result to its true v3 fixture identity, by position.

    Positional binding is safe here because ``run_v3_pass`` always feeds
    ``run_b3_mapping_study`` the same ``verified_fixtures``-ordered image list it validated, and
    that function processes/returns runs in the exact order its image list was given -- the same
    invariant C1's own reuse of this function already relies on for its (unrenamed) ``b3-fixture``
    labels.
    """

    return tuple(
        V3FixtureRunResult(
            fixture_id=fixture.fixture_id,
            fixture_sha256=fixture.sha256,
            status=run.status,
            error_code=run.error_code,
            error_detail=run.error_detail,
            attempt_number=run.attempt_number,
            repair_attempted=run.repair_attempted,
            wall_latency_ms=run.wall_latency_ms,
            peak_vram_mb=run.peak_vram_mb,
            vram_not_measured_reason=run.vram_not_measured_reason,
            fenced=run.fenced,
            truncated=run.truncated,
            extra_key=run.extra_key,
            invalid_enum=run.invalid_enum,
        )
        for run, fixture in zip(b3_runs, verified_fixtures, strict=True)
    )


def _to_mapping_summary(mapping: B3MappingStudyReport) -> V3MappingSummary:
    return V3MappingSummary(
        profile_id=mapping.profile_id,
        profile_catalog_hash=mapping.profile_catalog_hash,
        raw_output_mode=mapping.raw_output_mode,
        attempted_runs=mapping.attempted_runs,
        schema_valid_count=mapping.schema_valid_count,
        typed_failure_counts=dict(mapping.typed_failure_counts),
        lossless_unwrap_recovered_count=mapping.lossless_unwrap_recovered_count,
        fenced_count=mapping.fenced_count,
        truncated_count=mapping.truncated_count,
        extra_key_count=mapping.extra_key_count,
        invalid_enum_count=mapping.invalid_enum_count,
        known_policy_trigger_rate=mapping.known_policy_trigger_rate,
    )


@dataclass(frozen=True, slots=True)
class V3PassReport:
    """One v3 pass's safe report: prompt/manifest identity, aggregate counts, and per-fixture
    results re-bound to the approved ``v3-map-fixture-01..08`` identities. Never carries the
    prompt body, raw model output, a local path, or the reused primitive's internal
    ``b3-fixture-*`` label anywhere -- including in a full serialization of this dataclass.

    ``started_at``/``completed_at`` bound this call's own adapter-call work using whatever clock
    ``run_v3_pass`` was given; they are not a Lightning Studio session's billed start/stop time.
    """

    run_label: V3RunLabel
    prompt_protocol_id: str
    prompt_sha256: str
    fixture_manifest_version: str
    started_at: datetime
    completed_at: datetime
    mapping: V3MappingSummary
    runs: tuple[V3FixtureRunResult, ...]


def run_v3_pass(
    adapter_factory: V3AdapterFactory,
    collector: B3RawOutputCollector,
    *,
    run_label: V3RunLabel,
    profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    sample_vram: bool = True,
    fixtures_dir: Path | None = None,
    manifest_path: Path = _DEFAULT_V3_MANIFEST_PATH,
    images_root: Path = _DEFAULT_V3_IMAGES_ROOT,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> V3PassReport:
    """Execute one v3 mapping-validation pass: the eight approved v3 fixtures, one call each.

    Order of operations, all before any provider action: (1) :func:`load_and_verify_v3_fixtures`
    re-verifies the manifest and every fixture's on-disk hash/dimensions, failing closed with
    :class:`V3ManifestIntegrityError` on any mismatch; (2) :func:`_verified_v3_prompt_text`
    self-checks the frozen v3 prompt identity, failing closed with :class:`V3PromptBindingError`
    on any corruption; (3) the eight verified images are copied into a scratch directory and
    :func:`_require_real_p2t1_pass_for_all` runs a real P2-T1 validation against all eight copies,
    failing closed with :class:`NoRealV3P2T1PassAvailableError` on any failure. Only once all
    three pass is ``adapter_factory`` called, exactly once, with the verified v3 text and
    ``collector.hook``. The actual one-call-per-fixture-no-retry loop and VRAM/latency measurement
    are then delegated entirely to ``run_b3_mapping_study`` (unmodified), handing it the
    already-copied, already-validated fixture paths directly rather than letting it build its own.
    The returned report re-binds every per-fixture result to its true ``v3-map-fixture-NN``
    identity before returning.

    **Cleanup boundary.** A single ``try``/``except`` covers everything that can leave content in
    the scratch directory: the fixture-image/audio copy itself, the real P2-T1 pre-check, the
    ``adapter_factory`` call, and the mapping loop. Any exception raised anywhere in that span --
    including ``shutil.copy2`` failing mid-copy (e.g. after some but not all of the eight images
    were written), or ``adapter_factory`` raising before ``run_b3_mapping_study`` is ever reached
    -- removes the scratch ``fixtures_dir`` and calls ``collector.cleanup()`` before the
    *original* exception propagates unchanged -- never swallowed, wrapped, or replaced. Both
    calls are idempotent (``shutil.rmtree(..., ignore_errors=True)`` and
    ``B3RawOutputCollector.cleanup()`` are safe to call again on an already-clean target), so this
    never double-cleans up incorrectly even when ``run_b3_mapping_study``'s own ``finally``
    already ran first for a failure inside its loop. The persistent, manifest-declared images
    directory (``images_root``) is never a cleanup target of this boundary or of any path in this
    module -- only ``fixtures_dir``, the scratch copy destination, is ever removed.
    """

    verified_fixtures = load_and_verify_v3_fixtures(
        manifest_path=manifest_path, images_root=images_root
    )
    prompt_text = _verified_v3_prompt_text()

    resolved_fixtures_dir = fixtures_dir or _DEFAULT_V3_FIXTURES_DIR[run_label]
    _require_safe_scratch_target(resolved_fixtures_dir)

    try:
        image_paths, audio_path = _copy_v3_fixtures_into_scratch(
            verified_fixtures, resolved_fixtures_dir
        )
        _require_real_p2t1_pass_for_all(verified_fixtures, image_paths, audio_path)

        started_at = clock()
        adapter = adapter_factory(prompt_text, collector.hook)
        mapping = run_b3_mapping_study(
            adapter,
            collector,
            profile_id=profile_id,
            correlation_id_prefix=f"vision-{run_label.lower().replace('_', '-')}",
            sample_vram=sample_vram,
            fixtures_dir=resolved_fixtures_dir,
            build_fixtures=lambda _dir: (image_paths, audio_path),
        )
        completed_at = clock()
    except Exception:
        shutil.rmtree(resolved_fixtures_dir, ignore_errors=True)
        collector.cleanup()
        raise

    return V3PassReport(
        run_label=run_label,
        prompt_protocol_id=C1_PROMPT_V3.protocol_id,
        prompt_sha256=C1_PROMPT_V3.prompt_sha256,
        fixture_manifest_version=_V3_MANIFEST_VERSION,
        started_at=started_at,
        completed_at=completed_at,
        mapping=_to_mapping_summary(mapping),
        runs=_build_v3_runs(mapping.runs, verified_fixtures),
    )


class V3BlockingReason(StrEnum):
    """Closed set of reasons :func:`evaluate_v3_readiness` may cite for a non-ready verdict."""

    MAPPING_VALID_BELOW_THRESHOLD = "MAPPING_VALID_BELOW_THRESHOLD"
    SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS = (
        "SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS"
    )
    CONFIG_DRIFT = "CONFIG_DRIFT"
    FIXTURE_MANIFEST_MISMATCH = "FIXTURE_MANIFEST_MISMATCH"
    INPUT_INTEGRITY_FAILURE = "INPUT_INTEGRITY_FAILURE"
    RUNTIME_OR_DEVICE_FAILURE = "RUNTIME_OR_DEVICE_FAILURE"
    INCOMPLETE_RUN_SET = "INCOMPLETE_RUN_SET"
    REPEAT_WINDOW_EXCEEDED = "REPEAT_WINDOW_EXCEEDED"
    SESSION_RESET_DECLARED = "SESSION_RESET_DECLARED"


@dataclass(frozen=True, slots=True)
class V3PassEvaluation:
    """Derived, safe-only figures for one pass; never carries raw text or a path."""

    run_label: V3RunLabel
    attempted_runs: int
    run_record_count: int
    is_complete: bool
    mapping_valid_count: int
    truncated_count: int
    mapping_valid_ok: bool
    systemic_truncation: bool


@dataclass(frozen=True, slots=True)
class V3ReadinessVerdict:
    """The v3 mapping-readiness gate applied to two independent passes.

    ``overall`` is ``"NON_COMPARABLE"`` whenever the pair cannot be evaluated as a pair at all --
    configuration drift between the two passes, a fixture-manifest-version mismatch (either
    report not carrying exactly ``vision-v3-map-manifest-v1``, or the two reports disagreeing), a
    caller-declared Studio session reset, or a repeat-start gap
    (``V3_REPEAT_1.started_at - V3_PASS_1.completed_at``) exceeding 15 minutes -- distinct from
    ``"MAPPING_NOT_READY"``, which applies only to a genuinely comparable pair that still fails
    the numeric/integrity/truncation gate. ``pass_1``/``repeat_1`` are never pooled into a
    combined denominator.
    """

    prompt_protocol_id: str
    prompt_sha256: str
    pass_1: V3PassEvaluation
    repeat_1: V3PassEvaluation
    repeat_gap: timedelta
    same_lightning_session: bool
    overall: Literal["MAPPING_READY", "MAPPING_NOT_READY", "NON_COMPARABLE"]
    blocking_reasons: tuple[V3BlockingReason, ...]


def _mapping_valid_count(runs: tuple[V3FixtureRunResult, ...]) -> int:
    """``SUCCEEDED`` or ``PROHIBITED_CLAIM_DETECTED`` both count as mapping-valid.

    Both outcomes prove the model's raw output mapped onto the strict V2 JSON contract; a policy
    block is a content decision made *after* successful mapping, not a mapping failure. Mirrors
    ``vision_c1_prompt_mapping_study._mapping_valid_count`` exactly (duplicated, not imported,
    matching this project's per-module self-containment precedent).
    """

    return sum(
        1
        for run in runs
        if run.status == "SUCCEEDED"
        or run.error_code == VisionErrorCode.PROHIBITED_CLAIM_DETECTED.value
    )


def _has_runtime_or_device_failure(runs: tuple[V3FixtureRunResult, ...]) -> bool:
    return any(run.error_code in _RUNTIME_OR_DEVICE_ERROR_CODES for run in runs)


def _has_input_integrity_failure(runs: tuple[V3FixtureRunResult, ...]) -> bool:
    return any(run.error_detail in _INPUT_INTEGRITY_ERROR_DETAILS for run in runs)


def _evaluate_pass(pass_report: V3PassReport) -> V3PassEvaluation:
    valid_count = _mapping_valid_count(pass_report.runs)
    run_record_count = len(pass_report.runs)
    is_complete = (
        pass_report.mapping.attempted_runs == _EXPECTED_ATTEMPTED_RUNS
        and run_record_count == _EXPECTED_ATTEMPTED_RUNS
    )
    return V3PassEvaluation(
        run_label=pass_report.run_label,
        attempted_runs=pass_report.mapping.attempted_runs,
        run_record_count=run_record_count,
        is_complete=is_complete,
        mapping_valid_count=valid_count,
        truncated_count=pass_report.mapping.truncated_count,
        mapping_valid_ok=is_complete and valid_count >= _MIN_MAPPING_VALID_COUNT,
        systemic_truncation=pass_report.mapping.truncated_count >= _SYSTEMIC_TRUNCATION_THRESHOLD,
    )


def evaluate_v3_readiness(
    pass_1: V3PassReport,
    repeat_1: V3PassReport,
    *,
    same_lightning_session: bool,
) -> V3ReadinessVerdict:
    """Apply the v3 mapping-readiness gate, including the 15-minute repeat-comparability rule.

    ``same_lightning_session`` is a required, explicit operator attestation: this module cannot
    itself detect a Lightning Studio session reset, so the caller must state whether both passes
    ran in one uninterrupted session. ``pass_1``/``repeat_1`` must carry exactly the
    ``"V3_PASS_1"``/``"V3_REPEAT_1"`` labels (in either argument order is rejected -- each report
    must carry its own matching label).

    The pair is ``NON_COMPARABLE`` -- and cannot be evaluated for the numeric mapping-valid gate
    at all -- when ``same_lightning_session`` is ``False``; when the two reports' stamped
    profile/catalog/prompt identity disagree (``CONFIG_DRIFT``); when either report's
    ``fixture_manifest_version`` is not exactly ``"vision-v3-map-manifest-v1"``, or the two
    reports' manifest versions disagree with each other (``FIXTURE_MANIFEST_MISMATCH`` -- this
    closes the gap where a directly constructed/forged report stamped with a different manifest
    version could otherwise reach ``MAPPING_READY``); or when
    ``repeat_1.started_at - pass_1.completed_at`` is negative or exceeds 15 minutes
    (``REPEAT_WINDOW_EXCEEDED``). Otherwise the gate matches C1's: each pass independently needs
    ``>=7/8`` mapping-valid results; truncation ``>=2/8`` in either pass, an input-integrity
    failure, or a runtime/device failure blocks readiness regardless of the numeric threshold; and
    a malformed/partial run set (other than exactly eight attempted runs and eight run records)
    can never pass on the strength of a numerator alone.
    """

    if pass_1.run_label == repeat_1.run_label:
        raise ValueError("pass_1 and repeat_1 must carry distinct run labels")
    if pass_1.run_label != "V3_PASS_1" or repeat_1.run_label != "V3_REPEAT_1":
        raise ValueError("pass_1 must be labelled V3_PASS_1 and repeat_1 must be V3_REPEAT_1")

    expected_catalog_hash = vision_profile_catalog_hash_v2(vision_profile_catalog_v2())
    expected_profile_id = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1.value
    expected_prompt_sha256 = C1_PROMPT_V3.prompt_sha256
    expected_protocol_id = C1_PROMPT_V3.protocol_id

    config_drift = (
        pass_1.mapping.profile_id != expected_profile_id
        or repeat_1.mapping.profile_id != expected_profile_id
        or pass_1.mapping.profile_catalog_hash != expected_catalog_hash
        or repeat_1.mapping.profile_catalog_hash != expected_catalog_hash
        or pass_1.prompt_protocol_id != expected_protocol_id
        or repeat_1.prompt_protocol_id != expected_protocol_id
        or pass_1.prompt_sha256 != expected_prompt_sha256
        or repeat_1.prompt_sha256 != expected_prompt_sha256
    )
    manifest_mismatch = (
        pass_1.fixture_manifest_version != _V3_MANIFEST_VERSION
        or repeat_1.fixture_manifest_version != _V3_MANIFEST_VERSION
        or pass_1.fixture_manifest_version != repeat_1.fixture_manifest_version
    )

    repeat_gap = repeat_1.started_at - pass_1.completed_at
    window_exceeded = repeat_gap < timedelta(0) or repeat_gap > _COMPARABILITY_WINDOW
    session_reset = not same_lightning_session
    non_comparable = config_drift or manifest_mismatch or window_exceeded or session_reset

    integrity_failure = _has_input_integrity_failure(pass_1.runs) or _has_input_integrity_failure(
        repeat_1.runs
    )
    runtime_failure = _has_runtime_or_device_failure(pass_1.runs) or _has_runtime_or_device_failure(
        repeat_1.runs
    )

    pass_1_evaluation = _evaluate_pass(pass_1)
    repeat_1_evaluation = _evaluate_pass(repeat_1)

    incomplete = not pass_1_evaluation.is_complete or not repeat_1_evaluation.is_complete
    mapping_valid_ok = pass_1_evaluation.mapping_valid_ok and repeat_1_evaluation.mapping_valid_ok
    systemic_truncation = (
        pass_1_evaluation.systemic_truncation or repeat_1_evaluation.systemic_truncation
    )

    blocking: list[V3BlockingReason] = []
    if config_drift:
        blocking.append(V3BlockingReason.CONFIG_DRIFT)
    if manifest_mismatch:
        blocking.append(V3BlockingReason.FIXTURE_MANIFEST_MISMATCH)
    if window_exceeded:
        blocking.append(V3BlockingReason.REPEAT_WINDOW_EXCEEDED)
    if session_reset:
        blocking.append(V3BlockingReason.SESSION_RESET_DECLARED)
    if integrity_failure:
        blocking.append(V3BlockingReason.INPUT_INTEGRITY_FAILURE)
    if runtime_failure:
        blocking.append(V3BlockingReason.RUNTIME_OR_DEVICE_FAILURE)
    if incomplete:
        blocking.append(V3BlockingReason.INCOMPLETE_RUN_SET)
    if systemic_truncation:
        blocking.append(V3BlockingReason.SYSTEMIC_TRUNCATION_STOP_FOR_OUTPUT_BUDGET_ANALYSIS)
    if not incomplete and not mapping_valid_ok and not non_comparable:
        blocking.append(V3BlockingReason.MAPPING_VALID_BELOW_THRESHOLD)

    overall: Literal["MAPPING_READY", "MAPPING_NOT_READY", "NON_COMPARABLE"]
    if non_comparable:
        overall = "NON_COMPARABLE"
    elif blocking:
        overall = "MAPPING_NOT_READY"
    else:
        overall = "MAPPING_READY"

    return V3ReadinessVerdict(
        prompt_protocol_id=expected_protocol_id,
        prompt_sha256=expected_prompt_sha256,
        pass_1=pass_1_evaluation,
        repeat_1=repeat_1_evaluation,
        repeat_gap=repeat_gap,
        same_lightning_session=same_lightning_session,
        overall=overall,
        blocking_reasons=tuple(blocking),
    )


__all__ = [
    "NoRealV3P2T1PassAvailableError",
    "V3AdapterFactory",
    "V3BlockingReason",
    "V3FixtureRunResult",
    "V3ManifestIntegrityError",
    "V3MappingSummary",
    "V3PassEvaluation",
    "V3PassReport",
    "V3PromptBindingError",
    "V3ReadinessVerdict",
    "V3RunLabel",
    "V3UnsafeScratchDirectoryError",
    "V3VerifiedFixture",
    "evaluate_v3_readiness",
    "load_and_verify_v3_fixtures",
    "qwen_v3_adapter_factory",
    "run_v3_pass",
]
