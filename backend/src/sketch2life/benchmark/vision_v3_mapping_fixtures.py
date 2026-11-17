"""Deterministic Phase 3 authoring for the prompt-v3 mapping-validation fixture package.

Authorized only by `P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE3_IMPLEMENTATION_PLAN.md` (local-only,
gitignored evidence note) as phase-specific local fixture authoring inside the already-approved
P2-T3 Phase B B3 structured-output mapping-study boundary. This module contains pure, deterministic
code-generated PNG/WAV authoring and authoring-time local validation helpers only -- there is no
adapter, prompt injection, provider, runner, model, or GPU import or call anywhere in this module,
and none is reachable from any function it defines.

The eight fixtures below are the exact taxonomy fixed by the implementation plan's Section 5. Every
collection reference in a fixture's description names an observation *opportunity* only -- never an
expected output, ground truth, or quality criterion. A schema-valid but entirely empty result
(``entities``/``actions``/``relations``/``themes``/``ambiguous_regions`` all ``[]``) is an
acceptable outcome for every fixture; this module makes no correctness claim about any future model
output and never inspects one.

Interior fills use the same proven-safe technique as
``vision_b3_mapping_study.py``'s ``_interior_shade``: pixels inside a shape toggle between a dark
ink shade and the background shade in a periodic pattern, rather than a flat fill, so each filled
shape carries enough internal luminance transitions to clear the real P2-T1
``minimum_edge_strength`` gate -- the same reason B3's fixtures reliably pass it. A flat
single-shade fill of a shape this size would not.
"""

from __future__ import annotations

import math
import re
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from struct import pack
from wave import open as wave_open
from zlib import compress, crc32

from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

_FIXTURE_COUNT = 8
_CANVAS_SIZE = 192
_BACKGROUND_SHADE = 248
_PRIMARY_INK_SHADE = 25

_DEFAULT_IMAGES_DIR = Path(
    "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-map/images"
)
_DEFAULT_SCRATCH_AUDIO_DIR = Path("data/runtime/vision-v3-map-authoring-audio")
_RECIPE_MODULE_REF = "backend/src/sketch2life/benchmark/vision_v3_mapping_fixtures.py"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

_V3_PROMPT_PROTOCOL_ID = "vision-v2-structured-output-prompt-v3"
_V3_PROMPT_SHA256 = "bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3"
_V3_SCHEMA_TARGET = "VisionUnderstandingResultV2"
_WINDOWS_DRIVE_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class UnsafeFixturePathError(ValueError):
    """A caller-supplied directory or generated fixture path is not a safe target.

    ``images_dir``/``scratch_audio_dir`` must be relative and resolve strictly inside the
    current working directory; a generated image path must resolve strictly inside its own
    ``images_dir``. This guards both the persistent images directory and the deletable scratch
    audio directory the same way ``vision_b3_mapping_study.py`` guards its own scratch paths.
    """


class V3MapManifestIntegrityError(ValueError):
    """The authoring result cannot safely produce the review-pending manifest."""


@dataclass(frozen=True, slots=True)
class V3MapFixtureSpec:
    """One taxonomy entry, fixed by the implementation plan's Section 5 -- not inferred here."""

    fixture_id: str
    taxonomy_token: str
    description: str


TAXONOMY: tuple[V3MapFixtureSpec, ...] = (
    V3MapFixtureSpec(
        "v3-map-fixture-01",
        "single_entity_baseline",
        "centered pentagon with a wide margin",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-02",
        "unconnected_multi_entity",
        "unconnected pentagon and hexagon in a horizontal layout",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-03",
        "directed_arrow_action_opportunity",
        "two shapes joined by one clearly directed arrow",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-04",
        "three_entity_triangular_cap",
        "star, hexagon, and diamond in a triangular layout",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-05",
        "connector_with_repeated_motif",
        "two shapes with a simple connector and a repeated motif",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-06",
        "crescent_occluding_octagon",
        "crescent partially occluding an octagon",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-07",
        "straight_nondirectional_relation",
        "star and hexagon joined by a straight non-directional line",
    ),
    V3MapFixtureSpec(
        "v3-map-fixture-08",
        "dashed_outline_octagon",
        "one dashed-outline octagon with wide margins",
    ),
)


