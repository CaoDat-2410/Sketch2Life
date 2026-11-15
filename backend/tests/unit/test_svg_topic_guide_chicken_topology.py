from __future__ import annotations

import unittest

from sketch2life.domain.svg_engine import (
    SvgRuleError,
    _validate_chicken_guide_topology,
)


_PATH_BY_PART = {
    "body": "chicken_body",
    "neck": "chicken_neck",
    "head": "chicken_head",
    "beak": "chicken_beak",
    "comb": "chicken_comb",
    "wing": "chicken_wing",
    "tail": "chicken_tail",
    "left_leg": "chicken_left_leg",
    "right_leg": "chicken_right_leg",
}


def _parts() -> dict[str, dict[str, list[str]]]:
    dependencies = {
        "body": ["head"],
        "neck": ["head", "body"],
        "head": [],
        "beak": ["head"],
        "comb": ["head"],
        "wing": ["body"],
        "tail": ["body"],
        "left_leg": ["body"],
        "right_leg": ["body"],
    }
    return {
        part_id: {"path_ids": [path_id], "depends_on": dependencies[part_id]}
        for part_id, path_id in _PATH_BY_PART.items()
    }


def _geometry(*, short_body: bool = False, disconnected_wing: bool = False):
    boxes = {
        "chicken_body": (131, 163, 389, 374) if not short_body else (131, 200, 389, 245),
        "chicken_neck": (118, 145, 190, 232),
        "chicken_head": (107, 75, 184, 151),
        "chicken_beak": (79, 110, 111, 128),
        "chicken_comb": (120, 68, 171, 100),
        "chicken_wing": (430, 180, 490, 245) if disconnected_wing else (198, 237, 316, 308),
        "chicken_tail": (355, 151, 442, 273),
        "chicken_left_leg": (208, 358, 224, 418),
        "chicken_right_leg": (286, 359, 299, 418),
    }
    endpoints = {
        "chicken_body": ((190, 196), (190, 196)),
        "chicken_neck": ((190, 196), (118, 150)),
        "chicken_head": ((107, 113), (107, 113)),
        "chicken_beak": ((110, 111), (111, 124)),
        "chicken_comb": ((127, 88), (143, 96)),
        "chicken_wing": ((198, 275), (198, 275)),
        "chicken_tail": ((355, 235), (359, 257)),
        "chicken_left_leg": ((224, 358), (208, 418)),
        "chicken_right_leg": ((286, 359), (299, 418)),
    }
    return {
        path_id: {
            "bbox": box,
            "first": endpoints[path_id][0],
            "last": endpoints[path_id][1],
            "commands": {"M", "C"},
        }
        for path_id, box in boxes.items()
    }


class ChickenGuideTopologyTests(unittest.TestCase):
    def test_reference_pose_with_head_first_dependencies_passes(self) -> None:
        _validate_chicken_guide_topology(_parts(), _geometry())

    def test_body_size_failure_has_a_specific_diagnostic(self) -> None:
        with self.assertRaisesRegex(SvgRuleError, "SVG_CHICKEN_BODY_SHAPE_INVALID"):
            _validate_chicken_guide_topology(
                _parts(), _geometry(short_body=True)
            )

    def test_connection_failure_keeps_connection_diagnostic(self) -> None:
        with self.assertRaisesRegex(
            SvgRuleError, "SVG_CHICKEN_ANATOMY_CONNECTION_INVALID"
        ):
            _validate_chicken_guide_topology(
                _parts(), _geometry(disconnected_wing=True)
            )


if __name__ == "__main__":
    unittest.main()
