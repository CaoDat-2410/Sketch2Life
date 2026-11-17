"""Create a non-child, authored-path whiteboard visual pilot outside Git.

This is a visual spike, not automated vectorization or product media.  All
figures are unnamed; no real child input, remote model or TTS is used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sketch2life.infrastructure.media.whiteboard_mvp_renderer import (
    WhiteboardMvpRenderSpec,
)
from sketch2life.infrastructure.media.whiteboard_vector_pilot import render_vector_scene


def curve(start, *segments, steps=10):
    """Sample authored cubic Béziers into stable centerline points."""

    points = [list(start)]
    current = start
    for a, b, end in segments:
        for index in range(1, steps + 1):
            t = index / steps
            u = 1 - t
            points.append([
                round(u**3 * current[0] + 3 * u * u * t * a[0]
                      + 3 * u * t * t * b[0] + t**3 * end[0], 3),
                round(u**3 * current[1] + 3 * u * u * t * a[1]
                      + 3 * u * t * t * b[1] + t**3 * end[1], 3),
            ])
        current = end
    return points


def oval(cx, cy, rx, ry):
    k = 0.5523
    return curve((cx + rx, cy),
                 ((cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry)),
                 ((cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy)),
                 ((cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry)),
                 ((cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy)))


def stroke(points, width=2.1, color="#28303a"):
    return {"points": points, "width": width, "color": color}


def fill(points, color):
    return {"polygon": points, "color": color}


def _tree():
    trunk = curve((86, 255),
                  ((83, 216), (91, 179), (95, 132)),
                  ((99, 112), (104, 92), (107, 78)))
    branch_l = curve((97, 172), ((78, 151), (66, 132), (57, 109)))
    branch_r = curve((99, 150), ((115, 136), (127, 112), (135, 100)))
    canopy = curve((48, 130),
                   ((24, 137), (21, 113), (35, 104)),
                   ((20, 85), (41, 71), (56, 77)),
                   ((51, 55), (79, 51), (87, 63)),
                   ((98, 39), (123, 48), (127, 64)),
                   ((150, 56), (161, 77), (151, 93)),
                   ((169, 109), (156, 129), (137, 124)),
                   ((123, 143), (104, 134), (98, 129)),
                   ((81, 145), (64, 140), (48, 130)))
    leaf_veins = [curve((x, y), ((x + 4, y - 4), (x + 9, y - 5), (x + 13, y - 8)), steps=6)
                  for x, y in ((46, 101), (78, 82), (113, 73), (134, 100), (75, 118))]
    return {
        "id": "tree", "start": 0.01, "end": 0.27,
        "fills": [fill(canopy, "#a9d68c"),
                  fill([[86, 255], [97, 144], [101, 119], [105, 79], [111, 80],
                        [105, 158], [99, 212], [101, 255]], "#c79570")],
        "strokes": [stroke(trunk, 3.2), stroke(branch_l, 2.5), stroke(branch_r, 2.5),
                    stroke(canopy, 2.6)] + [stroke(path, 1.2, "#588457") for path in leaf_veins],
    }


def _house():
    roof = [[384, 121], [462, 53], [565, 116], [559, 126], [461, 69], [391, 132]]
    porch = [[406, 121], [548, 121], [548, 268], [406, 268]]
    door = [[462, 265], [462, 193], [468, 183], [486, 182], [494, 193], [494, 265]]
    windows = [
        [[419, 149], [449, 148], [449, 178], [419, 178]],
        [[506, 148], [536, 149], [536, 178], [506, 178]],
    ]
    strokes = [
        stroke(curve((384, 121), ((417, 99), (440, 65), (462, 53)),
                     ((492, 67), (537, 101), (565, 116))), 3.2),
        stroke([[384, 121], [392, 132], [461, 69], [558, 126], [565, 116]], 2.8),
        stroke([[406, 125], [406, 268], [548, 268], [548, 126]], 2.9),
        stroke(curve((462, 265), ((462, 240), (461, 212), (462, 193)),
                     ((465, 178), (491, 175), (494, 193)),
                     ((495, 217), (494, 245), (494, 265))), 2.3),
        stroke(oval(484, 227, 1.7, 1.7), 1.7, "#755a40"),
        stroke([[414, 266], [414, 285], [542, 285], [542, 266]], 2.1),
    ]
    for pane in windows:
        strokes.extend([stroke(pane + [pane[0]], 2.1),
                        stroke([[pane[0][0] + 15, pane[0][1]],
                                [pane[0][0] + 15, pane[2][1]]], 1.3),
                        stroke([[pane[0][0], pane[0][1] + 15],
                                [pane[1][0], pane[0][1] + 15]], 1.3)])
    strokes.extend(stroke([[414 + i * 12, 137], [420 + i * 12, 137]], 0.9,
                          "#ad695e") for i in range(11))
    return {"id": "house", "start": 0.18, "end": 0.52,
            "fills": [fill(porch, "#f5e7d5"), fill(roof, "#dc6c64"),
                      fill(door, "#b78b6e")]
                     + [fill(pane, "#a7dbea") for pane in windows],
            "strokes": strokes}


def _figure(name, x, y, scale, shirt, start, end):
    head_y = y - 38 * scale
    head = oval(x, head_y, 15 * scale, 17 * scale)
    hair = curve((x - 14 * scale, head_y - 4 * scale),
                 ((x - 17 * scale, head_y - 21 * scale),
                  (x + 12 * scale, head_y - 24 * scale),
                  (x + 15 * scale, head_y - 3 * scale)))
    torso = curve((x - 15 * scale, y - 13 * scale),
                  ((x - 12 * scale, y - 21 * scale),
                   (x + 10 * scale, y - 21 * scale), (x + 15 * scale, y - 13 * scale)),
                  ((x + 17 * scale, y + 12 * scale),
                   (x + 16 * scale, y + 29 * scale), (x + 12 * scale, y + 37 * scale)),
                  ((x - 1 * scale, y + 40 * scale),
                   (x - 14 * scale, y + 39 * scale), (x - 16 * scale, y + 36 * scale)),
                  ((x - 17 * scale, y + 13 * scale),
                   (x - 15 * scale, y - 5 * scale), (x - 15 * scale, y - 13 * scale)))
    left_arm = curve((x - 13 * scale, y - 6 * scale),
                     ((x - 27 * scale, y + 2 * scale),
                      (x - 30 * scale, y + 25 * scale),
                      (x - 43 * scale, y + 29 * scale)))
    right_arm = curve((x + 13 * scale, y - 6 * scale),
                      ((x + 27 * scale, y + 2 * scale),
                       (x + 30 * scale, y + 25 * scale),
                       (x + 43 * scale, y + 29 * scale)))
    left_leg = curve((x - 7 * scale, y + 37 * scale),
                     ((x - 8 * scale, y + 52 * scale),
                      (x - 11 * scale, y + 66 * scale),
                      (x - 17 * scale, y + 77 * scale)))
    right_leg = curve((x + 7 * scale, y + 37 * scale),
                      ((x + 8 * scale, y + 53 * scale),
                       (x + 10 * scale, y + 67 * scale),
                       (x + 16 * scale, y + 77 * scale)))
    smile = curve((x - 5 * scale, head_y + 5 * scale),
                  ((x - 2 * scale, head_y + 9 * scale),
                   (x + 3 * scale, head_y + 9 * scale),
                   (x + 6 * scale, head_y + 4 * scale)))
    strokes = [stroke(head, 1.9), stroke(hair, 2.5), stroke(torso, 2.2),
               stroke(left_arm, 2.2), stroke(right_arm, 2.2),
               stroke(left_leg, 2.5), stroke(right_leg, 2.5),
               stroke(smile, 1.2)]
    for eye_x in (x - 5 * scale, x + 5 * scale):
        strokes.append(stroke(oval(eye_x, head_y + 1 * scale,
                                   0.9 * scale, 1.2 * scale), 1.2))
    for foot_x, direction in ((x - 17 * scale, -1), (x + 16 * scale, 1)):
        strokes.append(stroke(curve((foot_x, y + 77 * scale),
                                    ((foot_x + 2 * direction, y + 81 * scale),
                                     (foot_x + 12 * direction, y + 81 * scale),
                                     (foot_x + 15 * direction, y + 78 * scale))), 2.4))
    return {"id": name, "start": start, "end": end,
            "fills": [fill(head, "#f7d5b9"), fill(torso, shirt)], "strokes": strokes}


def _details():
    ground = curve((15, 287), ((130, 294), (264, 292), (367, 288)),
                   ((475, 287), (565, 295), (625, 285)))
    path = curve((367, 288), ((384, 300), (378, 318), (358, 346)))
    blooms = []
    for x, y in ((385, 312), (400, 329), (564, 306), (589, 322), (132, 310)):
        blooms.append(stroke([[x, y + 13], [x, y - 3]], 1.5, "#688f68"))
        blooms.append(stroke(oval(x, y - 7, 4.5, 4.5), 1.3, "#ba656b"))
    return {"id": "details", "start": 0.76, "end": 1.0,
            "fills": [],
            "strokes": [stroke(ground, 1.9, "#768b6c"),
                        stroke(path, 1.5, "#b9a390")] + blooms}


def make_scene() -> dict:
    """A generic authored storyboard scene, not a copy of any uploaded image."""

    return {
        "version": 1, "width": 640, "height": 360,
        "objects": [
            _tree(), _house(),
            _figure("figure-left", 220, 218, 1.0, "#e99d72", 0.42, 0.65),
            _figure("figure-middle", 285, 238, 0.75, "#8ac2d7", 0.58, 0.77),
            _figure("figure-right", 350, 216, 1.05, "#e7be74", 0.69, 0.89),
            _details(),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.output_dir.resolve()
    repository_root = Path(__file__).resolve().parents[1]
    if directory.is_relative_to(repository_root) or directory.exists():
        raise ValueError("use a new output directory outside Git")
    directory.mkdir(parents=True)
    scene_path = directory / "synthetic-vector-scene.json"
    scene_path.write_text(json.dumps(make_scene(), indent=2), encoding="utf-8")
    result = render_vector_scene(
        scene_path, directory / "vector-pilot.mp4",
        spec=WhiteboardMvpRenderSpec(fps=12, duration_seconds=8),
        still_directory=directory / "frames",
    )
    print(json.dumps({"scene": str(scene_path), "mp4": result.output_path,
                      "frames": str(directory / "frames"), "size_bytes": result.size_bytes}))


if __name__ == "__main__":
    main()
