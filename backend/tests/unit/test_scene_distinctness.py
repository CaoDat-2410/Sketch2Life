from __future__ import annotations

import pytest

from sketch2life.infrastructure.media.scene_distinctness import near_duplicate_scene


def test_same_artwork_with_different_color_is_not_a_new_scene(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    paths = []
    for color, background in (("black", "white"), ("blue", (232, 225, 218))):
        image = Image.new("RGB", (160, 100), background)
        ImageDraw.Draw(image).rectangle((10, 15, 130, 85), outline=color, width=4)
        path = tmp_path / f"{color}.png"
        image.save(path)
        paths.append(path)

    assert near_duplicate_scene(paths[0], paths[1])


def test_new_visual_subject_is_a_distinct_scene(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    house = Image.new("RGB", (160, 100), "white")
    ImageDraw.Draw(house).rectangle((10, 15, 70, 85), outline="black", width=4)
    tree = Image.new("RGB", (160, 100), (232, 225, 218))
    ImageDraw.Draw(tree).ellipse((90, 15, 150, 75), outline="green", width=4)
    house_path = tmp_path / "house.png"
    tree_path = tmp_path / "tree.png"
    house.save(house_path)
    tree.save(tree_path)

    assert not near_duplicate_scene(house_path, tree_path)