# --- Pure geometry helpers -------------------------------------------------------------------


def _point_in_polygon(x: float, y: float, vertices: tuple[tuple[float, float], ...]) -> bool:
    """Standard ray-casting test; works for the convex and star (concave) polygons used below."""

    inside = False
    count = len(vertices)
    j = count - 1
    for i in range(count):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _regular_polygon(
    center: tuple[float, float], radius: float, sides: int, rotation_degrees: float
) -> tuple[tuple[float, float], ...]:
    cx, cy = center
    rotation = math.radians(rotation_degrees)
    return tuple(
        (
            cx + radius * math.cos(rotation + 2 * math.pi * i / sides),
            cy + radius * math.sin(rotation + 2 * math.pi * i / sides),
        )
        for i in range(sides)
    )


def _star_polygon(
    center: tuple[float, float],
    outer_radius: float,
    inner_radius: float,
    points: int,
    rotation_degrees: float,
) -> tuple[tuple[float, float], ...]:
    cx, cy = center
    rotation = math.radians(rotation_degrees)
    vertices: list[tuple[float, float]] = []
    for i in range(points * 2):
        radius = outer_radius if i % 2 == 0 else inner_radius
        angle = rotation + math.pi * i / points
        vertices.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return tuple(vertices)


def _arrowhead_vertices(
    tip: tuple[float, float], angle_degrees: float, size: float
) -> tuple[tuple[float, float], ...]:
    angle = math.radians(angle_degrees)
    back_left = angle + math.radians(150)
    back_right = angle - math.radians(150)
    return (
        tip,
        (tip[0] + size * math.cos(back_left), tip[1] + size * math.sin(back_left)),
        (tip[0] + size * math.cos(back_right), tip[1] + size * math.sin(back_right)),
    )


def _distance_to_segment(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.hypot(px - sx, py - sy)
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_squared))
    projected_x, projected_y = sx + t * dx, sy + t * dy
    return math.hypot(px - projected_x, py - projected_y)


