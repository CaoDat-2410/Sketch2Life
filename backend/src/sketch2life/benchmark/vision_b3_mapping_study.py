"""Internal (non-CLI) executor for the approved P2-T3 Phase B B3 structured-output mapping study.

Mirrors ``vision_b2_preflight``'s discipline and is imported/called directly, never exposed as
a CLI. It calls the real ``QwenVisionAdapter`` (or an injected fake for unit tests) exactly once
per fixture against exactly eight deterministic geometric synthetic images -- never a real
drawing, never real child data, never versioned into the repository -- generated only into the
already-ignored ``data/runtime/`` scratch location and deleted afterward, and disjoint from
B4's separate, still-unpopulated ``fixtures/vision-b4/images/**`` held-out set (B3 never reads
or writes that location).

Raw model output never becomes a public return value or a persisted field. A
:class:`B3RawOutputCollector` owns the adapter's optional diagnostic hook (see
``QwenVisionAdapter.on_raw_output``):

- ``CLASSIFY_ONLY`` (default): the raw string is classified in memory and discarded; nothing is
  ever written to a file, log, result, or evidence.
- ``EPHEMERAL_CAPTURE``: selected explicitly, per B3 run, by the owner or Person 2 under the
  already-approved B0 raw-output access rule. The raw string is additionally written to an
  ignored scratch file for the duration of classification and removed again in a ``finally``
  block that runs even when classification itself raises. Only the classification -- never the
  text -- is ever retained afterward, in both modes.

Only four independent raw-derived buckets persist into the report: ``fenced``, ``truncated``,
``extra_key``, and ``invalid_enum``. A classifier-local missing-required-field signal exists
only as a private, directly testable helper (:func:`_detect_missing_required_field`); it is
never returned by :func:`classify_raw_output`, never a field on
:class:`B3RawOutputClassification`, and therefore structurally cannot reach the report.
Duplicate-observation-ID and reference-integrity-violation counts are not raw-derived at all --
they come from the adapter's own typed ``error_detail`` -- and are read off ``typed_failure_counts``
below.

Each rate's denominator is ``attempted_runs`` (the count of fixtures the adapter actually
returned a typed result for), not the count of runs where raw output happened to be observed;
the four buckets are independent flags and may overlap on a single run.

No widening: B3 observes the schema-valid rate as a finding. It never adds JSON
completion/extraction repair, never retries a mapping failure, and never changes the frozen
greedy-decoding V2 profile. ``known_policy_trigger_rate`` is always ``NOT_APPLICABLE`` against
the synthetic fixture lexicon, per D-2.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import sin
from pathlib import Path
from struct import pack
from threading import Event, Thread
from typing import Any, Literal
from wave import open as wave_open
from zlib import compress, crc32

from sketch2life.application.ports.vision_understanding_v2 import VisionUnderstandingPortV2
from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.contracts.schemas.vision import (
    VisionErrorCode,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

_FIXTURE_COUNT = 8
_DEFAULT_FIXTURES_DIR = Path("data/runtime/vision-b3-mapping-study")
_DEFAULT_CAPTURE_DIR = Path("data/runtime/vision-b3-raw-capture")

# Mirrors qwen_vision.py's fence contract in spirit, but this classifier deliberately treats an
# *opened but never closed* fence as fenced output too (the model still visibly attempted a
# fence; it just got cut off) -- qwen_vision.py's own parser only ever sees a complete fence as
# eligible for repair, which is a narrower, unrelated question. Duplicated rather than imported
# so this module never depends on that module's private parsing internals.
_FENCE_OPEN_PATTERN = re.compile(r"^```(?:json)?\s*\n")
_FENCE_CLOSE_PATTERN = re.compile(r"\n```\s*$")
_ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {"entities", "actions", "relations", "themes", "ambiguous_regions"}
)
_VALID_LANGUAGE_STATUS_VALUES = frozenset({"DECLARED", "MIXED", "NOT_DETERMINED"})
_REQUIRED_KEYS_BY_COLLECTION: dict[str, frozenset[str]] = {
    "entities": frozenset({"observation_id", "label", "confidence"}),
    "actions": frozenset({"observation_id", "label", "confidence"}),
    "relations": frozenset(
        {"observation_id", "predicate", "subject_ref", "object_ref", "confidence"}
    ),
    "themes": frozenset({"observation_id", "label", "evidence_refs", "confidence"}),
    "ambiguous_regions": frozenset({"observation_id", "note"}),
}

# Mirrors the V2 candidate contracts' own ``extra="forbid"`` key sets (allowed, not merely
# required -- e.g. ``actor_ref``/``object_ref`` are optional on ActionCandidateV1 but still a
# legal key). An unknown key at any of these levels is what the real adapter maps to
# ``VISION_SCHEMA_INVALID`` / ``OUTPUT_MAPPING_FAILED``, so the classifier must walk the same
# nesting, not just the top level.
_CANDIDATE_ALLOWED_KEYS_BY_COLLECTION: dict[str, frozenset[str]] = {
    "entities": frozenset({"observation_id", "label", "confidence"}),
    "actions": frozenset(
        {"observation_id", "label", "actor_ref", "object_ref", "confidence"}
    ),
    "relations": frozenset(
        {"observation_id", "predicate", "subject_ref", "object_ref", "confidence"}
    ),
    "themes": frozenset({"observation_id", "label", "evidence_refs", "confidence"}),
    "ambiguous_regions": frozenset({"observation_id", "note"}),
}
# The one ObservedTextV1-typed field per collection (``label`` on three of them, ``predicate``
# on relations, ``note`` on ambiguous regions).
_TEXT_FIELD_BY_COLLECTION: dict[str, str] = {
    "entities": "label",
    "actions": "label",
    "relations": "predicate",
    "themes": "label",
    "ambiguous_regions": "note",
}
_OBSERVED_TEXT_ALLOWED_KEYS = frozenset({"value", "language"})
_LANGUAGE_DECLARATION_ALLOWED_KEYS = frozenset({"status", "tags", "is_ground_truth"})


class UnsafeScratchDirectoryError(ValueError):
    """A caller-supplied scratch directory is not a safe ``shutil.rmtree`` cleanup target.

    Applies to both the fixtures directory and the ``EPHEMERAL_CAPTURE`` directory: each is
    later deleted wholesale, so it must resolve strictly inside the current working directory
    -- never absolute, the working directory itself, or one of its ancestors.
    """


class UnsafeFixturePathError(ValueError):
    """A generated fixture path is not a real file strictly inside the guarded scratch dir."""


class NoRealP2T1PassAvailableError(RuntimeError):
    """A B3 synthetic fixture did not earn a real P2-T1 ``PASS``.

    B3 must call the adapter with real, earned ``VisionMediaValidationProvenanceV1`` -- never a
    fabricated one -- so this stops before that fixture's adapter call rather than forcing a
    ``PASS``.
    """


class UnexpectedFixtureCountError(ValueError):
    """``build_fixtures`` returned a number of image paths other than ``_FIXTURE_COUNT``.

    B3's approved scope is exactly eight fixtures. A builder that returns fewer or more must
    never silently proceed to P2-T1 validation or an adapter call -- this is checked before
    either, right after ``build_fixtures`` returns.
    """


class B3RawOutputHookNotWiredError(RuntimeError):
    """A model-produced result had no raw-output classification.

    ``SUCCEEDED``, ``PROHIBITED_CLAIM_DETECTED``, and schema-invalid results whose detail is
    ``OUTPUT_MAPPING_FAILED``/``DUPLICATE_OBSERVATION_ID``/``REFERENCE_INTEGRITY_VIOLATION`` can
    only occur after the adapter's generation call already returned raw text -- so a missing
    classification for one of these means the diagnostic hook was unavailable or failed for
    this call. The most likely cause is ``collector.hook`` never having been wired as the
    adapter's ``on_raw_output``, but a hook that raised and was swallowed (by
    ``QwenVisionAdapter``'s own `contextlib.suppress`) or a capture/classification failure would
    look identical from here -- this error does not claim to know which. It never means this run
    legitimately produced no raw text. Failing closed here, before any report is returned,
    prevents a report whose raw-derived bucket counts silently understate the true rate. Never
    carries raw text -- there is none to classify in the first place when this is raised.
    """


_SCHEMA_DETAILS_REQUIRING_CLASSIFICATION = frozenset(
    {"OUTPUT_MAPPING_FAILED", "DUPLICATE_OBSERVATION_ID", "REFERENCE_INTEGRITY_VIOLATION"}
)


def _classification_is_required(result: VisionUnderstandingResultV2) -> bool:
    """True for every outcome that can only be reached after raw text was returned."""

    if isinstance(result, VisionUnderstandingSuccessV2):
        return True
    assert isinstance(result, VisionUnderstandingFailureV2)
    if result.error_code is VisionErrorCode.PROHIBITED_CLAIM_DETECTED:
        return True
    if result.error_code is VisionErrorCode.VISION_SCHEMA_INVALID:
        return result.error_detail.value in _SCHEMA_DETAILS_REQUIRING_CLASSIFICATION
    return False


class B3RawOutputMode(StrEnum):
    """Default is the safer mode; ``EPHEMERAL_CAPTURE`` is an explicit, per-run choice."""

    CLASSIFY_ONLY = "CLASSIFY_ONLY"
    EPHEMERAL_CAPTURE = "EPHEMERAL_CAPTURE"


@dataclass(frozen=True, slots=True)
class B3RawOutputClassification:
    """Only the four buckets the approved B3 scope permits to persist.

    Deliberately has no ``missing_field``/``missing_required_field`` attribute: that signal is
    classifier-local only (see :func:`_detect_missing_required_field`) and must never persist,
    so it is never a field here.
    """

    fenced: bool
    truncated: bool
    extra_key: bool
    invalid_enum: bool


def _looks_truncated(candidate_text: str) -> bool:
    """Heuristic, not a parser: unbalanced/incomplete JSON reads as truncated."""

    stripped = candidate_text.strip()
    if not stripped or not stripped.endswith(("}", "]")):
        return True
    if stripped.count("{") != stripped.count("}"):
        return True
    return stripped.count("[") != stripped.count("]")


def _contains_invalid_enum_value(node: object) -> bool:
    """Walks for a ``language.status``-shaped value outside the closed literal set."""

    if isinstance(node, dict):
        if "status" in node and node["status"] not in _VALID_LANGUAGE_STATUS_VALUES:
            return True
        return any(_contains_invalid_enum_value(value) for value in node.values())
    if isinstance(node, list):
        return any(_contains_invalid_enum_value(item) for item in node)
    return False


def _has_unknown_key(node: object, allowed: frozenset[str]) -> bool:
    return isinstance(node, dict) and not set(node).issubset(allowed)


def _detect_nested_extra_key(parsed: Mapping[str, Any]) -> bool:
    """Walks the full raw B3 payload grammar for an unknown key at any nesting level.

    Covers candidate objects (entity/action/relation/theme/ambiguous-region), each candidate's
    single ``ObservedTextV1``-typed field (``label``/``predicate``/``note``), and that field's
    nested ``TextLanguageDeclarationV1`` (``language``). Top-level collection keys are checked
    separately in :func:`classify_raw_output`. A missing field or a field of the wrong type is
    never treated as an unknown key here -- this only ever flags a key that should not exist.
    """

    for collection_key, candidate_allowed in _CANDIDATE_ALLOWED_KEYS_BY_COLLECTION.items():
        items = parsed.get(collection_key)
        if not isinstance(items, list):
            continue
        text_field = _TEXT_FIELD_BY_COLLECTION[collection_key]
        for item in items:
            if not isinstance(item, dict):
                continue
            if _has_unknown_key(item, candidate_allowed):
                return True
            text_value = item.get(text_field)
            if not isinstance(text_value, dict):
                continue
            if _has_unknown_key(text_value, _OBSERVED_TEXT_ALLOWED_KEYS):
                return True
            if _has_unknown_key(text_value.get("language"), _LANGUAGE_DECLARATION_ALLOWED_KEYS):
                return True
    return False


def _detect_missing_required_field(parsed: Mapping[str, Any]) -> bool:
    """Classifier-local-only signal.

    Directly unit-testable, but deliberately never returned by :func:`classify_raw_output` and
    never a field on :class:`B3RawOutputClassification` -- see that class's docstring for why
    this must never persist into a B3 report.
    """

    for collection_key, required_keys in _REQUIRED_KEYS_BY_COLLECTION.items():
        items = parsed.get(collection_key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and not required_keys.issubset(item):
                return True
    return False


def classify_raw_output(raw_output: str) -> B3RawOutputClassification:
    """Deterministic, in-memory-only classification of one raw provider string.

    ``fenced`` and ``truncated`` are independent and may both be true: a fence that opens but
    never closes is both "the model used a fence" and "the output was cut off". ``extra_key``
    is true for an unknown key anywhere in the raw payload grammar the V2 candidate contracts
    define -- top-level collections, a candidate object, its ``ObservedTextV1``-typed field, or
    that field's nested ``TextLanguageDeclarationV1`` -- not only an unknown top-level key,
    matching every nesting level the real adapter's strict ``extra="forbid"`` schemas enforce.
    """

    stripped = raw_output.strip()
    fence_open_match = _FENCE_OPEN_PATTERN.match(stripped)
    fenced = fence_open_match is not None

    if fence_open_match is not None:
        after_open = stripped[fence_open_match.end() :]
        fence_close_match = _FENCE_CLOSE_PATTERN.search(after_open)
        if fence_close_match is not None:
            candidate_text = after_open[: fence_close_match.start()]
            fence_closed = True
        else:
            candidate_text = after_open
            fence_closed = False
    else:
        candidate_text = stripped
        fence_closed = True  # no fence to close; irrelevant to a plain payload

    try:
        parsed = json.loads(candidate_text)
        parse_failed = False
    except json.JSONDecodeError:
        parsed = None
        parse_failed = True

    truncated = not fence_closed or (parse_failed and _looks_truncated(candidate_text))
    extra_key = False
    invalid_enum = False
    if not parse_failed and isinstance(parsed, dict):
        extra_key = not set(parsed).issubset(_ALLOWED_TOP_LEVEL_KEYS) or _detect_nested_extra_key(
            parsed
        )
        invalid_enum = _contains_invalid_enum_value(parsed)

    return B3RawOutputClassification(
        fenced=fenced, truncated=truncated, extra_key=extra_key, invalid_enum=invalid_enum
    )


def _require_safe_cleanup_target(scratch_dir: Path) -> None:
    if scratch_dir.is_absolute():
        raise UnsafeScratchDirectoryError(
            "scratch directory must be a relative path so its later cleanup stays scoped "
            "under the current working directory"
        )
    cwd = Path.cwd().resolve()
    resolved = scratch_dir.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise UnsafeScratchDirectoryError(
            "scratch directory must resolve to a location strictly nested under the current "
            "working directory, never the working directory itself or an ancestor of it"
        )


def _require_fixture_path_within_scratch(fixtures_dir: Path, path: Path, *, label: str) -> None:
    if path.is_absolute():
        raise UnsafeFixturePathError(f"the {label} fixture path must be relative")
    fixtures_root = fixtures_dir.resolve()
    resolved = path.resolve()
    if resolved == fixtures_root or fixtures_root not in resolved.parents:
        raise UnsafeFixturePathError(
            f"the {label} fixture path must resolve strictly inside fixtures_dir"
        )
    if not resolved.is_file():
        raise UnsafeFixturePathError(f"the {label} fixture path must be an existing regular file")


class B3RawOutputCollector:
    """Owns the mode-gated diagnostic hook passed as ``QwenVisionAdapter(on_raw_output=...)``.

    One collector instance is shared across all eight sequential, non-concurrent B3 calls. The
    runner reads :meth:`take_latest` immediately after each ``adapter.understand`` call returns,
    so a stale classification can never leak into the next fixture's run.
    """

    def __init__(
        self,
        mode: B3RawOutputMode = B3RawOutputMode.CLASSIFY_ONLY,
        capture_dir: Path = _DEFAULT_CAPTURE_DIR,
    ) -> None:
        self.mode = mode
        self._capture_dir = capture_dir
        self._latest: B3RawOutputClassification | None = None
        if mode is B3RawOutputMode.EPHEMERAL_CAPTURE:
            _require_safe_cleanup_target(capture_dir)

    def hook(self, raw_output: str) -> None:
        if self.mode is B3RawOutputMode.EPHEMERAL_CAPTURE:
            self._capture_dir.mkdir(parents=True, exist_ok=True)
            capture_path = self._capture_dir / "b3-raw-output.txt"
            try:
                capture_path.write_text(raw_output, encoding="utf-8")
                self._latest = classify_raw_output(raw_output)
            finally:
                capture_path.unlink(missing_ok=True)
        else:
            self._latest = classify_raw_output(raw_output)

    def take_latest(self) -> B3RawOutputClassification | None:
        latest = self._latest
        self._latest = None
        return latest

    def cleanup(self) -> None:
        if self.mode is B3RawOutputMode.EPHEMERAL_CAPTURE:
            shutil.rmtree(self._capture_dir, ignore_errors=True)


class _VramSampler:
    """Background ``nvidia-smi`` poller. Duplicated from ``vision_b2_preflight`` rather than
    imported, matching that module's own precedent for keeping each benchmark module
    self-contained.
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

    def start(self) -> None:
        if not self._available:
            return
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            sample = self._sample_once()
            if sample is not None:
                self._peak_mb = sample if self._peak_mb is None else max(self._peak_mb, sample)
            self._stop.wait(self._interval_seconds)

    def stop_and_get_peak_mb(self) -> float | None:
        if not self._available:
            return None
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        return self._peak_mb


