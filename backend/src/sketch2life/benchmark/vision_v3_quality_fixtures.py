"""Deterministic Phase 8 authoring for the prompt-v3 held-out quality-benchmark fixture package.

Authorized only by the local-only, gitignored evidence notes
``P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE8_QUALITY_BENCHMARK_PLAN_DRAFT.md`` and the decision record
that fixed D-1..D-8, inside the already-approved P2-T3 Phase B B1-B5 boundary. This module contains
pure, deterministic code-generated PNG/WAV authoring, hand-authored ground truth, and
authoring-time local validation helpers only -- there is no adapter, prompt injection, provider,
runner, model, or GPU import or call anywhere in this module, and none is reachable from any
function it defines.

This package is fully disjoint from ``fixtures/vision-b4/**``, ``fixtures/vision-v3-map/**``, and
the B3 scratch recipes -- distinct fixture IDs, an independently authored 256x256 geometric recipe
with its own shade constants, and no shared image content. Its ground truth is fully determined by
the geometry this module defines: every entity, action, relation, theme, and ambiguous-region
target is fixed here, before any v3 model output for these fixtures is ever produced, exactly the
authoring-before-output discipline B4 itself used.

The taxonomy is deliberately denser in relations and themes than B4's own package (which carried
only 4 relation and 2 theme targets across its eight fixtures) because Direction A's prompt-v3
change targets exactly the relation/theme/ambiguous-region collection-omission gap. Fixture 06
carries no scored relation because three equally-direct spatial pairs exist -- the same kind of
honest exception B4 fixture 06 already used -- and fixture 07's circle/square overlap is the
ambiguous-region target with no scored relation, mirroring B4 fixture 07 exactly.

Interior fills reuse the same proven-safe technique as ``vision_b3_mapping_study.py``'s
``_interior_shade`` and ``vision_v3_mapping_fixtures.py``'s ``_textured_shade``: pixels inside a
shape toggle between a dark ink shade and the background shade in a periodic pattern, rather than a
flat fill, so each filled shape carries enough internal luminance transitions to clear the real
P2-T1 ``minimum_edge_strength`` gate.
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
from typing import Any
from wave import open as wave_open
from zlib import compress, crc32

from sketch2life.application.services.media_validation import (
    DeterministicMediaValidator,
    MediaValidationRequest,
)
from sketch2life.domain.understanding.media_quality import MediaDecision
from sketch2life.infrastructure.media_validation.file_inspector import FileMediaSignalInspector

_FIXTURE_COUNT = 8
_CANVAS_SIZE = 256
_BACKGROUND_SHADE = 252
_PRIMARY_INK_SHADE = 18

_DEFAULT_IMAGES_DIR = Path(
    "features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality/images"
)
_DEFAULT_SCRATCH_AUDIO_DIR = Path("data/runtime/vision-v3-quality-authoring-audio")
_RECIPE_MODULE_REF = "backend/src/sketch2life/benchmark/vision_v3_quality_fixtures.py"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

_V3_PROMPT_PROTOCOL_ID = "vision-v2-structured-output-prompt-v3"
_V3_PROMPT_SHA256 = "bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3"
_V3_SCHEMA_TARGET = "VisionUnderstandingResultV2"
_MATCHING_RULE_ID = "vision-v3-quality-matching-rule-v1"
_WINDOWS_DRIVE_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class UnsafeFixturePathError(ValueError):
    """A caller-supplied directory or generated fixture path is not a safe target."""


class V3QualityManifestIntegrityError(ValueError):
    """The authoring result cannot safely produce the review-pending manifest."""


class V3QualityGroundTruthIntegrityError(ValueError):
    """A hand-authored ground-truth reference does not resolve inside its own fixture."""


@dataclass(frozen=True, slots=True)
class V3QualityFixtureSpec:
    """One taxonomy entry -- fixed here, not inferred at runtime."""

    fixture_id: str
    taxonomy_token: str
    description: str


TAXONOMY: tuple[V3QualityFixtureSpec, ...] = (
    V3QualityFixtureSpec(
        "v3q-fixture-01",
        "two_entity_relation_above",
        "circle above a square, one unambiguous vertical relation",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-02",
        "entity_relation_action_combo",
        "circle pointing at a square: one action and one relation",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-03",
        "three_entity_chain_theme",
        "circle, square, triangle in a row: two relations and one sequence theme",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-04",
        "mirrored_pair_symmetry_theme",
        "two triangles mirrored about the vertical axis: a mirrors relation and a symmetry theme",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-05",
        "action_null_endpoint_theme",
        "one circle with an outward arrow to nowhere: a null-endpoint action and a motion theme",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-06",
        "no_canonical_relation_exception",
        "circle, square, triangle in a near-equilateral cluster: no single canonical relation",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-07",
        "overlap_ambiguous_region",
        "circle and square overlapping: the ambiguous-region target, no scored relation",
    ),
    V3QualityFixtureSpec(
        "v3q-fixture-08",
        "dense_multi_collection",
        "circle, square, triangle: one action, one relation, one theme together",
    ),
)


# --- Pure geometry helpers -------------------------------------------------------------------


def _point_in_polygon(x: float, y: float, vertices: tuple[tuple[float, float], ...]) -> bool:
    """Standard ray-casting test; works for the convex polygons used below."""

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


def _mirror_vertices_x(
    vertices: tuple[tuple[float, float], ...], axis_x: float
) -> tuple[tuple[float, float], ...]:
    """Exact reflection about the vertical line ``x == axis_x`` -- a true geometric mirror."""

    return tuple((2 * axis_x - x, y) for x, y in vertices)


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
    """Eight distinct deterministic interior patterns, mirroring the proven-safe technique."""

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


def _textured_circle_layer(center: tuple[float, float], radius: float, recipe_index: int) -> _Layer:
    def layer(x: int, y: int) -> int | None:
        if math.hypot((x + 0.5) - center[0], (y + 0.5) - center[1]) <= radius:
            return _textured_shade(recipe_index, x, y)
        return None

    return layer


def _textured_polygon_layer(vertices: tuple[tuple[float, float], ...], recipe_index: int) -> _Layer:
    def layer(x: int, y: int) -> int | None:
        if _point_in_polygon(x + 0.5, y + 0.5, vertices):
            return _textured_shade(recipe_index, x, y)
        return None

    return layer


def _textured_rect_layer(
    center: tuple[float, float], half_width: float, recipe_index: int
) -> _Layer:
    left, right = center[0] - half_width, center[0] + half_width
    top, bottom = center[1] - half_width, center[1] + half_width

    def layer(x: int, y: int) -> int | None:
        px, py = x + 0.5, y + 0.5
        if left <= px <= right and top <= py <= bottom:
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


def _solid_arrowhead_layer(
    tip: tuple[float, float], angle_degrees: float, size: float, shade: int
) -> _Layer:
    return _solid_polygon_layer(_arrowhead_vertices(tip, angle_degrees, size), shade)


def _arrow_layers(
    start: tuple[float, float], end: tuple[float, float], thickness: float, shade: int
) -> tuple[_Layer, ...]:
    angle_degrees = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
    return (
        _solid_line_layer(start, end, thickness, shade),
        _solid_arrowhead_layer(end, angle_degrees, thickness * 3.2, shade),
    )


def _fixture_layers(index: int) -> tuple[_Layer, ...]:
    """Exact taxonomy fixed above, indexed 0-7 (fixtures 01-08)."""

    if index == 0:
        circle = _textured_circle_layer((128, 74), 40, 0)
        square = _textured_rect_layer((128, 190), 40, 0)
        return (circle, square)
    if index == 1:
        circle = _textured_circle_layer((70, 128), 34, 1)
        square = _textured_rect_layer((186, 128), 34, 1)
        arrow = _arrow_layers((104, 128), (152, 128), 6, _PRIMARY_INK_SHADE)
        return (circle, square, *arrow)
    if index == 2:
        circle = _textured_circle_layer((56, 128), 30, 2)
        square = _textured_rect_layer((128, 128), 26, 2)
        triangle = _textured_polygon_layer(_regular_polygon((200, 128), 34, 3, -90), 2)
        return (circle, square, triangle)
    if index == 3:
        left_triangle = _regular_polygon((80, 128), 38, 3, -90)
        right_triangle = _mirror_vertices_x(left_triangle, 128)
        return (
            _textured_polygon_layer(left_triangle, 3),
            _textured_polygon_layer(right_triangle, 3),
        )
    if index == 4:
        circle = _textured_circle_layer((128, 128), 38, 4)
        arrow = _arrow_layers((166, 128), (222, 128), 5, _PRIMARY_INK_SHADE)
        return (circle, *arrow)
    if index == 5:
        circle = _textured_circle_layer((128, 74), 30, 5)
        square = _textured_rect_layer((78, 192), 30, 5)
        triangle = _textured_polygon_layer(_regular_polygon((178, 192), 34, 3, -90), 5)
        return (circle, square, triangle)
    if index == 6:
        # The square is taller than the circle's diameter, so its top-left and bottom-left
        # corners poke out above and below the circle's silhouette while the circle's own left arc
        # stays fully clear of the square -- both shapes keep an unmistakable, unoccluded
        # identifying feature (a right-angle corner; a full curve) instead of blending into one
        # seamless outline.
        circle = _textured_circle_layer((90, 128), 44, 6)
        square = _textured_rect_layer((150, 128), 56, 6)
        return (circle, square)
    if index == 7:
        circle = _textured_circle_layer((128, 76), 32, 7)
        square = _textured_rect_layer((76, 194), 32, 7)
        triangle = _textured_polygon_layer(_regular_polygon((182, 194), 36, 3, -90), 7)
        arrow = _arrow_layers((104, 100), (152, 158), 5, _PRIMARY_INK_SHADE)
        return (circle, square, triangle, *arrow)
    raise ValueError(f"no fixture layout defined for index {index}")


def _render_shade(layers: tuple[_Layer, ...], x: int, y: int) -> int:
    shade = _BACKGROUND_SHADE
    for layer in layers:
        result = layer(x, y)
        if result is not None:
            shade = result
    return shade


def _write_v3_quality_fixture_image(path: Path, index: int) -> None:
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


def _write_v3_quality_companion_audio(path: Path) -> None:
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
            image_artifact_ref=f"vision-v3-quality-{fixture_id}-synthetic-image",
            audio_artifact_ref="vision-v3-quality-synthetic-audio",
        )
    )
    return result.decision is MediaDecision.PASS


# --- Hand-authored ground truth ------------------------------------------------------------------
#
# Fully determined by the geometry fixed in ``_fixture_layers`` above, authored before any v3
# model output for these fixtures is ever seen. Every ``*_ref`` below must resolve to an
# ``ground_truth_id`` declared earlier in the same fixture; ``build_ground_truth`` checks this
# before the document can ever be written.

_GROUND_TRUTH_FIXTURES: tuple[Mapping[str, Any], ...] = (
    {
        "fixture_id": "v3q-fixture-01",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
        ],
        "actions": [],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "above",
                "subject_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "themes": [],
        "ambiguous_regions": [],
    },
    {
        "fixture_id": "v3q-fixture-02",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
        ],
        "actions": [
            {
                "ground_truth_id": "gt-a1",
                "label": "points",
                "actor_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "left of",
                "subject_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "themes": [],
        "ambiguous_regions": [],
    },
    {
        "fixture_id": "v3q-fixture-03",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
            {"ground_truth_id": "gt-e3", "label": "triangle"},
        ],
        "actions": [],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "left of",
                "subject_ref": "gt-e1",
                "object_ref": "gt-e2",
            },
            {
                "ground_truth_id": "gt-r2",
                "predicate": "left of",
                "subject_ref": "gt-e2",
                "object_ref": "gt-e3",
            },
        ],
        "themes": [
            {
                "ground_truth_id": "gt-t1",
                "label": "sequence",
                "evidence_refs": ["gt-r1", "gt-r2"],
            }
        ],
        "ambiguous_regions": [],
    },
    {
        "fixture_id": "v3q-fixture-04",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "triangle"},
            {"ground_truth_id": "gt-e2", "label": "triangle"},
        ],
        "actions": [],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "mirrors",
                "subject_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "themes": [
            {
                "ground_truth_id": "gt-t1",
                "label": "symmetry",
                "evidence_refs": ["gt-e1", "gt-e2", "gt-r1"],
            }
        ],
        "ambiguous_regions": [],
    },
    {
        "fixture_id": "v3q-fixture-05",
        "entities": [{"ground_truth_id": "gt-e1", "label": "circle"}],
        "actions": [
            {
                "ground_truth_id": "gt-a1",
                "label": "moves",
                "actor_ref": "gt-e1",
                "object_ref": None,
            }
        ],
        "relations": [],
        "themes": [
            {"ground_truth_id": "gt-t1", "label": "motion", "evidence_refs": ["gt-a1"]}
        ],
        "ambiguous_regions": [],
    },
    {
        "fixture_id": "v3q-fixture-06",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
            {"ground_truth_id": "gt-e3", "label": "triangle"},
        ],
        "actions": [],
        "relations": [],
        "relation_scoring_note": (
            "No canonical scored relation: the three entities form a near-equilateral cluster "
            "with multiple equally direct pairwise spatial relations, mirroring the B4 "
            "fixture-06 exception."
        ),
        "themes": [
            {
                "ground_truth_id": "gt-t1",
                "label": "cluster",
                "evidence_refs": ["gt-e1", "gt-e2", "gt-e3"],
            }
        ],
        "ambiguous_regions": [],
    },
    {
        "fixture_id": "v3q-fixture-07",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
        ],
        "actions": [],
        "relations": [],
        "relation_scoring_note": (
            "No canonical scored relation: overlap is deliberately the ambiguous-region target, "
            "mirroring the B4 fixture-07 exception."
        ),
        "themes": [],
        "ambiguous_regions": [{"ground_truth_id": "gt-ar1"}],
    },
    {
        "fixture_id": "v3q-fixture-08",
        "entities": [
            {"ground_truth_id": "gt-e1", "label": "circle"},
            {"ground_truth_id": "gt-e2", "label": "square"},
            {"ground_truth_id": "gt-e3", "label": "triangle"},
        ],
        "actions": [
            {
                "ground_truth_id": "gt-a1",
                "label": "points",
                "actor_ref": "gt-e1",
                "object_ref": "gt-e2",
            }
        ],
        "relations": [
            {
                "ground_truth_id": "gt-r1",
                "predicate": "left of",
                "subject_ref": "gt-e2",
                "object_ref": "gt-e3",
            }
        ],
        "themes": [
            {
                "ground_truth_id": "gt-t1",
                "label": "group",
                "evidence_refs": ["gt-e1", "gt-e2", "gt-e3"],
            }
        ],
        "ambiguous_regions": [],
    },
)


def _require_declared_reference(
    ref: str | None, *, declared: set[str], field: str, fixture_id: object
) -> None:
    if ref is not None and ref not in declared:
        raise V3QualityGroundTruthIntegrityError(
            f"{fixture_id}: {field} references undeclared id {ref!r}"
        )


def _validate_ground_truth_reference_integrity() -> None:
    expected_ids = tuple(spec.fixture_id for spec in TAXONOMY)
    fixture_ids = tuple(str(fixture["fixture_id"]) for fixture in _GROUND_TRUTH_FIXTURES)
    if fixture_ids != expected_ids:
        raise V3QualityGroundTruthIntegrityError(
            "ground truth must declare the exact ordered eight-fixture taxonomy"
        )
    for fixture in _GROUND_TRUTH_FIXTURES:
        fixture_id = fixture["fixture_id"]
        declared: set[str] = set()
        for entity in fixture["entities"]:
            declared.add(str(entity["ground_truth_id"]))
        for action in fixture["actions"]:
            declared.add(str(action["ground_truth_id"]))
        for relation in fixture["relations"]:
            declared.add(str(relation["ground_truth_id"]))
        for ambiguous_region in fixture["ambiguous_regions"]:
            declared.add(str(ambiguous_region["ground_truth_id"]))

        for action in fixture["actions"]:
            _require_declared_reference(
                action.get("actor_ref"),
                declared=declared,
                field="actor_ref",
                fixture_id=fixture_id,
            )
            _require_declared_reference(
                action.get("object_ref"),
                declared=declared,
                field="object_ref",
                fixture_id=fixture_id,
            )
        for relation in fixture["relations"]:
            _require_declared_reference(
                relation["subject_ref"],
                declared=declared,
                field="subject_ref",
                fixture_id=fixture_id,
            )
            _require_declared_reference(
                relation["object_ref"],
                declared=declared,
                field="object_ref",
                fixture_id=fixture_id,
            )
        for theme in fixture["themes"]:
            for ref in theme["evidence_refs"]:
                _require_declared_reference(
                    ref, declared=declared, field="evidence_refs", fixture_id=fixture_id
                )


_validate_ground_truth_reference_integrity()


def build_ground_truth() -> Mapping[str, object]:
    """Return the versioned ground-truth document. Reference integrity is checked at import time."""

    return {
        "contract_name": "VisionV3QualityGroundTruthV1",
        "contract_version": "1.0",
        "ground_truth_version": "vision-v3-quality-ground-truth-v1",
        "data_policy": "synthetic-only",
        "author": "Person 2",
        "authoring_boundary": (
            "Authored before any v3 model output for these fixtures; every entity, action, "
            "relation, theme, and ambiguous-region target is fully determined by this module's "
            "deterministic geometry recipe, not observed from any model. Do not revise from "
            "model output."
        ),
        "fixtures": list(_GROUND_TRUTH_FIXTURES),
    }


# --- Authoring orchestration ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class V3QualityFixtureResult:
    fixture_id: str
    image_ref: str
    image_sha256: str
    width: int
    height: int
    taxonomy_token: str
    p2t1_pass: bool


@dataclass(frozen=True, slots=True)
class V3QualityAuthoringResult:
    fixtures: tuple[V3QualityFixtureResult, ...]
    all_p2t1_pass: bool
    scratch_audio_deleted: bool
    model_or_gpu_called: bool = False


def author_v3_quality_fixture_package(
    *,
    images_dir: Path = _DEFAULT_IMAGES_DIR,
    scratch_audio_dir: Path = _DEFAULT_SCRATCH_AUDIO_DIR,
) -> V3QualityAuthoringResult:
    """Author exactly eight deterministic PNGs and locally validate each with a real P2-T1 PASS.

    Mirrors ``vision_v3_mapping_fixtures.py``'s ``author_v3_map_fixture_package`` exactly in
    safety discipline: default paths are accepted only from the repository root,
    ``scratch_audio_dir`` is always deleted in ``finally``, and no model, adapter, provider, or
    GPU path is reachable from this function.
    """

    _require_repository_root_for_default_paths(images_dir, scratch_audio_dir)
    _require_relative_repo_path(images_dir, label="images_dir")
    _require_relative_repo_path(scratch_audio_dir, label="scratch_audio_dir")

    images_dir.mkdir(parents=True, exist_ok=True)

    fixture_results: list[V3QualityFixtureResult] = []
    try:
        scratch_audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = scratch_audio_dir / "v3-quality-companion.wav"
        _write_v3_quality_companion_audio(audio_path)

        for index, spec in enumerate(TAXONOMY):
            image_path = images_dir / f"{spec.fixture_id}.png"
            _require_fixture_path_within(images_dir, image_path, label="image")
            _write_v3_quality_fixture_image(image_path, index)
            passed = _p2t1_pass(spec.fixture_id, image_path, audio_path)
            fixture_results.append(
                V3QualityFixtureResult(
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

    return V3QualityAuthoringResult(
        fixtures=tuple(fixture_results),
        all_p2t1_pass=all(fixture.p2t1_pass for fixture in fixture_results),
        scratch_audio_deleted=not scratch_audio_dir.exists(),
    )


def build_manifest(
    result: V3QualityAuthoringResult,
    *,
    recipe_module_sha256: str,
    ground_truth_sha256: str,
    matching_rule_sha256: str,
    b3_disjointness_verified: bool,
    b4_disjointness_verified: bool,
    v3_map_disjointness_verified: bool,
) -> Mapping[str, object]:
    """Safe, versioned manifest document -- never an absolute path, prompt body, or raw output."""

    expected_ids = tuple(spec.fixture_id for spec in TAXONOMY)
    fixture_ids = tuple(fixture.fixture_id for fixture in result.fixtures)
    fixture_hashes = tuple(fixture.image_sha256 for fixture in result.fixtures)
    if fixture_ids != expected_ids:
        raise V3QualityManifestIntegrityError(
            "the manifest requires the exact ordered eight-fixture taxonomy"
        )
    if len(set(fixture_hashes)) != _FIXTURE_COUNT or any(
        _SHA256_PATTERN.fullmatch(value) is None for value in fixture_hashes
    ):
        raise V3QualityManifestIntegrityError("fixture SHA-256 values must be valid and unique")
    if (
        not result.all_p2t1_pass
        or not all(fixture.p2t1_pass for fixture in result.fixtures)
        or not result.scratch_audio_deleted
        or result.model_or_gpu_called
    ):
        raise V3QualityManifestIntegrityError(
            "all fixtures need P2-T1 PASS, confirmed cleanup, and no model/GPU action"
        )
    all_disjoint = (
        b3_disjointness_verified and b4_disjointness_verified and v3_map_disjointness_verified
    )
    if not all_disjoint:
        raise V3QualityManifestIntegrityError(
            "B3, B4, and v3-map hash disjointness must all be verified"
        )
    for value in (recipe_module_sha256, ground_truth_sha256, matching_rule_sha256):
        if _SHA256_PATTERN.fullmatch(value) is None:
            raise V3QualityManifestIntegrityError("identity hashes must be lowercase SHA-256")
    for fixture, spec in zip(result.fixtures, TAXONOMY, strict=True):
        if (
            fixture.image_ref != f"images/{spec.fixture_id}.png"
            or _is_absolute_machine_path(Path(fixture.image_ref))
            or fixture.width != _CANVAS_SIZE
            or fixture.height != _CANVAS_SIZE
            or fixture.taxonomy_token != spec.taxonomy_token
        ):
            raise V3QualityManifestIntegrityError(
                f"fixture metadata does not match the approved taxonomy: {spec.fixture_id}"
            )

    return {
        "contract_name": "VisionV3QualityFixtureManifestV1",
        "contract_version": "1.0",
        "manifest_version": "vision-v3-quality-manifest-v1",
        "status": "AWAITING_OWNER_REVIEW",
        "split": "HELD_OUT",
        "purpose": "QUALITY_BENCHMARK",
        "has_ground_truth": True,
        "scope": "S3_FULL_SCORING_WITH_DIAGNOSTIC_SPLIT",
        "data_policy": "synthetic-only",
        "author": "Person 2",
        "authoring_boundary": (
            "All fixture IDs, image hashes, ground truth, and matching-rule identity were "
            "authored before any Phase 8 v3 model output."
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
            "palette_id": "vision-v3-quality-palette-v1",
        },
        "ground_truth": {
            "ref": "ground-truth-v1.json",
            "sha256": ground_truth_sha256,
        },
        "matching_rule": {
            "rule_id": _MATCHING_RULE_ID,
            "ref": "matching-rule-v1.md",
            "sha256": matching_rule_sha256,
        },
        "disjointness": {
            "b3_regenerated_hash_comparison_status": (
                "VERIFIED_NO_OVERLAP" if b3_disjointness_verified else "NOT_YET_VERIFIED"
            ),
            "b4_manifest_hash_comparison_status": (
                "VERIFIED_NO_OVERLAP" if b4_disjointness_verified else "NOT_YET_VERIFIED"
            ),
            "v3_map_manifest_hash_comparison_status": (
                "VERIFIED_NO_OVERLAP" if v3_map_disjointness_verified else "NOT_YET_VERIFIED"
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
    "V3QualityAuthoringResult",
    "V3QualityFixtureResult",
    "V3QualityFixtureSpec",
    "V3QualityGroundTruthIntegrityError",
    "V3QualityManifestIntegrityError",
    "author_v3_quality_fixture_package",
    "build_ground_truth",
    "build_manifest",
]