def _textured_shade(recipe_index: int, x: int, y: int) -> int:
    """Eight distinct deterministic interior patterns, mirroring B3's proven-safe technique."""

    if recipe_index == 0:
        on = (x // 6) % 2 == 0
    elif recipe_index == 1:
        on = (y // 6) % 2 == 0
    elif recipe_index == 2:
        on = ((x + y) // 8) % 2 == 0
    elif recipe_index == 3:
        on = ((x - y) // 8) % 2 == 0
    elif recipe_index == 4:
        on = (x // 4) % 2 == 0
    elif recipe_index == 5:
        on = (y // 10) % 2 == 0
    elif recipe_index == 6:
        on = ((x + 2 * y) // 9) % 2 == 0
    else:
        on = ((2 * x + y) // 9) % 2 == 0
    return _PRIMARY_INK_SHADE if on else _BACKGROUND_SHADE


_Layer = Callable[[int, int], int | None]


def _textured_polygon_layer(vertices: tuple[tuple[float, float], ...], recipe_index: int) -> _Layer:
    def layer(x: int, y: int) -> int | None:
        if _point_in_polygon(x + 0.5, y + 0.5, vertices):
            return _textured_shade(recipe_index, x, y)
        return None

    return layer


def _solid_polygon_layer(vertices: tuple[tuple[float, float], ...], shade: int) -> _Layer:
    def layer(x: int, y: int) -> int | None:
        return shade if _point_in_polygon(x + 0.5, y + 0.5, vertices) else None

    return layer


def _solid_line_layer(
    start: tuple[float, float], end: tuple[float, float], thickness: float, shade: int
) -> _Layer:
    def layer(x: int, y: int) -> int | None:
        distance = _distance_to_segment((x + 0.5, y + 0.5), start, end)
        return shade if distance <= thickness / 2 else None

    return layer


def _solid_polygon_outline_layers(
    vertices: tuple[tuple[float, float], ...], thickness: float, shade: int
) -> tuple[_Layer, ...]:
    return tuple(
        _solid_line_layer(start, end, thickness, shade)
        for start, end in zip(vertices, vertices[1:] + vertices[:1], strict=True)
    )


def _solid_arrowhead_layer(
    tip: tuple[float, float], angle_degrees: float, size: float, shade: int
) -> _Layer:
    return _solid_polygon_layer(_arrowhead_vertices(tip, angle_degrees, size), shade)


def _solid_crescent_layer(
    outer_center: tuple[float, float],
    outer_radius: float,
    inner_center: tuple[float, float],
    inner_radius: float,
    shade: int,
) -> _Layer:
    def layer(x: int, y: int) -> int | None:
        px, py = x + 0.5, y + 0.5
        distance_outer = math.hypot(px - outer_center[0], py - outer_center[1])
        distance_inner = math.hypot(px - inner_center[0], py - inner_center[1])
        if distance_outer <= outer_radius and distance_inner > inner_radius:
            return shade
        return None

    return layer


def _dashed_ring_layer(
    center: tuple[float, float],
    outer_radius: float,
    thickness: float,
    sides: int,
    rotation_degrees: float,
    dash_count: int,
    dash_duty: float,
    shade: int,
) -> _Layer:
    outer_vertices = _regular_polygon(center, outer_radius, sides, rotation_degrees)
    inner_vertices = _regular_polygon(center, outer_radius - thickness, sides, rotation_degrees)

    def layer(x: int, y: int) -> int | None:
        px, py = x + 0.5, y + 0.5
        if not _point_in_polygon(px, py, outer_vertices):
            return None
        if _point_in_polygon(px, py, inner_vertices):
            return None
        angle = math.atan2(py - center[1], px - center[0])
        if angle < 0:
            angle += 2 * math.pi
        segment_position = angle / (2 * math.pi / dash_count)
        fractional = segment_position - math.floor(segment_position)
        return shade if fractional < dash_duty else None

    return layer


def _fixture_layers(index: int) -> tuple[_Layer, ...]:
    """Exact taxonomy from the implementation plan's Section 5, indexed 0-7 (fixtures 01-08)."""

    if index == 0:
        pentagon = _regular_polygon((96, 96), 60, 5, -90)
        return (_textured_polygon_layer(pentagon, 0),)
    if index == 1:
        pentagon = _regular_polygon((58, 96), 32, 5, -90)
        hexagon = _regular_polygon((134, 96), 32, 6, 0)
        return (
            _textured_polygon_layer(pentagon, 1),
            _textured_polygon_layer(hexagon, 1),
        )
    if index == 2:
        pentagon = _regular_polygon((50, 96), 26, 5, -90)
        hexagon = _regular_polygon((142, 96), 26, 6, 0)
        return (
            _textured_polygon_layer(pentagon, 2),
            _textured_polygon_layer(hexagon, 2),
            _solid_line_layer((80, 96), (108, 96), 6, _PRIMARY_INK_SHADE),
            _solid_arrowhead_layer((116, 96), 0, 12, _PRIMARY_INK_SHADE),
        )
    if index == 3:
        star = _star_polygon((96, 50), 26, 13, 5, -90)
        hexagon = _regular_polygon((56, 140), 26, 6, 0)
        diamond = _regular_polygon((136, 140), 22, 4, 45)
        return (
            _textured_polygon_layer(star, 3),
            *_solid_polygon_outline_layers(star, 3, _PRIMARY_INK_SHADE),
            _textured_polygon_layer(hexagon, 3),
            _textured_polygon_layer(diamond, 3),
        )
    if index == 4:
        pentagon = _regular_polygon((56, 96), 26, 5, -90)
        hexagon = _regular_polygon((136, 96), 26, 6, 0)
        layers: list[_Layer] = [
            _textured_polygon_layer(pentagon, 4),
            _textured_polygon_layer(hexagon, 4),
            _solid_line_layer((82, 96), (110, 96), 4, _PRIMARY_INK_SHADE),
        ]
        for tick_x in (90, 96, 102):
            layers.append(_solid_line_layer((tick_x, 91), (tick_x, 101), 3, _PRIMARY_INK_SHADE))
        return tuple(layers)
    if index == 5:
        octagon = _regular_polygon((96, 96), 50, 8, 22.5)
        return (
            _textured_polygon_layer(octagon, 5),
            _solid_crescent_layer((130, 96), 38, (143, 96), 31, _PRIMARY_INK_SHADE),
        )
    if index == 6:
        star = _star_polygon((52, 96), 28, 14, 5, -90)
        hexagon = _regular_polygon((140, 96), 28, 6, 0)
        return (
            _textured_polygon_layer(star, 6),
            *_solid_polygon_outline_layers(star, 3, _PRIMARY_INK_SHADE),
            _textured_polygon_layer(hexagon, 6),
            _solid_line_layer((80, 96), (112, 96), 3, _PRIMARY_INK_SHADE),
        )
    if index == 7:
        return (_dashed_ring_layer((96, 96), 60, 9, 8, 22.5, 20, 0.7, _PRIMARY_INK_SHADE),)
    raise ValueError(f"no fixture layout defined for index {index}")


def _render_shade(layers: tuple[_Layer, ...], x: int, y: int) -> int:
    shade = _BACKGROUND_SHADE
    for layer in layers:
        result = layer(x, y)
        if result is not None:
            shade = result
    return shade


def _write_v3_fixture_image(path: Path, index: int) -> None:
    layers = _fixture_layers(index)
    rows = bytearray()
    for y in range(_CANVAS_SIZE):
        rows.append(0)
        for x in range(_CANVAS_SIZE):
            shade = _render_shade(layers, x, y)
            rows.extend((shade, shade, shade))
    compressed = compress(bytes(rows), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return pack(">I", len(data)) + tag + data + pack(">I", crc32(tag + data) & 0xFFFFFFFF)

    ihdr = pack(">IIBBBBB", _CANVAS_SIZE, _CANVAS_SIZE, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def _write_v3_companion_audio(path: Path) -> None:
    """Same deterministic tone shape already proven to pass P2-T1's audio quality gate."""

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


# --- Safety guards -----------------------------------------------------------------------------


def _is_absolute_machine_path(path: Path) -> bool:
    value = str(path)
    return value.startswith(("/", "\\")) or bool(_WINDOWS_DRIVE_ABSOLUTE_PATTERN.match(value))


def _require_relative_repo_path(path: Path, *, label: str) -> None:
    if _is_absolute_machine_path(path):
        raise UnsafeFixturePathError(f"{label} must be a relative path")
    cwd = Path.cwd().resolve()
    resolved = path.resolve()
    if resolved == cwd or cwd not in resolved.parents:
        raise UnsafeFixturePathError(
            f"{label} must resolve strictly inside the current working directory"
        )


def _require_repository_root_for_default_paths(images_dir: Path, scratch_audio_dir: Path) -> None:
    uses_default_path = (
        images_dir == _DEFAULT_IMAGES_DIR or scratch_audio_dir == _DEFAULT_SCRATCH_AUDIO_DIR
    )
    if uses_default_path and Path.cwd().resolve() != _REPOSITORY_ROOT:
        raise UnsafeFixturePathError(
            "default authoring paths require the repository root as the working directory"
        )


def _require_fixture_path_within(directory: Path, path: Path, *, label: str) -> None:
    if _is_absolute_machine_path(path):
        raise UnsafeFixturePathError(f"the {label} fixture path must be relative")
    directory_root = directory.resolve()
    resolved = path.resolve()
    if resolved == directory_root or directory_root not in resolved.parents:
        raise UnsafeFixturePathError(
            f"the {label} fixture path must resolve strictly inside {directory}"
        )


def _sha256_of(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _p2t1_pass(fixture_id: str, image_path: Path, audio_path: Path) -> bool:
    result = DeterministicMediaValidator(FileMediaSignalInspector()).validate(
        MediaValidationRequest(
            image_path=image_path,
            audio_path=audio_path,
            image_artifact_ref=f"vision-v3-map-{fixture_id}-synthetic-image",
            audio_artifact_ref="vision-v3-map-synthetic-audio",
        )
    )
    return result.decision is MediaDecision.PASS


# --- Authoring orchestration ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class V3MapFixtureResult:
    fixture_id: str
    image_ref: str
    image_sha256: str
    width: int
    height: int
    taxonomy_token: str
    p2t1_pass: bool


@dataclass(frozen=True, slots=True)
class V3MapAuthoringResult:
    fixtures: tuple[V3MapFixtureResult, ...]
    all_p2t1_pass: bool
    scratch_audio_deleted: bool
    model_or_gpu_called: bool = False


def author_v3_map_fixture_package(
    *,
    images_dir: Path = _DEFAULT_IMAGES_DIR,
    scratch_audio_dir: Path = _DEFAULT_SCRATCH_AUDIO_DIR,
) -> V3MapAuthoringResult:
    """Author exactly eight deterministic PNGs and locally validate each with a real P2-T1 PASS.

    The default paths are accepted only when the current working directory is the repository root,
    preventing a run from ``backend/`` from silently creating ``backend/features/``. Explicit
    caller-supplied relative paths remain available for guarded temporary-directory tests.
    ``images_dir`` is a persistent, gitignored directory -- it is created but never deleted here.
    ``scratch_audio_dir`` holds only the ephemeral validation-only companion audio signal and is
    always deleted in ``finally``, on both success and exception, mirroring
    ``vision_b3_mapping_study.py``'s own scratch-cleanup discipline. No model, adapter, provider,
    or GPU path is reachable from this function.
    """

    _require_repository_root_for_default_paths(images_dir, scratch_audio_dir)
    _require_relative_repo_path(images_dir, label="images_dir")
    _require_relative_repo_path(scratch_audio_dir, label="scratch_audio_dir")

    images_dir.mkdir(parents=True, exist_ok=True)

    fixture_results: list[V3MapFixtureResult] = []
    try:
        scratch_audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = scratch_audio_dir / "v3-map-companion.wav"
        _write_v3_companion_audio(audio_path)

        for index, spec in enumerate(TAXONOMY):
            image_path = images_dir / f"{spec.fixture_id}.png"
            _require_fixture_path_within(images_dir, image_path, label="image")
            _write_v3_fixture_image(image_path, index)
            passed = _p2t1_pass(spec.fixture_id, image_path, audio_path)
            fixture_results.append(
                V3MapFixtureResult(
                    fixture_id=spec.fixture_id,
                    image_ref=f"images/{spec.fixture_id}.png",
                    image_sha256=_sha256_of(image_path),
                    width=_CANVAS_SIZE,
                    height=_CANVAS_SIZE,
                    taxonomy_token=spec.taxonomy_token,
                    p2t1_pass=passed,
                )
            )
    finally:
        shutil.rmtree(scratch_audio_dir, ignore_errors=True)

    return V3MapAuthoringResult(
        fixtures=tuple(fixture_results),
        all_p2t1_pass=all(fixture.p2t1_pass for fixture in fixture_results),
        scratch_audio_deleted=not scratch_audio_dir.exists(),
    )


def build_manifest(
    result: V3MapAuthoringResult,
    *,
    recipe_module_sha256: str,
    b3_disjointness_verified: bool,
    b4_disjointness_verified: bool,
) -> Mapping[str, object]:
    """Safe, versioned manifest document -- never an absolute path, prompt body, or raw output."""

    expected_ids = tuple(spec.fixture_id for spec in TAXONOMY)
    fixture_ids = tuple(fixture.fixture_id for fixture in result.fixtures)
    fixture_hashes = tuple(fixture.image_sha256 for fixture in result.fixtures)
    if fixture_ids != expected_ids:
        raise V3MapManifestIntegrityError(
            "the manifest requires the exact ordered eight-fixture taxonomy"
        )
    if len(set(fixture_hashes)) != _FIXTURE_COUNT or any(
        _SHA256_PATTERN.fullmatch(value) is None for value in fixture_hashes
    ):
        raise V3MapManifestIntegrityError("fixture SHA-256 values must be valid and unique")
    if (
        not result.all_p2t1_pass
        or not all(fixture.p2t1_pass for fixture in result.fixtures)
        or not result.scratch_audio_deleted
        or result.model_or_gpu_called
    ):
        raise V3MapManifestIntegrityError(
            "all fixtures need P2-T1 PASS, confirmed cleanup, and no model/GPU action"
        )
    if not b3_disjointness_verified or not b4_disjointness_verified:
        raise V3MapManifestIntegrityError("B3 and B4 hash disjointness must both be verified")
    if _SHA256_PATTERN.fullmatch(recipe_module_sha256) is None:
        raise V3MapManifestIntegrityError("recipe_module_sha256 must be lowercase SHA-256")
    for fixture, spec in zip(result.fixtures, TAXONOMY, strict=True):
        if (
            fixture.image_ref != f"images/{spec.fixture_id}.png"
            or _is_absolute_machine_path(Path(fixture.image_ref))
            or fixture.width != _CANVAS_SIZE
            or fixture.height != _CANVAS_SIZE
            or fixture.taxonomy_token != spec.taxonomy_token
        ):
            raise V3MapManifestIntegrityError(
                f"fixture metadata does not match the approved taxonomy: {spec.fixture_id}"
            )

    return {
        "contract_name": "VisionV3MapFixtureManifestV1",
        "contract_version": "1.0",
        "manifest_version": "vision-v3-map-manifest-v1",
        "status": "AWAITING_OWNER_IMAGE_REVIEW",
        "purpose": "MAPPING_VALIDATION_ONLY",
        "has_ground_truth": False,
        "data_policy": "synthetic-only",
        "author": "Person 2",
        "authoring_boundary": (
            "All fixture IDs, image hashes, and recipe identity were authored before any v3 "
            "model output."
        ),
        "prompt_protocol": {
            "protocol_id": _V3_PROMPT_PROTOCOL_ID,
            "sha256": _V3_PROMPT_SHA256,
            "schema_target": _V3_SCHEMA_TARGET,
        },
        "image_generation": {
            "recipe_module_ref": _RECIPE_MODULE_REF,
            "recipe_module_sha256": recipe_module_sha256,
            "deterministic": True,
            "dimensions": {"width": _CANVAS_SIZE, "height": _CANVAS_SIZE},
            "palette_id": "vision-v3-map-palette-v1",
        },
        "disjointness": {
            "b3_regenerated_hash_comparison_status": (
                "VERIFIED_NO_OVERLAP" if b3_disjointness_verified else "NOT_YET_VERIFIED"
            ),
            "b4_manifest_hash_comparison_status": (
                "VERIFIED_NO_OVERLAP" if b4_disjointness_verified else "NOT_YET_VERIFIED"
            ),
        },
        "local_authoring_validation": {
            "p2t1_result": (
                "PASS_FOR_ALL_8_FIXTURES" if result.all_p2t1_pass else "NOT_ALL_FIXTURES_PASSED"
            ),
            "scratch_cleanup": "CONFIRMED" if result.scratch_audio_deleted else "NOT_CONFIRMED",
            "model_or_gpu_called": False,
        },
        "fixtures": [
            {
                "fixture_id": fixture.fixture_id,
                "image_ref": fixture.image_ref,
                "image_sha256": fixture.image_sha256,
                "dimensions": {"width": fixture.width, "height": fixture.height},
                "taxonomy_token": fixture.taxonomy_token,
                "p2t1_pass": fixture.p2t1_pass,
            }
            for fixture in result.fixtures
        ],
    }


__all__ = [
    "TAXONOMY",
    "UnsafeFixturePathError",
    "V3MapAuthoringResult",
    "V3MapFixtureResult",
    "V3MapFixtureSpec",
    "author_v3_map_fixture_package",
    "build_manifest",
]
