from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from sketch2life.application.services.auto_rig.part_masks import derive_part_masks_from_subject_mask
from sketch2life.contracts.schemas.auto_rig import RigArchetype


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _silhouette() -> bytes:
    mask = Image.new("L", (100, 100), 0)
    ImageDraw.Draw(mask).ellipse((12, 8, 88, 92), fill=255)
    return _png(mask)


@pytest.mark.parametrize(
    ("archetype", "expected_roles"),
    [
        (RigArchetype.BUTTERFLY, set()),
        (RigArchetype.BIRD, set()),
        (RigArchetype.FLOWER, set()),
        (RigArchetype.TREE_BRANCH, set()),
        (RigArchetype.FISH, set()),
        (RigArchetype.BIPED, set()),
    ],
)
def test_uniform_silhouette_does_not_invent_archetype_parts(
    archetype: RigArchetype, expected_roles: set[str]
) -> None:
    source = Image.new("RGB", (100, 100), "white")
    parent_bytes = _silhouette()

    parts = derive_part_masks_from_subject_mask(_png(source), parent_bytes, archetype)

    assert {part.role for part in parts} == expected_roles


def test_visible_disjoint_components_can_be_proposed_as_butterfly_parts() -> None:
    source = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(source)
    draw.ellipse((21, 33, 39, 51), fill=(255, 30, 30))
    draw.ellipse((41, 41, 59, 59), fill=(30, 80, 255))
    draw.ellipse((61, 33, 79, 51), fill=(255, 30, 30))
    parent_bytes = _silhouette()

    parts = derive_part_masks_from_subject_mask(_png(source), parent_bytes, RigArchetype.BUTTERFLY)

    assert {part.role for part in parts} == {"left-wing", "body", "right-wing"}
    parent = Image.open(BytesIO(parent_bytes)).convert("1")
    part_images = [Image.open(BytesIO(part.mask_png)).convert("1") for part in parts]
    parent_pixels = list(parent.getdata())
    assignments = [0] * len(parent_pixels)
    for part_image in part_images:
        for index, is_part in enumerate(part_image.getdata()):
            if not is_part:
                continue
            assert parent_pixels[index]
            assignments[index] += 1
    assert all(count <= 1 and (inside or count == 0) for count, inside in zip(
        assignments, parent_pixels, strict=True
    ))
    assert sum(assignments) < sum(parent_pixels)


@pytest.mark.parametrize(
    "archetype",
    [RigArchetype.GENERIC_ORGANIC, RigArchetype.RIGID, RigArchetype.UNKNOWN],
)
def test_unmapped_shapes_are_not_split_into_fabricated_anatomy(archetype: RigArchetype) -> None:
    source = Image.new("RGB", (100, 100), "white")

    assert derive_part_masks_from_subject_mask(_png(source), _silhouette(), archetype) == ()