def _interior_shade(recipe_index: int, x: int, y: int) -> int:
    """Eight distinct deterministic geometric patterns -- shapes only, never a real drawing."""

    local_x = x - 30
    local_y = y - 30
    if recipe_index == 0:
        on = (x // 8) % 2 == 0
    elif recipe_index == 1:
        on = (x // 4) % 2 == 0
    elif recipe_index == 2:
        on = (x // 12) % 2 == 0
    elif recipe_index == 3:
        on = (x // 10) % 2 == 0
    elif recipe_index == 4:
        on = (y // 10) % 2 == 0
    elif recipe_index == 5:
        on = ((x + y) // 10) % 2 == 0
    elif recipe_index == 6:
        distance = int((local_x * local_x + local_y * local_y) ** 0.5)
        on = (distance // 12) % 2 == 0
    else:
        on = ((x - y) // 10) % 2 == 0
    return 30 if on else 235


def _write_b3_fixture_image(path: Path, recipe_index: int) -> None:
    width, height = 160, 160
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            in_interior = 30 < x < 130 and 30 < y < 130
            shade = _interior_shade(recipe_index, x, y) if in_interior else 235
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


def _write_b3_companion_audio(path: Path) -> None:
    """Same tone shape already proven to pass P2-T1's audio quality gate."""

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


def _default_fixture_builder(fixtures_dir: Path) -> tuple[tuple[Path, ...], Path]:
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    image_paths = tuple(
        fixtures_dir / f"b3-fixture-{index + 1:02d}.png" for index in range(_FIXTURE_COUNT)
    )
    for index, image_path in enumerate(image_paths):
        _write_b3_fixture_image(image_path, index)
    audio_path = fixtures_dir / "b3-companion.wav"
    _write_b3_companion_audio(audio_path)
    return image_paths, audio_path


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _real_p2t1_pass_media_validation(
    fixture_id: str, image_path: Path, audio_path: Path
) -> VisionMediaValidationProvenanceV1:
    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref=f"vision-b3-{fixture_id}-synthetic-image",
            audio_artifact_ref="vision-b3-synthetic-audio",
        )
    )
    if result.decision is not MediaDecision.PASS:
        raise NoRealP2T1PassAvailableError(
            f"B3 fixture {fixture_id} did not earn a real P2-T1 PASS; refusing to fabricate one"
        )
    artifact_payload = result.model_dump_json().encode("utf-8")
    return VisionMediaValidationProvenanceV1(
        validation_artifact_ref=f"vision-b3-{fixture_id}-p2t1-validation",
        validation_artifact_sha256=sha256(artifact_payload).hexdigest(),
        decision="PASS",
        validator_policy_version=result.validator_policy_version,
    )


@dataclass(frozen=True, slots=True)
class B3FixtureRunResult:
    """One fixture's typed outcome plus its raw-derived classification, if observed.

    ``fenced``/``truncated``/``extra_key``/``invalid_enum`` are ``None`` exactly when the raw
    output was never produced for this run (e.g. ``INPUT_NOT_VALIDATED``, model/device
    unavailable, timeout, or a provider failure before generation returned) -- never a bare
    ``False`` standing in for "not observed".
    """

    fixture_id: str
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
class B3MappingStudyReport:
    """Safe, evidence-ready aggregate. Never carries raw model output, a prompt, or a path."""

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
    runs: tuple[B3FixtureRunResult, ...] = ()


def _to_run_result(
    fixture_id: str,
    result: VisionUnderstandingResultV2,
    classification: B3RawOutputClassification | None,
    *,
    wall_latency_ms: float,
    peak_vram_mb: float | None,
    vram_not_measured_reason: str | None,
) -> B3FixtureRunResult:
    if isinstance(result, VisionUnderstandingSuccessV2):
        error_code = None
        error_detail = None
    else:
        assert isinstance(result, VisionUnderstandingFailureV2)
        error_code = result.error_code.value
        error_detail = result.error_detail.value

    return B3FixtureRunResult(
        fixture_id=fixture_id,
        status=result.status,
        error_code=error_code,
        error_detail=error_detail,
        attempt_number=result.attempt_number,
        repair_attempted=result.repair_attempted,
        wall_latency_ms=wall_latency_ms,
        peak_vram_mb=peak_vram_mb,
        vram_not_measured_reason=vram_not_measured_reason,
        fenced=classification.fenced if classification is not None else None,
        truncated=classification.truncated if classification is not None else None,
        extra_key=classification.extra_key if classification is not None else None,
        invalid_enum=classification.invalid_enum if classification is not None else None,
    )


def run_b3_mapping_study(
    adapter: VisionUnderstandingPortV2,
    collector: B3RawOutputCollector,
    *,
    profile_id: VisionProfileIdV2 = VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
    correlation_id_prefix: str = "vision-b3",
    sample_vram: bool = True,
    fixtures_dir: Path = _DEFAULT_FIXTURES_DIR,
    build_fixtures: Callable[[Path], tuple[tuple[Path, ...], Path]] = _default_fixture_builder,
) -> B3MappingStudyReport:
    """Execute exactly one B3 call per fixture: eight fixtures, eight adapter calls, no retry.

    ``adapter`` must already be constructed with ``collector.hook`` as its
    ``on_raw_output`` (the real ``QwenVisionAdapter`` for a Lightning run, or an injected fake
    for unit tests). A mapping failure is never retried here: this loop calls
    ``adapter.understand`` exactly once per fixture and records whatever typed result comes
    back, matching the frozen V2 terminal-outcome matrix's own no-retry-on-schema-invalid rule.

    Raises ``UnsafeScratchDirectoryError``/``UnsafeFixturePathError`` before any adapter call if
    the scratch layout is unsafe, ``UnexpectedFixtureCountError`` before any P2-T1 validation or
    adapter call if ``build_fixtures`` did not return exactly ``_FIXTURE_COUNT`` image paths,
    ``NoRealP2T1PassAvailableError`` for a specific fixture that did not earn a real P2-T1
    ``PASS``, and ``B3RawOutputHookNotWiredError`` if a result that can only follow successfully
    returned raw text (``SUCCEEDED``, ``PROHIBITED_CLAIM_DETECTED``, or schema-invalid with
    ``OUTPUT_MAPPING_FAILED``/``DUPLICATE_OBSERVATION_ID``/``REFERENCE_INTEGRITY_VIOLATION``) has
    no classification -- a fail-closed guard against the diagnostic hook having been
    unavailable or having failed for that call (most commonly ``adapter`` constructed without
    ``on_raw_output=collector.hook``, but a swallowed hook/capture/classification failure would
    look identical), which would otherwise make the raw-derived bucket counts silently understate
    the true rate. The fixtures directory (and the capture directory, if ``collector.mode`` is
    ``EPHEMERAL_CAPTURE``) are deleted in a ``finally`` covering fixture creation itself, so
    every one of these raises still cleans up scratch.
    """

    _require_safe_cleanup_target(fixtures_dir)

    typed_failure_counts: dict[str, int] = {}
    schema_valid_count = 0
    lossless_unwrap_recovered_count = 0
    fenced_count = truncated_count = extra_key_count = invalid_enum_count = 0
    runs: list[B3FixtureRunResult] = []

    try:
        image_paths, audio_path = build_fixtures(fixtures_dir)
        if len(image_paths) != _FIXTURE_COUNT:
            raise UnexpectedFixtureCountError(
                f"build_fixtures must return exactly {_FIXTURE_COUNT} image paths, got "
                f"{len(image_paths)}"
            )
        for image_path in image_paths:
            _require_fixture_path_within_scratch(fixtures_dir, image_path, label="image")
        _require_fixture_path_within_scratch(fixtures_dir, audio_path, label="audio")

        for index, image_path in enumerate(image_paths):
            fixture_id = f"b3-fixture-{index + 1:02d}"
            media_validation = _real_p2t1_pass_media_validation(
                fixture_id, image_path, audio_path
            )
            request = VisionUnderstandingRequestV2(
                correlation_id=f"{correlation_id_prefix}-{fixture_id}",
                source_image_ref=VisionImageReferenceV1(
                    artifact_ref=image_path.as_posix(), sha256=_sha256_of(image_path)
                ),
                media_validation=media_validation,
                requested_profile_id=profile_id,
            )

            collector.take_latest()
            sampler = _VramSampler() if sample_vram else None
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
            classification = collector.take_latest()
            if classification is None and _classification_is_required(result):
                raise B3RawOutputHookNotWiredError(
                    f"{fixture_id}: no raw-output classification was observed for a "
                    f"{result.status} result whose detail requires one; the diagnostic hook "
                    "was unavailable or failed for this call (most likely never wired as "
                    "on_raw_output=collector.hook, but a swallowed hook/capture/classification "
                    "failure would look identical)"
                )

            vram_not_measured_reason: str | None
            if sample_vram:
                vram_not_measured_reason = (
                    None
                    if peak_vram_mb is not None
                    else "nvidia-smi was unavailable or returned no sample"
                )
            else:
                vram_not_measured_reason = "VRAM sampling was disabled for this call"

            runs.append(
                _to_run_result(
                    fixture_id,
                    result,
                    classification,
                    wall_latency_ms=elapsed_ms,
                    peak_vram_mb=peak_vram_mb,
                    vram_not_measured_reason=vram_not_measured_reason,
                )
            )

            if isinstance(result, VisionUnderstandingSuccessV2):
                schema_valid_count += 1
                if result.repair_attempted:
                    lossless_unwrap_recovered_count += 1
            else:
                assert isinstance(result, VisionUnderstandingFailureV2)
                key = result.error_detail.value
                typed_failure_counts[key] = typed_failure_counts.get(key, 0) + 1

            if classification is not None:
                fenced_count += int(classification.fenced)
                truncated_count += int(classification.truncated)
                extra_key_count += int(classification.extra_key)
                invalid_enum_count += int(classification.invalid_enum)
    finally:
        shutil.rmtree(fixtures_dir, ignore_errors=True)
        collector.cleanup()

    catalog = vision_profile_catalog_v2()
    return B3MappingStudyReport(
        profile_id=profile_id.value,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        raw_output_mode=collector.mode.value,
        attempted_runs=len(runs),
        schema_valid_count=schema_valid_count,
        typed_failure_counts=dict(typed_failure_counts),
        lossless_unwrap_recovered_count=lossless_unwrap_recovered_count,
        fenced_count=fenced_count,
        truncated_count=truncated_count,
        extra_key_count=extra_key_count,
        invalid_enum_count=invalid_enum_count,
        runs=tuple(runs),
    )


__all__ = [
    "B3FixtureRunResult",
    "B3MappingStudyReport",
    "B3RawOutputClassification",
    "B3RawOutputCollector",
    "B3RawOutputHookNotWiredError",
    "B3RawOutputMode",
    "NoRealP2T1PassAvailableError",
    "UnexpectedFixtureCountError",
    "UnsafeFixturePathError",
    "UnsafeScratchDirectoryError",
    "classify_raw_output",
    "run_b3_mapping_study",
]
